"""Unit tests for the Bash-runnable Microsoft Graph provisioner."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
PROVISIONER_PATH = ROOT / "scripts" / "sharepoint" / "provision.py"


def load_provisioner():
    spec = importlib.util.spec_from_file_location("provision", PROVISIONER_PATH)
    if spec is None or spec.loader is None:
        raise AssertionError(f"Could not load provisioner: {PROVISIONER_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_parse_site_url() -> None:
    provisioner = load_provisioner()

    assert provisioner.parse_site_url(
        "https://reedelsevier.sharepoint.com/sites/OG-TandemOrg/"
    ) == ("reedelsevier.sharepoint.com", "/sites/OG-TandemOrg")


def test_person_column_payload_is_single_person_only() -> None:
    provisioner = load_provisioner()

    payload = provisioner.build_column_payload(
        {
            "internalName": "ParticipantAccount",
            "displayName": "Participant account",
            "type": "User",
            "required": True,
        }
    )

    assert payload["personOrGroup"] == {
        "allowMultipleSelection": False,
        "chooseFromType": "peopleOnly",
        "displayAs": "nameWithPresence",
    }
    assert payload["required"] is True


def test_choice_column_does_not_allow_free_text() -> None:
    provisioner = load_provisioner()

    payload = provisioner.build_column_payload(
        {
            "internalName": "Status",
            "displayName": "Status",
            "type": "Choice",
            "choices": ["Active", "Needs review"],
        }
    )

    assert payload["choice"]["choices"] == ["Active", "Needs review"]
    assert payload["choice"]["allowTextEntry"] is False


def test_flow_derived_column_is_hidden() -> None:
    provisioner = load_provisioner()

    payload = provisioner.build_column_payload(
        {
            "internalName": "TimeZone",
            "displayName": "Time zone",
            "type": "Text",
            "hidden": True,
            "provisioning": "flow-derived",
        }
    )

    assert payload["hidden"] is True


def test_lookup_payload_uses_source_list_and_multiple_selection() -> None:
    provisioner = load_provisioner()

    payload = provisioner.build_lookup_payload(
        {
            "internalName": "TeachLanguages",
            "displayName": "Teach languages",
            "type": "Lookup",
            "lookupList": "Language catalogue",
            "lookupField": "Title",
            "allowMultiple": True,
        },
        {"id": "language-list-id", "displayName": "Language catalogue"},
        {"Title": {"id": "title-column-id", "name": "Title"}},
        indexed=False,
    )

    assert payload["lookup"] == {
        "listId": "language-list-id",
        "columnName": "Title",
        "allowMultipleValues": True,
    }


def test_location_is_not_created_by_graph_provisioner() -> None:
    provisioner = load_provisioner()

    # The current design intentionally keeps this rich SharePoint field manual.
    with pytest.raises(ValueError, match="Cannot create field type through Graph"):
        provisioner.build_column_payload(
            {"internalName": "Location", "displayName": "Location", "type": "Location"}
        )
