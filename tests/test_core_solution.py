"""Packaging coverage: linkage, complete batch, disabled import and credentials."""
from copy import deepcopy
import json
from xml.etree import ElementTree as ET
from zipfile import ZipFile, ZIP_DEFLATED
import pytest

from scripts.power_automate import core_solution as core
from scripts.power_automate import solution_source as native
from test_solution_source import export_fixture, CHILD, SITE


def source(path):
    export_fixture(path)
    with ZipFile(path) as z:
        entries = {name: z.read(name) for name in z.namelist()}
    entries = {name.replace(CHILD, core.CONTRACT['nativeSharedChildTemplateId']):
        data.replace(CHILD.encode(), core.CONTRACT['nativeSharedChildTemplateId'].encode())
            .replace(SITE.encode(), core.batch_schema.CONTRACT['site'].encode())
            .replace(b'unit-build', b'c79b7b64-b3ce-4de3-aa74-0ed62bca1524')
        for name, data in entries.items()}
    custom = ET.fromstring(entries['customizations.xml'])
    for node in custom.findall('./Workflows/Workflow'):
        for key, value in [('StateCode', '1'), ('StatusCode', '2'), ('IntroducedVersion', '1.0.0.0')]:
            ET.SubElement(node, key).text = value
        names = ET.SubElement(node, 'LocalizedNames')
        ET.SubElement(names, 'LocalizedName', {'languagecode': '1033', 'description': node.attrib['Name']})
    solution = ET.fromstring(entries['solution.xml'])
    names = ET.SubElement(solution.find('SolutionManifest'), 'LocalizedNames')
    ET.SubElement(names, 'LocalizedName', {'languagecode': '1033', 'description': 'Fixture'})
    entries['customizations.xml'] = ET.tostring(custom)
    entries['solution.xml'] = ET.tostring(solution)
    with ZipFile(path, 'w', ZIP_DEFLATED) as z:
        for name, data in entries.items(): z.writestr(name, data)


def documents(path):
    seed = native.inspect_caller_export(path, core.batch_schema.CONTRACT['site'], 'c79b7b64-b3ce-4de3-aa74-0ed62bca1524')
    return {name: deepcopy(seed['child'] if name == 'TandemValidateContext' else seed['probe'])
            for name in core.CONTRACT['productionFlows']}


def test_batch_has_twelve_production_components_fresh_ids_and_disabled_state(tmp_path):
    original = tmp_path / 'native.zip'; source(original)
    docs = documents(original)
    expected = deepcopy(docs)
    output = tmp_path / 'batch.zip'
    review = core.assemble(original, docs, output)
    assert docs == expected  # no mutation of per-ticket artifacts
    assert review['productionFlowCount'] == 12 and review['maintenanceFlowCount'] == 1
    assert review['nativeResult'] == 'NOT_IMPORTED_NOT_TESTED'
    with ZipFile(output) as z:
        custom = ET.fromstring(z.read('customizations.xml'))
        solution = ET.fromstring(z.read('solution.xml'))
        nodes = custom.findall('./Workflows/Workflow')
        assert len(nodes) == 13
        assert all(n.findtext('StateCode') == '0' and n.findtext('StatusCode') == '1' for n in nodes)
        assert len({n.attrib['WorkflowId'] for n in nodes}) == 13
        assert core.identifier('TandemValidateContext') != core.CONTRACT['nativeSharedChildTemplateId']
        roots = solution.findall('./SolutionManifest/RootComponents/RootComponent')
        assert {n.attrib['id'] for n in roots} == {n.attrib['WorkflowId'] for n in nodes}
        for node in nodes:
            doc = json.loads(z.read(node.findtext('JsonFileName').lstrip('/')))
            for _, action in native.walk(doc['properties']['definition']['actions']):
                if action['type'] == 'Workflow':
                    assert action['inputs']['host']['workflowReferenceName'] == core.identifier('TandemValidateContext')
                if action['type'] == 'OpenApiConnection':
                    assert action['inputs']['authentication'] == {'type': 'Raw', 'value': native.RAW_INVOKER}
    with pytest.raises(FileExistsError): core.assemble(original, docs, output)


@pytest.mark.parametrize('change', ['missing', 'extra', 'child', 'automated', 'connector'])
def test_incomplete_or_unverified_batch_is_rejected_before_zip(tmp_path, change):
    original = tmp_path / 'native.zip'; source(original)
    docs = documents(original)
    doc = docs['TandemSendRequest']
    if change == 'missing': docs.pop('TandemMyGroups')
    if change == 'extra': docs['UnapprovedFlow'] = deepcopy(doc)
    if change == 'child': doc['properties']['definition']['actions']['Call_child']['inputs']['host']['workflowReferenceName'] = 'unverified'
    if change == 'automated': doc['properties']['definition']['triggers']['manual']['kind'] = 'UnverifiedEvent'
    if change == 'connector': doc['properties']['definition']['actions']['Read_caller']['inputs']['host']['apiId'] = '/unapproved'
    output = tmp_path / 'batch.zip'
    with pytest.raises(ValueError): core.assemble(original, docs, output)
    assert not output.exists()
