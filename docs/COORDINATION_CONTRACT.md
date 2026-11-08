# Shared conditional writes and bounded recovery — #47

**In progress / draft.** This is the bounded shared protocol and isolated reference
proof, not an acceptance engine or deployed lock service. Python is optional local
test/build tooling only. No new production lists/fields/flows have been applied.
Live readers/actors, #12 mappings and actual cross-item fixtures are still gates.

## Why one shared guard is needed

An ETag on Request A cannot prevent Request B taking the same group's last slot.
Independent trigger concurrency=1 is per-flow, not coordination across flows.
All capacity/state/membership writers must use the same **group ownership token**.
One durable **operation receipt** saves the immutable intent/result so transport
replay cannot create another logical result or replay an old capacity/state edit.
No lease timeout, scheduler, distributed transaction or guaranteed repair daemon.

## Minimum proposed metadata — not applied

| Target | Purpose / constraints |
|---|---|
| OperationReceipts | One row per stable intent; required unique OperationKey; immutable typed IntentJson; stage/result/reference and attempt metadata |
| Groups.WriteOwner | Operation + attempt token in one field; per-item ETag claim/release; no expiry/takeover |
| Requests.SendOperationKey | Unique immutable send intent, including unknown/delayed create retries |
| Requests.ConnectionKey | Required unique nonblank live connection key; retained for Accepted-incomplete, history key only after settled result |
| Requests.WinningOperationKey / OperationComplete | Winning terminal decision and durable completion marker; Accepted alone does not prove setup finished |
| Existing SourceRequestId / MembershipKey | Verify actual unique/indexed identities before use; no blind constraint enablement/backfill |

This is one-time technical setup, not routine individual administration. Current
tenant mappings/permissions for these proposed fields/store are not assumed. #12
verifies group/member mapping; request-owning builders verify their metadata.
Use native JSON equality for frozen canonical intent. The local model's SHA is a
convenience, not an extra crypto API/connector dependency or actor authorization.

## Stable intent and history

Client creates one intent UUID per explicit user action and retains it for network
retries. Server scopes it to the verified actor and kind; client IDs do not confer
authority. A changed target/payload with the same operation key is a conflict.
Replays of a completed receipt return its saved historical result, then consumers
refresh current state; they never reapply that old edit after a later operation.

Pending personal connection key uses sorted participant IDs; group-join key uses
group + participant. Request creation needs both SendOperationKey and ConnectionKey
uniqueness. Terminal Declined/Cancelled releases the live key atomically with its
Pending-only CAS. Accepted-incomplete keeps the live key until setup commits.
SourceRequestId identifies one new group, MembershipKey identifies one membership
episode. Retried creates reread exact key/group/party/content; they do not infer
success from a duplicate HTTP code alone or ever revive a Left episode.

## Required write order

1. Establish authoritative actor/role and fresh complete data through the consuming
   flow's verified adapter; immutable receipt intent/result alone is not permission.
2. Get or create the unique operation receipt. Completed -> saved result; incomplete
   with another live/uncertain owner -> explicit Processing/Busy, not success.
3. For existing-group mutations claim WriteOwner with exact read ETag. Every
   writer, including capacity/state changes and Leave, uses this same group row.
   For initial personal acceptance, Pending request decision + unique SourceRequestId
   permit one incomplete group; acquire that group's guard before membership writes.
4. Under the guard, reread group/state/capacity, current memberships, request and
   required profile/focus/availability facts (#9). Count all Active rows including
   provisional rows/paused participants; do not silently filter a slot into existence.
   Complete-read or integrity failure is explicit, not partial-success admission.
5. Pending-only ETag request decision picks one Accepted/Declined/Cancelled winner.
   Cancel/Decline cannot reverse Accepted-incomplete. Accept that loses the CAS
   cannot create membership. No automatic unavailable-request cancellation policy.
6. Write expected parties/episodes only. Creates use stable unique keys; changes
   use exact ETags and no automatic write retry. Wrong source/party/group or Left
   episode is conflict/support, never a new key to bypass the mismatch.
7. Read back exact required group/request/membership result, fit and capacity;
   set request completion only with a consistent result. New group publishes
   SetupComplete after its required memberships; existing group state is preserved.
   Provisional rows count toward capacity but are not operational until committed
   accepted source plus complete group. Readers must implement those gates.
8. Save completed receipt, conditionally release only the matching ownership token,
   and verify before reporting success. A failed result/read/release is not success.
   No row deletions or historical-state reversal as a pretend rollback.

## Bounded recovery

- A deterministic conflict before any domain effect can return Rejected and safely
  release the guard. Never label a post-write or unknown-outcome failure no-effect.
- At a **stopped definite-error boundary**, after all earlier writes are reconciled
  to known stable keys and no I/O remains outstanding, persist a sealed attempt /
  Retryable stage, then release. A new user retry uses the same intent and reuses
  existing rows. A sealed attempt cannot write/reacquire; cap at three sealed
  attempts before rare assistance. If release failed after seal, its known sealed
  token can be finalized before the next claim without repeating domain writes.
- A timeout/missing row does not prove no effect. Unknown writes retain ownership;
  no automatic TTL/lease steal. Reconcile unique-key writes/readbacks first; if not
  provable, explicit exceptional assistance verifies settled runs/data before repair.
- Completed receipt but failed release can finalize exact old-token release without
  redoing memberships/state. Normal user retry does not promise automatic repair
  for every interruption. Never clear another live owner's token or erase history.
- Leave marks the current episode Left and preserves Closed; capacity cannot drop
  below counted rows; Ended remains final. Group update/Leave on incomplete setup
  is not an ordinary action. No reopening, rejoin or replacement automation.

Native consumer catch scopes must positively prove the stopped/known-prefix
condition before sealing; an app boolean cannot supply that evidence. The local
reference models that boundary as a precondition, not a proof of an HTTP timeout.

## Proof boundary and current evidence

Source/helper: scripts/power_automate/coordination.py. 27 protocol reference tests
plus 4 preflight tests; whole suite **152 passed**. Includes all **70 order-preserving
two-acceptor schedules** for one slot, competing terminal decisions/cancel, send
replay/reverse duplicate, partial initial group/membership, hidden provisional rows,
unknown owner/no TTL steal, bounded sealed-prefix retry, capacity writers/Leave,
stale completed-intent replay, receipt/release failure and committed event uniqueness.

Reference store explicitly assumes atomic per-row CAS and unique constraints,
fresh authorized adapters and all writers obeying the guard. That is **not native
SharePoint cross-list runtime certification**. Existing ETag owner tests (#61 and
earlier probes) support the single-row mechanism only. Native last-slot/uniqueness/
fault fixtures and actual metadata mappings remain unproven. Expected server error
codes and unknown-outcome readback handling must be verified, not guessed.

A unique terminal notification fact is emitted only after a committed receipt.
External delivery exactly-once is not guaranteed by that fact: #49 chooses channel,
#21 proves retry/idempotency/ambiguous delivery behavior. NOT-002 delivery stays gated.

## Read-only prerequisite preflight

Package TandemCoordinationPreflight.zip has **5 actions / depth 1** (limits 500/8).
It reads site technical ID and effective web permission metadata only using the
existing SharePoint connection. No fixture/list/field/item creation, row reads,
production edits or permission changes. Build/review beside ZIP. Import/run NOT RUN.

Full operator steps and checkboxes are directly in issue #47. Return Preflight_report
JSON. permissionMetadataCollected and fixturePermissionGatePassed distinguish known
metadata from missing rights. A passed permission mask is a prerequisite, not proof
that a future fixture was created or an atomic protocol works.

After that gate, prepare a **separate, explicitly tagged disposable fixture** with
synthetic rows only; verify its actual native unique-key/CAS/readback behavior
before production builders rely on it. No fixture writes until prerequisites are
verified. Cleanup must target only the verified fixture ID/tag; no production data.

## Consumer ownership

#10/#17: send keys and duplicate connection reservation. #11: initial acceptance /
group/membership commit. #13: same guard for state/capacity; #14: same guard for
Leave. #63: Pending-only cancel CAS. #65: existing-group join/last slot using the
same guard. #19/#20/#23 and #39–#42 own authority/private data bindings; #12 actual
group/member metadata. No silent client/caller substitution or new paid dependency.
Shared #47 can finish on its own reviewed contract and bounded proof; it does not
wait for every consumer to finish, nor certify them from reference tests alone.
