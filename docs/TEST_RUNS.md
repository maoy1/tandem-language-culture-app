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
| DISC-008 | DEFERRED / NOT RUN | #46/PR #59 approved display; live projection implementation/execution still pending |
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

### AUDIT-20261108-01 - #45 backlog/readiness metadata audit

- DOC-001 audit variant PASS: all 40 issues inventoried; 35 open bodies each have
  proposed experience, flow/readiness assessment, preserved AC and defined case
  references; remote GitHub reread verified exactly one lifecycle label each.
- 5 closed issues (#1-#4/#46) labeled Done for their historical/accepted scope.
  Open: 9 In progress, 8 Planned, 10 Blocked, 8 Deferred; none falsely marked
  whole-ticket Ready for review/testing. No issue state changed.
- Source snapshot and per-body before/after comparison retained locally; user
  edits were checked before mutation. Unrelated labels retained. #31's obsolete
  Paused-group wording corrected to Closed under the existing approved model.
- Added planned request/access/data/scale/handover/notification/Later test IDs.
  Existing local pytest rerun: 30 passed; configuration/package checks only.
  No new tenant runtime case executed/passed by this audit. Earlier registration,
  synthetic baseline and import-probe results retain their original scope.
- Branch codex/issue-45-flow-readiness-audit; actual production versions unknown
  unless recorded in earlier runs. No live app/flow/list/permissions changed.

### AUDIT-20261108-02 - #45 focused type/scope and activity correction

- DOC-002 metadata audit PASS: 48 issues accounted for; 41 focused open tickets,
  5 historical Done (#1-#4/#46), 2 Superseded (#22/#24) explicitly closed as
  not planned only after their successor bodies were published. No unfinished
  requirement is represented as delivered by retirement.
- Remote reread verified one focused type and one lifecycle label per issue,
  13 unique production-flow owners (12 core including provisional notification,
  one Deferred reminder), all 41 open proposed-experience/own-AC/test sections,
  and no active In progress issue while audit PR #60 awaits review.
- Eight successors #61-#68 created; every one of 246 original checklist items
  has an explicit active destination in config/ticket_scope_map.json. Partial
  work/evidence preserved as implementation history, not activity or PASS.
- Earlier AUDIT-20261108-01 counts/status meaning are historical and superseded
  for current tracking, not rewritten. No runtime test, app, flow, list or
  permission changed by this restructuring. New SCHEMA/UI definitions are NOT RUN.
- Existing local suite rerun: 30 passed (configuration/package tests only).
- This metadata PASS does not finish #45's MVP overview or any implementation.

### SCHEMA-20261108-01 - #66 owner schema audit and setup-v2

- Date: 2026-11-08, Europe/Berlin; exact local start times not supplied.
- Tester: owner, existing SharePoint connection; agent reviewed pasted outputs.
- No ordinary-participant account, new licence/role grant or participant row fixture.
- Audit build `1fd35100-e381-48b7-9d53-aa927d1131ed`, 73 actions / depth 5.
- Setup-v2 build `1080ab9d-fec5-4c42-92ef-4988bb36390f`, 47 actions / depth 4.
- Full raw participant metadata report remains in the owner chat; derived technical
  mappings/counts only in config/tenant_schema_mapping.json. No employee rows.

| Case/variant | Actual result | Status | Run reference/evidence |
|---|---|---|---|
| SCHEMA-001 initial metadata collection | collectionComplete true, errors []; 4 lists, no truncation; 28 language / 85 culture / 18 time-zone active values | PASS, inspection variant | 08584074638260638544180416987CU28 |
| SCHEMA-001 initial alignment | Account unique/required/indexed, four optional multi-lookups and optional single time zone correct; two availability fields missing, catalogue requiredness/time-zone key settings needed delta | NEEDS CHANGE, then bounded correction below | Derived tenant mapping; preserve IANA_ID display/legacy choices |
| Setup original import | InvalidConcurrencyConfiguration: Request trigger concurrency plus synchronous Response | FAIL, superseded by v2 | Failed build 850d5ca8-b2f3-491c-bed4-9c77996899ca; no execution/write claim |
| SCHEMA-002 v2 dry preview | applyRequested false; preflightReady true; DRY_RUN_READY; ManageLists checked on 3 affected lists | PASS | 08584074626663573896315130256CU26; results/dry-run.json |
| SCHEMA-002 v2 five-setting apply/readback | applyRequested true; preflightReady true; setupVerified true; SETUP_VERIFIED | PASS, bounded apply variant | 08584074626043544351187724959CU01; results/apply.json |
| SCHEMA-002 repeat result | applyRequested/preflightReady/setupVerified true, SETUP_VERIFIED again | PASS, final-state repeat; individual write skips unconfirmed | 08584074600200045376372808433CU02; results/repeat.json |
| SCHEMA-002 five-write skip trace | Need owner confirmation all five Create_/Update_ HTTP actions Skipped; summary has no action trace | PENDING confirmation | No extra run requested |
| SCHEMA-001/002 final whole-schema audit | Complete collection, errors [], all contract fields/defaults/requiredness/unique/index/lookups correct; normalized observed metadata analyzed Verified, no findings | PASS | 08584074601682073516023990276cU14; results/final-audit.metadata.json and final-audit.analysis.json |
| Local repository/package suite | 63 passed; ZIP/manifest checks, guards/readback, computed-Title/IANA/legacy metadata regressions, exact concurrency regression; max 500 actions / depth 8 enforced | PASS, local only | Agent pytest; not tenant execution of every error variant |

Five verified changes: ParticipationStatus required Choice default Active;
OpenToConnections required Boolean default Yes; language Title required;
time-zone Title required; IANA_ID required/indexed/unique. HTTP writes affect
field schema only, not participant rows/choices/permissions or working flows.
Successful readback is not whole-feature acceptance or new-form/save behavior.

No business records were created; required schema is intentionally retained.
Turn off disposable helpers after final evidence. Own schema acceptance is now passed; only delivery review/merge keeps #66 open; #5/#6/#61 and privacy tests are separate owners.

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

### SCHEMA-20261108-02 - pending screenshot/run correlation

Owner supplied a screenshot with Create ParticipationStatus green/Succeeded.
The screenshot does not show its run reference; the initial apply is expected to
create this field. Correlate its Setup_report.runReference before attributing it
to the repeat run or declaring a repeat failure/pass. No new run is requested.
The five-write skip trace remains unconfirmed; final-state repeat summary and
whole-schema audit evidence above remain separately scoped.

### SCHEMA-20261108-03 - #66 safe-repeat confirmation PASS

- Owner identified the earlier green-create screenshot as original apply run
  `08584074626043544351187724959CU01`; first-apply creation was expected.
- Owner ran the imported setup-v2 again and explicitly reported **all five writes
  Skipped**, `setupVerified: true`, `result: SETUP_VERIFIED`.
- Supplied screenshot shows Create ParticipationStatus and Create OpenToConnections
  grey/skipped and Apply setup succeeded. Other three write skips are owner-reported.
- Evidence: artifacts/schema_alignment/results/idempotency-confirmation.json and
  repeat-skipped.png. The new run reference was not supplied; do not reuse the
  earlier repeat reference for this screenshot. No further rerun is requested.
- **SCHEMA-002 safe repeat: PASS**. This supersedes the earlier pending trace and
  screenshot-correlation states while preserving their history. Initial metadata,
  permission preview, apply/readback and final full audit had already passed.
- All own #66 schema checks passed. Review/merge PR #69, then close #66. Ordinary
  app/flow/privacy tests remain separately owned. No business-row cleanup required.

### UI6-20261108-01 - #6 preparation and owner card-add checkpoint

- Branch codex/issue-6-participation-controls. Schema dependency #66 Done;
  PR #69 merged. Existing app/connection; no new permission or connector.
- Owner confirmed Form1 path and both availability cards added in Studio.
- Participation status shows Item 1/Item 2 sample items. Binding correction
  supplied: Items = Choices([@Participants].'Participation status'), display
  Value, single selection. Result not yet confirmed; save test paused.
- Local pytest: **79 passed** (16 new contract mutation/default-preservation
  checks plus existing 63). No Power Apps execution proof follows from local tests.
- UI6-001:006 / own PAR variants: NOT RUN. App saved/published version not supplied.
  First pending check: actual three Choice values, then save/reopen Paused/No
  without resetting identity/unrelated selections. No fixture cleanup yet.
- #61 revalidation / #7/#10 availability exclusion / #64/#68 derived membership
  integration portions remain separately owned; do not mark their outcomes passed.

### UI6-20261108-02 - #6 owner save-preservation PASS (bounded variant)

- Owner explicitly confirmed: real choices appeared, Paused/No persisted after
  saving, validation and reopening; participant account and selections unchanged.
- **PASS:** choice-binding correction and basic save/validation/reopen portion of
  UI6-002 / PAR-002 / REG-009. This supersedes the sample-choice issue, not every
  scenario in the full test catalogue. No new permission/connector introduced.
- App: Tandem Participant Registration, existing Form1; account role: owner.
  Exact app version/publish time, fixture item ID and flow run reference were
  not supplied. Publication is pending confirmation; do not call this a verified
  published-version run. No actual new-profile creation/default pass is claimed.
- **NOT RUN / unconfirmed:** UI6-001 new defaults/creation; UI6-002 second
  unrelated-edit cycle; UI6-003 Inactive; UI6-004 Active/No/Yes; UI6-005 language/
  culture fixture variants; UI6-006 group/membership side effects. Full #61/#7/#10
  integration acceptance remains with those owners. Prior local suite: 79 PASS;
  no rerun needed for this documentation-only evidence update.
- Continue with Studio Save/Publish to the existing audience and record its
  version/time. Keep #6 In progress until actual delivery/test context is recorded;
  hand remaining acceptance to testers after review rather than close prematurely.

### UI6-20261108-03 - #6 Version 16 delivery context

- Owner reported **Version 16**, timestamp **08/11/2026 15:34:26** after being
  directed to select the Live row in the app's Versions history. Record as
  owner-supplied context, not agent-observed history. Timezone Europe/Berlin.
- Publishing-start message: **2026-11-08 15:34:34**. Completion timestamp not
  supplied; do not turn the start timestamp into a completed-publish time.
- App/control context: Tandem Participant Registration, same existing Form1;
  no new permission, connection, licence, flow or app import artifact.
- Evidence: artifacts/participation_controls/version16.owner-report.json. No
  .msapp/export inspected. The UI6-20261108-02 core preservation PASS was reported
  before this version context; no extra published-player test is inferred.
- Implementation ready for PR #70 review. Remaining own test variants are
  UI6-001 defaults/creation; UI6-002 unrelated-edit cycle; UI6-003 Inactive;
  UI6-004 Active/No/Yes; UI6-005 language/culture fixtures; UI6-006 no unintended
  membership writes with a permitted fixture. Use Version 16's Live player after
  reload for tester handover. Mark unavailable fixture/integration cases blocked
  with the receiving owner, not passed. Separate #61/#7/#10/#64/#68 work stays owned.
- No code changed in this evidence update; previous local suite 79 PASS retained.
  After review/merge, #6 Ready for testing, not Done. No further field construction
  is known missing; report any failing test before changing bindings or defaults.

### UI6-20261108-04 - #6 new-registration default FAIL; correction pending

- Owner reported: for a new registration Participation status defaults to None.
  **FAIL: UI6-001 new-mode rendering / PAR-001 default portion.** Version 16
  is the latest supplied context; exact failing runtime/version not separately
  restated. Earlier Paused/No preservation PASS remains historical, not invalidated.
- Schema #66 had verified the Choice default Active, but that metadata did not
  prove this app selector's New-mode initialization. Prior local tests do not
  execute Power Fx or catch runtime card/control binding failures.
- Correction supplied for the outer data card Default: Form1.Mode New returns
  LookUp(Choices([@Participants].'Participation status'), Value="Active"); Edit
  returns ThisItem.'Participation status'. Both branches return Choice records.
  Formula is retained as ParticipationStatus.Card.Default.powerfx.
- Apply/retest still pending: New displays Active; existing Paused remains
  Paused; saved Paused/No remains unchanged; new openness displays Yes. Keep
  inner selector binding until its actual property/type indicates otherwise.
- #6 returns In progress and PR #70 draft. Do not claim the defect fixed, publish
  a new version number, or restore Ready labels until owner correction evidence.

### UI6-20261108-05 - #6 outer-card default attempt still FAIL

- Owner applied the supplied outer-card Default change, saved and ran the app,
  but still could not see default Active. **FAIL remains UI6-001.** Corrected app
  version/control property evidence not supplied; no fix PASS claimed.
- Next required evidence: inner selector control type and actual Default or
  DefaultSelectedItems formula, plus New-button OnSelect. Modern/classic controls
  require different default value shapes; do not guess an additional override.
- Source contract checks now require explicit New-mode card initialization with
  a Choice record and preserved stored record on edits. **82 local tests passed**;
  these guards still do not execute Power Fx or prove UI selection initialization.
- #6 is In progress; PR #70 is draft again. Earlier Paused/No edit-preservation
  PASS remains historical and must be retested if a default binding changes.

### UI6-20261108-06 - corrected Combo box default and own UI acceptance PASS

- Screenshots identified the selector as Combo box DataCardValue2 and its parent
  default as Record. Earlier formulas mixed text/Record or targeted the legacy
  Default property. Final working bindings: outer card Default =
  ThisItem.'Participation status'; inner Default = Blank(); inner
  DefaultSelectedItems = If(Form1.Mode=FormMode.New, Filter(Choices(...),
  Value="Active"), [Parent.Default]). Both branches return tables of Choice records.
- Owner confirmed Active now appears and explicitly verified (a) new Active/open
  Yes and edits preserving saved choices, (b) language/culture-only save/reopen
  without identity or unrelated-value changes. **Own #6 UI criteria PASS**, owner
  reported. Exact detailed per-state sequences/fixture IDs were not supplied.
- Owner supplied **Version 19** in response to Save/Publish and corrected Live
  version request. Exact save/publish time not supplied; do not reuse Version 16's
  timestamp for the correction. Evidence: version19.owner-report.json.
- This supersedes UI6-20261108-04/05 failures for the corrected controls while
  retaining their history. Existing Paused/No baseline save/validation/reopen
  evidence remains scoped; it is not full #61 acceptance.
- Receiving integration checks remain pending: #61 current validation preservation,
  #7 Discovery exclusion, #10 stale/unavailable request rejection, #25 group side
  effects with an operational fixture and #64/#68 derived displays. All were
  retained in participation_integration_handoffs.json and receiving issues; no test
  was marked passed by transfer. Their Planned/fixture gates are explicit blockers
  for those integration variants, not a reason to keep the UI-control ticket open.
- PR #70 review/merge remains for #6. No new role grant, connector, paid runtime,
  group/member write or manual row fabrication. Local checks recorded separately.

- Version 19 contract/package regression suite: **84 pytest passed**. Checks
  reject record/text initialization policy where the Combo box requires a table;
  this remains local contract protection, not Power Fx execution.

### CLOSE6-20261108 - #6 completed; #5 current-release form checks start

- PR #70 merged at 8f974f8d35af4be6546ca74daa0bc94e2b950f32; #6 already closed
  when inspected, lifecycle label corrected from Ready for review to Done.
- Own Version 19 UI acceptance and working bindings remain as reported. Flow/
  group integration cases stay open with #61/#7/#10/#25; no new PASS by closure.
- #5 starts on codex/issue-5-registration-form. Existing evidence: historical
  REG-005 Preview guard and language multi-lookups, #66 schema/85 culture values,
  owner culture-only save/reopen/identity preservation under #6. No rebuild yet.
- Version 19 check A (blank optional zone + all-four multi-lookups persistence)
  and B (empty guard retains input/no write) requested: **NOT RUN** until owner
  returns actual results. No backend inactive-ID/eligibility/privacy PASS inferred.
- No production code changed for this tracking/test-handover update. Existing
  84-test local suite result retained; repeating it would not test the actual app.

### UI5-20261108 - Live Version 19 registration-form acceptance

- Owner answered the requested A/B handover: **“A and bo passed”**, interpreted
  as both A and B passed. Evidence: artifacts/registration_form/version19.owner-report.json.
- A **PASS (owner report)**: two selections in each of four language/culture
  selectors persist after Save/reopen; Time zone blank; identity unchanged.
  Covers App portions of REG-003/007/009, not all backend variants of those cases.
- B **PASS (owner report)**: clearing all four, entering a temporary Comment and
  clicking Save shows the required-selection message; draft values remain visible
  and the saved item stays unchanged. Covers REG-005 UI guard in this release.
- Earlier culture-only/identity/unrelated-value evidence under #6 remains valid
  within its recorded scope. No new code/app rebuild was needed after A/B.
- Cleanup was requested (cancel B, restore original values); not separately
  reported. Exact test timestamp, fixture IDs and independent source/runtime
  inspection were not supplied. No additional detailed guide step is inferred.
- #5 own App acceptance is ready for review; issue stays open until merge.
  #61 validation/catalogue enforcement, #7 blank-zone eligibility/availability,
  #10 stale-request checks, #41 protected integration and #25 group-side-effect
  tests retain their prior pending/blocked status. No PASS by scope transfer.
- Documentation/deployment metadata only: JSON parsed and diff checked; prior
  84-test code-suite result retained, not rerun or presented as tenant UI proof.

### CLOSE5-START61-20261108 — merged form acceptance; validation preparation

- PR #71 merged at b80f0529590f9212a1ac382a03d1af3a44db37af; #5 closed,
  lifecycle corrected to Done. Version 19 A/B results retain their owner scope.
- #61 is the sole In progress ticket on codex/issue-61-submission-validation.
  Target contract/test handover prepared; current source export requested.
  No matching current submission export found in either local checkout and no
  connected tenant-flow read tool is available. No replacement package/live edit.
- Target catalogue/failure/concurrency/feedback cases remain NOT RUN. Historical
  REG-014/015 results remain scoped. Package action/nesting counts cannot yet be
  measured; delivery gate remains 500 actions / 8 nesting levels.

### BUILD61-20261108 — current export inspected; package prepared

- Owner supplied Tandem–Participantsubmission_20261108154030.zip. Its exact
  trigger/current-item mapping and existing changed-only Status branches reviewed.
  Missing catalogue validation and conditional update protection added to v2.
- Build 88637754-4c91-4833-9dcf-5116d8bfb77e: **26 action definitions / depth 3**.
  Trigger/recurrence/splitOn/site/list preserved; original connection instance IDs
  replaced by existing-connection import mapping. Original export untracked/local.
- Complete verbose reads parsed strictly; unknown/inactive IDs produce Needs
  review, blank zone allowed, changed Status-only MERGE uses exact ETag/no retry;
  failed/malformed/incomplete reads and failed readback cannot emit success.
- **101 pytest passed** (17 new tests); JSON/artifact structure/diff checked. Pure
  policy evaluation is local, not import/runtime evidence. No target tenant PASS.
- Exact cutover/smoke/recovery and deferred detailed cases documented. Actual
  Form1.OnSuccess/validation label requested before feedback integration. #61
  stays In progress: import/smoke, feedback and target cases pending.

### UI61-PREP-20261108 — actual save notification inspected

- Owner supplied Form1.OnSuccess: Notify("Registration saved", NotificationType.Success).
  No validation-label formula was supplied. Do not infer a missing label or edit
  any unknown existing navigation/reset behavior.
- Prepared informational OnSuccess, last-saved-ID latest Status label and manual
  Refresh formulas. Studio application, formula/layout verification, new Live
  version and owner feedback acceptance are **NOT RUN**. Last confirmed app is 19.
- No per-edit completion marker exists, so latest stored Active does not prove
  the newest edit finished validation. Feedback text preserves that distinction.
- No runtime Python/extra connector or schema field added. Local suite remains
  101 passed from BUILD61; static Power Fx handover is not Power Apps execution.

### RUN61-20261108-01 — valid Active no-change smoke PASS

- Owner pasted Validation_report for build 88637754-4c91-4833-9dcf-5116d8bfb77e,
  run 08584074536792033395422259203CU09, participant item 38.
  Report retained in artifacts/participant_submission/results/valid-no-change.owner-report.json.
- **PASS (owner report)**: valid=true, status=Active, statusChanged=false,
  result=NO_CHANGE. Target package ran successfully through catalogue/current-item
  validation and the no-change branch for this profile. Import/run is established;
  no independent inspection of import settings or disabled original is inferred.
- The Status-write branch was not exercised. Conditional MERGE permissions,
  changed-write/readback, necessary-write follow-up no-op, invalid/missing IDs,
  failure/conflict handling, creation and identity/availability preservation remain
  pending target cases; no full REG/PAR family PASS is inferred.
- Owner has not yet explicitly confirmed original validator off, v2 saved-field
  preservation or application/publication of prepared feedback formulas.
- Next bounded case: keep item 38's valid selections, change only validation Status
  to Needs review in the permitted Participants list, observe v2 restore Active,
  successful patch/readback and follow-up NO_CHANGE. Do not change Participation
  status. Compare identity/selections/availability; retain original data.
- No production code or package changed. Prior 101-test local result retained;
  JSON and diff checked for this evidence-only update. #61 remains In progress.

### RUN61-20261108-02 — necessary Active correction/readback PASS

- Owner supplied matching build 88637754-4c91-4833-9dcf-5116d8bfb77e,
  run 08584074534387722777188625214CU11, item 38: valid=true, Status Active,
  statusChanged=true, STATUS_UPDATED. Exact report in
  artifacts/participant_submission/results/active-correction.owner-report.json.
- **PASS (owner report)**: target necessary Status-write path and successful
  readback for the tested profile. Validation_report is reached only after
  Update_validation_status, Verify_status and Require_status_readback succeed.
- Initial NO_CHANGE run preceded this correction; it is not the post-write
  follow-up. Follow-up NO_CHANGE/update Skipped remains pending. No sustained-loop,
  independent field-preservation or original-validator-disabled pass inferred.
- Invalid/unknown/inactive selections, creation, failure/conflict, and applied/
  published app feedback retain prior pending states. No full REG/PAR case family
  or whole #61 completion claimed. No new import, package or app change required
  to inspect the already-triggered next matching-item run.
- Evidence/metadata only: JSON and diff checked; prior 101 local tests retained,
  not rerun. #61 remains In progress; PR #72 remains draft.

### RUN61-20261108-03 — Active correction follow-up no-op PASS

- Owner returned the requested subsequent run after the STATUS_UPDATED run:
  08584074534064918346698562621CU26, item 38, same build
  88637754-4c91-4833-9dcf-5116d8bfb77e; valid=true, Active,
  statusChanged=false, NO_CHANGE. Raw report retained in
  artifacts/participant_submission/results/active-correction-followup.owner-report.json.
- **PASS (owner report)**: observed Active correction -> readback -> requested
  follow-up no-op, following RUN61-20261108-02. This is the target REG-015 Active
  correction/follow-up portion; it does not certify global loop/race safety or
  the invalid/Needs review branch. Exact timestamps not supplied.
- Original-validator disabled state and preserved identity/selections/availability
  still lack explicit owner confirmation. App feedback application/publication,
  invalid/catalogue/creation/failure/conflict target cases retain pending scope.
- No package/code change; JSON parsed and diff checked. Prior 101 local tests
  retained, not rerun. #61 In progress; PR #72 draft. No repeat edit needed for
  this now-passed Active correction/follow-up sequence.

### CORRELATE61-20261108 — v2-only confirmed; selected-profile ID mismatch

- Owner confirms original validator off and only v2 enabled: cutover confirmation
  accepted. Owner also confirms identity/selections/participation/openness unchanged,
  but corrects the selected profile to item 3 and says they do not have item 38.
- All three supplied raw Validation_reports explicitly contain itemId 38. Preserve
  them unchanged. Their run-level outcomes remain as reported; do not silently
  rename them to 3 or treat them as correlated to the selected profile.
- Earlier item-38 attribution to the intended edited fixture was provisional and
  is now unresolved. Field-preservation statement is retained for the owner-selected
  profile, without claiming correlation to the reported runs. Clarify built-in
  SharePoint ID versus third row/profile before end-to-end fixture acceptance.
- No new edit/rerun requested until identity correlation is clear. No duplicate
  validator, flow mapping fault or corruption inferred solely from the mismatch.
- Evidence: results/owner-cutover-and-correlation.json under participant_submission.
  #61 remains In progress, PR #72 draft; no code/package changes or pytest rerun.

### CORRELATE61-20261108-RESOLVED — 3 meant third row

- Owner clarifies **the third row**, not built-in SharePoint ID 3. The apparent
  item-3/item-38 discrepancy is resolved by this clarification. Raw run reports
  retain itemId 38; no source report was changed or relabelled.
- Accept the owner preservation confirmation for the selected/tested profile:
  identity, selections, participation status and openness remained unchanged.
  Original validator off / only v2 enabled is already explicitly confirmed.
- Target Active correction/readback/follow-up and bounded preservation portions
  now pass on owner evidence. The SharePoint ID column itself was not independently
  inspected; no broader multi-account or privacy proof follows.
- No rerun is needed for this passed sequence. Applied/published app feedback,
  invalid/catalogue/creation/failure/conflict cases retain their pending scope;
  #61 In progress, PR #72 draft. Earlier unresolved-correlation notes are history.
- Evidence metadata/docs only; JSON parsed/diff checked; prior 101 local tests
  retained. No package, flow, app or permission change.

### UI61-NEXT-20261108 — ID visually confirmed; feedback handover continues

- Owner displayed SharePoint ID and confirms the selected third row is item 38.
  Correlation is now visually owner-confirmed, beyond the earlier row clarification.
  No new run needed; the supplied sequence and preservation confirmation match.
- Next bounded #61 implementation step: existing prepared Form1.OnSuccess,
  latest-stored validation label and Refresh button. Only original save notification
  has been observed so far; Studio application/layout/formula test, publication,
  new Live version and scoped feedback result remain pending. Version 19 remains
  the last confirmed published app version. No tenant action taken by agent.
- Guide reconciled to current smoke results; historical notes retained here.
  Remaining detailed negative cases remain unexecuted, respecting build-first
  priority; no full acceptance or Ready/Done claim. Metadata/docs-only change;
  JSON/diff checked, prior 101 code tests retained without rerun.

### UI61-LAYOUT-20261108 — feedback footer appearance accepted

- Owner supplied tree showing Form1, ValidationLabel and RefreshButton as siblings
  under MainContainer1. Guided moving label/button into a horizontal footer below
  Form1, with flexible label width/wrapping and fixed button width.
- Owner replies “looks good, continue”: **PASS for owner-accepted footer appearance
  only**. Exact resulting properties were not independently inspected. No applied
  Status-text/Refresh functional test or new published version supplied.
- Next guided step: align white registration header using its actual title's
  parent container; fixed-width navigation/actions, flexible-width title. Preserve
  existing action and visibility bindings. No live change performed by agent.
- Evidence: results/feedback-layout.owner-report.json. #61 In progress; PR #72
  draft; runtime feedback and remaining scoped negative cases remain pending.
  Evidence/docs only; JSON/diff checked; 101 local code tests retained, not rerun.

### UI61-REFRESH-20261108 — Active label and click acknowledgment observed

- Owner screenshot shows full latest-stored validation Active text and Refresh
  button after footer layout work; owner accepts other header arrangement.
  Actual header parent SelectedRecordHeaderContainer1 observed in supplied tree.
- Label1 formula is Signed in as plus User().Email; guided hide duplicate header
  identity label because top blue banner already shows it. Exact hidden state not
  separately confirmed. Existing action/visibility logic otherwise retained.
- Owner confirms the added “Refreshing validation status…” notification appears
  on clicking Refresh. This proves the action fires, not that changed server data
  was fetched. An unchanged Active label was previously over-described as a
  feedback PASS; that claim is qualified here. Changed-value refresh proof pending.
- Refresh artifact synchronized to the owner-applied Notify; Refresh sequence.
  It acknowledges a request, not completed validation or a successful data read.
- Next one bounded owner test: capture four original lookup selections for item
  38, clear them through SharePoint (bypassing App guard), wait for v2 Needs review,
  then click App Refresh and observe Needs review. Restore original selections,
  wait for Active, Refresh again. Preserve identity/availability. No new import.
- New Live version not supplied; last confirmed 19. #61 In progress / PR #72
  draft. No code/package change; JSON/diff checked, prior 101 local tests retained.

### UI61-TRANSITIONS-20261108 — changed-value refresh owner PASS; wording revision

- Owner responds “all fine” to the directed item-38 clear-four-selections -> v2
  Needs review -> App Refresh Needs review -> restore exact originals -> v2 Active
  -> Refresh Active check. **PASS (owner report)** for that invalid/restore and
  changed-value UI sequence. Raw invalid Validation_report/run IDs not supplied;
  no invalid no-op follow-up or catalogue-negative proof inferred.
- Owner quotes the full latest-stored Active/background/earlier-edit text and
  finds it confusing. Revised Text artifact only: “Last profile check: Passed” or
  “Needs attention” / “Not yet confirmed”, plus one short contextual helper line.
  Data lookup, status selection and Refresh behavior unchanged. “Last” preserves
  the existing limitation: this is not a per-edit completion marker.
- Shortened wording application/appearance acceptance and new Live version not
  yet supplied. Last confirmed published app remains 19. #61 In progress / PR #72
  draft. No new import/flow/schema/permission change. JSON/diff checked; no new
  tests for this low-impact copy/evidence change; prior 101 local tests retained.

### UI61-WORDING-FINAL-20261108 — final copy applied/accepted

- Owner rejects all background/earlier-edit/refresh explanatory text on the normal
  result and confirms “ok, done” after final wording guidance. Accept as owner
  application/wording confirmation: “Last profile check: Passed” alone. Invalid
  result: “Last profile check: Needs attention” plus “Review your profile details
  and save again.” Keep existing Refresh button and prior tested data binding.
- Text artifact synchronized; no normal-result helper line. Lookup/error handling
  and validation/availability separation retained. This is presentation copy only,
  not a new validation-completion marker or tenant-flow change.
- Save/Publish/new Live version still pending. Latest confirmed release remains
  19. Prior changed-value Refresh and invalid/restore owner passes retained; other
  scoped cases retain existing pending gates. #61 In progress / PR #72 draft.
- JSON/diff checked. No tests added/rerun for copy-only change; prior 101 local
  code tests retained. No whole-ticket completion claimed.

### UI61-LIVE26-20261108 — feedback release published, owner reported

- In response to Save/Publish and Live-version request, owner confirms done and
  supplies **Version 26**. Accept as Live publication evidence for Tandem
  Participant Registration with final feedback wording. Exact save/publish times
  not supplied; no timestamps copied from earlier Version 16/19 releases.
- Versioned evidence: artifacts/participant_submission/results/version26.owner-report.json.
  Existing Preview changed-value Refresh/invalid-restore, wording/layout and target
  flow sequence passes retain their scope. No separate Live-26 replay reported.
- Original validator off / only v2 and profile ID 38 correlation/preservation
  remain confirmed. No new flow build/import necessary for the copy publication.
- Target invalid follow-up, catalogue negatives, creation, failure/conflict and
  unexecuted account/availability variants retain pending/fixture gates. #61 stays
  open/In progress; PR #72 draft. No whole acceptance or broader access claim.
- Evidence/deployment metadata only; JSON and diff checked; 101 local code-test
  result retained without rerun. A passed Preview variant is not retroactively
  labelled as a separately executed Live-version test.

### HANDOVER61-20261108 — owner requests merge and Ready for testing

- Owner explicitly prefers moving on and asking others to test rather than
  personally completing #61 acceptance. Prepare #72 merge and testing handover.
- Implementation is imported/owner-smoked, final feedback published Live 26;
  101 local tests and 26 actions/depth 3 remain recorded. No code/package change.
- TEST_HANDOVER_61.md (historical filename; handover now in [#61](https://github.com/maoy1/tandem-language-culture-app/issues/61)) records passed owner cases, remaining target variants,
  operator versus authorized app-tester roles, exact steps/outcomes/cleanup,
  reporting and access/fixture/harness blockers. No send/invitation/grant action.
- Lifecycle Ready for testing; issue remains open, not Done. Counts retain 38
  open / 10 closed / 8 Done, WIP 0. Merge does not turn unexecuted tests into PASS.
- Ordinary-user access not implied by publication. Already authorized testers may
  use their own profiles; unavailable/unverified access is a blocked case under
  #39/#40/#41. Detailed tests handed over, not silently removed from #61 scope.
- JSON/diff checked for handover-only changes; prior 101-test result retained.

### COMP9-BUILD-20261108 — shared source and isolated synthetic proof

- #61 remains Ready for testing after merged #72; next #9 is sole In progress
  on codex/issue-9-compatibility-rules. No #61 pending acceptance marked passed.
- Owner says Any language is nice-to-have and not to consider it now. Defer
  wildcard/exact-sentinel matching: drop known sentinel from matching role arrays,
  reject as group focus, keep concrete choices; no catalogue/registration change.
- Maintained Expr source emits normalization/person/group rules. Typed adapters
  require complete active catalogues, canonical identities and explicit server
  group sharer-availability evidence; no app identity/availability assumed trusted.
- 39 independently specified expected cases pass locally; generated WDL-subset
  runner checks emitted normalization/loop/ref scoping as well as source evaluation.
  Strict malformed/duplicate input guards and package/runtime boundaries tested.
- **121 pytest passed** (20 new tests). Proof 57fa2bc6-2b02-4068-9999-fe46f3747d4a:
  **45 action definitions / maximum depth 4** (limits 500/8); largest generated
  expression 2800 characters. Source/fixture/package hashes in review metadata.
- Proof has zero connectors/live inputs/tenant reads/writes, no Response/trigger
  concurrency combination and no Terminate inside foreach. No employee data.
- Tenant import/run **NOT RUN**. No production consumer, caller authority,
  paging/scale or ordinary-user group availability pass inferred. Full current
  test handover and verification boxes are directly in issue #9; production
  #7/#10/#11/#17/#65 own their integration; #12 actual group mapping, #47 writes.

### COMP9-RUN-20261108 — matching-build 39-case tenant proof PASS

- Owner supplied Proof_report summary: kind TandemCompatibilityProof, rules v1,
  build 57fa2bc6-2b02-4068-9999-fe46f3747d4a, source SHA
  dfe0dcd587a5a348080dde288183ed3dff2d02d1f652f0ae23010b2e6e649c72,
  run 08584074461495133197897516907CU19. Build/source/hash match generated artifact.
- **PASS (owner report)**: testCount=39, allPassed=true, failedCases=[], synthetic
  only, connectors=0, writes=0. Summary retained in results/proof39.owner-report.json;
  full per-case result objects not supplied/requested. Proof source requires all
  case equality results and exact case count before allPassed=true.
- Check corresponding 39 synthetic verification boxes in #9. All passes bounded
  to this isolated proof; no production reader/caller/availability/projection/
  pagination/request or atomic-admission acceptance inferred for consumers.
- #9 Ready for review, PR #73 ready, own scope finishes on review/merge; consumer
  tickets do not hold it open. #61 remains Ready for testing. No further owner
  proof rerun requested. No production/schema/profile state changed by proof.
- Evidence/docs only; JSON/diff and source hash checked. Prior 121 local tests
  retained, not rerun for report/status changes. WIP 0; no issue closed yet.

### CLOSE9-START47-20261108 — bounded coordination/reference and preflight

- PR #73 merged at 6879bd90b1321a695143bd327e3aa3a52e9eece2; #9 closed, label
  corrected to Done. #61 remains Ready for testing; separate cleanup #74 still open.
- #47 sole In progress on codex/issue-47-bounded-coordination. Proposed shared
  group token + immutable intent/result receipts, stable duplicate keys, terminal
  CAS and completion/readback gates; no native schema/data/permission change.
- **152 pytest passed** (31 new tests), including all **70 order-preserving
  last-slot reference schedules**, terminal/cancel races, partial setup/retry,
  receipt failure, episode history/capacity/state and unique committed event tests.
- These are isolated reference scenarios assuming atomic CAS/native uniqueness,
  trusted complete adapters, common-writer guard and known stopped retry boundary.
  They do NOT establish native SharePoint multi-item/cross-flow certification.
- Read-only preflight ffd55bdf-ce46-4327-96bc-9e0cddc09ecd: **5 actions / depth 1**,
  only web identity/effective permission metadata GETs. No fixture created and no
  live data read/write. Existing SharePoint mapping selected at import. **NOT RUN**.
- Native fixture setup/permission/unique-key/CAS/race and unknown-write recovery
  still gated; future proposed metadata not applied. NOT-002 delivery remains
  with #49/#21 channel/idempotency proof, beyond unique committed event identity.
- Current handover is inline in #47 with checkboxes, expected report/errors and
  explicit next native-fixture gate. #47 not Ready/Done; draft code/design review.

### COORD47-PREFLIGHT-20261108 — permission metadata gate PASS

- Owner report matches preflight build ffd55bdf-ce46-4327-96bc-9e0cddc09ecd,
  run 08584074437966574454125674321CU01. permissionMetadataCollected=true,
  fixturePermissionGatePassed=true; view/add/edit/manageLists all true.
  readOnly=true, fixtureCreated=false, writes=0. Exact summary retained in
  artifacts/coordination/results/preflight.owner-report.json. No native fixture
  or production coordination PASS follows solely from permission bits.

### COORD47-NATIVE-BUILD-20261108 — tagged fixture package prepared

- Build 8b82de6a-95e7-40fc-aaff-d066b168442b / Tandem47Fixture_8b82de6a95e740fc.
  **321 action definitions / depth 6**, within 500/8. Ten native checks packaged;
  default Run fixture writes=false. Explicit boolean Yes rechecks actual rights
  and creates/reuses only the exact full-build-tagged synthetic list/schema.
- No production list/app/permission mutations or deletes. Fresh per-run prefixes;
  no repair of nonempty tampered schema. Exact ETag on every data MERGE; metadata
  wildcard limited to empty verified-fixture Title settings. No row data from
  employee/production lists. Synthetic list remains for inspection/explicit cleanup.
- **165 pytest passed**. New simulations exercise generated references/HTTP shapes,
  both writer orders, metadata-only and string-true no-write cases, tagged schema
  reuse/fresh prefix, foreign-tag collision, revoked rights, schema tampering,
  failed absence-read handling and receipt failure retaining ownership.
- Fake-service simulations caught/fixed a fake default-value bug and tightened
  real collection read checks: failed GET is never equivalent to a verified empty
  collection. Final package/hash reflects the corrected guards, not earlier
  unpublished generated builds. JSON/diff checked.
- Native import/run **NOT RUN**. Selected primitive/independent-branch races and
  an intentional handled non-I/O failure/known-prefix replay are distinct from a
  genuine network-unknown/killed-run proof. No external delivery or production
  mapping/authority certification. #47 stays In progress; PR #75 draft.


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
