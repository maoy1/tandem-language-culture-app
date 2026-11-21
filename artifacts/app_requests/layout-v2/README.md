# #67 — compact Requests layout v2

Native Studio property patch for the CURRENT working app; no app/flow/Solution
import and no replacement .msapp. Existing registration #108/#110 native fixes
and dropdown/search bindings are preserved. Owner screenshot matches the named
req* controls; the most recent export predates those registration edits.

## Result

Compact read-only details panel (maximum760px wide,136px tall for personal requests;
224px for a nonempty group introduction), with friendly status and local-format date.
No empty Introduction, Available or Not complete system labels. Preserve useful
accepted/processing and unavailable-request messages. Selected tabs are darker;
helper/empty text explains which requests belong in each view. Cancel is labelled
Withdraw request, including its confirmation. Action/retry/outcome controls follow
the compact panel. All invocation, authorization and frozen-retry formulas remain
unchanged, including internal decision value Cancel. Other screens are untouched.

Current reader supplies no person/group names. Request references remain visible.
#62 must add an approved display projection before names can be wired; this patch
adds no raw Participants lookups, caches or account/email exposure. That item is
explicitly pending, not delivered or inferred from the screenshot.

## Apply in Studio

Prerequisites: owner/maker can edit current working app; existing bindings and
approved own test profile. Save a copy/export before edits. No new connection,
permission or licence. Unavoidable editor work: apply the property entries below.

1. Open scrRequests in the current app. In Tree view select each named control.
2. Choose the PROPERTY in the TOP dropdown and paste the matching .fx file in the
   formula bar. Numeric boxes in the right pane do not accept these formulas.
   reqRowTitle is inside gallery reqList. No new controls are inserted.
3. Change only the listed properties. Keep OnSelect, DisplayMode and action Visible
   guards unchanged. In particular, do not rename the internal Cancel decision.
4. Run App checker. Save and publish the same app, close old player tabs and reopen.
5. For a regression, return first exact error, control/property and actual published
   version; restore that control's previous formula from patch.json if needed.
   No business action runs merely by applying these presentation properties.

## Property entries

| Control | Property | File |
|---|---|---|
| reqState | Text | reqState.Text.fx |
| reqTab0 | Fill | reqTab0.Fill.fx |
| reqTab1 | Fill | reqTab1.Fill.fx |
| reqTab2 | Fill | reqTab2.Fill.fx |
| reqTab3 | Fill | reqTab3.Fill.fx |
| reqRowTitle | Text | reqRowTitle.Text.fx |
| reqEmpty | Text | reqEmpty.Text.fx |
| reqSelectedTitle | Text | reqSelectedTitle.Text.fx |
| reqDetails | AccessibleLabel | reqDetails.AccessibleLabel.fx |
| reqDetails | Default | reqDetails.Default.fx |
| reqDetails | Height | reqDetails.Height.fx |
| reqDetails | Visible | reqDetails.Visible.fx |
| reqDetails | Width | reqDetails.Width.fx |
| reqActionAccept | Y | reqActionAccept.Y.fx |
| reqActionDecline | Y | reqActionDecline.Y.fx |
| reqActionCancel | Text | reqActionCancel.Text.fx |
| reqActionCancel | Width | reqActionCancel.Width.fx |
| reqActionCancel | X | reqActionCancel.X.fx |
| reqActionCancel | Y | reqActionCancel.Y.fx |
| reqRetry | Y | reqRetry.Y.fx |
| reqNewIntent | Y | reqNewIntent.Y.fx |
| reqOutcome | Width | reqOutcome.Width.fx |
| reqOutcome | Y | reqOutcome.Y.fx |
| reqDialogTitle | Text | reqDialogTitle.Text.fx |
| reqDialogHelp | Text | reqDialogHelp.Text.fx |
| reqConfirm | Text | reqConfirm.Text.fx |
| reqRowState (inside reqList) | Text | reqRowState.Text.fx |

## Native handover — NOT RUN

Coordinator records actual published app ID/version. Existing own Pending Sent
fixture and permitted connection required. Other participant/group fixtures can be
delegated; mark missing fixtures BLOCKED. No flow activation/switching test steps.

- [ ] 1. Sent: select the existing Pending request. Expect highlighted Sent tab,
  compact details, Waiting for a reply, readable date and Withdraw request directly
  below the panel. No Completion/Availability jargon or blank Introduction.
- [ ] 2. Withdrawal dialog: open Withdraw request. Expect a withdrawal explanation
  and Withdraw request confirmation. Choose Back; expect NO stored change. To test
  an actual withdrawal, use a disposable request and verify authoritative Cancelled
  readback/history under #63. Do not cancel the owner's real request for layout proof.
- [ ] 3. Received/History/empty: switch views and select existing fixtures. Expect
  highlighted tab, contextual empty text, appropriate accept/decline/withdrawn text
  and existing server-owned action visibility. Layout does not invent permission.
- [ ] 4. Group: choose an approved group request with an introduction. Expect plain
  text introduction, compact scrollable224px panel and actions below without overlap.
  Personal and blank-introduction group requests show no Introduction heading.
- [ ] 5. Retry fixture: use the existing safe uncertainty harness if available. Expect
  retry/review/outcome controls below the compact panel, retained intent and no new
  flow call or permission bypass from changing tabs/layout. Missing harness BLOCKED.
- [ ] 6. At desktop1366x768 and the owner's wide viewport, check no overlap/clipping;
  retain #108/#110 registration layout. Narrow/mobile acceptance remains NOT RUN.

Return case ID, app/patch version, role, PASS/FAIL/BLOCKED/NOT RUN, sanitized UI/error
and any persisted action result. Back/Cancel-dialog dismissal changes no rows. For
an action test, clean up only approved disposable fixtures via supported workflows.
Local source checks are not Studio compilation, native action or access proof.

#81 no-impact: presentation only; current schema, shared rules/normalization,
compatibility, capacity, atomic guards and app/flow inputs/outputs unchanged.
Name projection remains queued in #62; this handoff does not change that contract.
