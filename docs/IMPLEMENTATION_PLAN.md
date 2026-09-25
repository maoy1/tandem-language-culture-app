# Tandem implementation plan

This is the working plan for the new repository. GitHub issues remain the
authoritative task records; this document explains the order and the amount of
human involvement expected.

The current product and SharePoint design is recorded in
[CURRENT_DESIGN.md](CURRENT_DESIGN.md). Every implementation issue and pull
request must follow that file. If a decision changes, update the design source
of truth in the same pull request before changing the implementation.

## Operating model

Work proceeds in one small GitHub issue at a time:

1. Choose the next issue and confirm its acceptance criteria.
2. Make the change on a short-lived branch.
3. Run automated checks and document any manual tenant step.
4. Review the result together and merge when accepted.

Automation should handle tests, schema validation, and diagnostic summaries.
The owner should only need to decide product behavior, perform the documented
SharePoint/Power Platform tenant setup, test the user-facing experience, and
approve the final result.

## Sequence

- [x] **POC-01 — Repository foundation**
  - Create the repeatable repository layout and working instructions.
  - Human checkpoint: confirm the structure is easy to maintain.
- [x] **POC-02 — Define SharePoint schema and manual setup**
  - Keep the approved lists, columns, choices, lookups, unique constraints,
    and indexes in version-controlled schema.
  - Validate the schema locally with repeatable tests.
  - Human checkpoint: create and configure the lists in the approved tenant,
    including the rich Location field and participant-form settings.
- [ ] **POC-03 — Participant self-registration** *(implementation in progress)*
  - Let an authenticated colleague create and update their own profile.
  - Keep the registration contract and automated consistency checks in the
    repository; apply the form and item-level permissions manually in the
    tenant.
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

POC-03 is the current focus. Its registration contract and manual form setup
must follow [POC_03_PARTICIPANT_SELF_REGISTRATION.md](POC_03_PARTICIPANT_SELF_REGISTRATION.md).
POC-02 is complete. Its schema and manual setup must follow
[CURRENT_DESIGN.md](CURRENT_DESIGN.md), especially the current Participants
schema and the removal of the Culture, Time zone, and Location catalogues.
