# Participant submission validation — #61

Status: **In progress; valid/no-change and Active correction/readback/follow-up passed; remaining acceptance and app feedback pending**.
The owner supplied the current export. Inspection confirms GetOnUpdatedItems,
one-minute recurrence, splitOn body/value, current Get_item using triggerBody ID,
four-field nonempty OR and changed-only Status patches. Catalogue validity and
conditional-write protection were absent. Prior REG-014/015 partial passes remain.
No live flow has been changed by the packaging work.

Package: artifacts/participant_submission/TandemParticipantSubmission-v2.zip;
readable .definition.json and .review.json beside it. Build **88637754-4c91-4833-9dcf-5116d8bfb77e**.
**26 action definitions / maximum nesting 3**; local suite **101 passed**.
Source export SHA-256 is in the review; the original ZIP remains local/untracked.
Generated package uses new flow IDs and an import-time existing-connection selector;
original tenant connection instance identifiers are not copied.

## Inputs, validation and outputs

The existing SharePoint created-or-modified event provides the Participants item
ID. Read that current saved item. Trigger fields are not authoritative profile
values. Actual list/field IDs are verified in tenant_schema_mapping.json (#66).
participant_submission_contract.json records the target machine-readable contract.

- A required existing Person account plus at least one of the four language/culture
  offer/interest lookups is valid. Culture-only and share-only are supported.
- Resolve every supplied lookup ID against its mapped catalogue and require Active.
  Reject unknown/inactive IDs; an empty optional Time zone is valid. A supplied
  Time zone must resolve. Do not validate display text as identity or lookup ID.
- Keep participation/openness independent. Paused, Inactive and No do not cause
  validation failure and must survive edits/corrections unchanged.
- Valid -> Status Active; invalid -> Status Needs review. Write **only Status**,
  only when changed. Never use a full-row update that maps identity or selections.
- Failed/malformed/incomplete reads fail the run; do not convert them into a
  successful validation or silently mark a profile invalid. No new output column.
- Protect the Status-only update against edits after the current-item read. Exact
  current-item ETag is used with IF-MATCH and no retry on POST/MERGE. A conflict
  fails the run; no unconditional wildcard write. No global cross-flow lock claim.
- Read back a necessary write. Follow-up event must skip it when unchanged.
  No group/member/request changes, rejoin, reopening or catalogue writes.

## Exact mapping and controlled import / recovery

| Binding | Value |
|---|---|
| Display name | Tandem – Participant submission v2 |
| Import setup for flow | Create as new; do not update/overwrite the working original |
| SharePoint connection resource | Select the existing working SharePoint connection |
| Site | https://reedelsevier.sharepoint.com/sites/OG-TandemOrg |
| Event list | Participants / fd3adf46-f81d-4a7b-a80c-567fde0175dc |
| Event | Existing trigger name, GetOnUpdatedItems, recurrence and splitOn preserved |
| Current item | triggerBody()['ID']; REST reads Id, Person/lookup IDs and Status |
| Catalogue lists | Language 3c1fcd2b-ce62-4af0-a96d-9b0d7502cb63; Culture cf7ed5b4-2e11-4a0a-a417-6c63ed60f614; Timezone 7beddfff-1881-4a82-8003-29933b836350 |
| Profile internal fields | Participantaccount, Teachlanguages, Learnlanguages, ShareCultures, LearnCultures, Timezone, Status |
| Catalogue fields | Id, Active; complete bounded reads up to 5000, fail if next page exists |
| Profile write | Status only plus REST entity metadata; no identity/availability mapping |
| App call | None: event-driven; no new .Run() call or immediate validation response |

The existing SharePoint connector and metadata HTTP capability were exercised by
#66. Conditional participant-row write and verbose response shapes require this
package's smoke test; local tests do not certify them in the tenant. No new
connection, permission, connector, licence or external runtime is proposed.

1. Keep the original exported ZIP and note the original flow name/on-state. Before
   importing the new event-driven flow, turn **off only the existing Participant
   submission validator** in My flows. Registration saves during this short window
   may await validation; avoid test/user edits until cutover smoke is ready.
2. Import TandemParticipantSubmission-v2.zip using the legacy Import Package path.
   Expand the Flow resource: **Create as new**. Map the SharePoint Connection
   resource to the existing connection. The API resource remains Existing.
3. Import. If any resource fails/skips unexpectedly, capture its exact expanded
   error. Inspect whether v2 was partially created and turn it off before restoring
   the original. Never leave both validators enabled. No new account/grant workaround.
4. Open v2 and verify site/list plus the existing SharePoint connection. Turn v2
   on if import left it off; confirm the original remains off. No manual action
   rebuilding, added concurrency control or Response action is required.
5. Run the minimal smoke below before resuming broader test edits. Keep the old
   flow disabled and retained until target acceptance/review, not deleted.
6. If smoke fails, capture failed action/error, turn off v2, then re-enable the
   original. This restores the prior validator behavior; it does not undo any
   completed Status write. Verify the test profile and re-edit it after recovery.

## Minimal owner smoke — first import gate

Use your existing permitted valid profile (at least one useful selection); note
its item ID, Comments, Status, participation/openness and selections first.

1. In the app, change only Comments to a temporary smoke note and Save. The
   event is asynchronous. Wait for the matching v2 run in Run history (one-minute
   polling can add delay); match the item ID, not merely the latest unrelated run.
2. Open **Validation report → Outputs**. Expect valid=true, status=Active and
   result=NO_CHANGE if Status was already Active; Update validation status Skipped.
   If Status needed correction, expect STATUS_UPDATED and a successful patch /
   readback, followed by a matching-item run with NO_CHANGE and update Skipped.
3. Reopen the saved item: identity, selections, participation/openness unchanged;
   only your Comment and any necessary Status change differ. Confirm no sustained
   repeated writes without new profile edits. No membership/group changes.
4. Restore the original Comment through the app; confirm normal validation. Return
   Validation_report JSON plus write/follow-up status, or the first exact import/
   action error. No need to run all negative cases before reporting first smoke.

Source checks and 101 local tests passed. The owner has imported v2 and passed
the valid/no-change, necessary Active correction/readback and follow-up sequence.
These smoke steps are retained for regression, not requested again. The pure
expression evaluator is local protection, not Power Automate execution.

## Detailed target tenant acceptance — after import/smoke

Account: existing permitted owner/synthetic fixtures; ordinary-user access remains
deferred. Version: the imported build above. The Active/no-op/correction/follow-up
portion is owner-passed; remaining variants below stay pending unless explicitly
recorded in TEST_RUNS.md.
Capture original item ID, identity, selections, Comments, Status and availability.
Use existing test profiles; never delete a real profile to force a new identity.

1. Valid language-only, culture-only and share-only profiles, including blank zone:
   create where a permitted distinct fixture exists, otherwise record creation
   blocked; edit existing profiles normally. Current item becomes Active.
2. Isolated test profile with all four empty: direct-list save bypasses App guard,
   becomes Needs review; follow-up write skipped. Restore useful selections;
   becomes Active once, then follow-up skipped. App guard is already #5 accepted.
3. With an isolated catalogue fixture, select it while active, then disable it and
   edit the test profile: Needs review. Unknown-ID negative test requires a safe
   supported injection/harness; don't corrupt live catalogue rows or fabricate a
   pass when SharePoint rejects the invalid lookup before validation can run.
4. Set Paused/No, edit Comments and save; repeat with Inactive. Match item ID and
   run reference; participation, openness, identity, selections and unrelated data
   remain unchanged. Only necessary Status patch occurs (PAR-002/003, REG-014).
5. Already matching Active and Needs review: both update branches skipped. Force
   each necessary Status correction on a permitted test item; observe one write
   followed by no-op. Repeated writes without user edits fail REG-015.
6. Read failure/concurrent edit: failed read or conflict never reports successful
   validation. Exercise only an isolated supported harness; no permission changes
   or deliberate production outages. Record untestable variants explicitly.

Expected evidence: package/build ID, item ID, trigger event/run reference, relevant
action status/changed-only payload, saved Status and preserved fields; redact
employee identity in repository artifacts. No exact run/version is invented.
Failure: preserve draft/profile evidence, identify first failed action. Sustained
self-triggered writes require stopping the new validator and restoring the prior
working flow through the documented cutover path.
Cleanup: restore profile/catalogue fixture originals and check final validation;
don't delete group/member rows. These detailed tests follow the owner's integrated
build-first priority; a delivered package can await scoped runtime results.

## Boundaries

REG case families retain historical partial results in TEST_RUNS.md. App #5/#6
acceptance does not certify catalogue enforcement or asynchronous validation
feedback. Inspect the existing feedback binding before changing UI. #41 protects
registration access; #7/#10 consume availability; #25 owns operational group
side-effect integration. Their tests are retained, not passed by this ticket.

## Current limitations and feedback integration

- Catalogue rows are validated against successful complete reads for that run. A
  later catalogue activity change does not itself trigger every participant; a
  later profile event revalidates. No catalogue-wide freshness sweep is promised.
- A concurrent participant edit causes HTTP 412 rather than retrying stale data.
  Inspect the later current-item run; no guarantee that a failed event healed itself.
- Status is asynchronous. Owner supplied Form1.OnSuccess = Notify("Registration saved", NotificationType.Success).
  No result binding was supplied. The bounded feedback changes below are prepared,
  not yet applied/tested. Do not present SubmitForm success as server validation.
- No target creation/invalid-branch/no-op-follow-up/access test is marked passed by
  local package generation. Ordinary-user access remains separately deferred.

References: [SharePoint ETag/conditional update](https://learn.microsoft.com/en-us/sharepoint/dev/sp-add-ins/working-with-lists-and-list-items-with-rest),
[SharePoint connector event and HTTP operations](https://learn.microsoft.com/en-us/connectors/sharepoint/).

## App feedback — bounded Studio handover, implementation pending

Owner supplied the complete OnSuccess formula as:
`Notify("Registration saved", NotificationType.Success)`.
It reports persistence, not the later validation result. No existing label formula
or explicit confirmation that there is no label was supplied. Inspect the screen
first; reuse an existing feedback label/button if present, otherwise add one pair.
No new data source or .Run() call is needed. The existing Participants connection
is already used by this app; these steps use only the last successfully saved ID.

1. In Studio select Form1 at the verified registration-form path. Replace its
   OnSuccess with artifacts/participant_submission/Form1.OnSuccess.powerfx. The
   supplied existing formula contains no navigation/reset to preserve. If the
   actual property now differs, preserve those additional behaviors before editing.
2. Outside the editable data cards, add/reuse a text label in the registration
   screen/container. Set Text to ValidationLabel.Text.powerfx. It reads the item
   identified by the last successful Form1 submission and displays only validation
   feedback; it neither changes identity nor exposes another profile.
3. Add/reuse a button labelled **Refresh validation**. Its OnSelect is
   RefreshValidation.OnSelect.powerfx. Set its Visible and the label's Visible to
   `!IsBlank(varValidationParticipantId)` so they appear after successful Save.
   Let Power Apps infer the variable type from the Set call; do not initialize it
   to text or change the Form's existing Default/Item/Update bindings.
4. Preview: save an ordinary valid edit. Expect the informational saved/background
   message. After the matching flow succeeds, click Refresh validation; label
   shows latest stored Active. With an isolated invalid direct-list fixture after
   a prior app save, its successful validation run plus Refresh shows Needs review.
   Restore originals. Refresh must not submit the form, write profile fields or
   change participation/openness. A failed read shows the load error message.
5. Save/publish the app after checking layout/formula errors; record its new Live
   version and scoped feedback results. Version 19 remains the last confirmed app
   version until the owner supplies this update. The package can be smoke-tested
   before this UI step; whole #61 acceptance remains pending.

The existing schema has no per-edit validation completion marker. Therefore the
label deliberately says **latest stored** and warns that it may reflect an earlier
edit. It never claims a particular save passed merely because an old Status is
Active. No timer, automatic retry or extra tracking column is introduced. Detailed
read-error/race and creation fixtures remain explicitly pending when unavailable.

## Current tenant evidence and next step

Owner visually confirmed the selected third row has SharePoint **ID 38**. The
original validator is off; only v2 is enabled. Identity, selections, participation
status and openness stayed unchanged on this profile.

| Run | Result | Scope |
|---|---|---|
| 08584074536792033395422259203CU09 | NO_CHANGE | Valid Active no-op |
| 08584074534387722777188625214CU11 | STATUS_UPDATED | Necessary Active correction/readback |
| 08584074534064918346698562621CU26 | NO_CHANGE | Subsequent no-write follow-up |

All reports match build 88637754-4c91-4833-9dcf-5116d8bfb77e / item 38. No repeat
of this passed sequence is needed. Raw reports and clarification are in results/;
chronological failed/pending/resolved notes remain in TEST_RUNS.md.

Next bounded implementation step is the Studio feedback handover above. Apply the
three prepared bindings, verify a valid save plus manual Refresh displays latest
stored Active, then Save/Publish and report the new Live version. No new import,
connection or schema change is required. Failed-read and Needs review feedback
variants retain their unexecuted status until actually exercised. Detailed negative
cases follow the owner's build-first priority; none are marked passed by deferral.

## Feedback layout handover — current owner progress

Owner accepted footer appearance after grouping existing ValidationLabel and
RefreshButton beneath Form1. This is a layout confirmation, not a functional
validation-feedback or publication result. Latest confirmed Live release stays 19.

Next align the white registration-panel header (not the top blue site banner).
Select its title, identify its actual parent in Tree view and use that existing
horizontal auto-layout container. Direction Horizontal; justify Start; vertical
alignment Center; height 56; gap 12; left/right padding 16. Give the title flexible
width / fill portion 1 / minimum width 0. My requests and Discovery use fixed
width 140 and height 36; Save/Cancel icons fixed 40 by 40. Order the title first,
then navigation buttons, then actions. Preserve other existing conditional action
controls and their bindings. If that parent has no Direction/layout properties,
inspect it before applying auto-layout settings; do not insert a guessed wrapper.

Preview narrower/wider: title readable, My requests single-line, navigation/actions
grouped right without overlap; footer text readable and Refresh accessible. Then
run the documented save/Refresh functional smoke and publish/report Live version.

## Current feedback evidence and changed-value check

Owner screenshot shows the complete latest-stored Active label; layout is accepted.
Owner confirms button click shows the Refreshing notification. This acknowledges
the click only: unchanged Active cannot prove changed server data was loaded.
The Refresh artifact now includes the observed notification before Refresh.
No new Live version has been reported (last confirmed 19).

One bounded next test combines the target invalid branch and changed-value refresh.
Keep the app open after saving own item 38 so the feedback uses its saved ID.
Capture exact original selections in Teach languages, Learn languages, Cultures
I can share and Cultures of interest. In SharePoint edit only those four fields
to blank on the same own item; Save. Wait for matching v2 run valid=false /
Needs review. In the app click Refresh validation and expect Needs review text.
Restore the exact four selections in SharePoint, leaving identity/participation/
openness untouched. Wait for v2 Active and click Refresh again; expect Active.
Return invalid-run Validation_report and both label outcomes (or first error).
Capture the invalid follow-up NO_CHANGE if present; do not infer it without a
report. Restoration is required even if the test fails. Do not alter shared
catalogue rows, other profiles, connections or permissions for this check.

## Changed-value refresh passed; final wording handover

Owner reports all directed empty-profile Needs review / restored Active and App
Refresh steps passed. Raw invalid-run report IDs were not supplied; this is bounded
owner evidence. No repeat needed merely to re-prove the label can reload Status.

Replace ValidationLabel.Text with the revised artifact. It displays:

    Last profile check: Passed
    Changes are checked after saving. Refresh for the latest result.

Needs review displays “Last profile check: Needs attention” with “Review your
profile details, save, then refresh.” Blank/legacy Status displays “Not yet
confirmed”; load errors display “Profile check unavailable. Try Refresh validation.”
Keep AutoHeight/Wrap enabled. “Passed” describes validation Status Active, not
ParticipationStatus: Paused/Inactive users can have a passed profile check.
No new per-edit completion claim, timer, schema field or behaviour is introduced.

Next: owner apply/accept the shorter wording, Save/Publish, and supply the new
Live app version. Last confirmed Live is 19. Invalid no-op follow-up, catalogue,
creation and failure/conflict target variants remain pending under their existing
gates; they are not marked passed by this wording or broader owner “all fine”.

## Final accepted label copy — supersedes earlier helper wording

Owner confirms the final copy is done. Passed displays only “Last profile check:
Passed”. Needs attention adds only “Review your profile details and save again.”
The normal result has no background, earlier-edit or refresh-helper sentence. Text
artifact is synchronized; underlying saved Status lookup/Refresh behavior remains.

Next owner step: Save/Publish and return the new Live version. Publication is not
inferred from wording acceptance; last confirmed release remains 19. Prior tests
retain their exact scope and remaining case gates are unchanged.

## Current release — owner-reported Live Version 26

Owner confirms Save/Publish complete and supplies Version 26. This completes the
feedback publication handover; no exact publish timestamp or separate Live-player
replay supplied. Earlier publication-pending notes are historical and superseded.
See version26.owner-report.json. Flow remains build 88637754-4c91-4833-9dcf-5116d8bfb77e.

Core item-38 flow/feedback/preservation results retain their bounded owner scope.
Remaining target cases: invalid follow-up no-op/report, catalogue negatives,
creation and failure/conflict plus unexecuted account/availability variants.
Retain these gates under build-first priority, not as delivered acceptance.
If available, retrieve the already-executed Needs review report and its next
matching-item follow-up from run history without making another profile edit.
#61 stays In progress and PR #72 draft while own acceptance remains incomplete.
