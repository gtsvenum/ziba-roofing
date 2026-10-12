# Ziba Roofing — website

Static site, generated. **Edit the data, not the HTML.**

```
data.py         ← all business facts, services, service areas, FAQs
assets_src.py   ← CSS, favicon, form JS
build_site.py   ← generator
site/           ← OUTPUT (disposable; regenerated every run)
```

Rebuild:

```bash
cd "~/.openclaw/workspace/Other Projects/ziba-roofing"
python3 build_site.py
```

Preview locally:

```bash
cd site && python3 -m http.server 8791
# http://127.0.0.1:8791/
```

No dependencies. No build toolchain. Python 3 standard library only.

---

## ⚠️ Placeholders that MUST be replaced before launch

All in `data.py` → `BIZ`:

| Field | Current | Status |
|---|---|---|
| `phone_display` / `phone_e164` | (301) 366-8210 | ✅ Set by Faraz 2026-10-11. NOTE: this number is also on file as Sonela's management/emergency contact — confirm it's the right line for roofing leads. |
| `email` | mike@zibamgmt.com | ✅ Set by Faraz 2026-10-11 |
| `form_endpoint` | formsubmit.co/mike@… | ⚠️ **Needs one-time activation — see below** |
| `domain` | https://zibaroofing.com | ✅ **Registered 2026-10-11 (IONOS, expires 2027-10-11).** DNS not yet pointed — see DNS_SETUP.md |
| `street` | 712 15th Street NE | ❌ Conflict: contract template says 712 15th St NE, MEMORY.md says 1314 North Carolina Ave NE |
| `founded` | 2015 | ❌ Guess |
| `lat` / `lon` | approximate DC | ❌ Geocode once address is confirmed |

### ⚠️ Activating the contact form (one-time, 2 minutes)

The form posts to **FormSubmit** (formsubmit.co) — no account, no API key, free.
It emails each submission straight to `mike@zibamgmt.com`.

**It will not deliver anything until it is activated:**

1. Deploy the site (or submit the form once from the live domain).
2. FormSubmit emails `mike@zibamgmt.com` a one-time confirmation link.
3. Mike clicks it. Done — every submission after that lands in his inbox.

Until step 3, submissions silently go nowhere. Test it yourself after deploying.

Hidden fields already configured: `_subject` (readable subject line), `_template=table`
(formatted email, not raw key/value), `_captcha=false`, `_next` (redirect back to
`/contact/?sent=1` which triggers the on-page thank-you), and `_honey` (spam honeypot —
bots fill it, humans can't see it).

If you'd rather not use a third party, swap `form_endpoint` in `data.py` for Formspree,
Netlify Forms, or Basin and rebuild. The form markup is standard POST — it works with any of them.



---

## 19 pages

- `/` home
- `/services/` + 7 service pages
- `/areas/` + 6 DMV jurisdiction pages
- `/why-ziba-roofing/`, `/faq/`, `/contact/`, `404.html`

---

## SEO implementation

**Technical**
- Server-rendered HTML. No JS required to read any content — a crawler sees the full page in the initial response.
- Unique `<title>` and meta description per page (verified: zero duplicates).
- Exactly one `<h1>` per page (verified).
- Canonical URL on every page.
- Clean directory URLs (`/services/roof-repair/`), no file extensions.
- `sitemap.xml` with per-page priority and changefreq.
- Breadcrumb navigation, visible and structured.
- Mobile: zero horizontal overflow at 390 / 768 / 1440px (measured via CDP, not eyeballed).
- `prefers-reduced-motion` and print stylesheets.
- Total CSS ~10KB, one file, no CDN, no webfonts → fast LCP.

**Structured data (JSON-LD, 20 blocks, all schema-validated)**
- `RoofingContractor` with address, geo, hours, license credential, service catalog, areaServed — on every page
- `Service` on each service page
- `FAQPage` on home, FAQ, every service page, every area page
- `BreadcrumbList`, `WebSite`, `ContactPage`, `ItemList`

**Local SEO**
- A dedicated page per jurisdiction (DC, Montgomery, PG, Arlington, Alexandria, Fairfax), each with its own neighborhood list, permit notes, and FAQs — this is what ranks for "roofer in Bethesda" style queries.
- NAP (name/address/phone) identical in the footer of all 19 pages and in JSON-LD.
- Service × area internal linking grid.

---

## AEO — optimization for AI agents / answer engines

This is the part most contractor sites miss entirely.

1. **`/llms.txt`** — the emerging convention for handing an LLM a clean brief of the
   business. Markdown, no markup noise, ~6KB. Services, areas, key answers, page map.

2. **`/business.json`** — flat machine-readable profile for agents that prefer JSON
   over parsing prose. Includes an explicit `policies` array.

3. **`robots.txt` explicitly allows answer-engine crawlers** — GPTBot, OAI-SearchBot,
   ChatGPT-User, ClaudeBot, Claude-SearchBot, PerplexityBot, Google-Extended,
   Applebot-Extended, Bingbot, meta-externalagent and others, by name.
   *Most sites block these by default (often unknowingly, via a template or a WAF)
   and are therefore invisible when someone asks an AI assistant to recommend a roofer.*

4. **Answer-first content structure.** Every service and area page opens with a
   `.answer` block: a single self-contained sentence that directly answers the page's
   implied question, with no pronouns depending on earlier context. That is the
   format an extractive model quotes.

5. **Question-shaped H3s with the answer in the first sentence** — 40+ Q&A pairs,
   each one independently quotable.

6. **Facts as text, never as images.** License number, hours, phone, service areas,
   price ranges, material lifespans — all selectable text in the DOM.

7. **Specific, checkable claims** instead of marketing adjectives: "20 to 30 years,"
   "quarter inch per foot of fall," "one to three working days," "license #410520000203."
   Specificity is what gets retrieved and cited; "quality workmanship" is not.

---

## Not done yet

1. **Contact form needs one-time activation.** Wired to FormSubmit → mike@zibamgmt.com.
   Mike must click the confirmation email once before anything is delivered. See above.
2. **No photographs.** There is not a single project photo on the site. For a roofer
   this is the biggest remaining gap — before/after pairs beat any copy I can write.
   See the shoot list below.
3. **No reviews / testimonials.** Once there are real ones, they should be added with
   `Review` + `AggregateRating` schema. Do not fabricate these — Google penalizes fake
   review markup and it is also just lying.
4. **Not submitted** to Google Search Console or Bing Webmaster Tools.
5. **Google Business Profile** is a separate and arguably higher-impact task for local
   roofing search than anything on this site.

### Photo shoot list (priority order)

1. Before/after pairs, same angle, 4–6 completed roofs
2. Crew working — real people, not stock
3. A tear-off in progress showing exposed decking (proves you actually tear off)
4. Close-ups of new flashing and pipe boots (the claim the whole site rests on)
5. Branded truck / yard
6. Faraz on a roof or on site — a face builds more trust than any logo
7. A finished DC rowhouse flat roof and a standing seam metal install

---

## Deploy — ALREADY SET UP

**Repo:** https://github.com/gtsvenum/ziba-roofing (public)
**Live on GitHub's servers:** verified serving correct content
**Blocker:** DNS at IONOS not yet pointed — see `DNS_SETUP.md`

Deployment is automatic. Push to `main` and GitHub Actions rebuilds and redeploys
in ~25 seconds. You never deploy by hand:

```bash
cd "~/.openclaw/workspace/Other Projects/ziba-roofing"
# edit data.py
python3 build_site.py          # optional — verify locally first
git add -A && git commit -m "update" && git push
```

The workflow (`.github/workflows/deploy.yml`) runs the generator on a clean Ubuntu
box, asserts the key files exist, and **fails the build if a placeholder phone
number ever reaches the output**. The `site/` directory is committed for local
preview but the deployed copy is always rebuilt from source.

`site/CNAME` is generated from `BIZ["domain"]`, so the custom domain can never
drift out of sync with the canonical URLs.
