# Tandem implementation plan
## Current batch delivery — #45 / #81

All twelve production flows have local implementations under the authorized parallel batch. Finish the coordinated disabled-import Solution, run the combined regression suite and actual-packaged-graph smoke/interoperability tests, publish one focused PR per flow and put checkbox handovers in the issues. Two disposable owner helpers (schema setup/audit and shared smoke) are additional to the twelve production flows.

Owner sequence after delivery: import once; map existing SharePoint connections; enable shared child and helpers; run the 45-case shared smoke; run Setup dry, explicit Apply and complete audit; repeat Apply to check writes skip. Only then enable/test business flows in order Send → MyRequests → Cancel → Discovery → participant validation → personal response → group join/response → MyGroups → Update/Leave. Disable the old participant validator before enabling its replacement. Use owner/synthetic data; preserve working versions for cutover. Return exact reports/build/run references and keep unexecuted cases unchecked.

The new batch is NOT tenant-certified. Keep runtime tickets open; app integration and ordinary-user access/privacy are pending, and #21 email is blocked by the failed sender mailbox probe. The historical checkpoints below are retained, not transferred to new versions.


The approved design is CURRENT_DESIGN.md. This plan reflects the owner's
annotations to Combined Requirements v0.2. GitHub tickets hold implementation
acceptance and status; planning completion does not imply deployment.

## Historical implementation checkpoints

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

#18 and #39â€“#42 stay open. The owner will arrange ordinary-colleague testing later.
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

## Tracking checkpoint â€” 2026-11-07

Reviewed the live backlog: 40 tickets, #1â€“#4 closed and 36 open. The approved
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

## Owner testing handover decision â€” 2026-11-08

Owner asks to merge #72 and mark #61 Ready for testing so other authorized testers
can cover the remaining cases. [the #61 issue description](https://github.com/maoy1/tandem-language-culture-app/issues/61) preserves passed/pending/blocked
variants and access/fixture gates. #61 stays open, not Done; no full-test pass
required from the owner before moving implementation forward. #9 own proof is passed and awaits review.

## #9 implementation â€” 2026-11-08

Reusable typed normalization/person/group source, 39 synthetic expected cases and
connector-free import proof built; 121 local tests pass, proof 45 actions/depth 4.
Owner defers Any language; no wildcard/focus support. Tenant proof import/run and
source review pending. Detailed current test handover/check boxes live in issue #9.
Next #47 shared conditional-write/recovery proof, then #12 group schema, followed
by #7 Discovery per ordered batch. #61 remains open Ready for testing.

## #9 proof acceptance â€” 2026-11-08

Matching-build/source-hash tenant proof run 08584074461495133197897516907CU19
reports 39 cases, allPassed true, no failures. Own bounded proof passed; #9 Ready
for review in #73, no owner rerun needed. Consumer integrations remain separate.
#61 remains Ready for testing. Next implementation after this review is #47.

## #47 implementation â€” 2026-11-08

PR #73 merged (6879bd90b1321a695143bd327e3aa3a52e9eece2); #9 closed/Done.
#47 now owns bounded shared coordination contract/reference proof and read-only
fixture-permission preflight. 152 local tests, 70 reference schedules; native
cross-item proof and new metadata/fixture prerequisites still pending. Preflight
5 actions/depth 1, no writes. #61 remains Ready for testing; #74 cleanup still open.

## #47 native fixture preparation â€” 2026-11-08

Read-only preflight owner-passed (run 08584074437966574454125674321CU01).
Native synthetic tagged fixture package built: 10 checks, 321 actions/depth 6;
165 local tests. Explicit default-false write gate, existing SharePoint connection,
no production/permission changes or deletes. Import/run pending; model/native/
unknown-outcome/consumer evidence remain distinguished. Inline handover in #47.


### #47 connector duplicate-error correction â€” v2

The owner supplied the first native report: 5/10 checks passed, allPassed=false. All five failed cases invoke the duplicate-response predicate. The Duplicate primary raw body confirms SharePoint error -2130575169 / Microsoft.SharePoint.SPDuplicateValuesFoundException wrapped by the existing SharePoint connector as HTTP 502. The original proof's 400/409-only classifier was too narrow. The five-case common cause is supported by local replay; a native v2 pass remains unverified.

The classifier now requires the exact native duplicate exception/code together with HTTP 400, 409 or 502. For the wrapped form, both exact entries must exist in innerError.errors. Generic 502, unrelated 400/409, incomplete error identifiers and other statuses fail. Existing schema/row/ETag/count/readback checks remain required. All five duplicate-dependent reports now include diagnostic codes/messages. No cookie or response headers are stored.

Supported package: artifacts/coordination/TandemCoordinationFixture-v2.zip, build b54d7cee-971d-4af3-924f-e81d5fefaec9, new tagged list Tandem47Fixture_b54d7cee971d4af3. Import as Create as new, display name TandemCoordinationFixture v2, existing SharePoint connection; Run fixture writes=Yes. Old fixture is retained; no deletion or production mutation. Expected Fixture report: 10 tests, allPassed=true, failedCases=[]. Return that report; expected rejected duplicate actions may still show red 502.

Validation: 179 local tests passed, including wrapped native duplicate simulation in both writer orders and generic/error-negative cases; 321 actions / depth 6 (limits 500/8). V2 NOT_IMPORTED_NOT_TESTED. #47 remains In progress / PR #75 draft pending native results. No genuine timeout/killed-run, production consumer or notification-delivery proof inferred.


### #47 native bounded proof passed â€” 2026-11-08

Matching v2 build `b54d7cee-971d-4af3-924f-e81d5fefaec9`, owner run `08584074402025984197329193901CU08`: testCount=10, allPassed=true, failedCases=[]. Permission gate passed; existing tagged fixture `Tandem47Fixture_b54d7cee971d4af3` / `abade32d-8b24-4b30-b2e0-668d10238acb` reused (fixtureCreated=false). Summary exactly as supplied: `artifacts/coordination/results/fixture-v2.pass.owner-summary.json`; successful per-case details were not supplied and are not reconstructed. The package gates allPassed on exactly 10 results and no failed cases.

History retained: original classifier build 5/10 pass; first v2 run `08584074408126043497852268406CU03` 9/10 pass (`artifacts/coordination/results/fixture-v2.first-run.owner-report.json`). Its Shrink RequestB returned the typed duplicate exception despite distinct supplied A/B keys; actual cause remains unconfirmed. A fresh run prefix passed without code/formula edits. This does not establish connector retry causation or generic unknown-write recovery.

179 local tests / 70 reference schedules previously passed; final artifact remains 321 actions / depth 6, no runtime changes after owner proof. #47 **Ready for review**, PR #75 ready; no owner rerun required. Earlier pending-run entries above are historical. Own contract review/merge remains; no production schema applied, all 70 schedules are not native-proven, genuine timeout/killed-run, production consumer/access and external notification delivery remain separate. #12 group/member schema is next after merge; #61 stays Ready for testing.


## #12 active schema inspection â€” 2026-11-08

PR #75 merged `be278a1cc7a72b862154ae8ffe201acdf998f019`; #47 closed/Done after accepted bounded contract/native proof. #12 is the sole active ticket. Existing #57 group/member snapshot is historical source evidence; current actual list IDs/field definitions/settings remain unverified.

Prepared `artifacts/group_schema/TandemGroupSchemaAudit.zip`, build `cb49aded-f121-410e-b7df-d9646be892dd`: **51 actions / depth 3**, below 500/8. Existing SharePoint connection; GET-only list inventory/identities, Group/Group Members fields/defaults/SchemaXml/column index/list validation and effective list permission masks. Known #66 participant/language/culture list identities rechecked. **No list item reads, writes, permission changes or working-flow/app modifications.** Actual unique-key constraints/lookup targets/defaults/schema compatibility are not approved from packaging or reference proof.

194 local tests pass, including 15 generated-inspector cases (normal collection, ambiguous/missing/unsafe targets, paging, missing arrays/identities/permissions, failed reads and package safeguards). Tenant import/run **NOT RUN**. collectionComplete means bounded metadata collected, not schema acceptance; schemaVerified remains false. No setup until actual report reviewed, any changes flagged and actual per-list capability verified. Existing rows preserved; exceptions route #48. Full operator handover/checkboxes inline in issue #12; draft PR is partial preparation, not whole-ticket Ready. #61 remains Ready for testing.


### #12 actual mapping and direct settings â€” 2026-11-08

Owner opted for direct list settings rather than another setup package. Initial audit `08584074383115048211345636667CU09` and manual-settings readback `08584074377818105096431306544CU07` match build `cb49aded-f121-410e-b7df-d9646be892dd`: collectionComplete=true/errors empty; Groups and Group Members each itemCount=0. Actual field/list IDs, types, choices, defaults, XML constraints and lookup targets recorded in `config/group_schema_mapping.json`; source reports in `artifacts/group_schema/results/`.

Confirmed group Title now required; WriteOwner optional nonunique Text/blank default; native integer/type-specific capacity formula/message saved. SharePoint removed optional column brackets; canonical formula comparison confirms the same expression. Existing focus links, SourceRequestId/MembershipKey unique+indexed, dates, membership Title optional, State Closed and SetupComplete No remain. Participant lookup displays ID; preserve its linkage and resolve approved display in consumers.

Group Members Group and Participant still report indexed=false. Indexed columns page requested; no index completion or full schema acceptance claimed. #12 remains In progress / PR #76 draft. No setup package generated, row writes, renames/deletion or runtime/privacy certification. 194 existing local tests previously passed; this is metadata/evidence only, not new executable changes.


### #12 schema mapping and five manual settings verified â€” 2026-11-08

Final audit build `cb49aded-f121-410e-b7df-d9646be892dd`, run `08584074372941101122136369836CU17`: collectionComplete=true, errors=[], both lists itemCount=0. Groups `4bf1b37f-edce-40c5-8fa0-36543a2d0cd6`; Group Members `db611ec3-7fa3-477a-878e-effbbb195cb8`. Group and Participant now each indexed=true; owner Indexed columns page lists separate Group / MembershipKey / Participant. Prior combined Group, Participant index was replaced with separate indexes.

All five direct-setting changes read back: group Title required; WriteOwner optional blank nonunique Text/255; native integer/type-specific capacity formula/message; membership Group and Participant indexes. Source/membership keys remain required unique/indexed, correct links/focus choices/types, JoinedAt required/LeftAt optional, membership Title unused optional, State default Closed and SetupComplete default No. Other mapped business field IDs/properties/XML semantics unchanged. Formula bracket normalization is equivalent. Actual mapping in `config/group_schema_mapping.json`; raw report `artifacts/group_schema/results/final-audit.owner-report.json`. Raw inspector schemaVerified=false remains intentionally fixed; local reviewed mapping/readback is now verified.

#12 Ready for review / PR #76 ready. No owner rerun or settings package needed; owner chose manual UI changes. 194 local tests previously passed; no executable change in final evidence recording. No row rejection/creation/migration, ordinary-user privacy or consuming-flow/history behavior claimed. No migration exceptions in these observed empty lists. Dynamic count/focus/identity/Ended/history guards remain respective Flow scope; #48 migration remains separate. Source/contract review and merge remain; next focused implementation is #7 Discovery after merge, #61 still Ready for testing. Earlier pending-index entries are historical.


## #7 Discovery owner-preview build â€” 2026-11-08

PR #76 merged `39ebc0cd48c428602a0434a12db0c99ac77a9de5`; #12 closed/Done. #7 is sole active ticket. Actual TandemDiscovery export inspected (source hash `7b4dc1e5df96769615088d897cf86030a2622a47dc7db56a414dbe75f41085a9`): Power Apps V2 number reference, SharePoint Invoker source with Raw authentication, Get item/Get items and candidatesjson/errormessage response. No ordinary-user access proof or owner-credential fallback inferred.

Built `artifacts/tandem_discovery/TandemDiscovery-v2.zip`, build `7c8589d0-fdea-4db8-9d44-46b7d8548acf`, **165 actions / depth 6** (limits 500/8). Preserves actual trigger/Invoker expression, resolves current SharePoint user and unique own profile before candidate reads, uses unchanged #9 normalization/pair/group source, approved typed person/member/group allowlist and fresh membership counts/sharer availability. Optional timezone, culture-only and deferred Any language policy preserved. No writes. Fixed reads are bounded; rendering <=50 people, total group focus/member work <=100 units and response <=250000 characters; any incomplete/over-bound read returns no partial success. Tenant synchronous latency/load not certified.

242 local tests pass, including 48 generated Discovery graph/packaging cases (own/tampered references, availability, blank zone/culture/Any, source/member commitment, group state/count/focus/history, structured-field rejection, read/page/count/work/response limits and Invoker preservation). Native import/run NOT RUN; mode OWNER_PREVIEW_PENDING_ACCESS_PROOF. #42 privacy/ordinary-user two-account proof deferred; do not publish a participant endpoint or change permissions. Candidate groups additionally require live Connection Requests.OperationComplete Boolean plus accepted/complete source/episodes; missing schema fails explicitly, no field creation in #7. Current empty group lists allow an owner people/empty-group smoke without claiming populated group proof. Exact contract and remaining gates in config/discovery_flow_contract.json and inline #7 handover. Existing raw export remains user-owned/untracked, no source replacement or production cutover.


### #7 owner smoke â€” Paused rejected, Active empty success (2026-11-08)

Build `7c8589d0-fdea-4db8-9d44-46b7d8548acf`. Owner run `08584074350262917105745395996CU25` returned PROFILE_UNAVAILABLE/success=false while own Participation status was Paused. Owner manually changed it to Active; fresh run `08584074348343616902680114159CU10` returned OK/success=true, peopleCount=0/groupCount=0, writes=0, ordinaryUserAccessVerified=false. Exact reports and scoped evidence saved under `artifacts/tandem_discovery/results/`. No flow/package change needed for this expected availability result.

This proves owner-context invocation/own-reference path, Paused rejection and Active empty-result completion, not populated compatibility/projection, another candidate's availability, native tampered-ID/two-account proof, imported Run-only selector, group commitment schema or worst-case native bounds/latency. No published app/cutover claimed. #7 remains In progress / PR #77 draft. 242 local tests previously passed; only evidence/config/docs changed.

Owner restated self-service access: avoid individual participant approvals/grants; use verified existing group-based app/flow access. The shown SharePoint connection consent is separate from run/data authorization. Invoker is preserved; no switch to an owner connection and no new permission changes. #42 owns the final protected-data/caller boundary; owner smoke does not resolve it. Remaining versioned tests stay unchecked in issue #7.


## #7 resumed implementation review â€” 2026-11-08

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

## #62 metadata comparison correction

Owner's MyRequests v4 smoke stopped at requests_field_SenderParticipantId_gate; preceding query returned body []. The returned Read_requests_fields response was HTTP200 with the correct required Number/Decimals=0 SenderParticipantId, unique=false/hidden=false/readOnly=false. Schema remains verified by #10 preflight run08584074285601068216673996565CU29. No list setting changes are requested.

Reader used bare XPath attribute-node results as an array/value. Replace Decimals and lookup List extraction with XPath string() values, matching the native-passed preflight; handle empty XML safely. Microsoft documents XPath returning nodes or values, with scalar string() extraction: https://learn.microsoft.com/en-us/azure/logic-apps/expression-functions-reference#xpath. Exact native XPath serialization was not returned; the local regression models node/array/scalar shapes and the exact returned Sender metadata. The prior test evaluator incorrectly always returned plain attribute-value arrays. It now exercises the representation difference.

TandemMyRequests-v5.zip build **51130189-433c-4808-b605-031e92bd439c**, 228 actions/depth4 (limits500/8), zero writes. 365 local tests pass, 123 reader cases. Original trigger/Invoker/auth/response/public row shape retained. V4 runtime failure is recorded, not a schema failure or runtime success; v5 native retest NOT RUN. Evidence artifacts/my_requests/results/v4-sender-gate.owner-evidence.json and tests/fixtures/my_requests_sender_metadata.json. Import v5 Create as new (display name TandemMyRequests v5), existing SharePoint Provided by run-only user; run own ParticipantId previously38 and return Respond to a Power App or flow Outputs. Expect OK, requestsjson [], errormessage empty for the empty list. Keep old published app/working flows unchanged; no repeat schema preflight required for this reader fix. Issue #62 stays open.

## #62 legacy null availability — 2026-11-09

Owner v5 smoke reached Data_profiles and failed because rows [0]/[1] have null ParticipationStatus/OpenToConnections. Permit null Status/ParticipationStatus/OpenToConnections in read-only profile input parsing; keep null values and explicit Active/Active/true availability. Do not default them to available or alter profile/membership rows. Missing required properties, invalid non-null types, identity/commit/authority guards remain strict.

Reader v6 build b108407d-4714-4d58-9852-0ffc3099c1e9: 228 actions/depth4, zero writes, 373 local tests /131 reader cases pass. Empty history with unrelated legacy nulls and Pending history cancel/decline preservation are exercised; malformed values still rejected. V5 metadata/caller stages progressed, but native completed history remains unverified; v6 retest NOT RUN. No list changes or preflight rerun needed. Owner confirms affected list rows are disposable test data and welcomes bounded reset/reseed when it simplifies future testing; this fix needs only the package replacement.


### #62 v6 owner empty-history smoke passed - 2026-11-09

Owner returned resultcode=OK, requestsjson=[], errormessage empty, mode OWNER_PREVIEW_PENDING_ACCESS_PROOF; run 08584074267842029485356386842CU16. This is the response to the v6 handover (expected build b108407d-4714-4d58-9852-0ffc3099c1e9); the response does not independently include a build ID. The earlier null-profile error no longer blocks this empty-history run. Supplied excerpt retained in artifacts/my_requests/results/v6-empty-history.owner-evidence.json. No code/package changes or repeat of this smoke needed. Populated personal/group/terminal history, native action integration, app binding and ordinary-user access remain pending; #62 stays open. 373 prior local tests unchanged; evidence-only update.


## Parallel development batch â€” 2026-11-08

Owner explicitly requested parallel flow development after PR #77 merged
`a19176b5e273de56cd09f395153f1fd78f593b6b`. #10/#62/#63 are active in
separate branches/PRs for this batch; this supersedes the one-active-ticket
scheduling rule for this batch only. #7 is queued with remaining tests retained;
#39 audience/IT follow-up stays queued, no privacy cutover authorized.

### #10 implementation and exact bindings

TandemSendRequest v2 build **50e14992-a69a-4001-93f4-1ac8ed57dfe2**;
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
29 new emitted-graph/local cases pass; tenant import/write/race/ordinary-user
results NOT RUN. Schema prerequisites remain real integration work, not a PASS.

### One metadata preflight before this batch

TandemRequestSchemaPreflight build **f7fd078d-740a-4d68-a8fe-31ca2abc9e54**,
**18 actions / depth 3**. No inputs, item reads,
writes or permission/schema changes. Shares the expected request mapping with the
send gate. Local valid/missing-schema cases pass; native NOT RUN.

Do not enable required/unique fields or backfill existing requests blindly.
Old exported send omits the coordination keys; old cancel only changes Status.
Their incompatibility must be handled in the later coordinated cutover, not by
claiming the new flows are already integrated. Request Type/TargetGroup/custom
keys are proposed names until metadata is collected. #11/#17/#65 own their writers.
Exact operator/test checkboxes are inline in #10; #62/#63 own their handovers.

### Parallel batch delivery â€” 2026-11-08

All three isolated implementations are built: Send #10 / PR #78 (125 actions/depth 5), My requests #62 / PR #80 (223/depth 4), Cancel #63 / PR #79 (138/depth 5). Shared read-only request schema preflight is 18/depth 3. All source Invoker bindings preserved, no embedded fallback; send alone adds a required retained intent UUID. Reader preserves original created timestamp/order and response row fields; cancel preserves its two input arguments. No writer cutover, schema setup or app publication performed.

Combined disposable-checkout suite: 455 tests passed plus one additional cross-generator send -> cancel -> history -> same-send replay check passed. Per-flow added cases: send/preflight 29, reader 104, cancel 80. Version/hash/source commit evidence is in artifacts/send_request/request_batch.validation.json. This is local generated-graph proof, not native acceptance.

Packages delivered together locally in artifacts/request_batch/TandemRequestFlows-20261108.zip (outer delivery archive, not directly importable); extract and import the inner schema preflight first. Each individual flow ZIP also remains under its own artifact folder. Three separate implementation PRs are ready for code review; tickets stay open. Checkbox handovers are inline in #10/#62/#63. Real request mapping/constraints/legacy rows and coordinated old-writer compatibility remain native integration blockers; inspect schema metadata before running replacement writers. Participant rollout is still access-gated.

## Request schema native observation and adapter correction â€” 2026-11-08

Run 08584074297422149453962972460CU27 (initial preflight f7fd078d-740a-4d68-a8fe-31ca2abc9e54) collected metadata, schemaVerified=false, zero item reads/writes. SenderParticipantId/RecipientParticipantId are existing required Number/Decimals=0, not Lookup fields. Status already matches. Owner reports list empty. Preserve existing field IDs/names/types; no migration needed for this observed empty list. New fields RequestType/TargetGroup/SendOperationKey/ConnectionKey/WinningOperationKey/OperationComplete remain absent, and RecipientParticipantId optionality is needed for Group requests. Source report and reviewed mapping under artifacts/send_request/results and config/request_schema_mapping.json.

Corrected Send v3 a9251019-b7a5-4170-8877-682bb71b8693 (125/depth5), preflight v2 dd0c91b6-13b4-41e0-affd-ebafeeb87404 (18/depth3), preserve numeric references and report ItemCount in metadata. 34 added send/preflight cases / 276 branch tests pass locally. Reader/cancel adapters follow in separate PRs. No tenant settings or rows changed. Owner setup and test-window/cutover impact are explicit in #10; required keys make the old Send incompatible until new binding. Updated whole schema/native actions/privacy remain unverified. Prior local batch evidence is historical, not new-build/native certification.

Corrected Number-adapter batch: 493 combined local tests passed (includes cross-flow contract check); Send v3/preflight v2, reader v4, cancel v3. Latest manifest artifacts/send_request/request_batch.validation.json. New bundle artifacts/request_batch/TandemRequestFlows-20261108-v2.zip. Owner empty-list setup remains pending; no native pass inferred.

## Request schema verification passed â€” 2026-11-08

Corrected preflight dd0c91b6-13b4-41e0-affd-ebafeeb87404 run **08584074285601068216673996565CU29**: collectionComplete=true/schemaVerified=true, ItemCount=0, itemRowsRead=0/writes=0. Numeric SenderParticipantId/RecipientParticipantId field IDs retained; recipient optional, six new field types/required/unique/index/default/lookup/choice metadata all match. Status unchanged. Verified mapping in config/request_schema_mapping.json; curated report/evidence in artifacts/send_request/results/schema-verified.*. No migration necessary.

Actual returned metadata also passes all three generated graphs with synthetic rows locally (send SAVED, cancel CANCELLED, reader OK). This verifies metadata compatibility only; native writer/history, edit permission, races, app binding and ordinary-user privacy remain untested. Schema gate is cleared for owner smoke; no new package or setup needed. First smoke: MyRequests-v4, Create as new, existing Invoker connection, own ParticipantId (previously 38), expect resultcode OK / requestsjson [] / errormessage empty. Return Respond to a Power App or flow Outputs. Do not use old Send with required keys; new writer/app/all-writer cutover remains pending.


### #10 owner send smoke results - 2026-11-09

Owner reports matched send SAVED/Pending and unmatched send passed rejection after new-intent guidance. Expected Send v3 build a9251019-b7a5-4170-8877-682bb71b8693; successful run references/full outputs not supplied. Prior provided INTENT_CONFLICT run 08584074252930158987892330133CU13 is retained as separate evidence and is not the unmatched-case pass. Source in artifacts/send_request/results/v3-send-smokes.owner-evidence.json. Recipient30 previously lacked participation/openness, was excluded before matching; owner changed test fixture. This is bounded owner smoke, not full REQ-001/AUTH-002 acceptance: exact stored parties/keys, same-intent replay/no duplicate, cancellation/history, races, UI and ordinary-user access remain pending. No executable/package change; #10 remains open. Next: retry successful sender/recipient/IntentId unchanged, expect REPLAY/same request ID and one row.
## Planned single shared validation workflow â€” #81

Owner direction is tracked by [#81 TandemValidateContext](https://github.com/maoy1/tandem-language-culture-app/issues/81). Existing #9 shares generator source, not a single deployed validation workflow. #81 owns one read-only shared workflow for schema checks, normalization and person/group compatibility, with versioned operation-specific inputs/results. Business flows should retain their operation logic and the minimal identity/authority and atomic live-state/ETag/unique-key guards needed for correct writes. Full schema audit and fresh live eligibility have different timing; a setup audit cannot replace operation-time data checks.

Implementation has not started. Allowed invocation, deployment/import mechanism, tenant entitlements, caller propagation and latency must be verified before depending on child flows/Solutions or removing repeated checks. No paid/external fallback is approved. Existing working packages are unchanged. #81 contains unchecked capability, schema, rule-parity, version-drift and consumer-proof acceptance; consumer cutovers remain in their own Flow branches/PRs. Ordinary-user proof remains deferred, not waived.

Mandatory change rule: every schema/mapping/catalogue/rule/normalization/availability/capacity/commit/public-contract change updates #81 ledger, shared implementation/contract, design/plan, affected consumer issues/packages and relevant regressions/evidence, or records a concrete no-impact assessment. Old native evidence is retained with its version and affected new behavior stays NOT RUN until retested. AGENTS.md makes this a required review item until automated drift validation exists. Preserve completed #9/#12/#66 history and unresolved #10 replay/Pending-row tests.


## #81 invocation proof preparation and ordered consumer plan

Owner authorized this order: **#81 invocation proof -> #10 Send -> #62 My requests -> #63 Cancel -> #7 Discovery -> #61 submission**, applying the shared design while finishing #11 Respond. #81 is the sole active ticket; #10/#62/#63 are queued Planned with their implementations and evidence retained. See [#81](https://github.com/maoy1/tandem-language-culture-app/issues/81) and config/shared_validation_invocation_proof.json for the reviewed source hashes, measured consumer action/depth inventory and proof contract.

Microsoft's documented child-flow route requires Solution-aware parent/child flows. Parent connections cannot be passed to children; a child using SharePoint needs its own embedded connection. Sources: https://learn.microsoft.com/en-us/power-automate/create-child-flows and https://learn.microsoft.com/en-us/power-automate/create-flow-solution. These are documented platform requirements, not tenant entitlement/caller proof. The current account proved legacy import only; no Solution/database/maker entitlement or child invocation is inferred. There is no connected tenant browser session.

First owner check: inspect More -> Solutions in the existing Tandem environment and return whether the list opens or the exact prerequisite prompt. No trial, database/environment creation, paid dependency or working-flow change is part of that check. The first native proof is planned as disposable connector-free parent/child token+correlation echo in one allowed Solution, followed by repeat/error cases and export of that native envelope. No new generated package or measured proof-flow definition exists yet; do not label a legacy import as child-invocation proof. Exact test/setup/expected evidence and cleanup are inline in #81.

Pure child invocation does not prove SharePoint caller propagation. Parent business flows retain authenticated caller binding and atomic live write guards. The future shared child data-read/connection boundary is not selected; no embedded owner fallback or production Run-only change is approved. Full-schema audit belongs to maintenance/deployment mode, fresh relevant data remains operation-specific. No schema/rule/business package changes or transferred test PASS. #10 failed replay/unexplained old Pending row remain unresolved. All #81 native tests NOT RUN while first capability evidence is pending.


### #81 first tenant prerequisite result

Owner confirms the Solutions list opens normally in the existing Tandem environment. This proves page availability only; Solution creation/editing rights, current entitlements, linked parent/child execution and packaging remain NOT RUN. The next bounded owner test uses only two disposable connector-free flows in one unmanaged test Solution: manual child echoes ProofToken and returns native ChildRunReference; manual parent calls it and displays both outputs. Run V1/V2 tokens, retain distinct native parent/child runs, then export the unmanaged test Solution as the real packaging reference. No production credential mode, data, app or list changes. Full exact steps and stop conditions are inline in #81.


## #81 native echo passed; shared pure validator built

Owner supplied V1 echo `TANDEM81_INVOCATION_V1`, child run `08584069538865401663915371009CU10`. Native unmanaged `Tandem81InvocationProof` version 1.0.0.1 export SHA256 `5560d8d80f78de67966160fe0276711494b76c0f176e19356d6cf32d2c4c191c` was inspected: one child response, one parent Workflow call, matching native workflowReferenceName, no connector references. Publisher Tandem/prefix tandem was owner-created. This establishes bounded connector-free invocation, not general SharePoint caller/credential propagation or ordinary-user rights. Parent run reference/second-token run not supplied. Curated evidence: artifacts/shared_validation/results/invocation.owner-evidence.json; original raw export remains local/untracked.

Built **TandemSharedValidation81-v1.zip**, new unmanaged Solution `TandemSharedValidation81`, build `31382f7e-a0df-44a2-9fde-223a11774e67`, SHA256 `cb0102c74fc669541cb30895dea065f45ce6e410204df742bd949f190bae02c0`. Fresh workflow IDs preserve the original proof and all business flows. **TandemValidateContext: 84 definitions/depth 7; TandemValidationSmoke: 8/depth 2**, limits 500/8, import disabled. This package is Solution import, not legacy My flows package import: native linked-flow packaging is now the tested reference, generated imports still NOT RUN. Readable child/smoke definitions and review accompany the ZIP.

Implementation decision: the shared child is a **pure connector-free evaluator**. SCHEMA compares operator/parent-supplied complete native metadata against 7-role/48-field versioned baseline; it does not collect or authenticate snapshots. Full/schemaRoles audit is explicit, not repeated wholesale on participant actions. NORMALIZE, PAIR, GROUP and PROFILE centralize reusable rules, permit null availability as ineligible, keep optional time zone/culture-only/one-way fit and Any-deferred matching. PROFILE still accepts a known Any selection as valid registration content; it never makes Any a matching wildcard. New wrapper adapts #9 rather than changing the closed proof/source.

Parents keep trusted SharePoint reads and caller resolution; an embedded owner child connection is not introduced. Input data/returned `success` never authorize actions: PAIR consumers must check `result.eligible`, GROUP consumers `result.compatible` plus operation conditions, PROFILE `result.valid`; schema results certify supplied metadata equality only. Keep parent authority/commit/replay/ETag/unique-key writes and approved app projection. Raw internal normalized account keys must not be passed to the app. Group member/focus-availability freshness and metadata completeness come from trusted adapters, not client declarations. Current business packages unchanged; #10 replay failure/earlier Pending origin remain unresolved.

**330 local tests pass, 88 new cases**, including execution of the packaged parent across all 44 child cases (39 prior compatibility fixtures, exact synthetic 38/32 no-overlap, null participation, version mismatch, schema baseline/mutated-required). Schema regression cases cover type/required/unique/index/default/lookup/choice/decimals/formula, missing/duplicate/incomplete metadata, and extra benign indexes. Expected rejection uses normal result branches, no intentional divide-by-zero. Fingerprints reject stale participant/group/request mapping baselines; hashes/builds remain explicit. Native generated Solution import/smoke and real consumer parity NOT RUN.

Next owner step: **Solutions -> Import solution** for this ZIP, enable only new child then smoke parent, manually run TandemValidationSmoke (no inputs/connections), return Smoke_report Outputs. Expect matching build, testCount=44, completedCount=44, allPassed=true and failedCases=[]. Exact prerequisites, checkbox cases, failure handling and cleanup are inline in #81. Keep #81 active/open; #10/#62/#63 queued Planned. No list/app/data/permission/working-flow changes. Once shared smoke passes, #10 migration starts with native caller/consumer parity before duplicated guards are removed; then #62/#63/#7/#61 and shared design in #11.


## #81 v1 native input defect and v2 quick-first correction

Owner v1 report build 31382f7e-a0df-44a2-9fde-223a11774e67, run 08584069519927027175534029560CU24: 44 completed/44 cases, allPassed=false, all 44 results empty. Generated Solution import and linked invocation worked; validation failed. Owner then supplied Request_text ValidationFailed and its input: serialized JSON document with string/maxLength schema. Parse JSON deserializes that document before schema validation, so the object fails a string schema. The earlier local interpreter validated the raw string instead and missed this native boundary. V1 regression now reproduces the actual failed Request_text and INVALID_INPUT. Reports retained in artifacts/shared_validation/results/v1-*; no rule or tenant/list-setting fault inferred.

V2 validates an object containing bounded string value, then deserializes that value once. Child response adds sanitized stage statuses; parent failedCases adds actualCode/expectedCode/diagnostics. This changes no matching/schema baseline semantics, public input, eligibility/authority contract or consumer flow. **TandemSharedValidation81-v2.zip**, Solution version 1.0.0.1, build c79b7b64-b3ce-4de3-aa74-0ed62bca1524, SHA256 608052804073ccd2874a1f9d83fbfeb62fd331fcbe86e7be5ed375139576717e. The update preserves ONLY existing generated #81 child/full-smoke IDs and adds TandemValidationQuickSmoke; original proof and all business flows are untouched. Never delete/recreate or change list data to address this parser defect.

Measured: shared child84/depth7, full parent8/depth2, quick parent8/depth2 (limits500/8). 335 local tests/93 new cases pass with native-style Parse JSON and update-ID regressions; full packaged 44-case graph and 3-case quick gate pass locally. Prior native v1 is FAIL; v2 native NOT RUN. Input handling guidance: https://learn.microsoft.com/en-us/azure/logic-apps/logic-apps-perform-data-operations.

Owner next: Solutions -> Import v2 as UPDATE of TandemSharedValidation81, verify/enable child and new QuickSmoke, then run QuickSmoke only (no inputs). Expect suite QUICK, current build, testCount=3/completedCount=3/allPassed=true/failedCases=[]. Cases: compatible pair, exact 38/32 no-overlap and version rejection. Return Smoke_report Outputs; on failure actualCode and diagnostics are retained. Do not rerun the long 44-case full smoke until this short gate passes. No new connections/read/write fixtures. #81 remains active/open, real consumer/SharePoint boundary and batch business-flow delivery pending; no consumer readiness/acceptance upgraded.


### #81 v2 native quick gate PASS

Owner report matches v2 build c79b7b64-b3ce-4de3-aa74-0ed62bca1524, suite QUICK, run 08584069506351729738499173108cU14: 3 expected/3 completed, allPassed=true, failedCases=[], syntheticOnly=true, connectors/reads/writes=0. Curated body artifacts/shared_validation/results/v2-quick.owner-report.json. Confirms imported update/quick helper and corrected input path for compatible pair, exact no-overlap 38/32 and version rejection. Prior v1 44/44 failure is retained, not rewritten as passed.

The full v2 44-case corpus (including GROUP/schema) and production-parent SharePoint/caller/consumer parity remain NOT RUN. No elapsed-time measurement, live-schema audit, privacy proof or business-flow readiness inferred. Next: run the already imported TandemValidationSmoke full parent once, no new import/inputs/data edits, expect same build/suite FULL/testCount44/completedCount44/allPassed true/no failed cases. Record exact report/error; keep #81 open/In progress. 335 previous local tests unchanged; this is evidence-only.


### #81 v2 native FULL suite PASS

Owner report matches v2 build c79b7b64-b3ce-4de3-aa74-0ed62bca1524, suite FULL, run 08584069504668815720383921608CU09: testCount=44/completedCount=44, allPassed=true, failedCases=[], syntheticOnly=true, connectors/reads/writes=0. Exact curated report artifacts/shared_validation/results/v2-full.owner-report.json. Together with prior quick3 PASS, the imported shared evaluator now passes the complete packaged synthetic corpus, including GROUP/schema snapshots and expected rejection cases. V1 failure history is retained. No repeat full run requested.

This is supplied-fixture/runtime validation, not live SharePoint schema provenance, ordinary-user access, business parent Invoker mapping, current domain reads or atomic writer integration. No latency measurement supplied. #81 remains open/In progress pending relevant native parent/consumer proof; 335 prior local tests unchanged, evidence-only update. The next packaging prerequisite is a disposable Solution parent using the existing SharePoint connection with Run-only Provided by run-only user, GET currentuser Id, followed by the real shared child. No schema/data/permissions/working flows changed. Backend core batch remains 11 business flows plus validator; 2,000-character introduction planning is #17 and actual new schema/receipt setup must update #81 when mapped.


### #81 owner Solution SharePoint + shared-child probe passed; export pending

Owner supplied SharePoint GET body d.Id=16 and shared-child resultcode OK/success true, matching v2 build c79b7b64-b3ce-4de3-aa74-0ed62bca1524, child run 08584069483776257593504328231CU07. Empty normalization result and authorizesAction=false match the requested probe. Curated supplied values in artifacts/shared_validation/results/sharepoint-caller-probe.owner-evidence.json; parent run ID/name are not independently included in the supplied bodies.

This is an owner-context execution result for the requested Tandem81CallerProbe, not proof of Run-only Invoker source, connection-reference export shape, ordinary-user context separation, business authorization or caller-bound write parity. Parent performed a metadata GET; child's zero-I/O counters describe only the pure child. No business rows/schema/permissions changed. Next: export TandemSharedValidation81 UNMANAGED with the new probe/SharePoint reference and return ZIP path for native packaging inspection; no repeat probe/full smoke requested. #81 remains open, 335 prior local tests unchanged (evidence-only).


### #81 native Invoker envelope inspected and guarded builder adapter added

Inspected owner export TandemSharedValidation81_1_0_0_2.zip, SHA256 ce19af2e37e7de4a9317ec4c63e8d5777beaf23a57120c99b4e38d38ce4946d4, unmanaged Solution version 1.0.0.2. Four workflow roots match components. The shared child still matches the delivered native-passed c79b7b64-b3ce-4de3-aa74-0ed62bca1524 v2 action graph after ignoring designer metadata; its 84/depth7 structure is unchanged. CallerProbe has 2 actions/depth1: one GET of currentuser Id and one call to that child. Its SharePoint runtimeSource is explicitly invoker, logical reference cre46_sharepointonline_a22363a216 resolves to the standard SharePoint API component, and Raw authentication is the native per-trigger X-MS-APIM-Tokens/$ConnectionKey expression. No new connector, embedded fallback or owner token substituted.

Curated native configuration receipt: artifacts/shared_validation/results/native-sharepoint-solution.analysis.json. Original native export stays local/untracked. scripts/power_automate/solution_source.py now validates this source, linkage, site/read scope and interactive connection shape, then prepares caller-preserving parent documents. It rejects a changed connector/auth/site, wrong child/build, unresolved components, automatic-event trigger or unverified runtime. This adapter is local packaging code only; it does not itself create/deploy a business flow or certify it. Automated/event #61 owner binding must be preserved/reviewed in its own adapter, not converted through this manual Invoker seed.

**357 local tests pass (115 #81 cases, including 22 new native-source guard tests)**. No runtime definition/ZIP or matching/schema semantics changed; native QUICK3/FULL44 and owner Id16 execution evidence remain intact. This clears inspection of the manual Solution Invoker template. Power Apps Solution consumer invocation, actual data/authority/write parity, new schema/receipt/Introduction setup and ordinary-user access remain pending. No more owner connection-probe run or raw source export requested for this inspected seed. Batch implementation will use this observed envelope with receiving-ticket tests/guards; no all-business-flow delivery or release-readiness claim.
## #17 optional group-join introduction length accepted

Owner chose **2,000 characters** for the optional plain-text group-join introduction, enforced in both app and flow. Empty/omitted remains allowed; 2,001 characters must be rejected before a request write, preserving user edits in the app. This does not add a personal-request introduction requirement or select a notification channel.

Technical field proposal: optional plain-text Note column Introduction on Connection Requests, rich text/append disabled; actual column/settings are NOT verified or applied. SharePoint field mapping/setup and the flow/API/app mapping remain #17 work. All schema changes must update #81 baseline/audit/contract and affected consumers (#62/#65/#67), with existing native evidence retained by version. #81 has no Introduction persistence/parser today, so this planning decision does not change its current five-mode rule engine/package. Add actual schema coverage when the field is introduced.

Contract evidence only: acceptance cases empty/omitted, 2,000 accepted and 2,001 rejected in both app/server are NOT RUN. #17 remains Planned, not implemented/Ready. No flow, list, data, permission or existing app changed. This clears the remaining explicit product choice for core group-join implementation; receipt-schema and Solution SharePoint/caller prerequisites still need technical verification.

## #61 parallel-batch shared-consumer handoff — 2026-11-14

[#61](https://github.com/maoy1/tandem-language-culture-app/issues/61) only, under
[#45](https://github.com/maoy1/tandem-language-culture-app/issues/45). Owner explicitly
authorizes parallel work; other tickets and shared-child implementation are outside
this branch. Current source is origin/main 7eba0ba0e5739477d4259474c2cb8fb8b3e3ee94.

1. Local candidate: `scripts/power_automate/participant_submission_shared.py`,
   build issue-61-shared-consumer-v1, child contract1/rules1 PROFILE; emitted parent
   29 definitions/depth3. Execute actual emitted parent + unchanged v2 child in
   tests/test_participant_submission_shared.py. Preserve deployed v2 and evidence.
2. Core packaging consumes the separate `.solution-source.json`. Its automated
   adapter preserves legacy `$authentication` and resolves existing SharePoint
   logical component with `runtimeSource: embedded`; never call the interactive
   Invoker adapter. `_connectionEvidence=AUTOMATED_SOURCE_VERIFIED` attests the
   inspected legacy Embedded source only. Exact original owner reference and
   hashes are retained in the adjacent review; automatic Solution binding NOT RUN.
3. Do not deploy based on that marker. Final Solution assembly and existing owner
   connection resolution must be inspected, imported disabled, then tested under
   #61's controlled single-validator cutover. If binding differs/prompts a new
   permission/licence/connection mode, stop dependent activation. Standalone legacy
   ZIP is withheld pending valid final Solution parent assembly. No fabricated ZIP.
4. Run native parity/no-op/invalid/stale-write cases using the appended #61 guide.
   Keep old v2 results, remaining acceptance and ordinary-access deferral truthful;
   no shared-child or other consumer runtime is upgraded by this local change.

#81 drift ledger is nested in config/participant_submission_contract.json:
no shared schema, versions, semantic rules or baseline changes; native shared
QUICK3/FULL44 PASS retained; new consumer parity/binding NOT RUN. No issue edits
or pushes authorized. No additional deployed service, connector or entitlement.


## #61 shared consumer native no-op PASS — 2026-11-14

Owner report item38: parent08584069192652841427464544862CU18, consumerissue-61-shared-consumer-v1; shared PROFILE returns OK on batchbd66271f-090e-4f5c-a890-8cb5b61173cc, child08584069192622793814733430516CU11. valid=true, StatusActive, statusChanged=false, NO_CHANGE. Evidence artifacts/participant_submission/results/shared-v1-no-change.owner-report.json. Record bounded automatic event/read/child/no-op PASS; Status-write/readback/follow-up, broader acceptance and old-validator-off confirmation are not inferred. No source/package/semantic change; no local tests rerun for recording native evidence.

Report sharedChildId still contains the legacy template annotation e9aa88eb...; exact1.0.0.1 packaged Call_profile_child target is f1f91974-4124-557e-b7fe-d51e9972681d, and actual shared build/run are captured above. Track the annotation rebind in #81 for the next packaging revision; this does not justify reimporting during the functional test. Next bounded test: with oldv2off and valid selections intact, set only Participants item38 validation Status to Needs review. Expect STATUS_UPDATED/Active/statusChanged=true then autonomous NO_CHANGE/statusChanged=false without another user edit. Return both reports; identity/selections/participation/openness must remain preserved.

## #7 shared-consumer batch component — 2026-11-14

[#7 TandemDiscovery](https://github.com/maoy1/tandem-language-culture-app/issues/7):
local readable parent built on a separate branch for the authorized parallel
12-flow batch. Next integration step is final Solution assembly with the observed
Invoker envelope and existing #81 child; no legacy linked-flow import is implied.
164 actions/depth6, no writes, shared versions1/1 unchanged. See
[ISSUE_7_SHARED_CONSUMER.md](ISSUE_7_SHARED_CONSUMER.md) for versioned fixtures,
checks, #81 drift/no-impact ledger and exact connection/IO contract. Native
consumer parity/projection/load NOT RUN; ordinary access deferred/#42-blocked.
Preserve prior native/closed evidence and working flow/app. No ticket/label edit,
readiness upgrade or deployment is performed by this local component change.


## #63 shared consumer v4 — 2026-11-14

[#63 TandemCancelRequest](https://github.com/maoy1/tandem-language-culture-app/issues/63) implements the authorized parallel batch consumer refactor from cancel v3/PR #79 plus origin/main #81. Build d70520a1-e760-45ee-ab57-f211a490cbb2, ZIP SHA256 e5818c0ac14d27ceeb7f87297993fc191ef1e5102c804c3377ebdcf7b4f4fe68; 71 actions/depth5 (was138/5), one CAS/retries none. No per-click schema audit or unused NORMALIZE/compatibility call. #81 schema verification is explicit deployment/maintenance; caller/sender authority, typed coherent rows, exact Pending ETag CAS, deterministic winner/history, same cancel replay and unknown outcome readback remain. No shared child/common changes or shared rule/schema/IO impact; draft #81 ledger and exact owner/synthetic handover in docs/ISSUE_63_SHARED_CONSUMER.md. Parent assembles Solution; legacy ZIP is only owner-preview packaging. Native consumer/Power Apps/write tests NOT RUN; ordinary access deferred/not verified. v3 and #81 native history retained; no issue closure/readiness/push/deployment or GitHub edits.

## #62 v7 shared NORMALIZE reader — local build, native parent NOT RUN

[#62 TandemMyRequests](https://github.com/maoy1/tandem-language-culture-app/issues/62), PR [#80](https://github.com/maoy1/tandem-language-culture-app/pull/80), under overview [#45](https://github.com/maoy1/tandem-language-culture-app/issues/45). Owner explicitly authorizes parallel 12-flow batch for this work; no lifecycle/issue edits made. Merged origin/main #81 baseline, retaining #62 v6 owner empty-history evidence and main's subsequent child/Invoker proof history.

Readable parent `artifacts/my_requests/TandemMyRequests-v7.definition.json`, build `72df3b79-e724-412f-bfb9-e48a1a6011c1`, SHA256 `f18ee0b70837ae3c809d902e83912ca364d5d98d5a6e5999928051ad30d0526a`: **128 actions / depth 4**, six SharePoint GET definitions, zero writes (limits 500/8). New parent is NOT imported/tested. No legacy ZIP is delivered for v7: the external Workflow dependency requires enclosing Solution packaging by parent integration. Existing v6 ZIP/evidence remain historical; do not deploy it as this migration.

Parent keeps authenticated Invoker currentuser -> unique own participant -> exact positive number reference binding; bounded complete reads, typed integer reference canonicalization, request intent/history/commit keys, operational membership episodes, provisional/Left/Ended restrictions and audience-before-public-projection remain #62-owned. Per-click metadata/list-field audit removed; explicit setup/deployment/maintenance audit belongs to [#81](https://github.com/maoy1/tandem-language-culture-app/issues/81). This change makes no schema, permission, connection, app or tenant configuration changes.

NORMALIZE contract/rules 1/1 targets child `e9aa88eb-a666-4df1-b088-176be7bcd00d` and native-passed build `c79b7b64-b3ce-4de3-aa74-0ed62bca1524`. Reader supplies only availability fields and profile ID correlation tokens `participant:<Id>` with omitted role/timezone fields and explicit empty catalogues/Any null. These tokens are not authenticated account identities; they never authorize an actor or reach the app. No compatibility or identity-normalization claim follows from this narrow projection. Child report/version/build/zero I/O/non-authority, typed results and exact unique ID coverage are checked; any child failure/malformed/incomplete response clears all rows with SHARED_VALIDATION_FAILED. Current availability hints use normalized output; action writers must recheck authority/compatibility/freshness/commit.

#81 drift/no-impact assessment: no shared child/common source, shared contract, catalogue semantics or mapping/baseline changes; only #62 consumer packaging/projection changes. Shared implementation SHA256 `4d16f3291116cf5c297c28d22403d8a56edf6e9a3d9c220f6ce8034d7564428f`. Existing QUICK3/FULL44 native PASS remains version-bound; #62 new native parent parity is NOT RUN. No #81 issue/ledger edit under explicit no-issue-edit scope; this append is the consumer ledger handoff for parent integration. Introduction schema is still unapplied/unverified: default artifact does not select/expose it. After #17 verifies actual optional plain-text Introduction mapping/settings, explicit `--introduction-verified` rebuild supports null/absent/empty/2000 characters, rejects 2001, exposes only group-request text after the existing request audience filter. This grants no broader profile, discovery or raw-list visibility. Native Introduction acceptance remains BLOCKED on setup.

#62 v7 local verification: **463 full-suite PASS / 106 reader cases**, 80.82s; 128 actions/depth4, six GET definitions/one real-child call/zero writes. Delivered graph, artifact/generator/shared-source hashes and shared-source/contract equality to origin/main checked. Native new-parent tests NOT RUN; versioned evidence in `artifacts/my_requests/v7.validation.json`.


## #62 v7 follow-up — target Introduction option, responder authority and exact batch pin

[#62 TandemMyRequests](https://github.com/maoy1/tandem-language-culture-app/issues/62), [PR80](https://github.com/maoy1/tandem-language-culture-app/pull/80). Follow-up stays in codex/issue-62-package after independent #64 commit1070eb3; no #64 source/branch edits or shared/common edits. Parent integration remains responsible for the foundation merge and enclosing Solution assembly.

`build_actions`, `build_parent` and `build_package` now accept keyword `include_introduction=True` for PROSPECTIVE target compilation, without a tenant verification claim. Legacy `introduction_verified=True` remains an equivalent compatibility alias; review always records introductionVerified=false / actual setup NOT_APPLIED_NOT_VERIFIED. Default artifact omits the field; separate `TandemMyRequests-v7-introduction-target.definition.json` includes optional plain-text Introduction with 2000-character checks and unchanged audience-before-projection. Building target before setup is allowed; tenant use is blocked until actual field/settings/readback succeed. Owner planning context: root #81 setup114 actions/depth6, audits all8roles via shared child/new prospective59-field baseline. This is not tenant PASS evidence and adds no schema/receipt dependency to these NORMALIZE-only reader calls.

Runtime pin is configurable via keyword `expected_shared_build_id` (CLI --expected-shared-build-id), defaulting to canonical SHARED packageBuildId. Parent passes ONLY the explicit canonical batch-manifest engine build. The emitted report check stays EXACT, with existing child immutable ID, contract/rules1/1, success, non-authority, zero-I/O and complete-output checks. Native connection seed proof build is checked/recorded separately; a newer expected engine pin does not certify engine semantics or native parity. Default/target examples here retain expected `c79b7b64-b3ce-4de3-aa74-0ed62bca1524`; parent must rebind/regenerate against actual new batch engine, never run an old c79 pin on it. Exact shared implementation hash drift gate remains unchanged: reported integration old4d16/new7365 mismatch requires foundation merge and artifact regeneration by parent, not ignored/loosened checks.

Current operational Active group-member responder hints no longer require that member's personal Active participation/openness/validation availability. Paused/Inactive/null/non-open members keep group response authority under the existing committed-episode guards. New Group requester availability remains separate; current group capacity/open/busy hints remain. Accepting writers/shared rules still recheck requester eligibility, focus-sharer availability, compatibility/freshness and commit/CAS; this read hint is not approval. Personal-recipient new-connection availability behavior is retained.

Default v7 build `2c9d2814-dcfb-4951-8abe-955b9067863b`, SHA256 `9edaa4b8f3561d36c2f5e83a995e6d4db19dea58fcaab5fc04908dd9c18a99e5`; Introduction target build `24da4c0a-fd53-4143-8bfc-3d94b15e5913`, SHA256 `96c0f5c25e81c140f2b0e0c0965bcbf5880a5c9445bb1935e7b78dc75f5086a8`. Both128 actions/depth4/six GETs/one Workflow/zero writes; both native NOT_IMPORTED_NOT_TESTED and actual schema NOT verified. No deployed flow, app, permission, source schema, #81 engine/package/contract or ticket state changed; no issue edits/push. Shared drift/no-impact ledger: consumer option/hints only; parent source-hash/build-pin reconciliation remains explicit. Prior v7 artifacts/results retained in b9d6516 history, prior v6 owner PASS unchanged.

#62 follow-up final local evidence: **485 full-suite PASS / 128 reader cases**, 52.50s. Default and Introduction-target128/depth4, six GETs/one actual emitted child/zero writes; strict hash and exact configurable build checks PASS on this branch's unchanged main-based shared source. New foundation old4d16/new7365 drift remains a parent-owned merge/regeneration prerequisite, not waived. Validation records prior v7 history separately; native/schema/privacy still NOT RUN.

## #10 shared PAIR consumer implementation — 2026-11-14

[#10 TandemSendRequest](https://github.com/maoy1/tandem-language-culture-app/issues/10), [PR #78](https://github.com/maoy1/tandem-language-culture-app/pull/78): owner explicitly authorizes the parallel 12-flow batch; this branch owns only Send. Integrated merged #81 from origin/main, retaining both prior evidence histories and exact conflicting untracked exports in temp. V4 build `67071ada-681d-4522-ad5f-5d9c97235a7d` delegates fresh normalization/compatibility to native Workflow child `e9aa88eb-a666-4df1-b088-176be7bcd00d`, contract1/rules1 PAIR, pinned existing shared build c79b7b64-b3ce-4de3-aa74-0ed62bca1524. Authenticated own-profile, immutable replay before availability, fresh pair/catalogue reads, narrow request-only metadata checks, current live-key/unsettled checks and one POST/unique/readback-unknown protocol remain. No per-click full schema audit. Null availability stays ineligible; deterministic object-schema failure replaces unsafe div gates in this parent.

Parent 113 action definitions/depth4; shared child unchanged84/depth7; both within500/8. Readable native-envelope parent, review-only legacy ZIP, mappings, validation and complete future native test instructions are in artifacts/send_request/HANDOVER.shared-v4.md and shared-v4.validation.json. Final deployment requires parent-batch Solution assembly; legacy Workflow linkage is not natively proven. #10 native v4 caller/write/replay/race/privacy remains NOT RUN; historical v3/#81 evidence remains scoped to its versions.

#81 drift no-impact assessment: no shared schema, rules, normalization semantics, version/build or other consumer files changed. This is the #10 consumer migration only; build/hashes/regressions are retained in Send evidence. Parent owns #81/#10 ledger/issue updates, Solution packaging and integration. No push/issue modification from this branch; no schema/settings/permission changes, no Ready/Done claim. See the handover for exact fixture/account/actions/expected results/failure interpretation/cleanup/evidence.

Final local verification for #10 v4: **413 tests passed**, including **56 send cases**; exact delivered native parent + delivered shared-child graph exercised locally. ZIP/definition/hash checks PASS; parent113/depth4 and child84/depth7 PASS; seven shared files unchanged from merged origin/main and request mapping unchanged from prior #10 baseline. Native v4 integration remains NOT RUN.


#10 final batch refinement: removed all request-field metadata queries and Schema_* gates from ordinary Send. One-time #81 setup/audit owns schema; historical #10 metadata preflight remains reproducible with an explicit generation-only flag. Current identity, typed intent, compatibility, native unique key arbitration and exact readback remain. 57 focused tests pass; native new parent/replay/race tests remain NOT RUN.

## #81 coordinated core batch foundation — 2026-11-14

Owner explicitly authorized parallel implementation of one shared validator and eleven singly owned business flows, one coordinated Solution import, separate ticket branches/PRs and inline per-flow checklists. The old single-active-ticket sequence is superseded for this authorized batch. Core flow inventory and stable fresh component IDs are owned by config/core_batch_contract.json / scripts/power_automate/core_solution.py. No silent working-flow replacement; all generated components import disabled and the old/new event validators must never both be enabled during cutover. Full app screen implementation and ordinary-user access tests remain separate, not implied by backend import.

Production target schema is config/batch_schema_contract.json. Optional Introduction is a plain-text Note, 2,000 characters enforced by app/flow. New TandemOperationReceipts has unique required OperationKey, required plain-text IntentJson, optional ResultJson/SealedAttempts, completion/uncertain/retry/domain-effect flags, AttemptToken and Stage. No extra lock service, timer, lease takeover or background repair runtime. Setup is one bounded owner maintenance flow, dry by default; it checks ManageLists before additive writes, refuses an unrelated same-title receipt list, does not convert mismatches or add missing required receipt fields to a nonempty table, then rereads metadata. No business row writes, deletes or permission changes. Native setup/production mapping remains NOT RUN; returned receipt GUID must be retained in tenant evidence.

The shared schema evaluator now accepts a baseline-defined role count and plain-text Note checks, allowing the prospective eight-role/59-field batch baseline (seven native-passed roles plus receipts and request Introduction). Existing production list identities remain GUID-pinned; the new unique receipt list title is used until native GUID evidence exists. The native-passed old baseline and v2 ZIP remain unchanged historical evidence. Shared rule/availability/normalization semantics are unchanged. The new generator and its prospective schema require a fresh batch build/hash and native regression; prior QUICK3/FULL44 are not relabelled as new runtime PASS. Every consuming ticket/package carries this impact/remaining test gate.

#49 owner selected in-app plus email, sender Tandemteam@elsevier.com, and approved new personal requests to recipient, group-join requests to all active target-group members, accepted/declined to sender, cancellations to recipient or active target-group members. New Outlook connection was created, but the native shared-mailbox test failed REST capability; exact mailbox/connection compatibility remains unverified. No email connector, new licence, mailbox grant or delivery workaround is added to this twelve-flow batch. #21 email remains blocked; in-app request/group views remain within core work.


### #81 Discovery invocation bound

Added backward-compatible PAIRS mode: one actor plus the supplied profile set returns eligible pair projections using the existing PAIR expression source. It avoids a separate native child invocation per candidate (up to 500 profiles). No matching/availability/identity rule changed; result remains internal and never grants authority. Discovery consumes this additive mode; other consumers retain their existing modes. New batch engine/native evidence remains NOT RUN; old v2 evidence is not reused. Three bulk/single parity, missing actor/null availability and structure-limit tests pass. Shared foundation before this addition passed 378 full local tests.


#7 batch integration update: candidate matching now calls shared PAIRS once for the entire bounded profile set, preserving the existing PAIR rules; no child call inside Each_person. NORMALIZE and GROUP remain shared. This component requires the new #81 batch engine with PAIRS and is not executable against the old native-passed v2 child alone. Final Solution assembly rewires to fresh batch child ID; historical native evidence retained, new native performance/consumer tests NOT RUN. No matching semantics changed.

### #81 assembly and test handover refinement

The import remains one coordinated Solution: twelve production flows plus two disposable owner maintenance helpers (schema setup/audit and 45-case connector-free shared smoke). Existing v2 child and working business IDs are not overwritten. Assembly rebinds the inspected shared child ID and exact old build literal to the new batch child/build, preserving all consumer build identities and checks. Native document envelopes are copied from the inspected source for every component; automated owner binding remains separately marked legacy-inspected/Solution-native-NOT RUN. A local SharePoint transport fixture models only current reads, ETags and uniqueness for interoperability of actual generated graphs; no domain-rule implementation or hosted runtime is added. All final native tests remain NOT RUN.


## #81 final coordinated batch artifact — 2026-11-14

TandemCoreBatch version **1.0.0.0**, shared build **4db7f9fa-6d67-48b0-a7a6-33638d7ff4a1**, ZIP SHA256 **bd854ae74a5e0291d985aa5fadc3fb3088c8135e7c5e337148acb02e89d4c959**. Delivery: `artifacts/core_batch/TandemCoreBatch-v1.zip`; readable exact packaged definitions and IO/connection schema are alongside it. Twelve production flows plus two disposable owner helpers; all import disabled. The native-derived bundle preserves interactive Invoker and the separately inspected legacy automatic Embedded binding; new automatic Solution execution remains NOT RUN.

Measured production definitions/depth: shared93/7; Discovery167/6; participant validation29/3; Send99/4; MyRequests128/4; Cancel71/5; personal Respond296/7; group Send147/5; group Respond393/5; MyGroups185/5; Update250/5; Leave231/4. Helpers Setup115/6 and Smoke8/2. Every flow is below500 actions/depth8; maximum393/7. Exact fresh workflow IDs and hashes are in the review JSON. Shared contract/rules remain1; prospective schema baseline2 covers8roles/59fields. All eleven consumer tickets are impacted by this linked deployment and retain their native acceptance checklists.

Local combined regressions and actual-packaged-graph tests are recorded in TEST_RUNS and `artifacts/core_batch/validation.json`; native import/setup/audit/consumer/app/access results remain NOT RUN. Existing native QUICK3/FULL44/SharePoint owner-probe results remain tied to their old c79 build. No tenant state, working app/flow, permission or mailbox was changed by building this artifact.


## #81 native schema-input failure and compact collector repair — 2026-11-14

Owner #45 Apply run08584069362059040197682124425CU28 on batch4db7f9fa collected metadata but returned schemaVerified=false/result={}, with no local setup differences or business row/deletion/permission writes. Receipt list ID864dfe53-b67c-4504-9d48-ad4356b813d8/title was observed, not a full schema PASS. Child08584069361400134595726594162CU01 was invoked with the correct build but failed Request_text as INVALID_INPUT before Envelope/schema evaluation. Raw metadata-size overflow reproduces this signature locally; exact native Request_text detail remains requested. Preserve the failed native evidence in artifacts/core_batch/results/v1-schema-apply.owner-report.json.

Solution1.0.0.1 repairs the setup collector: source-read completeness and paging remain checked, but only the59 baseline contract fields and nine evaluator properties are forwarded. Hidden/system fields unrelated to the contract and per-field transport __metadata no longer consume the250000-character child bound. Exact SchemaXml, missing required fields and duplicate/mismatched contract fields remain intact; no truncation, relaxed schema/size gate, list settings or rule/normalization changes. Setup report exposes requestCharacters and child validationCode/diagnostics/run reference. Missing/duplicate/wrong-type, oversized required XML and no-write cases are regression-tested with native length enforcement. All consumer rule/authority/business graphs remain unchanged; new bundle hashes/build linkage and native retest must be recorded. Prior schema apply is not rolled back or repeated blindly; owner next uses read-only ApplyChanges=No after the corrected import.


### #81 corrected collector package1.0.0.1

Artifact `artifacts/core_batch/v1.0.0.1/TandemCoreBatch-v1.zip`; shared deployment build **bd66271f-090e-4f5c-a890-8cb5b61173cc**; SHA256 **2708aef6bdff431c6681e17aeaca44d46073b9ef83ed2bd81af2ea3124661e92**. Same Solution identity and component IDs, update to1.0.0.1; all components remain disabled in the package. Setup now117definitions/depth6; overallmax393/7 against500/8. All12production documents compare exactly to v1 after explicit shared-build rebinding; no operation/normalization/compatibility changes. New45-case packaged smoke and9actual-packaged business E2E cases PASS locally. Focused schema/packaging/shared regressions recorded in the new validation.json. Native collector retest NOT RUN; raw native Request_text detail still requested.

Owner next: import this as UPDATE of TandemCoreBatch, preserve existing SharePoint mappings, keep business/event flows disabled; enable shared child + Setup and run **ApplyChanges=No**. Existing receipt list is retained; no repeated schema write is needed to diagnose. Expect collectionComplete=true, validationCode=OK, schemaVerified=true and full schemaResult; report also gives requestCharacters/validationDiagnostics/validationRunReference. If false, return that report/error; do not adjust list settings or rerun Apply blindly. Once read-only audit succeeds, the prior repeat-apply/remaining native checklist still applies. All affected consumer tickets reference this new version/build/hash; historical v1failure and old native proofs remain unchanged.


### #81 corrected read-only native audit owner-confirmed — 2026-11-14

For #45's corrected1.0.0.1 retest, owner confirms validationCode=OK, collectionComplete=true and schemaVerified=true. Record **OWNER-CONFIRMED READ-ONLY SCHEMA PASS**, scoped to that report summary. Full report/current run reference were not pasted, so exact package-build/run correlation is not independently captured; the next repeat report can supply it. Evidence: artifacts/core_batch/v1.0.0.1/results/schema-audit.owner-confirmation.json. No code/schema/rule/package-byte changes; ZIP/build/hash remain unchanged. Original native input failure remains historical evidence, with exact old Request_text error not supplied.

Next bounded test: run TandemBatchSchemaSetup ApplyChanges=Yes once and confirm schemaVerified=true/validationCode=OK and every Create action Skipped. Return Setup_report plus skipped-action confirmation to capture runReference/build. Do not close #81/#45 or mark the combined repeat-apply acceptance passed yet. Native45-case smoke, individual business/automatic/app acceptance and ordinary-user access are not implied by this schema PASS; retain pending/deferred states.


### #81 native repeat-apply schema report PASS — 2026-11-14

Owner supplied the full corrected1.0.0.1 report: buildbd66271f-090e-4f5c-a890-8cb5b61173cc; ApplyChanges=true; parent08584069211508254579686294345CU13; child08584069211275890958307283979CU25. validationCode=OK, schemaVerified=true, collectionComplete=true, schemaMatches=true/allSchema=true, all8roles checked, no differences. Input41372characters; every diagnostic stage Succeeded. Business row writes/deletes/permissionChanges0; receipt GUID864dfe53-b67c-4504-9d48-ad4356b813d8 remains observed. Exact evidence: artifacts/core_batch/v1.0.0.1/results/schema-repeat-apply.owner-report.json.

Record native full-schema PASS on repeat apply, now with exact build/parent/child correlation. The report does not contain individual Create-action statuses; **all Create actions Skipped remains unconfirmed**, not failed and not a reason to rerun. rowWrites=0 concerns business rows, not schema-creation action status. Ask only for those statuses in this same run; do not check off the combined no-schema-write repeat criterion yet. Native45-case smoke/consumer/automatic/app/access gates remain separate. ZIP bytes/build/hash/rules/schema contract unchanged; no code change or new tests required for recording native evidence.


### #81 repeat setup safe-repeat criterion completed — 2026-11-14

Owner confirms every Create action was gray/Skipped in the same native Apply run08584069211508254579686294345CU13 (buildbd66271f-090e-4f5c-a890-8cb5b61173cc). Combined with the exact8-role schema PASS report, record **repeat setup PASS**; no additional setup rerun is needed. Status evidence: artifacts/core_batch/v1.0.0.1/results/schema-repeat-apply.owner-confirmation.json. This supersedes the pending Create-status confirmation above. No code/package/schema/rule change; ZIP/hash unchanged. Next pending native gate is TandemCoreValidationSmoke (no inputs), expecting suiteBATCH,45completed/45tests,allPassed=true,failedCases=[]. Keep business/event flows disabled until that gate passes; #81/#45 remain open with consumer/automatic/app/access acceptance separate.


## #45 delegated technical flow-test handover — 2026-11-14

Owner will hand flow testing to technical colleagues, arrange necessary test access if needed, and manage activation/isolation outside the cases. No further functional case must be personally run by the owner now: import/schema/safe-repeat and owner-checked smoke are complete, and #61 event/read/shared/no-op has native PASS. Status correction/write/readback/follow-up remains required acceptance assigned to colleagues, not waived or marked passed.

Current procedures live inline in #45/#81 and the11flow issues:75individual flow cases with role/fixture, numbered actions, expected response/persistence and evidence/cleanup. Repeated old-flow on/off/import/connection instructions are removed from tester steps. One-time access/entry/fixture preparation is centralized under #45 and may be delegated to a test coordinator. Colleague access is unknown; owner may arrange limited technical test access, without assuming new licensing or proving ordinary-participant privacy. First colleague test is read-only MyRequests with their actual own ParticipantId.

PowerAppsV2 invocation must be usable before its case: use the portal input form if available, otherwise a coordinator-prepared Power Apps test button. No invocation route is declared tenant-verified for colleagues. Missing input entry/account/fixture/harness is BLOCKED, not PASS or a reason to invent a screen/trigger change. Importing core does not deliver #16/#67/#68 UI; a minimal technical button is sufficient. Fault/race/paging cases go to a prepared isolated operator harness; no shared live schema/catalogue/permission faults are assigned. Ordinary-participant privacy remains deferred, email remains blocked. Original acceptance/test history is archived as dated JSON, not active instructions. Static checks confirm all75case IDs unique, every case has a checkbox/steps/expectation, actual input keys match packaged triggers, bodies fit GitHub limits, and legacy toggle instructions are absent. No runtime/code/schema/matching/IO/package change; current1.0.0.1 build/hash and existing native proof remain unchanged. Shared#81 no-impact: procedure and assignment change only, consumer acceptance still scoped to receiving tickets.
