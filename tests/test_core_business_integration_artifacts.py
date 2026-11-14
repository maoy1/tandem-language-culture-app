"""ZIP-mode fixture tests only; the same business cases run on the final bundle."""
import json
from xml.etree import ElementTree as ET
from zipfile import ZipFile

import pytest

import test_core_business_integration as e2e
from core_native_backend import seed

CHILD = '81000000-0000-4000-8000-000000000081'
BUILD = 'actual-packaged-build'


def bundle(path, target=CHILD):
    child = {'Validation_report': {'type': 'Compose', 'inputs': {'packageBuildId': BUILD}},
             'Reply': {'type': 'Response', 'kind': 'PowerApp', 'runAfter': {'Validation_report': ['Succeeded']},
                       'inputs': {'body': {'success': True, 'resultcode': 'PACKAGED_CHILD',
                                          'build': "@outputs('Validation_report')?['packageBuildId']"}}}}
    parent = {'Call': {'type': 'Workflow', 'inputs': {'host': {'workflowReferenceName': target},
                                                    'body': {'text': '{}'}}},
              'Reply': {'type': 'Response', 'kind': 'PowerApp', 'runAfter': {'Call': ['Succeeded']},
                        'inputs': {'body': {'success': "@body('Call')?['success']",
                                           'resultcode': "@body('Call')?['resultcode']",
                                           'build': "@body('Call')?['build']"}}}}
    custom = ET.Element('ImportExportXml')
    workflows = ET.SubElement(custom, 'Workflows')
    with ZipFile(path, 'w') as archive:
        for name, id_, actions in [('TandemValidateContext', CHILD, child),
                                   ('TandemSendRequest', '81000000-0000-4000-8000-000000000010', parent)]:
            file = 'Workflows/' + name + '.json'
            node = ET.SubElement(workflows, 'Workflow', {'Name': name, 'WorkflowId': '{' + id_ + '}'})
            ET.SubElement(node, 'JsonFileName').text = '/' + file
            archive.writestr(file, json.dumps({'properties': {'definition': {'actions': actions}}}))
        archive.writestr('customizations.xml', ET.tostring(custom))


def test_zip_mode_runs_exact_packaged_child_identity_build_and_graph_once(tmp_path, monkeypatch):
    path = tmp_path / 'core.zip'; bundle(path)
    monkeypatch.setenv('TANDEM_CORE_ZIP', str(path))
    def forbidden(*args, **kwargs):
        raise AssertionError('Packaged graphs must not be rebuilt or rebound')
    monkeypatch.setattr(e2e.core_solution, 'bind_shared_build', forbidden)
    monkeypatch.setattr(e2e.shared, 'definition_actions', forbidden)
    before = e2e.packaged_graphs.cache_info()
    for _ in range(2):
        response, _ = e2e.invoke(seed(), 'send', 1, {})
        assert response == {'success': True, 'resultcode': 'PACKAGED_CHILD', 'build': BUILD}
    after = e2e.packaged_graphs.cache_info()
    assert after.misses == before.misses + 1 and after.hits >= before.hits + 1


def test_zip_mode_missing_consumer_fails_instead_of_component_fallback(tmp_path, monkeypatch):
    path = tmp_path / 'core.zip'; bundle(path)
    monkeypatch.setenv('TANDEM_CORE_ZIP', str(path))
    with pytest.raises(AssertionError, match='Missing packaged consumer: TandemUpdateGroup'):
        e2e.invoke(seed(), 'update', 1, {})


def test_zip_mode_rejects_unresolved_child_reference(tmp_path):
    path = tmp_path / 'core.zip'; bundle(path, target='unresolved-child')
    with pytest.raises(AssertionError, match='Unresolved packaged child'):
        e2e.packaged_graphs(str(path))
