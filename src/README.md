# Application code

Production runs in SharePoint, Power Apps and Power Automate under existing
entitlements. No Python runtime, server, additional paid licence, premium/custom
connector, external API or separately hosted service is part of the application.
Local Python schema validators are development tools only.

## Current core build: Discover screen and flow

The owner prioritizes integrated app/flow construction before the remaining
detailed tests. Build a separate **TandemDiscovery** flow from a Power Apps button;
the submission flow continues to validate profiles. Use the existing Participants
list first. Notification/Approvals decisions and setup automation are postponed.

The new expression reference is config/discovery_core_build.json. Unlike the
historical language-only fragment below, it includes culture sharing/interests.
It is still an action fragment, not an importable flow or proof of deployment.
This first build uses existing validation Status. #6 participation/openness,
trusted caller binding and final display projection remain explicit integration
gates; this owner-only build must not be shared as an ordinary-user endpoint.

### Batch 1 — create the app-triggered reader

1. Create an Instant cloud flow named **TandemDiscovery**, with **Power Apps (V2)**
   trigger. Add one Number input named **ParticipantId**.
2. Keep the new flow owner-only and app changes unpublished while construction
   proceeds. Verify its run-only audience before reading data; no new individual
   grants or permission architecture is introduced here. An app-provided item ID
   is a reference, never proof of authorization for ordinary users.
3. Add SharePoint **Get item** using the existing site/connection and Participants.
   For Id select the ParticipantId input from Power Apps (V2) dynamic content.
   Keep the action's internal name **Get_item**, or map subsequent expressions to
   the actual internal name. Do not copy the submission trigger's ID expression:
   this flow has a different trigger/input shape.
4. Save this initial flow. It is a reader scaffold; response and matching actions
   below are required before the app can display Discovery results.

### Batch 2 — load and normalize profiles

1. Add SharePoint **Get items** named **Candidate source** for Participants with
   Filter Query `Status eq 'Active'` and deterministic `ID asc` order. Inspect its pagination
   settings before relying on results. Proposed owner-build bound: fetch at most
   501, with pagination sufficient to retrieve that bound; if more than 500 are
   returned, respond with an explicit limit error, not partial-result success.
   This limit/configuration is not yet verified or approved for wider scale.
2. Normalize the current Get item into one **My_profile** Compose and candidate
   rows into one **Candidate_profiles** Compose matching the fragment's shape.
   Use Data Operations Select for row mapping; the current item can be wrapped
   with `createArray(body('Get_item'))`, then take `first()` of that mapped row.
3. Verified existing field names are Participantaccount, Teachlanguages,
   Learnlanguages and Timezone. Culture creation names are ShareCultures and
   LearnCultures. Map Person Claims as accountId, Person DisplayName as displayName,
   ID as profileId and Status Value as status; never use app email as accountId.
4. Inspect actual read outputs before choosing lookup-ID mappings. Where the
   connector supplies whole ID arrays (for example the field's #Id property), map
   those directly. Otherwise use Select in text mode over lookup objects with
   `int(item()?['Id'])`. Do not silently interpret a misnamed field as an empty
   profile. Preserve separate language and culture ID namespaces.

Owner supplied Get item output confirms Learnlanguages#Id is an integer array.
Use built-in **Data Operations Select** named **My_profile_row**, From expression
`array(body('Get_item'))`, with this mapping. Keys are plain text; values are fx
expressions without @. Actual field keys for the other #Id arrays must still be
confirmed with populated data during binding; missing keys are not proof of emptiness.

| Key | Value expression |
|---|---|
| profileId | `item()?['ID']` |
| accountId | `item()?['Participantaccount']?['Claims']` |
| displayName | `item()?['Participantaccount']?['DisplayName']` |
| status | `item()?['Status']?['Value']` |
| teachIds | `coalesce(item()?['Teachlanguages#Id'], json('[]'))` |
| learnIds | `coalesce(item()?['Learnlanguages#Id'], json('[]'))` |
| shareCultureIds | `coalesce(item()?['ShareCultures#Id'], json('[]'))` |
| learnCultureIds | `coalesce(item()?['LearnCultures#Id'], json('[]'))` |

Then Compose **My_profile** = `first(body('My_profile_row'))`. Add another Select
named **Normalized_candidates**, From the **value** array of Candidate source,
using the same eight mappings. Compose **Candidate_profiles** =
`body('Normalized_candidates')`. These are data-shaping actions, not per-record
HTTP calls or a second matching implementation. Do not add an Apply to each.

### Batch 3 — match and respond

1. Add **Eligible_candidates** Filter array and **Candidate_fit** Select using
   config/discovery_core_build.json. In fx omit leading @. The fragment assumes
   the two normalized inputs above are Composes; adapt references only if the
   actual action kinds/names differ. No assignments/writes happen during search.
   In the basic Filter array editor, the complete Boolean predicate can be placed
   in the left fx field, compared with Boolean true. Candidate_fit now projects
   only profileId, displayName and fitType for the owner preview; matching ID
   arrays/identity/audit fields are not returned to the gallery.
2. Match either direction for language or culture, excluding self and non-Active
   validation status. Shared interest alone is insufficient without a matching
   sharer. Blank Time zone is not an exclusion.
3. Add **Respond to a Power App or flow** with Text outputs **candidatesjson** and
   **errormessage**, using the responseContract expressions in the same JSON.
   Candidate counts above 500 return [] plus a clear error, not partial matches.
   A missing account/unready validation status returns registration feedback.
   Failed reads do not reach the success response; the app's IfError handles the
   failed invocation. None of this establishes ordinary-user caller authorization.

### Batch 4 — wire the Power Apps screen

Configuration checkpoint (2026-11-07): the owner confirms the flow/actions and
app bindings below are configured. The sample artwork is removed. MainScreen1
holds Discover; scrDiscovery holds Back and Gallery1. Owner reports empty results
with no suitable candidate data and working Back navigation. Populated matching,
actual flow responses/query limits, published versions and caller/access
verification remain unverified. The JSON is a partial expression reference,
not a tenant/app export. Request flow TandemSendRequest is separate #10 work.

1. On scrDiscovery, use the vertical Gallery1 with Items **colCandidates**.
   Set Title4.Text to **ThisItem.displayName** and Subtitle4.Text to
   **ThisItem.fitType**. Back.OnSelect is
   **Navigate(MainScreen1, ScreenTransition.None)**. If starting from the sample
   template, remove the sample artwork controls after creating this gallery.
   The owner's picker did not expose Blank, so a blank-screen option is not a
   prerequisite. On MainScreen1 place Discover beside the registration view.
   Use **RecordsGallery1.Selected.ID**; the earlier **Form1.Item.ID** reference
   caused an editor error. This reference is not caller authorization.
2. Add the TandemDiscovery flow through the app's Power Automate pane. Verify the
   connector's actual name/output fields using IntelliSense if names differ.
3. Add a Discover button near the saved registration view and use this OnSelect
   after scrDiscovery and the flow/output schema exist:

```powerfx
If(
    IsBlank(RecordsGallery1.Selected.ID),
    Notify("Save your registration first.", NotificationType.Error),
    Clear(colCandidates);
    IfError(
        Set(varDiscoveryResponse, TandemDiscovery.Run(RecordsGallery1.Selected.ID));
        If(
            !IsBlank(varDiscoveryResponse.errormessage),
            Notify(varDiscoveryResponse.errormessage, NotificationType.Error),
            ClearCollect(
                colCandidates,
                ForAll(
                    Table(ParseJSON(varDiscoveryResponse.candidatesjson)) As candidate,
                    {
                        profileId: Value(candidate.Value.profileId),
                        displayName: Text(candidate.Value.displayName),
                        fitType: Text(candidate.Value.fitType)
                    }
                )
            );
            Navigate(scrDiscovery)
        ),
        Notify("Discovery could not load. Please try again.", NotificationType.Error)
    )
)
```

Display names and fit type are the minimal owner preview, not final field-exposure
acceptance. Internal candidate IDs are for subsequent request lookup/rechecks,
not authorization or a raw profile display. A list containing only the current
profile yields no candidates; do not manufacture a positive match. Next build the
in-app sent/received requests, accept/decline/cancel and Groups/My groups path;
attach required backing lists at those persistence steps. Core persistence is not
implemented merely by the screen/button or expression reference.

## Connection requests - configured #10 scaffold

Owner-reported build, recorded 2026-11-07. No exported app/flow package or actual
send/history/cancel run is supplied. This milestone does not complete #10.
All three flows use the existing SharePoint connection and Power Apps (V2).

| Flow | Inputs | Configured actions and response |
|---|---|---|
| TandemSendRequest | Number SenderParticipantId, RecipientParticipantId | Read both Participants; validate Active/present Claims/different people; bidirectional Pending query; create Pending; success/message |
| TandemMyRequests | Number ParticipantId | Read participant; Get_items from Connection Requests where either participant ID matches; Request rows Select; requestsjson/errormessage |
| TandemCancelRequest | Number ParticipantId, RequestId | Read participant and request; require sender-ID match, nonempty account and Pending; update Cancelled; success/message |

Connection Requests uses required zero-decimal Number SenderParticipantId and
RecipientParticipantId, required Choice Status (Pending/Accepted/Declined/
Cancelled, default Pending), Title and built-in Created. This is the current
person-to-person scaffold; group targets and recovery state are not yet bound.

History Get_items uses the participant ID read from SharePoint, order
Created desc, ID desc, Top Count 101. Request rows contains requestId,
senderParticipantId, recipientParticipantId, status (Choice Value), created
and direction (Sent if sender ID matches, otherwise Received). Both response
expressions must reference **Get_items**, the actual internal name observed in
the owner's Select code, rather than the original suggested Read_requests.
Above 100 records, return [] plus an explicit bound message; no pagination UI
or large-history acceptance is implemented. Existing history is not gated on
validation Active.

In the app, MainScreen1 My requests invokes TandemMyRequests with
RecordsGallery1.Selected.ID, parses requestsjson into typed colRequests and
navigates to scrRequests. galRequests.Items is colRequests; Title4_1 shows
direction plus request number; Subtitle4_1 shows status. Back Button1_1 returns
to MainScreen1. The copied send arrow was deleted from this screen.

Cancel is inside galRequests and visible only when direction is Sent and status
is Pending. It passes the selected profile ID and row requestId to
TandemCancelRequest. Only success updates the local status to Cancelled and hides
the button; failures show feedback. Cancellation Update item must preserve both
required participant-ID fields from Read_request; do not omit them or replace
the parties with a different identity.

Core gaps remain implementation work: trusted caller ownership rather than
app-supplied identity, #6 participation/openness and compatibility checks for new
connections, authoritative response authority, duplicate/retry protection and
atomic state transitions under #47. The current read/check/write cancellation
can race an acceptance and is not concurrency-safe. UI visibility is feedback,
not authorization. Ordinary-account access and detailed tenant tests stay pending.

The three flows above do not create groups. The subsequent #11 response build
is recorded in the sanitized observed reference
config/participant_response_flow.snapshot.json, with coordinated #12/#47 work.
The complete export review found 77 actions/depth 6 and valid structural
references, but requires the Decline stop flag and final Choice Value fixes.
The first input label also needs correction. Do not treat it as a ready import,
live matching/authorization proof or a completed #11 delivery. A corrected
export/review precedes app Accept/Decline controls.

The backend groups use unique SourceRequestId; membership episodes use unique
MembershipKey. SetupComplete defaults No and is workflow-managed. Only a group
with completed setup and an Accepted source request may be presented as an
operational group; temporary membership rows do not make it visible. Conditional
setup preserves a completed group's existing lifecycle state. Rejected-attempt
cleanup targets only unfinished source-owned groups and their request-owned
memberships, retaining JoinedAt/history and recording LeftAt. Remaining restart/
retry/availability/access cases stay in #47/#6/#18; no new paid runtime is added.

## Discovery eligibility in Power Automate

Scope update: this is the tested language-only baseline, not complete v0.2
eligibility. Freeze #46 fields first, then extend #7 for culture-only/combined
fit, independent participation/validation and open-to-connections. Show compatible
candidates only. Exact display fields remain undecided; participant fields such
as Comments are generally eligible, admin/system-only fields excluded. No Comments
notice or profile group-size preference is required. Time zone is optional; empty
values do not exclude candidates. Groups expose count/slots and Open/Closed/Ended.
Ranking #8 is Later. Agree response fields before real-data integration.

`config/discovery_eligibility.json` specifies two built-in actions: Filter array
(`Eligible_candidates`) and Select (`Candidate_fit`). It is an action-definition
fragment and expression reference, not an importable flow or deployed feature.
`tests/fixtures/discovery_flow_cases.json` supplies synthetic inputs and expected
results. The owner has verified the basic five-profile scenarios below in a
manually triggered Power Automate flow; additional fixture cases remain pending.

Power Automate hosts these actions. After integration, the user's Discovery
button invokes the flow; no one runs a script or approves each search. A trusted
data-access step resolves the caller, loads their profile and obtains candidate
records. Eligibility runs before any candidate response reaches Power Apps.
No generic read-all-profiles endpoint is permitted.

## Prerequisites to flag and verify before configuration

- Existing Power Apps/Power Automate entitlements cover every intended user and
  the selected actions. A standard connector label alone is not a tenant licence check.
- Existing environment policy permits the app, SharePoint connector and selected
  authenticated identity method together; no premium/custom connector fallback.
- Caller identity is trusted and bound to the invocation; app-supplied email,
  record ID or filter cannot select another user's profile.
- The agreed audience can self-onboard without individual grants, new-account
  administration or manual group updates. Connection ownership and any necessary
  exceptional maintenance are disclosed upfront.

The self-service requirement applies to ordinary operations. Necessary admin
approval or intervention in critical/exceptional cases is allowed, without
introducing per-user or per-search manual work into the standard flow.
- List-read rights and candidate response fields are explicitly agreed. Ordinary
  access testing remains deferred, not passed; admin site roles are expected.

These checks remain gates for ordinary-user integration and sharing. The owner's
new direction permits owner-only unshared app/flow construction described above;
it does not authorize access redesign, trials, paid services or ordinary rollout
without the relevant prerequisites. Existing tenant connection availability must
still be verified for each dependent action.

## Build steps after prerequisites pass

1. Create an isolated manually triggered test flow. First use only synthetic
   Compose inputs to verify the rule actions; this does not prove authorization.
2. Name two Compose actions `My_profile` and `Candidate_profiles`. Make the second
   follow the first so both outputs exist before filtering. Set their inputs to
   `myProfile` and `candidates` from the synthetic fixture.
3. Add Filter array named `Eligible_candidates`. Use the fragment's `from`
   expression and advanced-mode `where` expression. In an Expression editor,
   omit the leading `@`; the serialized definition includes it.
4. Add Select named `Candidate_fit`, From = body of `Eligible_candidates`. Map
   the four keys to the expressions in the fragment. This projects only internal
   candidate references and fit metadata, not raw profiles/comments/credentials.
5. Compare output with `expectedCandidateFit` and run the additional scenarios.
   Do not call them passed until actual flow results are recorded.
6. For real-data integration, normalize trusted SharePoint results into the
   documented shape first. Map multi-value lookups to integer ID arrays using
   Select in text mode; empty selections become `[]`. Use actual connector
   dynamic fields, not assumed internal column names. Reject duplicate account
   identities, unknown/non-integer language IDs and malformed records before
   filtering. No profile means an empty result, not a broad list fallback.
7. Load current Active candidates with bounded SharePoint Get items queries.
   Configure pagination deliberately; never treat a truncated first page as
   complete results. Verify the synchronous response time and action budget at
   POC scale. Return an error when bounds cannot be met, not partial success or
   an automatic paid-service workaround. Ranking belongs to #8.
8. After authorization and response fields are verified, add Respond to a Power
   App or flow and wire the Discovery button. Return only approved eligible
   candidate fields. Keep raw Get items results and run data protected. No
   permissions, groups, memberships or connection requests are written by search.

Eligibility uses the current Active status and catalogue IDs. Either exchange
direction qualifies, so teach-only participants can find learners; both directions
make a reciprocal suggestion. Time zone is retained for later ranking, not an
eligibility exclusion. No new open-to-connections field is introduced.

## Validation and remaining work

Owner-reported tenant checks on 2026-10-31:

| Check | Confirmed result |
|---|---|
| Two Compose actions with five synthetic profiles | Succeeded |
| Active learner/sharer filtering | Only test-b and test-c remain; self, Needs review and incompatible candidates excluded |
| Select fit projection | Reciprocal profile 2 and one-way profile 3 match expected values |
| Teach-only current profile | Only profile 2 remains, canTeachIds = [1], reciprocal = false |
| Current profile Needs review | Filter and Select return empty arrays |

These are owner-confirmed manual runs of the expressions supplied in chat, not
an exported production flow or automated replay of the full repository fixture.
The chat expressions use non-null ID arrays; the fragment's null-handling paths,
extra profile 6, malformed-input rejection, pagination and scale remain untested.
The manual trigger proves these data operations work for the owner's synthetic
test, not Power Apps connectivity, all-user licensing or authorization.

The former Python test result does not validate this flow. #7 remains open until
trusted SharePoint normalization, an authorized response and Power Apps integration
pass tenant tests. No production flow export exists yet.

Sources: [data operations](https://learn.microsoft.com/en-us/power-automate/data-operations),
[expression reference](https://learn.microsoft.com/en-us/azure/logic-apps/workflow-definition-language-functions-reference),
[flow limits](https://learn.microsoft.com/en-us/power-automate/limits-and-config).
