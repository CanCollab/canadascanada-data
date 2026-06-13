#!/usr/bin/env python3
"""
regen_manifest.py - rebuild outlets/records/_manifest.json from the record files.

Preserves the existing display order, appends any outlet record not yet listed
(alphabetically), and drops any order entry whose file no longer exists (reported).
Idempotent: running it twice changes nothing. Only the "order" array and
"last_updated" are touched; every other manifest field is left exactly as is.

Run with --dry-run first to preview. Usage:
    python3 scripts/regen_manifest.py --dry-run
    python3 scripts/regen_manifest.py
    python3 scripts/regen_manifest.py [--dry-run] DATA_DIR
"""

import datetime
import json
import sys
from pathlib import Path


def main():
    raw = sys.argv[1:]
    dry_run = "--dry-run" in raw
    positional = [a for a in raw if a != "--dry-run"]
    base = Path(positional[0] if positional else ".").resolve()

    records_dir = base / "outlets" / "records"
    manifest_path = records_dir / "_manifest.json"

    if not records_dir.is_dir():
        print(f"ERROR: {records_dir} not found. Run from the repo root or pass DATA_DIR.")
        return 1

    # collect outlet ids from the record files
    file_id_set = set()
    for f in sorted(records_dir.glob("*.json")):
        if f.name == "index.json" or f.name.startswith("_"):
            continue
        try:
            r = json.loads(f.read_text(encoding="utf-8"))
        except Exception as e:  # noqa: BLE001
            print(f"ERROR: {f.name} failed to parse ({e}); fix it before regenerating.")
            return 1
        oid = r.get("outlet_id", f.stem)
        if oid != f.stem:
            print(f"  note: {f.name} has outlet_id '{oid}' (filename stem differs)")
        file_id_set.add(oid)

    # load existing manifest, preserving all fields and their order
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    else:
        manifest = {
            "schema": "outlet-database",
            "project": "CanadaScanada",
            "version": "0.3.0",
            "last_updated": "",
            "description": "Outlet records. Facts-only, no scoring.",
            "order": [],
        }
    existing_order = manifest.get("order", [])

    kept = [oid for oid in existing_order if oid in file_id_set]
    dropped = [oid for oid in existing_order if oid not in file_id_set]
    appended = sorted(oid for oid in file_id_set if oid not in set(kept))
    new_order = kept + appended

    print(f"records on disk  : {len(file_id_set)}")
    print(f"kept in order    : {len(kept)}")
    print(f"appended         : {len(appended)}  {appended if appended else ''}")
    if dropped:
        print(f"dropped (no file): {dropped}")
    print(f"new order length : {len(new_order)}")

    if new_order == existing_order:
        print("\nManifest already up to date. Nothing to write.")
        return 0

    manifest["order"] = new_order
    manifest["last_updated"] = datetime.date.today().isoformat()

    if dry_run:
        print("\n--dry-run: not writing. Re-run without --dry-run to apply.")
        return 0

    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"\nWrote {manifest_path.relative_to(base)} ({len(new_order)} entries).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
