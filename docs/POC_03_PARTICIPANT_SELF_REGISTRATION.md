# POC-03 participant self-registration

This document defines the registration contract for the Participants list.
It records the tested language-registration baseline. Target v0.2 changes are
tracked in #45/#46/#5/#6: culture-only and combined participation, independent
participation/validation and optional time zone need implementation
and fresh tenant tests. JSON/schema now describe the desired POC-05 culture/optional
time-zone delta, explicitly pending deployment; this historical evidence remains
limited to the original language-registration baseline. Use
[POC_05_CULTURE_REGISTRATION.md](POC_05_CULTURE_REGISTRATION.md) for the delta.
One-time schema alignment has since been automated/verified under #66. The
current #6 Studio update is documented below; flow ZIP import does not establish
automated app editing. Historical registration evidence stays separately scoped.

The machine-readable contract is
[`config/participant_registration.json`](../config/participant_registration.json).
The local validator checks it against
[`config/sharepoint_schema.json`](../config/sharepoint_schema.json).

## Intended user experience

1. An authenticated company colleague opens the registration form.
2. The form identifies the signed-in colleague from their Microsoft 365
   account. They must not type an email address or select another person.
3. If no profile exists, the form creates one.
4. If a profile already exists for that account, the form opens that profile
   for editing instead of creating a second item.
5. The app opens and edits only the signed-in colleague's profile. They do not
   need administrator approval to register or update it. Direct SharePoint list
   access is a documented limitation of this POC.
6. The submission flow validates the profile and maintains `Status` as
   described in `CURRENT_DESIGN.md`.

## Current #6 app change - participation controls

Issue #6 is **Ready for review** in PR #70; remaining cases go to Ready for testing after review/merge. #66 schema/mappings/own tests are complete, PR #69
merged and #66 closed. Owner confirmed both cards added, real Participation status choices displayed,
and Paused/No persisted after saving, validation and reopening; account and
selections stayed unchanged (UI6-20261108-02). Owner reported **Version 16**,
saved **2026-11-08 15:34:26 Europe/Berlin**, after the requested Live-version
check. Publishing started at 15:34:34; completion time was not supplied.
The owner check preceded the version report; do not relabel it as a separately
observed published-player retest. Remaining UI6 variants are not passed.
Current form path confirmed by the owner:
`MainScreen1 > ScreenContainer1 > BodyContainer1 > RightContainer1 > MainContainer1 > Form1`.

### Smallest supported Studio update

1. Open the existing **Tandem Participant Registration** app in Studio. In
   **Data**, refresh its existing **Participants** data source. This uses the
   existing connection/edit access; do not add a new connector or permission.
2. Select **Form1** at the path above. Choose **Edit fields > Add field**.
   Select **Participation status** and **Open to new connections**, then Add.
   Actual internal names are `ParticipationStatus` and `OpenToConnections`.
3. Verify the generated controls. If Participation status shows Item 1/Item 2,
   select its dropdown/Combo box inside the card, choose **Items** beside the
   formula bar, and set `Choices([@Participants].'Participation status')`.
   Display the **Value** field and allow a single selection. Expected choices:
   Active, Paused, Inactive. Keep the card DataField `ParticipationStatus` and
   its selected-record Update binding; do not replace it with a text input.
   The openness card is a Boolean Yes/No control. Both inherit
   the form's display mode. Use the app's existing Edit/pencil action to edit;
   grey controls in View mode alone are not a broken binding.
4. Use the existing save action/form submission. Do not replace it with a Patch,
   add an OnVisible default reset, overwrite form Item/identity, or change the
   working Person/lookup cards. New mode uses data-source defaults Active/Yes;
   Edit mode reads stored values, including Paused/Inactive and false/No.
   Existing blank legacy choices must not be silently interpreted as new profiles.
5. Preview first and verify the cases below. Save the app draft; record the app
   version/time. Publish the tested version to the existing owner/test audience
   when ready. No new sharing/access grant or wider rollout is part of #6.

There is no flow package for this App ticket. No app edit session/export is
available to the agent. Microsoft documents generated `.pa.yaml` as read-only
outside supported Git Integration; no unverified offline app rewrite or new
Dataverse/CLI/sign-in dependency is introduced. Adding the two auto-bound fields
is the necessary bounded owner edit; formulas are only changed if actual generated
bindings fail, after inspecting their control names/properties.

References: [generated data cards](https://learn.microsoft.com/en-us/power-apps/maker/canvas-apps/working-with-cards),
[form New/Edit defaults](https://learn.microsoft.com/en-us/power-apps/maker/canvas-apps/controls/control-form-detail),
[canvas source limitations](https://learn.microsoft.com/en-us/power-apps/maker/canvas-apps/power-apps-yaml).

### Own UI test handover - #6

Observed pass: real choices plus basic Paused/No save/validate/reopen; see
UI6-20261108-02. The second unrelated-edit cycle, other states, new-profile
defaults and fixture variants below are not yet confirmed.

Test target: **Tandem Participant Registration, Version 16**, saved
2026-11-08 15:34:26 Europe/Berlin (owner-reported version). Use the Versions
row marked Live and reload the player so a cached older version is not tested.
Record the actual version and account role for each test. Use the owner
profile/synthetic allowed fixtures; normal-colleague privacy proof remains
deferred under #18/#39-#42. Capture its item ID and initial language/culture,
time-zone, Comments, identity, participation and openness before changing it.
Do not delete a real profile to manufacture a new-registration test.

| Case | Steps | Expected persisted result / limits |
|---|---|---|
| UI6-001 / PAR-001 defaults | In New mode inspect both fields; cancel if this account already has a profile. For actual creation use a permitted new test account/fixture with a useful language/culture selection. | New-mode Active/Yes. Actual new save creates one own profile with those values; merely inspecting/cancelling is only a rendering pass. |
| UI6-002 / PAR-002, REG-009 | Edit existing profile to Paused and No; save, let existing validation finish, reopen/refresh; edit only Comments and save/reopen again. | Same item/account; Paused and No both survive, other selections retained. Read saved fields in SharePoint, not just UI. |
| UI6-003 / PAR-003 | Change Paused to Inactive; save/reopen, make an unrelated edit and reopen again. | Inactive and stored openness survive; no automatic reset to Active. |
| UI6-004 / PAR-004, PAR-005 controls | Return to Active with openness No, save/reopen; then set Yes and save/reopen. | False/No is genuinely persisted before Yes; neither value is treated as a missing/default value. |
| UI6-005 / PAR-002/003 culture/language variants | Repeat preserve/save checks with a permitted culture-only profile and a language-only profile. | Same item/account and relevant lookups retained; no language requirement on culture-only. If no allowed fixture exists, mark that variant NOT RUN. |
| UI6-006 / PAR-006/007 side effects | If a completed group/membership fixture exists, change only the two participant controls. | Group state/capacity and membership rows unchanged. If no fixture exists, mark this variant NOT RUN; never invent a group by editing authoritative rows. |

On a save failure, keep entered data, inspect Form1.Error and the affected card's
error, and report the first exact message. Confirm the card DataField is the
verified internal name and its generated Update is the user-selected value.
Do not remove required identity/uniqueness or change privacy/connection settings.
If validation resets participation/openness, preserve the failed case/run reference
and fix its field writes under #61; do not mask it with an app reset.

Discovery/request exclusion is implemented/tested by #7/#10 using these fields.
UI6 tests prove the app saves/retains the input; they do not prove exclusion before
those flows are ready. PAR-006/007 membership-derived badges/views belong to
#64/#68; #6 owns only absence of unintended form writes. Record integration
portions as Blocked/NOT RUN with the receiving ticket, not as blanket PASS.

After tests, restore the fixture's original participation/openness/Comments through
the app and confirm the original item ID remains. Return version/role, case IDs,
saved values and exact errors. No new registration/group history should be deleted
as routine cleanup. The edited app version is now identified; repository policy checks alone still
do not prove the remaining UI cases. After PR #70 review/merge, mark #6 Ready
for testing until its own remaining variants pass; do not close it prematurely.

## Historical SharePoint setup (superseded where #66 changed metadata)

Complete these steps once in the `Participants` list:

1. Confirm `Participant account` is a required Person column configured for one
   person and has a unique-value constraint.
2. Target: `Time zone` is an optional single-value lookup to `Time zone catalogue`.
   The tested baseline required it; remove that restriction and its validation
   dependency during #5 implementation, then retest. No live change is implied here.
3. Do not enable SharePoint's built-in item-level permission setting: it is
   incompatible with the unique Participant account column. Keep administrators
   as owners or full-control users.
4. Configure the Power Apps form to show only the fields in the `visibleFields`
   section of the registration contract. Hide `Title` and `Status`.
5. Make `Participant account` read-only and populate it from the signed-in
   account. Do not allow a participant to choose another colleague.
6. Share the app with the intended Team/security group or the organisation,
   then add the app as a Power Apps tab in the chosen Teams channel.

## Power Apps form behavior

This describes the tested direct-connector registration baseline. The agreed
privacy boundary requires replacing its direct Participants reads/writes through
POC-18; see [the access implementation guide](POC_18_PARTICIPANT_ACCESS.md).

Power Apps is the recommended form for the POC because it can reliably choose
between creating and editing the signed-in user's own item:

- On screen load, look up `Participants` where `ParticipantAccount.Email`
  equals `User().Email`.
- If a row is found, open the form in **Edit** mode with that item.
- If no row is found, open the form in **New** mode.
- Set the Participant account field to the current signed-in user and lock the
  control so it cannot be changed.
- Add `Time zone` as a single-select lookup dropdown backed by the Time zone
  catalogue, optional in the target contract. No participant group-size field.
- Filter the gallery to the signed-in user's Participant account. This keeps
  the app experience focused on the user's profile but does not replace
  SharePoint permissions.
- Submit the form to SharePoint. Do not create a separate email input.

The exact Power Apps formulas depend on the generated form control names, so
they should be entered in the tenant form rather than copied into this
repository as tenant-specific identifiers.

## Acceptance test

### POC-04 language verification — 2026-10-31

The owner supplied a screenshot showing one profile with Learn languages =
Dutch and Teach languages = English, Chinese, then confirmed that the saved
values remained after reopening the app. This confirms persistence, multiple
Teach selections, and simultaneous learner/sharer participation for that test.
The schema defines both language fields as multi-value Language catalogue
lookups, providing structured identifiers for future discovery.

The owner subsequently confirmed both remaining tenant checks passed: multiple
Learn selections persist after save/reopen, and a teach-only profile saves with
Learn languages empty. POC-04 acceptance is verified: controlled multi-value
language preferences persist, one person can learn and share, and teaching does
not require a learning selection. Catalogue lookup identifiers provide the data
contract for future discovery; discovery behavior is covered by later tickets.
Issue #4 can close when its completion PR merges. These checks do not complete
issue #18's permission tests.

Use two normal test accounts and one administrator account. Remove the test
rows afterwards if they are not needed.

| Test | Expected result |
|---|---|
| Account A opens registration with no profile | A new profile can be submitted without admin approval. |
| Account A opens registration again | The existing profile opens for editing; no duplicate is created. |
| Account A changes its languages or time zone | The same profile is updated. |
| Account A uses the app while Account B has a profile | Account B's item is not shown in the app; direct SharePoint list privacy is not guaranteed. |
| Account A tries to change Participant account | The control is locked and the identity remains Account A. |
| Administrator opens the list | Administrator can review and correct profiles. |

POC-03 is complete after the automated checks pass, the first three acceptance
tests have been confirmed in the tenant, and the app has been shared as a Teams
tab for a controlled test audience. The cross-account test must record the
known limitation that the app filter is not a substitute for SharePoint row
security.
