// @ts-check

import sitemap from '@astrojs/sitemap';
import tailwindcss from '@tailwindcss/vite';
import { defineConfig } from 'astro/config';

// https://astro.build/config
export default defineConfig({
	// OPERATOR: replace with the production domain BEFORE deploying.
	// BaseLayout.astro uses this to build absolute canonical and OG image URLs,
	// and @astrojs/sitemap uses it to emit absolute URLs in sitemap-index.xml.
	// While this stays 'https://example.com', the generated sitemap and canonical
	// tags will point at example.com — so updating this is the single most
	// important SEO step for a new project. Example: 'https://yourdomain.com' (no trailing slash).
	site: 'https://example.com',

	// Keep canonical URLs and sitemap entries consistent. 'ignore' (Astro's
	// default) lets the host serve both /path and /path/. Set 'always' or 'never'
	// if your host is strict about trailing slashes.
	// trailingSlash: 'ignore',

	integrations: [
		// Generates /sitemap-index.xml + /sitemap-0.xml at build time from every
		// static route, using the `site` domain above. public/robots.txt points
		// crawlers to it. @astrojs/sitemap requires `site` to be set.
		sitemap({
			// Exclude non-content routes from the sitemap. Add more filters as needed.
			filter: (page) => !page.includes('/contact.php'),
		}),
	],

	vite: {
		plugins: [tailwindcss()],
	},
});
