#!/usr/bin/env python3
"""Static site generator for LocalProAI. Usage: BASE=https://example.com python3 build.py"""
import json, os, shutil, html, re, urllib.parse
from collections import defaultdict
BASE = os.environ.get("BASE", "https://localproai.example").rstrip("/")
PATH_PREFIX = os.environ.get("PATH_PREFIX", "").rstrip("/")  # e.g. /localai-directory for project Pages
SITE = "LocalProAI"; EMAIL = "d.bot@mail.grokbot.com"; FORM_ID = os.environ.get("FORM_ID", "").strip()  # newsletter flag: off until a real Formspree ID is set
FORM = f"https://formspree.io/f/{FORM_ID}"; SHOW_FORM = bool(FORM_ID) and FORM_ID != "FORM_ID"
OUT = "docs"
VERT = {"contractors": "Contractors & Trades", "realtors": "Realtors", "salons": "Salons & Beauty"}
UC = {"quotes-estimates":"Quotes & Estimates","scheduling":"Scheduling & Booking","invoicing-payments":"Invoicing & Payments",
 "crm":"CRM","phone-answering":"Phone Answering","reviews":"Reviews","listings-marketing":"Listings & Marketing Copy",
 "measurements":"Measurements","job-documentation":"Job Documentation","virtual-staging":"Virtual Staging",
 "lead-follow-up":"Lead Follow-up","general-assistant":"AI Assistants & Notes","video":"Video","social-media":"Social Media",
 "website":"Website Builders","local-seo":"Local SEO","bookkeeping":"Bookkeeping","automation":"Automation","website-chat":"Website Chat"}
tools = json.load(open("data/tools.json"))
slug = lambda s: re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
for t in tools: t["slug"] = slug(t["name"])
e = html.escape
pages = []
def link(p): return f"{PATH_PREFIX}{p}"

# ---------- inline SVG icon set (stroke icons, 24x24, no external assets) ----------
ICON_PATHS = {
 "quotes-estimates": '<rect x="5" y="3" width="14" height="18" rx="2"/><path d="M8 7h8M8 12h1M12 12h1M15.5 12h.5M8 16h1M12 16h1M15.5 16h.5"/>',
 "scheduling": '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M16 3v4M8 3v4M3 10h18M8 14h3"/>',
 "invoicing-payments": '<rect x="2" y="5" width="20" height="14" rx="2"/><path d="M2 10h20M6 15h4"/>',
 "crm": '<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20a6.5 6.5 0 0 1 13 0M16 4.6a3.5 3.5 0 0 1 0 6.8M18 14.2a6.5 6.5 0 0 1 3.5 5.8"/>',
 "phone-answering": '<path d="M5 3h3.5l2 5-2.3 1.4a11 11 0 0 0 6.4 6.4L16 13.5l5 2V19a2 2 0 0 1-2 2A16 16 0 0 1 3 5a2 2 0 0 1 2-2z"/>',
 "reviews": '<path d="M12 3l2.8 5.7 6.2.9-4.5 4.4 1 6.2L12 17.3 6.5 20.2l1-6.2L3 9.6l6.2-.9z"/>',
 "listings-marketing": '<path d="M3 10.5v3a1 1 0 0 0 1 1h3l7 4.5v-14L7 9.5H4a1 1 0 0 0-1 1zM18 8.5a5 5 0 0 1 0 7"/>',
 "measurements": '<path d="M3 16.5L16.5 3 21 7.5 7.5 21z"/><path d="M7 12.5l2 2M10 9.5l2 2M13 6.5l2 2"/>',
 "job-documentation": '<path d="M4 7h3l2-3h6l2 3h3a1 1 0 0 1 1 1v11a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V8a1 1 0 0 1 1-1z"/><circle cx="12" cy="13" r="3.5"/>',
 "virtual-staging": '<path d="M4 11V8a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v3"/><path d="M2 13a2 2 0 0 1 4 0v2h12v-2a2 2 0 0 1 4 0v5H2zM5 18v2M19 18v2"/>',
 "lead-follow-up": '<path d="M22 2L11 13M22 2l-7 20-4-9-9-4z"/>',
 "general-assistant": '<path d="M11 3l1.9 5.1L18 10l-5.1 1.9L11 17l-1.9-5.1L4 10l5.1-1.9zM19 14l.8 2.2L22 17l-2.2.8L19 20l-.8-2.2L16 17l2.2-.8z"/>',
 "video": '<rect x="2" y="6" width="14" height="12" rx="2"/><path d="M16 10.5l6-3.5v10l-6-3.5z"/>',
 "social-media": '<circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><path d="M8.6 13.5l6.8 4M15.4 6.5l-6.8 4"/>',
 "website": '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18"/>',
 "local-seo": '<path d="M12 21s-7-6.2-7-12a7 7 0 0 1 14 0c0 5.8-7 12-7 12z"/><circle cx="12" cy="9" r="2.5"/>',
 "bookkeeping": '<path d="M4 4.5A1.5 1.5 0 0 1 5.5 3H18v15H6.5A2.5 2.5 0 0 0 4 20.5z"/><path d="M4 20.5A2.5 2.5 0 0 1 6.5 18H18v3H6.5M8 7.5h6M8 11h4"/>',
 "automation": '<path d="M13 2L4 14h7l-1 8 9-12h-7z"/>',
 "website-chat": '<path d="M21 12a8 8 0 0 1-11.6 7.1L4 20.5l1.4-4.9A8 8 0 1 1 21 12z"/><path d="M8.5 12h.01M12 12h.01M15.5 12h.01"/>',
 "contractors": '<path d="M2 18.5h20M4 18.5V16a8 8 0 0 1 16 0v2.5M9.5 8.4V5.5h5v2.9M12 5.5v6"/>',
 "realtors": '<path d="M3 11l9-8 9 8M5 9.5V21h14V9.5M10 21v-6h4v6"/>',
 "salons": '<circle cx="6" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><path d="M8.2 8.2L20 20M8.2 15.8L20 4"/>',
 "search": '<circle cx="11" cy="11" r="7"/><path d="M20 20l-4-4"/>',
 "tag": '<path d="M3 12V4a1 1 0 0 1 1-1h8l9 9-9 9z"/><circle cx="7.5" cy="7.5" r="1.5"/>',
 "external": '<path d="M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5"/>',
 "check": '<path d="M20 6L9 17l-5-5"/>',
 "sun": '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
 "moon": '<path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/>',
 "menu": '<path d="M4 7h16M4 12h16M4 17h16"/>',
 "mail": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/>',
 "arrow": '<path d="M5 12h14M13 6l6 6-6 6"/>',
 "megaphone": '<path d="M3 10.5v3a1 1 0 0 0 1 1h3l7 4.5v-14L7 9.5H4a1 1 0 0 0-1 1zM18 8.5a5 5 0 0 1 0 7"/>',
 "shield": '<path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z"/><path d="M8.5 12l2.5 2.5 4.5-5"/>',
}
def icon(name, cls="i"):
    return f'<svg class="{cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">{ICON_PATHS[name]}</svg>'
LOGO = '<svg class="logo-mark" viewBox="0 0 32 32" aria-hidden="true" focusable="false"><defs><linearGradient id="lg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#7c5cff"/><stop offset=".55" stop-color="#4f8cff"/><stop offset="1" stop-color="#22d3ee"/></linearGradient></defs><rect width="32" height="32" rx="9" fill="url(#lg)"/><path d="M16 6.5l2.3 6.2 6.2 2.3-6.2 2.3L16 23.5l-2.3-6.2-6.2-2.3 6.2-2.3z" fill="#fff"/><circle cx="23.5" cy="8.5" r="1.6" fill="#fff" opacity=".85"/></svg>'

FAVICON = "data:image/svg+xml," + urllib.parse.quote('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#7c5cff"/><stop offset="1" stop-color="#22d3ee"/></linearGradient></defs><rect width="32" height="32" rx="9" fill="url(#g)"/><path d="M16 6.5l2.3 6.2 6.2 2.3-6.2 2.3L16 23.5l-2.3-6.2-6.2-2.3 6.2-2.3z" fill="#fff"/></svg>')
def price_label(p):
    """Short visual badge derived only from words already present in the vendor-stated pricing text."""
    pl = p.lower()
    if pl.startswith("free") or "free plan" in pl or pl.startswith("starter $0"): return ("Free option", "free")
    if "trial" in pl: return ("Free trial", "trial")
    if pl.startswith("quote-based") or pl.startswith("not published"): return ("Quote-based", "quote")
    if pl.startswith("see vendor") or "see vendor page" in pl: return ("See vendor", "quote")
    return ("Paid", "paid")

THEME_JS = "<script>try{var t=localStorage.getItem('theme');if(t)document.documentElement.setAttribute('data-theme',t)}catch(e){}</script>"
NEWS = f'''<section class="news wrap"><div class="news-card"><div class="news-copy"><span class="news-ico">{icon("mail")}</span><h2>Get new AI tools for local businesses</h2></div><form action="{FORM}" method="POST"><input type="email" name="email" placeholder="you@business.com" required aria-label="Email"><button>Subscribe</button></form></div></section>''' if SHOW_FORM else "<!-- NEWSLETTER HOOK: set FORM_ID env var to enable signup -->"

def write(path, title, desc, body, schema=None):
    url = BASE + PATH_PREFIX + path
    sj = f'<script type="application/ld+json">{json.dumps(schema)}</script>' if schema else ""
    CUR = ' aria-current="page"'
    navl = ''.join(f'<a href="{link("/"+k+"/")}"{CUR if path.startswith("/"+k+"/") else ""}>{v}</a>' for k,v in VERT.items())
    doc = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title><meta name="description" content="{e(desc)}"><link rel="canonical" href="{url}">
<meta property="og:type" content="website"><meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}"><meta property="og:url" content="{url}"><meta property="og:site_name" content="{SITE}">
<meta name="color-scheme" content="light dark"><meta name="theme-color" content="#0b0d1a">{THEME_JS}<link rel="icon" href="{FAVICON}">
<link rel="stylesheet" href="{link('/style.css')}">{sj}</head><body>
<a class="skip" href="#main">Skip to content</a>
<header class="site-head"><div class="wrap head-in"><a class="logo" href="{link('/')}">{LOGO}<span>{SITE}</span></a>
<nav id="nav" aria-label="Main">{navl}<a href="{link('/use-cases/')}"{' aria-current="page"' if path.startswith('/use-cases/') else ''}>Use cases</a><a href="{link('/advertise/')}"{' aria-current="page"' if path.startswith('/advertise/') else ''}>Advertise</a><a class="nav-cta" href="mailto:{EMAIL}?subject=Submit%20a%20tool">Submit a tool</a></nav>
<div class="head-act"><button class="icon-btn" id="theme" type="button" aria-label="Toggle dark mode">{icon("sun","i sun")}{icon("moon","i moon")}</button><button class="icon-btn menu-btn" id="menu" type="button" aria-label="Menu" aria-expanded="false" aria-controls="nav">{icon("menu")}</button></div></div></header>
<main id="main">{body}</main>
{NEWS}
<footer class="site-foot"><div class="wrap foot-in"><a class="logo" href="{link('/')}">{LOGO}<span>{SITE}</span></a><p>&copy; {SITE} &middot; Pricing as stated on vendor sites on the date shown; verify before buying. &middot; <a href="mailto:{EMAIL}?subject=Advertise">Advertise</a> &middot; <a href="mailto:{EMAIL}?subject=Submit%20a%20tool">Submit a tool</a> &middot; Anonymous visit counts via GoatCounter (no cookies).</p></div></footer>
<script src="{link('/app.js')}"></script>
<script>window.goatcounter={{path:function(){{return location.pathname||'/'}}}}</script>
<script data-goatcounter="https://jgonthego.goatcounter.com/count" async src="{link('/assets/gc.js')}"></script>
</body></html>"""
    fp = os.path.join(OUT, path.strip("/"), "index.html") if path.endswith("/") else os.path.join(OUT, path.strip("/"))
    os.makedirs(os.path.dirname(fp), exist_ok=True); open(fp, "w").write(doc); pages.append(url)

SP = f'<span class="sp">{icon("shield")}Sponsored</span>'
def tags_html(t): return "".join(f'<a class="tag" href="{link("/use-cases/"+u+"/")}">{icon(u)}{UC[u]}</a>' for u in t["use_cases"])
def card(t):
    sp = SP if t.get("sponsored") else ""
    pl, pk = price_label(t["pricing"])
    return f'''<article class="card{' is-sponsored' if t.get('sponsored') else ''}" data-v="{' '.join(t['verticals'])}" data-u="{' '.join(t['use_cases'])}" data-n="{e(t['name'].lower()+' '+t['best_for'].lower())}"><div class="card-top"><span class="ico">{icon(t['use_cases'][0])}</span>{sp}<span class="pbadge pb-{pk}">{pl}</span></div><h3><a class="stretch" href="{link('/tools/'+t['slug']+'/')}">{e(t['name'])}</a></h3><p class="bf">{e(t['best_for'])}</p><p class="price">{icon("tag")}<span>{e(t['pricing'])} <small>(checked {t['pricing_checked']})</small></span></p><div class="tags">{tags_html(t)}</div></article>'''
def itemlist(name, ts):
    return {"@context":"https://schema.org","@type":"ItemList","name":name,"itemListElement":[{"@type":"ListItem","position":i+1,"url":BASE+PATH_PREFIX+"/tools/"+t["slug"]+"/","name":t["name"]} for i,t in enumerate(ts)]}
def order(ts): return sorted(ts, key=lambda t:(not t.get("sponsored"), t["name"].lower()))
def grid(ts): return '<div class="grid">'+"".join(card(t) for t in order(ts))+"</div>"
def slot(subject, label):
    return f'<aside class="slot"><span class="slot-ico">{icon("megaphone")}</span><div><strong>{label}</strong><p class="adv"><a href="mailto:{EMAIL}?subject={subject}">Advertise / sponsor this page</a></p></div><span class="slot-arrow">{icon("arrow")}</span></aside>'
def crumbs(*items):
    out = [f'<a href="{link("/")}">Home</a>'] + [f'<a href="{h}">{e(n)}</a>' if h else f'<span aria-current="page">{e(n)}</span>' for n, h in items]
    return '<nav class="crumbs" aria-label="Breadcrumb">' + '<span class="sep">›</span>'.join(out) + '</nav>'
def page_hero(kicker_icon, kicker, h1, sub="", extra="", crumb=""):
    return f'<section class="phero"><div class="glow" aria-hidden="true"></div><div class="wrap">{crumb}<span class="kicker">{icon(kicker_icon)}{kicker}</span><h1>{h1}</h1>{f"<p class=lead>{sub}</p>" if sub else ""}{extra}</div></section>'

if os.path.exists(OUT): shutil.rmtree(OUT)
os.makedirs(OUT)
shutil.copy("static/style.css", OUT); shutil.copy("static/app.js", OUT)
os.makedirs(os.path.join(OUT, "assets")); shutil.copy("static/gc.js", os.path.join(OUT, "assets", "gc.js"))  # self-hosted GoatCounter count.js (ISC)
open(os.path.join(OUT, ".nojekyll"), "w").close()
uc_count = {u: len([t for t in tools if u in t["use_cases"]]) for u in UC}
# home
vchips = '<button type="button" class="chip" data-fv="" aria-pressed="true">All verticals</button>' + "".join(f'<button type="button" class="chip" data-fv="{k}" aria-pressed="false">{icon(k)}{v}</button>' for k,v in VERT.items())
uchips = '<button type="button" class="chip sm" data-fu="" aria-pressed="true">All use cases</button>' + "".join(f'<button type="button" class="chip sm" data-fu="{k}" aria-pressed="false">{icon(k)}{v}</button>' for k,v in UC.items() if uc_count[k])
write("/", f"{SITE} — AI Tools for Contractors, Realtors & Salons", f"A curated directory of {len(tools)} AI tools for local service businesses, with vendor-stated pricing and honest notes.",
 f'''<section class="hero"><div class="glow" aria-hidden="true"></div><div class="grid-bg" aria-hidden="true"></div><div class="wrap hero-in">
<span class="kicker">{icon("general-assistant")}{len(tools)} tools &middot; {len(VERT)} verticals &middot; {sum(1 for v in uc_count.values() if v)} use cases</span>
<h1>AI tools for <span class="grad">local service businesses</span></h1><p class="lead">{len(tools)} tools, hand-checked against vendor sites. No paid placements without a <span class="sp">{icon("shield")}Sponsored</span> label.</p>
<div class="filters" role="search"><label class="searchbox">{icon("search")}<input id="q" type="search" placeholder="Search tools…" aria-label="Search" autocomplete="off"><kbd>/</kbd></label>
<div class="chips seg" role="group" aria-label="Filter by vertical">{vchips}</div></div>
<div class="vcards">{"".join(f'<a class="vcard" href="{link("/"+k+"/")}"><span class="ico">{icon(k)}</span><span><strong>{v}</strong><small>{len([t for t in tools if k in t["verticals"]])} tools</small></span>{icon("arrow","i arr")}</a>' for k,v in VERT.items())}</div>
</div></section>
<div class="wrap">
<!-- SPONSOR SLOT: homepage feature (add real sponsor here) -->{slot(f"Sponsor%20{SITE}%20homepage", "Homepage feature slot")}
<div class="chips scroll" role="group" aria-label="Filter by use case">{uchips}</div>
<p class="count" id="count" aria-live="polite">Showing {len(tools)} tools</p>
{grid(tools)}<div class="empty" id="empty" hidden>{icon("search")}<p>No tools match those filters.</p><button type="button" class="btn ghost" id="reset">Clear filters</button></div></div>''', itemlist("All AI tools", tools))
# verticals, use cases, combos
for v, vn in VERT.items():
    ts = [t for t in tools if v in t["verticals"]]
    combos = [(u, un) for u, un in UC.items() if len([t for t in ts if u in t["use_cases"]]) >= 3]
    cl = "".join(f'<li><a href="{link(f"/best/{v}/{u}/")}">{icon(u)}<span>Best AI {un.lower()} tools for {vn.lower()}</span>{icon("arrow","i arr")}</a></li>' for u, un in combos)
    write(f"/{v}/", f"AI Tools for {vn} ({len(ts)} picks) | {SITE}", f"{len(ts)} AI tools for {vn.lower()}: quoting, scheduling, phone answering, marketing and more, with pricing checked on vendor sites.",
      page_hero(v, f"{len(ts)} tools", f'AI tools for <span class="grad">{vn}</span>', crumb=crumbs((vn, None))) +
      f'<div class="wrap"><!-- SPONSOR SLOT: featured {vn} (add real sponsor here) -->{slot(f"Sponsor%20{vn}%20page", f"Featured {vn} slot")}<h2 class="sec">Best-of guides</h2><ul class="guides">{cl}</ul><h2 class="sec">All {vn.lower()} tools</h2>{grid(ts)}</div>', itemlist(f"AI tools for {vn}", ts))
    for u, un in combos:
        cs = [t for t in ts if u in t["use_cases"]]
        rows = "".join(f'<tr><th scope="row"><a href="{link("/tools/"+t["slug"]+"/")}">{e(t["name"])}</a>{" "+SP if t.get("sponsored") else ""}</th><td data-l="Best for">{e(t["best_for"])}</td><td data-l="Pricing">{e(t["pricing"])}</td><td data-l="Checked">{t["pricing_checked"]}</td></tr>' for t in order(cs))
        write(f"/best/{v}/{u}/", f"Best AI Tools for {vn} {un} ({len(cs)}) | {SITE}", f"The best AI {un.lower()} tools for {vn.lower()}: {', '.join(t['name'] for t in cs[:4])} and more, with pricing and honest notes.",
          page_hero(u, f"{len(cs)} tools compared", f"Best AI tools for {vn} {un}", crumb=crumbs((vn, link("/"+v+"/")), (un, None))) +
          f'<div class="wrap"><h2 class="sec">At a glance</h2><div class="tbl-wrap"><table class="compare"><thead><tr><th scope="col">Tool</th><th scope="col">Best for</th><th scope="col">Pricing</th><th scope="col">Checked</th></tr></thead><tbody>{rows}</tbody></table></div><h2 class="sec">The picks</h2>{grid(cs)}</div>', itemlist(f"Best AI tools for {vn} {un}", cs))
idx = ""
for u, un in UC.items():
    ts = [t for t in tools if u in t["use_cases"]]
    if not ts: continue
    idx += f'<li><a href="{link("/use-cases/"+u+"/")}"><span class="ico">{icon(u)}</span><span class="uc-n">{un}</span> <span class="cnt">({len(ts)})</span></a></li>'
    write(f"/use-cases/{u}/", f"AI {un} Tools for Local Businesses | {SITE}", f"{len(ts)} AI {un.lower()} tools for contractors, realtors and salons, with vendor-stated pricing.",
      page_hero(u, f"{len(ts)} tools", f"AI {un} tools", crumb=crumbs(("Use cases", link("/use-cases/")), (un, None))) + f'<div class="wrap">{grid(ts)}</div>', itemlist(f"AI {un} tools", ts))
write("/use-cases/", f"AI Tools by Use Case | {SITE}", "Browse AI tools for local service businesses by job: quotes, scheduling, reviews, phone answering, bookkeeping and more.",
      page_hero("automation", "Browse by job", "Browse by use case", crumb=crumbs(("Use cases", None))) + f'<div class="wrap"><ul class="ucgrid">{idx}</ul></div>')
for t in tools:
    vs = ", ".join(f'<a href="{link("/"+v+"/")}">{VERT[v]}</a>' for v in t["verticals"])
    pl, pk = price_label(t["pricing"])
    rel = order([x for x in tools if x is not t and set(x["use_cases"]) & set(t["use_cases"]) and set(x["verticals"]) & set(t["verticals"])])[:3]
    relh = f'<h2 class="sec">Similar tools</h2><div class="grid">{"".join(card(x) for x in rel)}</div>' if rel else ""
    u0 = t["use_cases"][0]
    write(f"/tools/{t['slug']}/", f"{t['name']}: Pricing & Review for Local Businesses | {SITE}", f"{t['name']} — {t['best_for']} Pricing: {t['pricing']}"[:300],
      f'''<section class="phero tool-hero"><div class="glow" aria-hidden="true"></div><div class="wrap">{crumbs((UC[u0], link("/use-cases/"+u0+"/")), (t["name"], None))}
<div class="tool-head"><span class="ico xl">{icon(u0)}</span><div>{SP if t.get('sponsored') else ''}<h1>{e(t['name'])}</h1><p class="lead"><strong>Best for:</strong> {e(t['best_for'])}</p></div></div></div></section>
<div class="wrap tool-layout"><div class="tool-main">
<div class="panel"><h2>{icon("check")}Verticals</h2><p><strong class="vh">Verticals:</strong> {vs}</p></div>
<div class="panel"><h2>{icon("automation")}Use cases</h2><p class="tags">{tags_html(t)}</p></div>
<div class="panel muted"><p><small>Source: <a href="{e(t['source_url'])}" rel="nofollow">{e(t['source_url'])}</a></small></p>
<p><small>Are you the vendor? <a href="mailto:{EMAIL}?subject=Claim%20listing:%20{e(t['name'])}">Claim this free listing</a>.</small></p></div></div>
<aside class="price-card"><span class="pbadge pb-{pk}">{pl}</span><h2>Pricing</h2><p class="pc-price"><strong class="vh">Pricing:</strong> {e(t['pricing'])} <small>(as stated on vendor site, checked {t['pricing_checked']})</small></p>
<p><a class="btn" href="{e(t['url'])}" rel="nofollow noopener" target="_blank">Visit {e(t['name'])}{icon("external")}</a></p></aside></div>
<div class="wrap">{relh}</div>''',
      {"@context":"https://schema.org","@type":"SoftwareApplication","name":t["name"],"url":t["url"],"applicationCategory":"BusinessApplication","description":t["best_for"]})
TIERS = [("Basic listing (claim & update your info)", "Free", "check", ""), ("Featured in one vertical (top of vertical page + card badge)", "$49/mo", "megaphone", ""), ("Homepage feature", "$149/mo", "general-assistant", " hot")]
write("/advertise/", f"Advertise on {SITE} — Sponsored Listings", "Reach contractors, realtors and salon owners shopping for AI tools. Featured vertical and homepage placements, plus free claimable listings.",
 page_hero("megaphone", "Sponsored listings", f"Advertise on {SITE}", f'Draft pricing — all paid placements are clearly labeled <span class="sp">{icon("shield")}Sponsored</span>.', crumb=crumbs(("Advertise", None))) +
 f'''<div class="wrap"><div class="tiers" role="table" aria-label="Placement pricing"><div class="sr" role="row"><span role="columnheader">Placement</span><span role="columnheader">Price</span></div>{"".join(f'<div class="tier{hot}" role="row"><span class="ico">{icon(ic)}</span><p class="tier-price" role="cell">{pr}</p><p class="tier-name" role="cell">{n}</p></div>' for n,pr,ic,hot in TIERS)}</div>
<div class="panel center"><p>{icon("shield")}Sponsorship never changes our "best for" notes or pricing info.</p><p><a class="btn" href="mailto:{EMAIL}?subject=Advertise%20on%20{SITE}">Email us to advertise{icon("arrow")}</a></p></div></div>''')
open(f"{OUT}/sitemap.xml","w").write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+"".join(f"<url><loc>{u}</loc></url>" for u in pages)+"</urlset>\n")
open(f"{OUT}/robots.txt","w").write(f"User-agent: *\nAllow: /\nSitemap: {BASE}{PATH_PREFIX}/sitemap.xml\n")
print(f"Built {len(pages)} pages for {len(tools)} tools -> {OUT}/ (BASE={BASE}{PATH_PREFIX})")
