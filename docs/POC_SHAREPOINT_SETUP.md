# Tandem SharePoint POC setup

This document is the practical setup guide for the current participant
registration POC. The design authority is
[CURRENT_DESIGN.md](CURRENT_DESIGN.md). If this guide conflicts with it, the
design authority wins.

The #46 contract is accepted. #66 has now inspected the actual participant and
catalogue schema and applied the bounded changes below; final repeat/full-audit
acceptance remains pending. Discovery display is approved in MVP_FIELD_CONTRACT.md;
notifications remain undecided (#49). Catalogue time zone is optional for
participants; migration is the final phase (#48).

## #66 schema alignment handover - 2026-11-08

The accepted contract is #46; actual internal names and list IDs are now in
[tenant_schema_mapping.json](../config/tenant_schema_mapping.json). This mapping
combines the owner-returned full metadata audit with the successful bounded setup
readback. It is not an export of employee registrations. Fresh full audit and
repeat/idempotency checks below remain outstanding. Runtime app behavior stays
with #5/#6/#61; ordinary-user access remains a separate deferred proof.

### Packages and prerequisites

- [TandemSchemaAudit.zip](../artifacts/schema_alignment/TandemSchemaAudit.zip):
  build `1fd35100-e381-48b7-9d53-aa927d1131ed`, 73 actions / maximum depth 5;
  owner imported/ran successfully. Reads field metadata and catalogue values;
  never reads participant rows or changes data/settings.
- [TandemSchemaSetup-v2.zip](../artifacts/schema_alignment/TandemSchemaSetup-v2.zip):
  build `1080ab9d-fec5-4c42-92ef-4988bb36390f`, 47 actions / maximum depth 4;
  owner imported/ran preview and apply successfully. This is the supported setup
  artifact. Only v2 is delivered; synchronous Response has no trigger concurrency.
- Each ZIP has adjacent readable `.definition.json` and `.review.json` files.
  Use the existing owner SharePoint connection; both are disposable setup helpers,
  not production flows or a participant authorization method. No new connection,
  role grant, premium connector, account or licence was introduced.
- Setup verifies list ManageLists permission, exact target identities/types,
  missing-field collisions, complete bounded catalogue reads, nonblank labels/keys
  and duplicate keys before any write. Preview defaults to ApplyChanges = No.
  Each helper must be run once at a time; do not start overlapping apply runs.

### Verified minimum delta

| List/field | Actual setting after apply readback |
|---|---|
| Participants.ParticipationStatus | Required Choice Active/Paused/Inactive; default Active |
| Participants.OpenToConnections | Required Yes/No; default Yes |
| Language catalogue.Title | Required |
| Timezone catalog.Title | Required |
| Timezone catalog.IANA_ID | Required, indexed, unique |

Existing account uniqueness and optional four multi-lookups were already correct.
`Timezone` remains optional, single Lookup displaying `IANA_ID`. Existing Status
choices are preserved; validation uses Active/Needs review. Optional Windows
conversion metadata is not deployed or required by the IANA-based MVP. No row
updates or deletes, internal-name changes, lookup-display changes, permission
changes or working-flow replacement are included. New-field defaults do not
establish how old profiles are initialized by the app.

### Remaining acceptance checks (SCHEMA-001/002)

1. In the already imported **TandemSchemaSetup v2**, run again with
   **ApplyChanges = Yes**, after the prior run has ended. Expected:
   `SETUP_VERIFIED`, `setupVerified: true`, and all five **Create_/Update_**
   HTTP actions **Skipped** because settings already match. Readback actions
   still run. Return Setup_report Outputs and confirm the five writes skipped.
2. Run the already imported **TandemSchemaAudit** again. Expected:
   `collectionComplete: true`, `errors: []`, no truncation, both new required
   participant fields/defaults present, and all required/unique/index/lookup
   mappings correct. Paste **Audit_report Outputs** for local analysis. The
   collector's success alone means collection succeeded, not schema alignment.
3. The agent analyzes that actual report with `schema_audit.analyze`, which
   excludes SharePoint's computed Title aliases and preserves the working
   IANA_ID display and legacy Status choices. Expected **Verified**, no unexplained
   findings; existing account and four lookup settings remain correct. Record the
   repeat and audit run references before closing #66 on its own acceptance.
4. If permission, metadata, duplicate-key, queued-index or readback checks fail,
   report the first failed action/output; keep the case Pending/Blocked. Successful
   earlier field operations remain; there is no multi-field rollback. Repeat only
   after diagnosing the error. Never delete/recreate lists or perform deduplication
   as a workaround. SharePoint handles a duplicate key introduced after preview by
   rejecting uniqueness; readback cannot falsely report setup verified.
5. After evidence is retained, turn off the disposable helpers. No test/business
   records were created and no business-column cleanup is required. Required
   schema stays. Do not grant these owner-connection helpers to participants.

### Optional local authoring commands (Bash)

These build/analyze packages locally; deployed workflows run in Power Automate.
Output paths must be new: builders refuse to overwrite delivered versions.

```bash
./.venv/Scripts/python.exe -m pytest -q
./.venv/Scripts/python.exe scripts/power_automate/build_schema_audit.py --site-url https://reedelsevier.sharepoint.com/sites/OG-TandemOrg --output /tmp/TandemSchemaAudit-new.zip
./.venv/Scripts/python.exe scripts/power_automate/schema_setup.py --site-url https://reedelsevier.sharepoint.com/sites/OG-TandemOrg --output /tmp/TandemSchemaSetup-new.zip
./.venv/Scripts/python.exe scripts/power_automate/analyze_schema_audit.py /tmp/audit-report.json --output /tmp/audit-mapping-new.json
```

## Architecture

```text
SharePoint lists = operational database
Power Automate = validation, identity enrichment, and status updates
Power Automate discovery = compatible candidates; participants choose connections
SharePoint page = anonymised aggregate statistics
```

Participants register through the Power Apps form embedded in Teams. The app
filters the user experience to the signed-in participant. Direct SharePoint
row privacy is not guaranteed in this POC because the unique Participant
account field prevents the built-in item-level permission setting.

## Current lists

### Language catalogue

Create one controlled catalogue with:

| Column | Type |
|---|---|
| Title | Canonical language name |
| ISO code | Single line text, unique and indexed |
| Aliases | Multiple lines |
| Active | Yes/No |

Import the language seed JSON with a one-time manual flow:

1. Use **Manually trigger a flow**.
2. Add **Compose** and paste the JSON array.
3. Add **Apply to each** using the Compose output.
4. Add SharePoint **Create item** inside the loop.
5. Map `name` to Title, `iso` to ISO code, `aliases` with `join(...)`, and
   `active` to Active.
6. Run once, verify the row count, then turn the import flow off.

This import flow is only for maintaining the Language catalogue. It is not
used by the participant submission flow.

### Time zone catalogue

Use the **Time zone catalogue** sheet in the Excel import workbook. The list
must contain:

| Column | Type | Rule |
|---|---|---|
| Title / Time zone | Single line text | Required display label |
| IANA ID | Single line text | Required, unique, and indexed |
| Windows ID | Single line text | Optional |
| Active | Yes/No | Default Yes |

Import the catalogue before configuring the Participants lookup. Delete the
sample row after import, then set the IANA ID column to unique and indexed.

### Participants

| Column | Type | Participant-facing? |
|---|---|---|
| Title | SharePoint system text | No |
| Participant account | Person or Group, one person | Yes; required and unique |
| Teach languages | Lookup to Language catalogue, multiple | Yes; optional |
| Learn languages | Lookup to Language catalogue, multiple | Yes; optional |
| Time zone | Lookup to Time zone catalogue, one value | Yes; optional target (required restriction exists in baseline) |
| Learning focus | Multiple lines | Yes; optional |
| Comments | Multiple lines | Yes; optional |
| Status | Choice: Active; Needs review | No; flow-managed |

Do not ask participants for a separate email address. The Participant account
field is the identity source. If a hidden email helper is later required for
notifications, populate it from that account in the flow; it is not a form
input.

Leave SharePoint Created and Modified columns system-managed. Do not create
replacement columns for them.

## Participant form

The participant form should show only:

- Participant account
- Teach languages
- Learn languages
- Time zone
- Learning focus
- Comments

Hide Title, Status, and any technical helper fields through **Edit form → Edit
columns**. Keep Time zone visible; make it optional during #5 implementation and
remove mandatory-time-zone validation at the same time. Hiding a column from a list
view does not hide it from the New item form.

Language lookup fields must allow multiple selections and must use the
Language catalogue values. Do not replace them with free-text fields.

For the self-registration behavior, Power Apps configuration, and Teams
sharing, follow [POC-03 participant self-registration](POC_03_PARTICIPANT_SELF_REGISTRATION.md).

## Participant submission flow

Historical tested baseline below requires time zone. Do not use this as the new
contract: #5 must allow empty time zone, and extend the interest check for cultures
when those lookups are added. A supplied time zone must still be a valid active
catalogue value. Preserve existing test evidence separately from those changes.

The original automated cloud flow used:

1. SharePoint trigger **When an item is created** on `Participants`.
2. Condition:

   ```text
   (Teach languages is not empty OR Learn languages is not empty)
   AND Time zone is not empty
   ```

3. If true, set Status to `Active`.
4. If false, set Status to `Needs review`.
5. Use the trigger item ID when updating the item.
6. Target: if a Time zone is supplied, confirm it is active in the catalogue;
   an empty value is valid and does not prevent registration/discovery.
7. Send an exception notification only when review is needed.

The form saves before the flow runs. Therefore incomplete submissions are
saved and then marked `Needs review`; use Power Apps validation later if the
experience must block saving before submission.

Do not use **Get file content** or parse the language seed JSON in this flow.

## Time zone

Create a **Time zone catalogue** with the imported canonical values. The
catalogue should contain `Title` (display label), unique indexed `IANA ID`,
optional `Windows ID`, and `Active`.

Target: in Participants, make `Time zone` an optional single-value lookup to the
catalogue. Power Apps renders it as a controlled dropdown. Location or city is
deferred and is not part of the current registration form or schema.

## Sharing through Teams

After saving and publishing the app:

1. Share it with the intended Team/security group or the organisation.
2. In Teams, open the target Team and channel.
3. Select **+ → Power Apps**, choose the app, and save the tab.
4. Pin the tab or announce it in the channel.

Adding the Teams tab makes the app discoverable; it does not replace app or
SharePoint data-source permissions. The existing direct-connector app requires
Participants access and is not approved for wider rollout. POC-18 is split into
prerequisite assessment (#39), isolated proof (#40) and registration integration
(#41). No replacement architecture is selected. Flag and verify every required
permission/configuration before implementation; do not remove current test access
before a replacement is validated. See [the staged plan](POC_18_PARTICIPANT_ACCESS.md).

## Future lists

Create these only through their own implementation issues:

- Matching Cycles
- Groups
- Group Members
- Cycle Statistics

The future statistics page must expose aggregate, non-identifying results. It
must not expose participant names, email addresses, or membership details.

## Baseline limits and deferred fields

The implemented baseline does not yet contain the approved Culture catalogue
and culture fields. Their target contract is #46 and implementation is #5.
Do not interpret their absence as exclusion from the revised MVP.

Still excluded or deferred:

- Location catalogue
- Required native SharePoint Location input
- Consent confirmed
- Participant Role
- Required participant-entered Email

City/location derivation and optional language level remain Later. Controlled
culture sharing/interests are approved target MVP fields, not deferred enrichment.

For the complete rationale and change-control rules, see
[CURRENT_DESIGN.md](CURRENT_DESIGN.md).
