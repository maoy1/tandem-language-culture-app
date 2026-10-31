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
| Time zone | Keep required single selection from the Time zone catalogue | Current baseline retained |
| Location derivation | Lower priority; reconsider only when cheap and supported | Later; no profile-location dependency |
| Discovery audience | Present compatible available profiles/groups, not all profiles | #7, #16, #42 |
| Comments | Show Comments on compatible candidate profiles; warn users before save | #46 then #5/#7 |
| Private organiser notes | Participant emails organisers; no new private-Comments split | Contact route to identify; separate from notification-channel decision |
| Language groups | 1-to-1 or 1-to-2, meaning 2 or 3 people total | #12/#13 |
| Culture groups | Up to 10 total members | Minimum not decided; combined-type capacity also needs agreement in #46 |
| Participant status | Separate Active/Paused/Inactive participation from validation | #46 then #6 |
| Culture-only participation | Supported; no mandatory language selection | #5/#7 |
| Notifications | Evaluate options first; channel/event matrix not yet agreed | #49 then #21 |
| Membership changes | Normal acceptance, membership and slot updates automatic | #11/#12/#17/#47 |
| Exceptions | Necessary admin support permitted; avoid routine organiser matching | #13/#14 |
| Excel import | Inspect/map/migrate at the end of implementation | #48; before launch if existing-data launch requirement remains |
| Hosting | Standalone hosting alternative rejected under no-budget constraint | All tickets |

## Implemented SharePoint baseline

config/sharepoint_schema.json and config/participant_registration.json describe
the current registration baseline. They are not silently expanded by this plan.

Language catalogue: Title, required unique indexed ISOCode, Aliases, Active.
Time zone catalogue: Title, required unique indexed IANAId, optional WindowsId,
Active.

| Participants field | Current implementation |
|---|---|
| ParticipantAccount | Required unique single Person identity; locked to signed-in user in the app |
| TeachLanguages / LearnLanguages | Multi-value Language catalogue lookups |
| TimeZone | Required single Time zone catalogue lookup |
| LearningFocus / Comments | Optional multiple-line text |
| Status | Flow-managed validation baseline: Active / Needs review |
| Title | Hidden technical text |
| Created / Modified and authors | SharePoint system-managed columns |

Do not introduce a participant-entered identity email. Migration email matching
must resolve to the company account; decide mapping/duplicate handling in #46/#48.
Do not delete existing tenant helper/legacy columns during planning.

## Target fields and candidate exposure

Finalize exact types, requiredness, defaults, field ownership and exposure in #46
before schema/form changes in #5/#6. These target fields are approved requirements
but are not yet deployed:

- Controlled Cultures I can share and Cultures I am interested in, using a Culture
  catalogue. This supersedes the earlier removal/deferment of controlled culture fields.
- Preferred group size, with choices aligned to language/culture capacities.
- Participant-controlled participation status Active / Paused / Inactive.
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

Comments are candidate-visible. Show before saving:
“Your comments are shown to compatible participants in Discovery. For private
information, email the organisers.”
This is visibility to eligible discovery users, not public/internet publication
or general list access. Identify a real organiser email route before publishing;
do not invent an address or send mail automatically.

The candidate projection must be an explicit allowlist based on this project's
field contract, not every field in an old Excel workbook. Comments are included;
identity/name, language/culture preferences, time zone, focus and group context
still need exact projection decisions in #46. Do not expose validation/migration
flags, audit fields or other technical/admin metadata by default.

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
Language capacity is 2 or 3 total; culture capacity is at most 10. Do not infer
a universal minimum of 3. Open/Closed/Ended is the target simple MVP group state;
other lifecycle states and timers require a later decision. Active members may
make permitted changes, with necessary admin override.

Normal membership counts and free slots update automatically. A departure remains
self-service and preserves history; ambiguous group purpose/sharer recovery can
use exceptional admin support. Do not close/end/disband or rejoin people
automatically under unimplemented Later rules.

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
plus time zone and writes baseline Status. It must be revised for culture-only
registration and must never reactivate a paused participant. Retest edits as
well as creation. Existing baseline tests are preserved, not proof of the new MVP.

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
