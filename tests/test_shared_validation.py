"""Execute the emitted child graph and verify native Solution linkage locally.

These tests are not certification of Microsoft's runtime or tenant access.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
from xml.etree import ElementTree as ET
from zipfile import ZipFile

import pytest

from scripts.power_automate import shared_validation as shared
from scripts.power_automate import compatibility as rules
from scripts.power_automate.schema_audit import measure
from test_discovery_flow import FlowRunner

BASELINE = json.loads((shared.ROOT / 'config/shared_validation_schema.json').read_text())
FIXTURES = json.loads((shared.ROOT / 'tests/fixtures/compatibility_v1.json').read_text())


class NoIO:
    def request(self, parameters):
        raise AssertionError('The validation child must never use a connector')


class ChildRunner(FlowRunner):
    """The inherited interpreter exercises real generated actions/scoping.

    Scalar XPath is explicitly modeled rather than treating attribute nodes as
    scalar values. Native execution of these expressions remains a smoke gate.
    """
    def expr(self, text, context):
        pattern = r"xpath\(xml\(if\(empty\(item\(\)\?\['SchemaXml'\]\),'<Field/>',item\(\)\?\['SchemaXml'\]\)\),'([^']+)'\)"
        def replace(match):
            try: node = ET.fromstring(context['item'].get('SchemaXml') or '<Field/>')
            except ET.ParseError as e: raise ValueError('Bad metadata XML') from e
            path = match.group(1)
            if path.startswith('string(/Field/@'):
                value = node.attrib.get(path[len('string(/Field/@'):-1], '')
            else:
                assert path == '/Field/CHOICES/CHOICE/text()'
                value = [c.text or '' for c in node.findall('./CHOICES/CHOICE')]
            return "json('" + json.dumps(value).replace("'", "''") + "')"
        text = re.sub(pattern, replace, text)
        return super().expr(text, context)


def execute(payload):
    runner = ChildRunner(NoIO())
    runner.run(shared.definition_actions(BASELINE, 'local-build', 'local-source'),
               {'items': {}, 'triggerBody': {'text': payload if isinstance(payload, str) else json.dumps(payload)}})
    assert runner.response is not None, runner.action_states
    return json.loads(runner.response['resultjson'])


def request(mode='PAIR', **extra):
    return {'contractVersion': 1, 'rulesVersion': 1, 'mode': mode,
            'profiles': deepcopy(FIXTURES['profiles']), 'catalogues': deepcopy(FIXTURES['catalogues']), **extra}


@pytest.mark.parametrize('case', shared.smoke_cases(), ids=lambda c: c['id'])
def test_child_matches_independently_expected_compatibility_cases(case):
    result = execute(case['payload'])
    assert result['code'] == case['code'], result
    assert result['result'] == case['expected']
    assert result['authorizesAction'] is False
    assert result['connectors'] == result['reads'] == result['writes'] == 0


@pytest.mark.parametrize('property', ['status', 'participationStatus', 'openToConnections'])
def test_legacy_null_availability_is_normalized_but_never_eligible(property):
    payload = request(leftId=1, rightId=2)
    payload['profiles'][0][property] = None
    result = execute(payload)
    assert result['code'] == 'OK' and result['result']['eligible'] is False
    payload['mode'] = 'NORMALIZE'
    result = execute(payload)
    assert result['result']['profiles'][0][property] is None


@pytest.mark.parametrize('property,value', [('openToConnections', 'true'), ('participationStatus', 'Unknown'),
                                           ('status', 1), ('profileId', 1.5)])
def test_malformed_non_null_values_fail_without_partial_result(property, value):
    payload = request(leftId=1, rightId=2)
    payload['profiles'][0][property] = value
    result = execute(payload)
    assert result['code'] == 'INVALID_INPUT' and result['result'] == {}


@pytest.mark.parametrize('change,code', [('contract', 'VERSION_MISMATCH'), ('rules', 'VERSION_MISMATCH'),
                                       ('mode', 'UNSUPPORTED_MODE'), ('json', 'INVALID_INPUT')])
def test_structured_error_response_on_unsupported_contract_or_input(change, code):
    payload = request(leftId=1, rightId=2)
    if change == 'contract': payload['contractVersion'] = 2
    elif change == 'rules': payload['rulesVersion'] = 2
    elif change == 'mode': payload['mode'] = 'UNRECOGNIZED'
    else: payload = 'bad json'
    result = execute(payload)
    assert result['code'] == code and result['success'] is False and result['result'] == {}


@pytest.mark.parametrize('change', ['unknownId', 'unknownZone', 'duplicateIdentity', 'duplicateId', 'emptyAccount'])
def test_invalid_profile_content_does_not_return_partial_normalization(change):
    payload = request(mode='NORMALIZE')
    if change == 'unknownId': payload['profiles'][0]['teachIds'] = [98765]
    elif change == 'unknownZone': payload['profiles'][0]['timezoneId'] = 98765
    elif change == 'duplicateIdentity': payload['profiles'][1]['accountKey'] = payload['profiles'][0]['accountKey']
    elif change == 'duplicateId': payload['profiles'][1]['profileId'] = payload['profiles'][0]['profileId']
    else: payload['profiles'][0]['accountKey'] = ' '
    result = execute(payload)
    assert result['code'] == 'INVALID_PROFILE_DATA' and result['result'] == {}


def test_pair_target_missing_is_an_explicit_reference_error():
    result = execute(request(leftId=1, rightId=99999))
    assert result['code'] == 'PROFILE_NOT_FOUND' and result['result'] == {}


def test_normalization_matches_reference_for_existing_contract():
    result = execute(request(mode='NORMALIZE'))
    catalogues = rules.normalize_catalogues(FIXTURES['catalogues'])
    assert result['result']['profiles'] == rules.normalize_profiles(FIXTURES['profiles'], catalogues)


def test_complete_schema_snapshot_and_scoped_schema_check():
    metadata = shared.synthetic_metadata(BASELINE)
    payload = request(mode='SCHEMA', metadata=metadata)
    result = execute(payload)
    assert result['code'] == 'OK' and result['result']['schemaMatches']
    assert result['result']['allSchema'] and not result['result']['provenanceVerified']
    payload['schemaRoles'] = ['requests']
    payload['metadata']['lists'] = [x for x in metadata['lists'] if x['role'] == 'requests']
    result = execute(payload)
    assert result['code'] == 'OK' and not result['result']['allSchema']


@pytest.mark.parametrize('change', ['required', 'type', 'unique', 'indexed', 'default', 'lookup', 'choices',
                                   'listId', 'incomplete', 'missingList', 'duplicateList', 'missingField',
                                   'readOnly', 'hidden', 'decimals', 'formula'])
def test_schema_changes_are_reported_without_applying_any_changes(change):
    metadata = shared.synthetic_metadata(BASELINE)
    byrole = {x['role']: x for x in metadata['lists']}
    fields = byrole['requests']['Fields']
    if change == 'required': fields[0]['Required'] = not fields[0]['Required']
    elif change == 'type': fields[0]['TypeAsString'] = 'Lookup'
    elif change == 'unique': next(x for x in fields if x['InternalName'] == 'ConnectionKey')['EnforceUniqueValues'] = False
    elif change == 'indexed': next(x for x in fields if x['InternalName'] == 'ConnectionKey')['Indexed'] = False
    elif change == 'default': next(x for x in fields if x['InternalName'] == 'OperationComplete')['DefaultValue'] = '1'
    elif change == 'lookup': next(x for x in fields if x['InternalName'] == 'TargetGroup')['SchemaXml'] = '<Field List="wrong" ShowField="Title"/>'
    elif change == 'choices': next(x for x in fields if x['InternalName'] == 'Status')['SchemaXml'] = '<Field><CHOICES><CHOICE>Other</CHOICE></CHOICES></Field>'
    elif change == 'listId': byrole['requests']['Id'] = 'wrong'
    elif change == 'incomplete': byrole['requests']['complete'] = False
    elif change == 'missingList': metadata['lists'].remove(byrole['requests'])
    elif change == 'duplicateList': metadata['lists'].append(deepcopy(byrole['requests']));metadata['lists'].pop(0)
    elif change == 'missingField': fields.pop()
    elif change == 'readOnly': fields[0]['ReadOnlyField'] = True
    elif change == 'hidden': fields[0]['Hidden'] = True
    elif change == 'decimals': fields[0]['SchemaXml'] = '<Field Decimals="2"/>'
    else: byrole['groups']['ValidationFormula'] = '=TRUE'
    before = deepcopy(metadata)
    result = execute(request(mode='SCHEMA', metadata=metadata))
    assert result['code'] == 'SCHEMA_MISMATCH', result
    assert result['result']['differences'] and metadata == before


def test_extra_noncritical_index_is_not_a_schema_failure():
    metadata = shared.synthetic_metadata(BASELINE)
    metadata['lists'][0]['Fields'][0]['Indexed'] = True
    assert execute(request(mode='SCHEMA', metadata=metadata))['code'] == 'OK'


def test_duplicate_native_field_name_cannot_hide_behind_one_matching_definition():
    metadata = shared.synthetic_metadata(BASELINE)
    fields = metadata['lists'][0]['Fields']
    duplicate = deepcopy(fields[0]); duplicate['Required'] = not duplicate['Required']
    fields.append(duplicate)
    assert execute(request(mode='SCHEMA', metadata=metadata))['code'] == 'SCHEMA_MISMATCH'


def test_catalogue_and_role_duplicates_are_normalized():
    payload = request(mode='NORMALIZE')
    payload['catalogues']['languageIds'] *= 2
    payload['catalogues']['cultureIds'] *= 2
    payload['profiles'][0]['teachIds'] *= 2
    result = execute(payload)
    assert result['code'] == 'OK'
    cat = result['result']['catalogues']
    assert len(cat['concreteLanguageIds']) == len(set(cat['concreteLanguageIds']))
    assert len(cat['cultureIds']) == len(set(cat['cultureIds']))


@pytest.mark.parametrize('availability', [None, False, True])
def test_profile_content_check_is_independent_of_availability(availability):
    payload = request(mode='PROFILE');payload['profiles'] = payload['profiles'][:1]
    payload['profiles'][0]['openToConnections'] = availability
    result = execute(payload)
    assert result['code'] == 'OK' and result['result']['valid']


def test_any_language_is_still_a_valid_known_registration_selection_but_not_a_match():
    payload = request(mode='PROFILE');payload['profiles'] = payload['profiles'][:1]
    profile = payload['profiles'][0]
    for field in rules.ROLE_FIELDS:profile[field] = []
    profile['teachIds'] = [payload['catalogues']['anyLanguageId']]
    assert execute(payload)['result']['valid']
    payload['mode'] = 'NORMALIZE'
    assert execute(payload)['result']['profiles'][0]['teachIds'] == []


def test_mapping_drift_requires_baseline_update():
    shared.verify_baseline_sources(BASELINE)
    bad = deepcopy(BASELINE);bad['sourceMappingHashes']['participantCatalogue'] = 'stale'
    with pytest.raises(ValueError, match='update #81'):shared.verify_baseline_sources(bad)


class ParentRunner(ChildRunner):
    """Wire the actual emitted parent Workflow action to the emitted child."""
    def run(self, actions, ctx=None):
        if 'Call_validation_child' in actions:
            call = actions['Call_validation_child']
            payload = self.inputs(call['inputs']['body'], ctx)
            child = ChildRunner(NoIO())
            child.run(shared.definition_actions(BASELINE, getattr(self, 'build_id', 'local-build'), 'local-source'),
                      {'items': {}, 'triggerBody': payload})
            self.outputs['Call_validation_child'] = child.response
            self.action_states['Call_validation_child'] = 'Succeeded'
            actions = deepcopy(actions);actions.pop('Call_validation_child')
            for action in actions.values():action.get('runAfter', {}).pop('Call_validation_child', None)
        return super().run(actions, ctx)


def test_generated_parent_executes_child_contract_and_reports_all_case_results():
    # Schema regression cases are also verified through build_package below.
    runner = ParentRunner(NoIO())
    runner.run(shared.parent_actions('child-id', shared.smoke_cases(), 'local-build'))
    report = runner.outputs['Smoke_report']
    assert report['allPassed'] and report['completedCount'] == len(shared.smoke_cases())
    assert report['failedCases'] == []


def native_export(path):
    """Small synthetic export with the inspected native packaging structure."""
    child_id = '11111111-1111-4111-8111-111111111111';parent_id = '22222222-2222-4222-8222-222222222222'
    names = [('Tandem81InvocationChild', child_id), ('Tandem81InvocationParent', parent_id)]
    custom = ET.Element('ImportExportXml');workflows = ET.SubElement(custom, 'Workflows')
    solution = ET.Element('ImportExportXml');manifest = ET.SubElement(solution, 'SolutionManifest')
    for key, value in [('UniqueName', 'Tandem81InvocationProof'), ('Version', '1.0.0.1'), ('Managed', '0')]:ET.SubElement(manifest, key).text=value
    ET.SubElement(ET.SubElement(manifest, 'LocalizedNames'), 'LocalizedName', {'description': 'Original proof'})
    publisher=ET.SubElement(manifest, 'Publisher');ET.SubElement(publisher, 'CustomizationPrefix').text='tandem'
    ET.SubElement(manifest, 'RootComponents')
    with ZipFile(path, 'w') as z:
        for name, id_ in names:
            file = 'Workflows/' + name + '-' + id_ + '.json'
            node = ET.SubElement(workflows, 'Workflow', {'WorkflowId': '{'+id_+'}', 'Name': name})
            for key,value in [('JsonFileName','/'+file),('IntroducedVersion','1.0.0.0'),('StateCode','1'),('StatusCode','2')]:ET.SubElement(node,key).text=value
            ET.SubElement(ET.SubElement(node,'LocalizedNames'),'LocalizedName',{'description':name})
            actions = {'Call': {'type': 'Workflow', 'inputs': {'host': {'workflowReferenceName': child_id}}, 'runAfter': {}}} if name.endswith('Parent') else {}
            doc={'properties':{'connectionReferences':{},'definition':{'triggers':{'manual':{'type':'Request','kind':'Button','inputs':{'schema':{}}}},'actions':actions}}}
            z.writestr(file,json.dumps(doc))
        z.writestr('customizations.xml', ET.tostring(custom));z.writestr('solution.xml',ET.tostring(solution));z.writestr('[Content_Types].xml','<Types/>')
    return child_id,parent_id


def test_native_solution_has_fresh_linked_ids_disabled_import_and_no_connectors(tmp_path):
    source=tmp_path/'source.zip';old_ids=native_export(source);output=tmp_path/'new.zip'
    review=shared.build_package(source,output)
    assert review['packageSha256']==hashlib.sha256(output.read_bytes()).hexdigest()
    with ZipFile(output) as z:
        assert z.testzip() is None
        allbytes=b''.join(z.read(n) for n in z.namelist())
        assert all(id_.encode() not in allbytes for id_ in old_ids)
        child_id=review['flows']['TandemValidateContext']['id']
        docs=[json.loads(z.read(n)) for n in z.namelist() if n.endswith('.json')]
        assert all(not d['properties']['connectionReferences'] for d in docs)
        parent=next(d for d in docs if 'Call_validation_child' in str(d))
        assert parent['properties']['definition']['actions']['Each_smoke_case']['actions']['Call_validation_child']['inputs']['host']['workflowReferenceName']==child_id
        runner = ParentRunner(NoIO());runner.build_id = review['packageBuildId']
        runner.run(parent['properties']['definition']['actions'])
        assert runner.outputs['Smoke_report']['allPassed']
        assert runner.outputs['Smoke_report']['completedCount'] == review['testCount'] == 44
        custom=ET.fromstring(z.read('customizations.xml'))
        assert all(n.findtext('StateCode')=='0' for n in custom.findall('./Workflows/Workflow'))
    for value in review['flows'].values():assert value['actions']<=500 and value['maximumActionDepth']<=8
    with pytest.raises(FileExistsError):shared.build_package(source,output)


def test_no_expected_business_rejection_uses_division_failure_or_terminate():
    actions=shared.definition_actions(BASELINE,'build','hash');s=json.dumps(actions)
    assert 'div(1,0)' not in s and 'Terminate' not in s
    assert 'OpenApiConnection' not in s and 'Http' not in s
    assert measure(actions)['actions']<150
