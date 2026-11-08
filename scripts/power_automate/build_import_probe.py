"""Build a disposable Power Automate import probe (connector-free by default).

Local packaging utility only. The imported flow runs entirely in Power Automate.
Optional SharePoint mode reads site identity only and requires selecting an existing connection.
No existing tenant export, connection, account or list identifier is copied.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from uuid import uuid4
from urllib.parse import urlsplit
from zipfile import ZIP_DEFLATED, ZipFile

FLOW_NAME = "TandemImportProbe"
EXPECTED_MESSAGE = "IMPORT_PROBE_OK"


def build_package(output: Path, *, sharepoint_site: str | None = None) -> dict:
    output = Path(output)
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite an existing file: {output}")
    if sharepoint_site is not None:
        url = urlsplit(sharepoint_site)
        if (url.scheme != "https" or not url.hostname or
                not url.hostname.endswith(".sharepoint.com") or url.username or
                url.password or url.query or url.fragment):
            raise ValueError("Use an HTTPS SharePoint site URL without credentials, query or fragment")
    flow_name = "TandemSharePointImportProbe" if sharepoint_site else FLOW_NAME
    asset_id, flow_id, telemetry_id = (str(uuid4()) for _ in range(3))
    definition = {
        "$schema": "https://schema.management.azure.com/providers/Microsoft.Logic/schemas/2016-06-01/workflowdefinition.json#",
        "contentVersion": "1.0.0.0",
        "parameters": {
            "$authentication": {"defaultValue": {}, "type": "SecureObject"},
            "$connections": {"defaultValue": {}, "type": "Object"},
        },
        "triggers": {
            "manual": {
                "type": "Request",
                "kind": "PowerAppV2",
                "inputs": {"schema": {"type": "object", "properties": {}, "required": []}},
            }
        },
        "actions": {
            "Probe_message": {"type": "Compose", "inputs": EXPECTED_MESSAGE, "runAfter": {}},
            "Respond_to_a_Power_App_or_flow": {
                "type": "Response",
                "kind": "PowerApp",
                "runAfter": {"Probe_message": ["Succeeded"]},
                "inputs": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "success": {"title": "success", "type": "boolean", "x-ms-content-hint": "BOOLEAN", "x-ms-dynamically-added": True},
                            "message": {"title": "message", "type": "string", "x-ms-content-hint": "TEXT", "x-ms-dynamically-added": True},
                        },
                        "additionalProperties": {},
                    },
                    "statusCode": 200,
                    "body": {"success": True, "message": "@outputs('Probe_message')"},
                },
            },
        },
    }
    document = {
        "name": flow_id,
        "id": f"/providers/Microsoft.Flow/flows/{flow_id}",
        "type": "Microsoft.Flow/flows",
        "properties": {
            "apiId": "/providers/Microsoft.PowerApps/apis/shared_logicflows",
            "displayName": flow_name,
            "definition": definition,
            "connectionReferences": {},
            "flowFailureAlertSubscribed": False,
            "isManaged": False,
        },
    }
    manifest = {
        "schema": "1.0",
        "details": {
            "displayName": f"{flow_name}-package",
            "description": "Disposable generated-package import experiment. Two built-in actions; no connectors or data operations.",
            "createdTime": datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
            "packageTelemetryId": telemetry_id,
            "creator": "N/A",
            "sourceEnvironment": "",
        },
        "resources": {
            asset_id: {
                "type": "Microsoft.Flow/flows",
                "suggestedCreationType": "New",
                "creationType": "Existing, New, Update",
                "details": {"displayName": flow_name},
                "configurableBy": "User",
                "hierarchy": "Root",
                "dependsOn": [],
            }
        },
    }
    api_map, connection_map = {}, {}
    if sharepoint_site:
        api_id, connection_id = str(uuid4()), str(uuid4())
        connector = "shared_sharepointonline"
        api_path = "/providers/Microsoft.PowerApps/apis/shared_sharepointonline"
        api_map[connector], connection_map[connector] = api_id, connection_id
        manifest["resources"][asset_id]["dependsOn"] = [api_id, connection_id]
        manifest["details"]["description"] = "Disposable SharePoint connection mapping probe. One GET of site technical ID; no list or record operations."
        manifest["resources"][api_id] = {
            "id": api_path, "name": connector, "type": "Microsoft.PowerApps/apis",
            "suggestedCreationType": "Existing", "details": {"displayName": "SharePoint"},
            "configurableBy": "System", "hierarchy": "Child", "dependsOn": [],
        }
        manifest["resources"][connection_id] = {
            "type": "Microsoft.PowerApps/apis/connections",
            "suggestedCreationType": "Existing", "creationType": "Existing",
            "details": {"displayName": "Select your existing SharePoint connection"},
            "configurableBy": "User", "hierarchy": "Child", "dependsOn": [api_id],
        }
        document["properties"]["connectionReferences"] = {connector: {
            "connectionName": "IMPORT_SELECT_EXISTING_SHAREPOINT_CONNECTION",
            "source": "Embedded", "id": api_path, "tier": "NotSpecified",
            "apiName": "sharepointonline", "isProcessSimpleApiReferenceConversionAlreadyDone": False,
        }}
        definition["actions"] = {
            "Read_site_identity": {
                "type": "OpenApiConnection", "runAfter": {},
                "inputs": {
                    "parameters": {
                        "dataset": sharepoint_site.rstrip("/"),
                        "parameters/method": "GET",
                        "parameters/uri": "_api/web?$select=Id",
                        "parameters/headers": {"Accept": "application/json;odata=nometadata"},
                    },
                    "host": {"apiId": api_path, "connectionName": connector, "operationId": "HttpRequest"},
                    "authentication": "@parameters('$authentication')",
                },
            },
            "Respond_to_a_Power_App_or_flow": definition["actions"]["Respond_to_a_Power_App_or_flow"],
        }
        response = definition["actions"]["Respond_to_a_Power_App_or_flow"]
        response["runAfter"] = {"Read_site_identity": ["Succeeded"]}
        response["inputs"]["body"] = {
            "success": "@not(empty(body('Read_site_identity')?['Id']))",
            "message": "@if(empty(body('Read_site_identity')?['Id']), 'SHAREPOINT_READ_EMPTY', 'SHAREPOINT_IMPORT_PROBE_OK')",
        }
    prefix = f"Microsoft.Flow/flows/{asset_id}"
    entries = {
        f"{prefix}/apisMap.json": api_map,
        f"{prefix}/connectionsMap.json": connection_map,
        f"{prefix}/definition.json": document,
        "Microsoft.Flow/flows/manifest.json": {"packageSchemaVersion": "1.0", "flowAssets": {"assetPaths": [asset_id]}},
        "manifest.json": manifest,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "x", ZIP_DEFLATED) as archive:
        for name, payload in entries.items():
            archive.writestr(name, json.dumps(payload, indent=2) + "\n")
    return document


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[2] / "artifacts" / "import_probe" / "TandemImportProbe.zip")
    parser.add_argument("--sharepoint-site", help="Build a read-only SharePoint probe using an existing connection selected during import")
    args = parser.parse_args()
    document = build_package(args.output, sharepoint_site=args.sharepoint_site)
    readable = args.output.with_suffix(".definition.json")
    if not readable.exists():
        readable.write_bytes((json.dumps(document, indent=2) + "\n").encode("utf-8"))
    print(f"Prepared: {args.output}")
    message = "SHAREPOINT_IMPORT_PROBE_OK" if args.sharepoint_site else EXPECTED_MESSAGE
    print(f"Expected test output: success=true, message={message}")
    print("Tenant import/run NOT verified. Import only as Create as new.")


if __name__ == "__main__":
    main()
