# #7 Discovery shared-validator consumer

Ticket: [#7 TandemDiscovery](https://github.com/maoy1/tandem-language-culture-app/issues/7),
owner overview [#45](https://github.com/maoy1/tandem-language-culture-app/issues/45),
shared owner [#81](https://github.com/maoy1/tandem-language-culture-app/issues/81).
The explicitly authorized parallel 12-flow batch overrides the one-active-ticket
limit for this work. No GitHub issue, historical closed evidence, working flow,
app, permission or tenant setting was changed. GitHub currently reports #7 closed;
that state is preserved, not treated as acceptance of this new consumer.

Build `0ab956c1-cbb6-4da7-9e23-dbd8b4cd9ebe`:
`artifacts/tandem_discovery/TandemDiscovery-shared.definition.json` and adjacent
`.definition.review.json`. Parent **164 actions / maximum depth 6**, including all
control/loop/branch definitions; limits 500/8. Shared child remains **84/depth7**.
These are separate workflows; do not add their nesting depths. Zero writes.

The separate generator `scripts/power_automate/discovery_shared_consumer.py`
reuses the existing Discovery read/projection adapter without editing its legacy
implementation or fixtures. It replaces emitted normalization and pair/group
matching fragments with actual Workflow calls. The adapter retains native shape,
active-catalogue reference and approved-display filtering to exclude malformed
candidate source rows before bulk normalization; it does not derive normalized
arrays, fit types, overlap explanations or group compatibility. Minimal actor
availability and fresh focus-sharer evidence remain operation-time checks.

No per-click field/full schema audit remains. The bounded current request rows
must themselves have typed Id/Status/OperationComplete; missing/null/malformed
commit evidence fails the whole search. The deployment schema audit is a one-time
setup/change prerequisite, not a reservation of future compatibility or capacity.

## Exact input/output and connections

Public input remains required `number` (Power Apps Number, positive integer
ParticipantId reference). It supplies no account, eligibility or catalogue facts.
Same Invoker connection resolves `_api/web/currentuser`, binds exactly one own
ParticipantaccountId row and requires exact reference equality before Get item,
candidate reads or child calls. No embedded owner fallback.

Public Text outputs remain `candidatesjson`, `groupsjson`, `errormessage`,
`resultcode`, `runreference`, `mode`. OK returns complete compatible arrays and
empty error text; failure returns **both arrays `[]`**, a sanitized error/code and
run reference. Mode remains `OWNER_PREVIEW_PENDING_ACCESS_PROOF`. People retain
profileId/displayName/fitType, typed approved profile and four directional match
arrays. Groups retain approved focus/member displays, physical count/capacity/
free slots/join availability. Optional blank zone and culture-only matching stay
supported. Email, account keys/claims, raw account objects and system/commit data
never enter public result rows. No flow performs business writes.

Every native Workflow action has
`inputs.host.workflowReferenceName=e9aa88eb-a666-4df1-b088-176be7bcd00d` and
`inputs.body.text=string(RequestObject)` (the shared Button input key is `text`).
All requests contain `contractVersion=1`, `rulesVersion=1`, `mode`, `profiles`,
and `catalogues=Raw_catalogues` (languageIds/cultureIds/timezoneIds/anyLanguageId).

| Mode | Additional exact input | Consumed output |
|---|---|---|
| NORMALIZE | profiles=Raw_profiles | result.profiles and result.catalogues; internal only |
| PAIR | profiles=[Actor,current candidate], leftId=Actor.profileId, rightId=candidate.profileId | result.eligible must equal true; fitType and canLearnLanguageIds/canShareLanguageIds/canLearnCultureIds/canShareCultureIds |
| GROUP | profiles=Shared_Profiles, candidateId=Actor.profileId, group=Group_adapter | result.compatible must equal true, plus parent's accepted/complete source and all committed membership episode gates |

Group_adapter contains groupId/exchangeType/state/capacity/setupComplete,
languageFocusIds/cultureFocusIds/memberProfileIds/focusSharersAvailable. Current
physical Active episodes count paused members; duplicates, missing profiles,
incomplete or invalid focus relationships cannot manufacture capacity.

Every call requires native body.success=true and resultcode=OK; parsed resultjson
must have success=true/code=OK/contractVersion=1/rulesVersion=1/authorizesAction=false.
Success alone does not imply compatibility. Failed call, malformed result,
version mismatch or child/request/result bound failure fails the parent scope
and suppresses partial results, including any people accumulated earlier.

Only connector: existing standard SharePoint `shared_sharepointonline`, source
Invoker, placeholder `IMPORT_SELECT_EXISTING_SHAREPOINT_CONNECTION`. Each GET
preserves exported Raw authentication:
`@json(decodeBase64(triggerOutputs().headers['X-MS-APIM-Tokens']))['$ConnectionKey']`.
The final Solution assembler must map this to the observed native reference
`cre46_sharepointonline_a22363a216` with `runtimeSource=invoker`, preserve the
PowerAppV2 trigger and Raw expression, and assign a fresh parent component ID.
The child is pure/connector-free; no parent connection passes to it. No additional
connector, licence, sign-in, CLI, local runtime or individual grant is introduced.

Bounds remain profiles500/people50/groups100/memberships2000/requests500,
each catalogue5000/group focus-member work100/combined response250000 characters.
Next links, missing collections and overflow fail closed. Each serialized child
request is limited to250000 characters; child result limit200000. At most600
child calls (1 NORMALIZE +499 PAIR +100 GROUP); this is a bound, **not a latency
or load PASS**. There is no per-click SCHEMA call or metadata read.

## #81 change ledger and drift assessment

Shared contract/rules stay1/1, child build stays
`c79b7b64-b3ce-4de3-aa74-0ed62bca1524`; no shared schema/mapping/catalogue semantics,
normalization/null handling/availability/compatibility/capacity/commit rules or
shared implementation/IO changed. Existing #81 source and contract need no
modification. This consumer's request shape and operation adapters implement the
existing contract. Other consumer tickets/packages have no semantic/version
impact and are unchanged. This is the justified no-impact record for #81; remote
issue ledger edits are intentionally not made under the owner's instruction.

The parent has a new build/hash. Review receipt records parent definition,
generator, native source ZIP and exact real-child artifact SHA256. Child fingerprint
`0b45537750865f843114f86116d56c4d58dd9199fc8ca24d5b56e6400fdc6088`
is unchanged. Source ZIP SHA256
`7b4dc1e5df96769615088d897cf86030a2622a47dc7db56a414dbe75f41085a9`.
Historical #7 owner Paused/Active empty-result evidence and closed #9/#12/#66 proofs
remain attached to their original versions. Native child QUICK3/FULL44 PASS stays
its own evidence; new parent native parity/caller/projection/load **NOT RUN**;
ordinary-user protected access remains **BLOCKED/deferred** under #42. Generator
changes never update imported workflows.

## Assembly and versioned tenant handover (NOT RUN)

This is the requested readable **parent component for the final batch Solution**.
There is no new legacy ZIP: legacy package import does not establish linked child
Solution dependencies. Historical TandemDiscovery-v2.zip remains unchanged.
No import/overwrite is requested before the final assembler supplies its verified
Solution ZIP/version/hash and native Invoker mapping. Existing native envelope
proof covers the manual probe, not this Power Apps parent. Stop this dependent
cutover if the assembled mapping/entitlements/child linkage are unverified; no
paid workaround. Native import/connection selection and owner Studio preview
are unavoidable owner steps after assembly. Full schema audit/setup belongs to
deployment maintenance; no routine participant approval is added.

Prerequisites: owner account in existing permitted environment; final assembled
Solution receipt naming this exact parent build and real child; existing Invoker
SharePoint reference; verified participant/catalogue/group/request mappings,
including Boolean OperationComplete. Preserve existing source flow and published
app. Use owner/synthetic fixtures only; do not infer ordinary-user privacy.

1. Import final assembled Solution as new consumer, preserving the existing
   child identity and all working parents. Select existing SharePoint connection;
   inspect runtimeSource=invoker and Provided by run-only user. If either differs,
   STOP and return the reference/export/selector evidence without tokens. Expected:
   fresh Discovery component bound to this child, existing working flow unchanged.
2. In owner Studio draft add this new flow and temporary button using
   `Set(varDiscoveryPreview, NewDiscoveryName.Run(RecordsGallery1.Selected.ID))`
   inside the existing IfError wrapper. Use the signed-in owner's saved profile,
   validation Active/participation Active/open Yes, with optional zone blank.
   Expected: OK with arrays (possibly empty), writes0, matching report build;
   no list/app state changes. Empty results prove no populated matching case.
3. On disposable owner/synthetic fixtures record IDs/original values. Use a
   compatible language candidate and a culture-only sharer/learner pair, then
   Paused/Inactive/open No/Needs review/nonmatching/Any-only candidates. Expected:
   only compatible eligible non-self rows, approved labels/comments/optional
   details, null zone accepted; no email/claims/account/admin data. Preserve exact
   parent and child run IDs, reports and sanitized response JSON.
4. Supply a disposable Open/setup-complete/unlocked group with capacity3, two
   Active committed MembershipKey episodes, an Accepted/OperationComplete=true
   source, valid focus/sharer/different learner, owner not already a member.
   Expected: count2/freeSlots1/approved members. Then Closed/Ended/full/current
   member/duplicate or uncommitted episode/missing profile/unavailable sole sharer
   must hide it, without state changes. Missing commit mapping or fixtures means
   BLOCKED, not PASS; do not fabricate production acceptance history.
5. Test an alternate profile reference and a failed child/read in the disposable
   deployment. Expected: wrong reference stops before candidate/child reads;
   failed/malformed/version-mismatched child cannot return partial arrays. Ordinary
   two-account testing remains separately deferred under #42. Record first failed
   action, code, run references and sanitized diagnostics; do not return headers.
6. Native next-page/count/result/request/work bounds and synchronous load remain
   NOT RUN until a separately agreed bounded fixture is available. Return exact
   fixture sizes, versions, elapsed time and response/report; no silent partial OK.
7. Cleanup: restore intentionally changed fixture/profile values, remove only
   disposable test rows and temporary Studio button/binding after evidence is
   saved. Do not publish the draft, replace source flow or delete accepted history.
   The Discovery workflow itself has no data writes to undo.

Unexpected failures indicate mapping/child binding/data shape or boundary defects,
not permission to switch to an owner connection. Return parent build, final
Solution hash/version, account role, numbered case and expected/actual result,
parent/child run references and sanitized first error. No broad Ready/Done or
ordinary-user PASS is claimed.

## Local validation

The tests execute emitted parent actions with fake SharePoint, dispatch each
native Workflow input into the actual packaged child graph, and assert fixed
public outcomes. They do not replace shared evaluation with a mirrored matcher.
Coverage includes caller rejection before reads/calls, populated language/culture
and group projection, optional zone, unavailable/invalid exclusions, physical
capacity/commit/focus/history, child errors/versions/eligibility, no partial results,
read/request/render/work/response bounds, no writes, and source-envelope hygiene.

Final complete regression: **402 passed in 94.29s** (357 baseline +45 new
Discovery consumer cases). The expanded emitted-parent/real-child suite passes;
`git diff --check` passes. Native import/consumer/caller/projection/load remain
NOT RUN; ordinary-user access is not verified. Final packaging-only newline/hash
normalization is covered by the focused rerun before commit (46 cases, including
the additional exact generator-receipt fingerprint regression).
