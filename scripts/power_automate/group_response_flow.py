"""#65 Power Automate parent. Python is local build/test tooling only."""
from copy import deepcopy
import argparse, hashlib, json
from pathlib import Path
from uuid import uuid4
from . import discovery_flow as d
from .schema_audit import measure, ALL
from .solution_source import walk
ROOT=d.ROOT
CHILD='e9aa88eb-a666-4df1-b088-176be7bcd00d'
REQUESTS='3d17485d-1dac-41f0-a1af-24e45daa4567'
RECEIPTS="_api/web/lists/getbytitle('TandemOperationReceipts')"
NAME='TandemRespondGroupJoinRequest'
UUID_PATTERN='^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'


def trigger():
    props={'number':{'type':'number','title':'RequestId','x-ms-content-hint':'NUMBER'},'text':{'type':'string','title':'Decision','x-ms-content-hint':'TEXT'},'text_1':{'type':'string','title':'IntentUUID','x-ms-content-hint':'TEXT'}}
    return {'manual':{'type':'Request','kind':'PowerAppV2','inputs':{'schema':{'type':'object','properties':props,'required':list(props)}}}}


def source_document():return json.loads((ROOT/'artifacts/tandem_discovery/TandemDiscovery-v2.definition.json').read_text(encoding='utf-8'))


class Block:
    def __init__(self):self.actions={};self.last=None;self.code=None
    def add(self,name,action,always=False):
        action=deepcopy(action);action['runAfter']={self.last:['Succeeded','Failed','TimedOut'] if always else ['Succeeded']} if self.last else {}
        # Code is local to this sequential flow. Reassign it only when its value
        # can differ; every guard and its failure behavior remains emitted.
        if action['type']=='SetVariable' and action.get('inputs',{}).get('name')=='Code':
            value=action['inputs']['value'];self.code=value if isinstance(value,str) and not value.startswith('@') else None
        elif any(child.get('type')=='SetVariable' and child.get('inputs',{}).get('name')=='Code'
                 for _,child in walk({name:action})):
            self.code=None
        self.actions[name]=action;self.last=name;return name
    def compose(self,name,value):return self.add(name,d.compose(value))
    def set(self,name,var,value):return self.add(name,d.setvar(var,value))
    def gate(self,name,test,code):
        if code!=self.code and code not in ['NO_BOUND_RECEIPT','READ_OR_ETAG_FAILED','RECEIPT_WRITE_UNCERTAIN','ATTEMPT_NOT_ACTIVE']:self.set(name+'_Code','Code',code)
        return self.add(name,d.parse({'valid':'@'+test},{'type':'object','required':['valid'],'properties':{'valid':{'type':'boolean','enum':[True]}}}))


class Builder:
    def __init__(self,original,mapping,groups,build_id):
        if original['properties']['connectionReferences']['shared_sharepointonline']['source']!='Invoker':raise ValueError('Invoker source required')
        self.original=original;self.mapping=mapping;self.groups=groups;self.build_id=build_id
        self.template=deepcopy(next(a for name,a in walk(original['properties']['definition']['actions']) if name=='Get_item'))
        self.site=self.template['inputs']['parameters']['dataset'];self.auth=deepcopy(self.template['inputs']['authentication'])
        if self.template['inputs']['parameters']['table'].strip('{}').lower()!=mapping['lists']['participants']['listId']:raise ValueError('Unverified participant source')
        if self.site!='https://reedelsevier.sharepoint.com/sites/OG-TandemOrg':raise ValueError('Unverified site')
        if not groups['mappingVerified']:raise ValueError('Verified group mapping required')
        self.base={'requests':"_api/web/lists(guid'"+REQUESTS+"')",'receipts':RECEIPTS}
        for key in ['groups','members']:self.base[key]="_api/web/lists(guid'"+groups['lists'][key]['listId']+"')"
        self.base['participants']="_api/web/lists(guid'"+mapping['lists']['participants']['listId']+"')"
    def http(self,uri,method='GET',payload=None,etag=None):
        headers={'Accept':'application/json;odata=verbose','Content-Type':'application/json;odata=verbose'}
        if etag is not None:
            if etag in ['', '*']:raise ValueError('Exact ETag required')
            headers.update({'X-HTTP-Method':'MERGE','IF-MATCH':etag})
        p={'dataset':self.site,'parameters/method':method,'parameters/uri':uri,'parameters/headers':headers}
        if payload is not None:p['parameters/body']=payload
        return {'type':'OpenApiConnection','inputs':{'host':{'apiId':'/providers/Microsoft.PowerApps/apis/shared_sharepointonline','connectionName':'shared_sharepointonline','operationId':'HttpRequest'},'parameters':p,'authentication':deepcopy(self.auth),'retryPolicy':{'type':'none'}},'runAfter':{}}
    def uri(self,role,idexpr):return d.cat(self.base[role]+'/items(', '@string('+idexpr+')', ')')
    def getvar(self,b,prefix,role,idexpr,var,always=False,check_tag=True):
        b.add(prefix,self.http(self.uri(role,idexpr)),always);b.set(prefix+'_Save',var,"@body('"+prefix+"')?['d']")
        tag="and(not(empty(variables('"+var+"')?['__metadata']?['etag'])),not(equals(variables('"+var+"')?['__metadata']?['etag'],'*')))"
        if var=='Group':
            props={'Id':{'type':'integer','minimum':1},'Capacity':{'type':'integer','minimum':2,'maximum':10},
                'SourceRequestId':{'type':'integer','minimum':1},'SetupComplete':{'type':'boolean'},
                'State':{'type':'string','enum':['Open','Closed','Ended']}}
            for field in ['LanguageFocusId','CultureFocusId']:
                props[field]={'type':'object','required':['results'],'properties':{'results':{'type':'array','maxItems':100,'items':{'type':'integer','minimum':1}}}}
            # One native object parser validates both current group types and the
            # exact read tag. No extra control container or duplicated guard.
            b.add(prefix+'_Shape',d.parse({'row':"@variables('Group')",'etagValid':'@'+tag},
                {'type':'object','required':['row','etagValid'],'properties':{
                    'row':{'type':'object','required':list(props),'properties':props},
                    'etagValid':{'type':'boolean','enum':[True]}}}))
        elif check_tag:b.gate(prefix+'_Tag',tag,'READ_OR_ETAG_FAILED')
    def collection(self,b,name,uri,bound,always=False):
        b.add(name,self.http(uri),always);b.gate(name+'_Bound',d.complete(name,bound),'READ_BOUND_OR_INCOMPLETE')
    def patch_receipt(self,b,prefix,patch):
        read=prefix+'_Read';snapshot="body('"+read+"')?['d']"
        b.add(read,self.http(self.uri('receipts',"variables('Receipt')?['Id']")))
        authority="and(not(empty(variables('Receipt')?['__metadata']?['etag'])),not(equals(variables('Receipt')?['__metadata']?['etag'],'*')),equals(variables('Receipt')?['Complete'],false),equals(variables('Receipt')?['AttemptToken'],variables('Attempt')),not(contains(json(coalesce(variables('Receipt')?['SealedAttempts'],'[]')),variables('Attempt'))))"
        b.gate(prefix+'_Authority',authority.replace("variables('Receipt')",snapshot),'ATTEMPT_NOT_ACTIVE')
        fresh_patch=json.loads(json.dumps(patch).replace("variables('Receipt')",snapshot))
        b.add(prefix+'_Write',self.http(self.uri('receipts',"variables('Receipt')?['Id']"),'POST',{'__metadata':{'type':"@body('Receipt_type')?['value']"},**fresh_patch},'@'+snapshot+"?['__metadata']?['etag']"))
        self.getvar(b,prefix+'_Confirm','receipts',"variables('Receipt')?['Id']",'Receipt',True,check_tag=False)
        checks=["equals(variables('Receipt')?['"+k+"'],"+(v[1:] if isinstance(v,str) and v.startswith('@') else ('true' if v is True else 'false' if v is False else d.wdl_string(v)))+")" for k,v in patch.items()]
        checks.extend(["not(empty(variables('Receipt')?['__metadata']?['etag']))","not(equals(variables('Receipt')?['__metadata']?['etag'],'*'))"])
        b.gate(prefix+'_Persisted','and('+','.join(checks)+')','RECEIPT_WRITE_UNCERTAIN')
    def stage(self,b,prefix,stage):self.patch_receipt(b,prefix,{'Stage':stage,'Uncertain':True})
    def shared(self,b,prefix,mode,profiles,**extra):
        b.compose(prefix+'_Request',{'contractVersion':1,'rulesVersion':1,'mode':mode,'profiles':profiles,'catalogues':"@outputs('Catalogues')",**extra})
        b.gate(prefix+'_Size',"lessOrEquals(length(string(outputs('"+prefix+"_Request'))),250000)",'SHARED_REQUEST_BOUND')
        b.add(prefix+'_Call',{'type':'Workflow','inputs':{'host':{'workflowReferenceName':CHILD},'body':{'text':"@string(outputs('"+prefix+"_Request'))"}}})
        b.add(prefix+'_Result',d.parse("@json(body('"+prefix+"_Call')?['resultjson'])",{'type':'object','required':['result','success','code','contractVersion','rulesVersion','authorizesAction']}))
        checks=["equals(body('"+prefix+"_Call')?['success'],true)","equals(body('"+prefix+"_Call')?['resultcode'],'OK')"]
        for k,v in [('success','true'),('code',"'OK'"),('contractVersion','1'),('rulesVersion','1'),('authorizesAction','false')]:checks.append("equals(body('"+prefix+"_Result')?['"+k+"'],"+v+")")
        b.gate(prefix+'_Valid','and('+','.join(checks)+')','SHARED_VALIDATION_FAILED')
    def current(self,b,prefix):
        self.getvar(b,prefix+'_Request','requests',"body('Input')?['number']",'Request')
        b.gate(prefix+'_Request_binding',"and(equals(variables('Request')?['Id'],body('Input')?['number']),equals(variables('Request')?['RequestType'],'Group'),equals(variables('Request')?['TargetGroupId'],variables('TargetGroup')),equals(variables('Request')?['SenderParticipantId'],variables('Requester')))",'REQUEST_BINDING_CHANGED')
        self.getvar(b,prefix+'_Group','groups',"variables('TargetGroup')",'Group')
        self.collection(b,prefix+'_Members',d.cat(self.base['members']+'/items?$filter=GroupId eq ',"@string(variables('TargetGroup'))"," and MembershipStatus eq 'Active'&$top=12"),11)
        b.set(prefix+'_Save_members','Members',"@body('"+prefix+"_Members')?['d']?['results']")
        source_read=prefix+'_Source';source="body('"+source_read+"')?['d']"
        b.add(source_read,self.http(self.uri('requests',"variables('Group')?['SourceRequestId']")))
        b.gate(source_read+'_Tag',"and(not(empty("+source+"?['__metadata']?['etag'])),not(equals("+source+"?['__metadata']?['etag'],'*')))",'READ_OR_ETAG_FAILED')
        b.gate(prefix+'_Operational',"and(equals(variables('Group')?['SetupComplete'],true),equals("+source+"?['Status'],'Accepted'),equals("+source+"?['OperationComplete'],true),equals("+source+"?['RequestType'],'Personal'),equals("+source+"?['Id'],variables('Group')?['SourceRequestId']))",'GROUP_NOT_OPERATIONAL')
        b.add(prefix+'_Own_member',d.query("@variables('Members')","and(equals(item()?['GroupId'],variables('TargetGroup')),equals(item()?['ParticipantId'],variables('Actor')),equals(item()?['MembershipStatus'],'Active'))"))
        b.gate(prefix+'_Authority',"equals(length(body('"+prefix+"_Own_member')),1)",'NOT_CURRENT_GROUP_MEMBER')
        m=Block();m.add(prefix+'_Member_shape',d.parse('@item()',{'type':'object','required':['Id','GroupId','ParticipantId','MembershipKey','MembershipStatus'],'properties':{'ParticipantId':{'type':'integer','minimum':1},'MembershipKey':{'type':'string','pattern':'^request:[1-9][0-9]*:participant:[1-9][0-9]*$'}}}))
        m.add(prefix+'_Member_request',self.http(self.uri('requests',"int(first(skip(split(item()?['MembershipKey'],':'),1)))")))
        q="body('"+prefix+"_Member_request')?['d']"
        m.gate(prefix+'_Member_committed',"or("+"and(equals(item()?['MembershipKey'],concat('request:',string("+q+"?['Id']),':participant:',string(item()?['ParticipantId']))),equals("+q+"?['Status'],'Accepted'),equals("+q+"?['OperationComplete'],true),or(and(equals("+q+"?['RequestType'],'Personal'),equals("+q+"?['Id'],variables('Group')?['SourceRequestId']),or(equals("+q+"?['SenderParticipantId'],item()?['ParticipantId']),equals("+q+"?['RecipientParticipantId'],item()?['ParticipantId']))),and(equals("+q+"?['RequestType'],'Group'),equals("+q+"?['TargetGroupId'],variables('TargetGroup')),equals("+q+"?['SenderParticipantId'],item()?['ParticipantId']))))"+",and(equals(item()?['MembershipKey'],variables('EpisodeKey')),equals(item()?['ParticipantId'],variables('Requester')),equals(variables('Request')?['Status'],'Accepted'),equals(variables('Request')?['WinningOperationKey'],outputs('Operation_key')),equals(variables('Receipt')?['DomainEffects'],true)))",'UNCOMMITTED_OR_FOREIGN_MEMBER')
        members="@body('"+prefix+"_Own_member')" if prefix=='Initial' else "@if(equals(body('Input')?['text'],'Decline'),body('"+prefix+"_Own_member'),variables('Members'))"
        b.add(prefix+'_Each_member',d.loop(members,m.actions))
    def episode(self,b,prefix,always=False):
        self.collection(b,prefix,d.cat(self.base['members']+"/items?$filter=MembershipKey eq '","@variables('EpisodeKey')","'&$top=2"),1,always)
        b.set(prefix+'_Save','Episodes',"@body('"+prefix+"')?['d']?['results']")
    def release(self,b,prefix):
        self.getvar(b,prefix+'_Read','groups',"variables('TargetGroup')",'Group')
        yes=Block();yes.add(prefix+'_Write',self.http(self.uri('groups',"variables('TargetGroup')"),'POST',{'__metadata':{'type':"@body('Group_type')?['value']"},'WriteOwner':''},"@variables('Group')?['__metadata']?['etag']"))
        self.getvar(yes,prefix+'_Readback','groups',"variables('TargetGroup')",'Group',True)
        yes.gate(prefix+'_Gone',"not(equals(variables('Group')?['WriteOwner'],variables('ReleaseToken')))",'COMMITTED_RELEASE_PENDING')
        b.add(prefix+'_If_owned',d.condition("equals(variables('Group')?['WriteOwner'],variables('ReleaseToken'))",yes.actions));b.set(prefix+'_Released','Released',True)


def eligibility(g,mapping):
    b=Block();g.episode(b,'Existing_episode')
    b.add('Already_active_requester',d.query("@variables('Members')","equals(item()?['ParticipantId'],variables('Requester'))"))
    own="and(equals(variables('Request')?['Status'],'Accepted'),equals(variables('Request')?['WinningOperationKey'],outputs('Operation_key')),equals(variables('Receipt')?['DomainEffects'],true))"
    ep="first(union(variables('Episodes'),createArray(json('{}'))))"
    b.gate('No_episode_reactivation',"or(empty(variables('Episodes')),and("+own+",equals(length(variables('Episodes')),1),equals("+ep+"?['GroupId'],variables('TargetGroup')),equals("+ep+"?['ParticipantId'],variables('Requester')),equals("+ep+"?['MembershipStatus'],'Active')))",'EPISODE_EXISTS_NEVER_REACTIVATE')
    b.gate('Requester_not_member',"or(empty(body('Already_active_requester')),and("+own+",equals(length(body('Already_active_requester')),1),equals(first(union(body('Already_active_requester'),createArray(json('{}'))))?['MembershipKey'],variables('EpisodeKey'))))",'ALREADY_MEMBER')
    b.gate('Open_with_physical_slot',"and(equals(variables('Group')?['State'],'Open'),equals(variables('Group')?['SetupComplete'],true),less(sub(length(variables('Members')),length(body('Already_active_requester'))),variables('Group')?['Capacity']),lessOrEquals(variables('Group')?['Capacity'],if(equals(variables('Group')?['ExchangeType'],'Language'),3,10)),greaterOrEquals(variables('Group')?['Capacity'],2))",'GROUP_FULL_OR_UNAVAILABLE')
    for role in ['language','culture','timezone']:
        uri="_api/web/lists(guid'"+mapping['lists'][role]['listId']+"')/items?$select=Id,Active"+(',ISOcode' if role=='language' else '')+'&$top=5001'
        g.collection(b,'Catalogue_'+role,uri,5000)
        b.add('Active_'+role,d.query("@body('Catalogue_"+role+"')?['d']?['results']","equals(item()?['Active'],true)"));b.add('IDs_'+role,d.select("@body('Active_"+role+"')","@item()?['Id']"))
    b.add('Any_language',d.query("@body('Active_language')","equals(toLower(item()?['ISOcode']),'any')"));b.gate('Any_unique',"lessOrEquals(length(body('Any_language')),1)",'CATALOGUE_AMBIGUOUS')
    b.compose('Catalogues',{'languageIds':"@body('IDs_language')",'cultureIds':"@body('IDs_culture')",'timezoneIds':"@body('IDs_timezone')",'anyLanguageId':"@first(union(body('Any_language'),createArray(json('{}'))))?['Id']"})
    b.add('Existing_context_members',d.query("@variables('Members')","not(equals(item()?['ParticipantId'],variables('Requester')))"))
    b.add('Member_ids',d.select("@body('Existing_context_members')","@item()?['ParticipantId']"));b.compose('Context_ids',"@union(body('Member_ids'),createArray(variables('Requester')))")
    p=Block();read=deepcopy(g.template);read['inputs']['parameters']['id']='@item()';p.add('Read_context_profile',read)
    raw={'profileId':"@body('Read_context_profile')?['ID']",'accountKey':"@body('Read_context_profile')?['Participantaccount']?['Claims']",'status':"@body('Read_context_profile')?['Status']?['Value']",'participationStatus':"@body('Read_context_profile')?['ParticipationStatus']?['Value']",'openToConnections':"@body('Read_context_profile')?['OpenToConnections']",'timezoneId':"@body('Read_context_profile')?['Timezone']?['Id']"}
    for k,v in [('teachIds','Teachlanguages'),('learnIds','Learnlanguages'),('shareCultureIds','ShareCultures'),('learnCultureIds','LearnCultures')]:raw[k]="@body('Read_context_profile')?['"+v+"#Id']"
    p.add('Append_context',d.append('RawProfiles',raw));b.add('Each_context_profile',d.loop("@outputs('Context_ids')",p.actions))
    g.shared(b,'Normalize','NORMALIZE',"@variables('RawProfiles')")
    b.add('Normalized_members',d.query("@body('Normalize_Result')?['result']?['profiles']","contains(body('Member_ids'),item()?['profileId'])"))
    b.gate('Focus_work_bound',"lessOrEquals(add(length(variables('Group')?['LanguageFocusId']?['results']),length(variables('Group')?['CultureFocusId']?['results'])),100)",'FOCUS_WORK_BOUND')
    for kind,field,share in [('language','LanguageFocusId','teachIds'),('culture','CultureFocusId','shareCultureIds')]:
        f=Block();f.add('Find_'+kind+'_sharer',d.query("@body('Normalized_members')","and(equals(item()?['status'],'Active'),equals(item()?['participationStatus'],'Active'),equals(item()?['openToConnections'],true),contains(item()?['"+share+"'],items('Each_"+kind+"_focus')))"));f.add('Record_'+kind+'_sharer',d.append('FocusChecks',"@not(empty(body('Find_"+kind+"_sharer')))"));b.add('Each_'+kind+'_focus',d.loop("@variables('Group')?['"+field+"']?['results']",f.actions))
    b.add('Unavailable_focus',d.query("@variables('FocusChecks')","equals(item(),false)"))
    adapter={'groupId':"@variables('TargetGroup')",'exchangeType':"@variables('Group')?['ExchangeType']",'state':"@variables('Group')?['State']",'capacity':"@variables('Group')?['Capacity']",'setupComplete':"@variables('Group')?['SetupComplete']",'languageFocusIds':"@variables('Group')?['LanguageFocusId']?['results']",'cultureFocusIds':"@variables('Group')?['CultureFocusId']?['results']",'memberProfileIds':"@body('Member_ids')",'focusSharersAvailable':"@empty(body('Unavailable_focus'))"}
    g.shared(b,'Group_fit','GROUP',"@body('Normalize_Result')?['result']?['profiles']",candidateId="@variables('Requester')",group=adapter)
    b.gate('Requester_fits',"equals(body('Group_fit_Result')?['result']?['compatible'],true)",'REQUESTER_UNAVAILABLE_OR_INCOMPATIBLE')
    # Profiles change independently of the group guard. Re-read the relevant raw
    # context after shared evaluation; a changed snapshot requires a fresh retry.
    fresh=Block();read=deepcopy(g.template);read['inputs']['parameters']['id']='@item()';fresh.add('Read_fresh_context_profile',read)
    fresh.add('Recorded_context_profile',d.query("@variables('RawProfiles')","equals(item()?['profileId'],items('Each_fresh_context'))"))
    fresh.compose('Fresh_context_profile',json.loads(json.dumps(raw).replace('Read_context_profile','Read_fresh_context_profile')))
    fresh.gate('Relevant_profile_unchanged',"and(equals(length(body('Recorded_context_profile')),1),equals(outputs('Fresh_context_profile'),first(union(body('Recorded_context_profile'),createArray(json('{}'))))))",'RELEVANT_PROFILE_CHANGED')
    b.add('Each_fresh_context',d.loop("@outputs('Context_ids')",fresh.actions))
    return b.actions


def commit_join(g):
    b=Block();g.stage(b,'Member_stage','MEMBERSHIP_PLANNED')
    create=Block();create.add('Create_episode',g.http(g.base['members']+'/items','POST',{'__metadata':{'type':"@body('Member_type')?['value']"},'GroupId':"@variables('TargetGroup')",'ParticipantId':"@variables('Requester')",'MembershipStatus':'Active','MembershipKey':"@variables('EpisodeKey')",'JoinedAt':'@utcNow()'}))
    b.add('Create_only_missing',d.condition("empty(variables('Episodes'))",create.actions))
    g.episode(b,'Episode_readback',True)
    rejected=Block();rejected.set('Member_rejected_Boundary','DefiniteBoundary','MEMBERSHIP_REJECTED');rejected.gate('Member_definite_error','equals(1,0)','MEMBERSHIP_RETRY_REQUIRED')
    b.add('Member_definite_rejection',d.condition("and(empty(variables('Episodes')),equals(outputs('Create_episode')?['statusCode'],403))",rejected.actions))
    ep="first(union(variables('Episodes'),createArray(json('{}'))))"
    b.gate('Episode_exact',"and(equals(length(variables('Episodes')),1),equals("+ep+"?['GroupId'],variables('TargetGroup')),equals("+ep+"?['ParticipantId'],variables('Requester')),equals("+ep+"?['MembershipStatus'],'Active'),equals("+ep+"?['MembershipKey'],variables('EpisodeKey')))",'MEMBERSHIP_OUTCOME_UNKNOWN')
    g.patch_receipt(b,'Member_confirm',{'Uncertain':False,'DomainEffects':True,'Stage':'MEMBERSHIP_SAVED'})
    g.getvar(b,'Final_group','groups',"variables('TargetGroup')",'Group')
    g.collection(b,'Final_members',d.cat(g.base['members']+'/items?$filter=GroupId eq ',"@string(variables('TargetGroup'))"," and MembershipStatus eq 'Active'&$top=12"),11)
    b.add('Final_requester_rows',d.query("@body('Final_members')?['d']?['results']","equals(item()?['ParticipantId'],variables('Requester'))"))
    b.gate('Final_count_capacity',"and(equals(variables('Group')?['WriteOwner'],outputs('Owner_token')),equals(variables('Group')?['State'],'Open'),equals(variables('Group')?['SetupComplete'],true),lessOrEquals(length(body('Final_members')?['d']?['results']),variables('Group')?['Capacity']),equals(length(body('Final_requester_rows')),1))",'FINAL_CAPACITY_OR_OWNERSHIP_FAILED')
    g.stage(b,'Commit_stage','REQUEST_COMMIT_PLANNED');g.getvar(b,'Before_commit','requests',"body('Input')?['number']",'Request')
    winning="and(equals(variables('Request')?['Status'],'Accepted'),equals(variables('Request')?['WinningOperationKey'],outputs('Operation_key')),equals(variables('Request')?['TargetGroupId'],variables('TargetGroup')),equals(variables('Request')?['SenderParticipantId'],variables('Requester')))"
    b.gate('Winning_accept',winning,'WINNING_ACCEPT_REQUIRED')
    b.add('Commit_request',g.http(g.uri('requests',"body('Input')?['number']"),'POST',{'__metadata':{'type':"@body('Request_type')?['value']"},'OperationComplete':True,'ConnectionKey':"@concat('history:request:',string(body('Input')?['number']))"},"@variables('Request')?['__metadata']?['etag']"))
    g.getvar(b,'Commit_readback','requests',"body('Input')?['number']",'Request',True)
    commit_rejected=Block();commit_rejected.set('Commit_rejected_Boundary','DefiniteBoundary','COMMIT_REJECTED');commit_rejected.gate('Commit_definite_error','equals(1,0)','COMMIT_RETRY_REQUIRED')
    b.add('Commit_definite_rejection',d.condition("and(equals(outputs('Commit_request')?['statusCode'],403),equals(variables('Request')?['Status'],'Accepted'),equals(variables('Request')?['WinningOperationKey'],outputs('Operation_key')),equals(variables('Request')?['OperationComplete'],false))",commit_rejected.actions))
    b.gate('Committed_exact',"and("+winning+",equals(variables('Request')?['OperationComplete'],true),equals(variables('Request')?['ConnectionKey'],concat('history:request:',string(body('Input')?['number']))))",'COMMIT_OUTCOME_UNKNOWN')
    g.patch_receipt(b,'Commit_confirm',{'Uncertain':False,'DomainEffects':True,'Stage':'COMMITTED'});return b.actions


def business(g,mapping):
    b=Block();retry=Block()
    retry.gate('Retry_sealed',"and(equals(variables('Receipt')?['Retryable'],true),equals(variables('Receipt')?['Uncertain'],false),contains(json(variables('Receipt')?['SealedAttempts']),variables('Receipt')?['AttemptToken']),less(length(json(variables('Receipt')?['SealedAttempts'])),3))",'RECOVERY_REQUIRED')
    retry.set('Prior_sealed_token','ReleaseToken',"@concat(outputs('Operation_key'),'|',variables('Receipt')?['AttemptToken'])")
    g.release(retry,'Release_prior_sealed')
    retry.set('Reset_completed_release','Released',False)
    retry.add('Claim_retry',g.http(g.uri('receipts',"variables('Receipt')?['Id']"),'POST',{'__metadata':{'type':"@body('Receipt_type')?['value']"},'AttemptToken':"@variables('Attempt')",'Retryable':False},"@variables('Receipt')?['__metadata']?['etag']"));g.getvar(retry,'Retry_readback','receipts',"variables('Receipt')?['Id']",'Receipt',True)
    b.add('New_attempt_if_sealed',d.condition("not(equals(variables('Receipt')?['AttemptToken'],variables('Attempt')))",retry.actions))
    b.gate('Attempt_active',"and(equals(variables('Receipt')?['AttemptToken'],variables('Attempt')),equals(variables('Receipt')?['Complete'],false),equals(variables('Receipt')?['Uncertain'],false),not(contains(json(variables('Receipt')?['SealedAttempts']),variables('Attempt'))))",'RECOVERY_REQUIRED')
    g.getvar(b,'Before_claim','groups',"variables('TargetGroup')",'Group');b.gate('Group_free',"empty(variables('Group')?['WriteOwner'])",'GROUP_BUSY')
    g.stage(b,'Claim_stage','GROUP_CLAIM_PLANNED')
    b.add('Claim_group',g.http(g.uri('groups',"variables('TargetGroup')"),'POST',{'__metadata':{'type':"@body('Group_type')?['value']"},'WriteOwner':"@outputs('Owner_token')"},"@variables('Group')?['__metadata']?['etag']"));g.getvar(b,'Claim_readback','groups',"variables('TargetGroup')",'Group',True)
    claim_rejected=Block();claim_rejected.set('Claim_rejected_Boundary','DefiniteBoundary','CLAIM_REJECTED');claim_rejected.gate('Claim_race_busy','equals(1,0)','GROUP_BUSY')
    b.add('Claim_definite_rejection',d.condition("and(not(equals(variables('Group')?['WriteOwner'],outputs('Owner_token'))),equals(outputs('Claim_group')?['statusCode'],412))",claim_rejected.actions))
    b.gate('Claim_owned',"equals(variables('Group')?['WriteOwner'],outputs('Owner_token'))",'GROUP_CLAIM_UNCERTAIN')
    g.patch_receipt(b,'Claim_confirm',{'Stage':'GROUP_OWNED','Uncertain':False});g.current(b,'Locked')
    b.gate('Guard_still_owned',"equals(variables('Group')?['WriteOwner'],outputs('Owner_token'))",'GROUP_OWNERSHIP_LOST')
    b.gate('Pending_first_terminal',"or(and(equals(variables('Request')?['Status'],'Pending'),equals(variables('Request')?['OperationComplete'],false),empty(variables('Request')?['WinningOperationKey'])),and(equals(body('Input')?['text'],'Accept'),equals(variables('Request')?['Status'],'Accepted'),equals(variables('Request')?['OperationComplete'],false),equals(variables('Request')?['WinningOperationKey'],outputs('Operation_key')),equals(variables('Receipt')?['DomainEffects'],true)))",'ALREADY_DECIDED')
    b.add('Accept_eligibility',d.condition("equals(body('Input')?['text'],'Accept')",eligibility(g,mapping)))
    dec=Block()
    g.stage(dec,'Decision_stage','DECISION_PLANNED')
    desired="if(equals(body('Input')?['text'],'Accept'),'Accepted','Declined')"
    patch={'__metadata':{'type':"@body('Request_type')?['value']"},'Status':'@'+desired,'WinningOperationKey':"@outputs('Operation_key')",'OperationComplete':"@equals(body('Input')?['text'],'Decline')",'ConnectionKey':"@if(equals(body('Input')?['text'],'Decline'),concat('history:request:',string(body('Input')?['number'])),variables('Request')?['ConnectionKey'])"}
    dec.add('Decide_request',g.http(g.uri('requests',"body('Input')?['number']"),'POST',patch,"@variables('Request')?['__metadata']?['etag']"));g.getvar(dec,'Decision_readback','requests',"body('Input')?['number']",'Request',True)
    saved="and(equals(variables('Request')?['Status'],"+desired+"),equals(variables('Request')?['WinningOperationKey'],outputs('Operation_key')))"
    no=Block();no.gate('Decision_rejection_definite',"or(not(equals(variables('Request')?['Status'],'Pending')),equals(outputs('Decide_request')?['statusCode'],412))",'DECISION_OUTCOME_UNKNOWN');no.set('Decision_rejected_Boundary','DefiniteBoundary','DECISION_REJECTED');no.gate('Decision_conflict','equals(1,0)','DECISION_CONFLICT')
    dec.add('Decision_verified',d.condition(saved,{},no.actions));g.patch_receipt(dec,'Decision_confirm',{'Uncertain':False,'DomainEffects':True,'Stage':'DECIDED'})
    b.add('Decide_only_pending',d.condition("equals(variables('Request')?['Status'],'Pending')",dec.actions))
    b.add('Accept_membership',d.condition("equals(body('Input')?['text'],'Accept')",commit_join(g)))
    b.add('Result_member_ids',d.select("@variables('Episodes')","@item()?['Id']"))
    b.set('Public_result','Result',{'success':True,'code':"@if(equals(body('Input')?['text'],'Accept'),'ACCEPTED','DECLINED')",'requestId':"@body('Input')?['number']",'groupId':"@variables('TargetGroup')",'membershipIds':"@body('Result_member_ids')"})
    return b.actions


def reconcile_committed(g):
    """Positive committed-domain readback only; never repeat domain writes here.

    The old receipt attempt is retained, not stolen. Its exact group token must
    still be held. Receipt completion and matching-token release seal that writer.
    """
    b=Block();g.getvar(b,'Recovery_request','requests',"body('Input')?['number']",'Request')
    g.getvar(b,'Recovery_group','groups',"variables('TargetGroup')",'Group');g.episode(b,'Recovery_episode')
    g.collection(b,'Recovery_members',d.cat(g.base['members']+'/items?$filter=GroupId eq ',"@string(variables('TargetGroup'))"," and MembershipStatus eq 'Active'&$top=12"),11)
    b.add('Recovery_candidate_rows',d.query("@body('Recovery_members')?['d']?['results']","equals(item()?['ParticipantId'],variables('Requester'))"))
    ep="first(union(variables('Episodes'),createArray(json('{}'))))"
    decision="if(equals(body('Input')?['text'],'Accept'),'Accepted','Declined')"
    checks="and(equals(variables('Request')?['Status'],"+decision+"),equals(variables('Request')?['OperationComplete'],true),equals(variables('Request')?['WinningOperationKey'],outputs('Operation_key')),equals(variables('Request')?['TargetGroupId'],variables('TargetGroup')),equals(variables('Request')?['SenderParticipantId'],variables('Requester')),equals(variables('Request')?['ConnectionKey'],concat('history:request:',string(body('Input')?['number']))),equals(variables('Group')?['SetupComplete'],true),equals(variables('Group')?['WriteOwner'],concat(outputs('Operation_key'),'|',variables('Receipt')?['AttemptToken'])),lessOrEquals(length(body('Recovery_members')?['d']?['results']),variables('Group')?['Capacity']),or(and(equals(body('Input')?['text'],'Decline'),empty(variables('Episodes'))),and(equals(body('Input')?['text'],'Accept'),equals(length(variables('Episodes')),1),equals("+ep+"?['GroupId'],variables('TargetGroup')),equals("+ep+"?['ParticipantId'],variables('Requester')),equals("+ep+"?['MembershipStatus'],'Active'),equals("+ep+"?['MembershipKey'],variables('EpisodeKey')),equals(length(body('Recovery_candidate_rows')),1))))"
    b.gate('Recovery_complete_domain',checks,'RECOVERY_REQUIRED')
    b.add('Recovery_episode_ids',d.select("@variables('Episodes')","@item()?['Id']"))
    b.set('Recovery_result','Result',{'success':True,'code':"@if(equals(body('Input')?['text'],'Accept'),'ACCEPTED','DECLINED')",'requestId':"@body('Input')?['number']",'groupId':"@variables('TargetGroup')",'membershipIds':"@body('Recovery_episode_ids')"})
    b.set('Recovery_snapshot','RecoveryProof',{'etag':"@variables('Receipt')?['__metadata']?['etag']",'attempt':"@variables('Receipt')?['AttemptToken']"})
    return b.actions


def build_actions(original=None,mapping=None,groups=None,build_id='local-review'):
    original=original or source_document();mapping=mapping or json.loads((ROOT/'config/tenant_schema_mapping.json').read_text());groups=groups or json.loads((ROOT/'config/group_schema_mapping.json').read_text())
    g=Builder(original,mapping,groups,build_id);root=Block()
    initial=[('Code','string',''),('Actor','integer',0),('Requester','integer',0),('TargetGroup','integer',0),('Attempt','string',"@workflow()?['run']?['name']"),('Receipt','object',{}),('Request','object',{}),('Group','object',{}),('Members','array',[]),('Episodes','array',[]),('RawProfiles','array',[]),('FocusChecks','array',[]),('ReleaseToken','string',''),('Released','boolean',False),('Result','object',{}),('EpisodeKey','string',''),('IntentBound','boolean',False),('DefiniteBoundary','string',''),('RecoveryProof','object',{})]
    for name,kind,value in initial:root.add('Init_'+name,{'type':'InitializeVariable','inputs':{'variables':[{'name':name,'type':kind,'value':value}]}})
    b=Block();b.add('Input',d.parse('@triggerBody()',{'type':'object','required':['number','text','text_1'],'properties':{'number':{'type':'integer','minimum':1},'text':{'type':'string','enum':['Accept','Decline']},'text_1':{'type':'string','pattern':UUID_PATTERN}}}))
    b.add('Current_user',g.http('_api/web/currentuser?$select=Id'))
    g.collection(b,'Own_profile',d.cat(g.base['participants']+'/items?$select=Id&$filter=ParticipantaccountId eq ',"@string(body('Current_user')?['d']?['Id'])",'&$top=2'),1)
    b.gate('Own_profile_one',"equals(length(body('Own_profile')?['d']?['results']),1)",'CALLER_PROFILE_UNVERIFIED');b.set('Actor_id','Actor',"@first(body('Own_profile')?['d']?['results'])?['Id']")
    # The later Initial_Request reread must not differ only by case. Native
    # template name resolution can collapse those dependencies into a cycle.
    g.getvar(b,'Bootstrap_request','requests',"body('Input')?['number']",'Request')
    b.add('Request_shape',d.parse("@variables('Request')",{'type':'object','required':['Id','SenderParticipantId','TargetGroupId','RequestType','Status','OperationComplete','ConnectionKey'],'properties':{'SenderParticipantId':{'type':'integer','minimum':1},'TargetGroupId':{'type':'integer','minimum':1},'RequestType':{'type':'string','enum':['Group']},'OperationComplete':{'type':'boolean'}}}))
    b.set('Target_id','TargetGroup',"@variables('Request')?['TargetGroupId']");b.set('Requester_id','Requester',"@variables('Request')?['SenderParticipantId']")
    b.compose('Canonical_intent',{'version':1,'kind':'respond-group-join','actorId':"@variables('Actor')",'requestId':"@body('Input')?['number']",'decision':"@body('Input')?['text']",'groupId':"@variables('TargetGroup')",'requesterId':"@variables('Requester')"})
    b.compose('Operation_key',"@concat('respond-group-join:',string(variables('Actor')),':',toLower(body('Input')?['text_1']))");b.compose('Owner_token',"@concat(outputs('Operation_key'),'|',variables('Attempt'))");b.gate('Token_bound',"lessOrEquals(length(outputs('Owner_token')),255)",'TOKEN_BOUND')
    b.compose('Episode_key',"@concat('request:',string(body('Input')?['number']),':participant:',string(variables('Requester')))");b.set('Save_episode_key','EpisodeKey',"@outputs('Episode_key')")
    # Entity names support verbose native writes; no per-click field/schema audit.
    for role,prefix in [('receipts','Receipt'),('groups','Group'),('requests','Request'),('members','Member')]:
        b.add(prefix+'_list',g.http(g.base[role]+'?$select=ListItemEntityTypeFullName'))
        if b.code!='SCHEMA_SETUP_UNVERIFIED':b.set(prefix+'_type_known_Code','Code','SCHEMA_SETUP_UNVERIFIED')
        b.add(prefix+'_type',d.parse({'value':"@body('"+prefix+"_list')?['d']?['ListItemEntityTypeFullName']"},
            {'type':'object','required':['value'],'properties':{'value':{'type':'string','minLength':1}}}))
    g.current(b,'Initial')
    receipt_uri=d.cat(RECEIPTS+"/items?$filter=OperationKey eq '","@outputs('Operation_key')","'&$top=2")
    g.collection(b,'Find_receipt',receipt_uri,1)
    create=Block();create.add('Create_receipt',g.http(RECEIPTS+'/items','POST',{'__metadata':{'type':"@body('Receipt_type')?['value']"},'OperationKey':"@outputs('Operation_key')",'IntentJson':"@string(outputs('Canonical_intent'))",'Complete':False,'Uncertain':False,'Retryable':False,'DomainEffects':False,'AttemptToken':"@variables('Attempt')",'SealedAttempts':'[]','Stage':'START'}))
    b.add('Create_if_absent',d.condition("empty(body('Find_receipt')?['d']?['results'])",create.actions));g.collection(b,'Resolve_receipt',receipt_uri,1,True)
    b.gate('Receipt_one',"equals(length(body('Resolve_receipt')?['d']?['results']),1)",'RECEIPT_CREATE_UNCERTAIN');b.set('Save_receipt','Receipt',"@first(body('Resolve_receipt')?['d']?['results'])")
    b.gate('Immutable_intent',"and(equals(variables('Receipt')?['OperationKey'],outputs('Operation_key')),equals(json(variables('Receipt')?['IntentJson']),outputs('Canonical_intent')))",'INTENT_MISMATCH')
    b.set('Intent_is_bound','IntentBound',True)
    b.add('Receipt_shape',d.parse("@variables('Receipt')",{'type':'object','required':['Complete','Uncertain','Retryable','DomainEffects','AttemptToken','SealedAttempts','Stage'],'properties':{k:{'type':'boolean'} for k in ['Complete','Uncertain','Retryable','DomainEffects']}}))
    b.add('Run_if_incomplete',d.condition("equals(variables('Receipt')?['Complete'],false)",business(g,mapping)));root.add('Business',{'type':'Scope','actions':b.actions})
    finish=Block();finish.gate('Have_bound_receipt',"and(greater(coalesce(variables('Receipt')?['Id'],0),0),equals(variables('IntentBound'),true))",'NO_BOUND_RECEIPT')
    finish.compose('Finalize_error',"@variables('Code')")
    g.getvar(finish,'Final_receipt','receipts',"variables('Receipt')?['Id']",'Receipt')
    boundary=Block();g.patch_receipt(boundary,'Confirm_definite_boundary',{'Uncertain':False,'Stage':"@variables('DefiniteBoundary')"})
    finish.add('Definite_boundary_if_needed',d.condition("and(equals(variables('Receipt')?['Complete'],false),not(empty(variables('DefiniteBoundary'))))",boundary.actions))
    ready="not(equals(variables('Result')?['success'],null))"
    finish.add('Reconcile_if_needed',d.condition("and(equals(variables('Receipt')?['Complete'],false),not("+ready+"),or(equals(variables('Receipt')?['Uncertain'],true),equals(variables('Receipt')?['Stage'],'COMMITTED')))",reconcile_committed(g)))
    safe=Block();safe.gate('Safe_attempt',"and(equals(variables('Receipt')?['Uncertain'],false),equals(variables('Receipt')?['AttemptToken'],variables('Attempt')),not(contains(json(variables('Receipt')?['SealedAttempts']),variables('Attempt'))),less(length(json(variables('Receipt')?['SealedAttempts'])),3))",'RECOVERY_REQUIRED')
    g.patch_receipt(safe,'Seal_stopped',{'Retryable':True,'Stage':'SEALED_STOPPED','SealedAttempts':"@string(union(json(variables('Receipt')?['SealedAttempts']),createArray(variables('Attempt'))))"})
    reject=Block();reject.set('Rejected_result','Result',{'success':False,'code':"@outputs('Finalize_error')",'requestId':"@body('Input')?['number']",'groupId':"@variables('TargetGroup')",'membershipIds':[]})
    stopped=Block();stopped.add('Reject_or_seal',d.condition("and(equals(variables('Receipt')?['DomainEffects'],false),equals(variables('Receipt')?['Uncertain'],false),equals(variables('Receipt')?['AttemptToken'],variables('Attempt')),contains(createArray('GROUP_FULL_OR_UNAVAILABLE','REQUESTER_UNAVAILABLE_OR_INCOMPATIBLE','ALREADY_DECIDED','DECISION_CONFLICT','ALREADY_MEMBER','EPISODE_EXISTS_NEVER_REACTIVATE','GROUP_NOT_OPERATIONAL','UNCOMMITTED_OR_FOREIGN_MEMBER'),outputs('Finalize_error')))",reject.actions,safe.actions))
    finish.add('Seal_if_incomplete',d.condition("and(equals(variables('Receipt')?['Complete'],false),not("+ready+"))",stopped.actions))
    # No intervening remote I/O follows Final_receipt / the last confirmed
    # boundary/recovery/stop snapshot. The single completion CAS binds that exact
    # tag, including the original captured tag/attempt for recovery.
    complete=Block()
    active="and(equals(variables('Receipt')?['AttemptToken'],variables('Attempt')),not(contains(json(coalesce(variables('Receipt')?['SealedAttempts'],'[]')),variables('Attempt'))))"
    recovery="and(equals(variables('Receipt')?['__metadata']?['etag'],variables('RecoveryProof')?['etag']),equals(variables('Receipt')?['AttemptToken'],variables('RecoveryProof')?['attempt']),equals(variables('Group')?['WriteOwner'],concat(outputs('Operation_key'),'|',variables('RecoveryProof')?['attempt'])))"
    complete.gate('Complete_receipt_Authority',"and(equals(variables('Receipt')?['Complete'],false),not(empty(variables('Receipt')?['__metadata']?['etag'])),not(equals(variables('Receipt')?['__metadata']?['etag'],'*')),or(and(equals(variables('RecoveryProof')?['etag'],null),"+active+"),and(not(equals(variables('RecoveryProof')?['etag'],null)),"+recovery+")))",'ATTEMPT_NOT_ACTIVE')
    complete.add('Complete_receipt_Write',g.http(g.uri('receipts',"variables('Receipt')?['Id']"),'POST',{'__metadata':{'type':"@body('Receipt_type')?['value']"},'Complete':True,'ResultJson':"@string(variables('Result'))",'Uncertain':False,'Retryable':False,'Stage':'COMPLETE','DomainEffects':"@if(equals(variables('RecoveryProof')?['etag'],null),variables('Receipt')?['DomainEffects'],true)"},"@variables('Receipt')?['__metadata']?['etag']"))
    g.getvar(complete,'Complete_receipt_Confirm','receipts',"variables('Receipt')?['Id']",'Receipt',True)
    complete.gate('Complete_receipt_Persisted',"and(equals(variables('Receipt')?['Complete'],true),equals(variables('Receipt')?['ResultJson'],string(variables('Result'))),equals(variables('Receipt')?['Uncertain'],false),equals(variables('Receipt')?['Retryable'],false),equals(variables('Receipt')?['Stage'],'COMPLETE'))",'RECEIPT_WRITE_UNCERTAIN')
    finish.add('Complete_if_ready',d.condition("and(equals(variables('Receipt')?['Complete'],false),"+ready+")",complete.actions))
    completion_readback=Block();g.getvar(completion_readback,'Completion_retry_readback','receipts',"coalesce(variables('Receipt')?['Id'],body('Final_receipt')?['d']?['Id'])",'Receipt')
    finish.add('Completion_readback_if_needed',d.condition("and("+ready+",not(equals(actions('Complete_receipt_Persisted')?['status'],'Succeeded')))",completion_readback.actions),True)
    done=Block();done.add('Saved_result',d.parse("@json(variables('Receipt')?['ResultJson'])",{'type':'object','additionalProperties':False,'required':['success','code','requestId','groupId','membershipIds'],'properties':{'success':{'type':'boolean'},'code':{'type':'string'},'requestId':{'type':'integer','minimum':1},'groupId':{'type':'integer','minimum':1},'membershipIds':{'type':'array','items':{'type':'integer','minimum':1}}}}))
    done.gate('Saved_result_binding',"and(equals(body('Saved_result')?['requestId'],body('Input')?['number']),equals(body('Saved_result')?['groupId'],variables('TargetGroup')),or(equals(body('Saved_result')?['success'],false),equals(body('Saved_result')?['code'],if(equals(body('Input')?['text'],'Accept'),'ACCEPTED','DECLINED'))))",'RESULT_BINDING_MISMATCH')
    done.set('Replay_result','Result',"@body('Saved_result')")
    finish.add('Complete_replay',d.condition("equals(variables('Receipt')?['Complete'],true)",done.actions))
    release=Block();release.set('Completed_token','ReleaseToken',"@concat(outputs('Operation_key'),'|',variables('Receipt')?['AttemptToken'])");g.release(release,'Release_completed')
    sealed="and(equals(variables('Receipt')?['Retryable'],true),equals(variables('Receipt')?['Uncertain'],false),equals(variables('Receipt')?['AttemptToken'],variables('Attempt')),contains(json(coalesce(variables('Receipt')?['SealedAttempts'],'[]')),variables('Attempt')))"
    finish.add('Release_final_if_settled',d.condition("or(equals(variables('Receipt')?['Complete'],true),"+sealed+")",release.actions))
    root.add('Finalize',{'type':'Scope','actions':finish.actions},True)
    success="and(equals(variables('Receipt')?['Complete'],true),equals(variables('Released'),true),equals(variables('Result')?['success'],true))"
    root.compose('Group_response_report',{'kind':NAME,'sourceTicket':65,'packageBuildId':build_id,'contractVersion':1,'rulesVersion':1,'success':'@'+success,
      'code':"@if(equals(variables('Code'),'INTENT_MISMATCH'),'INTENT_MISMATCH',if(and(equals(variables('Receipt')?['Complete'],true),equals(variables('Released'),true)),variables('Result')?['code'],if(equals(variables('Receipt')?['Complete'],true),'COMMITTED_RELEASE_PENDING',if(equals(variables('Receipt')?['Uncertain'],true),'RECOVERY_REQUIRED',if(equals(variables('Receipt')?['Retryable'],true),outputs('Finalize_error'),if(empty(variables('Code')),'INVALID_INPUT_OR_READ_FAILED',variables('Code')))))))",
      'stage':"@variables('Receipt')?['Stage']",'retryable':"@and(equals(variables('IntentBound'),true),equals(variables('Receipt')?['Retryable'],true),equals(variables('Receipt')?['Uncertain'],false),less(length(json(coalesce(variables('Receipt')?['SealedAttempts'],'[]'))),3))",'runReference':"@workflow()?['run']?['name']",'ordinaryUserAccessVerified':False,'nativeEvidence':'NOT_RUN'})
    root.actions['Group_response_report']['runAfter']={'Finalize':ALL}
    outputs={'success':"@outputs('Group_response_report')?['success']",'resultcode':"@outputs('Group_response_report')?['code']",'resultjson':"@if(and(equals(variables('Receipt')?['Complete'],true),equals(variables('Released'),true)),string(variables('Result')),'{}')",'runreference':"@workflow()?['run']?['name']",'retryable':"@outputs('Group_response_report')?['retryable']",'errormessage':"@if(outputs('Group_response_report')?['success'],'','The response could not complete. Keep the same intent ID for a retry or return the run reference for recovery.')"}
    root.add('Respond_to_a_Power_App_or_flow',{'type':'Response','kind':'PowerApp','inputs':{'statusCode':200,'body':outputs,'schema':{'type':'object','properties':{k:{'type':'boolean' if k in ['success','retryable'] else 'string','title':k} for k in outputs}}}})
    measure(root.actions);return root.actions


def build_parent(original=None,mapping=None,groups=None,build_id='local-review'):
    original=original or source_document();actions=build_actions(original,mapping,groups,build_id)
    refs=deepcopy(original['properties']['connectionReferences']);refs['shared_sharepointonline']['connectionName']='IMPORT_SELECT_EXISTING_SHAREPOINT_CONNECTION'
    definition={k:deepcopy(v) for k,v in original['properties']['definition'].items() if k in ['$schema','parameters']};definition.update(contentVersion='1.0.0.0',triggers=trigger(),actions=actions)
    return {'properties':{'displayName':NAME,'definition':definition,'connectionReferences':refs}}


def build_package(output,original=None):
    output=Path(output)
    if output.exists() or output.with_suffix('.review.json').exists():raise FileExistsError(output)
    build_id=str(uuid4());parent=build_parent(original,build_id=build_id);output.parent.mkdir(parents=True,exist_ok=True);output.write_bytes((json.dumps(parent,indent=2)+'\n').encode())
    review={'sourceTicket':65,'packageBuildId':build_id,**measure(parent['properties']['definition']['actions']),'definitionSha256':hashlib.sha256(output.read_bytes()).hexdigest(),'generatorSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'childWorkflowReferenceName':CHILD,'contractVersion':1,'rulesVersion':1,'deployment':'PARENT_COMPONENT_FOR_FINAL_SOLUTION_ASSEMBLY','tenantResult':'NOT_RUN','ordinaryUserAccessVerified':False,'dependency':'Exact #81 batch receipt schema and existing request/group/member mappings and Invoker; not tenant-verified','legacyZip':'NOT_APPLICABLE: linked Workflow calls require final Solution assembly'}
    output.with_suffix('.review.json').write_bytes((json.dumps(review,indent=2)+'\n').encode());return review


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();print(json.dumps(build_package(a.output),indent=2))
