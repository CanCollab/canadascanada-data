# Methodology

How CanadaScanada decides what to publish, how it sources every claim,
and how it corrects errors.

This document is for readers. The technical specifications live in
the `CanadaScanada_Design_Standard_v3_4.md` document. The rules
described here are enforced automatically by the project's validator
before any event reaches a reader.

## The publication firewall

Every event in the corpus carries a flag called `needs_verification`.
When `true`, the event is suppressed from the public timeline,
regardless of how complete it is.

An event becomes publishable only when all of the following are true:

- A human has personally verified the date, the framing, the source,
  and the actors named.
- Every source cited in the event resolves to a real, verified
  reference record.
- Every claim is typed (fact, context, or inference).
- Any inference carries an explicit `inference_note` explaining the
  reasoning.
- The event passes the schema validator without errors.

When all of those pass, the operator flips `needs_verification` to
`false`, the validator confirms, and the next build includes the event.

## Sourcing tiers

Every reference is categorized at one of four tiers. Higher-tier
sources can carry more weight on a claim; lower-tier sources cannot
load-bear a fact alone.

- **Tier 1: Primary records.** Government documents, court filings,
  legislation, Hansard, official statements, audited financials,
  freedom-of-information disclosures, raw video or audio of public
  events.
- **Tier 2: Established news organizations.** Reporting from CBC, CTV,
  Global, Globe and Mail, Canadian Press wire, Reuters Canada, major
  regional dailies (Edmonton Journal, Calgary Herald, Toronto Star,
  La Presse, Le Devoir), public broadcasters (Radio-Canada, APTN), and
  similar.
- **Tier 3: Independent and specialized journalism.** Reporting from
  smaller publications and specialized outlets (The Tyee, The Walrus,
  Daily Hive, Press Progress, Canadaland, and similar). Includes
  opinion and analysis pieces, which carry the Bell rule restriction.
- **Tier 4: Aggregators and context-only sources.** Wire-service
  republication on aggregators (MSN, Yahoo), reposted content, and
  context-only sources that can support but not carry a claim.

A source's tier is recorded in its reference record and visible to
readers.

## The Bell rule

Opinion pieces, columns, editorials, and analytical commentary are
labelled as such in their reference records. Such sources cannot
load-bear a factual claim alone. If an opinion piece is the only
source for a date, a quote, or a specific action, the event stays
suppressed until a Tier 1 or Tier 2 source confirms.

This rule is named for an instance early in the project's development
where a Bell columnist's piece in the Calgary Herald was the only
source for a date; the date turned out to be wrong. The rule exists
to prevent that pattern from reaching a reader.

## "None-found-with-receipt"

When the project reports the absence of something (an outlet has no
published corrections policy, a government department has no published
guidance on a topic), the absence itself carries a receipt: a URL
pointing at *where the absence was checked*. This makes the verdict
auditable.

If a reader submits a real published policy URL that contradicts a
"none-found" entry, the entry is updated to point at the policy and
the absence becomes a presence. The append-only upgrade path is
visible in `CORRECTIONS.md`.

## Primary source beats internal files

Internal project files (drafts, working notes, prior versions of an
event) can be factually wrong. If a primary source contradicts an
internal record, the primary source wins. The project corrects the
internal record and logs the correction publicly.

This rule was added after several events were found to be mis-dated
or mis-framed in internal handoff documents from earlier project
iterations. Primary sources are the floor of fact; internal notes are
working material, not authority.

## Claim typing: fact, context, inference

Every claim in every event is one of three types.

- **Fact.** Directly sourced from a primary or Tier 2 source. The
  source's framing is the project's framing.
- **Context.** Background information needed to understand the fact.
  Sourced, but the framing may be the project's own summary of a
  larger body of reporting.
- **Inference.** The project's own reading of what a sequence of
  events means, where that reading goes beyond what any single source
  states explicitly. Always carries an `inference_note` explaining
  the reasoning. Visually distinguished from facts.

The reader sees the type of each claim and can weigh it accordingly.

## AI-assisted authoring

The project uses AI assistance for some authoring tasks:

- Draft extraction from news articles into structured event records
- Translation between English and French
- Suggesting relations between events (subject to human approval)

Every AI-assisted output is reviewed by a human before being marked
`needs_verification: false`. Translated content carries the
`ai_translated: true` flag and is reviewed for fidelity. AI is never
used for editorial framing of an event, choice of sources, decisions
about what to publish, or characterization of any actor.

This disclosure is operationalized via the schema (the flags above)
and is enforced by the validator.

## Editorial discipline

Several rules govern how events are written:

- **Educate, not accuse.** Where a tension turns on something the
  public may not know (jurisdictional divisions, funding mechanics,
  legal precedent), the answer is an explainer, not a sharper
  adjective.
- **Name the pattern, not the opponent.** Events describe what
  happened and who acted in their official role. No motive
  attribution, no "hypocrisy" or "deflection" framing.
- **Party affiliation never appears in event titles** or first-tier
  display, only institutional roles. The reader sees the action,
  not a coloured banner.
- **Symmetric treatment of all sides** with concrete examples. If a
  pattern is illustrated for one party or position, the same pattern
  is illustrated for the others where examples exist.
- **Statements are events.** A public statement is sourced and
  documented the same way as an action.

## Corrections

When an error is found, in any field of any record, the project
corrects it and logs the correction publicly in `CORRECTIONS.md`.
Entries follow this format:

```
## 2026-MM-DD · EVT-### · brief description of change
A short, plain-language paragraph explaining what was wrong, what is
now right, and (if applicable) who reported it. Source: [outlet,
date](URL).
```

`CORRECTIONS.md` is append-only. Post-launch, errors cannot be
silently fixed; every change is documented.

If you have found an error, please submit it via the form at
`canadascanada.ca/feedback`. You will be credited (with permission) or
the entry will note "submitted by a reader" (default).

## What the project does not do

- **Does not break news.** The corpus documents and links events that
  primary sources have already reported.
- **Does not rank or score outlets.** Outlet records are facts-only
  ("nutrition labels"). No grades, no rankings, no summary verdicts.
- **Does not personalize what readers see.** No algorithmic feed, no
  ranking, no recommendation, no tracking.
- **Does not characterize communities** in summary terms. Events
  describe what happened to a community, not what a community "is."
- **Does not accept funding from any government whose conduct it
  actively documents.** Carve-out for arm's-length agencies and
  programs designed for journalism or civic-tech independence.

## Questions

If you have questions about a specific event, source, or rule, the
fastest path is to file a feedback submission at
`canadascanada.ca/feedback`. The submission goes to the operator
directly. Substantive questions about methodology get a public
response in `CORRECTIONS.md` if the answer changes the corpus, or by
direct reply otherwise.
