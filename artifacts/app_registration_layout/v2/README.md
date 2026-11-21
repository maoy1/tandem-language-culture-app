# #108 — published registration layout repair (v2)

The published app showed one column at startup and reflowed after entering Edit.
The parent container had a valid width while Form1 reported zero. The owner
confirmed normal published layout after overriding Form1 alignment and restoring
original card widths. The platform engine cause is not claimed proven.

## Final settings

| Control/property | Value |
|---|---|
| Form1.AlignInContainer | AlignInContainer.Start |
| Form1.Width | Parent.Width |
| Form1.NumberOfColumns | 2 |
| Existing paired data-card Width | 458 (original value restored) |
| Existing data-card WidthFit | false |

Keep current parent Stretch settings, card X/Y order, native catalogue/search
bindings, modes, identity, navigation, save behavior and conditional form visibility.
Time zone stays alone on its existing row; no unrelated full-width redesign.
The earlier responsive-card-width experiment is reverted. Historical v1 alone
failed; its original ZIP is retained and is not the final repair.

## Apply only if reproducing the repair

Owner has already applied and confirmed this fix; no repeat deployment is needed.
Use the existing working app in Power Apps Studio; no app/flow/Solution import.
Select Form1 in Tree view, choose AlignInContainer in the top property dropdown,
and paste Form1.AlignInContainer.fx into the formula bar. Keep Width=Parent.Width.
Restore the original card widths (458) if the diagnostic changed them.
Save and publish the same app, close the old player and reopen it.
Expect the registration layout to show the original paired fields at startup.
For a regression, return the published version, actual result and sanitized error;
check saved/published version before making more changes. Preserve the existing
export/version before edits. Cleanup: remove temporary diagnostic labels only.

## Evidence and limits

Owner report: "yes, not it works, I have to change the data card width back to old
number, everything looks normal again". Published desktop symptom: PASS.
This is owner-reported native evidence, not a generated runtime certification.
No post-fix native export/hash or exact published version was supplied. v2 identifies
this property handoff, not a binary app release. The inspected earlier export is
not relabelled as a repaired app. Original exports are unchanged; no app repack.

Broader cases retained under #25 as NOT RUN: post-fix Save/Cancel/screen return,
profile/account and catalogue preservation, no-profile/New/Cancel and mobile.
They remain test obligations, not PASS or a general release/privacy claim. Owner
requested closure of the repaired desktop defect on 2026-11-21.

#81 drift review: no schema, identity, mapping, normalization, catalogue semantics,
compatibility, capacity, commit or flow input/output contract change. Presentation
alignment only; no flow rebuild, connector, extra read or permission change.
