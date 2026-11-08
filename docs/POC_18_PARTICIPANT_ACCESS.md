# POC-18: self-service access in small steps

Status: #39 read-only assessment resumed at owner request after the unique-column/creator-only setting conflict was reconfirmed. Ordinary-colleague proof remains pending; prior evidence is retained in PR #43. No architecture is selected and no live
permissions or app connections have changed. #18 is the registration-access
parent. This planning PR closes none of the access tickets.

## Operating rules

Registration, updates, joining, discovery and connecting must be self-service.
No routine admin approvals, per-person grants, manual participant account
creation, manual matching or manual group maintenance may be required.

These restrictions apply to ordinary operations in this trusted internal app.
Critical or exceptional cases may involve necessary admin approval, correction
or assistance. Minimize admin workload as participation grows; do not make every
new user or ordinary action a manual task. This permits exceptional intervention
without changing the agreed own-profile access rules or adding a routine approval
workflow.

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
- No public directory or extra discovery list is approved. Exact Discovery fields
  remain undecided; participant fields including Comments are generally eligible,
  admin/system-only information excluded. The proposed Comments notice is removed.

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
Finalize candidate display fields with #7/#42 using the reviewed field contract;
exclude admin/system-only data and impose no Comments notice for now. Reject arbitrary identities, record IDs
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


## #39 assessment evidence — 2026-10-31

Read-only browser inspection; no flows were created/run, no settings saved and
no participant records opened. UI availability is not a successful permission test.

| Check | Observation | Meaning |
|---|---|---|
| Actual Participants list | Settings identify the existing Participants list; it contains extra legacy/helper columns beyond the repository schema | Preserve current data; do not delete or migrate columns during assessment |
| List permissions | Inherits parent permissions; Members have Edit, Visitors Read, Owners Full Control | Current inherited list roles do not enforce own-profile-only access; effective per-item access and group membership are not yet tested |
| Permission tools | Stop Inheriting Permissions and Check Permissions are visible | Potential setup control exists; no change attempted and no assertion of effective change rights |
| Existing environment | Power Automate default environment loads; existing Tandem submission and seed flows are listed | Maker can view existing flows; no conclusion about all participant capabilities |
| Existing instant flow | Time-zone seed flow has a SharePoint connection and run-only settings; no run-only audience currently assigned | Reuse no existing seed flow for user access; its sharing is not a self-service proof |
| Connection modes | SharePoint selector offers Provided by run-only user and Use this connection; current value is caller-provided | Configuration capability observed on an existing instant flow only; Power Apps-triggered behavior and secure caller identity remain unknown |
| Current user's licences | My Licenses lists Power Automate for Office 365 and Free | No premium or all-user entitlement is established by this observation |
| Policy visibility | Admin center allows viewing policies, explicitly denies policy creation/editing privileges, and hides non-owned environments from policy scope view | Applicable policy and allowed connector combinations cannot be established from this account's scope view |

No personal identifiers, policy-owner names, tokens, employee rows or full tenant
policy exports are included in this record.

### Approach comparison and decision

| Approach | Assessment result |
|---|---|
| Existing app filter/direct list permissions | Does not meet the agreed underlying access requirement |
| Built-in creator-only list settings | Previously rejected by this tenant with unique columns; keep unique identity, do not retry by removing it |
| Automatic per-item permission flow | No manual per-person grants in principle, but creation-window exposure, failure handling, identity protection and self-onboarding are unverified; not selected |
| Private list with authenticated registration flows | Candidate for further assessment; requires verified caller identity, connector policy, audience/licensing, ownership and app changes; not selected |
| Different backend/custom service | Adds permissions, hosting/licensing and operational requirements not yet available; no migration proposed |

Decision: no-go for #40 yet. No approach has all prerequisites verified. The next
check is factual confirmation of the applicable environment policy, connector
combination and intended-user entitlements, not permission expansion.

For the flow option, check SharePoint together with the proposed identity method
(Office 365 Users if used), Power Apps-triggered run-only behavior, and a supported
invocation-bound caller identity. Do not treat the connection-mode selector or
an email input as proof. Confirm app/flow audience access permits self-onboarding
without routine individual grants or manual group maintenance.

One-time setup, if an approach is later selected: isolated proof resources,
explicit audience/connection configuration, and eventually permission cutover
with data preservation. Recurring dependencies to resolve first: connection
ownership/renewal, flow failures and policy/licence changes. Do not imply zero
operational maintenance or accept per-participant manual repair as normal use.

Reference for interpreting connection modes:
[Microsoft: run-only flow connections](https://learn.microsoft.com/en-us/power-automate/create-team-flows).
This supports the feature description, not this tenant's policy, licensing or
the security of an unbuilt registration flow.


## #39 resumed assessment — 2026-11-08

#47 and #12 are Done after merged PRs #75/#76. #39 is the sole In progress
ticket; #7 is Planned with owner-preview evidence retained in draft PR #77.
#61 remains Ready for testing. Ordinary-colleague tests remain deferred.

The owner reconfirmed the tenant rejects creator-only Item-level Permissions
while this list contains a unique column. Keep Participantaccount required,
indexed and unique; do not retry that setting by removing uniqueness.
An existing automatically maintained audience group is UNKNOWN (owner answer).
Do not create a manually maintained participant group or invite people individually.

Preferred candidate for further assessment: a private Participants list behind
authenticated, allowlisted read/save and Discovery operations. The caller path
must identify the invoking user independently of the backend connection; approved
Discovery projection remains #7's responsibility. This is not a selected or
implemented access architecture. Production access flows require focused Flow
tickets before implementation, and app rebinding belongs to #41 after #40.

An after-save per-row ACL flow remains unselected: initial inherited exposure,
failed permission changes, managed identity/status edits through direct APIs and
growing unique permission scopes need proof, not just a hidden app control.
Private-list setup would be one-time admin work; connection renewal, failures and
policy changes remain exceptional operational dependencies to resolve explicitly.

### Metadata-only capability experiment

`artifacts/access_assessment/TandemAccessCapabilityProbe.zip`, build
`2983ab84-af52-46c4-b944-8b7613a4543e`: **15 actions / depth 2** (limits 500/8).
Readable definition/review accompany the ZIP. Uses only the existing SharePoint
connector with two connection aliases: exported caller Invoker authentication and
an explicitly selected Embedded owner connection for metadata only. It reads user
technical IDs, list/field and permission metadata; zero employee item reads/writes.
Mixed connection modes in one imported flow are NOT tenant verified.
Local validation: 205 tests passed, including 11 helper tests. No tenant import/run
or permission-write capability is claimed. Owner-only metadata success cannot
prove different ordinary-user identity separation or direct/API denial.

The helper always reports privacyVerified=false, audienceGroupVerified=false,
twoAccountContextSeparationVerified=false and proceedToPrivacyCutover=false.
Applicable policy and intended-user entitlements remain unknown; historical owner
Office 365/Free licence visibility proves neither. No new identity connector,
paid licence, service or participant sign-in setup is assumed.

Decision: **no-go for privacy cutover / #40** until the capability, audience,
policy/licensing and isolated proof prerequisites are resolved. The working app,
Discovery flow credentials and production list permissions remain unchanged.
The exact operator steps and test checkboxes are inline in issue #39.
