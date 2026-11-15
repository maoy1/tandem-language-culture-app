# Native-repaired registration app — #101

Accepted native UI evidence: owner reports **all six registration dropdowns and
search work**, then saved/exported the app from Studio. Earlier own-profile load
PASS is retained. The final native export is preserved byte-for-byte, with no PAC
pack or formula edits.

Primary handoff:
`C:\projects\small_projects\tandem-language-culture-app\artifacts\app_integrated\native-repaired\TandemParticipantRegistration-Native-Repaired.msapp`

Source kept unchanged:
`C:\projects\small_projects\tandem-language-culture-app\artifacts\app\Tandem-Native-Repaired.msapp`

SHA256 for both: `673bff977448c4d31390c806681b96fc3d3bc056094d6e61b0e972868c8466ae`.

Read-only local inspection: valid ZIP; all six visible catalogue controls use
Studio-generated Choices(column, control.SearchText); known hidden-account
Self.Items default is absent. This verifies structure, not full Studio typing.
No new runtime dependency, schema/flow/permission change or Solution reimport.

Use the native Studio-saved app as the working version. Keep generated v4–v10
as historical candidates only; v8/v10 owner failures remain recorded. A working
native source may require Studio to regenerate dropdown bindings on import;
do not claim arbitrary repacking/import paths tested by the native result.

Unexecuted acceptance retained: new registration automatically stores the correct
Person/mailbox; edits preserve identity and lookup selections after save/reload;
optional blank time zone saves; complete App checker pass; colleague connection/
access; ordinary-participant privacy; regression actions in other screens. These
are NOT RUN/deferred, not implied by “all work, saved” (app save is not a participant
data submission). Discovery performance investigation is paused at owner request.
