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
   Flag and verify all permission, setting, connector, connection, licence and
   configuration prerequisites first. Separate one-time setup from recurring
   maintenance; participant workflows must require no routine admin intervention.
2. Make the change on a short-lived branch.
3. Run automated checks and document any manual tenant step.
4. In the same PR, update this plan, backlog alignment, and affected design/setup documents. State completed work, remaining tenant checks, and the next issue.
5. Review the result together and merge when accepted. Use `Closes #N` so GitHub closes the issue on merge; keep incomplete acceptance work in an open follow-up.
6. After merge, verify the PR is merged and the issue is closed, then reconcile the plan before starting another ticket. Do not call a tenant check complete without recorded evidence.

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
    including the Language and Time zone catalogues, lookup fields, indexes,
    and participant-form settings.
- [x] **POC-03 — Participant self-registration** *(issue #3 closed; PR #34 merged)*
  - Let an authenticated colleague create and update their own profile.
  - Use Power Apps to lock the unique Participant account to the signed-in
    user, and expose the Time zone catalogue as a dropdown.
  - Share the app through a Teams tab. Record the known limitation that the
    app filter is not row-level SharePoint security.
  - Human checkpoint: test the form once with a normal account and one second
    account.
- [ ] **POC-18 — Private self-service registration** *(parent remains open)*
  - [ ] #39 / POC-18A: check prerequisites and select the simplest supported approach. Next action; assessment only.
  - [ ] #40 / POC-18B: prove own-record access using two accounts and synthetic data, after #39.
  - [ ] #41 / POC-18C: integrate the proven approach and verify registration, after #40 and before wider testing.
  - Close #18 only after A–C are delivered and verified. No architecture is selected yet.
  - #42 / POC-18D is separate: controlled candidate access, delivered with #7–#9 after registration protection.
  - Follow [the staged access plan](POC_18_PARTICIPANT_ACCESS.md).
- [x] **POC-04 — Structured language preferences** *(PR #37 merged)*
  - Catalogue-backed multi-value Teach/Learn fields are present in the schema.
  - Owner confirmed persistence after reopening, multiple selections in both
    fields, simultaneous learner/sharer use, and teach-only saving on 2026-10-31.
- [ ] **POC-05 to POC-06 — Profile data and participation status**
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
- importing and maintaining the Time zone catalogue;
- configuring the Power Apps form and Teams tab;
- checking the user experience with real colleagues;
- approving match, request, and notification behavior;
- deciding when the POC is ready for wider use.

Everything else should be a candidate for a script, automated test, validation
report, or documented repeatable step.

## Current focus

### Owner-directed implementation session — 2026-10-31

The owner deferred the normal-colleague access test until a tester is available.
Keep #18 and #39–#42 open; do not spend this session on an access redesign.
The owner clarified site Members are trusted admins. Their inherited access
alone does not establish ordinary-participant exposure. Actual participant
access remains untested; draft PR #43 is partial evidence, not an access verdict.

Continue core implementation with owner/synthetic data. #5 optional profile
enrichment stays deferred. Start #7 eligibility against current Active/Needs
review status and language lookup IDs, without introducing an unapproved field.
#6's expanded status design and live discovery integration remain pending.
Record repository checks separately from Power Apps deployment and tenant tests;
finishing code does not establish a working end-to-end deployed app.

Runtime correction: discovery runs in Power Automate using built-in operations
and the existing SharePoint connector. PR #44 now contains an action-definition
fragment and synthetic tenant scenarios, not an unhosted Python implementation.
The flow still needs verified prerequisites, trusted data normalization, actual
tenant configuration and app integration. Do not claim the old Python tests
validate this replacement. No additional budget, premium/custom connectors or
external hosting is permitted; no routine admin action per participant/search.

POC-03 was delivered in merged PR #34 and issue #3 is closed. Its registration
contract, Power Apps form, and Teams sharing setup are documented in
[POC_03_PARTICIPANT_SELF_REGISTRATION.md](POC_03_PARTICIPANT_SELF_REGISTRATION.md).
POC-02 is complete. Its schema and manual setup must follow
[CURRENT_DESIGN.md](CURRENT_DESIGN.md), especially the current Participants
schema, the required Time zone catalogue, and the removal of the Culture and
Location catalogues.

Issue #4's owner-account checks passed and PR #37 is merged. Current implementation
priority is #7's core eligibility with synthetic data. #18 and #39–#42 remain open
but access investigation/testing is deferred by the owner until a colleague can
test. Do not configure replacement flows now. Wider rollout still needs access
verification; code work can proceed without declaring that requirement satisfied.
Optional profile enrichment remains deferred.
The first restart check should recheck live registration and sharing; repository
completion does not certify the current tenant configuration.
