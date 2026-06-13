#!/usr/bin/env python3
"""
state.py - ground-truth state of the CanadaScanada data tree.

Run this FIRST in any thread, before trusting a handoff's numbers. It reads the
per-file source records directly and reports live counts, the publish/suppress
split, the next id, the schema_version spread, and any structural drift (monolith
present, manifest/file mismatch, duplicate ids). Exit code is non-zero if a hard
invariant is violated, so it doubles as a pre-commit / CI guard.

Usage:
    python3 scripts/state.py [DATA_DIR]

DATA_DIR defaults to the repo root ("."). No third-party dependencies.
"""

import json
import sys
from pathlib import Path


def load_json(p):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        return {"__error__": str(e)}


def record_files(d):
    """Per-file source records only: skip index.json and _-prefixed files."""
    if not d.is_dir():
        return []
    return sorted(
        f for f in d.glob("*.json")
        if f.name != "index.json" and not f.name.startswith("_")
    )


def ver_hist(records):
    h = {}
    for _, r in records:
        v = r.get("schema_version", "MISSING")
        h[v] = h.get(v, 0) + 1
    return dict(sorted(h.items(), key=lambda kv: str(kv[0])))


def trailing_int(value):
    i = str(value)
    tail = i.split("-")[-1] if "-" in i else ""
    return int(tail) if tail.isdigit() else None


def main():
    base = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    problems = []   # hard invariant violations -> non-zero exit
    warnings = []   # advisory

    events_dir = base / "events"
    refs_dir = base / "references"
    outlets_dir = base / "outlets" / "records"

    # --- events ---
    ev = [(f, load_json(f)) for f in record_files(events_dir)]
    for f, r in ev:
        if "__error__" in r:
            problems.append(f"events: {f.name} failed to parse ({r['__error__']})")
    ev_ok = [(f, r) for f, r in ev if "__error__" not in r]

    ev_total = len(ev_ok)
    # Proxy for the build gate. The authoritative gate lives in build.py;
    # needs_verification is the dominant signal and keeps the number legible.
    ev_suppressed = sum(1 for _, r in ev_ok if bool(r.get("needs_verification", False)))
    ev_published = ev_total - ev_suppressed

    ev_nums = [n for n in (trailing_int(r.get("id", "")) for _, r in ev_ok) if n is not None]
    max_evt = max(ev_nums) if ev_nums else 0

    ev_ids = [str(r.get("id", "")) for _, r in ev_ok]
    dup_ev = sorted({i for i in ev_ids if ev_ids.count(i) > 1})
    if dup_ev:
        problems.append(f"events: duplicate ids {dup_ev}")
    ev_vers = ver_hist(ev_ok)
    if ev_vers.get("MISSING"):
        warnings.append(f"events: {ev_vers['MISSING']} record(s) missing schema_version")

    # --- references ---
    rf = [(f, load_json(f)) for f in record_files(refs_dir)]
    for f, r in rf:
        if "__error__" in r:
            problems.append(f"references: {f.name} failed to parse ({r['__error__']})")
    rf_ok = [(f, r) for f, r in rf if "__error__" not in r]
    rf_total = len(rf_ok)
    rf_verified = sum(1 for _, r in rf_ok if r.get("verified") is True)
    rf_ids = [str(r.get("id", "")) for _, r in rf_ok]
    dup_rf = sorted({i for i in rf_ids if rf_ids.count(i) > 1})
    if dup_rf:
        problems.append(f"references: duplicate ids {dup_rf}")
    rf_vers = ver_hist(rf_ok)
    if rf_vers.get("MISSING"):
        warnings.append(f"references: {rf_vers['MISSING']} record(s) missing schema_version "
                        "(grep -L schema_version references/*.json to find them)")

    # --- outlets ---
    ot_ids = []
    for f in record_files(outlets_dir):
        r = load_json(f)
        if "__error__" in r:
            problems.append(f"outlets: {f.name} failed to parse ({r['__error__']})")
            continue
        ot_ids.append(r.get("outlet_id", f.stem))
    ot_ids_set = set(ot_ids)

    # manifest discovery: check known candidate locations, report which was used
    manifest_candidates = [
        base / "outlets" / "_manifest.json",
        base / "outlets" / "records" / "_manifest.json",
        base / "outlets" / "manifest.json",
    ]
    manifest_path = next((p for p in manifest_candidates if p.exists()), None)
    manifest_order = []
    if manifest_path is None:
        warnings.append("outlets: no _manifest.json found (looked in outlets/ and "
                        "outlets/records/). Display order is undefined until one exists.")
    else:
        m = load_json(manifest_path)
        if "__error__" in m:
            problems.append(f"outlets: {manifest_path.name} failed to parse ({m['__error__']})")
        else:
            manifest_order = m.get("order", [])

    manifest_set = set(manifest_order)
    in_manifest_no_file = sorted(manifest_set - ot_ids_set)
    not_yet_in_manifest = sorted(ot_ids_set - manifest_set)

    # Dangling order entry (order points at a record that does not exist) is a real bug.
    if in_manifest_no_file:
        problems.append(f"outlets: manifest ids with no record file {in_manifest_no_file}")

    # Records not yet in the manifest are the ACCEPTED pending/backfill state
    # (the pending-rating outlet decision). Warn, do not block.
    if not_yet_in_manifest:
        shown = not_yet_in_manifest[:8]
        more = f" (+{len(not_yet_in_manifest) - 8} more)" if len(not_yet_in_manifest) > 8 else ""
        warnings.append(f"outlets: {len(not_yet_in_manifest)} record(s) not yet in manifest "
                        f"order (backfill): {shown}{more}")

    # --- monolith / drift detection ---
    monolith_candidates = [
        base / "timeline-events.json",
        base / "references.json",
        base / "outlets" / "outlet-database.json",
        base / "outlet-database.json",
        base / "outlet-records-new.json",
    ]
    for p in (p for p in monolith_candidates if p.exists()):
        problems.append(f"monolith present (delete it): {p.relative_to(base)}")

    # --- report ---
    print(f"# data state @ {base}")
    print()
    print(f"events       total {ev_total:>4}   published {ev_published:>4}   suppressed {ev_suppressed:>4}")
    print(f"references   total {rf_total:>4}   verified  {rf_verified:>4}")
    gap = len(not_yet_in_manifest)
    gap_note = f"   ({gap} not yet in manifest)" if gap else ""
    print(f"outlets      total {len(ot_ids):>4}   manifest  {len(manifest_order):>4}{gap_note}")
    if manifest_path:
        print(f"             manifest: {manifest_path.relative_to(base)}")
    print(f"next id      EVT-{max_evt + 1:03d}   (max live EVT-{max_evt:03d}, scanned all files)")
    print(f"event   schema_version {ev_vers}")
    print(f"ref     schema_version {rf_vers}")
    print()

    if warnings:
        print("WARNINGS")
        for w in warnings:
            print(f"  - {w}")
        print()

    if problems:
        print("INVARIANT VIOLATIONS (commit blocked)")
        for p in problems:
            print(f"  - {p}")
        print()
        return 1

    print("OK: per-file tree consistent, no monolith, manifest reconciles.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
