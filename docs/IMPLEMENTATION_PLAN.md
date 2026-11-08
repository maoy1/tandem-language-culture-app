# Tandem implementation plan

The approved design is CURRENT_DESIGN.md. This plan reflects the owner's
annotations to Combined Requirements v0.2. GitHub tickets hold implementation
acceptance and status; planning completion does not imply deployment.

## Current focus - #45 flow/readiness audit

#46 is closed and PR #59 merged. The contract is accepted; implementation is not
reopened into #46. #45 now inventories all 35 open tickets, proposed experiences,
flow interfaces, remaining work and versioned test handover. See
BACKLOG_ALIGNMENT.md and config/backlog_readiness.json for every ticket.

- [x] Read all 40 tickets, existing labels/PRs and recorded test evidence.
- [x] Distinguish 13 core flow implementation/integration tickets from 7 shared
      access-control tickets, tests, assessments, final migration and Later work.
- [x] Prepare per-ticket experiences/readiness/evidence/test references and add
      missing planned test definitions; preserve original acceptance obligations.
- [x] Published/verified one lifecycle label on all 40 tickets and experience/test review on all 35 open tickets.
- [ ] Review/merge this #45 audit batch before new feature implementation.

Proposed production inventory (technical probes excluded):

| Flow | Owner | Current evidence |
|---|---|---|
| Participant submission | #5 | Existing, partial owner checks |
| TandemDiscovery | #7 | Existing scaffold |
| TandemSendRequest | #10 | Existing scaffold |
| TandemMyRequests | #10 | Completion uncertain; assess then retain/rebuild |
| TandemCancelRequest | #10 | Existing scaffold |
| TandemRespondRequest | #11 | 77-action static review; runtime pending |
| TandemMyGroups | #12 | Proposed new |
| TandemUpdateGroup | #13 | Proposed new |
| TandemLeaveGroup | #14 | Proposed new |
| TandemSendGroupJoinRequest | #17 | Proposed new |
| TandemRespondGroupJoinRequest | #17 | Proposed new |
| TandemNotifyRequest (provisional) | #21 | Conditional after #49 |

This is a 12-flow baseline: six existing/started plus five new business flows
and one provisional notification flow. Existing means partial configuration,
not completed acceptance. Access architecture or notification choice may change
the final count. Package generation is possible for bounded owner prototypes;
not every production contract or prerequisite is ready. No new runtime/paid
connector is approved.

Ordered delivery batches (one owner ticket/branch/PR at a time):
1. **#6 next:** verify/bind participation/openness fields and form controls;
   preserve edits/validation and define membership-derived status integration.
   Complete outstanding catalogue/registration validation under separate #5 work.
2. **#47:** specify/prove minimum shared capacity/retry guard before acceptance
   packages rely on it; keep recovery proportionate, no elaborate lock platform.
3. **#10:** bounded request/history/cancel contract and package; assess actual
   MyRequests before retaining versus fresh generation. Coordinate group target
   schema with #17 without claiming group joins implemented.
4. **#11 then #12:** finish response/app path and group/member persistence/My groups.
5. **#13 then #14:** member-managed updates and self-service leave.
6. **#16 then #17:** group Discovery and join/send/respond with shared history.
7. **#49 then #21:** verify options, choose events/channel, implement notifications.
8. **#25-#28:** scoped acceptance, synthetic scale and handover as each deployed
   path is ready; fix actual blockers during construction, keep unrun cases open.
9. **#48 last:** actual old-data mapping/confirmation decision and migration.

Workstream gates: #7/#9 eligibility/interface completion accompanies affected
builds. #39-#42 and #19-#24 require the verified access approach before ordinary
integration/testing; owner deferred colleague proof, not the need for it. Do not
silently change connections, permissions or licences. A dependency blocks its
specific integration/test, not every preparatory task or an accepted design ticket.
#8/#15/#29-#31 stay Later. Organiser contact remains a #45 decision before related
guidance is published. No routine admin dispatch/individual grant work added.

Status labels: Planned, In progress, Blocked, Deferred, Ready for review,
Ready for testing, Done. At this audit no open whole-ticket deliverable meets the
two Ready stages; owner-only fragments may still be tested with explicit scope.
Done is applied only to closed tickets' own accepted scope, not new-MVP behavior.

## Completed package experiment checkpoint (#28)

Owner approved this bounded authoring-method experiment on 2026-11-08 after
pausing the #11 app-controls batch. No team assignments or app-control steps
have been confirmed. #57 is merged; backend configuration review is complete,
not runtime acceptance. Functional feature construction stays paused during
this probe.

Prepared locally: artifacts/import_probe/TandemImportProbe.zip plus readable
definition/review JSON, built by scripts/power_automate/build_import_probe.py.
The package follows the observed legacy export envelope but is generated from
scratch: fresh IDs, one New flow resource, empty connector maps/references,
Power Apps (V2) with no inputs, Compose + Response only. No SharePoint calls,
data/notification actions, schedule or original working-flow identifiers.

Local checks: 26 pytest passed (4 probe safety checks + 22 existing checks),
ZIP CRC/JSON/manifest checked, no original export identifiers/site/account
bindings copied. Initial restricted pytest run had 4 temporary-folder setup
errors; the permitted rerun passed all 26. This is not tenant import proof.

Owner-confirmed OPS-003 PASS (2026-11-08): package imported, initially off;
owner turned it on and supplied response statusCode 200, success true,
message IMPORT_PROBE_OK. This establishes connector-free import/run for this
account/environment, not a general role/policy audit. Keep the original
preparation evidence in TEST_RUNS.md. Owner chose to stay with legacy packages;
no Dataverse migration, new environment or licence dependency.

OPS-004 also passed (owner-reported import and test). Prepared
artifacts/import_probe/TandemSharePointImportProbe.zip and readable definition/
review JSON. Import as NEW TandemSharePointImportProbe and bind the existing
SharePoint connection once. It uses the standard SharePoint HTTP action already
exercised by the owner; one GET _api/web?$select=Id reads only site identity.
No lists, business records, writes, notifications or schedules. The disposable
probe uses an embedded owner connection; it is not participant caller binding.
Owner confirmed import and test succeeded using the selected existing connection;
raw action/response output was not supplied. Stop/report a
blocked connection or permission/licence prompt; do not change access/settings.

OPS-004 steps:
1. Import package as Create as new; select the existing SharePoint connection.
2. Turn on the new probe if imported off; Test > Manually > Run flow.
3. Read_site_identity and Response should succeed; response success true,
   message SHAREPOINT_IMPORT_PROBE_OK. Record actual result/error.
4. Only after this passes, choose a small remaining business-flow package.
   Do not replace the existing response flow or claim full #28 acceptance.

Local checks: 30 pytest passed; ZIP CRC, JSON and connector-resource mappings
checked. Owner confirms OPS-004 import/test succeeded. No business-feature
rollout or team handoff yet. Review/merge this #28 experiment batch before
resuming #11 app controls and selecting the next small business-flow package.
Keep #28 open for the remaining reproducibility acceptance. Official guidance:
https://learn.microsoft.com/en-us/power-automate/export-import-flow-non-solution

## Working process

Owner direction (2026-10-31): build the end-to-end app/flow path first and resume
the remaining detailed tests afterward. Stop the current per-case registration
test sequence. Retain passed/failed evidence and mark outstanding cases deferred,
not passed. Use batched build steps. One ticket per branch/PR still applies;
stacked build branches may proceed while earlier acceptance remains open. Actual
save/run blockers are fixed during construction; full verification follows the
integrated workflow. Do not close incomplete tickets or widen release on that basis.

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
- [ ] #46: final owner review/merge of the field/ownership and approved Discovery
      display contract. Product rules are agreed; target technical field tables
      are reviewable. Do not keep this design ticket open for per-flow payloads,
      tenant setup/tests, #47 proof, #48 migration or #39-#42 access verification.
      The scope audit in MVP_FIELD_CONTRACT.md names each receiving ticket.
- [ ] #5: implement controlled culture-share/interest fields; update registration
      and validation to allow empty time zone. No participant group-size field.
      PR #52 merged preparation (configuration, 85 culture values, setup guide
      and local tests); this does not complete #5 tenant acceptance. Owner confirms catalogue population/checks, but the latest Participants
      screenshot did not show culture lookups. Owner subsequently confirms both
      optional multi-value culture lookups and removal of the Time zone required
      setting. Owner also confirms both culture cards added to Form1 after refresh
      and app saved. Culture labels now display correctly, and the empty-selection
      save guard passes in Preview (owner-reported). Persistence and flow validation
      remain unverified; no new published app version confirmed.
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
| #11 | Response/Decline and acceptance membership scaffold configured, not runtime verified | Conditional transitions, publication/recovery, response and app UI with #12/#47 |
| #12/#13/#14/#16/#17 | #12 group/member lists and acceptance scaffold configured; other features not implemented | Complete accepted groups/memberships, My groups, lifecycle/leave and existing-group discovery/join |
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

## Completed #11 backend configuration batch

Latest owner checkpoint (recorded 2026-11-07): cleanup membership Left writes,
unfinished-group Ended write and feedback are owner-confirmed saved. Blocks 1
and 2 are configuration-complete. Block 3 is now configuration-review complete:
review2 verified Status Value and ParticipantId label, and the owner's subsequent
saved-action Code view verifies Decline ContinueProcessing = false with the
correct predecessor. No post-correction full export or runtime run is claimed.
The flow has not been exercised end to end. Owner confirmations of
Save/configuration do not establish runtime acceptance.

The product scope is unchanged. The guided #11 batch grew to include coordinated
#12 group persistence and #47 conditional transitions/recovery. This expansion
must be visible instead of presenting each added action as the final step.
The earlier plan's not-started/draft/ordinary-update descriptions below older
checkpoints are historical and superseded by this current section.

### What is configured

| Area | Evidence/state |
|---|---|
| Request history and Cancel (#10) | Owner confirms flow/screen/button bindings. PR #56 merged. Cancel conditional read/check/write owner-confirmed; no real cancellation run supplied |
| Respond input/validation and Decline (#11) | Owner confirms recipient/Pending checks, group-choice inputs, conditional Decline and result variables |
| Initial group/member persistence (#12 with #11) | Groups/Group Members, SourceRequestId/MembershipKey, create/reuse loop and membership verification configured |
| Conditional acceptance and group setup (#11/#12/#47) | ETag Accepted attempt, outcome reread, group SetupComplete/initial-state update configured; no real acceptance result supplied |
| Final result/response (#11) | Final request reader was missing; owner added it and saved the five-row condition and one success/message/groupid response |
| Structure and defects | First pasted block: 34 actions/depth 6. Later preparation block: 26 actions/depth 5; Membership key, recipient From, IF-MATCH and outcome predicate corrections statically verified. Complete exports reviewed at 77 actions/depth 6; later saved Decline correction verified separately |
| Rejected-attempt cleanup (#47 shared) | Guarded membership revision/conditional Left+LeftAt loop, conditional unfinished-group Ended write and terminal-status feedback owner-confirmed saved; no runtime cleanup pass |

The accepted intermediate structure keeps Group choices valid inside Prepare
group with its actions. Do not repeat the superseded instruction to empty that
branch. Memberships ready now has its completion work moved to the separate
main-level Complete acceptance stage; its failure branch stops processing.

### Finish line for this backend build batch

All three blocks in this bounded backend batch are configuration-complete.
The next checkpoint is owner review of PR #57, not new feature construction:

1. **Membership cleanup** - loop over the two request-owned membership episodes,
   read each current revision, conditionally mark only still-Active matching
   memberships Left and set LeftAt. Preserve keys, JoinedAt and history.
2. **Unfinished-group cleanup and feedback** - conditionally mark only the
   source-owned, not-SetupComplete group Ended after membership cleanup; preserve
   completed groups/Accepted results. Make final response reflect Cancelled/
   Declined versus incomplete setup, rather than report a completed acceptance.
3. **Configuration review and PR checkpoint** - inspect supplied current blocks,
   exact action references, status Value fields, gate/run-after dependencies and
   full available nesting. Save without template errors, synchronize docs/issues
   and raise the #11 draft/partial-delivery PR for review before new feature work.

Current status: **Blocks 1/2 saved; Block 3 configuration review complete.**
Review2 plus the verified post-export action correction resolves all three
findings: Decline stop flag false, final Choice Value, ParticipantId input label.
Structural checks: 77 actions, depth 6, valid action/sibling references, five
versioned MERGEs and one response. The sanitized reference explicitly records
the action overlay and retains the source-export fingerprints/history.
PR #57 is merged as partial configuration delivery; it does not close
#11/#12/#47 or establish end-to-end behavior. App controls are paused for the
owner-approved import experiment described at the top of this plan.

Do not add My groups, notification configuration, group-join features or a new
architecture to this backend batch.

The finish line means **backend configuration milestone**, not #11/#12/#47
closure or deployed readiness. Their unverified requirements remain open.

### After the backend PR review

1. Same #11 workstream, next batch: Accept/Decline buttons and the group-choice
   form in Power Apps; wire the saved response. These are not yet built.
2. #12/#13: My groups and allowed group state/name/description/capacity controls.
3. #16/#17/#14: compatible existing-group discovery/join and self-service leave.
4. #49 then #21: central notification options/decision and selected implementation.
5. Resume deferred #5/#25 and relevant #26-28 acceptance, then #48 Excel migration.

No new permission/connector/licence requirement is implied by flattening.
Production remains existing SharePoint/Power Apps/Power Automate entitlements.

### Required gaps kept visible

Separate participation/openness (#6), trusted caller identity and ordinary-user
access (#18-20/#22-24/#39-42), agreed projection, catalogue/persisted-focus checks,
bounded data access and full #47 retries/races/recovery are still required before
wider release. This cleanup does not by itself cover interruption before a group
ID is captured, accepted-but-unfinished retry recovery, duplicate create races
or last-slot joins. Design supported automatic recovery where needed; ordinary
use must not depend on admin repair. Necessary critical-case assistance remains
allowed. No completed test is inferred from a configured guard.

Detailed tests stay deferred per the owner; fix actual save/run blockers during
construction. Keep all unexecuted cases pending and preserve earlier scoped
evidence in TEST_RUNS.md.

### Merged build checkpoints

- #52: merged preparation for #5, not completed tenant acceptance.
- #54: merged partial discovery reference/app build; #7/#9 remain open.
- #55: merged tracking alignment.
- #56: merged partial #10 request history/cancellation record; #10 remains open.
- #57: merged response/group backend reference; #11/#12/#47 remain open.

One ticket/branch/PR per delivery batch; finish/review the current PR before
starting the next implementation batch. Keep incomplete tickets open.
