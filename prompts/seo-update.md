# Prompt — Update SEO for a new project

Copy everything below the line into your AI assistant (Claude Code, Cursor, etc.)
when you start a new site from this template. Fill in the **Project brief** first;
the assistant uses it to make every SEO change for you and reports what still
needs a human (real OG image, social handles, verification tokens).

---

You are an SEO engineer working inside an **Astro + Tailwind static site** built
from the `heymaia/astro-template`. Your job is to configure all baseline SEO for
this specific project. Do not change the architecture — only fill in
project-specific values and add the missing content assets.

## Project brief (the human fills this in)

- **Brand / site name:** <e.g. Acme Studio>
- **Production domain:** <https://acme.com — no trailing slash>
- **Primary language / locale:** <e.g. en, es, en-US>
- **One-line description of the business:** <what it does, for whom>
- **Primary keywords / topics:** <3–6 phrases real users would search>
- **Twitter/X handle (optional):** <@acme>
- **Social share image (optional):** <path or "generate a placeholder">
- **Pages that should NOT be indexed (optional):** <e.g. /thank-you, /admin>

## How SEO is wired in this template (read before editing)

- **`astro.config.mjs` → `site`** — the production domain. It drives absolute
  canonical URLs, OG image URLs, `robots.txt`, and the sitemap. **This is the #1
  thing to change.** While it says `https://example.com`, everything points at
  the wrong domain.
- **`src/layouts/BaseLayout.astro`** — the single source of truth for the
  `<head>`: title, description, canonical, robots, Open Graph, Twitter Card,
  favicons, JSON-LD, and analytics. Every page should render through it. It
  accepts these props (all optional except `title`):
  `title`, `description`, `image`, `imageAlt`, `canonical`, `noindex`, `lang`,
  `type` (`website` | `article` | ...), `siteName`, `themeColor`, `twitterSite`,
  `twitterCreator`, `publishedTime`, `modifiedTime`, `author`.
- **`src/pages/robots.txt.ts`** — generates `/robots.txt` at build time; its
  `Sitemap:` line tracks `site` automatically. Add `Disallow:` rules here.
- **`@astrojs/sitemap`** (in `astro.config.mjs`) — emits `/sitemap-index.xml` at
  build. Nothing to do unless you need to exclude routes (edit the `filter`).
- **`public/`** — anything here is copied verbatim to the site root. This is
  where the OG image, `favicon.svg`/`.ico`, and any `apple-touch-icon.png` live.

## Tasks — do these in order

1. **Set the domain.** In `astro.config.mjs`, replace `site: 'https://example.com'`
   with the production domain from the brief.

2. **Set brand-wide defaults.** Decide how each page will pass `siteName`,
   `lang`, `themeColor`, and (if given) `twitterSite`. If most pages repeat the
   same values, either create a thin wrapper layout that presets them or pass
   them from a shared constants file — don't hardcode the same string on every
   page. Keep `BaseLayout` itself generic.

3. **Write per-page `title` + `description` for every page.** These are the two
   highest-impact on-page fields. Rules:
   - **Title:** ~50–60 characters. Lead with the page's specific value, end with
     the brand (e.g. `Custom Leather Bags — Acme Studio`). Unique per page.
   - **Description:** ~140–155 characters, active voice, includes a primary
     keyword naturally, reads like ad copy (it often becomes the search snippet).
     Unique per page — never reuse one description across pages.
   - Weave in the brief's keywords where they fit naturally. Never keyword-stuff.

4. **Ensure one `<h1>` per page** that matches the page intent and roughly the
   title. Use a logical heading order (`h1` → `h2` → `h3`, no skips). Use
   semantic landmarks (`<main>`, `<nav>`, `<header>`, `<footer>`, `<article>`).

5. **Create the social share image.** Add `public/og-default.png`
   (1200×630, < ~1 MB). If you can't produce a real one, generate a simple
   branded placeholder and clearly flag that a designer should replace it. Pass
   descriptive `imageAlt` text. Pages can override with their own `image`.

6. **Handle noindex pages.** For any page in the brief's do-not-index list, pass
   `noindex` to `BaseLayout` AND add a `Disallow:` line in `src/pages/robots.txt.ts`.

7. **Add structured data where it fits.** Blog posts / articles: pass
   `type="article"` plus `publishedTime`, `modifiedTime`, `author` (BaseLayout
   emits Article JSON-LD + `article:*` OG tags). For a local business, product,
   FAQ, or breadcrumbs, add the matching schema.org JSON-LD via the `head` slot:
   `<script slot="head" type="application/ld+json" set:html={JSON.stringify(data)} />`.
   Only mark up content that actually appears on the page.

8. **Image SEO.** Every meaningful `<img>` needs descriptive `alt`. Prefer
   Astro's `<Image />` / `<Picture />` for responsive, lazy-loaded, modern
   formats. Give width/height to avoid layout shift (CLS).

9. **Internationalization (only if multi-language).** Set `lang` per page and
   add `hreflang` alternate links via the `head` slot for each locale + an
   `x-default`.

10. **Verify.** Run `pnpm build`, then confirm in `dist/`:
    - `robots.txt` shows the real domain in the `Sitemap:` line.
    - `sitemap-0.xml` lists the real pages under the real domain.
    - Each page's `<head>` has a unique `<title>`, unique `description`,
      a `canonical` on the real domain, absolute `og:image`, and valid JSON-LD.
    - No page unintentionally carries `noindex`.

## Report back

When done, output a short checklist of: what you changed, what you generated a
placeholder for (esp. the OG image), and what still needs a human — e.g. real
share image, social handles, Google/Bing Search Console verification, and
submitting the sitemap to Search Console. These live outside the codebase.

## Out of scope (do NOT touch)

- The contact form pipeline (`public/contact.php`, Turnstile keys, deploy secrets).
- `EXCLUDE_FILENAMES` in `scripts/deploy.py`.
- Anything requiring server-side rendering — this template ships a static build.
