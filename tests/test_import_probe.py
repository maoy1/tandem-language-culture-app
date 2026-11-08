"""Safety checks for the disposable import probe, not tenant import validation."""
import importlib.util
import json
from pathlib import Path
from zipfile import ZipFile

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "power_automate" / "build_import_probe.py"
spec = importlib.util.spec_from_file_location("build_import_probe", SCRIPT)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


def contents(path):
    with ZipFile(path) as archive:
        assert archive.testzip() is None
        return {name: json.loads(archive.read(name)) for name in archive.namelist()}


def test_package_has_one_new_flow_and_no_connection_dependencies(tmp_path):
    path = tmp_path / "probe.zip"
    probe.build_package(path)
    entries = contents(path)
    resources = entries["manifest.json"]["resources"]
    assert len(resources) == 1
    asset_id, resource = next(iter(resources.items()))
    assert resource["suggestedCreationType"] == "New"
    assert resource["type"] == "Microsoft.Flow/flows"
    assert resource["dependsOn"] == []
    assert entries["Microsoft.Flow/flows/manifest.json"]["flowAssets"]["assetPaths"] == [asset_id]
    assert entries[f"Microsoft.Flow/flows/{asset_id}/apisMap.json"] == {}
    assert entries[f"Microsoft.Flow/flows/{asset_id}/connectionsMap.json"] == {}
    document = entries[f"Microsoft.Flow/flows/{asset_id}/definition.json"]
    assert document["properties"]["connectionReferences"] == {}


def test_flow_is_manual_connector_free_and_returns_only_probe_result(tmp_path):
    document = probe.build_package(tmp_path / "probe.zip")
    definition = document["properties"]["definition"]
    assert len(definition["triggers"]) == 1
    assert definition["triggers"]["manual"]["kind"] == "PowerAppV2"
    assert not definition["triggers"]["manual"].get("recurrence")
    actions = definition["actions"]
    assert {a["type"] for a in actions.values()} == {"Compose", "Response"}
    assert len(actions) == 2
    assert all(not a["inputs"].get("host") if isinstance(a["inputs"], dict) else True for a in actions.values())
    assert actions["Probe_message"]["inputs"] == "IMPORT_PROBE_OK"
    response = actions["Respond_to_a_Power_App_or_flow"]
    assert response["runAfter"] == {"Probe_message": ["Succeeded"]}
    assert response["inputs"]["body"] == {"success": True, "message": "@outputs('Probe_message')"}
    assert "sharepoint.com" not in json.dumps(document)
    assert "TandemRespondRequest" not in json.dumps(document)


def test_fresh_builds_get_distinct_flow_identifiers(tmp_path):
    first = probe.build_package(tmp_path / "one.zip")
    second = probe.build_package(tmp_path / "two.zip")
    assert first["name"] != second["name"]
    assert first["id"] != second["id"]


def test_builder_refuses_to_replace_an_existing_file(tmp_path):
    path = tmp_path / "existing.zip"
    path.write_bytes(b"keep existing artifact")
    with pytest.raises(FileExistsError):
        probe.build_package(path)
    assert path.read_bytes() == b"keep existing artifact"


def test_sharepoint_probe_maps_existing_connection_and_only_reads_site_identity(tmp_path):
    path = tmp_path / "sharepoint.zip"
    document = probe.build_package(path, sharepoint_site="https://example.sharepoint.com/sites/Tandem")
    entries = contents(path)
    resources = entries["manifest.json"]["resources"]
    assert len(resources) == 3
    flow_id = next(k for k, v in resources.items() if v["type"] == "Microsoft.Flow/flows")
    prefix = f"Microsoft.Flow/flows/{flow_id}"
    api_id = entries[f"{prefix}/apisMap.json"]["shared_sharepointonline"]
    connection_id = entries[f"{prefix}/connectionsMap.json"]["shared_sharepointonline"]
    assert set(resources[flow_id]["dependsOn"]) == {api_id, connection_id}
    assert resources[connection_id]["creationType"] == "Existing"
    assert resources[connection_id]["dependsOn"] == [api_id]
    ref = document["properties"]["connectionReferences"]["shared_sharepointonline"]
    assert ref["source"] == "Embedded"
    assert ref["connectionName"] == "IMPORT_SELECT_EXISTING_SHAREPOINT_CONNECTION"
    actions = document["properties"]["definition"]["actions"]
    assert set(actions) == {"Read_site_identity", "Respond_to_a_Power_App_or_flow"}
    read = actions["Read_site_identity"]["inputs"]
    assert read["parameters"]["parameters/method"] == "GET"
    assert read["parameters"]["parameters/uri"] == "_api/web?$select=Id"
    assert read["host"]["operationId"] == "HttpRequest"
    assert actions["Respond_to_a_Power_App_or_flow"]["runAfter"] == {"Read_site_identity": ["Succeeded"]}
    response = actions["Respond_to_a_Power_App_or_flow"]["inputs"]["body"]
    assert "SHAREPOINT_IMPORT_PROBE_OK" in response["message"]
    assert "not(empty(" in response["success"]
    assert "siteid" not in response
    assert "TandemRespondRequest" not in json.dumps(document)


@pytest.mark.parametrize("site", ["http://example.sharepoint.com", "https://example.com", "https://example.sharepoint.com?token=secret"])
def test_sharepoint_probe_rejects_non_sharepoint_or_secret_bearing_urls(tmp_path, site):
    with pytest.raises(ValueError):
        probe.build_package(tmp_path / "probe.zip", sharepoint_site=site)
    assert not (tmp_path / "probe.zip").exists()
