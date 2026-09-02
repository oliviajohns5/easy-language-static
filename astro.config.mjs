import { defineConfig } from 'astro/config';
import react from '@astrojs/react';

export default defineConfig({
  site: 'https://easy-language.com.ua',
  integrations: [react()],
  output: 'static',
  trailingSlash: 'always'
});
