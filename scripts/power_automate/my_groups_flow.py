"""#64 read-only My Groups parent; Python is local generation/test tooling only.

The reader deliberately projects historical/current display facts without an
eligibility/normalization child. #81 owns explicit maintenance schema audits.
"""
from copy import deepcopy
import argparse
import hashlib
import json
from pathlib import Path
from uuid import uuid4

from .schema_audit import measure
from .solution_source import inspect_caller_export, invoker_parent_document, RAW_INVOKER, walk

ROOT = Path(__file__).resolve().parents[2]
NAME = 'TandemMyGroups v2'
REQUESTS = '3d17485d-1dac-41f0-a1af-24e45daa4567'
BOUNDS = {'requests': 500, 'groups': 100, 'memberships': 2000, 'profiles': 500,
          'language': 5000, 'culture': 5000, 'timezone': 5000, 'responseChars': 250000}

# Small emitted-action constructors adapted from #62 b9d6516; no import or
# stacked-branch dependency on that business reader or its operation rules.
def after(n): return {n: ['Succeeded']} if n else {}
def compose(v, n=None): return {'type': 'Compose', 'inputs': v, 'runAfter': after(n)}
def query(src, pred, n=None): return {'type': 'Query', 'inputs': {'from': src, 'where': '@' + pred}, 'runAfter': after(n)}
def select(src, projection, n=None): return {'type': 'Select', 'inputs': {'from': src, 'select': projection}, 'runAfter': after(n)}
def parse(src, schema, n=None): return {'type': 'ParseJson', 'inputs': {'content': src, 'schema': schema}, 'runAfter': after(n)}
def setvar(k, v, n=None): return {'type': 'SetVariable', 'inputs': {'name': k, 'value': v}, 'runAfter': after(n)}
def append(k, v, n=None): return {'type': 'AppendToArrayVariable', 'inputs': {'name': k, 'value': v}, 'runAfter': after(n)}
def loop(src, actions, n=None): return {'type': 'Foreach', 'foreach': src, 'actions': actions, 'runtimeConfiguration': {'concurrency': {'repetitions': 1}}, 'runAfter': after(n)}
def branch(pred, yes, no=None, n=None): return {'type': 'If', 'expression': '@' + pred, 'actions': yes, 'else': {'actions': no or {}}, 'runAfter': after(n)}
def rows(n): return "body('" + n + "')?['d']?['results']"
def first(n): return "first(union(body('" + n + "'),createArray(json('{}'))))"
def obj(props, optional=()): return {'type': 'object', 'required': [k for k in props if k not in optional], 'properties': props}
def integer(nullable=False): return {'type': ['integer', 'null'] if nullable else 'integer', 'minimum': 1}
def text(nullable=False, maximum=64000): return {'type': ['string', 'null'] if nullable else 'string', 'maxLength': maximum}
def choice(*values): return {'type': 'string', 'enum': list(values)}
def array(items, maximum): return {'type': 'array', 'maxItems': maximum, 'items': items}
def complete(n, bound):
    d = "body('" + n + "')?['d']"
    return f"and(not(equals({d}?['results'],null)),lessOrEquals(length(coalesce({d}?['results'],json('[]'))),{bound}),empty({d}?['__next']),empty(body('{n}')?['@odata.nextLink']),empty(body('{n}')?['odata.nextLink']))"

def gate(name, pred, code, n=None):
    return branch(pred, {}, {name + '_error': setvar('ErrorCode', code),
                            name + '_stop': compose('@div(1,0)', name + '_error')}, n)


def build_trigger():
    """Minimal explicit participant reference; never caller identity/authority."""
    return {'manual': {'type': 'Request', 'kind': 'PowerAppV2', 'inputs': {'schema': {
        'type': 'object', 'properties': {'number': {'type': 'number', 'title': 'ParticipantId',
        'x-ms-content-hint': 'NUMBER', 'x-ms-dynamically-added': True}}, 'required': ['number']}}}}


def build_source(seed, people):
    """Adapt the already-inspected native Invoker seed without owner fallback."""
    read = next(deepcopy(a) for _, a in walk(seed['probe']['properties']['definition']['actions'])
                if a['type'] == 'OpenApiConnection')
    read['inputs']['parameters']['table'] = people['lists']['participants']['listId']
    return {'properties': {'connectionReferences': {'shared_sharepointonline': {'source': 'Invoker'}},
        'definition': {'triggers': build_trigger(), 'actions': {'Read_participant': read}}}}


def source_metadata(source, people):
    props = source['properties']
    if props['connectionReferences']['shared_sharepointonline'].get('source') != 'Invoker':
        raise ValueError('Invoker required; no owner fallback')
    triggers = props['definition']['triggers']
    if len(triggers) != 1 or triggers['manual'].get('kind') != 'PowerAppV2':
        raise ValueError('Expected one PowerAppV2 trigger')
    schema = triggers['manual']['inputs']['schema']
    if set(schema['properties']) != {'number'} or schema['properties']['number'].get('type') != 'number' or schema.get('required') != ['number']:
        raise ValueError('Expected required ParticipantId number reference')
    inputs = props['definition']['actions']['Read_participant']['inputs']
    if inputs['authentication'] != {'type': 'Raw', 'value': RAW_INVOKER}:
        raise ValueError('Expected inspected native Raw Invoker authentication')
    if inputs['parameters']['table'].strip('{}').lower() != people['lists']['participants']['listId']:
        raise ValueError('Unexpected participant list target')
    host = inputs['host']
    if host.get('apiId') != '/providers/Microsoft.PowerApps/apis/shared_sharepointonline' or host.get('operationId') != 'HttpRequest':
        raise ValueError('Expected existing standard SharePoint HTTP operation')
    return inputs['parameters']['dataset'], deepcopy(inputs['authentication'])


def public_profile_schema():
    label = obj({'id': integer(), 'label': text(maximum=255)})
    label['additionalProperties'] = False
    props = {'profileId': integer(), 'displayName': {'type': 'string', 'minLength': 1, 'maxLength': 255},
        **{k: array(deepcopy(label), 5000) for k in ['teachLanguages', 'learnLanguages', 'shareCultures', 'learnCultures']},
        'timeZone': obj({'id': integer(True), 'label': text(True, 255), 'ianaId': text(True, 255)}),
        'learningFocus': text(), 'comments': text()}
    props['timeZone']['additionalProperties'] = False
    return {**obj(props), 'additionalProperties': False}


def public_group_schema():
    label = {'type': 'object', 'additionalProperties': False, 'required': ['id', 'label'],
             'properties': {'id': integer(), 'label': text(maximum=255)}}
    return {**obj({'groupId': integer(), 'membershipId': integer(), 'name': {'type': 'string', 'minLength': 1, 'maxLength': 255},
        'purpose': text(), 'exchangeType': choice('Language', 'Culture', 'Combined'),
        'languageFocus': array(label, 5000), 'cultureFocus': array(label, 5000),
        'capacity': {'type': 'integer', 'minimum': 2, 'maximum': 10}, 'state': choice('Open', 'Closed', 'Ended'),
        'memberCount': {'type': 'integer', 'minimum': 0, 'maximum': 2000},
        'freeSlots': {'type': 'integer', 'minimum': 0, 'maximum': 10},
        'members': array(public_profile_schema(), 500),
        'expectedETag': {'type': 'string', 'maxLength': 128, 'pattern': r'^(W/)?"[0-9]+"$'}}), 'additionalProperties': False}


def build_actions(source, people, groups, build_id):
    """Return the full parent graph. No metadata scan, writes or child invocation."""
    site, auth = source_metadata(source, people)
    targets = {'requests': REQUESTS, 'profiles': people['lists']['participants']['listId'],
        'groups': groups['lists']['groups']['listId'], 'memberships': groups['lists']['members']['listId'],
        **{r: people['lists'][r]['listId'] for r in ['language', 'culture', 'timezone']}}
    fields = people['lists']['participants']['fields']
    actual = lambda key: fields[key]['internalName']
    account = actual('ParticipantAccount')
    interests = [('teachLanguages', actual('TeachLanguages')), ('learnLanguages', actual('LearnLanguages')),
                 ('shareCultures', actual('ShareCultures')), ('learnCultures', actual('LearnCultures'))]
    zone = actual('TimeZone'); focus = actual('LearningFocus'); comments = actual('Comments')
    def base(role): return "_api/web/lists(guid'" + targets[role] + "')"
    def http(uri, n=None):
        return {'type': 'OpenApiConnection', 'runAfter': after(n), 'inputs': {
            'parameters': {'dataset': site, 'parameters/method': 'GET', 'parameters/uri': uri,
                           'parameters/headers': {'Accept': 'application/json;odata=verbose'}},
            'host': {'apiId': '/providers/Microsoft.PowerApps/apis/shared_sharepointonline',
                     'connectionName': 'shared_sharepointonline', 'operationId': 'HttpRequest'},
            'authentication': deepcopy(auth)}}
    a = {}; previous = None
    for k, kind, value in [('ErrorCode', 'string', ''), ('Groups', 'array', []), ('Members', 'array', []), ('OperationalEpisodes', 'array', [])]:
        name = 'Initialize_' + k
        a[name] = {'type': 'InitializeVariable', 'inputs': {'variables': [{'name': k, 'type': kind, 'value': value}]}, 'runAfter': after(previous)}
        previous = name
    s = {'Input_reference': parse("@triggerBody()?['number']", integer()),
         'Read_invoker': http('_api/web/currentuser?$select=Id', 'Input_reference'),
         'Invoker': parse("@body('Read_invoker')?['d']", obj({'Id': integer()}), 'Read_invoker')}
    own_uri = "@concat('" + base('profiles').replace("'", "''") + '/items?$select=Id&$filter=' + account + "Id eq ',string(body('Invoker')?['Id']),'&$top=2')"
    s['Read_own'] = http(own_uri, 'Invoker')
    s['Own_complete'] = gate('Own_complete', complete('Read_own', 1), 'UNAUTHORIZED_PROFILE', 'Read_own')
    s['Own_match'] = gate('Own_match', "and(equals(length(" + rows('Read_own') + "),1),equals(first(union(" + rows('Read_own') + ",createArray(json('{}'))))?['Id'],body('Input_reference')))", 'UNAUTHORIZED_PROFILE', 'Own_complete')
    s['Actor'] = compose("@body('Input_reference')", 'Own_match'); previous = 'Actor'
    optional_lookup = {'type': ['object', 'null'], 'required': ['results'], 'properties': {'results': array(integer(), 5000)}}
    profile_props = {'Id': integer(), account: obj({'Title': {'type': 'string', 'minLength': 1, 'maxLength': 255}}),
        **{f + 'Id': deepcopy(optional_lookup) for _, f in interests}, zone + 'Id': integer(True), focus: text(True), comments: text(True)}
    schemas = {
        'requests': obj({'Id': integer(), 'SenderParticipantId': {'type': 'number', 'minimum': 1},
            'RecipientParticipantId': {'type': ['number', 'null'], 'minimum': 1}, 'TargetGroupId': integer(True),
            'RequestType': choice('Personal', 'Group'), 'Status': choice('Pending', 'Accepted', 'Declined', 'Cancelled'),
            'OperationComplete': {'type': 'boolean'}}),
        'groups': obj({'Id': integer(), 'Title': {'type': 'string', 'minLength': 1, 'maxLength': 255}, 'Purpose': text(True),
            'ExchangeType': choice('Language', 'Culture', 'Combined'), 'LanguageFocusId': deepcopy(optional_lookup),
            'CultureFocusId': deepcopy(optional_lookup), 'Capacity': {'type': 'number', 'minimum': 2, 'maximum': 10},
            'State': choice('Open', 'Closed', 'Ended'), 'SourceRequestId': {'type':'number','minimum':1}, 'SetupComplete': {'type': 'boolean'},
            '__metadata': obj({'etag': {'type': 'string', 'maxLength': 128, 'pattern': r'^(W/)?"[0-9]+"$'}})},
            optional=['Purpose', 'LanguageFocusId', 'CultureFocusId']),
        'memberships': obj({'Id': integer(), 'GroupId': integer(), 'ParticipantId': integer(),
            'MembershipStatus': choice('Active', 'Left'), 'MembershipKey': {'type': 'string', 'minLength': 1}, 'LeftAt': text(True)}),
        'profiles': obj(profile_props, optional=[f + 'Id' for _, f in interests] + [zone + 'Id', focus, comments]),
    }
    for role in ['language', 'culture', 'timezone']:
        schemas[role] = obj({'Id': integer(), 'Title': text(maximum=255), **({'IANA_ID': text(maximum=255)} if role == 'timezone' else {})})
    selects = {'requests': 'Id,SenderParticipantId,RecipientParticipantId,TargetGroupId,RequestType,Status,OperationComplete',
        'groups': 'Id,Title,Purpose,ExchangeType,LanguageFocusId,CultureFocusId,Capacity,State,SourceRequestId,SetupComplete',
        'memberships': 'Id,GroupId,ParticipantId,MembershipStatus,MembershipKey,LeftAt',
        'profiles': ','.join(['Id', account + '/Title'] + [f + 'Id' for _, f in interests] + [zone + 'Id', focus, comments]),
        'language': 'Id,Title', 'culture': 'Id,Title', 'timezone': 'Id,Title,IANA_ID'}
    for role, selected in selects.items():
        read = 'Read_' + role; bound = role + '_complete'; parsed = 'Data_' + role
        uri = base(role) + '/items?$select=' + selected
        if role == 'profiles': uri += '&$expand=' + account
        s[read] = http(uri + '&$orderby=Id asc&$top=' + str(BOUNDS[role] + 1), previous)
        s[bound] = gate(bound, complete(read, BOUNDS[role]), 'READ_BOUND_OR_INCOMPLETE', read)
        s[role + '_parse_code'] = setvar('ErrorCode', 'DATA_INTEGRITY', bound)
        raw = 'Raw_groups' if role == 'groups' else parsed
        s[raw] = parse('@' + rows(read), array(schemas[role], BOUNDS[role]), role + '_parse_code')
        if role == 'groups':
            # Existing Capacity/SourceRequestId are Number, not integer fields.
            # Reject fractions and canonicalize integral values before counts/keys.
            ref = "items('Validate_group_numbers')"
            s['Validate_group_numbers'] = loop("@body('Raw_groups')", {
                'Whole_group_numbers': gate('Whole_group_numbers', f"and(equals({ref}?['Capacity'],int({ref}?['Capacity'])),equals({ref}?['SourceRequestId'],int({ref}?['SourceRequestId'])))", 'DATA_INTEGRITY')}, raw)
            projection = {k: "@item()?['" + k + "']" for k in schemas['groups']['properties']}
            for field in ['Capacity', 'SourceRequestId']: projection[field] = "@int(item()?['" + field + "'])"
            s[parsed] = select("@body('Raw_groups')", projection, 'Validate_group_numbers')
        s[role + '_parsed'] = setvar('ErrorCode', '', parsed)
        s[role + '_ids'] = select('@body(' + "'" + parsed + "')", "@item()?['Id']", role + '_parsed')
        s[role + '_unique'] = gate(role + '_unique', "equals(length(body('" + role + "_ids')),length(union(body('" + role + "_ids'),body('" + role + "_ids'))))", 'DATA_INTEGRITY', role + '_ids')
        previous = role + '_unique'
    r = "items('Validate_request_references')"
    s['Validate_request_references'] = loop("@body('Data_requests')", {'Whole_request_parties': gate('Whole_request_parties',
        f"and(equals({r}?['SenderParticipantId'],int({r}?['SenderParticipantId'])),equals(coalesce({r}?['RecipientParticipantId'],0),int(coalesce({r}?['RecipientParticipantId'],0))))", 'DATA_INTEGRITY')}, previous)
    s['Active_rows'] = query("@body('Data_memberships')", "equals(item()?['MembershipStatus'],'Active')", 'Validate_request_references')
    s['Active_pairs'] = select("@body('Active_rows')", "@concat(string(item()?['GroupId']),':',string(item()?['ParticipantId']))", 'Active_rows')
    s['Active_unique'] = gate('Active_unique', "equals(length(body('Active_pairs')),length(union(body('Active_pairs'),body('Active_pairs'))))", 'MEMBERSHIP_INTEGRITY', 'Active_pairs')
    s['Groups_sources'] = select("@body('Data_groups')", "@item()?['SourceRequestId']", 'Active_unique')
    s['Groups_sources_unique'] = gate('Groups_sources_unique', "equals(length(body('Groups_sources')),length(union(body('Groups_sources'),body('Groups_sources'))))", 'DATA_INTEGRITY', 'Groups_sources')
    m = "items('Each_episode')"; g = first('Episode_group')
    episode = {'Episode_group': query("@body('Data_groups')", f"equals(item()?['Id'],{m}?['GroupId'])")}
    personal_source = f"and(equals(item()?['Id'],{g}?['SourceRequestId']),equals(item()?['RequestType'],'Personal'),equals(item()?['TargetGroupId'],null),not(equals(item()?['RecipientParticipantId'],null)),not(equals(item()?['SenderParticipantId'],item()?['RecipientParticipantId'])),equals(item()?['Status'],'Accepted'),equals(item()?['OperationComplete'],true))"
    episode['Episode_source'] = query("@body('Data_requests')", personal_source, 'Episode_group')
    personal = f"and(equals(item()?['RequestType'],'Personal'),equals(item()?['Id'],{g}?['SourceRequestId']),or(equals(item()?['SenderParticipantId'],{m}?['ParticipantId']),equals(item()?['RecipientParticipantId'],{m}?['ParticipantId'])))"
    joined = f"and(equals(item()?['RequestType'],'Group'),equals(item()?['TargetGroupId'],{m}?['GroupId']),equals(item()?['RecipientParticipantId'],null),equals(item()?['SenderParticipantId'],{m}?['ParticipantId']))"
    episode['Episode_commit'] = query("@body('Data_requests')", f"and(equals({m}?['MembershipKey'],concat('request:',string(item()?['Id']),':participant:',string({m}?['ParticipantId']))),equals(item()?['Status'],'Accepted'),equals(item()?['OperationComplete'],true),or({personal},{joined}))", 'Episode_source')
    episode['Episode_operational'] = branch(f"and(equals(length(body('Episode_group')),1),equals({g}?['SetupComplete'],true),empty({m}?['LeftAt']),equals(length(body('Episode_source')),1),equals(length(body('Episode_commit')),1))",
        {'Remember_episode': append('OperationalEpisodes', {'groupId': '@' + m + "?['GroupId']", 'profileId': '@' + m + "?['ParticipantId']", 'membershipId': '@' + m + "?['Id']"})}, n='Episode_commit')
    s['Each_episode'] = loop("@body('Active_rows')", episode, 'Groups_sources_unique')
    s['Own_episodes'] = query("@variables('OperationalEpisodes')", "equals(item()?['profileId'],outputs('Actor'))", 'Each_episode')
    s['Own_group_ids'] = select("@body('Own_episodes')", "@item()?['groupId']", 'Own_episodes')
    s['Own_groups'] = query("@body('Data_groups')", "contains(body('Own_group_ids'),item()?['Id'])", 'Own_group_ids')
    group = "items('Each_own_group')"
    displayed = {
        'Own_group_episode': query("@body('Own_episodes')", f"equals(item()?['groupId'],{group}?['Id'])"),
        'Own_group_episode_unique': gate('Own_group_episode_unique', "equals(length(body('Own_group_episode')),1)", 'MEMBERSHIP_INTEGRITY', 'Own_group_episode'),
        'Reset_members': setvar('Members', [], 'Own_group_episode_unique'),
        'Physical_members': query("@body('Active_rows')", f"equals(item()?['GroupId'],{group}?['Id'])", 'Reset_members')}
    displayed['Capacity_valid'] = gate('Capacity_valid', f"and(lessOrEquals(length(body('Physical_members')),{group}?['Capacity']),lessOrEquals({group}?['Capacity'],if(equals({group}?['ExchangeType'],'Language'),3,10)))", 'CAPACITY_INTEGRITY', 'Physical_members')
    displayed['Public_episodes'] = query("@variables('OperationalEpisodes')", f"equals(item()?['groupId'],{group}?['Id'])", 'Capacity_valid')
    member = {'Member_profile': query("@body('Data_profiles')", "equals(item()?['Id'],items('Each_public_member')?['profileId'])")}
    member['Member_exists'] = gate('Member_exists', "equals(length(body('Member_profile')),1)", 'PROFILE_DATA_INCOMPLETE', 'Member_profile')
    p = first('Member_profile'); prev = 'Member_exists'
    # Pure explicit display projection, not availability/eligibility normalization.
    for label, field in interests:
        catalogue = 'language' if label in ['teachLanguages', 'learnLanguages'] else 'culture'
        ids = f"coalesce({p}?['{field}Id']?['results'],json('[]'))"
        q = 'Member_' + label + '_rows'; out = 'Member_' + label
        member[q] = query("@body('Data_" + catalogue + "')", f"contains({ids},item()?['Id'])", prev)
        check = 'Member_' + label + '_complete'
        member[check] = gate(check, f"equals(length(body('{q}')),length(union({ids},{ids})))", 'PROFILE_DATA_INCOMPLETE', q)
        member[out] = select("@body('" + q + "')", {'id': "@item()?['Id']", 'label': "@item()?['Title']"}, check); prev = out
    member['Member_zone_rows'] = query("@body('Data_timezone')", f"equals(item()?['Id'],{p}?['{zone}Id'])", prev)
    member['Member_zone_complete'] = gate('Member_zone_complete', f"or(equals({p}?['{zone}Id'],null),equals(length(body('Member_zone_rows')),1))", 'PROFILE_DATA_INCOMPLETE', 'Member_zone_rows')
    z = first('Member_zone_rows')
    member['Member_display'] = compose({'profileId': '@' + p + "?['Id']", 'displayName': '@' + p + f"?['{account}']?['Title']",
        **{k: "@body('Member_" + k + "')" for k, _ in interests},
        'timeZone': {'id': '@' + z + "?['Id']", 'label': '@' + z + "?['Title']", 'ianaId': '@' + z + "?['IANA_ID']"},
        'learningFocus': '@coalesce(' + p + f"?['{focus}'],'')", 'comments': '@coalesce(' + p + f"?['{comments}'],'')"}, 'Member_zone_complete')
    member['Member_public'] = parse("@outputs('Member_display')", public_profile_schema(), 'Member_display')
    member['Remember_member'] = append('Members', "@body('Member_public')", 'Member_public')
    displayed['Each_public_member'] = loop("@body('Public_episodes')", member, 'Public_episodes'); prev = 'Each_public_member'
    for label, field, role in [('languageFocus', 'LanguageFocusId', 'language'), ('cultureFocus', 'CultureFocusId', 'culture')]:
        ids = f"coalesce({group}?['{field}']?['results'],json('[]'))";q = 'Group_' + label + '_rows';out = 'Group_' + label
        displayed[q] = query("@body('Data_" + role + "')", f"contains({ids},item()?['Id'])", prev)
        check = 'Group_' + label + '_complete'
        displayed[check] = gate(check, f"equals(length(body('{q}')),length(union({ids},{ids})))", 'GROUP_DATA_INCOMPLETE', q)
        displayed[out] = select("@body('" + q + "')", {'id': "@item()?['Id']", 'label': "@item()?['Title']"}, check);prev = out
    displayed['Group_display'] = compose({'groupId': '@' + group + "?['Id']",
        'membershipId': '@' + first('Own_group_episode') + "?['membershipId']", 'name': '@' + group + "?['Title']",
        'purpose': '@coalesce(' + group + "?['Purpose'],'')", 'exchangeType': '@' + group + "?['ExchangeType']",
        'languageFocus': "@body('Group_languageFocus')", 'cultureFocus': "@body('Group_cultureFocus')",
        'capacity': '@' + group + "?['Capacity']", 'state': '@' + group + "?['State']",
        'memberCount': "@length(body('Physical_members'))", 'freeSlots': '@sub(' + group + "?['Capacity'],length(body('Physical_members')))",
        'members': "@variables('Members')", 'expectedETag': '@' + group + "?['__metadata']?['etag']"}, prev)
    displayed['Group_public'] = parse("@outputs('Group_display')", public_group_schema(), 'Group_display')
    displayed['Remember_group'] = append('Groups', "@body('Group_public')", 'Group_public')
    s['Each_own_group'] = loop("@body('Own_groups')", displayed, 'Own_groups')
    s['Response_bound'] = gate('Response_bound', "lessOrEquals(length(string(variables('Groups'))),250000)", 'RESPONSE_BOUND', 'Each_own_group')
    a['Read_authorized_groups'] = {'type': 'Scope', 'actions': s, 'runAfter': after('Initialize_OperationalEpisodes')}
    a['Read_failure'] = {'type': 'Scope', 'runAfter': {'Read_authorized_groups': ['Failed', 'TimedOut']}, 'actions': {
        'Failure_code': branch("empty(variables('ErrorCode'))", {'Set_generic_failure': setvar('ErrorCode', 'READ_OR_DATA_FAILED')}),
        'Clear_groups': setvar('Groups', [], 'Failure_code'), 'Clear_members': setvar('Members', [], 'Clear_groups')}}
    output_fields = ['groupsjson', 'groupstatus', 'errormessage', 'resultcode', 'runreference', 'mode', 'paging']
    a['Respond_to_a_Power_App_or_flow'] = {'type': 'Response', 'kind': 'PowerApp', 'runAfter': {'Read_failure': ['Succeeded', 'Skipped']}, 'inputs': {
        'statusCode': 200, 'schema': {'type': 'object', 'properties': {k: {'title': k, 'type': 'string', 'x-ms-content-hint': 'TEXT', 'x-ms-dynamically-added': True} for k in output_fields}},
        'body': {'groupsjson': "@if(empty(variables('ErrorCode')),string(variables('Groups')),'[]')",
            'groupstatus': "@if(empty(variables('ErrorCode')),if(empty(variables('Groups')),'Waiting','In a group'),'')",
            'errormessage': "@if(empty(variables('ErrorCode')),'','Groups could not be read completely. Refresh or return the result code for review.')",
            'resultcode': "@if(empty(variables('ErrorCode')),'OK',variables('ErrorCode'))", 'runreference': "@workflow()?['run']?['name']",
            'mode': 'OWNER_PREVIEW_PENDING_ACCESS_PROOF', 'paging': 'NO_PAGING_COMPLETE_BOUNDED_READ'}}}
    measure(a)
    return a


def build_parent(solution_source, output):
    """Readable native-envelope parent; integrator supplies new Solution root/ID."""
    output = Path(output); review_path = output.with_suffix('.review.json')
    if output.exists() or review_path.exists(): raise FileExistsError(output)
    evidence = json.loads((ROOT / 'artifacts/shared_validation/results/native-sharepoint-solution.analysis.json').read_text())
    seed = inspect_caller_export(solution_source, evidence['site'], evidence['sharedBuildId'])
    people = json.loads((ROOT / 'config/tenant_schema_mapping.json').read_text())
    groups = json.loads((ROOT / 'config/group_schema_mapping.json').read_text())
    source = build_source(seed, people); build_id = str(uuid4())
    actions = build_actions(source, people, groups, build_id)
    document = invoker_parent_document(seed, source['properties']['definition']['triggers'], actions)
    document['properties']['displayName'] = NAME
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(document, indent=2) + '\n', encoding='utf-8', newline='\n')
    review = {'sourceTicket': 64, 'version': 'v2', 'packageBuildId': build_id, **measure(actions), 'bounds': BOUNDS,
        'writes': 0, 'connectorReadDefinitions': sum(a['type']=='OpenApiConnection' for _, a in walk(actions)),
        'workflowCalls': 0, 'sharedChildRequired': False, 'schemaAuditPerClick': False,
        'nativeStatus': 'NOT_IMPORTED_NOT_TESTED', 'ordinaryUserAccessVerified': False,
        'runtimeSource': 'invoker', 'trigger': build_trigger(),
        'definitionSha256': hashlib.sha256(output.read_bytes()).hexdigest(),
        'generatorSha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'nativeSeedSha256': seed['receipt']['sourceExportSha256'],
        'packaging': 'READABLE_NATIVE_SOLUTION_PARENT; integrator assigns new workflow identity/root and packages existing SharePoint reference; no legacy ZIP or native certification',
        'limits': {'actions': 500, 'maximumActionDepth': 8}}
    review_path.write_text(json.dumps(review, indent=2) + '\n', encoding='utf-8', newline='\n')
    return review


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--solution-source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build_parent(args.solution_source, args.output), indent=2))


if __name__ == '__main__': main()
