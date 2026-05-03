<?php
/**
 * Template for public/contact.config.php.
 *
 * Copy this file to "contact.config.php" (gitignored) and fill in the
 * Turnstile secret + the destination email addresses for the project.
 */

const MAIL_FROM      = 'no-reply@example.com';
const MAIL_FROM_NAME = 'Website';
const MAIL_TO        = 'you@example.com';

// Cloudflare Turnstile (https://dash.cloudflare.com → Turnstile).
// Server-only — never exposed to the browser.
const TURNSTILE_SECRET = 'replace-with-turnstile-secret-key';
