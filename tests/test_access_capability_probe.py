"""#39 metadata experiment; no live permission grant or privacy proof."""
from collections import defaultdict
from copy import deepcopy
import json
from zipfile import ZipFile
import pytest
from test_compatibility_generated import Runner
from test_coordination_fixture import walk
from scripts.power_automate import build_access_capability_probe as probe

MAPPING=json.loads((probe.ROOT/'config/tenant_schema_mapping.json').read_text(encoding='utf-8'))


class Metadata:
    def __init__(self):self.mode='normal';self.calls=[]
    def request(self,connector,p):
        uri=p['parameters/uri'];self.calls.append((connector,uri))
        assert p['parameters/method']=='GET' and '/items' not in uri.lower()
        if 'currentuser' in uri:
            value={'Id':7 if connector==probe.CALLER else 8}
            if self.mode=='badCaller' and connector==probe.CALLER:value={'Id':'untrusted-string'}
        elif '/fields(' in uri:
            f=MAPPING['lists']['participants']['fields']['ParticipantAccount']
            value={'Id':f['id'],'InternalName':f['internalName'],'TypeAsString':'User','Required':True,'Indexed':True,'EnforceUniqueValues':self.mode!='uniqueOff'}
        elif '/EffectiveBasePermissions' in uri:
            value={'High':'0','Low':'33556481'}
            if self.mode=='wrappedMask':value={'EffectiveBasePermissions':value}
            if self.mode=='missingMask':value={}
        elif '/roleassignments?' in uri:
            value={'results':[{'Member':{'Id':5,'PrincipalType':8},'RoleDefinitionBindings':{'results':[{'Id':1073741829,'RoleTypeKind':5}]}}]}
            if self.mode=='pagedRoles':value['__next']='next'
        elif '/roledefinitions?' in uri:
            value={'results':[{'Id':1073741829,'Name':'Full Control','RoleTypeKind':5,'BasePermissions':{'High':'0','Low':'33556481'}}]}
        else:
            value={'Id':MAPPING['lists']['participants']['listId'],'Title':'Participants','BaseTemplate':100,'ItemCount':3,'HasUniqueRoleAssignments':False,'ReadSecurity':1,'WriteSecurity':1}
            if self.mode=='wrongTarget':value['Id']='wrong-list'
        return {'statusCode':403 if self.mode=='backendDenied' and connector==probe.BACKEND else 200,'body':{'d':value}}


class ProbeRunner(Runner):
    def __init__(self,server):super().__init__();self.server=server;self.outputs=defaultdict(lambda:None);self.action_states={};self.response=None
    def body(self,name):
        value=self.outputs[name];return value['body'] if isinstance(value,dict) and 'statusCode' in value else value
    def run(self,actions,ctx=None):
        ctx=ctx or {};todo=dict(actions);done={}
        while todo:
            ready=[n for n,a in todo.items() if set(a.get('runAfter',{}))<=set(done)];assert ready
            for name in ready:
                action=todo.pop(name);kind=action['type'];p=action.get('inputs',{});state='Succeeded'
                if any(done[n] not in states for n,states in action.get('runAfter',{}).items()):done[name]='Skipped';self.action_states[name]='Skipped';continue
                try:
                    if kind=='OpenApiConnection':
                        self.outputs[name]=self.server.request(p['host']['connectionName'],self.inputs(p['parameters'],ctx))
                        if self.outputs[name]['statusCode']>=400:state='Failed'
                    elif kind=='ParseJson':
                        value=self.inputs(p['content'],ctx);assert isinstance(value,dict) and type(value.get('Id'))is int and value['Id']>0
                        self.outputs[name]=value
                    elif kind=='Compose':self.outputs[name]=self.inputs(p,ctx)
                    elif kind=='Scope':
                        if not self.run(action['actions'],ctx):state='Failed'
                    elif kind=='Response':self.response=self.inputs(p['body'],ctx)
                    else:raise RuntimeError(kind)
                except (AssertionError,TypeError,KeyError,ValueError):state='Failed'
                done[name]=state;self.action_states[name]=state
        return all(s!='Failed' for s in done.values())


def execute(mode):
    server=Metadata();server.mode=mode;runner=ProbeRunner(server)
    runner.run(probe.actions('https://example.sharepoint.com/sites/test','fixture-only',{'type':'Raw','value':'SOURCE_EXPRESSION'},MAPPING))
    return runner


@pytest.mark.parametrize('mode',['normal','wrappedMask'])
def test_metadata_success_keeps_all_privacy_and_cutover_gates_false(mode):
    r=execute(mode);report=r.outputs['Capability_report']
    assert report['metadataComplete'] and report['result']=='CAPABILITY_METADATA_COLLECTED'
    assert report['callerSharePointUserId']==7 and report['backendSharePointUserId']==8
    assert report['backendPermissionFlags']=={'viewItems':True,'manageLists':True,'managePermissions':True}
    assert report['identityField']['unique']
    assert report['privacyVerified']==report['twoAccountContextSeparationVerified']==report['proceedToPrivacyCutover']==report['permissionWritesVerified']==report['audienceGroupVerified']==False
    assert json.loads(r.response['reportjson'])==report


@pytest.mark.parametrize('mode',['uniqueOff','wrongTarget','pagedRoles','missingMask','backendDenied','badCaller'])
def test_missing_prerequisite_never_reports_metadata_complete(mode):
    report=execute(mode).outputs['Capability_report']
    assert not report['metadataComplete'] and report['result']=='CAPABILITY_METADATA_INCOMPLETE'
    assert not report['proceedToPrivacyCutover']


def test_each_path_uses_its_declared_connection_and_no_employee_items():
    auth={'type':'Raw','value':'SOURCE_EXPRESSION'};actions=probe.actions('https://example.sharepoint.com/sites/test','fixture-only',auth,MAPPING)
    for path,action in walk(actions):
        if action['type']!='OpenApiConnection':continue
        p=action['inputs']['parameters'];assert p['parameters/method']=='GET' and '/items' not in p['parameters/uri'].lower()
        assert not any(v in p['parameters/uri'].lower() for v in ['breakrole','addrole','deleterole','resetrole'])
        if path[0]=='Caller_path':assert action['inputs']['host']['connectionName']==probe.CALLER and action['inputs']['authentication']==auth
        else:assert path[0]=='Backend_path' and action['inputs']['host']['connectionName']==probe.BACKEND and action['inputs']['authentication']=="@parameters('$authentication')"


def test_two_alias_import_maps_share_only_api_not_connection_resource(tmp_path):
    path=tmp_path/'source.zip'
    source={'properties':{'connectionReferences':{probe.CALLER:{'source':'Invoker'}},'definition':{'actions':{'Get_item':{'inputs':{'parameters':{'dataset':'https://example.sharepoint.com/sites/test','table':MAPPING['lists']['participants']['listId']},'authentication':{'type':'Raw','value':'SOURCE_EXPRESSION'}}}}}}}
    with ZipFile(path,'w') as z:z.writestr('Microsoft.Flow/flows/source/definition.json',json.dumps(source))
    output=tmp_path/'probe.zip';review=probe.build_package(path,output)
    assert review['actions']<=500 and review['maximumActionDepth']<=8 and review['writes']==review['itemRowsRead']==0 and review['newConnectorTypes']==0
    with ZipFile(output) as z:
        values={n:json.loads(z.read(n)) for n in z.namelist()};manifest=values['manifest.json']
        api=next(v for n,v in values.items() if n.endswith('/apisMap.json'));conn=next(v for n,v in values.items() if n.endswith('/connectionsMap.json'))
        assert api[probe.CALLER]==api[probe.BACKEND] and conn[probe.CALLER]!=conn[probe.BACKEND]
        doc=next(v for n,v in values.items() if n.endswith('/definition.json'));refs=doc['properties']['connectionReferences']
        assert refs[probe.CALLER]['source']=='Invoker' and refs[probe.BACKEND]['source']=='Embedded'
        assert len(doc['properties']['definition']['triggers']['manual']['inputs']['schema']['properties'])==0
        assert not any(s in json.dumps(values) for s in ['SOURCE_OWNER_CONNECTION_ID','source-user-email','source-creator-id'])
        assert len([r for r in manifest['resources'].values() if r['type']=='Microsoft.PowerApps/apis/connections'])==2
    with pytest.raises(FileExistsError):probe.build_package(path,output)


def test_owner_only_source_is_not_silently_treated_as_invoker(tmp_path):
    path=tmp_path/'source.zip'
    source={'properties':{'connectionReferences':{probe.CALLER:{'source':'Embedded'}},'definition':{'actions':{'Get_item':{'inputs':{'parameters':{'dataset':'https://example.sharepoint.com/sites/test'},'authentication':'unused'}}}}}}
    with ZipFile(path,'w') as z:z.writestr('Microsoft.Flow/flows/source/definition.json',json.dumps(source))
    with pytest.raises(ValueError,match='Invoker'):probe.build_package(path,tmp_path/'bad.zip')
