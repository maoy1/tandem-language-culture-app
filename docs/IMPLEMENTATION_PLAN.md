# Tandem implementation plan

The approved design is CURRENT_DESIGN.md. This plan reflects the owner's
annotations to Combined Requirements v0.2. GitHub tickets hold implementation
acceptance and status; planning completion does not imply deployment.

## Working process

1. Select one ticket; check its dependencies and current acceptance criteria.
2. Flag/verify permissions, licences, connectors, settings, connection owners and
   setup before dependent implementation. Existing Microsoft platform only; no
   extra budget. Ordinary users are self-service; necessary admin exceptions are allowed.
3. Use one branch and PR per ticket. Run appropriate checks and record tenant
   evidence separately from local/JSON validation.
4. Update design, plan, related setup/field contracts and affected open ticket
   bodies/dependencies/scheduling together. Preserve closed baseline evidence;
   do not equate an approved requirement with completed implementation.
5. Review and merge; use closing keywords only for completed acceptance work.
6. Verify issue/PR state after merge before the next ticket.

Use [TEST_CATALOGUE.md](TEST_CATALOGUE.md) for stable acceptance/regression IDs
and [TEST_RUNS.md](TEST_RUNS.md) for version-specific evidence. Add or identify
the relevant case when investigating an issue, then record its retest before
closing the fix. Planned cases and owner-reported baseline checks must remain
distinct from observed results for the deployed target MVP.

## Completed baseline

- [x] #1 repository foundation.
- [x] #2 initial schema/manual setup, delivered through PR #32.
- [x] #3 initial self-registration, delivered through PR #34.
- [x] #4 language selections and persistence, delivered through PR #37.
- [x] Owner-confirmed synthetic language eligibility in Power Automate under PR #44.
      #7 remains open: full v0.2 eligibility and real-data/app integration are pending.

These results certify the old baseline only. New fields and status rules need
their own implementation and regression checks.

## Revised delivery sequence

- [ ] #45: approve and track this MVP scope alignment; planning only.
- [ ] #46: field matrix in MVP_FIELD_CONTRACT.md for review; optional time zone,
      no participant size preference, and no Comments notice are now agreed.
      culture and combined 2–10 with valid focus relationships are approved. Defaults,
      exact technical choices and remaining projection decisions need acceptance.
      Pause real-data discovery wiring until this contract is agreed.
      Review progress: Active/Open defaults, culture participation, focus roles,
      any-active-member control, request cancellation/history and bounded departure
      handling are confirmed. Validation also blocks empty offer/interest saves,
      excludes invalid records and revalidates without resetting participation.
      Exact technical names, migration and display choices
      still need review; no live behavior changed by these notes.
- [ ] #5: implement controlled culture-share/interest fields; update registration
      and validation to allow empty time zone. No participant group-size field.
      Draft PR #52 prepares the configuration, 85 culture values, setup guide and
      tests. Owner confirms catalogue population/checks, but the latest Participants
      screenshot still shows required Time zone and no visible culture lookups.
      Participant columns, app/flow changes and tenant acceptance remain pending.
      Follow POC_05_CULTURE_REGISTRATION.md; verify active-value checks and the
      create/edit validation loop guard before treating the flow as complete.
- [ ] #6: implement independent participation/validation states and open-to-connections;
      verify validation never reactivates paused profiles.
- [ ] #7/#9: extend compatible participant discovery and maintain one rule location
      in Power Automate; connect trusted normalized data and the Power Apps response
      only after the prerequisite checks.
- [ ] #12/#13: define typed groups, memberships, capacity and simple state. Do schema
      work before group discovery; group creation depends on request acceptance.
      Detailed Groups/Group Members field tables now exist in MVP_FIELD_CONTRACT.md
      for review. Derived counts/slots are automatic; no participant group-text
      field. Owner approved Open-if-space/otherwise-Closed after memberships save,
      editable name/description, fixed type/focus, bounded capacity and Ended final.
- [ ] #16: compatible open-group discovery. Ranking #8 is not a dependency.
- [ ] #10/#11/#17: connect/join, accept/decline, sender visibility and availability checks.
- [ ] #47 alongside #11/#12/#17: implement/retest safe retries, simultaneous acceptance,
      last-slot capacity protection and partial-failure handling.
- [ ] #12/#14: complete automatic accepted-membership/free-slot updates and self-service
      leaving; necessary ambiguous group recovery may use exceptional admin support.
- [ ] #49: inspect available notification options and agree event/channel matrix.
      Do before any notification configuration; may be assessed alongside core work.
- [ ] #21: implement selected request notifications after #49 passes.
- [ ] #25 and relevant #26/#27/#28 checks: validate core workflows, capacity/retries,
      bounded data access and operational handover within existing platform.
- [ ] #48 LAST IMPLEMENTATION PHASE: inspect actual old Excel; approve mappings,
      migrate confirmed participants/groups, report exceptions and reconcile data.
      Do not hold core coding on a workbook inspection.
- [ ] Release checks: ordinary colleague access, approved exposure/data policy,
      notification delivery and migration confirmation, then broader rollout.

## Deferred access test

#18 and #39–#42 stay open. The owner will arrange ordinary-colleague testing later.
Trusted admin Members access is expected; ordinary access is unverified.
Continue owner/synthetic-data work without selecting/configuring a new access
architecture. Ordinary-user verification is still needed before broader rollout.

## Later delivery

#8 ranking; #15 active-group warning pending scope review; #29/#30 freshness and
reminders; #31 dashboards; automatic location/time-zone derivation only if cheap;
optional language level; bulk invitations; meet-first; expiry; detailed admin
audit UI; automatic departure recovery and needs-sharer timers.

No standalone hosting, new paid licence or premium/custom connector is allowed.

## Manual involvement

Participants decide whom to approach, accept/decline requests, arrange meetings
and maintain their participation. Routine system updates run automatically.
The owner/admins handle explicitly flagged one-time setup, product decisions,
test acceptance and necessary exceptional corrections. Migration mapping review
is one-off, at the end; no routine manual matching or per-user grant queue.

## Current focus

PR #51 merged the reviewed contract/test documentation. #46 remains open for
outstanding decisions; its approved registration subset is in progress under #5,
draft PR #52. Finish and verify participant culture lookups and optional Time zone,
then form/flow acceptance. #6 follows before
real-data discovery integration. Notifications (#49) are undecided; Excel (#48)
is scheduled last. Approved target fields are not yet in the deployed schema.
Discovery display fields remain to be decided in #7/#42, generally excluding
admin/system-only columns. Group Open/Closed/Ended and real count/slots replace
profile-level size preference. The existing schema's required time zone is a
documented baseline restriction to remove during implementation, not current intent.

Owner prerequisite update (2026-10-31): owner confirms all three access-screen
checks work: SharePoint New List/Create column, registration app Edit and submission
flow Edit. This confirms owner access to those screens, not successful creation,
catalogue connection access, ordinary-user access or deployment. Owner subsequently
confirms Culture catalogue bulk entry and checks (85 entries, keys, Active Yes).
Next: create the participant ShareCultures/LearnCultures lookup columns. App/flow
catalogue access and live registration acceptance remain unverified.

Latest Participants screenshot still shows Time zone required and does not show
the two culture lookups. Create/verify those lookups and make Time zone optional
before form/flow acceptance; see SETUP-20261031-03 in TEST_RUNS.md.

PR #53 merged the full 40-ticket backlog review on 2026-10-31. See
[the complete audit](BACKLOG_AUDIT_2026-10-31.md) for corrections, scheduling and
remaining decisions. The audit preserves issue states and does not close #45 or
any implementation ticket. Later #8/#15/#29–#31 are outside the core milestone;
required MVP and release-check tickets are included, even when owner-deferred.
