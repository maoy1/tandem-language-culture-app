# One-time matching-workbook migration v2.0.0 — issue #48

Ticket: https://github.com/maoy1/tandem-language-culture-app/issues/48
This Python bundle is NOT a Power Automate/Solution ZIP. Keep both .py files and profile-value-map.json together. Python standard library only, no pip install/server/schedule. Existing registration-v1 files remain unchanged history.

## What changed

Use the **matching-in-progress workbook**, not the original registration export, as the source of both participants and groups. The owner approved:

- Read all three current tabs: `active` → Active, `paused` → Paused, `non active` → Inactive. Active starts OpenToConnections=Yes; paused/inactive start No. Existing saved profiles remain unchanged during optional Apply.
- Exclude empty/safety-copy tabs completely. The provided inspection copy is not fully anonymised; do not send identified versions or private output files to the assistant.
- Start groups **Closed**, including review candidates; do not infer that a group ended just because known members left.
- Hold the oversized language groups of 4 and 5 for manual review. Do not expand the normal 2–3 capacity rule or silently drop members.
- Leave the remaining ambiguous accounts/fields for one-time owner correction.

## Prepare locally — Git Bash, needed first

From `C:/projects/small_projects/tandem-language-culture-app`, run:

```bash
python artifacts/participant_import/python/v2/import_participants_once.py \
  --workbook "C:/private/matching.xlsx"
```

Replace that file with your private matching workbook, containing the identities. Using the noemail inspection copy cannot restore missing emails. For a downloaded portable bundle, run `python import_participants_once.py --workbook "C:/private/matching.xlsx"` from its extracted folder. `python --version` should be 3.10+; the existing project `.venv/Scripts/python.exe` can replace `python` if needed. No cmd launcher is used.

A new `Tandem-import-<timestamp>` directory is created beside the workbook. It contains:

| File | Purpose |
| --- | --- |
| participants.csv | Email in Participantaccount; supported profile fields; unique ImportKey and original sheet/row/ID for traceability. |
| groups.csv | Stable MigrationKey, source group name, proposed type/focus/capacity, Closed state and ImportApproved Yes/No. |
| memberships.csv | Group MigrationKey → ParticipantRef/ImportKey links; proposed Active/Left/REVIEW status and source evidence. |
| manual-review.csv | Missing/conflicting/duplicate accounts, unmapped profile text and conflicting source statuses. |
| group-review.csv | Snapshot of the groups needing review, including oversized groups and uncertain memberships. Edit the authoritative groups.csv/memberships.csv, not just this report. |
| summary.json | Aggregate counts only. No SharePoint records have changed. |

The source workbook is never modified. Output folders are new and are never overwritten. Unrelated cached external-link parts are ignored and never followed; formulas in imported cells are refused. Formatted blank tails and the safety-copy worksheet do not become participants.

**Start with SkipRows=0 for this different source.** Optional `--skip-rows 206` skips the first206 actual participant records across active → paused → non active, not206 rows in each worksheet and not206 original registration responses. Use it only for unchanged append/order semantics. `--scope active` is available for a deliberately active-only load; default is all three. Do not use the safety copy via --sheet.

## Review the prepared files

### Participants

- Check Participantaccount is one correct email. Same email twice in the input is flagged; the script does not decide which conflicting person row to keep. Missing/conflicting email stays blank for manual repair.
- Check Teachlanguages/Learnlanguages and culture roles are in the right direction. Known mappings from other source cells are retained if one cell is unclear. Source learning I, sharing K and focus J replace the initial export's P/Q/R/N positions.
- Name fills Title, otherwise email. No fabricated account IDs. Explicit concrete language-name lists can be mapped; unknown prose/alternatives go to review rather than fuzzy guesses. No culture inferred from a language, country/city or department.
- Check Active/Paused/Inactive and Open Yes/No; active-sheet outcome notes conflicting with the tab are flagged for review. The script does not silently apply 'change group', future pause or deletion instructions from organiser prose.
- Keep ImportKey unchanged because memberships reference it. SourceID is an old response key, not a SharePoint Participant ID. Duplicate source IDs get separate row references and a review flag. If you remove a participant row, remove/fix its membership references too.
- Timezone remains blank; comments/private organiser remarks, group-size preferences, historic registration dates and notification suggestions are not copied. Validation Status remains owned by #61/#81, never forced Active.

### Groups and memberships

- Confirm each group is the intended actual group. Group cells separated by `|`, `;` or newlines create separate links. Full group labels are retained: reused letter codes with different focuses are not automatically merged. Similar labels such as a 'learning group' suffix can need manual consolidation; preserve one intended MigrationKey and update its membership rows explicitly.
- `active` + source outcome `active - matched` proposes Active membership. Waiting-list rows with no group create no membership. Other active outcomes and paused assignments propose REVIEW, not automatically Active/Left. `non active` uses 'Group that they left' and proposes Left.
- Leave uncertain membership REVIEW until you decide Active or Left. Left stays historical; a paused profile does not automatically leave a group.
- Check ExchangeType, LanguageFocus/CultureFocus and Capacity. Capacity is not the old participant size preference. Language must be2/3; Culture/Combined2–10; capacity cannot be below Active count. Unknown type/focus is blank for review. Entire unsupported groups remain in the files, not partially imported.
- `ImportApproved=Yes` means structurally suitable for optional Apply, **not** proof that accounts resolved or native behavior passed. Approved groups still require every referenced participant to resolve and every membership to be Active/Left. Review-only/oversized/historical-only candidates start No. After correcting a supported candidate, explicitly set Yes. Do not set Yes to bypass capacity or member guards.
- Groups start Closed. The importer does not permit Open; use normal group controls after review. Historical-only groups remain No/Closed until you decide their actual lifecycle; Ended can be explicitly selected in the reviewed CSV, never inferred.
- JoinedAt/LeftAt are blank for your historical date corrections. If unknown, optional Apply records the actual migration timestamp and documents it as import-time recording, not the original join/leave time. Source registration Date is not treated as a membership date. Supplied dates must use ISO8601 with a UTC offset; LeftAt cannot precede JoinedAt, and Active membership must have blank LeftAt.
- Keep CSV headers unchanged, multiple lookup labels separated by `; `, and save as CSV UTF-8. Formula-like text is escaped in local CSV and round-tripped by the script.

Source structure inspection, with identity cells skipped:217 participant rows (130 active,5 paused,82 non active),32 group candidates,76 links (48 Active proposals,20 Left,8 REVIEW).15 group candidates pass structural preparation;17 are held for review. These are source-row/candidate counts, not distinct resolved-account or successful-import counts. No identified workbook or raw output needs to be shared.

## Saving to existing SharePoint lists

Preparing files is immediately usable for private review/manual participant correction and requires no new authentication. It does not itself create SharePoint rows. Person/lookup cells are typed fields: email/labels in CSV are not yet saved account/lookup IDs. Native grid-paste resolution remains unverified. Keep existing Participants, Groups and Group Members schema; do not create replacement text-column lists from CSV.

**Groups cannot be made operational just by pasting groups.csv.** The app requires a committed SourceRequestId and canonical membership episodes. Use the optional supported upload below when an existing approved token is available, or keep the group bundle prepared pending that one-time upload. Do not invent IDs or mark SetupComplete manually on unlinked groups. Account/profile corrections can be made manually, then rerun the reviewed bundle to resolve existing participants.

## Optional direct combined Apply — existing approved authentication only

Native Python authentication and actual list writes remain NOT RUN. Apply requires an existing tenant-approved, delegated SharePoint-audience owner token in environment variable `TANDEM_SP_ACCESS_TOKEN` (or --token-env NAME). The script does not acquire credentials, create app registrations, request consent or add a licence/connector. A Power Automate connection/browser sign-in is not automatically a Python token. Do not introduce a new auth method just to bypass an unverified prerequisite.

After reviewing the combined CSV folder, with that token already set locally:

```bash
python artifacts/participant_import/python/v2/import_participants_once.py \
  --prepared-bundle "C:/private/Tandem-import-<timestamp>" \
  --apply --output "C:/private/matching-apply-01"
```

Apply order:

1. Verify current owner authentication, the unique Participantaccount Person field and active catalogues; create missing profiles or resolve existing ones without editing them. Account ensureuser may register a site user; no role assignment/sharing/group-permission API is called. Bad/unresolved accounts remain for manual correction. Unknown participant writes stop before group work.
2. Verify actual group/member/request unique keys and available native reader headroom (profiles500,groups100,memberships2000,requests500). Resolve each approved group's ParticipantRefs to actual existing Participant IDs. Missing members, duplicate resolved people, invalid dates/focus/capacity and REVIEW status prevent that whole group's writes; other supported groups can continue.
3. Create migration-labelled **Connection Requests** source/episode records, then Groups and Group Members. These attest imported historical membership; they do not claim an in-app invitation/response or an original joining order. No Pending approval action is created by the script. The first two linked people supply a technical Personal source; later members have Group episodes. There is no group leader/contact role.
4. Use actual numeric SourceRequestId, `history:request:<id>` terminal keys and exact `request:<id>:participant:<id>` membership keys so current readers and self-service actions can recognise them. Keep group SetupComplete=false until every saved link/request/status has been reread and verified, then publish true using the exact observed ETag. No wildcard patching.
5. Preserve already completed imports and subsequent member/app edits. Do not automatically repair or append to a partial migration. A failed/ambiguous write stops the run with private journal evidence; reconcile before repeating. There is no automatic retry, rollback, deletion or update of existing participant/group memberships. Patches only finalise newly created, migration-owned records.

**Visible history implication:** the current Requests screen may show these Accepted migration relationships. Database Title/keys identify the migration, but the current app does not show those tags. This is not proof that the participants clicked Accept. No notification/email send action exists in this script; any independently enabled external event automation is outside this utility and must be considered by the owner before live loading.

Apply writes `apply-results.private.json` and `group-results.private.json`. They contain actual IDs and must stay local. Journals are flushed before writes; summary counts distinguish confirmed creates from attempts. UNKNOWN/stopped/partial results may have created earlier rows. Never interpret zero confirmed creates as proof of zero effects after an unknown response.

`complete` means every selected row/group has a terminal processed result, not that all candidates were imported; MANUAL_REVIEW groups remain. Check outcome counts and private row/group journals. Review/import records do not certify ordinary-participant access or wider release.

## Delegated acceptance / evidence

Prerequisites: reviewed version2 bundle, synthetic/current allowed accounts, existing approved auth and the existing native list schema. Missing auth/access/fixture is BLOCKED, not PASS. No repeated flow imports or old-flow switch cases are required. Use a separate output directory for every test.

- [ ] Prepare the actual private matching workbook with no network: expect all three current tabs, no backup/blank-tail rows, source217 candidates if unchanged, all original source references retained, zero writes. Return only summary.json.
- [ ] Fix a missing account and a group/membership REVIEW locally; re-read --prepared-bundle without --apply and confirm links/CSV corrections remain. Broken/duplicate ImportKey or orphan references must fail before any writes.
- [ ] Apply a supported2/3-member group: verify Person/lookup IDs, Closed group, canonical source/member keys, actual migration timestamps, requests committed before SetupComplete publication. Check My groups for every Active member; no group should enter Discovery while Closed. Native result NOT RUN.
- [ ] Replay after changing group title/state or leaving through the app: completed import is preserved; no duplicate/rejoin/overwrite. Normal Leave and allowed management should recognise canonical episode links. Native result NOT RUN.
- [ ] Oversized language group, missing member, unknown focus, paused REVIEW, foreign/live request or invalid date: whole group left for review, no half-roster publication. Former members stay Left; paused is not auto-left.
- [ ] Interrupted/lost write: stop, preserve journal, leave group unpublished when possible and reconcile. Replaying a partial migration must not silently repair or duplicate it. Native result NOT RUN.
- [ ] Current Requests screen after migration: verify Accepted history implication and no malformed global records; preserve ordinary-user privacy/access acceptance as deferred.

Cleanup: preserve original matching workbook, corrected bundle and private journals. No schema/permission cleanup, bulk delete or automatic rollback. Old Power Automate importer remains failed history and must not be Applied. No further flow retest is required for this Python rewrite.

Local generated-data evidence accompanies this bundle. Native auth/apply/My groups/Leave/Requests behavior still needs tenant execution. Existing core/app flow definitions and shared #81 schema/rules/builds are unchanged; the one-time adapter produces their existing committed-row contract rather than creating a second deployed validator.
