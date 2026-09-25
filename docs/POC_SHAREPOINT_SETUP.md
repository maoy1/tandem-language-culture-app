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

Participants register through a SharePoint form or Power Apps form. They do
not receive access to other participant records.

## Current lists

### Language catalogue

Create one controlled catalogue with:

| Column | Type |
|---|---|
| Title | Canonical language name |
| ISO code | Single line text |
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

### Participants

| Column | Type | Participant-facing? |
|---|---|---|
| Title | SharePoint system text | No |
| Participant account | Person or Group, one person | Yes; required and unique |
| Teach languages | Lookup to Language catalogue, multiple | Yes; optional |
| Learn languages | Lookup to Language catalogue, multiple | Yes; optional |
| Location | SharePoint Location | Yes; required |
| Time zone | Single line text | No; derived by flow |
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
- Location
- Learning focus
- Comments

Hide Title, Time zone, Status, and any technical helper fields through **Edit
form → Edit columns**. Hiding a column from a list view does not hide it from
the New item form.

Language lookup fields must allow multiple selections and must use the
Language catalogue values. Do not replace them with free-text fields.

## Participant submission flow

Create an automated cloud flow with:

1. SharePoint trigger **When an item is created** on `Participants`.
2. Condition:

   ```text
   (Teach languages is not empty OR Learn languages is not empty)
   AND Location is not empty
   ```

3. If true, set Status to `Active`.
4. If false, set Status to `Needs review`.
5. Use the trigger item ID when updating the item.
6. Read `Location: City` and derive the hidden IANA time-zone value from the
   repository city mapping when that enrichment is implemented.
7. Send an exception notification only when review is needed.

The form saves before the flow runs. Therefore incomplete submissions are
saved and then marked `Needs review`; use Power Apps validation later if the
experience must block saving before submission.

Do not use **Get file content** or parse the language seed JSON in this flow.

## Location and time zone

Use the SharePoint Location field as the only location input. Do not create
separate Country, Office city, Location catalogue, or Time zone catalogue
columns/lists.

The flow uses the Location City component to derive an IANA time-zone value.
Participants never select a time zone. If the city is not in the repository
mapping, set Status to `Needs review` rather than guessing.

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
- Time zone catalogue
- Location catalogue
- Culture interests or culture themes in the SharePoint schema
- Separate Country or Office city fields
- Consent confirmed
- Participant Role
- Required participant-entered Email

For the complete rationale and change-control rules, see
[CURRENT_DESIGN.md](CURRENT_DESIGN.md).
