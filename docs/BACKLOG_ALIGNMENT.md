# Backlog alignment with approved MVP v0.2

This file maps the existing backlog to the owner's latest annotations. GitHub
is authoritative for live status. Approved target behavior is documented in
CURRENT_DESIGN.md. Registration schema/policy JSON now describes the POC-05
target, explicitly pending tenant setup/tests; Discovery JSON remains the earlier
language-only baseline. Neither file certifies live deployment.

The [2026-10-31 full audit](BACKLOG_AUDIT_2026-10-31.md) reviews all 40 tickets and
records the corrected live acceptance criteria and scheduling. PR #52 separately
prepares the desired POC-05 schema/policy; it remains a draft, not deployment.
Owner-confirmed catalogue import does not establish participant form/flow acceptance.

## Planning and new work

| Ticket | Purpose | Order |
|---|---|---|
| #45 | Parent for v0.2 scope and delivery alignment | Track; no implementation completion claimed |
| #46 | Field matrix under review. Culture and combined 2–10 approved; time zone optional; no participant size preference or Comments notice. Exact Discovery display fields decided in #7/#42 | In progress |
| #47 | Retry/idempotency, simultaneous accepts, capacity and partial-write recovery | With #11/#12/#17; before acceptance paths close |
| #48 | Actual Excel inspection, mapping and safe migration | Last implementation phase, before existing-data launch |
| #49 | Notification feasibility and event/channel decision | Before #21; email/Teams not preselected |

## Existing-ticket changes

| Ticket | Aligned scope |
|---|---|
| #2/#3/#4 | Completed initial baseline. Preserve prior evidence; do not reopen just to describe target fields |
| #5 | In progress in draft PR #52: catalogue setup reported complete; participant culture lookups not visible in latest screenshot, Time zone still required. Finish columns/app/flow and live acceptance. No size preference or Comments notice. See POC_05_CULTURE_REGISTRATION.md |
| #6 | Participation Active/Paused/Inactive independent of validation and migration confirmation; open-to-connections; never reactivate a paused participant through validation |
| #7/#9 | Compatible people only; language/culture/combined fit and status/open filters. Exact display fields pending; participant fields generally eligible, admin/system-only columns excluded. No Comments notice. Blank time zone never excludes a candidate |
| #8 | Later ranking; remove as dependency for group discovery. No required automatic location/time-zone derivation |
| #10/#11 | Requests, recipient authority, sender status, unavailable-recipient handling and safe acceptance coordinated with #47; meet-first/expiry/bulk Later |
| #12 | Typed groups: language 2 or 3 total; culture and combined 2–10 with valid focus relationships; membership creation on acceptance |
| #13 | Simple Open/Closed/Ended MVP lifecycle and permitted member changes/admin override; richer states and timers Later |
| #14 | Self-service leaving, preserved history and automatic counts/slots; keep Closed state until member reopens; hide groups lacking valid focus from Discovery. No auto-end/replacement/recovery timers; exceptional recovery can use admins |
| #15 | Not confirmed in revised MVP; Later scope review, not a mandatory launch gate |
| #16/#17 | Promote compatible existing-group discovery/join to MVP. Remove ranking dependency; recheck capacity and test #47 |
| #18/#39–#42 | Ordinary-colleague access tests deferred. Admin Members access expected; ordinary access unverified. Discovery field list undecided; exclude admin/system-only data, no Comments-specific notice |
| #19/#20/#22–#24 | Retain group/request/member authorization outcomes; item-specific ACL synchronization is an option, not an approved architecture. Verify approach first; no routine individual permission administration. Expiry stays Later |
| #21 | Depends on #49 channel/event decision; automatic selected request notifications with safe failure/deduplication behavior |
| #25 | Tests for culture-only, participation/validation, compatibility, comments projection, typed capacity and retries; no mandatory ranking or two-group warning |
| #26–#28 | Synthetic platform/scale/handover checks for current fields, optional time zone and manual one-time setup; no hosted-service fallback or tenant-provisioning promise |
| #29/#30/#31 | Later freshness/reminders/dashboard, not core implementation gates |

## Decision precedence and evidence

Groups and Group Members now have detailed proposed field tables in
MVP_FIELD_CONTRACT.md. Membership rows are maintained by accepted join/Leave
workflows. Counts/slots/joinability are derived, not participant input or assumed
cross-list calculated columns. Initial Open-if-space/otherwise-Closed follows
successful membership creation; type/focus fixed, name/description editable,
capacity bounded and Ended final are approved. No group schema changes deployed.

The source DOCX scope table is a reviewed proposal. The owner's annotations
override its automatic location derivation, blanket 3–10 group size, old-Excel
visibility rule, fixed notification-channel text and standalone-hosting option.
Culture catalogue/fields are now approved target MVP requirements, superseding
their previous removal. Do not change live schema/flows until #46 and
prerequisites pass.

PR #44 retains owner-confirmed synthetic language cases; it does not implement
culture/status/open filters or authorize real-data discovery. The scope-alignment
PR is planning only and must not close #5/#6/#7/#18 or #45–#49 automatically.
