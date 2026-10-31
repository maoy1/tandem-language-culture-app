# Backlog audit — 2026-10-31

Related to planning parent #45. Review covers all **40 issue tickets**: #1–#31,
#39–#42 and #45–#49. Pull requests are not counted as tickets.

## Authority and evidence

Reviewed CURRENT_DESIGN.md, MVP_FIELD_CONTRACT.md, IMPLEMENTATION_PLAN.md and
BACKLOG_ALIGNMENT.md against direct GitHub issue reads, including title, body,
state, labels and milestone. Search was used for inventory only; direct reads
verified the issue contents. PR #51 is merged; PR #52 remains a draft for #5.

The latest Participants screenshot still shows required Time zone and does not
show the two culture lookup columns. Owner reports the Culture catalogue's
85-row population/checks completed. Those are separate setup facts, not an app/
flow registration acceptance pass. POC-05 workbook/setup evidence is on PR #52.

## Reconciliation

- Updated 28 ticket titles/bodies to match approved scope and current evidence.
- Moved missing core MVP/release-gate tickets into POC Vertical Slice, so the
  milestone no longer omits required group discovery, authorization, tests and
  delivery-decision work.
- Removed Later #8/#15 from the core milestone and classified them P2, consistent
  with existing Later #29–#31.
- Preserved all issue states: 4 closed baseline tickets and 36 open tickets.
  Corrected #2's obsolete provisioning promise without reopening it or claiming
  automated tenant deployment.
- No tickets were closed by this audit. No permissions, app logic or live schema
  were changed by backlog reconciliation.

## Complete issue inventory

| Ticket | State retained | Action | Alignment |
|---|---|---|---|
| [#1](https://github.com/maoy1/tandem-language-culture-app/issues/1) | closed | Reviewed; retained | Retain closed repository baseline. |
| [#2](https://github.com/maoy1/tandem-language-culture-app/issues/2) | closed | Scope/evidence updated | Correct obsolete automated-provisioning scope; retain closed manual-setup baseline. |
| [#3](https://github.com/maoy1/tandem-language-culture-app/issues/3) | closed | Reviewed; retained | Retain closed self-registration baseline; no new privacy/culture pass inferred. |
| [#4](https://github.com/maoy1/tandem-language-culture-app/issues/4) | closed | Reviewed; retained | Retain closed language persistence baseline. |
| [#5](https://github.com/maoy1/tandem-language-culture-app/issues/5) | open | Scope/evidence updated | Record catalogue setup separately from still-missing/unverified participant culture fields and required time zone. |
| [#6](https://github.com/maoy1/tandem-language-culture-app/issues/6) | open | Scope/evidence updated | New defaults Active/open Yes; edits preserve choices; personal/group state independent. |
| [#7](https://github.com/maoy1/tandem-language-culture-app/issues/7) | open | Scope/evidence updated | Remove Comments notice/predefined inclusion; optional time zone; controlled compatible response. |
| [#8](https://github.com/maoy1/tandem-language-culture-app/issues/8) | open | Scope/evidence updated | Later, optional context only; remove participant preference assumption and core milestone. |
| [#9](https://github.com/maoy1/tandem-language-culture-app/issues/9) | open | Reviewed; retained | Already aligned: one platform rule location; no Python/paid runtime. |
| [#10](https://github.com/maoy1/tandem-language-culture-app/issues/10) | open | Scope/evidence updated | Sender cancellation, Pending deduplication and unavailable-recipient decision boundary. |
| [#11](https://github.com/maoy1/tandem-language-culture-app/issues/11) | open | Scope/evidence updated | Current member authority, acceptance rechecks, terminal history and cancel/accept race. |
| [#12](https://github.com/maoy1/tandem-language-culture-app/issues/12) | open | Scope/evidence updated | Separate group/member lists, approved capacities/focus roles, staged acceptance and initial state. |
| [#13](https://github.com/maoy1/tandem-language-culture-app/issues/13) | open | Scope/evidence updated | Any active member; fixed type/focus; bounded capacity; Ended final. |
| [#14](https://github.com/maoy1/tandem-language-culture-app/issues/14) | open | Scope/evidence updated | Closed preserved; invalid-focus discovery suppression; no automatic recovery. |
| [#15](https://github.com/maoy1/tandem-language-culture-app/issues/15) | open | Scheduling aligned | Later warning review; remove core milestone and P0 label. |
| [#16](https://github.com/maoy1/tandem-language-culture-app/issues/16) | open | Scope/evidence updated | Compatible open groups; fixed capacity ranges; real count/slots; projection undecided. |
| [#17](https://github.com/maoy1/tandem-language-culture-app/issues/17) | open | Scope/evidence updated | Any active member response; fit/capacity rechecks; sender cancellation. |
| [#18](https://github.com/maoy1/tandem-language-culture-app/issues/18) | open | Scope/evidence updated | Owner-deferred ordinary-user tests; no speculative architecture; exceptional admin support allowed. |
| [#19](https://github.com/maoy1/tandem-language-culture-app/issues/19) | open | Scope/evidence updated | Controlled discovery projection; permitted member fields; no general list access assumption. |
| [#20](https://github.com/maoy1/tandem-language-culture-app/issues/20) | open | Scope/evidence updated | Trusted request/membership actions, sender cancellation, verified access method. |
| [#21](https://github.com/maoy1/tandem-language-culture-app/issues/21) | open | Scheduling aligned | Body already aligned: selected notifications only after #49; include in core milestone. |
| [#22](https://github.com/maoy1/tandem-language-culture-app/issues/22) | open | Scope/evidence updated | Membership-aligned authority; item ACL synchronization is an option, not selected architecture. |
| [#23](https://github.com/maoy1/tandem-language-culture-app/issues/23) | open | Scope/evidence updated | Request visibility/authority through verified approach; no assumed individual ACL grants. |
| [#24](https://github.com/maoy1/tandem-language-culture-app/issues/24) | open | Scope/evidence updated | Terminal request controls/history; expiry Later; no assumed ACL cleanup design. |
| [#25](https://github.com/maoy1/tandem-language-culture-app/issues/25) | open | Scope/evidence updated | Stable MVP cases; no Comments notice; approved capacities, optional time zone and departure rules. |
| [#26](https://github.com/maoy1/tandem-language-culture-app/issues/26) | open | Scope/evidence updated | Current synthetic culture/status/group fields; no required location; isolated scale-load prerequisites. |
| [#27](https://github.com/maoy1/tandem-language-culture-app/issues/27) | open | Scope/evidence updated | Supported-platform scaling limits; remove hosted-service fallback. |
| [#28](https://github.com/maoy1/tandem-language-culture-app/issues/28) | open | Scope/evidence updated | Document manual setup/handover; no tenant-provisioning automation promise. |
| [#29](https://github.com/maoy1/tandem-language-culture-app/issues/29) | open | Reviewed; retained | Already marked Later freshness; unchanged. |
| [#30](https://github.com/maoy1/tandem-language-culture-app/issues/30) | open | Reviewed; retained | Already marked Later reminders; unchanged. |
| [#31](https://github.com/maoy1/tandem-language-culture-app/issues/31) | open | Reviewed; retained | Already marked Later dashboard; unchanged. |
| [#39](https://github.com/maoy1/tandem-language-culture-app/issues/39) | open | Scope/evidence updated | Deferred access assessment before access redesign, not a block on owner/synthetic core preparation. |
| [#40](https://github.com/maoy1/tandem-language-culture-app/issues/40) | open | Scope/evidence updated | Deferred ordinary-account proof; owner success does not establish privacy. |
| [#41](https://github.com/maoy1/tandem-language-culture-app/issues/41) | open | Scope/evidence updated | Retest current culture/optional-time-zone contract when access cutover is actually verified. |
| [#42](https://github.com/maoy1/tandem-language-culture-app/issues/42) | open | Scope/evidence updated | Reuse eligibility, not deferred ranking; agreed response fields; no Comments notice. |
| [#45](https://github.com/maoy1/tandem-language-culture-app/issues/45) | open | Scope/evidence updated | Latest scope/dependency parent and explicit baseline-versus-implementation evidence. |
| [#46](https://github.com/maoy1/tandem-language-culture-app/issues/46) | open | Scheduling aligned | Body already aligned: accepted subset plus outstanding decisions; include in core milestone. |
| [#47](https://github.com/maoy1/tandem-language-culture-app/issues/47) | open | Scope/evidence updated | Explicit accept/cancel races and stable concurrency test references. |
| [#48](https://github.com/maoy1/tandem-language-culture-app/issues/48) | open | Scheduling aligned | Body already aligned: actual Excel inspection/migration last; include in core milestone. |
| [#49](https://github.com/maoy1/tandem-language-culture-app/issues/49) | open | Scheduling aligned | Body already aligned: notification decision before implementation; include in core milestone. |

## Remaining decisions and gates

- Finish #5 participant lookup setup, optional time zone, app/flow validation and
  versioned live tests; the screenshot does not establish completion.
- #46 exact technical mappings and remaining field choices stay open. Decide
  actual candidate/group projections with #7/#42, not by returning raw lists.
- Personal Active/open defaults are agreed; validation must preserve choices.
  Group Open/Closed/Ended is independent of personal openness.
- The approved language capacity is 2 or 3 total; Culture and Combined are 2–10.
  Each stated focus requires a relevant sharer and a different learner; every
  member participates in at least one focus, collectively both for Combined.
- Notification matrix #49 remains undecided before #21. Unavailable-recipient
  pending-request disposition must be specified with requests; acceptance cannot
  admit an unavailable participant. No new automatic cancellation/timer policy
  was approved by this audit.
- #18/#39–#42 ordinary-colleague access checks remain deferred by the owner;
  required before wider rollout. Admin Members access does not prove exposure.
  No access architecture or automatic per-item permission design is selected.
- #47 safeguards all acceptance paths and retries before they close. A single
  flow's concurrency setting is not proof of cross-flow capacity safety.
- Actual source Excel inspection/migration #48 is last. Proposed migration-
  confirmation discovery behavior is still a decision, not a blanket early gate.
- Later ranking, warning, freshness, reminders and dashboard remain open future
  work; they do not block core implementation.

## Ongoing process

When an approved decision changes, reconcile affected **open ticket bodies,
dependencies and scheduling** together with design/plan changes. Preserve closed
baseline evidence. Do not check an implementation acceptance box merely because
the requirement is approved or a local test passes.

One ticket branch/PR at a time. Record stable test IDs, observed app/flow version,
actual result and remaining gaps before closing implementation work. Verify
GitHub issue/PR state and the plan after merge. This audit is documentation and
backlog maintenance under #45, not completion of the MVP parent.

