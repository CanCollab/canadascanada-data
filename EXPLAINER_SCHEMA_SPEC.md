# Explainer Layer — Schema & Process Spec

**Status:** SIGNED OFF (all four open questions resolved; see section 6).
**Design Standard:** new section 5.7 (Explainers) · **Depends on:** BCP-47 locale-map decision (locked)
**Companion:** `EXPLAINER_RHETORIC_GUIDE.md` (the voice; this is the shape).

The explainer layer is how the project **educates instead of accuses**. Where a claim turns on
something the public may not know (who holds jurisdiction, what a law already duplicated, whether a
"health" dollar is actually bound to health) the record links to a neutral, sourced explainer
instead of leaning on a charged adjective. It is the structural backstop for section 4 of the
Verification Checklist.

Explainers are the **pilot for the locale-map language shape**: every translatable field is a
BCP-47-keyed object, so adding a language later is a new key, never a schema change.

---

## 1. Record shape — `explainers/EXP-<slug>.json`

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

**Field notes**
- **Translatable fields** (`title`, `summary`, `body`, each `key_points` entry) are locale maps.
  `en-CA` is required; other locales may be `null` until authored. `body` and `key_points` are optional.
- **`summary`** is the card-side blurb. **`body`** is the fuller text for a dedicated page. Keep
  `summary` self-sufficient so a card never depends on the page (Rhetoric Guide Rule 3.1).
- **`ai_translated`** is a per-locale map; `true` means machine-drafted, pending human review.
- **`type`** is validator-enforced vocab in `meta/explainer-types.json`:
  `jurisdiction · legal_status · funding · standard · term · process`. Domain-agnostic by design.
- **`evidence_status`** is validator-enforced vocab (resolved this session, see section 6):
  `established` (default, sourced and stable) · `reviewed` (a human re-checked it; audit trail) ·
  `updated` (content materially changed post-publication; pairs with `update_log`) ·
  `superseded` (replaced; suppressed by the gate exactly as events are). Only `superseded` changes
  render behaviour today; the rest are honest audit metadata until something consumes them.
- **`applies_to`** are **inert classification tags for search/discovery only** (resolved, section 6).
  They are NEVER an automatic render join. Attachment to an event is always explicit.
- **Explainers are sourced like events.** `source_refs` must resolve to verified references; an
  explainer with no sources is not publishable.

## 2. How events reference an explainer (RESOLVED: both hooks)

1. **Card-level:** `explainer_refs: []` array on the event, for "this record needs context X."
2. **Edge-level:** the existing `explainer_ref` on a `jurisdiction_clarification` edge.

Attachment is **explicit only** — the event (or edge) names the explainer `id`. `applies_to` is
descriptive metadata, never a join. Implicit tag-matching would surface explainers on events the
editor never vetted, breaking the per-record editorial control the whole gate discipline rests on.

**Dedupe guard:** if the same explainer id is reachable both card-level and edge-level on one card,
render it once (the card-level Context block wins; the edge still links inline).

An explainer link renders only if the explainer's `needs_verification` is false **and** its sources
are verified, the same gate as every other publishable thing.

## 3. Rendering (build.py — implementation task, after sign-off)

- A uniform **"Context"** annotation block on the card (sibling to Inference / Connections /
  Response), showing the explainer `summary` plus source attribution. Same styling discipline: no
  special colour, no verdict tone. (RESOLVED: reader-facing label is "Context".)
- A `jurisdiction_clarification` edge whose `explainer_ref` resolves renders its "Jurisdiction"
  connection row linked to the explainer.
- **MVP is summary-inline only** (RESOLVED). `body` is authored only where it adds value beyond the
  summary; otherwise it stays `null` and there is no page to link. The Context block links to a
  dedicated page only if `body` exists. Dedicated `explainers/EXP-<slug>.html` pages come later.
- **`en-CA` fallback:** when a target locale value is `null`, the renderer falls back to `en-CA`
  (build.py task). No card ever renders an empty Context block because of a missing translation.

## 4. Validator additions (`validate.py` — warning-first, then promote)

- `explainer_refs[]` / edge `explainer_ref` resolve to an `explainers/` record — **warning** now,
  **error** once adopted (mirrors the `source_url` rollout).
- `type` in vocab — **error**.
- `evidence_status` in vocab — **error**.
- explainer with empty `source_refs` — **error** (explainers must be sourced).
- `title.en-CA` present — **error**; any locale present in a sibling field but missing here — **warning**.
- locale keys are well-formed BCP-47 — **warning**.

## 5. Seed records (AUTHORED this session — all `needs_verification: true` pending sources)

| id | type | status | sources needed before it can render |
|----|------|--------|--------------------------------------|
| `EXP-bike-lane-jurisdiction` | jurisdiction | authored | `R-mga` (load-bearer, province-wide), `R-prov-infrastructure-funding` still to author; `R-calgary-bike-infrastructure` + `R-calgary-traffic-bylaw` authored, `verified:false` pending sign-off |
| `EXP-notwithstanding` | standard | authored | `R-charter-s33`, `R-constitution-1982-history`, `R-alberta-legislative-process` |
| `EXP-fungible-funding` | funding | authored | `R-federal-transfer-framework`, `R-provincial-budget-docs`, `R-public-accounts`, `R-alberta-education-funding` |
| `EXP-prior-legal-status` | term | authored | `R-constitution-division-powers`, `R-paramountcy-doctrine` |

## 6. Sign-off record — the four open questions, RESOLVED

1. **`legal_status` granularity.** Per-law instances under the `legal_status` type carry the facts
   about a specific statute. The generic concept note is typed **`term`** (NOT `legal_status`),
   because it defines a mechanism (concurrent jurisdiction + federal paramountcy) rather than
   asserting a status about a law. Slugs drop the year unless two same-named laws collide
   (`EXP-education-act-prior-status`, not `EXP-2024-...`), since the date is an error-prone field
   the verification worklist already flags.
2. **`explainer_refs[]` on events vs edge-only.** Both, with a dedupe guard (section 2).
3. **Dedicated pages at MVP.** Inline-only at MVP. `body` null unless it earns a page.
4. **Render block name.** "Context."

Additional decisions locked this session:
- **Attachment is explicit; `applies_to` is inert** (section 1, section 2).
- **`evidence_status` is a closed vocab** of four values (section 1).
- **`en-CA` fallback** for null locales is a render rule (section 3).

### 6a. Priority next explainers

These are the highest-priority next explainers based on coverage gaps in
the current corpus. Each is sized to be a single concept explainer with a
non-null `summary` field and a `body` that may or may not be authored
depending on whether the concept earns its own page.

| Proposed ID | Type | Concept | Why it's needed |
|---|---|---|---|
| `EXP-bill18-paramountcy` | standard | The constitutional doctrine of federal paramountcy and how Bill 18 (Provincial Priorities Act) interacts with it | Multiple Bill 18 events in the corpus reference the legal-mechanism question without an explainer to point at |
| `EXP-charter-section-2` | standard | Charter section 2 freedoms (expression, association, peaceful assembly) and how section 33 interacts with them | Companion to the notwithstanding explainer; needed when events describe legislation that engages s.2 rights |
| `EXP-cabinet-confidentiality` | term | Cabinet confidentiality as a parliamentary norm: what it covers, what it doesn't, and how legislative privilege relates | Relates to the Guthrie cabinet notes event and any future events about leaked internal deliberations |
| `EXP-federal-transfers` | funding | How federal transfers to provinces work: the Canada Health Transfer, Canada Social Transfer, equalization, and bilateral agreements | Multiple events touch federal-provincial funding mechanics; the fungible-funding explainer addresses the general principle but not the specific transfer structures |
| `EXP-electoral-boundaries-process` | process | Alberta's electoral boundaries commission: how lines are drawn, when, by whom, under what oversight | Relates to EVT-112 (boundaries final report) and future events on the implementation of new boundaries |
| `EXP-anti-slapp` | term | Anti-SLAPP legislation in Canada: which provinces have it, what it does, what Alberta does not have | Relevant context for any defamation-adjacent event and for the project's own legal exposure posture |
| `EXP-conflict-of-interest-commissioner` | term | The Alberta Ethics Commissioner's role, the conflict-of-interest framework, and the limits of the office | Relates to multiple events about ministerial conduct and procurement decisions |

### Authoring order

A reasonable order to author these in is:

1. `EXP-charter-section-2` (highest leverage, supports several existing
   events plus the notwithstanding explainer's missing companion piece)
2. `EXP-bill18-paramountcy` (multiple existing events point at this
   mechanism)
3. `EXP-federal-transfers` (concrete and substitutable for several
   fungible-funding references)
4. `EXP-cabinet-confidentiality` (single high-leverage event motivates it)
5. `EXP-electoral-boundaries-process` (a small number of events need it)
6. `EXP-conflict-of-interest-commissioner` (helpful but not load-bearing
   for any single event)
7. `EXP-anti-slapp` (most useful as background for the project's own
   posture; can defer to post-launch)

### Authoring discipline (carried forward from section 5)

Each new explainer:

- Is a stable, generic concept explainer. No worked examples of specific
  governments doing specific things. The specific contested case is an
  event that links up to the stable concept.
- Title is a flat noun phrase, never a question.
- Summary is self-sufficient.
- Names mechanisms, not abstractions.
- Anchors relevance through recognition and utility, never stakes-inflation.
- Treats all sides symmetrically.
- Carries `source_refs[]` to verified reference records before publishing.
- Ships as `needs_verification: true` initially; the operator flips after
  review.

### What this list is not

This is not a frozen commitment. The operator may add explainers not on
this list as the corpus grows, or skip ones on this list if they turn out
to be unnecessary. The list represents priorities based on current
corpus coverage; it should be revisited each time a content batch is
authored.
