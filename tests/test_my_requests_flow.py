"""Execute emitted #62 WDL graph; fake connector is not native/access proof."""
from copy import deepcopy
from datetime import datetime, timedelta
import json
from pathlib import Path
import re
from xml.etree import ElementTree as ET
from zipfile import ZipFile
import pytest
from test_discovery_flow import FlowRunner
from scripts.power_automate import my_requests_flow as flow
from scripts.power_automate.schema_audit import measure

PEOPLE = json.loads((flow.ROOT / 'config/tenant_schema_mapping.json').read_text(encoding='utf-8'))
GROUPS = json.loads((flow.ROOT / 'config/group_schema_mapping.json').read_text(encoding='utf-8'))


class ReaderRunner(FlowRunner):
    def expr(self, expression, context):
        # Independently evaluate only emitted native XML metadata primitives.
        pattern = r"xpath\(xml\((?:coalesce\(item\(\)\?\['SchemaXml'\],'<Field/>'\)|if\(empty\(item\(\)\?\['SchemaXml'\]\),'<Field/>',item\(\)\?\['SchemaXml'\]\))\),'([^']+)'\)"
        def xpath(match):
            try: root = ET.fromstring(context['item'].get('SchemaXml') or '<Field/>')
            except ET.ParseError as error: raise ValueError('Invalid metadata XML') from error
            path = match.group(1)
            if path.startswith('string(/Field/@'):
                attribute = path[len('string(/Field/@'):-1]; value = root.attrib.get(attribute, '')
            elif path in ['/Field/@List', '/Field/@Decimals']:
                attribute = path.split('@')[1]
                raw = root.attrib.get(attribute)
                style = getattr(self, 'attribute_style', 'xml_nodes')
                if raw is None: value = []
                elif style == 'scalar': value = raw
                elif style == 'value_array': value = [raw]
                else: value = [attribute + '="' + raw + '"']
            elif path == '/Field/CHOICES/CHOICE/text()': value = [e.text or '' for e in root.findall('./CHOICES/CHOICE')]
            else: raise AssertionError('Unsupported XPath ' + path)
            return "json('" + json.dumps(value).replace("'", "''") + "')"
        return super().expr(re.sub(pattern, xpath, expression), context)


def metadata(name, expected):
    root = ET.Element('Field', {'Name': name, 'Type': expected['TypeAsString']})
    if 'LookupList' in expected: root.set('List', '{' + expected['LookupList'] + '}')
    if 'Decimals' in expected: root.set('Decimals', expected['Decimals'])
    if 'Choices' in expected:
        choices = ET.SubElement(root, 'CHOICES')
        for value in expected['Choices']: ET.SubElement(choices, 'CHOICE').text = value
    return {'InternalName': name, **expected, 'SchemaXml': ET.tostring(root, encoding='unicode')}


def source():
    auth = {'type': 'Raw', 'value': 'SOURCE_INVOKER_TOKEN_EXPRESSION'}
    return {'properties': {'connectionReferences': {'shared_sharepointonline': {'source': 'Invoker'}}, 'definition': {
        'triggers': {'manual': {'type': 'Request', 'kind': 'PowerAppV2', 'inputs': {'schema': {
            'type': 'object', 'properties': {'number': {'type': 'number', 'title': 'NumParticipantIdber'}}, 'required': ['number']}}}},
        'actions': {'Read_participant': {'inputs': {'parameters': {'dataset': 'https://example.sharepoint.com/sites/test', 'table': PEOPLE['lists']['participants']['listId']}, 'authentication': auth}},
                    'Get_items': {'inputs': {'parameters': {'table': flow.REQUESTS}}},
                    'Request_rows': {'inputs': {'select': {k: '' for k in ['requestId', 'senderParticipantId', 'recipientParticipantId', 'status', 'created', 'direction']}}}}}}}


def request(i=1, sender=1, recipient=2, group=None, status='Pending', complete=False):
    pair = f'open:person:{min(sender, recipient or 0)}:{max(sender, recipient or 0)}' if group is None else f'open:group:{group}:participant:{sender}'
    return {'Id': i, 'Created': (datetime(2026, 11, 8, 12) - timedelta(seconds=i)).isoformat() + 'Z', 'SenderParticipantId': sender, 'RecipientParticipantId': recipient, 'TargetGroupId': group,
            'RequestType': 'Personal' if group is None else 'Group', 'Status': status, 'OperationComplete': complete,
            'SendOperationKey': f'send:{sender}:intent-{i}', 'ConnectionKey': pair if status == 'Pending' or status == 'Accepted' and not complete else f'history:request:{i}',
            'WinningOperationKey': None if status == 'Pending' else f'decision:{i}', 'SECRET': 'PRIVATE_REQUEST', 'Email': 'PRIVATE_EMAIL'}


def profile(i):
    return {'Id': i, 'Status': 'Active', 'ParticipationStatus': 'Active', 'OpenToConnections': True, 'SECRET': 'PRIVATE_PROFILE', 'Participantaccount': {'Email': 'PRIVATE_EMAIL'}}


class Fake:
    def __init__(self):
        self.data = {'requests': [request(), request(2, 3, 1), request(3, 2, 3)], 'profiles': [profile(i) for i in [1, 2, 3]], 'groups': [], 'memberships': []}
        self.fields = {role: [metadata(name, expected) for name, expected in fields.items()]
                       for role, fields in flow.field_contracts(PEOPLE, GROUPS).items()}
        self.queries = []; self.own = [{'Id': 1}]; self.paged = None; self.overflow = None; self.fail = None
    def group(self):
        self.data['groups'] = [{'Id': 10, 'SourceRequestId': 70, 'SetupComplete': True, 'State': 'Open', 'Capacity': 3, 'WriteOwner': None}]
        self.data['requests'] += [request(70, 1, 2, status='Accepted', complete=True), request(71, 3, None, 10)]
        self.data['memberships'] = [{'Id': 20, 'GroupId': 10, 'ParticipantId': 1, 'MembershipStatus': 'Active', 'MembershipKey': 'request:70:participant:1', 'LeftAt': None},
                                    {'Id': 21, 'GroupId': 10, 'ParticipantId': 2, 'MembershipStatus': 'Active', 'MembershipKey': 'request:70:participant:2', 'LeftAt': None}]
    def request(self, p):
        assert p['parameters/method'] == 'GET'
        uri = p['parameters/uri']; self.queries.append(uri)
        if self.fail and self.fail in uri: return {'statusCode': 502, 'body': {'error': 'PRIVATE_BACKEND_ERROR'}}
        if uri.startswith('_api/web/currentuser'): return {'statusCode': 200, 'body': {'d': {'Id': 101}}}
        if 'ParticipantaccountId eq' in uri: role = 'own'; data = self.own
        else:
            role = next(k for k, target in {'requests': flow.REQUESTS, 'profiles': PEOPLE['lists']['participants']['listId'], 'groups': GROUPS['lists']['groups']['listId'], 'memberships': GROUPS['lists']['members']['listId']}.items() if target in uri)
            if '?$select=Id,BaseTemplate' in uri:
                target = {'requests': flow.REQUESTS, 'profiles': PEOPLE['lists']['participants']['listId'], 'groups': GROUPS['lists']['groups']['listId'], 'memberships': GROUPS['lists']['members']['listId']}[role]
                return {'statusCode': 200, 'body': {'d': {'Id': target, 'BaseTemplate': 100}}}
            if '/fields?' in uri: data = self.fields[role]; role += '_fields'
            else: data = self.data[role]
        data = deepcopy(data)
        if role == 'requests' and '/items?' in uri:
            assert '$orderby=Created desc,ID desc' in uri
            data.sort(key=lambda row: (str(row.get('Created', '')), row['Id']), reverse=True)
        if self.overflow == role: data = [data[0] if data else {}] * (flow.BOUNDS[role] + 1)
        d = {'results': data}
        if self.paged == role: d['__next'] = 'PRIVATE_NEXTLINK'
        return {'statusCode': 200, 'body': {'d': d}}


def execute(server=None, actor=1):
    r = ReaderRunner(server or Fake(), actor)
    r.run(flow.build_actions(source(), PEOPLE, GROUPS, 'test-build'))
    assert r.response is not None
    return r


def public(r): return json.loads(r.response['requestsjson'])
def row(r, i): return next(x for x in public(r) if x['requestId'] == i)
def failure(r, code=None):
    assert r.response['resultcode'] == code if code else r.response['resultcode'] != 'OK'
    assert public(r) == []
    assert not any(x in json.dumps(r.response) for x in ['PRIVATE_', 'SendOperationKey', 'WinningOperationKey', 'Participantaccount', 'ConnectionKey', 'MembershipKey'])


def test_own_sent_and_personal_received_filter_before_projection():
    r = execute(); assert r.response['resultcode'] == 'OK'
    assert [x['requestId'] for x in public(r)] == [1, 2]
    assert row(r, 1)['direction'] == 'Sent' and row(r, 1)['actions'] == {'cancel': True, 'accept': False, 'decline': False}
    assert row(r, 2)['direction'] == 'Received' and row(r, 2)['actions'] == {'cancel': False, 'accept': True, 'decline': True}
    assert not any(x in json.dumps(r.response) for x in ['PRIVATE_', 'Email', 'SECRET', 'account', 'OperationKey', 'ConnectionKey'])
    assert r.response['paging'] == 'NO_PAGING_COMPLETE_BOUNDED_READ'


@pytest.mark.parametrize('actor,own', [(2, [{'Id': 1}]), (1, []), (1, [{'Id': 1}, {'Id': 2}]), (1, [{'Id': 2}])])
def test_caller_binding_no_owner_fallback(actor, own):
    f = Fake(); f.own = own; r = execute(f, actor); failure(r, 'UNAUTHORIZED_PROFILE')
    assert not any('/items?' in q and 'ParticipantaccountId eq' not in q for q in f.queries)


@pytest.mark.parametrize('actor', [0, -1, 1.5, '1', None])
def test_bad_input_rejected_before_connector(actor):
    f = Fake(); failure(execute(f, actor)); assert f.queries == []


def test_group_incoming_requires_committed_source_episode_and_no_leader():
    f = Fake(); f.group(); r = execute(f)
    assert r.response['resultcode'] == 'OK' and row(r, 71)['actions']['accept']
    assert row(r, 71)['direction'] == 'Received'
    assert not any(k in json.dumps(public(r)) for k in ['Leader', 'WriteOwner', 'SourceRequestId', 'MembershipKey', 'SetupComplete'])


@pytest.mark.parametrize('variant', ['left', 'leftAt', 'setup', 'sourceIncomplete', 'episodeIncomplete', 'wrongParty', 'wrongGroup', 'ended', 'noSource'])
def test_nonoperational_group_has_no_audience_authority(variant):
    f = Fake(); f.group(); m = f.data['memberships'][0]; g = f.data['groups'][0]; req = f.data['requests'][-2]
    if variant == 'left': m['MembershipStatus'] = 'Left'
    if variant == 'leftAt': m['LeftAt'] = '2026-01-01T00:00:00Z'
    if variant == 'setup': g['SetupComplete'] = False
    if variant == 'sourceIncomplete':
        f.data['requests'][0] = request(status='Cancelled', complete=True)
        req.update(OperationComplete=False, ConnectionKey='open:person:1:2')
    if variant == 'episodeIncomplete': m['MembershipKey'] = 'request:999:participant:1'
    if variant == 'wrongParty': req.update(SenderParticipantId=3)
    if variant == 'wrongGroup':
        f.data['groups'].append({**g, 'Id': 99, 'SourceRequestId': 999}); f.data['requests'].append(request(80, 1, None, 99, 'Accepted', True)); m['MembershipKey'] = 'request:80:participant:1'
    if variant == 'ended': g['State'] = 'Ended'
    if variant == 'noSource': g['SourceRequestId'] = 999
    r = execute(f); assert r.response['resultcode'] == 'OK'
    assert 71 not in [x['requestId'] for x in public(r)]


def test_group_join_episode_committed_for_exact_actor_and_target():
    f = Fake(); f.group(); f.data['requests'][-2].update(SenderParticipantId=2, RecipientParticipantId=3)
    f.data['requests'].append(request(80, 1, None, 10, 'Accepted', True))
    f.data['memberships'][0]['MembershipKey'] = 'request:80:participant:1'
    assert row(execute(f), 71)['actions']['decline']


def test_duplicate_active_episode_errors_zero_arrays():
    f = Fake(); f.group(); f.data['memberships'].append({**f.data['memberships'][0], 'Id': 23})
    failure(execute(f), 'MEMBERSHIP_INTEGRITY')


@pytest.mark.parametrize('status,complete', [('Accepted', False), ('Accepted', True), ('Declined', True), ('Cancelled', True)])
def test_pending_terminal_history_processing(status, complete):
    f = Fake(); f.data['requests'][0] = request(status=status, complete=complete); r = execute(f); x = row(r, 1)
    assert r.response['resultcode'] == 'OK' and x['status'] == status
    assert x['completed'] is complete and x['processing'] is (status == 'Accepted' and not complete)
    assert not any(x['actions'].values())


@pytest.mark.parametrize('key,value', [('SendOperationKey', ''), ('SendOperationKey', '  '), ('ConnectionKey', 'open:person:2:1'), ('ConnectionKey', 'history:request:1'), ('WinningOperationKey', 'bad'), ('OperationComplete', True), ('RequestType', 'Individual'), ('RecipientParticipantId', None), ('TargetGroupId', 10), ('OperationComplete', None)])
def test_malformed_or_legacy_incomplete_history_explicitly_fails(key, value):
    f = Fake(); f.data['requests'][0][key] = value; failure(execute(f))


@pytest.mark.parametrize('status,complete,key,value', [('Cancelled', False, 'ConnectionKey', 'history:request:1'), ('Accepted', False, 'ConnectionKey', 'history:request:1'), ('Accepted', True, 'ConnectionKey', 'open:person:1:2'), ('Declined', True, 'WinningOperationKey', None)])
def test_settled_keys_and_completion_coherent(status, complete, key, value):
    f = Fake(); f.data['requests'][0] = request(status=status, complete=complete); f.data['requests'][0][key] = value
    failure(execute(f), 'REQUEST_DATA_INCOMPLETE')


@pytest.mark.parametrize('role', ['requests', 'profiles', 'groups', 'memberships', 'requests_fields', 'profiles_fields', 'groups_fields', 'memberships_fields', 'own'])
def test_nextlink_never_partial_success(role):
    f = Fake(); f.group(); f.paged = role; failure(execute(f))


@pytest.mark.parametrize('role', ['requests', 'profiles', 'groups', 'memberships'])
def test_count_overflow_never_partial_success(role):
    f = Fake(); f.group(); f.overflow = role; failure(execute(f), 'READ_BOUND_OR_INCOMPLETE')


@pytest.mark.parametrize('mutation', ['missing', 'type', 'unique', 'indexed', 'required', 'lookup', 'vocabulary', 'duplicateField'])
def test_schema_gate_before_row_reads(mutation):
    f = Fake(); fields = f.fields['requests']
    if mutation == 'missing': fields.pop()
    if mutation == 'type': fields[0]['TypeAsString'] = 'LookupMulti'
    if mutation == 'unique': next(x for x in fields if x['InternalName'] == 'SendOperationKey')['EnforceUniqueValues'] = False
    if mutation == 'indexed': next(x for x in fields if x['InternalName'] == 'ConnectionKey')['Indexed'] = False
    if mutation == 'required': fields[0]['Required'] = False
    if mutation == 'lookup':
        target = next(x for x in fields if x['InternalName'] == 'TargetGroup')
        target['SchemaXml'] = target['SchemaXml'].replace(GROUPS['lists']['groups']['listId'], 'wrong-list')
    if mutation == 'vocabulary': next(x for x in fields if x['InternalName'] == 'RequestType')['SchemaXml'] = '<Field><CHOICES><CHOICE>Personal</CHOICE><CHOICE>Team</CHOICE></CHOICES></Field>'
    if mutation == 'duplicateField': fields.append(deepcopy(fields[0]))
    failure(execute(f), 'REQUEST_SCHEMA_UNVERIFIED')
    assert not any('/items?' in q for q in f.queries)


@pytest.mark.parametrize('key,value', [('ParticipationStatus', 'Paused'), ('ParticipationStatus', 'Inactive'), ('OpenToConnections', False), ('Status', 'Needs review')])
def test_unavailable_pending_feedback_does_not_cancel(key, value):
    f = Fake(); f.data['profiles'][2][key] = value; before = deepcopy(f.data); r = execute(f); x = row(r, 2)
    assert x['availability'] == 'UnavailablePending' and not x['actions']['accept'] and x['actions']['decline']
    assert row(r, 1)['actions']['cancel'] and f.data == before


@pytest.mark.parametrize('variant', ['closed', 'full', 'owner'])
def test_group_unavailable_pending_does_not_hide_authorized_history(variant):
    f = Fake(); f.group(); g = f.data['groups'][0]
    if variant == 'closed': g['State'] = 'Closed'
    if variant == 'full': g['Capacity'] = 2
    if variant == 'owner': g['WriteOwner'] = 'busy'
    x = row(execute(f), 71)
    assert x['availability'] == 'UnavailablePending' and x['actions']['decline'] and not x['actions']['accept']


@pytest.mark.parametrize('fail', ['/currentuser', '/fields?', '/items?'])
def test_generic_502_sanitized_not_duplicate(fail):
    f = Fake(); f.fail = fail; failure(execute(f), 'REQUEST_SCHEMA_UNVERIFIED' if fail == '/fields?' else 'READ_OR_DATA_FAILED')


def test_projection_failure_after_first_append_clears_all():
    f = Fake(); f.data['requests'][1]['SenderParticipantId'] = 99
    r = execute(f); failure(r, 'REQUEST_DATA_INCOMPLETE')
    assert r.variables['Requests'] == []


def test_structure_global_uniqueness_raw_auth_get_only_and_no_shared_utility():
    graph = flow.build_actions(source(), PEOPLE, GROUPS, 'fixture'); metrics = measure(graph)
    assert metrics['actions'] <= 500 and metrics['maximumActionDepth'] <= 8
    def visit(block):
        for a in block.values():
            if a['type'] == 'OpenApiConnection':
                assert a['inputs']['authentication'] == source()['properties']['definition']['actions']['Read_participant']['inputs']['authentication']
                assert a['inputs']['parameters']['parameters/method'] == 'GET'
            visit(a.get('actions', {})); visit(a.get('else', {}).get('actions', {}))
    visit(graph)
    bad = source(); bad['properties']['connectionReferences']['shared_sharepointonline']['source'] = 'Embedded'
    with pytest.raises(ValueError, match='Invoker'): flow.build_actions(bad, PEOPLE, GROUPS, 'fixture')


def test_package_source_evidence_trigger_and_import_envelope(tmp_path):
    src = tmp_path / 'source.zip'
    with ZipFile(src, 'w') as z: z.writestr('Microsoft.Flow/flows/source/definition.json', json.dumps(source()))
    out = tmp_path / 'reader.zip'; review = flow.build_package(src, out)
    assert review['sourceTriggerPreserved'] and review['rawAuthenticationPreserved'] and review['globalActionNamesUnique']
    assert review['sourcePublicShape'] == ['requestId', 'senderParticipantId', 'recipientParticipantId', 'status', 'created', 'direction']
    with ZipFile(out) as z:
        doc = json.loads(z.read(next(n for n in z.namelist() if n.endswith('/definition.json'))))
        assert doc['properties']['definition']['triggers'] == source()['properties']['definition']['triggers']
        assert doc['properties']['connectionReferences']['shared_sharepointonline']['source'] == 'Invoker'
        manifest = json.loads(z.read('manifest.json'))
        assert next(x for x in manifest['resources'].values() if x['type'] == 'Microsoft.Flow/flows')['suggestedCreationType'] == 'New'
    with pytest.raises(FileExistsError): flow.build_package(src, out)

@pytest.mark.parametrize('role,field', [('requests', 'SendOperationKey'), ('requests', 'ConnectionKey'), ('profiles', 'Id'), ('groups', 'SourceRequestId')])
def test_duplicate_identity_keys_fail_closed(role, field):
    f = Fake(); f.group()
    if role == 'groups': f.data[role].append({**f.data[role][0], 'Id': 11})
    else: f.data[role][1][field] = f.data[role][0][field]
    failure(execute(f), 'DATA_INTEGRITY')


@pytest.mark.parametrize('role', ['requests_fields', 'profiles_fields', 'groups_fields', 'memberships_fields'])
def test_metadata_overflow_and_extra_choice_fail_closed(role):
    f = Fake(); request_fn = f.request
    def oversized(p):
        response = request_fn(p)
        if '/fields?' in p['parameters/uri'] and role.split('_')[0] in next((k for k, v in {'requests': flow.REQUESTS, 'profiles': PEOPLE['lists']['participants']['listId'], 'groups': GROUPS['lists']['groups']['listId'], 'memberships': GROUPS['lists']['members']['listId']}.items() if v in p['parameters/uri']), ''):
            response['body']['d']['results'] *= 501
        return response
    f.request = oversized; failure(execute(f), 'REQUEST_SCHEMA_UNVERIFIED')


@pytest.mark.parametrize('field', ['Id', 'BaseTemplate'])
def test_wrong_list_identity_is_schema_failure(field):
    f = Fake(); request_fn = f.request
    def mismatched(p):
        response = request_fn(p)
        if '?$select=Id,BaseTemplate' in p['parameters/uri']: response['body']['d'][field] = 'wrong' if field == 'Id' else 101
        return response
    f.request = mismatched; failure(execute(f), 'REQUEST_SCHEMA_UNVERIFIED')


def test_schema_xml_extra_choice_or_malformed_xml_cannot_authorize_reads():
    for xml in ['<Field><CHOICES><CHOICE>Personal</CHOICE><CHOICE>Group</CHOICE><CHOICE>Other</CHOICE></CHOICES></Field>', '<broken']:
        f = Fake(); next(x for x in f.fields['requests'] if x['InternalName'] == 'RequestType')['SchemaXml'] = xml
        failure(execute(f), 'REQUEST_SCHEMA_UNVERIFIED')


def test_later_failure_does_not_overwrite_first_specific_error():
    f = Fake(); f.data['requests'][0]['ConnectionKey'] = 'wrong'
    r = execute(f); failure(r, 'REQUEST_DATA_INCOMPLETE')
    assert r.action_states['Each_visible_request'] == 'Skipped'
    assert r.action_states.get('Set_generic_failure', 'Skipped') == 'Skipped'


def test_full_bounds_and_reverse_person_pair_remain_complete():
    f = Fake(); f.data['requests'] = [request(i, 3, 1, status='Cancelled', complete=True) for i in range(1, 501)]
    r = execute(f); assert r.response['resultcode'] == 'OK' and len(public(r)) == 500
    assert all(x['direction'] == 'Received' for x in public(r))
    f = Fake(); f.data['requests'] = [request(1, 3, 1)]
    assert row(execute(f), 1)['actions']['accept']


def test_no_setvariable_self_reference():
    def walk(actions):
        for a in actions.values():
            if a['type'] == 'SetVariable': assert "variables('" + a['inputs']['name'] + "')" not in str(a['inputs']['value'])
            walk(a.get('actions', {})); walk(a.get('else', {}).get('actions', {}))
    walk(flow.build_actions(source(), PEOPLE, GROUPS, 'fixture'))


@pytest.mark.parametrize('field', ['SenderParticipantId', 'RecipientParticipantId', 'TargetGroup', 'RequestType', 'Status', 'WinningOperationKey', 'OperationComplete'])
def test_benign_request_indexes_are_allowed(field):
    f = Fake(); next(x for x in f.fields['requests'] if x['InternalName'] == field)['Indexed'] = True
    r = execute(f)
    assert r.response['resultcode'] == 'OK' and len(public(r)) == 2


@pytest.mark.parametrize('field,required', [('RequestType', False), ('Status', False), ('WinningOperationKey', True), ('OperationComplete', True)])
def test_required_request_flags_remain_exact(field, required):
    f = Fake(); next(x for x in f.fields['requests'] if x['InternalName'] == field)['Required'] = required
    failure(execute(f), 'REQUEST_SCHEMA_UNVERIFIED')


@pytest.mark.parametrize('flag', ['Hidden', 'ReadOnlyField'])
def test_request_fields_must_be_visible_and_writable_as_shared_contract(flag):
    f = Fake(); next(x for x in f.fields['requests'] if x['InternalName'] == 'Status')[flag] = True
    failure(execute(f), 'REQUEST_SCHEMA_UNVERIFIED')


def test_original_created_field_and_descending_timestamp_then_id_order():
    f = Fake(); f.data['requests'] = [request(1), request(2, 3, 1), request(4, 1, 3, status='Cancelled', complete=True)]
    f.data['requests'][0]['Created'] = '2026-11-08T10:00:00Z'
    f.data['requests'][1]['Created'] = '2026-11-08T11:00:00Z'
    f.data['requests'][2]['Created'] = '2026-11-08T11:00:00Z'
    r = execute(f)
    assert r.response['resultcode'] == 'OK'
    assert [x['requestId'] for x in public(r)] == [4, 2, 1]
    assert row(r, 1)['created'] == '2026-11-08T10:00:00Z'
    original = {'requestId', 'senderParticipantId', 'recipientParticipantId', 'status', 'created', 'direction'}
    assert all(original <= set(x) for x in public(r))
    reads = [q for q in f.queries if '/items?' in q and flow.REQUESTS in q]
    assert len(reads) == 1 and '$select=Id,Created,' in reads[0] and '$orderby=Created desc,ID desc' in reads[0]
    profile_reads = [q for q in f.queries if '/items?' in q and PEOPLE['lists']['participants']['listId'] in q]
    assert all('Created' not in q and 'Email' not in q and 'DisplayName' not in q for q in profile_reads)


@pytest.mark.parametrize('missing', [True, False])
def test_missing_or_nonstring_created_rejects_incomplete_history(missing):
    f = Fake()
    if missing: del f.data['requests'][0]['Created']
    else: f.data['requests'][0]['Created'] = 123
    failure(execute(f), 'REQUEST_DATA_INCOMPLETE')


# Minimal metadata from owner preflight f7fd078d; no raw report/account data.
ACTUAL_REFERENCE_METADATA = [{'EnforceUniqueValues': False, 'Hidden': False, 'Indexed': False, 'InternalName': 'SenderParticipantId', 'ReadOnlyField': False, 'Required': True, 'SchemaXml': '<Field Type="Number" DisplayName="SenderParticipantId" Required="TRUE" EnforceUniqueValues="FALSE" Indexed="FALSE" Decimals="0" ID="{7909dcd2-f0b9-4158-9b9a-2017cb156fcd}" SourceID="{3d17485d-1dac-41f0-a1af-24e45daa4567}" StaticName="SenderParticipantId" Name="SenderParticipantId" ColName="float1" RowOrdinal="0"/>', 'TypeAsString': 'Number'}, {'EnforceUniqueValues': False, 'Hidden': False, 'Indexed': False, 'InternalName': 'RecipientParticipantId', 'ReadOnlyField': False, 'Required': True, 'SchemaXml': '<Field Type="Number" DisplayName="RecipientParticipantId" Required="TRUE" EnforceUniqueValues="FALSE" Indexed="FALSE" Decimals="0" ID="{e23db904-ddb4-451d-aa37-9b59b375b1ca}" SourceID="{3d17485d-1dac-41f0-a1af-24e45daa4567}" StaticName="RecipientParticipantId" Name="RecipientParticipantId" ColName="float2" RowOrdinal="0"/>', 'TypeAsString': 'Number'}, {'EnforceUniqueValues': False, 'Hidden': False, 'Indexed': False, 'InternalName': 'Status', 'ReadOnlyField': False, 'Required': True, 'SchemaXml': '<Field Type="Choice" DisplayName="Status" Required="TRUE" EnforceUniqueValues="FALSE" Indexed="FALSE" Format="Dropdown" FillInChoice="FALSE" ID="{9a1d79d6-44d3-4c17-8d85-c3c75e68c0df}" SourceID="{3d17485d-1dac-41f0-a1af-24e45daa4567}" StaticName="Status" Name="Status" ColName="nvarchar7" RowOrdinal="0"><Default>Pending</Default><CHOICES><CHOICE>Pending</CHOICE><CHOICE>Accepted</CHOICE><CHOICE>Declined</CHOICE><CHOICE>Cancelled</CHOICE></CHOICES></Field>', 'TypeAsString': 'Choice'}]


def corrected_actual_metadata():
    fields = deepcopy(ACTUAL_REFERENCE_METADATA)
    recipient = next(x for x in fields if x['InternalName'] == 'RecipientParticipantId')
    recipient['Required'] = False
    recipient['SchemaXml'] = recipient['SchemaXml'].replace('Required="TRUE"', 'Required="FALSE"')
    return fields


def test_actual_number_metadata_with_owner_setup_target_passes():
    f = Fake(); actual = corrected_actual_metadata(); names = {x['InternalName'] for x in actual}
    f.fields['requests'] = actual + [x for x in f.fields['requests'] if x['InternalName'] not in names]
    assert execute(f).response['resultcode'] == 'OK'


def test_actual_unconfigured_report_still_fails_closed():
    f = Fake(); f.fields['requests'] = deepcopy(ACTUAL_REFERENCE_METADATA)
    failure(execute(f), 'REQUEST_SCHEMA_UNVERIFIED')
    assert not any('/items?' in q for q in f.queries)


@pytest.mark.parametrize('field', ['SenderParticipantId', 'RecipientParticipantId'])
def test_former_participant_lookup_mapping_rejected(field):
    f = Fake(); target = next(x for x in f.fields['requests'] if x['InternalName'] == field)
    target.update(metadata(field[:-2], {'TypeAsString': 'Lookup', 'Required': field == 'SenderParticipantId', 'EnforceUniqueValues': False, 'Hidden': False, 'ReadOnlyField': False, 'LookupList': PEOPLE['lists']['participants']['listId']}))
    failure(execute(f), 'REQUEST_SCHEMA_UNVERIFIED')


@pytest.mark.parametrize('field', ['SenderParticipantId', 'RecipientParticipantId'])
@pytest.mark.parametrize('decimals', [None, '2', 'Auto'])
def test_wrong_or_missing_number_decimals_rejected(field, decimals):
    f = Fake(); target = next(x for x in f.fields['requests'] if x['InternalName'] == field)
    root = ET.fromstring(target['SchemaXml'])
    if decimals is None: del root.attrib['Decimals']
    else: root.set('Decimals', decimals)
    target['SchemaXml'] = ET.tostring(root, encoding='unicode')
    failure(execute(f), 'REQUEST_SCHEMA_UNVERIFIED')


@pytest.mark.parametrize('field', ['SenderParticipantId', 'RecipientParticipantId'])
def test_whole_float_number_references_normalize_before_keys_and_projection(field):
    f = Fake(); f.data['requests'][0][field] = float(f.data['requests'][0][field])
    r = execute(f); assert r.response['resultcode'] == 'OK'
    assert type(row(r, 1)['senderParticipantId']) is int and type(row(r, 1)['recipientParticipantId']) is int
    assert type(r.body('Data_requests')[0][field]) is int


@pytest.mark.parametrize('field', ['SenderParticipantId', 'RecipientParticipantId'])
def test_fractional_number_reference_rejected_before_keys_and_projection(field):
    f = Fake(); f.data['requests'][0][field] += 0.5
    r = execute(f); failure(r, 'REQUEST_DATA_INCOMPLETE')
    assert r.action_states['Data_requests'] == 'Skipped'


@pytest.mark.parametrize('style',['xml_nodes','scalar','value_array'])
def test_schema_attribute_values_do_not_depend_on_xpath_node_serialization(style):
    server=Fake();server.group();runner=ReaderRunner(server);runner.attribute_style=style
    runner.run(flow.build_actions(source(),PEOPLE,GROUPS,'scalar-attribute-regression'))
    assert runner.response['resultcode']=='OK'
    assert len(runner.outputs['requests_field_SenderParticipantId'])==1
    assert len(runner.outputs['requests_field_TargetGroup'])==1
    assert len(runner.outputs['memberships_field_Group'])==1


def test_legacy_attribute_node_comparison_rejects_valid_sender_but_scalar_check_accepts():
    server=Fake();actual=next(x for x in server.fields['requests'] if x['InternalName']=='SenderParticipantId')
    runner=ReaderRunner(server);ctx={'item':actual,'items':{}}
    old="@equals(first(union(xpath(xml(coalesce(item()?['SchemaXml'],'<Field/>')),'/Field/@Decimals'),createArray(''))),'0')"
    fixed="@equals(string(xpath(xml(if(empty(item()?['SchemaXml']),'<Field/>',item()?['SchemaXml'])),'string(/Field/@Decimals)')),'0')"
    assert not runner.expr(old,ctx)
    assert runner.expr(fixed,ctx)


def test_exact_owner_sender_field_without_fake_decimals_property_matches_metadata_gate():
    server=Fake();actual=json.loads((flow.ROOT/'tests/fixtures/my_requests_sender_metadata.json').read_text())
    assert 'Decimals' not in actual
    server.fields['requests']=[actual if x['InternalName']=='SenderParticipantId' else x for x in server.fields['requests']]
    result=execute(server);assert result.response['resultcode']=='OK'
    assert result.outputs['requests_field_SenderParticipantId']==[actual]


def test_empty_history_allows_unrelated_legacy_null_availability_without_defaults_or_writes():
    server=Fake();server.own=[{'Id':3}];server.data['requests']=[]
    for profile in server.data['profiles'][:2]:profile.update(ParticipationStatus=None,OpenToConnections=None)
    before=deepcopy(server.data);result=execute(server,actor=3)
    assert result.response['resultcode']=='OK' and public(result)==[]
    assert server.data==before
    assert result.body('Data_profiles')[0]['ParticipationStatus'] is None
    assert result.body('Data_profiles')[0]['OpenToConnections'] is None


@pytest.mark.parametrize('field',['Status','ParticipationStatus','OpenToConnections'])
def test_null_profile_availability_keeps_pending_history_and_cancel_decline_but_not_accept(field):
    server=Fake();server.data['profiles'][2][field]=None;before=deepcopy(server.data)
    result=execute(server);entry=row(result,2)
    assert result.response['resultcode']=='OK' and entry['availability']=='UnavailablePending'
    assert entry['actions']['decline'] and not entry['actions']['accept']
    assert row(result,1)['actions']['cancel'] and server.data==before


@pytest.mark.parametrize('field,value',[('ParticipationStatus',True),('ParticipationStatus','Unknown'),('OpenToConnections','true'),('Status',{})])
def test_malformed_availability_remains_a_data_error(field,value):
    server=Fake();server.data['profiles'][0][field]=value
    failure(execute(server),'DATA_INTEGRITY')
