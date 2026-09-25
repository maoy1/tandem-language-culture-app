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

1. Select the next GitHub issue from the POC Vertical Slice milestone.
2. Implement only that issue and its acceptance criteria.
3. Run the automated checks and update the relevant documentation.
4. Review the result together before moving to the next issue.

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

```bash
source .venv/Scripts/activate
python --version
```

If it does not exist, create it with `python -m venv .venv` using an available
Python 3.11+ installation. In Git Bash, activation uses
`source .venv/Scripts/activate`; PowerShell is not required.

## Current status

POC-01 (repository foundation) and POC-02 (SharePoint schema and manual setup)
are complete. POC-02 includes the version-controlled schema, local validation,
tests, an Excel import template, and the manual tenant setup guide.
