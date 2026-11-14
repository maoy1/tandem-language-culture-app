"""Build #62 read-only TandemMyRequests; Python is local build/test tooling only."""
from copy import deepcopy
import argparse
import hashlib
import json
import re
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4
from zipfile import ZipFile, ZIP_DEFLATED
from .build_import_probe import build_package as envelope
from .schema_audit import measure

ROOT = Path(__file__).resolve().parents[2]
NAME = 'TandemMyRequests v7'
SHARED = json.loads((ROOT / 'config/shared_validation_flow_contract.json').read_text())
NATIVE_EVIDENCE = json.loads((ROOT / 'artifacts/shared_validation/results/native-sharepoint-solution.analysis.json').read_text())
CHILD_ID = NATIVE_EVIDENCE['sharedChildId']
NATIVE_SHARED_BUILD = NATIVE_EVIDENCE['sharedBuildId']
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
    contracts = {
        'requests': {
            'SenderParticipantId': field('Number', True, Decimals='0'),
            'RecipientParticipantId': field('Number', False, Decimals='0'),
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
    # Extra indexes do not change request semantics; retain positive key requirements.
    for expected in contracts['requests'].values():
        if expected.get('Indexed') is False:
            del expected['Indexed']
        expected.update(Hidden=False, ReadOnlyField=False)
    return contracts


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


def introduction_option(introduction_verified=False, include_introduction=None):
    """Select target fields only; neither spelling certifies tenant setup.

    introduction_verified is a compatibility alias for existing batch callers.
    Compile planned target packages before setup, but do not run them until the
    actual Introduction field/settings are applied and read back successfully.
    """
    if type(introduction_verified) is not bool or (include_introduction is not None and type(include_introduction) is not bool):
        raise ValueError('Introduction inclusion must be boolean')
    if introduction_verified and include_introduction is False:
        raise ValueError('Conflicting Introduction inclusion options')
    return introduction_verified if include_introduction is None else include_introduction


def shared_build_option(expected_shared_build_id=None):
    """Exact runtime expectation supplied by canonical config or explicit manifest.

    Reusing a native connection seed is not proof that a newer engine is tested.
    There is no wildcard/version-only fallback and no runtime build discovery.
    """
    value = SHARED['packageBuildId'] if expected_shared_build_id is None else expected_shared_build_id
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,128}', value):
        raise ValueError('Expected explicit safe shared build identifier')
    return value


def build_actions(original, people, groups, build_id, introduction_verified=False, *, include_introduction=None, expected_shared_build_id=None):
    include_introduction = introduction_option(introduction_verified, include_introduction)
    expected_shared_build_id = shared_build_option(expected_shared_build_id)
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
    # URI is constructed only from server-validated numeric identity.
    ownuri = "@concat('" + base('profiles').replace("'", "''") + "/items?$select=Id&$filter=ParticipantaccountId eq ',string(body('Invoker')?['Id']),'&$top=2')"
    s['Read_own'] = http(ownuri, 'Invoker')
    s['Own_complete'] = gate('Own_complete', complete('Read_own', 1), 'UNAUTHORIZED_PROFILE', 'Read_own')
    s['Own_match'] = gate('Own_match', "and(equals(length(" + rows('Read_own') + "),1),equals(first(union(" + rows('Read_own') + ",createArray(json('{}'))))?['Id'],triggerBody()?['number']))", 'UNAUTHORIZED_PROFILE', 'Own_complete')
    s['Actor'] = compose("@triggerBody()?['number']", 'Own_match'); prev = 'Actor'
    selects = {
        'requests': 'Id,Created,SenderParticipantId,RecipientParticipantId,TargetGroupId,RequestType,Status,SendOperationKey,ConnectionKey,WinningOperationKey,OperationComplete',
        'profiles': 'Id,Status,ParticipationStatus,OpenToConnections',
        'groups': 'Id,SourceRequestId,SetupComplete,State,Capacity,WriteOwner',
        'memberships': 'Id,GroupId,ParticipantId,MembershipStatus,MembershipKey,LeftAt',
    }
    if include_introduction:
        selects['requests'] += ',Introduction'
    schemas = {
        'requests': obj({'Id': integer(), 'Created': text(), 'SenderParticipantId': {'type': 'number', 'minimum': 1}, 'RecipientParticipantId': {'type': ['number', 'null'], 'minimum': 1}, 'TargetGroupId': integer(True),
                         'RequestType': choice('Personal', 'Group'), 'Status': choice('Pending', 'Accepted', 'Declined', 'Cancelled'),
                         'SendOperationKey': text(), 'ConnectionKey': text(), 'WinningOperationKey': {'type': ['string', 'null']}, 'OperationComplete': {'type': 'boolean'}}),
        'profiles': obj({'Id': integer(), 'Status': {'type': ['string', 'null']}, 'ParticipationStatus': {'type': ['string', 'null'], 'enum': ['Active', 'Paused', 'Inactive', None]}, 'OpenToConnections': {'type': ['boolean', 'null']}}),
        'groups': obj({'Id': integer(), 'SourceRequestId': integer(), 'SetupComplete': {'type': 'boolean'}, 'State': choice('Open', 'Closed', 'Ended'), 'Capacity': {'type': 'integer', 'minimum': 2, 'maximum': 10}, 'WriteOwner': {'type': ['string', 'null']}}),
        'memberships': obj({'Id': integer(), 'GroupId': integer(), 'ParticipantId': integer(), 'MembershipStatus': choice('Active', 'Left'), 'MembershipKey': text(), 'LeftAt': {'type': ['string', 'null']}}),
    }
    if include_introduction:
        schemas['requests']['properties']['Introduction'] = {'type': ['string', 'null'], 'maxLength': 2000}
    for role in selects:
        read = 'Read_' + role; bound = role + '_complete'; parsed = 'Raw_requests' if role == 'requests' else 'Data_' + role
        order = 'Created desc,ID desc' if role == 'requests' else 'Id asc'
        s[read] = http(base(role) + '/items?$select=' + selects[role] + '&$orderby=' + order + '&$top=' + str(BOUNDS[role] + 1), prev)
        s[bound] = gate(bound, complete(read, BOUNDS[role]), 'READ_BOUND_OR_INCOMPLETE', read)
        code = 'REQUEST_DATA_INCOMPLETE' if role == 'requests' else 'DATA_INTEGRITY'
        s[role + '_parse_code'] = setvar('ErrorCode', code, bound)
        s[parsed] = parse('@' + rows(read), {'type': 'array', 'items': schemas[role]}, role + '_parse_code')
        parsed_end = parsed
        if role == 'requests':
            reference = "items('Validate_number_references')"
            sender = reference + "?['SenderParticipantId']"
            recipient = "coalesce(" + reference + "?['RecipientParticipantId'],0)"
            s['Validate_number_references'] = loop("@body('Raw_requests')", {
                'Whole_number_references': gate('Whole_number_references', 'and(equals(' + sender + ',int(' + sender + ')),equals(' + recipient + ',int(' + recipient + ')))', 'REQUEST_DATA_INCOMPLETE')}, parsed)
            projection = {key: "@item()?['" + key + "']" for key in schemas[role]['properties']}
            projection['SenderParticipantId'] = "@int(item()?['SenderParticipantId'])"
            projection['RecipientParticipantId'] = "@if(equals(item()?['RecipientParticipantId'],null),null,int(coalesce(item()?['RecipientParticipantId'],0)))"
            s['Data_requests'] = {'type': 'Select', 'inputs': {'from': "@body('Raw_requests')", 'select': projection}, 'runAfter': after('Validate_number_references')}
            parsed_end = 'Data_requests'
        s[role + '_parsed'] = setvar('ErrorCode', '', parsed_end); prev = role + '_parsed'
        s[role + '_ids'] = {'type': 'Select', 'inputs': {'from': "@body('" + parsed + "')", 'select': "@item()?['Id']"}, 'runAfter': after(prev)}
        s[role + '_unique'] = gate(role + '_unique', "equals(length(body('" + role + "_ids')),length(union(body('" + role + "_ids'),body('" + role + "_ids'))))", 'DATA_INTEGRITY', role + '_ids'); prev = role + '_unique'
    for role, field in [('requests', 'SendOperationKey'), ('requests', 'ConnectionKey'), ('groups', 'SourceRequestId')]:
        q = role + '_unique_' + field
        s[q] = {'type': 'Select', 'inputs': {'from': "@body('Data_" + role + "')", 'select': "@item()?['" + field + "']"}, 'runAfter': after(prev)}
        s[q + '_gate'] = gate(q + '_gate', "equals(length(body('" + q + "')),length(union(body('" + q + "'),body('" + q + "'))))", 'DATA_INTEGRITY', q)
        prev = q + '_gate'
    # Reader-only availability adapter: row IDs are internal correlation keys,
    # not account authentication. No role/catalogue data or compatibility claim.
    s['Normalization_profiles'] = {'type': 'Select', 'runAfter': after(prev), 'inputs': {
        'from': "@body('Data_profiles')", 'select': {
            'profileId': "@item()?['Id']", 'accountKey': "@concat('participant:',string(item()?['Id']))",
            'status': "@item()?['Status']", 'participationStatus': "@item()?['ParticipationStatus']",
            'openToConnections': "@item()?['OpenToConnections']"}}}
    s['Normalization_envelope'] = compose({'contractVersion': 1, 'rulesVersion': 1, 'mode': 'NORMALIZE',
        'profiles': "@body('Normalization_profiles')", 'catalogues': {
            'languageIds': [], 'cultureIds': [], 'timezoneIds': [], 'anyLanguageId': None}}, 'Normalization_profiles')
    s['Child_stage'] = setvar('ErrorCode', 'SHARED_VALIDATION_FAILED', 'Normalization_envelope')
    s['Call_normalization'] = {'type': 'Workflow', 'runAfter': after('Child_stage'), 'inputs': {
        'host': {'workflowReferenceName': CHILD_ID}, 'body': {'text': "@string(outputs('Normalization_envelope'))"}}}
    s['Normalization_report'] = parse("@json(body('Call_normalization')?['resultjson'])", {'type': 'object'}, 'Call_normalization')
    report = "body('Normalization_report')"
    valid = f"and(equals({report}?['kind'],'TandemValidateContext'),equals({report}?['contractVersion'],1),equals({report}?['rulesVersion'],1),equals({report}?['packageBuildId'],'{expected_shared_build_id}'),equals({report}?['success'],true),equals({report}?['code'],'OK'),equals({report}?['authorizesAction'],false),equals({report}?['connectors'],0),equals({report}?['reads'],0),equals({report}?['writes'],0))"
    s['Normalization_verified'] = gate('Normalization_verified', valid, 'SHARED_VALIDATION_FAILED', 'Normalization_report')
    s['Normalized_profiles'] = parse("@body('Normalization_report')?['result']?['profiles']", {'type': 'array', 'maxItems': BOUNDS['profiles'], 'items': obj({
        'profileId': integer(), 'status': {'type': ['string', 'null']},
        'participationStatus': {'type': ['string', 'null'], 'enum': ['Active', 'Paused', 'Inactive', None]},
        'openToConnections': {'type': ['boolean', 'null']}})}, 'Normalization_verified')
    s['Normalized_ids'] = {'type': 'Select', 'inputs': {'from': "@body('Normalized_profiles')", 'select': "@item()?['profileId']"}, 'runAfter': after('Normalized_profiles')}
    s['Normalization_complete'] = gate('Normalization_complete', "and(equals(length(union(body('Normalized_ids'),body('Normalized_ids'))),length(body('profiles_ids'))),equals(length(body('Normalized_ids')),length(body('profiles_ids'))),equals(length(union(body('Normalized_ids'),body('profiles_ids'))),length(body('profiles_ids'))))", 'SHARED_VALIDATION_FAILED', 'Normalized_ids')
    s['Normalization_finished'] = setvar('ErrorCode', '', 'Normalization_complete')
    prev = 'Normalization_finished'
    s['Actor_profile'] = query("@body('Normalized_profiles')", "equals(item()?['profileId'],outputs('Actor'))", prev)
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
    if include_introduction:
        valid = f"and({valid},lessOrEquals(length(coalesce({r}?['Introduction'],'')),2000))"
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
    def available(p): return f"and(equals({p}?['status'],'Active'),equals({p}?['participationStatus'],'Active'),equals({p}?['openToConnections'],true))"
    visible = {
        'Request_sender': query("@body('Normalized_profiles')", f"equals(item()?['profileId'],{r}?['SenderParticipantId'])"),
        'Request_recipient': query("@body('Normalized_profiles')", f"equals(item()?['profileId'],{r}?['RecipientParticipantId'])", 'Request_sender'),
        'Request_group': query("@body('Data_groups')", f"equals(item()?['Id'],{r}?['TargetGroupId'])", 'Request_recipient'),
        'Request_active_members': query("@body('Data_memberships')", f"and(equals(item()?['GroupId'],{r}?['TargetGroupId']),equals(item()?['MembershipStatus'],'Active'))", 'Request_group'),
    }
    gp = first('Request_group')
    groupavail = f"and(equals(length(body('Request_group')),1),equals({gp}?['SetupComplete'],true),equals({gp}?['State'],'Open'),empty({gp}?['WriteOwner']),less(length(body('Request_active_members')),coalesce({gp}?['Capacity'],0)))"
    visible['Request_available'] = compose('@and(' + available(first('Request_sender')) + ",if(equals(" + r + "?['RequestType'],'Personal'),and(equals(length(body('Request_recipient')),1)," + available(first('Request_recipient')) + '),' + groupavail + '))', 'Request_active_members')
    visible['Visible_parties_exist'] = gate('Visible_parties_exist', f"and(equals(length(body('Request_sender')),1),if(equals({r}?['RequestType'],'Personal'),equals(length(body('Request_recipient')),1),equals(length(body('Request_group')),1)))", 'REQUEST_DATA_INCOMPLETE', 'Request_available')
    canrespond = f"and(not({own}),or(and(equals({r}?['RequestType'],'Personal'),equals({r}?['RecipientParticipantId'],outputs('Actor'))),and(equals({r}?['RequestType'],'Group'),contains(variables('OperationalGroups'),{r}?['TargetGroupId']))))"
    visible['Append_public_request'] = append('Requests', {
        'requestId': '@' + r + "?['Id']", 'created': '@' + r + "?['Created']", 'senderParticipantId': '@' + r + "?['SenderParticipantId']", 'recipientParticipantId': '@' + r + "?['RecipientParticipantId']",
        'targetGroupId': '@' + r + "?['TargetGroupId']", 'requestType': '@' + r + "?['RequestType']", 'status': '@' + r + "?['Status']",
        'direction': '@if(' + own + ",'Sent','Received')",
        'processing': f"@and(equals({r}?['Status'],'Accepted'),equals({r}?['OperationComplete'],false))",
        'completed': '@' + r + "?['OperationComplete']",
        'availability': f"@if({pending},if(outputs('Request_available'),'Available','UnavailablePending'),'NotApplicable')",
        'actions': {'cancel': '@and(' + own + ',' + pending + ')', 'decline': '@and(' + canrespond + ',' + pending + ')',
                    'accept': '@and(' + canrespond + ',' + pending + ",outputs('Request_available')," + f"if(equals({r}?['RequestType'],'Group'),true," + available(first('Actor_profile')) + '))'},
    }, 'Visible_parties_exist')
    if include_introduction:
        visible['Append_public_request']['inputs']['value']['introduction'] = f"@if(equals({r}?['RequestType'],'Group'),coalesce({r}?['Introduction'],''),'')"
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


def build_package(source, output, introduction_verified=False, *, include_introduction=None, expected_shared_build_id=None):
    include_introduction = introduction_option(introduction_verified, include_introduction)
    expected_shared_build_id = shared_build_option(expected_shared_build_id)
    source, output = Path(source), Path(output)
    if any(p.exists() for p in [output, output.with_suffix('.definition.json'), output.with_suffix('.review.json')]): raise FileExistsError(output)
    original = read_source(source); site, _ = source_metadata(original)
    people = json.loads((ROOT / 'config/tenant_schema_mapping.json').read_text(encoding='utf-8'))
    groups = json.loads((ROOT / 'config/group_schema_mapping.json').read_text(encoding='utf-8'))
    build_id = str(uuid4()); actions = build_actions(original, people, groups, build_id, include_introduction=include_introduction, expected_shared_build_id=expected_shared_build_id)
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
    entries['manifest.json']['details'].update(displayName=NAME + '-package', description='Issue 62 owner-preview read-only reader; Create as new; requires existing shared child; native Solution consumer parity unproven.')
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
              'sourceShapeChange': 'Retain every original Request_rows field including created and Created desc, ID desc ordering; add group/type/completion/availability/actions. Full UI binding pending.',
              'packageSha256': hashlib.sha256(output.read_bytes()).hexdigest(), 'generatorSha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'tenantResult': 'NOT_IMPORTED_NOT_TESTED', 'ordinaryUserAccessVerified': False, 'requestSchema': 'MAINTENANCE_81_NO_PER_CLICK_AUDIT', 'sharedChildId': CHILD_ID, 'sharedBuildId': expected_shared_build_id, 'sharedBuildPinPolicy': 'EXACT_CANONICAL_OR_EXPLICIT_MANIFEST_BUILD_NO_FALLBACK', 'nativeSeedSharedBuildId': NATIVE_SHARED_BUILD, 'includeIntroduction': include_introduction, 'introductionVerified': False, 'introductionSetupStatus': 'NOT_APPLIED_NOT_VERIFIED', 'introductionParameterNote': 'Both include_introduction and legacy introduction_verified select planned target fields only; no tenant verification claim', 'nativeSolutionConsumerParity': 'NOT_RUN', 'legacyWorkflowDependencyImport': 'UNPROVEN_USE_REVIEWABLE_SOLUTION_PARENT',
              'referenceAdapter': 'SenderParticipantId/RecipientParticipantId Number with XML Decimals=0; whole-valued numeric refs normalized to int before canonical keys/public IDs.',
              'limits': {'actions': 500, 'maximumActionDepth': 8}, 'globalActionNamesUnique': True}
    output.with_suffix('.definition.json').write_bytes((json.dumps(document, indent=2) + '\n').encode('utf-8'))
    output.with_suffix('.review.json').write_bytes((json.dumps(review, indent=2) + '\n').encode('utf-8'))
    return review


def build_parent(source, solution_source, output, introduction_verified=False, *, include_introduction=None, expected_shared_build_id=None):
    """Readable #62 Solution parent only; enclosing Solution packaging belongs to parent integration.

    A legacy ZIP cannot establish the external Workflow dependency or native
    Power Apps Solution parity. Do not hand it over as an importable replacement.
    """
    from .solution_source import inspect_caller_export, invoker_parent_document, walk
    include_introduction = introduction_option(introduction_verified, include_introduction)
    expected_shared_build_id = shared_build_option(expected_shared_build_id)
    output = Path(output)
    review_path = output.with_suffix('.review.json')
    if output.exists() or review_path.exists(): raise FileExistsError(output)
    original = read_source(source); site, _ = source_metadata(original)
    seed = inspect_caller_export(solution_source, site, NATIVE_SHARED_BUILD)
    people = json.loads((ROOT / 'config/tenant_schema_mapping.json').read_text())
    groups = json.loads((ROOT / 'config/group_schema_mapping.json').read_text())
    build_id = str(uuid4())
    actions = build_actions(original, people, groups, build_id, include_introduction=include_introduction, expected_shared_build_id=expected_shared_build_id)
    document = invoker_parent_document(seed, original['properties']['definition']['triggers'], actions)
    document['properties']['displayName'] = NAME
    # Seed is a probe template; new workflow identity/root is assigned by the
    # integrating Solution packager, never overwrite the probe or working flow.
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(document, indent=2)+'\n', encoding='utf-8', newline='\n')
    review = {'sourceTicket': 62, 'packageBuildId': build_id, **measure(actions),
        'writes': 0, 'connectorReadDefinitions': sum(a['type']=='OpenApiConnection' for _, a in walk(actions)),
        'sharedChildId': CHILD_ID, 'sharedBuildId': expected_shared_build_id, 'sharedBuildPinPolicy': 'EXACT_CANONICAL_OR_EXPLICIT_MANIFEST_BUILD_NO_FALLBACK', 'nativeSeedSharedBuildId': NATIVE_SHARED_BUILD,
        'sharedMode': 'NORMALIZE', 'schemaAuditPerClick': False,
        'runtimeSource': 'invoker', 'sourceTriggerPreserved': True,
        'sourceExportSha256': hashlib.sha256(Path(source).read_bytes()).hexdigest(),
        'solutionSeedSha256': seed['receipt']['sourceExportSha256'],
        'generatorSha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'definitionSha256': hashlib.sha256(output.read_bytes()).hexdigest(),
        'sharedImplementationSha256': hashlib.sha256((ROOT/'scripts/power_automate/shared_validation.py').read_bytes()).hexdigest(),
        'sharedContractVersion': 1, 'sharedRulesVersion': 1,
        'includeIntroduction': include_introduction, 'introductionVerified': False, 'introductionSetupStatus': 'NOT_APPLIED_NOT_VERIFIED', 'introductionParameterNote': 'Both include_introduction and legacy introduction_verified select planned target fields only; no tenant verification claim', 'bounds': BOUNDS,
        'nativeStatus': 'NOT_IMPORTED_NOT_TESTED', 'ordinaryUserAccessVerified': False,
        'packaging': 'READABLE_SOLUTION_PARENT; parent integration assigns new workflow ID/root and packages existing child dependency; no legacy ZIP delivered',
        'nativeEvidence': 'v6 empty-history PASS retained separately; #81 child QUICK3/FULL44 and inspected Invoker envelope do not certify this parent',
        'limits': {'actions': 500, 'maximumActionDepth': 8}}
    review_path.write_text(json.dumps(review, indent=2)+'\n', encoding='utf-8', newline='\n')
    return review


def main():
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('--source', type=Path, required=True); p.add_argument('--output', type=Path, required=True)
    p.add_argument('--solution-source', type=Path, help='Inspected native #81 unmanaged source; emits readable parent instead of legacy ZIP')
    p.add_argument('--expected-shared-build-id', help='Exact runtime build from explicit canonical batch manifest; no wildcard or auto-detection')
    p.add_argument('--include-introduction', action='store_true', default=None, help='Compile planned target field; actual setup/readback required BEFORE tenant use, no verification claim')
    p.add_argument('--introduction-verified', action='store_true', help='Compatibility alias for target inclusion only; does NOT certify actual schema')
    args = p.parse_args()
    report = build_parent(args.source, args.solution_source, args.output, args.introduction_verified, include_introduction=args.include_introduction, expected_shared_build_id=args.expected_shared_build_id) if args.solution_source else build_package(args.source, args.output, args.introduction_verified, include_introduction=args.include_introduction, expected_shared_build_id=args.expected_shared_build_id)
    print(json.dumps(report, indent=2))


if __name__ == '__main__': main()
