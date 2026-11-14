# Current design source of truth
## Current authorized batch — 2026-11-14

[#45](https://github.com/maoy1/tandem-language-culture-app/issues/45) now delivers twelve production workflows together: [#81](https://github.com/maoy1/tandem-language-culture-app/issues/81) shared validation and business flows #7/#61/#10/#62/#63/#11/#17/#65/#64/#13/#14. Implementation is complete locally; one disabled-import Solution is assembled for owner testing. All new native import, schema setup, connection, app binding and runtime acceptance remain NOT RUN. Prior native results retain their original build and do not certify this batch. The owner authorized parallel implementation while retaining one flow per ticket/PR.

The shared child owns schema validation, normalization and matching. Whole-schema checks run during owner setup/audit; business flows retain authenticated identity, current operational authority, relevant live eligibility and exact ETag/unique-key/commit guards. Discovery uses one bulk PAIRS evaluation for people. Readers and group controls do not call shared eligibility when it has no bearing on their operation. Personal participation/openness is separate from validation and committed group-control authority.

One-time additive setup creates optional plain-text request Introduction (maximum 2,000 in app/flow) and TandemOperationReceipts with ten agreed fields. Exact title resolution allows one import followed by Setup Apply + Audit; no post-setup GUID rebuild is required. Setup changes no participant/request/member rows, deletes or permissions. Missing or mismatched schema blocks activation. No lease takeover, background repair service or additional production runtime is introduced.

Notifications are decided: in-app plus email, sender Tandemteam@elsevier.com, approved event/audience matrix in #49. The mailbox REST probe failed; #21 email delivery stays blocked and outside these twelve flows. Request/group views provide the core in-app path; no email success is claimed. Full app screens (#16/#67/#68) and deferred ordinary-participant access/privacy proof remain separate work.

The sections below preserve earlier decisions and versioned evidence; this current batch status supersedes old sequencing, undecided-channel and implementation-not-started statements.


This file records the approved MVP direction and the implemented baseline.
Approved target behavior is not evidence that a field, flow or permission exists.

## Authority and change control

Owner priority update (2026-10-31): build the integrated Power Apps/Power Automate
path through discovery, in-app requests, group/membership creation and notifications
before resuming remaining detailed tests. Preserve evidence and incomplete tickets;
no blanket validation pass or broader-release approval is implied. Prioritize the
app/flows over setup automation. Notification selection, including possible use of
Approvals, is discussed when that feature is built; central in-app experience is
the owner's preference. Required backing data is bound at the relevant build step.

- This file controls implementation decisions; IMPLEMENTATION_PLAN.md sets sequence and GitHub issues hold acceptance evidence.
- Combined Requirements v0.2 under docs/reference is the reviewed input. The owner's subsequent annotations recorded below override conflicting draft passages and reviewer comments.
- The old tandem_app repository and older DOCX files are reference material only.
- Update design, plan, affected ticket and setup evidence together on one ticket branch/PR.
- Do not close an issue until its implementation and applicable tenant tests pass.

## Fixed platform and operating constraints

Production is SharePoint with associated Power Apps/Power Automate under existing
entitlements only. No paid hosting, standalone server, Azure Functions, external
services, premium/custom connectors, new paid licences or trials as dependencies.
Python remains optional local repository tooling, never a participant runtime.

Ordinary internal-user actions are self-service. Admin effort must not grow per
normal registration, search or request. Critical/exceptional cases may involve
necessary approval, correction or assistance. Flag and verify permissions,
settings, connections, connector policy, licences, one-time setup and recurring
operational dependencies before relying on them.

## Approved v0.2 decisions

| Area | Decision | Delivery |
|---|---|---|
| Time zone | Optional single selection from the Time zone catalogue; blank never blocks registration/discovery | SharePoint optional verified #66; app acceptance #5 |
| Location derivation | Lower priority; reconsider only when cheap and supported | Later; no profile-location dependency |
| Discovery audience | Present compatible available profiles/groups, not all profiles | #7, #16, #42 |
| Discovery fields / Comments | Person/group display approved 2026-11-08; email/admin/system data excluded; no Comments notice | #46 contract; implement/test #7/#16/#42 |
| Private organiser notes | Participant emails organisers; no new private-Comments split | Contact route to identify; separate from notification-channel decision |
| Language groups | 1-to-1 or 1-to-2, meaning 2 or 3 people total | #12/#13 |
| Culture groups | 2â€“10 total members, including at least one relevant culture sharer | Owner approved; #12/#13 |
| Combined groups | Language/culture combined groups have 2â€“10 total; both focuses require a sharer and a different learner | Owner approved |
| Participant status | Separate Active/Paused/Inactive participation from validation | #46 then #6 |
| Culture-only participation | Supported; no mandatory language selection | #5/#7 |
| Notifications | In-app plus email approved; shared-mailbox REST capability failed, email delivery blocked | #49 / #21 |
| Membership changes | Normal acceptance, membership and slot updates automatic | #11/#12/#17/#47 |
| Exceptions | Necessary admin support permitted; avoid routine organiser matching | #13/#14 |
| Excel import | Inspect/map/migrate at the end of implementation | #48; before launch if existing-data launch requirement remains |
| Hosting | Standalone hosting alternative rejected under no-budget constraint | All tickets |

## Observed schema update - #66, 2026-11-08

Owner metadata audit and setup-v2 apply/readback succeeded. Actual casing, list
IDs, lookup display fields and observed settings are in
config/tenant_schema_mapping.json. ParticipationStatus (required Choice, default
Active) and OpenToConnections (required Boolean, default Yes) were added. Both
language/culture multi-lookups and optional single time zone already existed.
Catalogue label requiredness and time-zone IANA_ID required/unique/index settings
were corrected. Existing values, legacy Status choices and IANA_ID lookup display
were preserved; optional Windows conversion metadata is absent and unused.
Final full audit is Verified (zero findings); setup repeat returned SETUP_VERIFIED.
Owner confirmed all five writes skipped on a new repeat with SETUP_VERIFIED.
Own schema acceptance passed; PR #69 is merged and #66 closed. App/flow acceptance
stays with its separate owners. No ordinary-user privacy or rollout claim follows from owner setup.
See POC_SHAREPOINT_SETUP.md and TEST_RUNS.md for versions and finish line.

## Completed participation controls - #6

Corrected owner-reported Live target is **Version 19**. The Participation status
Combo box DataCardValue2 uses DefaultSelectedItems with table-returning branches:
New filters the Active Choice; Edit wraps Parent.Default's saved Record. The
outer card reads ThisItem.'Participation status'; inner legacy Default is Blank().
Owner confirms Active/Yes new defaults, saved choices preserved, and language/
culture-only save/reopen preserving identity/unrelated fields. #6 is Done; PR #70 merged and the issue closed on its own UI scope.

Flow revalidation stays #61, candidate exclusion #7 and stale request rejection
#10. Group side effects need an operational fixture and #25 integrated testing;
derived displays remain #64/#68. Exact retained cases/blockers are in
config/participation_integration_handoffs.json. No ordinary-user privacy, full
backend acceptance or new hosting/connector capability is inferred from UI checks.

## Current registration form work - #5

#5 is Done after merged PR #71. Owner confirmed Live Version 19 checks A/B passed:
all four multi-lookups persist with optional time zone cleared and identity
unchanged; all-four-empty Save retains input and leaves the saved item unchanged.
Existing culture-only/identity evidence is retained. No app rebuild was needed.
POC_05_CULTURE_REGISTRATION.md records scope and regression steps;
backend validation remains #61 and access integration #41.

## Implemented SharePoint baseline

The table below records the last verified registration baseline. The JSON schema
and registration policy now describe the desired POC-05 delta (culture fields and
optional time zone), explicitly marked pending tenant setup/tests. They are not a
live export. See [POC_05_CULTURE_REGISTRATION.md](POC_05_CULTURE_REGISTRATION.md).

Language catalogue: Title, required unique indexed ISOCode, Aliases, Active.
Time zone catalogue: Title, required unique indexed IANAId, optional WindowsId,
Active.

| Participants field | Current implementation |
|---|---|
| ParticipantAccount | Required unique single Person identity; locked to signed-in user in the app |
| TeachLanguages / LearnLanguages | Multi-value Language catalogue lookups |
| TimeZone | Optional single lookup verified by #66 metadata audit; displays IANA_ID; app acceptance remains #5 |
| LearningFocus / Comments | Optional multiple-line text |
| Status | Flow-managed validation baseline: Active / Needs review |
| Title | Hidden technical text |
| Created / Modified and authors | SharePoint system-managed columns |

Do not introduce a participant-entered identity email. Migration email matching
must resolve to the company account; decide mapping/duplicate handling in #46/#48.
Do not delete existing tenant helper/legacy columns during planning.

## Target fields and candidate exposure

The reviewable field matrix is [MVP_FIELD_CONTRACT.md](MVP_FIELD_CONTRACT.md).
It now includes separate Groups and Group Members tables, field ownership,
editability and derived count/slot/joinability rules. These are target contracts,
not proof that any existing tenant group lists have the proposed structure.
Group limits and Discovery display are approved; target technical field tables
need acceptance. #46 remains open and no schema/form is changed by this proposal.

#46 accepted the target types/requiredness/defaults/ownership and exposure. #66
verifies actual participant/catalogue mappings before dependent #5/#6 App
changes; #61 owns validation. Some setup has owner-reported evidence; the target
contract does not certify every deployed setting or its runtime acceptance:

- Controlled Cultures I can share and Cultures I am interested in, using a Culture
  catalogue. This supersedes the earlier removal/deferment of controlled culture fields.
- No participant group-size preference. People see actual group size/free slots
  and decide whether to request joining; the group accepts or declines.
- TimeZone remains a catalogue lookup but is optional. The baseline's required
  restriction and validation dependency must be removed in #5; no live change is
  implied by this contract review.
- Participant-controlled participation status Active / Paused / Inactive.
- Owner-approved new-registration defaults: participation Active and open to new
  connections Yes. Validation remains independent; edits never reset choices.
- Open to new connections, separate from validation; exact interaction with open
  group membership must be specified without inventing a second manual status.
- Independent validation state and migration-confirmation state. Retaining the
  existing Status as validation is an option to preserve flows; technical names
  and transition/default rules are finalized in #46.
- Group exchange type, capacity, Open/Closed/Ended state, authoritative membership
  records and derived free slots. Waiting / In a group are derived from memberships.

Culture-only validation must accept useful culture selections without requiring
Teach/Learn languages. Culture discovery needs a genuine sharer; interest alone
must not imply sharing expertise. Agree how combined interests are represented.

Discovery display is approved in MVP_FIELD_CONTRACT.md (2026-11-08): include
the proposed person fields, group description/member names and approved
member profile details. Exclude email and raw account/identity/admin/system data.
This decision does not establish deployed projection or verified access. Comments
are included; the proposed Comments notice remains removed.

## Discovery and baseline test evidence

The tested language baseline uses Active plus catalogue language IDs, excludes
self/non-Active profiles and allows either exchange direction; both directions
identify reciprocal fit. The owner confirmed synthetic Compose, Filter array,
Select, teach-only and Needs review cases in Power Automate on 2026-10-31.
config/discovery_eligibility.json remains that baseline, not the complete v0.2 rule.

Before real-data integration, extend normalization and filtering for separate
participation/validation, open-to-connections, culture-only/combined compatibility
and compatible open groups with space. No assignments or memberships are created
by discovery. Optional filters narrow compatible results, not a public directory.

Ranking by city/time zone/waiting time is Later (#8). Retain time zone for display;
do not require derived location, paid services, AI suggestions or scheduling.

## Requests and groups

MVP includes connect/join requests, recipient/member accept or decline, and sender
request-state visibility. Use Pending/Accepted/Declined/Cancelled where required;
meet-first, expiry and bulk invitations remain Later. Recheck availability and
capacity before acceptance. Unavailability cancellation details are specified
in #10/#11 without implicitly enabling an unchosen notification channel.

Group creation/membership updates follow accepted participant actions.
Store group details in Groups and one group/participant episode link in Group
Members. Keep personal profiles in Participants. Counts, slots and My groups
derive from active membership links, not editable participant text or presumed
cross-list calculated columns. Membership rows are workflow-maintained.
Current #11 creation flow, backed by #12 schema, uses SourceRequestId and membership
episode MembershipKey for retry identification, plus SetupComplete (default No)
to distinguish unfinished setup from the participant-controlled lifecycle state.
Operational My groups/discovery/count derivations must exclude unfinished groups:
require SetupComplete and an Accepted source request. Temporary Active rows
during multi-record setup are not an operational membership result. Ending
such an unfinished group after rejection is setup cleanup, not automatic
ending of an operating group after a member leaves.
Conditional status/setup/cleanup writes and these keys do not complete #47 or
caller/access proof. The current sanitized export review is recorded in
config/participant_response_flow.snapshot.json, not an importable deployment.

Owner-approved group creation publishes only after memberships save successfully:
start Open if space remains, otherwise Closed. Active members may edit name and
description and adjust capacity within bounds, never below current member count.
Exchange type and focus are fixed after creation for MVP. Open and Closed can
switch or become Ended; Ended is final, not a temporary closed state. Necessary
admin exceptions remain possible without adding a routine reopen-Ended path.
Groups control Open/Closed/Ended. Open groups can receive join requests only when
space remains; Closed groups continue without new joiners; Ended groups are no
longer operating. Show member count and free slots. No saved participant size
preference is required; the participant chooses and the group accepts/declines.
Language capacity is 2 or 3 total; culture capacity is 2â€“10 with a relevant culture
sharer, and combined language/culture capacity is 2â€“10 with a relevant culture
sharer. Do not infer a universal minimum of 3. Open/Closed/Ended is the target simple MVP group state;
other lifecycle states and timers require a later decision. Active members may
accept/decline join requests and set Open/Closed/Ended, with necessary admin override.

Every member participates in at least one stated group focus as sharer/learner
or both. A language focus needs a sharer and a different learner; culture follows
the equivalent rule. Combined groups support both focus relationships, while
individual members can participate in either or both. Reciprocal teaching is optional.

Requests start Pending; senders may cancel before response. Only one Pending
request per same person/group connection. Acceptance rechecks fit, availability
and capacity; Accepted/Declined/Cancelled history is preserved.

Normal membership counts and free slots update automatically. A departure remains
self-service and preserves history; ambiguous group purpose/sharer recovery can
use exceptional admin support. A Closed group stays Closed until a member reopens
it. When remaining members no longer support its stated focuses, hide it from
Discovery using ordinary eligibility validation, without automatically changing
its stored state. Do not auto-end/reopen, assign replacements, disband, expel
others or rejoin people; recovery automation/timers remain Later. This specifies
leaving, not a new pause/Inactive membership cascade.

#47 covers duplicate accepts, simultaneous last-slot joins, retries and partial
multi-record failure. It is shared acceptance logic/testing for #11/#12/#17,
not a second matching implementation. Ordinary successful processing is automatic.

## Focused implementation ownership - #45

Each production flow has one Flow ticket. App screens and shared schema/rule/
authorization artifacts are separate; current owners are listed in
config/backlog_readiness.json and docs/BACKLOG_ALIGNMENT.md. #61 owns validation,
#62 request reading, #63 cancellation, #64 My groups reading and #65 group-join
responses; #66 participant schema and #67/#68 screens are separate. #12 is group
schema, #16 the Discovery App, #10 personal send and #17 group-join send only.
#22/#24 are Superseded, not completed. The accepted product rules are unchanged.

## Contract ticket boundary - #46

#46 delivers the field/ownership and approved Discovery exposure specification;
owner review/merge accepts its target field tables. Runtime implementation,
permissions, flow interfaces, migration decisions and reliability tests have
explicit receiving tickets in MVP_FIELD_CONTRACT.md. They do not prevent #46
closing once its document review/merge is complete. All prerequisites remain
mandatory before their dependent integration/release work.

## Contract review decisions - 2026-11-08

The final owner choice removes the proposed group leader/contact role. All active
members can see incoming group join requests and accept/decline or manage allowed
controls. Requests target the group; no contact appointment/replacement fields or
exclusive authority. First valid saved response wins with #47 safeguards.
An optional introduction message is approved for group join requests; technical
request/payload mapping is still to specify under #46/#17.

Concurrency is expected to be rare: prefer basic prevention plus simple safe
retry/recovery and necessary exceptional admin help. Do not build an elaborate
lock/reconciliation platform. Duplicate membership, over-capacity success and
false success remain unacceptable; shared write protection still needs its
bounded #47 proof. Identity/access and detailed error/pagination decisions may
be reviewed later, with owner/synthetic construction only until required access
prerequisites pass. No ordinary-user rollout is approved by this deferral.

## Intake migration and notifications

Direct in-tool registration is the agreed intake. Do not implement a second
Microsoft Forms sync. Existing Excel inspection/migration is the final phase
(#48): preserve originals, resolve accounts, report ambiguous colours/statuses,
duplicates and mappings, recreate confirmed memberships and record confirmation.
Do not guess culture expertise from ambiguous historical interest text.
Whether unconfirmed migrated profiles appear in discovery remains to decide.

Notification options are undecided despite email-only statements in the draft.
#49 must compare permitted existing email/Teams capabilities and agree recipient,
event, privacy, reliability, retry and cost behavior before #21 implementation.
At least request-received/request-answered are candidates to evaluate, not a
silent commitment to every event in the source document.

## Access and release checks

Normal registration exposes only the caller's profile; discovery returns only
approved compatible candidate details. An app filter alone is not authorization.
Site Members are trusted admins; their inherited access does not establish an
ordinary user's access. The owner deferred colleague access testing; #18/#39â€“#42
remain open while work continues with owner/synthetic data. No access redesign
is approved. Verify actual ordinary-user access before broader release.

The former submission flow used language selection plus mandatory time zone and
rewrote identity from Created By. Owner-guided changes now use current item data,
four-field language/culture presence, modified-event handling and change-only
Status writes preserving identity. The Active no-op/correction/follow-up cases
have scoped owner evidence; remaining cases, catalogue validation and full
registration acceptance are deferred to the integrated test phase. Do not reset
participation/openness through validation or treat old baseline tests as new-MVP proof.

Confirmed target validation: the form blocks save if all four language/culture
offer/interest fields are empty, with a clear correction message. Empty time zone
is valid. Invalid existing/imported records are hidden from Discovery until
corrected; users fix their data and validation reruns without routine admin
approval. Successful validation never changes Paused/Inactive or a user's closed
connection choice. Exceptional migration/identity repairs may still require admins.

Go-live still needs data-policy review, field/exposure acceptance, actual
permissions, request/capacity tests, selected notifications and migration evidence
where existing participants/groups must be available at launch.

## Later or excluded

Later: automatic location/time-zone derivation, ranking, optional language level,
freshness/reminders (#29/#30), dashboards/statistics (#31), detailed admin audit
UI, needs-sharer timers, automatic departure recovery, bulk invitations, meet-first,
request expiry and search-broadening advice. The earlier two-active-groups warning
is not confirmed in v0.2; keep #15 for later review rather than silently require it.

Excluded: separate paid hosting, automatic AI matching/assignment, in-app chat/video,
detailed scheduling, mandatory Location catalogue, required native SharePoint
Location input, participant Role and required participant-entered identity email.

## Validation flow testing handover â€” #61

#61 is Ready for testing on owner direction; #9 is Done after merged #73; #47 is the sole In progress ticket. Target contract and tenant handover are in
FLOW_61_PARTICIPANT_SUBMISSION.md and participant_submission_contract.json.
Current owner export inspected; event/connection alias mapping preserved in a
new import package (26 actions / depth 3), with active-catalogue checks and
ETag-protected changed Status only. 101 local tests passed. Owner valid/no-change and necessary Active correction/readback/follow-up passed
for item 38; feedback accepted/published as owner-reported Live Version 26.
Remaining scoped target acceptance variants stay pending; no whole-ticket completion.

Owner chooses PR #72 merge and tester handover with remaining acceptance retained.
See [the #61 issue description](https://github.com/maoy1/tandem-language-culture-app/issues/61) for Live-26/build context, role/setup, steps/expected
results, cleanup and blocked cases. #61 stays open; no whole acceptance or
ordinary-user access pass is implied.

## Shared compatibility implementation â€” #9

compatibility.py is the maintained rule/normalization source for package builders;
config/compatibility_contract.json and COMPATIBILITY_RULES.md define adapters and
boundaries. Person fits support one-way language/culture sharing/learning; groups
require distinct sharer/learner per focus and every member relevant to a focus.
Owner defers Any language matching; exclude sentinel from matching/group focus
without changing catalogue or registration. Concrete selections remain supported.
39 synthetic fixture cases / 121 local tests pass; isolated connector-free proof
45 actions/depth 4. Tenant proof import/run NOT RUN; live consumer/caller/group
availability mapping remains each consuming flow's evidence, not assumed here.

#9 update: matching source/build tenant run 08584074461495133197897516907CU19
passed all 39 synthetic cases with no failures. Own shared proof accepted; #73
review/merge pending. No live consumer/authorization/group-availability certification
is inferred. Any language remains deferred; no further proof rerun requested.

## Shared bounded coordination preparation â€” #47

PR #73 merged; #9 own artifact complete. #47 proposes one group-specific owner
token plus saved operation receipt, stable request/episode keys and completion
gates. No lease-steal timer or general transaction/repair platform. Known stopped
prefix retry is bounded; unknown effects retain ownership for reconciliation or
rare exceptional support. Native JSON intent comparison needs no hash connector.
COORDINATION_CONTRACT.md / coordination_contract.json describe un-applied metadata,
consumer boundaries and assumptions. 152 local tests / 70 model schedules pass;
native cross-item fixture proof NOT RUN. Read-only metadata preflight is ready to
verify fixture permissions; no fixture/production schema or data change yet.

#47 update: read-only permission metadata gate passed on owner run. A native
tagged fixture package is prepared (321 actions/depth 6; 10 checks; 165 local
tests), defaulting to no fixture writes. Explicit Yes is limited to one verified
build-tagged synthetic list. Native runtime results, genuine unknown/killed-run
recovery and production mapping remain unverified; no production schema applied.


### #47 connector duplicate-error correction â€” v2

The owner supplied the first native report: 5/10 checks passed, allPassed=false. All five failed cases invoke the duplicate-response predicate. The Duplicate primary raw body confirms SharePoint error -2130575169 / Microsoft.SharePoint.SPDuplicateValuesFoundException wrapped by the existing SharePoint connector as HTTP 502. The original proof's 400/409-only classifier was too narrow. The five-case common cause is supported by local replay; a native v2 pass remains unverified.

The classifier now requires the exact native duplicate exception/code together with HTTP 400, 409 or 502. For the wrapped form, both exact entries must exist in innerError.errors. Generic 502, unrelated 400/409, incomplete error identifiers and other statuses fail. Existing schema/row/ETag/count/readback checks remain required. All five duplicate-dependent reports now include diagnostic codes/messages. No cookie or response headers are stored.

Supported package: artifacts/coordination/TandemCoordinationFixture-v2.zip, build b54d7cee-971d-4af3-924f-e81d5fefaec9, new tagged list Tandem47Fixture_b54d7cee971d4af3. Import as Create as new, display name TandemCoordinationFixture v2, existing SharePoint connection; Run fixture writes=Yes. Old fixture is retained; no deletion or production mutation. Expected Fixture report: 10 tests, allPassed=true, failedCases=[]. Return that report; expected rejected duplicate actions may still show red 502.

Validation: 179 local tests passed, including wrapped native duplicate simulation in both writer orders and generic/error-negative cases; 321 actions / depth 6 (limits 500/8). V2 NOT_IMPORTED_NOT_TESTED. #47 remains In progress / PR #75 draft pending native results. No genuine timeout/killed-run, production consumer or notification-delivery proof inferred.


### #47 native bounded proof passed â€” 2026-11-08

Matching v2 build `b54d7cee-971d-4af3-924f-e81d5fefaec9`, owner run `08584074402025984197329193901CU08`: testCount=10, allPassed=true, failedCases=[]. Permission gate passed; existing tagged fixture `Tandem47Fixture_b54d7cee971d4af3` / `abade32d-8b24-4b30-b2e0-668d10238acb` reused (fixtureCreated=false). Summary exactly as supplied: `artifacts/coordination/results/fixture-v2.pass.owner-summary.json`; successful per-case details were not supplied and are not reconstructed. The package gates allPassed on exactly 10 results and no failed cases.

History retained: original classifier build 5/10 pass; first v2 run `08584074408126043497852268406CU03` 9/10 pass (`artifacts/coordination/results/fixture-v2.first-run.owner-report.json`). Its Shrink RequestB returned the typed duplicate exception despite distinct supplied A/B keys; actual cause remains unconfirmed. A fresh run prefix passed without code/formula edits. This does not establish connector retry causation or generic unknown-write recovery.

179 local tests / 70 reference schedules previously passed; final artifact remains 321 actions / depth 6, no runtime changes after owner proof. #47 **Ready for review**, PR #75 ready; no owner rerun required. Earlier pending-run entries above are historical. Own contract review/merge remains; no production schema applied, all 70 schedules are not native-proven, genuine timeout/killed-run, production consumer/access and external notification delivery remain separate. #12 group/member schema is next after merge; #61 stays Ready for testing.


## #12 active schema inspection â€” 2026-11-08

PR #75 merged `be278a1cc7a72b862154ae8ffe201acdf998f019`; #47 closed/Done after accepted bounded contract/native proof. #12 is the sole active ticket. Existing #57 group/member snapshot is historical source evidence; current actual list IDs/field definitions/settings remain unverified.

Prepared `artifacts/group_schema/TandemGroupSchemaAudit.zip`, build `cb49aded-f121-410e-b7df-d9646be892dd`: **51 actions / depth 3**, below 500/8. Existing SharePoint connection; GET-only list inventory/identities, Group/Group Members fields/defaults/SchemaXml/column index/list validation and effective list permission masks. Known #66 participant/language/culture list identities rechecked. **No list item reads, writes, permission changes or working-flow/app modifications.** Actual unique-key constraints/lookup targets/defaults/schema compatibility are not approved from packaging or reference proof.

194 local tests pass, including 15 generated-inspector cases (normal collection, ambiguous/missing/unsafe targets, paging, missing arrays/identities/permissions, failed reads and package safeguards). Tenant import/run **NOT RUN**. collectionComplete means bounded metadata collected, not schema acceptance; schemaVerified remains false. No setup until actual report reviewed, any changes flagged and actual per-list capability verified. Existing rows preserved; exceptions route #48. Full operator handover/checkboxes inline in issue #12; draft PR is partial preparation, not whole-ticket Ready. #61 remains Ready for testing.


### #12 actual mapping and direct settings â€” 2026-11-08

Owner opted for direct list settings rather than another setup package. Initial audit `08584074383115048211345636667CU09` and manual-settings readback `08584074377818105096431306544CU07` match build `cb49aded-f121-410e-b7df-d9646be892dd`: collectionComplete=true/errors empty; Groups and Group Members each itemCount=0. Actual field/list IDs, types, choices, defaults, XML constraints and lookup targets recorded in `config/group_schema_mapping.json`; source reports in `artifacts/group_schema/results/`.

Confirmed group Title now required; WriteOwner optional nonunique Text/blank default; native integer/type-specific capacity formula/message saved. SharePoint removed optional column brackets; canonical formula comparison confirms the same expression. Existing focus links, SourceRequestId/MembershipKey unique+indexed, dates, membership Title optional, State Closed and SetupComplete No remain. Participant lookup displays ID; preserve its linkage and resolve approved display in consumers.

Group Members Group and Participant still report indexed=false. Indexed columns page requested; no index completion or full schema acceptance claimed. #12 remains In progress / PR #76 draft. No setup package generated, row writes, renames/deletion or runtime/privacy certification. 194 existing local tests previously passed; this is metadata/evidence only, not new executable changes.


### #12 schema mapping and five manual settings verified â€” 2026-11-08

Final audit build `cb49aded-f121-410e-b7df-d9646be892dd`, run `08584074372941101122136369836CU17`: collectionComplete=true, errors=[], both lists itemCount=0. Groups `4bf1b37f-edce-40c5-8fa0-36543a2d0cd6`; Group Members `db611ec3-7fa3-477a-878e-effbbb195cb8`. Group and Participant now each indexed=true; owner Indexed columns page lists separate Group / MembershipKey / Participant. Prior combined Group, Participant index was replaced with separate indexes.

All five direct-setting changes read back: group Title required; WriteOwner optional blank nonunique Text/255; native integer/type-specific capacity formula/message; membership Group and Participant indexes. Source/membership keys remain required unique/indexed, correct links/focus choices/types, JoinedAt required/LeftAt optional, membership Title unused optional, State default Closed and SetupComplete default No. Other mapped business field IDs/properties/XML semantics unchanged. Formula bracket normalization is equivalent. Actual mapping in `config/group_schema_mapping.json`; raw report `artifacts/group_schema/results/final-audit.owner-report.json`. Raw inspector schemaVerified=false remains intentionally fixed; local reviewed mapping/readback is now verified.

#12 Ready for review / PR #76 ready. No owner rerun or settings package needed; owner chose manual UI changes. 194 local tests previously passed; no executable change in final evidence recording. No row rejection/creation/migration, ordinary-user privacy or consuming-flow/history behavior claimed. No migration exceptions in these observed empty lists. Dynamic count/focus/identity/Ended/history guards remain respective Flow scope; #48 migration remains separate. Source/contract review and merge remain; next focused implementation is #7 Discovery after merge, #61 still Ready for testing. Earlier pending-index entries are historical.


## #7 Discovery owner-preview build â€” 2026-11-08

PR #76 merged `39ebc0cd48c428602a0434a12db0c99ac77a9de5`; #12 closed/Done. #7 is sole active ticket. Actual TandemDiscovery export inspected (source hash `7b4dc1e5df96769615088d897cf86030a2622a47dc7db56a414dbe75f41085a9`): Power Apps V2 number reference, SharePoint Invoker source with Raw authentication, Get item/Get items and candidatesjson/errormessage response. No ordinary-user access proof or owner-credential fallback inferred.

Built `artifacts/tandem_discovery/TandemDiscovery-v2.zip`, build `7c8589d0-fdea-4db8-9d44-46b7d8548acf`, **165 actions / depth 6** (limits 500/8). Preserves actual trigger/Invoker expression, resolves current SharePoint user and unique own profile before candidate reads, uses unchanged #9 normalization/pair/group source, approved typed person/member/group allowlist and fresh membership counts/sharer availability. Optional timezone, culture-only and deferred Any language policy preserved. No writes. Fixed reads are bounded; rendering <=50 people, total group focus/member work <=100 units and response <=250000 characters; any incomplete/over-bound read returns no partial success. Tenant synchronous latency/load not certified.

242 local tests pass, including 48 generated Discovery graph/packaging cases (own/tampered references, availability, blank zone/culture/Any, source/member commitment, group state/count/focus/history, structured-field rejection, read/page/count/work/response limits and Invoker preservation). Native import/run NOT RUN; mode OWNER_PREVIEW_PENDING_ACCESS_PROOF. #42 privacy/ordinary-user two-account proof deferred; do not publish a participant endpoint or change permissions. Candidate groups additionally require live Connection Requests.OperationComplete Boolean plus accepted/complete source/episodes; missing schema fails explicitly, no field creation in #7. Current empty group lists allow an owner people/empty-group smoke without claiming populated group proof. Exact contract and remaining gates in config/discovery_flow_contract.json and inline #7 handover. Existing raw export remains user-owned/untracked, no source replacement or production cutover.


### #7 owner smoke â€” Paused rejected, Active empty success (2026-11-08)

Build `7c8589d0-fdea-4db8-9d44-46b7d8548acf`. Owner run `08584074350262917105745395996CU25` returned PROFILE_UNAVAILABLE/success=false while own Participation status was Paused. Owner manually changed it to Active; fresh run `08584074348343616902680114159CU10` returned OK/success=true, peopleCount=0/groupCount=0, writes=0, ordinaryUserAccessVerified=false. Exact reports and scoped evidence saved under `artifacts/tandem_discovery/results/`. No flow/package change needed for this expected availability result.

This proves owner-context invocation/own-reference path, Paused rejection and Active empty-result completion, not populated compatibility/projection, another candidate's availability, native tampered-ID/two-account proof, imported Run-only selector, group commitment schema or worst-case native bounds/latency. No published app/cutover claimed. #7 remains In progress / PR #77 draft. 242 local tests previously passed; only evidence/config/docs changed.

Owner restated self-service access: avoid individual participant approvals/grants; use verified existing group-based app/flow access. The shown SharePoint connection consent is separate from run/data authorization. Invoker is preserved; no switch to an owner connection and no new permission changes. #42 owns the final protected-data/caller boundary; owner smoke does not resolve it. Remaining versioned tests stay unchecked in issue #7.


## #7 resumed implementation review â€” 2026-11-08

Owner deferred the audience-group/IT question and requested continued #7 work.
#39 assessment is queued Planned with draft #43 and successful owner metadata
run 08584074326403190336298551812CU15 retained; no access method or permission
cutover is approved. #7 is the sole active ticket during this review handoff.
The separate caller/backend modes observed in #39's helper do not change
TandemDiscovery v2's Invoker-only connection or prove ordinary-user access.

Existing build 7c8589d0-fdea-4db8-9d44-46b7d8548acf remains unchanged:
165 actions / depth 6, zero writes. Re-ran the full local suite: 242 passed.
Rechecked the existing ZIP checksum against review metadata; no rebuild/import
is needed. PR #77 is ready for implementation review only; #7 stays open and
does not acquire a whole-ticket Ready label from this partial PR.

The versioned checkbox handover remains inline in issue #7. Owner Paused/Active
empty-result tests are passed. Populated compatibility/projection, candidate
availability, native tampered reference, group commitment/slot/history and native
load/latency remain unexecuted. Request OperationComplete Boolean/live mapping
and operational groups remain explicit integration prerequisites, not permission
to fabricate production requests or groups. #42 access and ordinary-user rollout
remain blocked/deferred. No colleague test, production credential change, app
publication, source-flow replacement or additional import is requested now.

After implementation review/merge, retain #7's remaining tests and blocked cases
for later handover; the next build batch is #10 personal send, #62 inbox and #63
cancellation, with one focused production-flow ticket active at a time.

## #62 metadata comparison correction

Owner's MyRequests v4 smoke stopped at requests_field_SenderParticipantId_gate; preceding query returned body []. The returned Read_requests_fields response was HTTP200 with the correct required Number/Decimals=0 SenderParticipantId, unique=false/hidden=false/readOnly=false. Schema remains verified by #10 preflight run08584074285601068216673996565CU29. No list setting changes are requested.

Reader used bare XPath attribute-node results as an array/value. Replace Decimals and lookup List extraction with XPath string() values, matching the native-passed preflight; handle empty XML safely. Microsoft documents XPath returning nodes or values, with scalar string() extraction: https://learn.microsoft.com/en-us/azure/logic-apps/expression-functions-reference#xpath. Exact native XPath serialization was not returned; the local regression models node/array/scalar shapes and the exact returned Sender metadata. The prior test evaluator incorrectly always returned plain attribute-value arrays. It now exercises the representation difference.

TandemMyRequests-v5.zip build **51130189-433c-4808-b605-031e92bd439c**, 228 actions/depth4 (limits500/8), zero writes. 365 local tests pass, 123 reader cases. Original trigger/Invoker/auth/response/public row shape retained. V4 runtime failure is recorded, not a schema failure or runtime success; v5 native retest NOT RUN. Evidence artifacts/my_requests/results/v4-sender-gate.owner-evidence.json and tests/fixtures/my_requests_sender_metadata.json. Import v5 Create as new (display name TandemMyRequests v5), existing SharePoint Provided by run-only user; run own ParticipantId previously38 and return Respond to a Power App or flow Outputs. Expect OK, requestsjson [], errormessage empty for the empty list. Keep old published app/working flows unchanged; no repeat schema preflight required for this reader fix. Issue #62 stays open.

## #62 legacy null availability — 2026-11-09

Owner v5 smoke reached Data_profiles and failed because rows [0]/[1] have null ParticipationStatus/OpenToConnections. Permit null Status/ParticipationStatus/OpenToConnections in read-only profile input parsing; keep null values and explicit Active/Active/true availability. Do not default them to available or alter profile/membership rows. Missing required properties, invalid non-null types, identity/commit/authority guards remain strict.

Reader v6 build b108407d-4714-4d58-9852-0ffc3099c1e9: 228 actions/depth4, zero writes, 373 local tests /131 reader cases pass. Empty history with unrelated legacy nulls and Pending history cancel/decline preservation are exercised; malformed values still rejected. V5 metadata/caller stages progressed, but native completed history remains unverified; v6 retest NOT RUN. No list changes or preflight rerun needed. Owner confirms affected list rows are disposable test data and welcomes bounded reset/reseed when it simplifies future testing; this fix needs only the package replacement.


### #62 v6 owner empty-history smoke passed - 2026-11-09

Owner returned resultcode=OK, requestsjson=[], errormessage empty, mode OWNER_PREVIEW_PENDING_ACCESS_PROOF; run 08584074267842029485356386842CU16. This is the response to the v6 handover (expected build b108407d-4714-4d58-9852-0ffc3099c1e9); the response does not independently include a build ID. The earlier null-profile error no longer blocks this empty-history run. Supplied excerpt retained in artifacts/my_requests/results/v6-empty-history.owner-evidence.json. No code/package changes or repeat of this smoke needed. Populated personal/group/terminal history, native action integration, app binding and ordinary-user access remain pending; #62 stays open. 373 prior local tests unchanged; evidence-only update.


## Parallel development batch â€” 2026-11-08

Owner explicitly requested parallel flow development after PR #77 merged
`a19176b5e273de56cd09f395153f1fd78f593b6b`. #10/#62/#63 are active in
separate branches/PRs for this batch; this supersedes the one-active-ticket
scheduling rule for this batch only. #7 is queued with remaining tests retained;
#39 audience/IT follow-up stays queued, no privacy cutover authorized.

### #10 implementation and exact bindings

TandemSendRequest v2 build **50e14992-a69a-4001-93f4-1ac8ed57dfe2**;
**125 actions / depth 5**, limits 500/8.
Original export SHA `823383a1b2941a38ebf80c3e2f0a288f72a9956d24db793767e2dda5eeff0ab8`; raw archive private/untracked.
Preserves original SenderParticipantId `number`, RecipientParticipantId `number_1`,
Invoker Raw connection, Boolean success and Text message outputs. Adds required
Text `IntentId` (`text`) and report/reference/status/code outputs. The app must
refresh/add the new flow binding and supply the retained intent; no transparent
old-button cutover is claimed. Create as new only. Maintained #9 source unchanged.

Send resolves caller before request/candidate reads; scoped server identity,
current compatibility/availability, idempotent request receipt, native unique
live connection key and legacy unsettled-pair guard. One POST with retries off;
exact immutable readback reconciles lost success. Unknown stays unknown; no
fake rollback, membership/group creation, profile update or auto-cancellation.
29 new emitted-graph/local cases pass; tenant import/write/race/ordinary-user
results NOT RUN. Schema prerequisites remain real integration work, not a PASS.

### One metadata preflight before this batch

TandemRequestSchemaPreflight build **f7fd078d-740a-4d68-a8fe-31ca2abc9e54**,
**18 actions / depth 3**. No inputs, item reads,
writes or permission/schema changes. Shares the expected request mapping with the
send gate. Local valid/missing-schema cases pass; native NOT RUN.

Do not enable required/unique fields or backfill existing requests blindly.
Old exported send omits the coordination keys; old cancel only changes Status.
Their incompatibility must be handled in the later coordinated cutover, not by
claiming the new flows are already integrated. Request Type/TargetGroup/custom
keys are proposed names until metadata is collected. #11/#17/#65 own their writers.
Exact operator/test checkboxes are inline in #10; #62/#63 own their handovers.

### Parallel batch delivery â€” 2026-11-08

All three isolated implementations are built: Send #10 / PR #78 (125 actions/depth 5), My requests #62 / PR #80 (223/depth 4), Cancel #63 / PR #79 (138/depth 5). Shared read-only request schema preflight is 18/depth 3. All source Invoker bindings preserved, no embedded fallback; send alone adds a required retained intent UUID. Reader preserves original created timestamp/order and response row fields; cancel preserves its two input arguments. No writer cutover, schema setup or app publication performed.

Combined disposable-checkout suite: 455 tests passed plus one additional cross-generator send -> cancel -> history -> same-send replay check passed. Per-flow added cases: send/preflight 29, reader 104, cancel 80. Version/hash/source commit evidence is in artifacts/send_request/request_batch.validation.json. This is local generated-graph proof, not native acceptance.

Packages delivered together locally in artifacts/request_batch/TandemRequestFlows-20261108.zip (outer delivery archive, not directly importable); extract and import the inner schema preflight first. Each individual flow ZIP also remains under its own artifact folder. Three separate implementation PRs are ready for code review; tickets stay open. Checkbox handovers are inline in #10/#62/#63. Real request mapping/constraints/legacy rows and coordinated old-writer compatibility remain native integration blockers; inspect schema metadata before running replacement writers. Participant rollout is still access-gated.

## Request schema native observation and adapter correction â€” 2026-11-08

Run 08584074297422149453962972460CU27 (initial preflight f7fd078d-740a-4d68-a8fe-31ca2abc9e54) collected metadata, schemaVerified=false, zero item reads/writes. SenderParticipantId/RecipientParticipantId are existing required Number/Decimals=0, not Lookup fields. Status already matches. Owner reports list empty. Preserve existing field IDs/names/types; no migration needed for this observed empty list. New fields RequestType/TargetGroup/SendOperationKey/ConnectionKey/WinningOperationKey/OperationComplete remain absent, and RecipientParticipantId optionality is needed for Group requests. Source report and reviewed mapping under artifacts/send_request/results and config/request_schema_mapping.json.

Corrected Send v3 a9251019-b7a5-4170-8877-682bb71b8693 (125/depth5), preflight v2 dd0c91b6-13b4-41e0-affd-ebafeeb87404 (18/depth3), preserve numeric references and report ItemCount in metadata. 34 added send/preflight cases / 276 branch tests pass locally. Reader/cancel adapters follow in separate PRs. No tenant settings or rows changed. Owner setup and test-window/cutover impact are explicit in #10; required keys make the old Send incompatible until new binding. Updated whole schema/native actions/privacy remain unverified. Prior local batch evidence is historical, not new-build/native certification.

## Request schema verification passed â€” 2026-11-08

Corrected preflight dd0c91b6-13b4-41e0-affd-ebafeeb87404 run **08584074285601068216673996565CU29**: collectionComplete=true/schemaVerified=true, ItemCount=0, itemRowsRead=0/writes=0. Numeric SenderParticipantId/RecipientParticipantId field IDs retained; recipient optional, six new field types/required/unique/index/default/lookup/choice metadata all match. Status unchanged. Verified mapping in config/request_schema_mapping.json; curated report/evidence in artifacts/send_request/results/schema-verified.*. No migration necessary.

Actual returned metadata also passes all three generated graphs with synthetic rows locally (send SAVED, cancel CANCELLED, reader OK). This verifies metadata compatibility only; native writer/history, edit permission, races, app binding and ordinary-user privacy remain untested. Schema gate is cleared for owner smoke; no new package or setup needed. First smoke: MyRequests-v4, Create as new, existing Invoker connection, own ParticipantId (previously 38), expect resultcode OK / requestsjson [] / errormessage empty. Return Respond to a Power App or flow Outputs. Do not use old Send with required keys; new writer/app/all-writer cutover remains pending.


### #10 owner send smoke results - 2026-11-09

Owner reports matched send SAVED/Pending and unmatched send passed rejection after new-intent guidance. Expected Send v3 build a9251019-b7a5-4170-8877-682bb71b8693; successful run references/full outputs not supplied. Prior provided INTENT_CONFLICT run 08584074252930158987892330133CU13 is retained as separate evidence and is not the unmatched-case pass. Source in artifacts/send_request/results/v3-send-smokes.owner-evidence.json. Recipient30 previously lacked participation/openness, was excluded before matching; owner changed test fixture. This is bounded owner smoke, not full REQ-001/AUTH-002 acceptance: exact stored parties/keys, same-intent replay/no duplicate, cancellation/history, races, UI and ordinary-user access remain pending. No executable/package change; #10 remains open. Next: retry successful sender/recipient/IntentId unchanged, expect REPLAY/same request ID and one row.
## Planned single shared validation workflow â€” #81

Owner direction is tracked by [#81 TandemValidateContext](https://github.com/maoy1/tandem-language-culture-app/issues/81). Existing #9 shares generator source, not a single deployed validation workflow. #81 owns one read-only shared workflow for schema checks, normalization and person/group compatibility, with versioned operation-specific inputs/results. Business flows should retain their operation logic and the minimal identity/authority and atomic live-state/ETag/unique-key guards needed for correct writes. Full schema audit and fresh live eligibility have different timing; a setup audit cannot replace operation-time data checks.

Implementation has not started. Allowed invocation, deployment/import mechanism, tenant entitlements, caller propagation and latency must be verified before depending on child flows/Solutions or removing repeated checks. No paid/external fallback is approved. Existing working packages are unchanged. #81 contains unchecked capability, schema, rule-parity, version-drift and consumer-proof acceptance; consumer cutovers remain in their own Flow branches/PRs. Ordinary-user proof remains deferred, not waived.

Mandatory change rule: every schema/mapping/catalogue/rule/normalization/availability/capacity/commit/public-contract change updates #81 ledger, shared implementation/contract, design/plan, affected consumer issues/packages and relevant regressions/evidence, or records a concrete no-impact assessment. Old native evidence is retained with its version and affected new behavior stays NOT RUN until retested. AGENTS.md makes this a required review item until automated drift validation exists. Preserve completed #9/#12/#66 history and unresolved #10 replay/Pending-row tests.


## #81 invocation proof preparation and ordered consumer plan

Owner authorized this order: **#81 invocation proof -> #10 Send -> #62 My requests -> #63 Cancel -> #7 Discovery -> #61 submission**, applying the shared design while finishing #11 Respond. #81 is the sole active ticket; #10/#62/#63 are queued Planned with their implementations and evidence retained. See [#81](https://github.com/maoy1/tandem-language-culture-app/issues/81) and config/shared_validation_invocation_proof.json for the reviewed source hashes, measured consumer action/depth inventory and proof contract.

Microsoft's documented child-flow route requires Solution-aware parent/child flows. Parent connections cannot be passed to children; a child using SharePoint needs its own embedded connection. Sources: https://learn.microsoft.com/en-us/power-automate/create-child-flows and https://learn.microsoft.com/en-us/power-automate/create-flow-solution. These are documented platform requirements, not tenant entitlement/caller proof. The current account proved legacy import only; no Solution/database/maker entitlement or child invocation is inferred. There is no connected tenant browser session.

First owner check: inspect More -> Solutions in the existing Tandem environment and return whether the list opens or the exact prerequisite prompt. No trial, database/environment creation, paid dependency or working-flow change is part of that check. The first native proof is planned as disposable connector-free parent/child token+correlation echo in one allowed Solution, followed by repeat/error cases and export of that native envelope. No new generated package or measured proof-flow definition exists yet; do not label a legacy import as child-invocation proof. Exact test/setup/expected evidence and cleanup are inline in #81.

Pure child invocation does not prove SharePoint caller propagation. Parent business flows retain authenticated caller binding and atomic live write guards. The future shared child data-read/connection boundary is not selected; no embedded owner fallback or production Run-only change is approved. Full-schema audit belongs to maintenance/deployment mode, fresh relevant data remains operation-specific. No schema/rule/business package changes or transferred test PASS. #10 failed replay/unexplained old Pending row remain unresolved. All #81 native tests NOT RUN while first capability evidence is pending.


### #81 first tenant prerequisite result

Owner confirms the Solutions list opens normally in the existing Tandem environment. This proves page availability only; Solution creation/editing rights, current entitlements, linked parent/child execution and packaging remain NOT RUN. The next bounded owner test uses only two disposable connector-free flows in one unmanaged test Solution: manual child echoes ProofToken and returns native ChildRunReference; manual parent calls it and displays both outputs. Run V1/V2 tokens, retain distinct native parent/child runs, then export the unmanaged test Solution as the real packaging reference. No production credential mode, data, app or list changes. Full exact steps and stop conditions are inline in #81.


## #81 native echo passed; shared pure validator built

Owner supplied V1 echo `TANDEM81_INVOCATION_V1`, child run `08584069538865401663915371009CU10`. Native unmanaged `Tandem81InvocationProof` version 1.0.0.1 export SHA256 `5560d8d80f78de67966160fe0276711494b76c0f176e19356d6cf32d2c4c191c` was inspected: one child response, one parent Workflow call, matching native workflowReferenceName, no connector references. Publisher Tandem/prefix tandem was owner-created. This establishes bounded connector-free invocation, not general SharePoint caller/credential propagation or ordinary-user rights. Parent run reference/second-token run not supplied. Curated evidence: artifacts/shared_validation/results/invocation.owner-evidence.json; original raw export remains local/untracked.

Built **TandemSharedValidation81-v1.zip**, new unmanaged Solution `TandemSharedValidation81`, build `31382f7e-a0df-44a2-9fde-223a11774e67`, SHA256 `cb0102c74fc669541cb30895dea065f45ce6e410204df742bd949f190bae02c0`. Fresh workflow IDs preserve the original proof and all business flows. **TandemValidateContext: 84 definitions/depth 7; TandemValidationSmoke: 8/depth 2**, limits 500/8, import disabled. This package is Solution import, not legacy My flows package import: native linked-flow packaging is now the tested reference, generated imports still NOT RUN. Readable child/smoke definitions and review accompany the ZIP.

Implementation decision: the shared child is a **pure connector-free evaluator**. SCHEMA compares operator/parent-supplied complete native metadata against 7-role/48-field versioned baseline; it does not collect or authenticate snapshots. Full/schemaRoles audit is explicit, not repeated wholesale on participant actions. NORMALIZE, PAIR, GROUP and PROFILE centralize reusable rules, permit null availability as ineligible, keep optional time zone/culture-only/one-way fit and Any-deferred matching. PROFILE still accepts a known Any selection as valid registration content; it never makes Any a matching wildcard. New wrapper adapts #9 rather than changing the closed proof/source.

Parents keep trusted SharePoint reads and caller resolution; an embedded owner child connection is not introduced. Input data/returned `success` never authorize actions: PAIR consumers must check `result.eligible`, GROUP consumers `result.compatible` plus operation conditions, PROFILE `result.valid`; schema results certify supplied metadata equality only. Keep parent authority/commit/replay/ETag/unique-key writes and approved app projection. Raw internal normalized account keys must not be passed to the app. Group member/focus-availability freshness and metadata completeness come from trusted adapters, not client declarations. Current business packages unchanged; #10 replay failure/earlier Pending origin remain unresolved.

**330 local tests pass, 88 new cases**, including execution of the packaged parent across all 44 child cases (39 prior compatibility fixtures, exact synthetic 38/32 no-overlap, null participation, version mismatch, schema baseline/mutated-required). Schema regression cases cover type/required/unique/index/default/lookup/choice/decimals/formula, missing/duplicate/incomplete metadata, and extra benign indexes. Expected rejection uses normal result branches, no intentional divide-by-zero. Fingerprints reject stale participant/group/request mapping baselines; hashes/builds remain explicit. Native generated Solution import/smoke and real consumer parity NOT RUN.

Next owner step: **Solutions -> Import solution** for this ZIP, enable only new child then smoke parent, manually run TandemValidationSmoke (no inputs/connections), return Smoke_report Outputs. Expect matching build, testCount=44, completedCount=44, allPassed=true and failedCases=[]. Exact prerequisites, checkbox cases, failure handling and cleanup are inline in #81. Keep #81 active/open; #10/#62/#63 queued Planned. No list/app/data/permission/working-flow changes. Once shared smoke passes, #10 migration starts with native caller/consumer parity before duplicated guards are removed; then #62/#63/#7/#61 and shared design in #11.


## #81 v1 native input defect and v2 quick-first correction

Owner v1 report build 31382f7e-a0df-44a2-9fde-223a11774e67, run 08584069519927027175534029560CU24: 44 completed/44 cases, allPassed=false, all 44 results empty. Generated Solution import and linked invocation worked; validation failed. Owner then supplied Request_text ValidationFailed and its input: serialized JSON document with string/maxLength schema. Parse JSON deserializes that document before schema validation, so the object fails a string schema. The earlier local interpreter validated the raw string instead and missed this native boundary. V1 regression now reproduces the actual failed Request_text and INVALID_INPUT. Reports retained in artifacts/shared_validation/results/v1-*; no rule or tenant/list-setting fault inferred.

V2 validates an object containing bounded string value, then deserializes that value once. Child response adds sanitized stage statuses; parent failedCases adds actualCode/expectedCode/diagnostics. This changes no matching/schema baseline semantics, public input, eligibility/authority contract or consumer flow. **TandemSharedValidation81-v2.zip**, Solution version 1.0.0.1, build c79b7b64-b3ce-4de3-aa74-0ed62bca1524, SHA256 608052804073ccd2874a1f9d83fbfeb62fd331fcbe86e7be5ed375139576717e. The update preserves ONLY existing generated #81 child/full-smoke IDs and adds TandemValidationQuickSmoke; original proof and all business flows are untouched. Never delete/recreate or change list data to address this parser defect.

Measured: shared child84/depth7, full parent8/depth2, quick parent8/depth2 (limits500/8). 335 local tests/93 new cases pass with native-style Parse JSON and update-ID regressions; full packaged 44-case graph and 3-case quick gate pass locally. Prior native v1 is FAIL; v2 native NOT RUN. Input handling guidance: https://learn.microsoft.com/en-us/azure/logic-apps/logic-apps-perform-data-operations.

Owner next: Solutions -> Import v2 as UPDATE of TandemSharedValidation81, verify/enable child and new QuickSmoke, then run QuickSmoke only (no inputs). Expect suite QUICK, current build, testCount=3/completedCount=3/allPassed=true/failedCases=[]. Cases: compatible pair, exact 38/32 no-overlap and version rejection. Return Smoke_report Outputs; on failure actualCode and diagnostics are retained. Do not rerun the long 44-case full smoke until this short gate passes. No new connections/read/write fixtures. #81 remains active/open, real consumer/SharePoint boundary and batch business-flow delivery pending; no consumer readiness/acceptance upgraded.


### #81 v2 native quick gate PASS

Owner report matches v2 build c79b7b64-b3ce-4de3-aa74-0ed62bca1524, suite QUICK, run 08584069506351729738499173108cU14: 3 expected/3 completed, allPassed=true, failedCases=[], syntheticOnly=true, connectors/reads/writes=0. Curated body artifacts/shared_validation/results/v2-quick.owner-report.json. Confirms imported update/quick helper and corrected input path for compatible pair, exact no-overlap 38/32 and version rejection. Prior v1 44/44 failure is retained, not rewritten as passed.

The full v2 44-case corpus (including GROUP/schema) and production-parent SharePoint/caller/consumer parity remain NOT RUN. No elapsed-time measurement, live-schema audit, privacy proof or business-flow readiness inferred. Next: run the already imported TandemValidationSmoke full parent once, no new import/inputs/data edits, expect same build/suite FULL/testCount44/completedCount44/allPassed true/no failed cases. Record exact report/error; keep #81 open/In progress. 335 previous local tests unchanged; this is evidence-only.


### #81 v2 native FULL suite PASS

Owner report matches v2 build c79b7b64-b3ce-4de3-aa74-0ed62bca1524, suite FULL, run 08584069504668815720383921608CU09: testCount=44/completedCount=44, allPassed=true, failedCases=[], syntheticOnly=true, connectors/reads/writes=0. Exact curated report artifacts/shared_validation/results/v2-full.owner-report.json. Together with prior quick3 PASS, the imported shared evaluator now passes the complete packaged synthetic corpus, including GROUP/schema snapshots and expected rejection cases. V1 failure history is retained. No repeat full run requested.

This is supplied-fixture/runtime validation, not live SharePoint schema provenance, ordinary-user access, business parent Invoker mapping, current domain reads or atomic writer integration. No latency measurement supplied. #81 remains open/In progress pending relevant native parent/consumer proof; 335 prior local tests unchanged, evidence-only update. The next packaging prerequisite is a disposable Solution parent using the existing SharePoint connection with Run-only Provided by run-only user, GET currentuser Id, followed by the real shared child. No schema/data/permissions/working flows changed. Backend core batch remains 11 business flows plus validator; 2,000-character introduction planning is #17 and actual new schema/receipt setup must update #81 when mapped.


### #81 owner Solution SharePoint + shared-child probe passed; export pending

Owner supplied SharePoint GET body d.Id=16 and shared-child resultcode OK/success true, matching v2 build c79b7b64-b3ce-4de3-aa74-0ed62bca1524, child run 08584069483776257593504328231CU07. Empty normalization result and authorizesAction=false match the requested probe. Curated supplied values in artifacts/shared_validation/results/sharepoint-caller-probe.owner-evidence.json; parent run ID/name are not independently included in the supplied bodies.

This is an owner-context execution result for the requested Tandem81CallerProbe, not proof of Run-only Invoker source, connection-reference export shape, ordinary-user context separation, business authorization or caller-bound write parity. Parent performed a metadata GET; child's zero-I/O counters describe only the pure child. No business rows/schema/permissions changed. Next: export TandemSharedValidation81 UNMANAGED with the new probe/SharePoint reference and return ZIP path for native packaging inspection; no repeat probe/full smoke requested. #81 remains open, 335 prior local tests unchanged (evidence-only).


### #81 native Invoker envelope inspected and guarded builder adapter added

Inspected owner export TandemSharedValidation81_1_0_0_2.zip, SHA256 ce19af2e37e7de4a9317ec4c63e8d5777beaf23a57120c99b4e38d38ce4946d4, unmanaged Solution version 1.0.0.2. Four workflow roots match components. The shared child still matches the delivered native-passed c79b7b64-b3ce-4de3-aa74-0ed62bca1524 v2 action graph after ignoring designer metadata; its 84/depth7 structure is unchanged. CallerProbe has 2 actions/depth1: one GET of currentuser Id and one call to that child. Its SharePoint runtimeSource is explicitly invoker, logical reference cre46_sharepointonline_a22363a216 resolves to the standard SharePoint API component, and Raw authentication is the native per-trigger X-MS-APIM-Tokens/$ConnectionKey expression. No new connector, embedded fallback or owner token substituted.

Curated native configuration receipt: artifacts/shared_validation/results/native-sharepoint-solution.analysis.json. Original native export stays local/untracked. scripts/power_automate/solution_source.py now validates this source, linkage, site/read scope and interactive connection shape, then prepares caller-preserving parent documents. It rejects a changed connector/auth/site, wrong child/build, unresolved components, automatic-event trigger or unverified runtime. This adapter is local packaging code only; it does not itself create/deploy a business flow or certify it. Automated/event #61 owner binding must be preserved/reviewed in its own adapter, not converted through this manual Invoker seed.

**357 local tests pass (115 #81 cases, including 22 new native-source guard tests)**. No runtime definition/ZIP or matching/schema semantics changed; native QUICK3/FULL44 and owner Id16 execution evidence remain intact. This clears inspection of the manual Solution Invoker template. Power Apps Solution consumer invocation, actual data/authority/write parity, new schema/receipt/Introduction setup and ordinary-user access remain pending. No more owner connection-probe run or raw source export requested for this inspected seed. Batch implementation will use this observed envelope with receiving-ticket tests/guards; no all-business-flow delivery or release-readiness claim.
## #17 optional group-join introduction length accepted

Owner chose **2,000 characters** for the optional plain-text group-join introduction, enforced in both app and flow. Empty/omitted remains allowed; 2,001 characters must be rejected before a request write, preserving user edits in the app. This does not add a personal-request introduction requirement or select a notification channel.

Technical field proposal: optional plain-text Note column Introduction on Connection Requests, rich text/append disabled; actual column/settings are NOT verified or applied. SharePoint field mapping/setup and the flow/API/app mapping remain #17 work. All schema changes must update #81 baseline/audit/contract and affected consumers (#62/#65/#67), with existing native evidence retained by version. #81 has no Introduction persistence/parser today, so this planning decision does not change its current five-mode rule engine/package. Add actual schema coverage when the field is introduced.

Contract evidence only: acceptance cases empty/omitted, 2,000 accepted and 2,001 rejected in both app/server are NOT RUN. #17 remains Planned, not implemented/Ready. No flow, list, data, permission or existing app changed. This clears the remaining explicit product choice for core group-join implementation; receipt-schema and Solution SharePoint/caller prerequisites still need technical verification.


## #14 TandemLeaveGroup owner-preview builder — 2026-11-14

[#14](https://github.com/maoy1/tandem-language-culture-app/issues/14), authorized parallel batch: build 4ad78357-d0de-4920-88e1-e998ad529a6b / SHA256 0d8f4f688b1b410200d7f692f014ad01d4bf10643783a41ee0a1eab7de038b1f, 234 actions/depth4 (500/8 limits). Own committed Active episode -> Left/UTC LeftAt under shared opaque operation:attempt UUID WriteOwner exact-ETag guard; physical Active count includes provisional rows, which never authorize actions. Stable UUID intent, immutable completed receipt before exact old-token release; incomplete/unknown recovery read-only, no lease/auto-state/rejoin/delete/openness reset. Closed/Ended/history preserved. Parent receipt schema is proposed/unverified; shipped legacy ZIP returns CONFIGURATION_REQUIRED before I/O until parent rebuilds with verified GUID/schema binding. Parent assembles Solution; native consumer tests NOT RUN, ordinary access deferred. Local graph/Discovery evidence and exact IO/native handover/#81 draft ledger in docs/ISSUE_14_LEAVE_GROUP.md and config/leave_group_flow_contract.json. Shared child/common/other flow modules and #63 untouched; no push/issues/deployment/Ready claim.


## #14 one-import receipt target correction — 2026-11-14

[#14](https://github.com/maoy1/tandem-language-culture-app/issues/14) 14.1.1 supersedes earlier blocked preview: build ffc7d090-7f7f-4f9b-bc8d-bb255b69c56d, ZIP SHA256 dd87c748a9a6fcd9b0d4bca5946797d7d394f9121c9b15e9cbc0cbb5959b8c27, 231 actions/depth4. Default exact unique title TandemOperationReceipts; optional actual nonzero GUID pin. No zero placeholder or generation-time Configuration_verified blocker. One Solution import -> parent Setup Apply + full Audit -> enable/test same flows, without rebuild/reimport. Runtime reads live Id/Title/entity type/current receipts and fails closed if missing. Selection is not tenant schema verification (review false). IO/authority/counts/CAS/receipt-before-release recovery unchanged. Native setup/audit/consumer tests NOT RUN, ordinary access deferred. Own contract/handover record #81 adapter impact; no shared module/other flow edits.

## #13 TandemUpdateGroup local implementation — 2026-11-14

[#13](https://github.com/maoy1/tandem-language-culture-app/issues/13), under [#45](https://github.com/maoy1/tandem-language-culture-app/issues/45): dedicated codex/issue-13-update-group reused the clean former #81 worktree from origin/main7eba0ba; #10 untouched. Build 55d4d4c3-958d-48a1-ac0e-a20fdea8ad1f supplies a full parent/legacy ZIP with strict allowlisted actor/group/expectedETag/UUID and Title255/Purpose2000/capacity/state input. Purpose2000 is a technical plain-text API bound, no Note setting change. Type/focus immutable, Ended final, no automatic state changes.

Authority is authenticated own profile plus current committed Active membership/source/episode, re-read under the exact operation+attempt group guard. Personal Paused/Inactive/openness does not revoke group controls; no Discovery availability or matching guard is reused. Capacity includes all physical Active/provisional/paused rows. Immutable receipt/CAS/exact readback and own-token release protect updates/replay; unknown effects retain ownership without a lease/platform. Historical saved result and current snapshot/revision are separate.

Default receipt target resolves the exact unique title TandemOperationReceipts and reads current ID/title/BaseTemplate/entity type/rows, failing closed when absent/invalid. Parent imports the Solution once with business flows disabled, runs Setup Apply+Audit, then enables/tests the same flow: no GUID placeholder, always-false configuration gate, rebuild or reimport prerequisite. Optional actual GUID pin is supported. Runtime target selection does not certify all tenant fields/settings. Standard built-in receipt Title gets OperationKey without schema changes.

Parent250 definitions/depth5 within500/8. Exact IO/mapping, builder, app call and future native fixtures/steps/expectations/failure/cleanup/evidence: artifacts/update_group/HANDOVER.md; final counts/hashes: validation.json. Native schema/caller/member/write/race/app tests NOT RUN; ordinary-participant proof deferred. No Ready/Done claim.

#81 drift: shared schema/rule/normalization/compatibility source/version/build unchanged; operation-only #13 consumes the parent's ten-field receipt target hash f189c44795dd448faaf7c8a0087b3aeed6357b264f21f8cb4e8860955b308495. Parent owns Setup Apply+Audit, baseline title-to-ID evidence, native Solution/bindings and #81/#13 ledger/issue updates. No schema/permission changes, push or issue writes here; other flows/#10 were not edited. Historical native proofs remain scoped.

Final #13 local verification: **116 UpdateGroup tests / 473 repository tests PASS**; final parent **250 definitions/depth5**, ZIP/full-document/source hashes PASS. Same default title-resolving graph passes absent-store failure then post-setup success without rebuild; optional GUID pin/metadata failures tested. Native schema/caller/authority/write/race/app tests NOT RUN; one-import parent Setup Apply+Audit then enable/test remains the deployment sequence.

## #64 TandemMyGroups v1 — independent read-only parent, native NOT RUN

[#64 TandemMyGroups](https://github.com/maoy1/tandem-language-culture-app/issues/64), overview [#45](https://github.com/maoy1/tandem-language-culture-app/issues/45). Branch `codex/issue-64-my-groups` starts at origin/main `7eba0ba`; no #62 ancestry/import/cherry-pick. #62 b9d6516 remains unchanged. Tiny pure action constructors adapted into the new own module; contract/source/artifacts/tests are #64-only and shared docs append-only.

Readable `artifacts/my_groups/TandemMyGroups-v1.definition.json`, build `9222dc1c-bbec-48a6-8366-056d5897b7d7`, SHA256 `a63d21b6b3a44b61b669c3e9c5a6ad10b1f9dc3144655e95350a5656040ab1e3`. Measured **181 action definitions/depth5**, nine standard SharePoint GETs, zero writes/child calls (limits500/8). `build_actions(source, people, groups, build_id)` returns the FULL action graph; `build_trigger()`/`build_source(inspected_seed, people)` provide explicit PowerAppV2 number-reference/source builders. Parent integrator assigns new workflow/root and packages inspected native Invoker reference in its assembled Solution. No legacy ZIP/new native certification supplied; no original flow/app/child/schema/permissions changed.

Same Invoker currentuser -> unique own ParticipantaccountId -> exact positive-integer reference equality precedes broad data reads. Own current audience needs Active/empty LeftAt episode, SetupComplete group, Accepted+OperationComplete Personal source and exact committed Personal-source-party or Group-target/sender membership episode. Left/provisional/partial/mismatched groups are not current. Every committed own group remains visible in Open/Closed/**Ended**, per owner #64 direction; Waiting for zero, In a group for >0, empty status on failure. Member availability/validation never gates current/history membership, and no group state is mutated.

Counts use ALL physical Active rows, including provisional/paused; public member profiles use only operational committed episodes. Existing Number Capacity/SourceRequestId require whole values before canonicalization; enforce approved type-specific capacity and fail overfull instead of clamping/releasing slots. Return only approved #46 group/profile display allowlist, including optional Comments/timezone and historical inactive catalogue labels. Group expectedETag is the sole item revision marker needed by controls, pattern-limited; no emails/raw account/Claims/status/audit/processing/source/episode/write-owner data. Exact fields/bounds/failure contracts: `config/my_groups_flow_contract.json`.

#81 drift/no-impact: no shared child/common source/schema/baseline/contract/package change. Explicit maintenance audit is #81-owned; no per-click metadata scan. This direct typed allowlist display adapter needs no NORMALIZE/eligibility call; paused/Inactive members and inactive historic labels must remain displayable. No duplicate compatibility engine is added. Child failure is N/A (zero Workflow actions), while all backend/null/incomplete/projection failures sanitize and clear all output. Pending batch target receipt/Introduction schemas are irrelevant to these existing reads; actual tenant/native #64 proof is NOT RUN. Existing #12/#66/#81 proofs stay versioned; no issue/label/push changes. Parent ledger can consume this no-impact entry under no-issue-edit scope.

#64 local evidence: **465 full-suite PASS / 108 new reader cases**, 83.53s. Exact delivered graph/hash/source and 181/depth5/9GET/zero writes checked. Shared/common source and shared contracts match origin/main unchanged; #62 module absent/no ancestry/import. #62 b9d6516 remains in its separate worktree. Native own-flow/app/access cases NOT RUN. Evidence `artifacts/my_groups/validation.json`. Cross-flow authority reminder confirmed: personal Paused/openness never gates own committed group view/control/Leave/respond authority; new-requester/focus-sharer eligibility belongs separate operation rules. No available-actor Discovery gate used.


## #64 v2 — own committed membershipId for #14 Leave intent

[#64 TandemMyGroups](https://github.com/maoy1/tandem-language-culture-app/issues/64) now returns required positive-integer `membershipId` on each public OWN-group row for [#14 TandemLeaveGroup](https://github.com/maoy1/tandem-language-culture-app/issues/14) input `number_2`. Retain raw membership.Id inside OperationalEpisodes; filter actor-bound Own_episodes by current group, require exactly one result, then project only its Id. Other members' membership IDs, Left/history/provisional IDs and raw membership records remain private. Public member profiles are unchanged. MyGroups input remains only ownParticipantId; ID is a stale-intent reference, never authority. #14 still verifies authenticated actor, exact group/episode and freshness.

Readable artifact `artifacts/my_groups/TandemMyGroups-v2.definition.json`, build `31fbef9c-81bc-4409-bf9f-2f25b4c0e6a1`, SHA256 `440df39b310047dde6118e0c30fae9e78192bd9f52b6c9fdf5bc5c7c3031a101`. **185 actions/depth5, nine GET definitions/zero writes/zero child calls** (limits500/8). v1 artifacts/results retained as history; native v2 import/Leave binding/ordinary-user access NOT RUN. Parent assembles/imports Solution; no #62 edits or foundation merge, no shared/common/schema/contract/package changes. #81 drift/no-impact: only existing own membership system Id projected for the receiving #14 input; no capacity, commitment, normalization, eligibility or tenant mapping change. No ticket/remote/runtime changes.

#64 v2 local validation: **466 full-suite PASS / 109 reader cases**, 25.53s; exactly one added own-ID/no-other-membership-ID-leak regression. Delivered v2 definition/generator hashes and185/depth5/nine GETs/zero writes checked. #14 native binding remains NOT RUN; #62 untouched. Current evidence artifacts/my_groups/validation.json; v1 evidence retained as previousV1.

## #65 group-join response parent — 2026-11-14

[#65 TandemRespondGroupJoinRequest](https://github.com/maoy1/tandem-language-culture-app/issues/65)
has an isolated local parent on origin/main, build 040a6af8-ab91-4e09-b891-b638d96178ba,
449 definitions/depth5. Current operational Active membership is authority;
actor Paused/openness does not revoke it. Accept separately uses NORMALIZE/GROUP,
fresh requester/focus/profile context and all physical Active counts under the
same #47 group guard; Pending exact-ETag first terminal competes with cancellation.
One immutable episode, no Left reactivation or group state changes. Receipt result/
Complete precedes matching-token release; definite sealed retry is bounded and
unknown/partial outcomes cannot report success or use timed takeover. The exact
parent/schema/connection/IO and #81 justified no-impact ledger, prerequisites and
versioned NOT RUN handover are in [ISSUE_65_GROUP_RESPONSE.md](ISSUE_65_GROUP_RESPONSE.md).
One-time receipt/schema setup, final Solution assembly/import and native caller/
business/load proof remain pending; ordinary-user access is deferred/#42-blocked.
No #7/#11/shared helper/evidence/issue/working-flow edits or readiness upgrade.


## #65 shared finalization refactor — 2026-11-14

[#65 TandemRespondGroupJoinRequest](https://github.com/maoy1/tandem-language-culture-app/issues/65)
refined build `ea732b74-947a-4478-a7df-92d2ff5696a1`: **393 actions/depth5**, 107 action headroom.
Normal Accept/Decline, rejection and positive committed recovery share completion;
completed/sealed operations share final matching-token release. Prior sealed-token
release stays before retry claim. Fresh CAS/authority/commit/uniqueness checks and
#81 NORMALIZE/GROUP contract1/rules1 remain; no schema/public IO/shared-runtime
change or extra flow/helper. Historical 449/415 evidence remains versioned, not
transferred to this build. See ISSUE_65_GROUP_RESPONSE.md for new validation,
source-action alias mapping and remaining NOT RUN tenant/access/performance gates.

## #17 group join sender implementation candidate — 2026-11-14

[#17 TandemSendGroupJoinRequest](https://github.com/maoy1/tandem-language-culture-app/issues/17),
under [#45](https://github.com/maoy1/tandem-language-culture-app/issues/45), is built
locally on its own owner-authorized parallel-batch branch from origin/main7eba0ba.
Build **issue-17-group-send-v1**, **147 action definitions/depth5**. New Power Apps
V2 input order: **GroupId(number), IntentId(text UUID), Introduction(text_1 optional,
plain text max2,000)**. No caller-supplied actor: native SharePoint Invoker resolves
current account and exactly one own profile, rechecked against the current item.

Exact immutable **group:{actorId}:{lowerUUID}** replay precedes availability/group
checks. Stored sender, recipient=null, group and original Introduction (null/omitted
canonical empty) must match, including valid live/history lifecycle; changed payload
conflicts. Fresh sends check Open/SetupComplete/blank WriteOwner, committed source
and membership episodes, all physical Active rows/count/capacity, no own current or
provisional membership, and actual shared GROUP contract1/rules1 fit/availability.
Available focus sharers come from current member profiles; culture-only and optional
zone/null availability use unchanged child rules. No whole-schema audit per send.

One Pending request POST at most, retries off: RequestType=Group, numeric trusted
sender, nullable recipient, TargetGroupId, exact Introduction and unique immutable
SendOperationKey/live **open:group:{groupId}:participant:{actorId}**. Exact intent
readback reconciles lost success; unconfirmed/corrupt/failed readback stays unknown,
with no second POST. No separate receipt is needed for this sender. No group,
membership, permission or schema writes; acceptance rechecks remain #65, not a
slot reservation by #17. App call/draft preservation guide is prepared, not applied.

Readable full native Invoker Solution parent/review in artifacts/group_send; no
standalone legacy ZIP before valid final core Solution assembly. Native parent,
app, access and new request tests **NOT RUN**. Planned Introduction Note/plain/2,000
comes from #81 batch_schema_contract.json at a385e284; actual field/unique-key/setup
audit and connection/caller verification block activation. Ordinary access remains
deferred. No issue edit, native cutover or readiness/closure claim by this change.

#81 drift ledger in config/group_send_flow_contract.json: shared child/schema/rules
and other packages unchanged; same child e9aa88eb-a666-4df1-b088-176be7bcd00d/v2 build
c79b7b64-b3ce-4de3-aa74-0ed62bca1524, previous QUICK3/FULL44 results retain only their
old scope. Setup must cover actual Introduction before activation; #62/#65/#67
preserve immutable original text and authorized plain display. #61 commit996a3ae
and its automated Embedded marker remain separate and unchanged. Full #17 mapping,
bounded tests, blocked cases and cleanup: docs/FLOW_17_GROUP_SEND.md.

# Issue 11 native response build — 11.1.0

[#11 TandemRespondRequest](https://github.com/maoy1/tandem-language-culture-app/issues/11)
now has an isolated generated native consumer candidate. See
[its contract/handover](ISSUE_11_RESPOND_REQUEST.md) and
`config/respond_request_flow_contract.json`. Original eight inputs remain;
required ninth IntentId freezes one typed action for replay. The authenticated
Invoker must resolve to the Personal recipient; there is no leader.

This consumer uses the existing #81 child contract1/rules1 PAIR eligibility and
GROUP initial-member purpose/capacity checks, before decision and publication.
Pending exact-ETag winner, unique source group/episodes, shared WriteOwner,
complete committed readbacks and no-rollback bounded recovery remain parent
operation guards. WriteOwner is the plain operationKey + ':' + attemptUUID;
receipt AttemptToken is native guid(), sealed UUIDs are capped at three.
All ten finalized TandemOperationReceipts fields are consumed via exact list title;
no group/receipt additions requested. #81 owns actual setup/audit and this
consumer's drift-ledger handoff is in ISSUE_11_RESPOND_REQUEST.md.

Legacy and parent-only unmanaged Solution candidates are generated; shared child/
rules/schema source is unchanged. Neither import path nor native Power Apps
binding, trusted caller, intended permissions, business parity or cross-flow
acceptance is certified. These remain NOT RUN; ordinary-account access remains
owner-deferred. No working imported flow/app, notification channel, permissions
or historical proof changed. Owner authorized parallel flow builds and commit
only, with no push/issue edit.

## Issue 11 refinement and Send contract alignment — 11.2.0

[#11 TandemRespondRequest](https://github.com/maoy1/tandem-language-culture-app/issues/11)
candidate11.2.0 replaces the unimported11.1.0 candidate for integration:
**296 action definitions/depth7**, down122 from418, with204 actions of headroom.
One sequential two-party Foreach replaces duplicate membership fragments;
continuation plus an exact verified-iteration count prevents second-party I/O
after a failed first iteration. Common effect/decision/receipt stages and typed
Boolean assertion guards remove duplication. All #47 authority/CAS/unique/
readback/commit/recovery predicates remain. No runtime helper or extra flow.

Current request reads now enforce the actual #10 producer contract: typed
Personal parties/null target, immutable SendOperationKey and exact
open:person:min:max live reservation. Settled history uses history:request:id,
correcting11.1's shorter key to match #10 replay. Receipt intent representation2
freezes SendOperationKey; app I/O, shared contract1/rules1 and token formats
are unchanged. No new schema is requested; shared child/source is untouched.

Build28a0e136-7f75-4d65-b217-258ef163b112, new packages/review/validation and
the detailed #81 drift handoff are in ISSUE_11_RESPOND_REQUEST.md. Local affected
graph/envelope/coordination tests: **141 PASS** (92 response cases). Earlier
11.1/full-suite420 evidence is retained separately; it is not a new full-suite
run. Native import/authority/business/cross-flow acceptance remain NOT RUN.
No issue, working flow, app, permission or tenant setting was changed.


## #61 shared PROFILE consumer candidate — 2026-11-14

[#61](https://github.com/maoy1/tandem-language-culture-app/issues/61), under
[#45](https://github.com/maoy1/tandem-language-culture-app/issues/45): separate
owner-authorized parallel-batch branch from origin/main. New local generator
`participant_submission_shared.py` delegates profile normalization/content checks
to unchanged native child e9aa88eb-a666-4df1-b088-176be7bcd00d, contract1/rules1
PROFILE. Parent keeps trusted current reads, complete catalogue reads, changed
Status-only ETag write/readback and no-op follow-up. No per-event schema audit,
participation/openness/identity/selection, permission, group or membership writes.
PROFILE receives null availability without reading/resetting those business fields.

Actual legacy export SHA256 a81c0c87b262ffb5a13fe079dec4a13bcc345e763c1e57c10dd02bed57dae90c
uses named Embedded SharePoint owner connection b7e419509f0f4da89895a5ebd1f3a216
and `$authentication`. The readable draft preserves its trigger and references.
Separate automated adapter resolves the existing native component
cre46_sharepointonline_a22363a216 and emits `runtimeSource: embedded`; it never
uses the manual Invoker adapter or Raw trigger-token expression. Core marker
`AUTOMATED_SOURCE_VERIFIED` means **legacy automated source inspected only**.
Native automatic Solution import/owner-resolution/execution remains **NOT RUN**;
do not infer it from the manual probe or legacy evidence. Deployment is gated.

Build issue-61-shared-consumer-v1: 29 definitions/depth3; unchanged child84/depth7.
Readable draft, separate Solution source and hash/binding review are under
artifacts/participant_submission. No legacy ZIP until valid final Solution
assembly; no live flow/app replacement, readiness upgrade or issue edit.
Existing v2 build88637754-4c91-4833-9dcf-5116d8bfb77e, item38 evidence and Live26
remain historical/current runtime evidence, not proof for this new consumer.

#81 drift assessment: no shared schema/contract/rules/null/availability/catalogue
semantics change and no child/other consumer package edits. Existing PROFILE
content semantics, including active Any as content and culture-only/null-zone,
are reused; no matching occurs. Local #61 contract ledger records scope and
native NOT RUN gates; shared QUICK3/FULL44 PASS remains bounded to its old build.
Exact adapter/test handover is appended to docs/FLOW_61_PARTICIPANT_SUBMISSION.md.


## #61 shared consumer native no-op PASS — 2026-11-14

Owner report item38: parent08584069192652841427464544862CU18, consumerissue-61-shared-consumer-v1; shared PROFILE returns OK on batchbd66271f-090e-4f5c-a890-8cb5b61173cc, child08584069192622793814733430516CU11. valid=true, StatusActive, statusChanged=false, NO_CHANGE. Evidence artifacts/participant_submission/results/shared-v1-no-change.owner-report.json. Record bounded automatic event/read/child/no-op PASS; Status-write/readback/follow-up, broader acceptance and old-validator-off confirmation are not inferred. No source/package/semantic change; no local tests rerun for recording native evidence.

Report sharedChildId still contains the legacy template annotation e9aa88eb...; exact1.0.0.1 packaged Call_profile_child target is f1f91974-4124-557e-b7fe-d51e9972681d, and actual shared build/run are captured above. Track the annotation rebind in #81 for the next packaging revision; this does not justify reimporting during the functional test. Next bounded test: with oldv2off and valid selections intact, set only Participants item38 validation Status to Needs review. Expect STATUS_UPDATED/Active/statusChanged=true then autonomous NO_CHANGE/statusChanged=false without another user edit. Return both reports; identity/selections/participation/openness must remain preserved.

## #7 shared-validator consumer — 2026-11-14

[#7 TandemDiscovery](https://github.com/maoy1/tandem-language-culture-app/issues/7)
now has a separate local parent component using actual NORMALIZE/PAIR/GROUP
Workflow calls to #81 contract1/rules1. Build
`0ab956c1-cbb6-4da7-9e23-dbd8b4cd9ebe`, 164 actions/depth6, zero writes.
Authenticated own-profile/current commitment gates, approved public projection,
optional zone/culture-only/candidates-only behavior and bounded reads remain.
Per-click metadata audit is replaced by typed current commit-row evidence;
full schema verification remains deployment/change maintenance. Shared semantics,
versions and other packages unchanged: #81 no-impact ledger, exact IO/connection,
assembly prerequisites and NOT RUN handover are in
[ISSUE_7_SHARED_CONSUMER.md](ISSUE_7_SHARED_CONSUMER.md).
Final batch Solution assembly/import/native consumer proof remains pending;
legacy evidence/closed tickets are preserved, ordinary access is not verified.
The owner explicitly authorized the parallel 12-flow batch for this implementation.


## #63 shared consumer v4 — 2026-11-14

[#63 TandemCancelRequest](https://github.com/maoy1/tandem-language-culture-app/issues/63) implements the authorized parallel batch consumer refactor from cancel v3/PR #79 plus origin/main #81. Build d70520a1-e760-45ee-ab57-f211a490cbb2, ZIP SHA256 e5818c0ac14d27ceeb7f87297993fc191ef1e5102c804c3377ebdcf7b4f4fe68; 71 actions/depth5 (was138/5), one CAS/retries none. No per-click schema audit or unused NORMALIZE/compatibility call. #81 schema verification is explicit deployment/maintenance; caller/sender authority, typed coherent rows, exact Pending ETag CAS, deterministic winner/history, same cancel replay and unknown outcome readback remain. No shared child/common changes or shared rule/schema/IO impact; draft #81 ledger and exact owner/synthetic handover in docs/ISSUE_63_SHARED_CONSUMER.md. Parent assembles Solution; legacy ZIP is only owner-preview packaging. Native consumer/Power Apps/write tests NOT RUN; ordinary access deferred/not verified. v3 and #81 native history retained; no issue closure/readiness/push/deployment or GitHub edits.

## #62 v7 shared NORMALIZE reader — local build, native parent NOT RUN

[#62 TandemMyRequests](https://github.com/maoy1/tandem-language-culture-app/issues/62), PR [#80](https://github.com/maoy1/tandem-language-culture-app/pull/80), under overview [#45](https://github.com/maoy1/tandem-language-culture-app/issues/45). Owner explicitly authorizes parallel 12-flow batch for this work; no lifecycle/issue edits made. Merged origin/main #81 baseline, retaining #62 v6 owner empty-history evidence and main's subsequent child/Invoker proof history.

Readable parent `artifacts/my_requests/TandemMyRequests-v7.definition.json`, build `72df3b79-e724-412f-bfb9-e48a1a6011c1`, SHA256 `f18ee0b70837ae3c809d902e83912ca364d5d98d5a6e5999928051ad30d0526a`: **128 actions / depth 4**, six SharePoint GET definitions, zero writes (limits 500/8). New parent is NOT imported/tested. No legacy ZIP is delivered for v7: the external Workflow dependency requires enclosing Solution packaging by parent integration. Existing v6 ZIP/evidence remain historical; do not deploy it as this migration.

Parent keeps authenticated Invoker currentuser -> unique own participant -> exact positive number reference binding; bounded complete reads, typed integer reference canonicalization, request intent/history/commit keys, operational membership episodes, provisional/Left/Ended restrictions and audience-before-public-projection remain #62-owned. Per-click metadata/list-field audit removed; explicit setup/deployment/maintenance audit belongs to [#81](https://github.com/maoy1/tandem-language-culture-app/issues/81). This change makes no schema, permission, connection, app or tenant configuration changes.

NORMALIZE contract/rules 1/1 targets child `e9aa88eb-a666-4df1-b088-176be7bcd00d` and native-passed build `c79b7b64-b3ce-4de3-aa74-0ed62bca1524`. Reader supplies only availability fields and profile ID correlation tokens `participant:<Id>` with omitted role/timezone fields and explicit empty catalogues/Any null. These tokens are not authenticated account identities; they never authorize an actor or reach the app. No compatibility or identity-normalization claim follows from this narrow projection. Child report/version/build/zero I/O/non-authority, typed results and exact unique ID coverage are checked; any child failure/malformed/incomplete response clears all rows with SHARED_VALIDATION_FAILED. Current availability hints use normalized output; action writers must recheck authority/compatibility/freshness/commit.

#81 drift/no-impact assessment: no shared child/common source, shared contract, catalogue semantics or mapping/baseline changes; only #62 consumer packaging/projection changes. Shared implementation SHA256 `4d16f3291116cf5c297c28d22403d8a56edf6e9a3d9c220f6ce8034d7564428f`. Existing QUICK3/FULL44 native PASS remains version-bound; #62 new native parent parity is NOT RUN. No #81 issue/ledger edit under explicit no-issue-edit scope; this append is the consumer ledger handoff for parent integration. Introduction schema is still unapplied/unverified: default artifact does not select/expose it. After #17 verifies actual optional plain-text Introduction mapping/settings, explicit `--introduction-verified` rebuild supports null/absent/empty/2000 characters, rejects 2001, exposes only group-request text after the existing request audience filter. This grants no broader profile, discovery or raw-list visibility. Native Introduction acceptance remains BLOCKED on setup.

#62 v7 local verification: **463 full-suite PASS / 106 reader cases**, 80.82s; 128 actions/depth4, six GET definitions/one real-child call/zero writes. Delivered graph, artifact/generator/shared-source hashes and shared-source/contract equality to origin/main checked. Native new-parent tests NOT RUN; versioned evidence in `artifacts/my_requests/v7.validation.json`.


## #62 v7 follow-up — target Introduction option, responder authority and exact batch pin

[#62 TandemMyRequests](https://github.com/maoy1/tandem-language-culture-app/issues/62), [PR80](https://github.com/maoy1/tandem-language-culture-app/pull/80). Follow-up stays in codex/issue-62-package after independent #64 commit1070eb3; no #64 source/branch edits or shared/common edits. Parent integration remains responsible for the foundation merge and enclosing Solution assembly.

`build_actions`, `build_parent` and `build_package` now accept keyword `include_introduction=True` for PROSPECTIVE target compilation, without a tenant verification claim. Legacy `introduction_verified=True` remains an equivalent compatibility alias; review always records introductionVerified=false / actual setup NOT_APPLIED_NOT_VERIFIED. Default artifact omits the field; separate `TandemMyRequests-v7-introduction-target.definition.json` includes optional plain-text Introduction with 2000-character checks and unchanged audience-before-projection. Building target before setup is allowed; tenant use is blocked until actual field/settings/readback succeed. Owner planning context: root #81 setup114 actions/depth6, audits all8roles via shared child/new prospective59-field baseline. This is not tenant PASS evidence and adds no schema/receipt dependency to these NORMALIZE-only reader calls.

Runtime pin is configurable via keyword `expected_shared_build_id` (CLI --expected-shared-build-id), defaulting to canonical SHARED packageBuildId. Parent passes ONLY the explicit canonical batch-manifest engine build. The emitted report check stays EXACT, with existing child immutable ID, contract/rules1/1, success, non-authority, zero-I/O and complete-output checks. Native connection seed proof build is checked/recorded separately; a newer expected engine pin does not certify engine semantics or native parity. Default/target examples here retain expected `c79b7b64-b3ce-4de3-aa74-0ed62bca1524`; parent must rebind/regenerate against actual new batch engine, never run an old c79 pin on it. Exact shared implementation hash drift gate remains unchanged: reported integration old4d16/new7365 mismatch requires foundation merge and artifact regeneration by parent, not ignored/loosened checks.

Current operational Active group-member responder hints no longer require that member's personal Active participation/openness/validation availability. Paused/Inactive/null/non-open members keep group response authority under the existing committed-episode guards. New Group requester availability remains separate; current group capacity/open/busy hints remain. Accepting writers/shared rules still recheck requester eligibility, focus-sharer availability, compatibility/freshness and commit/CAS; this read hint is not approval. Personal-recipient new-connection availability behavior is retained.

Default v7 build `2c9d2814-dcfb-4951-8abe-955b9067863b`, SHA256 `9edaa4b8f3561d36c2f5e83a995e6d4db19dea58fcaab5fc04908dd9c18a99e5`; Introduction target build `24da4c0a-fd53-4143-8bfc-3d94b15e5913`, SHA256 `96c0f5c25e81c140f2b0e0c0965bcbf5880a5c9445bb1935e7b78dc75f5086a8`. Both128 actions/depth4/six GETs/one Workflow/zero writes; both native NOT_IMPORTED_NOT_TESTED and actual schema NOT verified. No deployed flow, app, permission, source schema, #81 engine/package/contract or ticket state changed; no issue edits/push. Shared drift/no-impact ledger: consumer option/hints only; parent source-hash/build-pin reconciliation remains explicit. Prior v7 artifacts/results retained in b9d6516 history, prior v6 owner PASS unchanged.

#62 follow-up final local evidence: **485 full-suite PASS / 128 reader cases**, 52.50s. Default and Introduction-target128/depth4, six GETs/one actual emitted child/zero writes; strict hash and exact configurable build checks PASS on this branch's unchanged main-based shared source. New foundation old4d16/new7365 drift remains a parent-owned merge/regeneration prerequisite, not waived. Validation records prior v7 history separately; native/schema/privacy still NOT RUN.

## #10 shared PAIR consumer implementation — 2026-11-14

[#10 TandemSendRequest](https://github.com/maoy1/tandem-language-culture-app/issues/10), [PR #78](https://github.com/maoy1/tandem-language-culture-app/pull/78): owner explicitly authorizes the parallel 12-flow batch; this branch owns only Send. Integrated merged #81 from origin/main, retaining both prior evidence histories and exact conflicting untracked exports in temp. V4 build `67071ada-681d-4522-ad5f-5d9c97235a7d` delegates fresh normalization/compatibility to native Workflow child `e9aa88eb-a666-4df1-b088-176be7bcd00d`, contract1/rules1 PAIR, pinned existing shared build c79b7b64-b3ce-4de3-aa74-0ed62bca1524. Authenticated own-profile, immutable replay before availability, fresh pair/catalogue reads, narrow request-only metadata checks, current live-key/unsettled checks and one POST/unique/readback-unknown protocol remain. No per-click full schema audit. Null availability stays ineligible; deterministic object-schema failure replaces unsafe div gates in this parent.

Parent 113 action definitions/depth4; shared child unchanged84/depth7; both within500/8. Readable native-envelope parent, review-only legacy ZIP, mappings, validation and complete future native test instructions are in artifacts/send_request/HANDOVER.shared-v4.md and shared-v4.validation.json. Final deployment requires parent-batch Solution assembly; legacy Workflow linkage is not natively proven. #10 native v4 caller/write/replay/race/privacy remains NOT RUN; historical v3/#81 evidence remains scoped to its versions.

#81 drift no-impact assessment: no shared schema, rules, normalization semantics, version/build or other consumer files changed. This is the #10 consumer migration only; build/hashes/regressions are retained in Send evidence. Parent owns #81/#10 ledger/issue updates, Solution packaging and integration. No push/issue modification from this branch; no schema/settings/permission changes, no Ready/Done claim. See the handover for exact fixture/account/actions/expected results/failure interpretation/cleanup/evidence.

Final local verification for #10 v4: **413 tests passed**, including **56 send cases**; exact delivered native parent + delivered shared-child graph exercised locally. ZIP/definition/hash checks PASS; parent113/depth4 and child84/depth7 PASS; seven shared files unchanged from merged origin/main and request mapping unchanged from prior #10 baseline. Native v4 integration remains NOT RUN.


#10 final batch refinement: removed all request-field metadata queries and Schema_* gates from ordinary Send. One-time #81 setup/audit owns schema; historical #10 metadata preflight remains reproducible with an explicit generation-only flag. Current identity, typed intent, compatibility, native unique key arbitration and exact readback remain. 57 focused tests pass; native new parent/replay/race tests remain NOT RUN.

## #81 coordinated core batch foundation — 2026-11-14

Owner explicitly authorized parallel implementation of one shared validator and eleven singly owned business flows, one coordinated Solution import, separate ticket branches/PRs and inline per-flow checklists. The old single-active-ticket sequence is superseded for this authorized batch. Core flow inventory and stable fresh component IDs are owned by config/core_batch_contract.json / scripts/power_automate/core_solution.py. No silent working-flow replacement; all generated components import disabled and the old/new event validators must never both be enabled during cutover. Full app screen implementation and ordinary-user access tests remain separate, not implied by backend import.

Production target schema is config/batch_schema_contract.json. Optional Introduction is a plain-text Note, 2,000 characters enforced by app/flow. New TandemOperationReceipts has unique required OperationKey, required plain-text IntentJson, optional ResultJson/SealedAttempts, completion/uncertain/retry/domain-effect flags, AttemptToken and Stage. No extra lock service, timer, lease takeover or background repair runtime. Setup is one bounded owner maintenance flow, dry by default; it checks ManageLists before additive writes, refuses an unrelated same-title receipt list, does not convert mismatches or add missing required receipt fields to a nonempty table, then rereads metadata. No business row writes, deletes or permission changes. Native setup/production mapping remains NOT RUN; returned receipt GUID must be retained in tenant evidence.

The shared schema evaluator now accepts a baseline-defined role count and plain-text Note checks, allowing the prospective eight-role/59-field batch baseline (seven native-passed roles plus receipts and request Introduction). Existing production list identities remain GUID-pinned; the new unique receipt list title is used until native GUID evidence exists. The native-passed old baseline and v2 ZIP remain unchanged historical evidence. Shared rule/availability/normalization semantics are unchanged. The new generator and its prospective schema require a fresh batch build/hash and native regression; prior QUICK3/FULL44 are not relabelled as new runtime PASS. Every consuming ticket/package carries this impact/remaining test gate.

#49 owner selected in-app plus email, sender Tandemteam@elsevier.com, and approved new personal requests to recipient, group-join requests to all active target-group members, accepted/declined to sender, cancellations to recipient or active target-group members. New Outlook connection was created, but the native shared-mailbox test failed REST capability; exact mailbox/connection compatibility remains unverified. No email connector, new licence, mailbox grant or delivery workaround is added to this twelve-flow batch. #21 email remains blocked; in-app request/group views remain within core work.


### #81 Discovery invocation bound

Added backward-compatible PAIRS mode: one actor plus the supplied profile set returns eligible pair projections using the existing PAIR expression source. It avoids a separate native child invocation per candidate (up to 500 profiles). No matching/availability/identity rule changed; result remains internal and never grants authority. Discovery consumes this additive mode; other consumers retain their existing modes. New batch engine/native evidence remains NOT RUN; old v2 evidence is not reused. Three bulk/single parity, missing actor/null availability and structure-limit tests pass. Shared foundation before this addition passed 378 full local tests.


#7 batch integration update: candidate matching now calls shared PAIRS once for the entire bounded profile set, preserving the existing PAIR rules; no child call inside Each_person. NORMALIZE and GROUP remain shared. This component requires the new #81 batch engine with PAIRS and is not executable against the old native-passed v2 child alone. Final Solution assembly rewires to fresh batch child ID; historical native evidence retained, new native performance/consumer tests NOT RUN. No matching semantics changed.

### #81 assembly and test handover refinement

The import remains one coordinated Solution: twelve production flows plus two disposable owner maintenance helpers (schema setup/audit and 45-case connector-free shared smoke). Existing v2 child and working business IDs are not overwritten. Assembly rebinds the inspected shared child ID and exact old build literal to the new batch child/build, preserving all consumer build identities and checks. Native document envelopes are copied from the inspected source for every component; automated owner binding remains separately marked legacy-inspected/Solution-native-NOT RUN. A local SharePoint transport fixture models only current reads, ETags and uniqueness for interoperability of actual generated graphs; no domain-rule implementation or hosted runtime is added. All final native tests remain NOT RUN.


## #81 final coordinated batch artifact — 2026-11-14

TandemCoreBatch version **1.0.0.0**, shared build **4db7f9fa-6d67-48b0-a7a6-33638d7ff4a1**, ZIP SHA256 **bd854ae74a5e0291d985aa5fadc3fb3088c8135e7c5e337148acb02e89d4c959**. Delivery: `artifacts/core_batch/TandemCoreBatch-v1.zip`; readable exact packaged definitions and IO/connection schema are alongside it. Twelve production flows plus two disposable owner helpers; all import disabled. The native-derived bundle preserves interactive Invoker and the separately inspected legacy automatic Embedded binding; new automatic Solution execution remains NOT RUN.

Measured production definitions/depth: shared93/7; Discovery167/6; participant validation29/3; Send99/4; MyRequests128/4; Cancel71/5; personal Respond296/7; group Send147/5; group Respond393/5; MyGroups185/5; Update250/5; Leave231/4. Helpers Setup115/6 and Smoke8/2. Every flow is below500 actions/depth8; maximum393/7. Exact fresh workflow IDs and hashes are in the review JSON. Shared contract/rules remain1; prospective schema baseline2 covers8roles/59fields. All eleven consumer tickets are impacted by this linked deployment and retain their native acceptance checklists.

Local combined regressions and actual-packaged-graph tests are recorded in TEST_RUNS and `artifacts/core_batch/validation.json`; native import/setup/audit/consumer/app/access results remain NOT RUN. Existing native QUICK3/FULL44/SharePoint owner-probe results remain tied to their old c79 build. No tenant state, working app/flow, permission or mailbox was changed by building this artifact.


## #81 native schema-input failure and compact collector repair — 2026-11-14

Owner #45 Apply run08584069362059040197682124425CU28 on batch4db7f9fa collected metadata but returned schemaVerified=false/result={}, with no local setup differences or business row/deletion/permission writes. Receipt list ID864dfe53-b67c-4504-9d48-ad4356b813d8/title was observed, not a full schema PASS. Child08584069361400134595726594162CU01 was invoked with the correct build but failed Request_text as INVALID_INPUT before Envelope/schema evaluation. Raw metadata-size overflow reproduces this signature locally; exact native Request_text detail remains requested. Preserve the failed native evidence in artifacts/core_batch/results/v1-schema-apply.owner-report.json.

Solution1.0.0.1 repairs the setup collector: source-read completeness and paging remain checked, but only the59 baseline contract fields and nine evaluator properties are forwarded. Hidden/system fields unrelated to the contract and per-field transport __metadata no longer consume the250000-character child bound. Exact SchemaXml, missing required fields and duplicate/mismatched contract fields remain intact; no truncation, relaxed schema/size gate, list settings or rule/normalization changes. Setup report exposes requestCharacters and child validationCode/diagnostics/run reference. Missing/duplicate/wrong-type, oversized required XML and no-write cases are regression-tested with native length enforcement. All consumer rule/authority/business graphs remain unchanged; new bundle hashes/build linkage and native retest must be recorded. Prior schema apply is not rolled back or repeated blindly; owner next uses read-only ApplyChanges=No after the corrected import.


### #81 corrected collector package1.0.0.1

Artifact `artifacts/core_batch/v1.0.0.1/TandemCoreBatch-v1.zip`; shared deployment build **bd66271f-090e-4f5c-a890-8cb5b61173cc**; SHA256 **2708aef6bdff431c6681e17aeaca44d46073b9ef83ed2bd81af2ea3124661e92**. Same Solution identity and component IDs, update to1.0.0.1; all components remain disabled in the package. Setup now117definitions/depth6; overallmax393/7 against500/8. All12production documents compare exactly to v1 after explicit shared-build rebinding; no operation/normalization/compatibility changes. New45-case packaged smoke and9actual-packaged business E2E cases PASS locally. Focused schema/packaging/shared regressions recorded in the new validation.json. Native collector retest NOT RUN; raw native Request_text detail still requested.

Owner next: import this as UPDATE of TandemCoreBatch, preserve existing SharePoint mappings, keep business/event flows disabled; enable shared child + Setup and run **ApplyChanges=No**. Existing receipt list is retained; no repeated schema write is needed to diagnose. Expect collectionComplete=true, validationCode=OK, schemaVerified=true and full schemaResult; report also gives requestCharacters/validationDiagnostics/validationRunReference. If false, return that report/error; do not adjust list settings or rerun Apply blindly. Once read-only audit succeeds, the prior repeat-apply/remaining native checklist still applies. All affected consumer tickets reference this new version/build/hash; historical v1failure and old native proofs remain unchanged.


### #81 corrected read-only native audit owner-confirmed — 2026-11-14

For #45's corrected1.0.0.1 retest, owner confirms validationCode=OK, collectionComplete=true and schemaVerified=true. Record **OWNER-CONFIRMED READ-ONLY SCHEMA PASS**, scoped to that report summary. Full report/current run reference were not pasted, so exact package-build/run correlation is not independently captured; the next repeat report can supply it. Evidence: artifacts/core_batch/v1.0.0.1/results/schema-audit.owner-confirmation.json. No code/schema/rule/package-byte changes; ZIP/build/hash remain unchanged. Original native input failure remains historical evidence, with exact old Request_text error not supplied.

Next bounded test: run TandemBatchSchemaSetup ApplyChanges=Yes once and confirm schemaVerified=true/validationCode=OK and every Create action Skipped. Return Setup_report plus skipped-action confirmation to capture runReference/build. Do not close #81/#45 or mark the combined repeat-apply acceptance passed yet. Native45-case smoke, individual business/automatic/app acceptance and ordinary-user access are not implied by this schema PASS; retain pending/deferred states.


### #81 native repeat-apply schema report PASS — 2026-11-14

Owner supplied the full corrected1.0.0.1 report: buildbd66271f-090e-4f5c-a890-8cb5b61173cc; ApplyChanges=true; parent08584069211508254579686294345CU13; child08584069211275890958307283979CU25. validationCode=OK, schemaVerified=true, collectionComplete=true, schemaMatches=true/allSchema=true, all8roles checked, no differences. Input41372characters; every diagnostic stage Succeeded. Business row writes/deletes/permissionChanges0; receipt GUID864dfe53-b67c-4504-9d48-ad4356b813d8 remains observed. Exact evidence: artifacts/core_batch/v1.0.0.1/results/schema-repeat-apply.owner-report.json.

Record native full-schema PASS on repeat apply, now with exact build/parent/child correlation. The report does not contain individual Create-action statuses; **all Create actions Skipped remains unconfirmed**, not failed and not a reason to rerun. rowWrites=0 concerns business rows, not schema-creation action status. Ask only for those statuses in this same run; do not check off the combined no-schema-write repeat criterion yet. Native45-case smoke/consumer/automatic/app/access gates remain separate. ZIP bytes/build/hash/rules/schema contract unchanged; no code change or new tests required for recording native evidence.


### #81 repeat setup safe-repeat criterion completed — 2026-11-14

Owner confirms every Create action was gray/Skipped in the same native Apply run08584069211508254579686294345CU13 (buildbd66271f-090e-4f5c-a890-8cb5b61173cc). Combined with the exact8-role schema PASS report, record **repeat setup PASS**; no additional setup rerun is needed. Status evidence: artifacts/core_batch/v1.0.0.1/results/schema-repeat-apply.owner-confirmation.json. This supersedes the pending Create-status confirmation above. No code/package/schema/rule change; ZIP/hash unchanged. Next pending native gate is TandemCoreValidationSmoke (no inputs), expecting suiteBATCH,45completed/45tests,allPassed=true,failedCases=[]. Keep business/event flows disabled until that gate passes; #81/#45 remain open with consumer/automatic/app/access acceptance separate.


## #45 delegated technical flow-test handover — 2026-11-14

Owner will hand flow testing to technical colleagues, arrange necessary test access if needed, and manage activation/isolation outside the cases. No further functional case must be personally run by the owner now: import/schema/safe-repeat and owner-checked smoke are complete, and #61 event/read/shared/no-op has native PASS. Status correction/write/readback/follow-up remains required acceptance assigned to colleagues, not waived or marked passed.

Current procedures live inline in #45/#81 and the11flow issues:75individual flow cases with role/fixture, numbered actions, expected response/persistence and evidence/cleanup. Repeated old-flow on/off/import/connection instructions are removed from tester steps. One-time access/entry/fixture preparation is centralized under #45 and may be delegated to a test coordinator. Colleague access is unknown; owner may arrange limited technical test access, without assuming new licensing or proving ordinary-participant privacy. First colleague test is read-only MyRequests with their actual own ParticipantId.

PowerAppsV2 invocation must be usable before its case: use the portal input form if available, otherwise a coordinator-prepared Power Apps test button. No invocation route is declared tenant-verified for colleagues. Missing input entry/account/fixture/harness is BLOCKED, not PASS or a reason to invent a screen/trigger change. Importing core does not deliver #16/#67/#68 UI; a minimal technical button is sufficient. Fault/race/paging cases go to a prepared isolated operator harness; no shared live schema/catalogue/permission faults are assigned. Ordinary-participant privacy remains deferred, email remains blocked. Original acceptance/test history is archived as dated JSON, not active instructions. Static checks confirm all75case IDs unique, every case has a checkbox/steps/expectation, actual input keys match packaged triggers, bodies fit GitHub limits, and legacy toggle instructions are absent. No runtime/code/schema/matching/IO/package change; current1.0.0.1 build/hash and existing native proof remain unchanged. Shared#81 no-impact: procedure and assignment change only, consumer acceptance still scoped to receiving tickets.


## #16 Discovery app candidate — 2026-11-14

Owner supplied the current Tandem Participant Registration `.msapp`. It contains MainScreen1, an older people-only scrDiscovery and scrRequests. Discovery still called older flow IDs and the personal send call lacked the current intent argument. The focused #16 candidate adds People/Groups views, plain-text approved profile/member details and matching catalogue labels, empty/error/loading states, refresh/back navigation, personal send and optional group introduction (2,000 characters). It consumes existing core #7/#10/#17 contracts; matching remains server-owned. An uncertain send retains its actor/target/introduction/UUID for an explicit same-intent retry; starting another intent is explicit. A confirmed request is described as recorded, with current status delegated to My requests.

Delivery: `artifacts/app_discovery/v1/TandemParticipantRegistration-Discovery-v1.msapp`, readable source overlays and binding manifest. Microsoft PAC 2.15.1 SourceCode unpack/pack succeeds, including an initial unchanged round-trip. This is a source-overlay candidate requiring Studio edit-time validation; cached Controls JSON/AppCheckerResult are original, not evidence of fresh compilation. Thirty-six package/preservation/contract checks pass. Registration source changes only at the Discovery entry; Requests/App source, app identity, non-flow properties and the participant SharePoint binding are preserved. Three Discovery-related references target core Solution 1.0.0.1; actual native resolution/connection/compilation/import/publication/UI acceptance remain NOT RUN. Do not overwrite/publish the working app before isolated Studio validation. No new tenant connection type, licence, hosted service or participant runtime is introduced. Local temporary Microsoft tooling is build-only.

Shared #81 drift review: no impact on schema, rules, normalization, availability, capacity, commit, input/output contracts or backend packages. Core build bd66271f-090e-4f5c-a890-8cb5b61173cc and its ZIP hash remain unchanged. This app consumes the accepted interfaces and does not add eligibility rules. Ordinary-participant access stays deferred; #67 Requests/#68 My groups and #21 blocked email remain separate.


## #16 imported-app Discovery load PASS — 2026-11-14

Owner confirms “ok discovery from the imported app works” after using the stable Discovery-v1 handoff under C:\projects\small_projects\tandem-language-culture-app\artifacts\app_discovery\v1. App SHA256 ee00b86d7810d2e6c1ccd52777b7a1ef9003e60aa8638fa270817503289ffdee unchanged. Record artifacts/app_discovery/v1/discovery-load.owner-confirmation.json. This proves imported-app opening and Discovery load, scoped to owner testing after core1.0.0.2 activation and matching45-case native smoke. It does not prove non-empty people/group fixtures, every approved display field, personal/group request actions or persistence, complete App checker, published app version or ordinary-user access. No runtime code/package/schema/rules/IO change; #81 drift no-impact. Remaining #16 checkboxes stay delegated and the ticket remains open. Future work builds the integrated UI; no full owner functional suite is requested.

Owner delivery correction: worktree artifact URLs disappear on branch switches. The immutable candidate and core1.0.0.2 ZIP now also live under the primary project artifacts folder. All future user-facing handoff copies use that stable location with hash verification; worktree paths are for development, not the sole download location.


## #67 Requests UI implementation — 2026-11-15

Owner authorized parallel #67/#68 implementation and one integrated app handoff. Requests module adds Sent, Received, group incoming and History views against #62, plain-text introductions, server-projected allowed actions, personal Accept configuration and #11/#65/#63 action calls. Focus choices reuse existing Participants lookup choices; numeric focus arrays are serialized invariantly and eligibility stays in flows. The personal response call has9 arguments (not10), group response3, cancel2, reader1. Frozen actor/request/decision/group options/intent survive uncertain replies; refresh preserves the retry and shows saved status. New action after uncertainty requires an explicit review/confirmation. Success is not inferred from HTTP200 or a button click. Full inbox names are not supplied by #62, so request references/direction/type identify cards without raw profile/account lookup.

Focused review artifact artifacts/app_requests/v1/TandemParticipantRegistration-Requests-v1.msapp, SHA256 88e609458ae7ee83f38fe8457780205e59a45e0254368b8b65967e1f5af2d9b5; not a separate owner import request. Microsoft PAC source pack PASS; 2156 actual-package preservation/interface checks PASS and5 source regression cases PASS. Registration Form1 is unchanged; Discovery controls remain unchanged except shared navigation/header space; disposable legacy Test Discovery1 button removed. Seven bindings are exact deployed core1.0.0.2 interfaces. Shared source overlays remain subject to Studio compilation/import; cached controls are not compilation proof. Native inbox/action/publish/ordinary-user tests NOT RUN. Desktop landscape1366x768 is the baseline; other sizes are not certified. No backend/schema/connector/licence/permission change, #81 drift no-impact. #68 extends this build to one final Integrated-v2 app in the stable primary project artifacts folder; each ticket retains its own PR and native acceptance.
