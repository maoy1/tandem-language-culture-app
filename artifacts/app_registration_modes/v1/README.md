# #103 — registration form mode fix v1

Native Studio property patch, not an app/Solution/flow import. It applies to the
accepted native-repaired app SHA256
`673bff977448c4d31390c806681b96fc3d3bc056094d6e61b0e972868c8466ae`.
Preserve that export/working app version; do not repack it. Existing SharePoint
and Office365Users bindings and catalogue controls need no changes.

## Apply in Studio

Open each .fx file as plain text, select the named control and property in Studio,
and paste the entire file contents into the formula bar. These are replacements,
not extra actions. Five properties only:

1. Form1 → OnSuccess: `Form1.OnSuccess.fx`.
2. ResetFormButton1 (Cancel) → OnSelect: `ResetFormButton1.OnSelect.fx`.
3. Discovery → OnSelect: `Discovery.OnSelect.fx`.
4. MyRequest → OnSelect: `MyRequest.OnSelect.fx`.
5. MyGroups → OnSelect: `MyGroups.OnSelect.fx`.

The first two retain current behavior and then explicitly return to View.
Successful Save clears editMode/newMode; failed Save stays editable. Cancel resets
unsaved values and clears the modes before returning to View. The three navigation
guards use actual Form1.Mode: saved View may navigate; Edit/New must Save/Cancel.
Other actor/intent guards and all flow calls are unchanged. No data refresh or
extra network call is added. OnFailure/SubmitForm and all form data fields remain.

## Owner acceptance (all NOT RUN until returned)

Prerequisite: existing owner account/profile and the previously working native
app/connections. Owner handles saving/publishing after the preview checks.

- [ ] Check App checker, then start a fresh Preview. In saved View, open Discovery,
  My requests and My groups separately, returning each time. Expect no false
  save/cancel warning; pencil remains available on registration.
- [ ] Pencil → edit a harmless value → Save. Expect persisted value, read-only
  fields, pencil visible and Save/Cancel hidden. Navigate without a false warning.
- [ ] Pencil → change a value → Cancel. Expect original saved value restored,
  read-only fields and pencil; navigate without a false warning.
- [ ] While actually editing or creating New, navigation still asks for Save/Cancel.
- [ ] New → Cancel exits New and hides Save/Cancel, without creating a row.
- [ ] Cause ordinary required-selection validation to fail without saving an empty
  profile: expect the form stays editable with its data retained. Cancel afterward.
- [ ] Existing catalogue choices/search and hidden account remain intact.

Delegated new-registration case (NOT RUN): use an existing approved test account
without a profile; successful New Save must return to View/pencil with the correct
automatically stored account. No fixture means BLOCKED; do not delete a working
profile. Backend/connection save failures require a safe prepared harness and
remain NOT RUN; do not break a shared connection to manufacture a failure.

Return case results and exact errors, without personal values. Restore harmless
saved test edits. Preview and Cancel do not write data. Missing colleague access
is BLOCKED; ordinary-participant privacy is still deferred under #41. Once the
native cases pass, save/export the working app; preserve those bytes unchanged.

Local generation verifies the exact guard-only navigation delta and original
success/cancel prefixes. It is not Studio type-check or native runtime acceptance.
No schema/shared validation/compatibility/identity/flow IO changes; #81 no-impact.
