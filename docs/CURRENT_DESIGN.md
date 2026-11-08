# Current design source of truth

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
| Culture groups | 2–10 total members, including at least one relevant culture sharer | Owner approved; #12/#13 |
| Combined groups | Language/culture combined groups have 2–10 total; both focuses require a sharer and a different learner | Owner approved |
| Participant status | Separate Active/Paused/Inactive participation from validation | #46 then #6 |
| Culture-only participation | Supported; no mandatory language selection | #5/#7 |
| Notifications | Evaluate options first; channel/event matrix not yet agreed | #49 then #21 |
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
Language capacity is 2 or 3 total; culture capacity is 2–10 with a relevant culture
sharer, and combined language/culture capacity is 2–10 with a relevant culture
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
ordinary user's access. The owner deferred colleague access testing; #18/#39–#42
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

## Validation flow testing handover — #61

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

## Shared compatibility implementation — #9

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

## Shared bounded coordination preparation — #47

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


### #47 connector duplicate-error correction — v2

The owner supplied the first native report: 5/10 checks passed, allPassed=false. All five failed cases invoke the duplicate-response predicate. The Duplicate primary raw body confirms SharePoint error -2130575169 / Microsoft.SharePoint.SPDuplicateValuesFoundException wrapped by the existing SharePoint connector as HTTP 502. The original proof's 400/409-only classifier was too narrow. The five-case common cause is supported by local replay; a native v2 pass remains unverified.

The classifier now requires the exact native duplicate exception/code together with HTTP 400, 409 or 502. For the wrapped form, both exact entries must exist in innerError.errors. Generic 502, unrelated 400/409, incomplete error identifiers and other statuses fail. Existing schema/row/ETag/count/readback checks remain required. All five duplicate-dependent reports now include diagnostic codes/messages. No cookie or response headers are stored.

Supported package: artifacts/coordination/TandemCoordinationFixture-v2.zip, build b54d7cee-971d-4af3-924f-e81d5fefaec9, new tagged list Tandem47Fixture_b54d7cee971d4af3. Import as Create as new, display name TandemCoordinationFixture v2, existing SharePoint connection; Run fixture writes=Yes. Old fixture is retained; no deletion or production mutation. Expected Fixture report: 10 tests, allPassed=true, failedCases=[]. Return that report; expected rejected duplicate actions may still show red 502.

Validation: 179 local tests passed, including wrapped native duplicate simulation in both writer orders and generic/error-negative cases; 321 actions / depth 6 (limits 500/8). V2 NOT_IMPORTED_NOT_TESTED. #47 remains In progress / PR #75 draft pending native results. No genuine timeout/killed-run, production consumer or notification-delivery proof inferred.


### #47 native bounded proof passed — 2026-11-08

Matching v2 build `b54d7cee-971d-4af3-924f-e81d5fefaec9`, owner run `08584074402025984197329193901CU08`: testCount=10, allPassed=true, failedCases=[]. Permission gate passed; existing tagged fixture `Tandem47Fixture_b54d7cee971d4af3` / `abade32d-8b24-4b30-b2e0-668d10238acb` reused (fixtureCreated=false). Summary exactly as supplied: `artifacts/coordination/results/fixture-v2.pass.owner-summary.json`; successful per-case details were not supplied and are not reconstructed. The package gates allPassed on exactly 10 results and no failed cases.

History retained: original classifier build 5/10 pass; first v2 run `08584074408126043497852268406CU03` 9/10 pass (`artifacts/coordination/results/fixture-v2.first-run.owner-report.json`). Its Shrink RequestB returned the typed duplicate exception despite distinct supplied A/B keys; actual cause remains unconfirmed. A fresh run prefix passed without code/formula edits. This does not establish connector retry causation or generic unknown-write recovery.

179 local tests / 70 reference schedules previously passed; final artifact remains 321 actions / depth 6, no runtime changes after owner proof. #47 **Ready for review**, PR #75 ready; no owner rerun required. Earlier pending-run entries above are historical. Own contract review/merge remains; no production schema applied, all 70 schedules are not native-proven, genuine timeout/killed-run, production consumer/access and external notification delivery remain separate. #12 group/member schema is next after merge; #61 stays Ready for testing.


## #12 active schema inspection — 2026-11-08

PR #75 merged `be278a1cc7a72b862154ae8ffe201acdf998f019`; #47 closed/Done after accepted bounded contract/native proof. #12 is the sole active ticket. Existing #57 group/member snapshot is historical source evidence; current actual list IDs/field definitions/settings remain unverified.

Prepared `artifacts/group_schema/TandemGroupSchemaAudit.zip`, build `cb49aded-f121-410e-b7df-d9646be892dd`: **51 actions / depth 3**, below 500/8. Existing SharePoint connection; GET-only list inventory/identities, Group/Group Members fields/defaults/SchemaXml/column index/list validation and effective list permission masks. Known #66 participant/language/culture list identities rechecked. **No list item reads, writes, permission changes or working-flow/app modifications.** Actual unique-key constraints/lookup targets/defaults/schema compatibility are not approved from packaging or reference proof.

194 local tests pass, including 15 generated-inspector cases (normal collection, ambiguous/missing/unsafe targets, paging, missing arrays/identities/permissions, failed reads and package safeguards). Tenant import/run **NOT RUN**. collectionComplete means bounded metadata collected, not schema acceptance; schemaVerified remains false. No setup until actual report reviewed, any changes flagged and actual per-list capability verified. Existing rows preserved; exceptions route #48. Full operator handover/checkboxes inline in issue #12; draft PR is partial preparation, not whole-ticket Ready. #61 remains Ready for testing.


### #12 actual mapping and direct settings — 2026-11-08

Owner opted for direct list settings rather than another setup package. Initial audit `08584074383115048211345636667CU09` and manual-settings readback `08584074377818105096431306544CU07` match build `cb49aded-f121-410e-b7df-d9646be892dd`: collectionComplete=true/errors empty; Groups and Group Members each itemCount=0. Actual field/list IDs, types, choices, defaults, XML constraints and lookup targets recorded in `config/group_schema_mapping.json`; source reports in `artifacts/group_schema/results/`.

Confirmed group Title now required; WriteOwner optional nonunique Text/blank default; native integer/type-specific capacity formula/message saved. SharePoint removed optional column brackets; canonical formula comparison confirms the same expression. Existing focus links, SourceRequestId/MembershipKey unique+indexed, dates, membership Title optional, State Closed and SetupComplete No remain. Participant lookup displays ID; preserve its linkage and resolve approved display in consumers.

Group Members Group and Participant still report indexed=false. Indexed columns page requested; no index completion or full schema acceptance claimed. #12 remains In progress / PR #76 draft. No setup package generated, row writes, renames/deletion or runtime/privacy certification. 194 existing local tests previously passed; this is metadata/evidence only, not new executable changes.


### #12 schema mapping and five manual settings verified — 2026-11-08

Final audit build `cb49aded-f121-410e-b7df-d9646be892dd`, run `08584074372941101122136369836CU17`: collectionComplete=true, errors=[], both lists itemCount=0. Groups `4bf1b37f-edce-40c5-8fa0-36543a2d0cd6`; Group Members `db611ec3-7fa3-477a-878e-effbbb195cb8`. Group and Participant now each indexed=true; owner Indexed columns page lists separate Group / MembershipKey / Participant. Prior combined Group, Participant index was replaced with separate indexes.

All five direct-setting changes read back: group Title required; WriteOwner optional blank nonunique Text/255; native integer/type-specific capacity formula/message; membership Group and Participant indexes. Source/membership keys remain required unique/indexed, correct links/focus choices/types, JoinedAt required/LeftAt optional, membership Title unused optional, State default Closed and SetupComplete default No. Other mapped business field IDs/properties/XML semantics unchanged. Formula bracket normalization is equivalent. Actual mapping in `config/group_schema_mapping.json`; raw report `artifacts/group_schema/results/final-audit.owner-report.json`. Raw inspector schemaVerified=false remains intentionally fixed; local reviewed mapping/readback is now verified.

#12 Ready for review / PR #76 ready. No owner rerun or settings package needed; owner chose manual UI changes. 194 local tests previously passed; no executable change in final evidence recording. No row rejection/creation/migration, ordinary-user privacy or consuming-flow/history behavior claimed. No migration exceptions in these observed empty lists. Dynamic count/focus/identity/Ended/history guards remain respective Flow scope; #48 migration remains separate. Source/contract review and merge remain; next focused implementation is #7 Discovery after merge, #61 still Ready for testing. Earlier pending-index entries are historical.


## #7 Discovery owner-preview build — 2026-11-08

PR #76 merged `39ebc0cd48c428602a0434a12db0c99ac77a9de5`; #12 closed/Done. #7 is sole active ticket. Actual TandemDiscovery export inspected (source hash `7b4dc1e5df96769615088d897cf86030a2622a47dc7db56a414dbe75f41085a9`): Power Apps V2 number reference, SharePoint Invoker source with Raw authentication, Get item/Get items and candidatesjson/errormessage response. No ordinary-user access proof or owner-credential fallback inferred.

Built `artifacts/tandem_discovery/TandemDiscovery-v2.zip`, build `7c8589d0-fdea-4db8-9d44-46b7d8548acf`, **165 actions / depth 6** (limits 500/8). Preserves actual trigger/Invoker expression, resolves current SharePoint user and unique own profile before candidate reads, uses unchanged #9 normalization/pair/group source, approved typed person/member/group allowlist and fresh membership counts/sharer availability. Optional timezone, culture-only and deferred Any language policy preserved. No writes. Fixed reads are bounded; rendering <=50 people, total group focus/member work <=100 units and response <=250000 characters; any incomplete/over-bound read returns no partial success. Tenant synchronous latency/load not certified.

242 local tests pass, including 48 generated Discovery graph/packaging cases (own/tampered references, availability, blank zone/culture/Any, source/member commitment, group state/count/focus/history, structured-field rejection, read/page/count/work/response limits and Invoker preservation). Native import/run NOT RUN; mode OWNER_PREVIEW_PENDING_ACCESS_PROOF. #42 privacy/ordinary-user two-account proof deferred; do not publish a participant endpoint or change permissions. Candidate groups additionally require live Connection Requests.OperationComplete Boolean plus accepted/complete source/episodes; missing schema fails explicitly, no field creation in #7. Current empty group lists allow an owner people/empty-group smoke without claiming populated group proof. Exact contract and remaining gates in config/discovery_flow_contract.json and inline #7 handover. Existing raw export remains user-owned/untracked, no source replacement or production cutover.


### #7 owner smoke — Paused rejected, Active empty success (2026-11-08)

Build `7c8589d0-fdea-4db8-9d44-46b7d8548acf`. Owner run `08584074350262917105745395996CU25` returned PROFILE_UNAVAILABLE/success=false while own Participation status was Paused. Owner manually changed it to Active; fresh run `08584074348343616902680114159CU10` returned OK/success=true, peopleCount=0/groupCount=0, writes=0, ordinaryUserAccessVerified=false. Exact reports and scoped evidence saved under `artifacts/tandem_discovery/results/`. No flow/package change needed for this expected availability result.

This proves owner-context invocation/own-reference path, Paused rejection and Active empty-result completion, not populated compatibility/projection, another candidate's availability, native tampered-ID/two-account proof, imported Run-only selector, group commitment schema or worst-case native bounds/latency. No published app/cutover claimed. #7 remains In progress / PR #77 draft. 242 local tests previously passed; only evidence/config/docs changed.

Owner restated self-service access: avoid individual participant approvals/grants; use verified existing group-based app/flow access. The shown SharePoint connection consent is separate from run/data authorization. Invoker is preserved; no switch to an owner connection and no new permission changes. #42 owns the final protected-data/caller boundary; owner smoke does not resolve it. Remaining versioned tests stay unchecked in issue #7.


## #7 resumed implementation review — 2026-11-08

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
