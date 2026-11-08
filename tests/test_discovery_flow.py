"""Generated #7 graph execution with fake connector; not caller/tenant proof."""
from collections import defaultdict
from copy import deepcopy
import json
from pathlib import Path
from zipfile import ZipFile
import pytest
from test_compatibility_generated import Runner
from test_coordination_fixture import walk
from scripts.power_automate import discovery_flow as discovery

ROOT=discovery.ROOT
PEOPLE=json.loads((ROOT/'config/tenant_schema_mapping.json').read_text(encoding='utf-8'))
GROUPS=json.loads((ROOT/'config/group_schema_mapping.json').read_text(encoding='utf-8'))


def source():
    common={'host':{'apiId':'/providers/Microsoft.PowerApps/apis/shared_sharepointonline','connectionName':'shared_sharepointonline'},'authentication':{'type':'Raw','value':'SOURCE_INVOKER_TOKEN_EXPRESSION'}}
    return {'properties':{'connectionReferences':{'shared_sharepointonline':{'source':'Invoker'}},'definition':{
      'triggers':{'manual':{'type':'Request','kind':'PowerAppV2','inputs':{'schema':{'type':'object','properties':{'number':{'type':'number'}},'required':['number']}}}},
      'actions':{'Get_item':{'type':'OpenApiConnection','inputs':{**deepcopy(common),'parameters':{'dataset':'https://example.sharepoint.com/sites/test','table':PEOPLE['lists']['participants']['listId'],'id':"@triggerBody()?['number']"}}},
       'Candidate_source':{'type':'OpenApiConnection','inputs':{**deepcopy(common),'parameters':{'$filter':"Status eq 'Active'",'$top':501}}},
       'Respond_to_a_Power_App_or_flow':{'type':'Response','kind':'PowerApp','inputs':{'statusCode':200,'schema':{'type':'object','properties':{k:{'type':'string'} for k in ['candidatesjson','errormessage']}},'body':{}}}}}}}


def profile(i,teach=None,learn=None,share=None,culture=None,**overrides):
    return {'ID':i,'Participantaccount':{'Claims':'trusted-'+str(i),'DisplayName':'Person '+str(i),'Email':'PRIVATE_EMAIL_'+str(i)},
      'Status':{'Value':'Active'},'ParticipationStatus':{'Value':'Active'},'OpenToConnections':True,
      'Teachlanguages#Id':teach or [],'Learnlanguages#Id':learn or [],'ShareCultures#Id':share or [],'LearnCultures#Id':culture or [],
      'Timezone':None,'Learningfocus':'Conversation','Comments':'Approved comments','SECRET':'PRIVATE_SYSTEM_VALUE',**overrides}


class Fake:
    def __init__(self):
        self.profiles=[profile(1,[1],[2]),profile(2,[2],[1]),profile(3,[],[1])]
        self.user_id=101;self.own_id=1;self.queries=[];self.http_fail=None;self.paged=None;self.commit_schema=True
        self.groups=[];self.members=[];self.requests=[]
    def valid_group(self):
        self.groups=[{'Id':10,'Title':'Practice','ExchangeType':'Language','LanguageFocusId':{'results':[1]},'CultureFocusId':{'results':[]},'Capacity':3,'State':'Open','Purpose':'Weekly chat','SourceRequestId':70,'SetupComplete':True,'WriteOwner':''}]
        self.profiles=[profile(1,[],[1]),profile(2,[1],[]),profile(3,[],[1])]
        self.members=[{'Id':20,'GroupId':10,'ParticipantId':2,'MembershipStatus':'Active','MembershipKey':'request:70:participant:2'},
          {'Id':21,'GroupId':10,'ParticipantId':3,'MembershipStatus':'Active','MembershipKey':'request:70:participant:3'}]
        self.requests=[{'Id':70,'Status':'Accepted','OperationComplete':True}]
    def request(self,p):
        uri=p.get('parameters/uri');self.queries.append(uri or ('GetItem' if 'id' in p else 'GetItems'))
        def result(data,code=200):return {'statusCode':code,'body':deepcopy(data)}
        if uri is None:
            if 'id' in p:return result(next(x for x in self.profiles if x['ID']==p['id']))
            obj={'value':self.profiles}
            if self.paged=='profiles':obj['@odata.nextLink']='next'
            return result(obj)
        assert p['parameters/method']=='GET'
        if self.http_fail and self.http_fail in uri:return result({'error':'PRIVATE_BACKEND_ERROR'},500)
        if uri.startswith('_api/web/currentuser'):return result({'d':{'Id':self.user_id}})
        if 'ParticipantaccountId eq' in uri:return result({'d':{'results':[{'Id':self.own_id}]}})
        role=next((k for k in ['language','culture','timezone'] if PEOPLE['lists'][k]['listId'] in uri),None)
        if role:
            if role=='language':rows=[{'Id':1,'Title':'English','Active':True,'ISOcode':'en'},{'Id':2,'Title':'French','Active':True,'ISOcode':'fr'},{'Id':99,'Title':'Any language','Active':True,'ISOcode':'any'}]
            elif role=='culture':rows=[{'Id':1,'Title':'Culture A','Active':True,'CultureKey':'culture-a'}]
            else:rows=[{'Id':1,'Title':'London','Active':True,'IANA_ID':'Europe/London'}]
        elif GROUPS['lists']['groups']['listId'] in uri:role='groups';rows=self.groups
        elif GROUPS['lists']['members']['listId'] in uri:role='members';rows=self.members
        elif '/fields?' in uri:role='request-fields';rows=[{'InternalName':'OperationComplete','TypeAsString':'Boolean'}] if self.commit_schema else []
        else:role='requests';rows=self.requests
        obj={'d':{'results':rows}}
        if self.paged==role:obj['d']['__next']='next'
        return result(obj)


class Terminated(Exception):pass


def validate(value,schema):
    types=schema.get('type');types=types if isinstance(types,list) else [types]
    check={'integer':lambda:type(value)is int,'number':lambda:type(value)in [int,float], 'string':lambda:isinstance(value,str),
      'boolean':lambda:type(value)is bool,'null':lambda:value is None,'object':lambda:isinstance(value,dict),'array':lambda:isinstance(value,list)}
    assert any(t is None or check[t]() for t in types),'schema type'
    if value is None:return
    if 'enum' in schema:assert value in schema['enum']
    if isinstance(value,dict):
        assert all(k in value for k in schema.get('required',[]))
        if schema.get('additionalProperties') is False:assert set(value)<=set(schema.get('properties',{}))
        for key,rule in schema.get('properties',{}).items():
            if key in value:validate(value[key],rule)
    if isinstance(value,list):
        assert len(value)<=schema.get('maxItems',10**9)
        for item in value:validate(item,schema.get('items',{}))
    if isinstance(value,str):assert len(value)>=schema.get('minLength',0)
    if type(value)in [int,float]:assert schema.get('minimum',float('-inf'))<=value<=schema.get('maximum',float('inf'))


class FlowRunner(Runner):
    def __init__(self,server,actor=1):
        super().__init__();self.server=server;self.actor=actor;self.outputs=defaultdict(lambda:None);self.action_states={};self.response=None
    def body(self,n):
        value=self.outputs[n];return value['body'] if isinstance(value,dict) and 'statusCode'in value else value
    def run(self,actions,ctx=None):
        ctx=ctx or {'items':{},'triggerBody':{'number':self.actor}};done={};todo=dict(actions)
        while todo:
            ready=[n for n,a in todo.items() if set(a.get('runAfter',{}))<=set(done)];assert ready,'invalid graph'
            for name in ready:
                action=todo.pop(name);kind=action['type'];p=action.get('inputs',{});state='Succeeded'
                if any(done[k] not in allowed for k,allowed in action.get('runAfter',{}).items()):done[name]='Skipped';self.action_states[name]='Skipped';continue
                try:
                    if kind=='OpenApiConnection':
                        self.outputs[name]=self.server.request(self.inputs(p['parameters'],ctx))
                        if self.outputs[name]['statusCode']>=400:state='Failed'
                    elif kind=='Compose':self.outputs[name]=self.inputs(p,ctx)
                    elif kind=='ParseJson':
                        self.outputs[name]=self.inputs(p['content'],ctx);validate(self.outputs[name],p['schema'])
                    elif kind=='InitializeVariable':
                        for v in p['variables']:self.variables[v['name']]=deepcopy(v['value'])
                    elif kind=='SetVariable':self.variables[p['name']]=self.inputs(p['value'],ctx)
                    elif kind=='AppendToArrayVariable':self.variables[p['name']].append(self.inputs(p['value'],ctx))
                    elif kind in ['Query','Select']:
                        result=[]
                        for row in self.inputs(p['from'],ctx):
                            c={**ctx,'item':row}
                            if kind=='Select':result.append(self.inputs(p['select'],c))
                            elif self.expr(p['where'],c):result.append(row)
                        self.outputs[name]=result
                    elif kind=='If':
                        if not self.run(action['actions'] if self.expr(action['expression'],ctx) else action['else']['actions'],ctx):state='Failed'
                    elif kind=='Scope':
                        if not self.run(action['actions'],ctx):state='Failed'
                    elif kind=='Foreach':
                        for row in self.inputs(action['foreach'],ctx):
                            if not self.run(action['actions'],{**ctx,'items':{**ctx['items'],name:row}}):state='Failed'
                    elif kind=='Response':self.response=self.inputs(p['body'],ctx)
                    elif kind=='Terminate':raise Terminated(p)
                    else:raise RuntimeError('Unsupported '+kind)
                except (AssertionError,ZeroDivisionError,TypeError,ValueError,KeyError,IndexError):state='Failed'
                done[name]=state;self.action_states[name]=state
        return all(s!='Failed' for s in done.values())


def execute(server=None,actor=1):
    runner=FlowRunner(server or Fake(),actor);runner.run(discovery.build_actions(source(),PEOPLE,GROUPS,'fixture-only'))
    return runner


def test_owner_preview_current_profile_people_projection_and_no_writes():
    runner=execute();response=runner.response;people=json.loads(response['candidatesjson'])
    assert response['resultcode']=='OK' and [p['profileId'] for p in people]==[2,3]
    assert people[0]['fitType']=='Language' and people[0]['profile']['teachLanguages']==[{'id':2,'label':'French'}]
    assert people[0]['profile']['timeZone']=={'id':None,'label':None,'ianaId':None}
    assert not any(secret in json.dumps(response) for secret in ['PRIVATE_EMAIL','PRIVATE_SYSTEM','Claims','accountKey','trusted-'])
    assert 'GetItems' in runner.server.queries and response['groupsjson']=='[]'


@pytest.mark.parametrize('actor,own',[(2,1),(1,2)])
def test_tampered_profile_reference_does_not_read_candidates(actor,own):
    server=Fake();server.own_id=own;r=execute(server,actor)
    assert r.response['resultcode']=='UNAUTHORIZED_PROFILE' and r.response['candidatesjson']=='[]'
    assert 'GetItems' not in server.queries and 'GetItem' not in server.queries


@pytest.mark.parametrize('field,value',[('ParticipationStatus',{'Value':'Paused'}),('ParticipationStatus',{'Value':'Inactive'}),('OpenToConnections',False),('Status',{'Value':'Needs review'})])
def test_unavailable_actor_returns_no_results(field,value):
    server=Fake();server.profiles[0][field]=value;r=execute(server)
    assert r.response['resultcode']=='PROFILE_UNAVAILABLE' and r.response['candidatesjson']==r.response['groupsjson']=='[]'


@pytest.mark.parametrize('field,value',[('ParticipationStatus',{'Value':'Paused'}),('ParticipationStatus',{'Value':'Inactive'}),('ParticipationStatus',None),('OpenToConnections',False),('Status',{'Value':'Needs review'})])
def test_unavailable_candidate_excluded_without_resetting_it(field,value):
    server=Fake();server.profiles[1][field]=value;r=execute(server)
    assert r.response['resultcode']=='OK'
    assert [p['profileId'] for p in json.loads(r.response['candidatesjson'])]==[3]
    assert server.profiles[1][field]==value


def test_culture_only_and_any_language_deferred():
    server=Fake();server.profiles=[profile(1,[],[],[1],[]),profile(2,[],[],[],[1]),profile(3,[99],[99])]
    r=execute(server);people=json.loads(r.response['candidatesjson'])
    assert r.response['resultcode']=='OK' and [p['profileId'] for p in people]==[2] and people[0]['fitType']=='Culture'


def test_operational_group_projection_shared_rules_and_committed_members():
    server=Fake();server.valid_group();r=execute(server);groups=json.loads(r.response['groupsjson'])
    assert r.response['resultcode']=='OK' and len(groups)==1
    assert groups[0]['memberCount']==2 and groups[0]['freeSlots']==1 and len(groups[0]['members'])==2
    assert groups[0]['languageFocus']==[{'id':1,'label':'English'}]
    assert not any(s in json.dumps(r.response) for s in ['trusted-','PRIVATE_EMAIL','MembershipKey','SourceRequestId','WriteOwner','SetupComplete'])


@pytest.mark.parametrize('field,value',[('State','Closed'),('State','Ended'),('SetupComplete',False),('WriteOwner','active-operation')])
def test_nonjoinable_group_filtered_before_extra_readers(field,value):
    server=Fake();server.valid_group();server.groups[0][field]=value;server.commit_schema=False;r=execute(server)
    assert r.response['resultcode']=='OK' and r.response['groupsjson']=='[]'


@pytest.mark.parametrize('variant',['full','invalidFocus','unavailableSharer','existingMember','uncommittedSource','uncommittedEpisode','leftSharer','duplicateMember'])
def test_group_eligibility_does_not_mutate_state_or_history(variant):
    server=Fake();server.valid_group()
    if variant=='full':server.groups[0]['Capacity']=2
    if variant=='invalidFocus':server.groups[0]['LanguageFocusId']={'results':[2]}
    if variant=='unavailableSharer':server.profiles[1]['ParticipationStatus']={'Value':'Paused'}
    if variant=='existingMember':server.members[1].update(ParticipantId=1,MembershipKey='request:70:participant:1')
    if variant=='uncommittedSource':server.requests[0]['OperationComplete']=False
    if variant=='uncommittedEpisode':server.members[1]['MembershipKey']='request:71:participant:3'
    if variant=='leftSharer':server.members[0]['MembershipStatus']='Left'
    if variant=='duplicateMember':server.members.append({**server.members[0],'Id':22})
    before=deepcopy((server.groups,server.members,server.requests));r=execute(server)
    assert r.response['resultcode']=='OK' and r.response['groupsjson']=='[]'
    assert (server.groups,server.members,server.requests)==before


def test_missing_commit_schema_fails_explicitly_no_partial_people():
    server=Fake();server.valid_group();server.commit_schema=False;r=execute(server)
    assert r.response['resultcode']=='GROUP_COMMIT_SCHEMA_UNVERIFIED' and r.response['candidatesjson']==r.response['groupsjson']=='[]'


@pytest.mark.parametrize('page',['profiles','groups','members','requests','language','request-fields'])
def test_paged_or_over_bound_read_never_returns_partial_success(page):
    server=Fake();server.valid_group();server.paged=page;r=execute(server)
    assert r.response['resultcode']!='OK' and r.response['candidatesjson']==r.response['groupsjson']=='[]'


def test_failed_backend_read_sanitizes_response():
    server=Fake();server.http_fail='/currentuser';r=execute(server)
    assert r.response['resultcode']=='READ_OR_DATA_FAILED' and 'PRIVATE_BACKEND_ERROR' not in json.dumps(r.response)
    assert 'GetItems' not in server.queries


def test_oversized_response_returns_explicit_bound():
    server=Fake();server.profiles[1]['Comments']='x'*250001;r=execute(server)
    assert r.response['resultcode']=='RESPONSE_BOUND' and r.response['candidatesjson']==r.response['groupsjson']=='[]'


def test_preserve_source_invoker_and_trigger_no_owner_fallback():
    original=source();actions=discovery.build_actions(original,PEOPLE,GROUPS,'fixture-only')
    for _,a in walk(actions):
        if a['type']=='OpenApiConnection':
            assert a['inputs']['authentication']==original['properties']['definition']['actions']['Get_item']['inputs']['authentication']
            p=a['inputs']['parameters'];assert p.get('parameters/method','GET')=='GET'
    original['properties']['connectionReferences']['shared_sharepointonline']['source']='Embedded'
    with pytest.raises(ValueError,match='Invoker'):discovery.build_actions(original,PEOPLE,GROUPS,'fixture-only')


@pytest.mark.parametrize('dataset,bound',[('profiles',500),('groups',100),('members',2000),('requests',500),('language',5000)])
def test_count_bounds_without_next_link_also_fail(dataset,bound):
    server=Fake();server.valid_group();request=server.request
    def overfull(p):
        response=request(p);uri=p.get('parameters/uri','')
        role=('profiles' if not uri and 'id' not in p else
              'groups' if GROUPS['lists']['groups']['listId'] in uri else
              'members' if GROUPS['lists']['members']['listId'] in uri else
              'language' if PEOPLE['lists']['language']['listId'] in uri else
              'requests' if '3d17485d-1dac-41f0-a1af-24e45daa4567' in uri and '/items?' in uri else None)
        if role==dataset:
            parent=response['body'] if role=='profiles' else response['body']['d'];key='value' if role=='profiles' else 'results'
            parent[key]=[deepcopy(parent[key][0]) for _ in range(bound+1)]
        return response
    server.request=overfull;r=execute(server)
    assert r.response['resultcode']!='OK' and r.response['candidatesjson']==r.response['groupsjson']=='[]'


def test_normalized_duplicate_identity_rejected_by_shared_source():
    server=Fake();server.profiles[1]['Participantaccount']['Claims']=server.profiles[0]['Participantaccount']['Claims']
    with pytest.raises(Terminated):execute(server)


def test_invalid_noninteger_reference_cannot_read_data():
    server=Fake();r=execute(server,1.5)
    assert r.response['resultcode']=='READ_OR_DATA_FAILED' and server.queries==[]


def test_stale_invalid_candidate_catalogue_selection_is_excluded():
    server=Fake();server.profiles[1]['Teachlanguages#Id']=[98765];r=execute(server)
    assert r.response['resultcode']=='OK' and [x['profileId'] for x in json.loads(r.response['candidatesjson'])]==[3]


def test_package_preserves_trigger_invoker_response_and_bounds(tmp_path):
    path=tmp_path/'source.zip'
    with ZipFile(path,'w') as z:z.writestr('Microsoft.Flow/flows/source/definition.json',json.dumps(source()))
    output=tmp_path/'discovery.zip';review=discovery.build_package(path,output)
    assert review['actions']<=500 and review['maximumActionDepth']<=8 and review['writes']==0
    assert review['sourceTriggerPreserved'] and review['connectionSource']=='Invoker' and not review['ownerCredentialFallback']
    with ZipFile(output) as z:
        doc=json.loads(z.read(next(n for n in z.namelist() if n.endswith('/definition.json'))))
        assert doc['properties']['definition']['triggers']==source()['properties']['definition']['triggers']
        assert doc['properties']['connectionReferences']['shared_sharepointonline']['source']=='Invoker'
        response=doc['properties']['definition']['actions']['Respond_to_a_Power_App_or_flow']['inputs']
        assert {'candidatesjson','errormessage','groupsjson','resultcode','runreference','mode'}==set(response['schema']['properties'])
        assert 'concurrency' not in json.dumps(doc['properties']['definition']['triggers'])
    with pytest.raises(FileExistsError):discovery.build_package(path,output)


def test_more_than_fifty_eligible_people_fails_before_projection_loop():
    server=Fake();server.profiles=[profile(1,[1],[2])]+[profile(i,[2],[1]) for i in range(2,53)]
    r=execute(server)
    assert r.response['resultcode']=='PEOPLE_RESULT_BOUND' and r.response['candidatesjson']=='[]'
    assert not r.variables['People']


def test_group_work_budget_stops_large_focus_loops():
    server=Fake();server.valid_group();server.groups[0]['LanguageFocusId']['results']=[1]*101
    r=execute(server)
    assert r.response['resultcode']=='GROUP_WORK_BOUND' and r.response['groupsjson']==r.response['candidatesjson']=='[]'


def test_unexpected_structured_note_cannot_escape_public_projection():
    server=Fake();server.profiles[1]['Comments']={'Email':'PRIVATE_BACKEND_EMAIL'};r=execute(server)
    assert r.response['resultcode']=='READ_OR_DATA_FAILED'
    assert r.response['groupsjson']==r.response['candidatesjson']=='[]'
    assert 'PRIVATE_BACKEND_EMAIL' not in json.dumps(r.response)
