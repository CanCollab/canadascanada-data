# Explainer Layer: Schema Specification

The explainer layer is how the project educates instead of accuses. Where
a claim turns on something the public may not know (who holds
jurisdiction, what a law already duplicated, whether a "health" dollar
is actually bound to health), the record links to a neutral, sourced
explainer instead of leaning on a charged adjective.

This document specifies the explainer record shape, how events attach
to explainers, how explainers render, and the validator rules that
enforce both. It is the canonical reference for anyone authoring,
extending, or forking the explainer subsystem.

For the overall system contract, see
`CanadaScanada_Design_Standard_v3_4.md` section 5.7. For the rules
governing every published claim, see `METHODOLOGY.md`. For the
operational rules the project commits to, see `ETHICS.md`.

---

## 1. Record shape

Explainer records live at `explainers/EXP-<slug>.json`. One record per
file.

```json
{
  "id": "EXP-bike-lane-jurisdiction",
  "schema_version": "3.0.0",
  "type": "jurisdiction",

  "title":   { "en-CA": "City and provincial roles for local roads and bike lanes",
               "fr-CA": null },
  "summary": { "en-CA": "Local streets, including their bike lanes ...",
               "fr-CA": null },
  "body":    { "en-CA": null,
               "fr-CA": null },
  "key_points": [
    { "en-CA": "Albertans elect a city or town council to run their municipality ...",
      "fr-CA": null }
  ],

  "ai_translated": { "fr-CA": false },

  "applies_to": ["municipal_jurisdiction"],
  "source_refs": ["R-mga", "R-calgary-bike-infrastructure"],
  "related_explainers": [],

  "needs_verification": true,
  "evidence_status": "established",
  "update_log": [],
  "submission_source": "editorial",
  "submission_status": "accepted",
  "extensions": {}
}
```

### Translatable fields

`title`, `summary`, `body`, and each entry in `key_points` are
**locale maps**: objects keyed by BCP-47 locale codes (`en-CA`,
`fr-CA`, `iu-CA-Latn`, and so on). `en-CA` is required on every
translatable field; other locales may be `null` until authored.

When a target locale value is `null` at render time, the build falls
back to `en-CA`. No card ever renders an empty Context block because
of a missing translation.

`summary` is the card-side blurb shown inline on the event. `body` is
the fuller text for a dedicated page. Keep `summary` self-sufficient
so a card never depends on the page being read. `body` and
`key_points` are optional; author them only where they add value
beyond what the summary conveys.

### `ai_translated`

A per-locale map indicating whether each translation was machine-
drafted. `{"fr-CA": true}` means the French version is AI-assisted and
pending human review; `false` means it has been reviewed and signed
off. `en-CA` (authored content) does not carry an `ai_translated`
entry.

### `type`

The kind of concept the explainer documents. Validator-enforced
vocabulary in `meta/explainer-types.json`:

| Type | What it covers | Example |
|---|---|---|
| `jurisdiction` | Who has authority over what | Bike lanes, healthcare, education |
| `legal_status` | Facts about a specific statute | Bill 18, Bill 22, Education Act |
| `funding` | How money flows from one level to another | Federal transfers, equalization |
| `standard` | A legal or institutional norm | Notwithstanding clause, paramountcy |
| `term` | A general concept or mechanism | Fungibility, prior legal status |
| `process` | A repeated procedure | Royal Assent, parliamentary order |

The vocabulary is domain-agnostic by design. A forking operator may
extend it; the structure stays the same.

### `evidence_status`

A closed four-value vocabulary describing the lifecycle state of the
explainer's content:

| Value | Meaning |
|---|---|
| `established` | Default. Sourced, stable, no known issues. |
| `reviewed` | A human re-checked the content recently. Audit-trail marker. |
| `updated` | Content materially changed after first publication. Pairs with `update_log[]`. |
| `superseded` | Replaced by another record. Suppressed by the publication gate. |

Only `superseded` currently changes rendering behaviour (the explainer
is hidden from the public build). The other three are honest audit
metadata until consumed by future tooling.

### `applies_to`

An array of inert classification tags. Used for search and discovery
only. **Never an automatic render join.** Attachment of an explainer
to an event is always explicit (see section 2).

Implicit tag-matching would surface explainers on events the editor
never vetted, breaking the per-record editorial control the
publication gate rests on.

### `source_refs`

An array of reference record IDs that source the explainer's content.
**An explainer with no sources is not publishable.** Each referenced
ID must resolve to a verified reference record in `references/`.

### `related_explainers`

An array of other explainer IDs that share scope or expand on the
concept. Renders as cross-links (in the future) but does not affect
the publication gate.

### Publication gate fields

`needs_verification` (boolean), `evidence_status` (vocab above), and
`source_refs` together govern whether the explainer renders publicly.
The gate is the same as for events and references: only verified
records with verified sources reach a reader.

### Other fields

`update_log[]` is the append-only correction history. `extensions{}`
holds experimental fields with no version bump. `submission_source`
and `submission_status` track the editorial pipeline.

---

## 2. How events attach to explainers

Attachment is **explicit only**. The event (or an edge on it) names
the explainer's `id` directly. Two hooks exist:

1. **Card-level**: `explainer_refs: []` array on the event itself,
   for "this record needs context X."
2. **Edge-level**: the existing `explainer_ref` field on a
   `jurisdiction_clarification` edge.

If the same explainer ID is reachable through both hooks on one card,
render it once. The card-level Context block wins; the edge still
links inline.

An explainer link renders only if the explainer's
`needs_verification` is `false` and its sources are verified, the
same gate as every other publishable thing.

---

## 3. Rendering rules

### The Context block

A uniform **"Context"** annotation block on the event card, a sibling
to the existing Inference, Connections, and Response blocks. Shows
the explainer's `summary` plus source attribution. Same styling
discipline as other annotation blocks: no special colour, no verdict
tone.

### Dedicated pages (post-MVP)

If the explainer has a non-null `body` field for the rendered locale,
the Context block links to a dedicated page at
`explainers/EXP-<slug>.html`. If `body` is `null`, no page exists;
the block renders inline-only.

MVP is summary-inline only. Dedicated pages come later. Author `body`
only when there is content that earns its own page.

### `en-CA` fallback

When the reader's selected locale has no authored content for a
translatable field, the renderer falls back to `en-CA`. Any other
locale's content takes precedence over the fallback when present.

---

## 4. Validator rules

`scripts/validate.py` enforces the following rules. The standard
warning-first promotion path applies (a rule begins as a warning and
becomes an error once coverage is high).

| Rule | Severity |
|---|---|
| `explainer_refs[]` and edge `explainer_ref` must resolve to an `explainers/` record | warning, promoting to error |
| `type` must be in `meta/explainer-types.json` | error |
| `evidence_status` must be one of the four vocabulary values | error |
| Explainer with empty `source_refs[]` | error (explainers must be sourced) |
| `title.en-CA` must be present (not null) | error |
| Any locale present in a sibling field but missing here | warning |
| Locale keys must be well-formed BCP-47 | warning |

---

## 5. Authoring guidance

When writing a new explainer:

- **Concept explainers are stable and generic.** A concept explainer
  explains a mechanism. It must not carry a worked example captioned
  "here is a government doing the bad thing," because that turns the
  explainer into the accusation it exists to defuse. A specific
  contested case is an *event* that links *up* to the stable concept.
- **Title is a flat noun phrase, never a question.** Interrogative
  titles import a frame that implies a contested answer. Use "City
  and provincial roles for local roads and bike lanes," not "Who
  controls bike lanes?"
- **Summary is self-sufficient.** A card must never depend on the
  (often-null) `body` to make sense. The summary carries the whole
  record alone.
- **Name mechanisms, not abstractions.** "Can alter them through
  legislation" hides the thing a reader wants: how. Write the
  mechanism: "by passing a law through a vote in the Legislature."
- **Relevance through recognition and utility, never stakes-
  inflation.** Anchor the concept to something the reader has lived
  (the health care they use, the property tax they pay). Frame the
  explainer as a reading skill ("here is what to check next time you
  see a number"). Never raise the stakes ("this could affect *your*
  hospital").
- **Symmetric treatment of all sides.** If a mechanism is illustrated
  with one party or position, illustrate it with the others where
  examples exist.

The full editorial guidance is governed by an internal style
discipline the project maintains for its own authors. Forking
operators are encouraged to develop their own equivalent.

---

## 6. Current seed explainers

The repository ships with four seed explainers, all currently
`needs_verification: true`:

| ID | Type | Concept |
|---|---|---|
| `EXP-bike-lane-jurisdiction` | jurisdiction | Municipal vs. provincial authority over local roads and bike lanes |
| `EXP-notwithstanding` | standard | The notwithstanding clause: scope, limits, history |
| `EXP-fungible-funding` | funding | Why "named" budget allocations don't always go where labelled |
| `EXP-prior-legal-status` | term | Concurrent jurisdiction and federal paramountcy |

These records show the schema in action. Read them alongside this
spec to understand the conventions.

The explainer rendering layer is not yet wired into the build. Once
Track A (explainer rendering) ships, these four become live on the
public timeline.

---

## 7. Extending the schema

The procedure for adding a new field, a new vocabulary value, or a
new explainer type is documented in `ADDING_A_FIELD.md`. Briefly:

- New fields are additive and optional-with-default.
- Validator rules start as warnings and promote to errors once
  coverage is high.
- Experimental fields live in `extensions{}` or as their own
  referencing record, never stamped inline onto every existing
  record.
- A new explainer type means adding to `meta/explainer-types.json`
  and authoring a seed record demonstrating the type.

---

## 8. Forking

When forking this project (see `FORKING.md`):

- The explainer schema is portable. Use it as-is.
- The vocabulary (`meta/explainer-types.json`) is portable. Extend
  for your jurisdiction's needs.
- The seed explainers shown in section 6 are Alberta-specific. A
  fork should replace them with its own jurisdiction's seed concepts
  (provincial vs. municipal authority for your province, your
  jurisdiction's analogue to the notwithstanding clause if any, your
  funding mechanisms, your shared-jurisdiction terms).
- Editorial style for explainers is the fork operator's choice. The
  schema does not enforce voice; the validator only enforces shape.
