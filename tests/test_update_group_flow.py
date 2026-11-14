"""#13 execute the real emitted parent against stateful exact-ETag/unique-key boundaries."""
from copy import deepcopy
import json,re
from uuid import uuid4
from zipfile import ZipFile
import pytest
from test_shared_validation import ChildRunner
from test_discovery_flow import PEOPLE,GROUPS
from scripts.power_automate import update_group_flow as flow
from scripts.power_automate.schema_audit import measure

CONTRACT=json.loads((flow.ROOT/'config/update_group_flow_contract.json').read_text(encoding='utf-8'))
BATCH=CONTRACT['parentBatchSchemaSnapshot']
RECEIPTS='11111111-2222-4333-8444-555555555555'
INTENT='01234567-89ab-cdef-0123-456789abcdef'
SITE=BATCH['site']


def payload(**changes):
    result={'actorId':1,'groupId':10,'expectedETag':'"1"','intentId':INTENT,
            'edits':{'Title':'Updated name','Purpose':'Plain description','Capacity':3,'State':'Closed'}}
    result.update(changes);return result


class Server:
    def __init__(self):
        self.group={'Id':10,'Title':'Original','Purpose':None,'ExchangeType':'Language','Capacity':3,'State':'Open',
                    'SourceRequestId':70,'SetupComplete':True,'WriteOwner':None,
                    'LanguageFocusId':{'results':[1]},'CultureFocusId':{'results':[]},'__metadata':{'etag':'"1"'}}
        self.members=[{'Id':201,'GroupId':10,'ParticipantId':1,'MembershipStatus':'Active','MembershipKey':'request:70:participant:1'},
                      {'Id':202,'GroupId':10,'ParticipantId':2,'MembershipStatus':'Active','MembershipKey':'request:70:participant:2'}]
        self.requests=[{'Id':70,'RequestType':'Personal','SenderParticipantId':1,'RecipientParticipantId':2,'TargetGroupId':None,'Status':'Accepted','OperationComplete':True}]
        self.own_rows=[{'Id':1}];self.receipts=[];self.writes=[];self.reads=[];self.faults={};self.fail_read_after=None
        self.receipt_available=True;self.receipt_metadata_changes={};self.last_write=None;self.paged=None;self.after_claim=None;self.claim_race=False;self.receipt_race=False
    @staticmethod
    def reply(value,status=200):return {'statusCode':status,'body':{'d':deepcopy(value)}}
    @staticmethod
    def bump(row):row['__metadata']['etag']='"'+str(int(row['__metadata']['etag'].strip('"'))+1)+'"'
    def add_member(self,participant=3,key='request:99:participant:3'):
        self.members.append({'Id':200+len(self.members)+1,'GroupId':10,'ParticipantId':participant,'MembershipStatus':'Active','MembershipKey':key})
    def request(self,p):
        uri=p['parameters/uri'];method=p['parameters/method'];patch=p.get('parameters/body');self.reads.append(uri) if method=='GET' else None
        if uri.startswith('_api/web/currentuser'):return self.reply({'Id':16})
        if 'ParticipantaccountId eq' in uri:return self.reply({'results':self.own_rows})
        receipt="getbytitle('tandemoperationreceipts')" in uri.lower() or RECEIPTS in uri
        group=GROUPS['lists']['groups']['listId'] in uri
        members=GROUPS['lists']['members']['listId'] in uri
        requests=flow.REQUESTS in uri
        if method=='GET':
            if self.fail_read_after and self.last_write==self.fail_read_after and (group or receipt):
                self.fail_read_after=None;return self.reply({'error':'PRIVATE_BACKEND_DETAIL'},502)
            if receipt:
                if '/items' not in uri:
                    if not self.receipt_available:return self.reply({'error':'list not found'},404)
                    return self.reply({'Id':RECEIPTS,'Title':'TandemOperationReceipts','BaseTemplate':100,'ListItemEntityTypeFullName':'SP.Data.TandemOperationReceiptsListItem',**self.receipt_metadata_changes})
                match=re.search(r'/items\((\d+)\)',uri)
                if match:return self.reply(next(r for r in self.receipts if r['Id']==int(match[1])))
                key=re.search(r"OperationKey eq '([^']+)'",uri)[1]
                result={'results':[r for r in self.receipts if r['OperationKey']==key]}
                if self.paged=='receipts':result['__next']='next'
                return self.reply(result)
            if group:return self.reply(self.group)
            if members:
                rows=[r for r in self.members if r['GroupId']==10 and r['MembershipStatus']=='Active']
                result={'results':rows}
                if self.paged=='members':result['__next']='next'
                return self.reply(result)
            if requests:
                if self.paged=='requests':return self.reply({'error':'incomplete request read'},502)
                match=re.search(r'/items\((\d+)\)',uri)
                if match:return self.reply(next((r for r in self.requests if r['Id']==int(match[1])),{}))
                result={'results':self.requests}
                if self.paged=='requests':result['__next']='next'
                return self.reply(result)
            raise AssertionError('Unexpected GET '+uri)
        assert method=='POST'
        merge=p['parameters/headers'].get('X-HTTP-Method')=='MERGE'
        if receipt and not merge:
            assert patch.get('Title')==patch['OperationKey']  # Standard built-in Title may be required.
            label='create_receipt';self.writes.append((label,deepcopy(patch)));self.last_write=label
            if self.faults.get(label)=='fail':return self.reply({'error':'PRIVATE_CREATE_ERROR'},502)
            if self.receipt_race:
                self.receipts.append({'Id':900,**deepcopy(patch),'AttemptToken':'other-live-attempt','__metadata':{'etag':'"1"'}})
            if any(r['OperationKey']==patch['OperationKey'] for r in self.receipts):return self.reply({'error':'unique conflict'},502)
            self.receipts.append({'Id':901+len(self.receipts),**deepcopy(patch),'__metadata':{'etag':'"1"'}})
            return self.reply(self.receipts[-1],502 if self.faults.get(label)=='lost' else 201)
        assert merge and p['parameters/headers']['IF-MATCH'] not in ['', '*']
        if group:
            row=self.group
            if set(patch)=={'WriteOwner'}:label='release' if patch['WriteOwner'] is None else 'claim'
            else:
                label='update';assert set(patch)=={'Title','Purpose','Capacity','State'}
            if label=='claim' and self.claim_race:
                self.group['WriteOwner']='different-operation-and-attempt';self.bump(self.group)
        elif receipt:
            match=re.search(r'/items\((\d+)\)',uri);row=next(r for r in self.receipts if r['Id']==int(match[1]))
            label='mark' if patch.get('Stage')=='Updating' else 'reject' if patch.get('Stage')=='Rejected' else 'complete'
        else:raise AssertionError('Unexpected write '+uri)
        self.writes.append((label,deepcopy(patch)));self.last_write=label
        if p['parameters/headers']['IF-MATCH']!=row['__metadata']['etag']:return self.reply({'error':'stale ETag'},412)
        if self.faults.get(label)=='fail':return self.reply({'error':'PRIVATE_WRITE_ERROR'},502)
        row.update(deepcopy(patch));self.bump(row)
        if label=='update' and row['Purpose']=='':row['Purpose']=None  # Native blank optional Note.
        if label=='claim' and self.after_claim:self.after_claim(self)
        return self.reply(row,502 if self.faults.get(label)=='lost' else 204)


class UpdateRunner(ChildRunner):
    def __init__(self,server):super().__init__(server);self.attempt=str(uuid4())
    def expr(self,text,context):
        text=text.replace('guid()',"'"+self.attempt+"'")
        def substring(match):
            value=self.body('Input')['intentId'][int(match[1]):int(match[1])+int(match[2])]
            return "json('"+json.dumps(value).replace("'","''")+"')"
        text=re.sub(r"substring\(body\('Input'\)\?\['intentId'\],(\d+),(\d+)\)",substring,text)
        # Additional native functions used by this parent, not eligibility mocks.
        def integer(match):return str(int(self.outputs[match[1]]['SourceRequestId']))
        text=re.sub(r"int\(outputs\('([^']+)'\)\?\['SourceRequestId'\]\)",integer,text)
        text=text.replace("empty(variables('SavedResult'))",'true' if not self.variables.get('SavedResult') else 'false')
        return super().expr(text,context)
    def parse_content(self,value,schema):
        value=super().parse_content(value,schema)
        def bounds(v,s):
            if isinstance(v,str):assert len(v)<=s.get('maxLength',10**9)
            if isinstance(v,dict):
                for k,r in s.get('properties',{}).items():
                    if k in v:bounds(v[k],r)
            if isinstance(v,list):
                for item in v:bounds(item,s.get('items',{}))
        bounds(value,schema);return value


def execute(server=None,request=None,configured=True,actions=None):
    server=server or Server();runner=UpdateRunner(server)
    actions=actions or flow.build_actions(SITE,PEOPLE,GROUPS,BATCH,'local-build',RECEIPTS if configured else None)
    runner.run(actions,{'items':{},'triggerBody':{'text':json.dumps(request or payload())}})
    assert runner.response is not None,runner.action_states
    return runner


def labels(server):return [name for name,_ in server.writes]


def test_update_real_emitted_flow_then_replay_preserves_one_domain_write():
    server=Server();runner=execute(server)
    assert runner.response['resultcode']=='UPDATED', (runner.response,runner.action_states)
    assert runner.response['success'] and server.group['Title']=='Updated name' and server.group['State']=='Closed'
    assert labels(server)==['create_receipt','claim','mark','update','complete','release']
    assert server.group['WriteOwner'] is None and server.receipts[0]['Complete'] and not server.receipts[0]['Uncertain']
    assert runner.response['etag']==server.group['__metadata']['etag']
    again=execute(server);assert again.response['resultcode']=='REPLAY' and again.response['success']
    assert labels(server).count('update')==1 and len(server.receipts)==1

@pytest.mark.parametrize('start',['Open','Closed'])
@pytest.mark.parametrize('end',['Open','Closed','Ended'])
def test_allowed_state_transitions_are_explicit(start,end):
    server=Server();server.group['State']=start;request=payload();request['edits']['State']=end
    result=execute(server,request).response
    assert result['success'] and server.group['State']==end
    assert server.group['ExchangeType']=='Language' and server.group['LanguageFocusId']=={'results':[1]}


@pytest.mark.parametrize('requested',['Open','Closed','Ended'])
def test_ended_group_is_final_for_fresh_edits(requested):
    server=Server();server.group['State']='Ended';request=payload();request['edits']['State']=requested
    assert execute(server,request).response['resultcode']=='GROUP_ENDED_FINAL' and not server.writes


@pytest.mark.parametrize('kind,capacity',[('Language',2),('Language',3),('Culture',2),('Culture',10),('Combined',2),('Combined',10)])
def test_capacity_type_bounds_accept_exact_integers(kind,capacity):
    server=Server();server.group['ExchangeType']=kind;request=payload();request['edits']['Capacity']=capacity
    assert execute(server,request).response['success'] and server.group['Capacity']==capacity


@pytest.mark.parametrize('value',[0,1,4,11,2.5,3.0,'3',True,None])
def test_invalid_language_capacity_never_writes(value):
    server=Server();request=payload();request['edits']['Capacity']=value
    result=execute(server,request).response
    assert not result['success'] and not server.writes


def test_capacity_counts_all_physical_active_including_provisional_and_paused():
    server=Server();server.add_member();server.members[-1]['ParticipationStatus']='Paused'
    request=payload();request['edits']['Capacity']=2
    assert execute(server,request).response['resultcode']=='CAPACITY_INVALID' and not server.writes


def test_closed_with_free_slots_stays_closed_and_full_open_is_not_automatically_closed():
    for state in ['Open','Closed']:
        server=Server();server.group['State']=state;request=payload();request['edits'].update(State=state,Capacity=2)
        assert execute(server,request).response['success'] and server.group['State']==state


@pytest.mark.parametrize('field,value',[('ExchangeType','Culture'),('LanguageFocusId',{'results':[9]}),('CultureFocusId',{'results':[9]}),('WriteOwner','forged'),('SourceRequestId',99),('SetupComplete',True),('ArbitraryPatch',{})])
@pytest.mark.parametrize('location',['envelope','edits'])
def test_type_focus_and_arbitrary_inputs_are_rejected(field,value,location):
    server=Server();request=payload();(request if location=='envelope' else request['edits'])[field]=value
    assert not execute(server,request).response['success'] and not server.writes and not server.reads


@pytest.mark.parametrize('title,purpose,allowed',[('x'*255,'x'*2000,True),('','',False),('   ','',False),('x'*256,'',False),('Title','x'*2001,False),('Title',None,False),('Title','',True),('Title','line1\nline2 <plain text>',True)])
def test_plain_text_bounds_and_empty_optional_note(title,purpose,allowed):
    server=Server();request=payload();request['edits'].update(Title=title,Purpose=purpose)
    result=execute(server,request).response
    assert result['success']==allowed
    if allowed:
        current=json.loads(result['groupjson']);assert current['purpose']==purpose
        assert current['etag']==result['etag']==server.group['__metadata']['etag']
    else:assert not server.writes


@pytest.mark.parametrize('change,value',[('actorId',2),('actorId',0),('groupId',0),('expectedETag','*'),('intentId','bad'),('intentId','x'*36),('intentId','01234567-89ab-cdef-0123-456789abcde-')])
def test_spoof_or_malformed_input_never_mutates(change,value):
    server=Server();request=payload(**{change:value});result=execute(server,request).response
    assert not result['success'] and not server.writes
    if change=='actorId' and value==2:
        assert result['resultcode']=='UNAUTHORIZED_PROFILE'
        assert not any(GROUPS['lists']['groups']['listId'] in q for q in server.reads)


@pytest.mark.parametrize('own_rows',[[],[{'Id':1},{'Id':2}]])
def test_own_profile_resolution_must_be_unique(own_rows):
    server=Server();server.own_rows=own_rows
    assert execute(server).response['resultcode']=='UNAUTHORIZED_PROFILE' and not server.writes


@pytest.mark.parametrize('variant',['left','missing','provisional','wrongParty','wrongGroupEpisode','incompleteOrigin','unpublishedGroup'])
def test_raw_active_or_provisional_membership_is_not_authority(variant):
    server=Server()
    if variant=='left':server.members[0]['MembershipStatus']='Left'
    elif variant=='missing':server.members=server.members[1:]
    elif variant=='provisional':server.requests[0]['OperationComplete']=False
    elif variant=='wrongParty':server.requests[0].update(SenderParticipantId=8,RecipientParticipantId=9)
    elif variant=='wrongGroupEpisode':
        server.members[0]['MembershipKey']='request:99:participant:1'
        server.requests.append({'Id':99,'RequestType':'Group','SenderParticipantId':1,'TargetGroupId':11,'Status':'Accepted','OperationComplete':True})
    elif variant=='incompleteOrigin':server.requests[0]['Status']='Pending'
    else:server.group['SetupComplete']=False
    assert not execute(server).response['success'] and not server.writes


@pytest.mark.parametrize('actor',[1,2])
@pytest.mark.parametrize('personal_status',['Active','Paused','Inactive'])
def test_current_operational_members_manage_regardless_of_personal_availability(actor,personal_status):
    server=Server();server.own_rows=[{'Id':actor,'ParticipationStatus':personal_status,'OpenToConnections':False,'Status':'Needs review'}]
    assert execute(server,payload(actorId=actor)).response['success']
    assert not any('/items('+str(actor)+')' in q and PEOPLE['lists']['participants']['listId'] in q for q in server.reads)


def test_committed_group_join_episode_can_manage_without_being_original_party():
    server=Server();server.own_rows=[{'Id':3}];server.add_member()
    server.requests.append({'Id':99,'RequestType':'Group','SenderParticipantId':3,'TargetGroupId':10,'Status':'Accepted','OperationComplete':True})
    assert execute(server,payload(actorId=3)).response['success']


@pytest.mark.parametrize('etag',['"0"','W/"1"'])
def test_stale_expected_etag_returns_conflict_without_receipt_or_group_write(etag):
    server=Server();assert execute(server,payload(expectedETag=etag)).response['resultcode']=='REVISION_CONFLICT'
    assert not server.writes


def test_busy_group_never_steals_or_expires_foreign_token():
    server=Server();server.group['WriteOwner']='update:999:old|attempt-old'
    assert execute(server).response['resultcode']=='GROUP_BUSY' and not server.writes
    assert server.group['WriteOwner']=='update:999:old|attempt-old'


def test_membership_count_reread_under_claim_rejects_shrink_and_seals_known_no_domain_failure():
    server=Server();server.after_claim=lambda s:s.add_member();request=payload();request['edits']['Capacity']=2
    result=execute(server,request).response
    assert result['resultcode']=='CAPACITY_CHANGED_OR_INVALID' and not result['success']
    assert 'update' not in labels(server) and server.group['Capacity']==3 and server.group['WriteOwner'] is None
    assert server.receipts[0]['Complete'] and not server.receipts[0]['DomainEffects'] and not server.receipts[0]['Uncertain']
    assert server.receipts[0]['Stage']=='Rejected'
    server.members.pop();before=len(server.writes)
    assert execute(server,request).response['resultcode']=='CAPACITY_CHANGED_OR_INVALID' and len(server.writes)==before


def test_membership_authority_is_reread_under_claim():
    server=Server();server.after_claim=lambda s:s.members[0].update(MembershipStatus='Left')
    result=execute(server).response
    assert not result['success'] and 'update' not in labels(server)
    assert server.group['WriteOwner'] is None and server.receipts[0]['Complete']


@pytest.mark.parametrize('stage',['create_receipt','claim','mark','update','complete','release'])
def test_lost_success_response_is_reconciled_by_exact_persisted_readback(stage):
    server=Server();server.faults[stage]='lost'
    result=execute(server).response
    assert result['success'] and result['resultcode']=='UPDATED',result
    assert labels(server).count('update')==1 and server.group['WriteOwner'] is None


@pytest.mark.parametrize('stage',['create_receipt','claim','update','complete','release'])
def test_unknown_failed_mutations_never_claim_success_or_no_effect(stage):
    server=Server();server.faults[stage]='fail'
    result=execute(server).response
    assert not result['success'] and result['resultcode'] not in ['UPDATED','REPLAY']
    assert 'PRIVATE_' not in json.dumps(result)
    if stage in ['update','complete','release']:
        assert server.group['WriteOwner'] is not None
        before=labels(server).count('update');server.faults={}
        retry=execute(server).response
        assert labels(server).count('update')==before
        assert retry['resultcode']==('REPLAY' if stage=='release' else 'OPERATION_IN_PROGRESS_OR_UNKNOWN')


def test_unknown_update_readback_retains_token_and_never_repeats_domain_write():
    server=Server();server.fail_read_after='update'
    result=execute(server).response
    assert not result['success'] and result['resultcode']=='UPDATE_OUTCOME_UNKNOWN'
    assert server.group['Title']=='Updated name' and server.group['WriteOwner'] is not None
    assert server.receipts[0]['Uncertain'] and not server.receipts[0]['Complete']
    assert execute(server).response['resultcode']=='OPERATION_IN_PROGRESS_OR_UNKNOWN'
    assert labels(server).count('update')==1


def test_completed_receipt_release_recovery_only_uses_exact_saved_old_token():
    server=Server();server.faults['release']='fail';request=payload();request['edits']['State']='Ended'
    assert not execute(server,request).response['success']
    token=server.group['WriteOwner'];assert server.receipts[0]['Complete'] and token==server.receipts[0]['AttemptToken']
    server.faults={};assert execute(server,request).response['resultcode']=='REPLAY'
    assert labels(server).count('update')==1 and server.group['State']=='Ended' and server.group['WriteOwner'] is None


def test_replay_is_historical_and_does_not_undo_a_later_update_or_clear_other_writer():
    server=Server();execute(server)
    first_result=json.loads(server.receipts[0]['ResultJson']);first_request=payload()
    request=payload(intentId='ffffffff-ffff-ffff-ffff-ffffffffffff',expectedETag=server.group['__metadata']['etag'])
    request['edits'].update(Title='Later',State='Open')
    assert execute(server,request).response['success']
    server.group['WriteOwner']='another-writer-token';server.bump(server.group);before=len(server.writes)
    result=execute(server,first_request).response
    assert result['resultcode']=='REPLAY' and json.loads(result['resultjson'])['saved']==first_result
    assert json.loads(result['groupjson'])['title']=='Later' and result['etag']==server.group['__metadata']['etag']
    assert server.group['WriteOwner']=='another-writer-token' and len(server.writes)==before


@pytest.mark.parametrize('change',['title','capacity','state','revision','group'])
def test_same_intent_changed_frozen_input_is_conflict(change):
    server=Server();execute(server);request=payload()
    if change=='title':request['edits']['Title']='Different'
    elif change=='capacity':request['edits']['Capacity']=2
    elif change=='state':request['edits']['State']='Open'
    elif change=='revision':request['expectedETag']=server.group['__metadata']['etag']
    else:request['groupId']=11
    before=len(server.writes);result=execute(server,request).response
    assert not result['success'] and len(server.writes)==before
    if change!='group':assert result['resultcode']=='INTENT_CONFLICT'


def test_unique_receipt_race_cannot_adopt_another_attempt():
    server=Server();server.receipt_race=True
    assert not execute(server).response['success']
    assert labels(server)==['create_receipt'] and server.group['WriteOwner'] is None


def test_claim_race_does_not_clear_other_writer_or_mutate_fields():
    server=Server();server.claim_race=True
    assert not execute(server).response['success'] and labels(server)==['create_receipt','claim','reject']
    assert server.group['WriteOwner']=='different-operation-and-attempt' and server.group['Title']=='Original'
    assert server.receipts[0]['Complete'] and not server.receipts[0]['DomainEffects']
    assert server.receipts[0]['Stage']=='Rejected'


@pytest.mark.parametrize('role',['members','requests','receipts'])
def test_paged_or_incomplete_authority_and_receipts_fail_closed(role):
    server=Server();server.paged=role
    assert not execute(server).response['success'] and not server.writes


def test_title_target_absent_fails_closed_then_same_graph_works_after_setup():
    server=Server();server.receipt_available=False
    actions=flow.build_actions(SITE,PEOPLE,GROUPS,BATCH,'same-import',None)
    result=execute(server,configured=False,actions=actions).response
    assert not result['success'] and result['resultcode']=='RECEIPT_STORE_UNAVAILABLE' and not server.writes
    assert any("getbytitle('TandemOperationReceipts')" in q for q in server.reads)
    server.receipt_available=True
    result=execute(server,configured=False,actions=actions).response
    assert result['resultcode']=='UPDATED' and result['success']
    report=json.loads(result['resultjson'])
    assert report['receiptTargetMode']=='EXACT_UNIQUE_TITLE' and not report['schemaSetupVerified']


def test_full_parent_document_and_package_io_bindings_counts_and_no_overwrite(tmp_path):
    batch=tmp_path/'batch.json';batch.write_text(json.dumps(BATCH),encoding='utf-8')
    path=tmp_path/'update.zip';review=flow.build_package(path,batch)
    assert review['actions']<=500 and review['maximumActionDepth']<=8 and review['receiptListId'] is None
    document=json.loads(path.with_suffix('.parent.json').read_text(encoding='utf-8'))
    assert document['properties']['connectionReferences']['shared_sharepointonline']['source']=='Invoker'
    definition=document['properties']['definition'];assert definition['triggers']==flow.trigger()
    assert set(definition['actions']['Respond']['inputs']['schema']['properties'])=={'success','resultcode','resultjson','groupjson','etag','errormessage','runreference'}
    server=Server();assert execute(server,actions=definition['actions']).response['resultcode']=='UPDATED'
    assert labels(server).count('update')==1 and server.reads
    with ZipFile(path) as archive:
        assert archive.testzip() is None
        assert json.loads(archive.read(next(n for n in archive.namelist() if n.endswith('/definition.json'))))==document
    with pytest.raises(FileExistsError):flow.build_package(path,batch)
    from test_coordination_fixture import walk
    actions=list(walk(flow.build_actions(SITE,PEOPLE,GROUPS,BATCH,'local',RECEIPTS)))
    assert not any(a['type']=='Workflow' for _,a in actions)
    assert '@div(' not in json.dumps(actions)
    writes=[a for _,a in actions if a['type']=='OpenApiConnection' and a['inputs']['parameters']['parameters/method']=='POST']
    assert all(a['inputs']['retryPolicy']=={'type':'none'} for a in writes)
    assert all(a['inputs']['parameters']['parameters/headers']['IF-MATCH']!='*' for a in writes if a['inputs']['parameters']['parameters/headers'].get('X-HTTP-Method')=='MERGE')
    assert measure(definition['actions'])['actions']==review['actions']


@pytest.mark.parametrize('state',['Pending','open','',None,1])
def test_only_exact_allowed_state_inputs_are_accepted(state):
    server=Server();request=payload();request['edits']['State']=state
    assert not execute(server,request).response['success'] and not server.writes


def test_full_parent_document_builder_executes_configured_fixture_and_excludes_personal_availability_guards():
    document=flow.build_parent_document(SITE,PEOPLE,GROUPS,BATCH,'full-parent-fixture',RECEIPTS)
    text=json.dumps(document)
    assert 'ParticipationStatus' not in text and 'OpenToConnections' not in text
    assert 'Require_available_actor' not in text and 'Workflow' not in text
    server=Server();server.group['Capacity']=3.0;server.group['SourceRequestId']=70.0
    runner=execute(server,actions=document['properties']['definition']['actions'])
    assert runner.response['success']
    assert json.loads(runner.response['groupjson'])['etag']==runner.response['etag']
    assert not any(k in runner.response['resultjson'] for k in ['AttemptToken','WriteOwner','IntentJson','Participantaccount'])


def test_unknown_claim_readback_does_not_seal_or_release_a_possibly_live_attempt():
    server=Server();server.fail_read_after='claim'
    result=execute(server).response
    assert not result['success'] and server.group['WriteOwner'] is not None
    assert not server.receipts[0]['Complete'] and labels(server)==['create_receipt','claim']


def test_saved_result_tampering_cannot_be_reported_as_success():
    server=Server();execute(server);server.receipts[0]['ResultJson']=json.dumps({'resultcode':'UPDATED','groupId':10})
    before=len(server.writes);result=execute(server).response
    assert not result['success'] and len(server.writes)==before


@pytest.mark.parametrize('changes',[{'Title':'Another list'},{'BaseTemplate':101},{'ListItemEntityTypeFullName':''},{'Id':None}])
def test_default_title_resolution_requires_current_native_list_metadata(changes):
    server=Server();server.receipt_metadata_changes=changes
    assert not execute(server,configured=False).response['success'] and not server.writes


def test_optional_guid_pin_rejects_different_actual_list_id():
    server=Server();server.receipt_metadata_changes={'Id':'99999999-2222-4333-8444-555555555555'}
    result=execute(server,configured=True).response
    assert result['resultcode']=='RECEIPT_LIST_MISMATCH' and not server.writes
