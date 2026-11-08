"""#12 disposable metadata-only group/member inspector; local packaging only."""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED,ZipFile
from .build_import_probe import build_package as envelope
from .build_coordination_preflight import SITE
from .schema_audit import ALL,FIELD_SELECT,get,measure,query,select,append,wdl_string

NAME='TandemGroupSchemaAudit'
ROOT=Path(__file__).resolve().parents[2]


def compose(value,previous=None):
    return {'type':'Compose','inputs':value,'runAfter':{previous:['Succeeded']} if previous else {}}


def complete(action):
    return "and(not(equals(body('"+action+"')?['value'],null)),empty(coalesce(body('"+action+"')?['@odata.nextLink'],body('"+action+"')?['odata.nextLink'],'')))"


def actions(site,build_id,mapping):
    a={}
    previous=None
    for name in ['AuditLists','AuditErrors','ReferenceLists']:
        key='Initialize_'+name
        a[key]={'type':'InitializeVariable','inputs':{'variables':[{'name':name,'type':'array','value':[]}]},'runAfter':{previous:['Succeeded']} if previous else {}}
        previous=key
    a['Read_list_index']=get(site,'_api/web/lists?$select=Id,Title,BaseTemplate,Hidden,ItemCount&$top=5000',previous)
    a['Read_list_index']['runAfter']={previous:['Succeeded']}
    a['List_index_status']=compose({'complete':'@'+complete('Read_list_index')},'Read_list_index')
    a['List_index_status']['runAfter']={'Read_list_index':ALL}
    previous='List_index_status'
    for role in ['participants','language','culture']:
        spec=mapping['lists'][role];key='Inspect_reference_'+role;read='Read_reference_'+role
        uri="_api/web/lists(guid'"+spec['listId']+"')?$select=Id,Title,BaseTemplate"
        inside={read:get(site,uri)}
        inside['Require_reference_'+role]={'type':'If','expression':"@and(equals(body('"+read+"')?['Id'],"+wdl_string(spec['listId'])+"),equals(body('"+read+"')?['BaseTemplate'],100),not(empty(body('"+read+"')?['Title'])))",
          'actions':{'Record_reference_'+role:append('ReferenceLists',{'role':role,'id':"@body('"+read+"')?['Id']",'title':"@body('"+read+"')?['Title']",'baseTemplate':"@body('"+read+"')?['BaseTemplate']"})},
          'else':{'actions':{'Invalid_reference_'+role:append('AuditErrors',{'role':role,'code':'REFERENCE_IDENTITY_INVALID'})}},'runAfter':{read:['Succeeded']}}
        a[key]={'type':'Scope','actions':inside,'runAfter':{previous:ALL}}
        fail='Reference_failure_'+role
        a[fail]=append('AuditErrors',{'role':role,'code':'REFERENCE_METADATA_READ_FAILED','message':'Known catalogue/participant list identity could not be read; no rows read or changes made.'})
        a[fail]['runAfter']={key:['Failed','TimedOut']};previous=fail
    for role,title in [('groups','groups'),('members','groupmembers')]:
        scope='Inspect_'+role;find='Find_'+role;meta='Read_'+role+'_list';fields='Read_'+role+'_fields';permissions='Read_'+role+'_permissions'
        choose='Choose_'+role;cid='Id_'+role;filtered='Filter_'+role+'_fields';project='Select_'+role+'_fields';index='Index_'+role
        predicate="and(equals(replace(replace(toLower(string(item()?['Title'])),' ',''),'_',''),"+wdl_string(title)+"),equals(item()?['BaseTemplate'],100))"
        inside={find:query("@coalesce(body('Read_list_index')?['value'],json('[]'))",predicate,None)}
        inside[find]['runAfter']={}
        yes={cid:compose("@first(body('"+find+"'))?['Id']")}
        def uri(suffix):return "@concat('_api/web/lists(guid''',outputs('"+cid+"'),''')"+suffix+"')"
        yes[meta]=get(site,uri('?$select=Id,Title,BaseTemplate,ItemCount,ValidationFormula,ValidationMessage'),cid)
        yes[fields]=get(site,uri('/fields?$select='+FIELD_SELECT+',FromBaseType&$top=5000'),meta)
        yes[permissions]=get(site,uri('/EffectiveBasePermissions'),fields)
        yes[filtered]=query("@coalesce(body('"+fields+"')?['value'],json('[]'))","or(equals(item()?['InternalName'],'Title'),equals(item()?['FromBaseType'],false))",permissions)
        projection={'id':"@item()?['Id']",'internalName':"@item()?['InternalName']",'displayName':"@item()?['Title']",'type':"@item()?['TypeAsString']",
          'required':"@item()?['Required']",'unique':"@item()?['EnforceUniqueValues']",'indexed':"@item()?['Indexed']",'hidden':"@item()?['Hidden']",'readOnly':"@item()?['ReadOnlyField']",
          'defaultValue':"@item()?['DefaultValue']",'schemaXml':"@item()?['SchemaXml']"}
        yes[project]=select("@body('"+filtered+"')",projection,filtered)
        yes[index]=select("@coalesce(body('"+fields+"')?['value'],json('[]'))",{k:projection[k] for k in ['id','internalName','displayName','type']},project)
        yes['Record_'+role]=append('AuditLists',{'role':role,'id':"@body('"+meta+"')?['Id']",'title':"@body('"+meta+"')?['Title']",'baseTemplate':"@body('"+meta+"')?['BaseTemplate']",
          'itemCount':"@body('"+meta+"')?['ItemCount']",'validationFormula':"@body('"+meta+"')?['ValidationFormula']",'validationMessage':"@body('"+meta+"')?['ValidationMessage']",
          'fields':"@body('"+project+"')",'columnIndex':"@body('"+index+"')",'fieldsComplete':'@'+complete(fields),
          'metadataComplete':"@and(equals(body('"+meta+"')?['Id'],outputs('"+cid+"')),equals(body('"+meta+"')?['BaseTemplate'],100),not(empty(body('"+meta+"')?['Title'])),not(equals(coalesce(body('"+permissions+"')?['High'],body('"+permissions+"')?['EffectiveBasePermissions']?['High']),null)),not(equals(coalesce(body('"+permissions+"')?['Low'],body('"+permissions+"')?['EffectiveBasePermissions']?['Low']),null)))",
          'permissionEvidence':{'High':"@coalesce(body('"+permissions+"')?['High'],body('"+permissions+"')?['EffectiveBasePermissions']?['High'])",
            'Low':"@coalesce(body('"+permissions+"')?['Low'],body('"+permissions+"')?['EffectiveBasePermissions']?['Low'])"}},index)
        inside[choose]={'type':'If','expression':"@and(equals(length(body('"+find+"')),1),outputs('List_index_status')?['complete'])",
          'actions':yes,'else':{'actions':{'Unresolved_'+role:append('AuditErrors',{'role':role,'code':'LIST_MISSING_AMBIGUOUS_OR_UNSAFE','message':'Expected exactly one ordinary list with normalized title Groups or Group Members; inspect listCandidates. No guessed target read.'})}},'runAfter':{find:['Succeeded']}}
        a[scope]={'type':'Scope','actions':inside,'runAfter':{previous:ALL}}
        failure='Failure_'+role;a[failure]=append('AuditErrors',{'role':role,'code':'LIST_METADATA_READ_FAILED','message':'Inspect failed metadata action; no item reads, schema/data writes or permission changes.'})
        a[failure]['runAfter']={scope:['Failed','TimedOut']};previous=failure
    a['Incomplete_fields']=query("@variables('AuditLists')","or(not(equals(item()?['fieldsComplete'],true)),not(equals(item()?['metadataComplete'],true)))",previous)
    a['Incomplete_fields']['runAfter']={previous:ALL}
    a['Audit_report']=compose({'kind':NAME,'schemaVersion':1,'sourceTicket':12,'packageBuildId':build_id,
      'runReference':"@workflow()?['run']?['name']",'readOnly':True,'rowReads':0,'writes':0,
      'collectionComplete':"@and(outputs('List_index_status')?['complete'],equals(length(variables('AuditLists')),2),equals(length(variables('ReferenceLists')),3),empty(variables('AuditErrors')),empty(body('Incomplete_fields')))",
      'schemaVerified':False,'writeCapability':'NOT_VERIFIED_NO_WRITES','lists':"@variables('AuditLists')",'referenceLists':"@variables('ReferenceLists')",
      'listCandidates':"@coalesce(body('Read_list_index')?['value'],json('[]'))",'errors':"@variables('AuditErrors')",
      'nextStep':'Review actual field mapping, lookup targets, choices/defaults/precision/validation and list permissions. No uniqueness runtime proof, row integrity/migration pass or approved setup correction inferred.'},'Incomplete_fields')
    measure(a);return a


def build_package(output,site=SITE):
    output=Path(output)
    if any(p.exists() for p in [output,output.with_suffix('.definition.json'),output.with_suffix('.review.json')]):raise FileExistsError(output)
    mapping=json.loads((ROOT/'config/tenant_schema_mapping.json').read_text(encoding='utf-8'))
    with TemporaryDirectory() as temp:
        base=Path(temp)/'base.zip';doc=envelope(base,sharepoint_site=site)
        with ZipFile(base) as z:entries={n:json.loads(z.read(n)) for n in z.namelist()}
    doc['properties']['displayName']=NAME
    doc['properties']['definition']['actions']=actions(site,doc['name'],mapping)
    for n in entries:
        if n.endswith('/definition.json'):entries[n]=doc
    entries['manifest.json']['details'].update(displayName=NAME+'-package',description='Issue 12 metadata only: list identity, fields and effective list permissions; no item reads, writes or changes.')
    for item in entries['manifest.json']['resources'].values():
        if item['type']=='Microsoft.Flow/flows':item['details']['displayName']=NAME
    output.parent.mkdir(parents=True,exist_ok=True)
    with ZipFile(output,'x',ZIP_DEFLATED) as z:
        for n,obj in entries.items():z.writestr(n,json.dumps(obj,indent=2)+'\n')
    review={'sourceTicket':12,'flowName':NAME,'packageBuildId':doc['name'],**measure(doc['properties']['definition']['actions']),
      'limits':{'actions':500,'nesting':8},'readOnly':True,'rowReads':0,'writes':0,'schemaVerified':False,
      'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'tenantResult':'NOT_IMPORTED_NOT_TESTED',
      'scope':'List metadata inventory; Groups/Group Members field and effective list permission metadata; known participant/language/culture list identities. No items, principals/ACLs or permission writes.',
      'truncation':'Fail incomplete for any next link, missing array, missing/ambiguous role or failed read. No silent first-page success.',
      'connection':'Existing working owner SharePoint connection only; no ordinary-user access or change capability inferred.'}
    output.with_suffix('.definition.json').write_bytes((json.dumps(doc,indent=2)+'\n').encode('utf-8'))
    output.with_suffix('.review.json').write_bytes((json.dumps(review,indent=2)+'\n').encode('utf-8'))
    return review


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    print(json.dumps(build_package(args.output),indent=2))


if __name__=='__main__':main()
