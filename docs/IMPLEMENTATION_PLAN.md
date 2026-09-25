# Tandem implementation plan

This is the working plan for the new repository. GitHub issues remain the
authoritative task records; this document explains the order and the amount of
human involvement expected.

## Operating model

Work proceeds in one small GitHub issue at a time:

1. Choose the next issue and confirm its acceptance criteria.
2. Make the change on a short-lived branch.
3. Run automated checks and document any manual tenant step.
4. Review the result together and merge when accepted.

Automation should handle tests, validation, repeatable provisioning, and
diagnostic summaries. The owner should only need to decide product behavior,
approve changes affecting the SharePoint/Power Platform tenant, test the
user-facing experience, and approve the final result.

## Sequence

- [x] **POC-01 — Repository foundation**
  - Create the repeatable repository layout and working instructions.
  - Human checkpoint: confirm the structure is easy to maintain.
- [ ] **POC-02 — Automate SharePoint provisioning** *(current)*
  - Create or validate the required lists, columns, choices, lookups, and views.
  - Human checkpoint: approve the target SharePoint site and permissions.
- [ ] **POC-03 — Participant self-registration**
  - Let an authenticated colleague create and update their own profile.
  - Human checkpoint: test the form once with a normal account.
- [ ] **POC-04 to POC-06 — Profile data and participation status**
  - Add controlled language preferences, profile context, and Active/Paused/
    Inactive behavior.
- [ ] **POC-07 to POC-09 — Discovery**
  - Implement eligibility and ranking in one testable location, then expose it
    to the user interface.
  - Human checkpoint: review example suggestions and ranking behavior.
- [ ] **POC-10 to POC-15 — Requests and 1:1 tandem lifecycle**
  - Add connection requests, accept/decline, tandem creation, group lifecycle,
    leaving, and the two-active-groups warning.
  - Human checkpoint: run one complete participant-to-tandem scenario.
- [ ] **POC-16 to POC-24 — Existing groups, permissions, and notifications**
  - Add group discovery, join requests, permission safeguards, and notifications.
  - Human checkpoint: approve notification wording and access boundaries.
- [ ] **POC-25 to POC-28 — Tests, scale, and reproducibility**
  - Add automated discovery tests, synthetic data, scale checks, and a
    repeatable handover process.
- [ ] **POC-29 to POC-31 — Operations**
  - Add freshness tracking, reminders, and an administrative status overview.

## Manual work that remains

The following cannot safely be fully automated from this repository:

- granting or approving tenant permissions;
- confirming SharePoint and Power Platform environment choices;
- checking the user experience with real colleagues;
- approving match, request, and notification behavior;
- deciding when the POC is ready for wider use.

Everything else should be a candidate for a script, automated test, validation
report, or documented repeatable step.

## Current focus

POC-02 is the active issue. The schema and repeatable provisioner are prepared;
the remaining checkpoint is a live validation against the approved SharePoint
site, followed by review of any reported manual Location-field or index steps.
