<?php
/**
 * Template for public/contact.config.php.
 *
 * Copy this file to "contact.config.php" (gitignored) and fill in the
 * Turnstile secret + the destination email addresses for the project.
 */

const MAIL_FROM      = 'no-reply@example.com';
const MAIL_FROM_NAME = 'Website';
// Change this to the address you want to receive the test emails at.
const MAIL_TO        = 'you@example.com';

// Cloudflare Turnstile (https://dash.cloudflare.com → Turnstile).
// Server-only — never exposed to the browser.
//
// The default below is Cloudflare's public "always passes" test secret — pairs
// with the test site key in .env.example so the Docker workflow needs zero
// Cloudflare configuration. REPLACE with your real secret before deploying.
const TURNSTILE_SECRET = '1x0000000000000000000000000000000AA';
