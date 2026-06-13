# Forking This Project

A recipe for taking the CanadaScanada platform and running your own version
of it in your own jurisdiction, language, or community. The data is licensed
CC-BY-4.0, the scripts are open, and the schema is jurisdiction-agnostic.
What follows is the shortest path from "I want to track X in Y place" to a
working, validating site you can publish.

This recipe assumes you are not the original operator. If you are forking
for a different province (Quebec, BC, Saskatchewan), a different country
(Minnesota, Japan, Ireland), or a different domain entirely (municipal
accountability, university governance, sectoral oversight), the steps are
the same.

---

## Ingredients

You will need:

- **A computer** with macOS, Windows, or Linux.
- **Python 3.10 or newer.** Check by opening a terminal and running
  `python3 --version`. If missing, download from python.org.
- **Git and GitHub Desktop.** Free, from desktop.github.com.
- **A GitHub account** (or any git host: Codeberg, GitLab, self-hosted
  Forgejo all work).
- **A text editor.** Any editor that handles UTF-8 JSON. Free options:
  VS Code, Sublime Text, BBEdit, Notepad++.
- **A few hours.** Most of the time will be authoring your own events;
  the technical setup is under an hour.

You will not need:

- A server, database, or hosting platform with a runtime.
- A JavaScript build chain, npm, or any frontend toolkit.
- A paid licence for any tool in the recipe.

---

## One-time setup

1. **Fork or clone the public repository.** From the canonical public repo's
   GitHub page, click "Fork" (creates your own copy under your account) or
   "Code → Download ZIP" (if you do not want a git connection). GitHub
   Desktop can also clone directly: File → Clone repository → enter the
   URL.

2. **Open the repo in your editor.** You will see folders for `events/`,
   `references/`, `outlets/records/`, `explainers/`, `meta/`, `scripts/`,
   and `docs/`.

3. **Confirm the scripts work.** In a terminal, navigate to the repo
   folder (use `cd ~/path/to/your-fork`) and run:

   ```
   python3 scripts/validate.py .
   python3 scripts/state.py
   ```

   If both run without errors, you have a working installation. If
   `state.py` reports clean and `validate.py` says `PASS`, the upstream
   corpus is intact.

That is the whole setup. The rest of the recipe is what you actually want
to change.

---

## The recipe, in order

### Step 1. Decide what you are tracking

Write one sentence answering: *what civic events does my version of this
project document?* Examples:

- "Documented Quebec provincial political events affecting language policy
  and Bill 96 implementation."
- "Minnesota state legislature accountability events affecting election
  administration and voter access."
- "Tokyo municipal procurement decisions over ¥100M."

You will use this sentence in your `README.md`, your About page, and in
every funding application or partnership conversation. Write it once and
keep it visible.

### Step 2. Set your jurisdiction config

Open `meta/jurisdiction.json` (create it if missing). Set the fields:

```json
{
  "jurisdiction_name": "Quebec",
  "jurisdiction_code": "QC-CA",
  "primary_locale": "fr-CA",
  "secondary_locales": ["en-CA"],
  "project_name": "QuebecScanada",
  "site_domain": "quebecscanada.ca",
  "operator_contact": "feedback@quebecscanada.ca"
}
```

Pick a project name that is yours, not a derivative that uses the original
brand. **"CanadaScanada" is not your project name.** Forking the data and
scripts is fully permitted; passing yourself off as the original project
is not. See the Attribution section below.

### Step 3. Set your locale defaults

If your primary locale is something other than `en-CA`, edit the build
defaults. In `scripts/build.py`, find the locale fallback (or the locale
read function) and change the default key from `"en-CA"` to your primary
locale code. The locale-map shape (BCP-47 keys like `fr-CA`, `iu`, `cmn`,
`pa`) lets you add any language pair to any field without touching the
schema.

After Step 1 of the upstream foundation pipeline lands, all translatable
fields will already be in the locale-map shape. Until then, the migration
script (`scripts/migrate_locale.py`) folds the old flat `_en`/`_fr`
fields into the new shape; run it once on your fork.

### Step 4. Clear out the upstream corpus (or keep it as reference)

You have two options.

**Option A: start empty.** Delete all files in `events/`,
`references/`, and `outlets/records/` except `index.json` and
`_manifest.json`. Empty those out (leave `{}` or `[]` as appropriate).
Now your corpus is empty and ready for your own events.

**Option B: keep upstream events as a reference branch.** Move
`events/`, `references/`, and `outlets/records/` to a folder called
`upstream-reference/`. Add new empty `events/`, `references/`, and
`outlets/records/` folders. The reference content stays as a model for
your authoring, but does not render in your build.

Most forks should go with Option A. Option B is for forks doing direct
comparative work.

### Step 5. Add your first event

Copy one upstream event file to use as a template. In `events/`, create
`EVT-001.json` with the event you want to document. The schema is in
`schemas_Event.ts` (a TypeScript declaration file you can read as plain
text). The minimum required fields:

- `event_id`: a string like `"EVT-001"`
- `schema_version`: `"3.0.0"` (current)
- `date`: an ISO date string
- `title`: a locale-map object `{ "your-locale": "...", "en-CA": null }`
- `summary`: a locale-map object
- `source_refs`: an array of reference IDs (you will create these next)
- `needs_verification`: `true` until you have personally verified

Add the event, save the file, and run `python3 scripts/validate.py .`
The validator will tell you what is missing if anything is.

### Step 6. Add your sources

For each source you cited in your event, create a reference file in
`references/`. Naming: `R-<short-slug>.json` (e.g. `R-cbc-2024-01-15-bill96.json`).
The minimum fields:

- `reference_id`: matches the filename
- `schema_version`: `"3.0.0"`
- `source_url`: the URL
- `archived_url`: a snapshot URL from web.archive.org or archive.today
  (Step 4 of the foundation pipeline will automate this; for now, do it
  manually by visiting web.archive.org/save and pasting the URL)
- `outlet_id`: matches an outlet record in `outlets/records/`
- `source_type`: from the vocabulary in `meta/source-types.json`
- `date_published`: ISO date

Validate again.

### Step 7. Add your outlets

For each new outlet, create a file in `outlets/records/`. Naming:
`<outlet-slug>.json`. Read several upstream outlet records first to see
the shape. The minimum:

- `outlet_id`: matches the filename
- `outlet_type`: from the vocabulary
- `name`: locale-map
- `rated`: `true` if you have rated the outlet, `false` if you are using
  it as a citable primary without a rating
- `citable`: usually `true`

Then add the outlet's `outlet_id` to `outlets/records/_manifest.json` in
the position you want it to display (the manifest is order-as-data).

### Step 8. Build and check

```
python3 scripts/build.py
```

The build generates `docs/index.html` and the supporting files. Open
`docs/index.html` in your browser. Your event should appear if
`needs_verification` is `false`; if it is `true`, the event is suppressed
from the public build. This is the firewall: nothing reaches readers
unverified.

When you have verified the event yourself (read the sources, confirmed
the date, checked the framing), set `needs_verification` to `false` and
rebuild.

### Step 9. Set your branding

Edit the CSS in the build template. Brand colours, fonts, and layout
choices live in `scripts/build.py` (look for the CSS block) or in a
separate template file if the upstream has split that out. The Design
Standard documents the constraints: zero JavaScript, semantic HTML,
reader-mode parity, WCAG 2.1 AA. If you respect those constraints,
visual changes are free.

### Step 10. Deploy

The build produces a `docs/` folder of static HTML, CSS, and JSON
fragments. Deploy options, easiest first:

- **GitHub Pages.** In your repo settings, enable Pages, point at the
  `main` branch's `docs/` folder. URL: `<your-username>.github.io/<repo-name>`
  or your custom domain.
- **Cloudflare Pages, Netlify, Vercel.** Connect the repo, set the
  output directory to `docs/`, click deploy.
- **Self-hosted on any web server.** Upload the `docs/` folder via SFTP
  or rsync. No runtime needed.

Add `docs/` to your `.gitignore` if you do not want the build artifacts
in version control; let the deploy platform build on its end.

### Step 11. Publish your fork

Push your changes to your fork's repository. Tweet, post, email
collaborators, file a grant application. Anyone who reads your version
should be able to read the data and trust it, the same way they would
the upstream.

---

## Variations

### Different language

The locale-map structure handles any BCP-47 code. For a Spanish fork, use
`es-MX` or `es-AR` or `es-ES`. For an Inuktitut fork, use `iu-CA-syl`
(syllabics) or `iu-CA-Latn` (Latin script). For Japanese, `ja-JP`. The
build will display whatever locale you set as primary.

If you want a multilingual fork from day one, set `primary_locale` to
your first language and include the second in `secondary_locales`.
Translation can be human-authored, AI-assisted (set `ai_translated: true`),
or absent (the `translation_status` field tracks what is and is not done).

### Different jurisdictional scope

The schema does not care whether your jurisdiction is federal, provincial,
state, municipal, sectoral, or organizational. You can fork to track
school-board decisions, hospital governance, university administration,
sectoral regulation, or any other domain where events have dates, sources,
and structural relations to each other.

Customize the `meta/threads.json` file (the narrative containers) to
match your domain. The thread names are neutral containers, not verdicts;
follow the upstream pattern (`<domain>-policy`, not `<domain>-attacks`).

### Different branding

The platform's brand colours are tied to provincial and federal Canadian
identity systems. For your fork, replace the colour tokens with your own
jurisdiction's official palette (or any palette you want). Run a
contrast-ratio check against WCAG 2.1 AA for any text-and-background pair.

Free contrast checker: webaim.org/resources/contrastchecker. Aim for a
4.5:1 ratio for body text, 3:1 for large text.

### Different funding model

The upstream's revenue model (single-sponsor, membership, grants) is a
choice, not a requirement. You can run your fork as a fully volunteer
operation, fund it through an existing nonprofit, accept government
grants if your jurisdiction's rules permit, or any combination. The
Spencer-aligned principles (no extractive monetization, no targeted
advertising, no paywall on the corpus, voluntary funder cap modeled on
RJO's 20% rule) apply wherever you can apply them.

---

## Attribution

CC-BY-4.0 means: free to use, modify, redistribute, and monetize, *with
attribution to the upstream*. Specifically:

- Include a credit line on your About or Methodology page:
  *"This project's schema, scripts, and methodology adapt the
  CanadaScanada platform, CC-BY-4.0,
  https://github.com/<canadascanada-org>/canadascanada-data."*
- If you use any of the upstream's actual event data, credit the
  upstream as the source of those events (in addition to the original
  reporting outlet). Use the upstream's `event_id` if your version cites
  the same event.
- Do not claim your version is the upstream project. Pick your own name.
- The data is CC-BY-4.0. The editorial content (memos, explainers, prose
  on the About page, the original project's logo) is all-rights-reserved
  to the original operator. You can fork the data; you cannot fork the
  editorial voice or the brand.

If the original project's name or branding is trademarked or under
common-law trademark in your jurisdiction, you may not use that name or
branding for your fork. Pick a name that is yours.

---

## Things you should not change

These are not technical restrictions; they are the design integrity of
the platform. Forks that change these stop being recognizably the same
thing.

- **The zero-JavaScript public surface.** Adding analytics, tracking,
  client-side filtering, or a JS-rendered timeline breaks the privacy
  posture, the accessibility commitments, and the durability claim. If
  you want a JS-driven site, build a different project.
- **The reader-mode parity rule.** Meaning lives in semantic HTML; CSS
  is progressive enhancement. Reader-mode views must carry the same
  facts and framing as styled views.
- **The publish firewall.** `needs_verification: true` blocks an event
  from the public build. Removing this gate would publish unverified
  content. Do not.
- **The append-only corrections discipline.** Post-launch, errors are
  corrected publicly with a dated `CORRECTIONS.md` entry. Silent edits
  to history are a trust violation.
- **The educate-not-accuse editorial rule.** Neutral containers. Party
  affiliation never in titles. The reader assembles meaning; the project
  supplies facts. If your editorial voice editorializes, you have a
  different project, not a fork.

---

## Troubleshooting

**`validate.py` reports errors.** Read the error message. It will name
the file and the field. The most common errors are: a referenced
`outlet_id` does not exist in `outlets/records/`, a `source_ref` does
not exist in `references/`, or a vocabulary value (source type,
relation type, era) is not in the `meta/` vocab file.

**`state.py` says the manifest does not reconcile.** A manifest entry
points to a record that does not exist, or a record exists with no
manifest entry. Open `outlets/records/_manifest.json` and either remove
the dangling entry or add the missing record's ID.

**Build runs but produces empty output.** Likely cause: all events have
`needs_verification: true`. The build suppresses unverified events from
the public output by design. Verify your events (set to `false`) and
rebuild.

**Reader-mode view looks different from the styled view.** This is the
reader-mode parity gap the upstream is currently addressing. If your
fork has the same gap, follow the upstream's Step 3 of the foundation
pipeline (semantic HTML in the timeline render).

**Your collaborators do not know git.** Use GitHub Desktop's drag-and-
drop. Create files in your editor, drag them into the GitHub Desktop
sidebar, write a commit message, click Commit, click Push. Done.

---

## Next steps for a serious fork

1. **Adopt the upstream's principles document.** Adapt the language for
   your jurisdiction; keep the framework.
2. **Set up an off-host backup.** Mirror your repo to a second git host
   (Codeberg, GitLab, self-hosted Forgejo) so a takedown or compromise
   does not lose the corpus.
3. **Sign up for the upstream's notification list** (when it exists) to
   stay informed about schema changes, validator updates, and
   foundation-pipeline progress that your fork can pull from.
4. **Contribute back.** If your fork develops a useful schema extension,
   a build improvement, or a translation file, consider opening a pull
   request to the upstream. The upstream maintains the canonical schema;
   improvements benefit every fork.
5. **Join the federation, if one exists.** Multiple forks running the
   same schema in different jurisdictions create a data network. Cross-
   linking between forks is one of the platform's intended use cases.

---

## Reference

- Upstream repository: https://github.com/<canadascanada-org>/canadascanada-data
- Schema: `schemas_Event.ts`, `EXPLAINER_SCHEMA_SPEC.md`, and the live
  files in `meta/`
- Design Standard: `CanadaScanada_Design_Standard_v3.3.md`
- Principles: `PRINCIPLES.md`
- Editorial guidance: `EXPLAINER_RHETORIC_GUIDE.md`
- Data licence: CC-BY-4.0 (https://creativecommons.org/licenses/by/4.0/)
- Editorial-content licence: all rights reserved to the original operator
