"""Orchestrator gates and actual temporary packaged graphs; no final batch output."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
from uuid import UUID
from xml.etree import ElementTree as ET
from zipfile import ZipFile

import pytest

from scripts.power_automate import build_core_batch as build
from scripts.power_automate import core_solution as core
from scripts.power_automate.solution_source import SP_API, inspect_caller_export, walk
from test_core_solution import source as native_fixture

BUILD = '81000000-0000-4000-8000-000000000001'
SECOND = '81000000-0000-4000-8000-000000000002'


def git(root, *args, input=None):
    result = subprocess.run(['git', '-C', str(root), *args], input=input,
                            capture_output=True, text=True, check=True)
    return result.stdout.strip()


@pytest.fixture
def integrated(tmp_path):
    """Synthetic deliveries test packaging without pretending they are business flows."""
    native = tmp_path / 'native.zip'
    native_fixture(native)
    seed = inspect_caller_export(native, core.batch_schema.CONTRACT['site'], build.NATIVE_SHARED_BUILD)
    root = tmp_path / 'combined'
    root.mkdir()
    for name, path in build.CONSUMER_ARTIFACTS.items():
        doc = deepcopy(seed['probe'])
        actions = doc['properties']['definition']['actions']
        actions['Own_build'] = {'type': 'Compose', 'inputs': {'packageBuildId': 'consumer-' + name}, 'runAfter': {}}
        actions['Shared_pin'] = {'type': 'Compose', 'inputs': {'packageBuildId': build.NATIVE_SHARED_BUILD}, 'runAfter': {}}
        if name == 'TandemParticipantSubmission':
            doc['properties']['definition']['triggers'] = {'Event': {'type': 'OpenApiConnection',
                'inputs': {'host': {'apiId': SP_API, 'connectionName': 'shared_sharepointonline',
                                    'operationId': 'GetOnUpdatedItems'},
                           'authentication': "@parameters('$authentication')",
                           'parameters': {'dataset': core.batch_schema.CONTRACT['site'], 'table': 'fixture'}}}}
            doc['_connectionEvidence'] = 'AUTOMATED_SOURCE_VERIFIED'
            doc['properties']['connectionReferences']['shared_sharepointonline']['runtimeSource'] = 'embedded'
            actions['Read_caller']['inputs']['authentication'] = "@parameters('$authentication')"
        file = root / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes((json.dumps(doc, indent=2) + '\n').encode())
    git(root, 'init', '--quiet')
    git(root, 'add', '.')
    git(root, '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
        'commit', '--quiet', '-m', 'Synthetic integrated consumer fixtures')
    return root, native


def output(tmp_path, name='out'):
    return tmp_path / name / build.OUTPUT_NAME


def components(path):
    with ZipFile(path) as archive:
        custom = ET.fromstring(archive.read('customizations.xml'))
        return {node.attrib['Name']: json.loads(archive.read(node.findtext('JsonFileName').lstrip('/')))
                for node in custom.findall('./Workflows/Workflow')}


def test_exact_delivered_registry_and_missing_all_are_clear_before_writes(tmp_path):
    assert set(build.CONSUMER_ARTIFACTS) | {'TandemValidateContext'} == set(core.CONTRACT['productionFlows'])
    assert build.CONSUMER_ARTIFACTS['TandemUpdateGroup'] == 'artifacts/update_group/TandemUpdateGroup-v1.parent.json'
    assert build.CONSUMER_ARTIFACTS['TandemRespondGroupJoinRequest'] == 'artifacts/group_response/TandemRespondGroupJoinRequest-activation.definition.json'
    destination = output(tmp_path)
    with pytest.raises(ValueError, match='Core batch incomplete') as error:
        build.build(tmp_path / 'unused-native.zip', destination, checkout=tmp_path, build_id=BUILD)
    assert all(path in str(error.value) for path in build.CONSUMER_ARTIFACTS.values())
    assert not destination.parent.exists()


def test_no_historical_or_sibling_fallback(integrated, tmp_path):
    root, native = integrated
    missing = root / build.CONSUMER_ARTIFACTS['TandemMyGroups']
    missing.rename(missing.with_name('TandemMyGroups-v1.definition.json'))
    with pytest.raises(ValueError, match='TandemMyGroups-v2.definition.json'):
        build.build(native, output(tmp_path), checkout=root)
    assert not output(tmp_path).exists()


def test_untracked_delivery_is_not_integrated(integrated, tmp_path):
    root, native = integrated
    git(root, 'rm', '--cached', build.CONSUMER_ARTIFACTS['TandemRespondGroupJoinRequest'])
    with pytest.raises(ValueError, match='not integrated into Git index'):
        build.build(native, output(tmp_path), checkout=root)
    assert not output(tmp_path).parent.exists()


def test_unresolved_merge_blocks_final_package(integrated, tmp_path, monkeypatch):
    root, native = integrated
    real_git = build.git
    monkeypatch.setattr(build, 'git', lambda checkout, *args:
        '100644 abc123 2\tunresolved.txt' if args == ('ls-files', '--unmerged') else real_git(checkout, *args))
    with pytest.raises(ValueError, match='unresolved merges'):
        build.build(native, output(tmp_path), checkout=root)
    assert not output(tmp_path).parent.exists()


@pytest.mark.parametrize('bad', ['{bad-json', '[]', '{"properties":{"definition":{"actions":[],"triggers":{}}}}'])
def test_malformed_artifact_names_flow_and_path(integrated, tmp_path, bad):
    root, native = integrated
    (root / build.CONSUMER_ARTIFACTS['TandemUpdateGroup']).write_text(bad)
    with pytest.raises(ValueError, match='Invalid delivered artifact TandemUpdateGroup'):
        build.build(native, output(tmp_path), checkout=root)
    assert not output(tmp_path).parent.exists()


@pytest.mark.parametrize('existing', ['zip', 'review'])
def test_existing_output_or_review_is_never_overwritten(tmp_path, existing):
    destination = output(tmp_path)
    destination.parent.mkdir()
    preserved = destination if existing == 'zip' else destination.with_suffix('.review.json')
    preserved.write_bytes(b'preserve')
    with pytest.raises(FileExistsError):
        build.build('unused', destination, checkout=tmp_path)
    assert preserved.read_bytes() == b'preserve'


def test_baseline_source_drift_rejected_before_output(integrated, tmp_path, monkeypatch):
    root, native = integrated
    def reject(_): raise ValueError('Schema mapping drift: update #81')
    monkeypatch.setattr(build.shared, 'verify_baseline_sources', reject)
    with pytest.raises(ValueError, match='Schema mapping drift'):
        build.build(native, output(tmp_path), checkout=root)
    assert not output(tmp_path).parent.exists()


def test_packaged_child_is_fresh_native_template_with_current_baseline_and_hash(integrated, tmp_path):
    root, native = integrated
    destination = output(tmp_path)
    report = build.build(native, destination, checkout=root, build_id=BUILD)
    docs = components(destination)
    assert set(core.CONTRACT['productionFlows']) < set(docs)
    assert len(docs) == 14 and report['productionFlowCount'] == 12 and report['maintenanceFlowCount'] == 2
    child = docs['TandemValidateContext']
    expected = build.shared.definition_actions(build.batch_schema.baseline(), BUILD,
        hashlib.sha256(Path(build.shared.rules.__file__).read_bytes()).hexdigest())
    assert child['properties']['definition']['actions'] == expected
    assert child['properties']['connectionReferences'] == {}
    provenance = report['buildProvenance']
    assert provenance['sourceCommit'] == git(root, 'rev-parse', 'HEAD')
    assert provenance['baselineRoleCount'] == 8 and provenance['baselineVersion'] == 2
    assert provenance['contractVersion'] == provenance['rulesVersion'] == 1
    assert provenance['consumerWorkingTree'] == []
    for name, details in provenance['consumers'].items():
        assert details['sha256'] == hashlib.sha256((root / build.CONSUMER_ARTIFACTS[name]).read_bytes()).hexdigest()
        assert 'consumer-' + name in details['sourceBuildIds']
    with ZipFile(destination) as archive:
        custom = ET.fromstring(archive.read('customizations.xml'))
        assert all(n.findtext('StateCode') == '0' for n in custom.findall('./Workflows/Workflow'))
    for name, doc in docs.items():
        actions = doc['properties']['definition']['actions']
        for _, action in walk(actions):
            if action['type'] == 'Workflow':
                assert action['inputs']['host']['workflowReferenceName'] == core.identifier('TandemValidateContext')
        if name in build.CONSUMER_ARTIFACTS:
            assert actions['Own_build']['inputs']['packageBuildId'] == 'consumer-' + name
            assert actions['Shared_pin']['inputs']['packageBuildId'] == BUILD
    auto = docs['TandemParticipantSubmission']
    assert auto['properties']['connectionReferences']['shared_sharepointonline']['runtimeSource'] == 'embedded'
    assert auto['properties']['definition']['triggers']['Event']['inputs']['authentication'] == "@parameters('$authentication')"
    assert report['nativeResult'] == 'NOT_IMPORTED_NOT_TESTED'
    assert report['sha256'] == hashlib.sha256(destination.read_bytes()).hexdigest()
    assert json.loads(destination.with_suffix('.review.json').read_text()) == report


def test_actual_packaged_smoke_executes_actual_packaged_batch_child(integrated, tmp_path):
    from core_native_backend import Connection, Database, ParentRunner
    root, native = integrated
    destination = output(tmp_path)
    build.build(native, destination, checkout=root, build_id=BUILD)
    docs = components(destination)
    child = docs['TandemValidateContext']['properties']['definition']['actions']
    smoke = docs['TandemCoreValidationSmoke']['properties']['definition']['actions']
    connection = Connection(Database(), child_actions=child, child_id=core.identifier('TandemValidateContext'))
    runner = ParentRunner(connection)
    runner.run(smoke)
    report = runner.outputs['Smoke_report']
    assert report['allPassed'], report['failedCases']
    assert report['completedCount'] == report['testCount'] == len(smoke['Smoke_cases']['inputs'])
    assert len(connection.child_calls) == report['testCount']
    assert report['packageBuildId'] == BUILD


def test_same_seed_build_gives_identical_zip_bytes(integrated, tmp_path):
    root, native = integrated
    first, second = output(tmp_path, 'first'), output(tmp_path, 'second')
    build.build(native, first, checkout=root, build_id=BUILD, include_setup=False, include_smoke=False)
    build.build(native, second, checkout=root, build_id=BUILD, include_setup=False, include_smoke=False)
    assert first.read_bytes() == second.read_bytes()
    assert first.with_suffix('.review.json').read_bytes() == second.with_suffix('.review.json').read_bytes()


def test_default_build_gets_new_uuid(integrated, tmp_path, monkeypatch):
    root, native = integrated
    ids = iter([UUID(BUILD), UUID(SECOND)])
    monkeypatch.setattr(build, 'uuid4', lambda: next(ids))
    a = build.build(native, output(tmp_path, 'a'), checkout=root, include_setup=False, include_smoke=False)
    b = build.build(native, output(tmp_path, 'b'), checkout=root, include_setup=False, include_smoke=False)
    assert a['sharedBuildId'] == BUILD and b['sharedBuildId'] == SECOND
    assert a['sha256'] != b['sha256']


def test_changed_consumer_during_assembly_never_publishes(integrated, tmp_path, monkeypatch):
    root, native = integrated
    assemble = core.assemble
    def changing(*args, **kwargs):
        report = assemble(*args, **kwargs)
        path = root / next(iter(build.CONSUMER_ARTIFACTS.values()))
        path.write_bytes(path.read_bytes() + b'\n')
        return report
    monkeypatch.setattr(core, 'assemble', changing)
    with pytest.raises(ValueError, match='changed during assembly'):
        build.build(native, output(tmp_path), checkout=root, build_id=BUILD)
    assert not output(tmp_path).parent.exists()


def test_assembler_failure_stays_temporary(integrated, tmp_path, monkeypatch):
    root, native = integrated
    def fail(*args, **kwargs):
        Path(args[2]).write_bytes(b'partial')
        raise ValueError('Unrecognized child dependency')
    monkeypatch.setattr(core, 'assemble', fail)
    with pytest.raises(ValueError, match='Unrecognized child'):
        build.build(native, output(tmp_path), checkout=root, build_id=BUILD)
    assert not output(tmp_path).parent.exists()


def test_cli_reports_missing_delivery_without_writing(tmp_path, capsys):
    with pytest.raises(SystemExit) as error:
        build.main(['--native-export', str(tmp_path / 'native.zip'), '--output', str(output(tmp_path)),
                    '--checkout', str(tmp_path)])
    assert error.value.code == 2
    assert 'Core batch incomplete' in capsys.readouterr().err
    assert not output(tmp_path).parent.exists()


def test_invalid_build_id_or_filename_rejected_without_output(tmp_path):
    with pytest.raises(ValueError):
        build.build('unused', output(tmp_path), build_id='not-a-uuid')
    with pytest.raises(ValueError, match='stable output filename'):
        build.build('unused', tmp_path / 'random.zip')
    assert not output(tmp_path).parent.exists()
