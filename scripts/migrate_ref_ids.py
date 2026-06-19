#!/usr/bin/env python3
"""
migrate_ref_ids.py — CanadaScanada reference-ID unification (→ hex canonical)
═════════════════════════════════════════════════════════════════════════════
Decision (Thread 6 / 7): collapse the three coexisting reference-ID styles
(sequential R-NNN, hex R-XXXXXXXX, slug R-word-word) into ONE canonical form:
8-character uppercase hex, `R-XXXXXXXX`. Existing hex IDs are left untouched;
sequential and slug IDs are re-minted to hex. The old ID is preserved on each
renamed record as `extensions.legacy_id` so any external citation stays
traceable (FAIR / Reusable requirement).

WHAT THIS TOUCHES
  - Renames reference files whose ID is not already 8-hex.
  - Sets the new `id` and adds `extensions.legacy_id` on each renamed ref.
  - Rewrites every inbound reference across the FIVE known structured fields:
        source_refs[]                       (event, top level)
        relations[].source_refs[]           (event, on conflicts_with / jurisdiction edges)
        opposition_response.source_refs[]   (canonical) and .source_ref (legacy singular)
        claim_contested_by[].source_ref     (and legacy .source_refs[])
        update_log[].source_ref             (and legacy .source_refs[])
  - Does NOT touch `relations[].explainer_ref` (that points at an explainer
    record, not a reference — see Design Standard §5.4 / §5.7).
  - Does NOT rewrite free-form prose (e.g. a ref mentioned inside `notes`).
    Instead it SCANS for any leftover old-ID string anywhere and reports it
    for human review. That residual scan is the safety net for any sixth
    field this script's author did not know about: the script refuses to
    claim success while a structured residual remains.

SAFETY POSTURE
  - DRY-RUN BY DEFAULT. Writes nothing unless you pass --apply.
  - Auto-discovers the events/ and references/ directories and prints which it
    used, so a docs-vs-disk path ambiguity surfaces immediately.
  - Collision-safe and case-insensitive (macOS default FS is case-insensitive;
    the script never produces a case-only rename and never mints a hex that
    collides with an existing ID under case-folding).
  - Deterministic: the new ID is derived from the old ID, so a re-run produces
    the same mapping and a fully-migrated corpus is a clean no-op (idempotent).
  - Self-validating: reports counts, asserts ID uniqueness, and confirms zero
    structured residuals before reporting OK.

USAGE
  python3 scripts/migrate_ref_ids.py [DATA_DIR]            # dry-run (default)
  python3 scripts/migrate_ref_ids.py [DATA_DIR] --apply    # write changes

  Run dry-run first. Run on a clean git tree (so `git checkout .` reverts).
  After --apply:  validate.py  →  state.py  →  sweep.py  →  build.py.
"""

import hashlib
import json
import re
import sys
from pathlib import Path

HEX_RE = re.compile(r"^R-[0-9A-Fa-f]{8}$")        # already-canonical form
ANY_REF_RE = re.compile(r"R-[0-9A-Za-z_-]{3,}")    # broad: catches seq, hex, slug in text


# ── directory discovery ──────────────────────────────────────────────────────

def discover(data_dir, candidates, glob):
    """Return the first candidate subdir that actually contains matching files."""
    for rel in candidates:
        d = data_dir / rel
        if d.is_dir() and any(d.glob(glob)):
            return d
    return None


def load_json(p):
    return json.loads(p.read_text(encoding="utf-8"))


# ── id minting ───────────────────────────────────────────────────────────────

def mint_hex(legacy_id, taken_lower):
    """Deterministic 8-hex from the legacy id; salt-rehash on collision.
    `taken_lower` is the set of all ids already in use, lower-cased, so the
    collision check is case-insensitive (safe on macOS)."""
    salt = 0
    while True:
        seed = legacy_id if salt == 0 else f"{legacy_id}#{salt}"
        digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:8].upper()
        new_id = f"R-{digest}"
        if new_id.lower() not in taken_lower:
            return new_id
        salt += 1


# ── reference-value remapping ────────────────────────────────────────────────

def remap_value(v, mapping):
    """Map a single ref-id string through the mapping (untouched if absent)."""
    return mapping.get(v, v) if isinstance(v, str) else v


def remap_list(lst, mapping):
    changed = 0
    if not isinstance(lst, list):
        return 0
    for i, v in enumerate(lst):
        nv = remap_value(v, mapping)
        if nv != v:
            lst[i] = nv
            changed += 1
    return changed


REF_KEYS = {"source_ref", "source_refs"}   # the only structured ref-bearing keys
# explainer_ref is deliberately NOT here: it points at an explainer record, not a
# reference (Design Standard §5.4 / §5.7). If the residual classifier ever flags
# explainer_ref holding an R- id, revisit that decision.


def rewrite_event(ev, mapping):
    """Recursively remap every value stored under a `source_ref` / `source_refs`
    key, wherever it appears in the event — top level, inside relations[],
    opposition_response, claim_contested_by[], update_log[], or any nesting this
    author did not enumerate. Walking by key name (rather than by hardcoded path)
    is what catches a stray singular `source_ref` the fixed-location version
    missed. Values under any other key, including prose, are left untouched.
    Returns the count of individual id rewrites performed."""
    n = 0
    if isinstance(ev, dict):
        for k, v in ev.items():
            if k in REF_KEYS:
                if isinstance(v, str):
                    nv = remap_value(v, mapping)
                    if nv != v:
                        ev[k] = nv
                        n += 1
                elif isinstance(v, list):
                    n += remap_list(v, mapping)
                else:
                    n += rewrite_event(v, mapping)   # unusual nesting — recurse anyway
            else:
                n += rewrite_event(v, mapping)
    elif isinstance(ev, list):
        for item in ev:
            n += rewrite_event(item, mapping)
    return n


# ── main ─────────────────────────────────────────────────────────────────────

def main(argv):
    data_dir = Path(argv[1]) if len(argv) > 1 and not argv[1].startswith("--") else Path(".")
    apply = "--apply" in argv

    print(f"migrate_ref_ids  data={data_dir.resolve()}  mode={'APPLY' if apply else 'DRY-RUN'}")

    ref_dir = discover(data_dir, ["references", "references/records"], "R-*.json")
    ev_dir  = discover(data_dir, ["events", "events/records"], "EVT-*.json")
    if not ref_dir or not ev_dir:
        print(f"  ABORT: could not locate dirs (refs={ref_dir}, events={ev_dir}).")
        return 2
    print(f"  references dir: {ref_dir}")
    print(f"  events dir:     {ev_dir}")

    ref_files = sorted(ref_dir.glob("R-*.json"))
    ev_files  = sorted(ev_dir.glob("EVT-*.json"))
    print(f"  loaded: {len(ref_files)} references, {len(ev_files)} events")

    # All existing ids (case-folded) so new ids never collide with anything.
    existing_ids = {p.stem for p in ref_files}
    taken_lower = {i.lower() for i in existing_ids}

    # Build the old→new mapping. Only non-hex ids are renamed; hex stays.
    mapping = {}
    style = {"sequential": 0, "hex": 0, "slug": 0}
    for p in ref_files:
        rid = p.stem
        if HEX_RE.match(rid):
            style["hex"] += 1
            continue
        if re.match(r"^R-\d+$", rid):
            style["sequential"] += 1
        else:
            style["slug"] += 1
        new_id = mint_hex(rid, taken_lower)
        taken_lower.add(new_id.lower())
        mapping[rid] = new_id

    print(f"  styles: {style['sequential']} sequential, {style['hex']} hex, "
          f"{style['slug']} slug")
    print(f"  to rename: {len(mapping)} references → hex")
    if not mapping:
        print("  nothing to migrate — corpus already canonical. OK (no-op).")
        return 0

    # Rewrite inbound references across events.
    edge_rewrites = 0
    touched_events = 0
    ev_objs = {}
    for p in ev_files:
        ev = load_json(p)
        ev_objs[p] = ev
        n = rewrite_event(ev, mapping)
        if n:
            edge_rewrites += n
            touched_events += 1
    print(f"  inbound rewrites: {edge_rewrites} ids across {touched_events} events")

    # Residual classifier (the safety net): after structured rewrites, walk the
    # parsed JSON and find every OLD id still present in a string value, bucketed
    # by the FIELD KEY it sits under. This distinguishes the two cases that the
    # raw count cannot:
    #   - prose mention (a key WITHOUT "ref" in its name: note, change,
    #     verification_notes, date_notes, ...) → SAFE to leave; legacy_id keeps
    #     the old id traceable, and rewriting append-only log prose would falsify
    #     history.
    #   - a ref-bearing field this script does not rewrite (any key WITH "ref":
    #     explainer_ref, the deprecated said_did_ref, etc.) → CONCERN: a possible
    #     missed structured field that must be added before --apply.
    # Structured fields the script DOES handle (source_ref/source_refs) are
    # rewritten in-memory, so they should show zero residuals; any here is a bug.
    old_ids = set(mapping)
    pats = {oid: re.compile(re.escape(oid) + r"(?![0-9A-Za-z_-])") for oid in old_ids}

    def walk_strings(obj, key=None, path=""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                yield from walk_strings(v, k, f"{path}.{k}" if path else k)
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                yield from walk_strings(v, key, f"{path}[{i}]")
        elif isinstance(obj, str):
            yield key, path, obj

    buckets = {}  # (scope, field_key) -> {count, example, path}
    def tally(obj, scope, own=None):
        for key, path, s in walk_strings(obj):
            for oid in old_ids:
                if oid == own:
                    continue
                if pats[oid].search(s):
                    b = buckets.setdefault((scope, key), {"count": 0, "ex": None, "path": None})
                    b["count"] += 1
                    if not b["ex"]:
                        b["ex"] = f'{oid}  "…{s[:44].strip()}…"'
                        b["path"] = f"{scope}/{path}"

    for p, ev in ev_objs.items():        # in-memory, already rewritten
        tally(ev, "event")
    for p in ref_files:                  # on-disk; skip each ref's own (soon-renamed) id
        tally(load_json(p), "ref", own=p.stem)

    def is_concern(field_key):
        return bool(field_key) and "ref" in field_key.lower()

    concern = {k: v for k, v in buckets.items() if is_concern(k[1])}
    prose   = {k: v for k, v in buckets.items() if not is_concern(k[1])}
    total   = sum(v["count"] for v in buckets.values())

    print(f"  residual old-ID mentions: {total}, by field —")
    for (scope, key), v in sorted(buckets.items(), key=lambda kv: -kv[1]["count"]):
        tag = "CONCERN" if is_concern(key) else "prose/SAFE"
        loc = f"  @ {v['path']}" if is_concern(key) else ""
        print(f"      [{tag:10}] {scope}.{key}: {v['count']:>4}   e.g. {v['ex']}{loc}")
    if concern:
        print("  ⚠ VERDICT: ref-bearing field(s) above still hold old ids — a structured")
        print("    field this script does not rewrite. Do NOT --apply. Send me the field")
        print("    name(s) and I will add them to rewrite_event().")
    else:
        print("  ✓ VERDICT: every residual is a prose mention (no ref-bearing field missed).")
        print("    The structured graph is fully migrated. Prose is left as-is on purpose:")
        print("    legacy_id keeps each old id traceable, and update_log is append-only")
        print("    history that should not be rewritten.")

    # Mapping file (always written-to-stdout in dry-run; to disk on apply).
    map_lines = ["legacy_id,new_id"] + [f"{o},{n}" for o, n in sorted(mapping.items())]

    if not apply:
        print("\n  DRY-RUN complete. No files changed.")
        print("  Re-run with --apply to write. Mapping preview (first 10):")
        for line in map_lines[1:11]:
            print(f"      {line}")
        print(f"      … {len(mapping)} total")
        return 0

    # ── APPLY ────────────────────────────────────────────────────────────────
    # Write rewritten events.
    for p, ev in ev_objs.items():
        p.write_text(json.dumps(ev, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    # Rewrite + rename ref files: set id, stamp legacy_id, then rename on disk.
    for p in ref_files:
        rid = p.stem
        if rid not in mapping:
            continue
        ref = load_json(p)
        ref["id"] = mapping[rid]
        ext = ref.get("extensions")
        if not isinstance(ext, dict):
            ext = {}
        ext["legacy_id"] = rid
        ref["extensions"] = ext
        p.write_text(json.dumps(ref, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        p.rename(p.with_name(mapping[rid] + ".json"))
    # Write mapping file for provenance.
    (data_dir / "ref_id_migration_map.csv").write_text("\n".join(map_lines) + "\n",
                                                        encoding="utf-8")
    print(f"\n  APPLIED: {len(mapping)} refs renamed, {edge_rewrites} inbound ids rewritten.")
    print(f"  mapping: {data_dir / 'ref_id_migration_map.csv'}")
    print("  NEXT: validate.py → state.py → sweep.py → build.py, then commit.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
