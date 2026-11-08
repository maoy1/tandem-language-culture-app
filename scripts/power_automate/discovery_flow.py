"""#7 generated owner-preview Discovery; no Python runtime dependency."""
from copy import deepcopy
import argparse,hashlib,json
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4
from zipfile import ZipFile,ZIP_DEFLATED
from . import compatibility as rules
from .build_import_probe import build_package as envelope
from .schema_audit import measure,wdl_string,ALL

ROOT=Path(__file__).resolve().parents[2]
NAME='TandemDiscovery v2'
BOUNDS={'profiles':500,'peopleResults':50,'groups':100,'groupWorkUnits':100,'memberships':2000,'requests':500,'catalogue':5000,'responseChars':250000}


def after(n):return {n:['Succeeded']} if n else {}
def compose(v,n=None):return {'type':'Compose','inputs':v,'runAfter':after(n)}
def select(source,projection,n=None):return {'type':'Select','inputs':{'from':source,'select':projection},'runAfter':after(n)}
def query(source,predicate,n=None):return {'type':'Query','inputs':{'from':source,'where':'@'+predicate},'runAfter':after(n)}
def condition(test,yes,no=None,n=None):return {'type':'If','expression':'@'+test,'actions':yes,'else':{'actions':no or {}},'runAfter':after(n)}
def setvar(name,value,n=None):return {'type':'SetVariable','inputs':{'name':name,'value':value},'runAfter':after(n)}
def append(name,value,n=None):return {'type':'AppendToArrayVariable','inputs':{'name':name,'value':value},'runAfter':after(n)}
def parse(source,schema,n=None):return {'type':'ParseJson','inputs':{'content':source,'schema':schema},'runAfter':after(n)}
def loop(source,actions,n=None):return {'type':'Foreach','foreach':source,'actions':actions,'runtimeConfiguration':{'concurrency':{'repetitions':1}},'runAfter':after(n)}
def body(n):return "body('"+n+"')"
def out(n):return "outputs('"+n+"')"
def arr(n):return body(n)+"?['d']?['results']"
def ids(n):return "body('"+n+"')"
def cat(*parts):return '@concat('+','.join(p[1:] if p.startswith('@') else wdl_string(p) for p in parts)+')'
def complete(n,bound,verbose=True):
    source=body(n)+("?['d']" if verbose else '')
    rows=source+("?['results']" if verbose else "?['value']")
    next_=source+"?['__next']" if verbose else "coalesce("+source+"?['@odata.nextLink'],"+source+"?['odata.nextLink'])"
    return 'and(not(equals('+rows+",null)),lessOrEquals(length(coalesce("+rows+",json('[]'))),"+str(bound)+'),empty('+next_+'))'


def public_profile_schema():
    labels={'type':'array','items':{'type':'object','additionalProperties':False,'required':['id','label'],
      'properties':{'id':{'type':'integer','minimum':1},'label':{'type':'string'}}}}
    props={'profileId':{'type':'integer','minimum':1},'displayName':{'type':'string','minLength':1},
      **{key:deepcopy(labels) for key in ['teachLanguages','learnLanguages','shareCultures','learnCultures']},
      'timeZone':{'type':'object','additionalProperties':False,'required':['id','label','ianaId'],'properties':{
        'id':{'type':['integer','null'],'minimum':1},'label':{'type':['string','null']},'ianaId':{'type':['string','null']}}},
      'learningFocus':{'type':'string'},'comments':{'type':'string'}}
    return {'type':'object','additionalProperties':False,'required':list(props),'properties':props}


def display_actions(prefix,profile,raw,n=None):
    """Explicit #46 allowlist only; never serialize raw account/profile objects."""
    a={};previous=n
    for field,role in [('teachLanguages','teachIds'),('learnLanguages','learnIds'),('shareCultures','shareCultureIds'),('learnCultures','learnCultureIds')]:
        catalogue='Active_language' if field in ['teachLanguages','learnLanguages'] else 'Active_culture'
        q=prefix+'_'+field+'_rows';s=prefix+'_'+field
        a[q]=query('@'+body(catalogue),'contains('+profile+"?['"+role+"'],item()?['Id'])",previous)
        a[s]=select('@'+body(q),{'id':"@item()?['Id']",'label':"@item()?['Title']"},q);previous=s
    q=prefix+'_zone_rows';a[q]=query('@'+body('Active_timezone'),"equals(item()?['Id'],"+profile+"?['timezoneId'])",previous)
    # first() always receives at least the fallback object, including eager evaluators.
    zone="first(union(body('"+q+"'),createArray(json('{}'))))"
    a[prefix+'_display']=compose({'profileId':'@'+profile+"?['profileId']",'displayName':'@'+raw+"?['Participantaccount']?['DisplayName']",
      **{f:'@'+body(prefix+'_'+f) for f in ['teachLanguages','learnLanguages','shareCultures','learnCultures']},
      'timeZone':{'id':'@'+zone+"?['Id']",'label':'@'+zone+"?['Title']",'ianaId':'@'+zone+"?['IANA_ID']"},
      'learningFocus':'@coalesce('+raw+"?['Learningfocus'],'')",'comments':'@coalesce('+raw+"?['Comments'],'')"},q)
    a[prefix+'_public']=parse('@'+out(prefix+'_display'),public_profile_schema(),prefix+'_display')
    return a


def build_actions(original,mapping,groups,build_id):
    old=original['properties'];ref=old['connectionReferences']['shared_sharepointonline']
    if ref.get('source')!='Invoker':raise ValueError('Source must preserve Invoker connection; no owner fallback')
    trigger=old['definition']['triggers']['manual']
    if trigger['kind']!='PowerAppV2' or set(trigger['inputs']['schema']['properties'])!={'number'}:raise ValueError('Unexpected source trigger')
    source=old['definition']['actions']['Get_item'];site=source['inputs']['parameters']['dataset']
    people_id=mapping['lists']['participants']['listId']
    if source['inputs']['parameters']['table'].strip('{}').lower()!=people_id:raise ValueError('Unverified participant target')
    auth=deepcopy(source['inputs']['authentication'])
    def http(uri,n=None):return {'type':'OpenApiConnection','inputs':{'parameters':{'dataset':site,'parameters/method':'GET','parameters/uri':uri,'parameters/headers':{'Accept':'application/json;odata=verbose'}},
      'host':{'apiId':'/providers/Microsoft.PowerApps/apis/shared_sharepointonline','connectionName':'shared_sharepointonline','operationId':'HttpRequest'},'authentication':deepcopy(auth)},'runAfter':after(n)}
    def base(list_id):return "_api/web/lists(guid'"+list_id+"')"
    def gate(test,code,n=None):return condition(test,{}, {'Error_'+code:setvar('ErrorCode',code),'Stop_'+code:compose('@div(1,0)','Error_'+code)},n)
    a={};prev=None
    for name,kind,value in [('People','array',[]),('Groups','array',[]),('FocusChecks','array',[]),('AvailableFocusChecks','array',[]),('MemberDisplays','array',[]),('GroupWork','integer',0),('ErrorCode','string','')]:
        key='Initialize_'+name;a[key]={'type':'InitializeVariable','inputs':{'variables':[{'name':name,'type':kind,'value':value}]},'runAfter':after(prev)};prev=key
    inside={'Input_reference':parse("@triggerBody()?['number']",{'type':'integer','minimum':1}),
      'Read_invoker':http('_api/web/currentuser?$select=Id','Input_reference'),
      'Invoker':parse("@body('Read_invoker')?['d']",{'type':'object','required':['Id'],'properties':{'Id':{'type':'integer','minimum':1}}},'Read_invoker')}
    own=cat(base(people_id)+"/items?$select=Id&$filter=ParticipantaccountId eq ","@string(body('Invoker')?['Id'])",'&$top=2')
    inside['Resolve_own_profile']=http(own,'Invoker')
    own_rows="coalesce("+arr('Resolve_own_profile')+",json('[]'))"
    inside['Own_profile']=compose('@first(union('+own_rows+",createArray(json('{}'))))",'Resolve_own_profile')
    test='and('+complete('Resolve_own_profile',1)+',equals(length('+own_rows+'),1),equals('+out('Own_profile')+"?['Id'],body('Input_reference')))"
    inside['Require_own_profile']=gate(test,'UNAUTHORIZED_PROFILE','Own_profile')
    get_item=deepcopy(source);get_item['runAfter']=after('Require_own_profile');inside['Get_item']=get_item
    # No broad candidate read before same-invoker own-profile binding succeeds.
    read=deepcopy(old['definition']['actions']['Candidate_source']);read['inputs']['parameters'].pop('$filter',None)
    read['inputs']['parameters'].update({'$top':501,'$orderby':'ID asc'});read['runAfter']=after('Get_item')
    read['runtimeConfiguration']={'paginationPolicy':{'minimumItemCount':501}};inside['Candidate_source']=read
    inside['Require_profile_bound']=gate(complete('Candidate_source',500,False),'PROFILE_BOUND_OR_INCOMPLETE','Candidate_source')
    prev='Require_profile_bound'
    for role in ['language','culture','timezone']:
        id_=mapping['lists'][role]['listId'];fields='Id,Title,Active,'+({'language':'ISOcode','culture':'CultureKey','timezone':'IANA_ID'}[role])
        read='Read_'+role;inside[read]=http(base(id_)+'/items?$select='+fields+'&$top=5001',prev)
        check='Require_'+role+'_bound';inside[check]=gate(complete(read,5000),'CATALOGUE_'+role.upper()+'_BOUND_OR_INCOMPLETE',read)
        q='Active_'+role;inside[q]=query('@'+arr(read),"equals(item()?['Active'],true)",check)
        s='IDs_'+role;inside[s]=select('@'+body(q),"@item()?['Id']",q);prev=s
    inside['Any_language']=query('@'+body('Active_language'),"equals(toLower(item()?['ISOcode']),'any')",prev)
    inside['Require_any_unambiguous']=gate("lessOrEquals(length(body('Any_language')),1)",'ANY_LANGUAGE_AMBIGUOUS','Any_language')
    any_row="first(union(body('Any_language'),createArray(json('{}'))))"
    inside['Raw_catalogues']=compose({'languageIds':"@body('IDs_language')",'cultureIds':"@body('IDs_culture')",'timezoneIds':"@body('IDs_timezone')",'anyLanguageId':'@'+any_row+"?['Id']"},'Require_any_unambiguous')
    # A nullable legacy availability value is ineligible data, not a default-to-available.
    checks=["not(empty(item()?['Participantaccount']?['Claims']))","not(empty(item()?['Participantaccount']?['DisplayName']))","not(empty(item()?['Status']?['Value']))",
      "contains(createArray('Active','Paused','Inactive'),item()?['ParticipationStatus']?['Value'])",
      "or(equals(item()?['OpenToConnections'],true),equals(item()?['OpenToConnections'],false))"]
    for field,cat_ in [('Teachlanguages','language'),('Learnlanguages','language'),('ShareCultures','culture'),('LearnCultures','culture')]:
        ids_="coalesce(item()?['"+field+"#Id'],json('[]'))"
        checks.append('equals(length(intersection('+ids_+",body('IDs_"+cat_+"'))),length("+ids_+'))')
    checks.append("or(equals(item()?['Timezone']?['Id'],null),contains(body('IDs_timezone'),item()?['Timezone']?['Id']))")
    inside['Qualified_source']=query("@body('Candidate_source')?['value']",'and('+','.join(checks)+')','Raw_catalogues')
    projection={'profileId':"@item()?['ID']",'accountKey':"@item()?['Participantaccount']?['Claims']",'status':"@item()?['Status']?['Value']",
      'participationStatus':"@item()?['ParticipationStatus']?['Value']",'openToConnections':"@item()?['OpenToConnections']",'timezoneId':"@item()?['Timezone']?['Id']"}
    for target,actual in [('teachIds','Teachlanguages'),('learnIds','Learnlanguages'),('shareCultureIds','ShareCultures'),('learnCultureIds','LearnCultures')]:projection[target]="@coalesce(item()?['"+actual+"#Id'],json('[]'))"
    inside['Raw_profiles']=select("@body('Qualified_source')",projection,'Qualified_source')
    inside.update(rules.normalization_actions('Shared',"@body('Raw_profiles')","@outputs('Raw_catalogues')",'Raw_profiles'))
    inside['Find_actor']=query("@body('Shared_Profiles')","equals(item()?['profileId'],body('Input_reference'))",'Shared_Catalogues')
    inside['Actor']=compose("@first(union(body('Find_actor'),createArray(json('{}'))))",'Find_actor')
    inside['Require_available_actor']=gate("and(equals(length(body('Find_actor')),1),"+rules.available('actor').wdl({'actor':"outputs('Actor')"})+')','PROFILE_UNAVAILABLE','Actor')
    predicate=rules.pair_rules()['eligible'].wdl({'left':"outputs('Actor')",'right':'item()'})
    inside['Eligible_people']=query("@body('Shared_Profiles')",predicate,'Require_available_actor')
    inside['Require_people_result_bound']=gate("lessOrEquals(length(body('Eligible_people')),50)",'PEOPLE_RESULT_BOUND','Eligible_people')
    p={'Person_raw':query("@body('Qualified_source')","equals(item()?['ID'],items('Each_person')?['profileId'])")}
    p['Person_fit']=compose(rules.pair_expression_projection("outputs('Actor')","items('Each_person')"),'Person_raw')
    p.update(display_actions('Person',"items('Each_person')","first(body('Person_raw'))",'Person_fit'))
    # Match arrays are public catalogue references only, never the source identity/account.
    p['Append_person']=append('People',{'profileId':"@items('Each_person')?['profileId']",'displayName':"@body('Person_public')?['displayName']",'fitType':"@outputs('Person_fit')?['fitType']",
      'profile':"@body('Person_public')",'match':{k:"@outputs('Person_fit')?['"+k+"']" for k in ['canLearnLanguageIds','canShareLanguageIds','canLearnCultureIds','canShareCultureIds']}},'Person_public')
    inside['Each_person']=loop("@body('Eligible_people')",p,'Require_people_result_bound')
    group_id=groups['lists']['groups']['listId'];members_id=groups['lists']['members']['listId']
    inside['Read_groups']=http(base(group_id)+'/items?$select=Id,Title,ExchangeType,LanguageFocusId,CultureFocusId,Capacity,State,Purpose,SourceRequestId,SetupComplete,WriteOwner&$orderby=Id&$top=101','Each_person')
    inside['Require_group_bound']=gate(complete('Read_groups',100),'GROUP_BOUND_OR_INCOMPLETE','Read_groups')
    inside['Potential_groups']=query('@'+arr('Read_groups'),"and(equals(item()?['State'],'Open'),equals(item()?['SetupComplete'],true),empty(item()?['WriteOwner']))",'Require_group_bound')
    # Readers do not silently treat missing commitment fields as committed.
    group_actions=group_pipeline(http,base,group_id,members_id,gate)
    inside['Groups_exist']=condition("not(empty(body('Potential_groups')))",group_actions,n='Potential_groups')
    a['Discovery_reads']={'type':'Scope','actions':inside,'runAfter':after('Initialize_ErrorCode')}
    ok="and(equals(actions('Discovery_reads')?['status'],'Succeeded'),empty(variables('ErrorCode')))"
    a['Response_size']=compose("@length(string(createArray(variables('People'),variables('Groups'))))")
    a['Response_size']['runAfter']={'Discovery_reads':ALL}
    success='and('+ok+",lessOrEquals(outputs('Response_size'),250000))"
    a['Discovery_report']=compose({'kind':'TandemDiscovery','schemaVersion':1,'sourceTicket':7,'packageBuildId':build_id,'rulesVersion':rules.VERSION,
      'runReference':"@workflow()?['run']?['name']",'mode':'OWNER_PREVIEW_PENDING_ACCESS_PROOF','writes':0,
      'success':'@'+success,'peopleCount':"@if("+success+",length(variables('People')),0)",'groupCount':"@if("+success+",length(variables('Groups')),0)",
      'code':"@if("+success+",'OK',if(not(empty(variables('ErrorCode'))),variables('ErrorCode'),if(greater(outputs('Response_size'),250000),'RESPONSE_BOUND','READ_OR_DATA_FAILED')))",
      'ordinaryUserAccessVerified':False},'Response_size')
    response=deepcopy(old['definition']['actions']['Respond_to_a_Power_App_or_flow'])
    response['runAfter']=after('Discovery_report')
    schema=response['inputs']['schema']['properties']
    for key in ['groupsjson','resultcode','runreference','mode']:schema[key]={'title':key,'type':'string','x-ms-content-hint':'TEXT','x-ms-dynamically-added':True}
    response['inputs']['body']={'candidatesjson':"@if(outputs('Discovery_report')?['success'],string(variables('People')),'[]')",'groupsjson':"@if(outputs('Discovery_report')?['success'],string(variables('Groups')),'[]')",
      'errormessage':"@if(outputs('Discovery_report')?['success'],'',if(equals(outputs('Discovery_report')?['code'],'PROFILE_UNAVAILABLE'),'Please save a valid Active profile and enable new connections before using Discovery.','Discovery could not complete. Please try again or report the run reference.'))",
      'resultcode':"@outputs('Discovery_report')?['code']",'runreference':"@outputs('Discovery_report')?['runReference']",'mode':'OWNER_PREVIEW_PENDING_ACCESS_PROOF'}
    a['Respond_to_a_Power_App_or_flow']=response
    measure(a);return a


def group_pipeline(http,base,group_id,members_id,gate):
    """Bounded analogue adapter; target request commit schema still needs observation."""
    # Connection Requests identity observed in #12 list inventory, fields checked live.
    requests='3d17485d-1dac-41f0-a1af-24e45daa4567'
    a={'Read_request_fields':http(base(requests)+'/fields?$select=InternalName,TypeAsString&$top=5000')}
    a['Request_commit_field']=query("@body('Read_request_fields')?['d']?['results']","and(equals(item()?['InternalName'],'OperationComplete'),equals(item()?['TypeAsString'],'Boolean'))",'Read_request_fields')
    a['Require_request_commit_schema']=gate('and('+complete('Read_request_fields',5000)+",equals(length(body('Request_commit_field')),1))",'GROUP_COMMIT_SCHEMA_UNVERIFIED','Request_commit_field')
    a['Read_memberships']=http(base(members_id)+'/items?$select=Id,GroupId,ParticipantId,MembershipStatus,MembershipKey&$orderby=Id&$top=2001','Require_request_commit_schema')
    a['Require_member_bound']=gate(complete('Read_memberships',2000),'MEMBERSHIP_BOUND_OR_INCOMPLETE','Read_memberships')
    a['Read_requests']=http(base(requests)+'/items?$select=Id,Status,OperationComplete&$orderby=Id&$top=501','Require_member_bound')
    a['Require_request_bound']=gate(complete('Read_requests',500),'REQUEST_BOUND_OR_INCOMPLETE','Read_requests')
    a['Open_groups']=query('@'+arr('Read_groups'),"and(equals(item()?['State'],'Open'),equals(item()?['SetupComplete'],true),empty(item()?['WriteOwner']))",'Require_request_bound')
    inner={'Reset_focus':setvar('FocusChecks',[]),'Reset_available':setvar('AvailableFocusChecks',[],'Reset_focus'),'Reset_members':setvar('MemberDisplays',[],'Reset_available')}
    inner['Physical_members']=query('@'+arr('Read_memberships'),"and(equals(item()?['GroupId'],items('Each_group')?['Id']),equals(item()?['MembershipStatus'],'Active'))",'Reset_members')
    inner['Member_profile_ids']=select("@body('Physical_members')","@item()?['ParticipantId']",'Physical_members')
    inner['Group_members']=query("@body('Shared_Profiles')","contains(body('Member_profile_ids'),item()?['profileId'])",'Member_profile_ids')
    inner['Accepted_source']=query('@'+arr('Read_requests'),"and(equals(item()?['Id'],items('Each_group')?['SourceRequestId']),equals(item()?['Status'],'Accepted'),equals(item()?['OperationComplete'],true))",'Group_members')
    commit_loop={'Membership_commit':query('@'+arr('Read_requests'),"and(equals(items('Check_member_commit')?['MembershipKey'],concat('request:',string(item()?['Id']),':participant:',string(items('Check_member_commit')?['ParticipantId']))),equals(item()?['Status'],'Accepted'),equals(item()?['OperationComplete'],true))")}
    commit_loop['Remember_commit']=append('AvailableFocusChecks',"@equals(length(body('Membership_commit')),1)",'Membership_commit')
    inner['Check_member_commit']=loop("@body('Physical_members')",commit_loop,'Accepted_source')
    inner['Uncommitted_members']=query("@variables('AvailableFocusChecks')","not(equals(item(),true))",'Check_member_commit')
    # Positive integer capacity/reference parsing precedes the shared rules.
    group_schema={'type':'object','required':['Id','Title','ExchangeType','Capacity','SourceRequestId','LanguageFocusId','CultureFocusId'],
      'properties':{'Id':{'type':'integer','minimum':1},'Title':{'type':'string','minLength':1},'ExchangeType':{'type':'string','enum':['Language','Culture','Combined']},'Capacity':{'type':'integer','minimum':2,'maximum':10},'SourceRequestId':{'type':'integer','minimum':1},
       **{f:{'type':'object','required':['results'],'properties':{'results':{'type':'array','items':{'type':'integer','minimum':1}}}} for f in ['LanguageFocusId','CultureFocusId']}}}
    inner['Parse_group']=parse("@items('Each_group')",group_schema,'Uncommitted_members')
    inner['Group_work_total']=compose("@add(variables('GroupWork'),add(length(body('Physical_members')),add(length(items('Each_group')?['LanguageFocusId']?['results']),length(items('Each_group')?['CultureFocusId']?['results']))))",'Parse_group')
    inner['Save_group_work']=setvar('GroupWork',"@outputs('Group_work_total')",'Group_work_total')
    inner['Require_group_work_bound']=gate("lessOrEquals(variables('GroupWork'),100)",'GROUP_WORK_BOUND','Save_group_work')
    inner['Reset_available_focus']=setvar('AvailableFocusChecks',[],'Require_group_work_bound')
    previous='Reset_available_focus'
    for kind,field,share in [('language','LanguageFocusId','teachIds'),('culture','CultureFocusId','shareCultureIds')]:
        loopname='Available_'+kind+'_focus'
        predicate='and('+rules.available('member').wdl({'member':'item()'})+",contains(item()?['"+share+"'],items('"+loopname+"')))"
        sub={'Find_available_'+kind:query("@body('Group_members')",predicate)}
        sub['Record_available_'+kind]=append('AvailableFocusChecks',"@not(empty(body('Find_available_"+kind+"')))",'Find_available_'+kind)
        inner[loopname]=loop("@items('Each_group')?['"+field+"']?['results']",sub,previous);previous=loopname
    inner['Unavailable_focus']=query("@variables('AvailableFocusChecks')","not(equals(item(),true))",previous)
    inner['Group_adapter']=compose({'groupId':"@items('Each_group')?['Id']",'exchangeType':"@items('Each_group')?['ExchangeType']",'state':"@items('Each_group')?['State']",'capacity':"@items('Each_group')?['Capacity']",'setupComplete':"@items('Each_group')?['SetupComplete']",
      'languageFocusIds':"@items('Each_group')?['LanguageFocusId']?['results']",'cultureFocusIds':"@items('Each_group')?['CultureFocusId']?['results']",'memberProfileIds':"@body('Member_profile_ids')",'focusSharersAvailable':"@empty(body('Unavailable_focus'))"},'Unavailable_focus')
    inner.update(rules.group_action_fragment('Group_fit',"outputs('Group_adapter')","body('Group_members')","outputs('Actor')","outputs('Shared_Catalogues')",'FocusChecks','Group_adapter'))
    displays={'Member_raw':query("@body('Qualified_source')","equals(item()?['ID'],items('Each_group_member')?['profileId'])")}
    displays.update(display_actions('Member',"items('Each_group_member')","first(body('Member_raw'))",'Member_raw'))
    displays['Append_member_display']=append('MemberDisplays',"@body('Member_public')",'Member_public')
    yes={'Each_group_member':loop("@body('Group_members')",displays)}
    for kind,field,catalogue in [('language','LanguageFocusId','Active_language'),('culture','CultureFocusId','Active_culture')]:
        previous='Each_group_member' if kind=='language' else 'Display_language_focus'
        q='Rows_'+kind+'_focus';s='Display_'+kind+'_focus'
        yes[q]=query('@'+body(catalogue),"contains(items('Each_group')?['"+field+"']?['results'],item()?['Id'])",previous)
        yes[s]=select('@'+body(q),{'id':"@item()?['Id']",'label':"@item()?['Title']"},q)
    yes['Append_group']=append('Groups',{'groupId':"@items('Each_group')?['Id']",'name':"@items('Each_group')?['Title']",'exchangeType':"@items('Each_group')?['ExchangeType']",
      'languageFocus':"@body('Display_language_focus')",'cultureFocus':"@body('Display_culture_focus')",'memberCount':"@length(body('Physical_members'))",'capacity':"@items('Each_group')?['Capacity']",'freeSlots':"@sub(items('Each_group')?['Capacity'],length(body('Physical_members')))",
      'joinAvailable':True,'description':"@coalesce(items('Each_group')?['Purpose'],'')",'members':"@variables('MemberDisplays')"},'Display_culture_focus')
    inner['Show_group']=condition("and(outputs('Group_fit_Result')?['compatible'],equals(length(body('Accepted_source')),1),empty(body('Uncommitted_members')))",yes,n='Group_fit_Result')
    a['Each_group']=loop("@body('Open_groups')",inner,'Open_groups')
    return a


def build_package(source,output):
    source,output=Path(source),Path(output)
    if any(p.exists() for p in [output,output.with_suffix('.definition.json'),output.with_suffix('.review.json')]):raise FileExistsError(output)
    with ZipFile(source) as z:
        original=json.loads(z.read(next(n for n in z.namelist() if n.endswith('/definition.json'))))
    mapping=json.loads((ROOT/'config/tenant_schema_mapping.json').read_text(encoding='utf-8'))
    groups=json.loads((ROOT/'config/group_schema_mapping.json').read_text(encoding='utf-8'))
    if not groups['mappingVerified']:raise ValueError('Verified group mapping required')
    build_id=str(uuid4());actions=build_actions(original,mapping,groups,build_id);metrics=measure(actions)
    site=original['properties']['definition']['actions']['Get_item']['inputs']['parameters']['dataset']
    with TemporaryDirectory() as temp:
        p=Path(temp)/'base.zip';envelope(p,sharepoint_site=site)
        with ZipFile(p) as z:entries={n:json.loads(z.read(n)) for n in z.namelist()}
    for n,doc in entries.items():
        if n.endswith('/definition.json'):
            doc['properties']['displayName']=NAME
            d=doc['properties']['definition'];d['triggers']=deepcopy(original['properties']['definition']['triggers']);d['actions']=actions
            # Preserve the actual Invoker source, never substitute an owner connection.
            ref=doc['properties']['connectionReferences']['shared_sharepointonline'];ref['source']='Invoker'
    entries['manifest.json']['details'].update(displayName='TandemDiscovery-v2',description='Issue 7 owner-preview read-only Discovery; preserves Invoker source, own-profile binding, shared rules and explicit bounds; ordinary-user access pending.')
    for item in entries['manifest.json']['resources'].values():
        if item['type']=='Microsoft.Flow/flows':item['details']['displayName']=NAME
    output.parent.mkdir(parents=True,exist_ok=True)
    with ZipFile(output,'x',ZIP_DEFLATED) as z:
        for n,doc in entries.items():z.writestr(n,json.dumps(doc,indent=2)+'\n')
    document=next(v for n,v in entries.items() if n.endswith('/definition.json'))
    review={'sourceTicket':7,'packageBuildId':build_id,'flowName':NAME,**metrics,'limits':{'actions':500,'nesting':8},'bounds':BOUNDS,
      'rulesSourceSha256':hashlib.sha256(Path(rules.__file__).read_bytes()).hexdigest(),'sourceExportSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'packageSha256':hashlib.sha256(output.read_bytes()).hexdigest(),
      'sourceTriggerPreserved':document['properties']['definition']['triggers']==original['properties']['definition']['triggers'],'connectionSource':'Invoker','ownerCredentialFallback':False,'writes':0,
      'mode':'OWNER_PREVIEW_PENDING_ACCESS_PROOF','tenantResult':'NOT_IMPORTED_NOT_TESTED','ordinaryUserAccessVerified':False,
      'groupDependency':'Connection Requests OperationComplete Boolean must exist when groups exist; accepted/complete source and member episodes required. Missing schema yields explicit error, never partial success.'}
    output.with_suffix('.definition.json').write_bytes((json.dumps(document,indent=2)+'\n').encode('utf-8'))
    output.with_suffix('.review.json').write_bytes((json.dumps(review,indent=2)+'\n').encode('utf-8'))
    return review


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    print(json.dumps(build_package(args.source,args.output),indent=2))


if __name__=='__main__':main()
