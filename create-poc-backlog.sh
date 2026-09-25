#!/usr/bin/env bash

set -euo pipefail

REPO="maoy1/tandem-language-culture-app"
MILESTONE="POC Vertical Slice"

# ---------------------------------------------------------------------------
# Prerequisites
# ---------------------------------------------------------------------------

if ! command -v gh >/dev/null 2>&1; then
  echo "ERROR: GitHub CLI (gh) is not installed."
  exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
  echo "ERROR: GitHub CLI is not authenticated."
  echo "Run: gh auth login"
  exit 1
fi

echo "Repository: $REPO"

gh repo view "$REPO" >/dev/null

# ---------------------------------------------------------------------------
# Labels
# ---------------------------------------------------------------------------

create_label() {
  local name="$1"
  local description="$2"

  gh label create "$name" \
    --repo "$REPO" \
    --description "$description" \
    --force >/dev/null
}

echo "Creating labels..."

create_label "priority:P0" "Required for the core POC vertical slice"
create_label "priority:P1" "Important POC hardening or extension"
create_label "priority:P2" "Operational completeness; can follow core POC"

create_label "type:feature" "Product or application feature"
create_label "type:automation" "Automated workflow or background process"
create_label "type:test" "Testing or validation work"
create_label "type:spike" "Investigation or technical validation"
create_label "type:infrastructure" "Repository, provisioning, or infrastructure"

create_label "area:github" "GitHub repository, CI, or source-control work"
create_label "area:sharepoint" "SharePoint data or configuration"
create_label "area:powerapps" "Power Apps user interface"
create_label "area:discovery" "Participant/group discovery logic"
create_label "area:permissions" "Authorization and permissions"
create_label "area:workflow" "Requests, notifications, or workflow"
create_label "area:admin" "Administration and operational tooling"

create_label "epic:foundation" "Foundation and repeatable setup"
create_label "epic:registration" "Participant registration and profile"
create_label "epic:discovery" "Self-service discovery"
create_label "epic:requests" "Connection requests"
create_label "epic:groups" "Language-group lifecycle"
create_label "epic:group-discovery" "Existing group discovery and joining"
create_label "epic:security" "Permissions and security"
create_label "epic:automation" "Power Automate and background automation"
create_label "epic:operations" "Status freshness and administration"
create_label "epic:testing" "Testing and scalability"

# ---------------------------------------------------------------------------
# Milestone
# ---------------------------------------------------------------------------

echo "Ensuring milestone exists..."

MILESTONE_NUMBER="$(
  gh api \
    --method GET \
    "repos/$REPO/milestones?state=all&per_page=100" \
    --jq ".[] | select(.title == \"$MILESTONE\") | .number" |
    head -n 1
)"

if [[ -z "$MILESTONE_NUMBER" ]]; then
  MILESTONE_NUMBER="$(
    gh api \
      --method POST \
      "repos/$REPO/milestones" \
      -f title="$MILESTONE" \
      -f description="Core Tandem POC vertical slice: register, discover a 1:1 language partner, request connection, accept, and create/manage the tandem group." \
      --jq '.number'
  )"
fi

echo "Milestone: $MILESTONE (#$MILESTONE_NUMBER)"

# ---------------------------------------------------------------------------
# Issue helpers
# ---------------------------------------------------------------------------

declare -A ISSUE_NUMBERS

dependency_text() {
  local result=""
  local dep

  for dep in "$@"; do
    [[ -z "$dep" ]] && continue

    if [[ -z "${ISSUE_NUMBERS[$dep]:-}" ]]; then
      echo "ERROR: Dependency $dep has not been created yet." >&2
      exit 1
    fi

    if [[ -n "$result" ]]; then
      result+=", "
    fi

    result+="#${ISSUE_NUMBERS[$dep]} ($dep)"
  done

  if [[ -z "$result" ]]; then
    result="None"
  fi

  printf '%s' "$result"
}

create_issue() {
  local id="$1"
  local title="$2"
  local priority="$3"
  local type="$4"
  local areas="$5"
  local epic="$6"
  local milestone="$7"
  local dependencies="$8"
  local description="$9"
  shift 9

  local deps
  deps="$(dependency_text $dependencies)"

  local body
  body=$(
    printf '## Description\n\n%s\n\n## Dependencies\n\n%s\n\n## Acceptance criteria\n' \
      "$description" \
      "$deps"

    local criterion
    for criterion in "$@"; do
      printf -- '- [ ] %s\n' "$criterion"
    done
  )

  local args=(
    issue create
    --repo "$REPO"
    --title "[$id] $title"
    --body "$body"
    --label "$priority"
    --label "$type"
    --label "$epic"
  )

  IFS=',' read -ra AREA_ARRAY <<< "$areas"
  local area
  for area in "${AREA_ARRAY[@]}"; do
    [[ -n "$area" ]] && args+=(--label "$area")
  done

  if [[ "$milestone" == "yes" ]]; then
    args+=(--milestone "$MILESTONE")
  fi

  echo "Creating $id: $title"

  local url
  url="$(gh "${args[@]}")"

  local number
  number="${url##*/}"

  ISSUE_NUMBERS["$id"]="$number"

  echo "  -> #$number"
}

# ---------------------------------------------------------------------------
# P0 - Core vertical slice
# ---------------------------------------------------------------------------

create_issue \
  "POC-01" \
  "Create Tandem POC repository structure" \
  "priority:P0" \
  "type:infrastructure" \
  "area:github" \
  "epic:foundation" \
  "yes" \
  "" \
  "Create the GitHub repository structure for the Tandem POC. The repository must contain source-controlled scripts, tests, application artifacts, and documentation required to understand and reproduce the POC. The POC may initially use a personal repository but must remain portable to a company-owned repository." \
  "Repository contains clear locations for source/application artifacts, scripts, tests, and documentation." \
  "No credentials or employee data are committed." \
  "Repository-owner username is not hard-coded into application/deployment logic." \
  "README explains the purpose and basic development/deployment workflow." \
  "Repository can later move to the company GitHub organization without redesign."

create_issue \
  "POC-02" \
  "Automate SharePoint provisioning" \
  "priority:P0" \
  "type:infrastructure" \
  "area:sharepoint,area:github" \
  "epic:foundation" \
  "yes" \
  "POC-01" \
  "Create repeatable provisioning scripts for the SharePoint structures required by the POC. Manual SharePoint configuration should be minimized." \
  "Required lists and core columns can be created or validated by script." \
  "Script is safe to rerun." \
  "Existing valid structures are not duplicated." \
  "Incorrect or missing configuration is clearly reported." \
  "Required indexes are provisioned or validated." \
  "Any unavoidable manual steps are explicitly documented." \
  "Script does not depend on the original developer's workstation."

create_issue \
  "POC-03" \
  "Implement participant self-registration" \
  "priority:P0" \
  "type:feature" \
  "area:powerapps,area:sharepoint" \
  "epic:registration" \
  "yes" \
  "POC-02" \
  "Allow an authenticated company colleague to register themselves in the Tandem program without administrator approval." \
  "Microsoft/company identity is used for the participant." \
  "One participant profile exists per user." \
  "Reopening registration edits the existing profile rather than creating a duplicate." \
  "No admin approval is required for initial registration." \
  "Participant can update their own profile."

create_issue \
  "POC-04" \
  "Add structured language preferences" \
  "priority:P0" \
  "type:feature" \
  "area:powerapps,area:discovery" \
  "epic:registration" \
  "yes" \
  "POC-03" \
  "Allow participants to specify languages they can offer and languages they want to learn or practise. A participant can be both learner and sharer." \
  "User can select language(s) they offer." \
  "User can select language(s) they want to learn." \
  "Values use a controlled vocabulary rather than arbitrary free text." \
  "A participant may be both learner and sharer." \
  "Data is usable by discovery logic." \
  "Additional sharers can be encouraged without restricting participation."

create_issue \
  "POC-05" \
  "Add participant profile context" \
  "priority:P0" \
  "type:feature" \
  "area:powerapps" \
  "epic:registration" \
  "yes" \
  "POC-03" \
  "Capture additional information useful when another participant evaluates whether to connect." \
  "Preferred group size can be stored." \
  "Optional language level can be stored/displayed." \
  "Informational language/culture interests can be entered." \
  "Participant city is obtained from SharePoint location." \
  "No separate time-zone field is requested." \
  "Derived time zone can be used by discovery."

create_issue \
  "POC-06" \
  "Implement participant participation status" \
  "priority:P0" \
  "type:feature" \
  "area:powerapps,area:sharepoint" \
  "epic:registration" \
  "yes" \
  "POC-03" \
  "Allow participants to pause or stop participation without deleting their profile or history." \
  "Supports Active, Paused, and Inactive." \
  "Participant can separately indicate whether they are open to new connections." \
  "Paused or inactive participants are excluded from new discovery suggestions." \
  "Existing memberships are not deleted when a participant pauses."

create_issue \
  "POC-07" \
  "Implement discovery eligibility logic" \
  "priority:P0" \
  "type:feature" \
  "area:discovery" \
  "epic:discovery" \
  "yes" \
  "POC-04 POC-06" \
  "Implement the first clean discovery boundary for finding potentially suitable 1:1 language partners. The system suggests opportunities; it does not automatically assign participants." \
  "Current participant is excluded from their own results." \
  "Candidate must be active and open to new connections." \
  "Candidate offering a language wanted by the current participant is considered eligible." \
  "Reciprocal matches are detectable." \
  "Eligibility logic is separate from UI presentation." \
  "Discovery does not automatically create a tandem/group."

create_issue \
  "POC-08" \
  "Implement discovery ranking" \
  "priority:P0" \
  "type:feature" \
  "area:discovery" \
  "epic:discovery" \
  "yes" \
  "POC-07" \
  "Rank eligible opportunities so the most practical candidates appear first." \
  "Reciprocal language fit may rank above one-way fit." \
  "Same-city candidate receives a ranking bonus." \
  "Time-zone proximity can be derived from SharePoint location and influence ranking." \
  "Preferred group size can influence ranking." \
  "Waiting time can influence ranking." \
  "Soft preferences do not become hard exclusions."

create_issue \
  "POC-09" \
  "Isolate discovery logic from Power Apps UI" \
  "priority:P0" \
  "type:feature" \
  "area:discovery,area:powerapps" \
  "epic:discovery" \
  "yes" \
  "POC-07 POC-08" \
  "Ensure eligibility and ranking rules have a clean implementation boundary rather than being duplicated across individual UI controls." \
  "Discovery rules have one clearly identified implementation location." \
  "Individual screens/controls do not duplicate core eligibility rules." \
  "Discovery behavior can be tested with synthetic input." \
  "Architecture permits moving discovery logic to another runtime later without changing the domain model."

create_issue \
  "POC-10" \
  "Create participant connection request" \
  "priority:P0" \
  "type:feature" \
  "area:workflow" \
  "epic:requests" \
  "yes" \
  "POC-07" \
  "Allow a participant to initiate a connection with a suggested participant." \
  "Participant can initiate Request to connect from discovery." \
  "Request is persisted." \
  "Request starts in Pending." \
  "Duplicate active/pending requests for the same connection are prevented." \
  "Requester can view request state."

create_issue \
  "POC-11" \
  "Accept or decline connection request" \
  "priority:P0" \
  "type:feature" \
  "area:workflow" \
  "epic:requests" \
  "yes" \
  "POC-10" \
  "Allow the target participant to accept or decline a connection request." \
  "Intended participant can accept." \
  "Intended participant can decline." \
  "Other normal participants cannot respond to the request." \
  "Accepted request proceeds to tandem/group creation." \
  "Declined request creates no membership." \
  "Request lifecycle is retained rather than deleted."

create_issue \
  "POC-12" \
  "Create 1:1 tandem after acceptance" \
  "priority:P0" \
  "type:feature" \
  "area:sharepoint" \
  "epic:groups" \
  "yes" \
  "POC-11" \
  "Create the initial language tandem/group and memberships after a successful connection. 1:1 is the primary POC language-tandem case." \
  "Accepted connection can create a Tandem group." \
  "Default capacity is 2." \
  "Both participant memberships are created." \
  "Group name follows the agreed language-oriented naming convention where practical." \
  "Structured language fields, not the group title, remain authoritative." \
  "Group reaches a valid initial lifecycle state."

create_issue \
  "POC-13" \
  "Implement group lifecycle management" \
  "priority:P0" \
  "type:feature" \
  "area:powerapps,area:sharepoint" \
  "epic:groups" \
  "yes" \
  "POC-12" \
  "Allow group members to maintain the lifecycle of their tandem." \
  "Supports Forming, Active, Paused, NeedsMember, and Ended." \
  "OpenToNewMembers is represented independently from lifecycle status." \
  "Any active group member may change group status." \
  "Admin can override group status." \
  "Ended groups no longer appear as active discovery opportunities."

create_issue \
  "POC-14" \
  "Implement leave-group behavior" \
  "priority:P0" \
  "type:feature" \
  "area:workflow" \
  "epic:groups" \
  "yes" \
  "POC-12 POC-13" \
  "Allow a participant to leave without deleting historical membership information." \
  "Membership becomes Left." \
  "Membership record is not deleted." \
  "Active member count can be recalculated." \
  "1:1 group can move to NeedsMember or Ended." \
  "Remaining participant can become available for discovery if appropriate."

create_issue \
  "POC-15" \
  "Add two-active-groups warning" \
  "priority:P0" \
  "type:feature" \
  "area:powerapps" \
  "epic:groups" \
  "yes" \
  "POC-12" \
  "Warn a participant before joining or creating another group when they already have two active memberships." \
  "Active memberships are counted." \
  "Count of 2 or more triggers warning." \
  "Warning does not prevent continuation." \
  "No persistent over-limit status is required." \
  "Admin approval is not required for the third group."

# ---------------------------------------------------------------------------
# P1
# ---------------------------------------------------------------------------

create_issue \
  "POC-16" \
  "Discover existing open groups" \
  "priority:P1" \
  "type:feature" \
  "area:discovery" \
  "epic:group-discovery" \
  "no" \
  "POC-08 POC-13" \
  "Allow participants to discover existing suitable groups that are open to new members." \
  "Only suitable groups are displayed." \
  "Ended, paused, or non-open groups are excluded." \
  "Capacity is considered." \
  "Relevant language compatibility is considered." \
  "Ranking preferences can also be applied."

create_issue \
  "POC-17" \
  "Request to join an existing group" \
  "priority:P1" \
  "type:feature" \
  "area:workflow" \
  "epic:group-discovery" \
  "no" \
  "POC-16" \
  "Allow a participant to request membership in an existing group." \
  "Join request is persisted." \
  "Active group members can respond." \
  "Capacity is rechecked at acceptance time." \
  "Accepted request creates active membership." \
  "Declined request leaves memberships unchanged."

create_issue \
  "POC-18" \
  "Protect participant profile edits" \
  "priority:P1" \
  "type:feature" \
  "area:permissions" \
  "epic:security" \
  "no" \
  "POC-03" \
  "Implement own-profile editing while preserving read access required for discovery." \
  "Participant can edit their own participant record." \
  "Participant cannot edit another participant's profile." \
  "Admin can edit all profiles." \
  "Discoverable participant information remains readable as required."

create_issue \
  "POC-19" \
  "Protect group-member actions" \
  "priority:P1" \
  "type:feature" \
  "area:permissions" \
  "epic:security" \
  "no" \
  "POC-13" \
  "Ensure only active group members and admins can modify a group's managed state." \
  "Non-member can read discoverable group data." \
  "Active member can change allowed group fields/status." \
  "Non-member cannot change group state." \
  "Admin can override all group state."

create_issue \
  "POC-20" \
  "Protect requests and memberships" \
  "priority:P1" \
  "type:feature" \
  "area:permissions" \
  "epic:security" \
  "no" \
  "POC-10 POC-12" \
  "Protect request responses and authoritative membership lifecycle data." \
  "Only correct recipients/group members may respond to requests." \
  "Participants cannot arbitrarily create active membership records." \
  "Membership lifecycle changes use the controlled path." \
  "Admin can repair records when necessary."

create_issue \
  "POC-21" \
  "Send request notifications" \
  "priority:P1" \
  "type:automation" \
  "area:workflow" \
  "epic:automation" \
  "no" \
  "POC-10" \
  "Send notification when a connection or join request is created." \
  "Correct recipient receives notification." \
  "Notification failure does not delete or roll back the request." \
  "Failure is visible/logged for admins." \
  "Core request state remains authoritative."

create_issue \
  "POC-22" \
  "Synchronize group item permissions" \
  "priority:P1" \
  "type:automation" \
  "area:permissions" \
  "epic:automation" \
  "no" \
  "POC-12 POC-19" \
  "Synchronize SharePoint group-item edit permissions with active memberships." \
  "Active member receives appropriate group-item edit access." \
  "Left/removed member loses group-management access." \
  "Remaining active members retain access." \
  "Admin retains access." \
  "Permission failure does not corrupt membership state." \
  "Flow behavior is tested for multiple members."

create_issue \
  "POC-23" \
  "Configure request item permissions" \
  "priority:P1" \
  "type:automation" \
  "area:permissions" \
  "epic:automation" \
  "no" \
  "POC-10 POC-17 POC-20" \
  "Grant request-item access to the appropriate target participant or active group members." \
  "Connect request target receives response access." \
  "Join request active group members receive response access." \
  "Requester retains required access." \
  "Failed permission assignment is logged." \
  "Request remains intact if permission automation fails."

create_issue \
  "POC-24" \
  "Close resolved request permissions" \
  "priority:P1" \
  "type:automation" \
  "area:permissions" \
  "epic:automation" \
  "no" \
  "POC-23" \
  "Remove unnecessary edit rights after a request is completed while preserving required history access." \
  "Handles Accepted, Declined, Cancelled, and Expired requests." \
  "Repeated execution is prevented or idempotent." \
  "Required read access is retained where agreed." \
  "Permission errors are reported." \
  "Request business status is never rolled back due to permission failure."

create_issue \
  "POC-25" \
  "Add automated discovery tests" \
  "priority:P1" \
  "type:test" \
  "area:discovery" \
  "epic:testing" \
  "no" \
  "POC-09" \
  "Create automated tests for the isolated discovery logic." \
  "Reciprocal language tandem is tested." \
  "One-way learner/sharer compatibility is tested." \
  "Paused participant exclusion is tested." \
  "Inactive participant exclusion is tested." \
  "Same-city ranking bonus is tested." \
  "Group capacity is tested." \
  "Two-group warning behavior is tested."

create_issue \
  "POC-26" \
  "Generate synthetic scale datasets" \
  "priority:P1" \
  "type:test" \
  "area:sharepoint,area:discovery" \
  "epic:testing" \
  "no" \
  "POC-02" \
  "Provide reproducible synthetic data for validating SharePoint/Power Apps behavior at representative scale." \
  "Can generate approximately 200 participants." \
  "Can generate approximately 1,000 participants." \
  "Can generate approximately 5,000 participants." \
  "Data contains realistic language, location, status, group, and membership distributions." \
  "No real employee data is required."

create_issue \
  "POC-27" \
  "Measure discovery scalability" \
  "priority:P1" \
  "type:spike" \
  "area:discovery,area:powerapps" \
  "epic:testing" \
  "no" \
  "POC-09 POC-26" \
  "Determine whether SharePoint plus Power Apps remains practical at expected POC and near-production scale." \
  "Discovery tested at approximately 200 participants." \
  "Discovery tested at approximately 1,000 participants." \
  "Discovery tested at approximately 5,000 participants." \
  "Query latency is recorded." \
  "Power Apps delegation warnings/limitations are recorded." \
  "Any client-side large-data processing is identified." \
  "Results document whether a hosted discovery service should be reconsidered."

create_issue \
  "POC-28" \
  "Validate deployment reproducibility" \
  "priority:P1" \
  "type:test" \
  "area:github" \
  "epic:testing" \
  "no" \
  "POC-01 POC-02" \
  "Verify that another person can reproduce and manage the POC without relying on the original developer's workstation." \
  "Another admin/developer can follow repository instructions." \
  "Provisioning/validation can run from shared automation or documented environment." \
  "No local-only secret/configuration is required." \
  "Failures produce understandable diagnostic output." \
  "Any remaining manual prerequisites are documented."

# ---------------------------------------------------------------------------
# P2
# ---------------------------------------------------------------------------

create_issue \
  "POC-29" \
  "Implement participant and group freshness tracking" \
  "priority:P2" \
  "type:feature" \
  "area:admin" \
  "epic:operations" \
  "no" \
  "POC-06 POC-13" \
  "Identify participants and groups whose status may be stale." \
  "LastConfirmedAt or equivalent freshness data exists." \
  "Stale participants can be identified." \
  "Stale groups can be identified." \
  "Records are not automatically deleted because they become stale."

create_issue \
  "POC-30" \
  "Implement freshness reminder workflow" \
  "priority:P2" \
  "type:automation" \
  "area:workflow" \
  "epic:operations" \
  "no" \
  "POC-29" \
  "Notify participants or group members when status confirmation is required." \
  "Scheduled check identifies stale records." \
  "Appropriate participant/group member receives reminder." \
  "Failure to send reminder is observable." \
  "Reminder does not automatically end a group."

create_issue \
  "POC-31" \
  "Build admin status overview" \
  "priority:P2" \
  "type:feature" \
  "area:admin" \
  "epic:operations" \
  "no" \
  "POC-06 POC-13 POC-29" \
  "Provide an admin view of the overall Tandem program state." \
  "Admin can identify participants available/waiting for connections." \
  "Admin can identify active groups." \
  "Admin can identify paused groups." \
  "Admin can identify groups needing members." \
  "Admin can identify ended groups." \
  "Admin can identify stale participants/groups." \
  "Admin can identify records requiring intervention." \
  "Admin can perform agreed status overrides or corrections."

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

echo
echo "Created issues:"
for i in $(seq -w 1 31); do
  id="POC-$i"
  printf '%-7s -> #%s\n' "$id" "${ISSUE_NUMBERS[$id]}"
done

echo
echo "Done."
echo "Repository: https://github.com/$REPO/issues"
echo "Milestone: $MILESTONE"