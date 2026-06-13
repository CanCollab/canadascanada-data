# Adding a Field or Factor

The decision procedure for any new data point, descriptor, or factor. The goal is
that adding one is cheap by default and never forces a rebuild. Run a candidate
through the questions below before touching the schema.

## The one rule that prevents monoliths

Every byte is either an **independent per-file source record** or a **fully
regenerable derived artifact**, and a derived artifact is never hand-edited. A
monolith forms the moment something derived (a combined file, an index) quietly
becomes the place you actually make changes. Indexes and `_manifest.json` are
derived order; regenerate them, never edit them by hand.

## Pick the right shape first (this decides the cost)

- **Attribute of one existing thing** (a date qualifier, a flag): an optional field,
  or `extensions{}` while experimental. No new machinery.
- **New allowed value of an existing attribute** (another category, era, discrepancy
  type): a one-line `meta/` edit. Zero code change; vocab lives in data.
- **Relationship between two things** (a new kind of connection): a relation type in
  `meta/relation-types.json`, stored once on the source record, inverse derived. No
  record-shape change.
- **New kind of thing with its own identity, sources, and lifecycle** (entities,
  explainers): a new directory + index + validator rule + render. Heaviest, but
  additive: it layers onto a green tree without touching existing records.
- **Cross-cutting descriptor that would apply to many record types at once**: do NOT
  stamp it inline on every record, that is the one move that manufactures a
  corpus-wide migration. Model it as its own referencing record, a sidecar, or a
  derived view, so the existing corpus stays untouched and the factor joins in.

## Cost tiers

| The new field is... | Version bump | validate.py | Backfill | Net burden |
|---|---|---|---|---|
| In `extensions{}`, optional, unrendered | none | none | none | effectively free |
| Core, optional, sensible default (`null`/`[]`) | additive | optional rule | script sets default, no judgment | low |
| Core, optional, locale-map, reader-facing | additive | shape rule | default script | low-moderate (cost is parity in both languages in build.py) |
| Core, **required**, needs per-record human judgment | major | required rule | one judgment-unit per record | high, Spine-1 red flag |

Only the last row is expensive, and you never have to land there directly. The
escape valve: add the field optional, populate it opportunistically as records are
touched, and promote it from a `validate.py` warning to an error once coverage is
high. This is the path already used for outlet `source_url` and the pending-rating
outlet state.

## The invariants that keep it scaling

- One record per file; blast radius is always the files you chose to touch.
- Indexes and manifests are derived order, never the source of truth.
- Vocabulary in `meta/`; code stays domain-agnostic. New enum values are data edits.
- `extensions{}` absorbs anything experimental: no version bump, no validator change.
- Additive and optional-with-default for core fields.
- Per-record `schema_version`: migrate record by record; a half-migrated corpus is
  still valid; there is no flag day.
- Derive, do not store, anything computable (inverse edges, thread membership,
  derived ownership percentage). Derived data never needs a backfill.

## The honest exception

Some changes legitimately touch every record (the locale-map migration). Per-file
does not make that free; it makes it **safe and resumable**: a scripted, idempotent
sweep, validator as the net, one clean diff per file, revert per file. The same
change on a monolith is a single giant rewrite where one serialization error loses
the corpus. So per-file converts a big-bang rebuild into an incremental sweep you can
stop and resume. The worst case of any single failure is one record, recoverable
from the diff. You never rebuild a file.
