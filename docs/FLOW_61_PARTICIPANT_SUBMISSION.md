# Participant submission validation — #61

Status: **In progress, preparation**. No replacement package or live flow change yet.
The existing flow has bounded REG-014/015 owner evidence; its current exported
definition is required before preserving trigger, reference and connection mapping.
No connected tool can read that tenant flow here; both local checkouts were searched.

## Inputs, validation and outputs

The existing SharePoint created-or-modified event provides the Participants item
ID. Read that current saved item. Trigger fields are not authoritative profile
values. Actual list/field IDs are verified in tenant_schema_mapping.json (#66).
participant_submission_contract.json records the target machine-readable contract.

- A required existing Person account plus at least one of the four language/culture
  offer/interest lookups is valid. Culture-only and share-only are supported.
- Resolve every supplied lookup ID against its mapped catalogue and require Active.
  Reject unknown/inactive IDs; an empty optional Time zone is valid. A supplied
  Time zone must resolve. Do not validate display text as identity or lookup ID.
- Keep participation/openness independent. Paused, Inactive and No do not cause
  validation failure and must survive edits/corrections unchanged.
- Valid -> Status Active; invalid -> Status Needs review. Write **only Status**,
  only when changed. Never use a full-row update that maps identity or selections.
- Failed/malformed/incomplete reads fail the run; do not convert them into a
  successful validation or silently mark a profile invalid. No new output column.
- Protect the Status-only update against edits after the current-item read. Exact
  version/conditional-write implementation must be inspected in the export; no
  serialization or race-safety claim follows from the old no-op test.
- Read back a necessary write. Follow-up event must skip it when unchanged.
  No group/member/request changes, rejoin, reopening or catalogue writes.

## Package and cutover gate

1. Obtain existing flow Package (.zip), leaving the working flow unchanged.
2. Inspect trigger operation, event/site/list/ID references, connection mapping,
   current validation/update payloads, error behavior and app feedback binding.
3. Generate legacy import ZIP, readable definition, mapping and local checks.
   Measure all action definitions and maximum nesting; reject above 500 / 8.
4. Provide exact import/cutover instructions after source inspection. Do not
   import a second enabled validator or silently overwrite the working flow.
   Retain original export for recovery; no atomic rollback promise.

Existing SharePoint connection/tenant metadata HTTP capability was exercised by
#66. No new connector/licence/grant is proposed. Actual production binding and
current flow permissions remain source/import verification gates.

## Target tenant acceptance handover — not yet executable

Account: existing permitted owner/synthetic fixtures; ordinary-user access remains
deferred. Version: **no target package yet**, so these cases remain NOT RUN.
Capture original item ID, identity, selections, Comments, Status and availability.
Use existing test profiles; never delete a real profile to force a new identity.

1. Valid language-only, culture-only and share-only profiles, including blank zone:
   create where a permitted distinct fixture exists, otherwise record creation
   blocked; edit existing profiles normally. Current item becomes Active.
2. Isolated test profile with all four empty: direct-list save bypasses App guard,
   becomes Needs review; follow-up write skipped. Restore useful selections;
   becomes Active once, then follow-up skipped. App guard is already #5 accepted.
3. With an isolated catalogue fixture, select it while active, then disable it and
   edit the test profile: Needs review. Unknown-ID negative test requires a safe
   supported injection/harness; don't corrupt live catalogue rows or fabricate a
   pass when SharePoint rejects the invalid lookup before validation can run.
4. Set Paused/No, edit Comments and save; repeat with Inactive. Match item ID and
   run reference; participation, openness, identity, selections and unrelated data
   remain unchanged. Only necessary Status patch occurs (PAR-002/003, REG-014).
5. Already matching Active and Needs review: both update branches skipped. Force
   each necessary Status correction on a permitted test item; observe one write
   followed by no-op. Repeated writes without user edits fail REG-015.
6. Read failure/concurrent edit: failed read or conflict never reports successful
   validation. Exercise only an isolated supported harness; no permission changes
   or deliberate production outages. Record untestable variants explicitly.

Expected evidence: package/build ID, item ID, trigger event/run reference, relevant
action status/changed-only payload, saved Status and preserved fields; redact
employee identity in repository artifacts. No exact run/version is invented.
Failure: preserve draft/profile evidence, identify first failed action. Sustained
self-triggered writes require stopping the new validator and restoring the prior
working flow through the documented cutover path.
Cleanup: restore profile/catalogue fixture originals and check final validation;
don't delete group/member rows. These detailed tests follow the owner's integrated
build-first priority; a delivered package can await scoped runtime results.

## Boundaries

REG case families retain historical partial results in TEST_RUNS.md. App #5/#6
acceptance does not certify catalogue enforcement or asynchronous validation
feedback. Inspect the existing feedback binding before changing UI. #41 protects
registration access; #7/#10 consume availability; #25 owns operational group
side-effect integration. Their tests are retained, not passed by this ticket.
