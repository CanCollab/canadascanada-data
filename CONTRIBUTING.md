# Contributing

How to help improve the CanadaScanada corpus. This guide is for
readers who want to report errors, propose new events, suggest
sources, or otherwise feed into the project's editorial work.

For instructions on forking the project for your own jurisdiction,
see `FORKING.md` instead.

## The easiest way: submit via the form

Visit `canadascanada.ca/feedback`. Fill out the form. Click Submit.
Your default email client opens with a pre-filled message; send it.
The project receives it and reviews.

No GitHub account required. No login. No technical knowledge
required.

## What you can submit

- **Corrections.** Something in an event is wrong (date, framing,
  source citation, link). Tell us what should change and why. Include
  a primary source if possible.
- **New events.** A documented public event the corpus should track.
  Include the date, what happened, who acted, and at least one
  source URL.
- **Fact checks.** A statement made by an actor in the corpus that
  the project should add or that conflicts with an existing record.
- **Outlet feedback.** Something about an outlet record (ownership
  detail, corrections policy, journalism standards) that should be
  added or corrected.
- **Other.** General feedback, methodology questions, partnership
  inquiries.

## What makes a submission useful

Three things turn a submission into a quick review:

1. **A primary source.** The strongest evidence is a primary record
   (government document, court filing, legislation, raw video of the
   public event, official statement). Tier 2 reporting (CBC, CTV,
   Globe, Canadian Press, regional dailies) is also strong.
2. **A specific event identifier.** If you're correcting an existing
   event, include its `EVT-###` ID (visible in the URL of each
   event's permalink).
3. **Plain language.** Tell us what changed, not what should be
   thought. The reader assembles meaning; the corpus supplies facts.

## What the project will not act on

- Submissions without a verifiable primary source for a contested
  factual claim. We'll respond asking for one.
- Submissions that characterize a person or community in a way that
  imputes crime, fraud, or corruption without a legal finding. The
  defamation discipline applies; see `METHODOLOGY.md`.
- Submissions that violate the privacy of a private third party
  (home addresses, personal contact information, even from public
  records).
- Submissions framed as harassment, intimidation, or doxxing of any
  named actor.

## What happens after you submit

1. The operator receives your submission via email.
2. The submission is reviewed (typically within 7-30 days).
3. The operator decides to approve, reject, defer, or approve with
   edits.
4. If approved (or approved with edits), the change lands in the
   corpus on the next build, and an entry appears in
   `CORRECTIONS.md`.
5. If rejected, you receive a reply explaining why (unless you
   submitted anonymously, in which case the rejection is silent).
6. If deferred (waiting for more information or a corroborating
   source), the operator may follow up or update you when the status
   changes.

## How submissions are credited

By default, accepted submissions are credited "submitted by a
reader" in `CORRECTIONS.md`. If you would like to be named (a real
name, a handle, an organization), tell us in your submission. We
will not name you without your explicit request.

## If you have a GitHub account

You can also:

- **File an issue** at the project's GitHub repository for
  bug-style problems with the site (broken links, rendering issues,
  validator errors).
- **Open a pull request** if you are technically inclined and want
  to propose specific record-level changes. PRs are reviewed
  against the same editorial discipline as form submissions.
- **Fork the project** to run your own jurisdiction's version
  (see `FORKING.md`).

For most contributors, the form is the right path.

## What you cannot do

- You cannot create new events directly in the corpus; new events
  pass through the publication firewall (`needs_verification: true`)
  and require human verification before they appear publicly.
- You cannot edit existing records anonymously. Every change is
  attributed somewhere (to a submitter, to a correction entry, or to
  the operator).
- You cannot bypass the sourcing rules. The Bell rule and the
  publication firewall are not negotiable.

## Privacy of your submission

See `PRIVACY.md` for how submission data is handled. The short
version: the operator receives your email, retains the submission
record while it's in review, and removes your contact email from the
record once a decision is made (unless follow-up is needed).

## Confidential contact

For sensitive submissions (whistleblower material, anything that
should be handled with care for the submitter's safety), email the
project's ProtonMail or Typewire address directly. PGP-encrypted
email is supported on both. See `PRIVACY.md` for the addresses.

## Code of conduct

Treat the project and other contributors with the same standards the
project applies to itself: facts with provenance, no characterization
of persons without sourced evidence, no harassment, no doxxing.

The operator reserves the right to ignore submissions that violate
these standards and to log abusive submissions for the operator's
own safety records (without making them public).

## Thank you

The project is a single-operator effort. Every legitimate submission
is a real contribution to the work, whether it leads to a correction,
a new event, or just helps the operator see something they missed.
