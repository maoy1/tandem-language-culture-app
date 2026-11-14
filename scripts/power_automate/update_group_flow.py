"""#13 TandemUpdateGroup: guarded SharePoint-only edits; local generation, not certification."""
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4, UUID
from zipfile import ZipFile, ZIP_DEFLATED
import argparse
import hashlib
import json

from . import discovery_flow as d
from .schema_audit import ALL, measure
from .solution_source import RAW_INVOKER, SP_API
from .build_import_probe import build_package as envelope

ROOT = Path(__file__).resolve().parents[2]
NAME = 'TandemUpdateGroup v1'
REQUESTS = '3d17485d-1dac-41f0-a1af-24e45daa4567'
RECEIPT_FIELDS = ['OperationKey', 'IntentJson', 'ResultJson', 'Complete', 'Uncertain',
                  'Retryable', 'DomainEffects', 'AttemptToken', 'SealedAttempts', 'Stage']
DESCRIPTION_LIMIT = 2000  # API technical bound; does not change the native Note setting.


def input_schema():
    edits = {'Title': {'type': 'string', 'minLength': 1, 'maxLength': 255},
             'Purpose': {'type': 'string', 'maxLength': DESCRIPTION_LIMIT},
             'Capacity': {'type': 'integer', 'minimum': 2, 'maximum': 10},
             'State': {'type': 'string', 'enum': ['Open', 'Closed', 'Ended']}}
    props = {'actorId': {'type': 'integer', 'minimum': 1}, 'groupId': {'type': 'integer', 'minimum': 1},
             'expectedETag': {'type': 'string', 'minLength': 1, 'maxLength': 128},
             'intentId': {'type': 'string', 'minLength': 36, 'maxLength': 36},
             'edits': {'type': 'object', 'additionalProperties': False, 'required': list(edits), 'properties': edits}}
    return {'type': 'object', 'additionalProperties': False, 'required': list(props), 'properties': props}


def trigger():
    return {'manual': {'type': 'Request', 'kind': 'PowerAppV2', 'inputs': {'schema': {
        'type': 'object', 'additionalProperties': False, 'required': ['text'], 'properties': {
            'text': {'type': 'string', 'title': 'RequestJson', 'x-ms-content-hint': 'TEXT', 'x-ms-dynamically-added': True}}}}}}


def validate_batch_contract(batch):
    fields = batch['receipts']['fields']
    if batch['sourceTicket'] != 81 or batch['receipts']['title'] != 'TandemOperationReceipts':
        raise ValueError('Expected parent #81 receipt schema target')
    if [f['name'] for f in fields] != RECEIPT_FIELDS:
        raise ValueError('Receipt drift: parent must review all 10 receipt fields')
    expected = ['Text', 'Note', 'Note', 'Boolean', 'Boolean', 'Boolean', 'Boolean', 'Text', 'Note', 'Text']
    if [f['type'] for f in fields] != expected:
        raise ValueError('Receipt field type drift')
    if not all(fields[0].get(k) is True for k in ['required', 'unique', 'indexed']):
        raise ValueError('Native unique OperationKey is required')


def build_actions(site, people, groups, batch, build_id, receipt_list_id=None):
    validate_batch_contract(batch)
    if receipt_list_id is not None:
        receipt_list_id = str(UUID(receipt_list_id))
    base = lambda lid: "_api/web/lists(guid'" + lid + "')"
    group_base = base(groups['lists']['groups']['listId'])
    member_base = base(groups['lists']['members']['listId'])
    person_base = base(people['lists']['participants']['listId'])
    receipt_base = base(receipt_list_id) if receipt_list_id else "_api/web/lists/getbytitle('TandemOperationReceipts')"
    request_base = base(REQUESTS)
    def http(uri, previous=None, payload=None, etag=None):
        headers = {'Accept': 'application/json;odata=verbose'}
        params = {'dataset': site, 'parameters/method': 'GET', 'parameters/uri': uri, 'parameters/headers': headers}
        inputs = {'host': {'apiId': SP_API, 'connectionName': 'shared_sharepointonline', 'operationId': 'HttpRequest'},
                  'parameters': params, 'authentication': {'type': 'Raw', 'value': RAW_INVOKER}}
        if payload is not None:
            params['parameters/method'] = 'POST'; params['parameters/body'] = payload
            headers['Content-Type'] = 'application/json;odata=nometadata'
            inputs['retryPolicy'] = {'type': 'none'}
            if etag is not None:
                if etag in ['', '*']: raise ValueError('Exact CAS ETag required')
                headers.update({'X-HTTP-Method': 'MERGE', 'IF-MATCH': etag})
        return {'type': 'OpenApiConnection', 'inputs': inputs, 'runAfter': d.after(previous)}
    def gate(test, code, previous=None):
        return d.condition(test, {}, {'Set_' + code: d.setvar('ErrorCode', code),
            'Stop_' + code: d.parse({'allowed': False}, {'type': 'object', 'required': ['allowed'],
                'properties': {'allowed': {'type': 'boolean', 'enum': [True]}}}, 'Set_' + code)}, previous)
    def always(action, previous):
        action['runAfter'] = {previous: ['Succeeded', 'Failed', 'TimedOut']}; return action
    def group_uri():
        return d.cat(group_base + '/items(', "@string(body('Input')?['groupId'])",
            ')?$select=Id,Title,Purpose,ExchangeType,Capacity,State,SourceRequestId,SetupComplete,WriteOwner,LanguageFocusId,CultureFocusId')
    def tag(group): return "outputs('" + group + "')?['__metadata']?['etag']"
    def row(action): return "body('" + action + "')?['d']"
    def receipt_uri(): return d.cat(receipt_base + '/items(', "@string(variables('ReceiptId'))", ')')
    def group_write_uri(): return d.cat(group_base + '/items(', "@string(body('Input')?['groupId'])", ')')
    def same_intent(expr):
        return "and(equals(" + expr + "?['OperationKey'],outputs('Operation_key')),equals(json(" + expr + "?['IntentJson']),outputs('Frozen_intent')))"
    def authority(prefix, group, previous):
        """Fresh operational authority, distinct from physical capacity count."""
        x = {}; g = "outputs('" + group + "')"; p = prefix
        x[p+'_Members'] = http(d.cat(member_base + '/items?$select=Id,GroupId,ParticipantId,MembershipStatus,MembershipKey&$filter=GroupId eq ',
            "@string(body('Input')?['groupId'])", " and MembershipStatus eq 'Active'&$top=11"), previous)
        x[p+'_Require_complete_members'] = gate(d.complete(p+'_Members', 10), p+'_MEMBERS_INCOMPLETE', p+'_Members')
        member_schema = {'type': 'array', 'maxItems': 10, 'items': {'type': 'object',
            'required': ['Id','GroupId','ParticipantId','MembershipStatus','MembershipKey'], 'properties': {
                **{k: {'type':'integer','minimum':1} for k in ['Id','GroupId','ParticipantId']},
                'MembershipStatus': {'type':'string','enum':['Active']}, 'MembershipKey': {'type':'string','minLength':1}}}}
        x[p+'_Member_rows'] = d.parse('@'+d.arr(p+'_Members'), member_schema, p+'_Require_complete_members')
        x[p+'_Wrong_group'] = d.query("@body('"+p+"_Member_rows')", "not(equals(item()?['GroupId'],body('Input')?['groupId']))", p+'_Member_rows')
        x[p+'_Actor_members'] = d.query("@body('"+p+"_Member_rows')", "equals(item()?['ParticipantId'],body('Input')?['actorId'])", p+'_Wrong_group')
        x[p+'_Require_one_member'] = gate("and(empty(body('"+p+"_Wrong_group')),equals(length(body('"+p+"_Actor_members')),1))", p+'_NOT_CURRENT_MEMBER', p+'_Actor_members')
        x[p+'_Origin'] = http(d.cat(request_base+'/items(', '@string(int('+g+"?['SourceRequestId']))", ')?$select=Id,RequestType,Status,OperationComplete'), p+'_Require_one_member')
        x[p+'_Require_operational'] = gate("and(equals("+g+"?['SetupComplete'],true),equals("+row(p+'_Origin')+"?['Id'],"+g+"?['SourceRequestId']),equals("+row(p+'_Origin')+"?['RequestType'],'Personal'),equals("+row(p+'_Origin')+"?['Status'],'Accepted'),equals("+row(p+'_Origin')+"?['OperationComplete'],true))", p+'_GROUP_NOT_OPERATIONAL', p+'_Origin')
        member="first(body('"+p+"_Actor_members'))"
        episode="int(replace(replace("+member+"?['MembershipKey'],concat(':participant:',string(body('Input')?['actorId'])),''),'request:',''))"
        x[p+'_Episode_id']=d.parse('@'+episode,{'type':'integer','minimum':1},p+'_Require_operational')
        x[p+'_Actor_request']=http(d.cat(request_base+'/items(',"@string(body('"+p+"_Episode_id'))",')?$select=Id,RequestType,SenderParticipantId,RecipientParticipantId,TargetGroupId,Status,OperationComplete'),p+'_Episode_id')
        item=row(p+'_Actor_request')
        predicate = "and(equals("+item+"?['Id'],body('"+p+"_Episode_id')),equals("+item+"?['Status'],'Accepted'),equals("+item+"?['OperationComplete'],true),equals("+member+"?['MembershipKey'],concat('request:',string("+item+"?['Id']),':participant:',string(body('Input')?['actorId']))),or(and(equals("+item+"?['RequestType'],'Personal'),equals("+item+"?['Id'],"+g+"?['SourceRequestId']),or(equals("+item+"?['SenderParticipantId'],body('Input')?['actorId']),equals("+item+"?['RecipientParticipantId'],body('Input')?['actorId']))),and(equals("+item+"?['RequestType'],'Group'),equals("+item+"?['TargetGroupId'],body('Input')?['groupId']),equals("+item+"?['SenderParticipantId'],body('Input')?['actorId']))))"
        x[p+'_Require_committed_member'] = gate(predicate,p+'_PROVISIONAL_OR_INVALID_EPISODE',p+'_Actor_request')
        return x, p+'_Require_committed_member'
    def group_parse(name, read, previous):
        props = {'Title': {'type':'string','minLength':1,'maxLength':255}, 'Purpose': {'type':['string','null']}, 'Id': {'type':'integer','minimum':1}, 'SourceRequestId': {'type':'number','minimum':1},
            'ExchangeType': {'type':'string','enum':['Language','Culture','Combined']},
            'State': {'type':'string','enum':['Open','Closed','Ended']}, 'SetupComplete': {'type':'boolean'},
            'Capacity': {'type':'number','minimum':2,'maximum':10}, 'WriteOwner': {'type':['string','null']},
            '__metadata': {'type':'object','required':['etag'],'properties':{'etag':{'type':'string','minLength':3,'maxLength':128}}},
            'LanguageFocusId': {'type':'object'}, 'CultureFocusId': {'type':'object'}}
        return d.parse('@'+row(read), {'type':'object','required':list(props),'properties':props}, previous)
    def capacity(group, member_prefix):
        g="outputs('"+group+"')"
        return "and(equals(mod("+g+"?['Capacity'],1),0),equals(mod("+g+"?['SourceRequestId'],1),0),greaterOrEquals(body('Input')?['edits']?['Capacity'],length(body('"+member_prefix+"_Member_rows'))),or(and(equals("+g+"?['ExchangeType'],'Language'),contains(createArray(2,3),body('Input')?['edits']?['Capacity'])),contains(createArray('Culture','Combined'),"+g+"?['ExchangeType'])))"
    a={}; previous=None
    for name,kind,value in [('ErrorCode','string','INPUT_OR_READ_FAILED'),('SavedResult','object',{}),('CurrentGroup','object',{}),('Replay','boolean',False),('Owned','boolean',False),('ClaimRuledOut','boolean',False),('DomainAttempted','boolean',False),('ReceiptId','integer',0)]:
        key='Initialize_'+name; a[key]={'type':'InitializeVariable','inputs':{'variables':[{'name':name,'type':kind,'value':value}]},'runAfter':d.after(previous)};previous=key
    s={}
    s['Request_text'] = d.parse({'value':"@triggerBody()?['text']"}, {'type':'object','required':['value'],'properties':{'value':{'type':'string','maxLength':8000}}})
    s['Input'] = d.parse("@json(body('Request_text')?['value'])",input_schema(),'Request_text')
    stripped="toLower(body('Input')?['intentId'])"
    for c in '0123456789abcdef-': stripped="replace("+stripped+",'"+c+"','')"
    uuid_test="and(empty("+stripped+"),equals(length(body('Input')?['intentId']),36),equals(substring(body('Input')?['intentId'],8,1),'-'),equals(substring(body('Input')?['intentId'],13,1),'-'),equals(substring(body('Input')?['intentId'],18,1),'-'),equals(substring(body('Input')?['intentId'],23,1),'-'),equals(length(replace(body('Input')?['intentId'],'-','')),32),not(empty(trim(body('Input')?['edits']?['Title']))),not(equals(body('Input')?['expectedETag'],'*')))"
    s['Require_input_values']=gate(uuid_test,'INVALID_INPUT','Input')
    s['Read_invoker']=http('_api/web/currentuser?$select=Id','Require_input_values')
    s['Invoker']=d.parse('@'+row('Read_invoker'),{'type':'object','required':['Id'],'properties':{'Id':{'type':'integer','minimum':1}}},'Read_invoker')
    s['Resolve_own_profile']=http(d.cat(person_base+'/items?$select=Id&$filter=ParticipantaccountId eq ',"@string(body('Invoker')?['Id'])",'&$top=2'),'Invoker')
    s['Require_own_profile']=gate('and('+d.complete('Resolve_own_profile',1)+",equals(length(coalesce("+d.arr('Resolve_own_profile')+",json('[]'))),1),equals(first(union(coalesce("+d.arr('Resolve_own_profile')+",json('[]')),createArray(json('{}'))))?['Id'],body('Input')?['actorId']))",'UNAUTHORIZED_PROFILE','Resolve_own_profile')
    s['Read_group_before']=http(group_uri(),'Require_own_profile')
    s['Group_before']=group_parse('Group_before','Read_group_before','Read_group_before')
    s['Require_group_identity']=gate("and(equals(outputs('Group_before')?['Id'],body('Input')?['groupId']),equals(mod(outputs('Group_before')?['SourceRequestId'],1),0))",'GROUP_DATA_INVALID','Group_before')
    auth,prev=authority('Before','Group_before','Require_group_identity');s.update(auth)
    s['Operation_key']=d.compose("@concat('update:',string(body('Input')?['actorId']),':',toLower(body('Input')?['intentId']))",prev)
    s['Frozen_intent']=d.compose({'kind':'update','actorId':"@body('Input')?['actorId']",'groupId':"@body('Input')?['groupId']",'expectedETag':"@body('Input')?['expectedETag']",'edits':"@body('Input')?['edits']"},'Operation_key')
    s['Set_receipt_discovery_error']=d.setvar('ErrorCode','RECEIPT_STORE_UNAVAILABLE','Frozen_intent')
    s['Read_receipt_list']=http(receipt_base+'?$select=Id,Title,BaseTemplate,ListItemEntityTypeFullName','Set_receipt_discovery_error')
    list_props={'Id':{'type':'string','minLength':36,'maxLength':36},'Title':{'type':'string','enum':['TandemOperationReceipts']},'BaseTemplate':{'type':'integer','enum':[100]},'ListItemEntityTypeFullName':{'type':'string','minLength':1}}
    s['Receipt_metadata']=d.parse('@'+row('Read_receipt_list'),{'type':'object','required':list(list_props),'properties':list_props},'Read_receipt_list')
    identity="and(equals(body('Receipt_metadata')?['Title'],'TandemOperationReceipts'),equals(body('Receipt_metadata')?['BaseTemplate'],100),not(empty(body('Receipt_metadata')?['ListItemEntityTypeFullName'])))"
    if receipt_list_id:identity="and("+identity+",equals(toLower(body('Receipt_metadata')?['Id']),'"+receipt_list_id+"'))"
    s['Require_receipt_identity']=gate(identity,'RECEIPT_LIST_MISMATCH','Receipt_metadata')
    receipt_query=d.cat(receipt_base+'/items?$select=Id,'+','.join(RECEIPT_FIELDS)+"&$filter=OperationKey eq '","@outputs('Operation_key')","'&$top=2")
    s['Find_receipt']=http(receipt_query,'Require_receipt_identity')
    s['Require_receipt_read']=gate(d.complete('Find_receipt',1),'RECEIPT_READ_INCOMPLETE','Find_receipt')
    s['Receipt']=d.compose('@first(union('+d.arr('Find_receipt')+",createArray(json('{}'))))",'Require_receipt_read')
    receipt_props = {'Id': {'type':'integer','minimum':1}, 'OperationKey': {'type':'string','minLength':1},
        'IntentJson': {'type':'string','minLength':1}, 'ResultJson': {'type':['string','null']},
        **{k:{'type':'boolean'} for k in ['Complete','Uncertain','Retryable','DomainEffects']},
        'AttemptToken': {'type':'string','minLength':1,'maxLength':255}, 'SealedAttempts': {'type':['string','null']},
        'Stage': {'type':['string','null']}, '__metadata': {'type':'object','required':['etag'],'properties':{'etag':{'type':'string','minLength':3,'maxLength':128}}}}
    receipt_schema = {'type':'object','required':list(receipt_props),'properties':receipt_props}
    result_props = {'resultcode':{'type':'string','minLength':1}, 'groupId':{'type':'integer','minimum':1},
        **{k:{'type':'string'} for k in ['title','purpose','state','etag']},
        'capacity':{'type':'integer','minimum':0,'maximum':10},'memberCount':{'type':'integer','minimum':0,'maximum':10}}
    result_schema = {'type':'object','additionalProperties':False,'required':list(result_props),'properties':result_props}
    def public_group(expr):
        return {'groupId':'@'+expr+"?['Id']", **{k.lower():('@coalesce('+expr+"?['Purpose'],'')" if k=='Purpose' else '@'+expr+"?['"+k+"']") for k in ['Title','Purpose','Capacity','State']}, 'etag':'@'+expr+"?['__metadata']?['etag']"}
    def release(prefix, token, previous, must_own=False):
        p=prefix; x={p+'_Read_release_group':http(group_uri(),previous)}
        x[p+'_Release_group']=group_parse(p+'_Release_group',p+'_Read_release_group',p+'_Read_release_group')
        x[p+'_Capture_current_group']=d.setvar('CurrentGroup',public_group("body('"+p+"_Release_group')"),p+'_Release_group')
        prev=p+'_Capture_current_group'
        if must_own:
            x[p+'_Require_release_owner']=gate("equals(outputs('"+p+"_Release_group')?['WriteOwner'],"+token+')',p+'_OWNERSHIP_LOST',prev)
            prev=p+'_Require_release_owner'
        yes={p+'_Set_release_unknown':d.setvar('ErrorCode','RELEASE_OUTCOME_UNKNOWN')}
        yes[p+'_Release_cas']=http(group_write_uri(),p+'_Set_release_unknown',{'WriteOwner':None},'@'+tag(p+'_Release_group'))
        yes[p+'_Read_released']=always(http(group_uri()),p+'_Release_cas')
        yes[p+'_Released_group']=group_parse(p+'_Released_group',p+'_Read_released',p+'_Read_released')
        yes[p+'_Require_released']=gate("and(equals("+row(p+'_Read_released')+"?['Id'],body('Input')?['groupId']),not(empty("+row(p+'_Read_released')+"?['__metadata']?['etag'])),not(equals("+row(p+'_Read_released')+"?['WriteOwner'],"+token+')))',p+'_RELEASE_UNVERIFIED',p+'_Released_group')
        yes[p+'_Capture_released_group']=d.setvar('CurrentGroup',public_group("body('"+p+"_Read_released')?['d']"),p+'_Require_released')
        x[p+'_Release_if_owned']=d.condition("equals(outputs('"+p+"_Release_group')?['WriteOwner'],"+token+')',yes,{},prev)
        settled="or(and(equals(actions('"+p+"_Require_released')?['status'],'Succeeded'),equals(actions('"+p+"_Capture_released_group')?['status'],'Succeeded')),and("+str(not must_own).lower()+",equals(actions('"+p+"_Capture_current_group')?['status'],'Succeeded'),not(equals(body('"+p+"_Release_group')?['WriteOwner'],"+token+"))))"
        x[p+'_Require_release_settled']=always(gate(settled,p+'_RELEASE_NOT_SETTLED'),p+'_Release_if_owned')
        x[p+'_Clear_owned']=d.setvar('Owned',False,p+'_Require_release_settled')
        return x,p+'_Clear_owned'
    def finish(prefix,result,previous,effects,release_owner=True):
        p=prefix;x={p+'_Read_receipt':http(receipt_uri(),previous)}
        x[p+'_Receipt']=d.parse('@'+row(p+'_Read_receipt'),receipt_schema,p+'_Read_receipt')
        x[p+'_Require_active_receipt']=gate('and('+same_intent("body('"+p+"_Receipt')")+",equals(body('"+p+"_Receipt')?['AttemptToken'],outputs('This_token')),equals(body('"+p+"_Receipt')?['Complete'],false))",p+'_RECEIPT_CHANGED',p+'_Receipt')
        x[p+'_Set_receipt_unknown']=d.setvar('ErrorCode','RECEIPT_COMPLETION_UNKNOWN',p+'_Require_active_receipt')
        patch={'ResultJson':'@string('+result+')','Complete':True,'Uncertain':False,'Retryable':False,
               'DomainEffects':effects,'Stage':'Complete' if effects else 'Rejected'}
        x[p+'_Complete_cas']=http(receipt_uri(),p+'_Set_receipt_unknown',patch,"@body('"+p+"_Receipt')?['__metadata']?['etag']")
        x[p+'_Read_completed']=always(http(receipt_uri()),p+'_Complete_cas')
        r=row(p+'_Read_completed')
        check='and('+same_intent(r)+",equals("+r+"?['AttemptToken'],outputs('This_token')),equals("+r+"?['Complete'],true),equals("+r+"?['Uncertain'],false),equals("+r+"?['Retryable'],false),equals("+r+"?['DomainEffects'],"+str(effects).lower()+"),equals(json("+r+"?['ResultJson']),"+result+'))'
        x[p+'_Require_completed']=gate(check,p+'_RECEIPT_COMPLETION_UNVERIFIED',p+'_Read_completed')
        prev=p+'_Require_completed'
        if release_owner:
            rel,prev=release(p,"outputs('This_token')",prev,must_own=True);x.update(rel)
        x[p+'_Save_result']=d.setvar('SavedResult','@'+result,prev)
        x[p+'_Clear_error']=d.setvar('ErrorCode','',p+'_Save_result')
        return x
    existing={'Existing_receipt':d.parse("@outputs('Receipt')",receipt_schema)}
    existing['Require_same_intent']=gate(same_intent("body('Existing_receipt')"),'INTENT_CONFLICT','Existing_receipt')
    existing['Require_completed_receipt']=gate("equals(body('Existing_receipt')?['Complete'],true)",'OPERATION_IN_PROGRESS_OR_UNKNOWN','Require_same_intent')
    existing['Saved_receipt_result']=d.parse("@json(body('Existing_receipt')?['ResultJson'])",result_schema,'Require_completed_receipt')
    expected_result="and(equals(body('Saved_receipt_result')?['groupId'],body('Input')?['groupId']),or(not(equals(body('Saved_receipt_result')?['resultcode'],'UPDATED')),and(equals(body('Saved_receipt_result')?['title'],body('Input')?['edits']?['Title']),equals(body('Saved_receipt_result')?['purpose'],body('Input')?['edits']?['Purpose']),equals(body('Saved_receipt_result')?['capacity'],body('Input')?['edits']?['Capacity']),equals(body('Saved_receipt_result')?['state'],body('Input')?['edits']?['State']),not(empty(body('Saved_receipt_result')?['etag'])),equals(body('Existing_receipt')?['DomainEffects'],true),equals(body('Existing_receipt')?['Uncertain'],false))))"
    existing['Require_saved_result']=gate(expected_result,'SAVED_RESULT_INVALID','Saved_receipt_result')
    rel,prev=release('Replay',"body('Existing_receipt')?['AttemptToken']",'Require_saved_result');existing.update(rel)
    existing['Replay_result']=d.setvar('SavedResult',"@body('Saved_receipt_result')",prev)
    existing['Mark_replay']=d.setvar('Replay',True,'Replay_result')
    existing['Replay_clear_error']=d.setvar('ErrorCode','','Mark_replay')
    fresh={
        'Require_expected_revision':gate("equals(outputs('Group_before')?['__metadata']?['etag'],body('Input')?['expectedETag'])",'REVISION_CONFLICT'),
        'Require_not_busy':gate("empty(outputs('Group_before')?['WriteOwner'])",'GROUP_BUSY','Require_expected_revision'),
        'Require_not_ended':gate("contains(createArray('Open','Closed'),outputs('Group_before')?['State'])",'GROUP_ENDED_FINAL','Require_not_busy'),
        'Require_capacity_before':gate(capacity('Group_before','Before'),'CAPACITY_INVALID','Require_not_ended'),
        'Attempt_uuid':d.compose('@guid()','Require_capacity_before')}
    fresh['This_token']=d.compose("@string(outputs('Token_parts'))",'Token_parts')
    fresh['Token_parts']=d.compose({'operation':"@outputs('Operation_key')",'attempt':"@outputs('Attempt_uuid')"},'Attempt_uuid')
    fresh['Set_receipt_create_unknown']=d.setvar('ErrorCode','RECEIPT_CREATE_OUTCOME_UNKNOWN','This_token')
    payload={'Title':"@outputs('Operation_key')",'OperationKey':"@outputs('Operation_key')",'IntentJson':"@string(outputs('Frozen_intent'))",'ResultJson':None,
             'Complete':False,'Uncertain':False,'Retryable':False,'DomainEffects':False,'AttemptToken':"@outputs('This_token')",'SealedAttempts':'[]','Stage':'Prepared'}
    fresh['Create_receipt']=http(receipt_base+'/items','Set_receipt_create_unknown',payload)
    fresh['Read_created_receipt']=always(http(receipt_query),'Create_receipt')
    fresh['Require_created_receipt_bound']=gate('and('+d.complete('Read_created_receipt',1)+",equals(length(coalesce("+d.arr('Read_created_receipt')+",json('[]'))),1))",'RECEIPT_CREATE_UNVERIFIED','Read_created_receipt')
    fresh['Created_receipt']=d.parse('@first('+d.arr('Read_created_receipt')+')',receipt_schema,'Require_created_receipt_bound')
    fresh['Require_our_receipt']=gate('and('+same_intent("body('Created_receipt')")+",equals(body('Created_receipt')?['AttemptToken'],outputs('This_token')),equals(body('Created_receipt')?['Complete'],false),equals(body('Created_receipt')?['DomainEffects'],false),equals(body('Created_receipt')?['Uncertain'],false))",'OPERATION_RACE_OR_UNKNOWN','Created_receipt')
    fresh['Set_receipt_id']=d.setvar('ReceiptId',"@body('Created_receipt')?['Id']",'Require_our_receipt')
    fresh['Set_claim_unknown']=d.setvar('ErrorCode','CLAIM_OUTCOME_UNKNOWN','Set_receipt_id')
    fresh['Claim_group']=http(group_write_uri(),'Set_claim_unknown',{'WriteOwner':"@outputs('This_token')"},'@'+tag('Group_before'))
    fresh['Read_claimed_group']=always(http(group_uri()),'Claim_group')
    fresh['Group_locked']=group_parse('Group_locked','Read_claimed_group','Read_claimed_group')
    fresh['Mark_claim_ruled_out']=d.setvar('ClaimRuledOut',"@and(equals(outputs('Group_locked')?['Id'],body('Input')?['groupId']),not(equals(outputs('Group_locked')?['WriteOwner'],outputs('This_token'))),not(equals("+tag('Group_locked')+','+tag('Group_before')+')))','Group_locked')
    fresh['Require_our_claim']=gate("and(equals(outputs('Group_locked')?['Id'],body('Input')?['groupId']),equals(outputs('Group_locked')?['WriteOwner'],outputs('This_token')),not(equals("+tag('Group_locked')+','+tag('Group_before')+')))', 'CLAIM_CONFLICT_OR_UNKNOWN','Mark_claim_ruled_out')
    fresh['Mark_owned']=d.setvar('Owned',True,'Require_our_claim')
    immutable=['ExchangeType','LanguageFocusId','CultureFocusId','SourceRequestId','SetupComplete']
    unchanged="and("+','.join("equals(outputs('Group_locked')?['"+k+"'],outputs('Group_before')?['"+k+"'])" for k in immutable+['Title','Purpose','Capacity','State'])+')'
    fresh['Set_locked_read_failure']=d.setvar('ErrorCode','LOCKED_READ_OR_DATA_FAILED','Mark_owned')
    fresh['Require_locked_snapshot']=gate(unchanged,'LOCKED_SNAPSHOT_CHANGED','Set_locked_read_failure')
    auth,prev=authority('Locked','Group_locked','Require_locked_snapshot');fresh.update(auth)
    fresh['Require_capacity_locked']=gate(capacity('Group_locked','Locked'),'CAPACITY_CHANGED_OR_INVALID',prev)
    fresh['Read_active_receipt']=http(receipt_uri(),'Require_capacity_locked')
    fresh['Active_receipt']=d.parse('@'+row('Read_active_receipt'),receipt_schema,'Read_active_receipt')
    fresh['Require_active_attempt']=gate('and('+same_intent("body('Active_receipt')")+",equals(body('Active_receipt')?['AttemptToken'],outputs('This_token')),equals(body('Active_receipt')?['Complete'],false))",'ATTEMPT_NO_LONGER_ACTIVE','Active_receipt')
    fresh['Mark_possible_effects']=http(receipt_uri(),'Require_active_attempt',{'DomainEffects':True,'Uncertain':True,'Retryable':False,'Stage':'Updating'},"@body('Active_receipt')?['__metadata']?['etag']")
    fresh['Read_effect_marker']=always(http(receipt_uri()),'Mark_possible_effects')
    marker=row('Read_effect_marker')
    fresh['Require_effect_marker']=gate('and('+same_intent(marker)+",equals("+marker+"?['AttemptToken'],outputs('This_token')),equals("+marker+"?['Complete'],false),equals("+marker+"?['DomainEffects'],true),equals("+marker+"?['Uncertain'],true))",'RECEIPT_STAGE_UNKNOWN','Read_effect_marker')
    fresh['Mark_domain_attempted']=d.setvar('DomainAttempted',True,'Require_effect_marker')
    fresh['Set_update_unknown']=d.setvar('ErrorCode','UPDATE_OUTCOME_UNKNOWN','Mark_domain_attempted')
    patch={k:"@body('Input')?['edits']?['"+k+"']" for k in ['Title','Purpose','Capacity','State']}
    fresh['Update_group_cas']=http(group_write_uri(),'Set_update_unknown',patch,'@'+tag('Group_locked'))
    fresh['Read_updated_group']=always(http(group_uri()),'Update_group_cas')
    fresh['Group_updated']=group_parse('Group_updated','Read_updated_group','Read_updated_group')
    exact=["equals(outputs('Group_updated')?['Id'],body('Input')?['groupId'])","equals(outputs('Group_updated')?['WriteOwner'],outputs('This_token'))","not(equals("+tag('Group_updated')+','+tag('Group_locked')+'))']
    exact += ["equals("+("coalesce(outputs('Group_updated')?['Purpose'],'')" if k=='Purpose' else "outputs('Group_updated')?['"+k+"']")+",body('Input')?['edits']?['"+k+"'])" for k in patch]
    exact += ["equals(outputs('Group_updated')?['"+k+"'],outputs('Group_locked')?['"+k+"'])" for k in immutable]
    fresh['Require_exact_update']=gate('and('+','.join(exact)+')','UPDATE_OUTCOME_UNKNOWN','Group_updated')
    result={'resultcode':'UPDATED','groupId':"@body('Input')?['groupId']",'title':"@body('Input')?['edits']?['Title']",'purpose':"@body('Input')?['edits']?['Purpose']",'capacity':"@body('Input')?['edits']?['Capacity']",'state':"@body('Input')?['edits']?['State']",'etag':'@'+tag('Group_updated'),'memberCount':"@length(body('Locked_Member_rows'))"}
    fresh['Proposed_result']=d.compose(result,'Require_exact_update')
    fresh.update(finish('Commit',"outputs('Proposed_result')",'Proposed_result',True))
    s['Has_receipt']=d.condition("not(empty("+d.arr('Find_receipt')+'))',existing,fresh,'Receipt')
    a['Update_operation']={'type':'Scope','actions':s,'runAfter':d.after(previous)}
    reject={'Rejected_result':d.compose({'resultcode':"@variables('ErrorCode')",'groupId':"@body('Input')?['groupId']",'title':'','purpose':'','state':'','etag':'','capacity':0,'memberCount':0})}
    reject['Reject_with_or_without_claim']=d.condition("equals(variables('Owned'),true)",finish('Reject',"outputs('Rejected_result')",None,False),finish('Reject_unclaimed',"outputs('Rejected_result')",None,False,release_owner=False),'Rejected_result')
    a['Finalize_known_no_domain_failure']=d.condition("and(or(equals(variables('Owned'),true),equals(variables('ClaimRuledOut'),true)),equals(variables('DomainAttempted'),false),empty(variables('SavedResult')))",reject,{})
    a['Finalize_known_no_domain_failure']['runAfter']={'Update_operation':ALL}
    ok="and(empty(variables('ErrorCode')),equals(variables('SavedResult')?['resultcode'],'UPDATED'))"
    code="if(not(empty(variables('ErrorCode'))),variables('ErrorCode'),if(equals(variables('Replay'),true),if(equals(variables('SavedResult')?['resultcode'],'UPDATED'),'REPLAY',variables('SavedResult')?['resultcode']),coalesce(variables('SavedResult')?['resultcode'],'READ_OR_DATA_FAILED')))"
    a['Update_report']=d.compose({'kind':'TandemUpdateGroup','sourceTicket':13,'schemaVersion':1,'packageBuildId':build_id,'success':'@'+ok,'code':'@'+code,'replay':"@variables('Replay')",'saved':"@variables('SavedResult')",'runReference':"@workflow()?['run']?['name']",'nativeAuthorityVerified':False,'schemaSetupVerified':False,'receiptTargetMode':'PINNED_GUID' if receipt_list_id else 'EXACT_UNIQUE_TITLE'})
    a['Update_report']['runAfter']={'Finalize_known_no_domain_failure':ALL}
    outputs={'success':('boolean','@'+ok),'resultcode':('string',"@outputs('Update_report')?['code']"),'resultjson':('string',"@string(outputs('Update_report'))"),'groupjson':('string',"@if("+ok+",string(variables('CurrentGroup')),'{}')"),'etag':('string',"@if("+ok+",variables('CurrentGroup')?['etag'],'')"),'errormessage':('string',"@if("+ok+",'','Group update was not confirmed. Keep the same intent ID, refresh and retain the run reference.')"),'runreference':('string',"@outputs('Update_report')?['runReference']")}
    a['Respond']={'type':'Response','kind':'PowerApp','runAfter':d.after('Update_report'),'inputs':{'statusCode':200,'schema':{'type':'object','properties':{k:{'type':t,'title':k,'x-ms-dynamically-added':True} for k,(t,v) in outputs.items()}},'body':{k:v for k,(t,v) in outputs.items()}}}
    measure(a);return a

def build_parent_document(site, people, groups, batch, build_id, receipt_list_id=None):
    """Complete legacy-format parent document: trigger, response, bindings and actions.

    Parent batch can adapt this document through #81's inspected native Solution
    builder. It is deliberately not represented as a deployed/native-certified flow.
    """
    actions=build_actions(site,people,groups,batch,build_id,receipt_list_id)
    with TemporaryDirectory() as temporary:
        path=Path(temporary)/'envelope.zip';document=envelope(path,sharepoint_site=site)
    document['properties']['displayName']=NAME
    document['properties']['connectionReferences']['shared_sharepointonline']['source']='Invoker'
    document['properties']['definition']['triggers']=trigger()
    document['properties']['definition']['actions']=actions
    return document


def build_package(output, batch_contract_path, receipt_list_id=None):
    output=Path(output)
    paths=[output,output.with_suffix('.parent.json'),output.with_suffix('.review.json')]
    if any(p.exists() for p in paths):raise FileExistsError('Use a fresh artifact stem')
    batch_bytes=Path(batch_contract_path).read_bytes();batch=json.loads(batch_bytes)
    people=json.loads((ROOT/'config/tenant_schema_mapping.json').read_text(encoding='utf-8'))
    groups=json.loads((ROOT/'config/group_schema_mapping.json').read_text(encoding='utf-8'))
    site=batch['site'];build_id=str(uuid4())
    document=build_parent_document(site,people,groups,batch,build_id,receipt_list_id)
    with TemporaryDirectory() as temporary:
        path=Path(temporary)/'envelope.zip';envelope(path,sharepoint_site=site)
        with ZipFile(path) as z:entries={n:json.loads(z.read(n)) for n in z.namelist()}
    # Keep the generated envelope resource identity, while supplying the complete
    # parent definition/bindings. No working native flow identity is copied.
    for name,value in entries.items():
        if name.endswith('/definition.json'):
            value['properties']=deepcopy(document['properties']);document=value
    entries['manifest.json']['details'].update(displayName=NAME,description='Issue13 owner prototype. Receipt schema setup/native member/write acceptance pending; no existing flow overwrite.')
    for resource in entries['manifest.json']['resources'].values():
        if resource['type']=='Microsoft.Flow/flows':resource['details']['displayName']=NAME
    output.parent.mkdir(parents=True,exist_ok=True)
    with ZipFile(output,'x',ZIP_DEFLATED) as z:
        for name,value in entries.items():z.writestr(name,json.dumps(value,indent=2)+'\n')
    parent_bytes=(json.dumps(document,indent=2)+'\n').encode();output.with_suffix('.parent.json').write_bytes(parent_bytes)
    review={'sourceTicket':13,'packageBuildId':build_id,'flowName':NAME,
        **measure(document['properties']['definition']['actions']), 'limits':{'actions':500,'maximumActionDepth':8},
        'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'parentSha256':hashlib.sha256(parent_bytes).hexdigest(),
        'generatorSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'batchSchemaSha256':hashlib.sha256(batch_bytes).hexdigest(),'batchSchemaVersion':batch['schemaVersion'],
        'receiptListId':receipt_list_id,'receiptSetupVerified':False,
        'receiptTargetMode':'PINNED_GUID' if receipt_list_id else 'EXACT_UNIQUE_TITLE',
        'deploymentGate':'ENABLE_ONLY_AFTER_PARENT_SETUP_APPLY_AND_AUDIT; NO_REBUILD_REQUIRED_FOR_TITLE_RESOLUTION',
        'connectionSource':'Invoker','ownerFallback':False,'schemaWrites':0,'membershipWrites':0,'participantWrites':0,
        'descriptionTechnicalLimit':DESCRIPTION_LIMIT,'nativeResult':'NOT_IMPORTED_NOT_TESTED',
        'nativeMemberAuthorityVerified':False,'ordinaryUserAccessVerified':False,
        'sharedValidator':'Not invoked: no profile normalization or matching; only operation-time authority/count/CAS guards.',
        'deployment':'Complete legacy-format parent. Parent batch owns Solution assembly/connection validation and #81 setup; no native linkage/readiness claim.'}
    output.with_suffix('.review.json').write_bytes((json.dumps(review,indent=2)+'\n').encode());return review


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--batch-contract',type=Path,required=True)
    p.add_argument('--receipt-list-id',help='Optional actual GUID pin; default exact title resolves after parent Setup Apply+Audit without rebuild')
    args=p.parse_args();print(json.dumps(build_package(args.output,args.batch_contract,args.receipt_list_id),indent=2))
