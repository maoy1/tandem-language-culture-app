"""Validate the participant self-registration contract against the schema."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return value


def validate(policy: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    list_name = policy.get("list")
    list_definition = next(
        (item for item in schema.get("lists", []) if item.get("name") == list_name),
        None,
    )
    if list_definition is None:
        return [f"Registration list does not exist in schema: {list_name!r}."]

    fields = {
        field.get("internalName"): field
        for field in list_definition.get("fields", [])
    }
    identity = policy.get("identity", {})
    identity_name = identity.get("field")
    identity_field = fields.get(identity_name)
    if identity_field is None:
        errors.append(f"Identity field does not exist in schema: {identity_name!r}.")
    else:
        if identity_field.get("type") != "User":
            errors.append("The registration identity field must be a User field.")
        if identity.get("required") is not True:
            errors.append("The registration identity must be required.")
        if identity.get("unique") is not True:
            errors.append("The registration identity must be unique.")
        if identity.get("participantEditable") is not False:
            errors.append("Participants must not be able to change the identity field.")

    access = policy.get("access", {})
    if access.get("approvalRequired") is not False:
        errors.append("Initial registration must not require administrator approval.")
    if access.get("participantCreate") != "own_profile":
        errors.append("participantCreate must be restricted to own_profile.")
    for key in ("participantRead", "participantUpdate"):
        if access.get(key) not in {"own_profile", "app_filtered_own_profile"}:
            errors.append(f"{key} must be restricted to the participant's own profile.")
    if access.get("participantDelete") is not False:
        errors.append("Participant deletion must not be enabled by this contract.")

    form = policy.get("form", {})
    visible = set(form.get("visibleFields", []))
    hidden = set(form.get("hiddenFields", []))
    unknown = (visible | hidden) - set(fields)
    if unknown:
        errors.append(f"Form refers to unknown fields: {sorted(unknown)!r}.")
    overlap = visible & hidden
    if overlap:
        errors.append(f"Form fields cannot be both visible and hidden: {sorted(overlap)!r}.")
    if form.get("mode") != "create_or_edit_own_profile":
        errors.append("The form must support create_or_edit_own_profile.")
    if identity_name not in visible:
        errors.append("The identity field must be present in the form contract.")
    for managed in ("Title", "Status"):
        if managed in fields and managed not in hidden:
            errors.append(f"Flow/system-managed field must be hidden: {managed!r}.")

    if access.get("sharepointItemLevelPermissions") != "unavailable_with_unique_identity":
        errors.append(
            "The registration contract must record that built-in SharePoint "
            "item-level permissions are unavailable with the unique identity field."
        )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("policy", type=Path)
    parser.add_argument("schema", type=Path)
    args = parser.parse_args()
    errors = validate(load_json(args.policy), load_json(args.schema))
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"Registration policy is valid: {args.policy}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
