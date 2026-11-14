"""Inspect the owner-tested #81 native Solution/Invoker connection envelope.

This module does not execute tokens, read tenant data, grant permissions or
certify ordinary-user access. It supplies only a validated packaging template.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

from .schema_audit import measure

SP_API = "/providers/Microsoft.PowerApps/apis/shared_sharepointonline"
RAW_INVOKER = "@json(decodeBase64(triggerOutputs().headers['X-MS-APIM-Tokens']))['$ConnectionKey']"


def walk(actions):
    for name, action in actions.items():
        yield name, action
        yield from walk(action.get("actions", {}))
        yield from walk(action.get("else", {}).get("actions", {}))
        for case in action.get("cases", {}).values():
            yield from walk(case.get("actions", {}))
        yield from walk(action.get("default", {}).get("actions", {}))


def inspect_caller_export(path, expected_site, expected_build):
    with ZipFile(path) as archive:
        if archive.testzip():
            raise ValueError("Corrupt native Solution")
        entries = {name: archive.read(name) for name in archive.namelist()}
    manifest = ET.fromstring(entries["solution.xml"]).find("SolutionManifest")
    custom = ET.fromstring(entries["customizations.xml"])
    if manifest.findtext("Managed") != "0":
        raise ValueError("Expected unmanaged native Solution")
    if manifest.findtext("UniqueName") != "TandemSharedValidation81":
        raise ValueError("Wrong native Solution")
    flows = {}
    for node in custom.findall("./Workflows/Workflow"):
        name = node.attrib["Name"]
        filename = node.findtext("JsonFileName").lstrip("/")
        if name in flows:
            raise ValueError("Duplicate workflow name")
        flows[name] = (node, json.loads(entries[filename]))
    if "TandemValidateContext" not in flows or "Tandem81CallerProbe" not in flows:
        raise ValueError("Native caller or shared child missing")
    child_node, child = flows["TandemValidateContext"]
    child_id = child_node.attrib["WorkflowId"].strip("{}").lower()
    child_definition = child["properties"]["definition"]
    if child["properties"].get("connectionReferences"):
        raise ValueError("Shared evaluator unexpectedly uses connections")
    child_report = child_definition["actions"]["Validation_report"]["inputs"]
    if child_report["packageBuildId"] != expected_build:
        raise ValueError("Unexpected native shared-child build")
    probe_node, probe = flows["Tandem81CallerProbe"]
    props = probe["properties"]
    refs = props["connectionReferences"]
    if len(refs) != 1:
        raise ValueError("Expected one SharePoint connection")
    key, ref = next(iter(refs.items()))
    if ref.get("runtimeSource") != "invoker":
        raise ValueError("Expected native Invoker; no embedded fallback")
    if ref.get("api", {}).get("name") != "shared_sharepointonline":
        raise ValueError("Unexpected connector")
    logical = ref.get("connection", {}).get("connectionReferenceLogicalName")
    components = [n for n in custom.findall("./connectionreferences/connectionreference")
                  if n.attrib.get("connectionreferencelogicalname") == logical]
    if not logical or len(components) != 1 or components[0].findtext("connectorid") != SP_API:
        raise ValueError("Unresolved SharePoint connection-reference component")
    actions = list(walk(props["definition"]["actions"]))
    reads = [a for _, a in actions if a["type"] == "OpenApiConnection"]
    calls = [a for _, a in actions if a["type"] == "Workflow"]
    if len(reads) != 1 or len(calls) != 1 or len(actions) != 2:
        raise ValueError("Unexpected probe actions; inspect before reusing")
    read = reads[0]["inputs"]
    if read["host"].get("connectionName") != key or read["host"].get("apiId") != SP_API:
        raise ValueError("Unbound native SharePoint action")
    if read["host"].get("operationId") != "HttpRequest":
        raise ValueError("Wrong native probe operation")
    params = read["parameters"]
    if (params.get("dataset") != expected_site or params.get("parameters/method") != "GET"
            or params.get("parameters/uri") != "_api/web/currentuser?$select=Id"):
        raise ValueError("Unexpected probe site/read scope")
    if read.get("authentication") != {"type": "Raw", "value": RAW_INVOKER}:
        raise ValueError("Unexpected authentication; do not substitute credentials")
    call = calls[0]["inputs"]
    if call.get("host", {}).get("workflowReferenceName", "").lower() != child_id:
        raise ValueError("Caller points to a different child")
    payload = json.loads(call.get("body", {}).get("text", ""))
    if (payload.get("contractVersion") != 1 or payload.get("rulesVersion") != 1
            or payload.get("mode") != "NORMALIZE" or payload.get("profiles") != []):
        raise ValueError("Unexpected caller-probe payload")
    workflow_ids = {n.attrib["WorkflowId"].strip("{}").lower() for n, _ in flows.values()}
    root_ids = {n.attrib["id"].strip("{}").lower()
                for n in manifest.findall("./RootComponents/RootComponent")
                if n.attrib.get("type") == "29"}
    if workflow_ids != root_ids:
        raise ValueError("Workflow root/component mismatch")
    receipt = {
        "sourceTicket": 81,
        "sourceExportSha256": hashlib.sha256(Path(path).read_bytes()).hexdigest(),
        "sourceFile": Path(path).name,
        "solutionName": manifest.findtext("UniqueName"),
        "solutionVersion": manifest.findtext("Version"),
        "unmanaged": True, "flowCount": len(flows),
        "probeActions": measure(props["definition"]["actions"]),
        "sharedActions": measure(child_definition["actions"]),
        "sharePointConnectionKey": key,
        "connectionReferenceLogicalName": logical,
        "runtimeSource": "invoker", "connector": SP_API,
        "sharedChildId": child_id, "sharedBuildId": expected_build,
        "probeFlowId": probe_node.attrib["WorkflowId"].strip("{}").lower(),
        "site": expected_site,
        "nativeConfigurationVerified": True,
        "ownerExecutionEvidence": "sharepoint-caller-probe.owner-evidence.json",
        "ordinaryUserAccessVerified": False,
        "powerAppsSolutionConsumerParity": "NOT_RUN",
        "automatedEventConnectionMode": "Not supplied by this manual Invoker probe",
        "businessWritesVerified": False,
    }
    return {"receipt": receipt, "probe": probe, "child": child,
            "connectionComponent": deepcopy(components[0])}


def invoker_parent_document(seed, trigger, actions):
    """Prepare an interactive parent using observed refs/auth, not new credentials.

    This is an unimported document template, not a deployment certificate.
    Automated event flows need a separately preserved/verified owner binding;
    they must never silently use this interactive Invoker adapter.
    """
    if len(trigger) != 1 or next(iter(trigger.values())).get("kind") not in ["Button", "PowerAppV2"]:
        raise ValueError("Only interactive parent triggers supported by this seed")
    doc = deepcopy(seed["probe"])
    props = doc["properties"]
    definition = props["definition"]
    definition["triggers"] = deepcopy(trigger)
    definition["actions"] = deepcopy(actions)
    observed_read = next(a["inputs"] for _, a in walk(seed["probe"]["properties"]["definition"]["actions"])
                         if a["type"] == "OpenApiConnection")
    for _, action in walk(definition["actions"]):
        kind = action["type"]
        if kind == "OpenApiConnection":
            inputs = action["inputs"]
            if inputs["host"].get("apiId") != SP_API:
                raise ValueError("No unverified additional connector")
            if inputs["parameters"].get("dataset") != seed["receipt"]["site"]:
                raise ValueError("Unexpected parent site")
            inputs["host"]["connectionName"] = seed["receipt"]["sharePointConnectionKey"]
            inputs["authentication"] = deepcopy(observed_read["authentication"])
        elif kind == "Workflow":
            if action["inputs"]["host"].get("workflowReferenceName") != seed["receipt"]["sharedChildId"]:
                raise ValueError("Only the verified shared child is supported")
        elif kind not in {
                "Compose", "ParseJson", "InitializeVariable", "SetVariable",
                "AppendToArrayVariable", "AppendToStringVariable", "IncrementVariable",
                "DecrementVariable", "Query", "Select", "If", "Switch", "Scope",
                "Foreach", "Until", "Response", "Terminate", "Wait"}:
            raise ValueError("No unverified runtime or connector")
    measure(definition["actions"])
    return doc
