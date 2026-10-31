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
