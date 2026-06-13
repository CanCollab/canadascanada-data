# Ethics

The rules CanadaScanada operates under. Adapted from the Product Ethics
Principles by Spencer Goldade
(github.com/spencergoldade/Product-Ethics-Principles), licensed
CC-BY-4.0.

## What this document commits to

This document is the project's statement of principles, public and
auditable. Eighteen rules govern every decision about the system,
the data, and the operator's conduct. Each rule is stated in the
project's own terms, with the framework's term shown in italic parens
for traceability.

The principles are not aspirational. They are operational. Every rule
binds in at least one of four places: at authoring time (the editor's
own discipline), at validation time (the `validate.py` schema gate), at
governance review (quarterly post-launch), or at pre-launch audit (a
one-time sweep of every record before public release).

## How to read

For each rule:

- **Statement** is what the project commits to.
- **In practice** is how the project demonstrates the commitment.

## The eighteen

### 1. Access *(Accessibility)*

**Statement.** Anyone who can reach the public site can use it, with
any device, connection quality, assistive technology, or level of
technical literacy.

**In practice.** Zero JavaScript on the public site. Static HTML
servable from any host. Semantic HTML where structure matters.
Screen-reader accommodations paired with every visual affordance.
Keyboard reachable throughout. Bilingual structural support. WCAG 2.1
AA as the audited floor.

### 2. Source Representation *(Diversity)*

**Statement.** The corpus draws from a wide range of reporting
establishments, not a narrow set. No single outlet's editorial frame
dominates the source mix.

**In practice.** Each event is sourced individually. The Bell rule
prevents opinion or columns from carrying a fact without
Tier 1/2 corroboration. Source-quality tiers (1-4) are visible. The
fork model means any jurisdiction or community can run their own
version with their own outlet mix.

### 3. Reach *(Equity)*

**Statement.** Removable barriers between a reader and the corpus
are removed.

**In practice.** No account required. No paywall on the timeline,
references, explainers, or outlet labels. Static HTML works on 3G and
on low-end devices. Single-card permalinks and thread URLs share
without infrastructure. CC-BY-4.0 on the data.

### 4. Participation *(Inclusion)*

**Statement.** A reader who is not a developer can contribute feedback,
submit a correction, or propose a new event.

**In practice.** A public submission form at `/feedback`, no login
required, no third-party form processor. Plain-language editorial
standard (Canadian Press style) on all reader-facing copy. Bilingual
intake.

### 5. Voice *(Belonging)*

**Statement.** No reader is made to feel unwelcome or othered by the
project's editorial voice, structural metadata, or defaults.

**In practice.** Educate-not-accuse rule. Neutral thread containers
that describe a domain, never deliver a verdict. Party affiliation
never appears in event titles or first-tier display, only
institutional roles. Symmetric illustration of all sides with concrete
examples. Library-not-pamphleteer voice.

### 6. Privacy *(Privacy)*

**Statement.** The project collects only what a reader voluntarily
provides. Everything else is architecture-level unable to be
collected.

**In practice.** No accounts. No login. No analytics. No cookies. No
third-party JavaScript. No tracking pixels. No fingerprintable
telemetry. The static-HTML architecture is structurally incapable of
collecting reader data. Submitted feedback collects only what the
submitter provides; details in `PRIVACY.md`.

### 7. Integrity *(Security)*

**Statement.** The corpus and its access surface are protected against
unauthorized modification, takedown, or loss.

**In practice.** No user data, no database, no server-side state. The
publish firewall (`needs_verification: true`) blocks unverified content
from the public build. Off-host backup mirror. Branch protection on
`main`. Hardware-2FA on the operator's account.

### 8. Care *(Safety)*

**Statement.** The project does not put readers, contributors, or
third parties named in the work at risk it could foreseeably prevent.

**In practice.** No engagement design, addictive patterns, or
notifications. Defamation discipline: every claim typed as fact,
context, or inference; no imputation of crime or fraud without legal
finding; no home addresses, personal contact information, or other
sensitive personal data, even when those appear in public records.

### 9. Representation *(Representation & Stigma)*

**Statement.** The project does not characterize people or communities
in ways that dehumanize, stereotype, or stigmatize.

**In practice.** Specific contested events live in event records, not
in concept explainers, so verdict-laden characterization never enters
structural metadata. Each claim typed. The educate-not-accuse rule
prevents summary characterization of communities.

### 10. Disclosure *(Algorithmic Accountability)*

**Statement.** Any automated or AI-assisted decision affecting what
readers see is disclosed in plain language. The project surfaces no
ranked, scored, or personalized output to readers.

**In practice.** No ranking. No recommendation. No personalization. No
feed. Display order is human-authored data. AI-assisted authoring
(extraction, translation, relation-drafting) is disclosed via the
`ai_translated: true` flag and the `needs_verification: true` gate.
The methodology page describes the two-stage authoring flow in
reader-facing language.

### 11. Sustainability *(User Health)*

**Statement.** The product does not optimize for engagement, attention
capture, or compulsive use.

**In practice.** No DAU or MAU targets. No notifications. No streaks,
badges, points, or gamification. No infinite scroll. No autoplay.
Reading the corpus is finite by structure. Success is measured in
judgment-minutes per published event, not in time-on-site.

### 12. Agency *(Autonomy & Agency)*

**Statement.** The reader assembles meaning. The project supplies
facts.

**In practice.** UI copy in the timeline says "you selected these
cards," never "these cards show X." Reader-composed groupings, when
they ship, produce a URL that reads as the reader's own arrangement,
not the project's. Any MLA-contact scaffold presents facts and
sources only.

### 13. Truth *(Honesty & Truth)*

**Statement.** The project distinguishes verified primary fact from
interpretation, discloses AI assistance, sources every claim, and
corrects errors publicly.

**In practice.** Sourcing tiers 1-4. Bell rule. `none_found-with-receipt`
documents verified absences with an auditable URL. Primary sources
override internal files when they conflict. `ai_translated` discloses
AI assistance. The publish firewall blocks unverified content.
Corrections are append-only in `CORRECTIONS.md`.

### 14. Durability *(False Obsolescence)*

**Statement.** Any operator can keep this project running indefinitely
without the original operator's involvement.

**In practice.** CC-BY-4.0 data. Flat JSON in git. Static HTML out. No
proprietary encoding, closed format, or platform dependency beyond
GitHub (mitigated by an off-host mirror). The fork model puts the
infrastructure in the hands of any community that wants it.

### 15. Fairness *(Economic Justice)*

**Statement.** The project does not extract value from readers,
exploit attention, or sell access to facts.

**In practice.** Timeline, references, labels, and explainers are
free. No paywall. No data broker. No targeted advertising.
Single-sponsor pattern when sponsorship begins (one ethics-aligned
sponsor at a time, flat fee, no behavioral targeting, no editorial
coupling). Voluntary 20% cap on any single funder's share of project
revenue.

### 16. Footprint *(Environmental Sustainability)*

**Statement.** The project minimizes its bandwidth, compute, and
storage footprint relative to its mission.

**In practice.** Static HTML. No JavaScript. No autoplay video.
Minimal images. CDN-cached. Compute happens at build time only;
no server runtime.

### 17. Reciprocity *(Labor Ethics)*

**Statement.** Anyone whose work or words appear in the project, or
who helps build it, is treated with dignity, credit, and fair
compensation.

**In practice.** Sources credited and linked, not republished or
hidden behind project framing. Hyperlinks send traffic to original
outlets. Contractor relationships, when they begin, are market-rate
in CAD with written scope and credit.

### 18. Civic Purpose *(Civic Responsibility)*

**Statement.** The project takes responsibility for its aggregate
effects on democratic participation and does not weaponize its
infrastructure against democratic safety.

**In practice.** Sourced facts. Transparent methodology. Neutral
containers. Library-not-pamphleteer voice. Fork model. MLA-contact
scaffold (planned) presents facts and sources only, never a
project-authored accusation. Editorial discipline is independent of
party affiliation. No funding accepted from any government whose
conduct the project actively documents.

## Localization

Localization is the lever that moves Access, Source Representation,
Reach, and Voice at once. The BCP-47 locale-map shape lets any
operator author content in any locale without modifying the schema. A
Quebec, Indigenous-nation, or international fork is a first-class use
of the system.

## Open feedback

If you believe the project has failed to live up to a principle
above, file a correction via the form at
`canadascanada.ca/feedback` (or email `feedback@canadascanada.ca`).
Substantive concerns receive a public response in `CORRECTIONS.md`.

## Re-audit cadence

These principles are reviewed at every material architecture change
and at least once annually.

## Audited against

[The Product Ethics Principles by Spencer Goldade, CC-BY-4.0.](https://github.com/spencergoldade/Product-Ethics-Principles)
