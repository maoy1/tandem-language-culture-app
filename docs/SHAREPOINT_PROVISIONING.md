# SharePoint provisioning

POC-02 uses a declarative schema and a repeatable Python/Microsoft Graph script.
The schema is [config/sharepoint_schema.json](../config/sharepoint_schema.json);
the script is [scripts/sharepoint/provision.py](../scripts/sharepoint/provision.py).
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
- create or validate the declared list indexes and unique participant identity;
- safely reuse existing lists and fields instead of duplicating them.

The script never stores the site URL, credentials, or employee data in the
repository. It uses an access token supplied through `GRAPH_ACCESS_TOKEN` or
retrieved from the Azure CLI after `az login`.

## One-time manual decisions

- choose the target SharePoint site;
- approve the interactive connection and required permissions;
- create or confirm the Participants `Location` field as a SharePoint Location
  field, because this complex field is intentionally validated rather than
  synthesized by the script;
- review any `ERROR` output before using the lists.

## Local validation

If the repository environment has not been created yet:

```bash
python -m venv .venv
source .venv/Scripts/activate
```

Run the schema-only check first:

```text
python scripts/sharepoint/validate_schema.py config/sharepoint_schema.json
```

This does not connect to SharePoint and does not change anything.

Install and run the local test suite:

```text
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

The tests validate the declarative schema, controlled language lookups,
required participant fields, removed catalogue fields, and validator error
handling. They do not connect to SharePoint.

## Tenant validation and provisioning

For a live run, use an approved Microsoft Graph identity. The script accepts a
token through `GRAPH_ACCESS_TOKEN`; Azure CLI is only one possible way to
obtain that token. If your organisation blocks Azure CLI sign-in, ask an
approved tenant administrator or service identity to run the script. Never
commit a token to the repository.

If Azure CLI is approved for your account, sign in once:

```bash
az login
```

Validate the live site without creating missing objects:

```bash
python scripts/sharepoint/provision.py \
  --site-url "https://<tenant>.sharepoint.com/sites/<site>" \
  --validate-only
```

After reviewing the output, run the same script without `--validate-only` to
create missing standard lists and fields. It is safe to rerun; existing valid
objects are reported as `OK`.

The script may report `MANUAL` for the Location field. Complete that one check,
then run validation again until no unexpected `ERROR` entries remain.
