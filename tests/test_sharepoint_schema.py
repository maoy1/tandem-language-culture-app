"""Tests for the declarative SharePoint schema and its validator."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "config" / "sharepoint_schema.json"
VALIDATOR_PATH = ROOT / "scripts" / "sharepoint" / "validate_schema.py"


def load_validator():
    spec = importlib.util.spec_from_file_location("validate_schema", VALIDATOR_PATH)
    if spec is None or spec.loader is None:
        raise AssertionError(f"Could not load validator: {VALIDATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_current_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def fields_by_name(list_definition: dict) -> dict:
    return {field["internalName"]: field for field in list_definition["fields"]}


def test_current_schema_passes_validator() -> None:
    validator = load_validator()
    schema = load_current_schema()

    assert validator.validate(schema) == []


def test_current_schema_contains_only_initial_registration_lists() -> None:
    schema = load_current_schema()

    assert [item["name"] for item in schema["lists"]] == [
        "Language catalogue",
        "Participants",
    ]


def test_language_catalogue_has_controlled_values() -> None:
    schema = load_current_schema()
    language_catalogue = next(
        item for item in schema["lists"] if item["name"] == "Language catalogue"
    )
    fields = fields_by_name(language_catalogue)

    assert fields["Title"]["required"] is True
    assert fields["ISOCode"]["required"] is True
    assert fields["ISOCode"]["unique"] is True
    assert fields["Active"]["defaultValue"] is True
    assert "ISOCode" in language_catalogue["indexes"]


def test_participants_schema_matches_current_design() -> None:
    schema = load_current_schema()
    participants = next(
        item for item in schema["lists"] if item["name"] == "Participants"
    )
    fields = fields_by_name(participants)

    assert fields["ParticipantAccount"]["required"] is True
    assert fields["ParticipantAccount"]["unique"] is True
    assert fields["Location"] == {
        "internalName": "Location",
        "displayName": "Location",
        "type": "Location",
        "provisioning": "manual",
        "required": True,
    }
    assert fields["TeachLanguages"]["allowMultiple"] is True
    assert fields["LearnLanguages"]["allowMultiple"] is True
    assert fields["TeachLanguages"]["lookupList"] == "Language catalogue"
    assert fields["LearnLanguages"]["lookupList"] == "Language catalogue"
    assert fields["TimeZone"]["hidden"] is True
    assert fields["TimeZone"]["provisioning"] == "flow-derived"
    assert fields["TimeZone"]["editableByParticipants"] is False
    assert fields["Status"]["choices"] == ["Active", "Needs review"]
    assert "Status" in participants["indexes"]
    assert "ParticipantAccount" in participants["indexes"]


def test_removed_catalogues_and_fields_are_absent() -> None:
    schema = load_current_schema()
    list_names = {item["name"] for item in schema["lists"]}
    participant = next(
        item for item in schema["lists"] if item["name"] == "Participants"
    )
    participant_fields = set(fields_by_name(participant))

    assert "Culture catalogue" not in list_names
    assert "Time zone catalogue" not in list_names
    assert "Location catalogue" not in list_names
    assert participant_fields.isdisjoint(
        {
            "CultureInterests",
            "OpenToOtherCultures",
            "Role",
            "ConsentConfirmed",
            "Country",
            "OfficeCity",
        }
    )


def test_validator_rejects_unknown_lookup_target() -> None:
    validator = load_validator()
    schema = copy.deepcopy(load_current_schema())
    participants = next(
        item for item in schema["lists"] if item["name"] == "Participants"
    )
    teach_languages = next(
        field for field in participants["fields"] if field["internalName"] == "TeachLanguages"
    )
    teach_languages["lookupList"] = "Missing catalogue"

    errors = validator.validate(schema)

    assert any("unknown lookup list" in error for error in errors)


def test_validator_requires_manual_location_provisioning() -> None:
    validator = load_validator()
    schema = copy.deepcopy(load_current_schema())
    participants = next(
        item for item in schema["lists"] if item["name"] == "Participants"
    )
    location = next(
        field for field in participants["fields"] if field["internalName"] == "Location"
    )
    location["provisioning"] = "automatic"

    errors = validator.validate(schema)

    assert any("Location fields must be marked manual" in error for error in errors)
