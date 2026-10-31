# POC-18: self-service access in small steps

Status: prerequisite assessment pending. No architecture is selected and no live
permissions or app connections have changed. #18 is the registration-access
parent. This planning PR closes none of the access tickets.

## Operating rules

Registration, updates, joining, discovery and connecting must be self-service.
No routine admin approvals, per-person grants, manual participant account
creation, manual matching or manual group maintenance may be required.

Every permission, setting, connector, connection, licence or configuration
prerequisite must be flagged to the owner and verified before dependent work.
Record one-time setup separately from recurring maintenance; neither is
implicitly approved. Unknown prerequisites block dependent implementation.
Owner decisions, explicitly identified one-time setup and acceptance testing
remain human checkpoints. Connection ownership, renewal and other recurring
operational dependencies must be disclosed before selecting an approach.

## Agreed behavior

- Registration exposes only the authenticated person's profile for create/read/update.
- Direct SharePoint list/item/API access cannot expose or change other profiles.
- Keep unique Participant account; administrators retain access.
- Clicking Discovery returns eligible candidates through a controlled operation.
- No public directory, extra discovery list or private-Comments classification
  is approved. Candidate fields will be agreed during discovery.

## Delivery sequence

| Stage | Ticket | Outcome | Timing |
|---|---|---|---|
| A | [#39: prerequisites](https://github.com/maoy1/tandem-language-culture-app/issues/39) | Establish the simplest supported approach and its exact setup needs | Next; assessment only |
| B | [#40: two-user proof](https://github.com/maoy1/tandem-language-culture-app/issues/40) | Two users automatically access only their own synthetic record | After A passes |
| C | [#41: registration integration](https://github.com/maoy1/tandem-language-culture-app/issues/41) | Apply the proven approach and retest the existing form | After B; before wider testing |
| D | [#42: discovery access](https://github.com/maoy1/tandem-language-culture-app/issues/42) | Return candidates without granting general participant-list access | With #7–#9, after C |

One child ticket, branch and PR at a time. Update evidence, documents and
pending tenant checks in the same PR. #18 closes after A–C are delivered and
verified. D remains separately open until discovery integration passes; it is
not required to finish private registration. A planning PR completes none of
these implementation stages.

## A: check before configuring

Inventory current app/list permissions and environment capabilities without
changing the working app or reading other participants' data.

| Prerequisite | Current status | Evidence needed |
|---|---|---|
| Authenticated caller identity | Unknown | Supported caller identity method; no trust in an app-supplied email |
| List/site permissions | Unknown | Available rights, inheritance, existing item shares |
| Connectors and tenant policies | Unknown | Permitted connectors and restrictions in the actual environment |
| User/automation licensing | Unknown | Entitlements required by each considered approach |
| App/flow audience and self-onboarding | Unknown | New colleagues join without individual grants or manual group maintenance |
| Setup and operational dependencies | Unknown | Exact settings, connection owners, renewal and maintenance requirements |

Do not ask the owner to create a flow or change permissions until requirements
are identified, flagged and checked. If a configuration experiment is needed
to verify a capability, explain its purpose and prerequisites beforehand and
keep it isolated from the working app and data.

Compare feasible approaches retaining unique identity. Authenticated flows
in front of a private Participants list are one candidate, not the selected
architecture: they can require changes to existing app reads/writes and add
connection/licensing dependencies. An after-save permission flow must also be
assessed for temporary exposure and permission failures. Neither is approved.

Finish A with a recommendation, verified prerequisite record and proceed/stop
result. If nothing meets the self-service requirements, report the constraint
before building a more complex workaround.

## B: one isolated proof

Using the verified approach, two normal accounts and synthetic data, prove
caller identity, self-onboarding, own-record create/read/update and admin access.
Try direct list/item/API access and tampered requests against the other record.
Users must not gain flow ownership or other users' execution data.
Do not change the working app. Record evidence and limits. Flag and verify any
new configuration dependency before proceeding.

## C: integrate the proof

Preserve records, unique identity and catalogue selections. Apply only the proven
access approach. Recheck save/reopen, multiple Teach/Learn selections, simultaneous
learner/sharer use and teach-only saving. Reject tampered identities and managed
fields; handle duplicate creates and update conflicts. Check inherited access,
old shares and old app paths cannot bypass protection.

Record cutover/recovery setup upfront and verify two normal accounts plus admin.
Registration must never routinely need per-person permission repair or approval.
Update the registration contract when the implemented path replaces the baseline.
Keep broader rollout paused until tenant evidence passes and is accepted.

## D: candidate access during discovery

Reuse eligibility/ranking in #7–#9, not a second matching implementation.
Agree candidate response fields there. Reject arbitrary identities, record IDs
and queries that could reveal all profiles. Candidate presentation is read-only;
search and connecting need no manual candidate grants or approvals. Verify
this path before discovery rollout while private registration stays protected.

## Evidence and status

- [x] Own-profile registration and candidate-only discovery rules agreed.
- [x] Stages A–D tracked in #39–#42.
- [ ] A: prerequisites verified and approach selected.
- [ ] B: isolated two-account proof passed.
- [ ] C: registration integrated and tested; parent #18 ready for closure.
- [ ] D: controlled discovery access tested with #7–#9.

No live access-control tests have passed. The working app still uses its
documented direct-connector/filter baseline. PR #38 is planning only.
