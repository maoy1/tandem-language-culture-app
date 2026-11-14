"""Regression checks for observed native Solution connection/caller packaging."""
from copy import deepcopy
import json
from xml.etree import ElementTree as ET
from zipfile import ZipFile

import pytest
from scripts.power_automate import solution_source as native

SITE = "https://example.sharepoint.com/sites/test"
CHILD = "11111111-1111-4111-8111-111111111111"
PARENT = "22222222-2222-4222-8222-222222222222"


def export_fixture(path, change=None):
    solution = ET.Element("ImportExportXml")
    manifest = ET.SubElement(solution, "SolutionManifest")
    for key, value in [("UniqueName", "TandemSharedValidation81"), ("Version", "1.0.0.2"), ("Managed", "0")]:
        ET.SubElement(manifest, key).text = value
    roots = ET.SubElement(manifest, "RootComponents")
    custom = ET.Element("ImportExportXml")
    workflows = ET.SubElement(custom, "Workflows")
    refs = ET.SubElement(custom, "connectionreferences")
    component = ET.SubElement(refs, "connectionreference", {"connectionreferencelogicalname": "fixture_sp_reference"})
    ET.SubElement(component, "connectorid").text = native.SP_API
    trigger = {"manual": {"type": "Request", "kind": "Button", "inputs": {"schema": {"type": "object", "properties": {}}}}}
    child = {"properties": {"connectionReferences": {}, "definition": {"triggers": trigger, "actions": {
        "Validation_report": {"type": "Compose", "inputs": {"packageBuildId": "unit-build"}, "runAfter": {}}}}}}
    read = {"type": "OpenApiConnection", "runAfter": {}, "inputs": {
        "host": {"connectionName": "shared_sharepointonline", "apiId": native.SP_API, "operationId": "HttpRequest"},
        "parameters": {"dataset": SITE, "parameters/method": "GET", "parameters/uri": "_api/web/currentuser?$select=Id"},
        "authentication": {"type": "Raw", "value": native.RAW_INVOKER}}}
    call = {"type": "Workflow", "inputs": {"host": {"workflowReferenceName": CHILD}, "body": {"text": json.dumps({
        "contractVersion": 1, "rulesVersion": 1, "mode": "NORMALIZE", "profiles": [],
        "catalogues": {"languageIds": [], "cultureIds": [], "timezoneIds": [], "anyLanguageId": None}})}}, "runAfter": {"Read_caller": ["Succeeded"]}}
    ref = {"runtimeSource": "invoker", "connection": {"connectionReferenceLogicalName": "fixture_sp_reference"},
           "api": {"name": "shared_sharepointonline"}}
    probe = {"properties": {"connectionReferences": {"shared_sharepointonline": ref}, "definition": {
        "parameters": {"$connections": {"defaultValue": {}, "type": "Object"}, "$authentication": {"defaultValue": {}, "type": "SecureObject"}},
        "triggers": deepcopy(trigger), "actions": {"Read_caller": read, "Call_child": call}}}}
    if change == "embedded": ref["runtimeSource"] = "embedded"
    elif change == "api": ref["api"]["name"] = "shared_http"
    elif change == "logical": ref["connection"]["connectionReferenceLogicalName"] = "missing"
    elif change == "auth": read["inputs"]["authentication"]["value"] = "OWNER_CREDENTIAL_NOT_ALLOWED"
    elif change == "site": read["inputs"]["parameters"]["dataset"] = "https://other.example"
    elif change == "write": read["inputs"]["parameters"]["parameters/method"] = "POST"
    elif change == "child": call["inputs"]["host"]["workflowReferenceName"] = "wrong"
    elif change == "build": child["properties"]["definition"]["actions"]["Validation_report"]["inputs"]["packageBuildId"] = "old"
    elif change == "managed": manifest.find("Managed").text = "1"
    elif change == "more_actions": probe["properties"]["definition"]["actions"]["Unexpected"] = deepcopy(read)
    elif change == "component": component.find("connectorid").text = "unverified"
    elif change == "payload": call["inputs"]["body"]["text"] = '{"mode":"GROUP"}'
    docs = {"TandemValidateContext": (CHILD, child), "Tandem81CallerProbe": (PARENT, probe)}
    entries = {}
    for name, (id_, doc) in docs.items():
        file = "Workflows/" + name + "-" + id_ + ".json"
        node = ET.SubElement(workflows, "Workflow", {"WorkflowId": "{"+id_+"}", "Name": name})
        ET.SubElement(node, "JsonFileName").text = "/" + file
        ET.SubElement(roots, "RootComponent", {"type": "29", "id": "{"+id_+"}"})
        entries[file] = json.dumps(doc).encode()
    if change == "root": roots[0].set("id", "{wrong}")
    entries.update({"customizations.xml": ET.tostring(custom), "solution.xml": ET.tostring(solution)})
    with ZipFile(path, "w") as z:
        for name, data in entries.items(): z.writestr(name, data)


def test_native_manual_invoker_source_is_resolved_without_certifying_other_users(tmp_path):
    path = tmp_path / "native.zip";export_fixture(path)
    seed = native.inspect_caller_export(path, SITE, "unit-build")
    receipt = seed["receipt"]
    assert receipt["runtimeSource"] == "invoker"
    assert receipt["connectionReferenceLogicalName"] == "fixture_sp_reference"
    assert receipt["sharedChildId"] == CHILD
    assert receipt["probeActions"] == {"actions": 2, "maximumActionDepth": 1}
    assert receipt["ordinaryUserAccessVerified"] is False
    assert receipt["businessWritesVerified"] is False


@pytest.mark.parametrize("change", ["embedded", "api", "logical", "auth", "site", "write",
                                    "child", "build", "managed", "more_actions", "component", "payload", "root"])
def test_unsupported_or_changed_source_must_not_be_silently_reused(tmp_path, change):
    path = tmp_path / "native.zip";export_fixture(path, change)
    with pytest.raises(ValueError): native.inspect_caller_export(path, SITE, "unit-build")


def test_interactive_template_preserves_native_binding_and_does_not_mutate_source(tmp_path):
    path = tmp_path / "native.zip";export_fixture(path)
    seed = native.inspect_caller_export(path, SITE, "unit-build")
    before = deepcopy(seed["probe"])
    trigger = {"manual": {"type": "Request", "kind": "PowerAppV2", "inputs": {"schema": {
        "type": "object", "properties": {"number": {"type": "number"}}, "required": ["number"]}}}}
    actions = deepcopy(seed["probe"]["properties"]["definition"]["actions"])
    actions["Read_caller"]["inputs"]["host"]["connectionName"] = "old_legacy_key"
    actions["Read_caller"]["inputs"].pop("authentication")
    doc = native.invoker_parent_document(seed, trigger, actions)
    assert doc["properties"]["definition"]["triggers"] == trigger
    assert doc["properties"]["connectionReferences"] == before["properties"]["connectionReferences"]
    read = doc["properties"]["definition"]["actions"]["Read_caller"]["inputs"]
    assert read["authentication"]["value"] == native.RAW_INVOKER
    assert read["host"]["connectionName"] == "shared_sharepointonline"
    assert seed["probe"] == before


@pytest.mark.parametrize("change", ["automated", "connector", "site", "child", "external", "webhook", "script"])
def test_template_cannot_introduce_unverified_runtime_or_automated_owner_binding(tmp_path, change):
    path = tmp_path / "native.zip";export_fixture(path)
    seed = native.inspect_caller_export(path, SITE, "unit-build")
    trigger = deepcopy(seed["probe"]["properties"]["definition"]["triggers"])
    actions = deepcopy(seed["probe"]["properties"]["definition"]["actions"])
    if change == "automated": trigger["manual"] = {"type": "OpenApiConnection"}
    elif change == "connector": actions["Read_caller"]["inputs"]["host"]["apiId"] = "premium"
    elif change == "site": actions["Read_caller"]["inputs"]["parameters"]["dataset"] = "https://other.example"
    elif change == "child": actions["Call_child"]["inputs"]["host"]["workflowReferenceName"] = "other-child"
    else: actions["Unexpected"] = {"type": {"webhook": "OpenApiConnectionWebhook", "script": "JavaScriptCode"}.get(change, "Http"), "inputs": {}, "runAfter": {}}
    with pytest.raises(ValueError): native.invoker_parent_document(seed, trigger, actions)
