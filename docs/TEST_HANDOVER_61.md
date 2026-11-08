# Participant submission — tester handover

[#61](https://github.com/maoy1/tandem-language-culture-app/issues/61) is **Ready for
testing**, not Done. Owner explicitly chooses merge/handover rather than completing
all acceptance personally. Untested cases remain untested; results stay in #61.
Do not close the issue merely because the implementation PR merges.

## Exact version and setup

- Published app: **Tandem Participant Registration, Live Version 26** (owner
  reported; exact publish time not supplied). Launch the published app from
  Power Apps, reload it, and confirm the available version before reporting.
- Flow: **Tandem – Participant submission v2**, build
  `88637754-4c91-4833-9dcf-5116d8bfb77e`. Original validator is off; only v2 enabled,
  owner confirmed. No reimport or manual action rebuild for this handover.
- Package/readable definition/review: artifacts/participant_submission/
  TandemParticipantSubmission-v2.*. **26 actions / depth 3**, local **101 tests**.
- Current schema/list mapping: config/tenant_schema_mapping.json (#66 verified).
  Existing SharePoint connection only; no new licence, connector or runtime.
- Existing owner fixture: Participants **ID 38** (third visible row for owner).
  Other testers use their own permitted profiles; row position is not item ID.

## Who can test

App testers need existing authorized access to the published app and its data.
Use own permitted profiles or approved synthetic fixtures. App publication alone
does not verify ordinary-user access. Other-account/privacy cases retain the
#39/#40/#41 gate: if access is unavailable or unverified, report that case BLOCKED
with the error; do not use owner credentials or change grants to force a pass.
This handover does not authorize routine per-person admin grants or expose rows.

The existing flow/list operator handles direct-list negative fixtures and run
history. Ordinary testers need no new flow-edit/admin permission. The operator
correlates their saved item ID to runs and supplies redacted reports as needed.
No messages/invitations or access changes have been sent/performed by the agent.

## Already passed — preserve exact scope

- Owner item 38: valid/no-change; necessary Active Status correction and readback;
  subsequent no-change. Three raw reports are under results/ (run suffixes CU09,
  CU11, CU26). Matching build and item ID; not global race/loop proof.
- Owner confirms identity, selections, participation/openness unchanged and only
  v2 enabled. Third row visually confirmed as ID 38.
- Owner reports empty-four-selections -> Needs review -> original selections
  restored -> Active, with Refresh displaying each changed result. Raw invalid-run
  JSON/new run IDs were not supplied; invalid follow-up no-op not inferred.
- Feedback layout and final copy accepted; Version 26 published. No independent
  replay in the Live-26 player has yet been reported.

## Test procedure

Before any change, note the actual item ID and original selections, optional time
zone, Comments, participation/openness and stored Status. Keep personal data out
of public reports. Preserve a valid way to restore the original profile.

1. **Live-26 basic feedback.** On an authorized own profile, change Comments, Save,
   wait for the matching asynchronous v2 run (one-minute polling may add delay),
   then Refresh validation. Expect “Last profile check: Passed” for a valid
   profile. Notification acknowledges the Refresh click, not validation completion.
   Match actual stored Status and run, not merely an old displayed result.

2. **Selection variants / blank zone.** On an existing permitted fixture, test
   language-only, culture-only and share-only variants, with Time zone blank.
   Save/reopen and correlate each run. Expect valid=true / Active, selections
   persisted and identity/participation/openness unchanged. Restore originals.

3. **Invalid branch and follow-up (operator).** On an isolated permitted profile,
   clear all four selection fields via SharePoint, bypassing the App save guard.
   Expect valid=false / Needs review, one necessary Status write/readback, then
   matching-item NO_CHANGE / statusChanged=false without another profile edit.
   Refresh in the app should show Needs attention. Restore exact selections;
   expect Active and follow-up no-op. This includes the still-unreported invalid
   follow-up variant; a successful restore is not evidence of that variant.

4. **Availability preservation.** Set Paused/No, save a Comments edit and correlate
   the current-item run; repeat with Inactive. Expect valid profile still Active
   validation, all user fields preserved, and only necessary validation Status
   changed. No auto-rejoin or group-state changes. Restore original choices.
   Operational group-side-effect fixtures remain with #25, not fabricated here.

5. **Inactive catalogue (isolated operator fixture only).** With a dedicated test
   catalogue entry and profile already permitted for testing, select it while
   active, then disable that fixture entry and edit the profile. Expect Needs
   review / Needs attention. Restore the catalogue/profile originals. Do not
   disable shared real catalogue entries. If no isolated fixture exists, BLOCKED
   until one is provisioned under the existing schema/permission rules.

6. **Unknown catalogue ID.** Use an approved isolated harness/injection method
   only. Expect no successful validation of an unknown selected ID. If SharePoint
   rejects it before it can be stored, record that as platform rejection; the
   validator negative remains BLOCKED without a supported harness. Local rule
   tests already cover unknown/mixed IDs; do not claim a tenant pass from them.

7. **Creation and other accounts.** Use a distinct authorized test account with
   no existing profile. Register useful selections; expect one signed-in profile,
   correct identity, Active/Yes defaults and subsequent validation. Never delete
   a real profile or enter someone else's identity to force this case. No account
   or access proof available -> BLOCKED (#41 prerequisite), not passed.

8. **Failed/incomplete reads and conflicts.** Exercise only an approved isolated
   harness. Expect explicit failed run, no misleading Validation_report success
   and no stale overwrite (ETag conflict yields failure). Do not revoke production
   permissions or create an outage. Without the harness, keep these variants
   BLOCKED/NOT RUN. Local guards are not target-tenant execution evidence.

## Cleanup and failure handling

Restore original profile values and any isolated catalogue fixture even when a
test fails. Verify restored Status/availability. No group/member deletion, grants
or new connector needed for normal testing. If v2 repeatedly writes Status without
user edits, capture evidence, have the operator stop v2, then restore the original
validator using FLOW_61_PARTICIPANT_SUBMISSION.md recovery steps; never both on.
Prior successful writes remain; recovery is not a transaction rollback.

## Evidence to return

Report in #61 or to the coordinating owner (the agent has not sent invitations):

    Case / app Live version / flow build:
    Tester role or synthetic alias / item ID:
    Steps and actual stored result:
    PASS / FAIL / BLOCKED / NOT RUN:
    Run reference and Validation_report JSON, or first failed action/error:
    Fields preserved? Cleanup completed?
    Access/fixture gate if blocked:

Redact employee details. Failed cases keep exact errors; blocked cases identify
the missing fixture/access/harness. Full acceptance and issue closure require
the remaining scoped results; this handover grants no overall Done/privacy pass.
