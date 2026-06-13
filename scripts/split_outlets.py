#!/usr/bin/env python3
"""
split_outlets.py — one-time migration: explode the outlet monolith into
per-outlet files, matching the per-file pattern already used by events/ and
references/.

  outlets/outlet-database.json  ->  outlets/records/<outlet_id>.json  (one each)
                                     outlets/records/_manifest.json     (meta{} + display order)

The monolith is LEFT IN PLACE so you can diff and verify before deleting it.
validate.py / build.py auto-detect outlets/records/ once it exists and fall back
to the monolith if it does not, so the split is safe to land incrementally.

The authored front-page outlet order (previously implicit in array position) is
captured explicitly in _manifest.json as "order": [ids...]. build.py honours it;
any id NOT in the list falls back to alphabetical. Delete the "order" list to make
the directory fully alphabetical.

Usage:
  python3 scripts/split_outlets.py .            # write the records
  python3 scripts/split_outlets.py . --dry-run  # report only, write nothing
"""
import json, sys
from pathlib import Path


def main(data_dir, dry_run=False):
    data_dir = Path(data_dir)
    mono = data_dir / "outlets" / "outlet-database.json"
    if not mono.exists():
        print(f"  ERROR: {mono} not found", file=sys.stderr)
        return 1
    raw = json.loads(mono.read_text(encoding="utf-8"))
    meta = dict(raw.get("meta", {})) if isinstance(raw, dict) else {}
    if isinstance(raw, dict) and "outlets" in raw:
        items = raw["outlets"]
    elif isinstance(raw, list):
        items = raw
    else:
        items = [v for v in raw.values() if isinstance(v, dict)]

    records_dir = data_dir / "outlets" / "records"
    seen, planned, order = set(), [], []
    for o in items:
        oid = o.get("outlet_id")
        if not oid:
            print(f"  WARNING: record without outlet_id skipped: {str(o)[:60]}", file=sys.stderr)
            continue
        if oid in seen:
            print(f"  ERROR: duplicate outlet_id '{oid}'", file=sys.stderr)
            return 1
        seen.add(oid)
        order.append(oid)
        planned.append((records_dir / f"{oid}.json", o))

    meta["order"] = order  # capture previously-implicit array order as explicit data

    print(f"  monolith: {len(items)} record(s)  ->  {len(planned)} file(s) in outlets/records/")
    print(f"  + manifest: outlets/records/_manifest.json (meta + display order of {len(order)})")
    if dry_run:
        for path, _ in planned:
            print(f"    would write {path}")
        print("  (dry-run — nothing written)")
        return 0

    records_dir.mkdir(parents=True, exist_ok=True)
    for path, o in planned:
        path.write_text(json.dumps(o, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (records_dir / "_manifest.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"  wrote {len(planned)} record file(s) + _manifest.json")
    print(f"  monolith left in place: {mono}  (delete after you verify)")
    return 0


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    dd = args[0] if args else "."
    sys.exit(main(dd, dry_run="--dry-run" in sys.argv))
