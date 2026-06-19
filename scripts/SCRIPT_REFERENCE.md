# CanadaScanada Script Reference

**Location:** All scripts live in `scripts/` of the private repo.
Run everything from the **private repo root** unless noted.

---

## scripts/state.py
**What:** Counts events, references, outlets, and schema versions. Checks for monolith drift and manifest consistency.
**When:** Start of every session. After any commit batch.
**How:** `python3 scripts/state.py`
**Repo:** Run in either repo. Results differ (public has only published events; private has all 116).
**Output to watch:** `OK: per-file tree consistent, no monolith, manifest reconciles.`

---

## scripts/validate.py
**What:** Structural gate. Checks outlet_id resolution, source_ref integrity, schema consistency, category vocab.
**When:** Before every commit. After every batch of file changes. Required to pass before sync or build.
**How:** `python3 scripts/validate.py`
**Repo:** Run in both repos before pushing. Public and private should both pass independently.
**Output to watch:** `PASS — 0 warning(s), 0 errors`
**Note:** validate.py uses `outlet_id` field (not `id`) in outlet records. This distinction caused the intl-journal outlet bug in this thread.

---

## scripts/sweep.py
**What:** Scans all events for keyword/category mismatches, unsourced opposition_response, and other deferred findings.
**When:** Before each verification-sweep batch. Re-run after any event edits — findings list can change as the corpus evolves (F-014).
**How:** `python3 scripts/sweep.py`
**Repo:** Private only (has suppressed events).
**Output:** List of findings. Paste into thread; Claude will triage disposition.

---

## scripts/build.py
**What:** Pre-render pipeline. Reads events, refs, outlets, meta and generates static HTML into `docs/`.
**When:** After validate.py passes on the public repo. Triggered automatically by the GitHub Action on push.
**How:** `python3 scripts/build.py . ./docs`
**Repo:** Public only. Never run on private (private events must not reach docs/).
**Note:** As of Thread 4, build.py has been updated to handle structured `opposition_response` objects and `name`/`name_en` outlet field fallback. Commit the updated build.py before the next build run.

---

## scripts/sync_to_public.sh
**What:** Copies the publishable subset of the private repo to the public repo. All references, outlets, meta, explainers, scripts, and LICENCE always copy. Events copy only if `needs_verification == false`.
**When:** After a private repo commit batch is validated. Before pushing to GitHub.
**How:**
```bash
bash scripts/sync_to_public.sh --dry-run   # see what would copy
bash scripts/sync_to_public.sh             # actually copy
```
**Repo:** Run from the private repo root. Writes into the sibling public repo directory.
**Auto-detects** the public repo as `../canadascanada-data`. Pass `--public-dir=/path/to/repo` if your layout differs.
**After running:** Switch to GitHub Desktop, select the public repo, commit and push.
**Does NOT:** Delete files that were removed in private (additive only). Does not run validate.py or commit anything. Does not copy suppressed events.
**Implication:** If you remove or rename a file in private, delete it from public manually before or after sync.

---

## scripts/regen_manifest.py
**What:** Regenerates `outlets/records/_manifest.json` from the outlet files on disk.
**When:** After adding or removing outlet records, if the manifest gets out of sync.
**How:** `python3 scripts/regen_manifest.py`
**Repo:** Either (outlets live in both).

---

## scripts/state.py vs validate.py — key difference
`state.py` counts and reports; it uses filename stems as fallbacks for missing id fields.
`validate.py` enforces; it only accepts outlet records with an `outlet_id` field.
They can disagree (state.py counts 47, validate.py counts 46) when an outlet file is malformed.
Always trust validate.py for release decisions.

---

*This reference is accurate as of HANDOFF v19 (Thread 4 close). Update it when scripts change.*
