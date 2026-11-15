# #103 — New only for users without a profile (v2)

Owner report: an existing participant can still choose New and enter another
registration. The accepted native app had an unconditional NewForm handler.

This adds two native Studio properties on top of the already applied v1 mode
fix. No app/flow/Solution import or repacking; preserve the current working app.

## Apply

Use the existing Studio app and its verified SharePoint/Office365Users connections.
Preserve its current version/export. Paste each entire .fx file into its property:

1. **NewRecordButtonBarContainer1 → Visible**:
   `NewRecordButtonBarContainer1.Visible.fx` (hides both New icon and label).
2. **NewRecordAddIcon1 → OnSelect**:
   `NewRecordAddIcon1.OnSelect.fx` (fresh lookup before opening New).

If already in a New form, Cancel once. An existing participant should then see
their saved profile and pencil, with New absent. Missing/resolving mailbox or
lookup errors hide New; a stale click rechecks the current own-profile lookup.
Existing-profile and failure branches leave the current form/data untouched.
Repeated New while editing/creating does not reset an unsaved draft. No extra
network read is added to Save/Cancel or any business flow; visibility and a New
click use the existing delegated Person Email lookup. Existing unique account
constraint and authenticated identity handling remain; this UI check does not
replace storage uniqueness or backend authorization.

## Owner checks — NOT RUN until confirmed

- [ ] App checker has no new errors. Existing profile: fresh Preview shows own
  saved profile and pencil, with no New icon/label. Editing still works.
- [ ] Edit/Cancel and Edit/Save return to View/pencil as before; New stays absent.
- [ ] Catalogue choices/search and registration navigation remain working.

Delegated account without a profile:

- [ ] In View, New appears after account/profile lookup resolves. It opens a
  new form once; New disappears while entering data. Cancel returns to empty View
  with New available again and no row created.
- [ ] A valid New Save creates the authenticated profile automatically, returns
  to View/pencil using v1, and New remains absent after save/reopen.
- [ ] Stale New handler with an existing profile warns without clearing form data
  or opening New; lookup failures never open New. Missing fixture/harness is
  BLOCKED; do not delete a working profile or break a shared connection to test.

Return case results and exact errors without personal values. Preview/Cancel and
the lookup guards do not write participant data. Restore deliberate saved edits;
use the existing fixture-cleanup plan for legitimate test registrations. Save and
publish this same app after native checks, close old player tabs and reopen it.
The earlier Preview/player mismatch does not establish a formula defect by itself.

Local checks cover the exact two-property package, fail-closed lookup/guard ordering,
and no writes in the rejection branches. Studio typing/native behavior is NOT RUN.
No schema/shared validation/compatibility/identity/flow IO change; #81 no-impact.
