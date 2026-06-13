#!/usr/bin/env python3
"""
build.py — CanadaScanada pre-render pipeline
════════════════════════════════════════════
Usage:  python3 scripts/build.py <data_dir> [<out_dir>]

  data_dir  root of the canadascanada-data repo  (default: ".")
  out_dir   where to write the static site        (default: "./docs")

Reads events/, references/, outlets/, meta/ from data_dir.
Writes index.html, outlets/*.html into out_dir.
Also writes events/index.json and outlets/index.json for CanScan lookup.

Run after validate.py passes.  The GitHub Action does this automatically.
"""

import datetime
import html as _html
import json
import os
import sys
from pathlib import Path


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def e(s):
    """HTML-escape any value. Safe to call on None."""
    return _html.escape(str(s)) if s is not None else ""


def load_dir(path):
    """Load all *.json files in a directory into a dict keyed by record id.
    Skips index.json (generated file)."""
    records = {}
    p = Path(path)
    if not p.exists():
        return records
    for f in sorted(p.glob("*.json")):
        if f.name == "index.json":
            continue
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            rid = data.get("id", f.stem)
            records[rid] = data
        except (json.JSONDecodeError, OSError) as ex:
            print(f"  WARNING: skipping {f}: {ex}", file=sys.stderr)
    return records


def load_outlet_db(data_dir):
    """Load outlets as {outlet_id: record}, in display order, from per-file
    outlets/records/*.json (skip _*.json). Field names are v3-only.

    Display order: outlets/records/_manifest.json may carry "order": [ids...].
    Ids in that list come first in listed order; any id not listed falls back
    to alphabetical."""
    rec_dir = Path(data_dir) / "outlets" / "records"
    items = []
    if not (rec_dir.is_dir() and any(
        f.suffix == ".json" and not f.name.startswith("_") for f in rec_dir.iterdir()
    )):
        print(f"  WARNING: no outlets/records/ found at {rec_dir}", file=sys.stderr)
        return {}
    for f in sorted(rec_dir.glob("*.json")):
        if f.name.startswith("_"):
            continue
        items.append(json.loads(f.read_text(encoding="utf-8")))
    order = []
    manifest = rec_dir / "_manifest.json"
    if manifest.exists():
        try:
            order = (json.loads(manifest.read_text(encoding="utf-8")) or {}).get("order", [])
        except Exception:
            order = []
    if order:
        pos = {oid: i for i, oid in enumerate(order)}
        items.sort(key=lambda o: (pos.get(o.get("outlet_id"), len(pos)),
                                  o.get("outlet_id", "")))
    return {o["outlet_id"]: o for o in items if isinstance(o, dict) and "outlet_id" in o}


def derive_ownership_split(o):
    """Return (canadian_pct, foreign_pct) as integers.

    Uses ownership_pct_canadian_derived if present; otherwise sums
    country=="CA" entries in ownership_breakdown.
    """
    val = o.get("ownership_pct_canadian_derived")
    if val is not None:
        cdn = int(val)
        return cdn, 100 - cdn
    breakdown = o.get("ownership_breakdown") or []
    if breakdown:
        cdn = sum(
            int(entry.get("percentage", 0))
            for entry in breakdown
            if entry.get("country", "") == "CA"
        )
        cdn = min(max(cdn, 0), 100)
        return cdn, 100 - cdn
    # ownership not yet assessed (e.g. outlets pending a CanScan rating)
    return None, None


# ══════════════════════════════════════════════════════════════════════════════
# PUBLICATION GATE
# ══════════════════════════════════════════════════════════════════════════════

def is_publishable(ev, refs_dict):
    """Return True only if the event passes all publication criteria.

    Gate (DATA_STRUCTURE_v3.md §9):
      - needs_verification must be false / absent
      - evidence_status must not be "superseded"
      - source_refs must be non-empty
      - every referenced source must have verified == true
      - if claim_type == "inference", inference_note must be present

    Unverified, stub, and superseded records stay in the repo (provenance)
    but never reach readers.
    """
    if ev.get("needs_verification"):
        return False
    if ev.get("evidence_status") == "superseded":
        return False
    source_refs = ev.get("source_refs") or []
    if not source_refs:
        return False
    for rid in source_refs:
        ref = refs_dict.get(rid)
        if ref is None:
            return False     # dangling ref — don't publish
        if not ref.get("verified"):
            return False
    if ev.get("claim_type") == "inference" and not ev.get("inference_note"):
        return False
    return True


# ══════════════════════════════════════════════════════════════════════════════
# VOCABULARY MAPS  —  update here; nowhere else
# ══════════════════════════════════════════════════════════════════════════════

OUTLET_TYPE_LABELS = {
    "public_broadcaster":          "Public broadcaster",
    "daily_print_digital":         "Daily print & digital",
    "broadcast_tv":                "Broadcast television",
    "digital_native":              "Digital native",
    "wire_service":                "Wire service",
    "advocacy_research":           "Advocacy / research",
    "foreign_operating_in_canada": "International outlet operating in Canada",
    "independent_digital":         "Independent digital",
    "government_institution":      "Government institution",
}

FACT_LABELS = {
    "corrections_policy_published": "Corrections policy",
    "editorial_standards_published": "Editorial standards",
}

# Default: "verified" — the publication gate already guarantees sourcing.
# "pending" and "false" are scaffolded for future use.
STATUS_MAP = {
    "verified": ("status-verified", "Verified"),
    "pending":  ("status-pending",  "Not yet verified"),
    "false":    ("status-false",    "Verified false"),
}

# ── Relations graph (Standard §5.4) ───────────────────────────────────────────
# Reader-facing label per edge type. Symmetric types read the same both ways;
# directional types flip to their inverse on the derived (inbound) side.
RELATION_LABELS = {
    "part_of_thread":             "Thread",
    "enables":                    "Enables",
    "enabled_by":                 "Enabled by",
    "responds_to":                "Responds to",
    "prompted":                   "Prompted",
    "conflicts_with":             "Discrepancy",   # reader noun, both directions
    "jurisdiction_clarification": "Jurisdiction",
    "same_actor":                 "Same actor",
    "same_legislation":           "Same legislation",
    "financial_link":             "Financial link",
    "supersedes":                 "Supersedes",
    "superseded_by":              "Superseded by",
}

# Forward type → inverse type used when deriving the edge on the TARGET event.
# Symmetric types map to themselves; part_of_thread has no event inverse.
RELATION_INVERSE = {
    "enables":                    "enabled_by",
    "enabled_by":                 "enables",
    "responds_to":                "prompted",
    "prompted":                   "responds_to",
    "supersedes":                 "superseded_by",
    "superseded_by":              "supersedes",
    "conflicts_with":             "conflicts_with",
    "jurisdiction_clarification": "jurisdiction_clarification",
    "same_actor":                 "same_actor",
    "same_legislation":           "same_legislation",
    "financial_link":             "financial_link",
}

# Dedupe key: both members of a directional pair share one family, so an edge
# stored on the lower-id event is never rendered twice if both sides carry it.
RELATION_FAMILY = {
    "enables": "enable", "enabled_by": "enable",
    "responds_to": "respond", "prompted": "respond",
    "supersedes": "supersede", "superseded_by": "supersede",
    "conflicts_with": "conflict",
    "jurisdiction_clarification": "jurisdiction",
    "same_actor": "same_actor",
    "same_legislation": "same_legislation",
    "financial_link": "financial_link",
}

# Causal-edge `note` fields currently hold migration cruft, not reader prose.
# Keep False until notes are swept to reader-facing text (Standard §12, sweep).
RENDER_CAUSAL_NOTES = False


# ══════════════════════════════════════════════════════════════════════════════
# COMBINED CSS
# Concatenated into page_shell() via string addition — never put inside an
# f-string, so CSS curly braces need no escaping.
# Class names here are the contract with the render functions below.
# ══════════════════════════════════════════════════════════════════════════════

_CSS = """\
/* ════════════════════════════════════════════════════════════════════
   CANSCAN  ·  Combined stylesheet  ·  v4  ·  Thread 3 build
   Source: wireframe_timeline_v4.html (Sections 1–8) +
           canscan_label_v4.html CSS, tokenised + scoped under .csl.

   HOW TO MODIFY SAFELY
   ─────────────────────
   Colours, type, spacing     →  SECTION 1 tokens only.
   Label colours / type       →  --csl-* tokens at end of SECTION 1.
   New status variant         →  one .status-xxx rule in SECTION 5.
   New annotation type        →  one .annotation.xxx rule in SECTION 6.
   Disable scroll animation   →  remove SECTION 8.
   Change page width          →  --cs-page-width in SECTION 1.

   DO NOT edit values outside SECTION 1 unless changing structure.
   Class names are the contract with build.py render functions.
   ════════════════════════════════════════════════════════════════════ */


/* ─────────────────────────────────────────────────────────────────────
   SECTION 1 — TOKENS
   ───────────────────────────────────────────────────────────────────── */
:root {
  --cs-ink:              #002B5C;
  --cs-ink-soft:         #5a6675;
  --cs-bg-page:          #F4F1EC;
  --cs-bg-card:          #ffffff;
  --cs-border:           #ddd7ca;
  --cs-accent:           #C8102E;
  --cs-verified:         #1B7A34;
  --cs-pending:          #8a5a00;
  --cs-false:            #C8102E;
  --cs-inference-ink:    #8a5a00;
  --cs-inference-bg:     #fcf6ea;
  --cs-font:             "Helvetica Neue", Arial, sans-serif;
  --cs-size-h1:          22px;
  --cs-size-title:       16px;
  --cs-size-body:        14px;
  --cs-size-meta:        11px;
  --cs-size-chip:        10px;
  --cs-card-pad:         18px;
  --cs-card-gap:         14px;
  --cs-page-width:       760px;
  --cs-radius:           4px;
  --cs-spine-offset:     22px;
  /* Label (.csl) tokens — reuses --cs-ink, --cs-font, --cs-bg-card */
  --csl-width:           300px;
  --csl-border:          2.5px;
  --csl-rule-thick:      7px;
  --csl-rule-1pt:        1px;
  --csl-rule-thin:       0.5px;
  --csl-pad:             9px;
  --csl-indent-1:        9px;
  --csl-indent-2:        18px;
  --csl-gap-cols:        8px;
  --csl-size-name:       20px;
  --csl-size-desc:       8.5px;
  --csl-size-hero-lbl:   10px;
  --csl-size-hero-num:   26px;
  --csl-size-fact:       9px;
  --csl-size-sub:        8px;
  --csl-size-addl:       9px;
  --csl-size-foot:       8px;
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: var(--cs-font);
  background: var(--cs-bg-page);
  color: var(--cs-ink);
  line-height: 1.5;
}

/* Accessibility: visible keyboard focus on every interactive element.
   The solid ink outline is the guaranteed indicator (5.85:1, never clipped);
   the translucent accent halo softens it visually. If color-mix is
   unsupported the halo simply drops and the compliant outline remains. */
a:focus-visible, summary:focus-visible, button:focus-visible,
[tabindex]:focus-visible {
  outline: 2px solid var(--cs-ink-soft);
  outline-offset: 2px;
  box-shadow: 0 0 0 5px color-mix(in srgb, var(--cs-accent) 16%, transparent);
  border-radius: 3px;
}

/* Skip link — offscreen until focused, then pinned top-left. */
.skip-link {
  position: absolute; left: 8px; top: -48px; z-index: 1000;
  background: var(--cs-bg-card); color: var(--cs-ink);
  border: 1px solid var(--cs-border); border-radius: var(--cs-radius);
  padding: 8px 14px; font-size: var(--cs-size-body); font-weight: 700;
  text-decoration: none; transition: top 0.15s ease;
}
.skip-link:focus { top: 8px; }


/* ─────────────────────────────────────────────────────────────────────
   SECTION 2 — PAGE SHELL
   ───────────────────────────────────────────────────────────────────── */
.site-header { border-bottom: 1px solid var(--cs-border); background: var(--cs-bg-card); }
.site-header .inner, .site-footer .inner {
  max-width: var(--cs-page-width); margin: 0 auto; padding: 14px 20px;
}
.site-header .inner {
  display: flex; align-items: baseline; justify-content: space-between;
  flex-wrap: wrap; gap: 8px;
}
.wordmark {
  font-size: 18px; font-weight: 700; letter-spacing: -0.3px;
  color: var(--cs-ink); text-decoration: none;
}
.wordmark .scanada { color: var(--cs-accent); }
.site-nav { display: flex; gap: 18px; font-size: var(--cs-size-meta);
  text-transform: uppercase; letter-spacing: 0.5px; }
.site-nav a { color: var(--cs-ink-soft); text-decoration: none; padding-bottom: 2px; }
.site-nav a.active { color: var(--cs-ink); border-bottom: 2px solid var(--cs-accent); }
main { max-width: var(--cs-page-width); margin: 0 auto; padding: 24px 20px 48px; }
.page-h1 { font-size: var(--cs-size-h1); font-weight: 700; margin-bottom: 4px; }
.page-intro {
  font-size: var(--cs-size-body); color: var(--cs-ink-soft);
  margin-bottom: 24px; max-width: 60ch;
}
.site-footer { border-top: 1px solid var(--cs-border); background: var(--cs-bg-card); }
.site-footer .inner {
  font-size: var(--cs-size-meta); color: var(--cs-ink-soft);
  line-height: 1.7; padding-bottom: 28px;
}
.site-footer a { color: var(--cs-ink); }
.foot-links { margin-bottom: 6px; display: flex; gap: 14px; flex-wrap: wrap; }


/* ─────────────────────────────────────────────────────────────────────
   SECTION 3 — CARD STRUCTURE
   ───────────────────────────────────────────────────────────────────── */
.timeline { position: relative; padding-left: var(--cs-spine-offset); border-left: 2px solid var(--cs-border); }
details.card {
  position: relative; background: var(--cs-bg-card);
  border: 1px solid var(--cs-border); border-radius: var(--cs-radius);
  margin-bottom: var(--cs-card-gap);
}
details.card::before {
  content: ""; position: absolute;
  left: calc(-1 * var(--cs-spine-offset) - 3px); top: 20px;
  width: 9px; height: 9px; border-radius: 50%;
  background: var(--cs-bg-page); border: 2px solid var(--cs-accent);
}
details[open].card { border-left: 2.5px solid var(--cs-ink); }
.card-summary {
  display: block; list-style: none; cursor: pointer;
  padding: var(--cs-card-pad);
  padding-right: calc(var(--cs-card-pad) + 22px);
  position: relative; -webkit-user-select: none; user-select: none;
}
.card-summary::-webkit-details-marker { display: none; }
.card-summary::after {
  content: "+"; position: absolute; top: var(--cs-card-pad); right: var(--cs-card-pad);
  font-size: 18px; font-weight: 300; color: var(--cs-ink-soft); line-height: 1;
}
details[open] > .card-summary::after { content: "\2212"; }
.card-body-area {
  padding: 0 var(--cs-card-pad) var(--cs-card-pad);
  border-top: 0.5px solid var(--cs-border); padding-top: 14px;
}


/* ─────────────────────────────────────────────────────────────────────
   SECTION 4 — CARD CONTENT
   ───────────────────────────────────────────────────────────────────── */
.card-top {
  display: flex; justify-content: space-between; align-items: baseline;
  gap: 12px; margin-bottom: 5px;
}
.card-date {
  font-size: var(--cs-size-meta); font-weight: 700; letter-spacing: 0.3px;
  color: var(--cs-ink-soft); text-transform: uppercase;
}
.card-title { font-size: var(--cs-size-title); font-weight: 700; color: var(--cs-ink); line-height: 1.3; padding-right: 4px; }
.card-body { font-size: var(--cs-size-body); color: var(--cs-ink); margin-bottom: 12px; line-height: 1.6; }
.hero-quote {
  border-left: 2px solid var(--cs-ink); padding: 6px 0 6px 12px; margin: 0 0 12px;
  font-style: italic; font-size: var(--cs-size-body); color: var(--cs-ink); line-height: 1.6;
}
.hero-quote p { margin-bottom: 4px; }
.hero-quote cite { font-style: normal; font-size: var(--cs-size-meta); font-weight: 700; color: var(--cs-ink-soft); }


/* ─────────────────────────────────────────────────────────────────────
   SECTION 5 — STATUS VARIANTS
   To add a new status: one .status-xxx rule. Nothing else.
   ───────────────────────────────────────────────────────────────────── */
.status {
  display: inline-flex; align-items: center; gap: 5px;
  font-size: var(--cs-size-meta); font-weight: 700;
  text-transform: uppercase; letter-spacing: 0.4px; white-space: nowrap;
}
.status::before { content: ""; width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.status-verified          { color: var(--cs-verified); }
.status-verified::before  { background: var(--cs-verified); }
.status-pending           { color: var(--cs-pending); }
.status-pending::before   { background: transparent; border: 1.5px solid var(--cs-pending); }
.status-false             { color: var(--cs-false); }
.status-false::before     { background: var(--cs-false); }


/* ─────────────────────────────────────────────────────────────────────
   SECTION 6 — ANNOTATION VARIANTS
   To add a type: one .annotation.xxx rule. Nothing else.
   ───────────────────────────────────────────────────────────────────── */
.annotation {
  font-size: var(--cs-size-body); border-left: 2px solid var(--cs-border);
  padding: 6px 12px; margin-bottom: 12px; color: var(--cs-ink); line-height: 1.5;
}
.annotation .annotation-label {
  display: block; font-size: var(--cs-size-meta); font-weight: 700;
  text-transform: uppercase; letter-spacing: 0.5px; color: var(--cs-ink-soft); margin-bottom: 3px;
}
.annotation.inference { border-left-color: var(--cs-inference-ink); background: var(--cs-inference-bg); }
.annotation.inference .annotation-label { color: var(--cs-inference-ink); }

/* Connections block (Standard §9) — uniform across edge types by design:
   no per-type colour or affordance, so a discrepancy reads no louder than a
   thread link. Edit spacing/width here; do not add type-specific variants. */
.annotation.connections { border-left-color: var(--cs-ink-soft); }
.connection-row { display: flex; gap: 10px; align-items: baseline; padding: 5px 0; }
.connection-row + .connection-row { border-top: 0.5px solid var(--cs-border); }
.connection-type {
  flex-shrink: 0; width: 104px;
  font-size: var(--cs-size-meta); font-weight: 700;
  text-transform: uppercase; letter-spacing: 0.4px; color: var(--cs-ink-soft);
}
.connection-detail { font-size: var(--cs-size-body); color: var(--cs-ink); line-height: 1.5; }
.connection-detail a { color: var(--cs-ink); text-decoration: underline; text-underline-offset: 2px; display: inline-block; padding: 3px 0; }
.connection-thread { font-weight: 700; }
.connection-framing { font-size: var(--cs-size-meta); color: var(--cs-ink-soft); margin-top: 2px; line-height: 1.5; }
.connection-disc { font-style: italic; }


/* ─────────────────────────────────────────────────────────────────────
   SECTION 7 — DETAILS EXPANSION  (sources + tags)
   ───────────────────────────────────────────────────────────────────── */
.card-details { margin-top: 4px; border-top: 0.5px solid var(--cs-border); padding-top: 8px; }
.card-details > summary {
  cursor: pointer; list-style: none; font-size: var(--cs-size-meta); font-weight: 700;
  text-transform: uppercase; letter-spacing: 0.4px; color: var(--cs-ink-soft);
}
.card-details > summary::-webkit-details-marker { display: none; }
.card-details > summary::before { content: "+ "; }
.card-details[open] > summary::before { content: "\2013 "; }
.detail-sources { margin: 10px 0; }
.detail-sources p { font-size: var(--cs-size-meta); color: var(--cs-ink-soft); line-height: 1.9; }
.detail-sources a { color: var(--cs-ink); text-decoration: underline; text-underline-offset: 2px; }
.detail-sources .src-pub { font-weight: 700; }
.chips-label {
  display: block; font-size: var(--cs-size-meta); font-weight: 700;
  text-transform: uppercase; letter-spacing: 0.4px; color: var(--cs-ink-soft); margin: 10px 0 6px;
}
.card-chips { display: flex; flex-wrap: wrap; gap: 5px; }
.chip {
  font-size: var(--cs-size-chip); text-transform: uppercase; letter-spacing: 0.4px;
  padding: 2px 7px; border-radius: 999px; border: 1px solid var(--cs-border); color: var(--cs-ink-soft);
}


/* ─────────────────────────────────────────────────────────────────────
   SECTION 8 — SCROLL ANIMATION
   Remove this entire block to disable. Nothing else breaks.
   ───────────────────────────────────────────────────────────────────── */
@media (prefers-reduced-motion: no-preference) {
  details.card {
    animation: card-reveal linear both;
    animation-timeline: view();
    animation-range: entry 0% entry 35%;
  }
  @keyframes card-reveal {
    from { opacity: 0; transform: translateY(12px); }
    to   { opacity: 1; transform: translateY(0); }
  }
}


/* ─────────────────────────────────────────────────────────────────────
   SECTION 9 — CANSCAN LABEL  (.csl scope)
   All rules scoped under .csl — no conflicts with the timeline.
   To restyle: edit --csl-* tokens in SECTION 1. Nothing else.
   ───────────────────────────────────────────────────────────────────── */
.csl {
  width: var(--csl-width); border: var(--csl-border) solid var(--cs-ink);
  background: var(--cs-bg-card); color: var(--cs-ink); font-family: var(--cs-font);
}
.csl .r-thin  { border-top: var(--csl-rule-thin)  solid var(--cs-ink); }
.csl .r-1pt   { border-top: var(--csl-rule-1pt)   solid var(--cs-ink); }
.csl .r-thick { border-top: var(--csl-rule-thick)  solid var(--cs-ink); }
.csl .head { padding: 6px var(--csl-pad) 5px; }
.csl .outlet-name { font-size: var(--csl-size-name); font-weight: 700; line-height: 1.1; color: var(--cs-ink); letter-spacing: -0.2px; }
.csl .descriptor { padding: 3px var(--csl-pad) 5px; font-size: var(--csl-size-desc); font-weight: 400; color: var(--cs-ink); line-height: 1.4; }
.csl .hero { padding: 5px var(--csl-pad); }
.csl .h-label { display: block; font-size: var(--csl-size-hero-lbl); font-weight: 700; color: var(--cs-ink); line-height: 1; }
.csl .h-pct { display: block; font-size: var(--csl-size-hero-num); font-weight: 700; color: var(--cs-ink); line-height: 1; margin-top: 3px; }
.csl .own-section { padding: 4px var(--csl-pad) 6px; }
.csl .own-row {
  display: flex; justify-content: space-between; align-items: baseline;
  font-size: var(--csl-size-sub); font-weight: 400;
  padding: 1.5px 0 1.5px var(--csl-indent-1); gap: var(--csl-gap-cols); color: var(--cs-ink);
}
.csl .own-row .own-pct { flex-shrink: 0; font-weight: 700; }
.csl .fact-row {
  display: flex; justify-content: space-between; align-items: center;
  padding: 3px var(--csl-pad); gap: var(--csl-gap-cols);
  font-size: var(--csl-size-fact); font-weight: 700; color: var(--cs-ink); line-height: 1.3;
}
.csl .fact-icon { font-size: 11px; font-weight: 400; color: var(--cs-ink); flex-shrink: 0; }
.csl .addl-row { padding: 2.5px var(--csl-pad); font-size: var(--csl-size-addl); font-weight: 700; color: var(--cs-ink); }
.csl .addl-row.sub { padding-left: var(--csl-indent-2); font-weight: 400; font-size: var(--csl-size-sub); color: var(--cs-ink); line-height: 1.5; }
.csl .sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap;border:0}
.csl .footnote { padding: 4px var(--csl-pad) 6px; font-size: var(--csl-size-foot); font-weight: 400; color: var(--cs-ink); line-height: 1.7; }
"""


# ══════════════════════════════════════════════════════════════════════════════
# A.  page_shell(title, body)
# ══════════════════════════════════════════════════════════════════════════════

def page_shell(title, body):
    """Outer HTML wrapper for every published page.
    CSS is concatenated as a plain string to avoid f-string brace escaping."""
    today = datetime.date.today().isoformat()
    head = (
        f'<!doctype html>\n'
        f'<html lang="en">\n'
        f'<head>\n'
        f'<meta charset="utf-8">\n'
        f'<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f'<title>{e(title)}</title>\n'
        f'<style>\n'
    )
    tail = (
        f'</style>\n'
        f'</head>\n'
        f'<body>\n'
        f'<a class="skip-link" href="#main-content">Skip to main content</a>\n'
        f'<header class="site-header">\n'
        f'  <div class="inner">\n'
        f'    <a href="/" class="wordmark">Canada<span class="scanada">Scanada</span></a>\n'
        f'    <nav class="site-nav">\n'
        f'      <a href="/index.html">Timeline</a>\n'
        f'      <a href="/outlets/">Media outlets</a>\n'
        f'      <a href="/about.html">About</a>\n'
        f'    </nav>\n'
        f'  </div>\n'
        f'</header>\n'
        f'<main id="main-content">\n'
        f'  <h1 class="page-h1">{e(title)}</h1>\n'
        f'  <p class="page-intro">Documented events, newest first.\n'
        f'  Tap a headline to read the full record.</p>\n'
        f'  {body}\n'
        f'</main>\n'
        f'<footer class="site-footer">\n'
        f'  <div class="inner">\n'
        f'    <div class="foot-links">\n'
        f'      <a href="/methodology.html">Methodology</a>\n'
        f'      <a href="/sources.html">Sources</a>\n'
        f'      <a href="/contribute.html">Contribute</a>\n'
        f'    </div>\n'
        f'    Data licensed CC BY 4.0 &middot; Code MIT &middot;\n'
        f'    Built {today} &middot;\n'
        f'    Static HTML, no JavaScript on this page.\n'
        f'  </div>\n'
        f'</footer>\n'
        f'</body>\n'
        f'</html>'
    )
    return head + _CSS + tail


# ══════════════════════════════════════════════════════════════════════════════
# B0.  RELATIONS GRAPH  —  bidirectional rendering (Standard §5.4, §8 task 3b)
# ══════════════════════════════════════════════════════════════════════════════

def load_threads(data_dir):
    """Load narrative-threads.json → {thread_id: title}. Missing file is fine;
    thread rows then fall back to the raw thread_id."""
    path = Path(data_dir) / "meta" / "narrative-threads.json"
    titles = {}
    if not path.exists():
        return titles
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as ex:
        print(f"  WARNING: could not read narrative-threads.json: {ex}",
              file=sys.stderr)
        return titles
    if isinstance(raw, dict) and "threads" in raw:
        items = raw["threads"]
    elif isinstance(raw, list):
        items = raw
    elif isinstance(raw, dict):
        items = list(raw.values())
    else:
        items = []
    for t in items:
        if not isinstance(t, dict):
            continue
        tid = t.get("id") or t.get("thread_id")
        if tid:
            titles[tid] = t.get("title_en") or t.get("title") or tid
    return titles


def build_relation_context(events, published_ids, thread_titles):
    """Precompute the inbound (derived-inverse) index once, in O(edges).

    An edge is stored on the lower-id source event; this derives the inverse so
    it renders on the target's card too. Only edges where the edge itself clears
    needs_verification AND both endpoints publish are indexed (Standard §6)."""
    inbound = {}
    for ev in events.values():
        sid = ev.get("id")
        if sid not in published_ids:
            continue
        for edge in (ev.get("relations") or []):
            if edge.get("needs_verification"):
                continue
            t = edge.get("type")
            if t == "part_of_thread":
                continue  # thread membership has no event-to-event inverse
            inv = RELATION_INVERSE.get(t)
            if not inv:
                continue
            tgt = edge.get("target_id")
            if not tgt or tgt not in published_ids:
                continue
            inbound.setdefault(tgt, []).append((inv, sid, edge))
    return {
        "events": events,
        "published_ids": published_ids,
        "inbound": inbound,
        "thread_titles": thread_titles,
    }


def _connection_row(rel_type, *, target_ev=None, edge=None, thread_title=None):
    """One uniform Connections row. Same markup for every edge type."""
    label = RELATION_LABELS.get(rel_type, rel_type.replace("_", " ").capitalize())
    if thread_title is not None:
        detail = f'<span class="connection-thread">{e(thread_title)}</span>'
    else:
        tid = target_ev.get("id", "")
        ttl = e(target_ev.get("title_en", "") or tid)
        detail = f'<a href="#{e(tid)}">{ttl}</a>'
        edge = edge or {}
        framing = edge.get("framing_en")
        if rel_type in ("conflicts_with", "jurisdiction_clarification") and framing:
            disc = edge.get("discrepancy")
            disc_html = (f' <span class="connection-disc">'
                         f'({e(disc.replace("_", " "))})</span>') if disc else ""
            detail += f'<p class="connection-framing">{e(framing)}{disc_html}</p>'
        elif RENDER_CAUSAL_NOTES and edge.get("note"):
            detail += f'<p class="connection-framing">{e(edge["note"])}</p>'
    return (
        f'<div class="connection-row">'
        f'<span class="connection-type">{e(label)}</span>'
        f'<div class="connection-detail">{detail}</div>'
        f'</div>'
    )


def render_connections(ev, ctx):
    """Render this event's Connections block: its own edges plus derived
    inverses from events that point at it. Returns "" if there are none."""
    if not ctx:
        return ""
    events        = ctx["events"]
    published_ids = ctx["published_ids"]
    inbound       = ctx["inbound"]
    thread_titles = ctx["thread_titles"]

    rows, seen = [], set()

    # Outbound — edges stored on this event.
    for edge in (ev.get("relations") or []):
        if edge.get("needs_verification"):
            continue
        t = edge.get("type")
        if t == "part_of_thread":
            tid = edge.get("thread_id")
            if not tid:
                continue
            key = ("thread", tid)
            if key in seen:
                continue
            seen.add(key)
            rows.append(_connection_row(t, thread_title=thread_titles.get(tid, tid)))
            continue
        tgt = edge.get("target_id")
        if not tgt or tgt not in published_ids:
            continue  # gate: target must publish
        key = (tgt, RELATION_FAMILY.get(t, t))
        if key in seen:
            continue
        seen.add(key)
        rows.append(_connection_row(t, target_ev=events[tgt], edge=edge))

    # Inbound — inverses derived from other events that target this one.
    for inv, sid, edge in inbound.get(ev.get("id"), []):
        key = (sid, RELATION_FAMILY.get(inv, inv))
        if key in seen:
            continue
        seen.add(key)
        rows.append(_connection_row(inv, target_ev=events[sid], edge=edge))

    if not rows:
        return ""
    return (
        '<div class="annotation connections" role="group" aria-label="Connections">\n'
        '  <span class="annotation-label">Connections</span>\n'
        + "".join(rows)
        + '\n</div>\n'
    )


# ══════════════════════════════════════════════════════════════════════════════
# B.  render_event(ev, refs, outlets)
# ══════════════════════════════════════════════════════════════════════════════

def render_event(ev, refs, outlets, conn_ctx=None):
    """Render one timeline card. Output matches wireframe_timeline_v4.html."""

    vstatus = ev.get("verification_status", "verified")
    status_cls, status_label = STATUS_MAP.get(vstatus, STATUS_MAP["verified"])

    # Source lines: Headline (link) · Publication · Date
    source_lines = ""
    for rid in (ev.get("source_refs") or []):
        ref = refs.get(rid)
        if not ref:
            continue
        outlet    = outlets.get(ref.get("outlet_id", ""), {})
        pub_name  = e(outlet.get("name_en") or ref.get("outlet_id", ""))
        title_txt = e(ref.get("title") or "")
        url       = e(ref.get("url") or "")
        pub_date  = e(ref.get("publication_date") or ref.get("pub_date") or "")
        link = f'<a href="{url}">{title_txt}</a>' if url else title_txt
        source_lines += (
            f'<p>{link} &nbsp;&middot;&nbsp; '
            f'<span class="src-pub">{pub_name}</span>'
            + (f' &nbsp;&middot;&nbsp; {pub_date}' if pub_date else '')
            + '</p>\n'
        )

    chips = "".join(
        f'<span class="chip">{e(c.replace("_", " "))}</span>'
        for c in (ev.get("category") or [])
    )

    # Hero quote — checks extensions.hero_quote first, then top-level
    hq = (ev.get("extensions") or {}).get("hero_quote") or ev.get("hero_quote")
    hero_quote_html = ""
    if hq:
        role_part = f', {e(hq.get("role", ""))}' if hq.get("role") else ""
        date_part = (
            f' &nbsp;&middot;&nbsp; {e(hq["date"])}' if hq.get("date") else ""
        )
        hero_quote_html = (
            f'<blockquote class="hero-quote">\n'
            f'  <p>{e(hq.get("text", ""))}</p>\n'
            f'  <cite>{e(hq.get("speaker", ""))}{role_part}{date_part}</cite>\n'
            f'</blockquote>\n'
        )

    inference_html = ""
    if ev.get("claim_type") == "inference" and ev.get("inference_note"):
        inference_html = (
            f'<div class="annotation inference">\n'
            f'  <span class="annotation-label">Inference</span>\n'
            f'  {e(ev["inference_note"])}\n'
            f'</div>\n'
        )

    response_html = ""
    if ev.get("opposition_response"):
        response_html = (
            f'<div class="annotation">\n'
            f'  <span class="annotation-label">Response</span>\n'
            f'  {e(ev["opposition_response"])}\n'
            f'</div>\n'
        )

    connections_html = render_connections(ev, conn_ctx)

    return (
        f'<details class="card" id="{e(ev["id"])}">\n'
        f'  <summary class="card-summary">\n'
        f'    <div class="card-top">\n'
        f'      <span class="card-date">{e(ev.get("event_date", ""))}</span>\n'
        f'      <span class="status {status_cls}">{status_label}</span>\n'
        f'    </div>\n'
        f'    <h2 class="card-title">{e(ev.get("title_en", ""))}</h2>\n'
        f'  </summary>\n'
        f'  <div class="card-body-area">\n'
        f'    <p class="card-body">{e(ev.get("description_en", ""))}</p>\n'
        f'    {hero_quote_html}'
        f'    {inference_html}'
        f'    {response_html}'
        f'    {connections_html}'
        f'    <details class="card-details">\n'
        f'      <summary>Details</summary>\n'
        f'      <div class="detail-sources">{source_lines}</div>\n'
        f'      <span class="chips-label">Tags</span>\n'
        f'      <div class="card-chips">{chips}</div>\n'
        f'    </details>\n'
        f'  </div>\n'
        f'</details>\n'
    )


# ══════════════════════════════════════════════════════════════════════════════
# C.  render_outlet(o)
# ══════════════════════════════════════════════════════════════════════════════

def render_outlet(o):
    """Render the CanScan media label. Facts-only: no scoring, no verdict.
    Shows ownership, then only VERIFIED facts. Non-news sources show a reason.
    NOTE: visual layout is provisional pending the label-design decision (A3)."""
    NL = chr(10)
    cdn, _foreign = derive_ownership_split(o)
    hero_pct = f"{cdn}%" if cdn is not None else "Pending"
    name = e(o.get("name_en", ""))
    outlet_type = OUTLET_TYPE_LABELS.get(o.get("outlet_type", ""), e(o.get("outlet_type", "")))
    breakdown = o.get("ownership_breakdown") or []
    parent = e(breakdown[0].get("entity", "")) if breakdown else ""
    descriptor = f"{parent} &nbsp;&middot;&nbsp; {outlet_type}" if parent else outlet_type
    own_rows = NL.join(
        f'<div class="own-row"><span>{e(entry.get("entity",""))}'
        f'{"(" + e(entry.get("country","")) + ")" if entry.get("country","") not in ("","CA") else ""}'
        f'</span><span class="own-pct">{entry.get("percentage",0)}%</span></div>'
        for entry in breakdown
    )
    head = (
        f'<article class="csl" id="outlet-{e(o["outlet_id"])}" role="group" aria-label="CanScan label for {name}">' + NL
        + f'  <div class="head"><div class="outlet-name">{name}</div></div>' + NL
        + '  <div class="r-1pt"></div>' + NL
        + f'  <div class="descriptor">{descriptor}</div>' + NL
        + '  <div class="r-thick"></div>' + NL
        + f'  <div class="hero"><span class="h-label">Canadian ownership</span><span class="h-pct">{hero_pct}</span></div>' + NL
        + '  <div class="r-thick"></div>' + NL
        + f'  <div class="own-section">{NL}{own_rows}{NL}  </div>' + NL
    )
    if not o.get("rated", True):
        reason = e(o.get("not_rated_reason", ""))
        body = f'<div class="addl-row sub">{reason}</div>' if reason else ""
        return (
            head
            + '  <div class="r-thick"></div>' + NL
            + '  <div class="addl-row">Not rated as a news outlet</div>' + NL
            + '  <div class="r-thin"></div>' + NL + "  " + body + NL
            + '</article>' + NL
        )
    facts = o.get("facts") or {}
    rows = []
    for key, label in FACT_LABELS.items():
        f = facts.get(key)
        if not f or not f.get("verified"):
            continue  # facts-only: omit unverified facts entirely
        yes = bool(f.get("value"))
        glyph = "&#x2713;" if yes else "&#x2715;"
        word = "Yes" if yes else "No"
        rows.append(
            f'<div class="fact-row"><span>{e(label)}</span>'
            f'<span class="fact-icon" aria-hidden="true">{glyph}</span>'
            f'<span class="sr-only">{word}</span></div>'
        )
    fact_section = ""
    if rows:
        sep = NL + '<div class="r-thin"></div>' + NL
        fact_section = '  <div class="r-thick"></div>' + NL + "  " + sep.join(rows) + NL
    return head + fact_section + '</article>' + NL


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main(data_dir, out_dir):
    data_dir = Path(data_dir)
    out_dir  = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"BUILD  data={data_dir}  →  {out_dir}")

    # ── Load ──────────────────────────────────────────────────────────────────
    events  = load_dir(data_dir / "events")
    refs    = load_dir(data_dir / "references")
    outlets = load_outlet_db(data_dir)

    print(f"  loaded: {len(events)} events, {len(refs)} references, "
          f"{len(outlets)} outlets")

    # ── Publication gate ──────────────────────────────────────────────────────
    publishable = [ev for ev in events.values() if is_publishable(ev, refs)]
    suppressed  = len(events) - len(publishable)
    print(f"  gate:   {len(publishable)} published, {suppressed} suppressed")

    # ── Relations graph (3b): published set + derived-inverse index ───────────
    published_ids = {ev["id"] for ev in publishable if "id" in ev}
    thread_titles = load_threads(data_dir)
    conn_ctx      = build_relation_context(events, published_ids, thread_titles)
    edge_count = sum(len(v) for v in conn_ctx["inbound"].values())
    print(f"  graph:  {edge_count} derived inverse edge(s), "
          f"{len(thread_titles)} thread(s)")

    # ── Sort newest-first ─────────────────────────────────────────────────────
    ordered = sorted(
        publishable,
        key=lambda ev: ev.get("event_date", ""),
        reverse=True,
    )

    # ── Timeline page → index.html ────────────────────────────────────────────
    timeline_body = (
        '<div class="timeline">'
        + "".join(render_event(ev, refs, outlets, conn_ctx) for ev in ordered)
        + '</div>'
    )
    (out_dir / "index.html").write_text(
        page_shell("Timeline", timeline_body), encoding="utf-8"
    )
    print(f"  → {out_dir}/index.html  ({len(ordered)} events)")

    # ── Outlet pages → outlets/<outlet_id>.html ───────────────────────────────
    if outlets:
        outlets_dir = out_dir / "outlets"
        outlets_dir.mkdir(exist_ok=True)
        # Index page listing all labels
        all_labels = "".join(render_outlet(o) for o in outlets.values())
        (outlets_dir / "index.html").write_text(
            page_shell("Media outlets", all_labels), encoding="utf-8"
        )
        for outlet_id, o in outlets.items():
            page = page_shell(o.get("name_en", outlet_id), render_outlet(o))
            (outlets_dir / f"{outlet_id}.html").write_text(
                page, encoding="utf-8"
            )
        print(f"  → {out_dir}/outlets/  ({len(outlets)} labels)")

    (out_dir / "events").mkdir(exist_ok=True)
    # ── events/index.json — for CanScan domain lookup ─────────────────────────
    events_index = [
        {
            "id":         ev["id"],
            "event_date": ev.get("event_date", ""),
            "title_en":   ev.get("title_en", ""),
        }
        for ev in ordered
    ]
    (out_dir / "events" / "index.json").write_text(
        json.dumps(events_index, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # ── outlets/index.json — for CanScan extension lookup ─────────────────────
    outlets_index = {
        oid: {
            "name_en":      o.get("name_en", ""),
            "outlet_type":  o.get("outlet_type", ""),
            "cdn_pct":      derive_ownership_split(o)[0],
        }
        for oid, o in outlets.items()
    }
    (out_dir / "outlets" / "index.json").write_text(
        json.dumps(outlets_index, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("BUILD COMPLETE")
    return 0


if __name__ == "__main__":
    data_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    out_dir  = sys.argv[2] if len(sys.argv) > 2 else "./docs"
    sys.exit(main(data_dir, out_dir))
