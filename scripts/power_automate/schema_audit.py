"""Read-only issue-66 inspection package and local analysis; never a cloud runtime."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
from tempfile import TemporaryDirectory
from xml.etree import ElementTree as ET
from zipfile import ZIP_DEFLATED, ZipFile

try:
    from .build_import_probe import build_package as build_probe
except ImportError:
    from build_import_probe import build_package as build_probe

FLOW_NAME = 'TandemSchemaAudit'
ALL = ['Succeeded', 'Failed', 'Skipped', 'TimedOut']
FIELD_SELECT = 'Id,Title,InternalName,TypeAsString,Required,Hidden,ReadOnlyField,EnforceUniqueValues,Indexed,DefaultValue,SchemaXml'
ROLES = {'Participants':'participants', 'Language catalogue':'language', 'Culture catalogue':'culture', 'Time zone catalogue':'timezone'}
KEYS = {'language':'ISOCode', 'culture':'CultureKey', 'timezone':'IANAId'}
LOOKUPS = {'language':['TeachLanguages','LearnLanguages'], 'culture':['ShareCultures','LearnCultures'], 'timezone':['TimeZone']}


def normalize(value):
    return re.sub(r'[\s_]', '', re.sub('_x0020_', '', str(value or ''), flags=re.I)).casefold()


def expected_schema(root=None):
    root = Path(root) if root else Path(__file__).resolve().parents[2]
    schema = deepcopy(json.loads((root/'config/sharepoint_schema.json').read_text(encoding='utf-8')))
    people = next(x for x in schema['lists'] if x['name']=='Participants')
    people['fields'] += [
        {'internalName':'ParticipationStatus','displayName':'Participation status','type':'Choice','required':True,
         'choices':['Active','Paused','Inactive'],'defaultValue':'Active'},
        {'internalName':'OpenToConnections','displayName':'Open to new connections','type':'Boolean','required':True,'defaultValue':True},
    ]
    return schema


def wdl_string(value):
    return "'"+str(value).replace("'", "''")+"'"


def normalized_expr(property_name):
    return f"replace(replace(replace(toLower(string(item()?['{property_name}'])), '_x0020_', ''), ' ', ''), '_', '')"


def match_expr(aliases):
    values='createArray('+', '.join(wdl_string(normalize(x)) for x in aliases)+')'
    return f"or(contains({values}, {normalized_expr('InternalName')}), contains({values}, {normalized_expr('Title')}))"


def query(source, expression, after):
    return {'type':'Query','inputs':{'from':source,'where':'@'+expression},'runAfter':{after:['Succeeded']}}


def get(site, uri, after=None):
    return {'type':'OpenApiConnection','inputs':{
        'parameters':{'dataset':site,'parameters/method':'GET','parameters/uri':uri,
                      'parameters/headers':{'Accept':'application/json;odata=nometadata'}},
        'host':{'apiId':'/providers/Microsoft.PowerApps/apis/shared_sharepointonline',
                'connectionName':'shared_sharepointonline','operationId':'HttpRequest'},
        'authentication':"@parameters('$authentication')"},
        'runAfter':{after:['Succeeded']} if after else {}}


def select(source, projection, after):
    return {'type':'Select','inputs':{'from':source,'select':projection},'runAfter':{after:['Succeeded']}}


def append(name, value, after=None):
    return {'type':'AppendToArrayVariable','inputs':{'name':name,'value':value},
            'runAfter':{after:['Succeeded']} if after else {}}


def field_projection():
    return {
        'id':"@item()?['Id']",'internalName':"@item()?['InternalName']",'displayName':"@item()?['Title']",
        'type':"@item()?['TypeAsString']",'required':"@item()?['Required']",'unique':"@item()?['EnforceUniqueValues']",
        'indexed':"@item()?['Indexed']",'hidden':"@item()?['Hidden']",'readOnly':"@item()?['ReadOnlyField']",
        'defaultValue':"@if(contains(createArray('Boolean','Choice'),item()?['TypeAsString']),item()?['DefaultValue'],null)",
        'schemaXml':"@if(contains(createArray('Lookup','LookupMulti','Choice','MultiChoice'),item()?['TypeAsString']),item()?['SchemaXml'],null)",
    }


def more(action):
    return f"@not(empty(coalesce(body('{action}')?['@odata.nextLink'],body('{action}')?['odata.nextLink'],'')))"


def definition(site, schema, build_id):
    actions={
        'Initialize_lists':{'type':'InitializeVariable','inputs':{'variables':[{'name':'AuditLists','type':'array','value':[]}]},'runAfter':{}},
        'Initialize_errors':{'type':'InitializeVariable','inputs':{'variables':[{'name':'AuditErrors','type':'array','value':[]}]},'runAfter':{'Initialize_lists':['Succeeded']}},
    }
    specs={ROLES[x['name']]:x for x in schema['lists']}
    field_aliases=lambda role:[v for f in specs[role]['fields'] for v in [f['internalName'],f.get('displayName',f['internalName'])]]
    base="_api/web/lists/getbytitle('Participants')"
    p={
        'Read_participant_list':get(site,base+'?$select=Id,Title'),
        'Read_participant_fields':get(site,base+'/fields?$select='+FIELD_SELECT+'&$top=5000','Read_participant_list'),
    }
    p['Filter_participant_fields']=query("@body('Read_participant_fields')?['value']",match_expr(field_aliases('participants')),'Read_participant_fields')
    p['Select_participant_fields']=select("@body('Filter_participant_fields')",field_projection(),'Filter_participant_fields')
    p['Participant_column_index']=select("@body('Read_participant_fields')?['value']",{
        'id':"@item()?['Id']",'internalName':"@item()?['InternalName']",'displayName':"@item()?['Title']",'type':"@item()?['TypeAsString']"},'Select_participant_fields')
    p['Record_participant_schema']=append('AuditLists',{
        'role':'participants','id':"@body('Read_participant_list')?['Id']",'title':"@body('Read_participant_list')?['Title']",
        'fields':"@body('Select_participant_fields')",'columnIndex':"@body('Participant_column_index')",
        'fieldsTruncated':more('Read_participant_fields'),'valuesTruncated':False,'values':[]},'Participant_column_index')
    actions['Inspect_participants']={'type':'Scope','actions':p,'runAfter':{'Initialize_errors':['Succeeded']}}
    actions['Participant_failure']=append('AuditErrors',{'role':'participants','code':'METADATA_READ_FAILED','message':'Participant metadata could not be read. Inspect the failed read action; no data or schema was changed.'})
    actions['Participant_failure']['runAfter']={'Inspect_participants':['Failed','TimedOut']}
    previous='Participant_failure'
    for role in ['language','culture','timezone']:
        find='Find_'+role+'_lookup'; scope='Inspect_'+role
        lookups=match_expr(LOOKUPS[role])
        q=query("@coalesce(body('Read_participant_fields')?['value'],json('[]'))",
            "and(contains(createArray('Lookup','LookupMulti'),item()?['TypeAsString']),"+lookups+')',None)
        q['runAfter']={}
        inside={find:q}
        cid='Catalogue_id_'+role
        fieldxml=f"first(body('{find}'))?['SchemaXml']"
        xpath=wdl_string('string(/*[local-name()="Field"]/@List)')
        yes={cid:{'type':'Compose','inputs':f"@replace(replace(string(xpath(xml({fieldxml}),{xpath})),'{{',''),'}}','')",'runAfter':{}}}
        meta='Read_'+role+'_list'; fields='Read_'+role+'_fields'; filtered='Filter_'+role+'_fields'
        chosen='Select_'+role+'_fields'; index='Index_'+role+'_columns'; key='Find_'+role+'_key'; active='Find_'+role+'_active'
        values='Read_'+role+'_values'; selected='Select_'+role+'_values'
        prefix="_api/web/lists(guid'"
        uri=lambda suffix:'@concat('+wdl_string(prefix)+f",outputs('{cid}'),"+wdl_string("')"+suffix)+')'
        reads={meta:get(site,uri('?$select=Id,Title')),
               fields:get(site,uri('/fields?$select='+FIELD_SELECT+'&$top=5000'),meta)}
        reads[filtered]=query(f"@body('{fields}')?['value']",match_expr(field_aliases(role)),fields)
        reads[chosen]=select(f"@body('{filtered}')",field_projection(),filtered)
        reads[index]=select(f"@body('{fields}')?['value']",{'internalName':"@item()?['InternalName']",'displayName':"@item()?['Title']",'type':"@item()?['TypeAsString']"},chosen)
        key_spec=next(f for f in specs[role]['fields'] if f['internalName']==KEYS[role])
        reads[key]=query(f"@body('{fields}')?['value']",match_expr([KEYS[role],key_spec['displayName']]),index)
        reads[active]=query(f"@body('{fields}')?['value']",match_expr(['Active']),key)
        values_uri='@concat('+wdl_string(prefix)+f",outputs('{cid}'),"+wdl_string("')/items?$select=Id,Title,")+f",first(body('{key}'))?['InternalName'],',',first(body('{active}'))?['InternalName'],'&$top=5000')"
        yes_values={values:get(site,values_uri)}
        yes_values[selected]=select(f"@body('{values}')?['value']",{
            'id':"@item()?['Id']",'title':"@item()?['Title']",
            'key':f"@item()?[first(body('{key}'))?['InternalName']]",
            'active':f"@item()?[first(body('{active}'))?['InternalName']]"},values)
        condition='Catalogue_columns_'+role
        reads[condition]={'type':'If','expression':{'and':[
            {'equals':[f"@length(body('{key}'))",1]}, {'equals':[f"@length(body('{active}'))",1]},
            {'not':{'equals':[f"@first(union(body('{key}'),createArray(json('{{}}'))))?['InternalName']",'Title']}}]},
            'actions':yes_values,'else':{'actions':{'Missing_'+role+'_columns':append('AuditErrors',{'role':role,'code':'CATALOGUE_COLUMNS_UNRESOLVED','message':'Key/Active columns are missing, ambiguous, or key aliases the Title field. Metadata is returned for mapping; catalogue rows were not read.'})}},
            'runAfter':{active:['Succeeded']}}
        reads['Record_'+role]=append('AuditLists',{
            'role':role,'id':f"@body('{meta}')?['Id']",'title':f"@body('{meta}')?['Title']",
            'fields':f"@body('{chosen}')",'columnIndex':f"@body('{index}')",
            'fieldsTruncated':more(fields),'valuesTruncated':more(values),
            'values':f"@coalesce(body('{selected}'),json('[]'))"},condition)
        gate='Safe_catalogue_'+role
        yes[gate]={'type':'If','expression':{'and':[
            {'equals':[f"@length(outputs('{cid}'))",36]},
            {'not':{'equals':[f"@toLower(outputs('{cid}'))","@toLower(string(body('Read_participant_list')?['Id']))"]}}]},
            'actions':reads,'else':{'actions':{'Unsafe_'+role+'_target':append('AuditErrors',{'role':role,'code':'CATALOGUE_TARGET_UNSAFE','message':'Lookup target is not a GUID or points to Participants; no catalogue-row read attempted.'})}},'runAfter':{cid:['Succeeded']}}
        condition_found='Has_'+role+'_lookup'
        inside[condition_found]={'type':'If','expression':{'greater':[f"@length(body('{find}'))",0]},'actions':yes,
            'else':{'actions':{'No_'+role+'_lookup':append('AuditErrors',{'role':role,'code':'LOOKUP_TARGET_UNRESOLVED','message':'No recognized participant lookup target. Participant column index is returned for mapping; no guessed list read.'})}},'runAfter':{find:['Succeeded']}}
        actions[scope]={'type':'Scope','actions':inside,'runAfter':{previous:ALL}}
        failure=role+'_failure';actions[failure]=append('AuditErrors',{'role':role,'code':'METADATA_READ_FAILED','message':'Catalogue inspection failed. Inspect the failed action; no data or schema was changed.'})
        actions[failure]['runAfter']={scope:['Failed','TimedOut']};previous=failure
    actions['Find_truncated_lists']=query("@variables('AuditLists')","or(equals(item()?['fieldsTruncated'],true),equals(item()?['valuesTruncated'],true))",previous)
    actions['Find_truncated_lists']['runAfter']={previous:ALL}
    complete="@and(equals(length(variables('AuditLists')),4),empty(variables('AuditErrors')),empty(body('Find_truncated_lists')))"
    actions['Audit_report']={'type':'Compose','inputs':{
        'kind':FLOW_NAME,'schemaVersion':1,'packageBuildId':build_id,'readOnly':True,'sourceTicket':66,
        'runReference':"@workflow()?['run']?['name']",'collectionComplete':complete,
        'writeCapability':'NOT_VERIFIED_NO_WRITES','lists':"@variables('AuditLists')",'errors':"@variables('AuditErrors')"},
        'runAfter':{'Find_truncated_lists':['Succeeded']}}
    actions['Respond_to_a_Power_App_or_flow']={'type':'Response','kind':'PowerApp','inputs':{
        'statusCode':200,'schema':{'type':'object','properties':{
            'success':{'title':'success','type':'boolean','x-ms-content-hint':'BOOLEAN','x-ms-dynamically-added':True},
            'message':{'title':'message','type':'string','x-ms-content-hint':'TEXT','x-ms-dynamically-added':True},
            'reportjson':{'title':'reportjson','type':'string','x-ms-content-hint':'TEXT','x-ms-dynamically-added':True}},'additionalProperties':{}},
        'body':{'success':complete,'message':"@if(outputs('Audit_report')?['collectionComplete'],'SCHEMA_METADATA_COLLECTED','SCHEMA_METADATA_INCOMPLETE')",
                'reportjson':"@string(outputs('Audit_report'))"}},'runAfter':{'Audit_report':['Succeeded']}}
    return actions


def measure(actions):
    count=0;depth=0;names=set();all_actions=[]
    def visit(block,level):
        nonlocal count,depth
        for name,action in block.items():
            if name in names:raise ValueError('Duplicate action '+name)
            names.add(name);count+=1;depth=max(depth,level);all_actions.append((name,action,block))
            visit(action.get('actions',{}),level+1)
            visit(action.get('else',{}).get('actions',{}),level+1)
            for case in action.get('cases',{}).values():visit(case.get('actions',{}),level+1)
            visit(action.get('default',{}).get('actions',{}),level+1)
    visit(actions,1)
    for name,action,siblings in all_actions:
        if set(action.get('runAfter',{}))-set(siblings):raise ValueError('Non-sibling runAfter '+name)
        payload=json.dumps(action.get('inputs',{}))+' '+json.dumps(action.get('expression',{}))
        for target in re.findall(r"(?:body|outputs|actions|items)\('([^']+)'\)",payload):
            if target not in names:raise ValueError('Missing action reference '+target)
    if count>500 or depth>8:raise ValueError(f'Flow exceeds limit: {count} actions, depth {depth}')
    return {'actions':count,'maximumActionDepth':depth}


def build_package(output, site, root=None):
    output=Path(output)
    if any(p.exists() for p in [output,output.with_suffix('.definition.json'),output.with_suffix('.review.json')]):raise FileExistsError(output)
    schema=expected_schema(root)
    with TemporaryDirectory(prefix='tandem-schema-envelope-') as tmp:
        base=Path(tmp)/'base.zip';document=build_probe(base,sharepoint_site=site)
        with ZipFile(base) as archive:entries={n:json.loads(archive.read(n)) for n in archive.namelist()}
    document['properties']['displayName']=FLOW_NAME
    document['properties']['definition']['actions']=definition(site,schema,document['name'])
    metrics=measure(document['properties']['definition']['actions'])
    for name in entries:
        if name.endswith('/definition.json'):entries[name]=document
    manifest=entries['manifest.json'];manifest['details']['displayName']=FLOW_NAME+'-package'
    manifest['details']['description']='Issue 66 disposable read-only field/catalogue inspection. No participant-row reads, schema/data writes or permission changes.'
    flow=next(v for v in manifest['resources'].values() if v['type']=='Microsoft.Flow/flows')
    flow['details']['displayName']=FLOW_NAME
    output.parent.mkdir(parents=True,exist_ok=True)
    with ZipFile(output,'x',ZIP_DEFLATED) as archive:
        for name,value in entries.items():archive.writestr(name,json.dumps(value,indent=2)+'\n')
    output.with_suffix('.definition.json').write_bytes((json.dumps(document,indent=2)+'\n').encode('utf-8'))
    review={'ticket':66,'flowName':FLOW_NAME,'packageBuildId':document['name'],'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),
        **metrics,'limits':{'actions':500,'nesting':8},'readOnly':True,'productionFlow':False,
        'connection':'Existing owner SharePoint connection; embedded only for disposable metadata inspection',
        'dataScope':'Field metadata; lookup-resolved catalogue Id/Title/key/Active only. No participant rows.',
        'catalogueBound':5000,'truncation':'Explicit incomplete result, never silent success',
        'tenantImportAndRun':'NOT RUN','scopeBoundary':'SCHEMA-001 inspector only. Full #66 alignment and SCHEMA-002 require observed mapping and verified repair capability.'}
    output.with_suffix('.review.json').write_bytes((json.dumps(review,indent=2)+'\n').encode('utf-8'))
    return document,review


def unwrap(value):
    for _ in range(5):
        if isinstance(value,str):value=json.loads(value)
        if not isinstance(value,dict):raise ValueError('Expected report object')
        if value.get('kind')==FLOW_NAME:return value
        if 'reportjson' in value:value=value['reportjson']
        elif 'body' in value:value=value['body']
        elif 'inputs' in value:value=value['inputs']
        else:raise ValueError('No schema audit report found')
    raise ValueError('Report envelope nesting too deep')


def analyze(value, root=None):
    report=unwrap(value)
    if report.get('schemaVersion')!=1 or report.get('readOnly') is not True:raise ValueError('Unsupported audit report')
    lists=report.get('lists')
    if not isinstance(lists,list):raise ValueError('Missing lists array')
    by_role={};findings=[];mapping={}
    def note(code,role,field,expected,actual,blocked=False):
        findings.append(dict(code=code,role=role,field=field,expected=expected,actual=actual,blocked=blocked))
    for item in lists:
        role=item.get('role')
        if role in by_role:note('AMBIGUOUS_LIST',role,None,'one list per role','multiple',True)
        by_role[role]=item
    if report.get('collectionComplete') is not True:note('INCOMPLETE_COLLECTION',None,None,True,False,True)
    if report.get('errors'):note('COLLECTION_ERRORS',None,None,[],report['errors'],True)
    for spec in expected_schema(root)['lists']:
        role=ROLES[spec['name']];actual=by_role.get(role)
        if not actual:note('MISSING_LIST_REPORT',role,None,spec['name'],None,True);continue
        if actual.get('fieldsTruncated') or actual.get('valuesTruncated'):note('TRUNCATED',role,None,False,True,True)
        fields=actual.get('fields',[]);used=set();mapping[role]={'listId':actual.get('id'),'listTitle':actual.get('title'),'fields':{}}
        for want in spec['fields']:
            name=want['internalName'];aliases={normalize(name),normalize(want.get('displayName',name))}
            candidates=[f for f in fields if f.get('type') != 'Computed' and (normalize(f.get('internalName')) in aliases or normalize(f.get('displayName')) in aliases)]
            if not candidates and role=='timezone' and name=='WindowsId':
                continue  # Optional conversion metadata; current MVP uses IANA catalogue IDs.
            if len(candidates)!=1:
                note('MISSING_FIELD' if not candidates else 'AMBIGUOUS_FIELD',role,name,'one mapped field',[f.get('internalName') for f in candidates],bool(candidates));continue
            f=candidates[0];internal=f['internalName']
            if internal in used:note('REUSED_FIELD',role,name,'separate logical fields',internal,True)
            used.add(internal);mapping[role]['fields'][name]={'internalName':internal,'id':f.get('id'),'type':f.get('type')}
            kind=want['type']+'Multi' if want.get('allowMultiple') else want['type']
            if f.get('type')!=kind:note('FIELD_TYPE',role,name,kind,f.get('type'))
            checks={'required':want.get('required',False)}
            if want.get('unique'):checks['unique']=True
            if name in spec.get('indexes',[]):checks['indexed']=True
            for prop,expected in checks.items():
                if f.get(prop) is not expected:note('FIELD_'+prop.upper(),role,name,expected,f.get(prop))
            if 'defaultValue' in want:
                expected=want['defaultValue'];value=f.get('defaultValue')
                if isinstance(expected,bool):value=True if str(value).casefold() in ['1','true','yes'] else False if str(value).casefold() in ['0','false','no'] else value
                if value!=expected:note('FIELD_DEFAULT',role,name,expected,value)
            xml=None
            if want['type'] in ['Choice','Lookup']:
                try:xml=ET.fromstring(f.get('schemaXml') or '')
                except ET.ParseError:note('FIELD_XML',role,name,'valid field metadata XML',None,True)
            if want.get('choices') and xml is not None:
                choices=[n.text or '' for n in xml.iter() if n.tag.split('}')[-1]=='CHOICE']
                valid_choices = set(want['choices']) <= set(choices) if role=='participants' and name=='Status' else set(choices)==set(want['choices'])
                if not valid_choices:note('FIELD_CHOICES',role,name,want['choices'],choices)
            if want.get('lookupList') and xml is not None:
                target=by_role.get(ROLES[want['lookupList']],{}).get('id')
                observed=xml.attrib.get('List','').strip('{}').casefold()
                if not target:note('LOOKUP_TARGET_UNKNOWN',role,name,want['lookupList'],observed,True)
                elif observed!=str(target).strip('{}').casefold():note('LOOKUP_TARGET',role,name,str(target),observed)
                allowed_display={want.get('lookupField','Title')}
                if role=='participants' and name=='TimeZone':
                    allowed_display.update(x['internalName'] for x in by_role.get('timezone',{}).get('fields',[]) if normalize(x.get('internalName'))==normalize('IANAId'))
                mapping[role]['fields'][name]['lookupDisplayField']=xml.attrib.get('ShowField')
                if xml.attrib.get('ShowField') not in allowed_display:note('LOOKUP_DISPLAY',role,name,sorted(allowed_display),xml.attrib.get('ShowField'))
        if role!='participants':
            seen=set()
            for row in actual.get('values',[]):
                if not isinstance(row.get('active'),bool):note('CATALOGUE_ACTIVE',role,None,'Boolean',row.get('active'))
                key=row.get('key')
                if key is None or not str(key).strip():note('CATALOGUE_KEY_EMPTY',role,None,'nonempty key',row.get('id'))
                norm=str(key).strip().casefold()
                if norm in seen:note('CATALOGUE_KEY_DUPLICATE',role,None,'unique key',key)
                seen.add(norm)
    status='Blocked' if any(x['blocked'] for x in findings) else 'Needs change' if findings else 'Verified'
    return {'sourceTicket':66,'packageBuildId':report.get('packageBuildId'),'runReference':report.get('runReference'),
            'status':status,'mapping':mapping,'findings':findings,'changesApplied':False,
            'nextStep':'Prepare only a concrete approved delta after mapping/capability review; no write is authorized by this local report alone.' if findings else 'Record SCHEMA-001 evidence; verify SCHEMA-002 alignment/repeat and remaining setup evidence before closing #66.'}
