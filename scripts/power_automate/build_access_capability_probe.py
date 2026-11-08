"""#39 metadata-only two-connection capability experiment; no access cutover."""
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4
from zipfile import ZipFile,ZIP_DEFLATED
import argparse,hashlib,json
from .build_import_probe import build_package as envelope
from .schema_audit import measure,ALL

ROOT=Path(__file__).resolve().parents[2]
NAME='TandemAccessCapabilityProbe'
CALLER='shared_sharepointonline';BACKEND='shared_sharepointonline_backend'


def after(n):return {n:['Succeeded']} if n else {}
def compose(v,n=None):return {'type':'Compose','inputs':v,'runAfter':after(n)}
def body(n):return "body('"+n+"')?['d']"
def complete(n):return "and(not(equals("+body(n)+"?['results'],null)),empty("+body(n)+"?['__next']))"


def actions(site,build_id,caller_auth,mapping):
    people=mapping['lists']['participants'];field=people['fields']['ParticipantAccount']
    base="_api/web/lists(guid'"+people['listId']+"')"
    def http(n,uri,prev=None):return {'type':'OpenApiConnection','runAfter':after(prev),'inputs':{'parameters':{
      'dataset':site,'parameters/method':'GET','parameters/uri':uri,'parameters/headers':{'Accept':'application/json;odata=verbose'}},
      'host':{'apiId':'/providers/Microsoft.PowerApps/apis/shared_sharepointonline','connectionName':n,'operationId':'HttpRequest'},
      'authentication':deepcopy(caller_auth) if n==CALLER else "@parameters('$authentication')"}}
    def identity(n,prev):return {'type':'ParseJson','runAfter':after(prev),'inputs':{'content':'@'+body(prev),'schema':{
      'type':'object','required':['Id'],'properties':{'Id':{'type':'integer','minimum':1}}}}}
    caller={'Read_caller_identity':http(CALLER,'_api/web/currentuser?$select=Id')}
    caller['Caller_identity']=identity('Caller_identity','Read_caller_identity')
    backend={'Read_backend_identity':http(BACKEND,'_api/web/currentuser?$select=Id')}
    backend['Backend_identity']=identity('Backend_identity','Read_backend_identity')
    backend['Read_participant_list']=http(BACKEND,base+'?$select=Id,Title,BaseTemplate,ItemCount,HasUniqueRoleAssignments,ReadSecurity,WriteSecurity','Backend_identity')
    backend['Read_identity_field']=http(BACKEND,base+"/fields(guid'"+field['id']+"')?$select=Id,InternalName,TypeAsString,Required,Indexed,EnforceUniqueValues",'Read_participant_list')
    backend['Read_list_permissions']=http(BACKEND,base+'/EffectiveBasePermissions','Read_identity_field')
    backend['Read_role_definitions']=http(BACKEND,'_api/web/roledefinitions?$select=Id,Name,RoleTypeKind,BasePermissions&$top=5000','Read_list_permissions')
    backend['Read_list_role_bindings']=http(BACKEND,base+'/roleassignments?$select=Member/Id,Member/PrincipalType,RoleDefinitionBindings/Id,RoleDefinitionBindings/RoleTypeKind&$expand=Member,RoleDefinitionBindings&$top=5000','Read_role_definitions')
    low="coalesce("+body('Read_list_permissions')+"?['Low'],"+body('Read_list_permissions')+"?['EffectiveBasePermissions']?['Low'],'0')"
    backend['Backend_permission_flags']=compose({key:'@equals(mod(div(int('+low+'),'+str(bit)+'),2),1)' for key,bit in [('viewItems',1),('manageLists',2048),('managePermissions',33554432)]},'Read_list_role_bindings')
    a={'Caller_path':{'type':'Scope','actions':caller,'runAfter':{}},
      'Backend_path':{'type':'Scope','actions':backend,'runAfter':{'Caller_path':ALL}}}
    a['Capabilities_collected']=compose('@and('+','.join([
      "equals(actions('Caller_path')?['status'],'Succeeded')","equals(actions('Backend_path')?['status'],'Succeeded')",
      "equals("+body('Read_participant_list')+"?['Id'],'"+people['listId']+"')","equals("+body('Read_participant_list')+"?['BaseTemplate'],100)",
      "equals("+body('Read_identity_field')+"?['Id'],'"+field['id']+"')","equals("+body('Read_identity_field')+"?['InternalName'],'"+field['internalName']+"')",
      "equals("+body('Read_identity_field')+"?['TypeAsString'],'User')","equals("+body('Read_identity_field')+"?['EnforceUniqueValues'],true)",
      "equals("+body('Read_identity_field')+"?['Required'],true)","equals("+body('Read_identity_field')+"?['Indexed'],true)",
      "not(equals("+body('Read_participant_list')+"?['ReadSecurity'],null))","not(equals("+body('Read_participant_list')+"?['WriteSecurity'],null))",
      "not(equals("+body('Read_participant_list')+"?['HasUniqueRoleAssignments'],null))",
      "not(equals(coalesce("+body('Read_list_permissions')+"?['Low'],"+body('Read_list_permissions')+"?['EffectiveBasePermissions']?['Low']),null))",complete('Read_role_definitions'),complete('Read_list_role_bindings')])+')')
    a['Capabilities_collected']['runAfter']={'Backend_path':ALL}
    a['Capability_report']=compose({'kind':NAME,'schemaVersion':1,'sourceTicket':39,'packageBuildId':build_id,'runReference':"@workflow()?['run']?['name']",
      'readOnly':True,'itemRowsRead':0,'writes':0,'metadataComplete':"@outputs('Capabilities_collected')",
      'result':"@if(outputs('Capabilities_collected'),'CAPABILITY_METADATA_COLLECTED','CAPABILITY_METADATA_INCOMPLETE')",
      'connectionPathStatus':{role:"@actions('"+name+"')?['status']" for role,name in [('caller','Caller_path'),('backend','Backend_path')]},
      'callerSharePointUserId':"@body('Caller_identity')?['Id']",'backendSharePointUserId':"@body('Backend_identity')?['Id']",
      'twoAccountContextSeparationVerified':False,'backendPermissionFlags':"@outputs('Backend_permission_flags')",
      'participantList':{'id':'@'+body('Read_participant_list')+"?['Id']",'title':'@'+body('Read_participant_list')+"?['Title']",'itemCount':'@'+body('Read_participant_list')+"?['ItemCount']",
        'hasUniqueRoleAssignments':'@'+body('Read_participant_list')+"?['HasUniqueRoleAssignments']",'readSecurity':'@'+body('Read_participant_list')+"?['ReadSecurity']",'writeSecurity':'@'+body('Read_participant_list')+"?['WriteSecurity']"},
      'identityField':{'internalName':'@'+body('Read_identity_field')+"?['InternalName']",'unique':'@'+body('Read_identity_field')+"?['EnforceUniqueValues']",'required':'@'+body('Read_identity_field')+"?['Required']"},
      'roleDefinitions':'@coalesce('+body('Read_role_definitions')+"?['results'],json('[]'))",'listRoleBindings':'@coalesce('+body('Read_list_role_bindings')+"?['results'],json('[]'))",
      'privacyVerified':False,'permissionWritesVerified':False,'audienceGroupVerified':False,'proceedToPrivacyCutover':False,
      'nextStep':'Assessment only: inspect imported Caller=Provided by run-only user and Backend=existing owner connection separately. One owner run cannot prove different-user separation, group onboarding, licences/policy or direct/API denial. #40 isolated proof remains gated; no production permission/schema/app changes.'},'Capabilities_collected')
    a['Respond']={'type':'Response','kind':'PowerApp','runAfter':after('Capability_report'),'inputs':{'statusCode':200,'schema':{'type':'object','properties':{
      'reportjson':{'type':'string','title':'reportjson','x-ms-content-hint':'TEXT','x-ms-dynamically-added':True}}},'body':{'reportjson':"@string(outputs('Capability_report'))"}}}
    measure(a);return a


def build_package(source,output):
    source,output=Path(source),Path(output)
    if any(p.exists() for p in [output,output.with_suffix('.definition.json'),output.with_suffix('.review.json')]):raise FileExistsError(output)
    with ZipFile(source) as z:original=json.loads(z.read(next(n for n in z.namelist() if n.endswith('/definition.json'))))
    props=original['properties'];old=props['definition']['actions']['Get_item'];site=old['inputs']['parameters']['dataset']
    if props['connectionReferences'][CALLER].get('source')!='Invoker':raise ValueError('Verified Invoker source export required')
    mapping=json.loads((ROOT/'config/tenant_schema_mapping.json').read_text(encoding='utf-8'))
    if old['inputs']['parameters']['table'].strip('{}').lower()!=mapping['lists']['participants']['listId']:raise ValueError('Unverified participant list target')
    with TemporaryDirectory() as temp:
        p=Path(temp)/'base.zip';envelope(p,sharepoint_site=site)
        with ZipFile(p) as z:entries={n:json.loads(z.read(n)) for n in z.namelist()}
    name=next(n for n in entries if n.endswith('/definition.json'));doc=entries[name]
    refs=doc['properties']['connectionReferences'];refs[CALLER]['source']='Invoker'
    refs[BACKEND]={**deepcopy(refs[CALLER]),'source':'Embedded','connectionName':'IMPORT_SELECT_EXISTING_OWNER_SHAREPOINT_CONNECTION'}
    d=doc['properties']['definition'];d['actions']=actions(site,doc['name'],old['inputs']['authentication'],mapping)
    doc['properties']['displayName']=NAME
    api_map=entries[next(n for n in entries if n.endswith('/apisMap.json'))];api_map[BACKEND]=api_map[CALLER]
    conn_map=entries[next(n for n in entries if n.endswith('/connectionsMap.json'))];backend_resource=str(uuid4());conn_map[BACKEND]=backend_resource
    manifest=entries['manifest.json'];resources=manifest['resources'];caller_resource=conn_map[CALLER]
    resources[caller_resource]['details']['displayName']='Caller SharePoint path — existing connection; Provided by run-only user'
    resources[backend_resource]=deepcopy(resources[caller_resource]);resources[backend_resource]['details']['displayName']='Backend metadata path — existing owner SharePoint connection'
    flow=next(r for r in resources.values() if r['type']=='Microsoft.Flow/flows');flow['dependsOn'].append(backend_resource);flow['details']['displayName']=NAME
    manifest['details'].update(displayName=NAME+'-package',description='Issue 39 owner-only metadata experiment: two existing SharePoint connection paths, no item reads or permission/schema/data changes. Not a private-registration implementation.')
    output.parent.mkdir(parents=True,exist_ok=True)
    with ZipFile(output,'x',ZIP_DEFLATED) as z:
        for n,value in entries.items():z.writestr(n,json.dumps(value,indent=2)+'\n')
    review={'sourceTicket':39,'packageBuildId':doc['name'],'flowName':NAME,**measure(d['actions']),'limits':{'actions':500,'nesting':8},
      'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'sourceExportSha256':hashlib.sha256(source.read_bytes()).hexdigest(),
      'readOnly':True,'itemRowsRead':0,'writes':0,'connectionPaths':{CALLER:'Invoker; exported Raw auth expression',BACKEND:'Embedded; explicitly selected existing owner connection for metadata only'},
      'connectorApis':['shared_sharepointonline'],'newConnectorTypes':0,'tenantResult':'NOT_IMPORTED_NOT_TESTED',
      'twoAccountProof':False,'audienceGroup':'UNKNOWN_OWNER_REPORTED','privacyCutoverApproved':False,
      'gates':['Legacy import/editor must preserve distinct connection modes for the same SharePoint API.','Current owner metadata success cannot prove ordinary caller/backend separation.','Audience/group onboarding, intended-user licences, actual policy and #40 two-user proof remain unknown/unverified.','Backend metadata manage-permissions mask does not prove ACL write capability.']}
    output.with_suffix('.definition.json').write_bytes((json.dumps(doc,indent=2)+'\n').encode('utf-8'))
    output.with_suffix('.review.json').write_bytes((json.dumps(review,indent=2)+'\n').encode('utf-8'))
    return review


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    print(json.dumps(build_package(args.source,args.output),indent=2))


if __name__=='__main__':main()
