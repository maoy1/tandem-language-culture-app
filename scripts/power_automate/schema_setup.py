"""Issue 66 bounded one-time setup, generated from owner-returned schema metadata.

This utility builds an import package. The imported flow runs in Power Automate.
Default run is read-only; ApplyChanges must explicitly be true to enable writes.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile, ZIP_DEFLATED

try:
    from .schema_audit import get, measure, ALL, wdl_string, match_expr
    from .build_import_probe import build_package as probe
except ImportError:
    from schema_audit import get, measure, ALL, wdl_string, match_expr
    from build_import_probe import build_package as probe

NAME='TandemSchemaSetup'
LISTS={'participants':'fd3adf46-f81d-4a7b-a80c-567fde0175dc',
       'language':'3c1fcd2b-ce62-4af0-a96d-9b0d7502cb63',
       'timezone':'7beddfff-1881-4a82-8003-29933b836350'}
NEW={
    'ParticipationStatus':dict(label='Participation status',kind='Choice',default='Active',
        xml='<Field Type="Choice" Name="ParticipationStatus" StaticName="ParticipationStatus" DisplayName="Participation status" Required="TRUE" Format="Dropdown" FillInChoice="FALSE"><Default>Active</Default><CHOICES><CHOICE>Active</CHOICE><CHOICE>Paused</CHOICE><CHOICE>Inactive</CHOICE></CHOICES></Field>'),
    'OpenToConnections':dict(label='Open to new connections',kind='Boolean',default='1',
        xml='<Field Type="Boolean" Name="OpenToConnections" StaticName="OpenToConnections" DisplayName="Open to new connections" Required="TRUE"><Default>1</Default></Field>')}
UPDATES=[('language','Title','fa564e0f-0c70-4ab9-b863-0177e6ddd247',{'Required':True}),
         ('timezone','Title','fa564e0f-0c70-4ab9-b863-0177e6ddd247',{'Required':True}),
         ('timezone','IANA_ID','2c179581-99f9-4700-9fed-f2e667fc3e8c',{'Required':True,'Indexed':True,'EnforceUniqueValues':True})]
FIELD_SELECT='Id,InternalName,Title,TypeAsString,Required,Indexed,EnforceUniqueValues,DefaultValue,ReadOnlyField,SchemaXml'


def condition(expression,actions,after=None,otherwise=None):
    return dict(type='If',expression='@'+expression,actions=actions,
                **{'else':{'actions':otherwise or {}}},runAfter={after:['Succeeded']} if after else {})


def request(site,uri,body,after=None,merge=False):
    result=get(site,uri,after)
    p=result['inputs']['parameters'];p['parameters/method']='POST'
    p['parameters/headers']['Content-Type']='application/json;odata=verbose'
    p['parameters/headers']['Accept']='application/json;odata=nometadata'
    if merge:p['parameters/headers']['X-HTTP-Method']='MERGE'
    p['parameters/body']=body
    result['inputs']['retryPolicy']={'type':'none'}
    return result


def base(role):return "_api/web/lists(guid'"+LISTS[role]+"')"


def field_rows(role,prefix='Read'):
    return f"body('{prefix}_{role}_fields')?['value']"


def query(source,where,after=None):
    return dict(type='Query',inputs={'from':'@'+source,'where':'@'+where},runAfter={after:['Succeeded']} if after else {})


def new_valid(name,source):
    spec=NEW[name]
    test=f"and(equals(item()?['InternalName'], '{name}'),equals(item()?['TypeAsString'], '{spec['kind']}'),equals(item()?['Required'],true),equals(string(item()?['DefaultValue']),'{spec['default']}'),equals(item()?['ReadOnlyField'],false))"
    if spec['kind']=='Choice':
        # Exact allowed values, including order-independent comparison.
        values="xpath(xml(coalesce(item()?['SchemaXml'],'<Field/>')), '/*[local-name()=\"Field\"]/*[local-name()=\"CHOICES\"]/*[local-name()=\"CHOICE\"]/text()')"
        test=f"and({test},equals(length({values}),3),contains({values},'Active'),contains({values},'Paused'),contains({values},'Inactive'))"
    return query(source,test)


def settings_valid(role,name,field_id,settings,source):
    checks=[f"equals(toLower(string(item()?['Id'])),'{field_id}')",f"equals(item()?['InternalName'],'{name}')","equals(item()?['TypeAsString'],'Text')","equals(item()?['ReadOnlyField'],false)"]
    checks += [f"equals(item()?['{k}'],true)" for k in settings]
    return query(source,'and('+','.join(checks)+')')


def definition(site,build_id):
    reads={};previous=None
    for role in LISTS:
        name=f'Read_{role}_permissions'
        reads[name]=get(site,base(role)+'/EffectiveBasePermissions',previous);previous=name
        name=f'Read_{role}_fields'
        reads[name]=get(site,base(role)+'/fields?$select='+FIELD_SELECT+'&$top=5000',previous);previous=name
    for role,key in [('language','ISOcode'),('timezone','IANA_ID')]:
        name=f'Read_{role}_values'
        reads[name]=get(site,base(role)+f'/items?$select=Id,Title,{key}&$top=5000',previous);previous=name
        name=f'Invalid_{role}_values'
        reads[name]=query(f"body('Read_{role}_values')?['value']",f"or(empty(trim(string(item()?['Title']))),empty(trim(string(item()?['{key}']))))",previous);previous=name
        name=f'Keys_{role}'
        reads[name]=dict(type='Select',inputs={'from':f"@body('Read_{role}_values')?['value']",'select':f"@toLower(trim(string(item()?['{key}'])))"},runAfter={previous:['Succeeded']});previous=name
    checks=[]
    for role in LISTS:
        checks.append(f"equals(mod(div(int(coalesce(body('Read_{role}_permissions')?['Low'],body('Read_{role}_permissions')?['EffectiveBasePermissions']?['Low'],'0')),2048),2),1)")
        checks += [f"empty(coalesce(body('Read_{role}_fields')?['@odata.nextLink'],body('Read_{role}_fields')?['odata.nextLink'],''))"]
    for role in ['language','timezone']:
        checks += [f"empty(body('Invalid_{role}_values'))",f"equals(length(body('Keys_{role}')),length(union(body('Keys_{role}'),body('Keys_{role}'))))",
                   f"empty(coalesce(body('Read_{role}_values')?['@odata.nextLink'],body('Read_{role}_values')?['odata.nextLink'],''))"]
    for name,spec in NEW.items():
        n='Candidates_'+name
        reads[n]=query(field_rows('participants'),match_expr([name,spec['label']]),previous);previous=n
        n='Valid_'+name
        reads[n]=new_valid(name,field_rows('participants'));reads[n]['runAfter']={previous:['Succeeded']};previous=n
        checks.append(f"or(empty(body('Candidates_{name}')),and(equals(length(body('Candidates_{name}')),1),equals(length(body('Valid_{name}')),1)))")
    for role,name,field_id,settings in UPDATES:
        token=role+'_'+name
        n='Target_'+token
        reads[n]=query(field_rows(role),f"and(equals(toLower(string(item()?['Id'])),'{field_id}'),equals(item()?['InternalName'],'{name}'),equals(item()?['TypeAsString'],'Text'),equals(item()?['ReadOnlyField'],false))",previous);previous=n
        checks.append(f"equals(length(body('{n}')),1)")
        n='Valid_'+token
        reads[n]=settings_valid(role,name,field_id,settings,field_rows(role));reads[n]['runAfter']={previous:['Succeeded']};previous=n
    reads['Preflight_ready']=dict(type='Compose',inputs='@and('+','.join(checks)+')',runAfter={previous:['Succeeded']})
    writes={};previous=None
    for name,spec in NEW.items():
        writes['Ensure_'+name]=condition(f"empty(body('Candidates_{name}'))",{
            'Create_'+name:request(site,base('participants')+'/fields/createfieldasxml',{'parameters':{'__metadata':{'type':'SP.XmlSchemaFieldCreationInformation'},'SchemaXml':spec['xml'],'Options':8}})},previous)
        previous='Ensure_'+name
    for role,name,field_id,settings in UPDATES:
        token=role+'_'+name
        writes['Ensure_'+token]=condition(f"empty(body('Valid_{token}'))",{
            'Update_'+token:request(site,base(role)+"/fields(guid'"+field_id+"')",{'__metadata':{'type':'SP.FieldText'},**settings},merge=True)},previous)
        previous='Ensure_'+token
    # Fresh readback is mandatory. Successful HTTP writes alone never mean alignment passed.
    for role in LISTS:
        n='Verify_'+role+'_fields'
        writes[n]=get(site,base(role)+'/fields?$select='+FIELD_SELECT+'&$top=5000',previous);previous=n
    verified=[]
    for name in NEW:
        n='Verified_'+name;writes[n]=new_valid(name,field_rows('participants','Verify'));writes[n]['runAfter']={previous:['Succeeded']};previous=n
        verified.append(f"equals(length(body('{n}')),1)")
    for role,name,field_id,settings in UPDATES:
        n='Verified_'+role+'_'+name;writes[n]=settings_valid(role,name,field_id,settings,field_rows(role,'Verify'));writes[n]['runAfter']={previous:['Succeeded']};previous=n
        verified.append(f"equals(length(body('{n}')),1)")
    writes['Setup_verified']=dict(type='Compose',inputs='@and('+','.join(verified)+')',runAfter={previous:['Succeeded']})
    actions={'Preflight':dict(type='Scope',actions=reads,runAfter={})}
    actions['Apply_only_when_ready']=condition("and(equals(outputs('Preflight_ready'),true),equals(triggerBody()?['boolean'],true))",{
        'Apply_setup':dict(type='Scope',actions=writes,runAfter={})},'Preflight')
    actions['Setup_report']=dict(type='Compose',runAfter={'Apply_only_when_ready':ALL},inputs={
        'kind':NAME,'schemaVersion':1,'sourceTicket':66,'packageBuildId':build_id,'runReference':"@workflow()?['run']?['name']",
        'applyRequested':"@equals(triggerBody()?['boolean'],true)",
        'preflightReady':"@equals(outputs('Preflight_ready'),true)",
        'setupVerified':"@and(equals(actions('Apply_setup')?['status'],'Succeeded'),equals(outputs('Setup_verified'),true))",
        'result':"@if(not(equals(outputs('Preflight_ready'),true)),'BLOCKED_PREFLIGHT',if(not(equals(triggerBody()?['boolean'],true)),'DRY_RUN_READY',if(and(equals(actions('Apply_setup')?['status'],'Succeeded'),equals(outputs('Setup_verified'),true)),'SETUP_VERIFIED','FAILED_OR_PENDING_READBACK')))",
        'scope':'Two new participant fields; required language/timezone Title; required indexed unique IANA_ID. No row writes, no deletes, no permissions or working-flow changes.',
        'recovery':'If any write fails, prior successful schema operations remain. Re-run dry mode to recheck. Never claim rollback; rerun audit after apply.',
        'permissionEvidence':{r:f"@body('Read_{r}_permissions')" for r in LISTS}})
    actions['Respond']=dict(type='Response',kind='PowerApp',runAfter={'Setup_report':['Succeeded']},inputs={'statusCode':200,
        'schema':{'type':'object','properties':{'reportjson':{'title':'reportjson','type':'string','x-ms-dynamically-added':True,'x-ms-content-hint':'TEXT'}}},
        'body':{'reportjson':"@string(outputs('Setup_report'))"}})
    # Even failure while collecting metadata produces a report, with all writes skipped.
    actions['Apply_only_when_ready']['runAfter']={'Preflight':ALL}
    return actions


def build_package(output,site):
    output=Path(output)
    for p in [output,output.with_suffix('.definition.json'),output.with_suffix('.review.json')]:
        if p.exists():raise FileExistsError(p)
    with TemporaryDirectory(prefix='tandem-schema-setup-') as tmp:
        path=Path(tmp)/'base.zip';document=probe(path,sharepoint_site=site)
        with ZipFile(path) as z:entries={n:json.loads(z.read(n)) for n in z.namelist()}
    document['properties']['displayName']=NAME
    d=document['properties']['definition'];d['actions']=definition(site,document['name'])
    d['triggers']['manual']['inputs']['schema']={'type':'object','properties':{'boolean':{'title':'ApplyChanges','type':'boolean','default':False,'x-ms-content-hint':'BOOLEAN','x-ms-dynamically-added':True}},'required':[]}
    # Request-trigger concurrency is incompatible with the synchronous Power Apps response.
    # This disposable owner setup helper must be run once at a time. Keep the response synchronous.
    metrics=measure(d['actions'])
    for n in entries:
        if n.endswith('/definition.json'):entries[n]=document
    m=entries['manifest.json'];m['details']['displayName']=NAME+'-package'
    m['details']['description']='Issue 66 one-time bounded schema delta. Default read-only dry run. Explicit ApplyChanges plus verified ManageLists/type/value checks gates all schema writes.'
    next(v for v in m['resources'].values() if v['type']=='Microsoft.Flow/flows')['details']['displayName']=NAME
    output.parent.mkdir(parents=True,exist_ok=True)
    with ZipFile(output,'x',ZIP_DEFLATED) as z:
        for n,v in entries.items():z.writestr(n,json.dumps(v,indent=2)+'\n')
    output.with_suffix('.definition.json').write_bytes((json.dumps(document,indent=2)+'\n').encode())
    review={'ticket':66,'flowName':NAME,'packageBuildId':document['name'],'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),**metrics,
        'limits':{'actions':500,'nesting':8},'defaultMode':'Read-only dry run; ApplyChanges omitted/false never writes',
        'productionFlow':False,'prerequisite':'Existing owner SharePoint connection; ManageLists verified per affected list before any write',
        'tenantImportAndRun':'NOT RUN','noParticipantRowReadsOrWrites':True,
        'evidenceSource':'Owner-returned Audit_report build 1fd35100-e381-48b7-9d53-aa927d1131ed, run 08584074638260638544180416987CU28',
        'unchanged':'Participant identity/selections, legacy Status choices, IANA_ID lookup display, optional Windows metadata, existing row values and permissions',
        'writeScope':[{'role':'participants','create':k,'required':True,'default':v['default']} for k,v in NEW.items()]+[{'role':r,'field':n,'settings':s} for r,n,i,s in UPDATES]}
    output.with_suffix('.review.json').write_bytes((json.dumps(review,indent=2)+'\n').encode())
    return document,review


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--site-url',required=True);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();_,r=build_package(args.output,args.site_url)
    print(json.dumps(r,indent=2))
