#!/usr/bin/env python3
"""
sweep.py - Cross-field consistency checks for the CanadaScanada corpus.

Runs alongside validate.py as a non-blocking sanity sweep. Where validate.py
enforces schema correctness (every field has the right type and references
resolve), sweep.py looks for INTERNAL INCONSISTENCY between fields that
schema validation cannot detect.

The classic pattern this catches: an event whose title and description are
about one subject but whose era, category, actors, or sources are about a
different subject (contamination from a sweep or batch operation).

Usage:  python3 scripts/sweep.py [<data_dir>]
  Default data_dir: . (the repo root)

Exit codes:
  0  No findings, or only findings the operator has already triaged.
  1  Findings exist that warrant operator review.

Output: a list of suspect records grouped by check, with rationale.
"""

import json
import re
import sys
from pathlib import Path


# Era boundaries (Alberta-specific; replace when forking)
ERA_BOUNDARIES = {
    "pre2019": ("0001-01-01", "2019-04-29"),
    "kenney":  ("2019-04-30", "2022-10-10"),
    "smith":   ("2022-10-11", "9999-12-31"),
}

# Keyword bundles for category/description coherence checks.
# Match is case-insensitive, substring-based, not word-boundary.
CATEGORY_KEYWORDS = {
    "healthcare_privatization": [
        "dynalife", "lab privatiz", "ahs ", "alberta health services",
        "private surgical", "private surgery", "private clinic",
        "tylenol", "atabay", "mhcare",
    ],
    "science_suppression": [
        "muzzle", "muzzling", "muzzled", "dfo library",
        "fisheries library", "science minister",
    ],
    "media_suppression": [
        "cbc cut", "cbc fund", "online news act", "bill c-18",
        "press freedom", "journalism cut",
    ],
    "education": [
        "teacher", "school", "ata ", "alberta teachers",
        "curriculum", "post-secondary", "university funding",
    ],
    "labour": [
        "union", "strike", "back-to-work", "labour code",
        "essential service", "collective bargain",
    ],
    "constitutional_override": [
        "notwithstanding", "section 33", "s. 33", "s.33", "override",
    ],
    "energy": [
        "pipeline", "oil sands", "tmx", "trans mountain",
        "renewable", "wind farm", "solar farm",
    ],
    "separatism": [
        "sovereignty act", "alberta independence", "separation referendum",
        "republic of alberta",
    ],
    "lgbtq": [
        "trans youth", "gender identity", "pronoun", "lgbtq",
        "two-spirit", "gender-affirm",
    ],
}

# Common-actor canonical names. Used for "title mentions X but actors[] does not"
# checks. Includes common short references the operator uses in titles.
KNOWN_ACTORS = {
    "kenney":      ["Jason Kenney", "Premier Kenney", "Kenney"],
    "smith":       ["Danielle Smith", "Premier Smith", "Smith"],
    "notley":      ["Rachel Notley", "Notley"],
    "harper":      ["Stephen Harper", "Harper"],
    "shepherd":    ["David Shepherd", "Shepherd"],
    "shandro":     ["Tyler Shandro", "Shandro"],
    "lagrange":    ["Adriana LaGrange", "LaGrange"],
    "nally":       ["Dale Nally", "Nally"],
    "dreeshen":    ["Devin Dreeshen", "Dreeshen"],
    "guthrie":     ["Peter Guthrie", "Guthrie"],
    "trudeau":     ["Justin Trudeau", "Trudeau"],
    "poilievre":   ["Pierre Poilievre", "Poilievre"],
    "carney":      ["Mark Carney", "Carney"],
    "menon":       ["Naheed Menon"],
    "amery":       ["Mickey Amery", "Amery"],
    "lametti":     ["David Lametti", "Lametti"],
}


def load_dir(path):
    out = {}
    if not path.exists():
        return out
    for f in sorted(path.glob("*.json")):
        if f.name.startswith("_") or f.name == "index.json":
            continue
        try:
            out[f.stem] = json.loads(f.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass  # validate.py will catch this
    return out


def get_text(record, *field_names):
    """Pull text from either flat fields or locale-map fields."""
    pieces = []
    for name in field_names:
        v = record.get(name)
        if isinstance(v, str):
            pieces.append(v)
        elif isinstance(v, dict):
            for locale_val in v.values():
                if isinstance(locale_val, str):
                    pieces.append(locale_val)
        # check legacy locale variants too
        for suffix in ("_en", "_fr"):
            v2 = record.get(name + suffix)
            if isinstance(v2, str):
                pieces.append(v2)
    return " ".join(pieces).lower()


def check_era_matches_date(events):
    findings = []
    for eid, ev in events.items():
        date = ev.get("event_date")
        era = ev.get("era")
        if not date or not era:
            continue
        if era not in ERA_BOUNDARIES:
            findings.append((eid, f"era '{era}' not in known boundaries"))
            continue
        lo, hi = ERA_BOUNDARIES[era]
        if not (lo <= date <= hi):
            findings.append((eid,
                f"event_date {date} is outside era '{era}' "
                f"({lo} to {hi}); check for contamination"))
    return findings


def check_title_mentions_actor(events):
    """If the title mentions a known person by surname, that person should
    be in actors[]. Catches the EVT-019 pattern (title about Kenney,
    actors[] says Auditor General)."""
    findings = []
    for eid, ev in events.items():
        title_text = get_text(ev, "title", "title_en")
        if not title_text:
            continue
        actors = ev.get("actors") or []
        actor_names = " ".join(
            (a.get("name") or "") + " " + (a.get("display_role") or "")
            for a in actors if isinstance(a, dict)
        ).lower()
        for key, variants in KNOWN_ACTORS.items():
            # Only check if surname appears in title; first names alone are
            # too noisy ("david" could be anyone).
            surname = variants[0].split()[-1].lower()
            if surname in title_text:
                if not any(v.lower() in actor_names for v in variants):
                    findings.append((eid,
                        f"title mentions '{surname}' but actors[] does not "
                        f"include any variant of {variants[0]}"))
    return findings


def check_category_keyword_consistency(events):
    """If the description contains keywords from a category bundle, that
    category should be in category[]. (Inverse not checked: a category
    can be present without any keyword if framing was deliberately neutral.)"""
    findings = []
    for eid, ev in events.items():
        desc = get_text(ev, "description", "description_en")
        cats = set(ev.get("category") or [])
        for cat, keywords in CATEGORY_KEYWORDS.items():
            if cat in cats:
                continue
            for kw in keywords:
                if kw in desc:
                    findings.append((eid,
                        f"description contains '{kw.strip()}' but "
                        f"category[] does not include '{cat}'"))
                    break  # one keyword hit per category is enough
    return findings


def check_response_date_sanity(events):
    """opposition_response.date should not be earlier than event_date and
    should not be implausibly far after (>3 years)."""
    findings = []
    for eid, ev in events.items():
        resp = ev.get("opposition_response")
        if not isinstance(resp, dict):
            continue
        rdate = resp.get("date")
        edate = ev.get("event_date")
        if not (rdate and edate):
            continue
        if rdate < edate:
            findings.append((eid,
                f"opposition_response.date {rdate} is before "
                f"event_date {edate}"))
        # rough 3-year sanity check (string comparison works for ISO dates)
        if rdate[:4].isdigit() and edate[:4].isdigit():
            year_gap = int(rdate[:4]) - int(edate[:4])
            if year_gap > 3:
                findings.append((eid,
                    f"opposition_response.date {rdate} is more than "
                    f"3 years after event_date {edate}"))
    return findings


def check_unsourced_opposition_response(events):
    """opposition_response should have source_refs. An unsourced response
    is a Bell-rule violation waiting to happen."""
    findings = []
    for eid, ev in events.items():
        resp = ev.get("opposition_response")
        if not isinstance(resp, dict):
            continue
        # An empty response object is fine; a response with content but no
        # sources is not.
        has_content = any(resp.get(k) for k in ("name", "description", "date"))
        srefs = resp.get("source_refs") or []
        if has_content and not srefs:
            findings.append((eid,
                "opposition_response has content but no source_refs; "
                "either source it or drop it"))
    return findings


def check_url_year_vs_event_year(events, refs):
    """Heuristic: if a reference URL contains a 4-digit year and that year
    is more than 18 months off from event_date, flag for review.
    Skips refs whose URLs don't contain a parseable year segment."""
    findings = []
    year_in_url = re.compile(r"/(20\d{2})/")
    for eid, ev in events.items():
        edate = ev.get("event_date")
        if not edate or not edate[:4].isdigit():
            continue
        eyear = int(edate[:4])
        for rid in (ev.get("source_refs") or []):
            ref = refs.get(rid)
            if not isinstance(ref, dict):
                continue
            url = ref.get("url") or ""
            m = year_in_url.search(url)
            if not m:
                continue
            ryear = int(m.group(1))
            if abs(ryear - eyear) > 1:
                findings.append((eid,
                    f"source {rid} URL year {ryear} is more than "
                    f"1 year off from event_date year {eyear}; "
                    f"verify the reference matches the event"))
    return findings


def check_locale_map_invariants(events):
    """For records using the locale-map shape, en-CA should be non-null
    on every translatable field."""
    findings = []
    translatable = ("title", "summary", "description", "body")
    for eid, ev in events.items():
        for field in translatable:
            v = ev.get(field)
            if not isinstance(v, dict):
                continue
            if v.get("en-CA") is None:
                findings.append((eid,
                    f"'{field}' is in locale-map shape but 'en-CA' is null"))
    return findings


def report(label, findings):
    if not findings:
        return 0
    print(f"\n  {label}: {len(findings)} finding(s)")
    for eid, msg in findings:
        print(f"    {eid}: {msg}")
    return len(findings)


def main(data_dir):
    data_dir = Path(data_dir)
    events = load_dir(data_dir / "events")
    refs   = load_dir(data_dir / "references")

    print(f"SWEEP  {data_dir}")
    print(f"  {len(events)} events, {len(refs)} references")

    total = 0
    total += report("era/date consistency",
                    check_era_matches_date(events))
    total += report("title actor in actors[]",
                    check_title_mentions_actor(events))
    total += report("category/keyword consistency",
                    check_category_keyword_consistency(events))
    total += report("opposition_response date sanity",
                    check_response_date_sanity(events))
    total += report("unsourced opposition_response",
                    check_unsourced_opposition_response(events))
    total += report("reference URL year vs event year",
                    check_url_year_vs_event_year(events, refs))
    total += report("locale-map en-CA presence",
                    check_locale_map_invariants(events))

    if total == 0:
        print("\n  CLEAN  no findings")
        return 0
    print(f"\n  {total} finding(s) for operator review")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "."))
