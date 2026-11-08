# Accepted MVP field contract

Issue #46; planning parent #45. This is the target field/ownership and Discovery
exposure contract accepted through merged PR #59 and closed #46. The field tables specify target
technical names, types, requiredness and defaults; owner review/merge accepts
those definitions. Existing tenant mappings must be checked by implementation
owners without silently renaming existing columns. Product rules and display
choices are approved; this document does not certify deployed configuration.
#46 closes after document review/merge, not after runtime implementation/tests.

Acceptance scenarios and stable bug-report references are in
[TEST_CATALOGUE.md](TEST_CATALOGUE.md); execution evidence and pending checks
are in [TEST_RUNS.md](TEST_RUNS.md). These checks do not imply implementation.

## Approved group limits

- Language: 2 or 3 total participants (1-to-1 or 1-to-2).
- Culture: 2–10 total participants, including at least one relevant culture sharer.
- Combined language/culture: 2–10 total, with both stated focus relationships
  supported by a sharer and a different learner for each focus. Owner approved.
- Capacity is a total, not the number of extra people. Free slots are derived
  from capacity minus active memberships and never maintained by participants.
- A Language group's capacity cannot exceed 3; Culture/Combined cannot exceed 10.
  Creation and acceptance enforce the same limits under #12/#47.
- The group controls State: Open welcomes requests when space remains; Closed
  continues operating without new requests; Ended no longer operates. Participants
  see member count and available slots, decide whether to request joining, and
  the group accepts or declines. No participant size-preference field is needed.

## Participant field contract

Baseline fields exist in config/sharepoint_schema.json. A new display label on
an existing internal field does not imply renaming its internal identity.

| Internal field | Purpose and SharePoint type | Required/default | Source and maintenance | Own form | Discovery display | State |
|---|---|---|---|---|---|---|
| ParticipantAccount | Authoritative single Person account | Required, unique; authenticated account | System resolves; user cannot change identity | Read-only name | Display name only; no email/raw account object | Existing |
| TeachLanguages | Offered languages; multi Lookup to Language catalogue | Optional, empty | Participant selection | Editable | Approved display | Existing |
| LearnLanguages | Wanted languages; multi Lookup to Language catalogue | Optional, empty | Participant selection | Editable | Approved display | Existing |
| ShareCultures | Cultures participant can meaningfully share; multi Lookup to Culture catalogue | Optional, empty | Participant declaration/selection | Editable | Approved display | Schema mapping observed #66 / App #5 |
| LearnCultures | Cultures of interest; multi Lookup to Culture catalogue | Optional, empty | Participant selection; not proof of sharing expertise | Editable | Approved display | Schema mapping observed #66 / App #5 |
| TimeZone | Meeting context; single Lookup to Time zone catalogue | Optional, empty allowed | Participant selection | Editable | Approved display | Optional schema verified #66; app acceptance #5 |
| LearningFocus | Exchange context; multiple lines plain text | Optional | Participant | Editable | Approved display | Existing |
| Comments | Additional exchange information; multiple lines plain text | Optional | Participant | Editable; proposed notice removed | Approved display | Existing |
| ParticipationStatus | Active/Paused/Inactive; Choice | Required; Active for new self-registration | Participant; exceptional admin override | Editable | Not exposed as a raw field; used to filter | Schema setup/readback passed #66; final schema checks pending / App #6 |
| OpenToConnections | Willing to receive new requests; Yes/No | Required; approved Yes for new self-registration | Participant | Editable | Eligibility filter only; exclude raw field from Discovery | Schema setup/readback passed #66; final schema checks pending / App #6 |
| Status | Existing validation state Active/Needs review; Choice, proposed display label Validation status | System sets on create/edit; fail closed until validated | Validation automation only | Read-only validation feedback | Never expose raw field | Existing; retain internal name to avoid breaking flow references |
| MigrationConfirmation | Not required/Pending confirmation/Confirmed; Choice | System default Not required for new self-registration | Migration sets Pending; successful owner review/save sets Confirmed | Banner only when Pending | Never expose raw field | Planned #48 |
| Title | Hidden technical text | Not participant-required | System if needed | Hidden | Excluded | Existing |
| Created/Modified and authors | Audit/system fields | SharePoint-managed | SharePoint | Hidden | Excluded | Existing |

PreferredGroupSize and its choices are removed. A participant judges a group's
actual member count, free slots and Open/Closed state instead. Group capacity
remains enforced; it is not inferred from a participant's profile preference.

No participant-entered email identity field, native Location dependency, language
level field, private organiser note field or separate per-participant exchange-type
selector is proposed. A person can have language and culture selections together.

## Culture catalogue contract

| Field | Type/rule | Owner |
|---|---|---|
| Title | Required display label | Approved catalogue maintenance |
| CultureKey | Required unique indexed text key, not assumed to be an ISO country code | Approved catalogue maintenance |
| Active | Yes/No; default Yes | Approved catalogue maintenance |

Catalogue population/setup has owner-reported evidence in #5; remaining live
acceptance stays there. Do not infer culture sharing from nationality, identity
or historical free-text interests. Existing inactive values may be retained for
history but cannot be chosen for new selections. This contract does not create
or certify tenant lists.

## Approved Discovery display - 2026-11-08

Owner approved the full proposed participant-facing display, including the
previously optional fields. Approved does not mean deployed or permission-tested.

| Result | Approved display |
|---|---|
| Person | Display name; matching languages/cultures and match explanation; offered/wanted languages and cultures; optional time zone; learning focus; Comments |
| Group | Name; exchange type; language/culture focus; member count; capacity/free slots; join availability; description; other member names and their approved participant-facing profile details |

Email is excluded from Discovery display and responses. Never serialize raw
Person/account objects, identity claims, audit/validation/migration fields,
processing markers, operation keys or other admin/system-only data. Internal
record references may support actions but do not grant generic record access.
Group member profile details use the same person-field allowlist above; do not
expand every SharePoint column. Member identities display names only.
Blank optional fields are allowed; time zone is not a discovery eligibility gate.
The proposed Comments notice remains removed. Exact JSON keys are still part of
the affected flow implementation contracts (#7/#9/#16/#42), not a #46 closure
condition. Those tickets implement/test this approved display.

## State and validation contract

The owner approved Active and OpenToConnections = Yes for new registrations.
Edits preserve these choices. Culture-only, language-only, combined and share-only
participation and the at-least-one-interest/offer validation rule are approved.
Target technical names are in the tables. Migration-specific choices belong
to #48 and must be resolved before migrated profiles are exposed.

- A valid profile has a required account and at least
  one TeachLanguages/LearnLanguages/ShareCultures/LearnCultures selection.
- Confirmed form behavior: when all four offer/interest fields are empty, explain
  the requirement and block saving until corrected. The rule applies across the
  four fields, not as a requirement on any one language/culture field.
- Existing/imported invalid records are excluded from Discovery. Participants
  correct their own editable data and automation revalidates; Needs review is
  validation feedback, not a routine admin-approval queue. Migration identity/data
  exceptions may still need necessary one-off admin help under #48.
- Time zone may be empty and must not block registration or discovery. If
  supplied, it must be a valid active catalogue value; no automatic derivation.
- Culture-only and share-only participation are valid; no language or learn field
  is individually required. Unsupported/inactive catalogue IDs fail validation.
- Continue using Status = Active to mean validation passed for compatibility;
  it must not be confused with ParticipationStatus = Active. A display label can
  clarify it without changing existing internal flow keys.
- On profile create/edit, recompute validation independently. Do not set
  ParticipationStatus or OpenToConnections to defaults on every edit.
  Successful validation never changes Paused/Inactive to Active or reopens a
  participant who chose not to receive new connections.
- Discovery requires validation Active, participation Active and OpenToConnections.
  Pending migration confirmation is proposed to suppress discovery until reviewed;
  this choice needs approval and does not block synthetic/core implementation.
- Waiting/In a group derive from authoritative active memberships. Pausing does
  not erase memberships; automatic rejoin/recovery is Later. Existing-group Open
  state is not changed by a member toggling their personal OpenToConnections.
  An unavailable person cannot be newly requested; group candidates depend on
  actual group Open state, space and relevant sharer availability.

## Groups field contract

One row represents one group, not one member. Its SharePoint item ID links the
memberships and requests to it. The tables define the target contract for
#12/#13; existing tenant lists need mapping/verification before live changes.

| Internal field | Purpose and SharePoint type | Required/default | Source and maintenance | Member-facing behavior | Discovery display | State |
|---|---|---|---|---|---|---|
| ID | Stable group reference; SharePoint system ID | Automatic | SharePoint | Read-only reference | Internal reference, not authorization | System |
| Title | Group name; single line text | Required; agreed at creation | Active members can edit through group form; admin exception | Editable name | Approved name display | Planned/mapping pending |
| ExchangeType | Language / Culture / Combined; Choice | Required at creation | Initial members choose; automation validates | Fixed after creation in MVP; approved | Approved exchange-type display | Planned/mapping pending |
| LanguageFocus | Declared languages; multi Lookup to Language catalogue | At least one for Language/Combined; empty for Culture-only | Initial members choose; automation verifies group purpose | Visible; fixed after creation in MVP | Approved focus display | Planned/mapping pending |
| CultureFocus | Declared cultures; multi Lookup to Culture catalogue | At least one for Culture/Combined; empty for Language-only | Initial members choose; automation verifies group purpose | Visible; same change rule as LanguageFocus | Approved focus display | Planned #12 |
| Capacity | Maximum total members; Number, integer | Required; Language 2 or 3, Culture/Combined 2–10 | Group selects within approved bounds; validate updates | Active member may propose change; never below current active member count | Show alongside current count/free slots | Planned/mapping pending |
| State | Open / Closed / Ended; Choice | Required; initially Open if space remains, otherwise Closed, only after membership creation succeeds | Workflow sets initial state; authorized active member manages later transitions | Open/Closed can switch or become Ended; Ended is final in MVP | Open with valid focus/space is joinable; Closed/Ended not joinable | Planned/mapping pending |
| Purpose | Brief group description; multiple lines plain text | Optional | Active members edit; admin exception | Editable | Approved description display | Proposed #12 |
| SourceRequestId | Originating person-to-person acceptance; Number, integer, unique | Required in current new-group path; old-group migration mapping remains #48 | Workflow-managed, never participant input | Hidden technical reference | Excluded | Owner-confirmed configured; runtime uniqueness not verified |
| SetupComplete | Technical publication/readiness marker; Yes/No | Default No | Acceptance sets Yes only after memberships and accepted result are established | Hidden; independent from Open/Closed/Ended | Gate operational group exposure; do not display raw marker | Owner-confirmed configured; export reviewed |
| Created / Modified and authors | System history fields | Automatic | SharePoint | Not participant inputs | Excluded as system/admin-only metadata | System |

Capacity is a group-level limit, not a registration preference. Group controls
can be changed without routine admin approval, subject to validity checks. Initial
group creation runs only after accepted participation; incomplete automation
must not publish a joinable group without its memberships (#47).

Owner-approved defaults/transitions: publish only after accepted memberships are
saved successfully. Start Open if capacity remains, otherwise Closed. An active
member can switch Open/Closed or set either to Ended; Ended is final in the MVP.
Use Closed when the group continues operating but temporarily wants no joiners.
Members can edit name/description and adjust capacity within bounds, never below
current member count. ExchangeType and language/culture focuses stay fixed after
creation in MVP; changing purpose later needs separate scope review. Necessary
exceptional admin corrections do not introduce routine approvals or an ordinary
reopen-Ended workflow. No automatic reopening on departure is added.

## Group Members field contract

One row links a participant to a group for a membership episode. It is not a
second participant profile. Participants do not add or edit membership rows
directly; ordinary accepted joins and Leave actions maintain them automatically.

| Internal field | Purpose and SharePoint type | Required/default | Source and maintenance | Member-facing behavior | Discovery display | State |
|---|---|---|---|---|---|---|
| ID | Membership reference; SharePoint system ID | Automatic | SharePoint | Read-only reference | Not exposed by default | System |
| Group | Single Lookup to Groups item | Required | Acceptance/migration automation resolves it; immutable for that episode | Shows which group, not an editable link | Technical link, not raw membership row | Planned/mapping pending |
| Participant | Single Lookup to Participants item | Required | Acceptance resolves approved participant; immutable for that episode | Shows member identity under agreed access rules | Approved display name and person-field allowlist | Planned/mapping pending |
| MembershipStatus | Active / Left; Choice | Required; provisional Active during setup, operational only after accepted/completed parent | Workflow records departure or rejected-setup cleanup as Left | Join/Leave actions, not a freely editable status field | Used internally for count and validity | Planned/mapping pending |
| MembershipKey | Request/participant episode key; single line text, unique | Required in current acceptance path | Workflow generates request:{requestId}:participant:{participantId}; immutable | Hidden | Excluded | Owner-confirmed configured; complete retry behavior remains #47 |
| JoinedAt | Episode start; Date/time in UTC | Required for new accepted joins; migration unknown-date handling decided in #48 | Workflow timestamps; do not invent historical dates | Read-only where useful | Not exposed by default | Proposed #12 |
| LeftAt | Episode departure; Date/time in UTC | Empty while Active; set on recorded departure | Leave workflow | Read-only history | Not exposed by default | Proposed #14 |
| Created / Modified and authors | System change metadata | Automatic | SharePoint | Not participant inputs | Excluded | System |

A rejoin must not erase a previous Left episode. Exact rejoin/return-from-pause
behavior is Later unless explicitly enabled; do not reactivate old rows merely
because a participant becomes Active again. No separate member Role field is
needed: sharer/learner compatibility comes from profile selections and group focus.

The current #11/#12 build uses SourceRequestId and MembershipKey as documented
above, plus ETag-conditional terminal/setup/cleanup writes. These are technical
implementation choices under #47, not proof of complete idempotency or a native
multi-column unique constraint. SourceRequestId migration mapping and group-join
episode keys still need their dependent #48/#17/#65 design. Built-in Title in Group
Members is optional and unused by the current flow. Active membership rows may
exist during partial construction; they do not represent an operational group
until the source request is Accepted and SetupComplete is Yes.
Retries must not create a second active membership, and acceptance must not
report success until its required group/membership result is consistent.

## Derived group values and profile links

| Value | Calculation/source | Maintenance and display |
|---|---|---|
| Current member count | Count MembershipStatus = Active rows for that Group | Automatic; shown to members and on group discovery |
| Free slots | Capacity minus current member count | Automatic; show 0 when full; negative count is an integrity error to resolve, not extra capacity |
| Has valid focus relationships | Remaining memberships plus relevant profile language/culture offers/interests | Automatic eligibility check; no new user-maintained status |
| Joinable | State = Open, free slots > 0, within approved capacity bounds, and valid focus | Checked for discovery and again on acceptance |
| My groups / Waiting / In a group | Current participant's active Group Members links | Derived app views; no manually maintained group text on Participants |

These are derived values, not a claim that a native SharePoint calculated column
can aggregate another list. #64 chooses supported flow/app queries and whether a
display cache is worthwhile; any cache is read-only and not capacity authority.
Acceptance must recheck actual memberships; #47 owns the concurrency design
and its proof, neither of which is certified by this document.
Count membership rows rather than silently dropping paused people; detailed
pause/Inactive recovery rules remain deferred.

An Open group may have zero free slots; it is then not joinable even though its
stored State is Open. Closed groups may have free slots but accept no new
requests. A departure does not automatically reopen a Closed group. Changing
state does not automatically remove memberships or send unchosen notifications.

## Confirmed group purpose and control rules

- Every member participates in at least one stated group focus as sharer,
  learner or both. Group purpose is structured, not inferred solely from its name.
- A language focus requires a relevant language sharer and a different member
  wanting to learn it. Reciprocal teaching is optional.
- A culture focus likewise requires a culture sharer and a different interested
  learner. Interest alone is not sharing expertise.
- A combined group supports both its language and culture focuses with those
  relationships; a member may participate in either focus or both.
- Any active group member can accept/decline join requests and set Open, Closed
  or Ended. Admin intervention is allowed in necessary exceptional cases.
- An Open group must still have capacity and valid purpose to appear as joinable.

## Shared group responsibility - final owner choice

Owner removed the proposed leader/contact role. No GroupContact field, leader
appointment, replacement or exclusive response permission is required. All active
members can see group join requests, accept/decline and manage permitted group
controls. A request targets the group, not a designated contact. The first valid
successfully persisted response wins, subject to #47 conflict protection.

Group join requests may contain an optional introduction message (owner-approved).
Its technical field name, app input/output mapping and request schema remain to
be specified before #17 package generation. Personal-request message scope is
not expanded by this group-join decision.

## Proportionate conflict and recovery scope - 2026-11-08

Owner expects low concurrency and prefers simple safe recovery. Keep conditional
updates, stable duplicate-prevention keys, write-time eligibility/capacity checks,
and a saved operation result so a retry cannot create another logical result.
Detect conflicts and incomplete setup; do not report success or expose an
unfinished group. Normal user retry should be supported; rare unresolved cases
may use documented exceptional admin assistance, not routine repair/approvals.
No general transaction/lock platform or elaborate background reconciliation is
approved. The minimum shared capacity guard across join/leave/capacity writers
still needs a concrete design/proof under #47; independent per-request version
checks do not establish last-slot safety. No guaranteed automatic recovery of
every failure is promised. Agree bounded recovery before package generation.

## Confirmed request behavior

- Requests start Pending; recipient or authorized active group member accepts
  or declines. Sender can cancel while Pending.
- Only one Pending request is allowed for the same person/group connection.
- Acceptance rechecks compatibility, availability and capacity before updating
  membership automatically. #47 covers retries and simultaneous responses.
- Accepted, Declined and Cancelled requests remain in history.

## Departure behavior accepted within the MVP boundary

- Leaving is self-service; retain membership history as Left.
- Recalculate member count/free slots automatically from remaining memberships.
- A Closed group stays Closed until a remaining authorized member reopens it.
- If remaining members cannot support the stated focus relationships, suppress
  the group from Discovery even if its stored state is Open. The same validity
  check used by discovery determines eligibility; no new recovery state is needed.
- Do not auto-end, auto-reopen, assign replacements, expel other members or start
  recovery timers. Remaining members/admins resolve exceptional group situations.
- This specifies recorded departures. Automatic pause/Inactive membership-recovery
  cascades and return-from-pause rejoining remain Later, not silently implemented.

This is consistent with automatic ordinary membership/slot updates and deferred
departure recovery: hiding an invalid candidate is an eligibility rule, not an
automatic recovery or dissolution workflow.

## Setup flags before implementation

#66 owns one-time verification/setup of participant/catalogue columns and exact
mappings. #5/#6 own form/control changes; #61 owns server validation and #7
Discovery. #12 separately owns group/member schema. Identify actual permissions
and existing connector/licence capabilities before dependent changes; this
contract changes none. Preserve existing values and map defaults deliberately;
do not reset all people to Active/Open or migration-confirmed.

Ordinary usage remains self-service, with necessary exceptional admin assistance.
Notification choice (#49), colleague access test (#18) and Excel migration (#48)
are separate pending items. No additional paid platform or hosting is permitted.

## Acceptance status

- [x] Culture and combined groups 2–10 approved; language groups remain 2 or 3 total.
- [x] Proposed matrix, projection, validation and ownership documented.
- [x] Separate Groups and Group Members field tables and derived values documented for review.
- [x] Group starts Open with space, otherwise Closed after successful membership creation; name/description editable, type/focus fixed, Ended final; capacity never below current member count.
- [x] Time zone optional; participant group-size preference and Comments notice removed.
- [x] Group decides Open/Closed/Ended; members/count/slots support joining decisions.
- [x] New registration Active/Open = Yes; preserve choices on edit; validation independent.
- [x] Culture/language/combined participation and distinct sharer/learner group-purpose rules confirmed.
- [x] Any active group member may respond/manage state; request cancellation/history rules confirmed.
- [x] Leaving/count updates, Closed-state preservation and invalid-focus discovery suppression accepted; automatic recovery remains Later.
- [x] Empty offer/interest form blocks save; invalid existing records excluded until corrected; self-service revalidation preserves participation/open choices.
- [x] Combined minimum 2 confirmed.
- [x] Final choice removes leader/contact role; all active members see/respond/manage.
- [x] Optional group-join introduction approved; technical field/length review belongs to #17.
- [x] Full person/group display approved; exclude email and admin/system data.
- [x] Implementation and deferred decisions have explicit receiving tickets below.
- [x] Owner accepted the target field tables; PR #59 merged and #46 closed on 2026-11-08.

## #46 scope audit and handoff - 2026-11-08

#46 delivers a reviewed field/ownership and Discovery exposure specification.
Document review/merge accepts the target field definitions above. No live flow,
permission configuration or tenant test is an acceptance requirement for this
contract ticket. Documentation review is its verification/handover, not a
runtime test assignment. Implementation tickets remain open independently.

| Follow-up | Receiving tickets and finish line |
|---|---|
| Participant/catalogue schema, registration UI/participation and validation | #66 schema; #5/#6 App; #61 validation Flow; verify each own scoped acceptance |
| Request type/target, introduction and per-flow interfaces | #10 personal send, #11 personal response, #17 join send, #65 join response, #62 reader, #63 cancel; #67 App inbox; each owns its package contract |
| Discovery response and screen | #7 Flow, #16 App; #9 shared compatibility, #42 shared access adapter/proof |
| Minimum shared capacity protection and bounded recovery | #47 shared proof; each consuming Flow owns integration/tests; #12 schema only |
| Caller identity, underlying permissions and ordinary-user proof | #39 assessment/#40 proof/#41 App/#42 adapter, #19 member guard/#20 membership writes/#23 request guard; #22/#24 superseded with explicit successors |
| Migration-confirmation discoverability and old-data field/key mappings | #48; decision required before migrated data is exposed, not before core development |
| Organiser contact route | #45 overview tracks the owner decision before publishing private-contact guidance; no route is invented here |
| Notifications and operational delivery | #49 decision, #21 implementation; no channel selected by #46 |
| Detailed error wording, paging and runtime coverage | Relevant reader/action implementation tickets and #25/#27; basic truthful failure handling remains mandatory |

The proposed 1,000-character introduction limit was not approved and is not a
contract default. Keep it for #17 review. Unavailable targets must never bypass
acceptance eligibility; detailed Pending display/cancellation policy remains
#10/#11/#17 work. No remaining follow-up is silently dropped or marked tested.

No target fields or permission changes are deployed by this contract.
