"""Execute emitted #17 and unchanged shared GROUP graph; not tenant proof."""
from copy import deepcopy
import hashlib
import json
import re

import pytest

from scripts.power_automate import group_send_flow as flow
from scripts.power_automate.schema_audit import measure
from scripts.power_automate.solution_source import RAW_INVOKER, SP_API, walk
from test_shared_validation import ChildRunner, NoIO

ARTIFACT=flow.ROOT/'artifacts/group_send/TandemSendGroupJoinRequest-v1.solution-parent.json'
CHILD=json.loads((flow.ROOT/'artifacts/shared_validation/TandemSharedValidation81-v2.child.definition.json').read_text())
INTENT='01234567-89ab-cdef-0123-456789abcdef'


def profile(id_,teach=None,learn=None,share=None,culture=None):
    return {'Id':id_,'ParticipantaccountId':100+id_,'Status':'Active','ParticipationStatus':'Active',
        'OpenToConnections':True,'TimezoneId':None,
        **{field+'Id':{'results':values or []} for field,values in zip(flow.PROFILE_FIELDS,[teach,learn,share,culture])}}


class Server:
    def __init__(self):
        self.profiles={1:profile(1,learn=[1]),2:profile(2,teach=[1]),3:profile(3,learn=[1])}
        self.user=101
        self.group={'Id':10,'ExchangeType':'Language','LanguageFocusId':{'results':[1]},'CultureFocusId':{'results':[]},
            'Capacity':3,'State':'Open','SourceRequestId':70,'SetupComplete':True,'WriteOwner':None}
        self.members=[{'Id':20+i,'GroupId':10,'ParticipantId':i,'MembershipStatus':'Active','MembershipKey':f'request:70:participant:{i}'} for i in [2,3]]
        self.source={'Id':70,'RequestType':'Personal','SenderParticipantId':2,'RecipientParticipantId':3,'TargetGroupId':None,'Introduction':None,
            'Status':'Accepted','SendOperationKey':'personal:2:old','ConnectionKey':'history:request:70','WinningOperationKey':'accept:3:old','OperationComplete':True}
        self.rows=[];self.writes=[];self.queries=[];self.child_calls=[]
        self.create_mode='ok';self.paged=None;self.fail=None;self.child_mode='ok';self.corrupt=None

    def culture_only(self):
        self.group.update(ExchangeType='Culture',LanguageFocusId={'results':[]},CultureFocusId={'results':[5]},Capacity=4)
        self.profiles={1:profile(1,culture=[5]),2:profile(2,share=[5]),3:profile(3,culture=[5])}

    def request(self,p):
        def response(value,status=200):return {'statusCode':status,'body':{'d':deepcopy(value)}}
        if '__child' in p:
            payload=p['__child'];self.child_calls.append(json.loads(payload['text']))
            if self.child_mode=='failed':return {'statusCode':504,'body':{}}
            child=ChildRunner(NoIO());child.run(CHILD,{'items':{},'triggerBody':payload})
            body=deepcopy(child.response)
            if self.child_mode=='badjson':body['resultjson']='bad-json'
            elif self.child_mode=='outer':body['success']=False
            elif self.child_mode!='ok':
                result=json.loads(body['resultjson'])
                if self.child_mode=='version':result['rulesVersion']=2
                if self.child_mode=='build':result['packageBuildId']='unreviewed'
                if self.child_mode=='authorizes':result['authorizesAction']=True
                if self.child_mode=='missing':result['result'].pop('compatible',None)
                if self.child_mode=='string':result['result']['compatible']='true'
                body['resultjson']=json.dumps(result)
            return {'statusCode':200,'body':body}
        uri=p['parameters/uri'];self.queries.append(uri)
        assert '/fields' not in uri and '/role' not in uri
        if self.fail and self.fail in uri:return response({},500)
        if uri.startswith('_api/web/currentuser'):return response({'Id':self.user})
        if flow.PEOPLE in uri:
            if 'ParticipantaccountId eq ' in uri:
                account=int(re.search(r'ParticipantaccountId eq (\d+)',uri)[1])
                return response({'results':[{'Id':x['Id']} for x in self.profiles.values() if x['ParticipantaccountId']==account]})
            id_=int(re.search(r'/items\((\d+)\)',uri)[1]);return response(self.profiles[id_])
        if flow.GROUPS in uri:return response(self.group)
        if flow.MEMBERS in uri:
            rows=[x for x in self.members if x['GroupId']==int(re.search(r'GroupId eq (\d+)',uri)[1])]
            if 'ParticipantId eq' in uri:rows=[x for x in rows if x['ParticipantId']==int(re.search(r'ParticipantId eq (\d+)',uri)[1]) and x['MembershipStatus']!='Left']
            else:rows=[x for x in rows if x['MembershipStatus']=='Active']
            data={'results':rows}
            if self.paged=='members':data['__next']='next'
            return response(data)
        if flow.REQUESTS in uri:
            if p['parameters/method']=='POST':
                self.writes.append(deepcopy(p))
                row=deepcopy(p['parameters/body'])
                if self.create_mode=='failed':return response({},502)
                if self.create_mode=='race':
                    self.rows.append({**row,'Id':99,'SendOperationKey':'group:1:different-intent'})
                if any(r['SendOperationKey']==row['SendOperationKey'] or r['ConnectionKey']==row['ConnectionKey'] for r in self.rows):return response({},409)
                row['Id']=80+len(self.rows)
                if self.corrupt:row[self.corrupt]='changed'
                self.rows.append(row)
                return response(row,502 if self.create_mode=='lost' else 201)
            if '/items(' in uri:
                id_=int(re.search(r'/items\((\d+)\)',uri)[1])
                return response(next(r for r in [self.source]+self.rows if r['Id']==id_))
            match=re.search(r"\$filter=(SendOperationKey|ConnectionKey) eq '([^']+)'",uri)
            if match:
                rows=[r for r in self.rows if r[match[1]]==match[2]]
                data={'results':rows}
                if self.paged=='intent' or self.paged=='readback' and self.writes:data['__next']='next'
                return response(data)
            if "RequestType eq 'Group'" in uri:
                group=int(re.search(r'TargetGroupId eq (\d+)',uri)[1]);actor=int(re.search(r'SenderParticipantId eq (\d+)',uri)[1])
                return response({'results':[r for r in self.rows if r['RequestType']=='Group' and r['TargetGroupId']==group and r['SenderParticipantId']==actor and (r['Status']=='Pending' or r['Status']=='Accepted' and r['OperationComplete'] is False)]})
            member=int(re.search(r'SenderParticipantId eq (\d+)',uri)[1])
            return response({'results':[r for r in [self.source]+self.rows if member in [r['SenderParticipantId'],r['RecipientParticipantId']] and r['Status']=='Accepted' and r['OperationComplete'] is True]})
        mapping=json.loads((flow.ROOT/'config/tenant_schema_mapping.json').read_text(encoding='utf-8'))
        role=next(r for r in ['language','culture','timezone'] if mapping['lists'][r]['listId'] in uri)
        data={'results':[{'Id':1,'Active':True,'ISOcode':'en'},{'Id':99,'Active':True,'ISOcode':'any'}] if role=='language' else [{'Id':5,'Active':True}] if role=='culture' else [{'Id':37,'Active':True}]}
        if self.paged=='catalogue':data['__next']='next'
        return response(data)


class GroupRunner(ChildRunner):
    def parse_content(self,value,schema):
        value=super().parse_content(value,schema)
        def bounds(value,schema):
            if isinstance(value,str):assert len(value)<=schema.get('maxLength',10**9)
            if isinstance(value,list):
                assert schema.get('minItems',0)<=len(value)<=schema.get('maxItems',10**9)
                for row in value:bounds(row,schema.get('items',{}))
            if isinstance(value,dict):
                for key,row in value.items():bounds(row,schema.get('properties',{}).get(key,{}))
        bounds(value,schema)
        return value

    def expr(self,text,ctx):
        text=re.sub(r"substring\(body\('Input'\)\?\['intent'\],(\d+),1\)",lambda m:"'"+self.body('Input')['intent'][int(m[1]):int(m[1])+1]+"'",text)
        return super().expr(text,ctx)

    def run(self,actions,ctx=None):
        adapted=deepcopy(actions)
        for action in adapted.values():
            if action['type']=='Workflow':
                assert action['inputs']['host']=={'workflowReferenceName':flow.CHILD}
                action['type']='OpenApiConnection'
                action['inputs']={'parameters':{'__child':action['inputs']['body']}}
        return super().run(adapted,ctx)


def execute(server=None,intro='',intent=INTENT,group=10,extra=None):
    server=server or Server()
    runner=GroupRunner(server)
    body={'number':group,'text':intent,**(extra or {})}
    if intro is not ...:body['text_1']=intro
    runner.run(json.loads(ARTIFACT.read_text())['properties']['definition']['actions'],{'items':{},'triggerBody':body})
    assert runner.response is not None,runner.action_states
    return runner


def test_fresh_send_and_repeat_before_availability_do_one_post():
    s=Server();before=deepcopy((s.profiles,s.group,s.members))
    r=execute(s,intro='Hello')
    assert r.response['resultcode']=='SAVED',r.action_states
    row=s.rows[0]
    assert row['RequestType']=='Group' and row['TargetGroupId']==10 and row['SenderParticipantId']==1 and row['RecipientParticipantId'] is None
    assert row['Introduction']=='Hello' and row['Status']=='Pending' and row['OperationComplete'] is False
    assert row['ConnectionKey']=='open:group:10:participant:1'
    assert row['SendOperationKey']=='group:1:'+INTENT
    assert (s.profiles,s.group,s.members)==before and len(s.writes)==1
    s.profiles[1]['ParticipationStatus']='Paused';s.group['State']='Closed'
    s.queries=[];r=execute(s,intro='Hello')
    assert r.response['resultcode']=='REPLAY' and len(s.writes)==1
    assert len(s.child_calls)==1 and not any(flow.GROUPS in q for q in s.queries)
    assert not any(k in json.dumps(r.response) for k in ['Introduction','accountKey','SendOperationKey','ConnectionKey'])


@pytest.mark.parametrize('intro',[...,None,'','x'*2000,'<b>literal plain text</b>','  '])
def test_introduction_optional_plain_literal_and_2000_boundary(intro):
    s=Server();r=execute(s,intro=intro)
    assert r.response['success'],(r.response,r.action_states)
    assert s.rows[0]['Introduction']==('' if intro is ... or intro is None else intro)


@pytest.mark.parametrize('intro',['x'*2001,42,True])
def test_bad_introduction_rejected_before_any_io(intro):
    s=Server();r=execute(s,intro=intro)
    assert r.response['resultcode']=='INVALID_INPUT' and not s.writes and not s.queries


@pytest.mark.parametrize('change',['group','intro'])
def test_same_intent_changed_payload_conflicts_before_new_checks(change):
    s=Server();execute(s,intro='Original');s.profiles[1]['ParticipationStatus']='Paused'
    r=execute(s,intro='Changed' if change=='intro' else 'Original',group=11 if change=='group' else 10)
    assert r.response['resultcode']=='INTENT_CONFLICT' and len(s.writes)==1 and len(s.child_calls)==1


def test_empty_introduction_canonical_replay_and_uuid_case():
    s=Server();execute(s,intro=...)
    assert execute(s,intro=None,intent=INTENT.upper()).response['resultcode']=='REPLAY'


@pytest.mark.parametrize('variant',['closed','ended','setup','owner','full','nofit','paused-actor','null-actor','closed-actor','paused-sharer','unknown-focus','unknown-zone','any-only','source','uncommitted','duplicate','own-active','own-provisional'])
def test_unavailable_or_uncommitted_context_never_writes(variant):
    s=Server()
    if variant in ['closed','ended']:s.group['State']=variant.title()
    if variant=='setup':s.group['SetupComplete']=False
    if variant=='owner':s.group['WriteOwner']='busy'
    if variant=='full':s.group['Capacity']=2
    if variant=='nofit':s.profiles[1]['LearnlanguagesId']['results']=[]
    if variant=='paused-actor':s.profiles[1]['ParticipationStatus']='Paused'
    if variant=='null-actor':s.profiles[1]['ParticipationStatus']=None
    if variant=='closed-actor':s.profiles[1]['OpenToConnections']=False
    if variant=='paused-sharer':s.profiles[2]['ParticipationStatus']='Paused'
    if variant=='unknown-focus':s.group['LanguageFocusId']['results']=[999]
    if variant=='unknown-zone':s.profiles[1]['TimezoneId']=999
    if variant=='any-only':s.profiles[1]['LearnlanguagesId']['results']=[99]
    if variant=='source':s.source['OperationComplete']=False
    if variant=='uncommitted':s.members[0]['MembershipKey']='request:999:participant:2'
    if variant=='duplicate':s.group['Capacity']=4;s.group['ExchangeType']='Combined';s.members.append({**s.members[0],'Id':99})
    if variant in ['own-active','own-provisional']:
        s.members.append({'Id':98,'GroupId':10,'ParticipantId':1,'MembershipStatus':'Active','MembershipKey':'request:999:participant:1'})
    r=execute(s)
    assert not r.response['success'] and not s.writes,(variant,r.response)


def test_culture_only_null_zone_uses_real_group_rules():
    s=Server();s.culture_only();r=execute(s)
    assert r.response['resultcode']=='SAVED',r.response
    assert s.child_calls[0]['mode']=='GROUP' and s.child_calls[0]['group']['memberProfileIds']==[2,3]
    assert all(p['timezoneId'] is None for p in s.child_calls[0]['profiles'])


@pytest.mark.parametrize('status',['Accepted','Declined','Cancelled'])
def test_terminal_replay_preserves_stored_request_and_new_intent_is_distinct(status):
    s=Server();execute(s)
    s.rows[0].update(Status=status,OperationComplete=True,WinningOperationKey='decision:old',ConnectionKey='history:request:80')
    r=execute(s)
    assert r.response['resultcode']=='REPLAY' and r.response['status']==status and len(s.writes)==1
    assert execute(s,intent='ffffffff-ffff-ffff-ffff-ffffffffffff').response['resultcode']=='SAVED'


def test_new_intent_duplicate_live_key_and_legacy_pending():
    s=Server();execute(s)
    assert execute(s,intent='ffffffff-ffff-ffff-ffff-ffffffffffff').response['resultcode']=='CONNECTION_EXISTS'
    s.rows[0]['ConnectionKey']=''
    assert execute(s,intent='ffffffff-ffff-ffff-ffff-ffffffffffff').response['resultcode']=='UNSETTLED_CONNECTION_EXISTS'
    assert len(s.writes)==1


@pytest.mark.parametrize('mode,code',[('lost','SAVED'),('failed','CREATE_OUTCOME_UNKNOWN'),('race','CREATE_OUTCOME_UNKNOWN')])
def test_unknown_create_exact_readback_only_no_second_post(mode,code):
    s=Server();s.create_mode=mode;r=execute(s)
    assert r.response['resultcode']==code and len(s.writes)==1
    assert len(s.rows)==int(mode!='failed')


@pytest.mark.parametrize('field',['Introduction','SenderParticipantId','TargetGroupId','RequestType','SendOperationKey','ConnectionKey'])
def test_corrupted_create_readback_never_confirms(field):
    s=Server();s.corrupt=field;r=execute(s,intro='original')
    assert r.response['resultcode']=='CREATE_OUTCOME_UNKNOWN' and len(s.writes)==1


@pytest.mark.parametrize('mode',['failed','badjson','version','build','authorizes','missing','string','outer'])
def test_child_failure_and_envelope_rejection_are_fail_closed(mode):
    s=Server();s.child_mode=mode;r=execute(s)
    assert not r.response['success'] and not s.writes


@pytest.mark.parametrize('case',['intent','members','catalogue','readback'])
def test_incomplete_reads_do_not_report_success(case):
    s=Server();s.paged=case;r=execute(s)
    assert not r.response['success']
    assert len(s.writes)==int(case=='readback')
    if case=='readback':assert r.response['resultcode']=='CREATE_OUTCOME_UNKNOWN'


@pytest.mark.parametrize('intent',['bad','x'*36,'01234567-89ab-cdef-0123-456789abcde-',INTENT+"'"])
def test_intent_rejected_without_io(intent):
    s=Server();r=execute(s,intent=intent)
    assert not r.response['success'] and not s.queries and not s.writes


def test_spoofed_actor_inputs_never_select_sender():
    s=Server();r=execute(s,extra={'ActorId':2,'SenderParticipantId':2,'number_1':2})
    assert r.response['success'] and s.rows[0]['SenderParticipantId']==1
    s=Server();s.profiles[1]['ParticipantaccountId']=202
    r=execute(s,extra={'ActorId':1})
    assert r.response['resultcode']=='UNAUTHORIZED_PROFILE' and not s.writes


def test_artifact_structure_binding_hash_and_single_write():
    doc=json.loads(ARTIFACT.read_text());actions=doc['properties']['definition']['actions']
    review=json.loads(ARTIFACT.with_suffix('.review.json').read_text())
    assert review['definitionSha256']==hashlib.sha256(ARTIFACT.read_bytes()).hexdigest()
    metrics=measure(actions)
    assert metrics['actions']<=500 and metrics['maximumActionDepth']<=8
    assert list(doc['properties']['definition']['triggers']['manual']['inputs']['schema']['properties'])==['number','text','text_1']
    assert '_connectionEvidence' not in doc
    refs=doc['properties']['connectionReferences']
    assert refs['shared_sharepointonline']['runtimeSource']=='invoker'
    writes=[];names=[]
    for name,a in walk(actions):
        names.append(name)
        if a['type']=='OpenApiConnection':
            assert a['inputs']['authentication']=={'type':'Raw','value':RAW_INVOKER}
            assert a['inputs']['host']['apiId']==SP_API
            p=a['inputs']['parameters']
            if p['parameters/method']!='GET':writes.append(a)
    assert len(names)==len(set(names))
    assert len(writes)==1 and writes[0]['inputs']['retryPolicy']=={'type':'none'}
    assert writes[0]['inputs']['parameters']['parameters/uri']==flow.base(flow.REQUESTS)+'/items'
    assert '/fields' not in json.dumps(actions) and 'SCHEMA' not in json.dumps(actions)


def test_generator_matches_emitted_graph_and_child_hash():
    doc=json.loads(ARTIFACT.read_text());actions=doc['properties']['definition']['actions']
    read=next(a for _,a in walk(actions) if a['type']=='OpenApiConnection')
    seed={'receipt':{'site':flow.SITE,'sharedChildId':flow.CHILD},'probe':{'properties':{
        'definition':{'actions':{'Native_read':read}}}}}
    assert flow.build_actions(seed)==actions
    review=json.loads(ARTIFACT.with_suffix('.review.json').read_text())
    child_path=flow.ROOT/'artifacts/shared_validation/TandemSharedValidation81-v2.child.definition.json'
    assert review['sharedChildSha256']==hashlib.sha256(child_path.read_bytes()).hexdigest()


def test_physical_uncommitted_row_still_consumes_capacity():
    s=Server();s.members.append({'Id':99,'GroupId':10,'ParticipantId':4,'MembershipStatus':'Active','MembershipKey':'request:999:participant:4'})
    r=execute(s)
    assert r.response['resultcode']=='GROUP_FULL_OR_DUPLICATE_MEMBER' and not s.writes and not s.child_calls


@pytest.mark.parametrize('part',[flow.PEOPLE,flow.GROUPS,'/items(70)','/currentuser'])
def test_failed_fresh_reads_cannot_report_saved(part):
    s=Server();s.fail=part;r=execute(s)
    assert not r.response['success'] and not s.writes


def test_missing_readback_after_attempt_is_unknown_without_retry():
    s=Server();original=s.request
    def request(parameters):
        if s.writes and parameters.get('parameters/method')=='GET' and 'SendOperationKey eq' in parameters.get('parameters/uri',''):
            return {'statusCode':500,'body':{}}
        return original(parameters)
    s.request=request
    r=execute(s)
    assert r.response['resultcode']=='CREATE_OUTCOME_UNKNOWN' and len(s.writes)==1


def test_actor_account_change_between_resolution_and_current_read_rejected():
    s=Server();original=s.request
    def request(parameters):
        result=original(parameters)
        if 'ParticipantaccountId eq' in parameters.get('parameters/uri',''):
            s.profiles[1]['ParticipantaccountId']=202
        return result
    s.request=request
    r=execute(s)
    assert r.response['resultcode']=='PROFILE_IDENTITY_MISMATCH' and not s.writes
