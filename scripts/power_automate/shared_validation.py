"""#81 connector-free validation child and native Solution packaging.

Inputs are data, never authority. SharePoint reads and conditional writes remain
with authenticated adapters. Python is used only for local generation/testing.
"""
from copy import deepcopy
import argparse
import hashlib
import json
from pathlib import Path
from uuid import uuid4
from xml.etree import ElementTree as ET
from zipfile import ZipFile, ZIP_DEFLATED

from . import compatibility as rules
from . import discovery_flow as d
from .schema_audit import ALL, measure

ROOT = Path(__file__).resolve().parents[2]
MODES = ['SCHEMA', 'NORMALIZE', 'PAIR', 'GROUP', 'PROFILE']
CONTRACT_VERSION = 1


def write_json(path, value):
    Path(path).write_bytes((json.dumps(value, indent=2) + '\n').encode())


def mapping_digest(path):
    # Formatting/line-ending changes alone do not invalidate a schema contract.
    value = json.loads(Path(path).read_text(encoding='utf-8-sig'))
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def setvar(name, value, previous=None):
    return d.setvar(name, value, previous)


def finish(code, result, prefix, previous=None):
    """Only publish a result after its entire mode completed successfully."""
    return {
        prefix + '_result': setvar('Result', result, previous),
        prefix + '_code': setvar('Code', code, prefix + '_result'),
    }


def metadata_actions(baseline):
    """Compare raw native metadata to a versioned baseline, not to client claims.

    The operator/parent supplies completed native snapshots. This function does
    not collect them and cannot certify their provenance or freshness.
    """
    list_schema = {'type': 'object', 'required': ['role', 'Id', 'BaseTemplate', 'Fields', 'complete'],
                   'properties': {'role': {'type': 'string'}, 'Id': {'type': 'string'},
                    'BaseTemplate': {'type': 'integer'}, 'complete': {'type': 'boolean'},
                    'ValidationFormula': {'type': ['string', 'null']},
                    'Fields': {'type': 'array', 'maxItems': 500, 'items': {'type': 'object',
                        'required': ['InternalName', 'TypeAsString', 'Required', 'Indexed',
                                     'EnforceUniqueValues', 'Hidden', 'ReadOnlyField', 'SchemaXml', 'DefaultValue'],
                        'properties': {**{k: {'type': 'boolean'} for k in ['Required', 'Indexed', 'EnforceUniqueValues', 'Hidden', 'ReadOnlyField']},
                            **{k: {'type': 'string'} for k in ['InternalName', 'TypeAsString']},
                            'SchemaXml': {'type': ['string', 'null']},
                            'DefaultValue': {'type': ['string', 'boolean', 'null']}}}}}}
    a = {'Parse_metadata': d.parse("@body('Envelope')?['metadata']", {'type': 'object',
         'required': ['lists'], 'properties': {'lists': {'type': 'array', 'maxItems': 7, 'items': list_schema}}}),
         'Schema_baseline': d.compose(baseline, 'Parse_metadata')}
    # Full audit by default. A caller may explicitly select just relevant roles;
    # report distinguishes scoped validation from an all-schema audit.
    a['Requested_roles'] = d.parse("@coalesce(body('Envelope')?['schemaRoles'],outputs('Schema_baseline')?['roles'])",
        {'type': 'array', 'minItems': 1, 'maxItems': 7, 'items': {'type': 'string', 'enum': baseline['roles']}}, 'Schema_baseline')
    a['Expected_lists'] = d.query("@outputs('Schema_baseline')?['lists']", "contains(body('Requested_roles'),item()?['role'])", 'Requested_roles')
    inner = {'Find_metadata_list': d.query("@body('Parse_metadata')?['lists']",
         "equals(item()?['role'],items('Each_schema_list')?['role'])"),
         'Metadata_list': d.compose("@first(union(body('Find_metadata_list'),createArray(json('{}'))))", 'Find_metadata_list'),
         'Metadata_field_names': {'type': 'Select', 'inputs': {'from': "@coalesce(outputs('Metadata_list')?['Fields'],json('[]'))",
             'select': "@item()?['InternalName']"}, 'runAfter': d.after('Metadata_list')}}
    good_list = "and(equals(length(body('Find_metadata_list')),1),equals(toLower(coalesce(outputs('Metadata_list')?['Id'],'')),items('Each_schema_list')?['listId']),equals(outputs('Metadata_list')?['BaseTemplate'],100),equals(outputs('Metadata_list')?['complete'],true),equals(length(body('Metadata_field_names')),length(union(body('Metadata_field_names'),body('Metadata_field_names')))))"
    expected = "items('Each_schema_field')"
    xml = "xml(if(empty(item()?['SchemaXml']),'<Field/>',item()?['SchemaXml']))"
    attr = lambda key: "string(xpath(" + xml + ",'string(/Field/@" + key + ")'))"
    terms = ["equals(item()?['InternalName']," + expected + "?['name'])",
             "equals(item()?['TypeAsString']," + expected + "?['type'])",
             "equals(item()?['Required']," + expected + "?['required'])",
             "equals(item()?['EnforceUniqueValues']," + expected + "?['unique'])",
             "equals(item()?['Hidden'],false)", "equals(item()?['ReadOnlyField'],false)",
             "or(not(" + expected + "?['indexed']),equals(item()?['Indexed'],true))"]
    for key, prop in [('List', 'lookupList'), ('ShowField', 'showField'), ('Decimals', 'decimals'), ('MaxLength', 'maxLength'), ('Min', 'min'), ('Max', 'max')]:
        value = attr(key)
        if key == 'List': value = "replace(replace(toLower(" + value + "),'{',''),'}','')"
        terms.append("or(equals(" + expected + "?['" + prop + "'],null),equals(" + value + ',' + expected + "?['" + prop + "']))")
    choices = "xpath(" + xml + ",'/Field/CHOICES/CHOICE/text()')"
    terms.append("or(equals(" + expected + "?['choices'],null),and(equals(length(" + choices + "),length(coalesce(" + expected + "?['choices'],json('[]')))),equals(length(intersection(" + choices + ',coalesce(' + expected + "?['choices'],json('[]')))),length(" + choices + ")),not(equals(toLower(" + attr('FillInChoice') + "),'true'))))")
    default = "toLower(string(coalesce(item()?['DefaultValue'],'')))"
    default = "if(equals(item()?['TypeAsString'],'Boolean'),if(contains(createArray('1','true')," + default + "),'1',if(contains(createArray('0','false')," + default + "),'0'," + default + ")),string(coalesce(item()?['DefaultValue'],'')))"
    terms.append("or(not(" + expected + "?['checkDefault']),equals(" + default + ',' + expected + "?['default']))")
    fields = {'Matching_field': d.query("@outputs('Metadata_list')?['Fields']", 'and(' + ','.join(terms) + ')')}
    fields['Field_matches'] = d.condition("equals(length(body('Matching_field')),1)", {},
        {'Append_field_difference': {'type': 'AppendToArrayVariable', 'inputs': {'name': 'Differences', 'value': {
            'role': "@items('Each_schema_list')?['role']", 'field': "@items('Each_schema_field')?['name']",
            'code': 'FIELD_MISMATCH'}}, 'runAfter': {}}}, 'Matching_field')
    each = {'Each_schema_field': {'type': 'Foreach', 'foreach': "@items('Each_schema_list')?['fields']",
          'runtimeConfiguration': {'concurrency': {'repetitions': 1}}, 'actions': fields, 'runAfter': {}}}
    # Formula normalization tolerates SharePoint's optional [] and ordinary spaces.
    formula = "replace(replace(replace(toLower(coalesce(outputs('Metadata_list')?['ValidationFormula'],'')),'[',''),']',''),' ','')"
    each['List_formula_matches'] = d.condition("or(equals(items('Each_schema_list')?['validationFormula'],null),equals(" + formula + ",items('Each_schema_list')?['validationFormula']))", {},
        {'Append_formula_difference': {'type': 'AppendToArrayVariable', 'inputs': {'name': 'Differences', 'value': {
            'role': "@items('Each_schema_list')?['role']", 'field': '', 'code': 'LIST_VALIDATION_MISMATCH'}}, 'runAfter': {}}}, 'Each_schema_field')
    inner['List_matches'] = d.condition(good_list, each,
        {'Append_list_difference': {'type': 'AppendToArrayVariable', 'inputs': {'name': 'Differences', 'value': {
            'role': "@items('Each_schema_list')?['role']", 'field': '', 'code': 'LIST_MISSING_INCOMPLETE_OR_WRONG_ID'}}, 'runAfter': {}}}, 'Metadata_field_names')
    a['Each_schema_list'] = {'type': 'Foreach', 'foreach': "@body('Expected_lists')", 'actions': inner,
         'runtimeConfiguration': {'concurrency': {'repetitions': 1}}, 'runAfter': d.after('Expected_lists')}
    valid = "and(empty(variables('Differences')),equals(length(body('Expected_lists')),length(body('Requested_roles'))))"
    a.update(finish('@if(' + valid + ",'OK','SCHEMA_MISMATCH')", {'schemaMatches': '@' + valid,
        'checkedRoles': "@body('Requested_roles')", 'allSchema': "@equals(length(body('Requested_roles')),7)",
        'differences': "@variables('Differences')", 'provenanceVerified': False,
        'note': 'Compares supplied snapshots only; collector owns current complete authenticated reads.'}, 'Schema', 'Each_schema_list'))
    return a


def rule_actions():
    a = rules.normalization_actions('Normalize', "@body('Envelope')?['profiles']", "@body('Envelope')?['catalogues']")
    # Legacy blank availability stays blank/ineligible, never silently Active/Yes.
    props = a['Normalize_Parse_profiles']['inputs']['schema']['items']['properties']
    for key in ['status', 'participationStatus', 'openToConnections']:
        props[key]['type'] = [props[key]['type'], 'null']
        if 'enum' in props[key]: props[key]['enum'].append(None)
    # Status is an availability fact, not required content validity.
    a['Normalize_Invalid_profiles']['inputs']['where'] = a['Normalize_Invalid_profiles']['inputs']['where'].replace(
        ",not(empty(trim(item()?['status'])))", '')
    dedup = 'Normalize_Deduplicated_catalogues'
    old_catalogues = "body('Normalize_Parse_catalogues')"
    projection = {k: '@union(' + old_catalogues + "?['" + k + "']," + old_catalogues + "?['" + k + "'])"
                  for k in ['languageIds', 'cultureIds', 'timezoneIds']}
    projection['anyLanguageId'] = '@' + old_catalogues + "?['anyLanguageId']"
    # Insert after the typed parser so missing/invalid catalogue data cannot be
    # made valid merely by coalescing it to an empty collection.
    for name, action in a.items():
        if name not in ['Normalize_Parse_profiles', 'Normalize_Parse_catalogues']:
            a[name] = json.loads(json.dumps(action).replace(old_catalogues, "outputs('" + dedup + "')"))
    a[dedup] = d.compose(projection, 'Normalize_Parse_catalogues')
    a['Normalize_Concrete_languages']['runAfter'] = d.after(dedup)
    check = a['Normalize_Require_valid_input']['expression']
    a['Normalize_Require_valid_input'] = d.compose(check, 'Normalize_Keys_profileId')
    normalized = {'profiles': "@body('Normalize_Profiles')", 'catalogues': "@outputs('Normalize_Catalogues')"}
    branches = {'Return_normalization': d.condition("equals(body('Envelope')?['mode'],'NORMALIZE')", finish('OK', normalized, 'Normalized'))}
    pair = {'Parse_pair': d.parse("@body('Envelope')", {'type': 'object', 'required': ['leftId', 'rightId'],
        'properties': {k: {'type': 'integer', 'minimum': 1} for k in ['leftId', 'rightId']}}),
        'Find_left': d.query("@body('Normalize_Profiles')", "equals(item()?['profileId'],body('Envelope')?['leftId'])", 'Parse_pair'),
        'Find_right': d.query("@body('Normalize_Profiles')", "equals(item()?['profileId'],body('Envelope')?['rightId'])", 'Find_left')}
    pair['Pair_exists'] = d.condition("and(equals(length(body('Find_left')),1),equals(length(body('Find_right')),1))",
        finish('OK', rules.pair_expression_projection("first(body('Find_left'))", "first(body('Find_right'))"), 'Pair'),
        {'Pair_missing': setvar('Code', 'PROFILE_NOT_FOUND')}, 'Find_right')
    branches['Evaluate_pair'] = d.condition("equals(body('Envelope')?['mode'],'PAIR')", pair, {}, 'Return_normalization')
    group = {'Parse_group': d.parse("@body('Envelope')?['group']", rules.group_schema()),
        'Parse_candidate': d.parse("@body('Envelope')?['candidateId']", {'type': 'integer', 'minimum': 1}, 'Parse_group'),
        'Find_members': d.query("@body('Normalize_Profiles')", "contains(body('Parse_group')?['memberProfileIds'],item()?['profileId'])", 'Parse_candidate'),
        'Find_candidate': d.query("@body('Normalize_Profiles')", "equals(item()?['profileId'],body('Parse_candidate'))", 'Find_members')}
    groupcalc = rules.group_action_fragment('Group', "body('Parse_group')", "body('Find_members')", "first(body('Find_candidate'))", "outputs('Normalize_Catalogues')", 'FocusChecks')
    groupcalc.update(finish('OK', "@outputs('Group_Result')", 'Group_done', 'Group_Result'))
    group['Candidate_exists'] = d.condition("equals(length(body('Find_candidate')),1)", groupcalc,
        {'Candidate_missing': setvar('Code', 'PROFILE_NOT_FOUND')}, 'Find_candidate')
    branches['Evaluate_group'] = d.condition("equals(body('Envelope')?['mode'],'GROUP')", group, {}, 'Evaluate_pair')
    # Content validation is independent of participation/validation status.
    profile = {'Single_profile': d.condition("equals(length(body('Normalize_Profiles')),1)",
        finish('OK', {'valid': "@or(not(empty(first(body('Normalize_Parse_profiles'))?['teachIds'])),not(empty(first(body('Normalize_Parse_profiles'))?['learnIds'])),not(empty(first(body('Normalize_Parse_profiles'))?['shareCultureIds'])),not(empty(first(body('Normalize_Parse_profiles'))?['learnCultureIds'])))"}, 'Profile'),
        {'Profile_count_error': setvar('Code', 'PROFILE_COUNT_INVALID')})}
    branches['Evaluate_profile'] = d.condition("equals(body('Envelope')?['mode'],'PROFILE')", profile, {}, 'Evaluate_group')
    a['Normalized_input_valid'] = d.condition("outputs('Normalize_Require_valid_input')", branches,
        {'Invalid_profile_content': setvar('Code', 'INVALID_PROFILE_DATA')}, 'Normalize_Catalogues')
    return a


def definition_actions(baseline, build_id, source_hash):
    a = {}; previous = None
    for name, kind, value in [('Code', 'string', 'INVALID_INPUT'), ('Result', 'object', {}), ('FocusChecks', 'array', []), ('Differences', 'array', [])]:
        n = 'Initialize_' + name
        a[n] = {'type': 'InitializeVariable', 'inputs': {'variables': [{'name': name, 'type': kind, 'value': value}]}, 'runAfter': d.after(previous)}
        previous = n
    stage = {'Request_text': d.parse("@triggerBody()?['text']", {'type': 'string', 'maxLength': 250000}),
             'Envelope': d.parse("@json(body('Request_text'))", {'type': 'object',
             'required': ['contractVersion', 'rulesVersion', 'mode'], 'properties': {
                 'contractVersion': {'type': 'integer'}, 'rulesVersion': {'type': 'integer'}, 'mode': {'type': 'string'}}}, 'Request_text')}
    stage['Header_code'] = d.compose("@if(and(equals(body('Envelope')?['contractVersion'],1),equals(body('Envelope')?['rulesVersion'],1)),if(contains(createArray('SCHEMA','NORMALIZE','PAIR','GROUP','PROFILE'),body('Envelope')?['mode']),'READY','UNSUPPORTED_MODE'),'VERSION_MISMATCH')", 'Envelope')
    stage['Set_header_error'] = setvar('Code', "@if(equals(outputs('Header_code'),'READY'),'INVALID_INPUT',outputs('Header_code'))", 'Header_code')
    stage['Schema_mode'] = d.condition("and(equals(outputs('Header_code'),'READY'),equals(body('Envelope')?['mode'],'SCHEMA'))", metadata_actions(baseline), {}, 'Set_header_error')
    stage['Rules_mode'] = d.condition("and(equals(outputs('Header_code'),'READY'),contains(createArray('NORMALIZE','PAIR','GROUP','PROFILE'),body('Envelope')?['mode']))", rule_actions(), {}, 'Schema_mode')
    a['Evaluate'] = {'type': 'Scope', 'actions': stage, 'runAfter': d.after(previous)}
    succeeded = "equals(actions('Evaluate')?['status'],'Succeeded')"
    a['Result_size'] = d.compose("@length(string(variables('Result')))")
    a['Result_size']['runAfter'] = {'Evaluate': ALL}
    bounded = "lessOrEquals(outputs('Result_size'),200000)"
    code = "if(" + succeeded + ",if(" + bounded + ",variables('Code'),'RESPONSE_BOUND'),'INVALID_INPUT')"
    a['Validation_report'] = d.compose({'kind': 'TandemValidateContext', 'sourceTicket': 81,
        'contractVersion': 1, 'rulesVersion': rules.VERSION, 'packageBuildId': build_id,
        'sourceSha256': source_hash, 'runReference': "@workflow()?['run']?['name']",
        'success': "@and(" + succeeded + ',' + bounded + ",equals(variables('Code'),'OK'))", 'code': '@' + code,
        'result': '@if(and(' + succeeded + ',' + bounded + "),variables('Result'),json('{}'))", 'authorizesAction': False,
        'connectors': 0, 'reads': 0, 'writes': 0})
    a['Validation_report']['runAfter'] = d.after('Result_size')
    a['Respond_to_a_Power_App_or_flow'] = {'type': 'Response', 'kind': 'PowerApp', 'runAfter': d.after('Validation_report'),
        'inputs': {'statusCode': 200, 'body': {'resultjson': "@string(outputs('Validation_report'))",
            'resultcode': "@outputs('Validation_report')?['code']", 'success': "@outputs('Validation_report')?['success']"},
            'schema': {'type': 'object', 'properties': {k: {'title': k, 'type': t, 'x-ms-dynamically-added': True}
                for k, t in [('resultjson', 'string'), ('resultcode', 'string'), ('success', 'boolean')]}}}}
    measure(a)
    return a


def read_native_source(path):
    """Only accept the observed connector-free two-flow export as a template."""
    with ZipFile(path) as z:
        if z.testzip(): raise ValueError('Bad source archive')
        entries = {n: z.read(n) for n in z.namelist()}
    if len(entries) != 5: raise ValueError('Unexpected Solution components')
    solution = ET.fromstring(entries['solution.xml'])
    if solution.findtext('./SolutionManifest/Managed') != '0': raise ValueError('Expected unmanaged source')
    custom = ET.fromstring(entries['customizations.xml'])
    flows = {}
    for workflow in custom.findall('./Workflows/Workflow'):
        file = workflow.findtext('JsonFileName').lstrip('/')
        doc = json.loads(entries[file])
        if doc['properties']['connectionReferences']: raise ValueError('Source must have no connections')
        name = workflow.attrib['Name']
        flows['child' if name.endswith('Child') else 'parent'] = (workflow, doc)
    if set(flows) != {'child', 'parent'}: raise ValueError('Missing proof flows')
    child_id = flows['child'][0].attrib['WorkflowId'].strip('{}').lower()
    parent_actions = flows['parent'][1]['properties']['definition']['actions']
    if len(parent_actions) != 1 or next(iter(parent_actions.values()))['inputs']['host']['workflowReferenceName'].lower() != child_id:
        raise ValueError('Unrecognized native linkage')
    return entries, solution, custom, flows


def smoke_cases():
    """Use native cross-flow smoke tests; the child owns all actual checking."""
    f = json.loads((ROOT / 'tests/fixtures/compatibility_v1.json').read_text())
    cases = []
    for c in f['cases']:
        payload = {'contractVersion': 1, 'rulesVersion': 1, 'mode': 'PAIR' if c['kind'] == 'person' else 'GROUP',
                   'profiles': f['profiles'], 'catalogues': f['catalogues']}
        payload.update({k: c[k] for k in (['leftId', 'rightId'] if c['kind'] == 'person' else ['group', 'candidateId'])})
        cases.append({'id': c['id'], 'payload': payload, 'code': 'OK', 'expected': c['expected']})
    # Exact no-overlap owner incident, synthetic identities only.
    p = [{'profileId': 38, 'accountKey': 'synthetic38', 'status': 'Active', 'participationStatus': 'Active', 'openToConnections': True,
          'teachIds': [60, 63], 'learnIds': [65, 57], 'shareCultureIds': [24, 23], 'learnCultureIds': [9, 7]},
         {'profileId': 32, 'accountKey': 'synthetic32', 'status': 'Active', 'participationStatus': 'Active', 'openToConnections': True,
          'teachIds': [], 'learnIds': [59], 'shareCultureIds': [], 'learnCultureIds': []}]
    cases.append({'id': 'OWNER_NO_OVERLAP_38_32', 'payload': {'contractVersion': 1, 'rulesVersion': 1, 'mode': 'PAIR',
          'profiles': p, 'catalogues': {'languageIds': [60, 63, 65, 57, 59], 'cultureIds': [24, 23, 9, 7], 'timezoneIds': [], 'anyLanguageId': None},
          'leftId': 38, 'rightId': 32}, 'code': 'OK', 'expected': {'eligible': False, 'fitType': None,
          **{k: [] for k in ['canLearnLanguageIds', 'canShareLanguageIds', 'canLearnCultureIds', 'canShareCultureIds']}}})
    nullable = deepcopy(cases[0])
    nullable['id'] = 'LEGACY_NULL_PARTICIPATION'
    next(p for p in nullable['payload']['profiles'] if p['profileId'] == nullable['payload']['leftId'])['participationStatus'] = None
    nullable['expected'] = {'eligible': False, 'fitType': None,
        **{k: [] for k in ['canLearnLanguageIds', 'canShareLanguageIds', 'canLearnCultureIds', 'canShareCultureIds']}}
    cases.append(nullable)
    wrong_version = deepcopy(cases[0]); wrong_version['id'] = 'CONTRACT_VERSION_REJECTED'
    wrong_version['payload']['contractVersion'] = 999
    wrong_version['code'] = 'VERSION_MISMATCH'; wrong_version['expected'] = {}
    cases.append(wrong_version)
    return cases


def parent_actions(child_id, cases, build_id):
    inner = {'Call_validation_child': {'type': 'Workflow', 'inputs': {'host': {'workflowReferenceName': child_id},
               'body': {'text': "@string(items('Each_smoke_case')?['payload'])"}}, 'runAfter': {}},
             'Parse_child_result': d.parse("@json(body('Call_validation_child')?['resultjson'])", {'type': 'object'}, 'Call_validation_child')}
    inner['Append_smoke_result'] = {'type': 'AppendToArrayVariable', 'runAfter': d.after('Parse_child_result'),
         'inputs': {'name': 'Results', 'value': {'id': "@items('Each_smoke_case')?['id']",
          'passed': "@and(equals(body('Parse_child_result')?['code'],items('Each_smoke_case')?['code']),equals(body('Parse_child_result')?['result'],items('Each_smoke_case')?['expected']),equals(body('Parse_child_result')?['packageBuildId'],'" + build_id + "'))",
          'childRunReference': "@body('Parse_child_result')?['runReference']", 'actual': "@body('Parse_child_result')?['result']"}}}
    a = {'Initialize_results': {'type': 'InitializeVariable', 'inputs': {'variables': [{'name': 'Results', 'type': 'array', 'value': []}]}, 'runAfter': {}},
         'Smoke_cases': d.compose(cases, 'Initialize_results'),
         'Each_smoke_case': {'type': 'Foreach', 'foreach': "@outputs('Smoke_cases')", 'actions': inner,
            'runtimeConfiguration': {'concurrency': {'repetitions': 1}}, 'runAfter': d.after('Smoke_cases')}}
    a['Failed_cases'] = d.query("@variables('Results')", "not(equals(item()?['passed'],true))")
    a['Failed_cases']['runAfter'] = {'Each_smoke_case': ALL}
    a['Smoke_report'] = d.compose({'kind': 'TandemValidationSmoke', 'sourceTicket': 81, 'packageBuildId': build_id,
        'syntheticOnly': True, 'runReference': "@workflow()?['run']?['name']", 'testCount': len(cases),
        'completedCount': "@length(variables('Results'))", 'allPassed': "@and(equals(actions('Each_smoke_case')?['status'],'Succeeded'),empty(body('Failed_cases')),equals(length(variables('Results'))," + str(len(cases)) + '))',
        'failedCases': "@body('Failed_cases')", 'connectors': 0, 'reads': 0, 'writes': 0}, 'Failed_cases')
    return a


def build_package(source, output, baseline_path=None):
    output = Path(output)
    if output.exists() or output.with_suffix('.review.json').exists(): raise FileExistsError(output)
    baseline_path = Path(baseline_path or ROOT / 'config/shared_validation_schema.json')
    baseline = json.loads(baseline_path.read_text())
    verify_baseline_sources(baseline)
    entries, solution, custom, flows = read_native_source(source)
    build_id = str(uuid4())
    rules_hash = hashlib.sha256(Path(rules.__file__).read_bytes()).hexdigest()
    new_ids = {k: str(uuid4()) for k in flows}
    child_actions = definition_actions(baseline, build_id, rules_hash)
    cases = smoke_cases()
    # Include complete and intentionally mismatched schema snapshots in native smoke.
    schema = synthetic_metadata(baseline)
    for label, metadata in [('SCHEMA_BASELINE', schema), ('SCHEMA_CHANGED_REQUIRED', deepcopy(schema))]:
        if label.endswith('REQUIRED'): metadata['lists'][0]['Fields'][0]['Required'] = not metadata['lists'][0]['Fields'][0]['Required']
        expected = {'schemaMatches': label == 'SCHEMA_BASELINE', 'checkedRoles': baseline['roles'], 'allSchema': True,
            'differences': [] if label == 'SCHEMA_BASELINE' else [{'role': baseline['lists'][0]['role'], 'field': baseline['lists'][0]['fields'][0]['name'], 'code': 'FIELD_MISMATCH'}],
            'provenanceVerified': False, 'note': 'Compares supplied snapshots only; collector owns current complete authenticated reads.'}
        cases.append({'id': label, 'payload': {'contractVersion': 1, 'rulesVersion': 1, 'mode': 'SCHEMA', 'metadata': metadata},
            'code': 'OK' if label == 'SCHEMA_BASELINE' else 'SCHEMA_MISMATCH', 'expected': expected})
    parent = parent_actions(new_ids['child'], cases, build_id)
    names = {'child': 'TandemValidateContext', 'parent': 'TandemValidationSmoke'}
    new_entries = {n: b for n, b in entries.items() if not n.startswith('Workflows/')}
    for role, (node, doc) in flows.items():
        id_ = new_ids[role]; name = names[role]
        file = 'Workflows/' + name + '-' + id_.upper() + '.json'
        node.set('WorkflowId', '{' + id_ + '}'); node.set('Name', name)
        node.find('JsonFileName').text = '/' + file
        node.find('IntroducedVersion').text = '1.0.0.0'
        # Import disabled; owner explicitly enables only disposable generated flows.
        node.find('StateCode').text = '0'; node.find('StatusCode').text = '1'
        node.find('./LocalizedNames/LocalizedName').set('description', name)
        definition = doc['properties']['definition']
        definition['triggers']['manual'].pop('metadata', None)
        definition['triggers']['manual']['inputs']['schema'] = {'type': 'object', 'properties': {} if role == 'parent' else {
            'text': {'title': 'RequestJson', 'type': 'string', 'x-ms-dynamically-added': True, 'x-ms-content-hint': 'TEXT'}},
            'required': [] if role == 'parent' else ['text']}
        definition['actions'] = child_actions if role == 'child' else parent
        new_entries[file] = (json.dumps(doc, indent=2) + '\n').encode()
    manifest = solution.find('SolutionManifest')
    manifest.find('UniqueName').text = 'TandemSharedValidation81'
    manifest.find('Version').text = '1.0.0.0'
    manifest.find('./LocalizedNames/LocalizedName').set('description', 'Tandem Shared Validation 81')
    roots = manifest.find('RootComponents'); roots.clear()
    for id_ in new_ids.values(): ET.SubElement(roots, 'RootComponent', {'type': '29', 'id': '{' + id_ + '}', 'behavior': '0'})
    new_entries['solution.xml'] = ET.tostring(solution, encoding='utf-8', xml_declaration=True)
    new_entries['customizations.xml'] = ET.tostring(custom, encoding='utf-8', xml_declaration=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, 'x', ZIP_DEFLATED) as z:
        for n, b in new_entries.items(): z.writestr(n, b)
    review = {'sourceTicket': 81, 'packageBuildId': build_id, 'solutionName': 'TandemSharedValidation81',
        'sourceExportSha256': hashlib.sha256(Path(source).read_bytes()).hexdigest(),
        'packageSha256': hashlib.sha256(output.read_bytes()).hexdigest(),
        'sourceSha256': rules_hash, 'schemaSha256': hashlib.sha256(baseline_path.read_bytes()).hexdigest(),
        'generatorSha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'flows': {names[k]: {'id': new_ids[k], **measure(child_actions if k == 'child' else parent)} for k in new_ids},
        'testCount': len(cases), 'connectors': 0, 'reads': 0, 'writes': 0,
        'newSolutionAndNewFlowIds': True, 'consumerCutover': False, 'importState': 'disabled',
        'nativeResult': 'NOT_IMPORTED_NOT_TESTED', 'metadataProvenance': 'Supplied snapshots; no live audit certification',
        'callerBoundary': 'Pure evaluator, never authorization; existing parent Invoker retained'}
    write_json(output.with_suffix('.review.json'), review)
    for name, actions in [('child', child_actions), ('smoke', parent)]: write_json(output.with_suffix('.' + name + '.definition.json'), actions)
    return review


def verify_baseline_sources(baseline):
    """Prevent rebuilding from a stale participant/group contract snapshot.

    Request mapping is evidence from the separate unmerged #10 branch; that
    immutable evidence is versioned here until the live mapping lands on main.
    Consumer migration/freshness validation remains separately required.
    """
    paths = {'participantCatalogue': ROOT / 'config/tenant_schema_mapping.json',
             'groupMembers': ROOT / 'config/group_schema_mapping.json',
             'requests': ROOT / 'artifacts/shared_validation/results/request-mapping.baseline.json'}
    for name, path in paths.items():
        if mapping_digest(path) != baseline['sourceMappingHashes'][name]:
            raise ValueError('Schema mapping drift: update #81 baseline/evidence for ' + name)


def synthetic_metadata(baseline):
    """Non-live metadata fixture for emitted/native regression tests only."""
    lists = []
    for spec in baseline['lists']:
        fields = []
        for f in spec['fields']:
            xml = ET.Element('Field')
            for key, prop in [('List', 'lookupList'), ('ShowField', 'showField'), ('Decimals', 'decimals'), ('MaxLength', 'maxLength'), ('Min', 'min'), ('Max', 'max')]:
                if f.get(prop) is not None: xml.set(key, f[prop])
            if f.get('choices') is not None:
                xml.set('FillInChoice', 'FALSE'); choices = ET.SubElement(xml, 'CHOICES')
                for value in f['choices']: ET.SubElement(choices, 'CHOICE').text = value
            fields.append({'InternalName': f['name'], 'TypeAsString': f['type'], 'Required': f['required'],
                'Indexed': f['indexed'], 'EnforceUniqueValues': f['unique'], 'Hidden': False, 'ReadOnlyField': False,
                'DefaultValue': f['default'] if f['checkDefault'] else None, 'SchemaXml': ET.tostring(xml, encoding='unicode')})
        lists.append({'role': spec['role'], 'Id': spec['listId'], 'BaseTemplate': 100, 'complete': True,
            'Fields': fields, 'ValidationFormula': spec.get('validationFormula')})
    return {'lists': lists}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True); parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); print(json.dumps(build_package(args.source, args.output), indent=2))
