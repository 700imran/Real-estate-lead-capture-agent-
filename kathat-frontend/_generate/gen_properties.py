#!/usr/bin/env python3
from data import PROPERTIES
from templates import (
    page_shell, NAV, FOOTER, TAGLINE, DISCLAIMER, CHAT_WIDGET, NAV_LABELS,
    unit_cards, feature_items, amenity_items, hero_art_svg, card_art_svg,
    enquiry_section, bi, ROOT,
)
import os

OUT_DIR = os.path.join(ROOT, "properties")
os.makedirs(OUT_DIR, exist_ok=True)

ROOT_PREFIX = "../"


def render_property(p):
    nav = NAV.format(root=ROOT_PREFIX, **NAV_LABELS)
    footer = FOOTER.format(root=ROOT_PREFIX, tagline=TAGLINE, disclaimer=DISCLAIMER)
    chat = CHAT_WIDGET.format(
        prop_attr=f' data-property-name="{p["name"]}"',
        title=bi("Ask Kathat", "\u0915\u0920\u093e\u0924 \u0938\u0947 \u092a\u0942\u091b\u0947\u0902"),
        placeholder="Ask about pricing, or book a visit\u2026",
        send=bi("Send", "\u092d\u0947\u091c\u0947\u0902"),
    )

    body = f"""{nav}
<main id="main">
  <section class="prop-hero">
    <div class="prop-hero__bg mood-{p['slug']}"></div>
    <div class="wrap">
      <a href="../index.html#portfolio" class="back-link">&larr; {bi('All developments', '\u0938\u092d\u0940 \u092a\u094d\u0930\u094b\u091c\u0947\u0915\u094d\u091f\u094d\u0938')}</a>
      <div class="prop-hero__row reveal">
        {hero_art_svg(p['heroArt'])}
        <div>
          <p class="eyebrow">{bi(p['areaEn'], p['areaHi'])}, {bi(p['cityEn'], p['cityHi'])}</p>
          <h1>{p['name']}</h1>
          <p class="prop-hero__dev">{bi('Developed by', '\u0921\u0947\u0935\u0932\u092a\u0930')}: {bi(p['developerEn'], p['developerHi'])}</p>
          <p class="prop-hero__tag">{bi(p['taglineEn'], p['taglineHi'])}</p>
        </div>
      </div>
    </div>
  </section>

  <section class="bg-ivory">
    <div class="wrap reveal" style="max-width:760px;">
      <p style="font-size:1.05rem;line-height:1.75;">{bi(p['descriptionEn'], p['descriptionHi'])}</p>
    </div>
  </section>

  <section class="bg-ink">
    <div class="wrap reveal">
      <p class="eyebrow">{bi('Why this address', '\u092f\u0939 \u092a\u0924\u093e \u0915\u094d\u092f\u094b\u0902 \u091a\u0941\u0928\u0947\u0902')}</p>
      <ul class="feature-list">
{feature_items(p['whyInvestEn'], p['whyInvestHi'])}
      </ul>
    </div>
  </section>

  <section class="bg-ivory">
    <div class="wrap reveal">
      <p class="eyebrow eyebrow--dark">{bi('Residences', '\u0930\u0947\u091c\u093c\u093f\u0921\u0947\u0902\u0938')}</p>
      <div class="units-grid">
{unit_cards(p['units'])}
      </div>

      <p class="eyebrow eyebrow--dark" style="margin-top:48px;">{bi('Amenities', '\u0938\u0941\u0935\u093f\u0927\u093e\u090f\u0902')}</p>
      <div class="amenities-grid">
{amenity_items(p['amenitiesEn'], p['amenitiesHi'])}
      </div>
    </div>
  </section>

  {enquiry_section(property_slug=p['slug'], units=p['units'], title_suffix=bi('Enquire about ' + p['name'], '\u0907\u0938\u0915\u0947 \u092c\u093e\u0930\u0947 \u092e\u0947\u0902 \u092a\u0942\u091b\u0924\u093e\u091b \u0915\u0930\u0947\u0902'))}
</main>
{footer}
{chat}
"""
    title = f"{p['name']} \u2014 Kathat Estate"
    desc = p["descriptionEn"]
    html = page_shell(title, desc, ROOT_PREFIX, body)
    path = os.path.join(OUT_DIR, f"{p['slug']}.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"wrote {path}")


for prop in PROPERTIES:
    render_property(prop)
