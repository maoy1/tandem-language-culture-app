"""#81 one-time additive schema setup; no production row/permission mutations."""
from copy import deepcopy
from pathlib import Path
import json
from xml.etree import ElementTree as ET

from . import discovery_flow as d
from .schema_audit import ALL, measure

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = json.loads((ROOT / 'config/batch_schema_contract.json').read_text())
SP_API = '/providers/Microsoft.PowerApps/apis/shared_sharepointonline'
RAW = "@json(decodeBase64(triggerOutputs().headers['X-MS-APIM-Tokens']))['$ConnectionKey']"


def field_xml(spec):
    attrs = {'Name': spec['name'], 'StaticName': spec['name'], 'DisplayName': spec['name'],
             'Type': spec['type'], 'Required': str(spec.get('required', False)).upper()}
    for key, attr in [('unique', 'EnforceUniqueValues'), ('indexed', 'Indexed')]:
        if key in spec: attrs[attr] = str(spec[key]).upper()
    if spec['type'] == 'Text': attrs['MaxLength'] = str(spec.get('maxLength', 255))
    if spec['type'] == 'Note': attrs.update(RichText='FALSE', AppendOnly='FALSE', NumLines='6')
    node = ET.Element('Field', attrs)
    if 'default' in spec: ET.SubElement(node, 'Default').text = spec['default']
    return ET.tostring(node, encoding='unicode')


def request(uri, previous=None, method='GET', payload=None):
    inputs = {'host': {'connectionName': 'shared_sharepointonline', 'operationId': 'HttpRequest', 'apiId': SP_API},
              'authentication': {'type': 'Raw', 'value': RAW},
              'parameters': {'dataset': CONTRACT['site'], 'parameters/method': method,
                             'parameters/uri': uri, 'parameters/headers': {'Accept': 'application/json;odata=verbose'}}}
    if payload is not None:
        inputs['parameters']['parameters/body'] = payload
        inputs['parameters']['parameters/headers']['Content-Type'] = 'application/json;odata=verbose'
    if method != 'GET': inputs['retryPolicy'] = {'type': 'none'}
    return {'type': 'OpenApiConnection', 'inputs': inputs, 'runAfter': d.after(previous)}


def complete(action):
    return "and(equals(actions('" + action + "')?['status'],'Succeeded'),not(equals(body('" + action + "')?['d']?['results'],null)),empty(coalesce(body('" + action + "')?['d']?['__next'],body('" + action + "')?['@odata.nextLink'],'')))"


def field_match(spec):
    terms = ["equals(item()?['InternalName'],'" + spec['name'] + "')",
             "equals(item()?['TypeAsString'],'" + spec['type'] + "')",
             "equals(item()?['Required']," + str(spec.get('required', False)).lower() + ")",
             "equals(item()?['ReadOnlyField'],false)", "equals(item()?['Hidden'],false)",
             "equals(item()?['EnforceUniqueValues']," + str(spec.get('unique', False)).lower() + ")"]
    if spec.get('indexed'): terms.append("equals(item()?['Indexed'],true)")
    attr = lambda key: "string(xpath(xml(if(empty(item()?['SchemaXml']),'<Field/>',item()?['SchemaXml'])),'string(/Field/@" + key + ")'))"
    if spec['type'] == 'Note':
        terms.extend("not(equals(toLower(" + attr(k) + "),'true'))" for k in ['RichText', 'AppendOnly'])
    if spec['type'] == 'Text': terms.append("equals(" + attr('MaxLength') + ",'255')")
    if 'default' in spec:
        terms.append("contains(createArray('0','false'),toLower(string(item()?['DefaultValue'])))")
    return 'and(' + ','.join(terms) + ')'


def actions(build_id):
    a = {'Initialize_differences': {'type': 'InitializeVariable', 'inputs': {'variables': [
        {'name': 'Differences', 'type': 'array', 'value': []}]}, 'runAfter': {}}}
    a['Initialize_schema_snapshots'] = {'type': 'InitializeVariable', 'inputs': {'variables': [
        {'name': 'SchemaSnapshots', 'type': 'array', 'value': []}]}, 'runAfter': d.after('Initialize_differences')}
    def difference(code, field, previous=None):
        return {'type': 'AppendToArrayVariable', 'inputs': {'name': 'Differences',
                'value': {'code': code, 'field': field}}, 'runAfter': d.after(previous)}
    s = {'Read_web_permissions': request('_api/web/EffectiveBasePermissions')}
    permission = "equals(mod(div(int(coalesce(body('Read_web_permissions')?['d']?['EffectiveBasePermissions']?['Low'],body('Read_web_permissions')?['d']?['Low'],'0')),2048),2),1)"
    work = {}
    receipts = CONTRACT['receipts']
    work['Find_receipts'] = request("_api/web/lists?$filter=Title eq '" + receipts['title'] + "'&$select=Id,Title,Description,BaseTemplate,ItemCount&$top=2")
    create = request('_api/web/lists', method='POST', payload={'__metadata': {'type': 'SP.List'},
        'Title': receipts['title'], 'Description': receipts['description'], 'BaseTemplate': 100})
    work['Create_receipts_when_requested'] = d.condition(
        "and(" + complete('Find_receipts') + ",empty(body('Find_receipts')?['d']?['results']),equals(triggerBody()?['boolean'],true))",
        {'Create_receipts': create}, {}, 'Find_receipts')
    work['Read_receipts_after_setup'] = request("_api/web/lists?$filter=Title eq '" + receipts['title'] + "'&$select=Id,Title,Description,BaseTemplate,ItemCount&$top=2", 'Create_receipts_when_requested')
    base = "_api/web/lists/getbytitle('" + receipts['title'] + "')"
    available = {'Receipt_list': d.compose("@first(body('Read_receipts_after_setup')?['d']?['results'])")}
    valid_list = "and(equals(outputs('Receipt_list')?['BaseTemplate'],100),equals(outputs('Receipt_list')?['Description'],'" + receipts['description'] + "'))"
    edits = {}
    specs = [('receipts', base, spec) for spec in receipts['fields']]
    specs.append(('requests', "_api/web/lists(guid'" + CONTRACT['requestsListId'] + "')", CONTRACT['introduction']))
    previous = None
    for role, target, spec in specs:
        prefix = role + '_' + spec['name']
        read = 'Read_' + prefix
        edits[read] = request(target + '/fields?$select=InternalName,TypeAsString,Required,EnforceUniqueValues,Indexed,DefaultValue,Hidden,ReadOnlyField,SchemaXml&$top=500', previous)
        find = 'Find_' + prefix
        edits[find] = d.query("@body('" + read + "')?['d']?['results']", "equals(item()?['InternalName'],'" + spec['name'] + "')", read)
        gate = 'Add_' + prefix + '_if_missing'
        safe_empty = "equals(outputs('Receipt_list')?['ItemCount'],0)" if role == 'receipts' else 'true'
        edits[gate] = d.condition("and(" + complete(read) + ",empty(body('" + find + "')),equals(triggerBody()?['boolean'],true)," + safe_empty + ")",
            {'Create_' + prefix: request(target + '/fields/createfieldasxml', method='POST', payload={
                'parameters': {'__metadata': {'type': 'SP.XmlSchemaFieldCreationInformation'}, 'SchemaXml': field_xml(spec), 'Options': 0}})}, {}, find)
        after = 'Verify_read_' + prefix
        edits[after] = request(target + '/fields?$select=InternalName,TypeAsString,Required,EnforceUniqueValues,Indexed,DefaultValue,Hidden,ReadOnlyField,SchemaXml&$top=500', gate)
        match = 'Match_' + prefix
        edits[match] = d.query("@body('" + after + "')?['d']?['results']", field_match(spec), after)
        check = 'Verify_' + prefix
        edits[check] = d.condition("and(" + complete(after) + ",equals(length(body('" + match + "')),1))", {},
            {'Mismatch_' + prefix: difference('FIELD_MISSING_OR_MISMATCH', prefix)}, match)
        previous = check
    available['Receipt_list_scope'] = d.condition(valid_list, edits,
        {'Receipt_list_mismatch': difference('RECEIPT_LIST_IDENTITY_MISMATCH', '')}, 'Receipt_list')
    work['Receipt_list_exists'] = d.condition("and(" + complete('Read_receipts_after_setup') + ",equals(length(body('Read_receipts_after_setup')?['d']?['results']),1))", available,
        {'Receipt_list_missing': difference('RECEIPT_LIST_MISSING_OR_READ_INCOMPLETE', '')}, 'Read_receipts_after_setup')
    s['Require_setup_permission'] = d.condition("or(not(equals(triggerBody()?['boolean'],true))," + permission + ')', work,
        {'No_schema_permission': difference('MANAGE_LISTS_PERMISSION_UNVERIFIED', '')}, 'Read_web_permissions')
    a['Setup_or_audit'] = {'type': 'Scope', 'actions': s, 'runAfter': d.after('Initialize_schema_snapshots')}
    audit = audit_actions()
    a['Schema_extensions_ready'] = d.condition(
        "and(equals(actions('Setup_or_audit')?['status'],'Succeeded'),empty(variables('Differences')))", audit, {})
    a['Schema_extensions_ready']['runAfter'] = {'Setup_or_audit': ALL}
    a['Setup_report'] = d.compose({'kind': 'TandemBatchSchema', 'sourceTicket': 81, 'packageBuildId': build_id,
        'applyRequested': "@equals(triggerBody()?['boolean'],true)", 'runReference': "@workflow()?['run']?['name']",
        'schemaVerified': "@and(equals(actions('Schema_extensions_ready')?['status'],'Succeeded'),equals(body('Parse_schema_result')?['code'],'OK'),equals(body('Parse_schema_result')?['result']?['schemaMatches'],true),equals(body('Parse_schema_result')?['result']?['allSchema'],true))",
        'schemaResult': "@body('Parse_schema_result')?['result']",
        'collectionComplete': "@and(equals(actions('Each_schema_metadata')?['status'],'Succeeded'),equals(length(variables('SchemaSnapshots')),8),empty(body('Incomplete_schema_snapshots')))",
        'differences': "@variables('Differences')", 'rowWrites': 0, 'deletes': 0, 'permissionChanges': 0,
        'receiptList': "@outputs('Receipt_list')", 'scope': 'Additive schema only; no automatic conversions or rollback. Dry run by default.'})
    a['Setup_report']['runAfter'] = {'Schema_extensions_ready': ALL}
    measure(a)
    return a


def trigger():
    return {'manual': {'type': 'Request', 'kind': 'Button', 'inputs': {'schema': {'type': 'object',
        'properties': {'boolean': {'type': 'boolean', 'title': 'ApplyChanges', 'default': False}}, 'required': ['boolean']}}}}


def baseline():
    """Prospective batch baseline; original native-passed seven-role file retained."""
    from .shared_validation import mapping_digest
    result = json.loads((ROOT / 'config/shared_validation_schema.json').read_text())
    result['baselineVersion'] = 2
    result['nativeEvidence'] = 'NOT RUN for new batch extensions; prior seven-role evidence retained'
    result['sourceMappingHashes']['batchExtensions'] = mapping_digest(ROOT / 'config/batch_schema_contract.json')
    def field(spec):
        return {'name': spec['name'], 'type': spec['type'], 'required': spec.get('required', False),
                'unique': spec.get('unique', False), 'indexed': spec.get('indexed', False),
                'checkDefault': 'default' in spec, 'default': spec.get('default', ''),
                'choices': None, 'lookupList': None, 'showField': None, 'decimals': None,
                'maxLength': str(spec['maxLength']) if 'maxLength' in spec else None,
                'min': None, 'max': None, 'plainText': spec['type'] == 'Note'}
    next(x for x in result['lists'] if x['role'] == 'requests')['fields'].append(field(CONTRACT['introduction']))
    result['roles'].append('receipts')
    result['lists'].append({'role': 'receipts', 'listId': None, 'listTitle': CONTRACT['receipts']['title'],
                            'validationFormula': None, 'fields': [field(f) for f in CONTRACT['receipts']['fields']]})
    return result


def audit_actions():
    """Collect metadata once; all comparison rules live in the shared child."""
    specs = baseline()['lists']
    targets = [{'role': s['role'], 'base': "_api/web/lists(guid'" + s['listId'] + "')" if s['listId'] else
                "_api/web/lists/getbytitle('" + s['listTitle'] + "')"} for s in specs]
    a = {'Schema_targets': d.compose(targets)}
    loop = {'Read_schema_list': request("@concat(items('Each_schema_metadata')?['base'],'?$select=Id,Title,BaseTemplate,ValidationFormula')")}
    loop['Read_schema_fields'] = request("@concat(items('Each_schema_metadata')?['base'],'/fields?$select=InternalName,TypeAsString,Required,EnforceUniqueValues,Indexed,DefaultValue,Hidden,ReadOnlyField,SchemaXml&$top=500')", 'Read_schema_list')
    loop['Record_schema_snapshot'] = {'type': 'AppendToArrayVariable', 'inputs': {'name': 'SchemaSnapshots', 'value': {
        'role': "@items('Each_schema_metadata')?['role']", 'Id': "@body('Read_schema_list')?['d']?['Id']",
        'Title': "@body('Read_schema_list')?['d']?['Title']", 'BaseTemplate': "@body('Read_schema_list')?['d']?['BaseTemplate']",
        'ValidationFormula': "@body('Read_schema_list')?['d']?['ValidationFormula']",
        'Fields': "@body('Read_schema_fields')?['d']?['results']", 'complete': '@' + complete('Read_schema_fields')}},
        'runAfter': d.after('Read_schema_fields')}
    a['Each_schema_metadata'] = d.loop("@outputs('Schema_targets')", loop, 'Schema_targets')
    a['Incomplete_schema_snapshots'] = d.query("@variables('SchemaSnapshots')", "not(equals(item()?['complete'],true))", 'Each_schema_metadata')
    a['Schema_request'] = d.compose({'contractVersion': 1, 'rulesVersion': 1, 'mode': 'SCHEMA',
        'metadata': {'lists': "@variables('SchemaSnapshots')"}}, 'Incomplete_schema_snapshots')
    a['Validate_collected_schema'] = {'type': 'Scope', 'runAfter': d.after('Schema_request'), 'actions': {
        'Call_schema_validator': {'type': 'Workflow', 'inputs': {'host': {'workflowReferenceName': 'e9aa88eb-a666-4df1-b088-176be7bcd00d'},
            'body': {'text': "@string(outputs('Schema_request'))"}}, 'runAfter': {}},
        'Parse_schema_result': d.parse("@json(body('Call_schema_validator')?['resultjson'])", {'type': 'object'}, 'Call_schema_validator')}}
    return a
