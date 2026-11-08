# Shared compatibility source — #9

One maintained rule source: scripts/power_automate/compatibility.py. Its expression
trees evaluate locally for reference and compile into Power Automate. Python is
never part of the deployed runtime. No child flow, hosting, connector, licence,
tenant schema change or employee-data export is needed for this shared proof.

config/compatibility_contract.json records typed interfaces and consumer boundaries;
artifacts/compatibility/CompatibilityRules-v1.fragments.json is generated review
material, not an independent second rule source. Future package builders import
the generator and pin its rules version/source SHA in their own review artifact.
Do not copy predicates into Power Apps or maintain separate manual variants.

## Normalization and inputs

Profiles: profileId, canonical accountKey, validation status, participationStatus,
openToConnections, four integer role-ID arrays, optional timezoneId. AccountKey is
a trusted stored identity key, not actor authorization. Use one canonical per-site
identity representation in every adapter, trimmed/lowercased; app email or supplied
profile ID does not authenticate anyone. No display-name matching.

Adapters unwrap SharePoint Choice/Person/Lookup records using verified tenant
mapping, enforce typed integer IDs and complete reads/pagination, and provide
complete active catalogue IDs. Missing optional arrays/null become []; duplicate
role IDs deduplicate. Unknown/inactive/malformed IDs, missing availability and
duplicate profile/canonical account IDs fail before matching. Empty time zone is
valid; supplied zone must be active. Batches above 500 fail, not truncate. A caller
may page/read within its verified bounds; it cannot call a truncated set complete.

Emit normalization_actions at top level or in a preflight Scope outside foreach.
All consumer success processing depends on <prefix>_Catalogues, which follows
Require_valid_input. Never consume intermediate Profiles output before the guard.
The generated Terminate for invalid input is intentionally outside loops.

## Any language — owner deferred

The owner explicitly does not want to consider this nice-to-have now. Resolve its
actual catalogue ID by the existing key (ISOcode=any) and pass anyLanguageId; null
only if absent. Known Any-language entries are removed from teach/learn matching
sets, never treated as wildcards. Concrete selections on the same profile still
work. An Any-only profile supplies no concrete language fit. Any as declared group
focus is invalid. No catalogue deletion, registration rewrite or new vocabulary.
Synthetic ID 99 is unrelated to the actual tenant ID 84.

## Person rules and output

Both participants need validation Active, participation Active, openness Yes and
a useful concrete language/culture selection. Exclude same profile or account.
Any directional language/culture sharer->different learner intersection qualifies;
reciprocity is optional, common interests alone do not qualify. Output eligible,
Language/Culture/Combined fitType and four directed matching-ID arrays. Ineligible
results expose no matching detail (null type/empty arrays). The consumer attaches
only approved display fields under #42/#46; this helper does not project identity,
email, Comments or admin fields, or authorize access.

## Group rules and availability boundary

Every declared concrete focus needs a relevant sharer and a different learner;
each roster member participates in at least one stated focus. Combined supports
both focus kinds; each person may participate in either. Validation-inactive
profiles do not support focus. Wrong type/focus shapes, unrelated/missing/duplicate
members or unsupported focuses fail purpose. Language capacity 2–3; Culture/Combined
2–10; capacity never below membership count. Focus/type remain unchanged.

The group input contains current authoritative active-membership profile IDs,
state, capacity, setupComplete and focusSharersAvailable. Count **all current
membership episodes**, including paused people; never silently drop those members
to manufacture a free slot. Duplicated profile IDs indicate inconsistent active
membership data and reject purpose rather than silently deduplicate occupancy.

focusSharersAvailable is a required **trusted server-adapter gate** for available
sharers for every declared focus; unknown evidence cannot be true by default or
come from the app. Detailed live availability/authority binding is proven by each
consumer, not by synthetic booleans. Structural focus matching alone is not that
availability proof and does not define deferred pause-recovery behavior.

compatible requires valid purpose/capacity, candidate role and personal availability,
Open state, free slot, setup complete, verified sharer-availability gate and candidate
not already a member. Closed/Ended/full/invalid-purpose groups do not qualify. It
does not reopen/end/rejoin/delete/write anything or guarantee atomic admission.

Parse group_schema first. Caller initializes/resets its own focus-check array,
embeds group_action_fragment with unique prefix and executes accumulating loops
sequentially. Actual group/member mappings remain #12; write races/recovery #47.

## Consumer adapter handover

| Owner | Adapter responsibility / generated source use |
|---|---|
| #7 Discovery | Fresh authorized complete profiles/groups/members/catalogues -> normalization; pair/group fragments; approved projection #42 |
| #10 SendRequest | Reread sender/recipient; pair fit at Send; never rely on a cached Discovery result |
| #11 RespondRequest | Reread actors plus proposed roster/focus/capacity; pair and group fragments; conditional group/membership persistence #47 |
| #17 SendGroupJoinRequest | Fresh candidate/current group/roster and availability evidence; group fragment; own duplicate/authority guards |
| #65 RespondGroupJoinRequest | Reread group/roster/candidate at acceptance; group fragment; #47 last-slot/version protection and recovery |

No production consumer is certified by importing the shared proof. DISC-008
projection, DISC-010 live freshness, DISC-011 pagination and REQ send/accept authority
or atomic writes remain consumer integration. Source #9 can finish on its own
review/proof evidence rather than waiting for all of those tickets to close.

## Verification

39 hand-authored synthetic expected cases cover directional/reciprocal language,
culture-only/share-only, combined, common-interest rejection, self/availability,
null/dedup/blank zone, distinct focus participants, per-member relevance, capacities,
Closed/Ended/full/incomplete states, unresolved availability, and deferred Any.
20 new local tests include strict malformed input rejection and independent small
WDL-subset execution of emitted references/loops/normalization against all fixtures.
The subset runner is a local check, not the Microsoft runtime or schema engine.

Whole local suite: **121 passed**. Proof **45 actions / depth 4**, no connector,
live reads or writes; largest generated expression 2800 characters. Build/version/
hash and NOT_IMPORTED_NOT_TESTED state are in the proof review. Action counts use
all branch/loop definitions. Recheck 500-action/8-depth limits in every consumer.

Current import/test steps and verification checkboxes are directly in issue #9.
No full rule/runtime or consumer PASS is inferred from local checks. No employee
fixtures, live profile changes or additional setup permission is needed for proof.
