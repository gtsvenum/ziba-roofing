#!/usr/bin/env python3
"""Ziba Roofing static site generator. Run: python3 build_site.py -> ./site/"""
import json, os, shutil, html
from datetime import date
from data import BIZ, COLORS, SERVICES, AREAS, WHY, PROCESS, GENERAL_FAQS
from assets_src import CSS, FAVICON, FORMJS

OUT = "site"
TODAY = date.today().isoformat()
D = BIZ["domain"].rstrip("/")
PAGES = []  # (path, priority, changefreq)
EM = "\u2014"  # real em dash; entities would be double-escaped by e()


def e(s):
    return html.escape(str(s), quote=True)


# ---------------------------------------------------------------- JSON-LD ---
def ld_business():
    return {
        "@type": "RoofingContractor",
        "@id": D + "/#business",
        "name": BIZ["name"],
        "legalName": BIZ["legal_name"],
        "description": "Licensed roofing contractor serving Washington DC, Maryland, and "
                       "Virginia. Roof replacement, repair, flat roofing, metal, slate, "
                       "gutters, and storm damage.",
        "url": D + "/",
        "telephone": BIZ["phone_e164"],
        "email": BIZ["email"],
        "foundingDate": BIZ["founded"],
        "priceRange": BIZ["price_range"],
        "image": D + "/assets/logo.png",
        "logo": D + "/assets/logo.png",
        "address": {
            "@type": "PostalAddress",
            "streetAddress": BIZ["street"],
            "addressLocality": BIZ["city"],
            "addressRegion": BIZ["region"],
            "postalCode": BIZ["postal"],
            "addressCountry": BIZ["country"],
        },
        "geo": {"@type": "GeoCoordinates", "latitude": BIZ["lat"], "longitude": BIZ["lon"]},
        "openingHoursSpecification": [
            {"@type": "OpeningHoursSpecification",
             "dayOfWeek": [{"Mo": "Monday", "Tu": "Tuesday", "We": "Wednesday", "Th": "Thursday",
                            "Fr": "Friday", "Sa": "Saturday", "Su": "Sunday"}[d]
                           for d in days.split(",")],
             "opens": o, "closes": c}
            for days, o, c in BIZ["hours"]
        ],
        "areaServed": [{"@type": "AdministrativeArea", "name": a["name"]} for a in AREAS],
        "hasCredential": {
            "@type": "EducationalOccupationalCredential",
            "credentialCategory": "license",
            "recognizedBy": {"@type": "Organization", "name": BIZ["license_authority"]},
            "identifier": BIZ["license"],
        },
        "hasOfferCatalog": {
            "@type": "OfferCatalog",
            "name": "Roofing Services",
            "itemListElement": [
                {"@type": "Offer",
                 "itemOffered": {"@type": "Service", "name": s["name"],
                                 "url": D + "/services/" + s["slug"] + "/"}}
                for s in SERVICES
            ],
        },
    }


def ld_faq(faqs):
    return {
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": q,
             "acceptedAnswer": {"@type": "Answer", "text": a}}
            for q, a in faqs
        ],
    }


def ld_crumbs(trail):
    return {
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": n,
             **({"item": D + u} if u else {})}
            for i, (n, u) in enumerate(trail)
        ],
    }


# ------------------------------------------------------------------ shell ---
NAV = ([("Services", "/services/")]
       + [("Areas", "/areas/"), ("Why Ziba", "/why-ziba-roofing/"),
          ("FAQ", "/faq/"), ("Contact", "/contact/")])


def shell(*, path, title, desc, h1, body, graph, trail, og_type="WebPage", scripts=""):
    canon = D + path
    crumbs = ""
    if trail:
        links = []
        for n, u in trail[:-1]:
            links.append(f'<a href="{u}">{e(n)}</a>')
        links.append(f"<span>{e(trail[-1][0])}</span>")
        crumbs = ('<nav class="crumbs" aria-label="Breadcrumb"><div class="wrap">'
                  + '<span class="sep">/</span>'.join(links) + "</div></nav>")

    full_graph = {"@context": "https://schema.org", "@graph": graph}
    nav_html = "".join(
        f'<a href="{u}"{" class=cur" if path.startswith(u) and u != "/" else ""}>{e(n)}</a>'
        for n, u in NAV)

    return f"""<!DOCTYPE html>
<html lang="en-US">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{canon}">
<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1">
<meta name="geo.region" content="US-DC"><meta name="geo.placename" content="Washington, DC">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{e(BIZ['name'])}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{canon}">
<meta property="og:image" content="{D}/assets/logo.png">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="/assets/site.css">
{scripts}
<script type="application/ld+json">{json.dumps(full_graph, separators=(",", ":"))}</script>
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="hdr">
  <div class="wrap hdr__in">
    <a class="brand" href="/">
      <img src="/assets/logo.png" alt="" width="44" height="44" class="brand__mark">
      <span class="brand__txt"><b>{e(BIZ["wordmark_a"])}</b><em>{e(BIZ["wordmark_b"])}</em></span>
    </a>
    <nav class="nav" aria-label="Main">{nav_html}</nav>
    <a class="tel" href="tel:{BIZ['phone_e164']}">{e(BIZ['phone_display'])}</a>
  </div>
</header>
{crumbs}
<main id="main">
{body}
</main>
<footer class="ftr">
  <div class="wrap ftr__in">
    <div class="ftr__col">
      <span class="brand__txt ftr__brand"><b>{e(BIZ["wordmark_a"])}</b><em>{e(BIZ["wordmark_b"])}</em></span>
      <p>{e(BIZ['legal_name'])}<br>{e(BIZ['street'])}<br>{e(BIZ['city'])}, {e(BIZ['region'])} {e(BIZ['postal'])}</p>
      <p>License #{e(BIZ['license'])}<br>{e(BIZ['hours_human'])}</p>
      <p><a href="tel:{BIZ['phone_e164']}">{e(BIZ['phone_display'])}</a><br>
         <a href="mailto:{BIZ['email']}">{e(BIZ['email'])}</a></p>
    </div>
    <div class="ftr__col">
      <h2>Services</h2>
      <ul>{"".join(f'<li><a href="/services/{s["slug"]}/">{e(s["name"])}</a></li>' for s in SERVICES)}</ul>
    </div>
    <div class="ftr__col">
      <h2>Service Areas</h2>
      <ul>{"".join(f'<li><a href="/areas/{a["slug"]}/">{e(a["name"])}</a></li>' for a in AREAS)}</ul>
    </div>
  </div>
  <div class="wrap ftr__base">
    <p>&copy; {date.today().year} {e(BIZ['legal_name'].rstrip('.'))}. Roofing contractor serving Washington DC, Maryland &amp; Virginia.</p>
  </div>
</footer>
</body>
</html>
"""


def cta(head="Get a free roof inspection", sub=None):
    sub = sub or ("Written line-item estimate. Inspection photos are yours whether or not you "
                  "hire us.")
    return f"""<section class="cta">
  <div class="wrap cta__in">
    <div><h2>{e(head)}</h2><p>{e(sub)}</p></div>
    <div class="cta__btns">
      <a class="btn btn--gold" href="tel:{BIZ['phone_e164']}">Call {e(BIZ['phone_display'])}</a>
      <a class="btn btn--ghost" href="/contact/">Request an estimate</a>
    </div>
  </div>
</section>"""


def faq_block(faqs, heading="Frequently asked questions"):
    items = "".join(
        f'<details class="faq"><summary><h3>{e(q)}</h3></summary><p>{e(a)}</p></details>'
        for q, a in faqs)
    return f'<section class="sec"><div class="wrap"><h2>{e(heading)}</h2>{items}</div></section>'


def write(path, content, prio="0.6", freq="monthly"):
    rel = path.lstrip("/")
    full = os.path.join(OUT, rel, "index.html") if rel else os.path.join(OUT, "index.html")
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        f.write(content)
    PAGES.append((path if path else "/", prio, freq))


# ------------------------------------------------------------------ pages ---
def page_home():
    svc = "".join(f"""<a class="card" href="/services/{s['slug']}/">
      <h3>{e(s['name'])}</h3><p>{e(s['short'])}</p><span class="card__go">Learn more &rarr;</span></a>"""
                  for s in SERVICES)
    areas = "".join(f'<a class="pill" href="/areas/{a["slug"]}/">{e(a["name"])}</a>' for a in AREAS)
    why = "".join(f"<div class='why'><h3>{e(t)}</h3><p>{e(b)}</p></div>" for t, b in WHY[:4])
    steps = "".join(f"<li><h3>{e(t)}</h3><p>{e(b)}</p></li>" for t, b in PROCESS)

    body = f"""
<section class="hero">
  <div class="wrap hero__in">
    <p class="eyebrow">Licensed roofing contractor &middot; DC &middot; Maryland &middot; Virginia</p>
    <h1>Roofing for the DMV, done by contractors who build houses</h1>
    <p class="lede">Ziba Roofing replaces, repairs, and maintains residential and commercial roofs
      across Washington DC, Montgomery and Prince George's County, Arlington, Alexandria, and
      Fairfax County. Written line-item estimates, flashing replaced on every job, and a straight
      answer about whether you need a repair or a replacement.</p>
    <div class="hero__btns">
      <a class="btn btn--gold" href="tel:{BIZ['phone_e164']}">Call {e(BIZ['phone_display'])}</a>
      <a class="btn btn--ghost" href="/contact/">Free roof inspection</a>
    </div>
    <ul class="trust">
      <li><b>License #{e(BIZ['license'])}</b><span>DC Home Improvement Contractor</span></li>
      <li><b>DC &middot; MD &middot; VA</b><span>Licensed in all three</span></li>
      <li><b>24/7</b><span>Emergency leak tarping</span></li>
    </ul>
  </div>
</section>

<section class="sec sec--mist">
  <div class="wrap">
    <h2>Roofing services</h2>
    <p class="sub">Every full roof includes new underlayment, new drip edge, and new flashing and
      pipe boots. Reused flashing is the most common reason a new roof leaks.</p>
    <div class="grid">{svc}</div>
  </div>
</section>

<section class="sec">
  <div class="wrap">
    <h2>Where we work</h2>
    <p class="sub">The DMV, specifically: the District, the two closest Maryland counties, and
      Northern Virginia inside and just outside the Beltway.</p>
    <div class="pills">{areas}</div>
  </div>
</section>

<section class="sec sec--mist">
  <div class="wrap">
    <h2>Why homeowners pick Ziba</h2>
    <div class="whys">{why}</div>
    <p class="more"><a href="/why-ziba-roofing/">All six reasons &rarr;</a></p>
  </div>
</section>

<section class="sec">
  <div class="wrap">
    <h2>How a Ziba roof job runs</h2>
    <ol class="steps">{steps}</ol>
  </div>
</section>

{faq_block(GENERAL_FAQS[:6], "Common roofing questions")}
{cta()}
"""
    write("", shell(
        path="/",
        title=f"{BIZ['name']} | Roofing Contractor in Washington DC, MD & VA",
        desc="Licensed DMV roofing contractor. Roof replacement, leak repair, flat roofing, "
             "metal, slate, and gutters in Washington DC, Montgomery County, Arlington, "
             "Alexandria, and Fairfax. Free inspection and written estimate.",
        h1="", body=body,
        graph=[ld_business(),
               {"@type": "WebSite", "@id": D + "/#website", "url": D + "/",
                "name": BIZ["name"], "publisher": {"@id": D + "/#business"}},
               ld_faq(GENERAL_FAQS[:6])],
        trail=None), prio="1.0", freq="weekly")


def page_services_index():
    cards = "".join(f"""<a class="card" href="/services/{s['slug']}/">
      <h3>{e(s['name'])}</h3><p>{e(s['short'])}</p><span class="card__go">Learn more &rarr;</span></a>"""
                    for s in SERVICES)
    body = f"""<section class="phead"><div class="wrap">
  <h1>Roofing services across the DMV</h1>
  <p class="lede">Ziba Roofing handles the full range of residential and commercial roofing in
    Washington DC, Maryland, and Virginia &mdash; from a single failed pipe boot to a complete
    standing seam metal installation.</p></div></section>
<section class="sec"><div class="wrap"><div class="grid">{cards}</div></div></section>
{cta()}"""
    write("/services", shell(
        path="/services/",
        title="Roofing Services in DC, Maryland & Virginia | Ziba Roofing",
        desc="Roof replacement, leak repair, flat roofing, metal, slate, gutters, and storm "
             "damage claims across the DMV. Licensed, insured, written estimates.",
        h1="", body=body,
        graph=[ld_business(), ld_crumbs([("Home", "/"), ("Services", None)]),
               {"@type": "ItemList", "itemListElement": [
                   {"@type": "ListItem", "position": i + 1, "name": s["name"],
                    "url": D + "/services/" + s["slug"] + "/"}
                   for i, s in enumerate(SERVICES)]}],
        trail=[("Home", "/"), ("Services", None)]), prio="0.9")


def page_service(s):
    secs = "".join(f"<section class='blk'><h2>{e(t)}</h2><p>{e(b)}</p></section>"
                   for t, b in s["detail"])
    others = "".join(f'<a class="pill" href="/services/{o["slug"]}/">{e(o["name"])}</a>'
                     for o in SERVICES if o["slug"] != s["slug"])
    areas = "".join(f'<a class="pill" href="/areas/{a["slug"]}/">{e(a["short_name"])}</a>'
                    for a in AREAS)
    body = f"""<section class="phead"><div class="wrap">
  <h1>{e(s['h1'])}</h1>
  <p class="answer">{e(s['answer'])}</p>
  <div class="hero__btns">
    <a class="btn btn--gold" href="tel:{BIZ['phone_e164']}">Call {e(BIZ['phone_display'])}</a>
    <a class="btn btn--navy" href="/contact/">Free inspection</a>
  </div></div></section>
<section class="sec"><div class="wrap narrow">{secs}</div></section>
{faq_block(s['faqs'], s["name"] + " " + EM + " questions we get")}
<section class="sec sec--mist"><div class="wrap">
  <h2>Available throughout the DMV</h2><div class="pills">{areas}</div>
  <h2 class="mt">Other services</h2><div class="pills">{others}</div>
</div></section>
{cta()}"""
    write("/services/" + s["slug"], shell(
        path=f"/services/{s['slug']}/",
        title=f"{s['name']} in Washington DC, MD & VA | Ziba Roofing",
        desc=s["short"] + " Licensed DMV roofing contractor. Free inspection and written estimate.",
        h1="", body=body,
        graph=[ld_business(),
               {"@type": "Service", "name": s["name"], "serviceType": s["name"],
                "url": D + "/services/" + s["slug"] + "/",
                "description": s["answer"],
                "provider": {"@id": D + "/#business"},
                "areaServed": [{"@type": "AdministrativeArea", "name": a["name"]} for a in AREAS]},
               ld_faq(s["faqs"]),
               ld_crumbs([("Home", "/"), ("Services", "/services/"), (s["name"], None)])],
        trail=[("Home", "/"), ("Services", "/services/"), (s["name"], None)]), prio="0.8")


def page_areas_index():
    cards = "".join(f"""<a class="card" href="/areas/{a['slug']}/">
      <h3>{e(a['name'])}</h3><p>{e(a['blurb'])}</p><span class="card__go">Learn more &rarr;</span></a>"""
                    for a in AREAS)
    body = f"""<section class="phead"><div class="wrap">
  <h1>Roofing service areas in the DMV</h1>
  <p class="lede">Ziba Roofing serves Washington DC, Montgomery County and Prince George's County in
    Maryland, and Arlington, Alexandria, and Fairfax County in Virginia. Each jurisdiction has its
    own permit rules and its own dominant roof types, and we work in all of them regularly.</p>
  </div></section>
<section class="sec"><div class="wrap"><div class="grid">{cards}</div></div></section>
{cta()}"""
    write("/areas", shell(
        path="/areas/",
        title="Roofing Service Areas | DC, Montgomery, PG, Arlington, Alexandria, Fairfax",
        desc="Ziba Roofing serves the DMV: Washington DC, Montgomery County, Prince George's "
             "County, Arlington, Alexandria, and Fairfax County.",
        h1="", body=body,
        graph=[ld_business(), ld_crumbs([("Home", "/"), ("Service Areas", None)]),
               {"@type": "ItemList", "itemListElement": [
                   {"@type": "ListItem", "position": i + 1, "name": a["name"],
                    "url": D + "/areas/" + a["slug"] + "/"} for i, a in enumerate(AREAS)]}],
        trail=[("Home", "/"), ("Service Areas", None)]), prio="0.9")


def page_area(a):
    hoods = "".join(f"<li>{e(n)}</li>" for n in a["neighborhoods"])
    svc = "".join(f"""<a class="card" href="/services/{s['slug']}/">
      <h3>{e(s['name'])}</h3><p>{e(s['short'])}</p><span class="card__go">Learn more &rarr;</span></a>"""
                  for s in SERVICES)
    faqs = [
        (f"Do you provide roofing services in {a['short_name']}?",
         f"Yes. {BIZ['name']} serves {a['name']} for roof replacement, leak repair, flat roofing, "
         f"metal, slate, gutters, and storm damage, under {BIZ['license_authority']} license "
         f"#{BIZ['license']}."),
        (f"How fast can you get to a roof leak in {a['short_name']}?",
         f"We schedule emergency tarping in {a['short_name']} as quickly as weather and safety "
         f"allow, and permanent repairs typically within the same week."),
        (f"What kind of roofs are most common in {a['short_name']}?",
         a["detail"].split(". ")[0] + "."),
    ]
    body = f"""<section class="phead"><div class="wrap">
  <h1>Roofing Contractor in {e(a['name'])}</h1>
  <p class="answer">{e(BIZ['name'])} is a licensed roofing contractor serving {e(a['name'])} &mdash;
    roof replacement, leak repair, flat and low-slope membrane, metal, slate, gutters, and storm
    damage claims.</p>
  <div class="hero__btns">
    <a class="btn btn--gold" href="tel:{BIZ['phone_e164']}">Call {e(BIZ['phone_display'])}</a>
    <a class="btn btn--navy" href="/contact/">Free inspection</a>
  </div></div></section>
<section class="sec"><div class="wrap narrow">
  <section class="blk"><h2>Roofing in {e(a['short_name'])}</h2><p>{e(a['detail'])}</p></section>
  <section class="blk"><h2>Permits and local requirements</h2><p>{e(a['note'])}</p></section>
  <section class="blk"><h2>Neighborhoods we cover</h2>
    <ul class="hoods">{hoods}</ul>
    <p class="fine">Not listed? If you are inside {e(a['name'])}, we serve you. Call and ask.</p>
  </section>
</div></section>
<section class="sec sec--mist"><div class="wrap">
  <h2>Services available in {e(a['short_name'])}</h2>
  <div class="grid">{svc}</div></div></section>
{faq_block(faqs, f"Roofing in {a['short_name']} " + EM + " questions")}
{cta(f"Free roof inspection in {a['short_name']}")}"""
    write("/areas/" + a["slug"], shell(
        path=f"/areas/{a['slug']}/",
        title=f"Roofing Contractor in {a['name']} | Ziba Roofing",
        desc=f"Licensed roofer serving {a['name']}. {a['blurb']} Roof replacement, repair, flat "
             f"roofing, metal, slate, and gutters. Free inspection.",
        h1="", body=body,
        graph=[ld_business(), ld_faq(faqs),
               ld_crumbs([("Home", "/"), ("Service Areas", "/areas/"), (a["name"], None)])],
        trail=[("Home", "/"), ("Service Areas", "/areas/"), (a["name"], None)]), prio="0.8")


def page_why():
    whys = "".join(f"<section class='blk'><h2>{e(t)}</h2><p>{e(b)}</p></section>" for t, b in WHY)
    steps = "".join(f"<li><h3>{e(t)}</h3><p>{e(b)}</p></li>" for t, b in PROCESS)
    body = f"""<section class="phead"><div class="wrap">
  <h1>Why hire Ziba Roofing</h1>
  <p class="answer">Ziba Roofing is the roofing arm of {e(BIZ['legal_name'])}, a licensed general
    contractor that builds and renovates whole houses across the DMV &mdash; so the person pricing
    your roof knows how it gets built, not just how to sell it.</p></div></section>
<section class="sec"><div class="wrap narrow">{whys}</div></section>
<section class="sec sec--mist"><div class="wrap">
  <h2>How a Ziba roof job runs</h2><ol class="steps">{steps}</ol></div></section>
{cta()}"""
    write("/why-ziba-roofing", shell(
        path="/why-ziba-roofing/",
        title="Why Hire Ziba Roofing | Licensed DMV Roofing Contractor",
        desc="Licensed in DC, Maryland, and Virginia. Written line-item estimates, flashing "
             "replaced on every roof, daily magnet sweeps, and honest repair-vs-replace advice.",
        h1="", body=body,
        graph=[ld_business(), ld_crumbs([("Home", "/"), ("Why Ziba Roofing", None)])],
        trail=[("Home", "/"), ("Why Ziba Roofing", None)]), prio="0.7")


def page_faq():
    body = f"""<section class="phead"><div class="wrap">
  <h1>Roofing questions, answered</h1>
  <p class="lede">Straight answers about cost, timing, materials, and insurance for roofs in the
    Washington DC metro area.</p></div></section>
{faq_block(GENERAL_FAQS, "General roofing questions")}
{cta("Still have a question?", "Call and ask. No sales script, no appointment required.")}"""
    write("/faq", shell(
        path="/faq/",
        title="Roofing FAQ | Cost, Timing & Materials in the DMV | Ziba Roofing",
        desc="How much a new roof costs in Washington DC, how long replacement takes, repair vs "
             "replacement, insurance claims, and the best time of year to reroof in the DMV.",
        h1="", body=body,
        graph=[ld_business(), ld_faq(GENERAL_FAQS),
               ld_crumbs([("Home", "/"), ("FAQ", None)])],
        trail=[("Home", "/"), ("FAQ", None)]), prio="0.8")


def page_contact():
    opts = "".join(f'<option value="{e(s["name"])}">{e(s["name"])}</option>' for s in SERVICES)
    aopts = "".join(f'<option value="{e(a["name"])}">{e(a["name"])}</option>' for a in AREAS)
    body = f"""<section class="phead"><div class="wrap">
  <h1>Request a free roof inspection</h1>
  <p class="answer">Call {e(BIZ['phone_display'])} or send the form below. We inspect, photograph,
    and give you a written line-item estimate at no cost &mdash; and you keep the photos whether or
    not you hire us.</p></div></section>
<section class="sec"><div class="wrap cols">
  <div class="col">
    <form class="form" id="estimate-form" method="post" action="{e(BIZ.get('form_endpoint', ''))}" novalidate>
      <input type="hidden" name="_subject" value="New roof inspection request &mdash; {e(BIZ['name'])} website">
      <input type="hidden" name="_template" value="table">
      <input type="hidden" name="_captcha" value="false">
      <input type="hidden" name="_next" value="{D}/contact/?sent=1">
      <input type="text" name="_honey" style="display:none" tabindex="-1" autocomplete="off" aria-hidden="true">
      <div class="f"><label for="name">Name</label>
        <input id="name" name="name" autocomplete="name" required></div>
      <div class="f"><label for="phone">Phone</label>
        <input id="phone" name="phone" type="tel" autocomplete="tel" required></div>
      <div class="f"><label for="email">Email</label>
        <input id="email" name="email" type="email" autocomplete="email" required></div>
      <div class="f"><label for="address">Property address</label>
        <input id="address" name="address" autocomplete="street-address" required></div>
      <div class="f"><label for="area">Service area</label>
        <select id="area" name="area"><option value="">Select&hellip;</option>{aopts}</select></div>
      <div class="f"><label for="service">What do you need?</label>
        <select id="service" name="service"><option value="">Select&hellip;</option>{opts}
        <option value="Not sure">Not sure &mdash; please advise</option></select></div>
      <div class="f"><label for="msg">Describe the problem</label>
        <textarea id="msg" name="message" rows="5"
          placeholder="Leak in the back bedroom ceiling after heavy rain, roof is about 20 years old&hellip;"></textarea></div>
      <button class="btn btn--gold btn--wide" type="submit">Request inspection</button>
      <p class="formnote" id="formnote" role="status"></p>
    </form>
  </div>
  <aside class="col col--side">
    <h2>Contact</h2>
    <p><a class="big" href="tel:{BIZ['phone_e164']}">{e(BIZ['phone_display'])}</a><br>
       <a href="mailto:{BIZ['email']}">{e(BIZ['email'])}</a></p>
    <h2>Hours</h2><p>{e(BIZ['hours_human'])}</p>
    <h2>Office</h2>
    <p>{e(BIZ['legal_name'])}<br>{e(BIZ['street'])}<br>{e(BIZ['city'])}, {e(BIZ['region'])} {e(BIZ['postal'])}</p>
    <h2>License</h2>
    <p>{e(BIZ['license_authority'])}<br>#{e(BIZ['license'])}</p>
    <h2>Emergency</h2>
    <p>Active leak right now? Call &mdash; we tarp 24/7 to stop interior damage.</p>
  </aside>
</div></section>"""
    write("/contact", shell(
        path="/contact/",
        title="Contact Ziba Roofing | Free Roof Inspection in DC, MD & VA",
        desc=f"Call {BIZ['phone_display']} or request a free roof inspection and written estimate "
             f"anywhere in the DMV. 24/7 emergency leak tarping.",
        h1="", body=body, scripts='<script src="/assets/form.js" defer></script>',
        graph=[ld_business(),
               {"@type": "ContactPage", "url": D + "/contact/"},
               ld_crumbs([("Home", "/"), ("Contact", None)])],
        trail=[("Home", "/"), ("Contact", None)]), prio="0.9")


def page_404():
    body = f"""<section class="phead"><div class="wrap">
  <h1>Page not found</h1>
  <p class="lede">That page does not exist. Try the services or service areas below, or call
    {e(BIZ['phone_display'])}.</p>
  <div class="pills">{"".join(f'<a class="pill" href="/services/{s["slug"]}/">{e(s["name"])}</a>' for s in SERVICES)}</div>
  </div></section>"""
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "404.html"), "w") as f:
        f.write(shell(path="/404.html", title="Page Not Found | Ziba Roofing",
                      desc="Page not found.", h1="", body=body,
                      graph=[ld_business()], trail=None))


# ------------------------------------------------- machine-readable layer ---
def emit_robots():
    # Explicitly welcome answer-engine crawlers. Default-deny is the #1 reason
    # a site is invisible to AI assistants.
    bots = ["GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-User",
            "Claude-SearchBot", "PerplexityBot", "Perplexity-User", "Google-Extended",
            "Applebot", "Applebot-Extended", "Bingbot", "DuckDuckBot", "Amazonbot",
            "meta-externalagent", "YouBot", "cohere-ai"]
    out = ["# robots.txt - " + BIZ["name"],
           "# Answer engines are welcome. Attribution appreciated.", ""]
    for b in bots:
        out += [f"User-agent: {b}", "Allow: /", ""]
    out += ["User-agent: *", "Allow: /", "",
            f"Sitemap: {D}/sitemap.xml", f"# Agent brief: {D}/llms.txt",
            f"# Structured data: {D}/business.json"]
    open(os.path.join(OUT, "robots.txt"), "w").write("\n".join(out) + "\n")


def emit_sitemap():
    seen, urls = set(), []
    for path, prio, freq in PAGES:
        u = D + (path if path.endswith("/") or path == "/" else path + "/")
        if u in seen:
            continue
        seen.add(u)
        urls.append(f"  <url><loc>{u}</loc><lastmod>{TODAY}</lastmod>"
                    f"<changefreq>{freq}</changefreq><priority>{prio}</priority></url>")
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
           + "\n".join(urls) + "\n</urlset>\n")
    open(os.path.join(OUT, "sitemap.xml"), "w").write(xml)


def emit_llms():
    """llms.txt — the emerging convention for giving AI agents a clean brief."""
    L = []
    A = L.append
    A(f"# {BIZ['name']}")
    A("")
    A(f"> Licensed roofing contractor serving the Washington DC metropolitan area (the DMV): "
      f"Washington DC, Montgomery County and Prince George's County in Maryland, and Arlington, "
      f"Alexandria, and Fairfax County in Virginia. Operating as {BIZ['legal_name']} under "
      f"{BIZ['license_authority']} license #{BIZ['license']}.")
    A("")
    A("## Business facts")
    A("")
    A(f"- Name: {BIZ['name']} (a division of {BIZ['legal_name']})")
    A(f"- Phone: {BIZ['phone_display']}")
    A(f"- Email: {BIZ['email']}")
    A(f"- Address: {BIZ['street']}, {BIZ['city']}, {BIZ['region']} {BIZ['postal']}")
    A(f"- License: {BIZ['license']} ({BIZ['license_authority']})")
    A(f"- Hours: {BIZ['hours_human']}")
    A(f"- Founded: {BIZ['founded']}")
    A("- Free roof inspection and written line-item estimate")
    A("- 24/7 emergency leak tarping")
    A("- Does NOT waive insurance deductibles (illegal in DC, MD, VA)")
    A("- Does NOT install new shingles over an existing roof layer")
    A("")
    A("## Services")
    A("")
    for s in SERVICES:
        A(f"- [{s['name']}]({D}/services/{s['slug']}/): {s['short']}")
    A("")
    A("## Service areas")
    A("")
    for a in AREAS:
        A(f"- [{a['name']}]({D}/areas/{a['slug']}/): {a['blurb']} "
          f"Neighborhoods include {', '.join(a['neighborhoods'][:6])}.")
    A("")
    A("## Key answers")
    A("")
    for q, ans in GENERAL_FAQS:
        A(f"**{q}** {ans}")
        A("")
    A("## Pages")
    A("")
    A(f"- [Home]({D}/): Overview of services and service areas")
    A(f"- [Services]({D}/services/): All roofing services")
    A(f"- [Service areas]({D}/areas/): DMV coverage by jurisdiction")
    A(f"- [Why Ziba Roofing]({D}/why-ziba-roofing/): Credentials and process")
    A(f"- [FAQ]({D}/faq/): Cost, timing, materials, insurance")
    A(f"- [Contact]({D}/contact/): Free inspection request")
    A("")
    A(f"Last updated: {TODAY}")
    open(os.path.join(OUT, "llms.txt"), "w").write("\n".join(L) + "\n")


def emit_business_json():
    """Flat machine-readable profile for agents that want JSON over prose."""
    doc = {
        "name": BIZ["name"],
        "legalName": BIZ["legal_name"],
        "category": "Roofing contractor",
        "url": D + "/",
        "telephone": BIZ["phone_display"],
        "telephoneE164": BIZ["phone_e164"],
        "email": BIZ["email"],
        "address": {"street": BIZ["street"], "city": BIZ["city"], "region": BIZ["region"],
                    "postalCode": BIZ["postal"], "country": BIZ["country"]},
        "license": {"number": BIZ["license"], "authority": BIZ["license_authority"]},
        "hours": BIZ["hours_human"],
        "foundedYear": BIZ["founded"],
        "emergencyService": "24/7 leak tarping",
        "freeEstimate": True,
        "servesArea": [{"name": a["name"], "url": D + "/areas/" + a["slug"] + "/",
                        "neighborhoods": a["neighborhoods"]} for a in AREAS],
        "services": [{"name": s["name"], "url": D + "/services/" + s["slug"] + "/",
                      "summary": s["answer"]} for s in SERVICES],
        "faq": [{"question": q, "answer": a} for q, a in GENERAL_FAQS],
        "policies": [
            "Does not waive or absorb insurance deductibles",
            "Does not install over existing roof layers",
            "Replaces all flashing and pipe boots on full roof replacements",
            "Provides written line-item estimates before scheduling",
        ],
        "lastUpdated": TODAY,
    }
    open(os.path.join(OUT, "business.json"), "w").write(json.dumps(doc, indent=2) + "\n")


def emit_assets():
    ad = os.path.join(OUT, "assets")
    os.makedirs(ad, exist_ok=True)
    open(os.path.join(ad, "site.css"), "w").write(CSS)
    open(os.path.join(ad, "favicon.svg"), "w").write(FAVICON)
    open(os.path.join(ad, "form.js"), "w").write(FORMJS)
    logo = os.path.expanduser(
        "~/.openclaw/workspace/Other Projects/Ziba Management/ziba-logo-transparent.png")
    if os.path.exists(logo):
        shutil.copy(logo, os.path.join(ad, "logo.png"))
    # GitHub Pages: don't run Jekyll over the output
    open(os.path.join(OUT, ".nojekyll"), "w").write("")
    # GitHub Pages custom domain. Derived from BIZ["domain"] so it can never
    # drift out of sync with the canonical URLs.
    host = BIZ["domain"].split("://", 1)[-1].rstrip("/")
    open(os.path.join(OUT, "CNAME"), "w").write(host + "\n")


def main():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    page_home()
    page_services_index()
    for s in SERVICES:
        page_service(s)
    page_areas_index()
    for a in AREAS:
        page_area(a)
    page_why()
    page_faq()
    page_contact()
    page_404()
    emit_assets()
    emit_robots()
    emit_sitemap()
    emit_llms()
    emit_business_json()
    print(f"built {len(PAGES)} pages -> ./{OUT}/")
    for p, _, _ in PAGES:
        print("  ", p or "/")


if __name__ == "__main__":
    main()
