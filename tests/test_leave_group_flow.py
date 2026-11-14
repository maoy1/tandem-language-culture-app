"""Execute #14 emitted WDL against adversarial SharePoint fakes; no tenant proof."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from uuid import uuid4
from zipfile import ZipFile

import pytest
import test_discovery_flow as shared
from test_discovery_flow import FlowRunner
from scripts.power_automate import leave_group_flow as leave

ROOT = leave.ROOT
PEOPLE = json.loads((ROOT/'config/tenant_schema_mapping.json').read_text())
GROUPS = json.loads((ROOT/'config/group_schema_mapping.json').read_text())
SOURCE = json.loads((ROOT/'artifacts/tandem_discovery/TandemDiscovery-v2.definition.json').read_text())
RECEIPT_ID = '14141414-1414-4414-8414-141414141414'
GROUPS['lists']['receipts'] = {'listId': RECEIPT_ID, 'schemaVerified': True}
INPUT = {'number': 3, 'number_1': 10, 'number_2': 20, 'text': '11111111-1111-4111-8111-111111111111'}


class Runner(FlowRunner):
    def parse_content(self, value, schema):
        return json.loads(value) if isinstance(value, str) and schema.get('type') != 'string' else value

    def expr(self, text, context):
        tokens = re.findall(r"'(?:[^']|'')*'|-?\d+|[A-Za-z_][A-Za-z0-9_]*|[^\s]", text.lstrip('@'))
        at = 0
        def value():
            nonlocal at
            t = tokens[at]; at += 1
            if t.startswith("'"): result = t[1:-1].replace("''", "'")
            elif re.fullmatch(r'-?\d+', t): result = int(t)
            elif t in ['true','false','null']: result = {'true':True,'false':False,'null':None}[t]
            else:
                assert tokens[at] == '('; at += 1; args = []
                while tokens[at] != ')':
                    args.append(value())
                    if tokens[at] == ',': at += 1
                at += 1
                funcs = {'body':self.body,'outputs':lambda n:self.outputs[n],'variables':lambda n:self.variables[n],
                    'item':lambda:context['item'],'items':lambda n:context['items'][n],
                    'and':lambda *v:all(v),'or':lambda *v:any(v),'not':lambda v:not v,
                    'equals':lambda a,b:a==b,'greater':lambda a,b:a>b,'lessOrEquals':lambda a,b:a<=b,
                    'length':len,'empty':lambda v:v is None or v=='' or v==[],
                    'if':lambda c,a,b:a if c else b,'coalesce':lambda *v:next((x for x in v if x is not None),None),
                    'int':int,'toLower':str.lower,'json':json.loads,'first':lambda a:a[0],
                    'concat':lambda *v:''.join(str(x) for x in v),
                    'string':lambda v:json.dumps(v,separators=(',',':')) if isinstance(v,(dict,list,bool)) else str(v),
                    'div':lambda a,b:a//b,'sub':lambda a,b:a-b,'split':lambda s,sep:s.split(sep),
                    'guid':lambda:str(uuid4()),'utcNow':lambda format_=None:'2026-11-14T15:00:00Z',
                    'workflow':lambda:{'run':{'name':'local-only'}},'triggerBody':lambda:context['triggerBody']}
                result = funcs[t](*args)
            while at < len(tokens) and tokens[at] == '?':
                at += 1; assert tokens[at] == '['; at += 1; key = value(); assert tokens[at] == ']'; at += 1
                result = (result[key] if isinstance(result,list) else result.get(key)) if result is not None else None
            return result
        result = value()
        assert at == len(tokens), (text,tokens[at:])
        return result


@pytest.fixture(autouse=True)
def strict_schemas(monkeypatch):
    validate = shared.validate
    def checked(value, schema):
        validate(value,schema)
        if isinstance(value,str):
            assert len(value) <= schema.get('maxLength',10**9)
            if 'pattern' in schema: assert re.fullmatch(schema['pattern'],value)
    monkeypatch.setattr(shared,'validate',checked)


def meta(kind, version=1):
    return {'type':'SP.Data.'+kind+'ListItem','etag':'"'+str(version)+'"'}


class Fake:
    def __init__(self):
        self.actor_rows=[{'Id':3}]
        self.group={'Id':10,'Capacity':3,'State':'Closed','SetupComplete':True,'SourceRequestId':70,
                    'WriteOwner':'','__metadata':meta('Groups'),'Title':'PRESERVE'}
        self.members={
            20:{'Id':20,'GroupId':10,'ParticipantId':3,'MembershipStatus':'Active',
                'MembershipKey':'request:71:participant:3','JoinedAt':'2026-11-01T00:00:00Z','LeftAt':None,'__metadata':meta('Members')},
            21:{'Id':21,'GroupId':10,'ParticipantId':2,'MembershipStatus':'Active',
                'MembershipKey':'request:70:participant:2','JoinedAt':'2026-11-01T00:00:00Z','LeftAt':None,'__metadata':meta('Members')},
            22:{'Id':22,'GroupId':10,'ParticipantId':9,'MembershipStatus':'Active',
                'MembershipKey':'request:72:participant:9','JoinedAt':'2026-11-01T00:00:00Z','LeftAt':None,'__metadata':meta('Members')},
            23:{'Id':23,'GroupId':10,'ParticipantId':4,'MembershipStatus':'Left',
                'MembershipKey':'request:69:participant:4','JoinedAt':'2026-10-01T00:00:00Z','LeftAt':'2026-10-02T00:00:00Z','__metadata':meta('Members')}}
        self.requests={
            70:{'Id':70,'Status':'Accepted','OperationComplete':True,'RequestType':'Personal',
                'SenderParticipantId':2,'RecipientParticipantId':1,'TargetGroupId':None},
            71:{'Id':71,'Status':'Accepted','OperationComplete':True,'RequestType':'Group',
                'SenderParticipantId':3,'RecipientParticipantId':None,'TargetGroupId':10},
            72:{'Id':72,'Status':'Accepted','OperationComplete':False,'RequestType':'Group',
                'SenderParticipantId':9,'RecipientParticipantId':None,'TargetGroupId':10}}
        self.receipts={}; self.calls=[]; self.writes=[]; self.faults={}; self.paged=None
        self.read_fail=None; self.after_leave=False; self.after_complete=False; self.tamper_after=None

    def request(self,p):
        uri=p['parameters/uri']; method=p['parameters/method']; self.calls.append(deepcopy(p))
        def out(value,status=200): return {'statusCode':status,'body':deepcopy(value)}
        if self.read_fail and method=='GET' and self.read_fail in uri:
            return out({'error':'PRIVATE_BACKEND'},503)
        if '/currentuser' in uri: return out({'d':{'Id':103}})
        if 'ParticipantaccountId eq' in uri: return out({'d':{'results':self.actor_rows}})
        role=next(k for k,id_ in [('groups',GROUPS['lists']['groups']['listId']),
            ('members',GROUPS['lists']['members']['listId']),('requests',leave.REQUESTS),
            ('receipts',RECEIPT_ID)] if id_ in uri)
        data={'groups':{10:self.group},'members':self.members,'requests':self.requests,'receipts':self.receipts}[role]
        m=re.search(r'/items\((\d+)\)',uri)
        if method=='POST':
            payload=deepcopy(p['parameters/body'])
            tag=('Create_receipt' if role=='receipts' and m is None else
                 'Complete_receipt' if role=='receipts' else
                 'Leave_CAS' if role=='members' else
                 'Release_group' if payload['WriteOwner']=='' else 'Claim_group')
            self.writes.append((tag,deepcopy(p)))
            fault=self.faults.get(tag)
            if fault in ['fail','timeout','duplicate502']: return out({'error':'PRIVATE_GATEWAY'},504 if fault=='timeout' else 502)
            if m:
                row=data[int(m[1])]
                if fault=='stale': row['__metadata']['etag']='"99"'
                if p['parameters/headers']['IF-MATCH']!=row['__metadata']['etag']:
                    return out({'error':'PRIVATE_412'},412)
                revision=int(row['__metadata']['etag'].strip('"'))+1
                row.update(payload)
                row['__metadata']['etag']='"'+str(revision)+'"'
            else:
                if any(r['OperationKey']==payload['OperationKey'] for r in data.values()):
                    return out({'error':'PRIVATE_DUPLICATE'},502)
                row={'Id':len(data)+1,'ResultJson':None,**payload,'__metadata':meta('Receipts')}
                data[row['Id']]=row
            if tag=='Leave_CAS': self.after_leave=True
            if tag=='Complete_receipt': self.after_complete=True
            return out({},502 if fault=='commit502' else 204)
        if m:
            if role=='members' and self.after_leave:
                if self.faults.get('Member_readback')=='fail':return out({'error':'PRIVATE_READ'},503)
                if self.tamper_after:self.members[20].update(self.tamper_after)
            return out({'d':data.get(int(m[1]),{})},200 if int(m[1]) in data else 404)
        if '/items?' in uri:
            values=list(data.values())
            if role=='receipts':
                if self.after_complete and self.faults.get('Receipt_readback')=='fail':return out({'error':'PRIVATE_READ'},503)
                key=re.search(r"OperationKey eq '([^']+)'",uri)[1]
                values=[v for v in values if v['OperationKey']==key]
            if role=='members':values=[v for v in values if v['GroupId']==10]
            result={'d':{'results':values}}
            if self.paged==role: result['d']['__next']='PRIVATE_NEXT'
            return out(result)
        return out({'d':{'Id':RECEIPT_ID,'ListItemEntityTypeFullName':'SP.Data.ReceiptsListItem'}})


def execute(server=None, inputs=None, actions=None, groups=None):
    server=server or Fake()
    runner=Runner(server)
    runner.run(actions or leave.build_actions(SOURCE,PEOPLE,groups or GROUPS,'local-build'),
               {'items':{},'triggerBody':INPUT if inputs is None else inputs})
    assert runner.response is not None
    assert not any(s in json.dumps(runner.response) for s in ['PRIVATE','Participantaccount','WriteOwner','AttemptToken'])
    return runner


def result(r):
    return json.loads(r.response['resultjson'])


def tags(s):
    return [n for n,p in s.writes]


@pytest.mark.parametrize('state',['Open','Closed','Ended'])
def test_explicit_leave_preserves_state_and_every_other_episode_and_setting(state):
    s=Fake(); s.group['State']=state; before=deepcopy((s.group,s.members,s.requests))
    r=execute(s)
    assert r.response['success'], (r.response,r.action_states)
    assert r.response['resultcode']=='LEFT' and not r.response['replay']
    assert result(r)['membercount']==2 and result(r)['freeslots']==1  # provisional 22 counted
    assert s.group['State']==state and s.group['WriteOwner']==''
    assert all(s.group[k]==v for k,v in before[0].items() if k not in ['WriteOwner','__metadata'])
    assert all(s.members[k]==v for k,v in before[1].items() if k!=20)
    assert s.requests==before[2]
    assert s.members[20]['MembershipStatus']=='Left' and s.members[20]['LeftAt']=='2026-11-14T15:00:00Z'
    assert {k:v for k,v in s.members[20].items() if k not in ['MembershipStatus','LeftAt','__metadata']}=={
        k:v for k,v in before[1][20].items() if k not in ['MembershipStatus','LeftAt','__metadata']}
    assert tags(s)==['Create_receipt','Claim_group','Leave_CAS','Complete_receipt','Release_group']


def test_same_intent_replay_is_saved_history_and_second_new_leave_is_harmless():
    s=Fake(); first=execute(s); writes=len(s.writes)
    s.group['State']='Ended'; s.group['Capacity']=10
    replay=execute(s)
    assert replay.response['success'] and replay.response['replay']
    assert result(replay)==result(first) and len(s.writes)==writes
    fresh=execute(s,{**INPUT,'text':str(uuid4())})
    assert not fresh.response['success'] and fresh.response['resultcode']=='ALREADY_LEFT'
    assert len(s.writes)==writes


@pytest.mark.parametrize('change',[
    lambda s:s.actor_rows.clear(),lambda s:s.actor_rows.append({'Id':3}),
    lambda s:s.actor_rows.__setitem__(0,{'Id':4}),lambda s:s.members[20].update(ParticipantId=4),
    lambda s:s.members[20].update(GroupId=11)])
def test_spoof_or_not_member_never_writes_or_discloses(change):
    s=Fake();change(s);r=execute(s)
    assert not r.response['success'] and r.response['resultjson']=='{}' and not s.writes


@pytest.mark.parametrize('variant',['setup','source','episode','wronggroup','wrongparty','wrongkey','fractional','personalwrongparty'])
def test_raw_active_provisional_or_foreign_commit_marker_never_authorizes(variant):
    s=Fake()
    if variant=='setup':s.group['SetupComplete']=False
    if variant=='source':s.requests[70]['OperationComplete']=False
    if variant=='episode':s.requests[71]['OperationComplete']=False
    if variant=='wronggroup':s.requests[71]['TargetGroupId']=11
    if variant=='wrongparty':s.requests[71]['SenderParticipantId']=4
    if variant=='wrongkey':s.members[20]['MembershipKey']='request:071:participant:3'
    if variant=='fractional':s.members[20]['MembershipKey']='request:71.5:participant:3'
    if variant=='personalwrongparty':s.members[20]['MembershipKey']='request:70:participant:3'
    r=execute(s)
    assert not r.response['success'] and not s.writes


@pytest.mark.parametrize('tag,fault',[(tag,fault) for tag in ['Create_receipt','Claim_group','Leave_CAS','Complete_receipt','Release_group'] for fault in ['fail','timeout','stale','commit502'] if (tag,fault)!=('Create_receipt','stale')])
def test_write_faults_never_duplicate_or_claim_unproved_success(tag,fault):
    s=Fake();s.faults[tag]=fault;r=execute(s)
    if fault=='commit502':assert r.response['success'],r.response
    else:
        assert not r.response['success']
        assert r.response['outcomeunknown'] and r.response['writeattempted']
        if tag in ['Create_receipt','Claim_group','Leave_CAS']:assert 'Complete_receipt' not in tags(s)
        if tag in ['Leave_CAS','Complete_receipt']: assert s.group['WriteOwner']!=''
    assert tags(s).count('Leave_CAS')<=1
    assert tags(s).count(tag)==1


def test_complete_receipt_then_release_failure_retry_only_releases_old_token():
    s=Fake();s.faults['Release_group']='fail'
    r=execute(s);assert not r.response['success']
    assert next(iter(s.receipts.values()))['Complete'] and s.group['WriteOwner']
    old=s.group['WriteOwner']; before=len(s.writes)
    s.faults.clear();r=execute(s)
    assert r.response['success'] and r.response['replay']
    assert tags(s)[before:]==['Release_group'] and s.group['WriteOwner']==''
    assert old.endswith(next(iter(s.receipts.values()))['AttemptToken'])


@pytest.mark.parametrize('tag',['Leave_CAS','Complete_receipt','Member_readback','Receipt_readback'])
def test_incomplete_or_unknown_receipt_recovery_is_read_only_no_lease_steal(tag):
    s=Fake();s.faults[tag]='fail'
    r=execute(s);assert not r.response['success'];before=deepcopy((s.members,s.group,s.receipts));n=len(s.writes)
    s.faults.clear();r=execute(s)
    if tag=='Receipt_readback':
        assert r.response['success'] and tags(s)[n:]==['Release_group']
    else:
        assert not r.response['success'] and r.response['resultcode']=='OUTCOME_UNKNOWN'
        assert (s.members,s.group,s.receipts)==before and len(s.writes)==n


def test_busy_other_writer_is_never_cleared_or_written_through():
    s=Fake();s.group['WriteOwner']='respond:2:intent:other-attempt';before=deepcopy((s.group,s.members))
    r=execute(s)
    assert r.response['resultcode']=='GROUP_BUSY'
    assert (s.group,s.members)==before and tags(s)==['Create_receipt']


def test_completed_replay_does_not_clear_another_writer_token():
    s=Fake();assert execute(s).response['success']
    s.group['WriteOwner']='update:another:attempt';n=len(s.writes)
    r=execute(s);assert r.response['success'] and r.response['replay']
    assert s.group['WriteOwner']=='update:another:attempt' and len(s.writes)==n


def test_intent_uuid_rebinding_to_another_episode_conflicts_without_writes():
    s=Fake();assert execute(s).response['success'];n=len(s.writes)
    s.members[24]={**deepcopy(s.members[20]),'Id':24,'MembershipStatus':'Active','LeftAt':None}
    r=execute(s,{**INPUT,'number_2':24})
    assert r.response['resultcode']=='INTENT_CONFLICT' and len(s.writes)==n


@pytest.mark.parametrize('inputs',[{}, {**INPUT,'number':4}, {**INPUT,'number_1':0},
    {**INPUT,'number_2':1.5},{**INPUT,'text':"x' or 1 eq 1"},{**INPUT,'text':'z'*36},{**INPUT,'extra':True}])
def test_invalid_input_and_spoof_fail_without_writes(inputs):
    s=Fake();r=execute(s,inputs)
    assert not r.response['success'] and not s.writes


@pytest.mark.parametrize('role',['members','receipts'])
def test_paged_reads_never_produce_partial_success(role):
    s=Fake();s.paged=role;r=execute(s)
    assert not r.response['success'] and 'Leave_CAS' not in tags(s)


@pytest.mark.parametrize('change',[{'JoinedAt':'tampered'},{'MembershipKey':'request:72:participant:3'},
    {'ParticipantId':4},{'MembershipStatus':'Active'},{'LeftAt':'other'}])
def test_post_leave_readback_must_prove_exact_episode_and_timestamp(change):
    s=Fake();s.tamper_after=change;r=execute(s)
    assert not r.response['success'] and r.response['outcomeunknown']
    assert not next(iter(s.receipts.values()))['Complete'] and s.group['WriteOwner']


def test_missing_receipt_setup_is_blocked_before_reads_and_writes():
    groups=deepcopy(GROUPS);groups['lists'].pop('receipts')
    s=Fake();r=execute(s,groups=groups)
    assert r.response['resultcode']=='CONFIGURATION_REQUIRED' and not s.calls


def walk(block):
    for name,a in block.items():
        yield name,a
        yield from walk(a.get('actions',{}))
        yield from walk(a.get('else',{}).get('actions',{}))


def test_emitted_graph_connection_etag_action_limit_and_zero_other_writes():
    a=leave.build_actions(SOURCE,PEOPLE,GROUPS,'test-build')
    nodes=list(walk(a));assert len({n for n,_ in nodes})==len(nodes)
    metrics=leave.measure(a);assert metrics['actions']<=500 and metrics['maximumActionDepth']<=8
    for name,node in nodes:
        assert node['type']!='Workflow'  # no normalization/compatibility needed
        if node['type']!='OpenApiConnection':continue
        p=node['inputs'];assert p['authentication']=={'type':'Raw','value':leave.RAW_INVOKER}
        assert p['retryPolicy']=={'type':'none'}
        if p['parameters']['parameters/method']=='GET':continue
        payload=p['parameters']['parameters/body'];fields=set(payload)-{'__metadata'}
        if name=='Leave_CAS':assert fields=={'MembershipStatus','LeftAt'}
        elif name in ['Claim_group','Release_group']:assert fields=={'WriteOwner'}
        else:assert name in ['Create_receipt','Complete_receipt']
        if name!='Create_receipt':
            assert p['parameters']['parameters/headers']['IF-MATCH'].startswith("@body('")
            assert p['parameters']['parameters/headers']['IF-MATCH']!='*'
    all_names={n for n,_ in nodes}
    def deps(block):
        for _,node in block.items():
            assert set(node.get('runAfter',{}))<=set(block)
            deps(node.get('actions',{}));deps(node.get('else',{}).get('actions',{}))
    deps(a)
    assert all(n in all_names for n in re.findall(r"(?:body|outputs)\('([^']+)'\)",json.dumps(a)))


@pytest.mark.parametrize('field',['source','auth','site','api'])
def test_source_invoker_guard_rejects_drift(field):
    source=deepcopy(SOURCE)
    if field=='source':source['properties']['connectionReferences']['shared_sharepointonline']['source']='Embedded'
    else:
        p=next(a['inputs'] for _,a in walk(source['properties']['definition']['actions']) if a.get('type')=='OpenApiConnection' and a.get('inputs',{}).get('parameters',{}).get('table')==PEOPLE['lists']['participants']['listId'])
        if field=='auth':p['authentication']['value']='owner'
        if field=='site':p['parameters']['dataset']='https://other.sharepoint.com/sites/other'
        if field=='api':p['host']['apiId']='other'
    with pytest.raises(ValueError):leave.build_actions(source,PEOPLE,GROUPS,'x')


def test_legacy_package_trigger_contract_and_graph_execution(tmp_path):
    output=tmp_path/'leave.zip'
    r=leave.build_package(ROOT/'artifacts/tandem_discovery/TandemDiscovery-v2.definition.json',output,groups=GROUPS,build_id='test-build')
    with ZipFile(output) as z:
        assert z.testzip() is None
        doc=json.loads(z.read(next(n for n in z.namelist() if n.endswith('/definition.json'))))
        assert doc==json.loads(output.with_suffix('.definition.json').read_text())
        assert list(doc['properties']['definition']['triggers']['manual']['inputs']['schema']['properties'])==list(INPUT)
        assert doc['properties']['connectionReferences']['shared_sharepointonline']['source']=='Invoker'
        assert execute(actions=doc['properties']['definition']['actions']).response['success']
    assert r['packageSha256']==hashlib.sha256(output.read_bytes()).hexdigest()
    with pytest.raises(FileExistsError):leave.build_package(ROOT/'artifacts/tandem_discovery/TandemDiscovery-v2.definition.json',output)



@pytest.mark.parametrize('variant',['source','membership','setup','key'])
def test_commit_and_own_episode_authority_are_refreshed_after_group_claim(variant):
    s=Fake();native=s.request
    def request(p):
        r=native(p)
        if p['parameters/method']=='POST' and p.get('parameters/body',{}).get('WriteOwner'):
            if variant=='source':s.requests[70]['OperationComplete']=False
            if variant=='membership':s.members[20]['MembershipStatus']='Left'
            if variant=='setup':s.group['SetupComplete']=False
            if variant=='key':s.members[20]['MembershipKey']='request:72:participant:3'
        return r
    s.request=request;r=execute(s)
    assert not r.response['success'] and 'Leave_CAS' not in tags(s)
    assert s.group['WriteOwner'] and not next(iter(s.receipts.values()))['Complete']


def test_other_writer_wins_group_claim_etag_and_is_not_overwritten():
    s=Fake();native=s.request
    def request(p):
        payload=p.get('parameters/body',{})
        if p['parameters/method']=='POST' and payload.get('WriteOwner'):
            s.group.update(WriteOwner='respond:other:attempt',State='Ended')
            s.group['__metadata']['etag']='"9"'
        return native(p)
    s.request=request;r=execute(s)
    assert not r.response['success'] and 'Leave_CAS' not in tags(s)
    assert s.group['WriteOwner']=='respond:other:attempt' and s.group['State']=='Ended'


def test_whole_native_number_source_and_capacity_values_are_supported():
    s=Fake();s.group.update(SourceRequestId=70.0,Capacity=3.0)
    r=execute(s);assert r.response['success']
    assert result(r)['membercount']==2


def test_own_initial_personal_episode_is_committed_via_source_request():
    s=Fake();s.members[20]['MembershipKey']='request:70:participant:3'
    s.requests[70]['RecipientParticipantId']=3
    r=execute(s);assert r.response['success']


@pytest.mark.parametrize('field',['SourceRequestId','Capacity'])
def test_fractional_group_numbers_never_authorize(field):
    s=Fake();s.group[field]=3.5
    r=execute(s);assert not r.response['success'] and not s.writes


def test_duplicate_active_own_episode_is_not_silently_left_or_collapsed():
    s=Fake();s.members[24]={**deepcopy(s.members[20]),'Id':24}
    r=execute(s);assert r.response['resultcode']=='MEMBERSHIP_INTEGRITY'
    assert 'Leave_CAS' not in tags(s)


def test_oversized_physical_membership_read_stops_before_domain_write():
    s=Fake()
    for i in range(100,2101):s.members[i]={**deepcopy(s.members[22]),'Id':i}
    r=execute(s);assert r.response['resultcode']=='INCOMPLETE_READ'
    assert 'Leave_CAS' not in tags(s) and s.group['WriteOwner']


def test_skipped_write_cannot_be_reconciled_as_saved_or_release_ownership():
    s=Fake();a=leave.build_actions(SOURCE,PEOPLE,GROUPS,'x')
    branch=a['Leave_work']['actions']['Existing_intent']['else']['actions']
    branch['Leave_CAS_mark']['inputs']['value']='@div(1,0)'
    r=execute(s,actions=a)
    assert not r.response['success'] and r.action_states['Member_after_get']=='Skipped'
    assert 'Leave_CAS' not in tags(s) and 'Release_group' not in tags(s)


def test_departure_of_only_learner_suppresses_discovery_without_state_edits():
    import test_discovery_flow as discovery_test
    s=Fake();s.members.pop(22);s.members.pop(23)
    s.group['State']='Open'
    s.members[20]['MembershipKey']='request:70:participant:3'
    s.requests[70]['RecipientParticipantId']=3
    def projected():
        ds=discovery_test.Fake();ds.valid_group()
        ds.members=[{k:v for k,v in row.items() if k not in ['JoinedAt','LeftAt','__metadata']} for row in s.members.values()]
        ds.requests=list(s.requests.values())
        return json.loads(discovery_test.execute(ds).response['groupsjson'])
    assert len(projected())==1
    assert execute(s).response['success']
    assert projected()==[] and s.group['State']=='Open'


def test_remaining_focus_can_still_be_discovered_without_reopening_or_rejoin():
    import test_discovery_flow as discovery_test
    ds=discovery_test.Fake();ds.valid_group()
    ds.profiles.append(discovery_test.profile(4,[],[1]))
    ds.members.append({'Id':24,'GroupId':10,'ParticipantId':4,'MembershipStatus':'Active','MembershipKey':'request:70:participant:4'})
    ds.members[1]['MembershipStatus']='Left'
    # Remaining sharer 2 + learner 4 keep focus, with physical Active count 2.
    response=discovery_test.execute(ds).response
    groups=json.loads(response['groupsjson'])
    assert len(groups)==1 and groups[0]['memberCount']==2



def test_missing_episode_is_not_membership_authority():
    s=Fake();s.members.pop(20)
    r=execute(s);assert not r.response['success'] and not s.writes


def test_receipt_unknown_result_fields_are_not_projected_to_the_app():
    s=Fake();assert execute(s).response['success'];n=len(s.writes)
    receipt=next(iter(s.receipts.values()));saved=json.loads(receipt['ResultJson'])
    saved['rawEmail']='PRIVATE_ACCOUNT';receipt['ResultJson']=json.dumps(saved)
    r=execute(s)
    assert not r.response['success'] and r.response['resultjson']=='{}' and len(s.writes)==n


def test_intent_uuid_case_is_canonical_and_attempt_is_distinct_uuid():
    s=Fake();inputs={**INPUT,'text':'ABCDEFAB-1234-4234-8234-123456789ABC'}
    assert execute(s,inputs).response['success']
    r=execute(s,{**inputs,'text':inputs['text'].lower()})
    assert r.response['success'] and r.response['replay']
    receipt=next(iter(s.receipts.values()))
    assert receipt['OperationKey'].endswith(inputs['text'].lower())
    assert re.fullmatch(leave.GUID['pattern'],receipt['AttemptToken'])
    assert receipt['AttemptToken'].lower()!=inputs['text'].lower()


def test_checked_in_artifact_is_exact_blocked_preview_with_matching_hashes():
    path=ROOT/'artifacts/leave_group/TandemLeaveGroup-v1.zip'
    review=json.loads(path.with_suffix('.review.json').read_text())
    contract=json.loads((ROOT/'config/leave_group_flow_contract.json').read_text())
    doc=json.loads(path.with_suffix('.definition.json').read_text())
    with ZipFile(path) as z:
        assert z.testzip() is None
        assert json.loads(z.read(next(n for n in z.namelist() if n.endswith('/definition.json'))))==doc
    assert hashlib.sha256(path.read_bytes()).hexdigest()==review['packageSha256']
    assert hashlib.sha256((ROOT/'scripts/power_automate/leave_group_flow.py').read_bytes()).hexdigest()==review['generatorSha256']
    assert contract['package']==review
    groups=json.loads((ROOT/'config/group_schema_mapping.json').read_text())
    assert doc['properties']['definition']['actions']==leave.build_actions(SOURCE,PEOPLE,groups,review['buildId'])
    s=Fake();r=execute(s,actions=doc['properties']['definition']['actions'])
    assert r.response['resultcode']=='CONFIGURATION_REQUIRED' and not s.calls


@pytest.mark.parametrize('participation',['Paused','Inactive'])
@pytest.mark.parametrize('openness',[False,True])
def test_group_membership_authority_is_independent_of_personal_availability(participation,openness):
    s=Fake();s.actor_rows[0].update(ParticipationStatus=participation,OpenToConnections=openness)
    before=deepcopy(s.actor_rows)
    r=execute(s)
    assert r.response['success'] and s.actor_rows==before
    assert all('ParticipationStatus' not in p['parameters/uri'] and 'OpenToConnections' not in p['parameters/uri'] for p in s.calls)
    assert all(PEOPLE['lists']['participants']['listId'] not in p['parameters/uri'] for _,p in s.writes)
