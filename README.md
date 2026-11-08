# Tandem language and culture app

This repository contains the Tandem proof of concept: participant registration,
language discovery, connection requests, and tandem-group management.

The GitHub issue backlog is the source of truth for implementation work. Work
is completed one issue at a time, with automation used for repeatable checks.
One-time SharePoint configuration uses bounded importable setup helpers where
verified; #66 schema audit and setup/readback succeeded with the existing owner
connection. This does not establish general provisioning or participant access. The older `tandem_app`
repository is reference material only.

## Repository layout

- `src/` — application and domain code
- `scripts/` — repeatable validation and data utilities
- `tests/` — automated tests
- `docs/` — architecture, operating instructions, and the living implementation plan
- `.github/` — repository automation and contribution settings

## Ticket readiness and implementation plan

Use [the all-ticket readiness overview](docs/BACKLOG_ALIGNMENT.md) for current
validity, implementation readiness and test handover. The machine-readable
[matrix](config/backlog_readiness.json) covers the current 48 tickets and the proposed
12-core-flow baseline plus the Deferred reminder. These are not 12 new flows. [The implementation plan](docs/IMPLEMENTATION_PLAN.md)
sets the ordered batches; GitHub labels hold live lifecycle status.

Quick filters: [Flow tickets](https://github.com/maoy1/tandem-language-culture-app/issues?q=is%3Aissue+is%3Aopen+label%3A%22type%3Aflow%22),
[App tickets](https://github.com/maoy1/tandem-language-culture-app/issues?q=is%3Aissue+is%3Aopen+label%3A%22type%3Aapp%22),
[Shared technical](https://github.com/maoy1/tandem-language-culture-app/issues?q=is%3Aissue+is%3Aopen+label%3A%22type%3Ashared-technical%22),
[Overviews](https://github.com/maoy1/tandem-language-culture-app/issues?q=is%3Aissue+is%3Aopen+label%3A%22type%3Aoverview%22).

Exactly one lifecycle label per ticket: Planned / In progress / Blocked /
Deferred / Ready for review / Ready for testing / Done / Superseded. In progress
means active work, at most one non-overview ticket; partial queued work is Planned.
Each issue has one type: Flow / App / Shared technical / Overview. One production
flow has one owner. Superseded means replaced, not completed. A partial merged PR or
saved flow is not a whole-ticket testing handover. Closed #46 is an accepted
contract, not proof of deployed behavior; keep runtime tests with their owner.

## Working method

Production is SharePoint + Power Apps + Power Automate within existing licences:
no additional hosting budget, paid service, premium/custom connector, trial or
Python application runtime. Ordinary participant workflows must be self-service,
with minimal admin effort as participation grows. Critical or exceptional cases
may involve necessary admin approval or intervention; routine actions do not.
Flag and verify permissions, connections, licences and settings before relying
on them. Necessary one-time setup and exceptional maintenance must be explicit.

1. Select the next GitHub issue from the POC Vertical Slice milestone.
2. Implement only that issue and its acceptance criteria.
3. Run appropriate checks from the [test catalogue](docs/TEST_CATALOGUE.md) and record actual results, versions and outstanding checks in [test run records](docs/TEST_RUNS.md).
4. Update the implementation plan and backlog alignment in the same PR, recording outstanding tenant checks.
5. Review and merge the PR, let `Closes #N` close the completed issue, then verify GitHub and the plan agree before starting the next issue.

The human checkpoints are intentionally limited to product decisions, SharePoint
or Power Platform tenant actions, and approval of user-facing behavior. Routine
validation, tests, and repeatable setup should be handled by the repository.

See [the implementation plan](docs/IMPLEMENTATION_PLAN.md) for the current
sequence and control points.

See the [current design source of truth](docs/CURRENT_DESIGN.md) for the
agreed SharePoint schema, participant flow, and removed design elements.

See the [backlog alignment notes](docs/BACKLOG_ALIGNMENT.md) for the written
alignment of the existing GitHub tickets with the current design.

## Disposable flow-package import probe

Current authoring-method experiment (#28): the prepared
[probe ZIP](artifacts/import_probe/TandemImportProbe.zip) contains only a
Power Apps (V2) trigger and two built-in actions, with no connectors/data calls.
Import **as new** named **TandemImportProbe**, then manually test. Expected:
success true, message IMPORT_PROBE_OK. It must not update a working flow.

Owner confirmed the connector-free import and run: success true and message
IMPORT_PROBE_OK (OPS-003). The probe imported off and was turned on before testing.

Also passed: [read-only SharePoint probe ZIP](artifacts/import_probe/TandemSharePointImportProbe.zip)
(OPS-004). Import as NEW **TandemSharePointImportProbe** and select the existing
SharePoint connection. Turn on if needed, then manually run. Expected: success
true, message SHAREPOINT_IMPORT_PROBE_OK. One GET reads site technical ID only;
no list/record operations. Embedded owner connection is only for this disposable
experiment, not participant authorization. Owner confirmed import and test
succeeded (OPS-004); raw response output was not supplied. Stop on access/licence
prompts when reproducing in another environment.

The optional local builder is scripts/power_automate/build_import_probe.py;
--sharepoint-site with --output selects the second probe. Python is development
tooling only. The current suite has 194 passing local tests (including #6/#66/#61/#9 and #47 protocol reference checks); app execution is separate. Owner chose legacy packages for now, keeping
SharePoint data and existing entitlements. Neither probe establishes complex-flow
import, ordinary-participant access or full reproducibility. Generated ZIPs are
experimental, not officially certified ALM packages. See the current
[implementation plan](docs/IMPLEMENTATION_PLAN.md).

## Schema alignment packages - #66

The [schema handover](docs/POC_SHAREPOINT_SETUP.md) includes the imported
TandemSchemaAudit and TandemSchemaSetup-v2 packages, actual field mapping and
passed safe-repeat evidence. Setup-v2 owner preview/apply/readback, five-write
skip confirmation and final whole-schema audit passed. PR #69 is merged; #66 is complete. These are one-time helpers, not participant production flows.

## Local Python environment

The repository uses the ignored `.venv` directory for local Python tools:

These tools validate repository files; they do not host or run the deployed app.

```bash
source .venv/Scripts/activate
python --version
```

If it does not exist, create it with `python -m venv .venv` using an available
Python 3.11+ installation. In Git Bash, activation uses
`source .venv/Scripts/activate`; PowerShell is not required.

## Current status

Current priority: build the integrated app/flow path first. Start with the Discover
screen and Power Apps-triggered flow using the existing Participants list, then
in-app requests, accepted groups/memberships and notifications. Remaining detailed
acceptance tests are deferred, not passed. Notification/Approvals choices and setup
automation are discussed at their build stage. See the current-priority table in
docs/IMPLEMENTATION_PLAN.md and the build batches in src/README.md.

The owner's v0.2 annotations are now the target planning baseline: parent #45,
reviewed contract #46 with outstanding decisions, registration #5 in progress,
acceptance concurrency #47, Excel migration #48 last,
and notification option review #49 before channel selection. Culture-only and
combined participation and separate statuses are approved target requirements,
not deployed features. Time zone is optional and catalogue-based. No participant
group-size preference or Comments notice; exact Discovery display fields remain
undecided, generally excluding admin/system-only columns. Groups show count/slots
and control Open/Closed/Ended. Location derivation and ranking are Later.
See docs/CURRENT_DESIGN.md and docs/IMPLEMENTATION_PLAN.md before real-data wiring.

The #46 [field contract](docs/MVP_FIELD_CONTRACT.md) is ready for review.
Culture and combined groups 2–10 with valid focus relationships are approved; the
proposed field names/defaults/projection do not yet change deployed registration.

POC-01 (repository foundation) and POC-02 (SharePoint schema and manual setup)
are complete. POC-02 includes the version-controlled Language and Time zone
catalogues, local validation, tests, an Excel import template, and the manual
tenant setup guide. POC-03 was delivered in merged PR #34 and issue #3 is closed.
POC-04's language preferences passed the owner's acceptance checks and PR #37
is merged. #18/#39–#42 remain open; the owner deferred ordinary-colleague access
testing until a tester is available. No replacement access architecture is
selected. Complete needed access checks before broader release; continue
owner/synthetic-data work meanwhile. PR #51 merged the reviewed contract and test
catalogue. Current work is the approved #5 registration subset; see
[the POC-05 setup guide](docs/POC_05_CULTURE_REGISTRATION.md). Schema/policy JSON
now describes that desired delta, explicitly pending tenant setup and tests.
#46 stays open for outstanding decisions; #6 follows registration implementation.
