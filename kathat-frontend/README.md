# Kathat Estate — Frontend (no build step)

Plain HTML, CSS, and vanilla JavaScript. Nothing to compile, bundle, or
`npm install`. Deploy this folder exactly as it is.

## Before you deploy: one variable

Open **`assets/config.js`** and set one line:

```js
window.KATHAT_API_BASE = "https://your-backend-url.com";
```

That's the only configuration in the entire frontend. Every page (home, all
6 property pages, the dashboard) reads the backend URL from this single
file — nothing else to find and edit.

## Deploy it

Any static host works — there's no server-side logic here at all:

- **Drag-and-drop**: Netlify Drop, Cloudflare Pages, GitHub Pages, Vercel
  (static mode) — just upload this folder.
- **Any web server**: Nginx, Apache, S3 + CloudFront, a VPS — point the
  document root at this folder.
- **Open it locally**: most pages work by double-clicking `index.html`,
  though `fetch`/tracking calls need a real HTTP origin (not `file://`) to
  reach the backend reliably — use `python3 -m http.server` or similar for
  local testing.

No environment variables, no build command, no `package.json`. If your
hosting platform asks for a "build command," leave it blank.

## What's in here

```
index.html                    Homepage — hero, portfolio, developers, about
properties/*.html             6 property detail pages (pre-rendered, real developer data)
dashboard.html                Admin panel (requires login — see below)
manifest.json, sw.js, icons   PWA support (installable, works offline for the shell)
assets/
  style.css                    All styling — plain CSS, no framework runtime
  config.js                    ← the one variable
  pixel.js                     Tracking pixel (posts to {KATHAT_API_BASE}/api/v1/track)
  main.js                      Language toggle, city filter, enquiry form, AI chat widget
  dashboard.js                 Dashboard login + live data (admin only)
```

## No signup required for visitors

The public site — browsing properties, the enquiry form, the AI chat
widget — requires no account, no signup, nothing. It's fully open. The
**only** page behind a login is `dashboard.html`, which is the admin panel
and is not linked from anywhere in the public navigation.

## Works even if the backend/AI isn't reachable

- The enquiry form always shows its success message immediately — the
  tracking call happens in the background and never blocks the UI, even if
  the backend is down or misconfigured.
- The AI chat widget shows a plain "having trouble responding" message
  instead of breaking if the backend or the AI provider is unavailable.
- No technical details, logs, or scores are ever shown to a visitor —
  that's exclusively in `dashboard.html`, behind login.

## Bilingual (EN/HI) without a build step

Every piece of text ships in the HTML twice — once per language, tagged
`data-lang="en"` / `data-lang="hi"` — and `style.css` shows only the active
one via a class on `<html>`. Switching languages is instant (pure CSS, no
re-fetch, no framework re-render) and the choice persists via
`localStorage`.

## Regenerating the property pages

If you ever need to change property data (price, amenities, add a new
city), don't hand-edit the 6 HTML files — edit `_generate/data.py` and
re-run `python3 _generate/gen_properties.py` (also `gen_index.py` for the
homepage). That folder is the source of truth; the `.html` files are its
output. `_generate/` itself needs Python to *regenerate* pages, but it is
not required to *deploy* the site — everything it produces is already
sitting in this folder, ready to ship.
