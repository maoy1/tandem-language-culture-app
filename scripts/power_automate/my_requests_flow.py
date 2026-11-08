"""Build #62 read-only TandemMyRequests; Python is local build/test tooling only."""
from copy import deepcopy
import argparse
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4
from zipfile import ZipFile, ZIP_DEFLATED
from .build_import_probe import build_package as envelope
from .schema_audit import measure

ROOT = Path(__file__).resolve().parents[2]
NAME = 'TandemMyRequests'
BOUNDS = {'requests': 500, 'memberships': 2000, 'profiles': 500, 'groups': 100, 'fields': 500, 'responseChars': 250000}
REQUESTS = '3d17485d-1dac-41f0-a1af-24e45daa4567'


def after(n): return {n: ['Succeeded']} if n else {}
def compose(v, n=None): return {'type': 'Compose', 'inputs': v, 'runAfter': after(n)}
def query(src, pred, n=None): return {'type': 'Query', 'inputs': {'from': src, 'where': '@' + pred}, 'runAfter': after(n)}
def parse(src, schema, n=None): return {'type': 'ParseJson', 'inputs': {'content': src, 'schema': schema}, 'runAfter': after(n)}
def setvar(k, v, n=None): return {'type': 'SetVariable', 'inputs': {'name': k, 'value': v}, 'runAfter': after(n)}
def append(k, v, n=None): return {'type': 'AppendToArrayVariable', 'inputs': {'name': k, 'value': v}, 'runAfter': after(n)}
def loop(src, actions, n=None): return {'type': 'Foreach', 'foreach': src, 'actions': actions, 'runtimeConfiguration': {'concurrency': {'repetitions': 1}}, 'runAfter': after(n)}
def branch(pred, yes, no=None, n=None): return {'type': 'If', 'expression': '@' + pred, 'actions': yes, 'else': {'actions': no or {}}, 'runAfter': after(n)}
def rows(n): return "body('" + n + "')?['d']?['results']"
def first(n): return "first(union(body('" + n + "'),createArray(json('{}'))))"
def obj(props): return {'type': 'object', 'required': list(props), 'properties': props}
def integer(nullable=False): return {'type': ['integer', 'null'] if nullable else 'integer', 'minimum': 1}
def text(): return {'type': 'string', 'minLength': 1}
def choice(*v): return {'type': 'string', 'enum': list(v)}


def complete(n, bound):
    d = "body('" + n + "')?['d']"
    return f"and(not(equals({d}?['results'],null)),lessOrEquals(length(coalesce({d}?['results'],json('[]'))),{bound}),empty({d}?['__next']),empty(body('{n}')?['@odata.nextLink']),empty(body('{n}')?['odata.nextLink']))"


def field_contracts(people, groups):
    p = people['lists']['participants']['listId']
    g = groups['lists']['groups']['listId']
    def field(t, required=False, unique=False, indexed=False, **extra):
        return {'TypeAsString': t, 'Required': required, 'EnforceUniqueValues': unique, 'Indexed': indexed, **extra}
    return {
        'requests': {
            'SenderParticipant': field('Lookup', True, LookupList=p),
            'RecipientParticipant': field('Lookup', False, LookupList=p),
            'TargetGroup': field('Lookup', False, LookupList=g),
            'RequestType': field('Choice', True, Choices=['Personal', 'Group']),
            'Status': field('Choice', True, Choices=['Pending', 'Accepted', 'Declined', 'Cancelled']),
            'SendOperationKey': field('Text', True, True, True),
            'ConnectionKey': field('Text', True, True, True),
            'WinningOperationKey': field('Text'), 'OperationComplete': field('Boolean'),
        },
        'profiles': {'Participantaccount': field('User', True, True, True)},
        # Existing #12 observed mappings: verify the fields actually relied on each run.
        'groups': {name: field(v['type'], v.get('required', False), v.get('unique', False), v.get('indexed', False), **({'Choices': v['choices']} if 'choices' in v else {}))
                   for name, v in groups['lists']['groups']['fields'].items()
                   if name in ['SourceRequestId', 'SetupComplete', 'State', 'Capacity', 'WriteOwner']},
        'memberships': {name: field(v['type'], v.get('required', False), v.get('unique', False), v.get('indexed', False),
                                   **({'LookupList': v['lookupListId']} if 'lookupListId' in v else {}), **({'Choices': v['choices']} if 'choices' in v else {}))
                        for name, v in groups['lists']['members']['fields'].items()
                        if name in ['Group', 'Participant', 'MembershipStatus', 'MembershipKey', 'LeftAt']},
    }


def read_source(path):
    path = Path(path)
    if path.suffix.lower() == '.zip':
        with ZipFile(path) as z:
            names = [n for n in z.namelist() if n.endswith('/definition.json')]
            if len(names) != 1: raise ValueError('Expected one source flow')
            return json.loads(z.read(names[0]))
    return json.loads(path.read_text(encoding='utf-8'))


def source_metadata(original):
    prop = original['properties']
    ref = prop['connectionReferences']['shared_sharepointonline']
    if ref.get('source') != 'Invoker': raise ValueError('Invoker required; no owner fallback')
    trigger = prop['definition']['triggers']
    if trigger['manual']['kind'] != 'PowerAppV2' or set(trigger['manual']['inputs']['schema']['properties']) != {'number'}:
        raise ValueError('Expected existing ParticipantId number trigger')
    source = prop['definition']['actions']['Read_participant']['inputs']
    if source['authentication'].get('type') != 'Raw': raise ValueError('Original Invoker Raw authentication required')
    if prop['definition']['actions']['Get_items']['inputs']['parameters']['table'].strip('{}').lower() != REQUESTS:
        raise ValueError('Unexpected request list target')
    return source['parameters']['dataset'], deepcopy(source['authentication'])


def build_actions(original, people, groups, build_id):
    site, auth = source_metadata(original)
    targets = {'requests': REQUESTS, 'profiles': people['lists']['participants']['listId'],
               'groups': groups['lists']['groups']['listId'], 'memberships': groups['lists']['members']['listId']}
    if original['properties']['definition']['actions']['Read_participant']['inputs']['parameters']['table'].strip('{}').lower() != targets['profiles']:
        raise ValueError('Unexpected participant target')
    def base(role): return "_api/web/lists(guid'" + targets[role] + "')"
    def http(uri, n=None):
        return {'type': 'OpenApiConnection', 'runAfter': after(n), 'inputs': {
            'parameters': {'dataset': site, 'parameters/method': 'GET', 'parameters/uri': uri,
                           'parameters/headers': {'Accept': 'application/json;odata=verbose'}},
            'host': {'apiId': '/providers/Microsoft.PowerApps/apis/shared_sharepointonline', 'connectionName': 'shared_sharepointonline', 'operationId': 'HttpRequest'},
            'authentication': deepcopy(auth)}}
    # Prefixes are unique across the ENTIRE graph, including every else branch.
    def gate(name, pred, code, n=None):
        return branch(pred, {}, {name + '_error': setvar('ErrorCode', code), name + '_stop': compose('@div(1,0)', name + '_error')}, n)
    a = {}; prev = None
    for k, t, v in [('ErrorCode', 'string', ''), ('Requests', 'array', []), ('OperationalGroups', 'array', [])]:
        name = 'Initialize_' + k
        a[name] = {'type': 'InitializeVariable', 'inputs': {'variables': [{'name': k, 'type': t, 'value': v}]}, 'runAfter': after(prev)}; prev = name
    s = {'Input_reference': parse("@triggerBody()?['number']", integer()),
         'Read_invoker': http('_api/web/currentuser?$select=Id', 'Input_reference'),
         'Invoker': parse("@body('Read_invoker')?['d']", obj({'Id': integer()}), 'Read_invoker')}
    s['Metadata_stage'] = setvar('ErrorCode', 'REQUEST_SCHEMA_UNVERIFIED', 'Invoker')
    prev = 'Metadata_stage'
    for role, fields in field_contracts(people, groups).items():
        read = 'Read_' + role + '_fields'
        identity = 'Read_' + role + '_list'
        s[identity] = http(base(role) + '?$select=Id,BaseTemplate', prev)
        verified = role + '_list_verified'
        s[verified] = gate(verified, "and(equals(toLower(body('" + identity + "')?['d']?['Id']),'" + targets[role] + "'),equals(body('" + identity + "')?['d']?['BaseTemplate'],100))", 'REQUEST_SCHEMA_UNVERIFIED', identity)
        s[read] = http(base(role) + '/fields?$select=InternalName,TypeAsString,Required,EnforceUniqueValues,Indexed,SchemaXml&$top=501', verified)
        bounded = role + '_metadata_complete'
        s[bounded] = gate(bounded, complete(read, 500), 'REQUEST_SCHEMA_UNVERIFIED', read); prev = bounded
        for name, expected in fields.items():
            q = role + '_field_' + name
            tests = ["equals(item()?['InternalName'],'" + name + "')"]
            schema_xml = "xml(coalesce(item()?['SchemaXml'],'<Field/>'))"
            lookup = "first(union(xpath(" + schema_xml + ",'/Field/@List'),createArray('')))"
            choices = "xpath(" + schema_xml + ",'/Field/CHOICES/CHOICE/text()')"
            for key, value in expected.items():
                if key == 'LookupList': tests.append("equals(toLower(replace(replace(" + lookup + ",'{',''),'}','')),'" + value + "')")
                elif key == 'Choices':
                    tests.append('equals(length(' + choices + '),' + str(len(value)) + ')')
                    tests += ["contains(" + choices + ",'" + v + "')" for v in value]
                else: tests.append("equals(item()?['" + key + "']," + (str(value).lower() if isinstance(value, bool) else "'" + value + "'") + ')')
            s[q] = query('@' + rows(read), 'and(' + ','.join(tests) + ')', prev)
            g = q + '_gate'; s[g] = gate(g, "equals(length(body('" + q + "')),1)", 'REQUEST_SCHEMA_UNVERIFIED', q); prev = g
    # URI is constructed only from server-validated numeric identity.
    ownuri = "@concat('" + base('profiles').replace("'", "''") + "/items?$select=Id&$filter=ParticipantaccountId eq ',string(body('Invoker')?['Id']),'&$top=2')"
    s['Metadata_verified'] = setvar('ErrorCode', '', prev)
    s['Read_own'] = http(ownuri, 'Metadata_verified')
    s['Own_complete'] = gate('Own_complete', complete('Read_own', 1), 'UNAUTHORIZED_PROFILE', 'Read_own')
    s['Own_match'] = gate('Own_match', "and(equals(length(" + rows('Read_own') + "),1),equals(first(union(" + rows('Read_own') + ",createArray(json('{}'))))?['Id'],triggerBody()?['number']))", 'UNAUTHORIZED_PROFILE', 'Own_complete')
    s['Actor'] = compose("@triggerBody()?['number']", 'Own_match'); prev = 'Actor'
    selects = {
        'requests': 'Id,SenderParticipantId,RecipientParticipantId,TargetGroupId,RequestType,Status,SendOperationKey,ConnectionKey,WinningOperationKey,OperationComplete',
        'profiles': 'Id,Status,ParticipationStatus,OpenToConnections',
        'groups': 'Id,SourceRequestId,SetupComplete,State,Capacity,WriteOwner',
        'memberships': 'Id,GroupId,ParticipantId,MembershipStatus,MembershipKey,LeftAt',
    }
    schemas = {
        'requests': obj({'Id': integer(), 'SenderParticipantId': integer(), 'RecipientParticipantId': integer(True), 'TargetGroupId': integer(True),
                         'RequestType': choice('Personal', 'Group'), 'Status': choice('Pending', 'Accepted', 'Declined', 'Cancelled'),
                         'SendOperationKey': text(), 'ConnectionKey': text(), 'WinningOperationKey': {'type': ['string', 'null']}, 'OperationComplete': {'type': 'boolean'}}),
        'profiles': obj({'Id': integer(), 'Status': {'type': 'string'}, 'ParticipationStatus': choice('Active', 'Paused', 'Inactive'), 'OpenToConnections': {'type': 'boolean'}}),
        'groups': obj({'Id': integer(), 'SourceRequestId': integer(), 'SetupComplete': {'type': 'boolean'}, 'State': choice('Open', 'Closed', 'Ended'), 'Capacity': {'type': 'integer', 'minimum': 2, 'maximum': 10}, 'WriteOwner': {'type': ['string', 'null']}}),
        'memberships': obj({'Id': integer(), 'GroupId': integer(), 'ParticipantId': integer(), 'MembershipStatus': choice('Active', 'Left'), 'MembershipKey': text(), 'LeftAt': {'type': ['string', 'null']}}),
    }
    for role in selects:
        read = 'Read_' + role; bound = role + '_complete'; parsed = 'Data_' + role
        s[read] = http(base(role) + '/items?$select=' + selects[role] + '&$orderby=Id asc&$top=' + str(BOUNDS[role] + 1), prev)
        s[bound] = gate(bound, complete(read, BOUNDS[role]), 'READ_BOUND_OR_INCOMPLETE', read)
        code = 'REQUEST_DATA_INCOMPLETE' if role == 'requests' else 'DATA_INTEGRITY'
        s[role + '_parse_code'] = setvar('ErrorCode', code, bound)
        s[parsed] = parse('@' + rows(read), {'type': 'array', 'items': schemas[role]}, role + '_parse_code')
        s[role + '_parsed'] = setvar('ErrorCode', '', parsed); prev = role + '_parsed'
        s[role + '_ids'] = {'type': 'Select', 'inputs': {'from': "@body('" + parsed + "')", 'select': "@item()?['Id']"}, 'runAfter': after(prev)}
        s[role + '_unique'] = gate(role + '_unique', "equals(length(body('" + role + "_ids')),length(union(body('" + role + "_ids'),body('" + role + "_ids'))))", 'DATA_INTEGRITY', role + '_ids'); prev = role + '_unique'
    for role, field in [('requests', 'SendOperationKey'), ('requests', 'ConnectionKey'), ('groups', 'SourceRequestId')]:
        q = role + '_unique_' + field
        s[q] = {'type': 'Select', 'inputs': {'from': "@body('Data_" + role + "')", 'select': "@item()?['" + field + "']"}, 'runAfter': after(prev)}
        s[q + '_gate'] = gate(q + '_gate', "equals(length(body('" + q + "')),length(union(body('" + q + "'),body('" + q + "'))))", 'DATA_INTEGRITY', q)
        prev = q + '_gate'
    s['Actor_profile'] = query("@body('Data_profiles')", "equals(item()?['Id'],outputs('Actor'))", prev)
    s['Actor_exists'] = gate('Actor_exists', "equals(length(body('Actor_profile')),1)", 'DATA_INTEGRITY', 'Actor_profile')
    # Validate modern request intents/terminal keys; legacy incomplete rows return explicit failure, never rewritten.
    r = "items('Validate_requests')"
    personal = f"and(equals({r}?['RequestType'],'Personal'),not(equals({r}?['RecipientParticipantId'],null)),equals({r}?['TargetGroupId'],null),not(equals({r}?['SenderParticipantId'],{r}?['RecipientParticipantId'])))"
    group = f"and(equals({r}?['RequestType'],'Group'),equals({r}?['RecipientParticipantId'],null),not(equals({r}?['TargetGroupId'],null)))"
    # Null-safe sort operands support eager expression evaluation.
    sender = r + "?['SenderParticipantId']"; recipient = "coalesce(" + r + "?['RecipientParticipantId'],0)"
    live = "if(equals(" + r + "?['RequestType'],'Personal'),concat('open:person:',string(if(less(" + sender + ',' + recipient + '),' + sender + ',' + recipient + ")),':',string(if(less(" + sender + ',' + recipient + '),' + recipient + ',' + sender + "))),concat('open:group:',string(" + r + "?['TargetGroupId']),':participant:',string(" + sender + ')))'
    pending = f"equals({r}?['Status'],'Pending')"
    unsettled = f"or({pending},and(equals({r}?['Status'],'Accepted'),equals({r}?['OperationComplete'],false)))"
    valid = f"and(or({personal},{group}),not(empty(trim({r}?['SendOperationKey']))),equals({r}?['ConnectionKey'],if({unsettled},{live},concat('history:request:',string({r}?['Id'])))),if({pending},and(equals({r}?['OperationComplete'],false),empty({r}?['WinningOperationKey'])),and(not(empty(trim(coalesce({r}?['WinningOperationKey'],'')))),or(equals({r}?['Status'],'Accepted'),equals({r}?['OperationComplete'],true)))))"
    s['Validate_requests'] = loop("@body('Data_requests')", {'Request_integrity': gate('Request_integrity', valid, 'REQUEST_DATA_INCOMPLETE')}, 'Actor_exists')
    # Source and episode authority includes exact party/group binding; Left/provisional never grant authority.
    m = "items('Each_own_episode')"; g = first('Episode_group'); e = "item()"
    personalparty = f"and(equals({e}?['RequestType'],'Personal'),equals({e}?['Id'],{g}?['SourceRequestId']),or(equals({e}?['SenderParticipantId'],outputs('Actor')),equals({e}?['RecipientParticipantId'],outputs('Actor'))))"
    groupparty = f"and(equals({e}?['RequestType'],'Group'),equals({e}?['TargetGroupId'],{m}?['GroupId']),equals({e}?['SenderParticipantId'],outputs('Actor')))"
    inner = {'Episode_group': query("@body('Data_groups')", f"equals(item()?['Id'],{m}?['GroupId'])"),
             'Episode_source': query("@body('Data_requests')", f"and(equals(item()?['Id'],{g}?['SourceRequestId']),equals(item()?['RequestType'],'Personal'),equals(item()?['Status'],'Accepted'),equals(item()?['OperationComplete'],true))", 'Episode_group'),
             'Episode_commit': query("@body('Data_requests')", f"and(equals({m}?['MembershipKey'],concat('request:',string(item()?['Id']),':participant:',string(outputs('Actor')))),equals(item()?['Status'],'Accepted'),equals(item()?['OperationComplete'],true),or({personalparty},{groupparty}))", 'Episode_source'),
             'Episode_duplicates': query("@body('Data_memberships')", f"and(equals(item()?['GroupId'],{m}?['GroupId']),equals(item()?['ParticipantId'],outputs('Actor')),equals(item()?['MembershipStatus'],'Active'))", 'Episode_commit')}
    inner['Episode_unique'] = gate('Episode_unique', "equals(length(body('Episode_duplicates')),1)", 'MEMBERSHIP_INTEGRITY', 'Episode_duplicates')
    inner['Episode_operational'] = branch(f"and(equals(length(body('Episode_group')),1),equals({g}?['SetupComplete'],true),not(equals({g}?['State'],'Ended')),empty({m}?['LeftAt']),equals(length(body('Episode_source')),1),equals(length(body('Episode_commit')),1))",
                                         {'Remember_operational_group': append('OperationalGroups', '@' + m + "?['GroupId']")}, n='Episode_unique')
    s['Own_active_episodes'] = query("@body('Data_memberships')", "and(equals(item()?['ParticipantId'],outputs('Actor')),equals(item()?['MembershipStatus'],'Active'))", 'Validate_requests')
    s['Each_own_episode'] = loop("@body('Own_active_episodes')", inner, 'Own_active_episodes')
    audience = "or(equals(item()?['SenderParticipantId'],outputs('Actor')),and(equals(item()?['RequestType'],'Personal'),equals(item()?['RecipientParticipantId'],outputs('Actor'))),and(equals(item()?['RequestType'],'Group'),contains(variables('OperationalGroups'),item()?['TargetGroupId'])))"
    s['Audience_requests'] = query("@body('Data_requests')", audience, 'Each_own_episode')
    r = "items('Each_visible_request')"
    own = f"equals({r}?['SenderParticipantId'],outputs('Actor'))"
    pending = f"equals({r}?['Status'],'Pending')"
    def available(p): return f"and(equals({p}?['Status'],'Active'),equals({p}?['ParticipationStatus'],'Active'),equals({p}?['OpenToConnections'],true))"
    visible = {
        'Request_sender': query("@body('Data_profiles')", f"equals(item()?['Id'],{r}?['SenderParticipantId'])"),
        'Request_recipient': query("@body('Data_profiles')", f"equals(item()?['Id'],{r}?['RecipientParticipantId'])", 'Request_sender'),
        'Request_group': query("@body('Data_groups')", f"equals(item()?['Id'],{r}?['TargetGroupId'])", 'Request_recipient'),
        'Request_active_members': query("@body('Data_memberships')", f"and(equals(item()?['GroupId'],{r}?['TargetGroupId']),equals(item()?['MembershipStatus'],'Active'))", 'Request_group'),
    }
    gp = first('Request_group')
    groupavail = f"and(equals(length(body('Request_group')),1),equals({gp}?['SetupComplete'],true),equals({gp}?['State'],'Open'),empty({gp}?['WriteOwner']),less(length(body('Request_active_members')),coalesce({gp}?['Capacity'],0)))"
    visible['Request_available'] = compose('@and(' + available(first('Request_sender')) + ",if(equals(" + r + "?['RequestType'],'Personal'),and(equals(length(body('Request_recipient')),1)," + available(first('Request_recipient')) + '),' + groupavail + '))', 'Request_active_members')
    visible['Visible_parties_exist'] = gate('Visible_parties_exist', f"and(equals(length(body('Request_sender')),1),if(equals({r}?['RequestType'],'Personal'),equals(length(body('Request_recipient')),1),equals(length(body('Request_group')),1)))", 'REQUEST_DATA_INCOMPLETE', 'Request_available')
    canrespond = f"and(not({own}),or(and(equals({r}?['RequestType'],'Personal'),equals({r}?['RecipientParticipantId'],outputs('Actor'))),and(equals({r}?['RequestType'],'Group'),contains(variables('OperationalGroups'),{r}?['TargetGroupId']))))"
    visible['Append_public_request'] = append('Requests', {
        'requestId': '@' + r + "?['Id']", 'senderParticipantId': '@' + r + "?['SenderParticipantId']", 'recipientParticipantId': '@' + r + "?['RecipientParticipantId']",
        'targetGroupId': '@' + r + "?['TargetGroupId']", 'requestType': '@' + r + "?['RequestType']", 'status': '@' + r + "?['Status']",
        'direction': '@if(' + own + ",'Sent','Received')",
        'processing': f"@and(equals({r}?['Status'],'Accepted'),equals({r}?['OperationComplete'],false))",
        'completed': '@' + r + "?['OperationComplete']",
        'availability': f"@if({pending},if(outputs('Request_available'),'Available','UnavailablePending'),'NotApplicable')",
        'actions': {'cancel': '@and(' + own + ',' + pending + ')', 'decline': '@and(' + canrespond + ',' + pending + ')',
                    'accept': '@and(' + canrespond + ',' + pending + ",outputs('Request_available')," + available(first('Actor_profile')) + ')'},
    }, 'Visible_parties_exist')
    s['Each_visible_request'] = loop("@body('Audience_requests')", visible, 'Audience_requests')
    s['Response_bound'] = gate('Response_bound', "lessOrEquals(length(string(variables('Requests'))),250000)", 'RESPONSE_BOUND', 'Each_visible_request')
    a['Read_authorized_requests'] = {'type': 'Scope', 'actions': s, 'runAfter': after('Initialize_OperationalGroups')}
    a['Read_failure'] = {'type': 'Scope', 'runAfter': {'Read_authorized_requests': ['Failed', 'TimedOut']}, 'actions': {
        'Failure_code': branch("empty(variables('ErrorCode'))", {'Set_generic_failure': setvar('ErrorCode', 'READ_OR_DATA_FAILED')}),
        'Clear_partial_results': setvar('Requests', [], 'Failure_code')}}
    fields = ['requestsjson', 'errormessage', 'resultcode', 'runreference', 'mode', 'paging']
    a['Respond_to_a_Power_App_or_flow'] = {'type': 'Response', 'kind': 'PowerApp', 'runAfter': {'Read_failure': ['Succeeded', 'Skipped']}, 'inputs': {
        'statusCode': 200, 'schema': {'type': 'object', 'properties': {k: {'title': k, 'type': 'string', 'x-ms-content-hint': 'TEXT', 'x-ms-dynamically-added': True} for k in fields}},
        'body': {'requestsjson': "@if(empty(variables('ErrorCode')),string(variables('Requests')),'[]')",
                 'errormessage': "@if(empty(variables('ErrorCode')),'','Requests could not be read completely. Refresh or return the result code for review.')",
                 'resultcode': "@if(empty(variables('ErrorCode')),'OK',variables('ErrorCode'))", 'runreference': "@workflow()?['run']?['name']",
                 'mode': 'OWNER_PREVIEW_PENDING_ACCESS_PROOF', 'paging': 'NO_PAGING_COMPLETE_BOUNDED_READ'}}}
    measure(a)
    return a


def build_package(source, output):
    source, output = Path(source), Path(output)
    if any(p.exists() for p in [output, output.with_suffix('.definition.json'), output.with_suffix('.review.json')]): raise FileExistsError(output)
    original = read_source(source); site, _ = source_metadata(original)
    people = json.loads((ROOT / 'config/tenant_schema_mapping.json').read_text(encoding='utf-8'))
    groups = json.loads((ROOT / 'config/group_schema_mapping.json').read_text(encoding='utf-8'))
    build_id = str(uuid4()); actions = build_actions(original, people, groups, build_id)
    with TemporaryDirectory() as temp:
        p = Path(temp) / 'envelope.zip'; envelope(p, sharepoint_site=site)
        with ZipFile(p) as z: entries = {n: json.loads(z.read(n)) for n in z.namelist()}
    document = next(v for n, v in entries.items() if n.endswith('/definition.json'))
    document['properties']['displayName'] = NAME
    document['properties']['definition']['actions'] = actions
    document['properties']['definition']['triggers'] = deepcopy(original['properties']['definition']['triggers'])
    selected_connection = document['properties']['connectionReferences']['shared_sharepointonline']['connectionName']
    document['properties']['connectionReferences']['shared_sharepointonline'] = deepcopy(original['properties']['connectionReferences']['shared_sharepointonline'])
    document['properties']['connectionReferences']['shared_sharepointonline']['connectionName'] = selected_connection
    entries['manifest.json']['details'].update(displayName=NAME + '-package', description='Issue 62 owner-preview read-only reader; Create as new; requires runtime schema verification.')
    for r in entries['manifest.json']['resources'].values():
        if r['type'] == 'Microsoft.Flow/flows': r['details']['displayName'] = NAME
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, 'x', ZIP_DEFLATED) as z:
        for name, value in entries.items(): z.writestr(name, json.dumps(value, indent=2) + '\n')
    review = {'sourceTicket': 62, 'packageBuildId': build_id, **measure(actions), 'bounds': BOUNDS, 'writes': 0,
              'connectionSource': 'Invoker', 'rawAuthenticationPreserved': True, 'sourceTriggerPreserved': True,
              'ownerCredentialFallback': False, 'paging': 'NO_PAGING_COMPLETE_BOUNDED_READ',
              'sourceExportSha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'sourceExportName': source.name,
              'sourcePublicShape': list(original['properties']['definition']['actions']['Request_rows']['inputs']['select']),
              'sourceShapeChange': 'Retain requestId/senderParticipantId/recipientParticipantId/status/direction; omit system created; add group/type/completion/availability/actions.',
              'packageSha256': hashlib.sha256(output.read_bytes()).hexdigest(), 'generatorSha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'tenantResult': 'NOT_IMPORTED_NOT_TESTED', 'ordinaryUserAccessVerified': False, 'requestSchema': 'PROPOSED_RUNTIME_FAIL_CLOSED',
              'limits': {'actions': 500, 'maximumActionDepth': 8}, 'globalActionNamesUnique': True}
    output.with_suffix('.definition.json').write_bytes((json.dumps(document, indent=2) + '\n').encode('utf-8'))
    output.with_suffix('.review.json').write_bytes((json.dumps(review, indent=2) + '\n').encode('utf-8'))
    return review


def main():
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('--source', type=Path, required=True); p.add_argument('--output', type=Path, required=True)
    args = p.parse_args(); print(json.dumps(build_package(args.source, args.output), indent=2))


if __name__ == '__main__': main()
