/**
 * robots.txt — generated at build time so the Sitemap URL always tracks the
 * `site` domain in astro.config.mjs (no hardcoded placeholder to forget).
 *
 * Output is served at /robots.txt. Edit the `lines` below to add crawl rules.
 * Docs: https://developers.google.com/search/docs/crawling-indexing/robots/intro
 */
import type { APIRoute } from 'astro';

export const GET: APIRoute = ({ site }) => {
	// `site` is astro.config.mjs → `site`. It should always be set; fall back to
	// a relative sitemap path if it isn't so the file is never broken.
	const sitemapURL = site ? new URL('sitemap-index.xml', site).href : '/sitemap-index.xml';

	const lines = [
		'User-agent: *',
		'Allow: /',
		// Block the server-side contact endpoint from being crawled/indexed.
		'Disallow: /contact.php',
		'',
		`Sitemap: ${sitemapURL}`,
		'',
	];

	return new Response(lines.join('\n'), {
		headers: { 'Content-Type': 'text/plain; charset=utf-8' },
	});
};
