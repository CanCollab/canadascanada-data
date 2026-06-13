# Changelog

Version history for the schema, platform, and reader-facing
documents.

This changelog covers the public repository (`canadascanada-data`).
Internal operator changes (workflow scripts, drafts, research)
are tracked in the project's private working repository.

## Format

```
## YYYY-MM-DD · component · brief description
```

Entries are in reverse chronological order (most recent first).

---

## Initial public release

The public repository goes live with:

- **Schema family:** 3.x. All event and reference records at
  `schema_version: 3.0.0`.
- **Corpus state:** 112 events, 242 references, 46 outlet records.
  40 events published, 72 suppressed pending pre-launch verification
  sweep.
- **Design Standard:** v3.4 (current). See
  `CanadaScanada_Design_Standard_v3_4.md`.
- **Foundation pipeline:** Step 0 (consolidation) complete. Step 1
  (locale-map migration to BCP-47 shape) imminent. Steps 2-4 (entity
  registry, accessibility, internet archive) planned.

## Schema versioning

Records carry per-record `schema_version`. The validator and build
tolerate the live version range, so the corpus migrates record by
record. There is no flag day.

Schema family changes (e.g. 3.x to 4.x) are announced here with a
migration script and a transition window. Most changes are additive
within a family and require no record migration.

## Document changes

When this repository's documents change in ways that affect readers
(privacy posture, terms of use, methodology), the change is logged
here with the date.

When the schema itself changes (a new vocab term, a new field, a new
relation type), the change is logged here and the validator is
updated in the same commit.

## How to read past versions

Every document and every record is fully version-controlled in git.
To see what changed between two dates, use:

```
git log --since=YYYY-MM-DD --until=YYYY-MM-DD --follow <filename>
```

Or browse the repository's commit history on GitHub.
