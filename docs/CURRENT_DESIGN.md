# Current design source of truth

This file records the approved MVP direction and the implemented baseline.
Approved target behavior is not evidence that a field, flow or permission exists.

## Authority and change control

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
| Time zone | Optional single selection from the Time zone catalogue; blank never blocks registration/discovery | Requiredness change pending #5 |
| Location derivation | Lower priority; reconsider only when cheap and supported | Later; no profile-location dependency |
| Discovery audience | Present compatible available profiles/groups, not all profiles | #7, #16, #42 |
| Discovery fields / Comments | Exact display fields undecided; participant fields generally eligible, admin/system-only fields excluded; no Comments notice for now | Decide in #7/#42 |
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
| TimeZone | Required in implemented baseline; approved target is optional, change pending #5 |
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
Group limits are approved; proposed technical names/defaults/projections still
need acceptance. #46 remains open and no schema/form is changed by this proposal.

Finalize exact types, requiredness, defaults, field ownership and exposure in #46
before schema/form changes in #5/#6. These target fields are approved requirements
but are not yet deployed:

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

Exact Discovery profile display fields remain undecided. Participant-provided
fields, including Comments, are generally eligible; admin/system-only columns
must not be shared. Remove the proposed Comments notice for now. Finalize an
explicit response projection with Discovery (#7/#42), based on this project's
contract rather than the old Excel sheet. Do not treat this general eligibility
as confirmation that every profile field is already displayed.

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

The current submission flow validates created profiles using language selection
plus required time zone and writes baseline Status. That is a legacy baseline,
not the approved target: time zone is optional. Revise for optional time zone, culture-only
registration and must never reactivate a paused participant. Retest edits as
well as creation. Existing baseline tests are preserved, not proof of the new MVP.

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
