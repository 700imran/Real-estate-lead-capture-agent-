#!/usr/bin/env python3
from data import PROPERTIES
from templates import (
    page_shell, NAV, FOOTER, TAGLINE, DISCLAIMER, CHAT_WIDGET, NAV_LABELS,
    card_art_svg, enquiry_section, bi, ROOT,
)
import os

nav = NAV.format(root="", **NAV_LABELS)
footer = FOOTER.format(root="", tagline=TAGLINE, disclaimer=DISCLAIMER)
chat = CHAT_WIDGET.format(
    prop_attr="",
    title=bi("Ask Kathat", "\u0915\u0920\u093e\u0924 \u0938\u0947 \u092a\u0942\u091b\u0947\u0902"),
    placeholder="Ask about a development, pricing, or book a visit\u2026",
    send=bi("Send", "\u092d\u0947\u091c\u0947\u0902"),
)

# ---- Hero SVG (tower blueprint line-art) ----
HERO_SVG = """<svg viewBox="0 0 200 280" fill="none" stroke="#D9BE8D" stroke-width="1"
     style="position:absolute;right:clamp(-40px,2vw,40px);top:50%;transform:translateY(-50%);width:min(320px,32vw);opacity:.5;">
  <rect x="30" y="20" width="140" height="240"/>
  <line x1="30" y1="60" x2="170" y2="60"/><line x1="30" y1="100" x2="170" y2="100"/>
  <line x1="30" y1="140" x2="170" y2="140"/><line x1="30" y1="180" x2="170" y2="180"/>
  <line x1="30" y1="220" x2="170" y2="220"/>
  <line x1="10" y1="260" x2="190" y2="260"/>
</svg>"""

# ---- City filter chips ----
cities = []
for p in PROPERTIES:
    if p["cityEn"] not in [c[0] for c in cities]:
        cities.append((p["cityEn"], p["cityHi"]))

chip_html = ['<button class="chip" data-city-chip="all" aria-pressed="true">' + bi("All", "\u0938\u092d\u0940") + "</button>"]
for en, hi in cities:
    chip_html.append(f'<button class="chip" data-city-chip="{en}" aria-pressed="false">{bi(en, hi)}</button>')

# ---- Property cards ----
card_html = []
for p in PROPERTIES:
    cheapest = min(u["priceCr"] for u in p["units"])
    card_html.append(f"""    <a href="properties/{p['slug']}.html" class="property-card reveal" data-track-hover="portfolio-{p['slug']}" data-city-card="{p['cityEn']}">
      <div class="property-card__art mood-{p['slug']}">{card_art_svg(p['heroArt'])}</div>
      <div class="property-card__glass">
        <p class="property-card__loc">{bi(p['areaEn'], p['areaHi'])}, {bi(p['cityEn'], p['cityHi'])}</p>
        <h3>{p['name']}</h3>
        <p class="property-card__dev">{bi(p['developerEn'], p['developerHi'])}</p>
        <p class="property-card__tag">{bi(p['taglineEn'], p['taglineHi'])}</p>
        <p class="property-card__price">
          <span data-lang="en">\u20b9{cheapest} Cr onwards</span>
          <span data-lang="hi">\u20b9{cheapest} \u0915\u0930\u094b\u0921\u093c \u0938\u0947 \u0936\u0941\u0930\u0942</span>
        </p>
        <span class="property-card__cta">{bi('View development', '\u092a\u094d\u0930\u094b\u091c\u0947\u0915\u094d\u091f \u0926\u0947\u0916\u0947\u0902')} &rarr;</span>
      </div>
    </a>""")

# ---- Developers strip ----
seen_devs = []
for p in PROPERTIES:
    pair = (p["developerEn"], p["developerHi"])
    if pair not in seen_devs:
        seen_devs.append(pair)
dev_html = "\n".join(f'    <span>{bi(en, hi)}</span>' for en, hi in seen_devs)

BODY = f"""{nav}
<main id="main">
  <section id="top" class="hero" style="position:relative;overflow:hidden;">
    {HERO_SVG}
    <div class="hero__inner" style="position:relative;z-index:2;">
      <p class="eyebrow">{bi('A curated real estate marketplace', '\u090f\u0915 \u0915\u094d\u092f\u0942\u0930\u0947\u091f\u0947\u0921 \u0930\u093f\u092f\u0932 \u090f\u0938\u094d\u091f\u0947\u091f \u092e\u093e\u0930\u094d\u0915\u0947\u091f\u092a\u094d\u0932\u0947\u0938')}</p>
      <h1>{bi('Every address has a story.', '\u0939\u0930 \u092a\u0924\u0947 \u0915\u0940 \u090f\u0915 \u0915\u0939\u093e\u0928\u0940 \u0939\u0948\u0964')}</h1>
      <p class="hero__sub">{bi(
        "Kathat Estate features considered developments from India's leading developers, across the country's most storied neighbourhoods — each one chosen for what surrounds it.",
        '\u0915\u0920\u093e\u0924 \u090f\u0938\u094d\u091f\u0947\u091f \u092d\u093e\u0930\u0924 \u0915\u0947 \u0905\u0917\u094d\u0930\u0923\u0940 \u0921\u0947\u0935\u0932\u092a\u0930\u094d\u0938 \u0915\u0947 \u0938\u0941\u0935\u093f\u091a\u093e\u0930\u093f\u0924 \u092a\u094d\u0930\u094b\u091c\u0947\u0915\u094d\u091f\u094d\u0938 \u0915\u094b \u0926\u0947\u0936 \u0915\u0947 \u0938\u092c\u0938\u0947 \u092a\u094d\u0930\u0924\u093f\u0937\u094d\u0920\u093f\u0924 \u0907\u0932\u093e\u0915\u094b\u0902 \u092e\u0947\u0902 \u092a\u0947\u0936 \u0915\u0930\u0924\u093e \u0939\u0948 \u2014 \u0939\u0930 \u090f\u0915 \u0915\u094b \u0909\u0938\u0915\u0947 \u0906\u0938-\u092a\u093e\u0938 \u0915\u0947 \u0932\u093f\u090f \u091a\u0941\u0928\u093e \u0917\u092f\u093e \u0939\u0948\u0964'
      )}</p>
      <div class="hero__ctas">
        <a href="#portfolio" class="btn btn--gold">{bi('Explore the portfolio', '\u092a\u094b\u0930\u094d\u091f\u092b\u094b\u0932\u093f\u092f\u094b \u0926\u0947\u0916\u0947\u0902')}</a>
        <a href="#enquiry" class="btn btn--ghost">{bi('Talk to us', '\u0939\u092e\u0938\u0947 \u092c\u093e\u0924 \u0915\u0930\u0947\u0902')}</a>
      </div>
    </div>
  </section>

  <section class="stats">
    <div class="stats__grid">
      <div><div class="stats__value">6</div><div class="stats__label">{bi('Cities', '\u0936\u0939\u0930')}</div></div>
      <div><div class="stats__value">6</div><div class="stats__label">{bi('Featured developments', '\u092a\u094d\u0930\u0926\u0930\u094d\u0936\u093f\u0924 \u092a\u094d\u0930\u094b\u091c\u0947\u0915\u094d\u091f\u094d\u0938')}</div></div>
      <div><div class="stats__value">24/7</div><div class="stats__label">{bi('Enquiry response, every listing', '\u0939\u0930 \u0932\u093f\u0938\u094d\u091f\u093f\u0902\u0917 \u092a\u0930 \u092a\u0942\u091b\u0924\u093e\u091b \u0915\u093e \u091c\u0935\u093e\u092c')}</div></div>
    </div>
  </section>

  <section id="portfolio" class="bg-ivory">
    <div class="wrap">
      <p class="eyebrow eyebrow--dark reveal">{bi('The portfolio', '\u092a\u094b\u0930\u094d\u091f\u092b\u094b\u0932\u093f\u092f\u094b')}</p>
      <h2 class="reveal">{bi('Six cities. One idea.', '\u091b\u0939 \u0936\u0939\u0930\u0964 \u090f\u0915 \u0938\u094b\u091a\u0964')}</h2>
      <p class="section-sub reveal">{bi(
        'Every development featured on Kathat Estate is chosen for what surrounds it, from developers with a track record in that market.',
        '\u0915\u0920\u093e\u0924 \u090f\u0938\u094d\u091f\u0947\u091f \u092a\u0930 \u0939\u0930 \u092a\u094d\u0930\u094b\u091c\u0947\u0915\u094d\u091f \u0909\u0938\u0915\u0947 \u0906\u0938-\u092a\u093e\u0938 \u0915\u0947 \u0907\u0932\u093e\u0915\u0947 \u0915\u0947 \u0932\u093f\u090f \u091a\u0941\u0928\u093e \u0917\u092f\u093e \u0939\u0948, \u0909\u0928 \u0921\u0947\u0935\u0932\u092a\u0930\u094d\u0938 \u0938\u0947 \u091c\u093f\u0928\u0915\u093e \u0909\u0938 \u092c\u093e\u091c\u093e\u0930 \u092e\u0947\u0902 \u090f\u0915 \u0938\u093f\u0926\u094d\u0927 \u0930\u093f\u0915\u0949\u0930\u094d\u0921 \u0939\u0948\u0964'
      )}</p>
      <div class="chips" role="group" aria-label="Filter by city">
        {''.join(chip_html)}
      </div>
      <div class="property-grid">
{chr(10).join(card_html)}
      </div>
    </div>
  </section>

  <section id="developers" class="bg-ivory" style="padding-top:0;">
    <div class="wrap">
      <p class="eyebrow eyebrow--dark reveal" style="text-align:center;">{bi('Featured developers', '\u092b़\u0940\u091a\u0930\u094d\u0921 \u0921\u0947\u0935\u0932\u092a\u0930\u094d\u0938')}</p>
      <div class="developers reveal">
{dev_html}
      </div>
    </div>
  </section>

  <section id="about" class="bg-ink">
    <div class="wrap reveal" style="max-width:640px;text-align:center;">
      <p class="eyebrow">{bi('About Kathat Estate', '\u0915\u0920\u093e\u0924 \u090f\u0938\u094d\u091f\u0947\u091f \u0915\u0947 \u092c\u093e\u0930\u0947 \u092e\u0947\u0902')}</p>
      <h2>{bi('Every address has a story behind it — we go looking for it.', '\u0939\u0930 \u092a\u0924\u0947 \u0915\u0947 \u092a\u0940\u091b\u0947 \u090f\u0915 \u0915\u0939\u093e\u0928\u0940 \u0939\u094b\u0924\u0940 \u0939\u0948 \u2014 \u0939\u092e \u0909\u0938\u0947 \u0922\u0942\u0902\u0922\u0924\u0947 \u0939\u0948\u0902\u0964')}</h2>
      <p style="color:rgba(251,250,246,.7);">{bi(
        "Kathat Estate is a curated marketplace. We don't build anything ourselves — we select developments from India's established developers, for the neighbourhood that surrounds them, and make sure every enquiry gets tracked and answered the same day.",
        '\u0915\u0920\u093e\u0924 \u090f\u0938\u094d\u091f\u0947\u091f \u090f\u0915 \u0915\u094d\u092f\u0942\u0930\u0947\u091f\u0947\u0921 \u092e\u093e\u0930\u094d\u0915\u0947\u091f\u092a\u094d\u0932\u0947\u0938 \u0939\u0948\u0964 \u0939\u092e \u0916\u0941\u0926 \u0915\u0941\u091b \u0928\u0939\u0940\u0902 \u092c\u0928\u093e\u0924\u0947 \u2014 \u0939\u092e \u092d\u093e\u0930\u0924 \u0915\u0947 \u0938\u094d\u0925\u093e\u092a\u093f\u0924 \u0921\u0947\u0935\u0932\u092a\u0930\u094d\u0938 \u0915\u0947 \u092a\u094d\u0930\u094b\u091c\u0947\u0915\u094d\u091f\u094d\u0938 \u0915\u094b \u091a\u0941\u0928\u0924\u0947 \u0939\u0948\u0902, \u0909\u0938 \u0907\u0932\u093e\u0915\u0947 \u0915\u0947 \u0932\u093f\u090f \u091c\u094b \u0909\u0928\u094d\u0939\u0947\u0902 \u0918\u0947\u0930\u0947 \u0939\u0941\u090f \u0939\u0948, \u0914\u0930 \u092f\u0939 \u0938\u0941\u0928\u093f\u0936\u094d\u091a\u093f\u0924 \u0915\u0930\u0924\u0947 \u0939\u0948\u0902 \u0915\u093f \u0939\u0930 \u092a\u0942\u091b\u0924\u093e\u091b \u0909\u0938\u0940 \u0926\u093f\u0928 \u091f\u094d\u0930\u0948\u0915 \u0914\u0930 \u091c\u0935\u093e\u092c\u0926\u0947\u0939 \u0939\u094b\u0964'
      )}</p>
    </div>
  </section>

  <section class="bg-ivory">
    <div class="wrap reveal" style="max-width:640px;text-align:center;">
      <p class="eyebrow eyebrow--dark">{bi('How enquiries are handled', '\u092a\u0942\u091b\u0924\u093e\u091b \u0915\u0948\u0938\u0947 \u0939\u0948\u0902\u0921\u0932 \u0939\u094b\u0924\u0940 \u0939\u0948')}</p>
      <h2>{bi('Every visit, tracked. Every enquiry, answered.', '\u0939\u0930 \u0935\u093f\u091c़\u093f\u091f \u091f\u094d\u0930\u0948\u0915 \u0939\u094b\u0924\u0940 \u0939\u0948\u0964 \u0939\u0930 \u092a\u0942\u091b\u0924\u093e\u091b \u0915\u093e \u091c\u0935\u093e\u092c \u092e\u093f\u0932\u0924\u093e \u0939\u0948\u0964')}</h2>
      <p style="color:rgba(23,20,15,.65);">{bi(
        "This site runs on the same engine behind it: visitor activity is scored in real time, enquiries sync straight to WhatsApp and the sales CRM, and an AI assistant can answer questions right here while a specialist picks up the follow-up.",
        '\u092f\u0939 \u0935\u0947\u092c\u0938\u093e\u0907\u091f \u0909\u0938\u0940 \u0907\u0902\u091c\u0928 \u092a\u0930 \u091a\u0932\u0924\u0940 \u0939\u0948 \u091c\u094b \u0907\u0938\u0915\u0947 \u092a\u0940\u091b\u0947 \u0939\u0948: \u0935\u093f\u091c़\u093f\u091f\u0930 \u0917\u0924\u093f\u0935\u093f\u0927\u093f \u0930\u093f\u092f\u0932-\u091f\u093e\u0907\u092e \u092e\u0947\u0902 \u0938\u094d\u0915\u094b\u0930 \u0939\u094b\u0924\u0940 \u0939\u0948, \u092a\u0942\u091b\u0924\u093e\u091b \u0938\u0940\u0927\u0947 \u0935\u094d\u0939\u093e\u091f\u094d\u0938\u090f\u092a \u0914\u0930 \u0938\u0947\u0932\u094d\u0938 CRM \u092e\u0947\u0902 \u091c\u093e\u0924\u0940 \u0939\u0948, \u0914\u0930 \u092f\u0939\u0940\u0902 \u090f\u0915 AI \u0938\u0939\u093e\u092f\u0915 \u0938\u0935\u093e\u0932\u094b\u0902 \u0915\u093e \u091c\u0935\u093e\u092c \u0926\u0947 \u0938\u0915\u0924\u093e \u0939\u0948, \u091c\u092c\u0924\u0915 \u0915\u093f \u0939\u092e\u093e\u0930\u0940 \u091f\u0940\u092e \u0916\u0941\u0926 \u092b़\u0949\u0932\u094b-\u0905\u092a \u0915\u0930\u0924\u0940 \u0939\u0948\u0964'
      )}</p>
    </div>
  </section>

  {enquiry_section()}
</main>
{footer}
{chat}
"""

html = page_shell(
    "Kathat Estate \u2014 A Curated Real Estate Marketplace",
    "Kathat Estate features considered developments from India's leading developers, across the country's most storied neighbourhoods.",
    "",
    BODY,
)
path = os.path.join(ROOT, "index.html")
with open(path, "w", encoding="utf-8") as f:
    f.write(html)
print(f"wrote {path}")
