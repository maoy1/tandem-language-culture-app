# Tandem language and culture app

This repository contains the Tandem proof of concept: participant registration,
language discovery, connection requests, and tandem-group management.

The GitHub issue backlog is the source of truth for implementation work. Work
is completed one issue at a time, with automation used for repeatable checks.
SharePoint tenant configuration is performed manually because tenant access
and permissions are not available to this repository. The older `tandem_app`
repository is reference material only.

## Repository layout

- `src/` — application and domain code
- `scripts/` — repeatable validation and data utilities
- `tests/` — automated tests
- `docs/` — architecture, operating instructions, and the living implementation plan
- `.github/` — repository automation and contribution settings

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
3. Run the automated checks and update the relevant documentation.
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

The owner's v0.2 annotations are now the target planning baseline: parent #45,
field contract #46 next, acceptance concurrency #47, Excel migration #48 last,
and notification option review #49 before channel selection. Culture-only and
combined participation, separate statuses and candidate-visible Comments after
warning are approved target requirements, not deployed features. Keep the
working Time zone catalogue; automatic location derivation and ranking are Later.
See docs/CURRENT_DESIGN.md and docs/IMPLEMENTATION_PLAN.md before real-data wiring.

POC-01 (repository foundation) and POC-02 (SharePoint schema and manual setup)
are complete. POC-02 includes the version-controlled Language and Time zone
catalogues, local validation, tests, an Excel import template, and the manual
tenant setup guide. POC-03 was delivered in merged PR #34 and issue #3 is closed.
POC-04's language preferences passed the owner's acceptance checks and PR #37
is merged. #18/#39–#42 remain open; the owner deferred ordinary-colleague access
testing until a tester is available. No replacement access architecture is
selected. Complete needed access checks before broader release; continue
owner/synthetic-data work meanwhile. Next is #46, not another access redesign.
