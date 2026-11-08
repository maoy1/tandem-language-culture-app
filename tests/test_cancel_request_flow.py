"""Execute generated #63 WDL graph with adversarial fake SharePoint, not tenant proof."""
from copy import deepcopy
from collections import defaultdict
import json
import re
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile
import pytest
import test_discovery_flow as shared
from test_discovery_flow import FlowRunner
from test_coordination_fixture import walk
from scripts.power_automate import cancel_request_flow as cancel

ROOT = cancel.ROOT
PEOPLE = json.loads((ROOT / 'config/tenant_schema_mapping.json').read_text(encoding='utf-8'))
GROUPS = json.loads((ROOT / 'config/group_schema_mapping.json').read_text(encoding='utf-8'))
SOURCE = json.loads((ROOT / 'artifacts/tandem_discovery/TandemDiscovery-v2.definition.json').read_text(encoding='utf-8'))


class CancelRunner(FlowRunner):
    # The shared graph executor is reused unchanged; this WDL evaluator adds XML
    # metadata support. Every emitted expression is evaluated, not a Python model.
    def expr(self, text, context):
        tokens = re.findall(r"'(?:[^']|'')*'|-?\d+|[A-Za-z_][A-Za-z0-9_]*|[^\s]", text.lstrip('@'))
        at = 0
        def parse_xml(value):
            try: return ET.fromstring(value)
            except ET.ParseError as exc: raise ValueError('Invalid connector metadata XML') from exc
        def xpath(root, path):
            if path == 'string(/Field/@Decimals)': return root.attrib.get('Decimals', '')
            if path == 'string(/Field/@List)': return root.attrib.get('List', '')
            if path == 'string(/Field/@FillInChoice)': return root.attrib.get('FillInChoice', '')
            if path == '/Field/CHOICES/CHOICE/text()': return [n.text or '' for n in root.findall('./CHOICES/CHOICE')]
            raise AssertionError('Unexpected xpath: ' + path)
        def value():
            nonlocal at
            t = tokens[at]; at += 1
            if t.startswith("'"): result = t[1:-1].replace("''", "'")
            elif re.fullmatch(r'-?\d+', t): result = int(t)
            elif t in ['true', 'false', 'null']: result = {'true': True, 'false': False, 'null': None}[t]
            else:
                assert tokens[at] == '('; at += 1; args = []
                while tokens[at] != ')':
                    args.append(value())
                    if tokens[at] == ',': at += 1
                at += 1
                funcs = {'body': self.body, 'outputs': lambda n: self.outputs[n], 'variables': lambda n: self.variables[n],
                         'item': lambda: context['item'], 'items': lambda n: context['items'][n],
                         'and': lambda *v: all(v), 'or': lambda *v: any(v), 'not': lambda v: not v,
                         'equals': lambda a,b: a == b, 'greater': lambda a,b: a > b, 'less': lambda a,b: a < b,
                         'lessOrEquals': lambda a,b: a <= b, 'length': len, 'empty': lambda v: v is None or v == '' or v == [],
                         'if': lambda c,a,b: a if c else b, 'intersection': lambda a,b: list(set(a) & set(b)),
                         'coalesce': lambda *v: next((x for x in v if x is not None), None),
                         'int': int, 'trim': lambda s: s.strip(), 'replace': lambda s,a,b: s.replace(a,b), 'toLower': lambda s: s.lower(), 'json': json.loads,
                         'first': lambda a: a[0], 'concat': lambda *v: ''.join(str(x) for x in v),
                         'string': lambda v: json.dumps(v,separators=(',',':')) if isinstance(v,(dict,list,bool)) else str(v),
                         'createArray': lambda *v: list(v), 'div': lambda a,b: a // b,
                         'workflow': lambda: {'run': {'name': 'local-graph-only'}}, 'triggerBody': lambda: context['triggerBody'],
                         'xml': parse_xml, 'xpath': xpath}
                result = funcs[t](*args)
            while at < len(tokens) and tokens[at] == '?':
                at += 1; assert tokens[at] == '['; at += 1; key = value(); assert tokens[at] == ']'; at += 1
                result = result.get(key) if result is not None else None
            return result
        result = value()
        assert at == len(tokens), (text, tokens[at:])
        return result


@pytest.fixture(autouse=True)
def validate_patterns(monkeypatch):
    original = shared.validate
    def checked(value, schema):
        original(value, schema)
        if isinstance(value, str) and 'pattern' in schema:
            assert re.fullmatch(schema['pattern'], value)
        if isinstance(value, str): assert len(value) <= schema.get('maxLength', 10**9)
    monkeypatch.setattr(shared, 'validate', checked)


def fields(spec):
    rows = []
    for name, rule in spec.items():
        xml = ET.Element('Field', Name=name, Type=rule['type'], FillInChoice='FALSE')
        if 'decimals' in rule: xml.set('Decimals', str(rule['decimals']))
        if rule.get('target'): xml.set('List', '{' + rule['target'] + '}')
        if rule.get('choices'):
            choices = ET.SubElement(xml, 'CHOICES')
            for c in rule['choices']: ET.SubElement(choices, 'CHOICE').text = c
        rows.append({'InternalName': name, 'TypeAsString': rule['type'], 'Required': rule['required'],
                     'Hidden': False, 'ReadOnlyField': False, 'EnforceUniqueValues': rule.get('unique', False),
                     'Indexed': rule.get('unique', False), 'SchemaXml': ET.tostring(xml, encoding='unicode')})
    return rows


class Fake:
    def __init__(self, kind='Personal'):
        self.fields = fields(cancel.expected_fields(PEOPLE['lists']['participants']['listId'], GROUPS['lists']['groups']['listId']))
        self.people_fields = fields({'Participantaccount': {'type': 'User', 'required': True, 'unique': True}})
        self.actor_rows = [{'Id': 3}]
        self.row = {'Id': 71, 'SenderParticipantId': 3, 'RecipientParticipantId': 2 if kind == 'Personal' else None,
                    'TargetGroupId': None if kind == 'Personal' else 9, 'RequestType': kind, 'Status': 'Pending',
                    'SendOperationKey': ('personal' if kind == 'Personal' else 'group') + ':3:11111111-1111-4111-8111-111111111111',
                    'ConnectionKey': 'open:person:2:3' if kind == 'Personal' else 'open:group:9:participant:3',
                    'WinningOperationKey': None, 'OperationComplete': False,
                    '__metadata': {'etag': '"1"', 'type': 'SP.Data.ConnectionRequestsListItem'},
                    'UnselectedPrivate': 'PRIVATE_EMAIL_ACCOUNT'}
        self.calls = []; self.writes = []; self.mode = None; self.page = None; self.fail = None
        self.read_count = 0; self.race_status = None; self.after_tamper = None
    def settled(self, status, winner='other:decision', complete=True):
        self.row.update(Status=status, WinningOperationKey=winner, OperationComplete=complete)
        if complete: self.row['ConnectionKey'] = 'history:request:71'
        self.row['__metadata']['etag'] = '"2"'
    def request(self, p):
        uri = p['parameters/uri']; method = p['parameters/method']; self.calls.append((method, uri))
        def response(body, status=200): return {'statusCode': status, 'body': body}
        if self.fail and self.fail in uri: return response({'PRIVATE_BACKEND': 'SECRET'}, 503)
        if method == 'POST':
            self.writes.append(deepcopy(p))
            if self.race_status:
                self.settled(self.race_status, complete=self.race_status != 'Accepted')
            if p['parameters/headers']['IF-MATCH'] != self.row['__metadata']['etag']:
                return response({'error': 'PRIVATE_412'}, 412)
            if self.mode in ['502', 'timeout', 'duplicate502', '412pending']:
                return response({'error': {'code': '-2130575169, Microsoft.SharePoint.SPDuplicateValuesFoundException'}
                                 if self.mode == 'duplicate502' else 'PRIVATE_GATEWAY'}, 412 if self.mode == '412pending' else 502)
            self.row.update(deepcopy(p['parameters/body'])); self.row['__metadata']['etag'] = '"2"'
            return response({}, 502 if self.mode == 'commit502' else 204)
        if '/currentuser' in uri: return response({'d': {'Id': 103}})
        if '/fields?' in uri:
            role = 'requests' if cancel.REQUESTS in uri else 'people'
            obj = {'d': {'results': deepcopy(self.fields if role == 'requests' else self.people_fields)}}
            if self.page == role: obj['d']['__next'] = 'NEXT_PRIVATE'
            return response(obj)
        if 'ParticipantaccountId eq' in uri:
            obj = {'d': {'results': self.actor_rows}}
            if self.page == 'actor': obj['d']['__next'] = 'NEXT_PRIVATE'
            return response(obj)
        if '/items(' in uri:
            self.read_count += 1
            if self.read_count > 1:
                if self.mode == 'readbackFail': return response({'error': 'PRIVATE_READ'}, 503)
                if self.after_tamper: self.row.update(self.after_tamper)
            return response({'d': deepcopy(self.row)})
        return response({'d': {'Id': cancel.REQUESTS, 'ListItemEntityTypeFullName': 'SP.Data.ConnectionRequestsListItem'}})


def execute(server=None, inputs=None, actions=None):
    server = server or Fake()
    runner = CancelRunner(server)
    runner.run(actions or cancel.build_actions(SOURCE, PEOPLE, GROUPS), {'items': {}, 'triggerBody': inputs or {'number': 3, 'number_1': 71}})
    assert runner.response is not None
    assert not any(s in json.dumps(runner.response) for s in ['PRIVATE', 'Participantaccount', 'SendOperationKey', 'ConnectionKey', 'WinningOperationKey'])
    return runner


@pytest.mark.parametrize('kind', ['Personal', 'Group'])
def test_pending_atomic_cancel_replay_and_parties_preserved(kind):
    server = Fake(kind); before = deepcopy(server.row)
    r = execute(server)
    assert r.response['resultcode'] == 'CANCELLED' and r.response['success'] and not r.response['replay']
    assert server.row['Status'] == 'Cancelled' and server.row['OperationComplete']
    assert server.row['ConnectionKey'] == 'history:request:71' and server.row['WinningOperationKey'] == 'cancel:3:request:71'
    assert all(server.row[f] == v for f,v in before.items() if f not in ['Status', 'ConnectionKey', 'WinningOperationKey', 'OperationComplete', '__metadata'])
    payload = server.writes[0]['parameters/body']
    assert set(payload) == {'__metadata', 'Status', 'ConnectionKey', 'WinningOperationKey', 'OperationComplete'}
    replay = execute(server)
    assert replay.response['success'] and replay.response['replay'] and len(server.writes) == 1


@pytest.mark.parametrize('status,done', [('Accepted', False), ('Accepted', True), ('Declined', True), ('Cancelled', True)])
def test_terminal_replay_truthful_and_no_write(status, done):
    s = Fake(); s.settled(status, complete=done); r = execute(s)
    assert r.response['resultcode'] == ('ACCEPTED_INCOMPLETE' if not done else 'ALREADY_DECIDED')
    assert r.response['currentstatus'] == status and r.response['operationcomplete'] == done
    assert not r.response['success'] and not s.writes


@pytest.mark.parametrize('status', ['Accepted', 'Declined', 'Cancelled'])
def test_race_412_rereads_winner_and_never_reverses(status):
    s = Fake(); s.race_status = status; r = execute(s)
    assert r.response['resultcode'] == ('ACCEPTED_INCOMPLETE' if status == 'Accepted' else 'ALREADY_DECIDED')
    assert r.response['currentstatus'] == status and len(s.writes) == 1 and s.read_count == 2


@pytest.mark.parametrize('mode,code', [('502','OUTCOME_UNKNOWN'), ('timeout','OUTCOME_UNKNOWN'), ('duplicate502','OUTCOME_UNKNOWN'),
                                       ('412pending','RETRY_REQUIRED'), ('readbackFail','OUTCOME_UNKNOWN'), ('commit502','CANCELLED')])
def test_unknown_writes_never_claim_no_effect_or_duplicate(mode, code):
    s = Fake(); s.mode = mode; r = execute(s)
    assert r.response['resultcode'] == code and r.response['success'] == (code == 'CANCELLED')
    assert len(s.writes) == 1


@pytest.mark.parametrize('mutate', [lambda s: s.row.update(SenderParticipantId=2), lambda s: s.actor_rows.clear(),
                                   lambda s: s.actor_rows.append({'Id':3}), lambda s: s.actor_rows.__setitem__(0, {'Id': 2})])
def test_tamper_or_nonunique_caller_never_reveals_terminal(mutate):
    s = Fake(); s.settled('Accepted'); mutate(s); r = execute(s)
    assert r.response['resultcode'] == 'UNAUTHORIZED' and r.response['currentstatus'] == '' and not s.writes


@pytest.mark.parametrize('inputs', [{'number':3,'number_1':0}, {'number':3,'number_1':1.5}, {'number':3,'number_1':'71'},
                                  {'number':3,'number_1':71,'suppliedactor':3}, {'number':0,'number_1':71}, {'number':3},
                                  {'number':3,'number_1':2147483648}])
def test_invalid_inputs_never_read(inputs):
    s = Fake(); r = execute(s, inputs); assert r.response['resultcode'] == 'INVALID_INPUT' and not s.calls


@pytest.mark.parametrize('page', ['requests','people','actor'])
def test_incomplete_reads_fail_closed(page):
    s = Fake(); s.page = page; r = execute(s)
    assert r.response['resultcode'] in ['REQUEST_SCHEMA_UNVERIFIED','UNAUTHORIZED'] and not s.writes


@pytest.mark.parametrize('field,prop,value', [
    ('SenderParticipantId','Required',False), ('RecipientParticipantId','Required',True), ('TargetGroup','TypeAsString','LookupMulti'),
    ('SendOperationKey','EnforceUniqueValues',False), ('SendOperationKey','Indexed',False), ('ConnectionKey','Required',False),
    ('ConnectionKey','Indexed',False), ('Status','ReadOnlyField',True), ('WinningOperationKey','TypeAsString','Note'),
    ('OperationComplete','TypeAsString','Text'), ('RequestType','Hidden',True), ('TargetGroup','SchemaXml','<Field List="wrong"/>'),
    ('Status','SchemaXml','<Field><CHOICES><CHOICE>Pending</CHOICE></CHOICES></Field>'),
    ('RequestType','SchemaXml','<Field FillInChoice="TRUE"><CHOICES><CHOICE>Personal</CHOICE><CHOICE>Group</CHOICE></CHOICES></Field>')])
def test_shared_schema_mismatch_blocks_mapping(field,prop,value):
    s = Fake(); next(f for f in s.fields if f['InternalName'] == field)[prop] = value
    r = execute(s); assert r.response['resultcode'] == 'REQUEST_SCHEMA_UNVERIFIED' and not s.writes and s.read_count == 0


@pytest.mark.parametrize('variant', ['missing','duplicate','overflow','actorUnique','actorRequired','nullable'])
def test_schema_missing_duplicate_overbound_and_identity_settings(variant):
    s = Fake()
    if variant == 'missing': s.fields.pop()
    if variant == 'duplicate': s.fields.append(deepcopy(s.fields[0]))
    if variant == 'overflow': s.fields += [{'InternalName':'unrelated'}] * 501
    if variant == 'actorUnique': s.people_fields[0]['EnforceUniqueValues'] = False
    if variant == 'actorRequired': s.people_fields[0]['Required'] = False
    if variant == 'nullable': s.fields[1]['Required'] = True
    r = execute(s); assert r.response['resultcode'] == 'REQUEST_SCHEMA_UNVERIFIED' and not s.writes


@pytest.mark.parametrize('update', [
    {'RecipientParticipantId':None}, {'TargetGroupId':9}, {'RecipientParticipantId':3}, {'ConnectionKey':'open:person:3:2'},
    {'SendOperationKey':''}, {'SendOperationKey':'   '}, {'OperationComplete':True}, {'WinningOperationKey':'other'},
    {'OperationComplete':None}, {'Status':'Legacy'}, {'__metadata': {'type':'wrong','etag':'*'}}])
def test_legacy_or_malformed_rows_preserved_without_guessing(update):
    s = Fake(); s.row.update(update); before = deepcopy(s.row); r = execute(s)
    assert r.response['resultcode'] in ['REQUEST_INTEGRITY'] and not s.writes and s.row == before


@pytest.mark.parametrize('update', [{'RecipientParticipantId':4}, {'SendOperationKey':'personal:3:22222222-2222-4222-8222-222222222222'}, {'SenderParticipantId':4}])
def test_readback_tamper_never_proves_success(update):
    s = Fake(); s.after_tamper = update; r = execute(s)
    assert r.response['resultcode'] == 'REQUEST_INTEGRITY' and not r.response['success']


def test_backend_failures_sanitized_before_write():
    s = Fake(); s.fail = '/currentuser'; r = execute(s)
    assert r.response['resultcode'] == 'READ_OR_DATA_FAILED' and not s.writes


def test_retry_after_unknown_uses_same_exact_decision():
    s = Fake(); s.mode = '502'; assert execute(s).response['resultcode'] == 'OUTCOME_UNKNOWN'
    s.mode = None; assert execute(s).response['success']
    assert execute(s).response['replay'] and len(s.writes) == 2


def test_skipped_write_cannot_readback_or_override_precondition():
    actions = cancel.build_actions(SOURCE, PEOPLE, GROUPS)
    branch = actions['Cancel_work']['actions']['Choose_pending']['actions']
    branch['Mark_write_attempt']['inputs']['value'] = '@div(1,0)'
    s = Fake(); r = execute(s, actions=actions)
    assert s.read_count == 1 and not s.writes and r.action_states['Read_after_CAS'] == 'Skipped'
    assert r.response['resultcode'] == 'READ_OR_DATA_FAILED'


def test_graph_global_names_etag_single_write_and_invoker_guards():
    actions = cancel.build_actions(SOURCE, PEOPLE, GROUPS); nodes = list(walk(actions))
    assert len({n for n,a in nodes}) == len(nodes)
    assert cancel.measure(actions)['actions'] <= 500 and cancel.measure(actions)['maximumActionDepth'] <= 8
    writes = []
    for n,a in nodes:
        if a['type'] != 'OpenApiConnection': continue
        assert a['inputs']['authentication']['type'] == 'Raw'
        assert a['inputs']['retryPolicy'] == {'type':'none'}
        if a['inputs']['parameters']['parameters/method'] != 'GET': writes.append(a)
    assert len(writes) == 1
    assert writes[0]['inputs']['parameters']['parameters/headers']['IF-MATCH'] == "@body('Before_row')?['__metadata']?['etag']"
    original = deepcopy(SOURCE); original['properties']['connectionReferences']['shared_sharepointonline']['source'] = 'Embedded'
    with pytest.raises(ValueError, match='Invoker'): cancel.build_actions(original, PEOPLE, GROUPS)


def test_baseline_package_and_actual_trigger_contract(tmp_path):
    output = tmp_path/'cancel.zip'; review = cancel.build_package(ROOT/'artifacts/tandem_discovery/TandemDiscovery-v2.definition.json', output)
    assert not review['sourceTriggerPreserved'] and review['globalActionNamesUnique']
    with ZipFile(output) as z:
        doc = json.loads(z.read(next(n for n in z.namelist() if n.endswith('/definition.json'))))
        manifest = json.loads(z.read('manifest.json'))
        assert doc['properties']['connectionReferences']['shared_sharepointonline']['source'] == 'Invoker'
        assert next(v for v in manifest['resources'].values() if v['type']=='Microsoft.Flow/flows')['suggestedCreationType']=='New'
    with pytest.raises(FileExistsError): cancel.build_package(ROOT/'artifacts/tandem_discovery/TandemDiscovery-v2.definition.json', output)
    trigger_source = deepcopy(SOURCE)
    trigger_source['properties']['definition']['triggers'] = deepcopy(doc['properties']['definition']['triggers'])
    path = tmp_path/'actual.json'; path.write_text(json.dumps(trigger_source), encoding='utf-8')
    review = cancel.build_package(path, tmp_path/'preserved.zip')
    assert review['sourceTriggerPreserved'] and review['triggerDelta'] == 'none'

@pytest.mark.parametrize('key', ['Id','SendOperationKey','WinningOperationKey','OperationComplete','__metadata'])
def test_missing_historical_data_never_fabricates_receipt(key):
    s=Fake(); s.row.pop(key); before=deepcopy(s.row); r=execute(s)
    assert r.response['resultcode']=='REQUEST_INTEGRITY' and not s.writes and s.row==before


@pytest.mark.parametrize('xml', ['not xml','<Field FillInChoice="unknown"><CHOICES><CHOICE>Personal</CHOICE><CHOICE>Group</CHOICE></CHOICES></Field>'])
def test_invalid_schema_xml_is_unverified(xml):
    s=Fake(); next(f for f in s.fields if f['InternalName']=='RequestType')['SchemaXml']=xml
    r=execute(s)
    assert r.response['resultcode']=='REQUEST_SCHEMA_UNVERIFIED' and not s.writes


def test_same_cancel_wins_before_our_cas_and_changed_revision_is_reread():
    s=Fake(); native=s.request
    def request(p):
        if p['parameters/method']=='POST':
            s.settled('Cancelled',winner='cancel:3:request:71')
        return native(p)
    s.request=request; r=execute(s)
    assert r.response['success'] and r.response['currentstatus']=='Cancelled' and len(s.writes)==1
    assert not r.response['outcomeunknown']


def test_same_sender_can_cancel_while_paused_no_profile_availability_read():
    s=Fake(); execute(s)
    assert not any('ParticipationStatus' in uri or 'OpenToConnections' in uri or '/groups' in uri for method,uri in s.calls)
    assert all(cancel.REQUESTS in uri for method,uri in s.calls if method!='GET')


def test_post_write_integrity_failure_marks_outcome_unknown():
    s=Fake(); s.after_tamper={'OperationComplete':False}; r=execute(s)
    assert r.response['resultcode']=='REQUEST_INTEGRITY' and r.response['writeattempted'] and r.response['outcomeunknown']
    assert not r.response['success'] and r.response['currentstatus']==''


def test_canonical_source_raw_auth_is_preserved_on_every_http_action():
    _,auth=cancel.source_adapter(SOURCE,PEOPLE)
    for name,action in walk(cancel.build_actions(SOURCE,PEOPLE,GROUPS)):
        if action['type']=='OpenApiConnection': assert action['inputs']['authentication']==auth


def test_global_duplicate_names_rejected_even_across_else_branches():
    actions=cancel.build_actions(SOURCE,PEOPLE,GROUPS)
    branches=actions['Cancel_work']['actions']['Choose_pending']
    branches['else']['actions']['Mark_write_attempt']={'type':'Compose','inputs':'invalid','runAfter':{}}
    with pytest.raises(ValueError,match='Duplicate action'): cancel.measure(actions)


# Exact observed Number metadata; no private attachment/runtime dependency.
OBSERVED_NUMBER_FIELDS = [{'InternalName': 'SenderParticipantId', 'TypeAsString': 'Number', 'Required': True, 'Hidden': False, 'ReadOnlyField': False, 'EnforceUniqueValues': False, 'Indexed': False, 'SchemaXml': '<Field Type="Number" DisplayName="SenderParticipantId" Required="TRUE" EnforceUniqueValues="FALSE" Indexed="FALSE" Decimals="0" ID="{7909dcd2-f0b9-4158-9b9a-2017cb156fcd}" SourceID="{3d17485d-1dac-41f0-a1af-24e45daa4567}" StaticName="SenderParticipantId" Name="SenderParticipantId" ColName="float1" RowOrdinal="0"/>'}, {'InternalName': 'RecipientParticipantId', 'TypeAsString': 'Number', 'Required': True, 'Hidden': False, 'ReadOnlyField': False, 'EnforceUniqueValues': False, 'Indexed': False, 'SchemaXml': '<Field Type="Number" DisplayName="RecipientParticipantId" Required="TRUE" EnforceUniqueValues="FALSE" Indexed="FALSE" Decimals="0" ID="{e23db904-ddb4-451d-aa37-9b59b375b1ca}" SourceID="{3d17485d-1dac-41f0-a1af-24e45daa4567}" StaticName="RecipientParticipantId" Name="RecipientParticipantId" ColName="float2" RowOrdinal="0"/>'}]

@pytest.mark.parametrize('kind', ['Personal','Group'])
def test_observed_number_metadata_passes_after_explicit_recipient_optional_setup(kind):
    s=Fake(kind)
    for field in OBSERVED_NUMBER_FIELDS:
        observed=deepcopy(field)
        if observed['InternalName']=='RecipientParticipantId':
            observed['Required']=False
            xml=ET.fromstring(observed['SchemaXml']); xml.set('Required','FALSE')
            observed['SchemaXml']=ET.tostring(xml,encoding='unicode')
        index=next(i for i,f in enumerate(s.fields) if f['InternalName']==observed['InternalName'])
        s.fields[index]=observed
    assert execute(s).response['success'] and len(s.writes)==1


def test_actual_pre_setup_metadata_is_still_blocked_without_writes():
    s=Fake()
    s.fields=deepcopy(OBSERVED_NUMBER_FIELDS)+[f for f in s.fields if f['InternalName']=='Status']
    r=execute(s)
    assert r.response['resultcode']=='REQUEST_SCHEMA_UNVERIFIED' and not s.writes and s.read_count==0


@pytest.mark.parametrize('field', ['SenderParticipantId','RecipientParticipantId'])
@pytest.mark.parametrize('old_name', [False,True])
def test_former_lookup_sender_recipient_metadata_is_rejected(field,old_name):
    s=Fake(); f=next(f for f in s.fields if f['InternalName']==field)
    f.update(TypeAsString='Lookup',SchemaXml='<Field Type="Lookup" List="{'+PEOPLE['lists']['participants']['listId']+'}"/>')
    if old_name: f['InternalName']=field.removesuffix('Id')
    r=execute(s)
    assert r.response['resultcode']=='REQUEST_SCHEMA_UNVERIFIED' and not s.writes


@pytest.mark.parametrize('field', ['SenderParticipantId','RecipientParticipantId'])
@pytest.mark.parametrize('decimals', ['2','Auto',None])
def test_number_metadata_wrong_or_missing_decimals_fails_closed(field,decimals):
    s=Fake(); f=next(f for f in s.fields if f['InternalName']==field)
    xml=ET.fromstring(f['SchemaXml'])
    if decimals is None: xml.attrib.pop('Decimals')
    else: xml.set('Decimals',decimals)
    f['SchemaXml']=ET.tostring(xml,encoding='unicode')
    r=execute(s)
    assert r.response['resultcode']=='REQUEST_SCHEMA_UNVERIFIED' and not s.writes


@pytest.mark.parametrize('kind', ['Personal','Group'])
def test_whole_float_number_refs_preserve_authority_and_canonical_keys(kind):
    s=Fake(kind); s.row['SenderParticipantId']=3.0
    if kind=='Personal': s.row['RecipientParticipantId']=2.0
    r=execute(s)
    assert r.response['success'] and s.row['WinningOperationKey']=='cancel:3:request:71'
    assert s.row['SenderParticipantId']==3.0 and len(s.writes)==1


@pytest.mark.parametrize('field,value', [('SenderParticipantId',3.5),('RecipientParticipantId',2.5),('RecipientParticipantId',0.5)])
def test_fractional_number_refs_never_cancel(field,value):
    s=Fake(); s.row[field]=value; r=execute(s)
    assert not r.response['success'] and not s.writes
    assert r.response['resultcode'] in ['UNAUTHORIZED','REQUEST_INTEGRITY']
