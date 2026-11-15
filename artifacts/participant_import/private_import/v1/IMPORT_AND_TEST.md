# Private participant importer v1 — issue #48

Ticket: https://github.com/maoy1/tandem-language-culture-app/issues/48
Owner overview: https://github.com/maoy1/tandem-language-culture-app/issues/45

Build `625d57bc-cab8-451e-9e4c-5e1f2f79f39c`. ZIP SHA256 `e486f3b3d7195acf6b6d8bd88e20148ad51aa576c81f143fa2f4e44bec732f3e`.
121 action definitions across all branches, maximum nesting 7 (limits 500 / 8).
Local generated-graph regression tests: 105 PASS. This ZIP has not been imported or run in the tenant.

## What this package does

Runs inside Power Automate with the existing standard Excel Online (Business) and SharePoint owner connections. No local runtime, additional connector, licence or external service is needed by the deployed flow. The original workbook and identities stay in Microsoft 365. The assistant does not need the workbook or private source settings.

Dry-run reads the selected table window, extracts a single explicit email from Email / the mixed name-email column, resolves it through SharePoint, preserves existing profiles, and maps reviewed whole-cell language/culture values against current active catalogue titles. Unknown/ambiguous text, missing accounts and empty/reconfirmation-only profiles are per-row exceptions. All responses for a duplicated resolved new account are blocked, including when one response has invalid selections. No fuzzy selection mapping or account invention.

Apply creates only eligible missing profiles. New profiles use ParticipationStatus=Active and OpenToConnections=Yes. It preserves existing profiles and does not write validation Status (#61 owns it). Learning focus is copied; optional timezone stays blank; comments, legacy group sizes, old manual matches, groups, requests and memberships are not imported.

**One-time account effect:** Apply may register a resolved account in the site's user-information store through ensureuser before assigning the Person field. It does not call sharing, permission or group-membership APIs. Failure stops that row before participant creation. No such explicit POST occurs during dry-run. Directory lookup behavior, combined connector execution, protected runtime result collection and history masking still need native verification in the first dry-run.

## First run — owner, needed now

Prerequisites: the two existing owner connections; access to the private Tandem SharePoint Excel table and Participants/catalogue lists; the batch participant validator available for subsequent created rows. Keep this helper owner-operated. No repeated core/app imports or schema setup are needed.

1. In Power Automate **My flows → Import → Import Package (Legacy)**, select **TandemPrivateParticipantImport-v1.zip**, use **Create as new**, and choose your existing Excel and SharePoint connections. This is a legacy package, not a Solution ZIP. If import/save fails, stop and return only the exact sanitized error. It may then be added to your existing Tandem Solution through **Add existing → Automation → Cloud flow → Outside Dataverse**; that move is optional and not a prerequisite for the first run.
2. Open the new **TandemPrivateParticipantImport v1**. On supplied **Read workbook**, privately choose **Location → Document Library → File → actual Excel Table**, in that order, replacing the fx placeholders. Use the same source that passed the v4 read. Save. No new actions or typed Graph IDs are needed. Leave advanced Skip Count expression/top bound and raw-action protection intact.
3. Run **ApplyChanges = No**, **SkipRows = 0**, **ExpectedRows = 206**. ExpectedRows counts rows after skipping; the table header is excluded. The flow makes no explicit participant/account-registration POST in this mode.
4. Open **Import report → Outputs**. Expect a one-element array: matching build, `applyChanges=false`, `rowCount=processedRows=206`, `complete=true`, `createdCount=unknownCount=accountRegistrationAttempts=0`, `identityValuesIncluded=false`. Each data row has READY_CREATE, EXISTING_PRESERVED or BLOCKED with a generic code. `code=OK` means no blocked rows; `COMPLETED_WITH_EXCEPTIONS` means the read/processing completed but some rows need private correction. Count identity resolution as proven only for resolved cases. Do not assume all 206 can be imported.
5. Privately confirm the raw **Read workbook, Private row, Resolve person, Prepared record, Prepared plans** inputs/outputs are hidden in history. **Import report** must remain visible and contain only counts/row numbers/status codes. Never disable security or share private action outputs. Return only **Import report**. If `complete=false`, stop before Apply: its generic code and diagnostics identify the failed stage. `ACCOUNT_LOOKUP_FAILED` can mean an unresolvable, ambiguous, different-primary-email account or a lookup/capability error; do not grant permissions or guess an account to bypass it.

**No Apply run is required before this first dry-run has been reviewed.**

## Apply — after the private dry-run is satisfactory

1. Keep the same reviewed source, mapping/package and row window. If source or catalogue choices changed, repeat dry-run first. The flow rereads current data on every run; it does not claim a file hash or stored approval token.
2. Run **ApplyChanges = Yes** with the same SkipRows and ExpectedRows. Only READY_CREATE candidates are attempted; BLOCKED rows remain exceptions and do not prevent other valid rows from being created. All source rows are prepared before the first write. Apply rechecks the resolved account, current absence and selected catalogue IDs/titles. It may partially complete; there is no automatic rollback.
3. Open **Import report**. Require `complete=true`, `unknownCount=0`; createdCount reports only HTTP201 followed by matching account reread. Existing profiles are preserved. Privately inspect a created Participants row for correct Person/teach/learn/culture/focus fields, Active/open Yes, blank timezone and untouched comments, then confirm #61 validates the row before expecting discovery. Return counts/codes/run reference only, no names or IDs.
4. If any UNKNOWN/UNKNOWN_WRITE appears, stop rerunning Apply. Privately reconcile the indicated data-row number against Participants before another attempt; failed/ambiguous responses are never reported as created. There is no automatic POST retry. BLOCKED with ACCOUNT_REGISTRATION_FAILED has no confirmed participant creation; check that row's sanitized failure before further attempts.

## Repeat imports and new appended rows

- Read all: **SkipRows=0**, ExpectedRows=current total (maximum250 per window). Existing accounts are skipped, never overwritten; changed Excel values do not update those profiles. There is no destructive reset/re-import-from-scratch mode.
- Only appended rows: **SkipRows=206** starts at data row207. If total is220, use ExpectedRows=14. Source ordering must remain append-only. If earlier rows moved or changed, use read-all.
- Exactly206 rows and SkipRows206: ExpectedRows=0; expect complete=true, zero processed/created counts. Header checks cannot be established from an empty window.
- More than250 remaining rows / paging / wrong expected count is refused, never silently truncated. Choose an appropriately reviewed bounded window/source, not an incomplete first-page import.
- Profiles created previously then edited through the app remain unchanged on replay. No per-run watermark is stored.

## Delegated acceptance — not required from the owner before first dry-run

All cases below are NOT RUN in the tenant. Technical testers need approved helper access and synthetic fixture accounts/workbook, prepared centrally under #45. Missing fixture/access is BLOCKED. Use this exact version/build and preserve sanitized reports.

- [ ] Dry-run with one valid fixture and one unmapped fixture: READY_CREATE1/BLOCKED1, zero explicit POSTs and participant rows unchanged.
- [ ] Apply the same fixtures: CREATED1/BLOCKED1; privately verify saved values and #61 outcome. Complete-with-exceptions is expected.
- [ ] Replay after app editing: EXISTING_PRESERVED1, zero new participant writes; edited values unchanged.
- [ ] Duplicate same-account responses, including one invalid selection: both blocked, zero creates for that account.
- [ ] Mixed name/email fallback, conflicting/missing address, unresolved directory account: exactly one address accepted; ambiguous/unresolved rows blocked, no guessed person.
- [ ] Culture-only profile: culture roles saved, no inferred language/timezone/group-size value.
- [ ] Appended-row window206/remaining, end-of-table206/0, changed-order guidance, wrong counts/headers/paging: correct absolute data-row numbers or bounded failure, no unreviewed writes.
- [ ] Lookup/ensure/create failure, ambiguous POST response, concurrent existing account and catalogue change: no false CREATED result, no duplicate/overwrite; UNKNOWN requires private reconciliation.
- [ ] History/aggregate privacy: verify masked raw actions, visible report with no identities. Ordinary participant privacy/access remains deferred; owner tests do not establish it.

Cleanup: preserve workbook, original exports, reports and legitimate profiles. Disable/remove only the disposable importer when finished. Do not delete participant history or change permissions as cleanup. Historical group/membership migration remains outside this participant-only load and #48 stays open.

Official references: [SharePoint Resolve person](https://learn.microsoft.com/en-us/connectors/sharepoint/#resolve-person), [secure history limitations](https://learn.microsoft.com/en-us/azure/logic-apps/set-up-security-permissions#secure-data-in-run-history-by-using-obfuscation), [runtime result collection](https://learn.microsoft.com/en-us/azure/logic-apps/expression-functions-reference#result), [EnsureUser](https://learn.microsoft.com/en-us/previous-versions/office/sharepoint-visio/jj245233%28v%3Doffice.15%29).
