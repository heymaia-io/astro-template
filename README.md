# Astro Boilerplate — Tailwind + Contact form + FTP deploy

Personal starting point for static Astro sites that need:

- A working contact form backed by a small PHP endpoint (no third-party email service).
- Cloudflare Turnstile in place of Google reCAPTCHA.
- A Python script that builds and uploads `dist/` over FTP/FTPS to the host.

## Commands

| Command                | Action                                              |
| :--------------------- | :-------------------------------------------------- |
| `pnpm install`         | Install dependencies                                |
| `pnpm dev`             | Start local dev server at `localhost:4321`          |
| `pnpm build`           | Build the production site to `./dist/`              |
| `pnpm preview`         | Preview the built site locally                      |
| `pnpm deploy`          | Build and upload `dist/` to the configured FTP host |
| `pnpm deploy:no-build` | Upload the existing `dist/` without rebuilding      |

## Layout

```
public/
  contact.php                  ← POST endpoint (validate, verify Turnstile, mail())
  contact.config.php           ← gitignored — destination addresses + Turnstile secret
  contact.config.example.php   ← committed template
src/
  components/
    Contact.astro              ← generic form: name / email / phone / subject / message
  scripts/
    contact.ts                 ← submit handler (fetch, loading, success/error, reset)
scripts/
  deploy.py                    ← Python 3 stdlib FTP/FTPS uploader
Dockerfile                     ← local-only PHP image (msmtp → mailpit)
docker-compose.yml             ← local-only stack: PHP + mailpit catcher
.env.example                   ← Turnstile site key + FTP creds
```

## Contact form

`Contact.astro` POSTs `FormData` to `/contact.php`, which:

1. Rejects non-POST requests.
2. Drops bots that fill the `_hp` honeypot.
3. Verifies the Turnstile token at `https://challenges.cloudflare.com/turnstile/v0/siteverify`.
4. Validates required fields (`name`, `email`, `message`) and the email format.
5. Sanitizes header-injection chars (`\r`, `\n`, `\0`).
6. Calls PHP's built-in `mail()` — on Hostinger / cPanel hosts this hands the message to the local MTA, which DKIM-signs outbound mail for any domain whose mailboxes live in the same hosting account. No SMTP credentials needed.

To embed: `import Contact from '../components/Contact.astro';` and drop `<Contact />` in a page.

### Setup

1. **Cloudflare Turnstile** → dashboard → add site → copy:
   - **Site key** → `.env` as `PUBLIC_TURNSTILE_SITE_KEY=`. Astro bakes it into the build.
   - **Secret key** → `public/contact.config.php` as `TURNSTILE_SECRET`. Gitignored.
2. **Mail addresses** → also in `public/contact.config.php`: edit `MAIL_FROM`, `MAIL_FROM_NAME`, `MAIL_TO`.
3. **First deploy** → upload everything once, then on the host edit `contact.config.php` to put the real values in. Subsequent `pnpm deploy` runs leave it alone.

### Customizing the form

Open `Contact.astro` and edit the `labels` / `placeholders` objects at the top. To add a field, also update `contact.php` (validation + body) and the form markup. To remove one, drop it from both ends.

## FTP deploy

`pnpm run deploy` runs `scripts/deploy.py` — Python 3, **stdlib only** (`ftplib`, `ssl`). Reads `.env` at the project root, builds via `pnpm build`, opens an FTP/FTPS connection, and uploads everything in `dist/` recursively. **Never overwrites `contact.config.php`** on the host so the production secret survives redeploys.

`.env` keys:

```
FTP_HOST            bare hostname or IP (no "ftp://" prefix)
FTP_USER
FTP_PASSWORD
FTP_REMOTE_DIR      empty when the FTP account is chrooted to the site root (Hostinger default)
FTP_PORT            default 21
FTP_USE_TLS         default true (explicit FTPS)
FTP_TLS_VERIFY      default true; set false to skip cert hostname check (e.g. when connecting by IP)
```

Output is colored, per-file, with size and total summary.

## Testing the contact form locally

`astro dev` does not execute PHP — submitting the form against the dev server returns 404 / serves `.php` as text. The repo ships a Docker setup that runs PHP + a fake SMTP catcher so you can exercise the full submit → validate → Turnstile → `mail()` flow without sending real email or owning a Cloudflare account.

**Requires:** Docker Desktop (or any Docker engine with the `compose` plugin).

### One-time setup

```sh
cp .env.example .env
cp public/contact.config.example.php public/contact.config.php
```

Open `public/contact.config.php` and change `MAIL_TO` to the address you want to see the test emails arrive at — though for local testing it doesn't really matter, since mailpit catches everything regardless of destination. **Nothing else needs to change.** Both example files ship with Cloudflare's public "always passes" Turnstile test keys baked in, so the widget renders and the server-side verification succeeds on any hostname (including `localhost`) with no Cloudflare configuration.

### Run

```sh
pnpm install
pnpm build
docker compose up
```

Then:

- **Form** → http://localhost:8080
- **Mailpit inbox** → http://localhost:8025

Submit the form. Mailpit will show the message instantly with full headers, the rendered body, and source view. Press `Ctrl+C` to stop, `docker compose down` to clean up.

### How it works

`docker-compose.yml` boots two containers:

1. **`php`** — `php:8.2-apache` with `msmtp` installed. `msmtp` is a tiny sendmail-compatible binary; PHP's `sendmail_path` is pointed at it, and msmtp is configured to forward to the mailpit container instead of attempting real SMTP delivery. The `dist/` folder is bind-mounted as the docroot, so any `pnpm build` rerun is reflected immediately.
2. **`mailpit`** — captures every message msmtp forwards and exposes a web UI on port 8025. Messages are in-memory; restarting the container clears them.

### Before deploying to production

Both example files default to Cloudflare's test keys for zero-friction local testing. Before your first real deploy:

1. Get a free pair of Turnstile keys from [Cloudflare Turnstile](https://www.cloudflare.com/application-services/products/turnstile/) — sign in, add your site, and Cloudflare hands you a **site key** + **secret key**.
2. Replace `PUBLIC_TURNSTILE_SITE_KEY` in `.env` with your real Turnstile **site** key.
3. Replace `TURNSTILE_SECRET` in `public/contact.config.php` with your real Turnstile **secret** key.
4. Set the real `MAIL_FROM`, `MAIL_FROM_NAME`, and `MAIL_TO` in `public/contact.config.php`.

### Plain-PHP fallback (no Docker)

If you only need to confirm the endpoint is reachable and don't care about catching the actual mail, you can skip Docker entirely:

```sh
pnpm build
php -S localhost:8080 -t dist
```

`mail()` will silently fail unless your machine has a local MTA configured, but Turnstile verification and form validation still run. Add `localhost` as a hostname in the Cloudflare Turnstile dashboard if you've swapped the test keys for real ones.
