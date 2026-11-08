# Test execution records

The test definitions are in TEST_CATALOGUE.md. This file stores observed results
without overwriting history when requirements or deployed versions change.

## Known baseline evidence

| Run reference | Date | Tests | Result and evidence source | Version/scope limits |
|---|---|---|---|---|
| HIST-REG-20261031 | 2026-10-31 | BASE-001–004 | PASS, owner-reported saved/reopened language selections, multiple Teach/Learn and teach-only profile in chat; see POC_03_PARTICIPANT_SELF_REGISTRATION.md | Published app/flow versions not recorded; original registration baseline, not optional-time-zone/culture target |
| HIST-FLOW-20261031 | 2026-10-31 | BASE-005–009 | PASS, owner-confirmed guided manual Compose/Filter/Select, teach-only and Needs review runs; see src/README.md and tests/fixtures/discovery_flow_cases.json | Manual synthetic trigger, five chat profiles, not full six-profile fixture or real-data/authenticated app integration; flow export/version not captured |

Do not claim that screenshots/full run logs were captured for every historical
check. These rows preserve owner reports, not agent-observed replay results.
These baseline rows do not certify the target MVP. Later entries record scoped
owner checks and retests; a partial case pass does not complete its other variants.
Target scenarios without explicit execution evidence remain NOT RUN or deferred.

## Deferred and pending checks

| Tests | State | Reason / linked work |
|---|---|---|
| ACC-001–002, ACC-005 | DEFERRED | Owner will arrange normal colleague testing; #18/#39–#42 remain open |
| DISC-008 | REQUIREMENT PENDING | Exact Discovery display fields not agreed |
| NOT-001 | REQUIREMENT PENDING | #49 must select event/channel/recipient behavior |
| MIG-001–002 | DEFERRED | Actual Excel inspection/migration is final phase #48 |
| Remaining registration/flow cases and unexecuted case portions | DEFERRED | Owner explicitly prioritizes integrated app/flow construction before the remaining detailed tests (2026-10-31); preserve prior passes/failures and resume after core build |

## Latest local checks

### RUN-20261031-01 — POC-05 local configuration checks

- Tester: agent; repository checks only, no tenant account used.
- Branch: codex/issue-5-culture-registration; working tree for the POC-05 PR.
- App/flow version: not applicable; neither was inspected or deployed.
- Inputs: repository schema/policy and synthetic mutated configurations; no
  employee data or live SharePoint calls.

| Check | Actual result | Status | Scope |
|---|---|---|---|
| pytest, tests/test_sharepoint_schema.py | 22 passed | PASS | Schema/policy consistency and rejection of required optional fields, omitted offer/interest branches, wrong culture targets and disabled inactive-selection rule |
| validate_schema.py | Schema is valid | PASS | Desired schema structure only |
| validate_registration.py | Registration policy is valid | PASS | Desired form/policy agrees with schema |
| git diff --check | No formatting errors | PASS | Working-tree text changes |
| REG-001–009, REG-011–012 tenant scenarios | Not executed | NOT RUN | Culture values, prerequisites, actual form/flow changes and acceptance remain pending |

The mutation tests cover configuration protections related to REG-002/003/005/
006/008. They do not establish a live save, active-option filter, validation flow,
edit-loop guard, authentication or discovery result. No cleanup was needed;
no live records were created. Retest live scenarios after owner setup and record
the app/flow versions separately.

### RUN-20261031-02 — expanded culture proposal

- Agent local check on codex/issue-5-culture-registration; no app/flow deployed.
- PASS: culture_catalogue_proposal.json parses; all 85 display labels and keys
  are unique; labels are alphabetically ordered; Active values are Boolean true;
  proposal_pending_owner_review status is preserved.
- PASS: git diff --check. No tenant records created or changed.
- This validates proposal data structure only, not coverage approval, import,
  active-option filtering or any REG acceptance scenario.

## Tenant setup evidence

### SETUP-20261031-01 — owner access screens

- Owner-reported: SharePoint New List/Create column options available; existing
  registration app and submission flow open in Edit. All three checks confirmed.
- No creation/save operation was tested by these checks; no app/flow version
  changed. Culture catalogue connection/read access remains to verify after creation.
- This is setup evidence, not a REG/ACC scenario pass or ordinary-user access proof.

### SETUP-20261031-02 — catalogue rename and bulk-entry workbook

- Owner reports the CultureKey display-name change to Culture key is done.
  Required/unique/default settings and catalogue contents have not been
  independently inspected.
- Agent generated docs/import/culture_catalogue_import.xlsx from the 85-value
  JSON proposal. PASS: all 85 rows and three columns match the source after XLSX
  export/reimport; first rows rendered and visually inspected.
- Owner subsequently confirms the bulk-entry step and its requested checks are
  done: 85 catalogue entries, populated keys and Active = Yes. Evidence is owner
  reported; no list export or screenshot captured. App/flow catalogue-read access
  remains NOT RUN. This is not a registration acceptance pass.

### SETUP-20261031-03 — Participants column screenshot

- Screenshot shows required Participant account and required Time zone; Time zone
  is a Lookup. ShareCultures/LearnCultures (or their intended display labels) are
  not visible in the supplied column list. Their creation/settings are unverified.
- Email, Matching cycle and Full name are visible existing helper/legacy fields;
  their presence does not authorize deletion or changing the identity contract.
- A column summary does not prove lookup catalogue targets, multiple selections,
  uniqueness or actual internal names. Inspect field settings for those checks.
- #5 remains open. Optional-time-zone acceptance and culture form/flow tests have
  not passed merely because the Culture catalogue was populated.

### SETUP-20261031-04 — optional SharePoint Time zone

- Owner confirms the instructed change: Participants Time zone, Require that
  this column contains information = No, saved in SharePoint.
- Owner-reported setting only; no new screenshot, app save/reopen, flow result or
  blank-time-zone discovery case observed. REG-003 and DISC-005 remain unverified.
- Culture lookup settings and app/flow refresh/validation remain pending.

### SETUP-20261031-05 — participant culture lookups

- Owner confirms both instructed lookup columns are ready: ShareCultures and
  LearnCultures, displayed as Cultures I can share and Cultures of interest,
  looking up Culture catalogue / Title, multiple selections Yes, required No.
- Evidence is owner-reported completion of the setup instructions. Internal names
  and settings were not independently inspected through a tenant export.
- No app refresh, culture save/reopen or flow validation result confirmed yet;
  REG tenant scenarios remain unverified. Next: add generated cards to Form1.

### SETUP-20261031-06 — culture cards added to app

- Owner confirms the instructed Participants refresh, addition of both culture
  fields to Form1 and app save. Publication was not requested; no published
  version or flow change is evidenced by this confirmation.
- Catalogue options/multiple selection, stored lookup IDs, blank Time zone,
  save/reopen and submission-flow validation remain unverified. Next: preview
  both culture dropdowns in Edit/New mode and check multiple selections.

### RUN-20261031-03 — culture selector options

- REG-013: FAIL, owner-reported. Both culture lookup controls show Item 1/2/3
  rather than the expected catalogue labels during the requested preview check.
- App editing/preview version not recorded; no screenshot or Items expression
  inspected. Sample/default control binding is suspected, not a proven cause.
- Proposed correction: select the control inside each culture card, inspect Items,
  and bind it to Choices of the corresponding Participants culture lookup; use
  Value as the display field for classic lookup combo boxes. Retest pending.
- No successful culture selection, save/reopen, flow validation or published
  app behavior is established by this run.

### RUN-20261031-04 — culture selector retest

- Owner reports the lookups are now correct after the supplied Items/display
  binding changes. The reported Item 1/2/3 display issue is resolved in preview.
- REG-013 label-display portion: PASS, owner-reported. Multiple selections and
  stored lookup persistence were not explicitly confirmed; full case remains
  pending those checks. Earlier failed run is retained above.
- No published app version or submission-flow version recorded. REG-002/003/007
  save/reopen and REG-005 empty-input blocking remain unverified.

### SETUP-20261031-07 — registration control names

- Owner confirms the four Combo box controls were renamed to cmbTeachLanguages,
  cmbLearnLanguages, cmbShareCultures and cmbLearnCultures as instructed.
- No new save, validation or persistence result confirmed. Next: configure the
  Save OnSelect all-four-empty guard and test REG-005 without submitting data.

### RUN-20261031-05 — empty-selection save guard

- REG-005 form/Preview portion: PASS, owner-reported. Following the supplied Save
  OnSelect formula, clearing all four language/culture selections and clicking
  Save shows the validation message and keeps the form open as expected.
- The instruction included cancelling the temporary edit. No SharePoint write
  audit, published app version or backend validation run was independently observed.
- This does not prove server-side rejection of invalid direct-list input. Culture
  save/reopen, optional blank Time zone, multi-selection persistence, inactive-ID
  checks and submission-flow create/edit validation remain unverified.
- Next prerequisite: inspect the actual participant-submission trigger and current
  validation actions before changing edit handling or its update-loop guard.

### SETUP-20261031-08 — submission trigger inspected

- Owner confirms the existing Tandem – Participant submission trigger is When an
  item is created. This trigger alone does not revalidate profile edits.
- No trigger change performed/confirmed. Inspect current Compose/Condition/Update
  item structure and design/test a guard against self-triggered Status updates
  before adopting created-or-modified validation. Create/edit acceptance pending.

### SETUP-20261031-09 — submission flow overview

- Owner screenshot shows When an item is created, followed by Timezone selected,
  Learn selected and Teach selected Compose actions, then an outer Condition.
- Outer True contains Condition 1 (collapsed); outer False shows two collapsed
  actions. Expressions, underlying lookup field references and Status writes are
  not visible, so their semantics and loop behavior remain unverified.
- No culture Compose actions appear in this overview. Next: inspect the outer
  Condition code, including nested branches, before editing validation/triggers.
- No flow changes, run results or deployment version confirmed by this screenshot.

### SETUP-20261031-10 — submission condition code inspected

- Pasted outer Condition checks Teach selected OR Learn selected non-empty. Its
  nested Condition_1 requires Timezone selected non-empty before Active; otherwise
  it writes Needs review. Neither culture selection participates in the predicate.
- All three Update item branches write Status and replace Participant account
  Claims using Resolve person results from Author/Email. Observed connector field
  path is item/Participantaccount/Claims; this records an existing action parameter,
  not a request to recreate or rename the unique identity column.
- No conditional skip for an already-correct Status is visible. Simply switching
  to a modified trigger would retain unconditional self-updates and identity writes.
- Planned correction: read current item once, use its lookup values, retain account
  identity, check language/culture presence and actual catalogue validity, and write
  only a differing validation Status. Read failure must not reach a success branch.
- No correction is deployed or tested by this inspection. Next guided action:
  add SharePoint Get item named Read participant immediately after the trigger,
  using the trigger ID; inspect/map its outputs before changing existing branches.

### SETUP-20261031-11 — current participant read action

- Owner initially showed an action without Id; its parameter layout suggested
  Get items. Guided replacement was SharePoint Get item (singular), renamed Read
  participant, with the existing site, Participants list and trigger ID token.
- Owner confirms that corrected configuration is done. No successful read/run or
  output schema has been inspected yet; connection/read access remains unverified.
- Next: inspect the existing Teach/Learn/Timezone Compose expressions to retain
  exact tenant field names while changing their source to Read participant, then
  include the two culture arrays. Trigger and validation branches remain unchanged.

### SETUP-20261031-12 — existing Compose field references

- Owner-provided Compose code reads triggerBody Teachlanguages, Learnlanguages
  and Timezone (exact casing). Timezone selected runs after Get_item, confirming
  that internal action reference in this flow despite the requested display name.
- Replacement expressions should read body('Get_item') with those same field
  keys. Do not guess TeachLanguages/LearnLanguages/TimeZone casing from the
  canonical proposed schema or recreate existing columns.
- Culture keys ShareCultures/LearnCultures remain based on the instructed column
  creation/owner confirmation; raw output keys still need runtime verification.
- No replacement expressions or successful action outputs confirmed yet.

### SETUP-20261031-13 — selection Composes configured

- Owner confirms the three existing Composes now read Get_item fields
  Teachlanguages, Learnlanguages and Timezone, and two new culture Composes read
  ShareCultures/LearnCultures as instructed.
- No successful read/output schema or action internal-name export inspected for
  the newly added culture actions. Configuration confirmation is not a run pass.
- Next: extend the outer OR presence condition with both culture arrays, then
  replace mandatory-time-zone validation and unconditional identity/status writes.
  Trigger remains creation-only until the completed guards are reviewed/tested.

### SETUP-20261031-14 — four-field outer presence condition

- Owner confirms the outer Condition retains OR and now includes non-empty Teach,
  Learn, Share selected and Culture interests selected comparisons as instructed.
- No flow execution or exported updated expression inspected. Culture branch
  behavior and typed Boolean comparisons remain pending runtime verification.
- Next: replace Condition_1's required-time-zone comparison with the current
  Get_item Status Value != Active guard; remove its obsolete Needs review False
  actions. The outer False path separately needs its own change-only guard.

### SETUP-20261031-15 — Active branch status guard

- Owner confirms Condition 1 now compares Get item's Status Value != Active in
  place of the Timezone presence check. Its obsolete False actions Update item 2
  and Resolve person 1 were removed, leaving False empty as instructed.
- Configuration report only; actual branch expression and loop behavior have not
  been re-exported/exercised. Active True still requires identity-write cleanup;
  the outer invalid branch still requires its own guarded update.
- Next: remove the Participant account Claims parameter from Update item 1, keep
  item ID and Status Active, then remove its unused Resolve person predecessor.

### SETUP-20261031-16 — outer False branch recovery needed

- Owner reports accidental deletion of the outer Condition False actions and
  confirms Condition 1 False is empty as intended. No flow run/data loss reported.
- Recovery plan: outer False gets a condition using current Get_item Status Value
  != Needs review. Its True contains a SharePoint Update item with the current ID
  and Status Needs review only; False stays empty. Do not restore the old
  Created By/Resolve person identity overwrite. Recovery is not yet confirmed.

### SETUP-20261031-17 — outer False recovery configured

- Owner confirms the recovery instructions are done: outer False contains a
  current-Status != Needs review condition; its True updates the current item to
  Needs review and its False is empty. Condition 1 False remains empty.
- No exported recovered code or run results inspected yet. Preservation of other
  fields and both guards must be checked in the actual condition export.
- Active-branch account-write/Resolve person cleanup is not explicitly confirmed
  after the accidental deletion. Next: verify that branch's payload/dependencies,
  then review the whole outer Condition before enabling modified-event handling.

### REVIEW-20261031-01 — updated outer Condition code

- Owner pasted the current condition export. Confirmed: four non-empty selection
  checks joined by OR, both already-correct branches empty, no Resolve person
  actions, and Active guard compares Get_item body/Status/Value with Active.
- REG-014 configuration review: FAIL. Active Update_item_1 still sends
  item/Participantaccount/Claims = Get_item body/ID, incorrectly mapping the
  numeric item ID into a Person Claims field. Remove that update parameter.
- REG-015 configuration review: FAIL. Condition_2 compares Get_item body/Status
  to the string Needs review; use body/Status/Value consistently with Condition_1.
  An object-versus-string comparison can cause repeated invalid-branch writes.
- Needs review Update_item payload contains ID and Status only, as intended.
- No runtime tests or trigger changes confirmed. Correct both defects before
  modified-trigger testing; catalogue validity checks remain separately pending.

### SETUP-20261031-18 — reviewed condition defects corrected

- Owner confirms the two requested corrections: Participant account Claims removed
  from Active Update item 1, and Condition 2 compares Get_item body/Status/Value
  rather than the whole Status object against Needs review.
- Earlier REVIEW-20261031-01 failures remain historical evidence. Corrected code
  was not re-exported and REG-014/015 runtime behavior has not yet been exercised.
- Next: replace the creation-only trigger with SharePoint created-or-modified,
  preserve site/list/ID bindings, then run controlled edit/loop tests. Concurrency
  Control remains unchanged after checking documented reversal/queue limitations;
  no serialized execution is assumed. No modified-trigger deployment confirmed yet.

### SETUP-20261031-19 — modified trigger saved with warnings

- Owner reports replacing the trigger with When an item is created or modified.
  Update item 1 initially lost its required Id binding; guided correction was
  outputs('Get_item')?['body/ID']. Owner then confirms the flow saved successfully.
- Designer reports possible circular-loop warnings on both Update item actions.
  These warnings identify the self-updating trigger pattern; they are not runtime
  proof of a loop or of successful prevention. No new run history inspected yet.
- Next controlled test: one owner-profile Comments edit with valid selections;
  inspect current Status, guards and actual write actions. Matching Status must
  skip the update; after one necessary change a follow-up must not write again.
  If consecutive follow-up runs repeatedly write the same Status without a new
  user edit, turn off this flow and inspect the guard/current-item values.
- REG-014–016 runtime acceptance, catalogue checks and culture/optional-time-zone
  persistence remain pending. No concurrency setting change confirmed.

### RUN-20261031-06 — already-Active edit/no-write path

- REG-015 matching-Status portion: PASS, owner screenshots from the requested
  Comments-only edit test. The profile shows Status Active and a Learn language
  selected; culture fields are empty and Time zone is populated.
- Run screenshot shows selection Composes and outer Condition succeeded, outer
  True reached Condition 1, and Update item 1 is Skipped with an empty no-change
  branch. The outer invalid path is not exercised by this run.
- This supports the already-Active no-write behavior for that edit. Run ID/time,
  flow version and complete later run history were not supplied; no global
  no-loop, required-write/follow-up or identity-preservation pass is inferred.
- Next controlled case: on a valid owner test profile, set validation Status to
  Needs review, verify the flow corrects it to Active once, then inspect any
  follow-up for no further write and confirm identity/selections unchanged.
- Culture-only, blank Time zone, empty-profile Needs review, catalogue validity
  and multi-selection persistence acceptance remain pending.

### RUN-20261031-07 — required Active correction unresolved

- Owner reports Status remains Needs review after the instructed one-off change
  on the same previously valid profile. Expected automatic return to Active has
  not been demonstrated; required-write portion of REG-015 remains unresolved.
- No newest-run timing, trigger delivery, Condition results or Update item error
  supplied yet. Do not infer an empty selection, trigger fault or failed write
  from the list status alone. No claim of global loop prevention is made.
- Next: inspect whether a new run exists after the edit, then its Get item Status,
  outer Condition, Condition 1 and Update item 1 result/error to locate the cause.

### RUN-20261031-08 — Active correction and follow-up confirmed

- Owner explicitly confirms all four requested outcomes: Status returned to
  Active, correcting Update item 1 Succeeded, follow-up Update item 1 Skipped,
  and Participant account/selections stayed unchanged.
- REG-015 Active correction/follow-up portion: PASS, owner-reported. Together
  with RUN-20261031-06, this verifies observed Active no-op/correction behavior for
  the tested owner profile. The Needs review branch still requires its own run.
- REG-014 owner-profile preservation portion: PASS, owner-reported. The separate
  admin-created/different-participant variant remains unverified.
- RUN-20261031-07 is resolved by this later owner retest; the cause/timing of the
  earlier unchanged Status was not supplied and is not invented here.
- Run IDs, timestamps and exact saved flow revision not supplied. Do not infer
  cross-flow/concurrent safety, invalid-catalogue checks or full #5 completion.
- Next: all-four-empty direct-list fixture to exercise Needs review correction
  and no-write follow-up, then restore the original selections.

### DECISION-20261031-01 — build integrated core before remaining tests

- Owner asks to prioritize app/Power Automate workflow construction through
  discovery, requests, group/membership creation and notifications; detailed
  tests/validation resume afterward. No pending case is promoted to PASS.
- Owner prefers a central experience inside the app. Approvals may be considered
  at the notification stage; no email/Teams/Approvals channel or connection chosen.
- Setup-automation investigation is postponed. Required lists/data bindings are
  attached when their dependent actions are built, not claimed completed now.
- Existing owner evidence remains scoped. Wider-rollout access and other release
  checks remain open; #5/#7 and other incomplete implementation tickets stay open.

### BUILD-DISC-20261031-01 — app-triggered reader configured

- Owner confirms the new TandemDiscovery flow setup: Power Apps (V2), numeric
  ParticipantId input and SharePoint Get item for Participants. Screenshot shows
  the trigger's Number token labelled ParticipantId; owner confirms it inserted
  in the Get item Id field and the setup saved.
- Configuration milestone only. No reader output, app invocation, candidate query,
  matching response or trusted ordinary-user caller binding demonstrated yet.
- Next build: Get items Candidate source with Status Active, bounded pagination,
  then map actual current/candidate lookup-ID arrays and matching actions. Existing
  submission-run output can establish field shape without new acceptance testing.

### BUILD-DISC-20261031-02 — lookup ID-array shape confirmed

- Owner supplied a scoped existing Get item output. Learnlanguages is an array
  of expanded lookup references (Id/Value); Learnlanguages#Id is an integer array
  annotated Collection(Int64). Direct numeric-ID normalization is available for
  this observed field. Timezone is a single expanded lookup object when selected.
- Record only the shape here, not the owner's actual profile values. Equivalent
  Teach/culture #Id mappings are based on the expected connector pattern and
  instructed internal names; verify returned values while binding the flow.
- Next: current My_profile_row Select + My_profile Compose, and candidate
  Normalized_candidates Select + Candidate_profiles Compose. No matching or app
  invocation success inferred; Candidate source configuration not yet confirmed.

### BUILD-DISC-20261031-03 — normalization actions configured

- Owner confirms the four requested actions are configured: My_profile_row Select
  with eight profile/identity/status/ID-array mappings, My_profile Compose,
  Normalized_candidates Select with the same mapping and Candidate_profiles Compose.
- Candidate source was a prerequisite in the instructions; its complete query/
  pagination settings and normalized runtime outputs have not been inspected.
- Next: Eligible_candidates Filter array, minimal Candidate_fit projection and
  the Power Apps response including explicit over-bound error/no partial result.
- Configuration milestone only; no successful matching/app invocation or completed
  #7 acceptance is inferred. Detailed cases remain deferred by owner.

### BUILD-DISC-20261031-04 — matching and response configured

- Owner confirms adding Eligible_candidates Filter array, Candidate_fit Select
  and Respond to a Power App or flow with candidatesjson/errormessage Text outputs,
  following the supplied expressions. Configuration report only; no new run output
  or app response has been inspected.
- Projection is the minimal owner preview (profileId, displayName, fitType).
  Matching covers either language/culture exchange direction and excludes self/
  non-Active validation. Response definitions suppress over-500 partial results
  and provide registration feedback; runtime behavior remains unverified.
- Next: add the saved flow to Power Apps, create scrDiscovery and colCandidates
  gallery, and bind the Discover button. Keep unpublished/owner-only while caller
  binding, participation/openness and broader exposure gates remain open.

### BUILD-DISC-20261031-05 — app flow and Discovery screen scaffold

- Owner screenshot shows TandemDiscovery listed under In your app in the Power
  Automate pane, and a screen named scrDiscovery with a sample art-gallery layout.
  A Blank option was not visible in the owner's screen picker; do not assume the
  template is an empty screen or that its sample fields match candidate records.
- Owner confirms the Back button instructions completed, with Text Back and
  OnSelect Navigate(MainScreen1, ScreenTransition.None).
- Discover button/collection binding and gallery replacement are not confirmed.
  Next: add the MainScreen1 Discover button and its flow/ParseJSON collection
  formula, then replace/rebind sample gallery content before showing results.
- No successful app-to-flow invocation or runtime candidate display claimed.

### BUILD-DISC-20261031-06 — button placement and ID-binding error

- Owner screenshot shows Back and Discovery buttons together on the sample
  results screen. Correct layout: Discover on MainScreen1, Back on scrDiscovery.
- The copied OnSelect reports IsBlank invalid arguments around Form1.Item.ID;
  app-to-flow invocation has not been demonstrated by this screenshot.
- Guided correction: move only the Discovery button to MainScreen1 and replace
  both Form1.Item.ID occurrences with RecordsGallery1.Selected.ID, the original
  registration-gallery reference. Verify its actual name if renamed.
- Keep Back Navigate(MainScreen1, ScreenTransition.None). Gallery candidate binding
  and editor-error resolution remain unconfirmed; no runtime pass inferred.

### BUILD-DISC-20261107-01 — resumed tracking of owner-reported app results

- Recorded on 2026-11-07 from the preceding owner confirmations; actual execution
  dates, versions, run IDs and published/sharing state were not supplied.
- Owner corrected the selected-record reference, replaced the sample artwork with
  Gallery1, and bound colCandidates, Title4 displayName and Subtitle4 fitType.
- Owner reports an empty discovery gallery and working Back navigation. Owner
  states suitable participant data is absent; no positive matching case or
  inspected flow response was supplied. Do not infer matching correctness or
  ordinary-user authorization from navigation/empty results.
- #7/#9 remain partial; remaining data mapping, caller, availability, projection,
  query bounds and tenant acceptance stay open.

### BUILD-REQ-20261107-01 — request creation scaffold configured

- Owner confirms the Connection Requests list and guided TandemSendRequest steps,
  including two participant-ID inputs, Read sender/Read recipient, Active/present
  Claims/different-account checks, bidirectional Pending query, conditional Create
  item, result variables and one success/message response.
- Owner confirms adding the flow to Power Apps and binding Gallery1.NextArrow4
  to send the selected sender/candidate IDs and show the response.
- These are configuration reports, not an observed send. No created request row,
  actual success/duplicate/error response, versions or run IDs were supplied.
- Query-then-create is not simultaneous-submit protection; compatibility,
  trusted caller ownership, #6 participation/openness and relevant #47 safeguards
  remain implementation gaps. Access is not proven by app ID references.
- List scaffold: Title, required Number SenderParticipantId/RecipientParticipantId
  (zero decimals), required Choice Status Pending/Accepted/Declined/Cancelled
  with Pending default, and built-in Created. No group-target/recovery fields
  have been confirmed.
- #10 remains open; #11 acceptance/decline and group/membership creation are not
  implemented by this flow.

### BUILD-REQ-20261107-02 — explicit pause/resume point

- Owner explicitly did NOT execute the instruction to create TandemMyRequests.
  Record it as NOT STARTED, not configured or tested.
- Resume under #10 with the in-app sent/received requests view; Pending
  cancellation and #11 responses still follow. #23 visibility/authority remains
  unimplemented/unverified. No acceptance case is newly marked passed.
- Scope/criteria remain in the existing tickets; no replacement issues, closure,
  permission architecture or notification channel is selected by this checkpoint.

### TRACK-20261107-01 - preparation merge, not tenant acceptance

- Owner approved merging PR #52 as partial preparation under build-first delivery.
- PR #52 merged; #5 remains open. No tenant test result changes.
- PR #54 retargeted from the merged #52 branch to main. PR #55 remains stacked
  on #54; both remain open. Do not infer their acceptance or merge from this step.

### TRACK-20261107-02 - discovery reference synchronized

- Discovery branch commit 15469f0 updates config/discovery_core_build.json and
  src/README.md with the guided filter/projection/response and actual app bindings.
- Version 3 distinguishes owner-reported configuration, empty-gallery/Back
  observations and unverified populated matching. It lists coverage/omissions;
  no live export or completed tenant acceptance is claimed.
- Local pytest: 22 passed. JSON parse, projection/response keys and diff checks
  passed. These do not execute Power Automate expressions or verify access.
- PR #54 and #7 updated; #54 remains draft and #7 open. Tracking PR #55 includes
  the updated discovery base. No new tenant run or published version supplied.

### BUILD-REQ-20261107-03 - history and cancellation configuration

- Owner confirms TandemMyRequests trigger/Read participant, Get items request
  query, Request rows Select and requestsjson/errormessage response saved.
- Supplied Select code confirms the actual request reader is Get_items and
  From is outputs('Get_items')?['body/value']. Invalid Read_requests response
  references were corrected before the owner reported a successful save.
- Query covers either participant-ID side, newest first; the 101-row scaffold
  returns an explicit error above the 100-request history bound. These settings
  and runtime values have not been exported or inspected as a successful run.
- Owner screenshot confirms scrRequests, galRequests, Title4_1/Subtitle4_1,
  Back Button1_1, and removal of the copied send arrow. Owner confirms the
  My requests button/flow, typed colRequests mapping and gallery bindings.
- Owner confirms TandemCancelRequest: participant/request reads, sender-ID match,
  Pending-state and nonempty account check, conditional Cancelled update and
  result variables/response. Update item required both participant IDs; guided
  fix preserves SenderParticipantId/RecipientParticipantId from Read_request.
- Owner confirms the Cancel button inside galRequests, visible only for Sent
  Pending, calls the flow and updates the local row only on reported success.
- No actual loaded history, cancellation response, changed persisted row,
  cancel/accept race, authenticated ownership or published version was supplied.
  These are configured milestones, not new acceptance passes. Query-then-update
  does not protect cancellation versus acceptance races; #47 still applies.
- #10 stays open. Core construction moves to #11; TandemRespondRequest not yet
  built. Existing caller/compatibility/availability/access gaps remain.

### BUILD-RESP-20261107-01 - response/group scaffold configured

- Owner confirms TandemRespondRequest inputs, participant/request readers,
  Requested decision, recipient/Pending/decision guard and Decline branch.
- Acceptance scaffold includes sender read, compatible language/culture ID
  intersections, group-name/type/capacity inputs and parsed focus arrays,
  Group choices valid, SourceRequestId group lookup/create/reuse, membership
  loop/key lookup/create, group/membership reads, sender/recipient membership
  filters and Memberships ready. No acceptance run is supplied.
- Owner confirms Groups and Group Members created with instructed contract
  fields, plus unique required Groups.SourceRequestId Number and Group Members
  MembershipKey Text. Actual schema/export is not inspected. These keys support
  retry identification; they do not prove full #47 safety.
- Decline and Cancel still use normal Update item at this point. No final
  Accepted write, publication, partial-group recovery or response UI is complete.
  Configuration confirmations are not tenant acceptance. #11/#12/#47 stay open.

### PREREQ-REQ-20261107-01 - conditional-update mechanism verified

- TandemSharePointCheck uses existing SharePoint Send an HTTP request action.
  Owner reports metadata GET succeeded with statusCode 200.
- Test creates a temporary technical request with zero participant references,
  reads verbose item metadata/ETag, attempts a current-version Cancelled MERGE,
  attempts Declined with the original stale ETag, then deletes the test row.
- Initial screenshot: first MERGE failed PreconditionFailed because IF-MATCH
  contained the entire response body, not its ETag. Stale test skipped; overall
  green banner did not establish the mechanism. Preserve this failed attempt.
- Guided correction on both writes:
  body('Read_test_revision')?['d']?['__metadata']?['etag'].
- Owner then supplied stale-test inputs showing IF-MATCH with the original
  quoted version. Owner reports stale PreconditionFailed and subsequently
  explicitly confirms the first conditional write and Delete test request both
  succeeded. Thus current-version write succeeds, stale write is rejected and
  cleanup succeeds in this scoped synthetic mechanism check.
- Run ID/time, flow revision and raw response codes for the final three actions
  were not supplied. Do not invent exact 204/412 evidence beyond the expected
  semantics and reported outcomes.
- Related #47; prerequisite evidence for REQ-009/010/011, NOT a pass for those
  full scenarios. Accept/Decline/Cancel still need conditional-write integration,
  conflict handling, partial-group recovery and end-to-end authorization/state/
  capacity verification. No routine admin workflow or new connection chosen.

### REVIEW-RESP-20261107-01 - pasted response block audit

- Source: owner-pasted Can respond action definition, not an entire flow export.
  Static count: 34 actions including the supplied If; deepest action depth 6
  within this block. Create_membership and Accept_conditionally are deepest.
  Any external ancestor containers were not supplied. No eight-level violation
  is established from this block alone.
- Confirmed configuration defects (not newly observed runtime test failures):
  Accept_conditionally header key is IF_MATCH rather than IF-MATCH;
  Membership_key inputs is literal concat text without expression prefix;
  Recipient_membership From contains its Boolean predicate instead of the
  Read_active_memberships value array.
- Condition_1 compares blank with blank and has no actions. It is a placeholder,
  not the instructed Acceptance confirmed predicate. SetupComplete creation is
  unconfirmed; no publication/recovery/Power Apps response implementation inferred.
- Decline_conditionally has IF-MATCH and current group/member creation mappings
  are visible, but static inspection does not certify actual runtime output shape
  or the complete conditional-write workflow.
- Next: owner fixes the three field errors, then restructure existing actions
  into sibling stages with ContinueProcessing and one final app response.
  Keep business actions outside accumulating validation branches. Preserve
  action names/expressions and check run-after dependencies after moving.
- Proposed sibling stages: validate request; decline; prepare/validate Accept
  choices; prepare group/memberships; commit/read/finalize or recover; respond.
  This is a layout plan, not a tested or imported replacement flow. No child-flow
  dependency or new connection/permission/licence is introduced.
- #11/#12/#47 remain open. Full caller, #6 availability, persisted focus/state,
  idempotency, conflict/recovery and tenant acceptance still apply.

### BUILD-RESP-20261107-02 - corrections, stages and final response configured

- Later owner-pasted preparation block statically confirms 26 actions, maximum
  depth 5 within that block and valid local sibling run-after references.
  Membership_key expression, recipient From array, IF-MATCH and the formerly
  empty Acceptance_confirmed predicate are corrected. Group choices valid was
  moved with its contents; this valid extra validation level was explicitly
  retained, superseding the instruction to empty its True branch.
- Owner confirms ContinueProcessing/response variables, Can respond and Process
  valid response separation, decline/failure flags, and Complete acceptance
  extracted to a sibling main-level stage. Final whole-flow nesting not inspected.
- Read group revision, SetupComplete condition, setup guard and conditional
  State/SetupComplete update are owner-confirmed configured. Setup condition
  was initially missing below the reader and was subsequently added.
- Final request reader was initially missing. Owner added it before final group,
  used five Dynamic content condition rows (recipient ID via known fx), and saved.
  No raw saved final-condition code is supplied; verify Status Value/reference
  choices in the final configuration review.
- Owner confirms one main-level success/message/groupid response with run-after
  handling. No actual Accept/Decline response or group/member persisted result.
- Cleanup gate, request terminal/identity checks, source-owned incomplete group
  guard and two-key Find cleanup memberships query are configured. No membership
  Left or group Ended cleanup writes yet.
- Backend batch finish line: membership cleanup, unfinished-group cleanup/feedback,
  configuration review and #11 PR checkpoint. App wiring is a later batch.
- No new tenant PASS. Remaining caller/availability/focus/retry/recovery gaps are
  implementation work, not waived by this configuration checkpoint.

### BUILD-RESP-20261107-03 - cleanup blocks saved, review pending

- Owner confirms Block 1 saved: cleanup loop, fresh membership revision read,
  Active/group/party/key guard and ETag MERGE MembershipStatus Left with LeftAt.
  Original membership, JoinedAt and keys are retained; no cleanup run supplied.
- Owner confirms Block 2 saved: after successful loop only, ETag MERGE sets the
  unfinished source-owned group State Ended, and final failure feedback uses the
  rejected request status. Completed SetupComplete groups remain outside the
  cleanup eligibility guard. No persisted end/feedback result supplied.
- Mark blocks 1 and 2 configuration-complete, not tenant PASS or full #47 safety.
- Block 3: obtain a current complete flow export if available (owner/co-owner
  export access not yet checked) or current action definitions; review names,
  references, run-after, Boolean/Choice field handling, nesting, terminal writes
  and response schema before the #11 PR checkpoint. No new feature work added.

### REVIEW-RESP-20261107-02 - complete export reviewed, changes required

- Owner supplied TandemRespondRequest-review_20261107212221.zip. Source SHA256:
  045fa25fb5243f3b6e98ae0913e3fe24194cf5004fdc67922fe1298910368d0b.
  Export metadata modified UTC: 2026-11-07T21:21:16.5567363Z.
- Static full-definition counts: 77 actions, maximum action depth 6, one app
  response with success/message/groupid, no missing body/outputs/items/action
  references and no non-sibling run-after references. Five MERGEs use IF-MATCH
  with version references and no wildcard.
- Required fix RESP-REVIEW-001: Decline Set_ContinueProcessing_2 is still true,
  allowing fall-through into group preparation that references skipped Accept
  inputs. Change it to Boolean false after the successful Decline.
- Required fix RESP-REVIEW-002: final status row reads body/Status rather than
  the declared Choice Value. Compare body('Read_final_request')?['Status']?['Value']
  with Accepted; current definition risks reporting successful acceptance as
  failure. Actual connector output needs runtime confirmation.
- Label cleanup RESP-REVIEW-003: first Number input title is NParticipantIdumber;
  rename its title ParticipantId, preserving property number/input order.
- Connection reference source is Invoker. This is a newly observed binding,
  not caller-to-participant authorization or ordinary-account proof; do not
  silently switch to owner credentials. Existing #18/#39-42 gates remain.
- Raw package is not committed. Sanitized observed definition preserves action
  logic/findings but removes creator/tenant/action metadata, site/list bindings
  and runtime authentication wrappers. It is not an importable replacement.
- Blocks 1/2 are configured; Block 3 remains CHANGES REQUIRED pending corrected
  saved/exported fields. No new tenant PASS or feature closure. Broader #47
  interruption/retry/duplicate/accepted-but-unfinished recovery remains open.

### REVIEW-RESP-20261107-03 - review2 export, one correction remains

- Source TandemRespondRequest-review2_20261107213618.zip; SHA256:
  4397df23d5dc40ee3fd1ae73ea27738b52766ba27abb7c223e7ff723ba3e0521.
  Modified UTC 2026-11-07T21:35:20.6910795Z.
- Compared definitions excluding metadata: exactly two changes, first input
  title corrected to ParticipantId and final request Choice path corrected to
  body('Read_final_request')?['Status']?['Value']. Required input order unchanged.
- RESP-REVIEW-002 and 003 resolved in this export. RESP-REVIEW-001 remains OPEN:
  Process_valid_response/True/Is_decline/True/Set_ContinueProcessing_2 still has
  value true, not false. No other change to the Decline branch observed.
- Counts remain 77 actions/depth 6, no missing action refs or non-sibling run-after
  refs, one response. Connection binding unchanged. This is static review only.
- Sanitized snapshot updated to the actual second export, preserving original
  findings/export fingerprint as history. Block 3 still changes-required until
  the final Decline stop flag is saved and inspected. No new feature work or
  tenant PASS. Existing local tests are not rerun for this evidence-only update.

### REVIEW-RESP-20261107-04 - saved Decline correction verified, Block 3 complete

- Owner supplied saved SetVariable Code view: ContinueProcessing Boolean false,
  run-after Set_ResponseSucceeded Succeeded. Its action identity matches the
  review2 Decline stop action; no new full export was requested or supplied.
- RESP-REVIEW-001 resolved by this scoped saved-action evidence. RESP-REVIEW-002
  and 003 were already resolved in review2. No outstanding corrections from this
  bounded static review.
- Reference uses review2 as exported base plus an explicitly recorded one-action
  overlay. Export hashes remain unchanged; no false post-fix ZIP provenance.
- Rechecked composed reference: 77 actions, depth 6, no missing action/sibling
  references, expected false stop flag/Choice Value/input label, five versioned
  writes and one response. Sanitization/diff checks passed.
- Blocks 1/2 configured and Block 3 configuration review complete. This is not a
  tenant scenario PASS. Full #11 app wiring, #6/caller/access and #47 retry/
  interruption/recovery acceptance remain open. PR #57 owner review is next.

### PREREQ-IMPORT-20261108-01 - generated disposable package prepared

- Owner approved one package-import experiment; no working flow/app change.
- Artifact: artifacts/import_probe/TandemImportProbe.zip, SHA256
  3471027d66ad42d733374af5bdc21e769bf067567244ff8e727e46b613bc89f2.
- One fresh flow resource suggests New, no API/connection dependencies. Power
  Apps (V2) has no inputs; Compose returns IMPORT_PROBE_OK and Response returns
  success/message. No SharePoint/read/write/notification/schedule actions.
- Archive CRC, five JSON entries and manifest paths checked. Original working
  export identifiers, site and account strings are absent. Readable definition
  and review JSON accompany the ZIP. Builder refuses existing-file overwrite.
- Initial restricted pytest: 22 existing passed, 4 new test setup errors caused
  by temporary-directory access. Permitted rerun: 26 passed, including 4 probe
  safety checks. This is local evidence, not a Power Automate run.
- OPS-003 tenant import/run NOT RUN; maker permission, legacy-import availability
  and policy unverified. User must select Create as new/TandemImportProbe.
- Expected actual run: success true and message IMPORT_PROBE_OK. No result
  inferred before owner reports the import/run. No #28 closure or blanket
  authoring/connection/ordinary-user capability promise.

### PREREQ-IMPORT-20261108-02 - OPS-003 tenant import/run PASS

- Owner reports package import succeeded. First run attempt said flow was off;
  owner subsequently ran it and supplied response action output: statusCode
  "200", body success true, message IMPORT_PROBE_OK.
- PASS (owner-reported execution evidence): generated connector-free package can
  import/run in the current environment/account. Original ZIP unchanged.
- Effective import availability proven here; exact assigned role/policy settings
  not inspected. SharePoint binding, ordinary users and complex flows not proven.
- Owner chose to retain legacy packages. No Dataverse/licence change.

### PREREQ-IMPORT-20261108-03 - OPS-004 read-only package prepared

- TandemSharePointImportProbe.zip plus readable definition/review JSON prepared.
  Fresh flow/API/connection resource identifiers; New flow, Existing connection
  mapping, no original account or connection identifiers copied.
- Requires one-time selection of the existing SharePoint connection. SharePoint
  HTTP action/owner connection was previously exercised; imported mapping is
  NOT RUN. Embedded owner source only, no participant authorization inference.
- One GET _api/web?$select=Id; response exposes only Boolean success and fixed
  message SHAREPOINT_IMPORT_PROBE_OK when ID is present. No list reads, business
  records, writes, notifications or automatic trigger.
- PASS local checks: 30 pytest, ZIP CRC/JSON and dependency mapping. OPS-004 tenant
  import/run NOT RUN. No #28 closure or business-feature acceptance implied.

### PREREQ-IMPORT-20261108-04 - OPS-004 tenant import/test PASS

- Owner supplied an import-screen image: new flow already green/Create as new;
  the unresolved row was the related SharePoint connection. Guided selection of
  the existing connection (Select during import), then Save and Import.
- Owner subsequently reports: "import succeed, test succeed". PASS is owner-
  reported import/manual execution, not independently inspected raw outputs.
  No claim that the exact response body/status was supplied for OPS-004.
- This demonstrates the generated package plus existing SharePoint connection
  can import/run for the owner in this environment. Expected operation remains
  the single read of site technical ID in the reviewed package.
- No ordinary-participant access, Power Apps identity binding, business writes,
  group workflow or full #28 reproducibility acceptance inferred.
- Both disposable probes passed at their stated scope; 30 local tests passed.
  Next is review/merge of the experiment batch, then the next feature batch.

## New run template

Copy this section for an execution. Record one row per case (or split a case into
named variants); use linked issue attachments for sanitized evidence when useful.

### RUN-YYYYMMDD-NN

- Date/time and timezone:
- Tester label and role (owner / ordinary A / ordinary B / admin):
- Environment and isolated fixture scope:
- App name and published version/time (or not applicable):
- Flow name and version/last-modified time (or unknown):
- Relevant repository commit / PR / issue:
- Preconditions/configuration verified:
- Fixture IDs, initial state and any reset steps (no real employee data):
- Known requirement changes since prior run:

| Test ID and variant | Action/input | Actual result | PASS/FAIL/NOT RUN/DEFERRED/REQUIREMENT PENDING | Sanitized evidence / related issue |
|---|---|---|---|---|
| | | | | |

- Comparison with catalogue Expected:
- Flow run time/reference and first failed action (if applicable):
- SharePoint records checked after actions:
- Test-record cleanup/reset performed (or intentionally retained):
- Remaining gaps and retest decision:

PASS applies only to that version, scenario and account role. An admin success
does not prove ordinary-user access. A local test does not prove live deployment.

## Recording a reported issue

Use the GitHub bug-report template or give the assistant the test ID, steps and
expected/actual results. For example: “REG-003 fails: blank time zone still causes
a required-field error in the published test app.” The assistant should locate
the test and relevant feature ticket, inspect version-specific evidence, fix on
the appropriate branch, and append retest results after verification.
