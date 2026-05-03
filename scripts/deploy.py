#!/usr/bin/env python3
"""Build the Astro site and deploy dist/ to the configured FTP host.

Reads connection details from .env at the project root:
    FTP_HOST            (required — bare hostname or IP, e.g. ftp.example.com)
    FTP_USER            (required)
    FTP_PASSWORD        (required)
    FTP_REMOTE_DIR      (optional — leave empty when the FTP account is already
                         chrooted to the site root, as Hostinger does)
    FTP_PORT            (optional — default 21)
    FTP_USE_TLS         (optional — default "true"; set to "false" for plain FTP)
    FTP_TLS_VERIFY      (optional — default "true"; set to "false" to skip cert
                         hostname verification when connecting by IP. The TLS
                         handshake still happens — only verification is relaxed.)

Run with `pnpm deploy` (uses package.json) or `python3 scripts/deploy.py`.
Use `--skip-build` to upload an existing dist/ without rebuilding.
"""
from __future__ import annotations

import argparse
import os
import ssl
import subprocess
import sys
import time
from ftplib import FTP, FTP_TLS, error_perm
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
ENV_FILE = ROOT / ".env"

# Files in dist/ that exist on the host but should never be overwritten.
# Their values live only on the server (e.g., the Turnstile secret).
EXCLUDE_FILENAMES = {"contact.config.php"}


class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    CYAN = "\033[36m"


def info(msg: str) -> None:
    print(f"{C.CYAN}→{C.RESET} {msg}")


def ok(msg: str) -> None:
    print(f"{C.GREEN}✓{C.RESET} {msg}")


def warn(msg: str) -> None:
    print(f"{C.YELLOW}⚠{C.RESET} {msg}")


def err(msg: str) -> None:
    print(f"{C.RED}✗{C.RESET} {msg}", file=sys.stderr)


def step(msg: str) -> None:
    print(f"\n{C.BOLD}{C.BLUE}{msg}{C.RESET}")


def load_env(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    out: dict[str, str] = {}
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        out[key.strip()] = value.strip().strip('"').strip("'")
    return out


def require(env: dict[str, str], key: str) -> str:
    val = env.get(key) or os.environ.get(key, "")
    if not val:
        err(f"Missing required env var: {key}. Add it to .env")
        sys.exit(1)
    return val


def normalize_host(host: str) -> str:
    """Strip URL-style scheme/path so ftplib gets a bare hostname."""
    cleaned = host.strip()
    for scheme in ("ftps://", "ftp://", "sftp://", "https://", "http://"):
        if cleaned.lower().startswith(scheme):
            cleaned = cleaned[len(scheme):]
            break
    return cleaned.rstrip("/").split("/", 1)[0]


def format_size(num: float) -> str:
    for unit in ("B", "KB", "MB"):
        if num < 1024:
            return f"{num:.1f} {unit}"
        num /= 1024
    return f"{num:.1f} GB"


def run_build() -> None:
    step("[1/3] Building site (pnpm build)")
    proc = subprocess.run(["pnpm", "build"], cwd=ROOT)
    if proc.returncode != 0:
        err("Build failed")
        sys.exit(proc.returncode)
    if not DIST.exists():
        err(f"Build succeeded but dist/ not found at {DIST}")
        sys.exit(1)
    ok("Build complete")


def collect_files(root: Path) -> list[tuple[Path, str]]:
    files: list[tuple[Path, str]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if path.name in EXCLUDE_FILENAMES:
            continue
        files.append((path, rel))
    return files


def connect_ftp(
    host: str,
    port: int,
    user: str,
    password: str,
    use_tls: bool,
    tls_verify: bool = True,
):
    label = "FTPS" if use_tls else "FTP"
    if use_tls and not tls_verify:
        label += " (cert verify off)"
    step(f"[2/3] Connecting to {user}@{host}:{port} ({label})")
    if use_tls:
        context = ssl.create_default_context()
        if not tls_verify:
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
        ftp = FTP_TLS(context=context)
    else:
        ftp = FTP()
    ftp.connect(host, port, timeout=30)
    ftp.login(user, password)
    if use_tls:
        ftp.prot_p()
    ok(f"Connected as {user}")
    return ftp


def cwd_or_create(ftp, remote_dir: str) -> None:
    """Ensure we're sitting in the remote upload root, creating it if needed."""
    if not remote_dir:
        return
    try:
        ftp.cwd(remote_dir)
        return
    except error_perm:
        pass
    # Build the path piece by piece from root.
    ftp.cwd("/")
    for piece in remote_dir.strip("/").split("/"):
        if not piece:
            continue
        try:
            ftp.cwd(piece)
        except error_perm:
            ftp.mkd(piece)
            ftp.cwd(piece)


def ensure_subdir(ftp, sub: str, created: set[str]) -> None:
    """Create each segment of `sub` (relative to ftp.pwd()) if missing."""
    if not sub or sub in created:
        return
    parts = sub.split("/")
    for i in range(len(parts)):
        partial = "/".join(parts[: i + 1])
        if partial in created:
            continue
        try:
            ftp.mkd(partial)
        except error_perm:
            pass  # most likely "already exists"
        created.add(partial)


def upload(ftp, remote_dir: str, files: list[tuple[Path, str]]) -> int:
    cwd_or_create(ftp, remote_dir)
    target = ftp.pwd()
    step(f"[3/3] Uploading {len(files)} file(s) → {target}")

    created: set[str] = set()
    total_bytes = 0
    width = len(str(len(files)))

    for i, (path, rel) in enumerate(files, 1):
        sub = "/".join(rel.split("/")[:-1])
        if sub:
            ensure_subdir(ftp, sub, created)

        size = path.stat().st_size
        total_bytes += size
        prefix = f"{C.DIM}[{i:>{width}}/{len(files)}]{C.RESET}"
        sys.stdout.write(f"  {prefix} {rel} {C.DIM}({format_size(size)}){C.RESET}\n")
        sys.stdout.flush()

        with path.open("rb") as fp:
            ftp.storbinary(f"STOR {rel}", fp)

    ok(f"Uploaded {len(files)} file(s) — {format_size(total_bytes)}")
    return total_bytes


def main() -> None:
    parser = argparse.ArgumentParser(description="Build and deploy via FTP/FTPS")
    parser.add_argument(
        "--skip-build",
        action="store_true",
        help="upload the existing dist/ without rebuilding",
    )
    args = parser.parse_args()

    env = {**load_env(ENV_FILE), **{k: v for k, v in os.environ.items() if k.startswith("FTP_")}}

    host = normalize_host(require(env, "FTP_HOST"))
    user = require(env, "FTP_USER")
    password = require(env, "FTP_PASSWORD")
    remote_dir = env.get("FTP_REMOTE_DIR", "").strip()
    port = int(env.get("FTP_PORT", "21"))
    use_tls = env.get("FTP_USE_TLS", "true").lower() in ("1", "true", "yes", "on")
    tls_verify = env.get("FTP_TLS_VERIFY", "true").lower() in ("1", "true", "yes", "on")

    if not args.skip_build:
        run_build()
    else:
        info("Skipping build (--skip-build)")
        if not DIST.exists():
            err("dist/ not found — drop --skip-build or run `pnpm build` first")
            sys.exit(1)

    files = collect_files(DIST)
    if not files:
        warn("No files to upload (dist/ is empty)")
        return

    skipped = sorted(EXCLUDE_FILENAMES & {p.name for p in DIST.iterdir() if p.is_file()})
    if skipped:
        info(f"Skipping (preserved on host): {', '.join(skipped)}")

    start = time.time()
    ftp = connect_ftp(host, port, user, password, use_tls, tls_verify)
    try:
        upload(ftp, remote_dir, files)
    finally:
        try:
            ftp.quit()
        except Exception:  # noqa: BLE001
            pass

    elapsed = time.time() - start
    print()
    ok(f"{C.BOLD}Deploy complete{C.RESET} in {elapsed:.1f}s")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        err("Aborted")
        sys.exit(130)
    except (error_perm, OSError, ssl.SSLError) as e:
        err(f"FTP error: {e}")
        sys.exit(1)
