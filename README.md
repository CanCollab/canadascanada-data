# CanadaScanada

A civic accountability platform that publishes verified, sourced,
individually-cited events affecting Canadians and their relationship to
government. Built as static HTML on flat JSON, with zero JavaScript on
the public site, no tracking, no accounts, and no proprietary formats.

The corpus is licensed CC-BY-4.0. Anyone can read, share, fork, or build
on this data. The methodology is public, the sources are linked, and
errors are corrected publicly in `CORRECTIONS.md`.

## What this is

A timeline of sourced civic and political events with their connections
to each other. Each event card carries:

- The factual description, in plain language
- Every claim typed (fact, context, or inference)
- Sources individually cited, each verified
- Links to related events (discrepancies, jurisdictional clarifications,
  thread membership, causal relationships)
- Context explainers for legal, jurisdictional, or fiscal concepts

The reader assembles meaning. The project supplies facts.

## What this is not

- Not a news site. The corpus does not break stories; it documents and
  links events that primary news sources have already reported.
- Not a partisan platform. Editorial discipline excludes party-affiliation
  framing in titles, summary characterization of communities, and
  imputation of crime or fraud without legal finding.
- Not an algorithmic feed. There is no ranking, recommendation, or
  personalization. Display order is human-authored data.
- Not engagement-optimized. No notifications, no streaks, no infinite
  scroll. Reading the corpus is finite by structure.

## How it works

```
Author or contribute JSON  →  validate.py  →  build.py  →  static HTML  →  GitHub Pages
```

Every event lives in a single file (`events/EVT-###.json`). Every source
lives in a single file (`references/R-<slug>.json`). Every outlet has a
record describing what's known about it (`outlets/records/<id>.json`).
The build script reads the data, runs the validator (which blocks
publication of anything unverified or unsourced), and emits static HTML.

No server. No database. No runtime dependency. The entire site can be
served from any static file host, mirrored, archived, or forked
indefinitely.

## Documents in this repository

- `METHODOLOGY.md`: sourcing rules, the publication gate, how errors are
  corrected
- `ETHICS.md`: the principles the project commits to
- `FORKING.md`: recipe for adapting this project to another
  jurisdiction
- `CONTRIBUTING.md`: how to submit a correction, new event, or feedback
- `ADDING_A_FIELD.md`: operator procedure for schema extension
- `EXPLAINER_SCHEMA_SPEC.md`: the schema for the educational layer
- `CanadaScanada_Design_Standard_v3_4.md`: the canonical system and
  data design contract
- `CORRECTIONS.md`: append-only public log of every approved correction
- `CHANGELOG.md`: schema and platform version history
- `LICENSE.md`: combined licence pointer
- `LICENSE-data.md`: CC-BY-4.0 for the corpus
- `LICENSE-editorial.md`: all-rights-reserved for editorial content
- `PRIVACY.md`: privacy posture
- `TERMS.md`: terms of use

## Getting involved

- **Submit a correction or new event:** see `CONTRIBUTING.md`.
- **Fork this project for your jurisdiction:** see `FORKING.md`.
- **Read the methodology:** see `METHODOLOGY.md`.
- **Read the corrections log:** see `CORRECTIONS.md`.

## Contact

Email: `feedback@canadascanada.ca`

For confidential contact, use ProtonMail or our Canadian-resident
Typewire address (see `PRIVACY.md`).

## Licence

- **Data** (events, references, outlets, explainers, meta): CC-BY-4.0.
  See `LICENSE-data.md`.
- **Editorial content** (memos, prose pages, original explainer text,
  branding): all rights reserved to the project operator. See
  `LICENSE-editorial.md`.

When citing or republishing data from this project, please credit:
*"CanadaScanada, canadascanada.ca, CC-BY-4.0."*

## Audited against

[The Product Ethics Principles by Spencer Goldade, CC-BY-4.0.](https://github.com/spencergoldade/Product-Ethics-Principles)
