# Current design source of truth

This file records the current agreed product and SharePoint design for the
Tandem proof of concept. It is the design reference for implementation work.

## Authority and change control

- This file is the source of truth for the current schema and product decisions.
- `docs/IMPLEMENTATION_PLAN.md` defines the delivery sequence.
- GitHub issues define the work for each ticket and its acceptance criteria.
- The old `tandem_app` repository and the DOCX files under
  `docs/reference/` are reference material only.
- If a new decision conflicts with this file, update this file in the same PR
  before implementing the conflicting change.

Every implementation ticket must:

1. Read this file before changing the schema, flow, or user experience.
2. State which sections it implements in the PR description.
3. Avoid reintroducing anything listed under “Removed from the current design”.
4. Update this file in the same PR when the product decision changes.

## Product boundary

The MVP helps colleagues register language preferences, discover potentially
compatible people or groups, and decide themselves whether to connect. The
system may validate data, filter opportunities, rank suggestions, send
notifications, and maintain status. It must not automatically decide that two
people are a match or place them into a group without participant action.

SharePoint is the operational database. Power Automate handles validation and
enrichment. Later matching logic can read approved participant data and write
proposed groups for review. A shared statistics page may show aggregated,
non-identifying results to participants.

## Current SharePoint schema

### Language catalogue

This is one of the controlled catalogues required by the current registration
design.

| Column | Type | Use |
|---|---|---|
| Title | Single line text | Canonical language name |
| ISO code | Single line text | Required, unique, and indexed ISO language code |
| Aliases | Multiple lines | Search or display aliases |
| Active | Yes/No | Allows a language to be retired without deleting history |

Participants select languages from this catalogue through lookup fields. They
may select multiple values in both language fields.

### Time zone catalogue

This catalogue is imported and maintained manually.

| Column | Type | Use |
|---|---|---|
| Title | Single line text | Display label shown in Power Apps |
| IANA ID | Single line text | Required, unique, and indexed canonical identifier |
| Windows ID | Single line text | Optional compatibility identifier |
| Active | Yes/No | Allows a time zone to be retired without deleting history |

Participants select one active value through the Power Apps dropdown; they do
not type a time zone.

### Participants

| Column | Type | Current rule |
|---|---|---|
| Title | System text | Hidden from the participant form; not user-maintained |
| Participant account | Person or Group, single | Required and unique; authoritative identity |
| Teach languages | Lookup to Language catalogue, multiple | Optional individually |
| Learn languages | Lookup to Language catalogue, multiple | Optional individually |
| Time zone | Lookup to Time zone catalogue, single | Required; selected in Power Apps |
| Learning focus | Multiple lines | Optional context |
| Comments | Multiple lines | Optional context |
| Status | Choice, flow-managed | `Active` or `Needs review` in the current POC |

The participant form must not ask users to type an email address. The Person
field is the identity source. A hidden email helper may be retained only if a
later automation genuinely needs it; it must be populated by the flow and not
be a participant input.

`Created` and `Modified` are SharePoint system columns. Leave them system
managed; do not create replacement columns or require users to edit them.

### Future lists

These are later delivery items, not part of the initial participant setup:

- Matching Cycles
- Groups
- Group Members
- Cycle Statistics

The statistics page should use aggregated values and avoid exposing the
Participants list or personal details.

## Time-zone policy

Participants choose one time zone from the controlled Time zone catalogue.
This is the authoritative value for matching and reporting. Location or city is
out of scope for the current POC. A later enhancement may add it as optional
context, but it must not replace the controlled time-zone selection.

## Participant submission flow

The current validation rule is:

```text
(Teach languages is not empty OR Learn languages is not empty)
AND Time zone is not empty
```

Expected behavior:

- Trigger: SharePoint **When an item is created** on `Participants`.
- If the rule is true, set `Status` to `Active`.
- If the rule is false, set `Status` to `Needs review`.
- Use the trigger's item ID when updating the item.
- Validate that the selected time zone is an active catalogue value.
- Do not use a file-content action or parse the language seed JSON in this
  participant submission flow.

Language seed JSON is used only when importing or maintaining the Language
catalogue. It is not the source of participant submissions.

## Visibility and manual work

Participants should use the Power Apps form to register and maintain their own
profile. The app filters its gallery to the signed-in user's unique
Participant account and locks that control. The form shows the required time
zone lookup.

This app filter is a user-experience rule, not a SharePoint security boundary.
Because Participant account remains unique, SharePoint's built-in item-level
permission setting cannot be enabled. Users with direct list permissions may
still see other rows in SharePoint. Strict row privacy requires a later custom
permission flow or a data source with row-level security.

Hide system and flow-managed fields from the participant form, including Title
and Status. Do not expose the Participant account people picker for choosing
another colleague.

Automation should handle validation, identity enrichment, time-zone lookup
validation, status updates, notifications, and repeatable checks. People still
decide whether to connect, accept or decline requests, arrange meetings, run
the exchange, approve tenant changes, and handle exceptional cases.

## Explicitly removed from the current design

Do not add these back unless a new product decision is recorded in this file:

- Culture catalogue
- Location catalogue
- Required native SharePoint Location input
- Consent confirmed field
- Participant Role field
- Participant-entered Email as a required registration field

Culture-related concepts may still appear in the older product reference
documents, but they are not part of the current SharePoint registration
schema.

## Deferred optional profile enrichment

After the registration and matching core is stable, a later ticket may add
optional profile context such as city/location, culture interests, or other
free-text information. Those fields must be reviewed for privacy, matching
value, and form usability before being added to the SharePoint schema.

## Implementation checklist

- [ ] Validate the SharePoint schema against this file.
- [ ] Confirm the participant form hides system and flow-managed fields.
- [ ] Confirm the language lookup fields allow multiple controlled selections.
- [ ] Confirm Time zone is a required single-value lookup to the Time zone catalogue.
- [ ] Implement and test the submission flow rule.
- [ ] Add later lists only through their own GitHub issues and PRs.
