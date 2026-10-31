# Tandem SharePoint POC setup

This document is the practical setup guide for the current participant
registration POC. The design authority is
[CURRENT_DESIGN.md](CURRENT_DESIGN.md). If this guide conflicts with it, the
design authority wins.

This guide describes the implemented registration baseline. The approved v0.2
target (#45) adds controlled culture fields and separate
statuses after #46 defines their exact contract. Do not create those columns
from this baseline guide yet. Target time zone is optional; no participant size
preference or Comments notice. Exact Discovery display fields remain undecided;
notifications remain undecided (#49). Catalogue time zone stays; Excel inspection
and migration are the final phase (#48).

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
