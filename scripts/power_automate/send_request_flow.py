"""#10 personal-send owner preview; native schema/unique keys required, no setup writes."""
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4
from zipfile import ZipFile, ZIP_DEFLATED
import argparse, hashlib, json
from . import discovery_flow as d
from . import compatibility as rules
from .build_import_probe import build_package as envelope
from .schema_audit import measure, ALL

ROOT=Path(__file__).resolve().parents[2]
NAME='TandemSendRequest v2'
REQUESTS='3d17485d-1dac-41f0-a1af-24e45daa4567'
EXPECTED={'SenderParticipant':'Lookup','RecipientParticipant':'Lookup','TargetGroup':'Lookup',
 'RequestType':'Choice','Status':'Choice','SendOperationKey':'Text','ConnectionKey':'Text',
 'WinningOperationKey':'Text','OperationComplete':'Boolean'}

def original_source(export):
    """Preserve actual Send actor/target and response bindings; reuse verified read adapter."""
    p=ROOT/'artifacts/tandem_discovery/TandemDiscovery-v2.definition.json'
    doc=json.loads(p.read_text(encoding='utf-8'));a=doc['properties']['definition']['actions']['Discovery_reads']['actions']
    with ZipFile(export) as z:doc=json.loads(z.read(next(n for n in z.namelist() if n.endswith('/definition.json'))))
    def flatten(actions):
        result={}
        for key,value in actions.items():
            result[key]=value;result.update(flatten(value.get('actions',{})));result.update(flatten(value.get('else',{}).get('actions',{})))
        return result
    old=flatten(doc['properties']['definition']['actions']);sender=old['Read_sender'];candidate=deepcopy(a['Candidate_source'])
    if old['Pending_requests']['inputs']['parameters']['table'].strip('{}').lower()!=REQUESTS:raise ValueError('Export request list target differs from verified inventory')
    candidate['inputs']['authentication']=deepcopy(sender['inputs']['authentication'])
    candidate['inputs']['parameters']['dataset']=sender['inputs']['parameters']['dataset']
    response=next(v for v in old.values() if v['type']=='Response')
    doc['properties']['definition']['actions']={'Get_item':deepcopy(sender),'Candidate_source':candidate,'Respond_to_a_Power_App_or_flow':deepcopy(response)}
    return doc

def trigger(source):
    t=deepcopy(source['properties']['definition']['triggers']);schema=t['manual']['inputs']['schema']
    if set(schema['properties'])!={'number','number_1'}:raise ValueError('Expected exported sender/recipient references')
    schema['properties']['text']={'type':'string','title':'IntentId','x-ms-content-hint':'TEXT','x-ms-dynamically-added':True}
    schema['required'].append('text');return t

def build_actions(source, people, groups, build_id):
    common=deepcopy(source['properties']['definition']['actions']['Get_item']['inputs'])
    site=common['parameters']['dataset'];base="_api/web/lists(guid'"+REQUESTS+"')"
    def http(uri,prev=None,method='GET',payload=None):
        p={'dataset':site,'parameters/method':method,'parameters/uri':uri,'parameters/headers':{'Accept':'application/json;odata=verbose'}}
        if payload is not None:p['parameters/body']=payload;p['parameters/headers']['Content-Type']='application/json;odata=nometadata'
        inp={'host':{**common['host'],'operationId':'HttpRequest'},'parameters':p,'authentication':deepcopy(common['authentication'])}
        if method!='GET':inp['retryPolicy']={'type':'none'}
        return {'type':'OpenApiConnection','inputs':inp,'runAfter':d.after(prev)}
    def gate(test,code,prev=None):
        return d.condition(test,{}, {'Set_'+code:d.setvar('ErrorCode',code),'Stop_'+code:d.compose('@div(1,0)','Set_'+code)},prev)
    adapter=deepcopy(source);adapter['properties']['definition']['triggers']['manual']['inputs']['schema']['properties']={'number':{'type':'number'}}
    template=d.build_actions(adapter,people,groups,build_id)['Discovery_reads']['actions']
    a={};previous=None
    for name,kind,value in [('ErrorCode','string',''),('ResultCode','string',''),('RequestId','integer',0),('SavedStatus','string','')]:
        key='Initialize_'+name;a[key]={'type':'InitializeVariable','inputs':{'variables':[{'name':name,'type':kind,'value':value}]},'runAfter':d.after(previous)};previous=key
    s={}
    for name in ['Input_reference','Read_invoker','Invoker','Resolve_own_profile','Own_profile','Require_own_profile']:
        s[name]=deepcopy(template[name])
    s['Input_reference']['inputs']['content']="@triggerBody()?['number_1']"
    s['Input_actor_reference']=d.parse("@triggerBody()?['number']",{'type':'integer','minimum':1},'Input_reference')
    s['Require_own_profile']=gate('and('+d.complete('Resolve_own_profile',1)+",equals(length(coalesce(body('Resolve_own_profile')?['d']?['results'],json('[]'))),1),equals(outputs('Own_profile')?['Id'],body('Input_actor_reference')))",'UNAUTHORIZED_PROFILE','Own_profile')
    s['Input_intent']=d.parse("@triggerBody()?['text']",{'type':'string','minLength':36,'maxLength':36},'Input_actor_reference')
    # Rewire identity after strict bounded intent parsing. UUID allows only hex at fixed hyphens.
    stripped="toLower(body('Input_intent'))"
    for c in '0123456789abcdef-':stripped="replace("+stripped+",'"+c+"','')"
    uuid_test="and(equals(length(body('Input_intent')),36),empty("+stripped+"),equals(substring(body('Input_intent'),8,1),'-'),equals(substring(body('Input_intent'),13,1),'-'),equals(substring(body('Input_intent'),18,1),'-'),equals(substring(body('Input_intent'),23,1),'-'),equals(length(replace(body('Input_intent'),'-','')),32))"
    s['Require_uuid']=gate(uuid_test,'INVALID_INTENT','Input_intent');s['Read_invoker']['runAfter']=d.after('Require_uuid')
    s['Operation_key']=d.compose("@concat('personal:',string(outputs('Own_profile')?['Id']),':',toLower(body('Input_intent')))",'Require_own_profile')
    s['Connection_key']=d.compose("@concat('open:person:',string(if(less(outputs('Own_profile')?['Id'],body('Input_reference')),outputs('Own_profile')?['Id'],body('Input_reference'))),':',string(if(less(outputs('Own_profile')?['Id'],body('Input_reference')),body('Input_reference'),outputs('Own_profile')?['Id'])))",'Operation_key')
    s['Read_request_list']=http(base+'?$select=Id,BaseTemplate','Connection_key')
    s['Read_request_fields']=http(base+'/fields?$select=InternalName,TypeAsString,Required,Indexed,EnforceUniqueValues,SchemaXml&$top=5000','Read_request_list')
    prior='Read_request_fields';matches=[]
    for field,kind in EXPECTED.items():
        terms=["equals(item()?['InternalName'],'"+field+"')","equals(item()?['TypeAsString'],'"+kind+"')"]
        if field in ['SendOperationKey','ConnectionKey']:
            terms += ["equals(item()?['Required'],true)","equals(item()?['Indexed'],true)","equals(item()?['EnforceUniqueValues'],true)"]
        if field=='SenderParticipant':terms.append("equals(item()?['Required'],true)")
        if field in ['RecipientParticipant','TargetGroup']:terms.append("equals(item()?['Required'],false)")
        if kind=='Lookup':
            target=groups['lists']['groups']['listId'] if field=='TargetGroup' else people['lists']['participants']['listId']
            terms.append("contains(toLower(coalesce(item()?['SchemaXml'],'')),'"+target+"')")
        if kind=='Choice':
            choices=['Personal','Group'] if field=='RequestType' else ['Pending','Accepted','Declined','Cancelled']
            terms.extend("contains(coalesce(item()?['SchemaXml'],''),'<CHOICE>"+c+"</CHOICE>')" for c in choices)
        key='Schema_'+field;s[key]=d.query("@body('Read_request_fields')?['d']?['results']",'and('+','.join(terms)+')',prior);prior=key
        matches.append("equals(length(body('"+key+"')),1)")
    s['Require_request_schema']=gate('and('+d.complete('Read_request_fields',5000)+",equals(body('Read_request_list')?['d']?['Id'],'"+REQUESTS+"'),equals(body('Read_request_list')?['d']?['BaseTemplate'],100),"+','.join(matches)+')','REQUEST_SCHEMA_UNVERIFIED',prior)
    select='Id,SenderParticipantId,RecipientParticipantId,TargetGroupId,RequestType,Status,SendOperationKey,ConnectionKey,OperationComplete'
    def readkey(field,value,prev):return http(d.cat(base+'/items?$select='+select+'&$filter='+field+" eq '",value,"'&$top=2"),prev)
    s['Read_send_intent']=readkey('SendOperationKey',"@outputs('Operation_key')",'Require_request_schema')
    s['Require_intent_read']=gate(d.complete('Read_send_intent',1),'INTENT_READ_INCOMPLETE','Read_send_intent')
    def result(code,row,prev=None):
        prefix=code+'_'
        x={prefix+'Set_result':d.setvar('ResultCode',code,prev),prefix+'Set_request_id':d.setvar('RequestId','@'+row+"?['Id']",prefix+'Set_result'),
           prefix+'Set_saved_status':d.setvar('SavedStatus','@'+row+"?['Status']",prefix+'Set_request_id')}
        return x
    def exact(row):return "and(equals("+row+"?['SenderParticipantId'],outputs('Own_profile')?['Id']),equals("+row+"?['RecipientParticipantId'],body('Input_reference')),equals("+row+"?['TargetGroupId'],null),equals("+row+"?['RequestType'],'Personal'),equals("+row+"?['SendOperationKey'],outputs('Operation_key')),contains(createArray('Pending','Accepted','Declined','Cancelled'),"+row+"?['Status']),or(and(contains(createArray('Pending','Accepted'),"+row+"?['Status']),equals("+row+"?['OperationComplete'],false),equals("+row+"?['ConnectionKey'],outputs('Connection_key'))),and(contains(createArray('Accepted','Declined','Cancelled'),"+row+"?['Status']),equals("+row+"?['OperationComplete'],true),equals("+row+"?['ConnectionKey'],concat('history:request:',string("+row+"?['Id']))))))"
    replay={'Prior_intent':d.compose("@first(body('Read_send_intent')?['d']?['results'])")}
    replay['Require_same_intent']=gate(exact("outputs('Prior_intent')"),'INTENT_CONFLICT','Prior_intent')
    replay.update(result('REPLAY',"outputs('Prior_intent')",'Require_same_intent'))
    # The same maintained availability/compatibility adapter as Discovery; no caller-supplied facts.
    new={};copying=False
    for name,action in template.items():
        if name=='Get_item':copying=True
        if copying:new[name]=deepcopy(action)
        if name=='Require_available_actor':break
    new['Get_item']['runAfter']={};new['Get_item']['inputs']['parameters']['id']="@outputs('Own_profile')?['Id']"
    new['Find_actor']['inputs']['where']="@equals(item()?['profileId'],outputs('Own_profile')?['Id'])"
    new['Target_profile']=d.query("@body('Shared_Profiles')","equals(item()?['profileId'],body('Input_reference'))",'Require_available_actor')
    new['Target']=d.compose("@first(union(body('Target_profile'),createArray(json('{}'))))",'Target_profile')
    compatible=rules.pair_rules()['eligible'].wdl({'left':"outputs('Actor')",'right':"outputs('Target')"})
    new['Require_current_fit']=gate("and(equals(length(body('Target_profile')),1),"+compatible+')','TARGET_UNAVAILABLE_OR_INCOMPATIBLE','Target')
    new['Read_live_connection']=readkey('ConnectionKey',"@outputs('Connection_key')",'Require_current_fit')
    new['Require_connection_read']=gate(d.complete('Read_live_connection',1),'CONNECTION_READ_INCOMPLETE','Read_live_connection')
    new['Require_no_live_connection']=gate("empty(body('Read_live_connection')?['d']?['results'])",'CONNECTION_EXISTS','Require_connection_read')
    # Existing rows may predate required-key settings; never bypass their Pending connection.
    legacy_filter=d.cat('((SenderParticipantId eq ',"@string(outputs('Own_profile')?['Id'])",' and RecipientParticipantId eq ',"@string(body('Input_reference'))",') or (SenderParticipantId eq ',"@string(body('Input_reference'))",' and RecipientParticipantId eq ',"@string(outputs('Own_profile')?['Id'])",")) and (Status eq 'Pending' or (Status eq 'Accepted' and OperationComplete eq false))")
    new['Read_unsettled_pair']=http(d.cat(base+'/items?$select=Id&$filter=',legacy_filter,'&$top=2'),'Require_no_live_connection')
    new['Require_pair_read']=gate(d.complete('Read_unsettled_pair',1),'PAIR_READ_INCOMPLETE','Read_unsettled_pair')
    new['Require_no_unsettled_pair']=gate("empty(body('Read_unsettled_pair')?['d']?['results'])",'UNSETTLED_CONNECTION_EXISTS','Require_pair_read')
    payload={'Title':'Personal request','RequestType':'Personal','SenderParticipantId':"@outputs('Own_profile')?['Id']",'RecipientParticipantId':"@body('Input_reference')",'TargetGroupId':None,'Status':'Pending',
      'SendOperationKey':"@outputs('Operation_key')",'ConnectionKey':"@outputs('Connection_key')",'OperationComplete':False}
    new['Create_pending']=http(base+'/items','Require_no_unsettled_pair','POST',payload)
    new['Read_created_intent']=readkey('SendOperationKey',"@outputs('Operation_key')",None)
    new['Read_created_intent']['runAfter']={'Create_pending':['Succeeded','Failed','TimedOut']}
    new['Require_created_read']=gate(d.complete('Read_created_intent',1),'CREATE_OUTCOME_UNKNOWN','Read_created_intent')
    new['Created_row']=d.compose("@first(union(coalesce(body('Read_created_intent')?['d']?['results'],json('[]')),createArray(json('{}'))))",'Require_created_read')
    # Readback alone may settle a lost success response; no broad 502-as-duplicate classification.
    new['Verified_create']=d.condition(exact("outputs('Created_row')"),result('SAVED',"outputs('Created_row')"),{'Unknown_create':d.setvar('ErrorCode','CREATE_OUTCOME_UNKNOWN')},'Created_row')
    s['Has_saved_intent']=d.condition("not(empty(body('Read_send_intent')?['d']?['results']))",replay,new,'Require_intent_read')
    # Shared normalization's Terminate is converted to a failed local branch so this flow still responds.
    def safe(actions):
        for name,action in list(actions.items()):
            if action['type']=='Terminate':actions[name]={'type':'Scope','runAfter':action.get('runAfter',{}),'actions':{name+'_Set_integrity_error':d.setvar('ErrorCode','PROFILE_DATA_INVALID'),name+'_Stop_integrity':d.compose('@div(1,0)',name+'_Set_integrity_error')}}
            else:
                for key in ['actions']:
                    if key in action:safe(action[key])
                if 'else'in action:safe(action['else']['actions'])
    safe(s)
    a['Send_request']={'type':'Scope','actions':s,'runAfter':d.after(previous)}
    # Reconciled saved result wins over a failed POST action, but only after exact immutable readback.
    a['Send_report']=d.compose({'kind':'TandemSendRequest','schemaVersion':1,'sourceTicket':10,'packageBuildId':build_id,
      'runReference':"@workflow()?['run']?['name']",'mode':'OWNER_PREVIEW_PENDING_ACCESS_PROOF','ordinaryUserAccessVerified':False,
      'success':"@and(not(empty(variables('ResultCode'))),empty(variables('ErrorCode')))",
      'code':"@if(not(empty(variables('ErrorCode'))),variables('ErrorCode'),if(not(empty(variables('ResultCode'))),variables('ResultCode'),'READ_OR_DATA_FAILED'))",
      'requestId':"@variables('RequestId')",'status':"@variables('SavedStatus')",'schemaVerified':"@equals(actions('Require_request_schema')?['status'],'Succeeded')"})
    a['Send_report']['runAfter']={'Send_request':ALL}
    keys=['resultjson','requestid','status','resultcode','errormessage','runreference']
    props=deepcopy(source['properties']['definition']['actions']['Respond_to_a_Power_App_or_flow']['inputs']['schema']['properties'])
    props.update({k:{'type':'string','title':k,'x-ms-content-hint':'TEXT','x-ms-dynamically-added':True} for k in keys})
    a['Respond']={'type':'Response','kind':'PowerApp','runAfter':d.after('Send_report'),'inputs':{'statusCode':200,'schema':{'type':'object','properties':props},
      'body':{'resultjson':"@string(outputs('Send_report'))",'requestid':"@string(variables('RequestId'))",'status':"@variables('SavedStatus')",'resultcode':"@outputs('Send_report')?['code']",
        'success':"@outputs('Send_report')?['success']",'message':"@if(outputs('Send_report')?['success'],'Request saved.','Request was not confirmed. Keep the same intent ID and check the run reference.')",
        'errormessage':"@if(outputs('Send_report')?['success'],'','Request was not confirmed. Keep the same intent ID and check the run reference.')",'runreference':"@workflow()?['run']?['name']"}}}
    measure(a);return a

def build_preflight_actions(source,people,groups,build_id):
    full=build_actions(source,people,groups,build_id)['Send_request']['actions'];read={};collect=False
    for name,action in full.items():
        if name=='Read_request_list':collect=True
        if collect:read[name]=deepcopy(action)
        if name=='Require_request_schema':break
    read['Read_request_list']['runAfter']={}
    actions={'Initialize_ErrorCode':{'type':'InitializeVariable','inputs':{'variables':[{'name':'ErrorCode','type':'string','value':''}]},'runAfter':{}},
      'Read_schema':{'type':'Scope','actions':read,'runAfter':d.after('Initialize_ErrorCode')}}
    actions['Schema_report']=d.compose({'kind':'TandemRequestSchemaPreflight','schemaVersion':1,'sourceTicket':10,'packageBuildId':build_id,
      'runReference':"@workflow()?['run']?['name']",'readOnly':True,'itemRowsRead':0,'writes':0,
      'schemaVerified':"@equals(actions('Require_request_schema')?['status'],'Succeeded')",
      'collectionComplete':'@'+d.complete('Read_request_fields',5000),
      'requestList':"@body('Read_request_list')?['d']",'fields':"@coalesce(body('Read_request_fields')?['d']?['results'],json('[]'))",
      'expectedFields':EXPECTED,'nextStep':'Metadata only. Do not change permissions or enable replacement writers until request mapping/keys and existing-row handling are reviewed. No old writer is proven compatible by this check.'})
    actions['Schema_report']['runAfter']={'Read_schema':ALL}
    actions['Respond']={'type':'Response','kind':'PowerApp','runAfter':d.after('Schema_report'),'inputs':{'statusCode':200,'schema':{'type':'object','properties':{'reportjson':{'type':'string','title':'reportjson','x-ms-content-hint':'TEXT','x-ms-dynamically-added':True}}},'body':{'reportjson':"@string(outputs('Schema_report'))"}}}
    return actions

def build_package(output,export=None,source=None,preflight=False):
    output=Path(output)
    if any(p.exists() for p in [output,output.with_suffix('.definition.json'),output.with_suffix('.review.json')]):raise FileExistsError(output)
    source=source or original_source(export);people=json.loads((ROOT/'config/tenant_schema_mapping.json').read_text());groups=json.loads((ROOT/'config/group_schema_mapping.json').read_text())
    if source['properties']['connectionReferences']['shared_sharepointonline']['source']!='Invoker':raise ValueError('Invoker required')
    site=source['properties']['definition']['actions']['Get_item']['inputs']['parameters']['dataset'];build_id=str(uuid4())
    flow_name='TandemRequestSchemaPreflight' if preflight else NAME
    actions=(build_preflight_actions if preflight else build_actions)(source,people,groups,build_id)
    with TemporaryDirectory() as temp:
        p=Path(temp)/'base.zip';envelope(p,sharepoint_site=site)
        with ZipFile(p) as z:entries={n:json.loads(z.read(n)) for n in z.namelist()}
    for name,doc in entries.items():
        if name.endswith('/definition.json'):
            doc['properties']['displayName']=flow_name;doc['properties']['connectionReferences']['shared_sharepointonline']['source']='Invoker'
            doc['properties']['definition']['triggers']={'manual':{'type':'Request','kind':'PowerAppV2','inputs':{'schema':{'type':'object','properties':{},'required':[]}}}} if preflight else trigger(source)
            doc['properties']['definition']['actions']=actions;document=doc
    entries['manifest.json']['details'].update(displayName=flow_name,description='Issue 10 personal-send integration: Create as new owner preview; metadata-only preflight or schema-gated sender, no group/member/permission/schema changes.')
    for item in entries['manifest.json']['resources'].values():
        if item['type']=='Microsoft.Flow/flows':item['details']['displayName']=flow_name
    output.parent.mkdir(parents=True,exist_ok=True)
    with ZipFile(output,'x',ZIP_DEFLATED) as z:
        for name,doc in entries.items():z.writestr(name,json.dumps(doc,indent=2)+'\n')
    review={'sourceTicket':10,'packageBuildId':build_id,'flowName':flow_name,**measure(actions),'limits':{'actions':500,'nesting':8},'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),
      'rulesSourceSha256':hashlib.sha256(Path(rules.__file__).read_bytes()).hexdigest(),'connectionSource':'Invoker','ownerCredentialFallback':False,
      'tenantResult':'NOT_IMPORTED_NOT_TESTED','ordinaryUserAccessVerified':False,'requestSchemaVerifiedInTenant':False,'schemaWrites':0,'membershipWrites':0,'groupWrites':0,
      'requestWrites':0 if preflight else 'At most one POST guarded by observed metadata and native unique SendOperationKey/ConnectionKey; retries disabled, readback reconciles exact immutable intent.',
      'sourceExportSha256':hashlib.sha256(Path(export).read_bytes()).hexdigest() if export else None,
      'existingActorTargetInputsPreserved':not preflight,'existingSuccessMessageOutputsPreserved':not preflight,'addedRequiredInput':None if preflight else 'text IntentId; client must retain same UUID for transport retries',
      'existingSendAppBindingsPreserved':False,'metadataOnly':preflight,'mode':'OWNER_PREVIEW_PENDING_ACCESS_PROOF'}
    output.with_suffix('.definition.json').write_bytes((json.dumps(document,indent=2)+'\n').encode());output.with_suffix('.review.json').write_bytes((json.dumps(review,indent=2)+'\n').encode());return review

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--source',type=Path,required=True);p.add_argument('--preflight',action='store_true');args=p.parse_args();print(json.dumps(build_package(args.output,args.source,preflight=args.preflight),indent=2))
