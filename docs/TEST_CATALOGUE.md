# MVP test catalogue

This catalogue turns the reviewed field contract into repeatable checks and
stable references for issue reports. It describes expected behavior, not proof
that a feature is implemented. Read MVP_FIELD_CONTRACT.md and CURRENT_DESIGN.md
for approved rules and outstanding decisions; record executions in TEST_RUNS.md.

## How to use this catalogue

- Keep IDs stable. If a requirement changes, record the old expectation, new
  expectation and linked decision; do not rewrite historical results as passes.
- Before testing, record app version/published time, flow version or last-modified
  time, relevant commit/PR, environment and test account role. Unknown is acceptable
  if explicitly recorded. The repository commit alone does not identify a live app.
- Record Actual separately from Expected: PASS, FAIL, NOT RUN, DEFERRED or
  REQUIREMENT PENDING. Distinguish owner-reported evidence from agent-observed or
  automated evidence. A blocked prerequisite is not a passing test.
- Verify and flag required permissions/licences/configuration before setup. Use
  existing SharePoint/Power Apps/Power Automate capabilities only; no paid test
  service, trial, extra hosting or ordinary-user permission expansion.
- Use an isolated app/list/flow copy and fictional profile data where possible.
  Synthetic profile names do not simulate authentication: cross-user tests need
  actual ordinary test accounts. Do not use owner/admin accounts as proof of
  ordinary-participant access.
- Do not run destructive or fault-injection tests on live participant data.
  Tag created test records and remove only identified disposable records after
  tests, through recoverable supported UI. Never bulk-delete participant lists.
- Keep screenshots/run links sanitized and restricted appropriately. Do not put
  tokens, raw Person claims, employee profiles or full flow payloads in GitHub.

## Execution layers

| Layer | Checks | Does not prove |
|---|---|---|
| Repository | Existing schema/registration validators and local tests | Live schema, deployed app or permissions |
| Synthetic flow | Controlled Compose/Filter/Select and business-flow cases | Authentication, real SharePoint normalization or published app |
| Integrated tenant | Published app with actual test lists, flows and account roles | Other environments/versions without retesting |

The schema JSON describes the desired POC-05 culture/optional-time-zone delta,
explicitly pending tenant setup/tests. Local checks do not exercise the live form.
New optional-time-zone/culture/status cases below are NOT RUN until implemented
and exercised at their specified layer.
The old BASE tests retain their original scope; do not relabel them as new-MVP tests.

## Reusable fictional fixtures

Use actual catalogue IDs from the isolated test lists, not assumed production
IDs. L1/L2 and C1/C2 below are symbolic placeholders, not pasteable values.

| Profile | Offers | Wants | Initial state |
|---|---|---|---|
| A | Language L1; culture C1 | Language L2 | Active, open, validation passed |
| B | Language L2 | Language L1 | Active, open, validation passed |
| C | None | Language L1; culture C1 | Active, open, validation passed |
| D | Language L2 | Language L1 | Needs review validation |
| E | Language L2 | Language L1 | Paused; open flag retained |
| F | Culture C1 only | None | Active, open, validation passed |
| G | None | Culture C1 only | Active, open, validation passed |
| H | Language L2 | Language L1 | Active but not open to connections |

For group tests use separate fixtures: an L1 language group with A and C, capacity
3; a C1 culture group with F and G; and a combined L1/C1 group with valid distinct
sharer/learner relationships for both. Start each case from its stated setup,
not from a prior case's mutated state. Create a second ordinary member when a
case needs independent responses; never share credentials or impersonate users.

## Original baseline checks

These IDs describe previously reported results only. See TEST_RUNS.md for scope
and evidence limits; they do not certify the target field contract.

| ID | Scenario | Expected in original baseline |
|---|---|---|
| BASE-001 | Save then reopen a profile containing Teach and Learn selections | Saved selections persist |
| BASE-002 | Save multiple Teach selections | All selected values persist |
| BASE-003 | Save multiple Learn selections and reopen | All selected values persist |
| BASE-004 | Save teach-only profile with Learn empty | Saves successfully |
| BASE-005 | Synthetic object/array Compose inputs | Both actions succeed |
| BASE-006 | Five-profile synthetic discovery filter | Only test-b and test-c remain; self/review/incompatible excluded |
| BASE-007 | Select fit on BASE-006 | Profile 2 reciprocal with canLearn [2]/canTeach [1]; profile 3 one-way with canLearn [2]/canTeach [] |
| BASE-008 | Teach-only synthetic current profile | Only profile 2; canLearn [], canTeach [1], reciprocal false |
| BASE-009 | Needs review synthetic current profile | Filter and Select produce [] |

## Registration and validation

Issues #5/#6/#46. Each save/reopen includes checking the stored test item, not
only a success message. Use the currently published test app.

| ID | Setup and action | Expected |
|---|---|---|
| REG-001 | New account supplies useful language selections; save/reopen | One own profile, selected lookup values retained; no admin approval |
| REG-002 | Save culture-only F or G with both language fields empty | Valid and retained; no language requirement |
| REG-003 | Save otherwise valid profile with Time zone empty | Save succeeds; missing time zone does not invalidate/hide profile |
| REG-004 | Supply a valid active catalogue time zone; save/reopen | Correct lookup persists; not converted to another zone |
| REG-005 | Clear all four language/culture offer/interest fields; Save | Clear validation message; save blocked without discarding entered form data |
| REG-006 | Test language-only, culture-only and combined offers/interests | All supported; at least one field sufficient; no separate profile exchange type required |
| REG-007 | Save multiple values in every applicable language/culture lookup | All values persist as lookups, not display-text substitutes |
| REG-008 | Attempt inactive/unknown catalogue IDs in isolated validation test | Invalid values rejected; no misleading success; empty optional time zone still valid |
| REG-009 | Edit existing own profile and reopen | Same identity/item updated; no duplicate; unrelated values preserved |
| REG-010 | Inspect registration controls | No participant group-size-preference field and no proposed Comments notice |
| REG-011 | Existing/imported invalid record; correct editable inputs and save | Revalidation succeeds without ordinary admin approval; no premature discovery before valid |
| REG-012 | Submit twice or retry an interrupted create | At most one profile per company account; understandable result |
| REG-013 | Open each culture selector in Edit/New mode after refresh | Both show Culture catalogue labels rather than sample Item 1/2/3, and allow multiple selections; inactive-value handling is separately REG-008 |
| REG-014 | Validate an existing profile, including a fixture created by an admin for a different participant | Participant account is preserved; Created By/Modified By never silently replaces the registered identity |
| REG-015 | Validate when Status already equals the computed result; then allow one required Status change | Matching status causes no item write; a necessary write may trigger a follow-up run which performs no further write; no sustained self-update loop |
| REG-016 | Edit and correct a profile under the modified trigger; exercise queued older events in an isolated fixture | Validation reads current saved values, rechecks edits and converges to the correct Status without overwriting profile fields; read failure cannot report validation success |

## Participation and availability

Issues #6/#7. Test after any asynchronous validation finishes; record the observed
run and elapsed time rather than inventing a timing guarantee.

| ID | Setup and action | Expected |
|---|---|---|
| PAR-001 | Create valid new self-registration | Participation Active, Open to connections Yes |
| PAR-002 | Set Paused; edit Comments/languages and let validation pass | Remains Paused; hidden from new discovery; stored openness not reset |
| PAR-003 | Set Inactive; edit and revalidate | Remains Inactive; no new discovery appearance |
| PAR-004 | Active profile sets Open to connections No; edit/revalidate | Remains closed to personal requests and absent from participant discovery |
| PAR-005 | Set Active/open and correct validation errors | Discoverable when compatible; no need for routine admin approval |
| PAR-006 | Pause or reactivate someone already in a group | No silent membership deletion, automatic rejoin or group reopening; derived information matches actual membership records |
| PAR-007 | Member changes personal openness, then group openness | Personal and group fields remain independent; no unintended cross-update |

## Compatible discovery

Issues #7/#9/#16/#42. Profile/group display is approved by #46/PR #59.
DISC-008 still needs implementation/execution evidence. Use derived group
validity, not names alone; exclude email and admin/system fields.

| ID | Setup and action | Expected |
|---|---|---|
| DISC-001 | A searches against self, B, C and incompatible profiles | Self excluded; one-way/reciprocal fit supported; no general directory |
| DISC-002 | F searches for culture C1 opportunities | G can qualify as learner; culture-only profile works |
| DISC-003 | Two profiles only want C1; neither shares C1 | Shared interest alone is not a valid culture exchange |
| DISC-004 | Search against D/E/H and an Inactive profile | Review/Paused/closed/Inactive profiles excluded under separate fields |
| DISC-005 | Compatible profile has no time zone | Remains eligible; no UTC inference or implicit missing-zone exclusion |
| DISC-006 | Search compatible Open group with valid focus and a free slot | Group shown as joinable with correct count/slots; unrelated group excluded |
| DISC-007 | Repeat for Closed, Ended, full and invalid-focus groups | None appear as joinable; no automatic changes to stored group state |
| DISC-008 | Inspect app response/UI against the approved #46 field allowlist | Only approved profile/group fields shown; admin/system-only metadata excluded; Comments treatment matches decision |
| DISC-009 | No compatible candidates | Empty result is handled clearly; no automatic assignment or unsolicited alternative-matching feature |
| DISC-010 | Search after profile/member changes | Results reflect current authoritative eligibility; stale displayed result cannot bypass acceptance recheck |
| DISC-011 | Dataset exceeds one default query page or chosen flow bound | Verified pagination/bounds behavior; no silent partial-result success; no paid fallback |

## Group structure and controls

Issues #12/#13/#16/#46. Creation checks require the acceptance workflow; a manual
row insert is fixture setup and not proof of automatic creation.

| ID | Setup and action | Expected |
|---|---|---|
| GRP-001 | Accept creation of a valid 2-person language group with capacity 3 | One Groups row, 2 active membership links, count 2/slots 1, initially Open after memberships save |
| GRP-002 | Accept creation with capacity 2 and two members | Initially Closed after successful memberships; slots 0 |
| GRP-003 | Create language group at capacity 2/3; try 1/4 | 2/3 allowed, out-of-range rejected |
| GRP-004 | Create culture/combined groups with 2/10; try 1/11 | 2–10 allowed, out-of-range rejected; focus validity also required |
| GRP-005 | Language group has A sharing L1 and C learning L1; try unrelated L2-only joiner | Valid initial focus; unrelated member rejected; reciprocal teaching not required |
| GRP-006 | Culture group has F sharing C1 and G interested; remove sharing role in isolated fixture | Valid with both roles; interest-only group not joinable |
| GRP-007 | Combined group has distinct sharer/learner for each focus; each member participates in at least one | Valid even if some participate only in language or only in culture; reject missing focus relationship/unrelated member |
| GRP-008 | A different active member accepts/declines or changes Open/Closed | Allowed without owner-only or routine admin requirement; non-member denied under ACC tests |
| GRP-009 | Edit name/description; attempt exchange-type/focus changes after creation | Name/description allowed; type/focus fixed in MVP |
| GRP-010 | Change capacity within type bounds, then below current member count | Valid change allowed; below-count/out-of-bounds rejected; derived slots consistent |
| GRP-011 | Open/Closed to Ended, then try ordinary reopening/joining | Ended final in MVP; no new joins or ordinary reopening |
| GRP-012 | Open group becomes full; Closed group has free slots | Neither can accept new joins; free space alone does not reopen Closed |
| GRP-013 | One participant belongs to multiple groups | Separate membership links; My groups correct; participant profile contains no manual group text |
| GRP-014 | Two different active members view/respond to group join requests and manage permitted controls | Both authorized through verified access; no leader/contact prerequisite; non-members denied; conflicting responses follow REQ-009 |

## Requests retries and simultaneous actions

Issues #10/#11/#17/#47. Run fault/concurrency checks only with isolated fixtures;
document how simultaneous runs were triggered and inspect records afterward.

| ID | Setup and action | Expected |
|---|---|---|
| REQ-001 | Send valid person/group request | Pending, trusted sender/recipient, sender can see status; no active membership yet |
| REQ-002 | Repeat same Pending request | No duplicate Pending connection; clear response |
| REQ-003 | Authorized recipient/member accepts | Availability/fit/space rechecked; one membership result; request becomes Accepted consistently |
| REQ-004 | Authorized actor declines | Declined history remains; no membership created |
| REQ-005 | Sender cancels Pending | Cancelled history remains; later acceptance attempt cannot create membership |
| REQ-006 | Candidate pauses/closes or group closes/fills after request | Acceptance recheck prevents invalid join; state handling follows agreed unavailable-recipient rules |
| REQ-007 | Replay/retry same accepted operation | One logical group/membership result, no duplicate slots or events |
| REQ-008 | Two requests accepted simultaneously for one free slot | At most one new active membership; capacity never exceeded; other result clear |
| REQ-009 | Two group members answer the same request concurrently | One consistent terminal decision/result; no duplicate memberships |
| REQ-010 | Simulate failure between group, membership and request writes | No false successful acceptance; retry/recovery preserves history and restores one consistent result |
| REQ-011 | Cancel and accept race | One consistent winning transition; no contradictory Accepted/Cancelled result or extra membership |

## Leaving and history

Issues #14/#47. These tests do not approve automatic pause recovery or replacement.

| ID | Setup and action | Expected |
|---|---|---|
| LEAVE-001 | Member leaves valid group | Membership Left/history retained; count decreases and free slots increase automatically |
| LEAVE-002 | Leave a Closed group | Stays Closed even with space; remaining member must choose to reopen |
| LEAVE-003 | Sole relevant sharer or sole learner leaves | Group disappears from joinable discovery; no automatic ending/replacement/expulsion |
| LEAVE-004 | Remaining members still satisfy focus | Group remains eligible only if its state/space/other rules permit; no manual count update |
| LEAVE-005 | Repeat departure action | No extra decrement, negative count or duplicated history change |
| LEAVE-006 | Participant becomes Active after leaving/pausing | No silent rejoin or resurrection of a Left episode |

## Access operations notifications and migration

Some prerequisites/decisions remain deferred. Document the reason instead of
inventing an expected channel, field allowlist or migration-confirmation rule.

| ID | Setup and action | Expected/status gate |
|---|---|---|
| ACC-001 | Ordinary A opens/edits own profile; B does the same | Each can manage only own registration; actual account-role test, not admin simulation |
| ACC-002 | Ordinary account tries another profile through list/item/API or altered request | No read/edit bypass beyond approved discovery response; DEFERRED until colleague test |
| ACC-003 | Non-member attempts member group actions | Denied; legitimate active member allowed |
| ACC-004 | Admin reviews/corrects records in an exceptional case | Authorized support works without requiring approval for ordinary use |
| ACC-005 | New ordinary user opens published app through intended audience route | Self-onboarding works without per-user manual grants; verify data and flow access separately |
| OPS-001 | Normal registration/search/request/join/leave | No routine organiser approvals, matching or manual count/permission repair |
| OPS-002 | Supported test of rejected input, denied access or transient flow failure | Clear safe error; no raw credentials/data leak, false success or automatic paid fallback |
| OPS-003 | Import generated disposable TandemImportProbe ZIP as Create as new, then manually run | Separate flow, no working-flow update/connector dependency; success true and message IMPORT_PROBE_OK. Check import permission/policy first. This proves only the connector-free package path; results recorded separately in TEST_RUNS.md |
| OPS-004 | Import TandemSharePointImportProbe as new, map an existing SharePoint connection, turn on and manually run | GET reads site technical ID only; response success true and SHAREPOINT_IMPORT_PROBE_OK. No list/record writes. Owner-only connection probe, not participant authorization or full deployment acceptance |
| NOT-001 | Run selected request-notification events after #49 decision | Correct channel/recipient/link and safe retry/failure handling; REQUIREMENT PENDING until matrix agreed |
| MIG-001 | Final-phase dry run of actual source mappings | Exception report for ambiguous/missing/duplicate data; no silent dropping or guessing; DEFERRED to #48 |
| MIG-002 | Repeat accepted migration; reconcile profiles/groups/memberships | No duplicates, preserved source, correct links/counts and explicit confirmation state; DEFERRED to #48 |

## Audit coverage additions - 2026-11-08 (#45)

These definitions close test-plan gaps found in the all-ticket audit. They are
NOT RUN unless TEST_RUNS.md records an actual versioned execution. Later/decision
cases are REQUIREMENT PENDING, not approval of new policies or runtime behavior.

| ID | Setup and action | Expected / gate |
|---|---|---|
| REQ-012 | Inspect own Sent/Received history and attempt an unrelated request | Only authorized rows/actions; tampered inputs denied under verified access; stable terminal history |
| REQ-013 | Two active group members, a non-member and a departed member inspect group inbox/respond | Current active members see/respond; no leader role; others denied; detailed departed-history projection follows the reader contract |
| REQ-014 | Submit group join with blank/nonblank introduction; inspect retained request | Introduction optional, stored/displayed as plain text only to authorized request audience; final length boundary awaits #17 approval |
| REQ-015 | Inspect Accepted/Declined/Cancelled history and retry old action buttons | Agreed history retained; no second conflicting decision or membership; no rollback on permission failure |
| AUTH-001 | Active member edits permitted group controls; non-member tries same | Membership checked against current authoritative data through verified access; non-member denied |
| AUTH-002 | Direct/tampered flow invocation with another participant/request/group reference | Authenticated caller binding enforced; input IDs/email are not authorization; no private data leak |
| AUTH-003 | Ordinary user attempts direct Active membership creation/update | Controlled lifecycle path enforced; no arbitrary active membership manufacture; admins retain necessary support |
| AUTH-004 | Member leaves, then retries a stale management/respond call | Current membership revocation respected; remaining members still authorized; no routine individual grants |
| AUTH-005 | Review access prerequisite inventory and selected method before proof | Evidence marks actual capability available/unknown/unavailable; unverified prerequisite blocks dependent configuration; no silent paid fallback |
| DATA-001 | Generate isolated fictional sets near 200/1,000/5,000 profiles | Reproducible counts and expected language/culture/state/blank-zone coverage; no real employee data required |
| DATA-002 | Validate dataset links/uniqueness and proposed tenant loading | Group/member/request references consistent; verify isolated loading and account-identity representation first; fake records do not simulate authentication |
| SCALE-001 | Measure versioned Discovery on 200-profile fixture | Record latency, query/paging completeness and delegation; no silent truncation |
| SCALE-002 | Repeat on 1,000-profile fixture | Same completeness/measurement evidence; explicit bound failure is not successful scale support |
| SCALE-003 | Repeat on 5,000-profile fixture | Same completeness/measurement evidence; a 500-candidate guard alone does not pass 5,000 support |
| DEP-001 | Second permitted developer reproduces app/business-flow setup from repository | Documented one-time steps and allowed connection selection work; published/imported versions and results recorded |
| DEP-002 | Review handover configuration and required credentials | No original workstation/local-only secret/runtime required; mappings and connection ownership explicit; existing entitlements only |
| DEP-003 | Exercise supported missing/denied connection/configuration case in isolated deployment | Understandable safe diagnostics, no false success or inadvertent working-flow/data replacement |
| DOC-001 | Audit issue inventory/status/experiences/test mappings and repository overview | Every issue accounted for, one lifecycle label each, no open Done/closed ready label, proposed experience on open tickets, case IDs defined and evidence scope preserved; no runtime claim |
| NOT-002 | Retry selected notification event or simulate allowed delivery failure | Deduplicate logical delivery under approved policy; failure visible; request/membership state not rolled back; REQUIREMENT PENDING until #49 |
| NOT-003 | Review notification options/prerequisites/event-recipient matrix | Explicit permitted choice or documented constraint; no assumed email/Teams/Approvals connection, paid upgrade or ordinary admin dispatch; decision evidence, not delivery test |
| LATER-001 | Review/run ranking only after future policy approval (#8) | Only eligible results ranked under approved policy; blank time zone supported; current status REQUIREMENT PENDING |
| LATER-002 | Review/run multi-group warning only if selected (#15) | Agreed warning behavior, no unapproved hard limit/routine approval; current status REQUIREMENT PENDING |
| LATER-003 | Review/run freshness only after fields/thresholds approved (#29) | Identify agreed stale records without auto deletion; current status REQUIREMENT PENDING |
| LATER-004 | Review/run reminders only after freshness/channel approved (#30) | Correct recipient/failure visibility; no automatic group ending; current status REQUIREMENT PENDING |
| LATER-005 | Review later admin dashboard against agreed scope (#31) | Group Open/Closed/Ended and separate participant Active/Paused/Inactive; freshness/overrides only when approved; no Paused-group state inferred |

## Suggested regression sets

- Profile/schema changes: REG-001–016, PAR-001–007 and DISC-004–005.
- Eligibility/projection changes: DISC-001–011, GRP-005–007, LEAVE-003–004,
  plus ACC-001–003 after access prerequisites exist.
- Group/request/flow changes: GRP-001–014, REQ-001–015 and LEAVE-001–006.
- Deployment/sharing changes: affected behavior cases plus ACC-001–005 and OPS.
- Notification changes: NOT-001 and retry/acceptance cases after #49.
- Final migration: MIG-001–002 and affected profile/group regression sets.

These sets are planned coverage, not a requirement to repeat unrelated checks for
every documentation edit. New bugs should gain a stable regression case if not
already covered. Add a run record before closing the related implementation ticket.
