#!/usr/bin/env python3
"""Long-tail guide pages for LocalProAI.

build.py calls prepare() and emit(). Every listing page is built from
data/tools.json (verticals, use_cases, best_for, pricing, pricing_checked).
A listing page is emitted only when at least three tools match. Pricing text
is copied from those fields. This module does not invent prices, ratings or reviews.
"""
import json
import re
from collections import Counter

MIN_TOOLS = 3

# Phrase must appear in the tool's own best_for text. `vertical` is set when a
# page for that phrase would repeat an existing vertical page.
NICHES = [
    {"slug": "hvac", "phrase": "HVAC", "rx": r"\bhvac\b", "title": "AI tools for HVAC shops", "vertical": None},
    {"slug": "plumbing", "phrase": "plumbing", "rx": r"\bplumbing\b", "title": "AI tools for plumbing shops", "vertical": None},
    {"slug": "electrical", "phrase": "electrical", "rx": r"\belectrical\b", "title": "AI tools for electrical shops", "vertical": None},
    {"slug": "lawn-care", "phrase": "lawn", "rx": r"\blawn\b", "title": "AI tools for lawn care", "vertical": None},
    {"slug": "pest-control", "phrase": "pest control", "rx": r"\bpest control\b", "title": "AI tools for pest control", "vertical": None},
    {"slug": "pool-service", "phrase": "pool", "rx": r"\bpool\b", "title": "AI tools for pool service", "vertical": None},
    {"slug": "barbers", "phrase": "barber", "rx": r"\bbarbers?\b", "title": "AI tools for barbers", "vertical": None},
    {"slug": "medspas", "phrase": "medspa", "rx": r"\bmedspas?\b", "title": "AI tools for medspas", "vertical": None},
    {"slug": "multi-location", "phrase": "multi-location", "rx": r"\bmulti-location\b", "title": "AI tools for multi-location businesses", "vertical": None},
    {"slug": "real-estate", "phrase": "real estate", "rx": r"\breal estate\b", "title": "AI tools for real estate agents", "vertical": None},
    {"slug": "roofing", "phrase": "roofing", "rx": r"\broof(?:ing|ers?)?\b", "title": "AI tools for roofing companies", "vertical": None},
    {"slug": "spas", "phrase": "spa", "rx": r"\bspas?\b", "title": "AI tools for spas", "vertical": None},
    {"slug": "stylists", "phrase": "stylist", "rx": r"\bstylists?\b", "title": "AI tools for stylists", "vertical": None},
    {"slug": "receptionists", "phrase": "receptionist", "rx": r"\breceptionists?\b", "title": "AI receptionist tools", "vertical": None},
    {"slug": "home-service", "phrase": "home service", "rx": r"\bhome service\b", "title": "AI tools for home service businesses", "vertical": None},
    {"slug": "field-service", "phrase": "field service", "rx": r"\bfield service\b", "title": "Field service tools", "vertical": None},
    {"slug": "solo", "phrase": "solo", "rx": r"\bsolo\b", "title": "AI tools for solo operators", "vertical": None},
    {"slug": "salons", "phrase": "salon", "rx": r"\bsalons?\b", "title": "AI tools for salons", "vertical": "salons"},
]

SHORT_JOB = {
    "quotes-estimates": "estimates",
    "scheduling": "scheduling",
    "invoicing-payments": "invoicing",
    "crm": "CRM",
    "phone-answering": "phone answering",
    "reviews": "reviews",
    "listings-marketing": "marketing copy",
    "measurements": "measurements",
    "job-documentation": "job documentation",
    "virtual-staging": "virtual staging",
    "lead-follow-up": "lead follow-up",
    "general-assistant": "AI notes",
    "video": "video",
    "social-media": "social media",
    "website": "websites",
    "local-seo": "local SEO",
    "bookkeeping": "bookkeeping",
    "automation": "automation",
    "website-chat": "website chat",
}

LABEL_ORDER = ["Free option", "Free trial", "Paid", "Quote-based", "See vendor"]
LISTING_KINDS = ("alternatives", "pricing", "comparison", "niche")

_MONTHLY = re.compile(
    r"\$(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?)"
    r"(?:\s*[–—-]\s*\$\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?)?"
    r"(?:\s*/\s*(?:seat|user|person|location|channel|business|calendar))?"
    r"\s*(?:/\s*mo\b|\s*/\s*month\b|\s+per\s+month\b)"
    r"|"
    r"\$(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?)\s+per\s+"
    r"(?:seat|user|person|location|channel|business|calendar)\s*/\s*mo\b",
    re.I,
)


def _norm_money(raw):
    raw = raw.replace(",", "")
    if "." not in raw:
        return str(int(raw))
    whole, frac = raw.split(".", 1)
    frac = (frac + "00")[:2]
    whole = str(int(whole))
    if frac == "00":
        return whole
    return whole + "." + frac


def monthly_fact(pricing):
    """First monthly dollar amount written in a vendor pricing sentence.

    Annual, per-minute and quote-only sentences return basis 'none'. A leading
    free / $0 plan with no monthly dollar amount returns basis 'free'. The
    substring 'no free plan' is not treated as a free plan.
    """
    match = _MONTHLY.search(pricing)
    if match:
        raw = match.group(1) or match.group(2)
        return {"basis": "monthly", "monthly": _norm_money(raw)}
    pl = pricing.lower()
    if pl.startswith("free") or pl.startswith("starter $0"):
        return {"basis": "free", "monthly": "0"}
    return {"basis": "none", "monthly": None}


def _self_check():
    if re.search(r"\bspas?\b", "dispatch plus payments", re.I):
        raise SystemExit("spa regex matched inside another word")
    if not re.search(r"\bspas?\b", "Salons and spas", re.I):
        raise SystemExit("spa regex missed a real spa mention")
    cases = [
        ("Core $49/mo no commitment, $39/mo with 1-year commitment", "monthly", "49"),
        ("Standard $10/seat/mo; Teams $16/seat/mo", "monthly", "10"),
        ("Quote-based (no public price listed)", "none", None),
        ("$0.14/min with $0 platform fee; $0.12/min with $299/mo platform fee", "monthly", "299"),
        ("Paige AI from $99/business/mo", "monthly", "99"),
        ("$129 per business/mo", "monthly", "129"),
        ("Hobbyist $16–$24/person/mo; Creator $24–$35", "monthly", "16"),
        ("Essentials $5/mo per channel", "monthly", "5"),
        ("Pay per project; $999/year plan for discounted pricing", "none", None),
        ("Starter $0; card payments 2.9% + $0.60", "free", "0"),
        ("Free $0/mo; Plus $49/mo; Premium $149/mo", "monthly", "0"),
        ("Free (30 jobs/mo); Starter $29/mo (50 jobs/mo)", "monthly", "29"),
        ("Pro $10/seat/mo annual; Business $19/seat/mo annual", "monthly", "10"),
        ("Paid plans; additional users $29 each (billed annually)", "none", None),
        ("Promo from $1.99/mo (48-mo term), renews $10.99/mo", "monthly", "1.99"),
        ("From $59/mo billed annually; 14-day free trial", "monthly", "59"),
        ("Lite $23/mo regular (promo $4.60/mo for first 4 months)", "monthly", "23"),
        ("promo $4.60/mo for first 4 months", "monthly", "4.60"),
        ("Owner Operator $49.95/mo ($45.95/mo yearly)", "monthly", "49.95"),
        ("Plans $14–$99/mo (credits)", "monthly", "14"),
        ("Quote-based annual enterprise contract (no free plan, trial or per-minute rate)", "none", None),
        ("Free plan; paid from $25/mo", "monthly", "25"),
        ("Pay per image: $7–$10 per Apply Coin; first image free", "none", None),
    ]
    for text, basis, monthly in cases:
        got = monthly_fact(text)
        if got["basis"] != basis or got["monthly"] != monthly:
            raise SystemExit(f"price parse failed for {text!r}: {got} != {(basis, monthly)}")


def _fit_title(*cands, limit=65):
    for title in cands:
        for option in (title, title.rsplit(" | ", 1)[0]):
            if len(option) <= limit:
                return option
    return cands[-1]


def _clip(text, limit=160):
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    return text[: limit - 1].rsplit(" ", 1)[0].rstrip(",;:—-") + "…"


def _join_and(items):
    items = list(items)
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return ", ".join(items[:-1]) + ", and " + items[-1]


def _n_tools(n):
    return f"{n} tool" + ("" if n == 1 else "s")


def _uc_order(UC, keys):
    wanted = set(keys)
    return [u for u in UC if u in wanted]


def _vert_order(VERT, keys):
    wanted = set(keys)
    return [v for v in VERT if v in wanted]


def _vshort(VERT, v):
    return VERT[v].split(" & ")[0]


def _vplural(VERT, v):
    return _vshort(VERT, v).lower()


def _job_mid(UC, u):
    name = UC[u]
    return name if name.isupper() else name.lower()


def _short_job(UC, u):
    return SHORT_JOB.get(u, UC[u].lower())


def _cap(text):
    return text[:1].upper() + text[1:] if text else text


def _shared(UC, VERT, a, b):
    uses = [u for u in UC if u in a["use_cases"] and u in b["use_cases"]]
    verts = [v for v in VERT if v in a["verticals"] and v in b["verticals"]]
    return uses, verts


def _lastmod(ts):
    return max(t["pricing_checked"] for t in ts)


def _year(ts):
    years = {t["pricing_checked"][:4] for t in ts}
    return years.pop() if len(years) == 1 else None


def _tool_icon(UC, tool):
    if tool.get("use_cases"):
        return tool["use_cases"][0]
    return "search"


def _set_icon(UC, VERT, tools):
    if not tools:
        return "search"
    common_v = [v for v in VERT if all(v in t["verticals"] for t in tools)]
    if len(common_v) == 1:
        return common_v[0]
    common_u = set.intersection(*(set(t["use_cases"]) for t in tools))
    for use in UC:
        if use in common_u:
            return use
    return "search"


def _claim_title(candidates, seen, token):
    ordered = []
    for cand in candidates:
        cand = " ".join(cand.split())
        if cand:
            ordered.append(cand)
            short = cand.rsplit(" | ", 1)[0]
            if short != cand:
                ordered.append(short)
    for cand in ordered:
        if len(cand) <= 65 and cand not in seen:
            seen.add(cand)
            return cand
    for cand in ordered:
        if cand not in seen:
            seen.add(cand)
            return cand
    fallback = f"{ordered[-1]} ({token})"
    if fallback in seen:
        raise SystemExit(f"duplicate title: {fallback}")
    seen.add(fallback)
    return fallback


def _claim_desc(raw, seen, token):
    desc = _clip(raw, 160)
    if desc not in seen:
        seen.add(desc)
        return desc
    suffix = f" ({token})"
    desc = _clip(raw, 160 - len(suffix)) + suffix
    if len(desc) > 160:
        desc = desc[:159].rstrip() + "…"
    if desc in seen:
        raise SystemExit(f"duplicate meta description: {token}")
    seen.add(desc)
    return desc


def _skip(skips, code, ident, detail):
    skips.append({"code": code, "id": ident, "detail": detail})


def _niche_matches(tools, niche):
    rx = re.compile(niche["rx"], re.I)
    return [t for t in tools if rx.search(t["best_for"])]


def prepare(tools, UC, VERT, SITE):
    _self_check()
    slugs = [t["slug"] for t in tools]
    if len(slugs) != len(set(slugs)):
        raise SystemExit("duplicate tool slugs in data/tools.json")
    for tool in tools:
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", tool.get("pricing_checked", "")):
            raise SystemExit(f"Bad pricing_checked on {tool['name']}")

    by = {t["slug"]: t for t in tools}
    pages = []
    skips = []
    titles, descs = set(), set()
    vertical_links = {v: {"pricing": [], "comparisons": [], "niches": []} for v in VERT}
    alt_path, alt_count, price_path = {}, {}, {}

    def add(spec):
        if not spec["path"].startswith("/guides/") or spec["path"] in {p["path"] for p in pages}:
            raise SystemExit(f"bad or duplicate guide path {spec['path']}")
        if spec["kind"] in LISTING_KINDS and spec["match_count"] < MIN_TOOLS:
            raise SystemExit(f"{spec['path']} has only {spec['match_count']} matches")
        pages.append(spec)

    # --- alternatives ---
    for tool in tools:
        ranked = []
        for other in tools:
            if other is tool:
                continue
            uses, verts = _shared(UC, VERT, tool, other)
            if uses and verts:
                ranked.append((-len(uses), -len(verts), other["name"].lower(), other, uses, verts))
        ranked.sort()
        if len(ranked) < MIN_TOOLS:
            _skip(skips, "alt-under-3", tool["slug"], f"{len(ranked)} other tools share a vertical and a use case with {tool['name']}")
            continue
        overlap = {}
        ordered = []
        for _, _, _, other, uses, verts in ranked:
            overlap[other["slug"]] = {"uses": uses, "verts": verts}
            ordered.append(other["slug"])
        n = len(ordered)
        verts = _vert_order(VERT, tool["verticals"])
        vert_phrase = _join_and(_vplural(VERT, v) for v in verts)
        closest = by[ordered[0]]
        c_uses = overlap[closest["slug"]]["uses"]
        title = _claim_title(
            [f"{tool['name']} alternatives for {vert_phrase} ({n}) | {SITE}", f"{tool['name']} alternatives ({n}) | {SITE}"],
            titles,
            tool["slug"],
        )
        desc = _claim_desc(
            f"{n} tools overlap {tool['name']} for {vert_phrase}, led by {closest['name']}. The page lists the shared jobs and each vendor pricing sentence.",
            descs,
            tool["slug"] + "-alt",
        )
        path = f"/guides/{tool['slug']}-alternatives/"
        h1 = f"{tool['name']} alternatives"
        lead = f"{_n_tools(n).capitalize()} share a vertical and a use case with {tool['name']}. The closest is {closest['name']}, which also lists {_join_and(_job_mid(UC, u) for u in c_uses)}."
        spec = {
            "kind": "alternatives",
            "path": path,
            "title": title,
            "desc": desc,
            "h1": h1,
            "kicker": f"{n} overlapping tools · {vert_phrase}",
            "lead": lead,
            "icon": _tool_icon(UC, tool),
            "lastmod": _lastmod([tool] + [by[s] for s in ordered]),
            "tool_slugs": [tool["slug"]] + ordered,
            "match_count": n,
            "verticals": verts,
            "subject": tool["slug"],
            "overlap": overlap,
            "link_label": f"{h1} ({n})",
        }
        add(spec)
        alt_path[tool["slug"]] = path
        alt_count[tool["slug"]] = n

    # --- category pricing (one use case × one vertical) ---
    single_price = 0
    for tool in tools:
        single_price += 1
        _skip(skips, "price-single", tool["slug"], f"{tool['name']} pricing would list only that tool, which already has a tool page")
    for vertical in VERT:
        for use in UC:
            group = [t for t in tools if vertical in t["verticals"] and use in t["use_cases"]]
            ident = f"{vertical}/{use}"
            if len(group) < MIN_TOOLS:
                if group:
                    _skip(skips, "price-under-3", ident, f"{len(group)} {_vplural(VERT, vertical)} tools list {UC[use]}")
                continue
            group = sorted(group, key=lambda t: t["name"].lower())
            year = _year(group)
            job = _short_job(UC, use)
            vert = _vplural(VERT, vertical)
            year_bit = f", {year}" if year else ""
            h1 = f"{UC[use]} pricing for {vert}"
            title = _claim_title(
                [
                    f"{_cap(job)} pricing for {vert}{year_bit} | {SITE}",
                    f"{h1}{year_bit} | {SITE}",
                    f"{_cap(job)} pricing for {vert} ({len(group)}) | {SITE}",
                ],
                titles,
                ident,
            )
            names = [t["name"] for t in group[:3]]
            desc = _claim_desc(
                f"Pricing for {_n_tools(len(group))} for {vert} covering {job}, including {_join_and(names)}. The date on each sentence is when it was checked.",
                descs,
                ident,
            )
            path = f"/guides/pricing/{vertical}/{use}/"
            lead = f"{_n_tools(len(group)).capitalize()} for {vert} list {_job_mid(UC, use)}. Includes {_join_and(names)}. The sentences below are copied from vendor pages, with the date each one was checked."
            spec = {
                "kind": "pricing",
                "path": path,
                "title": title,
                "desc": desc,
                "h1": h1,
                "kicker": f"{len(group)} tools · vendor prices" + (f" · {year}" if year else ""),
                "lead": lead,
                "icon": use,
                "lastmod": _lastmod(group),
                "tool_slugs": [t["slug"] for t in group],
                "match_count": len(group),
                "verticals": [vertical],
                "vertical": vertical,
                "use": use,
                "link_label": f"{h1} ({len(group)})",
            }
            add(spec)
            price_path[(vertical, use)] = path
            vertical_links[vertical]["pricing"].append({"path": path, "label": spec["link_label"], "icon": use})

    # --- one comparison page per vertical + two use cases with 3+ tools ---
    ucs = list(UC)
    featured_pairs = set()
    for vertical in VERT:
        for i, left in enumerate(ucs):
            for right in ucs[i + 1 :]:
                group = [t for t in tools if vertical in t["verticals"] and left in t["use_cases"] and right in t["use_cases"]]
                ident = f"{vertical}/{left}+{right}"
                if len(group) < MIN_TOOLS:
                    if group:
                        names = ", ".join(t["name"] for t in sorted(group, key=lambda t: t["name"].lower()))
                        _skip(skips, "jobpair-under-3", ident, f"{len(group)} tools ({names}) list both {UC[left]} and {UC[right]} for {_vplural(VERT, vertical)}")
                    continue
                candidates = []
                for ai, a in enumerate(group):
                    for b in group[ai + 1 :]:
                        uses, verts = _shared(UC, VERT, a, b)
                        n1, n2 = sorted((a["name"].lower(), b["name"].lower()))
                        candidates.append(((-len(uses), -len(verts), n1, n2), a, b, uses))
                candidates.sort(key=lambda row: row[0])
                top = candidates[0][0]
                tier = [row for row in candidates if row[0][0] == top[0] and row[0][1] == top[1]]
                best = next((row for row in tier if frozenset((row[1]["slug"], row[2]["slug"])) not in featured_pairs), tier[0])
                featured_pairs.add(frozenset((best[1]["slug"], best[2]["slug"])))
                pair = tuple(sorted((best[1], best[2]), key=lambda t: t["name"].lower()))
                pair_uses = best[3]
                rest = sorted((t for t in group if t not in pair), key=lambda t: t["name"].lower())
                ordered = list(pair) + rest
                j1, j2 = _short_job(UC, left), _short_job(UC, right)
                vert = _vplural(VERT, vertical)
                h1 = f"{pair[0]['name']} vs {pair[1]['name']}"
                title = _claim_title(
                    [
                        f"{h1}: {j1} & {j2} for {vert} | {SITE}",
                        f"{h1}: {j1} & {j2} | {SITE}",
                        f"{_cap(j1)} and {j2} tools for {vert} ({len(group)}) | {SITE}",
                    ],
                    titles,
                    ident,
                )
                desc = _claim_desc(
                    f"{pair[0]['name']} vs {pair[1]['name']} and {len(group) - 2} other tools for {vert} that list both {j1} and {j2}. Vendor prices are copied from each listing.",
                    descs,
                    ident,
                )
                others = len(group) - 2
                other_word = "1 other tool also lists" if others == 1 else f"{others} other tools also list"
                lead = f"{pair[0]['name']} and {pair[1]['name']} share as many use cases as any pair in this set. {other_word} both {_job_mid(UC, left)} and {_job_mid(UC, right)} for {vert}."
                path = f"/guides/compare/{vertical}/{left}-and-{right}/"
                spec = {
                    "kind": "comparison",
                    "path": path,
                    "title": title,
                    "desc": desc,
                    "h1": h1,
                    "kicker": f"{len(group)} tools for {vert} · {j1} and {j2}",
                    "lead": lead,
                    "icon": left,
                    "lastmod": _lastmod(ordered),
                    "tool_slugs": [t["slug"] for t in ordered],
                    "match_count": len(group),
                    "verticals": [vertical],
                    "vertical": vertical,
                    "uses": [left, right],
                    "pair": [pair[0]["slug"], pair[1]["slug"]],
                    "pair_uses": pair_uses,
                    "link_label": f"{h1}: {j1} and {j2} ({len(group)})",
                }
                add(spec)
                vertical_links[vertical]["comparisons"].append({"path": path, "label": spec["link_label"], "icon": left})

    # Standalone "{A} vs {B}" URLs are not emitted. Count them so the skip report
    # can say why (under 3 tools, or folded into a two-job comparison above).
    for i, left_tool in enumerate(tools):
        for right_tool in tools[i + 1 :]:
            uses, verts = _shared(UC, VERT, left_tool, right_tool)
            if len(uses) < 2 or not verts:
                continue
            cluster = [
                t for t in tools
                if all(u in t["use_cases"] for u in uses) and any(v in t["verticals"] for v in verts)
            ]
            ident = " vs ".join(sorted((left_tool["name"], right_tool["name"]), key=str.lower))
            jobs = _join_and(UC[u] for u in uses)
            if len(cluster) < MIN_TOOLS:
                _skip(skips, "pair-under-3", ident, f"only {len(cluster)} tools include every shared use case ({jobs}), so a two-tool page stays under the minimum")
            else:
                _skip(skips, "pair-folded", ident, f"shared jobs ({jobs}) are already covered by a two-job comparison page with {len(cluster)} tools")

    # --- niches from best_for text ---
    niche_sets = []
    for niche in NICHES:
        matches = _niche_matches(tools, niche)
        niche_sets.append((niche, matches))
        ident = niche["slug"]
        if niche["vertical"] and len(matches) >= MIN_TOOLS:
            _skip(skips, "niche-vertical", ident, f"{len(matches)} listings mention {niche['phrase']}, and the {VERT[niche['vertical']]} page already covers that audience")
            for tool in matches:
                _skip(skips, "tool-niche-vertical", f"{tool['slug']}×{ident}", f"{tool['name']} for {niche['phrase']} repeats the {VERT[niche['vertical']]} vertical page")
            continue
        if len(matches) < MIN_TOOLS:
            names = ", ".join(t["name"] for t in sorted(matches, key=lambda t: t["name"].lower())) or "none"
            word = "listing mentions" if len(matches) == 1 else "listings mention"
            _skip(skips, "niche-under-3", ident, f"{len(matches)} {word} {niche['phrase']} ({names})")
            for tool in matches:
                _skip(skips, "tool-niche-under-3", f"{tool['slug']}×{ident}", f"{tool['name']} mentions {niche['phrase']}, but only {len(matches)} listings do")
            continue
        matches = sorted(matches, key=lambda t: t["name"].lower())
        names = [t["name"] for t in matches]
        h1 = niche["title"]
        title = _claim_title([f"{h1} ({len(matches)}) | {SITE}", f"{h1} | {SITE}"], titles, ident)
        desc = _claim_desc(
            f"{_join_and(names)} mention {niche['phrase']} in their best-for notes. Listings that do not are left off.",
            descs,
            ident,
        )
        common_v = [v for v in VERT if all(v in t["verticals"] for t in matches)]
        where = _join_and(_vplural(VERT, v) for v in common_v) if common_v else _join_and(_vplural(VERT, v) for v in _vert_order(VERT, set().union(*(t["verticals"] for t in matches))))
        lead = f"{_join_and(names)} mention {niche['phrase']} in their best-for notes. Listings that do not mention {niche['phrase']} are left off this page."
        path = f"/guides/for/{niche['slug']}/"
        spec = {
            "kind": "niche",
            "path": path,
            "title": title,
            "desc": desc,
            "h1": h1,
            "kicker": f"{len(matches)} listings mention {niche['phrase']}",
            "lead": lead,
            "icon": _set_icon(UC, VERT, matches),
            "lastmod": _lastmod(matches),
            "tool_slugs": [t["slug"] for t in matches],
            "match_count": len(matches),
            "verticals": common_v or _vert_order(VERT, set().union(*(t["verticals"] for t in matches))),
            "phrase": niche["phrase"],
            "where": where,
            "link_label": f"{h1} ({len(matches)})",
        }
        add(spec)
        for vertical in common_v:
            vertical_links[vertical]["niches"].append({"path": path, "label": spec["link_label"], "icon": spec["icon"]})
        for tool in matches:
            _skip(skips, "tool-niche-merged", f"{tool['slug']}×{ident}", f"{tool['name']} for {niche['phrase']} is listed on {path} with the other {len(matches) - 1} matching listings")

    # Tool × niche pairs the best-for text does not support (prototype assigned these).
    ungrounded = 0
    ungrounded_examples = []
    match_map = {niche["slug"]: {t["slug"] for t in matches} for niche, matches in niche_sets}
    for niche, _matches in niche_sets:
        for tool in tools:
            if tool["slug"] in match_map[niche["slug"]]:
                continue
            ungrounded += 1
            if tool["name"] == "Jobber" and len(ungrounded_examples) < 8:
                ungrounded_examples.append(f"Jobber for {niche['phrase']}")
    _skip(skips, "tool-niche-ungrounded", "best-for", f"{ungrounded} tool/trade pages were not built because that listing's best-for text does not mention the trade")

    # --- calculator + hub ---
    jobs = []
    for vertical in VERT:
        for use in UC:
            group = [t for t in tools if vertical in t["verticals"] and use in t["use_cases"]]
            if len(group) >= MIN_TOOLS:
                jobs.append({
                    "vertical": vertical,
                    "use": use,
                    "slugs": [t["slug"] for t in sorted(group, key=lambda t: t["name"].lower())],
                })
    calc_tools = []
    seen_calc = set()
    for job in jobs:
        for slug in job["slugs"]:
            if slug not in seen_calc:
                seen_calc.add(slug)
                calc_tools.append(by[slug])
    calc_path = "/guides/software-cost/"
    calc_h1 = "Software cost worksheet"
    if jobs:
        calc = {
            "kind": "calculator",
            "path": calc_path,
            "title": _claim_title([f"Software cost worksheet for local businesses | {SITE}"], titles, "calc"),
            "desc": _claim_desc(
                "Add the first monthly dollar amount written in vendor pricing sentences. Annual, per-minute and quote-only plans are not converted.",
                descs,
                "calc",
            ),
            "h1": calc_h1,
            "kicker": "Vendor sentences only",
            "lead": "Choose a vertical and a tool for each job. The total adds the first monthly dollar amount written in each selected pricing sentence. It does not convert annual prices, per-minute rates or quote-only plans.",
            "icon": "tag",
            "lastmod": _lastmod(calc_tools),
            "tool_slugs": [t["slug"] for t in calc_tools],
            "match_count": len(calc_tools),
            "verticals": [v for v in VERT if any(j["vertical"] == v for j in jobs)],
            "jobs": jobs,
            "link_label": calc_h1,
        }
        add(calc)
    else:
        _skip(skips, "calculator-empty", "software-cost", "no vertical and use case has 3 tools to add up")

    counts = Counter(p["kind"] for p in pages)
    worksheet = "plus a cost worksheet" if counts["calculator"] else "no cost worksheet (no job had 3 tools)"
    hub_h1 = "Pricing, alternatives and comparisons"
    hub_lead = (
        f"{counts['alternatives']} alternative pages, {counts['pricing']} pricing pages, "
        f"{counts['comparison']} comparisons and {counts['niche']} trade and audience pages, {worksheet}. "
        f"Each listing page includes at least {MIN_TOOLS} matching tools from this directory."
    )
    hub_tools = [by[s] for s in {s for p in pages for s in p["tool_slugs"]}] or list(tools)
    hub = {
        "kind": "hub",
        "path": "/guides/",
        "title": _claim_title([f"Pricing, alternatives and comparisons | {SITE}"], titles, "hub"),
        "desc": _claim_desc(
            f"Guides from the {SITE} directory: alternatives, vendor pricing, comparisons and trade pages. Each listing page matches at least {MIN_TOOLS} tools.",
            descs,
            "hub",
        ),
        "h1": hub_h1,
        "kicker": f"{len(pages)} guide pages",
        "lead": hub_lead,
        "icon": "search",
        "lastmod": _lastmod(tools),
        "tool_slugs": [t["slug"] for t in hub_tools],
        "match_count": len(hub_tools),
        "verticals": list(VERT),
        "link_label": "All guides",
    }
    add(hub)
    counts = Counter(p["kind"] for p in pages)

    for vertical in vertical_links:
        for key in vertical_links[vertical]:
            vertical_links[vertical][key].sort(key=lambda item: item["label"].lower())

    def pack(code, limit=8):
        rows = [s for s in skips if s["code"] == code]
        return {"count": len(rows), "examples": [{"id": s["id"], "detail": s["detail"]} for s in rows[:limit]]}

    under_codes = ("alt-under-3", "price-under-3", "price-single", "niche-under-3", "jobpair-under-3", "pair-under-3", "tool-niche-under-3")
    folded_codes = ("niche-vertical", "tool-niche-vertical", "tool-niche-merged", "pair-folded")
    report = {
        "published_total": len(pages),
        "published_by_kind": dict(counts),
        "guide_count_excluding_hub": len(pages) - 1,
        "under_3": sum(pack(c)["count"] for c in under_codes),
        "folded": sum(pack(c)["count"] for c in folded_codes),
        "ungrounded_tool_trades": ungrounded,
        "ungrounded_examples": ungrounded_examples,
        "skips": {code: pack(code, 12 if code.endswith("under-3") or code == "niche-vertical" else 6) for code in (
            "alt-under-3", "price-under-3", "price-single", "niche-under-3", "niche-vertical",
            "jobpair-under-3", "pair-under-3", "pair-folded", "tool-niche-under-3",
            "tool-niche-merged", "tool-niche-vertical", "tool-niche-ungrounded",
        )},
        "samples": [],
    }
    # ungrounded pack count is 1 summary row; replace with the real combination count
    report["skips"]["tool-niche-ungrounded"] = {"count": ungrounded, "examples": [{"id": ex, "detail": "best-for text does not mention that trade"} for ex in ungrounded_examples]}
    for kind in ("hub", "calculator", "alternatives", "pricing", "comparison", "niche"):
        for spec in pages:
            if spec["kind"] == kind:
                report["samples"].append({"kind": kind, "path": spec["path"], "title": spec["title"], "h1": spec["h1"]})
                break
    report["published_niches"] = [
        {"path": p["path"], "title": p["title"], "tools": [by[s]["name"] for s in p["tool_slugs"]]}
        for p in pages if p["kind"] == "niche"
    ]
    report["published_comparisons"] = [
        {"path": p["path"], "title": p["title"], "h1": p["h1"], "tools": [by[s]["name"] for s in p["tool_slugs"]]}
        for p in pages if p["kind"] == "comparison"
    ]

    for spec in pages:
        if spec["kind"] in LISTING_KINDS and len(spec["tool_slugs"]) < MIN_TOOLS:
            raise SystemExit(f"{spec['path']} lists fewer than {MIN_TOOLS} tools")
    for job in jobs:
        if len(job["slugs"]) < MIN_TOOLS:
            raise SystemExit("calculator job under the 3-tool minimum")

    return {
        "pages": pages,
        "by": by,
        "vertical_links": vertical_links,
        "alt_path": alt_path,
        "alt_count": alt_count,
        "price_path": price_path,
        "guide_count": len(pages) - 1,
        "report": report,
        "UC": UC,
        "VERT": VERT,
        "SITE": SITE,
    }


def _related(spec, pages):
    if spec["kind"] == "hub":
        return []
    mine = set(spec["tool_slugs"])
    scored = []
    for other in pages:
        if other is spec or other["kind"] in ("hub", "calculator"):
            continue
        share = len(mine & set(other["tool_slugs"]))
        if share == 0 and other["kind"] != spec["kind"]:
            continue
        scored.append((-share, other["kind"] != spec["kind"], other["path"], other))
    scored.sort()
    picked = [row[-1] for row in scored[:6]]
    if len(picked) < 6:
        for other in sorted(pages, key=lambda p: p["path"]):
            if other is spec or other in picked or other["kind"] in ("hub", "calculator"):
                continue
            if spec["kind"] == "calculator" and other["kind"] != "pricing":
                continue
            picked.append(other)
            if len(picked) >= 6:
                break
    return picked


def emit(plan, env):
    UC, VERT = plan["UC"], plan["VERT"]
    by = plan["by"]
    e, link, icon = env["e"], env["link"], env["icon"]
    pages = plan["pages"]

    def tool_link(slug):
        tool = by[slug]
        return f'<a href="{link("/tools/" + slug + "/")}">{e(tool["name"])}</a>'

    def cards(slugs):
        return '<div class="grid">' + "".join(env["card"](by[s]) for s in slugs) + "</div>"

    def tool_rows(slugs, overlap_of=None):
        head = ["Tool"]
        if overlap_of:
            head.append(f"Overlap with {by[overlap_of]['name']}")
        head += ["Best for", "Pricing", "Checked"]
        th = "".join(f'<th scope="col">{e(h)}</th>' for h in head)
        body = []
        subject = by[overlap_of] if overlap_of else None
        spec_overlap = None
        for spec in pages:
            if overlap_of and spec["kind"] == "alternatives" and spec["subject"] == overlap_of:
                spec_overlap = spec["overlap"]
                break
        for slug in slugs:
            tool = by[slug]
            sp = (" " + env["SP"]) if tool.get("sponsored") else ""
            cells = [f'<th scope="row"><a href="{link("/tools/" + slug + "/")}">{e(tool["name"])}</a>{sp}</th>']
            if overlap_of:
                if slug == overlap_of:
                    shared = "Compared listing"
                else:
                    info = spec_overlap[slug]
                    jobs = ", ".join(UC[u] for u in info["uses"])
                    if set(info["verts"]) == set(subject["verticals"]):
                        shared = jobs
                    else:
                        shared = jobs + " (" + ", ".join(_vplural(VERT, v) for v in info["verts"]) + ")"
                cells.append(f'<td data-l="Overlap">{e(shared)}</td>')
            cells.append(f'<td data-l="Best for">{e(tool["best_for"])}</td>')
            cells.append(f'<td data-l="Pricing">{e(tool["pricing"])}</td>')
            cells.append(f'<td data-l="Checked">{e(tool["pricing_checked"])}</td>')
            body.append("<tr>" + "".join(cells) + "</tr>")
        return f'<div class="tbl-wrap"><table class="compare"><thead><tr>{th}</tr></thead><tbody>{"".join(body)}</tbody></table></div>'

    def related_html(spec):
        items = _related(spec, pages)
        if not items:
            return ""
        lis = []
        for item in items:
            lis.append(
                f'<li><a href="{link(item["path"])}">{icon(item["icon"])}<span>{e(item["link_label"])}</span>{icon("arrow", "i arr")}</a></li>'
            )
        return f'<h2 class="sec">Related guides</h2><ul class="guides">{"".join(lis)}</ul>'

    def hero(spec):
        crumb = env["crumbs"](("Guides", link("/guides/")), (spec["h1"], None))
        return env["page_hero"](spec["icon"], e(spec["kicker"]), e(spec["h1"]), e(spec["lead"]), crumb=crumb)

    def write_spec(spec, inner, schema=None):
        body = hero(spec) + f'<div class="wrap">{inner}{related_html(spec)}</div>'
        tools = [by[s] for s in spec["tool_slugs"]]
        if schema is None and spec["kind"] in LISTING_KINDS:
            schema = env["itemlist"](spec["h1"], tools)
        env["write"](spec["path"], spec["title"], spec["desc"], body, schema, lastmod=spec["lastmod"])

    def render_alternatives(spec):
        subject = by[spec["subject"]]
        verts = _join_and(
            f'<a href="{link("/" + v + "/")}">{e(_vplural(VERT, v))}</a>' for v in spec["verticals"]
        )
        jobs = _join_and(e(_job_mid(UC, u)) for u in _uc_order(UC, subject["use_cases"]))
        closest = spec["tool_slugs"][1]
        prose = (
            f"<p>{tool_link(spec['subject'])} is filed under {verts} for {jobs}. "
            f"Best for: {e(subject['best_for'])} "
            f"Vendor pricing: {e(subject['pricing'])} (checked {e(subject['pricing_checked'])}).</p>"
            f"<p>The table is ordered by how many of those use cases each tool shares. "
            f"{tool_link(closest)} is listed first among the tools that share the most. "
            f"A tool is included only when it shares at least one vertical and one use case with {e(subject['name'])}.</p>"
        )
        write_spec(spec, f'<div class="prose">{prose}</div><h2 class="sec">Overlap</h2>{tool_rows(spec["tool_slugs"], spec["subject"])}<h2 class="sec">The tools</h2>{cards(spec["tool_slugs"])}')

    def render_pricing(spec):
        vertical, use = spec["vertical"], spec["use"]
        groups = {label: [] for label in LABEL_ORDER}
        extra = []
        for slug in spec["tool_slugs"]:
            tool = by[slug]
            label, _key = env["price_label"](tool["pricing"])
            if label in groups:
                groups[label].append(slug)
            else:
                extra.append((label, slug))
        blocks = []
        for label in LABEL_ORDER:
            slugs = groups[label]
            if not slugs:
                continue
            panels = []
            for slug in slugs:
                tool = by[slug]
                badge_label, key = env["price_label"](tool["pricing"])
                sp = env["SP"] if tool.get("sponsored") else ""
                panels.append(
                    f'<article class="panel"><div class="card-top"><span class="pbadge pb-{key}">{e(badge_label)}</span>{sp}</div>'
                    f'<h3><a href="{link("/tools/" + slug + "/")}">{e(tool["name"])}</a></h3>'
                    f'<p class="price">{icon("tag")}<span>{e(tool["pricing"])} <small>(checked {e(tool["pricing_checked"])})</small></span></p></article>'
                )
            blocks.append(f'<h2 class="sec">{e(label)}</h2><div class="stack">{"".join(panels)}</div>')
        prose = (
            f"<p>These are the {e(UC[use])} listings filed under "
            f'<a href="{link("/" + vertical + "/")}">{e(_vplural(VERT, vertical))}</a>. '
            f"Groups follow the same Free option, Free trial, Paid, Quote-based and See vendor badges as the directory, "
            f"read from words already in the pricing sentence. They are not a ranking.</p>"
            f'<p>Fit notes for this job are on the <a href="{link("/best/" + vertical + "/" + use + "/")}">best-of page</a> '
            f'and the <a href="{link("/use-cases/" + use + "/")}">{e(UC[use])} use-case page</a>.</p>'
        )
        write_spec(spec, f'<div class="prose">{prose}</div>{"".join(blocks)}')

    def render_comparison(spec):
        vertical = spec["vertical"]
        left, right = spec["uses"]
        a, b = spec["pair"]
        extra = [u for u in spec["pair_uses"] if u not in (left, right)]
        extra_sentence = ""
        if extra:
            extra_sentence = f" They also both list {_join_and(e(_job_mid(UC, u)) for u in extra)}."
        prose = (
            f"<p>{tool_link(a)} and {tool_link(b)} are the first two rows. "
            f"Among tools that list both {e(_job_mid(UC, left))} and {e(_job_mid(UC, right))} for "
            f'<a href="{link("/" + vertical + "/")}">{e(_vplural(VERT, vertical))}</a>, '
            f"this pair shares the most use cases.{extra_sentence}</p>"
            f"<p>{e(by[a]['name'])} is best for {e(by[a]['best_for'])} "
            f"Pricing: {e(by[a]['pricing'])} (checked {e(by[a]['pricing_checked'])}). "
            f"{e(by[b]['name'])} is best for {e(by[b]['best_for'])} "
            f"Pricing: {e(by[b]['pricing'])} (checked {e(by[b]['pricing_checked'])}).</p>"
            f"<p>Single-job guides: "
            f'<a href="{link("/best/" + vertical + "/" + left + "/")}">{e(UC[left])}</a> and '
            f'<a href="{link("/best/" + vertical + "/" + right + "/")}">{e(UC[right])}</a>.</p>'
        )
        write_spec(
            spec,
            f'<div class="prose">{prose}</div><h2 class="sec">All {len(spec["tool_slugs"])} tools with both jobs</h2>{tool_rows(spec["tool_slugs"])}<h2 class="sec">The tools</h2>{cards(spec["tool_slugs"])}',
        )

    def render_niche(spec):
        common_uses = set.intersection(*(set(by[s]["use_cases"]) for s in spec["tool_slugs"]))
        if common_uses:
            share = f"All {len(spec['tool_slugs'])} also list {_join_and(e(_job_mid(UC, u)) for u in _uc_order(UC, common_uses))}."
        else:
            share = "They do not share a single use case. The best-for wording is what they have in common, so read each note before treating them as substitutes."
        quotes = "".join(
            f'<li>{tool_link(s)} <q>{e(by[s]["best_for"])}</q></li>' for s in spec["tool_slugs"]
        )
        where_links = []
        # link verticals that every tool shares; otherwise link each vertical that any tool uses
        common = [v for v in VERT if all(v in by[s]["verticals"] for s in spec["tool_slugs"])]
        targets = common or _vert_order(VERT, set().union(*(by[s]["verticals"] for s in spec["tool_slugs"])))
        for vertical in targets:
            where_links.append(f'<a href="{link("/" + vertical + "/")}">{e(VERT[vertical])}</a>')
        prose = (
            f"<p>Included only when the best-for note itself says {e(spec['phrase'])}. {share} "
            f"Verticals these listings are filed under: {_join_and(where_links)}.</p>"
        )
        write_spec(
            spec,
            f'<div class="prose">{prose}</div><ul class="quote-list">{quotes}</ul><h2 class="sec">Pricing</h2>{tool_rows(spec["tool_slugs"])}<h2 class="sec">The tools</h2>{cards(spec["tool_slugs"])}',
        )

    def render_calculator(spec):
        data = {}
        for slug in spec["tool_slugs"]:
            tool = by[slug]
            fact = monthly_fact(tool["pricing"])
            data[slug] = {
                "name": tool["name"],
                "pricing": tool["pricing"],
                "checked": tool["pricing_checked"],
                "basis": fact["basis"],
                "monthly": fact["monthly"] or "",
            }
        blob = json.dumps(data, ensure_ascii=True).replace("<", "\\u003c")
        verts = spec["verticals"]
        options = "".join(f'<option value="{v}">{e(VERT[v])}</option>' for v in verts)
        sections = []
        for i, vertical in enumerate(verts):
            hidden = "" if i == 0 else " hidden"
            blocks = [f'<div class="calc-vert" data-vertical="{vertical}"{hidden}><h2 class="sec">{e(VERT[vertical])}</h2>']
            for job in spec["jobs"]:
                if job["vertical"] != vertical:
                    continue
                opts = "".join(f'<option value="{s}">{e(by[s]["name"])}</option>' for s in job["slugs"])
                label = f'{_vplural(VERT, vertical)} {UC[job["use"]]}'
                blocks.append(
                    f'<label class="calc-row">{e(UC[job["use"]])}'
                    f'<select aria-label="{e(label)}"><option value="">Skip</option>{opts}</select></label>'
                )
            blocks.append("</div>")
            sections.append("".join(blocks))
        price_links = []
        for item in sorted((p for p in pages if p["kind"] == "pricing"), key=lambda p: p["path"]):
            price_links.append(
                f'<li><a href="{link(item["path"])}">{icon(item["icon"])}<span>{e(item["link_label"])}</span>{icon("arrow", "i arr")}</a></li>'
            )
        prose = (
            "<p>Each job below is shown only when at least three tools in that vertical list it. "
            "The result repeats the vendor pricing sentence. When that sentence contains a monthly dollar amount, "
            "the worksheet adds the first one. A sentence that only says the plan is free is counted as $0. "
            "Per-minute rates, annual prices and quote-only plans stay out of the total.</p>"
        )
        inner = (
            f'<div class="prose">{prose}</div>'
            f'<div id="cost-calc"><label class="calc-row">Vertical'
            f'<select id="calc-vert" aria-label="Vertical">{options}</select></label>'
            f'{"".join(sections)}'
            f'<div class="calc-actions"><button type="button" class="btn" id="calc-go">Add stated monthly figures</button></div>'
            f'<div id="calc-out" aria-live="polite"></div></div>'
            f'<script type="application/json" id="calc-data">{blob}</script>'
            f'<noscript><style>#cost-calc [hidden]{{display:block !important}}</style>'
            f'<p class="prose">Adding the figures needs JavaScript. The pricing guides below list every vendor sentence.</p></noscript>'
            f'<h2 class="sec">Pricing pages</h2><ul class="guides">{"".join(price_links)}</ul>'
        )
        # related_html also adds pricing links; the explicit list above is the full set.
        body = hero(spec) + f'<div class="wrap">{inner}</div>'
        env["write"](spec["path"], spec["title"], spec["desc"], body, None, lastmod=spec["lastmod"])

    def render_hub(spec):
        def guide_items(items):
            lis = []
            for item in items:
                lis.append(
                    f'<li><a href="{link(item["path"])}">{icon(item["icon"])}<span>{e(item["link_label"])}</span>{icon("arrow", "i arr")}</a></li>'
                )
            return f'<ul class="guides">{"".join(lis)}</ul>'

        def bucket(spec_page):
            if len(spec_page["verticals"]) == 1:
                return spec_page["verticals"][0]
            return "*"

        sections = []
        calcs = [p for p in pages if p["kind"] == "calculator"]
        if calcs:
            sections.append(f'<h2 class="sec">Worksheet</h2>{guide_items(calcs)}')
        for vertical in list(VERT) + ["*"]:
            group = [p for p in pages if p["kind"] == "pricing" and bucket(p) == vertical]
            if not group:
                continue
            heading = VERT[vertical] if vertical in VERT else "More than one vertical"
            sections.append(f'<h2 class="sec">{e(heading)} pricing</h2>{guide_items(sorted(group, key=lambda p: p["link_label"].lower()))}')
        comparisons = [p for p in pages if p["kind"] == "comparison"]
        if comparisons:
            sections.append(f'<h2 class="sec">Comparisons</h2>{guide_items(sorted(comparisons, key=lambda p: p["path"]))}')
        niches = [p for p in pages if p["kind"] == "niche"]
        if niches:
            sections.append(f'<h2 class="sec">Trades and audiences</h2>{guide_items(sorted(niches, key=lambda p: p["link_label"].lower()))}')
        for vertical in list(VERT) + ["*"]:
            group = [p for p in pages if p["kind"] == "alternatives" and bucket(p) == vertical]
            if not group:
                continue
            heading = _vplural(VERT, vertical) if vertical in VERT else "more than one vertical"
            sections.append(
                f'<h2 class="sec">Alternatives for {e(heading)}</h2>{guide_items(sorted(group, key=lambda p: p["link_label"].lower()))}'
            )
        prose = (
            f"<p>These pages are rebuilt from the same listings as the directory whenever the site is built. "
            f"A page is published only when at least {MIN_TOOLS} tools match, either on vertical and use-case tags "
            f"or because their best-for notes use the same trade or audience words. "
            f"Pricing text is copied from each listing. Nothing here is a paid ranking.</p>"
        )
        schema = {
            "@context": "https://schema.org",
            "@type": "ItemList",
            "name": spec["h1"],
            "itemListElement": [
                {"@type": "ListItem", "position": i + 1, "name": p["h1"], "url": env["abs_url"](p["path"])}
                for i, p in enumerate(p for p in pages if p["kind"] != "hub")
            ],
        }
        body = hero(spec) + f'<div class="wrap"><div class="prose">{prose}</div>{"".join(sections)}</div>'
        env["write"](spec["path"], spec["title"], spec["desc"], body, schema, lastmod=spec["lastmod"])

    dispatch = {
        "alternatives": render_alternatives,
        "pricing": render_pricing,
        "comparison": render_comparison,
        "niche": render_niche,
        "calculator": render_calculator,
        "hub": render_hub,
    }
    # Hub last so its item list matches pages that were accepted.
    for spec in pages:
        if spec["kind"] != "hub":
            dispatch[spec["kind"]](spec)
    dispatch["hub"](next(p for p in pages if p["kind"] == "hub"))
