"""Generate #63 owner-preview cancel; Python is build/test tooling only."""
from copy import deepcopy
import argparse
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4
from zipfile import ZIP_DEFLATED, ZipFile

from .build_import_probe import build_package as envelope
from .discovery_flow import after, cat, complete, compose, condition, parse, query, setvar
from .schema_audit import ALL, FIELD_SELECT, measure, wdl_string

ROOT = Path(__file__).resolve().parents[2]
NAME = 'TandemCancelRequest v2'
REQUESTS = '3d17485d-1dac-41f0-a1af-24e45daa4567'
API = '/providers/Microsoft.PowerApps/apis/shared_sharepointonline'
MODE = 'OWNER_PREVIEW_PENDING_ACCESS_PROOF'


def load_source(path):
    path = Path(path)
    if path.suffix.lower() == '.zip':
        with ZipFile(path) as z:
            matches = [n for n in z.namelist() if n.endswith('/definition.json')]
            if len(matches) != 1:
                raise ValueError('Exactly one source flow required')
            return json.loads(z.read(matches[0]))
    return json.loads(path.read_text(encoding='utf-8'))


def source_adapter(original, mapping):
    p = original['properties']
    ref = p['connectionReferences']['shared_sharepointonline']
    if ref.get('source') != 'Invoker':
        raise ValueError('Invoker only; no owner fallback')
    def walk(block):
        for action in block.values():
            yield action
            yield from walk(action.get('actions', {}))
            yield from walk(action.get('else', {}).get('actions', {}))
    candidates = [a for a in walk(p['definition']['actions'])
                  if a.get('type') == 'OpenApiConnection' and
                  a['inputs'].get('parameters', {}).get('table', '').strip('{}').lower()
                  == mapping['lists']['participants']['listId']]
    if not candidates:
        raise ValueError('Missing participant source mapping')
    source = candidates[0]['inputs']
    if source['authentication'].get('type') != 'Raw':
        raise ValueError('Source Raw Invoker authentication required')
    return source['parameters']['dataset'], deepcopy(source['authentication'])


def expected_fields(people, groups):
    fields = {
        'SenderParticipant': {'type': 'Lookup', 'required': True, 'target': people},
        'RecipientParticipant': {'type': 'Lookup', 'required': False, 'target': people},
        'TargetGroup': {'type': 'Lookup', 'required': False, 'target': groups},
        'RequestType': {'type': 'Choice', 'required': True, 'choices': ['Personal', 'Group']},
        'Status': {'type': 'Choice', 'required': True, 'choices': ['Pending', 'Accepted', 'Declined', 'Cancelled']},
        'SendOperationKey': {'type': 'Text', 'required': True, 'unique': True},
        'ConnectionKey': {'type': 'Text', 'required': True, 'unique': True},
        'WinningOperationKey': {'type': 'Text', 'required': False},
        'OperationComplete': {'type': 'Boolean', 'required': False},
    }
    return fields


def snapshot_schema():
    integer = {'type': 'integer', 'minimum': 1, 'maximum': 2147483647}
    nullable = {**integer, 'type': ['integer', 'null']}
    fields = {'Id': integer, 'SenderParticipantId': integer,
              'RecipientParticipantId': nullable, 'TargetGroupId': nullable,
              'RequestType': {'type': 'string', 'enum': ['Personal', 'Group']},
              'Status': {'type': 'string', 'enum': ['Pending', 'Accepted', 'Declined', 'Cancelled']},
              'SendOperationKey': {'type': 'string', 'minLength': 1, 'maxLength': 255},
              'ConnectionKey': {'type': 'string', 'minLength': 1},
              'WinningOperationKey': {'type': ['string', 'null']},
              'OperationComplete': {'type': 'boolean'},
              '__metadata': {'type': 'object', 'required': ['etag', 'type'], 'properties': {
                  'etag': {'type': 'string', 'pattern': '^"[0-9]+"$'},
                  'type': {'type': 'string', 'minLength': 1}}}}
    return {'type': 'object', 'required': list(fields), 'properties': fields}


def row_expr(name, field):
    return f"body('{name}')?['{field}']"


def build_actions(original, mapping, groups):
    site, auth = source_adapter(original, mapping)
    people = mapping['lists']['participants']['listId']
    group = groups['lists']['groups']['listId']

    def base(id_):
        return "_api/web/lists(guid'" + id_ + "')"

    def http(uri, previous=None, *, method='GET', headers=None, payload=None):
        params = {'dataset': site, 'parameters/method': method, 'parameters/uri': uri,
                  'parameters/headers': {'Accept': 'application/json;odata=verbose', **(headers or {})}}
        if payload is not None:
            params['parameters/body'] = payload
        return {'type': 'OpenApiConnection', 'runAfter': after(previous), 'inputs': {
            'parameters': params,
            'host': {'apiId': API, 'connectionName': 'shared_sharepointonline', 'operationId': 'HttpRequest'},
            'authentication': deepcopy(auth), 'retryPolicy': {'type': 'none'}}}

    def gate(prefix, predicate, code, previous=None):
        # Names are globally unique, including both branches and stopped gates.
        return condition(predicate, {}, {
            prefix + '_error': setvar('ErrorCode', code),
            prefix + '_stop': compose('@div(1,0)', prefix + '_error')}, previous)

    def result(prefix, code, state, done, replay=False, previous=None):
        return {prefix + '_code': setvar('ResultCode', code, previous),
                prefix + '_state': setvar('CurrentStatus', state, prefix + '_code'),
                prefix + '_complete': setvar('Complete', done, prefix + '_state'),
                prefix + '_replay': setvar('Replay', replay, prefix + '_complete')}

    def metadata(prefix, id_, fields, previous):
        a = {prefix + '_guard': setvar('ErrorCode', 'REQUEST_SCHEMA_UNVERIFIED', previous),
             prefix + '_read': http(base(id_) + '/fields?$select=' + FIELD_SELECT + '&$top=501', prefix + '_guard')}
        prev = prefix + '_bound'
        a[prev] = gate(prev, complete(prefix + '_read', 500), 'REQUEST_SCHEMA_UNVERIFIED', prefix + '_read')
        for field, spec in fields.items():
            find = prefix + '_' + field
            tests = ["equals(item()?['InternalName']," + wdl_string(field) + ')',
                     "equals(item()?['TypeAsString']," + wdl_string(spec['type']) + ')',
                     "equals(item()?['Required']," + str(spec['required']).lower() + ')',
                     "equals(item()?['Hidden'],false)", "equals(item()?['ReadOnlyField'],false)"]
            if spec.get('unique'):
                tests += ["equals(item()?['EnforceUniqueValues'],true)", "equals(item()?['Indexed'],true)"]
            a[find] = query("@body('" + prefix + "_read')?['d']?['results']", 'and(' + ','.join(tests) + ')', prev)
            check = find + '_one'
            a[check] = gate(check, f"equals(length(body('{find}')),1)", 'REQUEST_SCHEMA_UNVERIFIED', find)
            prev = check
            xml = f"xml(first(body('{find}'))?['SchemaXml'])"
            if spec.get('target'):
                target = f"replace(replace(toLower(string(xpath({xml},'string(/Field/@List)'))),'{{',''),'}}','')"
                check = find + '_target'
                a[check] = gate(check, f"equals({target},'{spec['target']}')", 'REQUEST_SCHEMA_UNVERIFIED', prev)
                prev = check
            if spec.get('choices'):
                choices = f"xpath({xml},'/Field/CHOICES/CHOICE/text()')"
                expected = 'createArray(' + ','.join(wdl_string(c) for c in spec['choices']) + ')'
                tests = [f'equals(length({choices}),{len(spec["choices"])})',
                         f'equals(length(intersection({choices},{expected})),{len(spec["choices"])})',
                         f"or(empty(string(xpath({xml},'string(/Field/@FillInChoice)'))),equals(toLower(string(xpath({xml},'string(/Field/@FillInChoice)'))),'false'))"]
                check = find + '_choices'
                a[check] = gate(check, 'and(' + ','.join(tests) + ')', 'REQUEST_SCHEMA_UNVERIFIED', prev)
                prev = check
        a[prefix + '_verified'] = setvar('ErrorCode', '', prev)
        return a, prefix + '_verified'

    def validate_row(prefix, read, previous):
        a = {prefix + '_parse_guard': setvar('ErrorCode', 'REQUEST_INTEGRITY', previous),
             prefix: parse(f"@body('{read}')?['d']", snapshot_schema(), prefix + '_parse_guard')}
        r = lambda f: row_expr(prefix, f)
        pair_min = f"if(less({r('SenderParticipantId')},coalesce({r('RecipientParticipantId')},0)),{r('SenderParticipantId')},coalesce({r('RecipientParticipantId')},0))"
        pair_max = f"if(greater({r('SenderParticipantId')},coalesce({r('RecipientParticipantId')},0)),{r('SenderParticipantId')},coalesce({r('RecipientParticipantId')},0))"
        live = f"if(equals({r('RequestType')},'Personal'),concat('open:person:',string({pair_min}),':',string({pair_max})),concat('open:group:',string({r('TargetGroupId')}),':participant:',string({r('SenderParticipantId')})))"
        history = f"concat('history:request:',string({r('Id')}))"
        personal = f"and(equals({r('RequestType')},'Personal'),greater(coalesce({r('RecipientParticipantId')},0),0),not(equals({r('RecipientParticipantId')},{r('SenderParticipantId')})),equals({r('TargetGroupId')},null))"
        group_ = f"and(equals({r('RequestType')},'Group'),equals({r('RecipientParticipantId')},null),greater(coalesce({r('TargetGroupId')},0),0))"
        pending = f"and(equals({r('Status')},'Pending'),equals({r('OperationComplete')},false),empty({r('WinningOperationKey')}),equals({r('ConnectionKey')},{live}))"
        accepting = f"and(equals({r('Status')},'Accepted'),equals({r('OperationComplete')},false),not(empty({r('WinningOperationKey')})),equals({r('ConnectionKey')},{live}))"
        settled = f"and(not(equals({r('Status')},'Pending')),equals({r('OperationComplete')},true),not(empty({r('WinningOperationKey')})),equals({r('ConnectionKey')},{history}))"
        tests = [f"equals({r('Id')},body('Input')?['number_1'])", f"equals({r('SenderParticipantId')},outputs('Actor')?['Id'])",
                 f"equals({r('__metadata')}?['type'],body('Read_list_type')?['d']?['ListItemEntityTypeFullName'])",
                 f'not(empty(trim({r("SendOperationKey")})))', f'or({personal},{group_})', f'or({pending},{accepting},{settled})']
        a[prefix + '_checks'] = gate(prefix + '_checks', 'and(' + ','.join(tests) + ')', 'REQUEST_INTEGRITY', prefix)
        a[prefix + '_integrity'] = setvar('ErrorCode', '', prefix + '_checks')
        return a

    def terminal(prefix, row, previous=None):
        r = lambda f: row_expr(row, f)
        same = f"and(equals({r('Status')},'Cancelled'),equals({r('WinningOperationKey')},outputs('Cancel_key')),equals({r('OperationComplete')},true))"
        other = result(prefix + '_other', f"@if(equals({r('OperationComplete')},false),'ACCEPTED_INCOMPLETE','ALREADY_DECIDED')", '@' + r('Status'), '@' + r('OperationComplete'))
        return condition(same, result(prefix + '_saved', 'CANCELLED', 'Cancelled', True, prefix == 'Before'), other, previous)

    a = {}
    prev = None
    for name, kind, value in [('ErrorCode', 'string', 'INVALID_INPUT'), ('ResultCode', 'string', 'READ_OR_DATA_FAILED'),
                              ('CurrentStatus', 'string', ''), ('Complete', 'boolean', False),
                              ('Replay', 'boolean', False), ('WriteAttempted', 'boolean', False)]:
        n = 'Initialize_' + name
        a[n] = {'type': 'InitializeVariable', 'inputs': {'variables': [{'name': name, 'type': kind, 'value': value}]}, 'runAfter': after(prev)}
        prev = n
    integer = {'type': 'integer', 'minimum': 1, 'maximum': 2147483647}
    b = {'Input': parse('@triggerBody()', {'type': 'object', 'required': ['number', 'number_1'],
                                         'properties': {'number': integer, 'number_1': integer}, 'additionalProperties': False}),
         'Validated_input': setvar('ErrorCode', '', 'Input'),
         'Read_invoker': http('_api/web/currentuser?$select=Id', 'Validated_input'),
         'Invoker': parse("@body('Read_invoker')?['d']", {'type': 'object', 'required': ['Id'], 'properties': {'Id': integer}}, 'Read_invoker')}
    m, prev = metadata('People_schema', people, {'Participantaccount': {'type': 'User', 'required': True, 'unique': True}}, 'Invoker')
    b.update(m)
    own = cat(base(people) + '/items?$select=Id&$filter=ParticipantaccountId eq ', "@string(body('Invoker')?['Id'])", '&$top=2')
    b['Resolve_actor'] = http(own, prev)
    b['Require_actor_count'] = gate('Require_actor_count', complete('Resolve_actor', 1), 'UNAUTHORIZED', 'Resolve_actor')
    b['Require_actor_count']['expression'] = '@and(' + complete('Resolve_actor', 1) + ",equals(length(coalesce(body('Resolve_actor')?['d']?['results'],json('[]'))),1))"
    b['Actor'] = compose("@first(body('Resolve_actor')?['d']?['results'])", 'Require_actor_count')
    b['Require_actor_reference'] = gate('Require_actor_reference', "equals(outputs('Actor')?['Id'],body('Input')?['number'])", 'UNAUTHORIZED', 'Actor')
    m, prev = metadata('Request_schema', REQUESTS, expected_fields(people, group), 'Require_actor_reference')
    b.update(m)
    b['Read_list_type'] = http(base(REQUESTS) + '?$select=Id,ListItemEntityTypeFullName', prev)
    b['Require_list_type'] = parse("@body('Read_list_type')?['d']", {'type': 'object', 'required': ['ListItemEntityTypeFullName'], 'properties': {'ListItemEntityTypeFullName': {'type': 'string', 'minLength': 1}}}, 'Read_list_type')
    uri = cat(base(REQUESTS) + '/items(', "@string(body('Input')?['number_1'])", ')?$select=Id,SenderParticipantId,RecipientParticipantId,TargetGroupId,RequestType,Status,SendOperationKey,ConnectionKey,WinningOperationKey,OperationComplete')
    b['Read_request'] = http(uri, 'Require_list_type')
    b['Require_sender'] = gate('Require_sender', "equals(body('Read_request')?['d']?['SenderParticipantId'],outputs('Actor')?['Id'])", 'UNAUTHORIZED', 'Read_request')
    b.update(validate_row('Before_row', 'Read_request', 'Require_sender'))
    b['Cancel_key'] = compose("@concat('cancel:',string(outputs('Actor')?['Id']),':request:',string(body('Input')?['number_1']))", 'Before_row_integrity')
    write = {'Mark_write_attempt': setvar('WriteAttempted', True),
             'Cancel_CAS': http(cat(base(REQUESTS) + '/items(', "@string(body('Input')?['number_1'])", ')'), 'Mark_write_attempt', method='POST', headers={
                 'Content-Type': 'application/json;odata=verbose', 'X-HTTP-Method': 'MERGE', 'IF-MATCH': "@body('Before_row')?['__metadata']?['etag']"}, payload={
                     '__metadata': {'type': "@body('Before_row')?['__metadata']?['type']"},
                     'Status': 'Cancelled', 'ConnectionKey': "@concat('history:request:',string(body('Input')?['number_1']))",
                     'WinningOperationKey': "@outputs('Cancel_key')", 'OperationComplete': True})}
    write['Read_after_CAS'] = http(uri)
    write['Read_after_CAS']['runAfter'] = {'Cancel_CAS': ['Succeeded', 'Failed', 'TimedOut']}
    write.update(validate_row('After_row', 'Read_after_CAS', 'Read_after_CAS'))
    immutable = ['Id', 'SenderParticipantId', 'RecipientParticipantId', 'TargetGroupId', 'RequestType', 'SendOperationKey']
    write['Require_same_request'] = gate('Require_same_request', 'and(' + ','.join(f"equals(body('Before_row')?['{f}'],body('After_row')?['{f}'])" for f in immutable) + ')', 'REQUEST_INTEGRITY', 'After_row_integrity')
    still_pending = result('Unsettled', "@if(equals(outputs('Cancel_CAS')?['statusCode'],412),'RETRY_REQUIRED','OUTCOME_UNKNOWN')", 'Pending', False)
    write['Reconcile'] = condition("equals(body('After_row')?['Status'],'Pending')", still_pending, {'After_terminal': terminal('After', 'After_row')}, 'Require_same_request')
    b['Choose_pending'] = condition("equals(body('Before_row')?['Status'],'Pending')", write, {'Before_terminal': terminal('Before', 'Before_row')}, 'Cancel_key')
    a['Cancel_work'] = {'type': 'Scope', 'actions': b, 'runAfter': after('Initialize_WriteAttempted')}
    # A failed CAS is expected in a race; classification survives the red scope.
    a['Final_code'] = compose("@if(empty(variables('ErrorCode')),if(empty(variables('CurrentStatus')),if(variables('WriteAttempted'),'OUTCOME_UNKNOWN','READ_OR_DATA_FAILED'),variables('ResultCode')),variables('ErrorCode'))")
    a['Final_code']['runAfter'] = {'Cancel_work': ALL}
    a['Messages'] = compose({
        'CANCELLED': 'Your request was cancelled.',
        'ALREADY_DECIDED': 'This request already has a saved decision. Refresh history.',
        'ACCEPTED_INCOMPLETE': 'This request has been accepted and setup is not yet complete. It cannot be cancelled.',
        'OUTCOME_UNKNOWN': 'The cancellation outcome could not be confirmed. Refresh and retry the same request.',
        'RETRY_REQUIRED': 'The request changed while cancellation was attempted. Refresh and retry.',
        'REQUEST_INTEGRITY': 'The request record is incomplete or inconsistent. Contact support before retrying.',
        'REQUEST_SCHEMA_UNVERIFIED': 'Request configuration has not been verified. Contact the app owner.',
        'READ_OR_DATA_FAILED': 'The request could not be verified. Refresh and try again.',
        'UNAUTHORIZED': 'Only the sender can cancel this request.',
        'INVALID_INPUT': 'Choose a valid request before cancelling.'}, 'Final_code')
    props = {'success': {'type': 'boolean'}, 'message': {'type': 'string'}, 'resultcode': {'type': 'string'},
             'currentstatus': {'type': 'string'}, 'operationcomplete': {'type': 'boolean'}, 'replay': {'type': 'boolean'},
             'runreference': {'type': 'string'}, 'mode': {'type': 'string'},
             'writeattempted': {'type': 'boolean'}, 'outcomeunknown': {'type': 'boolean'}}
    for name, schema in props.items():
        schema.update(title=name, **{'x-ms-content-hint': 'BOOLEAN' if schema['type'] == 'boolean' else 'TEXT', 'x-ms-dynamically-added': True})
    a['Respond_to_a_Power_App_or_flow'] = {'type': 'Response', 'kind': 'PowerApp', 'runAfter': after('Messages'), 'inputs': {
        'statusCode': 200, 'schema': {'type': 'object', 'properties': props, 'additionalProperties': {}},
        'body': {'success': "@equals(outputs('Final_code'),'CANCELLED')", 'message': "@coalesce(outputs('Messages')?[outputs('Final_code')],'The request could not be verified. Refresh and try again.')",
                 'resultcode': "@outputs('Final_code')", 'currentstatus': "@if(empty(variables('ErrorCode')),variables('CurrentStatus'),'')",
                 'operationcomplete': "@and(empty(variables('ErrorCode')),variables('Complete'))", 'replay': "@variables('Replay')",
                 'runreference': "@workflow()?['run']?['name']", 'mode': MODE,
                 'writeattempted': "@variables('WriteAttempted')",
                 'outcomeunknown': "@and(variables('WriteAttempted'),or(equals(outputs('Final_code'),'OUTCOME_UNKNOWN'),not(empty(variables('ErrorCode')))))"}}}
    measure(a)
    return a


def build_package(source, output):
    source, output = Path(source), Path(output)
    if any(p.exists() for p in [output, output.with_suffix('.definition.json'), output.with_suffix('.review.json')]):
        raise FileExistsError(output)
    original = load_source(source)
    mapping = json.loads((ROOT / 'config/tenant_schema_mapping.json').read_text(encoding='utf-8'))
    groups = json.loads((ROOT / 'config/group_schema_mapping.json').read_text(encoding='utf-8'))
    site, _ = source_adapter(original, mapping)
    actions = build_actions(original, mapping, groups)
    # Actual cancel export preserves both arguments; baseline-only fallback documents fresh trigger.
    source_trigger = original['properties']['definition']['triggers']
    preserve = set(source_trigger['manual']['inputs']['schema']['properties']) == {'number', 'number_1'}
    if preserve:
        trigger = deepcopy(source_trigger)
    else:
        trigger = {'manual': {'type': 'Request', 'kind': 'PowerAppV2', 'inputs': {'schema': {
            'type': 'object', 'properties': {n: {'type': 'number', 'title': t, 'x-ms-content-hint': 'NUMBER', 'x-ms-dynamically-added': True}
                                          for n, t in [('number', 'ParticipantId'), ('number_1', 'RequestId')]}, 'required': ['number', 'number_1']}}}}
    if trigger['manual'].get('kind') != 'PowerAppV2':
        raise ValueError('PowerAppV2 trigger required')
    with TemporaryDirectory() as tmp:
        path = Path(tmp) / 'envelope.zip'
        envelope(path, sharepoint_site=site)
        with ZipFile(path) as z:
            entries = {n: json.loads(z.read(n)) for n in z.namelist()}
    doc = next(v for n, v in entries.items() if n.endswith('/definition.json'))
    doc['properties']['displayName'] = NAME
    doc['properties']['definition']['triggers'] = trigger
    doc['properties']['definition']['actions'] = actions
    ref = deepcopy(original['properties']['connectionReferences']['shared_sharepointonline'])
    ref['connectionName'] = 'IMPORT_SELECT_EXISTING_SHAREPOINT_CONNECTION'
    doc['properties']['connectionReferences'] = {'shared_sharepointonline': ref}
    entries['manifest.json']['details'].update(displayName=NAME, description='Issue 63 Invoker-only owner preview; Pending-only exact-ETag cancellation. Create as new; metadata gates required.')
    for item in entries['manifest.json']['resources'].values():
        if item['type'] == 'Microsoft.Flow/flows':
            item['details']['displayName'] = NAME
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, 'x', ZIP_DEFLATED) as z:
        for n, v in entries.items():
            z.writestr(n, json.dumps(v, indent=2) + '\n')
    review = {'sourceTicket': 63, 'packageBuildId': doc['name'], 'flowName': NAME, **measure(actions),
              'sourceSha256': hashlib.sha256(source.read_bytes()).hexdigest(),
              'generatorSha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'packageSha256': hashlib.sha256(output.read_bytes()).hexdigest(),
              'sourceTriggerPreserved': preserve, 'triggerDelta': 'none' if preserve else 'Fresh PowerAppV2 ParticipantId number + RequestId number_1; original Discovery input replaced.',
              'connectionSource': 'Invoker', 'rawAuthenticationPreserved': True, 'ownerCredentialFallback': False,
              'globalActionNamesUnique': True, 'writeActionDefinitions': 1, 'maximumWritesPerInvocation': 1,
              'writeRetries': 'none', 'requestMapping': 'PROPOSED_NOT_TENANT_VERIFIED_RUNTIME_GATED',
              'operationKey': 'cancel:{trustedParticipantId}:request:{requestId}', 'receipt': 'Atomic immutable terminal request row; no new receipt list.',
              'limits': {'actions': 500, 'depth': 8}, 'mode': MODE,
              'tenantResult': 'NOT_IMPORTED_NOT_TESTED', 'ordinaryUserAccessVerified': False}
    output.with_suffix('.definition.json').write_text(json.dumps(doc, indent=2) + '\n', encoding='utf-8')
    output.with_suffix('.review.json').write_text(json.dumps(review, indent=2) + '\n', encoding='utf-8')
    return review


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT / 'artifacts/tandem_discovery/TandemDiscovery-v2.definition.json')
    parser.add_argument('--output', type=Path, default=ROOT / 'artifacts/cancel_request/TandemCancelRequest-v2.zip')
    args = parser.parse_args()
    print(json.dumps(build_package(args.source, args.output), indent=2))


if __name__ == '__main__':
    main()
