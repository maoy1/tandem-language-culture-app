# #13 TandemUpdateGroup v1 handover

[#13](https://github.com/maoy1/tandem-language-culture-app/issues/13), under [#45](https://github.com/maoy1/tandem-language-culture-app/issues/45). Parent owns #81 receipt setup, native Solution assembly, ledger/issue updates and integration. No owner action or tenant change is requested now.

## Exact version and gate

Build **55d4d4c3-958d-48a1-ac0e-a20fdea8ad1f**, **250 action definitions / depth5**, within500/8 across all branches and control containers (not execution counts). Native import/caller/member authority/writes/races/app binding are **NOT RUN**; ordinary-participant tests remain deferred. Local results/hashes are in validation.json.

- `TandemUpdateGroup-v1.parent.json`: complete readable parent document, including trigger, SharePoint binding, actions, Respond schema and body. SHA256 `3a1798ac11460a3d6d0348ba4f6e5752cf0fd055ed0316345c6e0169d71934a2`.
- `TandemUpdateGroup-v1.zip`: legacy-format owner prototype, SHA256 `593f01560f346d65d56d6d4f6c3549773956c6dbc4638fa49efec511bff5afa4`. Import-format artifact only, not native deployment certification. Parent batch owns final native Solution assembly.
- `TandemUpdateGroup-v1.review.json`, `validation.json`, `config/update_group_flow_contract.json`: exact version, IO, mapping, native/dependency state, tests and drift assessment.

Default receiptListId=null means **resolve the approved exact unique title TandemOperationReceipts**, not a configuration failure. Parent imports the Solution once with business flows disabled, performs Setup Apply+Audit, then enables/tests this same imported flow. **No regeneration/reimport or preknown GUID is required.** Optional actual GUID pinning remains available. Normal operation reads current ID/title/BaseTemplate/entity type and receipt rows; an absent/malformed store fails closed. Target resolution does not certify all tenant schema/settings, and schemaSetupVerified remains an informational false flag, not an enable gate.

## Exact IO

One required Power Apps V2 Text input `text` / RequestJson; wrapper max8000 characters:

```json
{"actorId":38,"groupId":10,"expectedETag":"\"7\"","intentId":"01234567-89ab-cdef-0123-456789abcdef","edits":{"Title":"Practice group","Purpose":"Plain description","Capacity":3,"State":"Closed"}}
```

All listed properties are required. Both envelope and edits reject unexpected properties. Only Title/Purpose/Capacity/State can be edited. Title is nonblank/max255 characters. Purpose is optional in content (empty string allowed), plain text/max2000 characters; native blank Note readback normalizes to empty string. The 2000 bound is a technical API bound for the approved brief description; **no SharePoint Note limit or schema setting changes**. Capacity is strict integer Language2/3 or Culture/Combined2..10, at least all physical Active rows. State is exact Open/Closed/Ended; fresh edits only from Open/Closed, Ended final. No automatic close/reopen/end follows a count change. Type/focus/source/setup/system fields cannot be supplied or patched.

Outputs: Boolean success; Text resultcode/resultjson/groupjson/etag/errormessage/runreference. Successful codes UPDATED or REPLAY require positive completion/release proof. `resultjson.saved` is the immutable historical receipt result (old saved values, original domain revision and member count). `groupjson` is the current captured public snapshot `{groupId,title,purpose,capacity,state,etag}`; output etag matches that exact snapshot after release if performed. Thus an old receipt can replay without undoing a later edit or presenting its revision as the current snapshot. Refresh before a new deliberate edit. Failed/unknown output never claims no effect; backend details, raw accounts, receipts and owner tokens are excluded.

## Connection and field mapping

Site `https://reedelsevier.sharepoint.com/sites/OG-TandemOrg`; standard SharePoint key `shared_sharepointonline`, source Invoker, no embedded owner fallback. Raw authentication preserves the existing inspected X-MS-APIM-Tokens/$ConnectionKey expression. Select an existing allowed connection, Run-only provided by run-only user. Parent native assembler uses the already-inspected #81 connection adapter/seed. This legacy parent does not certify native caller propagation. No new connector, licence, sign-in, paid service or deployed Python runtime.

Participants `fd3adf46-f81d-4a7b-a80c-567fde0175dc` (ParticipantaccountId -> same Invoker currentuser); Groups `4bf1b37f-edce-40c5-8fa0-36543a2d0cd6`; Group Members `db611ec3-7fa3-477a-878e-effbbb195cb8`; Requests `3d17485d-1dac-41f0-a1af-24e45daa4567`. Existing #12 metadata is retained; this flow's native authority/write proof is pending.

Default receipts resolve `_api/web/lists/getbytitle('TandemOperationReceipts')` and validate current metadata ID/title/BaseTemplate/ListItemEntityTypeFullName. Optional actual GUID pin uses that GUID and verifies its metadata identity/title. Parent target SHA256 `f189c44795dd448faaf7c8a0087b3aeed6357b264f21f8cb4e8860955b308495`. Ten custom fields: OperationKey, IntentJson, ResultJson, Complete, Uncertain, Retryable, DomainEffects, AttemptToken, SealedAttempts, Stage. OperationKey must be required/unique/indexed. Creates additionally populate standard built-in Title with OperationKey; parent verifies it remains writable. No custom eleventh field or schema setting is added. Parent Setup Apply+Audit owns full field/Note/access verification and unique-title validation before business enablement; runtime metadata resolution alone is not schema certification.

## Authority and coordination

Identity: same Invoker currentuser -> exactly one own ParticipantaccountId -> actorId equality before group/request/receipt data reads. Group-control authority: SetupComplete group with completed Accepted personal source, current physical Active membership and exact canonical request/participant episode whose completed Accepted request has the correct personal-source parties or group target/sender. Raw provisional Active is not authority. Read group, memberships and exact source/episode requests again under the claim. Exact episode reads avoid scanning growing request history.

**Personal Paused/Inactive/openness/validation does not remove operational membership authority.** No Discovery available-actor guard, profile normalization or eligibility matching is reused. No child call is needed for these operation guards. All physical Active rows, including provisional rows and paused participants, count toward capacity; no availability filtering creates a slot. Paging, >10 physical rows, malformed/missing proof or duplicate actor episode fails closed.

OperationKey = update:trustedActor:lowercaseIntentUUID. WriteOwner and AttemptToken contain the same compact serialized `{operation: operationKey, attempt: freshServerGuid}` object. Other writers treat nonempty ownership as opaque/busy and release only their own exact saved token with a fresh ETag. No lease, expiry, takeover timer, scheduler or lock platform. All writes disable automatic retry.

Write order: immutable receipt unique create/readback -> exact expected-ETag group claim/readback -> fresh operational authority/count -> persist possible-effect marker -> exact-ETag patch of only the four allowlisted fields -> exact field/immutable/token/changed-revision readback -> completed receipt CAS/readback -> exact own-token release/readback -> success. DomainEffects=true/Uncertain=true is conservative before attempting the edit, not proof it happened. Successful completion clears Uncertain. Known no-domain rejection completes a Rejected receipt with DomainEffects=false; it releases only a confirmed owned token. A changed revision plus different token positively rules out a delayed original stale CAS, permitting rejection without touching that foreign owner.

Generic502/timeout/readback failure never implies saved or no effect. Incomplete receipts never resume domain mutations, regardless of flags or elapsed time. Unknown effects retain ownership for reconciliation/exceptional support. Completed receipt plus failed release can finalize only its exact old-token release on current-authority replay, with no second edit. Other current ownership remains untouched. Changed payload/group/revision with the same operation key conflicts; completed saved results, including terminal rejections, replay without applying another domain change.

## Builder and minimal unpublished app call

`build_parent_document(site, people, groups, batch, build_id, receipt_list_id=None)` clearly returns the **full parent**, with trigger and response. Parent can use its trigger/actions through the existing native invoker_parent_document adapter and inspected seed. Shared files are not edited.

```powershell
python3.13 -m scripts.power_automate.update_group_flow --output <fresh-output>.zip --batch-contract <parent-config/batch_schema_contract.json>
# Optional actual GUID pin only if already available; default title mode needs no post-setup rebuild:
python3.13 -m scripts.power_automate.update_group_flow --output <fresh-bound-output>.zip --batch-contract <parent-config/batch_schema_contract.json> --receipt-list-id <verified-guid>
python3.13 -m pytest tests/test_update_group_flow.py -q -p no:cacheprovider
python3.13 -m pytest tests -q -p no:cacheprovider
```

Use an unused stem; builder refuses overwrite. Python is optional local build/test tooling only. Old inaccessible cache directories were left untouched. ID binding alone is not schema/permission proof.

```powerfx
Set(varUpdateIntent, Text(GUID()));
Set(varUpdatePayload, JSON({actorId: varOwnParticipantId, groupId: varGroup.groupId, expectedETag: varGroup.etag, intentId: varUpdateIntent, edits: {Title: txtGroupName.Text, Purpose: txtGroupPurpose.Text, Capacity: varChosenCapacity, State: varChosenState}}, JSONFormat.Compact));
Set(varUpdateResult, TandemUpdateGroup.Run(varUpdatePayload))
```

Use Studio's actual imported alias. Keep payload/UUID unchanged on transport/unknown retry; refreshed snapshot/new UUID only for a new deliberate edit. Full screen/navigation remains #68. App editor/import/binding has not been executed or claimed proven.

## Future native test handover — NOT RUN

Prerequisites/account: parent verifies all ten receipt fields, standard Title writeability, unique OperationKey, plain JSON Notes, actual ID and existing allowed Invoker read/write authority; existing #12 group/member metadata; every capacity/state/membership writer obeys the same group guard. Parent records exact bound build/hash/Solution version before testing. Use owner/synthetic data; ordinary-participant privacy tests remain deferred. Do not infer actor authority from admin group permissions or add individual routine grants/approvals.

Fixture: two permitted operational members and disposable coherent groups with current ETags; SetupComplete=true, completed Accepted source, canonical Active membership episodes with completed Accepted request proof. Raw Active/incomplete real rows are not sufficient. Parent supplies a valid committed fixture through its permitted acceptance/harness path. Separate disposable groups for Ended tests, since ordinary reopening is forbidden.

1. One-import smoke: parent imports the assembled Solution once using existing Invoker bindings, leaving business flows disabled; parent Setup Apply+Audit creates/verifies the exact unique receipt store and fields. Then enable/test this same imported UpdateGroup. No regenerate/reimport/GUID insertion is needed in default title mode. Use the actual imported alias/build/hash. Runtime missing/invalid metadata fails closed without business writes; the local same-graph absent-then-present test covers that transition. The legacy ZIP is an optional owner prototype, not an extra required import. Never overwrite a working flow or publish untested bindings.
2. GRP-008/009/014 and AUTH-001: each operational member edits the allowed fields with current ETag/new UUID. Expect UPDATED, only those edits persisted, completed exact receipt, owner released, matching groupjson/etag. Repeat with actor personally Paused/Inactive/openness=false: still authorized. Spoof/non-member/provisional episode denied with no domain edit. Return outputs plus sanitized episode/source references.
3. Bounds/immutability: Title255/Purpose2000/empty Purpose accepted; blank name/256/2001/fractional or out-of-type capacity/unknown state rejected. Extra type/focus/WriteOwner/source/setup/arbitrary properties reject before writes. Participant/membership and all immutable group fields remain unchanged. No schema setting adjustment is part of the case.
4. GRP-010/012: type capacities and >=all physical Active rows enforced, including provisional/paused members. Closed with free slots stays Closed; explicit Open does not auto-close by count. Join admission is a separate receiving-flow guard. Under a disposable controlled race, add a physical row or remove authority between preliminary read and under-claim reread: no edit; settle only the positively known no-domain result and exact own release.
5. GRP-011: Open/Closed -> Ended; new edit/reopen rejects. Completed original intent still replays historically. Never reopen Ended as cleanup.
6. Revision/race: stale ETag/busy token rejects; concurrent claims using the same old revision yield one owner. Never overwrite/clear a foreign token. Native races across actual other writers are pending integration, not inferred from fake CAS tests.
7. Replay: same exact payload -> REPLAY, one domain edit; changed title/group/capacity/state/revision with same key -> conflict/no second edit. Make a later distinct edit then replay the old intent: saved result stays historical, current snapshot stays later, other ownership untouched.
8. Faults only in an isolated copy/harness: lost success responses may reconcile only by exact state. Unknown post-edit/readback retains ownership and cannot repeat the edit. Completed receipt plus failed release may finalize only that exact old release. A missing response/row is not no effect. Never force-clear unknown ownership, delete receipts, roll back history or use elapsed time as recovery authority.
9. Cleanup/evidence: remove temporary unpublished controls/bindings, restore only permitted nonterminal fixture/profile choices through normal flows, retain receipt/request history and Ended groups as agreed. Unknown attempts require exceptional settled-run reconciliation. Return Respond Outputs, exact account role/build/Solution/parent run, group/receipt IDs, sanitized field/ETag/count/release checks and every FAIL/BLOCKED/NOT RUN. Exclude raw accounts/tokens/emails. Preserve the working app/flows.

Blocked native tests until parent setup/integration: one-time schema audit and unique-title/access proof, owner/current-member/cross-account authority, real state/capacity/race/fault and app-call tests. No preknown GUID or rebuild dependency exists for default title mode. No Ready/Done or release claim; #13 stays open.

## #81 drift ledger for parent

Only the new #13 operation parent/guards change. Shared schema/normalization/compatibility source, contracts, versions and deployed child are untouched. No profile matching duplicated. The parent's ten-field receipt target is consumed by snapshot/hash; no schema setup applied here. Parent records build/hashes,250/depth5, local tests, technical Purpose2000 bound, built-in Title write mapping and native NOT RUN statuses in #81/#13 when integrating. Existing #9/#12/#47/#81 proof remains historical/scoped. No push/issue update or #10 change from this branch.

Final #13 local verification: **116 UpdateGroup tests / 473 repository tests PASS**; final parent **250 definitions/depth5**, ZIP/full-document/source hashes PASS. Same default title-resolving graph passes absent-store failure then post-setup success without rebuild; optional GUID pin/metadata failures tested. Native schema/caller/authority/write/race/app tests NOT RUN; one-import parent Setup Apply+Audit then enable/test remains the deployment sequence.
