# Test execution records

The test definitions are in TEST_CATALOGUE.md. This file stores observed results
without overwriting history when requirements or deployed versions change.

## Known baseline evidence

| Run reference | Date | Tests | Result and evidence source | Version/scope limits |
|---|---|---|---|---|
| HIST-REG-20261031 | 2026-10-31 | BASE-001–004 | PASS, owner-reported saved/reopened language selections, multiple Teach/Learn and teach-only profile in chat; see POC_03_PARTICIPANT_SELF_REGISTRATION.md | Published app/flow versions not recorded; original registration baseline, not optional-time-zone/culture target |
| HIST-FLOW-20261031 | 2026-10-31 | BASE-005–009 | PASS, owner-confirmed guided manual Compose/Filter/Select, teach-only and Needs review runs; see src/README.md and tests/fixtures/discovery_flow_cases.json | Manual synthetic trigger, five chat profiles, not full six-profile fixture or real-data/authenticated app integration; flow export/version not captured |

Do not claim that screenshots/full run logs were captured for every historical
check. These rows preserve owner reports, not agent-observed replay results.
No target REG/PAR/DISC/GRP/REQ/LEAVE/ACC/OPS/NOT/MIG case is currently recorded
as passed. Catalogue targets are NOT RUN unless specifically deferred/pending.

## Deferred and pending checks

| Tests | State | Reason / linked work |
|---|---|---|
| ACC-001–002, ACC-005 | DEFERRED | Owner will arrange normal colleague testing; #18/#39–#42 remain open |
| DISC-008 | REQUIREMENT PENDING | Exact Discovery display fields not agreed |
| NOT-001 | REQUIREMENT PENDING | #49 must select event/channel/recipient behavior |
| MIG-001–002 | DEFERRED | Actual Excel inspection/migration is final phase #48 |

## Latest local checks

### RUN-20261031-01 — POC-05 local configuration checks

- Tester: agent; repository checks only, no tenant account used.
- Branch: codex/issue-5-culture-registration; working tree for the POC-05 PR.
- App/flow version: not applicable; neither was inspected or deployed.
- Inputs: repository schema/policy and synthetic mutated configurations; no
  employee data or live SharePoint calls.

| Check | Actual result | Status | Scope |
|---|---|---|---|
| pytest, tests/test_sharepoint_schema.py | 22 passed | PASS | Schema/policy consistency and rejection of required optional fields, omitted offer/interest branches, wrong culture targets and disabled inactive-selection rule |
| validate_schema.py | Schema is valid | PASS | Desired schema structure only |
| validate_registration.py | Registration policy is valid | PASS | Desired form/policy agrees with schema |
| git diff --check | No formatting errors | PASS | Working-tree text changes |
| REG-001–009, REG-011–012 tenant scenarios | Not executed | NOT RUN | Culture values, prerequisites, actual form/flow changes and acceptance remain pending |

The mutation tests cover configuration protections related to REG-002/003/005/
006/008. They do not establish a live save, active-option filter, validation flow,
edit-loop guard, authentication or discovery result. No cleanup was needed;
no live records were created. Retest live scenarios after owner setup and record
the app/flow versions separately.

### RUN-20261031-02 — expanded culture proposal

- Agent local check on codex/issue-5-culture-registration; no app/flow deployed.
- PASS: culture_catalogue_proposal.json parses; all 85 display labels and keys
  are unique; labels are alphabetically ordered; Active values are Boolean true;
  proposal_pending_owner_review status is preserved.
- PASS: git diff --check. No tenant records created or changed.
- This validates proposal data structure only, not coverage approval, import,
  active-option filtering or any REG acceptance scenario.

## Tenant setup evidence

### SETUP-20261031-01 — owner access screens

- Owner-reported: SharePoint New List/Create column options available; existing
  registration app and submission flow open in Edit. All three checks confirmed.
- No creation/save operation was tested by these checks; no app/flow version
  changed. Culture catalogue connection/read access remains to verify after creation.
- This is setup evidence, not a REG/ACC scenario pass or ordinary-user access proof.

### SETUP-20261031-02 — catalogue rename and bulk-entry workbook

- Owner reports the CultureKey display-name change to Culture key is done.
  Required/unique/default settings and catalogue contents have not been
  independently inspected.
- Agent generated docs/import/culture_catalogue_import.xlsx from the 85-value
  JSON proposal. PASS: all 85 rows and three columns match the source after XLSX
  export/reimport; first rows rendered and visually inspected.
- Owner subsequently confirms the bulk-entry step and its requested checks are
  done: 85 catalogue entries, populated keys and Active = Yes. Evidence is owner
  reported; no list export or screenshot captured. App/flow catalogue-read access
  remains NOT RUN. This is not a registration acceptance pass.

### SETUP-20261031-03 — Participants column screenshot

- Screenshot shows required Participant account and required Time zone; Time zone
  is a Lookup. ShareCultures/LearnCultures (or their intended display labels) are
  not visible in the supplied column list. Their creation/settings are unverified.
- Email, Matching cycle and Full name are visible existing helper/legacy fields;
  their presence does not authorize deletion or changing the identity contract.
- A column summary does not prove lookup catalogue targets, multiple selections,
  uniqueness or actual internal names. Inspect field settings for those checks.
- #5 remains open. Optional-time-zone acceptance and culture form/flow tests have
  not passed merely because the Culture catalogue was populated.

### SETUP-20261031-04 — optional SharePoint Time zone

- Owner confirms the instructed change: Participants Time zone, Require that
  this column contains information = No, saved in SharePoint.
- Owner-reported setting only; no new screenshot, app save/reopen, flow result or
  blank-time-zone discovery case observed. REG-003 and DISC-005 remain unverified.
- Culture lookup settings and app/flow refresh/validation remain pending.

### SETUP-20261031-05 — participant culture lookups

- Owner confirms both instructed lookup columns are ready: ShareCultures and
  LearnCultures, displayed as Cultures I can share and Cultures of interest,
  looking up Culture catalogue / Title, multiple selections Yes, required No.
- Evidence is owner-reported completion of the setup instructions. Internal names
  and settings were not independently inspected through a tenant export.
- No app refresh, culture save/reopen or flow validation result confirmed yet;
  REG tenant scenarios remain unverified. Next: add generated cards to Form1.

### SETUP-20261031-06 — culture cards added to app

- Owner confirms the instructed Participants refresh, addition of both culture
  fields to Form1 and app save. Publication was not requested; no published
  version or flow change is evidenced by this confirmation.
- Catalogue options/multiple selection, stored lookup IDs, blank Time zone,
  save/reopen and submission-flow validation remain unverified. Next: preview
  both culture dropdowns in Edit/New mode and check multiple selections.

### RUN-20261031-03 — culture selector options

- REG-013: FAIL, owner-reported. Both culture lookup controls show Item 1/2/3
  rather than the expected catalogue labels during the requested preview check.
- App editing/preview version not recorded; no screenshot or Items expression
  inspected. Sample/default control binding is suspected, not a proven cause.
- Proposed correction: select the control inside each culture card, inspect Items,
  and bind it to Choices of the corresponding Participants culture lookup; use
  Value as the display field for classic lookup combo boxes. Retest pending.
- No successful culture selection, save/reopen, flow validation or published
  app behavior is established by this run.

### RUN-20261031-04 — culture selector retest

- Owner reports the lookups are now correct after the supplied Items/display
  binding changes. The reported Item 1/2/3 display issue is resolved in preview.
- REG-013 label-display portion: PASS, owner-reported. Multiple selections and
  stored lookup persistence were not explicitly confirmed; full case remains
  pending those checks. Earlier failed run is retained above.
- No published app version or submission-flow version recorded. REG-002/003/007
  save/reopen and REG-005 empty-input blocking remain unverified.

### SETUP-20261031-07 — registration control names

- Owner confirms the four Combo box controls were renamed to cmbTeachLanguages,
  cmbLearnLanguages, cmbShareCultures and cmbLearnCultures as instructed.
- No new save, validation or persistence result confirmed. Next: configure the
  Save OnSelect all-four-empty guard and test REG-005 without submitting data.

### RUN-20261031-05 — empty-selection save guard

- REG-005 form/Preview portion: PASS, owner-reported. Following the supplied Save
  OnSelect formula, clearing all four language/culture selections and clicking
  Save shows the validation message and keeps the form open as expected.
- The instruction included cancelling the temporary edit. No SharePoint write
  audit, published app version or backend validation run was independently observed.
- This does not prove server-side rejection of invalid direct-list input. Culture
  save/reopen, optional blank Time zone, multi-selection persistence, inactive-ID
  checks and submission-flow create/edit validation remain unverified.
- Next prerequisite: inspect the actual participant-submission trigger and current
  validation actions before changing edit handling or its update-loop guard.

### SETUP-20261031-08 — submission trigger inspected

- Owner confirms the existing Tandem – Participant submission trigger is When an
  item is created. This trigger alone does not revalidate profile edits.
- No trigger change performed/confirmed. Inspect current Compose/Condition/Update
  item structure and design/test a guard against self-triggered Status updates
  before adopting created-or-modified validation. Create/edit acceptance pending.

## New run template

Copy this section for an execution. Record one row per case (or split a case into
named variants); use linked issue attachments for sanitized evidence when useful.

### RUN-YYYYMMDD-NN

- Date/time and timezone:
- Tester label and role (owner / ordinary A / ordinary B / admin):
- Environment and isolated fixture scope:
- App name and published version/time (or not applicable):
- Flow name and version/last-modified time (or unknown):
- Relevant repository commit / PR / issue:
- Preconditions/configuration verified:
- Fixture IDs, initial state and any reset steps (no real employee data):
- Known requirement changes since prior run:

| Test ID and variant | Action/input | Actual result | PASS/FAIL/NOT RUN/DEFERRED/REQUIREMENT PENDING | Sanitized evidence / related issue |
|---|---|---|---|---|
| | | | | |

- Comparison with catalogue Expected:
- Flow run time/reference and first failed action (if applicable):
- SharePoint records checked after actions:
- Test-record cleanup/reset performed (or intentionally retained):
- Remaining gaps and retest decision:

PASS applies only to that version, scenario and account role. An admin success
does not prove ordinary-user access. A local test does not prove live deployment.

## Recording a reported issue

Use the GitHub bug-report template or give the assistant the test ID, steps and
expected/actual results. For example: “REG-003 fails: blank time zone still causes
a required-field error in the published test app.” The assistant should locate
the test and relevant feature ticket, inspect version-specific evidence, fix on
the appropriate branch, and append retest results after verification.
