# POC-03 participant self-registration

This document defines the registration contract for the Participants list.
The repository cannot change the SharePoint tenant, so the final list,
Power Apps form, sharing, and Teams-tab settings are applied manually.

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

## Manual SharePoint setup

Complete these steps once in the `Participants` list:

1. Confirm `Participant account` is a required Person column configured for one
   person and has a unique-value constraint.
2. Confirm `Time zone` is a required single-value lookup to `Time zone catalogue`.
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

Power Apps is the recommended form for the POC because it can reliably choose
between creating and editing the signed-in user's own item:

- On screen load, look up `Participants` where `ParticipantAccount.Email`
  equals `User().Email`.
- If a row is found, open the form in **Edit** mode with that item.
- If no row is found, open the form in **New** mode.
- Set the Participant account field to the current signed-in user and lock the
  control so it cannot be changed.
- Add `Time zone` as a single-select lookup dropdown backed by the Time zone
  catalogue.
- Filter the gallery to the signed-in user's Participant account. This keeps
  the app experience focused on the user's profile but does not replace
  SharePoint permissions.
- Submit the form to SharePoint. Do not create a separate email input.

The exact Power Apps formulas depend on the generated form control names, so
they should be entered in the tenant form rather than copied into this
repository as tenant-specific identifiers.

## Acceptance test

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
