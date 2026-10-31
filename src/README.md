# Application code

Production runs in SharePoint, Power Apps and Power Automate under existing
entitlements. No Python runtime, server, additional paid licence, premium/custom
connector, external API or separately hosted service is part of the application.
Local Python schema validators are development tools only.

## Discovery eligibility in Power Automate

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

These checks are still pending. Do not create flows, change access, start trials
or deploy a new service merely to follow this guide.

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
