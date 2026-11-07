# LocalProAI — Maintenance

## Build
    BASE=https://yourdomain.com python3 build.py          # custom domain
    BASE=https://USER.github.io PATH_PREFIX=/repo python3 build.py   # project Pages
Output goes to `docs/` (GitHub Pages: Settings → Pages → branch `main`, folder `/docs`). Not deployed yet.

## Data (`data/tools.json`)
Fields: name, url, source_url, verticals, use_cases, pricing, pricing_checked, best_for, sponsored.
- Pricing is copied from the vendor pricing page (`source_url`) on `pricing_checked`. Re-check quarterly; update the date.
- Only add tools you've verified on the vendor site. Never invent prices.
- Verticals/use cases are defined in `build.py` (VERT, UC). Add a vertical there, then tag tools.
- "Best AI tools for {vertical} {use case}" pages are generated automatically when 3+ tools match.
- Long-tail guides (`/guides/`) come from `longtail.py`, which `build.py` runs on the same `data/tools.json`. A listing page is emitted only when at least 3 tools match on vertical and use-case tags, or on a phrase in that tool's own `best_for` text. The hub is linked from the header and the homepage. Sitemap URLs include `lastmod` (latest `pricing_checked` among the tools on that page). Single-tool pricing URLs, trades named by fewer than 3 listings, and internal submission checklists are not published.
- `research/` holds the raw scrape (fetch.py) used to seed pricing; rerun `python3 research/fetch.py` to spot changes.

## Sponsored listings
Set `"sponsored": true` only for paying customers — it shows a "Sponsored" badge and sorts first. Sponsored placement slots on homepage/vertical pages are placeholders until sold.

## Placeholders to replace
- Newsletter form: controlled by the `FORM_ID` env var (Formspree form ID, currently `mjygpydo`), set in the build step `env:` of `.github/workflows/pages.yml`. If unset, the signup form is omitted and a `NEWSLETTER HOOK` comment marks its spot. Local build: `FORM_ID=mjygpydo BASE=... python3 build.py`.
- `BASE` env var (default https://localproai.example)
- Contact email d.bot@mail.grokbot.com (mailto links)

## Design
All styling is in `static/style.css`; filter chips, theme toggle and mobile menu in `static/app.js`. Icons are inline SVG in `ICON_PATHS` (build.py), one per use case/vertical. Card pricing badges (Free option / Free trial / Quote-based / See vendor / Paid) are derived from words already in the `pricing` text (`price_label`). System fonts only; no external assets.
