# POC-18: private registration and controlled discovery

Status: design and tenant feasibility work in progress. No tenant permissions
or application connections have been changed by this document. Issue #18 stays
open until implementation and two-account acceptance tests pass.

## Agreed behavior

- My registration returns only the signed-in participant's profile.
- Participants create and update only their own profile; no participant delete.
- Direct SharePoint access must not expose other profiles or permit editing them.
- Clicking Discovery requests eligible candidates through a separate controlled
  operation. Eligibility and candidate presentation belong to #7–#9.
- Administrators retain access to all profiles.
- Keep the unique Participant account field. Do not introduce a public directory,
  extra discovery list, or a private-Comments requirement without a new decision.

The candidate response fields still need agreement in the discovery tickets.
Until then no candidate records are returned. This does not impose a new
private/public classification on Comments or Learning focus.

## Proposed implementation to validate in the tenant

Use authenticated Power Apps-triggered flows as the registration access path.
The Participants list is accessible to administrators and the automation account;
ordinary participants have no direct list access, including inherited group or
sharing-link access. Catalogue lists remain readable by the app audience.

The flow uses a controlled owner connection for SharePoint. Every profile
operation resolves the authenticated caller, checks authorization, and returns
only that caller's record. This avoids a post-create permission-change window
and avoids managing a unique permission scope for every participant.

This changes the current app: direct Participants galleries, lookup queries,
SubmitForm, and Patch operations must be replaced for registration by calls to
these flows. Existing language/time-zone catalogue controls can remain. Do not
remove list access from the working app audience before the replacement has
passed isolated tests and a cutover plan is ready.

This is a proposed architecture, not a deployable flow export. The tenant must
prove caller identity, connector policies, sharing and licensing support first.
If the tenant cannot support this securely, stop and choose another authenticated
backend with the owner; do not fall back to app filtering or client-supplied email.

## First tenant step: identity feasibility probe (no participant data)

1. Create a test instant flow with the Power Apps (V2) trigger and no inputs.
2. Add Office 365 Users **Get my profile (V2)**. Request only ID and user principal
   name. Do not use Get user profile with an email passed from Power Apps.
3. Configure its Office 365 Users connection as **Provided by run-only user**,
   where supported by this trigger/environment. The identity action must never
   silently use the automation owner's connection.
4. Return the resolved identity to a temporary test app. Add the flow to that app.
   Share the test app and flow with the two test accounts as users/run-only users,
   not co-owners. No Participants list or owner SharePoint connection is needed.
5. Run as A and B. Record the resolved Entra object IDs and confirm A resolves
   to A, B to B, and neither resolves to the owner. Do not commit personal IDs.
6. Confirm the connection is bound to the authenticated invocation, not merely
   any supplied account connection. Reject mismatches with trusted invocation
   identity. Where the tenant exposes no supported way to prove this binding,
   treat the probe as incomplete and do not add elevated SharePoint operations.
7. Verify normal users cannot edit the flow or inspect other users' run data.
   Verify applicable tenant connector policies and user licensing with the admin.

The Microsoft documentation supports run-only connection selection and the
current-user profile action; it does not establish that this complete design
works in this tenant. Record the actual outcome before the next phase.

## Registration operations after the identity gate passes

| Operation | Accepted app inputs | Server-side behavior |
|---|---|---|
| Get my profile | None | Resolve caller; query by caller's canonical Participant account; return zero or one own profile |
| Save my profile | Teach/learn lookup IDs, time-zone ID, learning focus, comments, optional concurrency token | Resolve caller; validate allowlisted values; create/update only the caller's record |
| Discover candidates (later #7–#9) | Only approved bounded preferences | Resolve caller; load own profile; apply eligibility and ranking server-side; return approved candidate fields only |

Never accept a participant identity, owner email, arbitrary item ID, OData filter,
field list, or arbitrary query as authorization. Use canonical identity resolved
server-side; keep the object-ID-to-SharePoint-person mapping under server control.
Updates find the caller's item server-side. Allowlist mutable fields; ignore no
unexpected fields silently. Status is computed by validation, not chosen by the
app. Reject unknown/inactive catalogue IDs. Preserve unique-account enforcement
under concurrent creates and handle version conflicts without overwriting edits.

No generic participant-list/read-by-ID endpoint may be exposed to normal users.
An invoked flow is a security boundary: calling it outside the app must enforce
the same rules. Return minimal own-profile data and safe error messages; do not
return SharePoint response bodies, all profiles, or owner credentials. Restrict
flow ownership/run history and protect sensitive action inputs/outputs.

An owner-created profile records the automation account in Created By. Do not
use Created By as participant identity. The existing created-item status flow
must be reviewed alongside the new save validation; edits also need validation.

## Cutover and acceptance (all pending)

Work in an isolated test list/app first, using synthetic data where possible.

- [ ] Identity probe passes with A and B and resists attempted identity substitution.
- [ ] Get/save operations pass create, reopen, edit, multi-language and teach-only tests.
- [ ] Tampered identity, another person's item ID, arbitrary queries and managed fields are rejected.
- [ ] Catalogue validation, duplicate-create and concurrent-update failure cases are handled.
- [ ] A and B cannot browse/read/write Participants via direct list, item link or API.
- [ ] A gets only A's profile and B only B's, including when invoking flows outside the app.
- [ ] Administrators and automation retain the intended access.
- [ ] Existing records are preserved; inherited access and old item shares are audited.
- [ ] Tenant permissions are restricted, the new app is published to the test audience,
      and direct Participants connections/old app access paths no longer expose data.
- [ ] Catalogue access and Teams/app/flow sharing work for a normal account.
- [ ] Evidence is recorded without committing employee data or secrets.

Do not close #18 on a documentation PR. Implementation and tenant evidence must
be reviewed first. If reverting to the old app, keep broad rollout paused rather
than restoring broad list read/write access as an automatic fallback.

## Sources

- [Microsoft: share a cloud flow and configure run-only connections](https://learn.microsoft.com/en-us/power-automate/create-team-flows)
- [Microsoft: Office 365 Users connector, Get my profile (V2)](https://learn.microsoft.com/en-us/connectors/office365users/)
- [Microsoft: SharePoint list permissions and inheritance](https://support.microsoft.com/en-us/sharepoint/lists/sharepoint-sharing-and-permissions/customize-permissions-for-a-sharepoint-list-or-library)
