#!/usr/bin/env python3
"""Static site generator for LocalProAI. Usage: BASE=https://example.com python3 build.py"""
import json, os, shutil, html, re
from collections import defaultdict
BASE = os.environ.get("BASE", "https://localproai.example").rstrip("/")
PATH_PREFIX = os.environ.get("PATH_PREFIX", "").rstrip("/")  # e.g. /localai-directory for project Pages
SITE = "LocalProAI"; EMAIL = "d.bot@mail.grokbot.com"; FORM = "https://formspree.io/f/FORM_ID"
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
def write(path, title, desc, body, schema=None):
    url = BASE + PATH_PREFIX + path
    sj = f'<script type="application/ld+json">{json.dumps(schema)}</script>' if schema else ""
    doc = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title><meta name="description" content="{e(desc)}"><link rel="canonical" href="{url}">
<meta property="og:type" content="website"><meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}"><meta property="og:url" content="{url}"><meta property="og:site_name" content="{SITE}">
<link rel="stylesheet" href="{link('/style.css')}">{sj}</head><body>
<header><a class="logo" href="{link('/')}">{SITE}</a><nav>{''.join(f'<a href="{link("/"+k+"/")}">{v}</a>' for k,v in VERT.items())}<a href="{link('/use-cases/')}">Use cases</a><a href="{link('/advertise/')}">Advertise</a><a href="mailto:{EMAIL}?subject=Submit%20a%20tool">Submit a tool</a></nav></header>
<main>{body}</main>
<section class="news"><h2>Get new AI tools for local businesses</h2><form action="{FORM}" method="POST"><input type="email" name="email" placeholder="you@business.com" required aria-label="Email"><button>Subscribe</button></form></section>
<footer>&copy; {SITE} &middot; Curated in Linwood, NJ &middot; Pricing as stated on vendor sites on the date shown; verify before buying. &middot; <a href="mailto:{EMAIL}?subject=Advertise">Advertise</a> &middot; <a href="mailto:{EMAIL}?subject=Submit%20a%20tool">Submit a tool</a></footer>
</body></html>"""
    fp = os.path.join(OUT, path.strip("/"), "index.html") if path.endswith("/") else os.path.join(OUT, path.strip("/"))
    os.makedirs(os.path.dirname(fp), exist_ok=True); open(fp, "w").write(doc); pages.append(url)
def card(t):
    sp = '<span class="sp">Sponsored</span>' if t.get("sponsored") else ""
    tags = " ".join(f'<a class="tag" href="{link("/use-cases/"+u+"/")}">{UC[u]}</a>' for u in t["use_cases"])
    return f'''<article class="card" data-v="{' '.join(t['verticals'])}" data-u="{' '.join(t['use_cases'])}" data-n="{e(t['name'].lower()+' '+t['best_for'].lower())}">{sp}<h3><a href="{link('/tools/'+t['slug']+'/')}">{e(t['name'])}</a></h3><p>{e(t['best_for'])}</p><p class="price">{e(t['pricing'])} <small>(checked {t['pricing_checked']})</small></p><div>{tags}</div></article>'''
def itemlist(name, ts):
    return {"@context":"https://schema.org","@type":"ItemList","name":name,"itemListElement":[{"@type":"ListItem","position":i+1,"url":BASE+PATH_PREFIX+"/tools/"+t["slug"]+"/","name":t["name"]} for i,t in enumerate(ts)]}
def grid(ts): return '<div class="grid">'+"".join(card(t) for t in sorted(ts, key=lambda t:(not t.get("sponsored"), t["name"].lower())))+"</div>"
if os.path.exists(OUT): shutil.rmtree(OUT)
os.makedirs(OUT)
shutil.copy("static/style.css", OUT); shutil.copy("static/app.js", OUT)
open(os.path.join(OUT, ".nojekyll"), "w").close()
# home
opts = lambda d: "".join(f'<option value="{k}">{v}</option>' for k,v in d.items())
write("/", f"{SITE} — AI Tools for Contractors, Realtors & Salons", f"A curated directory of {len(tools)} AI tools for local service businesses, with vendor-stated pricing and honest notes.",
 f'''<h1>AI tools for local service businesses</h1><p>{len(tools)} tools, hand-checked against vendor sites. No paid placements without a <span class="sp">Sponsored</span> label.</p>
<div class="slot"><span class="sp">Sponsored</span> Homepage feature available — <a href="{link('/advertise/')}">advertise here</a>.</div>
<div class="filters"><input id="q" placeholder="Search tools…" aria-label="Search"><select id="fv"><option value="">All verticals</option>{opts(VERT)}</select><select id="fu"><option value="">All use cases</option>{opts(UC)}</select></div>
{grid(tools)}<script src="{link('/app.js')}"></script>''', itemlist("All AI tools", tools))
# verticals, use cases, combos
for v, vn in VERT.items():
    ts = [t for t in tools if v in t["verticals"]]
    combos = [(u, un) for u, un in UC.items() if len([t for t in ts if u in t["use_cases"]]) >= 3]
    cl = "".join(f'<li><a href="{link(f"/best/{v}/{u}/")}">Best AI {un.lower()} tools for {vn.lower()}</a></li>' for u, un in combos)
    write(f"/{v}/", f"AI Tools for {vn} ({len(ts)} picks) | {SITE}", f"{len(ts)} AI tools for {vn.lower()}: quoting, scheduling, phone answering, marketing and more, with pricing checked on vendor sites.",
      f'<h1>AI tools for {vn}</h1><div class="slot"><span class="sp">Sponsored</span> Featured slot for {vn} — <a href="{link("/advertise/")}">$49/mo</a></div><h2>Best-of guides</h2><ul>{cl}</ul>{grid(ts)}', itemlist(f"AI tools for {vn}", ts))
    for u, un in combos:
        cs = [t for t in ts if u in t["use_cases"]]
        write(f"/best/{v}/{u}/", f"Best AI Tools for {vn} {un} ({len(cs)}) | {SITE}", f"The best AI {un.lower()} tools for {vn.lower()}: {', '.join(t['name'] for t in cs[:4])} and more, with pricing and honest notes.",
          f'<p><a href="{link("/"+v+"/")}">{vn}</a> › {un}</p><h1>Best AI tools for {vn} {un}</h1>{grid(cs)}', itemlist(f"Best AI tools for {vn} {un}", cs))
idx = ""
for u, un in UC.items():
    ts = [t for t in tools if u in t["use_cases"]]
    if not ts: continue
    idx += f'<li><a href="{link("/use-cases/"+u+"/")}">{un}</a> ({len(ts)})</li>'
    write(f"/use-cases/{u}/", f"AI {un} Tools for Local Businesses | {SITE}", f"{len(ts)} AI {un.lower()} tools for contractors, realtors and salons, with vendor-stated pricing.",
      f'<h1>AI {un} tools</h1>{grid(ts)}', itemlist(f"AI {un} tools", ts))
write("/use-cases/", f"AI Tools by Use Case | {SITE}", "Browse AI tools for local service businesses by job: quotes, scheduling, reviews, phone answering, bookkeeping and more.", f"<h1>Browse by use case</h1><ul>{idx}</ul>")
for t in tools:
    vs = ", ".join(f'<a href="{link("/"+v+"/")}">{VERT[v]}</a>' for v in t["verticals"])
    write(f"/tools/{t['slug']}/", f"{t['name']}: Pricing & Review for Local Businesses | {SITE}", f"{t['name']} — {t['best_for']} Pricing: {t['pricing']}"[:300],
      f'''{'<span class="sp">Sponsored</span>' if t.get('sponsored') else ''}<h1>{e(t['name'])}</h1><p><strong>Best for:</strong> {e(t['best_for'])}</p>
<p><strong>Pricing:</strong> {e(t['pricing'])} <small>(as stated on vendor site, checked {t['pricing_checked']})</small></p><p><strong>Verticals:</strong> {vs}</p>
<p>{" ".join(f'<a class="tag" href="{link("/use-cases/"+u+"/")}">{UC[u]}</a>' for u in t["use_cases"])}</p>
<p><a class="btn" href="{e(t['url'])}" rel="nofollow noopener" target="_blank">Visit {e(t['name'])}</a></p><p><small>Source: <a href="{e(t['source_url'])}" rel="nofollow">{e(t['source_url'])}</a></small></p>
<p><small>Are you the vendor? <a href="mailto:{EMAIL}?subject=Claim%20listing:%20{e(t['name'])}">Claim this free listing</a>.</small></p>''',
      {"@context":"https://schema.org","@type":"SoftwareApplication","name":t["name"],"url":t["url"],"applicationCategory":"BusinessApplication","description":t["best_for"]})
write("/advertise/", f"Advertise on {SITE} — Sponsored Listings", "Reach contractors, realtors and salon owners shopping for AI tools. Featured vertical and homepage placements, plus free claimable listings.",
 f'''<h1>Advertise on {SITE}</h1><p>Draft pricing — all paid placements are clearly labeled <span class="sp">Sponsored</span>.</p>
<table><tr><th>Placement</th><th>Price</th></tr><tr><td>Basic listing (claim & update your info)</td><td>Free</td></tr><tr><td>Featured in one vertical (top of vertical page + card badge)</td><td>$49/mo</td></tr><tr><td>Homepage feature</td><td>$149/mo</td></tr></table>
<p>Sponsorship never changes our "best for" notes or pricing info.</p><p><a class="btn" href="mailto:{EMAIL}?subject=Advertise%20on%20{SITE}">Email us to advertise</a></p>''')
open(f"{OUT}/sitemap.xml","w").write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+"".join(f"<url><loc>{u}</loc></url>" for u in pages)+"</urlset>\n")
open(f"{OUT}/robots.txt","w").write(f"User-agent: *\nAllow: /\nSitemap: {BASE}{PATH_PREFIX}/sitemap.xml\n")
print(f"Built {len(pages)} pages for {len(tools)} tools -> {OUT}/ (BASE={BASE}{PATH_PREFIX})")
