# DNS setup — point zibaroofing.com at the live site

The website is **already built and deployed**. It is running right now on GitHub's
servers. The only thing left is telling the domain where to look.

Everything below happens at **IONOS** (ionos.com), where zibaroofing.com is registered.

---

## What to do

Log in to IONOS → **Domains & SSL** → `zibaroofing.com` → **DNS**.

Add these **6 records**. Nothing else needs to change.

### 1. Four A records (these make the bare domain work)

| Type | Host / Name | Points to | TTL |
|---|---|---|---|
| A | `@` | `185.199.108.153` | 1 hour |
| A | `@` | `185.199.109.153` | 1 hour |
| A | `@` | `185.199.110.153` | 1 hour |
| A | `@` | `185.199.111.153` | 1 hour |

All four are required — they are GitHub's redundant Pages servers. If IONOS
labels the field "Host" and won't accept `@`, leave it blank or enter
`zibaroofing.com`.

### 2. One CNAME record (makes www.zibaroofing.com work)

| Type | Host / Name | Points to | TTL |
|---|---|---|---|
| CNAME | `www` | `gtsvenum.github.io.` | 1 hour |

Note the trailing dot. IONOS usually adds it automatically.

### 3. Delete any conflicting records

If IONOS pre-created a parking page, remove any existing `@` A record or
`@`/`www` CNAME pointing at IONOS parking. Leaving them in place will make the
site load intermittently — some visitors get the real site, some get a parking page.

**Do not touch the MX records** if any exist (that's email).

---

## Then wait

DNS takes **15 minutes to 2 hours** typically, occasionally up to 24 hours.

Check progress:

```bash
dig +short zibaroofing.com A
```

When it returns the four `185.199.x.153` addresses, it's live.

---

## Last step: turn on HTTPS

Once DNS resolves, GitHub automatically issues a free Let's Encrypt certificate.
This takes a few more minutes.

Then go to **github.com/gtsvenum/ziba-roofing → Settings → Pages** and tick
**"Enforce HTTPS"**.

Until that's ticked the site loads over plain `http://`, which browsers label
"Not secure" — bad for a contractor asking people for their home address.

(Or tell Max and he'll flip it via the API once the cert is ready.)

---

## Verifying it worked

```bash
curl -I https://zibaroofing.com          # expect: HTTP/2 200
curl -I https://www.zibaroofing.com      # expect: 301 -> https://zibaroofing.com
```

In a browser: padlock icon, no warnings, site loads at `https://zibaroofing.com`.

---

## ⚠️ Your DNS currently points at an IONOS parking page

`dig +short zibaroofing.com A` returns **74.208.236.24** — that's IONOS parking,
not GitHub. Replace that A record with the four GitHub ones above.

## When DNS is fixed, flip two switches

The site is temporarily configured for the preview URL. Once the A records point
at GitHub, in `data.py` set:

```python
"pages_custom_domain": True,
"base_path": "",
```

then `git add -A && git commit -m "Switch to live domain" && git push`, and
re-attach the domain:

```bash
gh api -X PUT repos/gtsvenum/ziba-roofing/pages -f "cname=zibaroofing.com"
```

(Or just tell Max and he'll do it.)

## Current status

| Item | State |
|---|---|
| Domain registered | ✅ 2026-10-11, IONOS, expires 2027-10-11 |
| Repo | ✅ github.com/gtsvenum/ziba-roofing |
| Build + deploy workflow | ✅ Passing — rebuilds on every push to `main` |
| Site live on GitHub servers | ✅ Verified serving 200 with correct content |
| Custom domain configured | ⏸️ Temporarily OFF so the preview URL works |
| Preview URL | ✅ **https://gtsvenum.github.io/ziba-roofing/** — live and verified |
| **DNS records at IONOS** | ❌ **Pointing at IONOS parking (74.208.236.24) — must be changed to GitHub's four IPs** |
| HTTPS certificate | ⏳ Issues automatically after DNS resolves |

---

## Note on the repo

It is **public**. The site content is meant to be public anyway, but that also
means the source is visible. There's nothing sensitive in it — no keys, no
passwords. The contact form posts to FormSubmit, which needs no credentials.

If you'd rather it be private, GitHub Pages on a private repo requires a paid
plan. Netlify or Cloudflare Pages host from private repos for free, and moving
is a 10-minute job.
