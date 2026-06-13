#!/usr/bin/env python3
"""
migrate_locale.py - fold flat *_en / *_fr fields into BCP-47 locale objects.

Step 1 of the foundation pipeline. Converts every translatable field, at any nesting
depth, from the flat pair:
    "title_en": "...", "title_fr": "..."
into a single object:
    "title": {"en-CA": "...", "fr-CA": "..."}
A missing half becomes null. Records already in object shape are left untouched, so the
script is idempotent: a second run reports zero changes.

Scope: events/, references/, outlets/records/ by default. Field-name agnostic: it keys
off the _en / _fr suffix, so it catches title, description, framing (inside relations),
verification_prompt, name, not_rated_reason, and any future pair with no code change. It
never touches ids, dates, source_refs, relation targets, vocab values, or any field that
does not end in _en / _fr.

Run --dry-run first. Usage:
    python3 scripts/migrate_locale.py --dry-run
    python3 scripts/migrate_locale.py
    python3 scripts/migrate_locale.py [--dry-run] DATA_DIR

This script does the DATA half only. After it runs, update the read paths in build.py /
validate.py to read field["en-CA"] instead of field_en, then run validate.py and
state.py before committing. See FOUNDATION_PIPELINE.md, Step 1.
"""

import json
import sys
from pathlib import Path

EN_KEY = "en-CA"
FR_KEY = "fr-CA"


def convert(node, stats):
    """Transformed copy of node: fold *_en/*_fr sibling pairs into {base: {en-CA, fr-CA}},
    preserving key order. Recurses into dicts and lists."""
    if isinstance(node, list):
        return [convert(x, stats) for x in node]
    if not isinstance(node, dict):
        return node

    pair_bases = {k[:-3] for k in node if k.endswith("_en") or k.endswith("_fr")}
    # a base whose name is already used by a literal key is a collision: leave it alone
    collision = {b for b in pair_bases if b in node}

    out = {}
    emitted = set()
    for k, v in node.items():
        if k.endswith("_en") or k.endswith("_fr"):
            base = k[:-3]
            if base in collision:
                out[k] = convert(v, stats)        # leave untouched, flagged via residual
                continue
            if base in emitted:
                continue
            out[base] = {EN_KEY: node.get(base + "_en"), FR_KEY: node.get(base + "_fr")}
            emitted.add(base)
            stats["fields"] += 1
        else:
            out[k] = convert(v, stats)
    return out


def has_locale_suffix(node):
    if isinstance(node, dict):
        return any(k.endswith("_en") or k.endswith("_fr") or has_locale_suffix(v)
                   for k, v in node.items())
    if isinstance(node, list):
        return any(has_locale_suffix(x) for x in node)
    return False


def record_files(d):
    if not d.is_dir():
        return []
    return sorted(f for f in d.glob("*.json")
                  if f.name != "index.json" and not f.name.startswith("_"))


def main():
    raw = sys.argv[1:]
    dry_run = "--dry-run" in raw
    positional = [a for a in raw if a != "--dry-run"]
    base = Path(positional[0] if positional else ".").resolve()

    dirs = [base / "events", base / "references", base / "outlets" / "records"]
    files_scanned = files_changed = fields_total = 0
    residual = []

    for d in dirs:
        for f in record_files(d):
            files_scanned += 1
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
            except Exception as e:  # noqa: BLE001
                print(f"ERROR: {f} failed to parse ({e}); fix before migrating.")
                return 1
            stats = {"fields": 0}
            converted = convert(data, stats)
            if stats["fields"]:
                fields_total += stats["fields"]
                files_changed += 1
                if not dry_run:
                    f.write_text(json.dumps(converted, ensure_ascii=False, indent=2) + "\n",
                                 encoding="utf-8")
            if has_locale_suffix(converted):
                residual.append(str(f.relative_to(base)))

    print(f"files scanned : {files_scanned}")
    print(f"files changed : {files_changed}")
    print(f"fields folded : {fields_total}")
    if residual:
        print(f"RESIDUAL _en/_fr keys remain (name collisions, review by hand): {residual}")
    if dry_run:
        print("\n--dry-run: nothing written. Re-run without --dry-run to apply.")
    elif files_changed:
        print("\nData migrated. Next: update read paths in build.py / validate.py to read")
        print('field["en-CA"], then run validate.py and state.py before committing.')
    else:
        print("\nNothing to migrate (already locale-shaped).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
