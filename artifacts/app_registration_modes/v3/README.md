# #103 — clear no-registration view (v3)

Owner report: a user with no Participants row sees the form's persistent
"Getting your data..." message. The accepted form is visible with a blank Item.
Hide the unbound form and show a clear no-profile hint next to the existing New
control. Native property changes only; no app/flow/Solution import or repacking.
Keep the already applied v1 mode/navigation and v2 New-guard fixes.

## Apply in the current Studio app

Prerequisite: the working native app with v1/v2, existing SharePoint/Office365Users
connections. Preserve its saved version/export first.

1. Select **Form1 → Visible**. Paste `Form1.Visible.fx`.
2. Select **SidebarContainer1** in Tree view, then Insert → Text label. Name it
   **lblRegistrationEmpty**. Keep it inside SidebarContainer1 and place it just
   above RecordsGallery1 in Tree view, so the hint appears below the New bar.
3. Set that label's **Text** to `lblRegistrationEmpty.Text.fx` and **Visible** to
   `lblRegistrationEmpty.Visible.fx`.
4. For the label, set **AutoHeight** to `true` and **Width** to `Parent.Width - 32`
   so the message fits the sidebar on smaller screens.

The hint requires View mode, a resolved mailbox, no selected saved record and a
successful own-profile lookup returning no ID. Lookup errors and unresolved
identity do not show the no-profile hint. Existing startup error handling is
unchanged; this is not a new custom loading-state/cache implementation.
The form is always shown in New mode, and otherwise only with a selected record.
No change to data fields, defaults, SubmitForm, Cancel, identity, New guards,
catalogue search or navigation. The sidebar placement also works when the mobile
layout hides the empty right-hand pane.

## Native acceptance — NOT RUN until returned

- [ ] Account with no row: fresh Preview settles on the no-profile hint and New,
  without persistent Getting your data text. Do not delete a working profile:
  use the existing no-profile test account, or mark missing fixture BLOCKED.
- [ ] New: the hint disappears and the empty registration form appears normally.
- [ ] New/Cancel: no row is written; the hint and New return.
- [ ] Valid New Save: the saved own profile appears, the hint disappears and New
  remains hidden using v2. Verify the account and lookups as in the existing plan.
- [ ] Existing participant: saved data and pencil remain visible, no empty hint or
  New, and Edit/Save/Cancel still work. Check desktop and phone layout.
- [ ] Catalogue choices/search and normal registration navigation remain intact.

An error response must not be labelled no-profile; safe prepared error fixtures
remain NOT RUN if unavailable. This patch does not test permissions/privacy.
Return case results and exact errors without personal data. Restore deliberate
saved edits; follow existing fixture cleanup, without deleting legitimate rows.
Check App checker, save and publish the same app, close old player tabs and reopen
to verify the normal app (not only Preview). Preserve the resulting native export
unchanged; do not repack it.

Local checks verify source bindings, exact three formula files and ZIP hashes;
they are not native Studio typing/runtime evidence. No new connector/schema,
shared validation/compatibility/identity/authority or flow IO changes; #81 no-impact.
