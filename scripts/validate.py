#!/usr/bin/env python3
"""
validate.py — CanadaScanada integrity gate
═══════════════════════════════════════════
Usage:  python3 scripts/validate.py <data_dir>

  Exit 0  PASS — build may proceed
  Exit 1  FAIL — build is aborted, errors listed

Enforced rules (errors — build-blocking):
  - JSON parse errors in any record
  - Every reference outlet_id must exist in outlets/records/
  - Every reference source_type must be in meta/source-types.json
  - Every event source_ref must exist in references/
  - Every event category must be in meta/categories.json
  - Every event era must be in meta/era-labels.json
  - Inference events must have inference_note
  - Every relation edge type must be in meta/relation-types.json
  - part_of_thread edges: thread_id must exist in meta/narrative-threads.json
  - all other edges: target_id must resolve to an existing event
  - said_did_ref must resolve to an existing said-did record   (PROMOTED to error)
  - said-did source_refs must exist in references/

Warnings (non-blocking):
  - verified=true references with no URL and source_type=url_article
  - verified=true outlet facts missing source_url (must become sourced or
    be downgraded to verified=false; slated to become an error)
  - meta/narrative-threads.json or any meta/ vocab file absent (checks skipped)
"""

import json
import sys
from pathlib import Path


# ─── loaders ────────────────────────────────────────────────────────────────

def load_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except json.JSONDecodeError as ex:
        print(f"  FAIL  {path}: JSON parse error — {ex}")
        return "__PARSE_ERROR__"


def load_dir(path, errors):
    """Load all *.json in directory. Appends parse errors to `errors` list."""
    records = {}
    p = Path(path)
    if not p.exists():
        return records
    for f in sorted(p.glob("*.json")):
        if f.name == "index.json":
            continue
        raw = load_json(f)
        if raw == "__PARSE_ERROR__":
            errors.append(f"{f}: JSON parse error (see above)")
            continue
        if raw is not None:
            rid = raw.get("id", f.stem)
            records[rid] = raw
    return records


def load_outlets(data_dir, errors):
    """Outlets as a list, loaded from per-file outlets/records/*.json
    (skip _*.json)."""
    rec_dir = Path(data_dir) / "outlets" / "records"
    if not (rec_dir.is_dir() and any(
        f.suffix == ".json" and not f.name.startswith("_") for f in rec_dir.iterdir()
    )):
        errors.append(f"outlets/: no records found at {rec_dir}")
        return []
    outlets = []
    for f in sorted(rec_dir.glob("*.json")):
        if f.name.startswith("_"):
            continue
        raw = load_json(f)
        if raw == "__PARSE_ERROR__":
            errors.append(f"{f}: JSON parse error (see above)")
            continue
        if isinstance(raw, dict):
            outlets.append(raw)
    return outlets


def extract_vocab(raw, *keys):
    """Pull a flat set of id-strings out of whatever structure a vocab file uses:
    a bare list of strings, a list of dicts, or a dict wrapping one of those
    under any of `keys`."""
    if raw is None or raw == "__PARSE_ERROR__":
        return None
    lst = raw if isinstance(raw, list) else None
    if lst is None and isinstance(raw, dict):
        for k in keys:
            if k in raw:
                lst = raw[k]
                break
        if lst is None:
            # last resort: treat top-level dict keys as the vocab
            return set(raw.keys())
    result = set()
    for item in (lst or []):
        if isinstance(item, str):
            result.add(item)
        elif isinstance(item, dict):
            val = (item.get("id") or item.get("name") or item.get("term") or
                   item.get("slug") or item.get("value") or "")
            if val:
                result.add(val)
    return result


# ─── main ───────────────────────────────────────────────────────────────────

def main(data_dir):
    data_dir = Path(data_dir)
    errors   = []
    warnings = []

    # ── Load records ──────────────────────────────────────────────────────────
    events   = load_dir(data_dir / "events",     errors)
    refs     = load_dir(data_dir / "references", errors)
    said_did = load_dir(data_dir / "said-did",   errors)

    # ── Outlets (list | {meta,outlets} | legacy keyed dict) ───────────────────
    outlets = load_outlets(data_dir, errors)
    outlet_ids = {o["outlet_id"] for o in outlets if isinstance(o, dict) and "outlet_id" in o}

    # ── Narrative threads ─────────────────────────────────────────────────────
    threads_raw = load_json(data_dir / "meta" / "narrative-threads.json")
    if threads_raw is None:
        warnings.append("meta/narrative-threads.json not found — thread checks skipped")
        thread_ids = None
    else:
        thread_ids = extract_vocab(threads_raw, "threads")

    # ── Vocabularies (meta/) ──────────────────────────────────────────────────
    valid_cats   = extract_vocab(load_json(data_dir / "meta" / "categories.json"),
                                 "categories", "terms")
    valid_eras   = extract_vocab(load_json(data_dir / "meta" / "era-labels.json"),
                                 "eras")
    valid_rels   = extract_vocab(load_json(data_dir / "meta" / "relation-types.json"),
                                 "relation_types")
    valid_stypes = extract_vocab(load_json(data_dir / "meta" / "source-types.json"),
                                 "source_types")
    if valid_cats   is None: warnings.append("meta/categories.json absent — category checks skipped")
    if valid_eras   is None: warnings.append("meta/era-labels.json absent — era checks skipped")
    if valid_rels   is None: warnings.append("meta/relation-types.json absent — relation-type checks skipped")
    if valid_stypes is None: warnings.append("meta/source-types.json absent — source-type checks skipped")

    ref_ids   = set(refs.keys())
    event_ids = set(events.keys())

    # ── References ─────────────────────────────────────────────────────────────
    for rid, ref in refs.items():
        oid = ref.get("outlet_id")
        if oid and oid != "NEEDS-ADDITION" and oid not in outlet_ids:
            errors.append(f"references/{rid}: outlet_id '{oid}' not in outlets/records/")
        stype = ref.get("source_type")
        if valid_stypes is not None and stype and stype not in valid_stypes:
            errors.append(f"references/{rid}: source_type '{stype}' not in meta/source-types.json")
        if ref.get("verified") and not ref.get("url") and ref.get("source_type", "url_article") == "url_article":
            warnings.append(f"references/{rid}: verified=true but no url (source_type=url_article)")

    # ── Events ─────────────────────────────────────────────────────────────────
    for eid, ev in events.items():
        for rid in (ev.get("source_refs") or []):
            if rid not in ref_ids:
                errors.append(f"events/{eid}: source_ref '{rid}' not in references/")

        if valid_cats is not None:
            for cat in (ev.get("category") or []):
                if cat not in valid_cats:
                    errors.append(f"events/{eid}: category '{cat}' not in meta/categories.json")

        if valid_eras is not None and ev.get("era") and ev.get("era") not in valid_eras:
            errors.append(f"events/{eid}: era '{ev.get('era')}' not in meta/era-labels.json")

        if ev.get("claim_type") == "inference" and not ev.get("inference_note"):
            errors.append(f"events/{eid}: claim_type=inference but inference_note is missing")

        for rel in (ev.get("relations") or []):
            rtype = rel.get("type")
            if valid_rels is not None and rtype and rtype not in valid_rels:
                errors.append(f"events/{eid}: relation type '{rtype}' not in meta/relation-types.json")
            if rtype == "part_of_thread":
                tid = rel.get("thread_id")
                if thread_ids is not None and tid and tid not in thread_ids:
                    errors.append(f"events/{eid}: thread_id '{tid}' not in meta/narrative-threads.json")
            elif rtype == "jurisdiction_clarification":
                # may point to a counter-event (target_id) and/or an explainer_ref;
                # at least one is required
                tgt = rel.get("target_id")
                if not tgt and not rel.get("explainer_ref"):
                    errors.append(f"events/{eid}: jurisdiction_clarification edge needs target_id or explainer_ref")
                if tgt and tgt not in event_ids:
                    errors.append(f"events/{eid}: relation target_id '{tgt}' not in events/")
            else:
                tgt = rel.get("target_id")
                if not tgt:
                    errors.append(f"events/{eid}: '{rtype}' edge has no target_id")
                elif tgt not in event_ids:
                    errors.append(f"events/{eid}: relation target_id '{tgt}' not in events/")

        sdref = ev.get("said_did_ref")
        if sdref and sdref not in said_did:
            errors.append(f"events/{eid}: said_did_ref '{sdref}' not in said-did/")

    # ── Said-did ───────────────────────────────────────────────────────────────
    for sid, sd in said_did.items():
        for rid in (sd.get("source_refs") or []):
            if rid not in ref_ids:
                errors.append(f"said-did/{sid}: source_ref '{rid}' not in references/")

    # ── Outlet facts: verified facts must carry a source_url ──────────────────
    need = {"value", "verified", "evidence_type", "source_url"}
    for o in outlets:
        if not isinstance(o, dict):
            continue
        for fk, fv in (o.get("facts") or {}).items():
            if isinstance(fv, dict) and fv.get("verified") is True and not need.issubset(fv.keys()):
                missing = need - set(fv.keys())
                warnings.append(
                    f"outlets/{o.get('outlet_id')}: verified fact '{fk}' missing {sorted(missing)} "
                    f"(source it or set verified=false)"
                )

    # ── Report ─────────────────────────────────────────────────────────────────
    print(f"VALIDATE  {data_dir}")
    print(f"  {len(events)} events  {len(refs)} references  "
          f"{len(said_did)} said-did  {len(outlet_ids)} outlets")

    for w in warnings:
        print(f"  WARN  {w}")

    if errors:
        for err in errors:
            print(f"  FAIL  {err}")
        print(f"\nVALIDATION FAILED — {len(errors)} error(s). Build will not run.")
        return 1

    print(f"  PASS — {len(warnings)} warning(s), 0 errors")
    return 0


if __name__ == "__main__":
    data_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    sys.exit(main(data_dir))
