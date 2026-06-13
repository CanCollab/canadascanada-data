# CanadaScanada, System and Data Design Standard

**Standard version:** 3.4 · **Schema family:** 3.x · **Status:** current (supersedes 3.3)

This document is the canonical reference for the project's data layer,
information architecture, validation contract, and visual design system.
It describes the system as built and committed (with target-state
additions clearly marked), not its history; where a rule exists, it is
the rule now.

Read this first in any new working session. For the operating principles
the project commits to, see `PRINCIPLES.md`. For the contribution and
fork workflow, see `FORKING.md`. For the visual design kickoff (UX
thread), see `FRONTEND_UX_KICKOFF.md`. This document is the contract; the
others are the application.

---

## 1. Governing principles

Load-bearing. Every structural decision below traces to one of these.

- **Facts with provenance, never verdicts.** The system conveys
  structured, sourced information and lets the reader judge. No scores,
  grades, rankings, or summary characterizations of an outlet or actor.
- **Name the pattern, not the opponent.** Records and framing describe
  what happened and who acted in their official role. No motive, no
  "hypocrisy/deflection/scapegoat" language, even where the facts
  invite it. The reader concludes.
- **Educate over accuse.** Where a tension turns on something the
  public may not know (division of powers, funding mechanics,
  journalistic standards, CRTC rules), the answer is an explainer, not
  a sharper adjective. The "hate the game, not the player" posture made
  structural.
- **Statements are events.** A documented public statement is a sourced
  event like any action. There is no separate class of "claims"
  floating outside the timeline.
- **Connections are edges, not categories.** A contradiction or
  jurisdictional clarification is a typed relationship over the event
  graph, never a dedicated "gotcha" filing system.
- **Transparency as the immune system.** The validator and the
  publication gate are the mechanism that makes the project trustworthy.
  Unsourced or unverified material is preserved for provenance but never
  reaches a reader. Strengthening these checks is always in scope;
  weakening one to make a record pass is the compromise the project
  exists to refuse.
- **Domain-agnostic by construction.** Vocabulary and content live in
  `meta/` and data, never in code. The schema is portable to any
  accountability domain; structural field names never hard-code a
  country or party.
- **Reader-mode parity.** Styled view and reader-mode view must carry
  identical sourced facts and neutral framing. Meaning lives in
  semantic HTML; modern CSS is progressive enhancement only.
- **CP Style** governs all prose fields.

---

## 2. System architecture

Two products over one shared, flat JSON data layer.

| Product | Domain | Renders |
|---|---|---|
| **CanadaScanada** (`canadascanada.ca`) | political accountability timeline | sourced event timeline, on-card connections (discrepancies, jurisdiction, threads), memos |
| **Outlet-label layer** (name pending, see DECISIONS_LOG entry 27) | media literacy | facts-only "nutrition-label" outlet labels with browser-extension lookup |

**Stack discipline.** Zero JavaScript on the public site. Plain HTML and
CSS. Flat JSON data. No framework, no runtime build step. JSON authored
per record, served via GitHub raw URLs, pre-rendered to static HTML by
`build.py` behind a validation gate, hosted on GitHub Pages.

**Data flow.** Author or contribute JSON, `validate.py` (gate),
`build.py` pre-renders `docs/`, GitHub Pages serves.

---

## 3. Repository layout (`canadascanada-data`)

```
events/                EVT-###.json           one event per file (statements and actions alike)
references/            R-###.json             one source per file
outlets/
  records/<id>.json                           one outlet per file, facts-only
  records/_manifest.json                      outlet display order (order-as-data)
explainers/            EXP-###.json           the educational layer (5.7)
meta/
  schema-version.json
  categories.json                             locked category vocabulary
  relation-types.json                         locked edge vocabulary
  discrepancy-types.json                      qualifiers for conflicts_with edges
  discrepancy-backlog.json                    discrepancy leads with no event records yet
  source-types.json
  era-labels.json
  narrative-threads.json                      thread definitions (no member lists)
  feed-map.json                               RSS capture configuration
  keyword-filter.json                         RSS capture filter terms
scripts/
  validate.py                                 the gate
  build.py                                    pre-render pipeline
  state.py                                    ground-truth guard
  regen_manifest.py                           outlet manifest reconciliation
  split_outlets.py                            historical migration script
  migrate_locale.py                           locale-map migration (Step 1)
  rss-pipeline.py                             capture loop (zero-LLM filter)
  intake.py                                   submission email parser (planned)
  build_review.py                             operator-side review page generator (planned)
  apply_decisions.py                          submission to corpus writer (planned)
docs/                                         generated site (gitignored)

Top-level documentation in the public repo:
  README.md                                   project overview and links
  LICENSE-data.md                             CC-BY-4.0 statement for the corpus
  LICENSE-editorial.md                        all-rights-reserved for editorial content
  LICENSE.md                                  combined pointer
  CONTRIBUTING.md                             high-level contribution guide
  FORKING.md                                  recipe for forking the project
  ETHICS.md                                   reader-facing principles statement
  ADDING_A_FIELD.md                           operator procedure for schema extension
  EXPLAINER_SCHEMA_SPEC.md                    schema documentation
  CORRECTIONS.md                              append-only public corrections log
  CHANGELOG.md                                schema and platform version history
  CanadaScanada_Design_Standard_v3_4.md       this file

Planned (not yet built):
entities/              ENT-### or registry    the search and identity layer (5.6)
```

The `said-did/` collection has been retired; its contents migrated to
graph edges (5.4). The `said_did_ref` field on events is deprecated
(inert `null` values may remain pending a sweep). The legacy combined
monolith is deleted; the per-file tree (`events/`, `references/`,
`outlets/records/`) is the sole source of truth.

### 3.1 Invariants (the anti-monolith contract)

One record per file. Indexes and manifests are derived or curated order,
never the source of truth for what exists. Vocabulary lives in `meta/`;
code stays domain-agnostic. `extensions{}` absorbs experimental fields
with no version bump. Core fields are additive and optional-with-default;
a `validate.py` warning is promoted to an error once coverage is high.
Derive, do not store, anything computable (inverse edges, thread
membership, derived ownership percentage). The procedure for adding any
new field or factor is `ADDING_A_FIELD.md`; the cross-thread work-order
format is `FOUNDATION_PIPELINE.md`.

---

## 4. Controlled vocabularies (`meta/`)

Authoritative and validator-enforced. Records may only use values
defined here; extend by editing the `meta/` file, never inline. `meta/`
defines the full vocabulary; the set actually in use is a subset,
reported by `scripts/state.py`. Do not prune a term merely because it
is currently unused (a category defined but not yet applied, or a
relation type whose inverse is derived rather than authored).

- **categories (21):** science_suppression, media_suppression,
  healthcare_privatization, fiscal, labour, education, charter,
  constitutional_override, democratic_process, electoral_process,
  privacy, transparency, accountability, energy, environment,
  federal_provincial, political_convoy, separatism, party_discipline,
  lgbtq, diagolon. Neutral framing is deliberate.
- **relation_types:** part_of_thread, enables and enabled_by,
  responds_to and prompted, **conflicts_with**,
  **jurisdiction_clarification**, same_actor, same_legislation,
  financial_link, supersedes and superseded_by. (`contradicts` removed,
  superseded by the broader `conflicts_with`.)
- **discrepancy_types** (qualifier on `conflicts_with`):
  reversed_position, promise_broken, position_vs_outcome,
  claim_vs_evidence.
- **source_types (7):** url_article, wire_article, primary_record,
  government_statement, finding_tool, video_transcript, pasted_text.
- **eras (3):** pre2019, kenney, smith. Domain-specific; replace
  wholesale when porting.

---

## 5. Record types

### 5.1 Event (`events/EVT-###.json`)

The atomic unit. Statements and actions are both events.

- **Identity and timing:** `id`, `schema_version`, `event_date`,
  `event_date_precision` (`day|month|year|approximate`), `date_notes`.
- **Content:** translatable fields in the locale-map shape
  (`{en-CA, fr-CA, ...}`), `ai_translated` flag, `era`, `category[]`.
  (Pre-Step-1 records still use flat `_en`/`_fr` fields; the migration
  is record by record.)
- **Epistemics:** `claim_type` (`fact|context|inference`);
  `inference_note` required when `inference`.
- **Actors:** `actors[]` of `{display_role, name, party, jurisdiction}`
  (official role only). `entity_ids[]` is the planned stable link
  (5.6).
- **Sourcing and graph:** `source_refs[]`, `relations[]` (5.4),
  deprecated `said_did_ref`.
- **Gate:** `needs_verification`, `evidence_status`, `standards_flags[]`,
  `verification_notes`, `community_can_verify`, `verification_prompt`.
- **Contestability:** `claim_contested_by[]` of
  `{actor, position, source_ref}`; `opposition_response`.
- **Provenance:** `submission_source`, `submission_status`, append-only
  `update_log[]`, `extensions{}`.

### 5.2 Reference (`references/R-###.json`)

`id`, `title`, `outlet`, `outlet_id`, `section`, `author`,
`publication_date`, `url`, `source_type`, `url_status`, `archived_url`,
`tier`, `verified` (gate-critical), `wire_source`, `notes`, submission
fields. Published claims must resolve to a `verified: true` reference.

### 5.3 Outlet (`outlets/records/<id>.json` + manifest), facts-only

One record per file; display order curated in `_manifest.json`,
reconciled by `scripts/regen_manifest.py`. No score, grade, or verdict.
Three states:

- **Rated** (`rated: true`): `outlet_id, name (locale-map), outlet_type,
  ownership_pct_canadian_derived, ownership_breakdown[], facts{},
  accountability{}, citable`. Each `facts{}` entry carries
  `{value, verified, evidence_type, source_url}`. Only `verified: true`
  facts render; a verified fact must carry a `source_url`
  (validator-checked). Absence of a fact is neutral, never a penalty.
- **Not-rated** (`rated: false`): government or primary, advocacy or
  research, or single-subject sources. `not_rated_reason` populated;
  no fact rows.
- **Pending rating** (record exists, no rating authored yet): renders
  "Canadian ownership: Pending." This is `none_found-with-receipt`
  applied to outlet metadata, the honest state rather than a blank or
  a penalty. A new outlet ships in the same commit as the references
  citing it, and its id is appended to the manifest order.

### 5.4 Connections, the relations graph (replaces said-did)

Connectivity lives entirely in event `relations[]`. An edge is stored
once on the lower-id (source) event; the build derives the inverse so
it renders on both events' cards. An event may carry any number of
edges of any types; a reader landing on any node sees every connection
and can traverse from there ("enter the chain anywhere"). There is no
separate connection record type and no toggle or destination page;
edges render inline on cards, all types alike.

Edge shapes:

- **Thread membership:** `{type: "part_of_thread", thread_id}`. The
  container for multi-event arcs (e.g. a procurement scandal, a
  campaign).
- **Causal or associative:**
  `{type: "enables"|"responds_to"|"same_actor"|"same_legislation"|"financial_link"|"supersedes", target_id, note?}`.
- **Discrepancy**
  (`{type: "conflicts_with", target_id, discrepancy, framing (locale-map), source_refs[], claim_type, needs_verification}`):
  two sourced events in documented tension. `discrepancy` qualifies the
  shape (4); `framing` is the factual reader-facing sentence (no
  verdict); `source_refs` support the connection (typically drawn from
  the two endpoints). Reader-facing noun: "Discrepancy."
- **Jurisdiction**
  (`{type: "jurisdiction_clarification", explainer_ref, target_id?, framing (locale-map), source_refs[], claim_type, needs_verification}`):
  an event attributes responsibility or outcome to an external party;
  the clarification documents actual jurisdiction and funding. Requires
  `explainer_ref` (the educational payload, 5.7) and a counter-event
  `target_id` or both. Framing states only the documented sequence; the
  explainer educates. Coexists with `conflicts_with` on the same event,
  so a reader arriving from either chain finds the other.

### 5.5 Narrative thread (`meta/narrative-threads.json`)

Thread definitions only (title, framing, era). Membership is expressed
by `part_of_thread` edges, so red-thread visualization is a graph
query, not a maintained list.

### 5.6 Entity model (planned), the search and identity layer

Search must return everything involving a person regardless of the
role they held at the time ("Kenney" returns MLA, Opposition leader,
Premier, and after), and must also resolve non-actors (a place like
Coutts, a movement, a program like daycare).

- Registry `entities/`:
  `{ entity_id, name, type (person|organization|place|movement|program|government_body), aliases[], roles_held[], description, source_refs[] }`.
- Events gain `entity_ids[]`. Actors keep `display_role` for in-context
  labelling; `entity_ids` is the stable, role-independent link;
  non-actor involvements attach here too.
- Search and filter indexes `entity_ids`. This also lets search
  behaviour be written as test fixtures ("query Kenney returns these
  event ids") and stress-tested.

### 5.7 Explainer or education layer

Unifies the jurisdiction-education need with site-wide standards,
journalism, CRTC, and funding blurbs into one reusable subsystem.

- Records `explainers/EXP-###.json`:
  `{ id, term, title (locale-map), scope, body (locale-map), source_refs[], last_reviewed }`.
  Gated like everything else.
- Referenced via the optional `explainer_ref` hook (on jurisdiction
  edges, outlet labels, category tags). Four seed explainers authored
  (`EXP-bike-lane-jurisdiction`, `EXP-fungible-funding`,
  `EXP-notwithstanding`, `EXP-prior-legal-status`); rendering wires up
  with Track A.

### 5.8 Date model (all record types)

One pattern. `date_approx` is retired. Point in time: `date` plus
`*_precision` (`day|month|year|approximate`). Range: `{from, to}`.
Events use `event_date` plus `event_date_precision`.

---

## 6. The publication gate

`build.py::is_publishable()` decides what a reader sees. A **record**
publishes only if: `needs_verification` is false; `evidence_status` is
not `superseded`; `source_refs[]` is non-empty; every referenced
reference exists and is `verified: true`; and any `inference` carries
an `inference_note`. An **edge** publishes only if its own
`needs_verification` is false and both endpoint events publish, so a
discrepancy never references an invisible event. Failing records and
edges stay in the repo for provenance and are silently suppressed; fill
the gap and they appear.

---

## 7. Validation standard (`validate.py`)

Runs before every build; any error aborts it.

**Errors (build-blocking):** JSON parse failure; reference `outlet_id`
or `source_type` unknown; event `source_ref` unresolved; event
`category` or `era` not in vocab; `inference` without `inference_note`;
relation `type` not in vocab; `part_of_thread` `thread_id` unresolved;
non-thread edge missing or unresolved `target_id` (with
`jurisdiction_clarification` exempt when it carries `explainer_ref`);
`said_did_ref` that resolves to nothing.

**Warnings:** verified `url_article` reference with no URL; verified
outlet fact missing `source_url` (slated to become an error once
coverage is high); absent `meta/` vocab file (checks skipped).

**Per-record `schema_version` is the migration mechanism.** The
validator and build tolerate the live version range, so the corpus
migrates record by record and a half-migrated corpus stays valid. There
is no flag day. Each foundation step adds exactly one validator rule
(see `FOUNDATION_PIPELINE.md`).

`scripts/state.py` runs first as a ground-truth guard: it reports live
counts, the publish/suppress split, the next id, the `schema_version`
spread, and structural drift (monolith present, manifest and file
mismatch, duplicate ids), exiting non-zero on a hard violation.

---

## 8. Build pipeline (`build.py`)

`python3 scripts/build.py <data_dir> [<out_dir>]` (default
`. ./docs`), after `validate.py` passes. Outputs `docs/index.html`
(timeline, published events), `docs/outlets/` (labels), and JSON
indexes for the extension lookup. Vocabulary used in rendering is
sourced from `meta/`; any label maps still hard-coded in `build.py`
are portability debt to migrate. **Bidirectional rendering of
`relations[]` on event cards is live** (3b shipped). `events/index.json`
is a render index (published-eligible events, newest first); it is not
the source of the next id, scan all `events/` files or read
`scripts/state.py`. `outlets/records/_manifest.json` holds curated
display order; the record files, not the manifest, are the source of
truth for which outlets exist.

---

## 9. Visual design system

The reader's experience of the corpus is structurally constrained.
These rules define what readers see; the operator's UX-thread work
(see `FRONTEND_UX_KICKOFF.md`) applies them.

### 9.1 Hard constraints

- **Zero JavaScript on the public site.** Published HTML contains no
  `<script>` tags, no inline event handlers, no client-side
  frameworks. Native HTML elements (`<details>/<summary>`,
  `<a href>`, `<form action="mailto:">`, the `:target` pseudo-class)
  carry every interaction.
- **Reader-mode parity.** A reader-mode (Safari, Firefox) view of any
  page must carry the same facts and the same neutral framing as the
  styled view. Meaning lives in semantic HTML (`<article>`,
  `<section>`, `<cite>`, `<time>`, headings), not class names or
  visual treatment. Modern CSS is progressive enhancement only.
- **WCAG 2.1 AA.** Colour contrast 4.5:1 for body text, 3:1 for large
  text. Keyboard reachable throughout. Visible focus states. No motion
  without explicit opt-in. Screen-reader compatible. `axe` and
  `pa11y` as a CI floor (Step 3 of the foundation pipeline).
- **Bilingual structure.** Every reader-facing string in the
  locale-map shape (`{en-CA, fr-CA, ...}`). The language toggle is a
  plain `<a href>` to a locale-suffixed URL, not JS.
- **No tracking.** No analytics, no third-party scripts, no fonts
  loaded from external CDNs that log requests. Self-host any font or
  asset.

### 9.2 Brand palette system

A reader can switch between palettes (each respecting the WCAG floor);
the default is the federal palette. Each palette is a set of CSS
custom properties (`--primary`, `--secondary`, `--tertiary`) selected
by a `data-theme` attribute on `<body>` or a class. Theme selection
persists via a URL parameter (`?theme=ab`) since client-side storage
is out of scope.

| Jurisdiction | Primary | Secondary | Tertiary | Header font | Body font |
|---|---|---|---|---|---|
| Canada (default) | `#EB2D37` | `#000000` | `#26374A` | Helvetica Neue | Noto Sans |
| British Columbia | `#013366` | `#FCBA19` | `#255A90` | BC Sans Bold | BC Sans |
| Alberta | `#0D3692` | `#FFEB43` | `#FFFFFF` | Acumin Pro | Acumin Pro |
| Saskatchewan | `#076A21` | `#FBDD40` | `#FFFFFF` | Helvetica | Arial |
| Manitoba | `#C8102E` | `#012169` | `#165016` | Arial Bold | Arial |
| Ontario | `#000000` | `#39B54A` | `#047BC1` | Raleway | Open Sans |
| Quebec | `#003DA5` | `#FFFFFF` | `#000000` | Helvetica Neue Bold | Helvetica Neue |
| New Brunswick | `#1A3C86` | `#F4C600` | `#D32927` | Arial | Arial |
| Nova Scotia | `#002868` | `#FFD100` | `#FFFFFF` | Arial | Arial |
| Prince Edward Island | `#2AA299` | `#D54040` | `#F3DB61` | Arial | Arial |
| Newfoundland and Labrador | `#003865` | `#BA0C2F` | `#FFA400` | Arial | Arial |
| Yukon | `#0738AC` | `#187B01` | `#D51810` | Arial | Arial |
| Northwest Territories | `#004B87` | `#FFFFFF` | `#FFD700` | Arial | Arial |
| Nunavut | `#0164BB` | `#FDD500` | `#D51516` | Arial | Arial plus ProStyle (Inuktitut syllabics) |

Values sourced from each jurisdiction's official identity guide,
design system, or flag specification. Ontario has an additional named
accent palette (eleven values) for creative applications. A forking
operator replaces this table with their own jurisdiction's identity.

### 9.3 Light and dark mode

Both required. Implemented via the `prefers-color-scheme` media query
plus a manual override (the theme selector). Light mode uses
canvas-white surfaces; dark mode uses near-black (`#1A1A1A` or similar,
never pure black for body backgrounds). The colour tokens shift
between modes; the named values (primary, secondary, tertiary) stay
constant, only the resolved colours change.

### 9.4 Typography

- **Body:** a serif intended for sustained reading. Charter, Source
  Serif Pro, or Iowan Old Style.
- **Headings:** a sans-serif. Inter, Source Sans Pro, or IBM Plex Sans.
- **Monospace** (for code, IDs, structured data): JetBrains Mono, IBM
  Plex Mono, or system monospace.
- **Type scale:** 1.0× body, 0.875× small, 1.125× lead, 1.5× h3, 2.0×
  h2, 2.5× h1. Line-height 1.5 for body, 1.25 for headings.
- **Page width:** 700-820px (a 65-75 character line at 16px body).

### 9.5 Information design

- **Timeline cards** render each event's connections inline as a
  "Connections" block: discrepancies, jurisdiction clarifications,
  threads, and causal links alike, each linking to the related event
  with its factual framing. Uniform rendering across edge types is
  what keeps discrepancies neutral (no special "hall of shame"
  affordance) and lets a reader enter any chain at any node. Depth and
  clustering (how many hops to show) is a UI calibration over a data
  model that already supports arbitrary plurality.
- **Outlet label.** Facts-only. Ownership headline, breakdown, then
  only verified fact rows; not-rated sources show the reason. Absence
  is neutral and must not read as a penalty (the open visual
  question). Accessibility: status glyphs (`✓` and `✕`) always pair
  with `.sr-only` text; `role="region"` plus `aria-label` per label.
- **Explainer.** A reusable concept page (jurisdiction, statute,
  funding mechanism) inserted inline into events as a "Context" block
  or readable standalone. The same explainer can be referenced from
  multiple events.
- **Search, sort, filter** (planned, main page): facets drawn from
  already-structured fields, entity (5.6), category, era, date range,
  relation type, `discrepancy_type`. No new data work is required
  beyond the entity layer; the validator hardening is what keeps
  these facets reliable.
- **Language parity:** every reader-facing field in the locale-map
  shape (post-Step-1); `ai_translated` flags machine output pending
  review. A structured `translation_status` field (Step 3 of the
  foundation pipeline) makes language coverage measurable.

### 9.6 Interaction patterns sanctioned

The complete list of interaction primitives the design may use:
permalinks (every event has a stable URL, `#evt-019` jumps,
`:target` styling highlights), `<details>` and `<summary>` (the only
CSS-only disclosure), anchor links, `<form action="mailto:">` for the
submission form (MVP), CSS `:target`, CSS `:focus-visible`,
`prefers-color-scheme`, `hreflang` and language-suffixed URLs, CSS
container queries (progressive enhancement). Anything not on this
list, including client-side filters, search, sort, expand-all,
animation, autoplay, modal dialogs, accordions beyond `<details>`,
client-side validation, and infinite scroll, is out of scope unless
explicitly proposed and audited.

### 9.7 Scale considerations

Realistic horizon: tens to low-hundreds of events per quarter. Above
roughly 150 events on a single page, `build.py` emits pre-built
per-era or per-year pages linked by anchors, never CSS-only
filtering. Above roughly 500, per-quarter pages. JavaScript-based
search is not on the roadmap; introducing it would trigger a fresh
Privacy and Access audit.

---

## 10. Contribution and the automated pipeline

- **Public path.** Static HTML form at `canadascanada.ca/feedback`
  with a `mailto:` action. No backend, no third-party form processor,
  no JavaScript on the public surface. The form opens the reader's
  email client pre-filled. Confidential contact via ProtonMail or
  Typewire (Canadian-resident alternative). Full spec:
  `INTERNAL_REVIEW_TOOL_SPEC.md`.
- **Operator-side review.** Three Python scripts: `intake.py`
  (submission email to record), `build_review.py` (local HTML review
  page with side-by-side card preview), `apply_decisions.py` (writes
  corpus, archives submissions, appends to `CORRECTIONS.md`).
- **The complexity stays out of the unattended loop.** The RSS
  pipeline (zero-LLM filter) only proposes candidate event nodes with
  cheap structured fields (date, title, source and outlet, suggested
  category), marked `needs_verification: true`. It never invents
  edges, entities, discrepancies, jurisdiction tags, or explainers.
- **Relational enrichment** (edges, `entity_ids`, `discrepancy_type`,
  jurisdiction, `explainer_ref`) happens at the human-approval step,
  where graph context exists; LLM-assisted (e.g. entity-id suggestions
  from the registry), human-confirmed. The validator runs in CI on
  every change, and `needs_verification` keeps captures invisible
  until cleared, so a captured event can sit safely with zero edges
  and simply not publish.
- **Corrections** are append-only via `update_log[]` per record, plus
  a public `CORRECTIONS.md` at the repo root mirrored to
  `canadascanada.ca/corrections`. Every approved correction generates
  one plain-language paragraph entry.

---

## 11. Portability

**Stays on a fork:** record shapes, the gate, the validator, the
graph and edge model, the entity and explainer subsystems, the
contribution and correction model, the facts-only outlet model, the
visual design system shape (palette table can be replaced wholesale).

**Swaps (in `meta/` or data, never code):** categories, eras, outlet
roster, the events, the palette values.

A clean fork edits `meta/` and data, not `build.py` or `validate.py`.
See `FORKING.md` for the operator handoff.

Licence: data CC-BY-4.0; editorial content all-rights-reserved to the
original operator.

---

## 12. Open items (state at this revision)

The foundation track (locale-map, entity registry, accessibility,
internet archive) is sequenced as cross-thread work orders in
`FOUNDATION_PIPELINE.md`. Step 0 (consolidation, the per-file and
monolith cleanup and the state guard) is complete. Step 1 (locale-map
migration to BCP-47 shape) is imminent.

- **Step 1 (locale-map).** Migrate all translatable fields in events,
  references, and outlets from flat `_en`/`_fr` to the locale-map
  shape (`{en-CA, fr-CA, ...}`). Adds the locale-shape validator
  rule.
- **Step 2 (entity registry).** New `entities/` collection plus
  additive `entity_ids[]` on events. The SKILL v3 rewrite happens
  here, against the now-settled record shape.
- **Step 3 (accessibility).** Reader-mode parity in the timeline
  render (`<article>/<section>/<cite>/<time>` semantic tags),
  optional `translation_status` field, axe and pa11y as a CI floor.
- **Step 4 (internet archive).** Archive-on-capture into
  `archived_url`, resumable backfill. Decoupled, can slot
  opportunistically.
- **Explainer rendering.** Wire validate and build for explainers;
  flip the four seed explainers' `needs_verification` to `false`.
- **Track A: ten ready reference records** to author against sourced
  primaries (Constitution Act, Charter s.33, Alberta public accounts,
  federal transfers, LGFF, education property tax, etc.).
- **Smith current-events cluster** (in v1 scope): convoy
  associations, US relationships, gender policy, Take Back Alberta,
  separatism and voter-list incidents, Peterson and Regulated
  Professions Act, federal-provincial blocking actions, town halls.
- **CSV-cluster authoring:** childcare federal-provincial agreements
  (with balance), AHS governance scandal, environment and wildlife,
  private-school funding, COVID misinformation, Indigenous
  consultation, spring-2025 legislative session.
- **Pre-launch verification sweep** of the suppressed events (gate to
  flip `needs_verification: false` on each).
- **Class-3 discrepancy leads** in `discrepancy-backlog.json` (need
  events authored before they can become edges).
- **Trademark search** (CIPO database for "CanadaScanada"), pre-launch.
- **Outlet-label layer rename** decision (Media Diet, News Diet, or
  other; DECISIONS_LOG entry 27).
