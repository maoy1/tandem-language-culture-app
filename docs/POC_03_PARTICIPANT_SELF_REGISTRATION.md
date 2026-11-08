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

**Completed: PR #70 merged, #6 closed/Done; corrected owner-reported Live target Version 19.**
Owner confirms New defaults Active/open Yes, saved choices preserved on edits,
and language/culture-only save/reopen without identity/unrelated changes. Exact
Version 19 timestamp/fixture IDs were not supplied; no whole-backend PASS follows.
Version 16 is historical and contained the new-default failure. See TEST_RUNS.md.

The owner edits the existing registration app with its existing SharePoint
connection; no new connector, role grant, CLI/sign-in, licence or flow is needed.
Verified form path:
`MainScreen1 > ScreenContainer1 > BodyContainer1 > RightContainer1 > MainContainer1 > Form1`.
Actual fields are `ParticipationStatus` (Choice) and `OpenToConnections` (Boolean).

### Working Version 19 bindings

Refresh Participants and add the two fields to Form1. Participation status's
inner control is **Combo box DataCardValue2**, single selection; Items is
`Choices([@Participants].'Participation status')`, DisplayFields is `["Value"]`.
Keep the card's generated DataField/selected-record Update binding.

**Outer Participation status card > Default:**

```powerfx
ThisItem.'Participation status'
```

**Inner DataCardValue2 > Default:**

```powerfx
Blank()
```

**Inner DataCardValue2 > DefaultSelectedItems:**

```powerfx
If(
    Form1.Mode = FormMode.New,
    Filter(
        Choices([@Participants].'Participation status'),
        Value = "Active"
    ),
    [Parent.Default]
)
```

The two branches return tables of Choice records, preserving the existing parent
record on Edit. Do not compare a text Active value with Parent.Default's Record,
or put the selection formula into the Combo box's legacy Default property.
The three copyable `.powerfx` files are in artifacts/participation_controls.
Open to new connections keeps its generated Boolean binding; the owner confirmed
new Yes and saved choices including No. Use the existing form Save/checkmark.
No reset-on-open, identity replacement or group/membership write is introduced.

### Own App acceptance and integration ownership

#6 owns these three UI criteria, all owner-confirmed for the corrected controls:

1. Show Active/Paused/Inactive and Yes/No using the verified fields.
2. New-mode defaults Active/Yes; edits preserve stored choices.
3. Save/reopen language/culture-only profiles preserving identity and unrelated values.

The earlier wording also put backend behavior into #6. These checks are now
explicitly handed to their implementation owners in
config/participation_integration_handoffs.json. Nothing is dropped or marked passed
merely because ownership moved. #6 review/closure uses its App scope, not completion
of the later production flows. New-profile record creation/duplicate-identity
variants remain #5/#61; #6's default rendering is independently testable.

| Check | Receiving owner | How to test / current limit |
|---|---|---|
| Validation preserves participation | #61 | Set Paused/No, change Comments, Save; inspect the matching item-ID submission run, then reread Paused/No. Repeat with Inactive. Baseline owner preservation passed; full #61 target acceptance still Planned. |
| No membership/group side effects | #25 integrated test; #64/#68 derived displays | With a permitted operational group fixture, capture group/membership IDs/state/capacity/count; pause/reactivate/change openness. All unchanged; no auto-rejoin/reopen. Blocked if no fixture. |
| Discovery excludes unavailable targets | #7 | Compatible Active/Yes/validated target appears; Paused, Inactive and No target absent; restoring eligibility permits appearance. Target-flow implementation pending. |
| Request rejects stale unavailable target | #10 | Target becomes unavailable after discovery; Send rejects without a new request/group/member. Target-flow guard pending; existing requests are not auto-cancelled. |

To check the **existing validation baseline now**, do not inspect the app alone:
open Tandem participant submission in Power Automate > Run history after your
Comments edit; find the run whose item ID matches the profile. It must succeed.
Reopen the stored Participants item and confirm ParticipationStatus/Openness are
unchanged; validation Status is a different field and may be recomputed. If no
edit-triggered run exists, record that case Blocked for #61 instead of passing it.
This is not completion of #61's catalogue/error/loop/creation acceptance.

Do not create group rows manually to unblock a test. Wait for the relevant
group creation/schema fixture (#11/#12), then run the #25 integrated case.
Discovery/request tests need the #7/#10 packages and permitted compatible test
profiles/caller context; their current Planned status is not a #6 implementation gap.

### Tester handover and evidence

Use the corrected **Version 19** Live player after reload. Owner is the verified
test role; ordinary-user privacy tests remain deferred #18/#39-#42. Capture the
actual version, role, fixture item ID and initial selections/participation/openness.
Do not delete a real profile to force New mode: inspect/cancel New if an account
already has a unique profile. Use a permitted new fixture for actual creation.

Retain UI6-001:006 and PAR-001:007 as stable bug/regression references. Their App
portions are accepted by owner confirmation; exact per-state detailed sequences
were not separately logged. Backend/creation/group portions have the receiving
owners above. Do not convert those portions into blanket PASS.

On failure, record the exact card/Form1.Error, selected input, saved value and
matching flow run ID. Preserve entered data; fix the failing layer. Restore test
participation/openness/Comments through the app; keep identity and business history.
PR #70 is merged and #6 closed on its passed UI scope. Receiving flow/
integration tickets stay open until their own packages and tests are complete.

References: [Combo box defaults](https://learn.microsoft.com/en-us/power-apps/maker/canvas-apps/controls/control-combo-box),
[form modes](https://learn.microsoft.com/en-us/power-platform/power-fx/reference/function-form).
No automated app-export rewriting is claimed; the owner edited/tested the actual
app, and these bindings/configs are the reviewable repository handover.

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
