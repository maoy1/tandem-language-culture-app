"""#7 shared-child Discovery parent; legacy v2 remains reproducible."""
from copy import deepcopy
import argparse, hashlib, json
from pathlib import Path
from uuid import uuid4
from zipfile import ZipFile
from . import discovery_flow as legacy
from .schema_audit import measure
ROOT=legacy.ROOT
CHILD_ID='e9aa88eb-a666-4df1-b088-176be7bcd00d'


def child_call(prefix,mode,profiles,previous=None,**extra):
    request,call,parsed,guard,result=[prefix+s for s in ['_Request','_Call','_Envelope','_Require','_Result']]
    payload={'contractVersion':1,'rulesVersion':1,'mode':mode,'profiles':profiles,'catalogues':"@outputs('Raw_catalogues')",**extra}
    a={request:legacy.compose(payload,previous)}
    a[prefix+'_Bound']=legacy.condition("lessOrEquals(length(string(outputs('"+request+"'))),250000)",{},
        {prefix+'_Too_large':legacy.compose('@div(1,0)')},request)
    a[call]={'type':'Workflow','inputs':{'host':{'workflowReferenceName':CHILD_ID},'body':{'text':"@string(outputs('"+request+"'))"}},'runAfter':legacy.after(prefix+'_Bound')}
    schema={'type':'object','required':['success','code','contractVersion','rulesVersion','result','authorizesAction'],
      'properties':{'success':{'type':'boolean'},'code':{'type':'string'},'contractVersion':{'type':'integer'},'rulesVersion':{'type':'integer'},'result':{'type':'object'},'authorizesAction':{'type':'boolean'}}}
    a[parsed]=legacy.parse("@json(body('"+call+"')?['resultjson'])",schema,call)
    checks=["equals(body('"+call+"')?['success'],true)","equals(body('"+call+"')?['resultcode'],'OK')"]
    for key,value in [('success','true'),('code',"'OK'"),('contractVersion','1'),('rulesVersion','1'),('authorizesAction','false')]:
        checks.append("equals(body('"+parsed+"')?['"+key+"'],"+value+")")
    a[guard]=legacy.condition('and('+','.join(checks)+')',{}, {prefix+'_Reject':legacy.compose('@div(1,0)')},parsed)
    a[result]=legacy.compose("@body('"+parsed+"')?['result']",guard)
    return a


def build_actions(original,mapping,groups,build_id):
    # Reuse the proven caller/read/projection adapter, replacing emitted rules.
    a=legacy.build_actions(original,mapping,groups,build_id)
    inside=a['Discovery_reads']['actions']
    for key in list(inside):
        if key.startswith('Shared_'):del inside[key]
    inside.update(child_call('Normalize','NORMALIZE',"@body('Raw_profiles')",'Raw_profiles'))
    inside['Shared_Profiles']=legacy.parse("@outputs('Normalize_Result')?['profiles']",{'type':'array'},'Normalize_Result')
    inside['Shared_Catalogues']=legacy.compose("@outputs('Normalize_Result')?['catalogues']",'Shared_Profiles')
    inside['Eligible_people']=legacy.query("@body('Shared_Profiles')","not(equals(item()?['profileId'],outputs('Actor')?['profileId']))",'Require_available_actor')
    del inside['Require_people_result_bound']
    projection=inside['Each_person']['actions']
    projection['Person_fit']=legacy.compose("@outputs('Pair_Result')",'Person_raw')
    projection['Result_bound']=legacy.condition("less(length(variables('People')),50)",{},
      {'Error_people_bound':legacy.setvar('ErrorCode','PEOPLE_RESULT_BOUND'),'Stop_people_bound':legacy.compose('@div(1,0)','Error_people_bound')})
    projection['Person_raw']['runAfter']=legacy.after('Result_bound')
    person=child_call('Pair','PAIR',"@createArray(outputs('Actor'),items('Each_person'))",leftId="@outputs('Actor')?['profileId']",rightId="@items('Each_person')?['profileId']")
    person['Show_person']=legacy.condition("equals(outputs('Pair_Result')?['eligible'],true)",projection,n='Pair_Result')
    inside['Each_person']=legacy.loop("@body('Eligible_people')",person,'Eligible_people')
    g=inside['Groups_exist']['actions']
    # Full/schema metadata audits belong to explicit deployment/maintenance.
    for key in ['Read_request_fields','Request_commit_field','Require_request_commit_schema']:del g[key]
    g['Read_memberships']['runAfter']={}
    # Validate the operation-time rows themselves instead of rereading field
    # metadata. Absent/null commit evidence must not produce partial success.
    request_schema={'type':'array','items':{'type':'object','required':['Id','Status','OperationComplete'],
        'properties':{'Id':{'type':'integer','minimum':1},'Status':{'type':'string'},'OperationComplete':{'type':'boolean'}}}}
    g['Parse_current_commit_rows']=legacy.parse("@body('Read_requests')?['d']?['results']",request_schema,'Require_request_bound')
    g['Open_groups']['runAfter']=legacy.after('Parse_current_commit_rows')
    inner=g['Each_group']['actions']
    for key in list(inner):
        if key.startswith('Group_fit_'):del inner[key]
    inner.update(child_call('Group','GROUP',"@body('Shared_Profiles')",'Group_adapter',candidateId="@outputs('Actor')?['profileId']",group="@outputs('Group_adapter')"))
    inner['Group_fit_Result']=legacy.compose("@outputs('Group_Result')",'Group_Result')
    a['Discovery_report']['inputs'].update(sharedChildWorkflow=CHILD_ID,contractVersion=1,sharedConsumer=True,nativeConsumerEvidence='NOT_RUN')
    measure(a)
    return a


def build_package(source,output):
    """Emit parent component for final Solution assembly, not a legacy call ZIP."""
    source,output=Path(source),Path(output)
    if output.exists() or output.with_suffix('.review.json').exists():raise FileExistsError(output)
    with ZipFile(source) as z:
        original=json.loads(z.read(next(n for n in z.namelist() if n.endswith('/definition.json'))))
    mapping=json.loads((ROOT/'config/tenant_schema_mapping.json').read_text(encoding='utf-8'))
    groups=json.loads((ROOT/'config/group_schema_mapping.json').read_text(encoding='utf-8'))
    if not groups['mappingVerified']:raise ValueError('Verified group mapping required')
    build_id=str(uuid4());actions=build_actions(original,mapping,groups,build_id)
    # Carry the observed trigger/auth expressions, never source-flow identity,
    # creator metadata or an actual connection instance into the component.
    definition={k:deepcopy(v) for k,v in original['properties']['definition'].items()
                if k in ['$schema','parameters','triggers']}
    definition.update(contentVersion='1.0.0.0',actions=actions)
    references=deepcopy(original['properties']['connectionReferences'])
    references['shared_sharepointonline']['connectionName']='IMPORT_SELECT_EXISTING_SHAREPOINT_CONNECTION'
    document={'name':build_id,'type':'Microsoft.Flow/flows','properties':{
        'displayName':'TandemDiscovery shared consumer','definition':definition,'connectionReferences':references}}

    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_bytes((json.dumps(document,indent=2)+'\n').encode('utf-8'))
    review={'sourceTicket':7,'packageBuildId':build_id,**measure(actions),'writes':0,'childWorkflowReferenceName':CHILD_ID,'contractVersion':1,'rulesVersion':1,
      'definitionSha256':hashlib.sha256(output.read_bytes()).hexdigest(),'sourceExportSha256':hashlib.sha256(source.read_bytes()).hexdigest(),
      'sharedChildSha256':hashlib.sha256((ROOT/'artifacts/shared_validation/TandemSharedValidation81-v2.child.definition.json').read_bytes()).hexdigest(),
      'generatorSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'connectionSource':'Invoker','ordinaryUserAccessVerified':False,'tenantResult':'NOT_RUN',
      'deployment':'PARENT_COMPONENT_FOR_FINAL_SOLUTION_ASSEMBLY','legacyZip':'NOT_APPLICABLE: Workflow calls require final Solution assembly; historical v2 ZIP unchanged'}
    output.with_suffix('.review.json').write_bytes((json.dumps(review,indent=2)+'\n').encode('utf-8'))
    return review


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    print(json.dumps(build_package(args.source,args.output),indent=2))
