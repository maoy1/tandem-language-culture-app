# #65 TandemRespondGroupJoinRequest

[#65](https://github.com/maoy1/tandem-language-culture-app/issues/65) is the sole
Flow owner; [#45](https://github.com/maoy1/tandem-language-culture-app/issues/45)
is the overview, [#47](https://github.com/maoy1/tandem-language-culture-app/issues/47)
owns the bounded coordination protocol, and
[#81](https://github.com/maoy1/tandem-language-culture-app/issues/81) owns shared
validation/schema. Separate managed worktree/branch `codex/issue-65-group-response`,
base `origin/main` = `7eba0ba0e5739477d4259474c2cb8fb8b3e3ee94`; no stacked #7 dependency.
No #7/#11/shared helper/fixture files, remote issues, working flows, apps, schema,
permissions or licences are modified. The owner's parallel batch authorization
is retained. #11 personal response remains Euclid's separate deliverable.

## Exact component and entry points

Build **040a6af8-ab91-4e09-b891-b638d96178ba**, readable parent
`artifacts/group_response/TandemRespondGroupJoinRequest.definition.json`, adjacent
`.definition.review.json`, exact IO/schema/connection contract
`config/group_response_flow_contract.json`. Parent **449 action definitions / depth5**
across all branches, scopes and loops, within 500/8, with 51 definitions of headroom;
re-measure after final assembly/any added actions. Child is a separate84/depth7
workflow; do not sum the nesting depths or confuse loop executions with definitions.

`group_response_flow.build_actions(original=None, mapping=None, groups=None,
build_id="local-review")` returns actions. `build_parent` has the same signature
and returns the complete `properties.definition`, displayName and
connectionReferences document. Defaults use the historical main Discovery v2
nested Get_item action; they do not import the #7 consumer. Source must preserve
Invoker and the observed participant table/site. No source-flow ID/creator or
actual connection instance is copied. Local generator command:

```powershell
python -m scripts.power_automate.group_response_flow --output artifacts/group_response/NEW.definition.json
```

Python is optional local tooling only. This is the requested parent component for
final Solution assembly, **not a standalone legacy linked-flow ZIP**. There is no
new legacy package or silently overwritten production flow. The assembler must
supply the final importable Solution/version/hash, use the observed #81 native
Invoker envelope and existing connection component, assign a fresh parent ID,
and map the Workflow reference to the corresponding shared component. Import
and Power Apps Solution caller parity remain NOT RUN. No manual action-by-action
flow construction is requested.

## Public and shared IO

PowerAppV2 `.Run(RequestId, Decision, IntentUUID)` maps in order to required
`number` (positive integer), `text` (exact Accept/Decline), `text_1` (stable UUID,
canonical lowercase). These references are not authority. No actor ID, account,
group ID, matching facts or availability Boolean comes from the app.

Outputs: Boolean `success` and `retryable`; Text `resultcode`, `resultjson`,
`runreference`, `errormessage`. Completed resultjson contains only
`{success,code,requestId,groupId,membershipIds}`. A saved rejection has success=false
and no membership IDs; unresolved outcomes return `{}`. Completed Accept/Decline
returns success=true only after result/Complete persistence and matching-token
release. Decline is a successful saved decision, not a join. No emails, claims,
raw account objects, Introduction, receipt/episode internals or system fields are
returned. The authorized request viewer/app owns introduction display; #65 adds
no message input or notification channel.

SharePoint resolves currentuser through the same Invoker connection, then exactly
one own ParticipantaccountId profile, current target group and exactly one Active
member episode committed by its Accepted/OperationComplete source. Every member
has equal response authority. **Actor ParticipationStatus/OpenToConnections are
not authority gates**; Paused/closed-to-connections actors retain membership.
Accept separately requires the new requester and relevant focus sharers to be
available. Decline requires the actor operational membership/source proof but no requester
availability, compatibility or Open/capacity admission test. It can settle an
existing Pending request after the requester pauses or the group closes/fills;
an unrelated provisional join does not revoke the actor authority.

Accept makes exactly two native Workflow calls, to
`e9aa88eb-a666-4df1-b088-176be7bcd00d`: NORMALIZE then GROUP, contract1/rules1.
The wire input is `inputs.body.text=string(RequestObject)`. RequestObject contains
contractVersion/rulesVersion/mode, current raw or normalized relevant member and
requester profiles, and trusted active catalogue ID sets. GROUP adds candidateId
and the documented group adapter. The adapter uses existing committed member IDs;
an own confirmed provisional joining episode is excluded from compatibility
membership context while still counted physically. GROUP receives fresh
focusSharersAvailable evidence. Both outer success/resultcode and parsed version,
code, success/authorizesAction guards must pass; result.compatible must explicitly
be true. No per-click SCHEMA or full field audit exists. The additive PAIRS work
on #7 is independent and does not alter #65 business semantics.

After shared evaluation, a bounded fresh read of each relevant profile must equal
the evaluated raw context before the terminal decision. A changed profile requires
a fresh retry. This is operation-time freshness, not a cross-list transaction or
a reservation of future profile state. Membership/state/capacity writers must
all follow the same group guard.

## Exact writes, stages and recovery

Canonical typed immutable intent is
`{version:1,kind:respond-group-join,actorId,requestId,decision,groupId,requesterId}`.
OperationKey=`respond-group-join:<trustedActor>:<lowerUUID>`; native JSON equality
binds IntentJson without a hash connector. Changing request/decision/target/sender
under that UUID cannot rebind the receipt. AttemptToken is the native run name.
WriteOwner=`OperationKey|AttemptToken`, max255, claimed only from blank using the
current exact group ETag. There is no lease, expiry, timed steal or repair platform.

Under the guard, reread current request/group/source/all physical Active episodes
and committed membership evidence. Provisional/paused rows count; malformed,
duplicate, foreign or uncommitted rows cannot establish authority or free slots.
Pending-only terminal CAS uses the exact request ETag, so Accept/Decline/cancel
compete on one row and the first saved terminal wins. Accept leaves the open
ConnectionKey while incomplete; Decline commits/rekeys to history:request:id.

A winning Accept creates only
`request:<requestId>:participant:<requesterId>` with GroupId/ParticipantId,
MembershipStatus=Active and JoinedAt. Native MembershipKey uniqueness and exact
readback reconcile an unknown create. Existing Left, wrong-party or wrong-group
episodes are never overwritten/reactivated. Before request commit, reread current
group plus **all** Active physical rows and require count<=current capacity,
exact ownership, Open/setup, and exactly one requester episode. CAS our winning
Accepted request to OperationComplete=true and history key; verify persisted
request/group/member results. Group State/Capacity are never changed: no auto
reopen/close at the last slot.

Persist ResultJson/Complete before releasing only the matching token. Complete
replay returns the saved result without domain writes; later Left history remains
Left. A release-only retry never clears a different operation's token. Positive
exact readback can reconcile 5xx persisted effects. Fully committed positive
request/member/count/owner readback can finish only receipt and release, retaining
the original attempt identity; it does not take over or repeat domain mutations.

At a stopped definite boundary, persist the old attempt in SealedAttempts and
Retryable before release. If that release failed, a retry first finishes only
the exact sealed old-token release. A subsequent bounded same-intent retry CAS-claims the
receipt, reacquires the group and resumes its confirmed prefix without another
terminal decision or duplicate episode. Definite 403 create/commit rejection and
412 group-claim contention are covered. Three sealed attempts exhaust automatic
retry; return explicit support. Unknown absence, partial/missing readback, stale
attempts or unproven effects retain ownership/uncertainty and never claim success.
Do not clear tokens, delete receipts or fabricate accepted history to recover.
Necessary exceptional assistance remains explicit.

Bounds: receipt/episode/own-profile matches1 (fetch2); all Active group rows11
(fetch12; valid capacity is at most10), context profiles12, each catalogue5000,
combined focuses100, shared request250000/result200000 characters, sealed attempts3.
Missing collection, next link, overflow, malformed type or invalid source fails
closed. Requests are fetched by their current IDs, not by loading a global inbox.
Writes use retryPolicy none and exact ETags; no wildcard merge/delete or member
update is generated. Local synthetic schedules do not prove tenant latency.

## Connection/schema dependencies and #81 drift ledger

Only existing standard SharePoint, source Invoker, site
`https://reedelsevier.sharepoint.com/sites/OG-TandemOrg`, reference
`shared_sharepointonline`, placeholder `IMPORT_SELECT_EXISTING_SHAREPOINT_CONNECTION`.
Raw auth is preserved:
`@json(decodeBase64(triggerOutputs().headers['X-MS-APIM-Tokens']))['$ConnectionKey']`.
The assembler uses the inspected native `cre46_sharepointonline_a22363a216`
component/runtimeSource=invoker. Connector-free child receives data, not a
SharePoint connection or actor authority. Native manual envelope/child proof does
not certify this Power Apps consumer or ordinary-user rights.

The parent foundation's `config/batch_schema_contract.json` was read only.
The exact `TandemOperationReceipts` target is snapshotted in this consumer contract:
OperationKey (unique/required/indexed Text255), IntentJson (required Note),
ResultJson (Note), Complete/Uncertain/Retryable/DomainEffects (Boolean default0),
AttemptToken (Text255), SealedAttempts (Note), Stage (Text255). ListId is still null;
this is **not applied/tenant-verified** evidence. One-time setup/audit must verify
this list, its actual settings/permissions and all request/group/member native
mappings before live integration. Runtime entity-type reads support verbose
writes and do not certify the schema. No schema auto-creation or paid fallback.

Shared NORMALIZE/GROUP IO/rules stay1/1; shared implementation, normalization,
null handling, catalogue semantics, compatibility/capacity rules are unchanged.
This new consumer implements the existing #47 protocol and exact batch receipt
target; no shared source or sibling package change is needed. This is the justified
#81 no-impact/change-ledger entry; remote issue edits are forbidden for this task.
Final foundation/schema and Solution updates must retain this receiving consumer
and its versioned native tests. Generator updates never update imported flows.

Receipt records this parent build/definition/generator hashes. Tested child is
c79b7b64-b3ce-4de3-aa74-0ed62bca1524; the consumer contract records its exact SHA256
and the parent schema target SHA256. Historical closed #9/#12/#66 and #7 evidence,
#47 proof and #81 QUICK3/FULL44 remain version-scoped. New #65 import/Power Apps
caller/business/parity/load tests: **NOT RUN**. Ordinary participant/privacy tests:
**BLOCKED/deferred**, not PASS. No Ready/Done/closure or wider-release claim.

## Versioned native test handover (NOT RUN)

Unavoidable owner steps are final Solution import/connection selection, owner-only
Studio draft binding and tenant test execution. Before those steps, require the
final assembler's ZIP/version/hash tied to 040a6af8-ab91-4e09-b891-b638d96178ba, enabled matching shared
child, verified schema target/unique/index settings, existing Invoker connection,
and an owner/synthetic isolated operational fixture produced by the owning flows
(#11 source group, #17 join requests). No production history fabrication or broad
individual grants. Stop if any connection/licence/config prerequisite is unknown.
Do not assume all unrelated tickets must close for local review.

1. Import the final Solution as a new consumer, preserve existing production
   flows/app and verify the fresh parent ID plus correct shared reference. Inspect
   Run-only Provided by run-only user and native runtimeSource=invoker. Expected:
   existing connection, no embedded owner fallback. Return exact selector/export
   evidence if unavailable; stop, with no trial/new permission workaround.
2. Record fixture IDs and original rows: owner A has an operational Active
   membership; B is a second member, C/D eligible requesters; group Open/setup,
   committed source/episodes and one free slot; two Pending Group requests. Record
   exact package build, account role, request/group/member IDs and current ETags.
   Missing fixture/receipt schema means BLOCKED, not empty-test PASS.
3. Add the new flow to an owner Studio draft, not the published app. On a new
   explicit response action freeze the request/decision/UUID once; disable changing
   request/decision while unresolved. A minimal Accept test uses:

```powerfx
If(IsBlank(varGroupResponseIntent),
    Set(varGroupResponseIntent, {
        requestId: Value(RequestsGallery.Selected.requestId),
        decision: "Accept",
        intentId: Text(GUID())
    })
);
IfError(
    Set(varGroupResponseResult, TandemRespondGroupJoinRequest.Run(
        varGroupResponseIntent.requestId,
        varGroupResponseIntent.decision,
        varGroupResponseIntent.intentId
    )),
    Notify("Response call failed. Keep this intent for retry.", NotificationType.Error)
)
```

   Substitute the actual Studio binding name. For a new Decline use decision
   Decline only when no unresolved intent exists. Retry invokes the frozen record
   unchanged. A completed resultjson (not `{}`) settles the intent; unresolved
   results keep it for retry/support. Expected Accept: success true/ACCEPTED,
   one requester episode, request complete/history key, receipt complete/result,
   token gone, same Open state even when now full. Return report and sanitized
   response plus persisted field evidence (no auth headers/raw account fields).
4. Repeat the exact UUID then retry after marking only the disposable admitted
   episode Left through its proper owner. Expected: saved result, no duplicate or
   reactivation. Reusing that UUID for another decision/request must fail binding
   without writes. A new Decline must save Declined/complete/history with no join.
5. Pause/close openness for the acting member while keeping the membership
   operational. Expected: Decline still works; Accept works if another eligible
   focus sharer remains. Make requester Paused/Inactive/open No/null availability,
   group Closed/Ended/full or focus unsupported. Expected: no admitted membership,
   no changed group State, saved rejection or explicit incomplete result. Restore
   deliberate fixture changes after each case. Culture-only/optional-zone rules
   are shared; blank zone must remain allowed.
6. Run two frozen owner intents against the last slot concurrently; also race
   cancel with response using #63's same Pending ETag. Expected: at most one new
   episode; losing decision never changes the saved terminal. Actual different
   member/foreign-account authorization requires verified permitted accounts;
   that ordinary-user/two-account case stays deferred under #42, not inferred
   from owner/synthetic tests or admin permissions.
7. On a disposable instrumented test copy, exercise definite stopped create/commit
   rejection, persisted unknown write, partial readback and release failure.
   Expected: definite sealed retry resumes the same keys; positive committed
   readback can finish receipt/release; unresolved/absent readback holds ownership
   and returns no success; complete release retry does not repeat domain writes.
   Do not induce destructive failures in production. If no safe native harness
   exists, record NOT RUN and return the missing prerequisite.
8. Return build/ZIP hash/account role, numbered case, parent/child run references,
   Group_response_report, sanitized response and first unexpected failed action.
   A red expected CAS action is not itself a business failure if exact readback
   proves the result. Lack of receipt/commit readback is never an Accept PASS.
   Native pagination/bounds/latency/load need recorded sizes/times, not local PASS.
9. Cleanup only disposable fixture rows/components and the temporary draft button/
   binding after evidence is saved; restore intentional own-profile values. Keep
   working flows/published app and historical accepted/Left evidence unchanged.
   Do not clear an uncertain operation's token or receipt without scoped recovery.

## Local validation

The suite executes actual emitted parent actions, native-style exact ETag and
unique episode/receipt primitives, and the real packaged shared child. It does
not replace GROUP/normalization with a mirrored matcher. It covers first terminal,
member/cancel/last-slot races, paused actor authority, requester null availability,
profile freshness, source/party/foreign membership, immutable replay/Left, unknown
persisted writes, partial readback, sealed prefix/three-attempt bounds, current
physical count/capacity, release-only replay and exact target receipt fields.

Final full regression: **415 passed in 58.90s** (357 baseline +58 #65 cases).
The focused suite and final full run cover the Closed/full/unavailable Decline
cases, unrelated provisional-member independence, sealed-release replay and
combined wildcard-ETag guards. `git diff --check` and final definition/generator
fingerprints pass. No native/ordinary-user certification follows from these tests.
