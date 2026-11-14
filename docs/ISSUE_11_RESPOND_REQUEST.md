# TandemRespondRequest — issue 11 handover

[#11](https://github.com/maoy1/tandem-language-culture-app/issues/11) owns this
personal response flow; [#45](https://github.com/maoy1/tandem-language-culture-app/issues/45)
is the owner overview. The owner-authorized parallel batch supersedes the earlier
single-active-ticket constraint. No issue, label, working flow or app was edited.

Version **11.1.0**, build **94e47272-28bc-4529-bb2f-521b90e43011**. Generated native
Power Automate actions; Python is optional local generation/testing only. The old
77-action snapshot/Decline overlay remain historical evidence. Native integration
and this consumer's authority proof are **NOT RUN**. Ordinary-account access is
owner-deferred. Keep #11 open until its scoped acceptance and tenant tests pass.

## One-time setup and native gates

1. Parent [#81](https://github.com/maoy1/tandem-language-culture-app/issues/81)
   owns setup/audit of `TandemOperationReceipts`. All ten finalized fields are used;
   Title is unused. Address via the exact title until native GUID readback.
   No receipt additions or new group fields are requested.
2. Verify request party/type/target mappings, `WinningOperationKey`,
   `OperationComplete`, required unique `ConnectionKey`; group
   `SourceRequestId` and member `MembershipKey` uniqueness; existing
   `Groups.WriteOwner`. #12 metadata proof does not prove consumer writes.
3. Verify the existing deployed child `e9aa88eb-a666-4df1-b088-176be7bcd00d`,
   contract1/rules1/build `c79b7b64-b3ce-4de3-aa74-0ed62bca1524`, and existing
   connection reference `cre46_sharepointonline_a22363a216`.
4. Verify actual Power Apps Invoker/run-only binding, caller identity, intended
   request/group/member/receipt rights and existing entitlements. The inspected
   manual #81 owner envelope is not proof of Power Apps caller/private write
   isolation. A setup description saying “No participant direct writes” does not
   grant Invoker permissions. Resolve this gate with #23/#39–42 before dependent
   native writes; no silent owner-connection fallback or individual grants.

These are integration gates, not requirements to close unrelated tickets. No
routine approval, leader/contact role, notification channel, external service,
premium connector, licence, scheduler, Python/server or hosted runtime is added.
Exceptional uncertain-write assistance remains necessary in some failures.

## Artifacts and import

The `artifacts/respond_request/` directory contains:

- `TandemRespondRequest-11.1.0.zip`: legacy package.
- `TandemRespondRequest-11.1.0.definition.json`: readable legacy definition.
- `TandemRespondRequest-11.1.0.solution.zip`: parent-only unmanaged Solution,
  retaining the native Invoker connection-reference shape.
- `TandemRespondRequest-11.1.0.review.json`: source receipt, hashes and metrics.
- `validation.json`: local results and explicit native evidence boundaries.

Both import paths are **unimported**. Legacy child-reference resolution remains
a native gate. The companion avoids manual action construction if the existing
Solution import path is required. It contains only this new parent and the
existing connection-reference component; it never bundles or updates the child.

1. Record working flow/app IDs and versions and retain them unchanged. Review
   this version/build/hashes and the exact contract.
2. After setup gates pass, import **one** route in the existing permitted
   environment, disabled. Legacy: Import package, **Create as new**, distinct name
   `TandemRespondRequest 11.1.0 candidate`, existing SharePoint connection.
   Never select Update for the working flow. If child resolution fails, stop
   that route and review/import the companion through the existing permitted
   Solution path. New parent ID: `fd170a11-2aec-4bab-a3f1-38ed38f23211`.
   Stop on a collision/update prompt. Do not import both routes.
3. Read back/export the candidate. Verify the exact child reference and existing
   connection; all SharePoint actions retain native Raw Invoker authentication,
   with native `runtimeSource=invoker` and caller-provided run-only connection.
   The legacy reference uses explicit `source=Invoker`. Do not replace a missing
   token/reference with owner credentials.
4. Add only the candidate to a disposable copy of the owner app; refresh its
   action to establish actual positional binding. Enable for synthetic tests
   only after permission/identity gates pass.
5. Record imported definition hash, flow/app versions, connection source,
   fixture IDs and run references. No production switch follows from local tests.

Local reproduction (use a new empty output directory):

```text
python -m scripts.power_automate.respond_request --native-source <owner-native-export.zip> --output <new-directory>/TandemRespondRequest-11.1.0.zip
python -m pytest tests/test_respond_request.py -q
```

The source is the user-specified unmodified local
`TandemSharedValidation81_1_0_0_2.zip`; it is not committed. The generator rejects
an existing destination. No App import/export editing capability is assumed.

## Exact app interface

Original eight positions are preserved; the ninth is required for stable replay.

| Position | Property/title | Value |
|---|---|---|
| 1 | number / ParticipantId | Current participant positive integer; reference only |
| 2 | number_1 / RequestId | Selected Personal request ID |
| 3 | text / Decision | Exact Accept or Decline |
| 4 | text_1 / GroupName | Accept: nonblank, max255 |
| 5 | text_2 / ExchangeType | Accept: Language/Culture/Combined |
| 6 | number_2 / Capacity | Accept: integer Language2/3, Culture/Combined2–10 |
| 7 | text_3 / LanguageFocusIds | JSON positive-integer array, e.g. [1]; max100 unique |
| 8 | text_4 / CultureFocusIds | Same; shared rules determine valid focuses |
| 9 | text_5 / IntentId | GUID once per explicit action, retained on retries |

Decline sends empty strings,0,"[]","[]" at positions4–8; these acceptance values
are ignored. The same intent with changed typed actor/target/payload conflicts.
JSON whitespace is parsed away; retain array order on retries. A changed explicit
decision/payload needs a new GUID and is subject to the saved request state.

Minimal app binding sketch; adapt the actual imported action/control names:

```powerfx
// Explicit response action: freeze these values once, before submission.
Set(responseIntentId, Text(GUID()));
Set(responseRequestId, selectedRequest.ID);
Set(responseDecision, "Accept");
Set(responseGroupName, groupNameInput.Text);
Set(responseExchangeType, exchangeTypeSelection.Value);
Set(responseCapacity, Value(capacityInput.Text));
Set(responseLanguageJson, "[" & Concat(selectedLanguageIds, Text(Value, "0", "en-US"), ",") & "]");
Set(responseCultureJson, "[" & Concat(selectedCultureIds, Text(Value, "0", "en-US"), ",") & "]");

// Submit and retry use the SAME frozen values and GUID.
Set(responseResult, TandemRespondRequestCandidate.Run(
    currentParticipantId, responseRequestId, responseDecision,
    responseGroupName, responseExchangeType, responseCapacity,
    responseLanguageJson, responseCultureJson, responseIntentId
));
Refresh('Connection Requests');
If(responseResult.success,
    Notify(responseResult.message, NotificationType.Success),
    Notify(responseResult.message, NotificationType.Warning)
);
```

The selected-ID tables here have one numeric column named Value; adapt the actual
SelectedItems ID column. The result must be a scalar numeric array, not a JSON
record array. Verify it in the disposable app. This sketch is not a saved
app change/binding proof. Disable duplicate submit while outstanding; retain the
intent after timeout. Refresh authoritative displays after every outcome.

Outputs preserve `success` Boolean, `message` text and `groupid` number, with
additive text `resultcode` and `operationkey`. Failure always returns false and
groupid0. Accepted alone is incomplete: require request OperationComplete and
group SetupComplete. Provisional Active rows count physically but become
operational only through both markers. Sender-facing screens need the same gate;
their full layout belongs to the App ticket.

## Token, commit and bounded recovery

`OperationKey=respond:{trustedRecipientId}:{lowercaseIntentGuid}`.
`AttemptToken` is a fresh native `guid()`. `WriteOwner` is the plain string
`OperationKey + ':' + AttemptToken`. Other writers only compare empty/exact
strings; they do not parse prefixes for authority. `SealedAttempts` is a JSON
array of UUID strings, blank→[]. Cap three sealed attempts; no TTL/lease takeover.

Personal Pending-only CAS saves the winner with the exact request ETag. Decline
atomically saves Declined/complete and `ConnectionKey=history:{requestId}` and
does no acceptance work. Accept retains the live key until completion and creates/
reuses one unique SourceRequestId group, with WriteOwner already set on create.
Group claims/publication/release use exact ETags. Episodes use
`request:{requestId}:participant:{participantId}`; exact group/party/key/Active/
JoinedAt/LeftAt readbacks reject foreign/Left episodes. No alternate keys or revival.
Publish Open if capacity>2, Closed if full, only after both memberships are exact.

PAIR and GROUP run before decision and again before publication. PAIR must return
eligible=true. GROUP receives both proposed initial members, Closed/incomplete
and focusSharersAvailable=false; its join-only compatible flag is correctly false.
The initial-creation gates are purposeValid and capacityValid. Every declared
focus still requires a sharer/distinct learner and every member participates,
through the maintained child. The parent checks transport/code/contract1/rules1/
authorizesAction=false, never child success alone.

Current raw REST profiles map to the shared contract; complete catalogues supply
Active=true IDs. Resolve Any by ISOcode=any including inactive rows; absent→null.
Optional time zone remains null. Recipient account ownership is rechecked.
Fresh profile ETags are compared after evaluation. Parent retains operation
authority, CAS, unique writes and guard. Cross-item eligibility is not an atomic
SharePoint transaction: facts can change after their final read. All group writers
must share the guard; readers must honor both commit markers.

Only a definite rejected member create (HTTP400/401/403/404/409/412/422) plus
successful complete unique-key absence read establishes the automatic stopped
prefix. Earlier effects have exact readbacks; native writes are serial with
connector retry disabled. Seal attempt/Retryable then release the exact token.
A new run can CAS-claim, finalize failed sealed-token release, revalidate and
reuse the source group/first episode. The old attempt has no later domain-write
path. Timeout/429/5xx without exact saved-row readback retains Uncertain/ownership
for exceptional settled-run/data inspection. An exact stable immutable create
readback can reconcile a lost create response in the same run.

After committed request/group/two-member readbacks, save/verify completed receipt,
release/verify matching token, then return success. Failed release returns false.
Completed same-intent replay only finalizes that saved token and returns historical
result; later edits/Ended/Leave are not reapplied or reversed. No rollback/delete,
fake Accepted-incomplete success, scheduler or generalized recovery platform.

## Parent 81 drift ledger handoff

This introduces consumer IntentId and its business commit/recovery contract.
Shared child/rules/schema baseline/normalization source and runtime build/hash
are unchanged. All ten finalized parent receipt fields are consumed exactly;
no schema additions requested. Closed #9/#12/#66 proofs are preserved.

The owner prohibited shared/common source and issue edits; this section is the
reviewable #81 description/change-ledger handoff. Parent integration should add
this consumer version/build/hashes from the review JSON and its own cross-flow
results. Generator changes do not update imported flows.

| Evidence | Status |
|---|---|
| Generated WDL + fake SharePoint + real shared graph | Local results in validation.json |
| Shared runtime/schema/rule implementation delta | NONE; no shared rebuild |
| Legacy / parent-only Solution native import | NOT RUN |
| Power Apps binding/trusted caller/private authority | NOT RUN |
| Native Accept/Decline/replay/race/fault/cross-flow | NOT RUN |
| Ordinary participant permission/privacy | DEFERRED by owner |
| Notification delivery | Separate #49/#21; no channel selected |

## Native smoke and acceptance

Prerequisites/account: complete the gates above; use owner/synthetic fixtures.
Record actual authenticated SharePoint ID and resolved profile. Create synthetic A
sharing language L and B learning L, both Active validation/participation and open;
leave time zone blank. Create Personal Pending A→B, empty winner/completion false
and verified live connection key. Record exact fixture IDs/keys/before snapshots.
Never reuse real records32/38: those numbers are synthetic in local tests.

Use this build unless a separately versioned disposable fault copy is specified:

1. **Decline:** as B, blank unused Accept inputs. Expected UI Declined; true/0;
   Declined/complete/history key, complete receipt, zero groups/members. Sender
   refresh sees truthful terminal history.
2. **Accept:** capacity3 and L. Expected ACCEPTED, exactly one source group/two
   distinct Active episodes, correct persisted focuses, Open/SetupComplete,
   Accepted/OperationComplete/history key, complete receipt and blank WriteOwner.
   Repeat fresh capacity2→Closed/full.
3. **Culture/Combined:** culture-only sharer/distinct learner, languages[], total
   capacity2–10 succeeds. Combined needs both relationships. Missing sharer/
   distinct learner, unrelated member, Any/unknown/inactive focus or fractional/
   out-of-range capacity fails without successful publication.
4. **38/32 negative:** synthesize both learning L/no sharer. Shared transport OK
   is insufficient; false with Pending and no group. No claim about real records.
5. **Authority/type:** sender/nonrecipient/forged ParticipantId/Group request
   fails without domain effects. Ordinary-user isolation tests stay deferred.
6. **Race/CAS:** Accept vs Decline and Accept vs Accept with distinct intent GUIDs
   against one Pending request: one winner; loser cannot overwrite/create another
   group. Force stale request ETag; conflict/no overwrite. Capture both runs.
7. **Freshness:** in a disposable fault copy, pause sender or rebind recipient
   between initial/Fresh/Last reads. Expected false and unpublished/incomplete
   group with provisional history preserved. A change after the final read is
   an explicit cross-row limitation, not an atomic reservation claim.
8. **Partial/retry:** safely reject second member create with returned403 and
   prove complete absence. Expect first episode retained, sealed/Retryable and
   released matching guard. Remove rejection and retry same intent: reuse group/
   first episode, finish two. Three sealed attempts require assistance.
9. **Unknown/readback:** timeout/5xx without exact saved row or failed/paged final
   readback returns false/0. Unknown retry cannot steal. Native fault injection
   availability is unproven: mark these BLOCKED if no safe disposable mechanism.
   A failed Compose is not genuine native timeout proof.
10. **Replay/integrity:** completed replay is historical/no domain writes or child
    evaluation. Edit/end group then replay: no reversal. Same intent/changed payload
    conflicts. Completed receipt/failed release returns false; settled retry only
    releases its old token. Wrong token/source/party/key or Left never overwritten.
11. **Cross-flow:** parent tests #13/#14/#65 concurrent writers. No foreign-token
    steal, stale group CAS cannot publish, provisional slots count and readers
    honor completion. Native parity remains NOT RUN until versioned evidence.

Failure interpretation: false never means rollback. DECISION_CONFLICT means
refresh the saved winner. PROCESSING_OR_ASSISTANCE/Uncertain needs settled-run
inspection. Correct validation/input failures and create a new explicit action
after refresh. Never repair by clearing arbitrary tokens or deleting history.

Cleanup: capture evidence first; disable/remove only the candidate app/flow/fault
copy. Remove only exact synthetic IDs from the fixture ledger after runs stop,
using approved owner tools. Preserve production data/history; no cleanup writes
are included in the package.

Return version/definition hash, imported connection source, permitted account/
resolved-ID evidence privately, fixture/intent keys, outputs, paired race run
references and exact request/group/member/receipt readbacks/ETags; include blocked
cases and cleanup record. Exclude tokens/cookies/emails from committed reports.
