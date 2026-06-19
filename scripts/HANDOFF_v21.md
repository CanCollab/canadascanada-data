# HANDOFF v21 — pre-front-end integrity gate (Thread 7 close)

**Produced:** 2026-06-19. **Supersedes** the forward-looking sections and counts
of `STATE_OF_PLAY_v1` and `HANDOFF_v20` (both carried pre-batch-7 or mid-flight
numbers). Where this document and an older handoff disagree, this wins; where it
and a live `state.py`/`validate.py` run disagree, the live run wins.

> Numbering note: prior handoffs referenced run to v20; this is v21 by sequence.
> Rename if your local count differs.

---

## Read first (in order)

1. This document.
2. `THREAD_FINDINGS.md` — now includes F-029…F-039 from this thread.
3. `FAIR_DATA_STANDARD_CANONICAL.md` — authoritative FAIR statement.
4. `CanadaScanada_Design_Standard_v3_4.md` + `HANDOFF_v20` — methodology authority
   (operator's ruling: these own methodology; the Thread-6 working docs only
   identify drift/gaps).
5. `DECISIONS_LOG.md` — but see F-039: the project-knowledge copy is stale (ends at
   31; Decision 32 exists). Reconcile before renumbering.

---

## 1. Live baseline (ground truth, this thread)

Confirmed by the operator's local `state.py` + `validate.py`:

| Metric | Value |
|---|---|
| Events | 116 (39 published, 77 suppressed) |
| References | 320 (293 verified) |
| Outlets | 55 (manifest reconciles) |
| Schema | 3.0.0 uniform (events + refs) |
| Next ids | EVT-118, and references are now hex (see §2) |
| validate.py | PASS 0/0 |
| Derived files | `git diff docs/events/index.json docs/outlets/index.json` was empty → derived data current |

Batch 7 is applied. The post-batch-7 figures are authoritative; `STATE_OF_PLAY_v1`'s
289/231/50 are stale (F-029).

---

## 2. The reference-ID migration (built, validated, status: READY or DONE)

**Decision:** all reference IDs become 8-hex canonical (`R-XXXXXXXX`). The 197
sequential and 4 slug IDs migrate; the 119 already-hex stay. Every renamed ref
keeps its prior id in `extensions.legacy_id`. Slugs are retired as a style. EVT IDs
stay sequential (see §3).

**Tool:** `migrate_ref_ids.py` (produced this thread). Dry-run by default,
auto-discovers dirs, deterministic hex (re-run = no-op), case-insensitive
collision-safe, and self-verifying: it walks the parsed JSON, rewrites every
`source_ref`/`source_refs` value wherever it nests (F-035), and classifies any
residual old-ID mention as prose/SAFE or CONCERN (F-036).

**Dry-run result (final):** 201 refs → hex, 219 inbound rewrites across 90 events,
248 residuals all prose, **✓ VERDICT: every residual is a prose mention**. Safe to
apply.

**If not yet applied, the immediate next action is:**
```
# on a clean git tree
python3 scripts/migrate_ref_ids.py .            # confirm ✓ VERDICT
python3 scripts/migrate_ref_ids.py . --apply
python3 scripts/validate.py     # expect 320/116/55, 0/0
python3 scripts/state.py        # counts identical, only ids changed
python3 scripts/sweep.py
python3 scripts/build.py .      # regenerate docs
# review, then commit (public derived files too)
```
A `ref_id_migration_map.csv` (legacy_id → new_id) is written for provenance.
Prose mentions of old IDs are intentionally left as-is; `legacy_id` keeps them
traceable and `update_log` is append-only (do not rewrite it).

**One tidy-up surfaced:** the migration found a single stray `event.source_ref`
(was R-060) sitting outside the canonical locations — a record using singular
`source_ref` where plural `source_refs[]` is the norm. It migrates correctly; if
you want to normalize that record's shape, ask for the three-line locator.

---

## 3. Decisions locked this thread (merge into DECISIONS_LOG; numbers ≥33, confirm live max per F-039)

- **Reference IDs are 8-hex canonical (`R-XXXXXXXX`).** Supersedes Decision 14's
  "prefer hex/slug" with "hex only." Sequential and slug forms migrate; slugs
  retired. Minted independently (no central counter) for collision-free parallel
  intake. Renamed refs preserve `extensions.legacy_id`. Docs to update in the same
  spirit: Design Standard §5.2 + tree diagram, FORKING.md (the `R-###` path gloss).
- **EVT IDs remain sequential.** They are the public, citable, URL-anchor identity;
  display order is by `event_date`, not id, so there is no chronological-insertion
  problem (F-037). New events take the next id regardless of date. Keeping EVT
  sequential also avoids a much larger migration blast radius.
- **fr-CA localization uses the locale-map `{en-CA, fr-CA}` shape.** Not flat
  `_en`/`_fr`, not a new record type per locale. `migrate_locale.py` runs as a
  PAIRED commit with build.py accessor updates (F-038).

---

## 4. Outstanding / next actions, in order

1. **Apply the ref-ID migration** if not already done (§2), and commit.
2. **Apply `PATCH_doc_and_comment_fixes.md`** — the §5.4 / §5.2 / build.py
   "lower-id → source record" corrections + the hex-canonical ref-path wording.
   Cheap, no code/data change. Update FORKING.md's `R-###` path in the same pass.
3. **Add the `relation-types.json` symmetric note** (F-034) and, optionally, a
   validate.py rule rejecting manually-stored derived inverses
   (`enabled_by`/`prompted`/`superseded_by`/`continued_by`) — turns the "do not
   store manually" convention into an enforced gate.
4. **Reconcile DECISIONS_LOG.md** against the live log (F-039), then merge §3's
   three decisions with proper numbers.
5. **Locale-map migration** (paired data + build.py accessor commit, F-038) when
   ready. Ask for the build.py accessor changes at that point.
6. **Publish backlog → its own thread** (operator's call): finalize all 116. The
   structure is 57 instant flag-flips + verify 39 refs to unlock 20 more, taking
   published from 39 toward ~116. This must precede front-end IA/density work, and
   it is what regenerates `index.json` from 39 to ~116. Will need
   `EVENT_PUBLISH_BACKLOG.csv` (or regenerate the classification from the corpus).

---

## 5. Parked (do not action unless raised)

- Internal review tool build (spec is ready: `INTERNAL_REVIEW_TOOL_SPEC_v1.md`) and
  the management-panel question — learnings captured in
  `SCRIPTS_AND_PANEL_PROPOSAL.md`. Headline: a static HTML tool cannot run the
  scripts (browser sandbox); the button-panel version is a local-server fork, best
  built on an extracted `canscan/` library. Ship the static tool first.
- Scripts refinement (Tier 1: extract `canscan/` library; add a `check_derived`
  regen-and-diff CI gate; remove the build-date diff noise). See the proposal doc.
- AHS allegations timeline mining (abconservatives.ca/ahs-allegations/).
- R-154 heritage-fund cluster — needs event assignment.
- The 20 batch-7 parked orphan refs (R-176–R-197) — need events; a natural first
  job for the review tool with sources in hand. NOT generated this thread (no
  source content available; fabrication risk).
- EVT-092 split (Kenney proposal vs Smith enactment) — the `continues` build fix
  makes a split-and-link clean now.
- VOCABULARY_REFERENCE.md from the `meta/` audit.

---

## 6. Files produced this thread (outputs)

| File | Status |
|---|---|
| `migrate_ref_ids.py` | Built, dry-run green, ready to `--apply` (or applied) |
| `PATCH_doc_and_comment_fixes.md` | Ready to apply (doc/comment only) |
| `SCRIPTS_AND_PANEL_PROPOSAL.md` | Reference for a future scripts/tooling thread |
| `THREAD_FINDINGS.md` | Complete, +F-029…F-039 |
| `HANDOFF_v21.md` | This document |

Core artifacts for project knowledge: `THREAD_FINDINGS.md`, `HANDOFF_v21.md`.
Working files for the private repo: `migrate_ref_ids.py`,
`ref_id_migration_map.csv` (after apply), `PATCH_doc_and_comment_fixes.md`,
`SCRIPTS_AND_PANEL_PROPOSAL.md`.

---

## 7. One-paragraph state-of-the-world for the next thread

The corpus is at 116 events / 320 references / 55 outlets, validate-clean, with the
reference-ID scheme unified to hex canonical (migration built and dry-run-verified;
apply it first if it has not already run). The relations graph is confirmed
complete in build.py, the EVT and fr-CA shape questions are decided (sequential
EVT, locale-map fr-CA), and the remaining pre-launch work is mechanical: apply the
doc patch, reconcile the decisions log, run the paired locale-map migration when
ready, and then take the publish backlog (39 → ~116) in its own thread before any
front-end/UX design begins. The integrity gate is essentially closed.
