// @ts-check

import tailwindcss from '@tailwindcss/vite';
import { defineConfig } from 'astro/config';

// https://astro.build/config
export default defineConfig({
	// OPERATOR: replace with the production domain before deploying.
	// BaseLayout.astro uses this to build absolute canonical and OG image URLs.
	// Example: 'https://yourdomain.com'  (no trailing slash)
	site: 'https://example.com',

	vite: {
		plugins: [tailwindcss()],
	},
});
