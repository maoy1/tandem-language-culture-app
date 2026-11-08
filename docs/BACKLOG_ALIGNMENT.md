# Backlog alignment with approved MVP v0.2

This file maps the existing backlog to the owner's latest annotations. GitHub
is authoritative for live status. Approved target behavior is documented in
CURRENT_DESIGN.md. Registration schema/policy JSON now describes the POC-05
target, explicitly pending tenant acceptance. config/discovery_eligibility.json is
the historical language-only baseline; config/discovery_core_build.json is the
owner-only language/culture build fragment. Neither certifies live deployment.

The [2026-10-31 full audit](BACKLOG_AUDIT_2026-10-31.md) reviews all 40 tickets and
records the corrected live acceptance criteria and scheduling. PR #52 separately
prepared the desired POC-05 schema/policy and merged on 2026-11-07 as partial
delivery, not completed tenant acceptance. #5 stays open.
Owner-confirmed catalogue import does not establish participant form/flow acceptance.

## Current all-ticket readiness audit - 2026-11-08 (#45)

40 tickets reviewed: 35 open and 5 closed (#1-#4 and #46). All open tickets remain
valid in their stated phase. #8/#15/#29-#31 are Later, #48 is final migration,
and access tests remain owner-deferred. #31's obsolete Paused-group wording is
corrected to Closed; participant Paused is independent. No issue is closed by
this audit. #46 remains Done and is not reopened for implementation work.

Use exactly one lifecycle label per issue. Ready for review means the whole
ticket deliverable is reviewable, not merely a partial PR. Ready for testing
requires an actual reviewed/imported/deployed version and required test context;
saved fragments without mandatory implementation are not a whole-ticket handover.
Done follows that ticket's own acceptance and closure (document review for a
design ticket). Planned/In progress/Blocked/Deferred distinguish earlier stages.
Preserve unrelated priority/area/type labels.

At this audit, no open ticket meets whole-ticket Ready for review or Ready for
testing. This does not forbid scoped owner smoke tests: #5 has explicit partial
owner passes, #11 has bounded static review, and #28 has two import-probe passes.
None establishes the remaining whole-ticket implementation/ordinary-user AC.

Source matrix: [config/backlog_readiness.json](../config/backlog_readiness.json).
Tests: [catalogue](TEST_CATALOGUE.md), actual immutable [runs](TEST_RUNS.md).
The table is the current snapshot; earlier checkpoint sections below are history
where they conflict. Live labels/bodies must be verified after the audit publish.

| Ticket | Label | Flow scope | Can implementation start? |
|---|---|---|---|
| [#5](https://github.com/maoy1/tandem-language-culture-app/issues/5) | In progress | Core flow change | Can start bounded completion after deployed mapping check |
| [#6](https://github.com/maoy1/tandem-language-culture-app/issues/6) | Planned | Core integration; no standalone flow required | Ready for bounded owner build; verify actual columns first |
| [#7](https://github.com/maoy1/tandem-language-culture-app/issues/7) | In progress | Core flow change | Owner-only package completion can start; mapping/bounds needed |
| [#8](https://github.com/maoy1/tandem-language-culture-app/issues/8) | Deferred | Later flow change | Not an MVP package |
| [#9](https://github.com/maoy1/tandem-language-culture-app/issues/9) | In progress | Shared core flow implementation | Can start shared-source/interface work |
| [#10](https://github.com/maoy1/tandem-language-culture-app/issues/10) | In progress | Core flow changes | Needs bounded request/interface definition before package |
| [#11](https://github.com/maoy1/tandem-language-culture-app/issues/11) | In progress | Core flow change | Needs response/app interface and bounded #47 integration |
| [#12](https://github.com/maoy1/tandem-language-culture-app/issues/12) | In progress | Core persistence plus new reader | Complete owner scaffolds after live field/member mapping |
| [#13](https://github.com/maoy1/tandem-language-culture-app/issues/13) | Planned | New core flow | Ready for owner prototype after field mapping |
| [#14](https://github.com/maoy1/tandem-language-culture-app/issues/14) | Planned | New core flow | Ready for owner prototype after membership mapping |
| [#15](https://github.com/maoy1/tandem-language-culture-app/issues/15) | Deferred | Later product/UI decision; no core flow | Not an MVP package |
| [#16](https://github.com/maoy1/tandem-language-culture-app/issues/16) | Planned | Extend existing core reader | Owner group-reader design can start; mapping required |
| [#17](https://github.com/maoy1/tandem-language-culture-app/issues/17) | Planned | Two new core flows plus history/cancel extensions | Needs request/interface schema and minimum #47 guard |
| [#18](https://github.com/maoy1/tandem-language-culture-app/issues/18) | Deferred | Access parent; no assumed new flow | Owner deferred access work |
| [#19](https://github.com/maoy1/tandem-language-culture-app/issues/19) | Blocked | Shared flow authorization | Protected integration blocked on verified access |
| [#20](https://github.com/maoy1/tandem-language-culture-app/issues/20) | Blocked | Shared flow authorization | Protected integration blocked on verified access |
| [#21](https://github.com/maoy1/tandem-language-culture-app/issues/21) | Blocked | Provisional new notification flow | Blocked on #49 decision and prerequisites |
| [#22](https://github.com/maoy1/tandem-language-culture-app/issues/22) | Blocked | Shared flow authorization; ACL flow not assumed | Protected integration blocked on verified access |
| [#23](https://github.com/maoy1/tandem-language-culture-app/issues/23) | Blocked | Shared reader/action authorization | Protected integration blocked on verified access |
| [#24](https://github.com/maoy1/tandem-language-culture-app/issues/24) | Blocked | Shared terminal-state controls | Conditional logic review possible; protected integration blocked |
| [#25](https://github.com/maoy1/tandem-language-culture-app/issues/25) | Planned | Acceptance work; no production flow | Test planning ready; full execution needs deployed paths |
| [#26](https://github.com/maoy1/tandem-language-culture-app/issues/26) | Planned | Optional local test tooling; no runtime flow | Local generator can start; tenant loading separate |
| [#27](https://github.com/maoy1/tandem-language-culture-app/issues/27) | Blocked | Scale tests; no extra production flow | Measurements blocked on dataset/deployed reader |
| [#28](https://github.com/maoy1/tandem-language-culture-app/issues/28) | In progress | Deployment/handover tests; no business flow | Probe checks passed; full handover not ready |
| [#29](https://github.com/maoy1/tandem-language-culture-app/issues/29) | Deferred | Later flow/data change | Not an MVP package |
| [#30](https://github.com/maoy1/tandem-language-culture-app/issues/30) | Deferred | Later scheduled flow | Not an MVP package |
| [#31](https://github.com/maoy1/tandem-language-culture-app/issues/31) | Deferred | Later dashboard; reader reuse possible | Not an MVP package; obsolete state wording corrected |
| [#39](https://github.com/maoy1/tandem-language-culture-app/issues/39) | Deferred | Access assessment; no assumed new flow | Assessment can resume; owner deferred access work |
| [#40](https://github.com/maoy1/tandem-language-culture-app/issues/40) | Blocked | Isolated access proof; temporary flow only if chosen | Blocked on #39 approach and ordinary accounts |
| [#41](https://github.com/maoy1/tandem-language-culture-app/issues/41) | Blocked | Conditional registration flow changes | Blocked on passing #40 proof |
| [#42](https://github.com/maoy1/tandem-language-culture-app/issues/42) | Blocked | Controlled Discovery flow integration | Blocked on proven registration access path |
| [#45](https://github.com/maoy1/tandem-language-culture-app/issues/45) | In progress | Delivery overview; no production flow | Audit/coordination in progress; MVP parent not complete |
| [#47](https://github.com/maoy1/tandem-language-culture-app/issues/47) | In progress | Shared core safeguards; no separate engine | Needs bounded shared-capacity/recovery design and proof |
| [#48](https://github.com/maoy1/tandem-language-culture-app/issues/48) | Deferred | Final migration; one-off method pending | Final phase; source mappings not reviewed |
| [#49](https://github.com/maoy1/tandem-language-culture-app/issues/49) | Planned | Notification decision; no flow yet | Ready to assess options at notification block |

**Production-flow baseline:** 12 proposed flows, not 12 new ones: six
existing/started, five new business flows, one provisional notification flow.
Access/channel decisions may change this; do not assume an ACL/permission flow
or a notification connector. Technical helper/probe flows are excluded.

**Core flow implementation/integration tickets:** #5/#6/#7/#9/#10/#11/#12/#13/
#14/#16/#17/#21/#47. **Shared access controls affecting those flows:** #19/#20/
#22/#23/#24/#41/#42. These seven do not imply seven new flows. Later possible
flow changes: #8/#29/#30; #31 may reuse readers. #18/#39/#40/#49 are assessment/
proof/decision tickets, not preselected production flows. #25-#28 are tests or
optional local tooling. #48's one-off migration method remains to decide.

## Historical contract-review checkpoint - 2026-11-08

#58 merged; #46 is ready for final contract review. Its closure requires owner
review/merge of the target field/ownership/display tables, not other tickets
finishing. The scope audit in MVP_FIELD_CONTRACT.md assigns each follow-up to
#5/#6/#7/#9-#17/#39-#42/#47/#48/#49/#21 and #45 as applicable.
Final owner choice removes the leader/contact role; all active members can see
and respond to group join requests/manage permitted controls. Optional join
introduction message approved.
Full proposed Discovery display approved, including optional person/group fields;
exclude email and admin/system data. Exact JSON/mappings remain to review.
#47 is bounded to proportionate safeguards and simple safe recovery; low expected
concurrency does not waive capacity, duplicate and truthful-success requirements.
#45 is the overview; no issue per question. Group-join schema/payloads and per-flow interfaces belong to #10/#11/#17
implementation batches; the minimum capacity guard/proof belongs to #47. Identity and
detailed error/pagination decisions are deferred at their integration gates.
TandemMyRequests existing work is assessed against the contract, not presumed
complete or discarded automatically. No live configuration changes here.

## Completed authoring experiment - 2026-11-08

Owner approved one disposable generated-package import probe under #28. #11 app
controls stay paused; no developer/tester assignments or flow permissions changed.
OPS-003 connector-free package import/run passed with owner-supplied output
(success true, IMPORT_PROBE_OK). Owner chose legacy packages. OPS-004 read-only
SharePoint connection package import and test also passed, owner-reported.
Raw OPS-004 action/response output was not supplied.
30 local tests pass. Existing owner SharePoint connection/action was previously
exercised; no new permissions/licences proposed. See IMPLEMENTATION_PLAN.md.
The first probe has no connectors; the second reads only site identity. Neither
replaces #18 access proof, #47 recovery or full deployment reproducibility.
#57 is merged partial backend delivery; #11/#12/#47 remain open.

## Tracking checkpoint — 2026-11-07

Reviewed the live backlog: 40 tickets, #1–#4 closed and 36 open. The approved
scope remains valid; build-first scheduling does not waive acceptance or close
partial features. This checkpoint records owner-reported configuration and
observations, not a tenant export or inferred successful test.

| Tickets | Configured or observed | Remaining |
|---|---|---|
| #5 | Culture setup/form guard and previously recorded Active correction/no-op evidence | Deferred registration/persistence/catalogue checks |
| #7/#9 | TandemDiscovery app binding, MainScreen1 Discover, scrDiscovery Gallery1 and Back; owner reports empty results and working Back | Populated candidate matching, lookup mappings, bounded-query behavior, #6 availability, caller binding and final projection |
| #10 | Connection Requests list; TandemSendRequest reads/Active-different-account check, bidirectional Pending query, create/response branches; candidate arrow connected | No actual send/persistence test; caller/compatibility/availability checks, simultaneous-submit/retry protection, sent/received views and cancellation |
| #11 | Response/Decline and membership scaffold configured, not runtime verified | Complete conditional transitions, publication/recovery, response and UI with #12/#47 |
| #12/#13/#14/#16/#17 | #12 list/member scaffold configured, remaining features unimplemented | Groups/memberships, My groups, lifecycle/leave and existing-group discovery/join |
| #23 and related access tickets | Not implemented/verified by the request scaffold | Private request visibility, caller/response authority and ordinary-user evidence |

**Earlier pause point (superseded by the update below): TandemMyRequests was not started.** The owner explicitly did
not execute the flow-creation instruction. Build the in-app sent/received view
next, then cancellation and #11 responses. Use a separate #10 branch/PR for
request implementation; current #7 artifacts do not constitute a #10 delivery.

The request list currently has Title, SenderParticipantId and
RecipientParticipantId (required Number, zero decimals), and required Status
Choice Pending/Accepted/Declined/Cancelled, default Pending, plus built-in
Created. It is a person-to-person scaffold, not the final group-join/recovery
schema. The Active check tests validation only; app-supplied IDs do not prove
caller identity. Query-then-create checks sequential Pending duplicates only.

No current app/flow versions, populated discovery response, request run or
publication/sharing verification were supplied. Keep implementation tickets
open. Notifications #49/#21 remain undecided; migration #48 stays last.
Detailed tests remain deferred until the integrated core is built, with missing
identity/state/compatibility/reliability behavior tracked as implementation,
not merely unexecuted tests. See TEST_RUNS.md for the evidence checkpoint.

## Latest bounded build checkpoint - 2026-11-07

Current #11 backend construction includes coordinated #12 persistence and #47
conditional-write work. Main response/group-setup configuration is owner-confirmed;
membership cleanup and unfinished-group Ended/feedback writes are now
owner-confirmed saved. Blocks 1 and 2 are configuration-complete; Block 3 review
review2 and the subsequent verified saved-action fragment resolve all three
findings, including the Decline stop flag. Block 3 configuration review is
complete; owner PR #57 review is next. The exported base has
77 actions/depth 6 with valid structural references and five versioned MERGEs.
See config/participant_response_flow.snapshot.json for observed evidence; no
end-to-end cleanup run is supplied.
The previous not-started/unfixed checkpoints below are historical.

Remaining backend batch: (1) conditional membership departure writes,
(2) source-owned unfinished-group end/feedback, (3) configuration review and
the #11 PR checkpoint. Stop for review before app controls or new group features.
No new tenant acceptance is claimed. See IMPLEMENTATION_PLAN.md Current focus
for the bounded finish line and separate unresolved caller/#6/recovery gates.
#52/#54/#55/#56 are merged partial/preparation/tracking deliveries; implementation
tickets stay open. #11 Accept/Decline app controls and group-choice form are next,
not part of the three remaining backend blocks.

## Planning and new work

Current owner scheduling overrides the earlier per-case sequence: core app/flow
construction first, remaining acceptance afterward. #5 stays open; its remaining
cases are deferred while #7/#9 owner-only discovery is built on the existing list.
Then in-app requests, accepted groups/memberships, group actions and notifications.
No notification channel or setup-automation path selected; Approvals is a candidate
for later evaluation. Build completion and verified completion are tracked separately.

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
| #5 | In progress; preparation PR #52 merged, #5 stays open: catalogue/columns/form guard owner-confirmed; Active no-op and correction/follow-up tested, identity/selections preserved. Needs review path, culture/blank-time-zone persistence, catalogue checks and published acceptance remain pending. See POC_05_CULTURE_REGISTRATION.md |
| #6 | Participation Active/Paused/Inactive independent of validation and migration confirmation; open-to-connections; never reactivate a paused participant through validation |
| #7/#9 | Compatible people only; language/culture/combined fit and status/open filters. Exact display fields pending; participant fields generally eligible, admin/system-only columns excluded. No Comments notice. Blank time zone never excludes a candidate |
| #8 | Later ranking; remove as dependency for group discovery. No required automatic location/time-zone derivation |
| #10/#11 | #10 send flow, My requests flow/screen and cancel flow/button owner-confirmed configured; no runtime request/cancellation pass. Earlier not-started checkpoint is superseded. #11 response/Decline and acceptance membership scaffold configured, not runtime verified; conditional transitions/publication/recovery/UI remain. Caller/compatibility/#6 availability and #47 safeguards remain. Meet-first/expiry/bulk Later |
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
