# SharePoint provisioning

POC-02 uses a declarative schema and a repeatable PowerShell script. The schema
is [config/sharepoint_schema.json](../config/sharepoint_schema.json); the script
is [scripts/sharepoint/provision.ps1](../scripts/sharepoint/provision.ps1).
The schema provisions the current participant-registration slice only:
`Language catalogue` and `Participants`. Future group, request, and statistics
lists are added through their own issues after their design is approved.

The schema follows [CURRENT_DESIGN.md](CURRENT_DESIGN.md). It deliberately
does not provision Culture, Time zone, or Location catalogues. Participants
provide one SharePoint Location value; the time zone is derived later by flow
enrichment.

## What is automated

- create missing generic SharePoint lists;
- create missing standard fields;
- create choice fields and lookup fields after their target lists exist;
- validate required fields and report missing configuration;
- create or validate the declared list indexes;
- safely reuse existing lists and fields instead of duplicating them.

The script never stores the site URL, credentials, or employee data in the
repository. It uses interactive sign-in through PnP PowerShell.

## One-time manual decisions

- choose the target SharePoint site;
- approve the interactive connection and required permissions;
- create or confirm the Participants `Location` field as a SharePoint Location
  field, because this complex field is intentionally validated rather than
  synthesized by the script;
- review any `ERROR` output before using the lists.

## Local validation

If the repository environment has not been created yet:

```powershell
python -m venv .venv
& .\.venv\Scripts\Activate.ps1
```

Run the schema-only check first:

```text
python scripts/sharepoint/validate_schema.py config/sharepoint_schema.json
```

This does not connect to SharePoint and does not change anything.

## Tenant validation and provisioning

Install PnP PowerShell once for the account that will administer the site:

```powershell
Install-Module PnP.PowerShell -Scope CurrentUser
```

Validate the live site without creating missing objects:

```powershell
./scripts/sharepoint/provision.ps1 `
  -SiteUrl "https://<tenant>.sharepoint.com/sites/<site>" `
  -ValidateOnly
```

After reviewing the output, run the same script without `-ValidateOnly` to
create missing standard lists and fields. It is safe to rerun; existing valid
objects are reported as `OK`.

The script may report `MANUAL` for the Location field. Complete that one check,
then run validation again until no unexpected `ERROR` entries remain.
