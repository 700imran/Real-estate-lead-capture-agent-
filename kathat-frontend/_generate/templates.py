#!/usr/bin/env python3
"""Generates the final static HTML files. Run: python3 generate.py"""
import os
from data import PROPERTIES

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def bi(en, hi):
    """Bilingual span pair: both ship in the HTML, CSS shows only one."""
    return f'<span data-lang="en">{en}</span><span data-lang="hi">{hi}</span>'


HEAD = """<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,wght@0,400;0,500;0,600;1,500&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<link rel="manifest" href="{root}manifest.json">
<link rel="icon" href="{root}favicon.svg" type="image/svg+xml">
<link rel="icon" href="{root}favicon-32.png" sizes="32x32" type="image/png">
<link rel="icon" href="{root}favicon-16.png" sizes="16x16" type="image/png">
<link rel="apple-touch-icon" href="{root}apple-touch-icon.png">
<meta name="theme-color" content="#17140F">
<link rel="stylesheet" href="{root}assets/style.css">
"""

NAV = """<a class="skip-link" href="#main">Skip to content</a>
<header class="nav">
  <div class="nav__inner">
    <a href="{root}index.html" class="nav__brand">
      <img src="{root}assets/logo/mark.svg" alt="" width="34" height="34">
      <span>Kathat Estate</span>
    </a>
    <ul class="nav__links">
      <li><a href="{root}index.html#portfolio">{portfolio}</a></li>
      <li><a href="{root}index.html#developers">{developers}</a></li>
      <li><a href="{root}index.html#about">{about}</a></li>
      <li><a href="{root}index.html#enquiry">{enquire}</a></li>
    </ul>
    <div class="nav__right">
      <div class="lang-toggle">
        <button data-lang-btn="en">EN</button>
        <button data-lang-btn="hi">\u0939\u093f</button>
      </div>
      <a href="{root}index.html#enquiry" class="btn btn--gold" style="padding:.55em 1.2em;font-size:.8rem;">
        <span data-lang="en">Book a call</span><span data-lang="hi">\u0915\u0949\u0932 \u092c\u0941\u0915 \u0915\u0930\u0947\u0902</span>
      </a>
    </div>
  </div>
</header>
"""

FOOTER = """<footer class="footer">
  <p class="footer__brand"><img src="{root}assets/logo/mark.svg" alt=""><span>Kathat Estate</span></p>
  <p>{tagline}</p>
  <p class="footer__fine">{disclaimer}</p>
</footer>
"""

TAGLINE = bi(
    "Kathat Estate — a curated marketplace of considered addresses across India.",
    "\u0915\u0920\u093e\u0924 \u090f\u0938\u094d\u091f\u0947\u091f \u2014 \u092d\u093e\u0930\u0924 \u092d\u0930 \u0915\u0947 \u0938\u0941\u0935\u093f\u091a\u093e\u0930\u093f\u0924 \u092a\u0924\u094b\u0902 \u0915\u093e \u090f\u0915 \u0915\u094d\u092f\u0942\u0930\u0947\u091f\u0947\u0921 \u092e\u093e\u0930\u094d\u0915\u0947\u091f\u092a\u094d\u0932\u0947\u0938\u0964",
)
DISCLAIMER = bi(
    "Kathat Estate is a demonstration portal built to showcase this sales platform. Featured developments are real projects by their respective developers, compiled from public listings for illustration — always confirm current availability and pricing directly with the developer. Kathat Estate is not the developer or builder of record for any property shown.",
    "\u0915\u0920\u093e\u0924 \u090f\u0938\u094d\u091f\u0947\u091f \u0907\u0938 \u0938\u0947\u0932\u094d\u0938 \u092a\u094d\u0932\u0947\u091f\u092b\u0949\u0930\u094d\u092e \u0915\u094b \u092a\u094d\u0930\u0926\u0930\u094d\u0936\u093f\u0924 \u0915\u0930\u0928\u0947 \u0915\u0947 \u0932\u093f\u090f \u092c\u0928\u093e\u092f\u093e \u0917\u092f\u093e \u090f\u0915 \u0921\u0947\u092e\u094b \u092a\u094b\u0930\u094d\u091f\u0932 \u0939\u0948\u0964 \u092a\u094d\u0930\u0926\u0930\u094d\u0936\u093f\u0924 \u092a\u094d\u0930\u094b\u091c\u0947\u0915\u094d\u091f\u094d\u0938 \u0938\u0902\u092c\u0902\u0927\u093f\u0924 \u0921\u0947\u0935\u0932\u092a\u0930\u094d\u0938 \u0915\u0940 \u0935\u093e\u0938\u094d\u0924\u0935\u093f\u0915 \u092a\u0930\u093f\u092f\u094b\u091c\u0928\u093e\u090f\u0902 \u0939\u0948\u0902, \u091c\u094b \u0938\u093e\u0930\u094d\u0935\u091c\u0928\u093f\u0915 \u0932\u093f\u0938\u094d\u091f\u093f\u0902\u0917 \u0938\u0947 \u0938\u0902\u0915\u0932\u093f\u0924 \u0915\u0940 \u0917\u0908 \u0939\u0948\u0902 \u2014 \u0915\u0943\u092a\u092f\u093e \u092e\u094c\u091c\u0942\u0926\u093e \u0909\u092a\u0932\u092c\u094d\u0927\u0924\u093e \u0914\u0930 \u0915\u0940\u092e\u0924 \u0915\u0940 \u092a\u0941\u0937\u094d\u091f\u093f \u0938\u0940\u0927\u0947 \u0921\u0947\u0935\u0932\u092a\u0930 \u0938\u0947 \u0915\u0930\u0947\u0902\u0964 \u0915\u0920\u093e\u0924 \u090f\u0938\u094d\u091f\u0947\u091f \u0915\u093f\u0938\u0940 \u092d\u0940 \u0926\u093f\u0916\u093e\u0908 \u0917\u0908 \u092a\u094d\u0930\u0949\u092a\u0930\u094d\u091f\u0940 \u0915\u093e \u0921\u0947\u0935\u0932\u092a\u0930 \u092f\u093e \u092c\u093f\u0932\u094d\u0921\u0930 \u0928\u0939\u0940\u0902 \u0939\u0948\u0964",
)

CHAT_WIDGET = """<button class="chat-launcher" aria-label="Ask Kathat">\U0001F4AC</button>
<div class="chat-panel" hidden{prop_attr}>
  <div class="chat-panel__head">{title}</div>
  <div class="chat-panel__body"></div>
  <form class="chat-panel__form">
    <input type="text" placeholder="{placeholder}" required>
    <button type="submit">{send}</button>
  </form>
</div>
"""

SCRIPTS = """<script src="{root}assets/config.js"></script>
<script src="{root}assets/pixel.js" defer></script>
<script src="{root}assets/main.js" defer></script>
<script src="{root}assets/interactions.js" defer></script>
"""


def page_shell(title, description, root, body, extra_head=""):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
{HEAD.format(root=root)}
<title>{title}</title>
<meta name="description" content="{description}">
{extra_head}
</head>
<body>
{body}
{SCRIPTS.format(root=root)}
</body>
</html>
"""


def unit_cards(units):
    out = []
    for u in units:
        out.append(f"""    <div class="unit-card">
      <h3>{bi(u['type'], u['typeHi'])}</h3>
      <p class="unit-card__size">{u['size']} <span data-lang="en">sq.ft.</span><span data-lang="hi">\u0935\u0930\u094d\u0917 \u092b\u0941\u091f</span></p>
      <p class="unit-card__price">
        <span data-lang="en">\u20b9{u['priceCr']} Cr onwards</span>
        <span data-lang="hi">\u20b9{u['priceCr']} \u0915\u0930\u094b\u0921\u093c \u0938\u0947 \u0936\u0941\u0930\u0942</span>
      </p>
    </div>""")
    return "\n".join(out)


def feature_items(en_list, hi_list):
    out = []
    for en, hi in zip(en_list, hi_list):
        out.append(f'      <li><span class="dot"></span><span>{bi(en, hi)}</span></li>')
    return "\n".join(out)


def amenity_items(en_list, hi_list):
    out = []
    for en, hi in zip(en_list, hi_list):
        out.append(f'    <div><span class="dot"></span>{bi(en, hi)}</div>')
    return "\n".join(out)


def hero_art_svg(kind):
    if kind == "villa":
        return """<svg class="prop-hero__art" viewBox="0 0 200 160" stroke="#C9A26A" stroke-width="1" fill="none">
      <path d="M20 80 L100 30 L180 80" />
      <rect x="35" y="80" width="130" height="60" />
      <line x1="80" y1="140" x2="80" y2="100" />
      <line x1="120" y1="140" x2="120" y2="100" />
      <line x1="35" y1="110" x2="165" y2="110" />
    </svg>"""
    return """<svg class="prop-hero__art" viewBox="0 0 200 260" stroke="#C9A26A" stroke-width="1" fill="none">
      <rect x="50" y="20" width="100" height="220" />
      <line x1="50" y1="60" x2="150" y2="60" /><line x1="50" y1="100" x2="150" y2="100" />
      <line x1="50" y1="140" x2="150" y2="140" /><line x1="50" y1="180" x2="150" y2="180" />
      <line x1="50" y1="220" x2="150" y2="220" />
      <line x1="80" y1="20" x2="80" y2="240" /><line x1="120" y1="20" x2="120" y2="240" />
    </svg>"""


def card_art_svg(kind):
    if kind == "villa":
        return """<svg class="card-icon" viewBox="0 0 100 70" width="56" height="40" stroke="#F6F2E9" stroke-width="1.1" fill="none" opacity="0.85">
        <path d="M8 40 L50 14 L92 40" /><rect x="16" y="40" width="68" height="26" />
        <line x1="40" y1="66" x2="40" y2="48" /><line x1="60" y1="66" x2="60" y2="48" /></svg>"""
    return """<svg class="card-icon" viewBox="0 0 100 70" width="56" height="40" stroke="#F6F2E9" stroke-width="1.1" fill="none" opacity="0.85">
        <rect x="30" y="6" width="40" height="60" />
        <line x1="30" y1="22" x2="70" y2="22" /><line x1="30" y1="38" x2="70" y2="38" /><line x1="30" y1="54" x2="70" y2="54" /></svg>"""


NAV_LABELS = dict(
    portfolio=bi("Portfolio", "\u092a\u094b\u0930\u094d\u091f\u092b\u094b\u0932\u093f\u092f\u094b"),
    developers=bi("Developers", "\u0921\u0947\u0935\u0932\u092a\u0930\u094d\u0938"),
    about=bi("About", "\u0939\u092e\u093e\u0930\u0947 \u092c\u093e\u0930\u0947 \u092e\u0947\u0902"),
    enquire=bi("Enquire", "\u092a\u0942\u091b\u0924\u093e\u091b"),
)


def enquiry_section(property_slug=None, units=None, title_suffix=""):
    unit_options = ""
    if units:
        opts = []
        for u in units:
            opts.append(f'<option value="{u["type"]}">{u["type"]}</option>')
        unit_options = f"""<label>
              <span data-lang="en">Interested in</span><span data-lang="hi">\u0915\u093f\u0938\u092e\u0947\u0902 \u0930\u0941\u091a\u093f \u0939\u0948</span>
              <select name="unit">{''.join(opts)}</select>
            </label>"""
    prop_attr = f' data-property="{property_slug}"' if property_slug else ""
    return f"""<section id="enquiry" class="enquiry">
  <div class="enquiry__box reveal">
    <p class="eyebrow">{bi('Enquire', '\u092a\u0942\u091b\u0924\u093e\u091b')}</p>
    <h2>{title_suffix or bi('Speak with our sales team', '\u0939\u092e\u093e\u0930\u0940 \u0938\u0947\u0932\u094d\u0938 \u091f\u0940\u092e \u0938\u0947 \u092c\u093e\u0924 \u0915\u0930\u0947\u0902')}</h2>
    <p class="section-sub">{bi("Leave your details — we'll be in touch on WhatsApp within the hour.", '\u0905\u092a\u0928\u0940 \u091c\u093e\u0928\u0915\u093e\u0930\u0940 \u0926\u0947\u0902 \u2014 \u0939\u092e \u090f\u0915 \u0918\u0902\u091f\u0947 \u0915\u0947 \u092d\u0940\u0924\u0930 \u0935\u094d\u0939\u093e\u091f\u094d\u0938\u090f\u092a \u092a\u0930 \u0938\u0902\u092a\u0930\u094d\u0915 \u0915\u0930\u0947\u0902\u0917\u0947\u0964')}</p>

    <div class="enquiry__panel">
      <form class="enquiry-form"{prop_attr}>
        <label>
          <span data-lang="en">Full name</span><span data-lang="hi">\u092a\u0942\u0930\u093e \u0928\u093e\u092e</span>
          <input required type="text" name="name">
        </label>
        <label>
          <span data-lang="en">WhatsApp number</span><span data-lang="hi">\u0935\u094d\u0939\u093e\u091f\u094d\u0938\u090f\u092a \u0928\u0902\u092c\u0930</span>
          <input required type="tel" name="phone" placeholder="+91">
        </label>
        {unit_options}
        <button type="submit" class="btn btn--gold btn--full">
          <span data-lang="en">Send enquiry</span><span data-lang="hi">\u092a\u0942\u091b\u0924\u093e\u091b \u092d\u0947\u091c\u0947\u0902</span>
        </button>
        <p class="note">{bi('Your enquiry is tracked automatically — no spam, ever.', '\u0906\u092a\u0915\u0940 \u092a\u0942\u091b\u0924\u093e\u091b \u0938\u094d\u0935\u091a\u093e\u0932\u093f\u0924 \u0930\u0942\u092a \u0938\u0947 \u091f\u094d\u0930\u0948\u0915 \u0939\u094b\u0924\u0940 \u0939\u0948 \u2014 \u0915\u092d\u0940 \u0938\u094d\u092a\u0948\u092e \u0928\u0939\u0940\u0902\u0964')}</p>
      </form>
      <div class="enquiry-success" hidden>
        {bi('Thank you — our team will reach out on WhatsApp shortly.', '\u0927\u0928\u094d\u092f\u0935\u093e\u0926 \u2014 \u0939\u092e\u093e\u0930\u0940 \u091f\u0940\u092e \u091c\u0932\u094d\u0926 \u0939\u0940 \u0935\u094d\u0939\u093e\u091f\u094d\u0938\u090f\u092a \u092a\u0930 \u0938\u0902\u092a\u0930\u094d\u0915 \u0915\u0930\u0947\u0917\u0940\u0964')}
      </div>
    </div>
  </div>
</section>
"""


print("Templates loaded OK")
