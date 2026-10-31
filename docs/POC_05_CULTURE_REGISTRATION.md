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

### Confirmed existing flow and safe edit handling

The owner-provided Condition code checks Teach OR Learn, then requires a time
zone for Active. Culture selections are ignored. Three branches unconditionally
update Status and rewrite Participant account from Created By through Resolve
person. This behavior must be replaced, not carried into edit validation.

First add SharePoint **Get item**, named **Read participant**, immediately after
the current trigger. Select the existing site and Participants list, and use
the trigger's **ID** dynamic token for Id. Leave Limit Columns by View unrestricted
so validation fields are available. This uses the existing SharePoint connection;
successful action/read access is still a tenant check, not assumed from editing.

Use that current item's fields for the selection Composes and validation, not a
stale queued trigger payload. The trigger supplies only the item ID for retrieval.
Do not route read failures to an Active update or success response.

Owner-provided Compose code confirms these existing tenant keys: Teachlanguages,
Learnlanguages and Timezone. Its runAfter references Get_item; use that observed
internal action name in expressions even if the display name is Read participant.
Canonical schema names differ in casing; do not recreate/rename existing fields
to match the proposal. Existing identity updates reference Participantaccount.

| Compose | Replacement input in fx editor (no leading @) |
|---|---|
| Teach selected | `body('Get_item')?['Teachlanguages']` |
| Learn selected | `body('Get_item')?['Learnlanguages']` |
| Timezone selected | `body('Get_item')?['Timezone']` |
| Share selected (new) | `body('Get_item')?['ShareCultures']` |
| Culture interests selected (new) | `body('Get_item')?['LearnCultures']` |

New culture keys match the instructed internal column creation names; verify
the actual read output during tenant testing. Missing/misnamed keys must not be
mistaken for a verified empty profile. Put the two new Composes after Teach
selected and before the outer Condition. Condition/trigger changes follow later.

Before enabling create-or-modify handling, replace the old timezone presence
condition and all unconditional status writes. Validate language OR culture offers/
interests, required identity and the actual catalogue rules. Blank Time zone skips
its optional lookup check; a supplied value must still be valid. Compare computed
Status to the current item's Status and update only when different. Keep the
already-correct branch empty. A necessary Status update can cause a follow-up run;
that run must perform no further write when the result matches.

Compare the scalar **Status Value** in both guards, using the verified expression
`outputs('Get_item')?['body/Status/Value']`. Do not compare the whole Status object
to Needs review. Never map Get item's numeric ID into Participant account Claims.

Preserve existing Participant account; do not replace it from Author/Editor. Remove
unneeded identity-write parameters and their Resolve person dependencies carefully.
If the designer requires the Person parameter, supply the existing item's account
Claims, not the creator's. Leave all unrelated profile fields untouched. This is
identity preservation, not proof of authenticated caller authorization (#18).

Only after reviewing the complete replacement branches should the trigger become
**When an item is created or modified**. Test REG-014–016, ordinary edits, Status
follow-up runs and read failures before treating revalidation as complete. Trigger
configuration/available controls must be verified in the actual designer. No other
flow may rewrite the same identity/status in a conflicting manner; inspect known
related automations when testing convergence.

Leave trigger Concurrency Control unchanged during this guided trigger replacement.
It is not required to implement the change-only write guards, and serialized runs
have not been configured or verified. Microsoft's guidance documents reversal
limitations and bounded waiting-run queues when enabling concurrency control;
review those operational consequences with the owner before choosing that setting.
Do not claim a general lock on users/other flows or #47 acceptance safety from it.
Test follow-up no-op runs and edit convergence under the actual current settings.
After replacing the trigger, verify Get item's Id expression remains
`triggerBody()?['ID']`; downstream references to Get_item remain unchanged.

References: [trigger concurrency guidance](https://learn.microsoft.com/en-us/power-automate/guidance/coding-guidelines/optimize-power-automate-triggers)
and [waiting-run limits](https://learn.microsoft.com/en-us/power-automate/limits-and-config).

Both Update item actions may produce a designer circular-loop warning after the
trigger replacement. A saved flow/warning is not proof of runtime safety. First
use an owner test profile with a known valid language selection and Status already
Active, edit only Comments directly in SharePoint, and inspect the resulting run.
Condition 1 must take its no-change branch; both Update item actions should be
skipped. Then test a required Status transition and its follow-up no-write run.
Repeated consecutive writes of the same Status without new input are a failed
guard: turn off the flow and inspect the current-item Status Value/comparisons.

For the inspected existing layout, outer True / Condition 1 can be reused as the
current **Get item Status Value is not equal to Active** guard. Remove the old
empty(Timezone selected) comparison. Its True writes Active only when needed;
its False must be empty. The old False actions Update item 2 and Resolve person 1
must not remain there: False now means already Active, not invalid time zone.
Remove the Participant account Claims write from Update item 1 and the now-unused
Resolve person action; only the item ID and intended Status change should be
sent. If the connector requires an identity parameter, preserve the current item's
Claims. The outer False invalid-profile path needs a separate Needs review guard;
do not enable a modified trigger while that path still writes unconditionally.

If the old outer False actions were deleted, restore their validation function
with a new Condition there: **Status Value from Get item is not equal to Needs
review**. Its True runs SharePoint Update item using the same site, Participants,
the current item's ID and Status Needs review; False is empty. Set only the Status
payload, preserving Participant account and other profile fields. Resolve person
from Created By is not part of this recovery. If the designer requires account
Claims, inspect that requirement and preserve the current item's account instead.

### Selection predicate

The app rule is feedback, not a trusted validation boundary. In the existing
flow, add Compose actions named **Share selected** and **Culture interests
selected** and insert the corresponding multi-value dynamic tokens from the
current item from Read participant. Inspect real outputs; do not type display names as text.

The current outer Condition has four OR rows comparing each selection's empty()
result with Boolean false. Its equivalent expression is below for inspection
(fx editor, no leading @); no extra Has selections Compose is required.

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

Actual output shapes, catalogue-ID checks and the replacement write branches
still need mapping/testing in the existing flow. The presence predicate above is
not a complete validation flow or deployment evidence. Culture-aware Discovery
is ticket #7.

## Acceptance and record keeping

### Box-by-box diagnostic checks

Inspect the newest run after the test edit, not just the designer. A Condition's
green check means successful evaluation; inspect its actual True/False result.

| Box | Logic/input | Check for a valid profile deliberately set to Needs review |
|---|---|---|
| When an item is created or modified | Existing site and Participants; create and edit events | A new run exists after the edit and its ID identifies the intended test item |
| Read participant / Get_item | Id = `triggerBody()?['ID']` | Success; returned ID matches; returned Status/Value is Needs review for the correcting run |
| Timezone selected | `body('Get_item')?['Timezone']` | Selected lookup or blank; never a mandatory presence gate |
| Learn selected | `body('Get_item')?['Learnlanguages']` | Non-empty lookup array when a Learn language is saved; not a literal field-name string |
| Teach selected | `body('Get_item')?['Teachlanguages']` | Correct array or empty when no Teach selections |
| Share selected | `body('Get_item')?['ShareCultures']` | Correct array or empty; actual new-field keys still require output verification |
| Culture interests selected | `body('Get_item')?['LearnCultures']` | Correct array or empty; same output-key check |
| Outer Condition | At least one of those four offer/interest arrays is non-empty; OR, with Boolean false comparisons | True when the saved Learn selection is present |
| Condition 1 (outer True) | `not(equals(outputs('Get_item')?['body/Status/Value'], 'Active'))` | True when Status is Needs review; False if already Active |
| Update item 1 (Condition 1 True) | Existing site/Participants, Id = `outputs('Get_item')?['body/ID']`, Status = Active only | Succeeded when correction is needed; returned/stored Status Active, identity and selections unchanged |
| Condition 1 False | No actions | Expected skip path when already Active |
| Condition 2 (outer False) | `not(equals(outputs('Get_item')?['body/Status/Value'], 'Needs review'))` | Not reached for a non-empty valid-language profile; True for an empty profile with a different current Status |
| Update item (Condition 2 True) | Same current ID, Status = Needs review only | Runs only when empty-input status needs correction |
| Condition 2 False | No actions | Expected skip path when already Needs review |

Do not send the item's ID into Participant account Claims. No Resolve person from
Created By/Modified By belongs in either update path. On a correcting run with a
saved Learn selection, the expected path is outer True, Condition 1 True, Update
item 1 Succeeded. Any follow-up reading Active must skip another write. If the
current read instead shows a different state, compare item ID and run timestamp.
The first mismatch in this ordered checklist identifies the next diagnostic step;
do not guess from the displayed list Status alone. This is presence/status logic;
full catalogue-ID/Active validation remains outstanding before #5 acceptance.

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
