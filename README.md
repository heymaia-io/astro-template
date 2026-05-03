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

`pnpm deploy` runs `scripts/deploy.py` — Python 3, **stdlib only** (`ftplib`, `ssl`). Reads `.env` at the project root, builds via `pnpm build`, opens an FTP/FTPS connection, and uploads everything in `dist/` recursively. **Never overwrites `contact.config.php`** on the host so the production secret survives redeploys.

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

## Local-dev limitation

`astro dev` does not execute PHP — submitting the form locally returns 404 / serves `.php` as text. To test the endpoint locally:

```sh
pnpm build
php -S localhost:8080 -t dist
```

For Turnstile to work on `localhost`, add it as a hostname in the Cloudflare Turnstile dashboard.
