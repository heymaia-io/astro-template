# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

Package manager is **pnpm** (Node ≥ 22.12). Deploy uses **Python 3 stdlib only** — no extra Python deps.

| Command                | Action                                              |
| :--------------------- | :-------------------------------------------------- |
| `pnpm install`         | Install dependencies                                |
| `pnpm dev`             | Astro dev server at `localhost:4321`                |
| `pnpm build`           | Build static output to `./dist/`                    |
| `pnpm preview`         | Serve the built site locally                        |
| `pnpm deploy`          | `pnpm build` + FTP/FTPS upload of `dist/`           |
| `pnpm deploy:no-build` | Upload existing `dist/` without rebuilding          |

There is no test/lint setup.

## Architecture — hybrid static Astro + PHP endpoint

The site is a static Astro build, but the contact form is served by a sibling **PHP file in `public/`**, not an Astro endpoint or third-party email service. Anything in `public/` is copied verbatim into `dist/`, so `public/contact.php` lands next to the static HTML on the host and runs under the host's PHP (Hostinger / cPanel — uses local `mail()` MTA which DKIM-signs outbound mail, so no SMTP creds are configured).

Request lifecycle:

1. `src/components/Contact.astro` renders the form + injects Cloudflare Turnstile.
2. `src/scripts/contact.ts` POSTs `FormData` to `/contact.php`.
3. `public/contact.php` does honeypot drop → Turnstile siteverify → field validation → header-injection sanitization → `mail()`.
4. `public/contact.config.php` (gitignored) holds `MAIL_FROM`, `MAIL_FROM_NAME`, `MAIL_TO`, `TURNSTILE_SECRET`. Template is `public/contact.config.example.php`.

### Turnstile keys are split across two systems on purpose
- **Site key** → `.env` as `PUBLIC_TURNSTILE_SITE_KEY`. Astro bakes it into the build at `pnpm build` time. Public.
- **Secret key** → lives only in `public/contact.config.php` *on the host*. Server-side only, **never in `.env`**, never in the bundle.

### Local dev does not run PHP
`astro dev` serves `.php` as text / 404. To exercise the endpoint locally:

```sh
pnpm build && php -S localhost:8080 -t dist
```

Add `localhost` as a Turnstile hostname in the Cloudflare dashboard or the widget will refuse to render.

## Deploy script — `scripts/deploy.py`

Stdlib-only Python (`ftplib`, `ssl`). Reads `.env`, runs `pnpm build` (unless `--skip-build`), connects FTPS by default, and recursively uploads `dist/`. Configured via `.env`: `FTP_HOST`, `FTP_USER`, `FTP_PASSWORD`, `FTP_REMOTE_DIR`, `FTP_PORT`, `FTP_USE_TLS`, `FTP_TLS_VERIFY`. `FTP_REMOTE_DIR` is intentionally empty for Hostinger (FTP accounts are chrooted into the site root).

**Critical invariant:** `EXCLUDE_FILENAMES` in `scripts/deploy.py` (currently `{"contact.config.php"}`) lists files that exist in `dist/` but must **never overwrite the copy on the host** — those carry production-only secrets. The first deploy uploads the example/template, then the operator edits `contact.config.php` on the server with real values, and every subsequent `pnpm deploy` leaves it alone. Any new server-only secret file follows this same pattern: add the basename to `EXCLUDE_FILENAMES`.

## Editing the contact form

Strings are at the top of `src/components/Contact.astro` (`labels` / `placeholders` objects — currently Spanish; all error strings in `contact.php` are also Spanish). Adding/removing a field requires changes in **three places**: the form markup in `Contact.astro`, validation + body assembly in `public/contact.php`, and (if user-facing label text) the `labels` object. The PHP side already strips `\r\n\0` from every field except `message` to prevent header injection — preserve that when adding string fields.

## Styling

Tailwind v4 via `@tailwindcss/vite` (configured in `astro.config.mjs`); global stylesheet at `src/styles/global.css`. No `tailwind.config.*` file — v4 is CSS-first.
