"""Validate the declarative SharePoint schema without connecting to a tenant."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


SUPPORTED_TYPES = {"Text", "Note", "Boolean", "DateTime", "Choice", "Number", "User", "Lookup", "Location"}


def load_schema(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        schema = json.load(handle)
    if not isinstance(schema, dict) or not isinstance(schema.get("lists"), list):
        raise ValueError("Schema must be an object with a lists array.")
    return schema


def validate(schema: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    lists = schema["lists"]
    list_names = [item.get("name") for item in lists]

    if len(list_names) != len(set(list_names)):
        errors.append("List names must be unique.")

    known_lists = set(list_names)
    for list_definition in lists:
        list_name = list_definition.get("name", "<unnamed list>")
        fields = list_definition.get("fields", [])
        internal_names = [field.get("internalName") for field in fields]

        if len(internal_names) != len(set(internal_names)):
            errors.append(f"{list_name}: field internal names must be unique.")

        for field in fields:
            field_name = field.get("internalName", "<unnamed field>")
            field_type = field.get("type")
            if field_type not in SUPPORTED_TYPES:
                errors.append(f"{list_name}.{field_name}: unsupported type {field_type!r}.")
            if field_type == "Choice" and not field.get("choices"):
                errors.append(f"{list_name}.{field_name}: choices are required.")
            if field_type == "Lookup":
                lookup_list = field.get("lookupList")
                if lookup_list not in known_lists:
                    errors.append(f"{list_name}.{field_name}: unknown lookup list {lookup_list!r}.")
                if not field.get("lookupField"):
                    errors.append(f"{list_name}.{field_name}: lookupField is required.")
            if field_type == "Location" and field.get("provisioning") != "manual":
                errors.append(f"{list_name}.{field_name}: Location fields must be marked manual.")

        for index in list_definition.get("indexes", []):
            if index not in internal_names:
                errors.append(f"{list_name}: index refers to missing field {index!r}.")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("schema", type=Path)
    args = parser.parse_args()
    errors = validate(load_schema(args.schema))
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"Schema is valid: {args.schema}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
