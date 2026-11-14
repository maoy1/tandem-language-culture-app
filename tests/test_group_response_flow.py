"""Execute #65 emitted parent and real #81 child with a synthetic CAS store."""
from copy import deepcopy
import json,re
import pytest
from scripts.power_automate import group_response_flow as flow
from scripts.power_automate.schema_audit import measure
from test_shared_validation import ChildRunner, NoIO
from test_discovery_flow import profile

CHILD=json.loads((flow.ROOT/'artifacts/shared_validation/TandemSharedValidation81-v2.child.definition.json').read_text())
UUID='11111111-1111-4111-8111-111111111111'
UUID2='22222222-2222-4222-8222-222222222222'


class Store:
    def __init__(self):
        self.mapping=json.loads((flow.ROOT/'config/tenant_schema_mapping.json').read_text());self.groups_mapping=json.loads((flow.ROOT/'config/group_schema_mapping.json').read_text())
        self.tables={k:{} for k in ['requests','groups','members','receipts']};self.actor=1;self.calls=[];self.child_calls=[];self.hook=None;self.faults={};self.paged=None
        self.profiles={1:profile(1,[1],[]),2:profile(2,[],[1]),3:profile(3,[],[1]),4:profile(4,[],[1])}
        self.put('requests',70,{'RequestType':'Personal','SenderParticipantId':1,'RecipientParticipantId':2,'Status':'Accepted','OperationComplete':True,'WinningOperationKey':'old','ConnectionKey':'history:request:70'})
        self.put('requests',80,{'RequestType':'Group','SenderParticipantId':3,'TargetGroupId':10,'Status':'Pending','OperationComplete':False,'WinningOperationKey':None,'ConnectionKey':'open:group:10:participant:3'})
        self.put('requests',81,{'RequestType':'Group','SenderParticipantId':4,'TargetGroupId':10,'Status':'Pending','OperationComplete':False,'WinningOperationKey':None,'ConnectionKey':'open:group:10:participant:4'})
        self.put('groups',10,{'ExchangeType':'Language','LanguageFocusId':{'results':[1]},'CultureFocusId':{'results':[]},'Capacity':3,'State':'Open','SetupComplete':True,'WriteOwner':'','SourceRequestId':70})
        for i,p in [(20,1),(21,2)]:self.put('members',i,{'GroupId':10,'ParticipantId':p,'MembershipStatus':'Active','MembershipKey':f'request:70:participant:{p}'})
    def put(self,role,id,values):self.tables[role][id]={'Id':id,'_v':1,**deepcopy(values)}
    def row(self,role,id):
        row=deepcopy(self.tables[role][id]);version=row.pop('_v');row['__metadata']={'etag':'"'+str(version)+'"','type':'SP.Data.'+role};return row
    def request(self,p):
        if '_workflow' in p:
            req=p['_workflow'];assert req['host']=={'workflowReferenceName':flow.CHILD};payload=json.loads(req['body']['text']);self.child_calls.append(payload)
            c=ChildRunner(NoIO());c.run(deepcopy(CHILD),{'items':{},'triggerBody':req['body']});return {'statusCode':200,'body':deepcopy(c.response)}
        action=p.pop('_action',None);self.calls.append((action,deepcopy(p)))
        if self.hook:self.hook(action,p,self)
        fault=self.faults.pop(action,None)
        if fault and not fault.get('persist'):return {'statusCode':fault.get('status',500),'body':deepcopy(fault.get('body',{}))}
        def result(data,status=200):return {'statusCode':status,'body':{'d':data}}
        if 'id' in p:return {'statusCode':200,'body':deepcopy(self.profiles[p['id']])}
        uri=p['parameters/uri'];method=p['parameters/method']
        if uri.startswith('_api/web/currentuser'):return result({'Id':100+self.actor})
        if 'ParticipantaccountId eq' in uri:return result({'results':[{'Id':self.actor}]})
        for role in ['language','culture','timezone']:
            if self.mapping['lists'][role]['listId'] in uri:
                rows=[{'Id':1,'Active':True,'ISOcode':'en'},{'Id':99,'Active':True,'ISOcode':'any'}] if role=='language' else [{'Id':1,'Active':True}]
                return result({'results':rows})
        role='receipts' if 'TandemOperationReceipts' in uri else 'requests' if flow.REQUESTS in uri else next(k for k in ['groups','members'] if self.groups_mapping['lists'][k]['listId'] in uri)
        if 'ListItemEntityTypeFullName' in uri:return result({'ListItemEntityTypeFullName':'SP.Data.'+role})
        m=re.search(r'/items\((\d+)\)',uri);id=int(m[1]) if m else None
        if method=='GET':
            if id is not None:
                if id not in self.tables[role]:return result({},404)
                return result(self.row(role,id))
            rows=[self.row(role,i) for i in self.tables[role]]
            if 'OperationKey eq' in uri or 'MembershipKey eq' in uri:
                field,value=re.search(r"(OperationKey|MembershipKey) eq '([^']+)'",uri).groups();rows=[r for r in rows if r.get(field)==value]
            if 'GroupId eq' in uri:
                gid=int(re.search(r'GroupId eq (\d+)',uri)[1]);rows=[r for r in rows if r.get('GroupId')==gid and r.get('MembershipStatus')=='Active']
            data={'results':rows}
            if self.paged==role:data['__next']='more'
            return result(data)
        assert method=='POST' and p['parameters/body']['__metadata']['type']=='SP.Data.'+role
        values={k:v for k,v in p['parameters/body'].items() if k!='__metadata'}
        if id is not None:
            row=self.tables[role][id];tag=p['parameters/headers']['IF-MATCH'];assert tag!='*' and tag
            if tag!='"'+str(row['_v'])+'"':return result({},412)
            row.update(deepcopy(values));row['_v']+=1
        else:
            unique={'receipts':'OperationKey','members':'MembershipKey'}[role]
            if any(r.get(unique)==values.get(unique) for r in self.tables[role].values()):return result({},409)
            id=max(self.tables[role],default=0)+1;self.put(role,id,values)
        if fault:return {'statusCode':fault.get('status',500),'body':fault.get('body',{})}
        return result(self.row(role,id),201 if m is None else 204)


class Parent(ChildRunner):
    def __init__(self,server,run):super().__init__(server);self.run_name=run
    def expr(self,text,ctx):
        text=text.replace("workflow()?['run']?['name']", "'"+self.run_name+"'").replace('utcNow()',"'2026-11-14T12:00:00Z'")
        token="first(skip(split(item()?['MembershipKey'],':'),1))"
        if token in text:text=text.replace(token,"'"+ctx['item']['MembershipKey'].split(':')[1]+"'")
        return super().expr(text,ctx)
    def parse_content(self,value,schema):
        value=super().parse_content(value,schema)
        def patterns(v,s):
            if 'pattern' in s:assert re.fullmatch(s['pattern'],v)
            if isinstance(v,dict):
                for k,rule in s.get('properties',{}).items():
                    if k in v:patterns(v[k],rule)
        patterns(value,schema);return value
    def run(self,actions,ctx=None):
        ctx=ctx or {'items':{},'triggerBody':{}}
        if ctx.get('items'):ctx={**ctx,'item':list(ctx['items'].values())[-1]}
        actions=deepcopy(actions)
        for name,a in actions.items():
            if a['type']=='Workflow':a['type']='OpenApiConnection';a['inputs']={'parameters':{'_workflow':a['inputs']}}
            elif a['type']=='OpenApiConnection':a['inputs']['parameters']['_action']=name
            elif a['type']=='InitializeVariable':
                for v in a['inputs']['variables']:v['value']=self.inputs(v['value'],ctx)
        return super().run(actions,ctx)


def execute(store=None,request=80,decision='Accept',intent=UUID,actor=1,run='run-A'):
    store=store or Store();old=store.actor;store.actor=actor
    r=Parent(store,run)
    try:r.run(flow.build_actions(build_id='test-65'),{'items':{},'triggerBody':{'number':request,'text':decision,'text_1':intent}})
    finally:store.actor=old
    return r,store


def test_happy_accept_real_child_and_complete_receipt_before_release():
    r,s=execute();assert r.response['success'],(r.response,r.action_states)
    assert r.response['resultcode']=='ACCEPTED'
    assert s.tables['requests'][80]['OperationComplete'] is True and s.tables['groups'][10]['WriteOwner']==''
    assert len(s.tables['members'])==3 and s.tables['groups'][10]['State']=='Open'
    assert [p['mode'] for p in s.child_calls]==['NORMALIZE','GROUP']
    names=[n for n,p in s.calls];assert names.index('Complete_receipt_Write')<names.index('Release_completed_Write')
    assert json.loads(r.response['resultjson'])['membershipIds']==[22]


def test_decline_works_for_paused_actor_and_unavailable_requester():
    s=Store();s.profiles[1]['ParticipationStatus']={'Value':'Paused'};s.profiles[1]['OpenToConnections']=False
    s.profiles[3]['ParticipationStatus']=None
    r,s=execute(s,decision='Decline');assert r.response['success'],r.action_states
    assert s.tables['requests'][80]['Status']=='Declined' and len(s.tables['members'])==2 and not s.child_calls


def test_completed_replay_does_not_repeat_domain_writes_even_after_episode_left():
    r,s=execute();s.tables['members'][22]['MembershipStatus']='Left'
    before=deepcopy(s.tables);r,s=execute(s,run='run-B')
    assert r.response['success'] and s.tables==before
    assert s.tables['members'][22]['MembershipStatus']=='Left'


@pytest.mark.parametrize('change',['decision','request'])
def test_same_intent_uuid_rebind_rejected_without_writes(change):
    r,s=execute();before=deepcopy(s.tables)
    r,s=execute(s,decision='Decline' if change=='decision' else 'Accept',request=81 if change=='request' else 80,run='run-B')
    assert not r.response['success'] and s.tables==before


@pytest.mark.parametrize('field,value',[('ParticipationStatus',None),('ParticipationStatus',{'Value':'Paused'}),('OpenToConnections',False),('Status',None)])
def test_new_requester_unavailable_rejected_without_decision_or_membership(field,value):
    s=Store();s.profiles[3][field]=value;r,s=execute(s)
    assert not r.response['success'] and s.tables['requests'][80]['Status']=='Pending'
    assert len(s.tables['members'])==2 and s.tables['groups'][10]['WriteOwner']==''
    assert list(s.tables['receipts'].values())[0]['Complete']


def test_paused_closed_to_connections_actor_can_accept_when_another_focus_sharer_available():
    s=Store();s.profiles[1]['ParticipationStatus']={'Value':'Paused'};s.profiles[1]['OpenToConnections']=False
    s.profiles[2]['Teachlanguages#Id']=[1]
    r,s=execute(s);assert r.response['success']


@pytest.mark.parametrize('variant',['foreign','left','uncommitted','forgedEpisode'])
def test_actor_requires_current_committed_membership_not_a_leader_role(variant):
    s=Store()
    if variant=='foreign':s.tables['members'][20]['GroupId']=11
    if variant=='left':s.tables['members'][20]['MembershipStatus']='Left'
    if variant=='uncommitted':s.tables['requests'][70]['OperationComplete']=False
    if variant=='forgedEpisode':s.tables['members'][20]['MembershipKey']='request:80:participant:1'
    before=deepcopy(s.tables);r,s=execute(s,decision='Decline')
    assert not r.response['success'] and s.tables==before


@pytest.mark.parametrize('first',['Accept','Decline'])
def test_conflicting_members_first_terminal_wins(first):
    r,s=execute(decision=first);before=deepcopy(s.tables['requests'][80]);members=deepcopy(s.tables['members'])
    r,s=execute(s,actor=2,intent=UUID2,decision='Decline' if first=='Accept' else 'Accept',run='run-B')
    assert not r.response['success'] and s.tables['requests'][80]==before and s.tables['members']==members


def test_cancel_race_wins_exact_request_etag_and_no_join():
    s=Store()
    def cancel(action,p,s):
        if action=='Decide_request':
            s.hook=None;q=s.tables['requests'][80];q.update(Status='Cancelled',OperationComplete=True,WinningOperationKey='cancel:3:test',ConnectionKey='history:request:80');q['_v']+=1
    s.hook=cancel;r,s=execute(s)
    assert not r.response['success'] and s.tables['requests'][80]['Status']=='Cancelled'
    assert len(s.tables['members'])==2 and s.tables['groups'][10]['WriteOwner']==''
    assert list(s.tables['receipts'].values())[0]['Complete']


def test_last_slot_interleaving_serialized_then_retry_observes_full():
    s=Store();other=[]
    def interleave(action,p,s):
        if action=='Locked_Request':
            s.hook=None;other.append(execute(s,request=81,intent=UUID2,actor=2,run='run-B')[0])
    s.hook=interleave;first,s=execute(s)
    assert first.response['success'] and not other[0].response['success']
    assert len(s.tables['members'])==3
    second,s=execute(s,request=81,intent=UUID2,actor=2,run='run-C')
    assert not second.response['success'] and len(s.tables['members'])==3 and s.tables['requests'][81]['Status']=='Pending'


@pytest.mark.parametrize('action',['Decide_request','Create_episode','Commit_request','Complete_receipt_Write'])
def test_unknown_write_persisted_reconciles_same_key_without_duplicate(action):
    s=Store();s.faults[action]={'status':500,'persist':True}
    r,s=execute(s)
    if not r.response['success']:r,s=execute(s,run='run-B')
    assert r.response['success'],(r.response,r.action_states)
    assert len(s.tables['members'])==3 and s.tables['requests'][80]['OperationComplete']


def test_definite_stopped_prefix_sealed_and_retried_without_second_terminal_write():
    s=Store();s.faults['Create_episode']={'status':403};r,s=execute(s)
    assert not r.response['success'] and r.response['retryable']
    receipt=list(s.tables['receipts'].values())[0]
    assert json.loads(receipt['SealedAttempts'])==['run-A'] and s.tables['groups'][10]['WriteOwner']==''
    assert s.tables['requests'][80]['Status']=='Accepted' and not s.tables['requests'][80]['OperationComplete']
    r,s=execute(s,run='run-B');assert r.response['success'],(r.response,r.action_states)
    assert len(s.tables['members'])==3
    assert len([1 for n,p in s.calls if n=='Decide_request'])==1


@pytest.mark.parametrize('action',['Decision_readback','Episode_readback','Commit_readback'])
def test_partial_readback_never_reports_false_success(action):
    s=Store();s.faults[action]={'status':200,'body':{'d':{}}}
    r,s=execute(s)
    if r.response['success']:
        assert s.tables['requests'][80]['OperationComplete'] and len(s.tables['members'])==3
    else:
        assert r.response['resultjson']=='{}' and not list(s.tables['receipts'].values())[0]['Complete']


def test_unknown_absence_retains_owner_no_timeout_steal():
    s=Store();s.faults['Create_episode']={'status':500};r,s=execute(s)
    assert not r.response['success'] and not r.response['retryable']
    token=s.tables['groups'][10]['WriteOwner'];assert token
    before=deepcopy(s.tables);r,s=execute(s,run='much-later-run')
    assert not r.response['success'] and s.tables==before and s.tables['groups'][10]['WriteOwner']==token


@pytest.mark.parametrize('variant',['Left','foreignGroup','foreignParticipant'])
def test_episode_conflict_never_overwrites_or_reactivates_history(variant):
    s=Store();row={'GroupId':10,'ParticipantId':3,'MembershipStatus':'Active','MembershipKey':'request:80:participant:3'}
    if variant=='Left':row['MembershipStatus']='Left'
    if variant=='foreignGroup':row['GroupId']=11
    if variant=='foreignParticipant':row['ParticipantId']=4
    s.put('members',30,row);before=deepcopy(s.tables['members']);r,s=execute(s)
    assert not r.response['success'] and s.tables['members']==before and s.tables['requests'][80]['Status']=='Pending'


def test_foreign_committed_episode_cannot_grant_group_authority():
    s=Store();s.put('requests',90,{'RequestType':'Group','TargetGroupId':11,'SenderParticipantId':1,'Status':'Accepted','OperationComplete':True})
    s.tables['members'][20]['MembershipKey']='request:90:participant:1'
    r,s=execute(s,decision='Decline');assert not r.response['success'] and not s.tables['receipts']


def test_active_provisional_row_is_not_a_free_slot_or_operational_authority():
    s=Store();s.put('requests',90,{'RequestType':'Group','TargetGroupId':10,'SenderParticipantId':4,'Status':'Accepted','OperationComplete':False})
    s.put('members',30,{'GroupId':10,'ParticipantId':4,'MembershipStatus':'Active','MembershipKey':'request:90:participant:4'})
    before=deepcopy(s.tables['members']);r,s=execute(s)
    assert not r.response['success'] and s.tables['members']==before and s.tables['requests'][80]['Status']=='Pending'


@pytest.mark.parametrize('state',['Closed','Ended'])
def test_reject_accept_preserves_group_state(state):
    s=Store();s.tables['groups'][10]['State']=state;r,s=execute(s)
    assert not r.response['success'] and s.tables['groups'][10]['State']==state and s.tables['groups'][10]['WriteOwner']==''


def test_full_group_counts_paused_members():
    s=Store();s.tables['groups'][10]['Capacity']=2;s.profiles[2]['ParticipationStatus']={'Value':'Paused'}
    r,s=execute(s);assert not r.response['success'] and len(s.tables['members'])==2


@pytest.mark.parametrize('role',['members','receipts'])
def test_paged_or_incomplete_reads_stop_without_success(role):
    s=Store();s.paged=role;r,s=execute(s)
    assert not r.response['success'] and s.tables['requests'][80]['Status']=='Pending' and len(s.tables['members'])==2


@pytest.mark.parametrize('request_id,decision,intent',[(0,'Accept',UUID),(80,'Cancel',UUID),(80,'Accept','not-a-uuid'),(1.5,'Accept',UUID)])
def test_invalid_inputs_cannot_read_or_write(request_id,decision,intent):
    r,s=execute(request=request_id,decision=decision,intent=intent)
    assert not r.response['success'] and not s.calls


def test_final_current_count_detects_extra_physical_row_before_commit():
    s=Store()
    def add_provisional(action,p,s):
        if action=='Final_members':
            s.hook=None;s.put('members',40,{'GroupId':10,'ParticipantId':4,'MembershipStatus':'Active','MembershipKey':'request:90:participant:4'})
    s.hook=add_provisional;r,s=execute(s)
    assert not r.response['success'] and not s.tables['requests'][80]['OperationComplete']
    assert list(s.tables['receipts'].values())[0]['Complete'] is False


def test_release_failure_replays_only_matching_completed_token():
    s=Store();s.faults['Release_completed_Write']={'status':500};r,s=execute(s)
    assert not r.response['success'] and list(s.tables['receipts'].values())[0]['Complete']
    before=deepcopy(s.tables['members']);r,s=execute(s,run='run-B')
    assert r.response['success'] and s.tables['members']==before and s.tables['groups'][10]['WriteOwner']==''


def test_exact_receipt_contract_and_write_guard_structure():
    parent=flow.build_parent(build_id='structure');metrics=measure(parent['properties']['definition']['actions'])
    assert metrics['actions']<=500 and metrics['maximumActionDepth']<=8
    assert parent['properties']['connectionReferences']['shared_sharepointonline']['source']=='Invoker'
    from scripts.power_automate.solution_source import walk
    receipt_fields={'OperationKey','IntentJson','ResultJson','Complete','Uncertain','Retryable','DomainEffects','AttemptToken','SealedAttempts','Stage'}
    for name,a in walk(parent['properties']['definition']['actions']):
        if a['type']!='OpenApiConnection':continue
        assert a['inputs']['authentication']==flow.Builder(flow.source_document(),Store().mapping,Store().groups_mapping,'test').auth
        p=a['inputs']['parameters']
        if p.get('parameters/method')=='POST':
            assert a['inputs']['retryPolicy']=={'type':'none'}
            if p['parameters/headers'].get('X-HTTP-Method')=='MERGE':assert p['parameters/headers']['IF-MATCH']!='*'
            if 'TandemOperationReceipts' in str(p['parameters/uri']):assert set(p['parameters/body'])-{'__metadata'}<=receipt_fields
            if Store().groups_mapping['lists']['groups']['listId'] in str(p['parameters/uri']):assert set(p['parameters/body'])=={'__metadata','WriteOwner'}
    assert '/fields' not in json.dumps(parent) and 'SCHEMA' not in json.dumps(parent['properties']['definition']['actions']).replace('SCHEMA_SETUP_UNVERIFIED','')


def test_definite_commit_rejection_seals_then_resumes_existing_episode():
    s=Store();s.faults['Commit_request']={'status':403};r,s=execute(s)
    assert not r.response['success'] and r.response['retryable'] and len(s.tables['members'])==3
    assert s.tables['groups'][10]['WriteOwner']=='' and not s.tables['requests'][80]['OperationComplete']
    r,s=execute(s,run='run-B');assert r.response['success'] and len(s.tables['members'])==3
    assert len([1 for n,p in s.calls if n=='Create_episode'])==1


def test_exact_group_claim_race_rejection_is_retryable_not_a_lease_takeover():
    s=Store()
    def foreign_claim(action,p,s):
        if action=='Claim_group':
            s.hook=None;s.tables['groups'][10]['WriteOwner']='other-operation|other-attempt';s.tables['groups'][10]['_v']+=1
    s.hook=foreign_claim;r,s=execute(s)
    assert not r.response['success'] and r.response['retryable']
    assert s.tables['groups'][10]['WriteOwner']=='other-operation|other-attempt' and len(s.tables['members'])==2


def test_three_sealed_attempts_require_support_and_do_not_advertise_retry():
    s=Store();s.tables['groups'][10]['WriteOwner']='foreign|held'
    for run in ['run-A','run-B','run-C']:
        r,s=execute(s,run=run);assert not r.response['success']
    assert not r.response['retryable']
    before=deepcopy(s.tables);r,s=execute(s,run='run-D');assert s.tables==before and not r.response['retryable']


def test_wrong_invoker_source_is_rejected_by_builder():
    src=flow.source_document();src['properties']['connectionReferences']['shared_sharepointonline']['source']='Embedded'
    with pytest.raises(ValueError,match='Invoker'):flow.build_parent(src)


def test_changed_relevant_profile_after_shared_result_requires_fresh_retry():
    s=Store()
    def pause_after_result(action,p,s):
        if action=='Read_fresh_context_profile' and p.get('id')==3:
            s.hook=None;s.profiles[3]['ParticipationStatus']=None
    s.hook=pause_after_result;r,s=execute(s)
    assert not r.response['success'] and s.tables['requests'][80]['Status']=='Pending' and len(s.tables['members'])==2
    assert r.response['retryable'] and s.tables['groups'][10]['WriteOwner']==''


def test_parent_entry_points_and_component_receipt(tmp_path):
    output=tmp_path/'group-response.definition.json';review=flow.build_package(output)
    parent=json.loads(output.read_text());assert parent['properties']['definition']['triggers']==flow.trigger()
    assert measure(parent['properties']['definition']['actions'])=={k:review[k] for k in ['actions','maximumActionDepth']}
    assert review['tenantResult']=='NOT_RUN' and not review['ordinaryUserAccessVerified']
    assert not {'metadata','creator'} & set(parent['properties']['definition'])
    with pytest.raises(FileExistsError):flow.build_package(output)


def test_sealed_prefix_release_failure_is_finished_before_new_attempt_claim():
    s=Store();s.faults['Create_episode']={'status':403};s.faults['Release_completed_Write']={'status':500}
    first,s=execute(s);assert not first.response['success'] and s.tables['groups'][10]['WriteOwner']
    row=list(s.tables['receipts'].values())[0];assert row['Retryable'] and json.loads(row['SealedAttempts'])==['run-A']
    second,s=execute(s,run='run-B');assert second.response['success'],(second.response,second.action_states)
    names=[n for n,p in s.calls];assert names.index('Release_prior_sealed_Write')<names.index('Claim_retry')
    assert len(s.tables['members'])==3 and s.tables['groups'][10]['WriteOwner']==''


@pytest.mark.parametrize('action,role,id',[('Before_claim','groups',10),('Claim_stage_Read','receipts',1),('Claim_stage_Confirm','receipts',1)])
def test_combined_etag_guards_reject_wildcard_readbacks_before_group_claim(action,role,id):
    s=Store()
    def wildcard(action_name,p,s):
        if action_name==action:
            s.hook=None;row=s.row(role,id);row['__metadata']['etag']='*';s.faults[action]={'status':200,'body':{'d':row}}
    s.hook=wildcard;r,s=execute(s)
    assert not r.response['success'] and s.tables['requests'][80]['Status']=='Pending'
    assert not any(name=='Claim_group' for name,p in s.calls) and len(s.tables['members'])==2


def test_decline_authority_does_not_depend_on_another_members_provisional_join():
    s=Store();s.put('requests',90,{'RequestType':'Group','TargetGroupId':10,'SenderParticipantId':4,'Status':'Accepted','OperationComplete':False})
    s.put('members',30,{'GroupId':10,'ParticipantId':4,'MembershipStatus':'Active','MembershipKey':'request:90:participant:4'})
    before=deepcopy(s.tables['members']);r,s=execute(s,decision='Decline')
    assert r.response['success'] and r.response['resultcode']=='DECLINED' and s.tables['members']==before


@pytest.mark.parametrize('variant',['closed','full','requesterUnavailable'])
def test_decline_pending_after_group_closed_full_or_requester_unavailable(variant):
    s=Store()
    if variant=='closed':s.tables['groups'][10]['State']='Closed'
    if variant=='full':s.tables['groups'][10]['Capacity']=2
    if variant=='requesterUnavailable':s.profiles[3]['ParticipationStatus']={'Value':'Paused'};s.profiles[3]['OpenToConnections']=False
    before=deepcopy(s.tables['members']);state=s.tables['groups'][10]['State']
    r,s=execute(s,decision='Decline')
    assert r.response['success'] and r.response['resultcode']=='DECLINED'
    assert s.tables['requests'][80]['Status']=='Declined' and s.tables['requests'][80]['OperationComplete']
    assert s.tables['requests'][80]['ConnectionKey']=='history:request:80'
    assert s.tables['members']==before and s.tables['groups'][10]['State']==state and not s.child_calls


@pytest.mark.parametrize('decision,full',[('Accept',False),('Decline',False),('Accept',True)])
@pytest.mark.parametrize('persist',[False,True])
def test_shared_completion_unknown_response_keeps_receipt_before_release(decision,full,persist):
    s=Store()
    if full:s.tables['groups'][10]['Capacity']=2
    s.faults['Complete_receipt_Write']={'status':500,'persist':persist}
    r,s=execute(s,decision=decision)
    receipt=list(s.tables['receipts'].values())[0]
    if persist:
        assert receipt['Complete'] and s.tables['groups'][10]['WriteOwner']==''
        assert r.response['success']==(not full)
    else:
        assert not r.response['success'] and not receipt['Complete']
        assert s.tables['groups'][10]['WriteOwner'] and r.response['resultjson']=='{}'
    names=[n for n,p in s.calls]
    if 'Release_completed_Write' in names:assert names.index('Complete_receipt_Write')<names.index('Release_completed_Write')
    assert len(s.tables['members'])==(3 if decision=='Accept' and not full else 2)


@pytest.mark.parametrize('decision,full',[('Accept',False),('Decline',False),('Accept',True)])
def test_shared_completion_rechecks_partial_receipt_before_releasing(decision,full):
    s=Store()
    if full:s.tables['groups'][10]['Capacity']=2
    s.faults['Complete_receipt_Confirm']={'status':200,'body':{'d':{}}}
    r,s=execute(s,decision=decision)
    assert list(s.tables['receipts'].values())[0]['Complete'] and s.tables['groups'][10]['WriteOwner']==''
    assert r.response['success']==(not full)
    assert any(n=='Completion_retry_readback' for n,p in s.calls)


def test_common_definite_boundary_cannot_update_a_foreign_attempt():
    s=Store();s.faults['Create_episode']={'status':403}
    def replace_attempt(action,p,s):
        if action=='Confirm_definite_boundary_Read':
            s.hook=None;receipt=s.tables['receipts'][1];receipt['AttemptToken']='foreign-attempt';receipt['_v']+=1
    s.hook=replace_attempt;r,s=execute(s)
    receipt=s.tables['receipts'][1]
    assert not r.response['success'] and not receipt['Complete'] and receipt['Uncertain']
    assert receipt['AttemptToken']=='foreign-attempt' and s.tables['groups'][10]['WriteOwner']
    assert not any(n=='Confirm_definite_boundary_Write' for n,p in s.calls)


def test_receipt_patch_uses_fresh_sealed_history_without_snapshot_copy():
    s=Store();s.tables['groups'][10]['WriteOwner']='other-operation|held'
    def extend_history(action,p,s):
        if action=='Seal_stopped_Read':
            s.hook=None;receipt=s.tables['receipts'][1];receipt['SealedAttempts']='["prior-sealed"]';receipt['_v']+=1
    s.hook=extend_history;r,s=execute(s)
    assert not r.response['success'] and r.response['retryable']
    assert json.loads(s.tables['receipts'][1]['SealedAttempts'])==['prior-sealed','run-A']
    assert s.tables['groups'][10]['WriteOwner']=='other-operation|held'


def test_shared_completion_cas_rejects_changed_receipt_attempt():
    s=Store()
    def replace_attempt(action,p,s):
        if action=='Complete_receipt_Write':
            s.hook=None;receipt=s.tables['receipts'][1];receipt['AttemptToken']='foreign-attempt';receipt['_v']+=1
    s.hook=replace_attempt;r,s=execute(s)
    assert not r.response['success'] and not s.tables['receipts'][1]['Complete']
    assert s.tables['groups'][10]['WriteOwner'] and r.response['resultjson']=='{}'


@pytest.mark.parametrize('action',['Group_list','Request_list','Member_list'])
def test_reused_error_code_still_reports_later_metadata_failure(action):
    s=Store();s.faults[action]={'status':200,'body':{'d':{}}};r,s=execute(s)
    assert not r.response['success'] and r.response['resultcode']=='SCHEMA_SETUP_UNVERIFIED'
    assert not s.tables['receipts'] and s.tables['requests'][80]['Status']=='Pending'


def test_direct_source_snapshot_still_requires_exact_source_and_tag():
    s=Store()
    def wrong_source(action,p,s):
        if action=='Initial_Source':
            s.hook=None;row=s.row('requests',70);row['Id']=71;s.faults[action]={'status':200,'body':{'d':row}}
    s.hook=wrong_source;r,s=execute(s)
    assert not r.response['success'] and not s.tables['receipts']


def test_one_shared_completion_boundary_and_final_release_are_emitted():
    from scripts.power_automate.solution_source import walk
    actions=flow.build_actions();rows=list(walk(actions));names=[n for n,a in rows]
    assert measure(actions)['actions']<=397
    assert names.count('Complete_receipt_Write')==1 and names.count('Confirm_definite_boundary_Write')==1
    assert names.count('Release_completed_Write')==1 and names.count('Release_prior_sealed_Write')==1
    assert 'Release_sealed_Write' not in names and 'Recover_receipt_only' not in names
    completion_writes=[n for n,a in rows if a['type']=='OpenApiConnection' and a.get('inputs',{}).get('parameters',{}).get('parameters/body',{}).get('Complete') is True]
    assert completion_writes==['Complete_receipt_Write']
