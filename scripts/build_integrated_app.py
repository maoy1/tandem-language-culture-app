"""Assemble #67/#68 source overlays onto the owner-tested #16 app.

Local Microsoft PAC tooling only; nothing is imported/published by this script.
Keep each screen in its own module/PR. One final .msapp is handed to the owner.
"""
from __future__ import annotations
import argparse
from copy import deepcopy
import hashlib
import importlib
import json
from pathlib import Path
import re
import subprocess
from tempfile import TemporaryDirectory
from uuid import NAMESPACE_URL, uuid5
from xml.etree import ElementTree as ET
from zipfile import ZipFile, ZIP_DEFLATED

from scripts import build_discovery_app as discovery

BASE_SHA='ee00b86d7810d2e6c1ccd52777b7a1ef9003e60aa8638fa270817503289ffdee'
CORE_SHA='0d1b97508db5c5995199bac0853d45ee73ba147a48008c0fb1c369740b4868bd'
MODULES={'requests':'scripts.app_requests_screen','groups':'scripts.app_groups_screen'}
BASE_FLOWS={'TandemDiscovery','TandemSendRequest','TandemSendGroupJoinRequest'}
LEGACY_JOIN_CALL='TandemSendGroupJoinRequest.Run(varDiscoveryIntentTarget, varDiscoveryIntent, varDiscoveryIntentIntroduction)'
FIXED_JOIN_CALL='TandemSendGroupJoinRequest.Run(varDiscoveryIntentTarget, varDiscoveryIntent, {text_1: varDiscoveryIntentIntroduction})'


def repair_discovery(document):
    """Optional Power Apps flow inputs are supplied as a final record."""
    result=deepcopy(document)
    button=next(c['btnDiscoverySend'] for c in result['Screens']['scrDiscovery']['Children'] if 'btnDiscoverySend' in c)
    formula=button['Properties']['OnSelect']
    if formula.count(LEGACY_JOIN_CALL)!=1:
        raise ValueError('Unexpected Discovery group-join call; review before patching')
    button['Properties']['OnSelect']=formula.replace(LEGACY_JOIN_CALL,FIXED_JOIN_CALL)
    return result


def core_contracts(path):
    if hashlib.sha256(Path(path).read_bytes()).hexdigest()!=CORE_SHA:
        raise ValueError('Expected the owner-activated/smoke-tested core1.0.0.2 ZIP')
    with ZipFile(path) as z:
        manifest=ET.fromstring(z.read('solution.xml'))
        if manifest.findtext('SolutionManifest/UniqueName')!='TandemCoreBatch' or manifest.findtext('SolutionManifest/Version')!='1.0.0.2':
            raise ValueError('Unexpected core Solution')
        flows={}
        for node in ET.fromstring(z.read('customizations.xml')).findall('./Workflows/Workflow'):
            doc=json.loads(z.read(node.findtext('JsonFileName').lstrip('/')))
            definition=doc['properties']['definition']
            def responses(block):
                result={}
                for name,a in block.items():
                    if a['type']=='Response':result[name]=a['inputs']['schema']
                    for child in [a.get('actions',{}),a.get('else',{}).get('actions',{})]:result.update(responses(child))
                return result
            flows[node.attrib['Name']]={'id':node.attrib['WorkflowId'].strip('{}').lower(),
                'trigger':definition['triggers'],'responses':responses(definition['actions']),
                'connectionReferences':doc['properties'].get('connectionReferences',{})}
        return flows


def command(pac,args):
    result=subprocess.run([*pac,*args],capture_output=True,text=True,encoding='utf8')
    if result.returncode:raise RuntimeError(result.stdout+'\n'+result.stderr)
    return result.stdout


def busy(modules,modal=False):
    parts=[getattr(m,'BUSY','false') for m in modules]
    if modal:parts += [getattr(m,'MODAL','false') for m in modules]
    return ' || '.join('('+p+')' for p in parts) or 'false'


def main_entry(module,modules):
    pending=' || '.join('('+m.PENDING+')' for m in modules)
    return '''If(Form1.Unsaved || newMode || IsBlank(RecordsGallery1.Selected.ID),
    Notify("Save or cancel your registration changes first.", NotificationType.Warning),
    If((!IsBlank(varDiscoveryIntent) && varDiscoveryActorId <> RecordsGallery1.Selected.ID) ||
       (PENDING && !IsBlank(varAppActorId) && varAppActorId <> RecordsGallery1.Selected.ID),
        Notify("Finish or clear the earlier request intent before changing profiles.", NotificationType.Warning),
        Set(varAppActorId, RecordsGallery1.Selected.ID);
        Navigate(SCREEN, ScreenTransition.None);
        LOAD
    )
)'''.replace('PENDING',pending).replace('SCREEN',module.SCREEN_NAME).replace('LOAD',module.LOAD)


def patch_main(text,modules):
    # No registration form/card/button logic is changed.
    start=text.index('                              - MyRequest:')
    end=text.index('                              - Discovery:',start)
    requests=next(m for m in modules if m.SCREEN_NAME=='scrRequests')
    nav=[discovery.control('MyRequest','ModernButton@1.0.0',{
        'Height':'36','Width':'110','Text':'"My requests"','OnSelect':main_entry(requests,modules),
        'DisplayMode':f'If({busy(modules)}, DisplayMode.Disabled, DisplayMode.Edit)'})]
    groups=next((m for m in modules if m.SCREEN_NAME=='scrMyGroups'),None)
    if groups:nav.append(discovery.control('MyGroups','ModernButton@1.0.0',{
        'Height':'36','Width':'110','Text':'"My groups"','OnSelect':main_entry(groups,modules),
        'DisplayMode':f'If({busy(modules)}, DisplayMode.Disabled, DisplayMode.Edit)'}))
    text=text[:start]+discovery.dump_yaml(nav,15)+text[end:]
    # Include pending actions from all screens in Discovery's actor-switch guard.
    pending=' || '.join('('+m.PENDING+')' for m in modules)
    old='!IsBlank(varDiscoveryIntent) && varDiscoveryActorId <> RecordsGallery1.Selected.ID'
    new='('+old+') || (('+pending+') && !IsBlank(varAppActorId) && varAppActorId <> RecordsGallery1.Selected.ID)'
    start=text.index('                              - Discovery:')
    end=text.index('                              - SubmitFormButton1:',start)
    block=text[start:end]
    if block.count(old)!=1:raise ValueError('Unexpected Discovery entry; preserve it for manual review')
    text=text[:start]+block.replace(old,new)+text[end:]
    # Original export has one disposable legacy-flow test button. It is outside
    # the registration layout and must not invoke the now-retired preview flow.
    marker='      - Button2:'
    if marker in text:
        start=text.index(marker);tail=text[start:]
        if 'TandemDiscoveryv2.Run' not in tail or '"Test Discovery1"' not in tail:
            raise ValueError('Unexpected Button2; refusing to remove a real control')
        if re.search(r'^      - ',tail[len(marker):],re.M):raise ValueError('Test button is not the final root control')
        text=text[:start]
    return text


def cross_navigation(source,target,module_map):
    if target=='scrDiscovery':
        return 'Set(varDiscoveryActorId, varAppActorId); Navigate(scrDiscovery, ScreenTransition.None); '+discovery.LOAD
    module=module_map[target]
    prefix='Set(varAppActorId, varDiscoveryActorId); ' if source=='scrDiscovery' else ''
    return prefix+f'Navigate({target}, ScreenTransition.None); '+module.LOAD


def add_navigation(document,source,modules):
    module_map={m.SCREEN_NAME:m for m in modules}
    targets=[('scrDiscovery','Discovery')]+[(m.SCREEN_NAME,'My requests' if m.SCREEN_NAME=='scrRequests' else 'My groups') for m in modules]
    others=[(screen,label) for screen,label in targets if screen!=source]
    c=document['Screens'][source]['Children']
    controls=[]
    for i,(screen,label) in enumerate(others):
        controls.append(discovery.control(source+'_Nav_'+screen,'Classic/Button@2.2.0',{
            'Text':json.dumps(label),'X':f'Parent.Width - {610-i*150}','Y':'20','Width':'140','Height':'40','Size':'12',
            'DisplayMode':f'If(varDiscoveryBusy || varDiscoverySending || {busy(modules,modal=True)}, DisplayMode.Disabled, DisplayMode.Edit)',
            'OnSelect':cross_navigation(source,screen,module_map)}))
    # Place links below modal overlays in the source z-order.
    document['Screens'][source]['Children']=controls+c
    if source=='scrDiscovery':
        for item in c:
            if 'lblDiscoveryTitle' in item:item['lblDiscoveryTitle']['Properties']['Width']='=Parent.Width - 640'
    return document


def bind_flows(entries,flows,required):
    data=json.loads(entries['msapp/References/DataSources.json'])
    props=json.loads(entries['msapp/Properties.json']);refs=json.loads(props['LocalConnectionReferences'])
    template=next(d for d in data['DataSources'] if d['Name']=='TandemSendRequest')
    prototype=deepcopy(next(v for v in refs.values() if v.get('dataSources')==['TandemSendRequest']))
    old_service_names={d['Name'] for d in data['DataSources'] if d['Type']=='ServiceInfo'}
    old_keys={k for k,r in refs.items() if set(r.get('dataSources',[])) & old_service_names}
    refs={k:r for k,r in refs.items() if k not in old_keys}
    data['DataSources']=[d for d in data['DataSources'] if d['Type']!='ServiceInfo']
    for r in refs.values():
        r['dependents']=[k for k in r.get('dependents',[]) if k not in old_keys]
    for name in sorted(required):
        spec=flows[name];flow_id=spec['id']
        data['DataSources'].append(discovery.flow_binding(template,name,spec,flow_id))
        key=str(uuid5(NAMESPACE_URL,'tandem-app-integrated-v2:'+name));r=deepcopy(prototype)
        r.update(id=key,connectionInstanceId='/providers/microsoft.powerapps/apis/shared_logicflows/connections/'+flow_id,dataSources=[name])
        for hints in ['parameterHints','parameterHintsV2']:
            r['connectionRef'][hints]['workflowName']={'value':flow_id}
            r['connectionRef'][hints]['workflowEntityId']={'value':flow_id}
            r['connectionRef'][hints]['workflowDisplayName']={'value':name}
        refs[key]=r
        for dep in r.get('dependencies',{}).values():
            if dep not in refs:raise ValueError('Unresolved existing connection dependency: '+str(dep))
            refs[dep].setdefault('dependents',[]).append(key)
    props['LocalConnectionReferences']=json.dumps(refs,separators=(',',':'))
    entries['msapp/Properties.json']=json.dumps(props,ensure_ascii=False).encode()
    entries['msapp/References/DataSources.json']=json.dumps(data,ensure_ascii=False).encode()


def build(base_app,core_zip,output,pac,screen_names=('requests','groups')):
    base_app,output=Path(base_app),Path(output)
    if hashlib.sha256(base_app.read_bytes()).hexdigest()!=BASE_SHA:raise ValueError('Expected the owner-tested Discovery-v1 source app')
    if output.exists():raise FileExistsError('Versioned app output already exists; preserve it: '+str(output))
    if 'requests' not in screen_names:raise ValueError('Requests is the integrated navigation foundation')
    modules=[importlib.import_module(MODULES[n]) for n in screen_names]
    flows=core_contracts(core_zip);required=BASE_FLOWS|{n for m in modules for n in m.FLOW_NAMES}
    with TemporaryDirectory(prefix='tandem-app-integrated-') as directory:
        srcroot=Path(directory)/'source'
        unpack=command(pac,['canvas','unpack','--msapp',str(base_app),'--sources',str(srcroot),'--layout','SourceCode'])
        src=srcroot/'Src'
        (src/'MainScreen1.pa.yaml').write_text(patch_main((src/'MainScreen1.pa.yaml').read_text(encoding='utf8'),modules),encoding='utf8')
        # Assert the currently generated Discovery source matches the tested base
        # before making only its intentional cross-navigation/title-width edits.
        original=(src/'scrDiscovery.pa.yaml').read_text(encoding='utf8')
        if original.strip()!=discovery.dump_yaml(discovery.screen()).strip():
            raise ValueError('Working Discovery source differs from generator; do not overwrite it')
        screens=[('scrDiscovery',repair_discovery(discovery.screen()))]+[(m.SCREEN_NAME,m.screen()) for m in modules]
        for name,document in screens:
            document=add_navigation(deepcopy(document),name,modules)
            (src/(name+'.pa.yaml')).write_text(discovery.dump_yaml(document),encoding='utf8')
        order=['MainScreen1','scrDiscovery']+[m.SCREEN_NAME for m in modules]
        (src/'_EditorState.pa.yaml').write_text('EditorState:\n  ScreensOrder:\n'+''.join('    - '+n+'\n' for n in order),encoding='utf8')
        archive=next(srcroot.glob('*.msapr'))
        with ZipFile(archive) as z:entries={n:z.read(n) for n in z.namelist()}
        bind_flows(entries,flows,required)
        with ZipFile(archive,'w',ZIP_DEFLATED) as z:
            for n,b in entries.items():z.writestr(n,b)
        output.parent.mkdir(parents=True,exist_ok=True)
        pack=command(pac,['canvas','pack','--sources',str(srcroot),'--msapp',str(output),'--layout','SourceCode'])
        with ZipFile(output) as z:
            if z.testzip():raise ValueError('Corrupt app package')
        sources=output.parent/'source';sources.mkdir(exist_ok=True)
        for file in src.glob('*.pa.yaml'):(sources/file.name).write_bytes(file.read_bytes())
        manifest={'artifactVersion':'Integrated-v3' if 'groups' in screen_names else 'Requests-v2','sourceTickets':[16,67]+([68] if 'groups' in screen_names else []),
            'baseAppSha256':BASE_SHA,'coreSolutionVersion':'1.0.0.2','coreZipSha256':CORE_SHA,
            'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'screens':order,
            'flowBindings':{n:{'id':flows[n]['id'],'inputs':next(iter(flows[n]['trigger'].values()))['inputs']['schema'],
                                  'responses':flows[n]['responses']} for n in sorted(required)},
            'packager':'Microsoft PAC 2.15.1 SourceCode; Studio validation required',
            'nativeImport':'NOT RUN','publishedAppVersion':None,'ordinaryUserAccess':'DEFERRED',
            'runtimeFlowChanges':0,'schemaChanges':0,'newConnectors':0}
        output.with_suffix('.manifest.json').write_bytes((json.dumps(manifest,indent=2)+'\n').encode())
        output.with_suffix('.pack.log').write_text(unpack+'\n'+pack,encoding='utf8')
        return manifest


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--base-app',type=Path,required=True);p.add_argument('--core-solution',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--dotnet',required=True);p.add_argument('--pac-dll',required=True)
    p.add_argument('--screens',nargs='+',choices=list(MODULES),default=['requests','groups']);a=p.parse_args()
    result=build(a.base_app,a.core_solution,a.output,[a.dotnet,a.pac_dll],tuple(a.screens))
    print(json.dumps({k:result[k] for k in ['artifactVersion','sourceTickets','sha256','screens','nativeImport']},indent=2))
