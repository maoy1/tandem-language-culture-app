# POC-05 registration form acceptance

Issue [#5](https://github.com/maoy1/tandem-language-culture-app/issues/5), **App**;
currently Ready for review; own UI acceptance passed. Target is the existing Tandem Participant Registration
**Version 19**, reported Live by the owner. #66 schema and #6 participation
controls are Done (PRs #69/#70 merged). This guide covers form behavior only;
the production submission flow belongs to #61. No new flow ZIP or app rebuild
is needed merely to verify the already configured form.

## Existing implementation and bounded evidence

- Four controlled multi-value lookups: Teach languages, Learn languages,
  Cultures I can share, Cultures of interest. #66 verified exact targets/types;
  config/tenant_schema_mapping.json contains actual names/IDs.
- Owner confirmed catalogue labels and the Preview all-four-empty guard in
  historical REG-005. Earlier language multi-selection tests are preserved.
- Owner confirmed language/culture-only save/reopen with identity/unrelated
  values preserved while testing #6, and corrected Active/open Yes defaults for
  new profiles. Version 19 is the corrected release; the Version 16 default failure
  and subsequent fix history remain in TEST_RUNS.md.
- Owner reported **A and B passed** on Live Version 19: all four multi-lookups
  persisted with Time zone cleared and identity unchanged; all-four-empty Save
  showed the required-selection message, retained the draft and left the saved
  item unchanged. See artifacts/registration_form/version19.owner-report.json.
  Exact timestamps/fixture IDs and separate cleanup evidence were not supplied.
  No backend eligibility/active-ID enforcement or ordinary-colleague privacy pass
  is inferred from form save.

## Own scope and acceptance

1. Four lookups show catalogue labels, permit multiple values and support
   language-only/culture-only/share-only/combined profiles.
2. Signed-in identity remains read-only/required; existing own-profile edits
   keep the same item/account. Time zone is optional and clearable.
3. All four empty blocks Save with a clear message while keeping entered values.
4. Saved multi-lookups and unrelated fields persist on reopen in the test release.
5. Record app version and scoped REG results; UI success is not backend success.

No participant group-size preference, leader role, Comments notice, private-note
split, native Location or new identity input is introduced. The culture labels
remain the existing approved vocabulary, not a new nationality/official taxonomy.

## Version 19 checks - owner-reported A/B PASS; regression steps retained

Use your existing permitted owner profile in the **Live Version 19 player after
reload**. Record original item/account, selections, time zone and Comments first;
restore them after testing. Do not delete profiles to obtain a fresh identity,
or fabricate authoritative group/member rows. Ordinary-user access testing remains
with its existing deferred owners; no new grant/connection is required here.

### A - multiple lookups plus cleared optional time zone

1. Edit your own existing profile. Select **two values in each** of the four
   language/culture selectors. Clear Time zone and change Comments to a short
   temporary test note. Leave identity and participation/openness unchanged.
2. Save using the app's checkmark. Reopen/refresh the same profile.
3. Expected: all selected values retained in each selector, Time zone blank,
   temporary Comment retained, same account/item and participation/openness.
   Also inspect the saved Participants item so a displayed cached value is not
   mistaken for persistence. This covers App portions of REG-003/007/009.
4. If Save fails, keep entered values and report Form1.Error/affected card error.
   No fallback making time zone mandatory or removing identity uniqueness.

### B - all-four-empty Save guard without losing entered data

1. Edit that same saved profile; clear all four language/culture selectors.
   Enter a distinguishable unsaved Comment; click the app Save/checkmark.
2. Expected: **Choose at least one language or culture to share or learn**
   (or equivalent clear required-selection message). Form stays open with the
   entered Comment and empty selections still visible. No successful-save
   navigation/reset. The saved item must still contain A's previous values.
3. A server uniqueness/identity/time-zone error does not count as this guard PASS.
   If the invalid row was submitted/saved, report the failure and restore the
   previously noted valid selections through the app; do not mark the test passed
   merely because the validation flow later set Needs review.
4. Cancel the unsaved B edit. Restore the original valid profile through the app;
   confirm the original item/account remains. This covers REG-005 UI behavior.

Return A/B outcome and first exact error if any. Already-confirmed culture-only/
identity behavior is retained; no need to rebuild working cards to repeat it.

## If a check fails - inspect before changing bindings

Select Form1 at the verified path in POC_03_PARTICIPANT_SELF_REGISTRATION.md.
Inspect the actual failing control/card Items, DefaultSelectedItems and Update.
Multi-lookups store selected lookup records/IDs, not joined text. Each lookup is
individually optional; the form enforces the OR across all four.

Historical owner-confirmed control names were cmbTeachLanguages,
cmbLearnLanguages, cmbShareCultures and cmbLearnCultures. Confirm current names
before inserting formulas. The expected all-four-empty guard is:

```powerfx
If(
    IsEmpty(cmbTeachLanguages.SelectedItems) &&
    IsEmpty(cmbLearnLanguages.SelectedItems) &&
    IsEmpty(cmbShareCultures.SelectedItems) &&
    IsEmpty(cmbLearnCultures.SelectedItems),
    Notify("Choose at least one language or culture to share or learn.", NotificationType.Error),
    SubmitForm(Form1)
)
```

This is the existing guided guard, not a claim that the latest app source/export
was inspected. Preserve any other actual Save behavior; do not add a second
unconditional SubmitForm. On failure the form must show an error and retain input;
do not reset it. Ask for the actual formula/control type before guessing a repair.
The working #6 Choice default binding must not be replaced by a text/record mix.

## Receiving-flow boundaries

- #61 owns current-item validation, unknown/inactive catalogue IDs, creation/edit
  revalidation, Status-only updates, no-op follow-up and identity/availability
  preservation. Its implementation is still Planned; legacy manual instructions
  are not the new package delivery. Do not rebuild it manually from this App guide.
- #7 owns blank-time-zone eligibility and unavailable-profile exclusion; #10 owns
  stale/unavailable Send rejection. App save is not evidence that they work.
- #41 owns protected own-profile registration integration. Owner/admin UI tests
  are not ordinary-participant row privacy proof. Existing access tests stay deferred.
- Case IDs REG-008/011/014:016 and DISC-005 keep their receiving owners. #5 can
  close after its own form/version acceptance and review; later flows do not hold
  the App ticket open after an explicit handoff. All historical results remain.
