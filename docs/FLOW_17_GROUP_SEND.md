# #17 TandemSendGroupJoinRequest — local candidate

[#17](https://github.com/maoy1/tandem-language-culture-app/issues/17), overview
[#45](https://github.com/maoy1/tandem-language-culture-app/issues/45). Own flow only:
create a Pending group join request; #65 responds, #62 reads, #63 cancels, #67 owns
the full screen. No membership, group, permission or schema writes. No notification
channel chosen. This candidate changes no deployed flow or ordinary-user access.

Build **issue-17-group-send-v1**, **147 action definitions / maximum depth5**,
below500/8. Uses unchanged connector-free child **e9aa88eb-a666-4df1-b088-176be7bcd00d**,
contract1/rules1 **GROUP**, build c79b7b64-b3ce-4de3-aa74-0ed62bca1524, child84/depth7.
Actual parent/child native parity and app binding remain **NOT RUN**.

## Exact artifacts and binding

Full readable parent including trigger/response:
`artifacts/group_send/TandemSendGroupJoinRequest-v1.solution-parent.json`.
Exact hashes, bounds, prerequisites and provenance:
`artifacts/group_send/TandemSendGroupJoinRequest-v1.solution-parent.review.json`.
Contract: `config/group_send_flow_contract.json`; generator:
`scripts/power_automate/group_send_flow.py`; tests: `tests/test_group_send_flow.py`.

The parent is prepared from the inspected native unmanaged Solution export
`TandemSharedValidation81_1_0_0_2.zip`, SHA256
ce19af2e37e7de4a9317ec4c63e8d5777beaf23a57120c99b4e38d38ce4946d4.
Standard SharePoint logical reference **cre46_sharepointonline_a22363a216**,
**runtimeSource=invoker**, native Raw X-MS-APIM-Tokens/$ConnectionKey binding.
Existing site https://reedelsevier.sharepoint.com/sites/OG-TandemOrg.
The #61 automated Embedded marker is **not** used here. Its separate source and
commit996a3ae remain untouched. No owner substitution/new connection is introduced.

No standalone legacy ZIP: the native Workflow dependency needs final core Solution
assembly. Do not treat this readable JSON as an import package. Core must resolve
its child reference, preserve this interactive Invoker boundary, verify final
500/8 metrics, record the final package/parent ID/version/hash and import disabled.
Do not silently overwrite an existing production flow or manually rebuild actions.

## Trigger and response mapping

New Power Apps V2 flow input order is definitive:

| Position | Trigger key | Display name | Contract |
|---|---|---|---|
| 1 | number | GroupId | Required positive integer; selected group's reference |
| 2 | text | IntentId | Required36-character UUID; same value for uncertain retries |
| 3 | text_1 | Introduction | Optional plain text, maximum2,000; missing/null -> empty |

No actor input. The flow resolves currentuser.Id through Invoker, then exactly one
Participants row for that Person account. The actor's current item account is
rechecked before new-send validation. Injected actor fields never select a sender.
Whitespace in nonempty Introduction is significant. No HTML transformation occurs:
plain Note storage and Text rendering display literal text; never use an HTML control.

| Output | Type | Meaning |
|---|---|---|
| success | Boolean | Exact stored own request confirmed, SAVED or REPLAY |
| requestid | String | Stored numeric request ID, otherwise0 |
| status | String | Stored Pending/Accepted/Declined/Cancelled, otherwise blank |
| resultcode | String | SAVED/REPLAY or bounded rejection/unknown code |
| resultjson | String | Versioned sanitized Send_report JSON |
| runreference | String | Parent run ID for operator correlation |
| errormessage | String | Safe message; retain intent/check run if not confirmed |

Main failures: INVALID_INPUT (including Introduction2001), INVALID_INTENT,
UNAUTHORIZED_PROFILE, INTENT_CONFLICT, GROUP_UNAVAILABLE,
GROUP_SOURCE_UNCOMMITTED, ALREADY_MEMBER_OR_PROVISIONAL,
GROUP_FULL_OR_DUPLICATE_MEMBER, MEMBERSHIP_UNCOMMITTED,
GROUP_UNAVAILABLE_OR_INCOMPATIBLE, CONNECTION_EXISTS,
UNSETTLED_CONNECTION_EXISTS, CREATE_OUTCOME_UNKNOWN. Malformed/failed domain or
child reads fail safely with READ_OR_DATA_FAILED or the recorded bounded guard.
No backend data, Introduction or technical account/intent keys are returned.

## Business order, persistence and uncertainty

1. Parse group/UUID/Introduction and enforce2,000 before any I/O. Canonicalize only
   missing/null Introduction to empty; preserve all other characters.
2. Resolve trusted actor. Read unique SendOperationKey **group:{actorId}:{lowerUUID}**.
   Exact replay happens **before** availability/group reads. Return stored ID/status
   only if sender, recipient=null, target group, Introduction and key/lifecycle match.
   Same UUID with changed group/text is INTENT_CONFLICT. Settled history remains
   replayable after actor Paused, group Closed/full or membership changes.
3. For new intent, read target group: Open, SetupComplete=true, blank WriteOwner;
   verify the Accepted/OperationComplete settled source Personal request and parties.
   Read own non-Left memberships: any current or provisional episode blocks.
4. Read all physical Active members (bounded10, extra/pagination fails). Count every
   physical row for capacity; duplicates/provisional rows cannot manufacture space.
   Validate each immutable request:{requestId}:participant:{participantId} episode
   against an Accepted/complete history-keyed request and the target/source group.
   Per-member relevant committed-request reads are bounded500; exceeding fails closed.
5. Read current actor/member profiles and complete active catalogues. Pass nullable
   availability and optional zone unchanged. Compute available focus-sharer evidence
   only from current member profiles with explicit Active/Active/true. Call real
   GROUP rules for purpose, distinct focus relationships, type-specific capacity,
   actor fit/availability, free slot and not-already-member. Check typed envelope,
   versions/build/zero-I/O/authorizesAction=false and result.compatible, not success alone.
6. Check unique **open:group:{groupId}:participant:{actorId}** plus a fallback read
   for legacy Pending/Accepted-incomplete joins with missing keys.
7. At most one request POST, retryPolicy=none: RequestType=Group,
   SenderParticipantId numeric, RecipientParticipantId=null, TargetGroupId numeric,
   canonical Introduction, Status=Pending, immutable SendOperationKey, live
   ConnectionKey, WinningOperationKey=null, OperationComplete=false. The request
   row itself stores immutable intent; no second receipt write/list is needed.
8. After POST success/failure/timeout, read exact SendOperationKey once. Confirm only
   exact immutable payload and valid stored lifecycle. Lost success may reconcile;
   generic502, another intent's live duplicate, missing/corrupt/failed/incomplete
   readback remain CREATE_OUTCOME_UNKNOWN. No second POST or blind retry. Later
   retry uses the same UUID; native unique keys prevent a second request.

This is a join **request**, not a capacity reservation. Group/profile/catalogue state
can change after these reads; #65 must recheck fresh authority/fit/membership/space
at acceptance. No group/member lock or write is performed by this sender.
Downstream flows must preserve immutable parties/group/Introduction/SendOperationKey.

## One-time setup gates — not routine participant work

The planned Introduction comes from #81 batch_schema_contract.json at commit
a385e2847aa733eb3fd8069dfdecf5c20e216193, SHA256
f189c44795dd448faaf7c8a0087b3aeed6357b264f21f8cb4e8860955b308495:
optional Note, RichText=false, AppendOnly=false, max2,000 enforced in app/server.
Actual tenant field/settings remain unverified. #81 owns setup; this flow does not
create schema and does not depend on that batch's receipts list.

Before activation verify request field types, nullable numeric recipient, nullable
TargetGroup lookup, RequestType Group choice, key uniqueness/index/required,
OperationComplete/winner semantics and existing-row handling through one deployment
audit. No full/per-click schema audit is emitted. Stop activation on missing or
unverified setup/connection/access; no new grant, licence/trial or paid workaround.
Requests list3d17485d-1dac-41f0-a1af-24e45daa4567; Participants
fd3adf46-f81d-4a7b-a80c-567fde0175dc; Groups4bf1b37f-edce-40c5-8fa0-36543a2d0cd6;
Group Members db611ec3-7fa3-477a-878e-effbbb195cb8. Catalogue IDs use verified #66
mapping. Bounded native shape/latency and caller behavior still need tenant tests.

## Minimal app binding — prepared issue #17 handover, not applied

Add the new flow to the app only after final Solution import/connection verification.
Optional multiline **plain-text** input: MaxLength=2000. Server validation is still
authoritative for direct calls. Keep a submitted draft record with groupId,
intentId=Text(GUID()), introduction=Coalesce(input.Text,""). Freeze that record for
transport retries; changed group/text is a new deliberate draft with a new UUID.
Never regenerate a UUID merely because the previous response was lost/unknown.

Exact invocation (same order as trigger):

```powerfx
TandemSendGroupJoinRequest.Run(
    varGroupJoinDraft.groupId,
    varGroupJoinDraft.intentId,
    varGroupJoinDraft.introduction
)
```

Before freezing/submitting, reject Len(Coalesce(input.Text,""))>2000 with a clear
notification and no call. Store the flow result; show confirmed request/status only
for success=true. On rejection/unknown do not Reset the input, navigate away, erase
the draft or recreate the intent. Retain the frozen submitted payload for an exact
retry and preserve any unsent edits separately. Do not substitute an actor ID or
client eligibility flag. Full controls/layout/audience work stays #67. Native app
boundary/preservation tests remain NOT RUN. No issue edits were made by instruction.

## Reproduction and native test handover

Local generation uses the existing Python environment only; no deployed Python:

```powershell
python -m scripts.power_automate.group_send_flow --native-export '<native TandemSharedValidation81_1_0_0_2.zip>' --output artifacts/group_send/TandemSendGroupJoinRequest-v1.solution-parent.json
python -m pytest tests/test_group_send_flow.py -q -p no:cacheprovider
```

Builder refuses existing outputs. The original native export stays local/untracked.
Tests execute emitted parent and delivered unchanged v2 child, not a rule oracle;
fake SharePoint models exact filters/uniqueness/uncertain create. This does not
certify native Parse JSON, Power Apps input order, access, latency or tenant writes.

Prerequisites/role: existing authorized owner/operator and permitted synthetic actor
plus a valid operational fixture group with two committed distinct members and free
slot; isolated catalogues/harness for negatives. Setup/audit and final imported
Solution IDs/version/hash must be recorded first. Ordinary participant access is
owner-deferred. Missing setup, fixture or account -> BLOCKED, never a fabricated PASS.

1. Import final assembled Solution disabled, preserving working flows. Verify child
   linkage/hash, exact input order/output types and native Invoker connection source.
   Resolve currentuser and own profile under the permitted account. No grant changes.
2. Record fixture group/source/member/profile/request IDs and originals. Send a fresh
   UUID with empty Introduction, then another independent actor/group fixture with
   exactly2,000. Expect one Pending request with exact fields/readback, no membership
   or group changes. Exercise optional null zone and culture-only fit separately.
3. Retry same UUID/payload after changing actor availability/group state on isolated
   fixtures. Expect stored request/status REPLAY, zero new POST; restore originals.
   Same UUID with changed group or one changed character -> INTENT_CONFLICT.
4. Direct flow call with2,001 and app length guard -> rejection before request write;
   preserve unsent edits and UUID. Plain-text display must show literal text only
   to the authorized sender/current-member audience (#62/#67); that audience test
   remains blocked until its access method is verified.
5. Isolate no-fit/full/Closed/Ended/uncommitted source, occupied/provisional own
   membership and unavailable actor/sharer variants. Expect no new request. Verify
   duplicate UUID and live-key races through an approved harness, not live corruption.
6. Harness lost success should reconcile only the exact saved row. Generic failure,
   another-intent duplicate, corrupt/missing/incomplete readback -> unknown, one POST
   maximum. Keep same UUID; never manually create a second request to force success.
   If no safe harness, mark native uncertainty/race variants BLOCKED/NOT RUN.
7. Restore profile/group/catalogue fixture originals; use existing permitted cancel
   workflow for test Pending requests if available. Otherwise retain tagged test rows
   and record cleanup blocked; no direct group/member/permission/delete workaround.

Return each variant PASS/FAIL/BLOCKED/NOT RUN, final package/hash/parent/child build,
role alias and fixture IDs, exact inputs without employee text, request stored fields,
parent report or first action/error/run ID, POST count and cleanup result. Stop a
failing candidate and preserve evidence. This branch requests no live activation.

## #81 drift ledger

Shared engine/rules/schema packages and other consumers are unchanged. This adopts
existing GROUP and request-key/commit semantics, plus the already planned2,000 Note
dependency. #81 must include actual Introduction in its setup/audit baseline before
activation; #62/#65/#67 must preserve immutable text and authorized plain rendering.
Local ledger is config/group_send_flow_contract.json; no issue edits or shared-child
edits. Existing native QUICK3/FULL44 PASS is retained only for its prior shared build;
new send/schema/access/app/native acceptance remains NOT RUN/BLOCKED as applicable.

Local validation for this candidate: **71 #17 cases PASS; full repository428 PASS**
(pytest34.47s). Parent147 definitions/depth5; unchanged shared child84/depth7.
Actual native source -> full parent reproduction and staged whitespace validation
are checked before commit. These local results do not upgrade any native or access
evidence, and this branch performs no import, enablement, app edit, issue edit or push.
