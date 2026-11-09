"""#10 emitted-graph tests with a stateful fake native uniqueness boundary."""
from copy import deepcopy
import json,re
from zipfile import ZipFile
import pytest
from test_discovery_flow import Fake,FlowRunner,source as discovery_source,PEOPLE,GROUPS
from test_coordination_fixture import walk
from scripts.power_automate import send_request_flow as send

INTENT='01234567-89ab-cdef-0123-456789abcdef'
def source():
    s=discovery_source();schema=s['properties']['definition']['triggers']['manual']['inputs']['schema']
    schema['properties']['number_1']={'type':'number','description':'RecipientParticipantId'};schema['required'].append('number_1')
    s['properties']['definition']['actions']['Respond_to_a_Power_App_or_flow']['inputs']['schema']['properties']={'success':{'type':'boolean'},'message':{'type':'string'}}
    return s

def fields():
    rows=[]
    for n,t in send.EXPECTED.items():
        xml=''
        if t=='Number':xml='<Field Decimals="0" />'
        if t=='Lookup':xml='<Field List="'+(GROUPS['lists']['groups']['listId'] if n=='TargetGroup' else PEOPLE['lists']['participants']['listId'])+'" />'
        if t=='Choice':xml='<Field FillInChoice="FALSE"><CHOICES>'+''.join('<CHOICE>'+v+'</CHOICE>' for v in (['Personal','Group'] if n=='RequestType' else ['Pending','Accepted','Declined','Cancelled']))+'</CHOICES></Field>'
        rows.append({'InternalName':n,'TypeAsString':t,'Required':n in ['SendOperationKey','ConnectionKey','SenderParticipantId','RequestType','Status'],'Hidden':False,'ReadOnlyField':False,'Indexed':n in ['SendOperationKey','ConnectionKey'],'EnforceUniqueValues':n in ['SendOperationKey','ConnectionKey'],'SchemaXml':xml})
    return rows

class Server(Fake):
    def __init__(self):
        super().__init__();self.rows=[];self.fields=fields();self.writes=0;self.create_mode='ok';self.schema_page=False
    def request(self,p):
        uri=p.get('parameters/uri','')
        if send.REQUESTS not in uri:return super().request(p)
        self.queries.append(uri)
        def response(x,status=200):return {'statusCode':status,'body':{'d':deepcopy(x)}}
        if '/fields?' in uri:
            x={'results':self.fields}
            if self.schema_page:x['__next']='next'
            return response(x)
        if '/items' not in uri:return response({'Id':send.REQUESTS,'BaseTemplate':100})
        if p['parameters/method']=='POST':
            self.writes+=1;row=deepcopy(p['parameters/body'])
            if self.create_mode=='fail':return response({'error':'PRIVATE_BACKEND_FAILURE'},502)
            if self.create_mode=='reverse_race':self.rows.append({**row,'Id':79,'SenderParticipantId':2,'RecipientParticipantId':1,'SendOperationKey':'personal:2:other-intent'})
            if any(x['ConnectionKey']==row['ConnectionKey'] or x['SendOperationKey']==row['SendOperationKey'] for x in self.rows):return response({'error':{'innerError':{'errors':['-2130575169','Microsoft.SharePoint.SPDuplicateValuesFoundException']}}},502)
            self.rows.append({'Id':80+len(self.rows),**row})
            return response(self.rows[-1],502 if self.create_mode=='lost_success' else 201)
        if '$filter=((' in uri:
            actor,target=map(int,re.search(r'SenderParticipantId eq (\d+) and RecipientParticipantId eq (\d+)',uri).groups())
            return response({'results':[{'Id':x['Id']} for x in self.rows if {x['SenderParticipantId'],x['RecipientParticipantId']}=={actor,target} and (x['Status']=='Pending' or x['Status']=='Accepted' and not x['OperationComplete'])]})
        key,value=re.search(r"\$filter=(\w+) eq '([^']*)'",uri).groups()
        return response({'results':[x for x in self.rows if x[key]==value]})

def execute(server=None,target=2,actor=1,intent=INTENT):
    runner=FlowRunner(server or Server());runner.run(send.build_actions(source(),PEOPLE,GROUPS,'synthetic-build'),{'items':{},'triggerBody':{'number':actor,'number_1':target,'text':intent}});return runner

def test_send_exact_pending_then_replay_retains_one_row():
    s=Server();r=execute(s)
    assert r.response['success'] and r.response['resultcode']=='SAVED'
    assert s.rows[0]['SenderParticipantId']==1 and s.rows[0]['RecipientParticipantId']==2
    assert s.rows[0]['ConnectionKey']=='open:person:1:2' and s.rows[0]['OperationComplete'] is False
    assert s.writes==1 and len(s.rows)==1
    s.profiles[0]['ParticipationStatus']={'Value':'Paused'}
    r=execute(s);assert r.response['resultcode']=='REPLAY' and s.writes==1
    assert not any(v in json.dumps(r.response) for v in ['PRIVATE_EMAIL','Claims','accountKey','SendOperationKey'])

def test_same_intent_changed_target_conflicts_without_write():
    s=Server();execute(s);r=execute(s,target=3)
    assert r.response['resultcode']=='INTENT_CONFLICT' and s.writes==1

def test_legacy_pending_without_live_key_cannot_be_bypassed():
    s=Server();s.rows=[{'Id':19,'SenderParticipantId':2,'RecipientParticipantId':1,'Status':'Pending','OperationComplete':False,'ConnectionKey':'','SendOperationKey':''}]
    r=execute(s);assert r.response['resultcode']=='UNSETTLED_CONNECTION_EXISTS' and s.writes==0

def test_new_intent_existing_live_connection_rejected():
    s=Server();execute(s);r=execute(s,intent='ffffffff-ffff-ffff-ffff-ffffffffffff')
    assert r.response['resultcode']=='CONNECTION_EXISTS' and s.writes==1

@pytest.mark.parametrize('field,value',[('ParticipationStatus',{'Value':'Paused'}),('ParticipationStatus',{'Value':'Inactive'}),('OpenToConnections',False),('Status',{'Value':'Needs review'})])
def test_stale_target_unavailable_cannot_send(field,value):
    s=Server();s.profiles[1][field]=value;r=execute(s)
    assert r.response['resultcode']=='TARGET_UNAVAILABLE_OR_INCOMPATIBLE' and s.writes==0

@pytest.mark.parametrize('variant',['missing','unique','lookup','choice','paging'])
def test_schema_unknown_never_writes(variant):
    s=Server()
    if variant=='missing':s.fields.pop()
    if variant=='unique':next(x for x in s.fields if x['InternalName']=='ConnectionKey')['EnforceUniqueValues']=False
    if variant=='lookup':next(x for x in s.fields if x['InternalName']=='TargetGroup')['SchemaXml']='<Field List="other-list" />'
    if variant=='choice':next(x for x in s.fields if x['InternalName']=='RequestType')['SchemaXml']='<Field><CHOICES><CHOICE>Wrong</CHOICE></CHOICES></Field>'
    if variant=='paging':s.schema_page=True
    r=execute(s);assert r.response['resultcode']=='REQUEST_SCHEMA_UNVERIFIED' and s.writes==0

def test_tampered_sender_reference_stops_before_request_or_candidate_reads():
    s=Server();r=execute(s,actor=2)
    assert r.response['resultcode']=='UNAUTHORIZED_PROFILE' and s.writes==0
    assert not any(send.REQUESTS in q or q=='GetItems' for q in s.queries)

@pytest.mark.parametrize('intent',['bad','x'*36,'01234567-89ab-cdef-0123-456789abcde-',INTENT+"'"])
def test_invalid_intent_is_bounded_and_not_interpolated(intent):
    s=Server();r=execute(s,intent=intent)
    assert not r.response['success'] and s.writes==0 and not s.queries

def test_self_target_cannot_send():
    s=Server();r=execute(s,target=1);assert not r.response['success'] and s.writes==0

def test_unknown_create_failure_is_not_reported_saved():
    s=Server();s.create_mode='fail';r=execute(s)
    assert r.response['resultcode']=='CREATE_OUTCOME_UNKNOWN' and not r.response['success'] and s.rows==[]
    assert 'PRIVATE_BACKEND_FAILURE' not in json.dumps(r.response)

def test_lost_success_response_reconciled_by_exact_immutable_readback():
    s=Server();s.create_mode='lost_success';r=execute(s)
    assert r.response['success'] and r.response['resultcode']=='SAVED' and len(s.rows)==1

def test_reverse_send_race_native_unique_key_prevents_second_pending():
    s=Server();s.create_mode='reverse_race';r=execute(s)
    assert len(s.rows)==1 and not r.response['success'] and r.response['resultcode']=='CREATE_OUTCOME_UNKNOWN'

def test_terminal_history_replay_keeps_old_result_and_can_start_distinct_intent():
    s=Server();execute(s);s.rows[0].update(Status='Cancelled',OperationComplete=True,WinningOperationKey='cancel:1:request:80',ConnectionKey='history:request:80')
    r=execute(s);assert r.response['resultcode']=='REPLAY' and r.response['status']=='Cancelled'
    r=execute(s,intent='ffffffff-ffff-ffff-ffff-ffffffffffff');assert r.response['resultcode']=='SAVED' and len(s.rows)==2

def test_generated_package_and_original_response_shape(tmp_path):
    p=tmp_path/'send.zip';review=send.build_package(p,source=source());assert review['actions']<=500 and review['maximumActionDepth']<=8
    with ZipFile(p) as z:doc=json.loads(z.read(next(n for n in z.namelist() if n.endswith('/definition.json'))))
    a=doc['properties']['definition']['actions'];names=[n for n,_ in walk(a)];assert len(names)==len(set(names))
    assert set(doc['properties']['definition']['triggers']['manual']['inputs']['schema']['properties'])=={'number','number_1','text'}
    assert a['Respond']['inputs']['schema']['properties']['success']['type']=='boolean'
    assert doc['properties']['connectionReferences']['shared_sharepointonline']['source']=='Invoker'
    writes=[v for _,v in walk(a) if v['type']=='OpenApiConnection' and v['inputs']['parameters'].get('parameters/method')=='POST']
    assert len(writes)==1 and writes[0]['inputs']['retryPolicy']=={'type':'none'}
    with pytest.raises(FileExistsError):send.build_package(p,source=source())

@pytest.mark.parametrize('valid',[True,False])
def test_metadata_preflight_collects_missing_fields_without_item_reads_or_writes(valid,tmp_path):
    s=Server()
    if not valid:s.fields=[]
    r=FlowRunner(s);r.run(send.build_preflight_actions(source(),PEOPLE,GROUPS,'synthetic-schema'))
    report=json.loads(r.response['reportjson'])
    assert report['collectionComplete'] and report['schemaVerified']==valid and report['writes']==report['itemRowsRead']==0
    assert s.writes==0 and not any('/items' in q for q in s.queries)
    output=tmp_path/'schema.zip';review=send.build_package(output,source=source(),preflight=True)
    assert review['metadataOnly'] and review['requestWrites']==0


def test_actual_export_adapter_finds_nested_request_actions_and_preserves_auth(tmp_path):
    original=source();old=original['properties']['definition']['actions']
    original['properties']['definition']['actions']={
        'Read_sender':old['Get_item'],
        'Check':{'type':'If','actions':{'Pending_requests':{'type':'OpenApiConnection','inputs':{'parameters':{'table':send.REQUESTS}}}},'else':{'actions':{}}},
        'Respond_original':old['Respond_to_a_Power_App_or_flow']}
    export=tmp_path/'source.zip'
    with ZipFile(export,'w') as z:z.writestr('Microsoft.Flow/flows/source/definition.json',json.dumps(original))
    adapted=send.original_source(export)
    assert adapted['properties']['definition']['actions']['Get_item']['inputs']['authentication']==old['Get_item']['inputs']['authentication']
    assert send.build_package(tmp_path/'new.zip',export)['sourceExportSha256']


def test_metadata_preflight_requires_status_type_and_canonical_choices():
    for field,change in [('Status',{'Required':False}),('RequestType',{'SchemaXml':'<Field FillInChoice="TRUE"><CHOICES><CHOICE>Personal</CHOICE><CHOICE>Group</CHOICE></CHOICES></Field>'}),('SenderParticipantId',{'ReadOnlyField':True})]:
        server=Server();next(x for x in server.fields if x['InternalName']==field).update(change)
        runner=execute(server);assert runner.response['resultcode']=='REQUEST_SCHEMA_UNVERIFIED' and server.writes==0


def test_replay_rejects_incoherent_winning_marker_without_writing():
    s=Server();execute(s);s.rows[0]['WinningOperationKey']='unexpected-live-decision'
    r=execute(s);assert r.response['resultcode']=='INTENT_CONFLICT' and s.writes==1


def test_observed_number_columns_are_preserved_and_missing_coordination_is_reported():
    report=json.loads((send.ROOT/'artifacts/send_request/results/initial-schema.owner-report.json').read_text())
    server=Server();server.fields=deepcopy(report['fields'])
    runner=FlowRunner(server);runner.run(send.build_preflight_actions(source(),PEOPLE,GROUPS,'observed-schema'))
    actual=json.loads(runner.response['reportjson'])
    assert actual['collectionComplete'] and not actual['schemaVerified'] and server.writes==0
    assert len(runner.outputs['Schema_SenderParticipantId'])==1
    assert not runner.outputs['Schema_RecipientParticipantId']  # Current Required=true; group-target shape needs optional.
    assert not runner.outputs['Schema_SendOperationKey']


@pytest.mark.parametrize('variant',['oldLookup','fractionalColumn','wrongRecipientRequired'])
def test_number_metadata_contract_not_replaced_by_legacy_lookup_guess(variant):
    server=Server();field=next(x for x in server.fields if x['InternalName']=='SenderParticipantId')
    if variant=='oldLookup':field.update(InternalName='SenderParticipant',TypeAsString='Lookup',SchemaXml='<Field List="'+PEOPLE['lists']['participants']['listId']+'" />')
    if variant=='fractionalColumn':field['SchemaXml']='<Field Decimals="2" />'
    if variant=='wrongRecipientRequired':next(x for x in server.fields if x['InternalName']=='RecipientParticipantId')['Required']=True
    result=execute(server);assert result.response['resultcode']=='REQUEST_SCHEMA_UNVERIFIED' and server.writes==0


def test_readback_accepts_whole_number_reference_representation():
    server=Server();request=server.request
    def coerce(p):
        result=request(p)
        if p.get('parameters/method')=='POST' and server.rows:
            server.rows[-1].update(SenderParticipantId=1.0,RecipientParticipantId=2.0)
        return result
    server.request=coerce
    assert execute(server).response['resultcode']=='SAVED'
    assert execute(server).response['resultcode']=='REPLAY' and server.writes==1
