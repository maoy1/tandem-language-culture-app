"""Assemble the twelve individually owned flows using the inspected native ZIP.

This packages definitions; it never imports, enables, grants access or certifies
them. Each flow's native evidence and outstanding tests stay with its ticket.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from uuid import UUID, uuid5
from xml.etree import ElementTree as ET
from zipfile import ZIP_DEFLATED, ZipFile

from .schema_audit import measure
from .solution_source import inspect_caller_export, invoker_parent_document, walk
from . import batch_schema
from . import shared_validation

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = json.loads((ROOT / 'config/core_batch_contract.json').read_text())
NAMESPACE = UUID('6e36e09f-5b99-4477-9420-e6b6f61f13b4')


def identifier(name):
    return str(uuid5(NAMESPACE, CONTRACT['solutionName'] + ':' + name))


def bind_shared_build(value, old, new):
    """Rebind only the inspected shared build's exact literal, not flow builds."""
    if isinstance(value, dict): return {k: bind_shared_build(v, old, new) for k, v in value.items()}
    if isinstance(value, list): return [bind_shared_build(v, old, new) for v in value]
    if isinstance(value, str): return new if value == old else value.replace("'" + old + "'", "'" + new + "'")
    return value


def assemble(native_source, documents, output, include_setup=True, include_smoke=True):
    """Reject missing/extraneous production flows and unresolved dependencies."""
    output = Path(output)
    if output.exists() or output.with_suffix('.review.json').exists(): raise FileExistsError(output)
    expected = CONTRACT['productionFlows']
    if set(documents) != set(expected):
        raise ValueError('Expected all twelve production flow documents; missing=' +
                         str(sorted(set(expected) - set(documents))) + '; extra=' + str(sorted(set(documents) - set(expected))))
    source_build = 'c79b7b64-b3ce-4de3-aa74-0ed62bca1524'
    shared_build = documents['TandemValidateContext']['properties']['definition']['actions']['Validation_report']['inputs']['packageBuildId']
    if not isinstance(shared_build, str) or not shared_build:
        raise ValueError('Shared batch build identity required')
    seed = inspect_caller_export(native_source, batch_schema.CONTRACT['site'], source_build)
    with ZipFile(native_source) as archive:
        raw = {n: archive.read(n) for n in archive.namelist()}
    solution, custom = ET.fromstring(raw['solution.xml']), ET.fromstring(raw['customizations.xml'])
    prototype = deepcopy(custom.find('./Workflows/Workflow'))
    workflows = custom.find('Workflows'); workflows.clear()
    manifest = solution.find('SolutionManifest')
    manifest.find('UniqueName').text = CONTRACT['solutionName']
    manifest.find('Version').text = CONTRACT['solutionVersion']
    manifest.find('./LocalizedNames/LocalizedName').set('description', 'Tandem core flow batch')
    roots = manifest.find('RootComponents'); roots.clear()
    # Preserve only the observed SharePoint component; no email or extra API.
    refs = custom.find('connectionreferences')
    refs.clear(); refs.append(deepcopy(seed['connectionComponent']))
    entries = {n: b for n, b in raw.items() if not n.startswith('Workflows/') and n not in ['solution.xml', 'customizations.xml']}
    source_docs = deepcopy(documents)
    original_child = CONTRACT['nativeSharedChildTemplateId']
    if include_setup:
        source_docs['TandemBatchSchemaSetup'] = invoker_parent_document(seed, batch_schema.trigger(), batch_schema.actions('batch-schema-v1'))
    if include_smoke:
        cases = shared_validation.smoke_cases()
        prospective = batch_schema.baseline()
        schema = shared_validation.synthetic_metadata(prospective)
        expected_schema = {'schemaMatches': True, 'checkedRoles': prospective['roles'], 'allSchema': True,
            'differences': [], 'provenanceVerified': False,
            'note': 'Compares supplied snapshots only; collector owns current complete authenticated reads.'}
        cases.append({'id': 'BATCH_EIGHT_ROLE_SCHEMA', 'payload': {'contractVersion': 1, 'rulesVersion': 1,
            'mode': 'SCHEMA', 'metadata': schema}, 'code': 'OK', 'expected': expected_schema})
        for fixture, fits in [(shared_validation.quick_cases()[0], True), (shared_validation.quick_cases()[1], False)]:
            payload = deepcopy(fixture['payload']); payload['mode'] = 'PAIRS'
            right = payload.pop('rightId')
            cases.append({'id': 'BULK_' + fixture['id'], 'payload': payload, 'code': 'OK',
                'expected': {'pairs': [{'profileId': right, **fixture['expected']}] if fits else []}})
        smoke = deepcopy(seed['child'])
        smoke['properties']['definition']['triggers'] = {'manual': {'type': 'Request', 'kind': 'Button',
            'inputs': {'schema': {'type': 'object', 'properties': {}, 'required': []}}}}
        smoke['properties']['definition']['actions'] = shared_validation.parent_actions(original_child, cases, shared_build, 'BATCH')
        source_docs['TandemCoreValidationSmoke'] = smoke
    review = {'sourceTicket': 81, 'solutionName': CONTRACT['solutionName'],
              'solutionVersion': CONTRACT['solutionVersion'], 'productionFlowCount': len(expected),
              'maintenanceFlowCount': int(include_setup) + int(include_smoke), 'importState': 'disabled',
              'nativeResult': 'NOT_IMPORTED_NOT_TESTED', 'ordinaryUserAccessVerified': False,
              'sourceExportSha256': hashlib.sha256(Path(native_source).read_bytes()).hexdigest(), 'flows': {},
              'automatedConnectionEvidence': 'Legacy Embedded source inspected; automatic Solution binding/import/execution NOT RUN',
              'ordinaryUserAccess': 'Deferred by owner; not verified by owner-context tests',
              'sharedBuildId': shared_build, 'sharedDependencyRebinding': {'fromBuild': source_build, 'toBuild': shared_build}}
    child_id = identifier('TandemValidateContext')
    for name, source in source_docs.items():
        doc = deepcopy(source)
        props = doc['properties']; definition = props['definition']
        if name == 'TandemValidateContext':
            if props.get('connectionReferences'): raise ValueError('Shared validator must remain connector-free')
        else:
            trigger = next(iter(definition['triggers'].values()))
            if trigger.get('kind') in ['Button', 'PowerAppV2']:
                if name != 'TandemCoreValidationSmoke':
                    doc = invoker_parent_document(seed, definition['triggers'], definition['actions'])
                    props = doc['properties']; definition = props['definition']
            else:
                # Automatic binding requires a separately reviewed native source;
                # a manual Invoker seed cannot certify or silently replace it.
                if source.get('_connectionEvidence') != 'AUTOMATED_SOURCE_VERIFIED':
                    raise ValueError('Automated participant connection evidence required before bundling')
                for ref in props.get('connectionReferences', {}).values():
                    logical = ref.get('connection', {}).get('connectionReferenceLogicalName')
                    if logical != seed['receipt']['connectionReferenceLogicalName'] or ref.get('runtimeSource') != 'embedded':
                        raise ValueError('Unresolved automated embedded SharePoint reference')
        for _, action in walk(definition['actions']):
            if name == 'TandemValidateContext' and action['type'] in ['Workflow', 'OpenApiConnection']:
                raise ValueError('Shared validator cannot invoke connectors or other flows')
            if action['type'] == 'Workflow':
                host = action['inputs']['host']
                if host.get('workflowReferenceName') != original_child: raise ValueError('Unrecognized child dependency')
                host['workflowReferenceName'] = child_id
            if action['type'] == 'OpenApiConnection':
                inputs = action['inputs']
                if inputs['host'].get('apiId') != '/providers/Microsoft.PowerApps/apis/shared_sharepointonline':
                    raise ValueError('Core batch only uses SharePoint')
                parameters = inputs['parameters']
                if parameters.get('dataset') != batch_schema.CONTRACT['site']:
                    raise ValueError('Unexpected target site')
                method = parameters.get('parameters/method', 'GET')
                if method != 'GET' and '/items' in str(parameters.get('parameters/uri', '')):
                    if inputs.get('retryPolicy') != {'type': 'none'}:
                        raise ValueError('Business writes must not automatically retry')
        if name != 'TandemValidateContext':
            definition['actions'] = bind_shared_build(definition['actions'], source_build, shared_build)
        # All components use the actual native document envelope, including the
        # automated source. No legacy flow IDs/creator/migration data leak in.
        native_doc = deepcopy(seed['child'] if name in ['TandemValidateContext', 'TandemCoreValidationSmoke'] else seed['probe'])
        native_doc['properties']['definition'] = definition
        native_doc['properties']['connectionReferences'] = deepcopy(props.get('connectionReferences', {}))
        doc, props = native_doc, native_doc['properties']
        display_name = name + ' (batch preview)'
        if 'displayName' in props: props['displayName'] = display_name
        id_ = identifier(name)
        node = deepcopy(prototype); node.set('WorkflowId', '{' + id_ + '}'); node.set('Name', name)
        file = 'Workflows/' + name + '-' + id_.upper() + '.json'
        node.find('JsonFileName').text = '/' + file
        node.find('StateCode').text = '0'; node.find('StatusCode').text = '1'
        node.find('IntroducedVersion').text = '1.0.0.0'
        node.find('./LocalizedNames/LocalizedName').set('description', display_name)
        workflows.append(node)
        ET.SubElement(roots, 'RootComponent', {'type': '29', 'id': '{' + id_ + '}', 'behavior': '0'})
        encoded = (json.dumps(doc, indent=2) + '\n').encode()
        entries[file] = encoded
        review['flows'][name] = {'sourceTicket': expected.get(name, 81), 'id': id_,
                                **measure(definition['actions']), 'definitionSha256': hashlib.sha256(encoded).hexdigest()}
    entries['solution.xml'] = ET.tostring(solution, encoding='utf-8', xml_declaration=True)
    entries['customizations.xml'] = ET.tostring(custom, encoding='utf-8', xml_declaration=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, 'x', ZIP_DEFLATED) as archive:
        for name, data in entries.items(): archive.writestr(name, data)
    review['sha256'] = hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_suffix('.review.json').write_bytes((json.dumps(review, indent=2) + '\n').encode())
    return review
