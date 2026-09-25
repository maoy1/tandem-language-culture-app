# Tandem SharePoint POC setup

This document is the practical setup guide for the current participant
registration POC. The design authority is
[CURRENT_DESIGN.md](CURRENT_DESIGN.md). If this guide conflicts with it, the
design authority wins.

## Architecture

```text
SharePoint lists = operational database
Power Automate = validation, identity enrichment, and status updates
Future matching logic = discovery and proposed groups
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
| Time zone | Lookup to Time zone catalogue, one value | Yes; required |
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
columns**. Keep Time zone visible and required. Hiding a column from a list
view does not hide it from the New item form.

Language lookup fields must allow multiple selections and must use the
Language catalogue values. Do not replace them with free-text fields.

For the self-registration behavior, Power Apps configuration, and Teams
sharing, follow [POC-03 participant self-registration](POC_03_PARTICIPANT_SELF_REGISTRATION.md).

## Participant submission flow

Create an automated cloud flow with:

1. SharePoint trigger **When an item is created** on `Participants`.
2. Condition:

   ```text
   (Teach languages is not empty OR Learn languages is not empty)
   AND Time zone is not empty
   ```

3. If true, set Status to `Active`.
4. If false, set Status to `Needs review`.
5. Use the trigger item ID when updating the item.
6. Confirm the selected Time zone lookup is active in the Time zone catalogue.
7. Send an exception notification only when review is needed.

The form saves before the flow runs. Therefore incomplete submissions are
saved and then marked `Needs review`; use Power Apps validation later if the
experience must block saving before submission.

Do not use **Get file content** or parse the language seed JSON in this flow.

## Time zone

Create a **Time zone catalogue** with the imported canonical values. The
catalogue should contain `Title` (display label), unique indexed `IANA ID`,
optional `Windows ID`, and `Active`.

In Participants, make `Time zone` a required single-value lookup to the
catalogue. Power Apps renders it as a controlled dropdown. Location or city is
deferred and is not part of the current registration form or schema.

## Sharing through Teams

After saving and publishing the app:

1. Share it with the intended Team/security group or the organisation.
2. In Teams, open the target Team and channel.
3. Select **+ → Power Apps**, choose the app, and save the tab.
4. Pin the tab or announce it in the channel.

Adding the Teams tab makes the app discoverable; it does not replace app or
SharePoint data-source permissions. Users need access to the Participants list
for the SharePoint connector to work.

## Future lists

Create these only through their own implementation issues:

- Matching Cycles
- Groups
- Group Members
- Cycle Statistics

The future statistics page must expose aggregate, non-identifying results. It
must not expose participant names, email addresses, or membership details.

## Removed from this setup

The current design does not use:

- Culture catalogue
- Location catalogue
- Culture interests or culture themes in the SharePoint schema
- Required native SharePoint Location input
- Consent confirmed
- Participant Role
- Required participant-entered Email

Optional profile enrichment such as city/location, culture interests, and
additional free-text context is deferred to a later ticket.

For the complete rationale and change-control rules, see
[CURRENT_DESIGN.md](CURRENT_DESIGN.md).
