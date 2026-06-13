# Privacy

How CanadaScanada handles reader data. The short version: there isn't
any. The architecture is structurally incapable of collecting reader
data, and the only data the project does collect (from voluntary
submissions) is handled with PIPEDA-aligned discipline.

## What the public site collects

**Nothing.**

The public site at `canadascanada.ca` is static HTML served from a
content delivery network. It contains:

- No JavaScript
- No cookies
- No analytics (no Google Analytics, no Plausible, no Fathom, none)
- No tracking pixels
- No third-party scripts
- No social-media share buttons that phone home
- No fingerprinting code
- No fonts loaded from external services that log requests

The site is structurally incapable of building a profile of any reader.
There is no server-side state to record. There is no database to leak.
There is no user account system to compromise.

This posture is verifiable. Open the page in your browser's developer
tools and check the network tab; you will see a single HTML document
load, plus any same-origin CSS and image files. No third-party
requests.

## What the hosting provider sees

Like every website on the internet, when you load `canadascanada.ca`,
the hosting provider (currently GitHub Pages, served via Cloudflare or
the equivalent) sees:

- Your IP address (necessary to deliver the content to you)
- Your browser's user agent string
- The page you requested

These are standard HTTP server logs. The project does not have access
to these logs, does not analyze them, and does not retain them.
Hosting-provider log retention is governed by the hosting provider's
own privacy policy.

If you want to read the site without your IP address being visible to
the hosting provider, use a VPN or the Tor Browser. The site is
designed to work normally over both.

## What the submission form collects

The form at `canadascanada.ca/feedback` uses a `mailto:` action. When
you click Submit, your default email application opens with a
pre-filled message. You decide whether to send it.

If you send the submission, the project receives:

- The information you typed into the form (submission type,
  description, source URL, etc.)
- Your email address (whichever account you sent from)
- Standard email metadata (timestamps, mail servers in the delivery
  path)

If you do not want to share your email address, you can use a
project-specific anonymous account (ProtonMail, Tutanota, or
similar) to submit. The project does not require a real identity.

## How submission data is handled

- **Stored in the operator's private working repository**, not in the
  public repo.
- **Retained while the submission is pending review.** Most submissions
  are processed within 7-30 days.
- **The email address is removed** from the submission record after a
  decision is made, unless the operator marks the submission as
  "follow up needed" (rare; e.g. if the operator needs more information
  to verify a correction).
- **The body of the submission** is retained as part of the project's
  editorial input record. This becomes part of the project's own
  history and may be referenced in `CORRECTIONS.md` if the submission
  led to a correction.
- **Approved submissions** may be credited in `CORRECTIONS.md` if you
  ask to be credited, or noted as "submitted by a reader" (default).

## Your rights under PIPEDA

The Personal Information Protection and Electronic Documents Act
(PIPEDA) governs how Canadian organizations handle personal
information. Under PIPEDA, you have the right to:

- **Access** the personal information the project holds about you.
- **Correct** any personal information that is inaccurate.
- **Withdraw consent** for the project to retain your personal
  information (subject to legal or contractual restrictions).
- **Complain** to the Privacy Commissioner of Canada if you believe
  the project has mishandled your information.

For any of the above, contact: `feedback@canadascanada.ca` with the
subject line `[PRIVACY]`.

## Email contact

For contact that should be kept confidential:

- **ProtonMail:** `feedback@canadascanada.ca` (Swiss-hosted,
  end-to-end encrypted, no tracking)
- **Typewire (Canadian-resident alternative):** a Canadian-hosted
  email address is listed on the Contact page for readers who prefer
  Canadian-jurisdiction handling of their message.

## No third-party data sharing

The project does not sell, share, or transmit submission data to any
third party. Period.

Exceptions, narrowly defined:

- If the project is legally compelled to disclose information (e.g. a
  court order), it will comply with the law. The project does not
  voluntarily share data with law enforcement, government agencies,
  marketing partners, or analytics services.
- If a submission contains material that requires reporting to law
  enforcement (e.g. credible threats of imminent harm to a specific
  person), the project will report it. This is a narrow exception.

## Children

The project is not directed at children under 13 and does not
knowingly collect information from them.

## Updates to this policy

When this privacy policy changes, the change is logged in
`CHANGELOG.md` and the new version replaces this file. Material
changes (anything that expands data collection or sharing) are
announced on the front page of the site for at least 30 days before
taking effect.

## Last updated

This document is current as of the latest entry in `CHANGELOG.md`
that references privacy.

## Operator

CanadaScanada is operated by a single individual under a pseudonymous
project identity. Identity will be disclosed at a natural milestone
(incorporation, public speaking, or in response to a substantive
legal inquiry).

## Questions

For questions about this privacy policy, email
`feedback@canadascanada.ca` with subject line `[PRIVACY]`.
