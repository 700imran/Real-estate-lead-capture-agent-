# Kathat Estate — Frontend (no build step)

Plain HTML, CSS, and vanilla JavaScript. Nothing to compile, bundle, or
`npm install`. Deploy this folder exactly as it is.

## What's new in this pass

- **Glassmorphism** throughout: nav, property cards, unit cards, the
  enquiry form, the AI chat widget, and the dashboard are all frosted-glass
  panels (`backdrop-filter: blur()`) over a soft gold/bronze gradient
  "atmosphere" layer fixed behind the whole page. Pure CSS, no runtime
  library — see `.glass` in `assets/style.css`. There's a graceful
  fallback (`@supports not (backdrop-filter...)`) for older browsers.
- **A proper logo**: a geometric "K" monogram with a diamond finial inside
  a thin crest ring — `assets/logo/mark.svg`. "Royal" through restraint
  (a seal-like ring, a jewel accent) rather than a literal crown clip-art,
  "modern" through clean geometric strokes. It's on every page (nav +
  footer) and is also the favicon/link icon set (`favicon.svg`,
  `favicon-16/32.png`, `apple-touch-icon.png`, the PWA icons).
- **Mouse + touch interaction polish** (`assets/interactions.js`):
  property cards tilt subtly toward the cursor on mouse (skipped entirely
  on touch via `matchMedia('(hover: hover) and (pointer: fine)')`, so it
  never fights a finger); every button gets a tap/click ripple; all
  interactive elements have real `:active` states (not just `:hover`, which
  doesn't help touch users) and meet a 44px minimum touch target.

## On "images of properties" — what's actually here, and why

Every property card and hero uses a **distinct color-graded gradient**
("mood") standing in for a photo — sea-teal-to-gold for the Mumbai
sea-facing listing, tropical coral for the Goa villa, and so on — with the
frosted glass panel floating on top. This is a real, common glassmorphism
pattern (macOS/iOS-style gradient blooms behind glass), not a placeholder
I'd normally settle for.

The reason it's gradients and not stock photos: a stock or web-sourced
photo attributed to "Godrej Bandra West" or "DLF The Camellias" would very
likely **not actually be a photo of that building** — and presenting a
random photo as if it depicts a specific real property those specific real
developers own is its own kind of misrepresentation, on top of the
copyright question of reusing someone else's photography long-term in a
site you're deploying. Once you have real, licensed photography for these
(from the developer, a licensed stock library, or your own shoot), swapping
it in is a one-line change per property — see below.

### Swapping in real photos

In `assets/style.css`, each property has a `.mood-<slug>` rule, e.g.:

```css
.mood-bandra-west{background:linear-gradient(135deg,#0d3b4a 0%,#1c6e73 45%,#C9A26A 100%);}
```

Replace it with an image:

```css
.mood-bandra-west{background:url('images/bandra-west.jpg') center/cover;}
```

Do this in one place per property; it updates both the homepage card and
that property's detail-page hero automatically, since both reference the
same class.

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
favicon.svg, favicon-*.png,
apple-touch-icon.png          Browser tab / home-screen icon set
assets/
  style.css                    All styling — plain CSS, glassmorphism, no framework runtime
  config.js                    ← the one variable
  pixel.js                     Tracking pixel (posts to {KATHAT_API_BASE}/api/v1/track)
  main.js                      Language toggle, city filter, enquiry form, AI chat widget
  interactions.js               Card tilt (mouse), ripple (mouse+touch), touch-safe hover
  dashboard.js                  Dashboard login + live data (admin only)
  logo/mark.svg                 The logo mark (also the favicon source)
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
homepage, `gen_dashboard.py` for the dashboard). That folder is the source
of truth; the `.html` files are its output. `_generate/` needs Python to
*regenerate* pages, but it is not required to *deploy* the site —
everything it produces is already sitting in this folder, ready to ship.

