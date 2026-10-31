# Backlog alignment with approved MVP v0.2

This file maps the existing backlog to the owner's latest annotations. GitHub
is authoritative for live status. Approved target behavior is documented in
CURRENT_DESIGN.md; schema/config JSON still describes the implemented baseline.

## Planning and new work

| Ticket | Purpose | Order |
|---|---|---|
| #45 | Parent for v0.2 scope and delivery alignment | Track; no implementation completion claimed |
| #46 | Field/exposure contract, Comments notice, separated statuses and capacity decisions | Next; before schema and real-data integration |
| #47 | Retry/idempotency, simultaneous accepts, capacity and partial-write recovery | With #11/#12/#17; before acceptance paths close |
| #48 | Actual Excel inspection, mapping and safe migration | Last implementation phase, before existing-data launch |
| #49 | Notification feasibility and event/channel decision | Before #21; email/Teams not preselected |

## Existing-ticket changes

| Ticket | Aligned scope |
|---|---|
| #2/#3/#4 | Completed initial baseline. Preserve prior evidence; do not reopen just to describe target fields |
| #5 | Controlled culture sharing/interests and preferred group size; culture-only registration; candidate-visible Comments warning. Time zone catalogue retained; no derived-location requirement |
| #6 | Participation Active/Paused/Inactive independent of validation and migration confirmation; open-to-connections; never reactivate a paused participant through validation |
| #7/#9 | Compatible people only; language/culture/combined fit, status/open filters and authorized projection including Comments after notice. Existing synthetic language tests are baseline evidence only |
| #8 | Later ranking; remove as dependency for group discovery. No required automatic location/time-zone derivation |
| #10/#11 | Requests, recipient authority, sender status, unavailable-recipient handling and safe acceptance coordinated with #47; meet-first/expiry/bulk Later |
| #12 | Typed groups: language 2 or 3 total; culture up to 10, minimum/mixed capacity decided in #46; membership creation on acceptance |
| #13 | Simple Open/Closed/Ended MVP lifecycle and permitted member changes/admin override; richer states and timers Later |
| #14 | Self-service leaving, preserved history and automatic normal membership counts; ambiguous recovery can be exceptional admin work |
| #15 | Not confirmed in revised MVP; Later scope review, not a mandatory launch gate |
| #16/#17 | Promote compatible existing-group discovery/join to MVP. Remove ranking dependency; recheck capacity and test #47 |
| #18/#39–#42 | Ordinary-colleague access tests deferred by owner; remain open. Admin Members access is expected, ordinary access unverified; candidate Comments is now approved after notice |
| #19/#20/#22–#24 | Retain necessary group/request access safeguards; no routine individual permission administration. Check selected approach/configuration before implementing |
| #21 | Depends on #49 channel/event decision; automatic selected request notifications with safe failure/deduplication behavior |
| #25 | Tests for culture-only, participation/validation, compatibility, comments projection, typed capacity and retries; no mandatory ranking or two-group warning |
| #26–#28 | Synthetic platform/scale/handover checks within no-budget runtime; target current approved fields only |
| #29/#30/#31 | Later freshness/reminders/dashboard, not core implementation gates |

## Decision precedence and evidence

The source DOCX scope table is a reviewed proposal. The owner's annotations
override its automatic location derivation, blanket 3–10 group size, old-Excel
visibility rule, fixed notification-channel text and standalone-hosting option.
Culture catalogue/fields are now approved target MVP requirements, superseding
their previous removal. Do not change live schema/flows until #46 and
prerequisites pass.

PR #44 retains owner-confirmed synthetic language cases; it does not implement
culture/status/open filters or authorize real-data discovery. The scope-alignment
PR is planning only and must not close #5/#6/#7/#18 or #45–#49 automatically.
