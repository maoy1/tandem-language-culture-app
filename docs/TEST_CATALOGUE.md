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

The existing schema JSON still describes the original required-time-zone baseline.
New optional-time-zone/culture/status cases below are NOT RUN until implementation.
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

Issues #7/#9/#16/#42. Profile field projection is still undecided; DISC-008 cannot
pass until that decision exists. Use derived group validity, not names alone.

| ID | Setup and action | Expected |
|---|---|---|
| DISC-001 | A searches against self, B, C and incompatible profiles | Self excluded; one-way/reciprocal fit supported; no general directory |
| DISC-002 | F searches for culture C1 opportunities | G can qualify as learner; culture-only profile works |
| DISC-003 | Two profiles only want C1; neither shares C1 | Shared interest alone is not a valid culture exchange |
| DISC-004 | Search against D/E/H and an Inactive profile | Review/Paused/closed/Inactive profiles excluded under separate fields |
| DISC-005 | Compatible profile has no time zone | Remains eligible; no UTC inference or implicit missing-zone exclusion |
| DISC-006 | Search compatible Open group with valid focus and a free slot | Group shown as joinable with correct count/slots; unrelated group excluded |
| DISC-007 | Repeat for Closed, Ended, full and invalid-focus groups | None appear as joinable; no automatic changes to stored group state |
| DISC-008 | Inspect app response/UI after field projection is agreed | Only approved profile/group fields shown; admin/system-only metadata excluded; Comments treatment matches decision |
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
| NOT-001 | Run selected request-notification events after #49 decision | Correct channel/recipient/link and safe retry/failure handling; REQUIREMENT PENDING until matrix agreed |
| MIG-001 | Final-phase dry run of actual source mappings | Exception report for ambiguous/missing/duplicate data; no silent dropping or guessing; DEFERRED to #48 |
| MIG-002 | Repeat accepted migration; reconcile profiles/groups/memberships | No duplicates, preserved source, correct links/counts and explicit confirmation state; DEFERRED to #48 |

## Suggested regression sets

- Profile/schema changes: REG-001–012, PAR-001–007 and DISC-004–005.
- Eligibility/projection changes: DISC-001–011, GRP-005–007, LEAVE-003–004,
  plus ACC-001–003 after access prerequisites exist.
- Group/request/flow changes: GRP-001–013, REQ-001–011 and LEAVE-001–006.
- Deployment/sharing changes: affected behavior cases plus ACC-001–005 and OPS.
- Notification changes: NOT-001 and retry/acceptance cases after #49.
- Final migration: MIG-001–002 and affected profile/group regression sets.

These sets are planned coverage, not a requirement to repeat unrelated checks for
every documentation edit. New bugs should gain a stable regression case if not
already covered. Add a run record before closing the related implementation ticket.
