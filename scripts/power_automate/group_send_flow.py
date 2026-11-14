"""#17 group join send: one request POST, exact replay/readback, no setup writes.

Local generator only. Send/readback pattern adapted from #10 fd3e8d0; this
module owns no other flow and does not change shared child or schema setup.
"""
from copy import deepcopy
import argparse
import hashlib
import json
from pathlib import Path

from . import discovery_flow as d
from .schema_audit import ALL, measure
from .solution_source import inspect_caller_export, invoker_parent_document

ROOT = Path(__file__).resolve().parents[2]
NAME = 'TandemSendGroupJoinRequest'
BUILD = 'issue-17-group-send-v1'
CHILD = 'e9aa88eb-a666-4df1-b088-176be7bcd00d'
CHILD_BUILD = 'c79b7b64-b3ce-4de3-aa74-0ed62bca1524'
SITE = 'https://reedelsevier.sharepoint.com/sites/OG-TandemOrg'
REQUESTS = '3d17485d-1dac-41f0-a1af-24e45daa4567'
PEOPLE = 'fd3adf46-f81d-4a7b-a80c-567fde0175dc'
GROUPS = '4bf1b37f-edce-40c5-8fa0-36543a2d0cd6'
MEMBERS = 'db611ec3-7fa3-477a-878e-effbbb195cb8'
SELECT_REQUEST = 'Id,SenderParticipantId,RecipientParticipantId,TargetGroupId,RequestType,Introduction,Status,SendOperationKey,ConnectionKey,WinningOperationKey,OperationComplete'
PROFILE_FIELDS = ['Teachlanguages','Learnlanguages','ShareCultures','LearnCultures']


def trigger():
    props={}
    for key,title,kind in [('number','GroupId','number'),('text','IntentId','string'),('text_1','Introduction','string')]:
        props[key]={'type':kind,'title':title,'x-ms-content-hint':'NUMBER' if kind=='number' else 'TEXT','x-ms-dynamically-added':True}
    return {'manual':{'type':'Request','kind':'PowerAppV2','inputs':{'schema':{
        'type':'object','properties':props,'required':['number','text']}}}}


def base(list_id):
    return "_api/web/lists(guid'"+list_id+"')"


def request_schema():
    props={'Id':{'type':'integer','minimum':1},'SenderParticipantId':{'type':'integer','minimum':1},
        'RecipientParticipantId':{'type':['integer','null'],'minimum':1},'TargetGroupId':{'type':['integer','null'],'minimum':1},
        'RequestType':{'type':'string','enum':['Personal','Group']},'Introduction':{'type':['string','null'],'maxLength':2000},
        'Status':{'type':'string','enum':['Pending','Accepted','Declined','Cancelled']},
        'SendOperationKey':{'type':'string'},'ConnectionKey':{'type':'string'},
        'WinningOperationKey':{'type':['string','null']},'OperationComplete':{'type':'boolean'}}
    return {'type':'object','required':list(props),'properties':props}


def gate(test, code, previous=None):
    # Expected rejection records its code and fails this scope using typed Parse
    # JSON. No Terminate in a scope (which would prevent the bounded response).
    return d.condition(test,{}, {'Set_'+code:d.setvar('ErrorCode',code),
        'Stop_'+code:d.parse({'allowed':False},{'type':'object','required':['allowed'],
            'properties':{'allowed':{'type':'boolean','enum':[True]}}},'Set_'+code)},previous)


def committed(row):
    return "and(equals("+row+"?['Status'],'Accepted'),equals("+row+"?['OperationComplete'],true),not(empty("+row+"?['WinningOperationKey'])),equals("+row+"?['ConnectionKey'],concat('history:request:',string("+row+"?['Id']))))"


def exact(row):
    immutable=["greater(coalesce("+row+"?['Id'],0),0)",
        "equals("+row+"?['SenderParticipantId'],outputs('Actor_id'))",
        "equals("+row+"?['RecipientParticipantId'],null)",
        "equals("+row+"?['TargetGroupId'],body('Input')?['groupId'])",
        "equals("+row+"?['RequestType'],'Group')",
        "equals(coalesce("+row+"?['Introduction'],''),body('Input')?['introduction'])",
        "equals("+row+"?['SendOperationKey'],outputs('Operation_key'))"]
    pending="and(equals("+row+"?['Status'],'Pending'),equals("+row+"?['OperationComplete'],false),empty("+row+"?['WinningOperationKey']),equals("+row+"?['ConnectionKey'],outputs('Live_key')))"
    accepting="and(equals("+row+"?['Status'],'Accepted'),equals("+row+"?['OperationComplete'],false),not(empty("+row+"?['WinningOperationKey'])),equals("+row+"?['ConnectionKey'],outputs('Live_key')))"
    settled="and(contains(createArray('Accepted','Declined','Cancelled'),"+row+"?['Status']),equals("+row+"?['OperationComplete'],true),not(empty("+row+"?['WinningOperationKey'])),equals("+row+"?['ConnectionKey'],concat('history:request:',string("+row+"?['Id']))))"
    return 'and('+','.join(immutable)+',or('+pending+','+accepting+','+settled+'))'


def result(code, row, previous=None):
    return {code+'_id':d.setvar('RequestId','@'+row+"?['Id']",previous),
        code+'_status':d.setvar('SavedStatus','@'+row+"?['Status']",code+'_id'),
        code+'_result':d.setvar('ResultCode',code,code+'_status')}


def build_actions(seed, build_id=BUILD):
    if seed['receipt']['site']!=SITE or seed['receipt']['sharedChildId']!=CHILD:
        raise ValueError('Unreviewed site/child')
    observed=next(a['inputs'] for a in seed['probe']['properties']['definition']['actions'].values() if a['type']=='OpenApiConnection')
    def http(uri, previous=None, payload=None):
        params={'dataset':SITE,'parameters/method':'GET' if payload is None else 'POST',
            'parameters/uri':uri,'parameters/headers':{'Accept':'application/json;odata=verbose'}}
        inp={'host':deepcopy(observed['host']),'authentication':deepcopy(observed['authentication']),'parameters':params}
        inp['host']['operationId']='HttpRequest'
        if payload is not None:
            params['parameters/body']=payload
            params['parameters/headers']['Content-Type']='application/json;odata=nometadata'
            inp['retryPolicy']={'type':'none'}
        return {'type':'OpenApiConnection','inputs':inp,'runAfter':d.after(previous)}
    def readkey(field,value,previous=None):
        return http(d.cat(base(REQUESTS)+'/items?$select='+SELECT_REQUEST+'&$filter='+field+" eq '",value,"'&$top=2"),previous)
    def item(list_id,reference,fields,previous=None):
        return http(d.cat(base(list_id)+'/items(',reference,')?$select='+fields),previous)
    def rows(name):return "body('"+name+"')?['d']?['results']"
    def one(name):return "first(union("+rows(name)+",createArray(json('{}'))))"
    a={};previous=None
    for name,kind,value in [('ErrorCode','string','INVALID_INPUT'),('ResultCode','string',''),('RequestId','integer',0),('SavedStatus','string',''),('Profiles','array',[]),('AvailableFocus','array',[])]:
        key='Initialize_'+name
        a[key]={'type':'InitializeVariable','inputs':{'variables':[{'name':name,'type':kind,'value':value}]},'runAfter':d.after(previous)}
        previous=key
    s={'Input':d.parse({'groupId':"@triggerBody()?['number']",'intent':"@triggerBody()?['text']",'introduction':"@coalesce(triggerBody()?['text_1'],'')"},
        {'type':'object','required':['groupId','intent','introduction'],'properties':{
            'groupId':{'type':'integer','minimum':1},'intent':{'type':'string','minLength':36,'maxLength':36},
            'introduction':{'type':'string','maxLength':2000}}})}
    stripped="toLower(body('Input')?['intent'])"
    for char in '0123456789abcdef-':stripped="replace("+stripped+",'"+char+"','')"
    uuid=["empty("+stripped+")","equals(length(replace(body('Input')?['intent'],'-','')),32)"]
    uuid += [f"equals(substring(body('Input')?['intent'],{index},1),'-')" for index in [8,13,18,23]]
    s['Require_uuid']=gate('and('+','.join(uuid)+')','INVALID_INTENT','Input')
    s['Clear_input_error']=d.setvar('ErrorCode','','Require_uuid')
    s['Read_invoker']=http('_api/web/currentuser?$select=Id','Clear_input_error')
    s['Invoker']=d.parse("@body('Read_invoker')?['d']",{'type':'object','required':['Id'],'properties':{'Id':{'type':'integer','minimum':1}}},'Read_invoker')
    s['Resolve_actor']=http(d.cat(base(PEOPLE)+'/items?$select=Id&$filter=ParticipantaccountId eq ',"@string(body('Invoker')?['Id'])",'&$top=2'),'Invoker')
    s['Require_actor']=gate('and('+d.complete('Resolve_actor',1)+',equals(length('+rows('Resolve_actor')+'),1))','UNAUTHORIZED_PROFILE','Resolve_actor')
    s['Actor_reference']=d.parse('@'+one('Resolve_actor')+"?['Id']",{'type':'integer','minimum':1},'Require_actor')
    s['Actor_id']=d.compose("@body('Actor_reference')",'Actor_reference')
    s['Operation_key']=d.compose("@concat('group:',string(outputs('Actor_id')),':',toLower(body('Input')?['intent']))",'Actor_id')
    s['Live_key']=d.compose("@concat('open:group:',string(body('Input')?['groupId']),':participant:',string(outputs('Actor_id')))",'Operation_key')
    s['Read_intent']=readkey('SendOperationKey',"@outputs('Operation_key')",'Live_key')
    s['Parsed_intent']=d.parse('@'+rows('Read_intent'),{'type':'array','maxItems':1,'items':request_schema()},'Read_intent')
    s['Require_intent_read']=gate(d.complete('Read_intent',1),'INTENT_READ_INCOMPLETE','Parsed_intent')
    replay={'Prior':d.compose('@'+one('Read_intent'))}
    replay['Require_same_intent']=gate(exact("outputs('Prior')"),'INTENT_CONFLICT','Prior')
    replay.update(result('REPLAY',"outputs('Prior')",'Require_same_intent'))
    new={}
    group_fields='Id,ExchangeType,LanguageFocusId,CultureFocusId,Capacity,State,SourceRequestId,SetupComplete,WriteOwner'
    new['Read_group']=item(GROUPS,"@string(body('Input')?['groupId'])",group_fields)
    id_schema={'type':'integer','minimum':1}
    lookup={'type':'object','required':['results'],'properties':{'results':{'type':'array','maxItems':50,'items':id_schema}}}
    group_props={'Id':id_schema,'ExchangeType':{'type':'string'},'Capacity':{'type':'integer','minimum':2,'maximum':10},
        'State':{'type':'string'},'SourceRequestId':id_schema,'SetupComplete':{'type':'boolean'},'WriteOwner':{'type':['string','null']},
        'LanguageFocusId':lookup,'CultureFocusId':lookup}
    new['Group']=d.parse("@body('Read_group')?['d']",{'type':'object','required':list(group_props),'properties':group_props},'Read_group')
    new['Require_open_group']=gate("and(equals(body('Group')?['Id'],body('Input')?['groupId']),equals(body('Group')?['State'],'Open'),equals(body('Group')?['SetupComplete'],true),empty(body('Group')?['WriteOwner']))",'GROUP_UNAVAILABLE','Group')
    new['Read_source']=item(REQUESTS,"@string(body('Group')?['SourceRequestId'])",SELECT_REQUEST,'Require_open_group')
    new['Source']=d.parse("@body('Read_source')?['d']",request_schema(),'Read_source')
    source="body('Source')"
    new['Require_source']=gate('and('+committed(source)+",equals("+source+"?['Id'],body('Group')?['SourceRequestId']),equals("+source+"?['RequestType'],'Personal'),equals("+source+"?['TargetGroupId'],null),greater(coalesce("+source+"?['SenderParticipantId'],0),0),greater(coalesce("+source+"?['RecipientParticipantId'],0),0),not(equals("+source+"?['SenderParticipantId'],"+source+"?['RecipientParticipantId'])))",'GROUP_SOURCE_UNCOMMITTED','Source')
    own=d.cat(base(MEMBERS)+"/items?$select=Id&$filter=GroupId eq ","@string(body('Input')?['groupId'])",' and ParticipantId eq ',"@string(outputs('Actor_id'))"," and MembershipStatus ne 'Left'&$top=2")
    new['Read_own_memberships']=http(own,'Require_source')
    new['Require_own_memberships_read']=gate(d.complete('Read_own_memberships',1),'MEMBERSHIP_READ_INCOMPLETE','Read_own_memberships')
    new['Require_not_member']=gate('empty('+rows('Read_own_memberships')+')','ALREADY_MEMBER_OR_PROVISIONAL','Require_own_memberships_read')
    new['Read_active_members']=http(d.cat(base(MEMBERS)+"/items?$select=Id,GroupId,ParticipantId,MembershipStatus,MembershipKey&$filter=GroupId eq ","@string(body('Input')?['groupId'])"," and MembershipStatus eq 'Active'&$top=11"),'Require_not_member')
    new['Require_active_read']=gate(d.complete('Read_active_members',10),'MEMBERSHIP_BOUND_OR_INCOMPLETE','Read_active_members')
    member_props={'Id':id_schema,'GroupId':id_schema,'ParticipantId':id_schema,'MembershipStatus':{'type':'string','enum':['Active']},'MembershipKey':{'type':'string','minLength':1}}
    new['Members']=d.parse('@'+rows('Read_active_members'),{'type':'array','maxItems':10,'items':{'type':'object','required':list(member_props),'properties':member_props}},'Require_active_read')
    new['Member_ids']=d.select("@body('Members')","@item()?['ParticipantId']",'Members')
    new['Require_physical_capacity']=gate("and(greater(body('Group')?['Capacity'],length(body('Members'))),equals(length(body('Member_ids')),length(union(body('Member_ids'),body('Member_ids')))),not(contains(body('Member_ids'),outputs('Actor_id'))))",'GROUP_FULL_OR_DUPLICATE_MEMBER','Member_ids')
    # Authenticate each active episode through its immutable request key. Failed
    # or provisional members never disappear to manufacture free capacity.
    checks={}
    # MembershipKey is not interpolated into OData: derive expected membership
    # key from each candidate commit ID returned by an exact sender/recipient filter.
    commit_filter=d.cat(base(REQUESTS)+'/items?$select='+SELECT_REQUEST+'&$filter=(SenderParticipantId eq ',"@string(items('Each_member')?['ParticipantId'])",' or RecipientParticipantId eq ',"@string(items('Each_member')?['ParticipantId'])",
        ") and Status eq 'Accepted' and OperationComplete eq true&$top=501")
    checks['Read_member_commit']=http(commit_filter)
    checks['Require_member_commit_read']=gate(d.complete('Read_member_commit',500),'MEMBER_COMMIT_READ_INCOMPLETE','Read_member_commit')
    member="items('Each_member')"
    match='and('+committed('item()')+",equals("+member+"?['GroupId'],body('Group')?['Id']),equals("+member+"?['MembershipKey'],concat('request:',string(item()?['Id']),':participant:',string("+member+"?['ParticipantId']))),or(and(equals(item()?['RequestType'],'Personal'),equals(item()?['Id'],body('Group')?['SourceRequestId'])),and(equals(item()?['RequestType'],'Group'),equals(item()?['TargetGroupId'],body('Group')?['Id']),equals(item()?['SenderParticipantId'],"+member+"?['ParticipantId']),equals(item()?['RecipientParticipantId'],null))))"
    checks['Committed_episode']=d.query('@'+rows('Read_member_commit'),match,'Require_member_commit_read')
    checks['Require_committed_episode']=gate("equals(length(body('Committed_episode')),1)",'MEMBERSHIP_UNCOMMITTED','Committed_episode')
    new['Each_member']=d.loop("@body('Members')",checks,'Require_physical_capacity')
    profile_select='Id,ParticipantaccountId,Status,ParticipationStatus,OpenToConnections,TimezoneId,'+','.join(f+'Id' for f in PROFILE_FIELDS)
    profile_props={'Id':id_schema,'ParticipantaccountId':id_schema,'Status':{'type':['string','null']},'ParticipationStatus':{'type':['string','null']},
        'OpenToConnections':{'type':['boolean','null']},'TimezoneId':{'type':['integer','null'],'minimum':1},
        **{f+'Id':{'type':'object','required':['results'],'properties':{'results':{'type':'array','items':id_schema}}} for f in PROFILE_FIELDS}}
    new['Profile_ids']=d.compose("@union(createArray(outputs('Actor_id')),body('Member_ids'))",'Each_member')
    reads={'Read_profile':item(PEOPLE,"@string(items('Each_profile'))",profile_select)}
    reads['Profile']=d.parse("@body('Read_profile')?['d']",{'type':'object','required':list(profile_props),'properties':profile_props},'Read_profile')
    reads['Require_profile_identity']=gate("and(equals(body('Profile')?['Id'],items('Each_profile')),or(not(equals(body('Profile')?['Id'],outputs('Actor_id'))),equals(body('Profile')?['ParticipantaccountId'],body('Invoker')?['Id'])))",'PROFILE_IDENTITY_MISMATCH','Profile')
    raw={'profileId':"@body('Profile')?['Id']",'accountKey':"@string(body('Profile')?['ParticipantaccountId'])",'status':"@body('Profile')?['Status']",'participationStatus':"@body('Profile')?['ParticipationStatus']",'openToConnections':"@body('Profile')?['OpenToConnections']",'timezoneId':"@body('Profile')?['TimezoneId']"}
    for target,field in zip(['teachIds','learnIds','shareCultureIds','learnCultureIds'],PROFILE_FIELDS):raw[target]="@body('Profile')?['"+field+"Id']?['results']"
    reads['Add_profile']=d.append('Profiles',raw,'Require_profile_identity')
    new['Each_profile']=d.loop("@outputs('Profile_ids')",reads,'Profile_ids')
    previous='Each_profile'
    mapping=json.loads((ROOT/'config/tenant_schema_mapping.json').read_text(encoding='utf-8'))
    for role in ['language','culture','timezone']:
        name='Read_'+role
        new[name]=http(base(mapping['lists'][role]['listId'])+'/items?$select=Id,Active'+(',ISOcode' if role=='language' else '')+'&$top=5001',previous)
        check='Require_'+role+'_read';new[check]=gate(d.complete(name,5000),'CATALOGUE_'+role.upper()+'_INCOMPLETE',name)
        parsed='Catalogue_'+role
        new[parsed]=d.parse('@'+rows(name),{'type':'array','maxItems':5000,'items':{'type':'object','required':['Id','Active'],'properties':{'Id':id_schema,'Active':{'type':'boolean'},'ISOcode':{'type':['string','null']}}}},check)
        active='Active_'+role;new[active]=d.query("@body('"+parsed+"')","equals(item()?['Active'],true)",parsed)
        ids='IDs_'+role;new[ids]=d.select("@body('"+active+"')","@item()?['Id']",active);previous=ids
    new['Any_language']=d.query("@body('Active_language')","equals(toLower(coalesce(item()?['ISOcode'],'')),'any')",previous)
    new['Require_any']=gate("lessOrEquals(length(body('Any_language')),1)",'ANY_LANGUAGE_AMBIGUOUS','Any_language')
    previous='Require_any'
    for role,field,share in [('language','LanguageFocusId','teachIds'),('culture','CultureFocusId','shareCultureIds')]:
        loop='Available_'+role
        inner={'Available_sharers_'+role:d.query("@variables('Profiles')","and(contains(body('Member_ids'),item()?['profileId']),equals(item()?['status'],'Active'),equals(item()?['participationStatus'],'Active'),equals(item()?['openToConnections'],true),contains(item()?['"+share+"'],items('"+loop+"')))")}
        inner['Record_'+role]=d.append('AvailableFocus',"@not(empty(body('Available_sharers_"+role+"')))",'Available_sharers_'+role)
        new[loop]=d.loop("@body('Group')?['"+field+"']?['results']",inner,previous);previous=loop
    new['Missing_sharer']=d.query("@variables('AvailableFocus')","equals(item(),false)",previous)
    new['Group_context']=d.compose({'groupId':"@body('Group')?['Id']",'exchangeType':"@body('Group')?['ExchangeType']",'state':"@body('Group')?['State']",'capacity':"@body('Group')?['Capacity']",'setupComplete':"@body('Group')?['SetupComplete']",'languageFocusIds':"@body('Group')?['LanguageFocusId']?['results']",'cultureFocusIds':"@body('Group')?['CultureFocusId']?['results']",'memberProfileIds':"@body('Member_ids')",'focusSharersAvailable':"@empty(body('Missing_sharer'))"},'Missing_sharer')
    new['Group_payload']=d.compose({'contractVersion':1,'rulesVersion':1,'mode':'GROUP','profiles':"@variables('Profiles')",'candidateId':"@outputs('Actor_id')",'group':"@outputs('Group_context')",'catalogues':{'languageIds':"@body('IDs_language')",'cultureIds':"@body('IDs_culture')",'timezoneIds':"@body('IDs_timezone')",'anyLanguageId':"@first(union(body('Any_language'),createArray(json('{}'))))?['Id']"}},'Group_context')
    new['Call_group_child']={'type':'Workflow','inputs':{'host':{'workflowReferenceName':CHILD},'body':{'text':"@string(outputs('Group_payload'))"},'retryPolicy':{'type':'none'}},'runAfter':d.after('Group_payload')}
    props={k:{'type':kind,'enum':[value]} for k,kind,value in [('kind','string','TandemValidateContext'),('sourceTicket','integer',81),('contractVersion','integer',1),('rulesVersion','integer',1),('packageBuildId','string',CHILD_BUILD),('success','boolean',True),('code','string','OK'),('authorizesAction','boolean',False),('connectors','integer',0),('reads','integer',0),('writes','integer',0)]}
    props['result']={'type':'object','required':['compatible'],'properties':{'compatible':{'type':'boolean'}}}
    new['Group_result']=d.parse("@json(body('Call_group_child')?['resultjson'])",{'type':'object','required':list(props),'properties':props},'Call_group_child')
    new['Require_group_fit']=gate("and(equals(body('Call_group_child')?['resultcode'],'OK'),equals(body('Call_group_child')?['success'],true),equals(body('Group_result')?['result']?['compatible'],true))",'GROUP_UNAVAILABLE_OR_INCOMPATIBLE','Group_result')
    new['Read_live']=readkey('ConnectionKey',"@outputs('Live_key')",'Require_group_fit')
    new['Require_live_read']=gate(d.complete('Read_live',1),'LIVE_READ_INCOMPLETE','Read_live')
    new['Require_no_live']=gate('empty('+rows('Read_live')+')','CONNECTION_EXISTS','Require_live_read')
    legacy_filter=d.cat(base(REQUESTS)+"/items?$select=Id&$filter=RequestType eq 'Group' and TargetGroupId eq ","@string(body('Input')?['groupId'])",' and SenderParticipantId eq ',"@string(outputs('Actor_id'))"," and (Status eq 'Pending' or (Status eq 'Accepted' and OperationComplete eq false))&$top=2")
    new['Read_unsettled']=http(legacy_filter,'Require_no_live')
    new['Require_unsettled_read']=gate(d.complete('Read_unsettled',1),'UNSETTLED_READ_INCOMPLETE','Read_unsettled')
    new['Require_no_unsettled']=gate('empty('+rows('Read_unsettled')+')','UNSETTLED_CONNECTION_EXISTS','Require_unsettled_read')
    payload={'Title':'Group join request','RequestType':'Group','SenderParticipantId':"@outputs('Actor_id')",'RecipientParticipantId':None,'TargetGroupId':"@body('Input')?['groupId']",'Introduction':"@body('Input')?['introduction']",'Status':'Pending','SendOperationKey':"@outputs('Operation_key')",'ConnectionKey':"@outputs('Live_key')",'WinningOperationKey':None,'OperationComplete':False}
    new['Set_unknown_create']=d.setvar('ErrorCode','CREATE_OUTCOME_UNKNOWN','Require_no_unsettled')
    new['Create_pending']=http(base(REQUESTS)+'/items','Set_unknown_create',payload)
    new['Read_created_intent']=readkey('SendOperationKey',"@outputs('Operation_key')")
    new['Read_created_intent']['runAfter']={'Create_pending':['Succeeded','Failed','TimedOut']}
    new['Parsed_created']=d.parse('@'+rows('Read_created_intent'),{'type':'array','maxItems':1,'items':request_schema()},'Read_created_intent')
    new['Require_created_read']=gate(d.complete('Read_created_intent',1),'CREATE_OUTCOME_UNKNOWN','Parsed_created')
    new['Created_row']=d.compose('@'+one('Read_created_intent'),'Require_created_read')
    saved=result('SAVED',"outputs('Created_row')")
    saved['Clear_confirmed_create']=d.setvar('ErrorCode','','SAVED_result')
    new['Reconcile_create']=d.condition(exact("outputs('Created_row')"),saved,{'Unknown_create':d.setvar('ErrorCode','CREATE_OUTCOME_UNKNOWN')},'Created_row')
    s['Has_intent']=d.condition('not(empty('+rows('Read_intent')+'))',replay,new,'Require_intent_read')
    a['Group_send']={'type':'Scope','actions':s,'runAfter':d.after('Initialize_AvailableFocus')}
    a['Send_report']=d.compose({'kind':NAME,'sourceTicket':17,'packageBuildId':build_id,'contractVersion':1,'rulesVersion':1,
        'success':"@and(not(empty(variables('ResultCode'))),empty(variables('ErrorCode')))",
        'code':"@if(not(empty(variables('ErrorCode'))),variables('ErrorCode'),if(not(empty(variables('ResultCode'))),variables('ResultCode'),'READ_OR_DATA_FAILED'))",
        'requestId':"@variables('RequestId')",'status':"@variables('SavedStatus')",'runReference':"@workflow()?['run']?['name']",'ordinaryUserAccessVerified':False})
    a['Send_report']['runAfter']={'Group_send':ALL}
    body={'success':"@outputs('Send_report')?['success']",'requestid':"@string(variables('RequestId'))",'status':"@variables('SavedStatus')",'resultcode':"@outputs('Send_report')?['code']",'resultjson':"@string(outputs('Send_report'))",'runreference':"@workflow()?['run']?['name']",'errormessage':"@if(outputs('Send_report')?['success'],'','Request was not confirmed. Keep this intent ID and check the run reference.')"}
    a['Respond']={'type':'Response','kind':'PowerApp','runAfter':d.after('Send_report'),'inputs':{'statusCode':200,'body':body,'schema':{'type':'object','properties':{k:{'type':'boolean' if k=='success' else 'string','title':k,'x-ms-dynamically-added':True} for k in body}}}}
    measure(a)
    return a


def build(native_export, output):
    output=Path(output)
    paths=[output,output.with_suffix('.review.json')]
    if any(p.exists() for p in paths):raise FileExistsError(output)
    seed=inspect_caller_export(native_export,SITE,CHILD_BUILD)
    actions=build_actions(seed)
    doc=invoker_parent_document(seed,trigger(),actions)
    doc['properties']['displayName']=NAME+' (owner preview)'
    doc.pop('name',None);doc.pop('id',None)
    doc['properties']['definition'].pop('metadata',None)
    output.parent.mkdir(parents=True,exist_ok=True)
    encoded=(json.dumps(doc,indent=2)+'\n').encode()
    output.write_bytes(encoded)
    child=ROOT/'artifacts/shared_validation/TandemSharedValidation81-v2.child.definition.json'
    review={'sourceTicket':17,'packageBuildId':BUILD,'flowName':NAME,**measure(actions),
        'definitionSha256':hashlib.sha256(encoded).hexdigest(),'nativeExportSha256':seed['receipt']['sourceExportSha256'],
        'sharedChildId':CHILD,'sharedBuildId':CHILD_BUILD,'sharedChildSha256':hashlib.sha256(child.read_bytes()).hexdigest(),
        'contractVersion':1,'rulesVersion':1,'mode':'GROUP','runtimeSource':'invoker',
        'connectionReferenceLogicalName':seed['receipt']['connectionReferenceLogicalName'],
        'inputOrder':['number GroupId','text IntentId','text_1 Introduction optional'],
        'nativeResult':'NOT_RUN','tenantPrerequisites':'BLOCKED: Introduction Note/plain/2000 and request unique keys/immutable fields need deployment audit; owner/native consumer and access tests pending',
        'schemaAuditPerCall':False,'requestWrites':'At most one POST per invocation; retries none; exact immutable readback only',
        'receiptWrites':0,'membershipWrites':0,'groupWrites':0,'schemaWrites':0,'permissionWrites':0,
        'legacyZip':'NOT_EMITTED: Workflow child requires final Solution assembly; readable full parent supplied',
        'templateProvenance':'#10 sender fd3e8d01dba9f3120d5a2b098081d3657b37ebc9 pattern adapted; no edits/dependency on that worktree',
        'evidenceMarker61':'Not applicable: interactive Invoker parent; keep #61 automated-source marker separate'}
    output.with_suffix('.review.json').write_bytes((json.dumps(review,indent=2)+'\n').encode())
    return review


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--native-export',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    args=p.parse_args()
    print(json.dumps(build(args.native_export,args.output),indent=2))
