"""#48 owner-only, tenant-private Excel CREATE-ONLY importer.

Python builds the package locally; deployed execution uses existing standard
Excel and SharePoint connections only. No identity-bearing input leaves M365.
"""
from __future__ import annotations
from copy import deepcopy
import argparse
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4
from zipfile import ZipFile, ZIP_DEFLATED
from . import private_excel_probe as excel
from . import participant_import as old
from .build_import_probe import build_package as envelope
from .schema_audit import ALL, get, append, measure, wdl_string
from .activation_graph import analyze, walk
from .activation_schema import has_patterns

ROOT=Path(__file__).resolve().parents[2]
NAME='TandemPrivateParticipantImport'
HEADERS={'learn':'Which Language/Culture would you like to learn?',
         'learn2':'Which Language/Culture would you like to learn?2',
         'share':'Which Language/Culture would you love to share?'}
TARGETS={'teachIds':('language','TeachLanguages'),'learnIds':('language','LearnLanguages'),
         'shareCultureIds':('culture','ShareCultures'),'learnCultureIds':('culture','LearnCultures')}


def secure(node):
    if node['type'] not in ('If','Scope','Foreach','InitializeVariable','SetVariable','AppendToArrayVariable'):
        node['runtimeConfiguration']=deepcopy(excel.SECURE_INPUTS if node['type'] in ('Compose','ParseJson','Response') else excel.SECURE)
    return node


def comp(value,prev=None):return secure(old.compose(value,prev))
def check(expr,prev=None):return secure(old.gate(expr,prev))
def qry(source,expr,prev=None,statuses=None):return secure(old.query(source,expr,prev,statuses))
def add(var,value,prev=None):return secure(append(var,value,prev))
def setvar(var,value,prev=None):return secure({'type':'SetVariable','inputs':{'name':var,'value':value},'runAfter':old.after(prev)})
def select(source,value,prev=None):return secure({'type':'Select','inputs':{'from':source,'select':value},'runAfter':old.after(prev)})
def loop(source,actions,prev=None):return {'type':'Foreach','foreach':source,'actions':actions,'runAfter':old.after(prev),'runtimeConfiguration':{'concurrency':{'repetitions':1}}}
def last(actions):return next(reversed(actions),None)
def norm(expr):return 'toLower(trim(string('+expr+')))'
def safe_first(name):return "first(union(coalesce(body('"+name+"'),json('[]')),createArray(json('{}'))))"


def actions(site,mapping,values,build):
    lists=mapping['lists']; fields=lists['participants']['fields']
    field=lambda k:fields[k]['internalName']
    base=lambda r:"_api/web/lists(guid'"+lists[r]['listId']+"')"
    account=field('ParticipantAccount')
    def read(uri,prev=None):return secure(get(site,uri,prev))
    def resolve(email,prev=None):
        return secure({'type':'OpenApiConnection','runAfter':old.after(prev),'inputs':{
            'host':{'apiId':'/providers/Microsoft.PowerApps/apis/shared_sharepointonline','connectionName':'shared_sharepointonline','operationId':'SearchForUser'},
            'parameters':{'dataset':site,'table':lists['participants']['listId'],'entityId':account,'searchValue':email},
            'authentication':"@parameters('$authentication')",'retryPolicy':{'type':'none'}}})
    def post(uri,payload,prev=None):
        node=read(uri,prev);node['inputs']['parameters'].update({'parameters/method':'POST','parameters/body':payload,
            'parameters/headers':{'Accept':'application/json;odata=nometadata','Content-Type':'application/json;odata=verbose'}})
        node['inputs']['retryPolicy']={'type':'none'};return node
    def outcome(status,index,code=None):
        return {'dataRow':index,'status':status,'code':code or status}
    a={}
    for name,typ,value in [('Eligible','array',[]),('Outcomes','array',[]),
                           ('Stage','string','NOT_STARTED'),('WriteAttempted','boolean',False),('AccountAttempts','array',[]),
                           *[(key,'array',[]) for key in TARGETS]]:
        a['Init_'+name]=secure({'type':'InitializeVariable','runAfter':old.after(last(a)),
            'inputs':{'variables':[{'name':name,'type':typ,'value':value}]}})
    source=excel.actions(site,build)
    previous=last(a)
    a['Workbook_configuration']=deepcopy(source['Workbook_configuration']);a['Workbook_configuration']['runAfter']=old.after(previous)
    a['Read_options']=deepcopy(source['Read_options'])
    a['Read_options']['inputs']['schema']['properties']['ApplyChanges']={'type':'boolean'}
    a['Read_options']['inputs']['schema']['required'].append('ApplyChanges')
    a['Read_options']['inputs']['content']['ApplyChanges']="@coalesce(triggerBody()?['ApplyChanges'],false)"
    a['Read_workbook']=deepcopy(source['Read_workbook']);a['Private_rows']=deepcopy(source['Private_rows'])
    count="length(coalesce(body('Private_rows'),json('[]')))"
    a['Missing_headers']=qry("@body('Private_rows')",'not(and('+','.join(
        'contains(item(),'+wdl_string(h)+')' for h in [excel.EMAIL,excel.OTHER,*HEADERS.values()])+'))','Private_rows')
    a['Read_window_gate']=check('and('+','.join([
        'less('+count+',251)',"equals("+count+",body('Read_options')?['ExpectedRows'])",
        "empty(body('Missing_headers'))",
        "empty(body('Read_workbook')?['@odata.nextLink'])","empty(body('Read_workbook')?['odata.nextLink'])"]) + ')','Missing_headers')
    # Only bounded current reads; shared production schema is not recreated here.
    pre={}
    pre['Read_account_field']=read(base('participants')+"/fields(guid'"+fields['ParticipantAccount']['id']+"')?$select=InternalName,TypeAsString,EnforceUniqueValues,ReadOnlyField")
    pre['Read_item_type']=read(base('participants')+'?$select=ListItemEntityTypeFullName','Read_account_field')
    pre['Read_existing']=read(base('participants')+'/items?$select=Id,'+account+'Id,'+account+'/Name&$expand='+account+'&$top=5000','Read_item_type')
    for role in ('language','culture'):
        pre['Read_'+role]=read(base(role)+'/items?$select=Id,Title,Active&$top=5000',last(pre))
    pre['Current_reads_gate']=check('and('+','.join([
        "equals(body('Read_account_field')?['InternalName'],"+wdl_string(account)+")",
        "equals(body('Read_account_field')?['TypeAsString'],'User')",
        "equals(body('Read_account_field')?['EnforceUniqueValues'],true)",
        "equals(body('Read_account_field')?['ReadOnlyField'],false)",
        "not(empty(body('Read_item_type')?['ListItemEntityTypeFullName']))",
        *[old.complete('Read_'+r) for r in ('existing','language','culture')]])+')',last(pre))
    a['Prerequisites']=old.scope(pre,'Read_window_gate')
    # Workbook email cells may be mixed display-name/address text. No names are
    # sent to directory search: exactly one explicit validated address is required.
    r="outputs('Private_row')"
    raw="toLower(concat(string("+r+"?['Email']),' ',string("+r+"?['Please leave your name and Email'])))"
    tokens="replace("+raw+",'mailto:','')"
    for char in ['(',')','<','>','[',']',',',';',':','\r','\n','\t','\u00a0','\"']:
        tokens='replace('+tokens+','+wdl_string(char)+",' ')"
    rownum="@add(add(body('Read_options')?['SkipRows'],items('Prepare_rows')),1)"
    work={
        'Identity_stage':setvar('Stage','INVALID_OR_AMBIGUOUS_EMAIL'),
        'Private_row':comp("@body('Private_rows')?[items('Prepare_rows')]",'Identity_stage'),
        'Email_tokens':qry('@split('+tokens+",' ')","contains(item(),'@')",'Private_row'),
        'Unique_emails':comp("@union(body('Email_tokens'),body('Email_tokens'))",'Email_tokens'),
        'One_email':check("equals(length(outputs('Unique_emails')),1)",'Unique_emails'),
        'Email_document':comp({'root':{'email':"@first(outputs('Unique_emails'))"}},'One_email')}
    # XPath 1.0 performs character validation without unsupported ParseJSON regex.
    xpath=('boolean(string-length(/root/email)<=254 and contains(/root/email,"@") and '
        'string-length(substring-before(/root/email,"@"))>0 and '
        'not(contains(substring-after(/root/email,"@"),"@")) and '
        'contains(substring-after(/root/email,"@"),".") and '
        'not(starts-with(substring-after(/root/email,"@"),".")) and '
        'substring(/root/email,string-length(/root/email))!="." and '
        'translate(/root/email,"abcdefghijklmnopqrstuvwxyz0123456789._%+-@","")="")')
    work['Email_shape']=check("xpath(xml(outputs('Email_document')),"+wdl_string(xpath)+")",'Email_document')
    work['Lookup_stage']=setvar('Stage','ACCOUNT_LOOKUP_FAILED','Email_shape')
    work['Resolve_person']=resolve("@first(outputs('Unique_emails'))",'Lookup_stage')
    work['Exact_account']=check("and(equals("+norm("body('Resolve_person')?['Email']")+",first(outputs('Unique_emails'))),not(empty(body('Resolve_person')?['Claims'])),not(empty(trim(string(body('Resolve_person')?['DisplayName'])))),lessOrEquals(length(string(body('Resolve_person')?['DisplayName'])),255))",'Resolve_person')
    work['Existing_profile']=qry("@body('Read_existing')?['value']",'equals('+norm("item()?['"+account+"']?['Name']")+','+norm("body('Resolve_person')?['Claims']")+')','Exact_account')
    work['Existing_count_gate']=check("less(length(body('Existing_profile')),2)",'Existing_profile')
    details={}
    for key in TARGETS:details['Reset_'+key]=setvar(key,[],last(details))
    details['Selection_stage']=setvar('Stage','UNMAPPED_PROFILE_SELECTION',last(details))
    # A configuration entry covers a whole source cell, not a fuzzy substring.
    mapping_rows=[]
    for role,rows in values['mappings'].items():
        for value,spec in rows.items():
            mapping_rows.append({'role':role,'value':value,
                'state':'mapped' if spec['status']=='MAPPED' or (not value and spec['status']=='EXCLUDED') else 'blocked',
                'language':[v.lower() for v in spec['languageTitles']],
                'culture':[v.lower() for v in spec['cultureTitles']]})
    a['Value_mapping']=comp(mapping_rows,'Prerequisites')
    cells=[]
    for column,role in [('learn','learn'),('learn2','learn'),('share','share')]:
        cells.append({'role':role,'value':'@'+norm(r+'?['+wdl_string(HEADERS[column])+']')})
    details['Source_selections']=comp(cells,last(details))
    cell="outputs('Source_selections')?[items('Map_cells')]"
    m={
        'Cell_mapping':qry("@outputs('Value_mapping')",
            "and(equals(item()?['role'],"+cell+"?['role']),equals(item()?['value'],"+cell+"?['value']))"),
        'Require_cell_mapping':check("equals(length(body('Cell_mapping')),1)",'Cell_mapping'),
        'Mapping_valid':check("equals(first(body('Cell_mapping'))?['state'],'mapped')",'Require_cell_mapping')}
    for cat,dest_learn,dest_share in [('language','learnIds','teachIds'),('culture','learnCultureIds','shareCultureIds')]:
        inner={
            'Find_'+cat:qry("@body('Read_"+cat+"')?['value']","and(equals(item()?['Active'],true),equals("+norm("item()?['Title']")+",items('Map_"+cat+"')))"),
            'Require_'+cat:check("equals(length(body('Find_"+cat+"')),1)",'Find_'+cat)}
        inner['Assign_'+cat]=old.condition("equals("+cell+"?['role'],'learn')",
            {'Add_'+dest_learn:add(dest_learn,"@first(body('Find_"+cat+"'))?['Id']")},
            {'Add_'+dest_share:add(dest_share,"@first(body('Find_"+cat+"'))?['Id']")},'Require_'+cat)
        m['Map_'+cat]=loop("@first(body('Cell_mapping'))?['"+cat+"']",inner,last(m))
    details['Map_cells']=loop('@range(0,3)',m,last(details))
    details['Require_profile']=check("greater(add(add(length(variables('teachIds')),length(variables('learnIds'))),add(length(variables('shareCultureIds')),length(variables('learnCultureIds')))),0)",last(details))
    plan={'dataRow':rownum,'email':"@first(outputs('Unique_emails'))",'claims':"@body('Resolve_person')?['Claims']",
        'Learningfocus':"@string(outputs('Private_row')?['Is your learning focus:'])",
        'Title':"@body('Resolve_person')?['DisplayName']",**{k:"@union(variables('"+k+"'),variables('"+k+"'))" for k in TARGETS}}
    details['Keep_private_plan']=comp(plan,last(details))
    work['Preserve_existing']=old.condition("equals(length(body('Existing_profile')),1)",
        {'Preserved':add('Outcomes',outcome('EXISTING_PRESERVED',rownum))},details,'Existing_count_gate')
    per={'Prepare_one':old.scope(work)}
    # Every source row gets either a private plan or a safe terminal outcome.
    per['Already_handled']=qry("@variables('Outcomes')","equals(item()?['dataRow'],"+rownum[1:]+')','Prepare_one',ALL)
    per['Record_rejection']=old.condition("and(empty(body('Already_handled')),not(equals(actions('Keep_private_plan')?['status'],'Succeeded')))",
        {'Rejected':add('Outcomes',outcome('BLOCKED',rownum,"@variables('Stage')"))},previous='Already_handled')
    per['Prepared_record']=comp({'dataRow':rownum,
        'claims':"@if(equals(actions('Exact_account')?['status'],'Succeeded'),body('Resolve_person')?['Claims'],'')",
        'eligible':"@equals(actions('Keep_private_plan')?['status'],'Succeeded')",
        'plan':"@if(equals(actions('Keep_private_plan')?['status'],'Succeeded'),outputs('Keep_private_plan'),json('{}'))"},'Record_rejection')
    a['Prepare_rows']=loop('@range(0,'+count+')',per,'Value_mapping')
    a['Prepared_plans']=qry("@result('Prepare_rows')","and(equals(item()?['name'],'Prepared_record'),equals(item()?['status'],'Succeeded'))",'Prepare_rows',ALL)
    # Deduplicate by resolved account after ALL source rows have been prepared.
    p="body('Prepared_plans')?[items('Classify_rows')]?['outputs']?['plan']"
    c={'Same_account':qry("@body('Prepared_plans')",'equals('+norm("item()?['outputs']?['claims']")+','+norm(p+"?['claims']")+')')}
    c['Unique_source_account']=old.condition("equals(length(body('Same_account')),1)",
        {'Eligible_row':add('Eligible',"@items('Classify_rows')")},
        {'Duplicate_source':add('Outcomes',outcome('BLOCKED','@'+p+"?['dataRow']",'DUPLICATE_SOURCE_ACCOUNT'))},'Same_account')
    a['Classify_rows']=loop("@range(0,length(body('Prepared_plans')))",{
        'Classify_valid_plan':old.condition("equals(body('Prepared_plans')?[items('Classify_rows')]?['outputs']?['eligible'],true)",c)},'Prepared_plans')
    a['Prepared_count_gate']=check("and(equals(actions('Read_window_gate')?['status'],'Succeeded'),equals(actions('Prerequisites')?['status'],'Succeeded'),equals(length(body('Prepared_plans')),"+count+"),equals(add(length(variables('Eligible')),length(variables('Outcomes'))),"+count+'))','Classify_rows')
    # Apply rechecks account, uniqueness, current catalogue and current absence.
    q="body('Prepared_plans')?[variables('Eligible')?[items('Execute_rows')]]?['outputs']?['plan']"
    qnum='@'+q+"?['dataRow']"
    apply={
        'Apply_identity_stage':setvar('Stage','ACCOUNT_RECHECK_FAILED'),
        'Recheck_person':resolve('@'+q+"?['email']",'Apply_identity_stage'),
        'Recheck_exact':check('and(equals('+norm("body('Recheck_person')?['Claims']")+','+norm(q+"?['claims']")+'),equals('+norm("body('Recheck_person')?['Email']")+','+q+"?['email']))",'Recheck_person'),
        'Ensure_stage':setvar('Stage','ACCOUNT_REGISTRATION_FAILED','Recheck_exact'),
        'Account_attempt':add('AccountAttempts',{'dataRow':qnum},'Ensure_stage'),
        'Ensure_account':post('_api/web/ensureuser',{'logonName':'@'+q+"?['claims']"},'Account_attempt'),
        'Ensure_exact':check("and(greater(coalesce(body('Ensure_account')?['Id'],0),0),equals("+norm("body('Ensure_account')?['LoginName']")+','+norm(q+"?['claims']")+'))','Ensure_account')}
    existing_uri="@concat("+wdl_string(base('participants')+'/items?$select=Id,'+account+'Id&$filter='+account+'Id eq ')+",string(body('Ensure_account')?['Id']),'&$top=2')"
    apply['Current_existing']=read(existing_uri,'Ensure_exact')
    apply['Current_existing_gate']=check(old.complete('Current_existing',2),'Current_existing')
    new={'Catalogue_stage':setvar('Stage','CATALOGUE_CHANGED')}
    for role in ('language','culture'):
        new['Fresh_'+role]=read(base(role)+'/items?$select=Id,Title,Active&$top=5000',last(new))
        new['Fresh_'+role+'_complete']=check(old.complete('Fresh_'+role),last(new))
        # Compare active id/title pairs for selected IDs; an ID rename is drift.
        ids='union('+q+"?['"+('teachIds' if role=='language' else 'shareCultureIds')+"'],"+q+"?['"+('learnIds' if role=='language' else 'learnCultureIds')+"'])"
        for prefix,source_name in [('Old','Read_'),('Now','Fresh_')]:
            name=prefix+'_selected_'+role
            new[name]=qry("@body('"+source_name+role+"')?['value']","and(equals(item()?['Active'],true),contains("+ids+",item()?['Id']))",last(new))
            new[name+'_projection']=select("@body('"+name+"')",{'Id':"@item()?['Id']",'Title':"@item()?['Title']"},last(new))
        new['Catalogue_'+role+'_gate']=check("and(equals(length(body('Now_selected_"+role+"')),length("+ids+")),equals(length(intersection(body('Old_selected_"+role+"_projection'),body('Now_selected_"+role+"_projection'))),length("+ids+')))',last(new))
    payload={'__metadata':{'type':"@body('Read_item_type')?['ListItemEntityTypeFullName']"},field('Title'):'@'+q+"?['Title']",
        field('LearningFocus'):'@'+q+"?['Learningfocus']",
        account+'Id':"@body('Ensure_account')?['Id']",field('ParticipationStatus'):'Active',field('OpenToConnections'):True,
        **{field(logical)+'Id':{'results':'@'+q+"?['"+k+"']"} for k,(_,logical) in TARGETS.items()}}
    new['Write_stage']=setvar('Stage','CREATE_UNCONFIRMED',last(new))
    new['Mark_write']=setvar('WriteAttempted',True,'Write_stage')
    new['Create_participant']=post(base('participants')+'/items',payload,'Mark_write')
    new['Reread_created']=read(existing_uri)
    new['Reread_created']['runAfter']=old.after('Create_participant',ALL)
    new['Reread_created']['runAfter']['Mark_write']=['Succeeded']
    success="and(equals(actions('Create_participant')?['status'],'Succeeded'),equals(outputs('Create_participant')?['statusCode'],201),"+old.complete('Reread_created',2)+",equals(length(coalesce(body('Reread_created')?['value'],json('[]'))),1),not(empty(body('Create_participant')?['Id'])),equals(body('Create_participant')?['Id'],first(union(coalesce(body('Reread_created')?['value'],json('[]')),createArray(json('{}'))))?['Id']))"
    new['Record_create']=add('Outcomes',outcome("@if("+success+",'CREATED','UNKNOWN')",qnum), 'Reread_created')
    apply['Still_absent']=old.condition("empty(body('Current_existing')?['value'])",new,
        {'Concurrent_existing':add('Outcomes',outcome('EXISTING_PRESERVED',qnum))},'Current_existing_gate')
    run={'Reset_write_flag':setvar('WriteAttempted',False), 'Apply_one':old.scope(apply,'Reset_write_flag')}
    run['Apply_recorded']=qry("@variables('Outcomes')","equals(item()?['dataRow'],"+q+"?['dataRow'])",'Apply_one',ALL)
    run['Fallback_apply']=old.condition("empty(body('Apply_recorded'))",{'Apply_failed':add('Outcomes',outcome("@if(variables('WriteAttempted'),'UNKNOWN','BLOCKED')",qnum,"@variables('Stage')"))},previous='Apply_recorded')
    dry={'Dry_rows':loop("@range(0,length(variables('Eligible')))",{'Dry_ready':add('Outcomes',outcome('READY_CREATE',"@body('Prepared_plans')?[variables('Eligible')?[items('Dry_rows')]]?['outputs']?['dataRow']"))})}
    a['Execute_mode']=old.condition("equals(body('Read_options')?['ApplyChanges'],true)",
        {'Execute_rows':loop("@range(0,length(variables('Eligible')))",run)},dry,'Prepared_count_gate')
    for status in ['READY_CREATE','CREATED','EXISTING_PRESERVED','BLOCKED','UNKNOWN']:
        a['Count_'+status]=qry("@variables('Outcomes')","equals(item()?['status'],"+wdl_string(status)+')',last(a),ALL)
    processed="length(variables('Outcomes'))"
    finished="and(equals(actions('Prepared_count_gate')?['status'],'Succeeded'),equals("+processed+','+count+'))'
    failure_code="if(not(equals(actions('Read_options')?['status'],'Succeeded')),'INVALID_READ_OPTIONS',if(not(equals(actions('Read_workbook')?['status'],'Succeeded')),'EXCEL_READ_FAILED',if(not(equals(actions('Private_rows')?['status'],'Succeeded')),'INVALID_TABLE_RESPONSE',if(not(empty(body('Missing_headers'))),'SOURCE_HEADERS_MISMATCH',if(not(equals(actions('Read_window_gate')?['status'],'Succeeded')),'INCOMPLETE_SOURCE_WINDOW',if(not(equals(actions('Prerequisites')?['status'],'Succeeded')),'SHAREPOINT_PREREQUISITES_FAILED','IMPORT_INCOMPLETE'))))))"
    a['Import_report']={'type':'Select','runtimeConfiguration':deepcopy(excel.SECURE_INPUTS),
        'runAfter':old.after(last(a),ALL),'inputs':{'from':'@createArray(0)','select':{
            'kind':NAME,'schemaVersion':1,'sourceTicket':48,'packageBuildId':build,
            'runReference':"@workflow()?['run']?['name']",'complete':'@'+finished,
            'code':"@if(not("+finished+"),"+failure_code+",if(not(empty(body('Count_UNKNOWN'))),'UNKNOWN_WRITE',if(not(empty(body('Count_BLOCKED'))),'COMPLETED_WITH_EXCEPTIONS','OK')))",
            'applyChanges':"@equals(triggerBody()?['ApplyChanges'],true)",
            'skipRows':"@if(equals(actions('Read_options')?['status'],'Succeeded'),body('Read_options')?['SkipRows'],0)",'rowCount':'@'+count,'processedRows':'@'+processed,
            'readyCount':"@length(body('Count_READY_CREATE'))",'createdCount':"@length(body('Count_CREATED'))",
            'existingCount':"@length(body('Count_EXISTING_PRESERVED'))",'blockedCount':"@length(body('Count_BLOCKED'))",
            'unknownCount':"@length(body('Count_UNKNOWN'))",'accountRegistrationAttempts':"@length(variables('AccountAttempts'))",
            'identityValuesIncluded':False,'newParticipationStatus':'Active','newOpenToConnections':True,
            'validationStatusOwner':61,'rows':"@variables('Outcomes')",
            'diagnostics':{name:"@actions('"+name+"')?['status']" for name in ['Read_options','Read_workbook','Private_rows','Read_window_gate','Prerequisites','Prepared_count_gate']}}}}
    return a


def build_package(output):
    output=Path(output);paths=[output,output.with_suffix('.definition.json'),output.with_suffix('.review.json')]
    if any(p.exists() for p in paths):raise FileExistsError('Preserve existing packages')
    mapping=json.loads((ROOT/'config/tenant_schema_mapping.json').read_text(encoding='utf-8'))
    values=json.loads((ROOT/'config/participant_excel_value_mapping.json').read_text(encoding='utf-8'))
    if values.get('reviewed') is not True:raise ValueError('Technical source mapping review is required')
    site=json.loads((ROOT/'config/batch_schema_contract.json').read_text())['site']
    with TemporaryDirectory() as tmp:
        base=Path(tmp)/'seed.zip';doc=envelope(base,sharepoint_site=site)
        with ZipFile(base) as z:entries={n:json.loads(z.read(n)) for n in z.namelist()}
    flow=doc['properties']['definition'];props=doc['properties'];props['displayName']=NAME+' v1'
    flow['actions']=actions(site,mapping,values,doc['name'])
    flow['triggers']={'manual':{'type':'Request','kind':'Button','inputs':{'schema':{'type':'object','properties':{
        'ApplyChanges':{'type':'boolean','default':False,'title':'ApplyChanges','x-ms-content-hint':'BOOLEAN'},
        'SkipRows':{'type':'integer','minimum':0,'default':0,'title':'SkipRows (data rows)','x-ms-content-hint':'NUMBER'},
        'ExpectedRows':{'type':'integer','minimum':0,'maximum':250,'default':206,'title':'ExpectedRows (after skip)','x-ms-content-hint':'NUMBER'}},'required':[]}},'runtimeConfiguration':{'concurrency':{'runs':1}}}}
    connector=excel.CONNECTOR
    props['connectionReferences'][connector]={'connectionName':'IMPORT_SELECT_EXISTING_EXCEL_CONNECTION','source':'Embedded','id':excel.API,'tier':'NotSpecified','apiName':'excelonlinebusiness','isProcessSimpleApiReferenceConversionAlreadyDone':False}
    metrics=measure(flow['actions']);excel.validate_secure_data(flow['actions']);excel.validate_excel_template(flow['actions']);old.validate_expressions(flow)
    if has_patterns(flow['actions']) or analyze(flow):raise ValueError('Activation guard failed: '+str(analyze(flow)))
    manifest=entries['manifest.json'];resource=next(k for k,v in manifest['resources'].items() if v['type']=='Microsoft.Flow/flows')
    api,conn=str(uuid4()),str(uuid4());manifest['resources'][resource]['dependsOn'] += [api,conn]
    manifest['resources'][resource]['details']['displayName']=NAME+' v1'
    manifest['details'].update(displayName=NAME+'-v1',description='#48 private Excel dry-run/create-only importer. Existing owner Excel/SharePoint. Native importer NOT RUN.')
    manifest['resources'][api]={'id':excel.API,'name':connector,'type':'Microsoft.PowerApps/apis','suggestedCreationType':'Existing','details':{'displayName':'Excel Online (Business)'},'configurableBy':'System','hierarchy':'Child','dependsOn':[]}
    manifest['resources'][conn]={'type':'Microsoft.PowerApps/apis/connections','suggestedCreationType':'Existing','creationType':'Existing','details':{'displayName':'Select existing owner Excel connection'},'configurableBy':'User','hierarchy':'Child','dependsOn':[api]}
    for n in entries:
        if n.endswith('/definition.json'):entries[n]=doc
        elif n.endswith('/apisMap.json'):entries[n][connector]=api
        elif n.endswith('/connectionsMap.json'):entries[n][connector]=conn
    output.parent.mkdir(parents=True,exist_ok=True)
    with ZipFile(output,'x',ZIP_DEFLATED) as z:
        for n,v in entries.items():z.writestr(n,json.dumps(v,indent=2,ensure_ascii=False)+'\n')
    review={'sourceTicket':48,'artifactVersion':'v1','packageBuildId':doc['name'],**metrics,
        'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'mappingSha256':hashlib.sha256((ROOT/'config/participant_excel_value_mapping.json').read_bytes()).hexdigest(),
        'nativeImport':'NOT RUN','nativeCombinedConnectors':'NOT RUN','nativeResolvePerson':'NOT RUN','nativeApply':'NOT RUN',
        'connections':'Existing standard Excel Online (Business) and SharePoint owner connections; Embedded. No other connectors/runtime.',
        'inputs':{'ApplyChanges':'Boolean false default. First run false. True creates only eligible missing profiles; exceptions are skipped.','SkipRows':'Integer >=0 default0;206 starts data row207, header excluded.','ExpectedRows':'Exact number after skip,0..250; default206'},
        'outputs':'Import_report Outputs is a one-element array; aggregate counts and data-row-number/status/code only, no identities or raw connector errors.',
        'configuration':'Import legacy ZIP as NEW. Privately select Read_workbook Location/Document Library/File/actual Table. Source settings not known to generator.',
        'semantics':'Fresh preflight each run, exact single email/person, reviewed whole-cell catalogue mapping, duplicate source accounts blocked, existing profiles untouched. Apply may partially complete; no rollback, no update/delete/reset. Status is owned by #61 event validator.',
        'oneTimeAccountEffect':'Apply calls SharePoint ensureuser for resolved claims before assigning Person field. May register account in site user information; no role assignment/group membership/sharing API is called. Dry-run has no explicit POST/ensureuser/participant write.',
        'privacy':'Raw actions secured explicitly; report is deliberate input-secured Select projection. Verify native private histories without sharing raw values. Owner-only operator; not participant UI.',
        'drift81':'One-time source adapter only: reviewed Excel whole-cell interpretation and email extraction do not replace shared production profile normalization/compatibility. No shared/core/app schema/IO/build changes. #61 still uses #81 after create; imported validation acceptance NOT RUN.',
        'limitations':['No fuzzy mappings or guessed accounts. Unmapped selections/reconfirmation-only/no-account rows are exceptions.','Apply must follow reviewed dry-run; resolve person and combined connector capability are first checked there. Ensureuser/create capability remains a native apply gate.','Same-account uniqueness prevents replay duplicates; concurrent writes can yield UNKNOWN and require private reconciliation. Never automatically retry an unknown write.','SkipRows is positional; use0 if previous source rows were reordered.','No source file byte hash is claimed: Excel table reads do not supply one. Dry-run and Apply both reread current table; review any intervening source/mapping changes.','An Excel read can create a service-managed file version; no worksheet write operation exists.']}
    paths[1].write_text(json.dumps(doc,indent=2,ensure_ascii=False)+'\n',encoding='utf-8');paths[2].write_text(json.dumps(review,indent=2)+'\n',encoding='utf-8')
    return doc,review

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    _,review=build_package(args.output);print(json.dumps(review,indent=2))
