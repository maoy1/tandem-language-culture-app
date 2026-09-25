# POC-03 participant self-registration

This document defines the registration contract for the Participants list.
The repository cannot change the SharePoint tenant, so the final form and
permission settings are applied manually once in SharePoint or Power Apps.

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
5. The colleague can edit only their own profile. They do not need administrator
   approval to register or update it.
6. The submission flow validates the profile and maintains `Status` and the
   hidden derived time zone as described in `CURRENT_DESIGN.md`.

## Manual SharePoint setup

Complete these steps once in the `Participants` list:

1. Open **List settings → Advanced settings**.
2. Under item-level permissions, set **Read access** to **Read items that were
   created by the user**.
3. Set **Create and Edit access** to **Create items and edit items that were
   created by the user**.
4. Do not grant participants delete access. Keep administrators as owners or
   full-control users so they can correct exceptional records.
5. Confirm `Participant account` is a required Person column configured for one
   person and has a unique-value constraint.
6. Configure the participant form to show only the fields in the `visibleFields`
   section of the registration contract. Hide `Title`, `Time zone`, and
   `Status`; hiding a list-view column alone is not enough.
7. Make `Participant account` read-only for the participant and populate it
   from the signed-in account. Do not allow a participant to choose another
   colleague.

## Power Apps form behavior

Power Apps is the recommended form for the POC because it can reliably choose
between creating and editing the signed-in user's own item:

- On screen load, look up `Participants` where `ParticipantAccount.Email`
  equals `User().Email`.
- If a row is found, open the form in **Edit** mode with that item.
- If no row is found, open the form in **New** mode.
- Set the Participant account field to the current signed-in user and lock the
  control so it cannot be changed.
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
| Account A changes its languages or location | The same profile is updated. |
| Account A tries to edit Account B's item | The action is denied or the item is unavailable. |
| Account A tries to change Participant account | The control is locked and the identity remains Account A. |
| Administrator opens the list | Administrator can review and correct profiles. |

POC-03 is complete after the automated checks pass and the first three
acceptance tests have been confirmed in the tenant. The cross-account and
administrator checks are the security sanity check before sharing the form
more widely.
