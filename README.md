# Easy Language static site

Static Astro migration of `easy-language.com.ua` from legacy PHP pages.

## Migration goals

- No PHP runtime and no database.
- Clean trailing-slash URLs instead of `.php` pages.
- Local WebP images with descriptive filenames.
- 301 redirects from legacy `.php` and `/img/...` URLs.
- Preserved page titles and generated meta descriptions.
- GitHub → Vercel Git import; pushes to `main` auto-deploy.

## Commands

```bash
npm install
npm run import:site
npm run build
npm run verify
```

## Canonical URLs

The migrated site uses paths such as `/about/`, `/languages/`, `/english-courses/`, `/order/` instead of `/about.php`, `/languages.php`, etc.

The live domain is not switched here; DNS/domain migration is a separate final step after preview verification.
