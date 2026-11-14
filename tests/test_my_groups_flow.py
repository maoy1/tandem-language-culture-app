"""Execute #64 emitted graph with synthetic REST; not tenant/access proof."""
from copy import deepcopy
import hashlib
import json
import re
from pathlib import Path
from zipfile import ZipFile

import pytest
from test_discovery_flow import FlowRunner
from scripts.power_automate import my_groups_flow as flow
from scripts.power_automate.solution_source import RAW_INVOKER, walk
from scripts.power_automate.schema_audit import measure

PEOPLE=json.loads((flow.ROOT/'config/tenant_schema_mapping.json').read_text())
GROUPS=json.loads((flow.ROOT/'config/group_schema_mapping.json').read_text())
SITE='https://example.sharepoint.com/sites/test'


def source():
    return {'properties': {'connectionReferences': {'shared_sharepointonline': {'source':'Invoker'}},
        'definition': {'triggers':flow.build_trigger(), 'actions': {'Read_participant': {'inputs': {
            'host': {'apiId':'/providers/Microsoft.PowerApps/apis/shared_sharepointonline','operationId':'HttpRequest','connectionName':'shared_sharepointonline'},
            'parameters':{'dataset':SITE,'table':PEOPLE['lists']['participants']['listId']},
            'authentication':{'type':'Raw','value':RAW_INVOKER}}}}}}}


def profile(i):
    return {'Id':i, 'Participantaccount':{'Title':f'Person {i}','Email':'PRIVATE_EMAIL','Claims':'PRIVATE_CLAIMS'},
        'TeachlanguagesId':{'results':[1]},'LearnlanguagesId':{'results':[2]},'ShareCulturesId':{'results':[5]},
        'LearnCulturesId':{'results':[6]},'TimezoneId':None,'Learningfocus':f'Focus {i}','Comments':f'Comments {i}',
        'Status':'PRIVATE_VALIDATION','ParticipationStatus':'Paused','OpenToConnections':False,
        'Title':'PRIVATE_TECHNICAL_TITLE','Created':'PRIVATE_AUDIT','SECRET':'PRIVATE_PROFILE'}


def request(i,sender=1,recipient=2,group=None,complete=True,status='Accepted'):
    return {'Id':i,'SenderParticipantId':sender,'RecipientParticipantId':recipient,'TargetGroupId':group,
        'RequestType':'Personal' if group is None else 'Group','Status':status,'OperationComplete':complete,
        'WinningOperationKey':'PRIVATE_WINNER','ConnectionKey':'PRIVATE_CONNECTION'}


def group(i=10,source_id=100,state='Open',capacity=3):
    return {'Id':i,'Title':f'Group {i}','Purpose':f'Purpose {i}','ExchangeType':'Combined',
        'LanguageFocusId':{'results':[1]},'CultureFocusId':{'results':[5]},'Capacity':capacity,'State':state,
        'SourceRequestId':source_id,'SetupComplete':True,'__metadata':{'etag':'"7"','uri':'PRIVATE_URI'},
        'WriteOwner':'PRIVATE_OWNER','Created':'PRIVATE_AUDIT','SECRET':'PRIVATE_GROUP'}


def membership(i=20,g=10,p=1,request_id=100,status='Active',left=None):
    return {'Id':i,'GroupId':g,'ParticipantId':p,'MembershipStatus':status,
        'MembershipKey':f'request:{request_id}:participant:{p}','LeftAt':left,
        'JoinedAt':'PRIVATE_JOINED','SECRET':'PRIVATE_MEMBERSHIP'}


class Fake:
    def __init__(self):
        self.data={'requests':[],'groups':[],'memberships':[],'profiles':[profile(i) for i in range(1,6)],
            'language':[{'Id':1,'Title':'French','Active':False},{'Id':2,'Title':'German','Active':True}],
            'culture':[{'Id':5,'Title':'Culture A','Active':False},{'Id':6,'Title':'Culture B','Active':True}],
            'timezone':[{'Id':9,'Title':'Berlin','IANA_ID':'Europe/Berlin','Active':False}]}
        self.own=[{'Id':1}];self.queries=[];self.fail=None;self.null=None;self.paged=None;self.overflow=None
    def populate(self,g=10,source_id=100,other=2):
        self.data['groups'].append(group(g,source_id))
        self.data['requests'].append(request(source_id,recipient=other))
        self.data['memberships'] += [membership(g*10,g,1,source_id),membership(g*10+1,g,other,source_id)]
    def request(self,p):
        assert p['parameters/method']=='GET'
        uri=p['parameters/uri'];self.queries.append(uri)
        if self.fail and self.fail in uri:return {'statusCode':502,'body':{'error':'PRIVATE_BACKEND'}}
        if uri.startswith('_api/web/currentuser'):return {'statusCode':200,'body':{'d':{'Id':101}}}
        if 'ParticipantaccountId eq' in uri:role='own';data=deepcopy(self.own)
        else:
            targets={'requests':flow.REQUESTS,'profiles':PEOPLE['lists']['participants']['listId'],
                'groups':GROUPS['lists']['groups']['listId'],'memberships':GROUPS['lists']['members']['listId'],
                **{r:PEOPLE['lists'][r]['listId'] for r in ['language','culture','timezone']}}
            role=next(r for r,target in targets.items() if target in uri);data=deepcopy(self.data[role])
            assert '/fields' not in uri and 'BaseTemplate' not in uri
            assert '$orderby=Id asc' in uri
        if role==self.overflow:data=[(data or [{}])[0]]*(flow.BOUNDS.get(role,1)+1)
        d={'results':None if role==self.null else data}
        if role==self.paged:d['__next']='PRIVATE_NEXT'
        return {'statusCode':200,'body':{'d':d}}


class GroupsRunner(FlowRunner):
    def parse_content(self,value,schema):
        # The reusable subset validator omits maxLength/pattern. Enforce those
        # independently for nested production schemas (especially public ETag).
        def extra(v,s):
            if isinstance(v,str):
                assert len(v)<=s.get('maxLength',10**9)
                if 'pattern' in s:assert re.fullmatch(s['pattern'],v)
            if isinstance(v,dict):
                for key,rule in s.get('properties',{}).items():
                    if key in v:extra(v[key],rule)
            if isinstance(v,list):
                for row in v:extra(row,s.get('items',{}))
        extra(value,schema);return value


def execute(server=None,actor=1,actions=None):
    runner=GroupsRunner(server or Fake(),actor)
    runner.run(actions or flow.build_actions(source(),PEOPLE,GROUPS,'local-build'))
    assert runner.response is not None,runner.action_states
    return runner


def public(r):return json.loads(r.response['groupsjson'])
def failure(r,code=None):
    assert r.response['resultcode']!='OK'
    if code:assert r.response['resultcode']==code
    assert public(r)==[] and r.response['groupstatus']==''
    assert 'PRIVATE_' not in json.dumps(r.response)


def test_empty_is_waiting_no_writes_and_current_actor_bound():
    server=Fake();before=deepcopy(server.data);r=execute(server)
    assert r.response['resultcode']=='OK' and public(r)==[] and r.response['groupstatus']=='Waiting'
    assert server.data==before
    assert len(server.queries)==9 and 'ParticipantaccountId eq 101' in server.queries[1]


def test_committed_own_group_approved_display_and_only_revision_marker():
    server=Fake();server.populate();before=deepcopy(server.data);r=execute(server)
    assert r.response['resultcode']=='OK' and r.response['groupstatus']=='In a group'
    row=public(r)[0]
    assert row['groupId']==10 and row['name']=='Group 10' and row['purpose']=='Purpose 10'
    assert row['memberCount']==2 and row['freeSlots']==1 and row['expectedETag']=='"7"'
    assert [p['displayName'] for p in row['members']]==['Person 1','Person 2']
    assert row['members'][0]['teachLanguages']==[{'id':1,'label':'French'}] # inactive/history still displayed
    assert row['members'][0]['comments']=='Comments 1'
    assert row['members'][0]['timeZone']=={'id':None,'label':None,'ianaId':None}
    assert server.data==before
    text=json.dumps(r.response)
    assert not any(x in text for x in ['PRIVATE_','Email','Claims','WriteOwner','SourceRequestId','MembershipKey','OperationComplete','ParticipationStatus'])
    assert set(row)==set(flow.public_group_schema()['properties'])
    assert set(row['members'][0])==set(flow.public_profile_schema()['properties'])


@pytest.mark.parametrize('state',['Open','Closed','Ended'])
def test_all_own_states_remain_visible_without_mutation(state):
    server=Fake();server.populate();server.data['groups'][0]['State']=state
    before=deepcopy(server.data);r=execute(server)
    assert r.response['resultcode']=='OK' and public(r)[0]['state']==state
    assert r.response['groupstatus']=='In a group' and server.data==before


def test_multiple_current_groups_plus_left_history():
    server=Fake();server.populate();server.populate(11,101,3);server.populate(12,102,4)
    server.data['memberships'][-2].update(MembershipStatus='Left',LeftAt='2026-01-01')
    r=execute(server)
    assert [x['groupId'] for x in public(r)]==[10,11]
    assert r.response['groupstatus']=='In a group'
    assert [x['memberCount'] for x in public(r)]==[2,2]


@pytest.mark.parametrize('variant',['left','leftAt','provisional','sourceIncomplete','sourcePending','setupIncomplete','wrongParty','wrongGroup','noSource','noGroup'])
def test_uncommitted_or_history_own_episode_is_not_current(variant):
    server=Fake();server.populate();m=server.data['memberships'][0];g=server.data['groups'][0];req=server.data['requests'][0]
    if variant=='left':m['MembershipStatus']='Left'
    if variant=='leftAt':m['LeftAt']='2026-01-01'
    if variant=='provisional':m['MembershipKey']='request:999:participant:1'
    if variant=='sourceIncomplete':req['OperationComplete']=False
    if variant=='sourcePending':req['Status']='Pending'
    if variant=='setupIncomplete':g['SetupComplete']=False
    if variant=='wrongParty':req.update(SenderParticipantId=3,RecipientParticipantId=4)
    if variant=='wrongGroup':m['GroupId']=99
    if variant=='noSource':g['SourceRequestId']=999
    if variant=='noGroup':server.data['groups']=[]
    r=execute(server)
    assert r.response['resultcode']=='OK' and public(r)==[] and r.response['groupstatus']=='Waiting'


def test_group_join_episode_needs_exact_actor_group_and_both_commits():
    server=Fake();server.populate();server.data['requests'].append(request(200,3,None,10))
    server.data['memberships'].append(membership(103,10,3,200))
    # Actor 3 resolves to their own profile; history/paused availability does not gate membership.
    server.own=[{'Id':3}];r=execute(server,3)
    assert r.response['resultcode']=='OK' and public(r)[0]['memberCount']==3
    assert [m['profileId'] for m in public(r)[0]['members']]==[1,2,3]


@pytest.mark.parametrize('variant',['incomplete','wrongSender','wrongGroup','wrongRecipient','wrongKey','sourceIncomplete'])
def test_bad_group_join_episode_cannot_authorize_current_group(variant):
    server=Fake();server.populate();req=request(200,3,None,10);m=membership(103,10,3,200)
    if variant=='incomplete':req['OperationComplete']=False
    if variant=='wrongSender':req['SenderParticipantId']=4
    if variant=='wrongGroup':req['TargetGroupId']=11
    if variant=='wrongRecipient':req['RecipientParticipantId']=2
    if variant=='wrongKey':m['MembershipKey']='request:200:participant:4'
    if variant=='sourceIncomplete':server.data['requests'][0]['OperationComplete']=False
    server.data['requests'].append(req);server.data['memberships'].append(m);server.own=[{'Id':3}]
    r=execute(server,3);assert r.response['resultcode']=='OK' and public(r)==[]


def test_physical_active_provisional_and_paused_count_but_public_only_committed():
    server=Fake();server.populate();server.data['memberships'].append(membership(103,10,3,999))
    r=execute(server);row=public(r)[0]
    assert row['memberCount']==3 and row['freeSlots']==0
    assert [m['profileId'] for m in row['members']]==[1,2]
    assert all(p['ParticipationStatus']=='Paused' for p in server.data['profiles'])


def test_left_member_neither_public_nor_capacity_and_paused_committed_remains():
    server=Fake();server.populate();server.data['memberships'][1].update(MembershipStatus='Left',LeftAt='2026-01-01')
    row=public(execute(server))[0]
    assert row['memberCount']==1 and row['freeSlots']==2 and [p['profileId'] for p in row['members']]==[1]


@pytest.mark.parametrize('actor,own',[(2,[{'Id':1}]),(1,[]),(1,[{'Id':1},{'Id':2}]),(1,[{'Id':2}])])
def test_invoker_unique_own_profile_not_supplied_actor(actor,own):
    server=Fake();server.own=own;failure(execute(server,actor),'UNAUTHORIZED_PROFILE')
    assert len(server.queries)==2


@pytest.mark.parametrize('actor',[None,0,-1,1.5,'1',True])
def test_bad_input_never_reads(actor):
    server=Fake();failure(execute(server,actor));assert server.queries==[]


@pytest.mark.parametrize('role',list(flow.BOUNDS)[:-1]+['own'])
@pytest.mark.parametrize('variant',['null','paged','overflow'])
def test_incomplete_bounds_fail_closed(role,variant):
    server=Fake();server.populate();setattr(server,variant,role)
    failure(execute(server),'UNAUTHORIZED_PROFILE' if role=='own' else 'READ_BOUND_OR_INCOMPLETE')


@pytest.mark.parametrize('spelling',['@odata.nextLink','odata.nextLink'])
def test_other_native_nextlinks_are_rejected(spelling):
    server=Fake();server.populate();original=server.request
    def request_(params):
        result=original(params)
        if flow.REQUESTS in params['parameters/uri']:result['body'][spelling]='PRIVATE_NEXT'
        return result
    server.request=request_;failure(execute(server),'READ_BOUND_OR_INCOMPLETE')


@pytest.mark.parametrize('role',list(flow.BOUNDS)[:-1])
def test_duplicate_row_ids_fail_closed(role):
    server=Fake();server.populate();server.data[role].append(deepcopy(server.data[role][0]))
    failure(execute(server),'DATA_INTEGRITY')


def test_duplicate_active_episode_fails_even_with_different_row_id():
    server=Fake();server.populate();server.data['memberships'].append({**server.data['memberships'][0],'Id':999})
    failure(execute(server),'MEMBERSHIP_INTEGRITY')


@pytest.mark.parametrize('capacity,exchange',[(1,'Combined'),(11,'Combined'),(4,'Language'),(2.5,'Combined')])
def test_invalid_capacity_never_truncates_or_returns_negative_free_slots(capacity,exchange):
    server=Fake();server.populate();server.data['groups'][0].update(Capacity=capacity,ExchangeType=exchange)
    failure(execute(server))


def test_overfull_physical_active_is_integrity_error():
    server=Fake();server.populate();server.data['groups'][0]['Capacity']=2
    server.data['memberships'].append(membership(103,10,3,999))
    failure(execute(server),'CAPACITY_INTEGRITY')


@pytest.mark.parametrize('field,value',[('SenderParticipantId',1.5),('RecipientParticipantId',2.5),('OperationComplete',None)])
def test_malformed_commit_data_fails_closed(field,value):
    server=Fake();server.populate();server.data['requests'][0][field]=value
    failure(execute(server),'DATA_INTEGRITY')


@pytest.mark.parametrize('value',['PRIVATE_ETAG','*','7','"7" PRIVATE_','',None])
def test_revision_is_only_etag_never_arbitrary_private_marker(value):
    server=Fake();server.populate();server.data['groups'][0]['__metadata']['etag']=value
    failure(execute(server),'DATA_INTEGRITY')


@pytest.mark.parametrize('variant',['missingProfile','missingLabel','missingZone','missingGroupFocus','badProfileType'])
def test_incomplete_public_projection_fails_closed(variant):
    server=Fake();server.populate()
    if variant=='missingProfile':server.data['profiles']=server.data['profiles'][1:]
    if variant=='missingLabel':server.data['language']=server.data['language'][1:]
    if variant=='missingZone':server.data['profiles'][0]['TimezoneId']=999
    if variant=='missingGroupFocus':server.data['groups'][0]['CultureFocusId']={'results':[999]}
    if variant=='badProfileType':server.data['profiles'][0]['Comments']={'Secret':'PRIVATE_DATA'}
    failure(execute(server))


def test_later_projection_failure_clears_prior_authorized_group():
    server=Fake();server.populate();server.populate(11,101,3)
    server.data['groups'][1]['CultureFocusId']={'results':[999]}
    r=execute(server);failure(r,'GROUP_DATA_INCOMPLETE')
    assert r.variables['Groups']==[]


@pytest.mark.parametrize('fail',['currentuser','ParticipantaccountId eq',flow.REQUESTS,PEOPLE['lists']['participants']['listId'],PEOPLE['lists']['language']['listId']])
def test_backend_errors_are_sanitized(fail):
    server=Fake();server.fail=fail;failure(execute(server))


def test_optional_profile_values_and_deduplicated_display_labels_not_eligibility():
    server=Fake();server.populate();p=server.data['profiles'][0]
    for key in ['TeachlanguagesId','LearnlanguagesId','ShareCulturesId','LearnCulturesId','TimezoneId','Learningfocus','Comments']:p.pop(key,None)
    p['TeachlanguagesId']={'results':[1,1]}
    row=public(execute(server))[0]['members'][0]
    assert row['teachLanguages']==[{'id':1,'label':'French'}] and row['learnLanguages']==[]
    assert row['comments']==row['learningFocus']==''


def test_structure_full_actions_unique_names_get_only_and_no_child():
    graph=flow.build_actions(source(),PEOPLE,GROUPS,'local-build');report=measure(graph)
    assert report['actions']<=500 and report['maximumActionDepth']<=8
    names=[n for n,_ in walk(graph)];assert len(names)==len(set(names))
    reads=[a for _,a in walk(graph) if a['type']=='OpenApiConnection']
    assert len(reads)==9 and not any(a['type']=='Workflow' for _,a in walk(graph))
    assert all(a['inputs']['parameters']['parameters/method']=='GET' for a in reads)
    assert all(a['inputs']['authentication']=={'type':'Raw','value':RAW_INVOKER} for a in reads)
    assert not any('/fields' in a['inputs']['parameters']['parameters/uri'] for a in reads)
    assert not any('my_requests_flow' in line for line in Path(flow.__file__).read_text().splitlines())


@pytest.mark.parametrize('variant',['embedded','auth','target','trigger','connector'])
def test_unverified_source_is_rejected(variant):
    original=source();p=original['properties'];i=p['definition']['actions']['Read_participant']['inputs']
    if variant=='embedded':p['connectionReferences']['shared_sharepointonline']['source']='Embedded'
    if variant=='auth':i['authentication']['value']='PRIVATE_OWNER'
    if variant=='target':i['parameters']['table']='wrong'
    if variant=='trigger':p['definition']['triggers']['manual']['kind']='Button'
    if variant=='connector':i['host']['apiId']='custom_connector'
    with pytest.raises(ValueError):flow.build_actions(original,PEOPLE,GROUPS,'x')


@pytest.mark.parametrize('field',['Capacity','SourceRequestId'])
def test_whole_native_number_group_values_canonicalized_before_public_projection(field):
    server=Fake();server.populate();server.data['groups'][0][field]=float(server.data['groups'][0][field])
    r=execute(server);assert r.response['resultcode']=='OK'
    assert type(public(r)[0]['capacity']) is int


def test_fractional_source_reference_cannot_bind_group():
    server=Fake();server.populate();server.data['groups'][0]['SourceRequestId']=100.5
    failure(execute(server),'DATA_INTEGRITY')


def test_native_parent_builder_preserves_invoker_and_uses_no_business_dependency(tmp_path,monkeypatch):
    from test_solution_source import export_fixture
    from scripts.power_automate import solution_source as native
    path=tmp_path/'native.zip';export_fixture(path)
    inspect=native.inspect_caller_export
    monkeypatch.setattr(flow,'inspect_caller_export',lambda p,s,b:inspect(p,SITE,'unit-build'))
    output=tmp_path/'groups.definition.json';review=flow.build_parent(path,output)
    document=json.loads(output.read_text());props=document['properties']
    assert props['definition']['triggers']==flow.build_trigger()
    assert props['connectionReferences']['shared_sharepointonline']['runtimeSource']=='invoker'
    assert review['nativeStatus']=='NOT_IMPORTED_NOT_TESTED' and review['sharedChildRequired'] is False
    assert review['definitionSha256']==hashlib.sha256(output.read_bytes()).hexdigest()
    assert execute(Fake(),actions=props['definition']['actions']).response['resultcode']=='OK'
    with pytest.raises(FileExistsError):flow.build_parent(path,output)


def test_response_bound_never_truncates_or_returns_partial_groups():
    server=Fake();server.populate();server.data['groups'][0]['Capacity']=10
    for i in [3,4,5]:
        server.data['requests'].append(request(200+i,i,None,10))
        server.data['memberships'].append(membership(200+i,10,i,200+i))
    for p in server.data['profiles']:p['Comments']='x'*64000
    failure(execute(server),'RESPONSE_BOUND')


def test_weak_native_group_revision_is_allowed_only_as_expected_etag():
    server=Fake();server.populate();server.data['groups'][0]['__metadata']['etag']='W/"8"'
    assert public(execute(server))[0]['expectedETag']=='W/"8"'


def test_delivered_artifact_hash_source_and_real_graph_match_contract():
    path=flow.ROOT/'artifacts/my_groups/TandemMyGroups-v2.definition.json'
    review=json.loads(path.with_suffix('.review.json').read_text())
    assert review['definitionSha256']==hashlib.sha256(path.read_bytes()).hexdigest()
    assert review['generatorSha256']==hashlib.sha256(Path(flow.__file__).read_bytes()).hexdigest()
    graph=json.loads(path.read_text())['properties']['definition']['actions']
    assert measure(graph)=={'actions':review['actions'],'maximumActionDepth':review['maximumActionDepth']}
    server=Fake();server.populate();before=deepcopy(server.data)
    result=execute(server,actions=graph)
    assert result.response['resultcode']=='OK' and len(public(result))==1 and server.data==before


def test_group_membership_id_is_only_callers_exact_committed_episode():
    server=Fake();server.populate();server.populate(11,101,3)
    for m,identifier in zip(server.data['memberships'],[641001,641002,642001,642002]):m['Id']=identifier
    server.data['memberships'].insert(0,membership(649900,10,1,90,status='Left',left='2026-01-01'))
    before=deepcopy(server.data);result=execute(server);rows=public(result)
    assert result.response['resultcode']=='OK'
    assert {row['groupId']:row['membershipId'] for row in rows}=={10:641001,11:642001}
    assert all(type(row['membershipId']) is int and row['membershipId']>0 for row in rows)
    assert all('membershipId' not in member for row in rows for member in row['members'])
    assert not any(str(identifier) in json.dumps(result.response) for identifier in [641002,642002,649900])
    assert server.data==before
