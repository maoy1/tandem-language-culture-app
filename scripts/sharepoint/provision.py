"""Provision and validate the current SharePoint schema through Microsoft Graph.

Authentication uses an access token from GRAPH_ACCESS_TOKEN or the Azure CLI.
This keeps the workflow runnable from Bash and avoids a PowerShell dependency.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


GRAPH_BASE = "https://graph.microsoft.com/v1.0"


class GraphError(RuntimeError):
    """Raised when Microsoft Graph returns an error response."""


def load_schema(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        schema = json.load(handle)
    if not isinstance(schema, dict) or not isinstance(schema.get("lists"), list):
        raise ValueError("Schema must be an object with a lists array.")
    return schema


def parse_site_url(site_url: str) -> tuple[str, str]:
    parsed = urlparse(site_url)
    if parsed.scheme not in {"https", "http"} or not parsed.netloc:
        raise ValueError("Site URL must be an absolute SharePoint URL.")
    path = parsed.path.rstrip("/") or "/"
    return parsed.netloc, path


def get_access_token() -> str:
    token = os.environ.get("GRAPH_ACCESS_TOKEN")
    if token:
        return token

    try:
        result = subprocess.run(
            ["az", "account", "get-access-token", "--resource-type", "ms-graph", "--output", "json"],
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise GraphError(
            "No GRAPH_ACCESS_TOKEN was supplied and Azure CLI (az) was not found. "
            "Install Azure CLI and run 'az login', or export GRAPH_ACCESS_TOKEN."
        ) from exc
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout).strip()
        raise GraphError(
            "Azure CLI could not provide a Microsoft Graph token. Run 'az login' first. "
            f"Details: {detail}"
        ) from exc

    token = json.loads(result.stdout).get("accessToken")
    if not token:
        raise GraphError("Azure CLI returned no access token.")
    return token


class GraphClient:
    def __init__(self, token: str) -> None:
        self.token = token

    def request(self, method: str, endpoint: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        url = endpoint if endpoint.startswith("https://") else GRAPH_BASE + endpoint
        headers = {"Authorization": f"Bearer {self.token}", "Accept": "application/json"}
        data = None
        if body is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(body).encode("utf-8")
        request = Request(url, data=data, headers=headers, method=method)
        try:
            with urlopen(request) as response:
                raw = response.read().decode("utf-8")
        except HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace")
            try:
                error = json.loads(raw).get("error", {})
                message = error.get("message", raw)
            except json.JSONDecodeError:
                message = raw
            raise GraphError(f"Graph request failed ({exc.code}): {message}") from exc
        except URLError as exc:
            raise GraphError(f"Graph request could not connect: {exc.reason}") from exc
        return json.loads(raw) if raw else {}

    def paged(self, endpoint: str) -> Iterable[dict[str, Any]]:
        next_endpoint: str | None = endpoint
        while next_endpoint:
            response = self.request("GET", next_endpoint)
            yield from response.get("value", [])
            next_endpoint = response.get("@odata.nextLink")


def find_site(client: GraphClient, site_url: str) -> dict[str, Any]:
    hostname, path = parse_site_url(site_url)
    endpoint = f"/sites/{hostname}:{path}?$select=id,displayName,webUrl"
    return client.request("GET", endpoint)


def find_lists(client: GraphClient, site_id: str) -> dict[str, dict[str, Any]]:
    endpoint = f"/sites/{site_id}/lists?$select=id,displayName"
    return {item["displayName"]: item for item in client.paged(endpoint)}


def find_columns(client: GraphClient, site_id: str, list_id: str) -> dict[str, dict[str, Any]]:
    endpoint = (
        f"/sites/{site_id}/lists/{list_id}/columns"
        "?$select=id,name,displayName,required,hidden,indexed,enforceUniqueValues"
    )
    return {item["name"]: item for item in client.paged(endpoint)}


def build_column_payload(field: dict[str, Any], indexed: bool = False) -> dict[str, Any]:
    field_type = field["type"]
    payload: dict[str, Any] = {
        "name": field["internalName"],
        "displayName": field["displayName"],
        "required": field.get("required", False),
        "hidden": field.get("hidden", False),
        "enforceUniqueValues": field.get("unique", False),
        "indexed": indexed,
    }
    if field_type == "Text":
        payload["text"] = {"allowMultipleLines": False}
    elif field_type == "Note":
        payload["text"] = {"allowMultipleLines": True, "textType": "plain"}
    elif field_type == "Boolean":
        payload["boolean"] = {}
    elif field_type == "Choice":
        payload["choice"] = {
            "choices": field["choices"],
            "allowTextEntry": False,
            "displayAs": "dropDownMenu",
        }
    elif field_type == "DateTime":
        payload["dateTime"] = {"format": "dateTime"}
    elif field_type == "Number":
        payload["number"] = {}
    elif field_type == "User":
        payload["personOrGroup"] = {
            "allowMultipleSelection": False,
            "chooseFromType": "peopleOnly",
            "displayAs": "nameWithPresence",
        }
    else:
        raise ValueError(f"Cannot create field type through Graph: {field_type}")
    return payload


def build_lookup_payload(
    field: dict[str, Any], target_list: dict[str, Any], target_columns: dict[str, dict[str, Any]], indexed: bool
) -> dict[str, Any]:
    target_field = field["lookupField"]
    if target_field not in target_columns:
        raise GraphError(
            f"Lookup target column does not exist: {target_list['displayName']}.{target_field}"
        )
    return {
        "name": field["internalName"],
        "displayName": field["displayName"],
        "required": field.get("required", False),
        "hidden": field.get("hidden", False),
        "enforceUniqueValues": field.get("unique", False),
        "indexed": indexed,
        "lookup": {
            "listId": target_list["id"],
            "columnName": target_field,
            "allowMultipleValues": field.get("allowMultiple", False),
        },
    }


def print_result(level: str, message: str) -> None:
    print(f"[{level}] {message}")


def provision(schema: dict[str, Any], client: GraphClient, site_url: str, validate_only: bool) -> int:
    site = find_site(client, site_url)
    site_id = site["id"]
    print_result("OK", f"Connected to site: {site.get('webUrl', site_url)}")
    existing_lists = find_lists(client, site_id)
    errors = 0

    for list_definition in schema["lists"]:
        list_name = list_definition["name"]
        list_item = existing_lists.get(list_name)
        if list_item is None:
            if validate_only:
                print_result("ERROR", f"Missing list: {list_name}")
                errors += 1
                continue
            list_item = client.request(
                "POST",
                f"/sites/{site_id}/lists",
                {"displayName": list_name, "list": {"template": "genericList"}},
            )
            existing_lists[list_name] = list_item
            print_result("CREATE", f"Created list: {list_name}")
        else:
            print_result("OK", f"List exists: {list_name}")

        columns = find_columns(client, site_id, list_item["id"])
        indexes = set(list_definition.get("indexes", []))
        for field in list_definition.get("fields", []):
            internal_name = field["internalName"]
            if field.get("type") == "Location":
                print_result(
                    "MANUAL",
                    f"{list_name}.{internal_name} must be created or checked in SharePoint as a Location field.",
                )
                continue
            current = columns.get(internal_name)
            if current is not None:
                if field.get("hidden", False) != bool(current.get("hidden", False)):
                    expected = "hidden" if field.get("hidden", False) else "visible"
                    print_result("ERROR", f"Field is not {expected}: {list_name}.{internal_name}")
                    errors += 1
                elif field.get("unique", False) and not current.get("enforceUniqueValues", False):
                    print_result("ERROR", f"Field is not unique: {list_name}.{internal_name}")
                    errors += 1
                elif field.get("required", False) and not current.get("required", False):
                    print_result("ERROR", f"Field is not required: {list_name}.{internal_name}")
                    errors += 1
                elif internal_name in indexes and not current.get("indexed", False):
                    print_result("ERROR", f"Missing index: {list_name}.{internal_name}")
                    errors += 1
                else:
                    print_result("OK", f"Field exists: {list_name}.{internal_name}")
                continue

            if validate_only:
                print_result("ERROR", f"Missing field: {list_name}.{internal_name}")
                errors += 1
                continue

            try:
                if field.get("type") == "Lookup":
                    target_list = existing_lists.get(field["lookupList"])
                    if target_list is None:
                        raise GraphError(f"Lookup target list is missing: {field['lookupList']}")
                    target_columns = find_columns(client, site_id, target_list["id"])
                    payload = build_lookup_payload(field, target_list, target_columns, internal_name in indexes)
                else:
                    payload = build_column_payload(field, internal_name in indexes)
                client.request("POST", f"/sites/{site_id}/lists/{list_item['id']}/columns", payload)
                print_result("CREATE", f"Created field: {list_name}.{internal_name}")
            except (GraphError, ValueError) as exc:
                print_result("ERROR", f"{list_name}.{internal_name}: {exc}")
                errors += 1

    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-url", required=True, help="SharePoint site URL")
    parser.add_argument(
        "--schema-path",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "config" / "sharepoint_schema.json",
    )
    parser.add_argument("--validate-only", action="store_true", help="Do not create lists or columns")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        schema = load_schema(args.schema_path)
        client = GraphClient(get_access_token())
        errors = provision(schema, client, args.site_url, args.validate_only)
    except (GraphError, ValueError, json.JSONDecodeError) as exc:
        print_result("ERROR", str(exc))
        return 1
    if args.validate_only:
        print("Validation completed. ERROR entries require attention; MANUAL entries require one-time SharePoint checks.")
    else:
        print("Provisioning completed. Review ERROR and MANUAL entries before using the lists.")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
