# Tandem implementation plan

The approved design is CURRENT_DESIGN.md. This plan reflects the owner's
annotations to Combined Requirements v0.2. GitHub tickets hold implementation
acceptance and status; planning completion does not imply deployment.

## Current focus - #7 Discovery owner preview; #12/#47 complete; #61 Ready for testing

#46 is accepted/closed. Tracking now separates Flow, App, Shared technical and
Overview tickets. One production flow has one owner; old partial work/evidence
does not mean active In progress. See BACKLOG_ALIGNMENT.md and the complete
config/ticket_scope_map.json transfer of 246 former checklist items.

- [x] Prepare 41 focused open scopes and 8 new successor tickets.
- [x] Route every original acceptance item to an active focused owner.
- [x] Published/verified all 48 types/lifecycle labels, 41 focused open bodies, 2 Superseded handoffs and WIP 0 pending review.
- [x] PR #60 merged; focused-ticket implementation resumed.
- [x] #66: metadata inspection, permission preview and five-setting apply/readback succeeded.
- [x] #66: fresh whole-schema audit Verified with no findings; repeat setup returned SETUP_VERIFIED.
- [x] #66: owner confirmed all five writes Skipped on a new repeat, SETUP_VERIFIED; own schema tests passed.
- [x] PR #69 merged; #66 closed and labelled Done.
- [x] #6: owner confirmed both fields added to Form1.
- [x] #6: real choices and basic Paused/No save/validation/reopen preservation passed; account/selections unchanged.
- [x] #6: owner reported Version 16, saved 2026-11-08 15:34:26 Europe/Berlin; implementation context recorded.
- [x] #6: working Combo box table-default binding; owner confirms New Active/open Yes, edit preservation and language/culture-only save/reopen; corrected Live Version 19 recorded.
- [x] PR #70 merged; #6 closed/Done on owner-confirmed Version 19 UI scope. Backend integration checks remain #61/#7/#10/#25.
- [x] #5: owner confirmed Live Version 19 A/B PASS for blank-zone/multi-selection persistence and all-four-empty guard/input retention/no saved-item change. PR #71 merged; #5 closed/Done.
- [x] #61 implementation/testing handover: current export inspected; 26-action/depth-3 package generated; 101 local tests passed. Owner valid/no-change and necessary Active correction/readback/follow-up passed (item 38); feedback accepted/published as owner-reported Live Version 26; remaining scoped target acceptance pending.

See POC_03_PARTICIPANT_SELF_REGISTRATION.md for #6 Studio steps and UI6 tests.
POC_SHAREPOINT_SETUP.md retains the completed #66 package/mapping evidence.

Sole production-flow ownership:

| Flow | Owner | Phase |
|---|---|---|
| TandemDiscovery | #7 | Core |
| TandemSendRequest | #10 | Core |
| TandemRespondRequest | #11 | Core |
| TandemUpdateGroup | #13 | Core |
| TandemLeaveGroup | #14 | Core |
| TandemSendGroupJoinRequest | #17 | Core |
| TandemNotifyRequest (provisional) | #21 | Core |
| TandemFreshnessReminder | #30 | Later |
| Participant submission | #61 | Core |
| TandemMyRequests | #62 | Core |
| TandemCancelRequest | #63 | Core |
| TandemMyGroups | #64 | Core |
| TandemRespondGroupJoinRequest | #65 | Core |

Next focused batches (one selected non-overview ticket at a time; #7 is current):

1. **#66 Shared technical:** verify participant/catalogue field
   mappings and availability defaults once; flag any permitted setup first.
2. **#6 App:** participation/openness controls; **#5 App:** complete registration
   UI. **#61 Flow** owns server validation independently.
3. **#9 Shared technical** maintained compatibility and **#47 Shared technical**
   minimal conditional/capacity/recovery artifact and proof. **#12 Shared
   technical** owns actual group/member schema, not acceptance implementation.
4. **#7 Flow** Discovery / **#16 App** screen. **#10 Flow** personal send,
   **#62 Flow** inbox reader, **#63 Flow** cancellation,
   **#67 App** request screen; assess current MyRequests before rebuild.
5. **#11 Flow** personal response/new-group creation, **#64 Flow** own
   groups reader, **#68 App** screen; then **#13 Flow** group update
   and **#14 Flow** leave. Reuse existing saved work only if it fits the contract.
6. **#17 Flow** group-join send and **#65 Flow** group-join response.
7. **#49 Shared technical** notification choice, then **#21 Flow** if required.
8. **#25-#28 Shared technical** scoped acceptance/data/scale/handover as actual
   artifacts become testable; **#48 Shared technical** migration is final phase.

Access is its own bounded workstream: #39 assessment -> #40 isolated proof ->
#41 App registration integration; #42 controlled-candidate adapter/proof and #19/
#20/#23 shared guards integrate only through the verified method. Ordinary-user
tests remain owner-deferred, not passed. Unknown permission/setting/connection/
licence stops the dependent live change. No routine individual admin work or
paid fallback. #18/#45 are overview rollups, never active development merely
because children are unfinished. #8/#15/#29-#31 remain Later.

Close each ticket on its own scoped acceptance; record concrete blocked cases
rather than require every parent/dependency closed. Minimal app-call smoke tests
belong to Flow tickets; full layout belongs to App tickets. Disposable proof
harnesses belong to their explicitly scoped Shared technical evidence, not an
untracked production service. In progress is active work only, max one. Queued
partial work stays Planned. Superseded is not Done. PR #60 is merged. #66 and #6 are Done after merged PRs #69/#70. #5 is Done after merged #71. #61 remains Ready for testing; #9 is Done after merged #73; #47 is the sole In progress scope.

## Ticket execution agreement - #45

Before each ticket starts, inspect its current scope/AC and evidence, identify
exact inputs/outputs and prerequisite gates, and refine the test description.
Routine technical choices are the agent's work. The owner decides material
product choices and supplies unavoidable tenant access/actions; do not turn
technical drafting into repeated owner decisions.

Flow ticket delivery is package-first: importable legacy ZIP, readable definition,
input/output/connection mapping, local validation, and numbered import/smoke/
acceptance tests. Manual action-by-action construction is not the default.

Every Flow package has a structural gate: **at most 500 action definitions and
8 nesting levels**, with measured totals included in its handover. Count all
branches/control actions, not runtime loop iterations. Reject an over-limit
package and flatten/redesign before import; keep headroom where practical.
Child flows/Solutions are not an assumed workaround under the legacy-package
and existing-entitlement constraints. Official reference:
https://learn.microsoft.com/en-us/power-automate/limits-and-config
Shared technical metadata/test probes may also use disposable packages if that
reduces inspection work; they are not extra production flows.

Each test handover must provide:

1. Verified prerequisites, permitted account role and isolated scope.
2. Exact artifact/version, fixture/setup and input values.
3. Numbered actions and expected UI/output/persisted state for each case.
4. Failure/blocked interpretation, retry/cleanup and sanitized evidence to return.
5. What has actually passed, what is NOT RUN and what blocks own acceptance.

Minimize manual owner implementation using allowed packaging/tooling. Import,
existing-connection choice and actual tenant execution may still need the owner.
App package/edit capabilities must be checked at the relevant App ticket; flow
probe success does not prove automated App editing. Flag required unavoidable
steps and verify setup before relying on them. No additional paid platform,
permission expansion or CLI/sign-in dependency is assumed.

#66 packages are implemented/imported. Owner supplied metadata collection, dry
preview and successful apply/readback evidence on 2026-11-08. Final full audit is Verified; owner confirmed the five writes skipped on a new
repeat with SETUP_VERIFIED. All own schema tests passed; PR #69 merged and #66 closed. See TEST_RUNS.md and PR #69.

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

## Owner testing handover decision — 2026-11-08

Owner asks to merge #72 and mark #61 Ready for testing so other authorized testers
can cover the remaining cases. [the #61 issue description](https://github.com/maoy1/tandem-language-culture-app/issues/61) preserves passed/pending/blocked
variants and access/fixture gates. #61 stays open, not Done; no full-test pass
required from the owner before moving implementation forward. #9 own proof is passed and awaits review.

## #9 implementation — 2026-11-08

Reusable typed normalization/person/group source, 39 synthetic expected cases and
connector-free import proof built; 121 local tests pass, proof 45 actions/depth 4.
Owner defers Any language; no wildcard/focus support. Tenant proof import/run and
source review pending. Detailed current test handover/check boxes live in issue #9.
Next #47 shared conditional-write/recovery proof, then #12 group schema, followed
by #7 Discovery per ordered batch. #61 remains open Ready for testing.

## #9 proof acceptance — 2026-11-08

Matching-build/source-hash tenant proof run 08584074461495133197897516907CU19
reports 39 cases, allPassed true, no failures. Own bounded proof passed; #9 Ready
for review in #73, no owner rerun needed. Consumer integrations remain separate.
#61 remains Ready for testing. Next implementation after this review is #47.

## #47 implementation — 2026-11-08

PR #73 merged (6879bd90b1321a695143bd327e3aa3a52e9eece2); #9 closed/Done.
#47 now owns bounded shared coordination contract/reference proof and read-only
fixture-permission preflight. 152 local tests, 70 reference schedules; native
cross-item proof and new metadata/fixture prerequisites still pending. Preflight
5 actions/depth 1, no writes. #61 remains Ready for testing; #74 cleanup still open.

## #47 native fixture preparation — 2026-11-08

Read-only preflight owner-passed (run 08584074437966574454125674321CU01).
Native synthetic tagged fixture package built: 10 checks, 321 actions/depth 6;
165 local tests. Explicit default-false write gate, existing SharePoint connection,
no production/permission changes or deletes. Import/run pending; model/native/
unknown-outcome/consumer evidence remain distinguished. Inline handover in #47.


### #47 connector duplicate-error correction — v2

The owner supplied the first native report: 5/10 checks passed, allPassed=false. All five failed cases invoke the duplicate-response predicate. The Duplicate primary raw body confirms SharePoint error -2130575169 / Microsoft.SharePoint.SPDuplicateValuesFoundException wrapped by the existing SharePoint connector as HTTP 502. The original proof's 400/409-only classifier was too narrow. The five-case common cause is supported by local replay; a native v2 pass remains unverified.

The classifier now requires the exact native duplicate exception/code together with HTTP 400, 409 or 502. For the wrapped form, both exact entries must exist in innerError.errors. Generic 502, unrelated 400/409, incomplete error identifiers and other statuses fail. Existing schema/row/ETag/count/readback checks remain required. All five duplicate-dependent reports now include diagnostic codes/messages. No cookie or response headers are stored.

Supported package: artifacts/coordination/TandemCoordinationFixture-v2.zip, build b54d7cee-971d-4af3-924f-e81d5fefaec9, new tagged list Tandem47Fixture_b54d7cee971d4af3. Import as Create as new, display name TandemCoordinationFixture v2, existing SharePoint connection; Run fixture writes=Yes. Old fixture is retained; no deletion or production mutation. Expected Fixture report: 10 tests, allPassed=true, failedCases=[]. Return that report; expected rejected duplicate actions may still show red 502.

Validation: 179 local tests passed, including wrapped native duplicate simulation in both writer orders and generic/error-negative cases; 321 actions / depth 6 (limits 500/8). V2 NOT_IMPORTED_NOT_TESTED. #47 remains In progress / PR #75 draft pending native results. No genuine timeout/killed-run, production consumer or notification-delivery proof inferred.


### #47 native bounded proof passed — 2026-11-08

Matching v2 build `b54d7cee-971d-4af3-924f-e81d5fefaec9`, owner run `08584074402025984197329193901CU08`: testCount=10, allPassed=true, failedCases=[]. Permission gate passed; existing tagged fixture `Tandem47Fixture_b54d7cee971d4af3` / `abade32d-8b24-4b30-b2e0-668d10238acb` reused (fixtureCreated=false). Summary exactly as supplied: `artifacts/coordination/results/fixture-v2.pass.owner-summary.json`; successful per-case details were not supplied and are not reconstructed. The package gates allPassed on exactly 10 results and no failed cases.

History retained: original classifier build 5/10 pass; first v2 run `08584074408126043497852268406CU03` 9/10 pass (`artifacts/coordination/results/fixture-v2.first-run.owner-report.json`). Its Shrink RequestB returned the typed duplicate exception despite distinct supplied A/B keys; actual cause remains unconfirmed. A fresh run prefix passed without code/formula edits. This does not establish connector retry causation or generic unknown-write recovery.

179 local tests / 70 reference schedules previously passed; final artifact remains 321 actions / depth 6, no runtime changes after owner proof. #47 **Ready for review**, PR #75 ready; no owner rerun required. Earlier pending-run entries above are historical. Own contract review/merge remains; no production schema applied, all 70 schedules are not native-proven, genuine timeout/killed-run, production consumer/access and external notification delivery remain separate. #12 group/member schema is next after merge; #61 stays Ready for testing.


## #12 active schema inspection — 2026-11-08

PR #75 merged `be278a1cc7a72b862154ae8ffe201acdf998f019`; #47 closed/Done after accepted bounded contract/native proof. #12 is the sole active ticket. Existing #57 group/member snapshot is historical source evidence; current actual list IDs/field definitions/settings remain unverified.

Prepared `artifacts/group_schema/TandemGroupSchemaAudit.zip`, build `cb49aded-f121-410e-b7df-d9646be892dd`: **51 actions / depth 3**, below 500/8. Existing SharePoint connection; GET-only list inventory/identities, Group/Group Members fields/defaults/SchemaXml/column index/list validation and effective list permission masks. Known #66 participant/language/culture list identities rechecked. **No list item reads, writes, permission changes or working-flow/app modifications.** Actual unique-key constraints/lookup targets/defaults/schema compatibility are not approved from packaging or reference proof.

194 local tests pass, including 15 generated-inspector cases (normal collection, ambiguous/missing/unsafe targets, paging, missing arrays/identities/permissions, failed reads and package safeguards). Tenant import/run **NOT RUN**. collectionComplete means bounded metadata collected, not schema acceptance; schemaVerified remains false. No setup until actual report reviewed, any changes flagged and actual per-list capability verified. Existing rows preserved; exceptions route #48. Full operator handover/checkboxes inline in issue #12; draft PR is partial preparation, not whole-ticket Ready. #61 remains Ready for testing.


### #12 actual mapping and direct settings — 2026-11-08

Owner opted for direct list settings rather than another setup package. Initial audit `08584074383115048211345636667CU09` and manual-settings readback `08584074377818105096431306544CU07` match build `cb49aded-f121-410e-b7df-d9646be892dd`: collectionComplete=true/errors empty; Groups and Group Members each itemCount=0. Actual field/list IDs, types, choices, defaults, XML constraints and lookup targets recorded in `config/group_schema_mapping.json`; source reports in `artifacts/group_schema/results/`.

Confirmed group Title now required; WriteOwner optional nonunique Text/blank default; native integer/type-specific capacity formula/message saved. SharePoint removed optional column brackets; canonical formula comparison confirms the same expression. Existing focus links, SourceRequestId/MembershipKey unique+indexed, dates, membership Title optional, State Closed and SetupComplete No remain. Participant lookup displays ID; preserve its linkage and resolve approved display in consumers.

Group Members Group and Participant still report indexed=false. Indexed columns page requested; no index completion or full schema acceptance claimed. #12 remains In progress / PR #76 draft. No setup package generated, row writes, renames/deletion or runtime/privacy certification. 194 existing local tests previously passed; this is metadata/evidence only, not new executable changes.


### #12 schema mapping and five manual settings verified — 2026-11-08

Final audit build `cb49aded-f121-410e-b7df-d9646be892dd`, run `08584074372941101122136369836CU17`: collectionComplete=true, errors=[], both lists itemCount=0. Groups `4bf1b37f-edce-40c5-8fa0-36543a2d0cd6`; Group Members `db611ec3-7fa3-477a-878e-effbbb195cb8`. Group and Participant now each indexed=true; owner Indexed columns page lists separate Group / MembershipKey / Participant. Prior combined Group, Participant index was replaced with separate indexes.

All five direct-setting changes read back: group Title required; WriteOwner optional blank nonunique Text/255; native integer/type-specific capacity formula/message; membership Group and Participant indexes. Source/membership keys remain required unique/indexed, correct links/focus choices/types, JoinedAt required/LeftAt optional, membership Title unused optional, State default Closed and SetupComplete default No. Other mapped business field IDs/properties/XML semantics unchanged. Formula bracket normalization is equivalent. Actual mapping in `config/group_schema_mapping.json`; raw report `artifacts/group_schema/results/final-audit.owner-report.json`. Raw inspector schemaVerified=false remains intentionally fixed; local reviewed mapping/readback is now verified.

#12 Ready for review / PR #76 ready. No owner rerun or settings package needed; owner chose manual UI changes. 194 local tests previously passed; no executable change in final evidence recording. No row rejection/creation/migration, ordinary-user privacy or consuming-flow/history behavior claimed. No migration exceptions in these observed empty lists. Dynamic count/focus/identity/Ended/history guards remain respective Flow scope; #48 migration remains separate. Source/contract review and merge remain; next focused implementation is #7 Discovery after merge, #61 still Ready for testing. Earlier pending-index entries are historical.


## #7 Discovery owner-preview build — 2026-11-08

PR #76 merged `39ebc0cd48c428602a0434a12db0c99ac77a9de5`; #12 closed/Done. #7 is sole active ticket. Actual TandemDiscovery export inspected (source hash `7b4dc1e5df96769615088d897cf86030a2622a47dc7db56a414dbe75f41085a9`): Power Apps V2 number reference, SharePoint Invoker source with Raw authentication, Get item/Get items and candidatesjson/errormessage response. No ordinary-user access proof or owner-credential fallback inferred.

Built `artifacts/tandem_discovery/TandemDiscovery-v2.zip`, build `7c8589d0-fdea-4db8-9d44-46b7d8548acf`, **165 actions / depth 6** (limits 500/8). Preserves actual trigger/Invoker expression, resolves current SharePoint user and unique own profile before candidate reads, uses unchanged #9 normalization/pair/group source, approved typed person/member/group allowlist and fresh membership counts/sharer availability. Optional timezone, culture-only and deferred Any language policy preserved. No writes. Fixed reads are bounded; rendering <=50 people, total group focus/member work <=100 units and response <=250000 characters; any incomplete/over-bound read returns no partial success. Tenant synchronous latency/load not certified.

242 local tests pass, including 48 generated Discovery graph/packaging cases (own/tampered references, availability, blank zone/culture/Any, source/member commitment, group state/count/focus/history, structured-field rejection, read/page/count/work/response limits and Invoker preservation). Native import/run NOT RUN; mode OWNER_PREVIEW_PENDING_ACCESS_PROOF. #42 privacy/ordinary-user two-account proof deferred; do not publish a participant endpoint or change permissions. Candidate groups additionally require live Connection Requests.OperationComplete Boolean plus accepted/complete source/episodes; missing schema fails explicitly, no field creation in #7. Current empty group lists allow an owner people/empty-group smoke without claiming populated group proof. Exact contract and remaining gates in config/discovery_flow_contract.json and inline #7 handover. Existing raw export remains user-owned/untracked, no source replacement or production cutover.


### #7 owner smoke — Paused rejected, Active empty success (2026-11-08)

Build `7c8589d0-fdea-4db8-9d44-46b7d8548acf`. Owner run `08584074350262917105745395996CU25` returned PROFILE_UNAVAILABLE/success=false while own Participation status was Paused. Owner manually changed it to Active; fresh run `08584074348343616902680114159CU10` returned OK/success=true, peopleCount=0/groupCount=0, writes=0, ordinaryUserAccessVerified=false. Exact reports and scoped evidence saved under `artifacts/tandem_discovery/results/`. No flow/package change needed for this expected availability result.

This proves owner-context invocation/own-reference path, Paused rejection and Active empty-result completion, not populated compatibility/projection, another candidate's availability, native tampered-ID/two-account proof, imported Run-only selector, group commitment schema or worst-case native bounds/latency. No published app/cutover claimed. #7 remains In progress / PR #77 draft. 242 local tests previously passed; only evidence/config/docs changed.

Owner restated self-service access: avoid individual participant approvals/grants; use verified existing group-based app/flow access. The shown SharePoint connection consent is separate from run/data authorization. Invoker is preserved; no switch to an owner connection and no new permission changes. #42 owns the final protected-data/caller boundary; owner smoke does not resolve it. Remaining versioned tests stay unchecked in issue #7.


## #7 resumed implementation review — 2026-11-08

Owner deferred the audience-group/IT question and requested continued #7 work.
#39 assessment is queued Planned with draft #43 and successful owner metadata
run 08584074326403190336298551812CU15 retained; no access method or permission
cutover is approved. #7 is the sole active ticket during this review handoff.
The separate caller/backend modes observed in #39's helper do not change
TandemDiscovery v2's Invoker-only connection or prove ordinary-user access.

Existing build 7c8589d0-fdea-4db8-9d44-46b7d8548acf remains unchanged:
165 actions / depth 6, zero writes. Re-ran the full local suite: 242 passed.
Rechecked the existing ZIP checksum against review metadata; no rebuild/import
is needed. PR #77 is ready for implementation review only; #7 stays open and
does not acquire a whole-ticket Ready label from this partial PR.

The versioned checkbox handover remains inline in issue #7. Owner Paused/Active
empty-result tests are passed. Populated compatibility/projection, candidate
availability, native tampered reference, group commitment/slot/history and native
load/latency remain unexecuted. Request OperationComplete Boolean/live mapping
and operational groups remain explicit integration prerequisites, not permission
to fabricate production requests or groups. #42 access and ordinary-user rollout
remain blocked/deferred. No colleague test, production credential change, app
publication, source-flow replacement or additional import is requested now.

After implementation review/merge, retain #7's remaining tests and blocked cases
for later handover; the next build batch is #10 personal send, #62 inbox and #63
cancellation, with one focused production-flow ticket active at a time.


## Parallel development batch — 2026-11-08

Owner explicitly requested parallel flow development after PR #77 merged
`a19176b5e273de56cd09f395153f1fd78f593b6b`. #10/#62/#63 are active in
separate branches/PRs for this batch; this supersedes the one-active-ticket
scheduling rule for this batch only. #7 is queued with remaining tests retained;
#39 audience/IT follow-up stays queued, no privacy cutover authorized.

### #10 implementation and exact bindings

TandemSendRequest v2 build **381d4dd5-d5e0-4863-8ca9-f5d0ed7b8700**;
**125 actions / depth 5**, limits 500/8.
Original export SHA `823383a1b2941a38ebf80c3e2f0a288f72a9956d24db793767e2dda5eeff0ab8`; raw archive private/untracked.
Preserves original SenderParticipantId `number`, RecipientParticipantId `number_1`,
Invoker Raw connection, Boolean success and Text message outputs. Adds required
Text `IntentId` (`text`) and report/reference/status/code outputs. The app must
refresh/add the new flow binding and supply the retained intent; no transparent
old-button cutover is claimed. Create as new only. Maintained #9 source unchanged.

Send resolves caller before request/candidate reads; scoped server identity,
current compatibility/availability, idempotent request receipt, native unique
live connection key and legacy unsettled-pair guard. One POST with retries off;
exact immutable readback reconciles lost success. Unknown stays unknown; no
fake rollback, membership/group creation, profile update or auto-cancellation.
26 new emitted-graph/local cases pass; tenant import/write/race/ordinary-user
results NOT RUN. Schema prerequisites remain real integration work, not a PASS.

### One metadata preflight before this batch

TandemRequestSchemaPreflight build **88990545-0026-40b6-913b-fdfa3d623ef7**,
**18 actions / depth 3**. No inputs, item reads,
writes or permission/schema changes. Shares the expected request mapping with the
send gate. Local valid/missing-schema cases pass; native NOT RUN.

Do not enable required/unique fields or backfill existing requests blindly.
Old exported send omits the coordination keys; old cancel only changes Status.
Their incompatibility must be handled in the later coordinated cutover, not by
claiming the new flows are already integrated. Request Type/TargetGroup/custom
keys are proposed names until metadata is collected. #11/#17/#65 own their writers.
Exact operator/test checkboxes are inline in #10; #62/#63 own their handovers.
