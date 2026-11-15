# One-time Python participant import v1 — #48

Ticket: https://github.com/maoy1/tandem-language-culture-app/issues/48

The owner explicitly approved a local script for this one-time migration. It is not required by the deployed participant app. Python standard library only: no pip install, server, schedule, extra licence or new flow. The original workbook and account values stay on your computer. No identified workbook was read by the assistant.

## Start here — no sign-in or tenant writes

1. Extract/keep this folder together. Use a local downloaded/synced copy of the original workbook, containing the emails. Do not send it to the assistant.
2. Drag that workbook onto **Run-prepare.cmd**. The launcher uses the existing project Python environment if present, otherwise Windows `py -3` (Python 3.10+). This only prepares files.
3. A new **Tandem-import-<date/time>** folder appears beside the workbook. Open **participants.csv** in Excel: `Participantaccount` contains the extracted email; the other columns contain mapped values. The source workbook is unchanged. Earlier output folders are never overwritten.
4. Open **manual-review.csv** for the source data/Excel row number, missing/conflicting email, duplicate email, and any unmapped original language/culture text. Correct the local participants.csv or original source as you prefer. Every selected source row remains in participants.csv, including rows needing manual work. No account has been resolved merely because an email is present.
5. For manual loading, use your existing **Participants** list and its existing Person/lookup columns. In **Edit in grid view**, align the visible columns with the CSV before copying values from Excel; start with one row. SharePoint must accept the account email and lookup labels as their actual types. If it rejects a Person/multiple-lookup cell, select that value manually in the existing field. Paste support for these tenant-specific fields is NOT VERIFIED; do not assume a pasted label is a saved lookup. Do not create a new list from CSV: that can create text columns instead of the required Person/lookups. Check one saved row before the remaining load. Grid pasting does not deduplicate against existing profiles: skip accounts already present. Existing-account deduplication is automatic only in the optional direct Apply below.

PowerShell alternative from this extracted folder:

```powershell
python .\import_participants_once.py --workbook "C:\private\original.xlsx"
# Only data rows after the original 206; header is not counted:
python .\import_participants_once.py --workbook "C:\private\new-version.xlsx" --skip-rows 206
# Choose a new output directory explicitly:
python .\import_participants_once.py --workbook "C:\private\original.xlsx" --output "C:\private\prepared-01"
```

For multiple worksheets, add `--sheet "Sheet1"` (use the actual name). Skipping is positional: use 0 after sorting/inserting/deleting previous data rows. No implicit watermark is stored. This Python reader supports up to 10,000 data rows, unlike the temporary flow's 250-row window. Formula/external-link workbooks are refused; use a values-only source export.

## Field mapping

| Existing Participants column | Prepared value |
| --- | --- |
| Participantaccount | Single explicit email from Email, or the mixed name/email field. The same address in both is accepted; conflicting addresses remain blank for manual correction. |
| Title | Name, otherwise email. No fabricated identity. |
| Teachlanguages | Known sharing languages from R. |
| Learnlanguages | Union of known learning languages from P and Q. |
| ShareCultures / LearnCultures | Explicit reviewed culture selections in those same share/learn source cells. No country inferred from a language. |
| Learningfocus | N, as text. |
| ParticipationStatus | Active, per owner decision. |
| OpenToConnections | Yes, per owner decision. |

Lookup CSV cells contain catalogue **labels**, separated by `; `. The optional direct Apply resolves current active labels to real lookup IDs. A recognised whole-cell interpretation is used only if reviewed; unknown cells are preserved in manual-review.csv. Valid mappings from other cells are still included. Thus partial profiles may need your manual completion and may not become discoverable until #61 validates them.

Timezone stays blank: no inference from city/country. Comments/old organiser notes, historical matches, group-size preferences, groups, memberships and requests are not copied. Validation Status is not forced; the existing #61/#81 path owns it. Excel formula-like text is escaped with a leading apostrophe in CSV exports; the script reverses only its own escape when reading a prepared CSV.

## Optional direct SharePoint upload — only if approved authentication is available

This is implemented but **NOT TESTED in the tenant**. It needs an existing, tenant-approved **SharePoint-audience delegated access token** for the owner, in environment variable `TANDEM_SP_ACCESS_TOKEN` (or `--token-env OTHER_NAME`). A Power Automate connection or browser sign-in is not itself a Python token. The script does not acquire tokens, register an app, request consent, install an authentication module or bypass policies. If you do not already have an approved token method, use the prepared files/manual route; do not create a new registration just for this task.

After privately reviewing/correcting participants.csv, with the token already set locally:

```powershell
python .\import_participants_once.py --prepared-csv "C:\private\prepared-01\participants.csv" --apply --output "C:\private\apply-01"
```

Apply verifies current-user access, the unique Person field and current catalogues before participant writes. It uses the email to `ensureuser` and writes the returned real user ID to ParticipantaccountId. This may register the account in the site user-information store; it does not call sharing, role-assignment or group-membership APIs. Missing/ambiguous/unresolved accounts are left for your manual correction, not fabricated or saved as blank required Person values.

Existing participants are preserved without updates. Duplicate source emails are reported, not arbitrarily merged. A row with some known selections can be created while remaining source selections need manual completion; a row with no mapped selections is left for manual review. Different email aliases for the same person are not automatically merged. Current catalogue choices are read at startup; do not change catalogues during this one-time load.

`apply-results.private.json` records per-row results; it can contain actual participant IDs and must stay private. Write-start evidence is flushed before each participant POST; requests are never automatically retried. `summary.json` is aggregate only. CREATED requires HTTP201 and a matching account reread. UNKNOWN or STOPPED halts further rows: reconcile privately before any rerun. A stopped run can have earlier successful creations; there is no rollback. Re-running after reconciliation preserves existing accounts instead of resetting them. No delete/update/permission/schema API is called.

## What is proven / what remains

- Local synthetic workbook, mapping, mixed-email, CSV safety, partial mapping, skip206, manual-correction roundtrip and fake SharePoint create/replay/failure tests pass; exact test evidence accompanies the package.
- Native Python authentication, actual SharePoint Apply, Person/lookup grid-paste behavior and imported-row validation/discovery are **NOT RUN**. Owner can manually correct the remaining fields as approved. Ordinary-participant access remains deferred.
- The previous Power Automate importer v1 dry-run **FAILED**: source206 rows, terminal outcomes110, ready0, existing2, blocked108, created0; run08584068624644781117257877718CU11. Do not Apply that flow. It is preserved history, not a prerequisite for this script. No further flow retest is requested now.
- After manually/directly saving one profile, check Person/lookup values, Active/open Yes and #61 validation before expecting discovery. Do not set validation Status=Active to bypass missing profile values. Keep source and local results. Remove/disable only temporary import tools when no longer needed; no participant rollback or permission cleanup is performed by the script.

Official references: [SharePoint grid entry and column types](https://support.microsoft.com/en-us/sharepoint/lists/data-and-lists/add-list-items), [SharePoint REST item creation](https://learn.microsoft.com/en-us/sharepoint/dev/sp-add-ins/working-with-lists-and-list-items-with-rest), [EnsureUser](https://learn.microsoft.com/en-us/previous-versions/office/sharepoint-visio/jj245233%28v%3Doffice.15%29).
