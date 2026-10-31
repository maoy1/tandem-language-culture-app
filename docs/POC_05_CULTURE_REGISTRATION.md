# POC-05 culture registration and optional time zone

Issue #5. Repository configuration is prepared; tenant setup and tests are NOT
complete. PR #51 merged the contract and test catalogue. #46 stays open for its
remaining decisions. This ticket uses only the approved registration subset.

## Check before live setup

- Confirm the owner can create a list/columns on the existing site, edit the app
  and validation flow, and read the new catalogue through the existing SharePoint
  connection. Use existing entitlements; no premium connector or new service.
- Agree the initial culture labels/keys. Do not infer cultures from nationality,
  manufacture an ISO culture taxonomy or copy real employee data into fixtures.
- Verify actual internal column names before inserting flow expressions. Existing
  columns may have names different from the display labels or schema proposal.
- Inspect whether submission validation handles edits as well as creation. A
  creation-only trigger does not revalidate corrections. Inspect its loop guard
  before switching to a create-or-modify trigger: its own Status update must not
  repeatedly trigger validation. This remains a tenant implementation check.
- Keep the owner/synthetic test audience. Deferred ordinary-user access checks
  still gate wider rollout; this ticket makes no permission architecture change.

These are one-time setup checks. Ordinary registration needs no admin approval.

Owner inspection confirms the current submission trigger is **When an item is
created** (SETUP-20261031-08). Edit revalidation is not established. Inspect the
existing branches and status writes before switching triggers; configure and test
loop prevention along with the culture/optional-time-zone validation update.

## Suggested starter culture values — review before import

[culture_catalogue_proposal.json](../config/culture_catalogue_proposal.json)
contains 85 suggested country/region labels, expanded across Africa, Asia,
Europe, the Americas and Oceania. Examples include Ghana, Kenya, Nigeria, Egypt,
India, Indonesia, Philippines, Vietnam, China, Japan, Brazil, Colombia, Mexico,
Canada, France, Germany, Poland, Ukraine, Australia and New Zealand. The JSON file
contains the full alphabetically ordered list. These are suggested labels, not
an official classification or an exhaustive programme list.

Treat selections as places whose culture a participant wants to discuss from
experience or learn about; do not infer nationality or assume one homogeneous
culture per country. Sharing and interest remain distinct selections. No values
are preselected from the participant's identity. Regional labels can be added
deliberately later, with distinct keys and no automatic parent/child matching.
Avoid a common Other value: it would falsely match unrelated interests. Agree
coverage for the programme audience before launch; do not require a routine
organiser approval just to register with existing values. This proposal is not
imported, and no automated participant taxonomy-maintenance workflow is added.

## SharePoint changes

Use config/sharepoint_schema.json as the desired POC-05 configuration. Its
deploymentStatus explicitly says setup/testing are pending; it is not a live export.

1. Create **Culture catalogue**. Create CultureKey first as single-line text,
   then rename its display label to **Culture key** to preserve the internal name.
   Require Title and CultureKey; enforce unique CultureKey values (indexed).
   Add Active as Yes/No, default Yes. Populate only agreed labels/keys.
2. In Participants create **ShareCultures** and **LearnCultures** as lookups to
   Culture catalogue / Title with multiple values allowed; neither required.
   Then rename their display labels to **Cultures I can share** and
   **Cultures of interest**. Preserve any existing data; do not recreate lists.
3. Edit the existing Time zone lookup: **Require that this column contains
   information = No**. Preserve its catalogue target and single selection.
4. Keep Participant account required/unique and the existing language lookups.
   Do not add a preferred group-size field or Comments notice. Separate
   participation/open-status fields are ticket #6, not this setup.

## Bulk catalogue entry

The workbook [culture_catalogue_import.xlsx](import/culture_catalogue_import.xlsx)
contains the 85 proposed values from the JSON. In Excel select **A2:B86** (data
only, no headers). In the empty Culture catalogue, put Title and Culture key next
to each other in that order, choose Edit in grid view, select the first blank
Title cell and paste. Active is omitted from the paste: its list default must be
Yes. Exit grid view, refresh and verify 85 entries with keys populated and Active
Yes. This method populates the existing list; do not create a second list from
the workbook. If rows already exist, reconcile by Culture key before pasting;
this is not an upsert/import automation. Live paste/row counts remain unverified
until the owner confirms them.

## Power Apps form

Refresh Participants in the Data pane, select Form1, then Edit fields and add
the two culture fields. Preserve the existing identity and own-profile behavior.
Use the generated lookup cards rather than adding text boxes.

For the formulas below, first rename the four classic combo-box controls:
**cmbTeachLanguages**, **cmbLearnLanguages**, **cmbShareCultures**,
**cmbLearnCultures**. These are explicit setup names, not claims about the existing
generated controls. The form must be named Form1; adapt that name if different.

| Culture card | Combo Items | Combo SelectMultiple | Card Update |
|---|---|---|---|
| Cultures I can share | `Choices([@Participants].'Cultures I can share')` | `true` | `cmbShareCultures.SelectedItems` |
| Cultures of interest | `Choices([@Participants].'Cultures of interest')` | `true` | `cmbLearnCultures.SelectedItems` |

On each culture combo set DisplayFields and SearchFields to `["Value"]` and
DefaultSelectedItems to `Parent.Default`. Each culture card Required is `false`.
Refresh and verify the Time zone card Required also resolves to `false`. Keep its
existing typed lookup Update mapping; an empty selection must save as blank.

Choices preserves the lookup ID/value shape, but does not by itself filter
Active catalogue items. Confirm active-option filtering and server validation
against the actual catalogue before acceptance; REG-008 remains unverified.

Replace the Save button's SubmitForm call with this expression. If it has other
behavior, preserve it deliberately; never add a second unconditional SubmitForm.

```powerfx
If(
    IsEmpty(cmbTeachLanguages.SelectedItems) &&
    IsEmpty(cmbLearnLanguages.SelectedItems) &&
    IsEmpty(cmbShareCultures.SelectedItems) &&
    IsEmpty(cmbLearnCultures.SelectedItems),
    Notify("Choose at least one language or culture to share or learn.", NotificationType.Error),
    SubmitForm(Form1)
)
```

Keep existing successful-save navigation. Show failure on **Form1.OnFailure**:

```powerfx
Notify(Coalesce(Form1.Error, "Registration could not be saved."), NotificationType.Error)
```

Do not reset the form after failure. A successful SubmitForm saves the item; it
does not prove asynchronous validation or Discovery integration has succeeded.

## Submission validation changes

The app rule is feedback, not a trusted validation boundary. In the existing
flow, add Compose actions named **Share selected** and **Culture interests
selected** and insert the corresponding multi-value dynamic tokens from the
trigger/current item. Inspect real outputs; do not type display names as text.

After **Teach selected**, **Learn selected** and those two actions, add Compose
named **Has selections** with this expression (fx editor, no leading @):

```text
or(
  not(empty(outputs('Teach_selected'))),
  not(empty(outputs('Learn_selected'))),
  not(empty(outputs('Share_selected'))),
  not(empty(outputs('Culture_interests_selected')))
)
```

These action names are setup requirements; use the designer's actual internal
names if it suffixes them. Compare the result with Boolean `true` inserted
through fx, not the text "true". No Time zone non-empty condition belongs here.

Keep identity verification. Validate selected lookup IDs against their proper
catalogue and Active flag; blank Time zone skips only that catalogue check.
Malformed/unknown/inactive selections must not become validation Active. A failed
lookup/flow must not take a success branch. Preserve unrelated fields in Update
item. Do not reset future participation/open choices during validation (#6).

The precise trigger/edit loop guard and catalogue-ID checks require inspection
of the existing flow; the presence predicate above is not a complete validation
flow and is not evidence of deployment. Culture-aware Discovery is ticket #7.

## Acceptance and record keeping

Run REG-001–009, REG-011–012, with these variants in an isolated fixture:

- Culture sharer only; culture learner only; combined language/culture; language
  only. Save and reopen each, checking stored lookup IDs and all multi-selections.
- Blank Time zone on create and edit; remove an existing Time zone and reopen.
- Empty all four fields: app blocks save and retains input; invalid direct-list
  fixture cannot validate Active. Correcting it must revalidate on edit.
- Invalid/inactive selection, validation-flow failure, and repeat save.

Record app/flow versions, actual results and evidence in TEST_RUNS.md. Local
pytest checks configuration consistency only. Do not mark tenant REG tests PASS
or close #5 until live acceptance is confirmed.

## Microsoft references

The form/selection formulas follow [SubmitForm and form outcomes](https://learn.microsoft.com/en-us/power-platform/power-fx/reference/function-form)
and [classic combo-box properties](https://learn.microsoft.com/en-us/power-apps/maker/canvas-apps/controls/control-combo-box).
