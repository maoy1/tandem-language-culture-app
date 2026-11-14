"""Inspect the actual #67/#68 .msapp, not a reconstructed screen model.

Static source/contract/preservation gates only. Studio compilation and tenant
actions remain explicit handover gates, never inferred from this report.
"""
from __future__ import annotations
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
from xml.etree import ElementTree as ET
from zipfile import ZipFile
import yaml

from scripts.build_integrated_app import BASE_SHA,CORE_SHA,core_contracts
from scripts.verify_discovery_app import formula_sanity


def all_controls(document):
    result={}
    def descend(children):
        for row in children:
            assert isinstance(row,dict) and len(row)==1,'Each child must name one control'
            name,node=next(iter(row.items()))
            assert name not in result,'Duplicate control name: '+name
            result[name]=node;descend(node.get('Children',[]))
    for screen in document.get('Screens',{}).values():descend(screen.get('Children',[]))
    return result


def formulas(document):
    for name,node in all_controls(document).items():
        for prop,value in node.get('Properties',{}).items():
            if isinstance(value,str) and value.startswith('='):yield name,prop,value[1:]
    for name,screen in document.get('Screens',{}).items():
        for prop,value in screen.get('Properties',{}).items():
            if isinstance(value,str) and value.startswith('='):yield name,prop,value[1:]


def run_calls(formula):
    for match in re.finditer(r'\b(Tandem\w+)\.Run\(',formula):
        stack=['('];quoted=False;count=1;i=match.end();start=i
        while i<len(formula) and stack:
            c=formula[i]
            if c=='"':
                if quoted and i+1<len(formula) and formula[i+1]=='"':i+=2;continue
                quoted=not quoted
            elif not quoted:
                if c in '([{':stack.append(c)
                elif c in ')]}':
                    assert stack.pop()=={')':'(',']':'[','}':'{'}[c],'Unbalanced Run expression'
                elif c==',' and len(stack)==1:count+=1
            i+=1
        assert not stack,'Unclosed Run call'
        if i==start+1:count=0
        yield match[1],count


def verify(base_path,core_path,path):
    base_path,path=Path(base_path),Path(path)
    with ZipFile(base_path) as z:before={n:z.read(n) for n in z.namelist()}
    with ZipFile(path) as z:
        assert z.testzip() is None,'Corrupt app archive'
        after={n:z.read(n) for n in z.namelist()}
    flows=core_contracts(core_path);checks=[]
    def check(name,condition):checks.append({'case':name,'passed':bool(condition)})
    check('owner-tested base hash',hashlib.sha256(base_path.read_bytes()).hexdigest()==BASE_SHA)
    check('native-tested core hash',hashlib.sha256(Path(core_path).read_bytes()).hexdigest()==CORE_SHA)
    main_old=yaml.safe_load(before['Src/MainScreen1.pa.yaml']);main_new=yaml.safe_load(after['Src/MainScreen1.pa.yaml'])
    controls_old,controls_new=all_controls(main_old),all_controls(main_new)
    # Compare every complete registration card/form, not just selected formulas.
    check('entire registration Form1 unchanged',controls_old['Form1']==controls_new['Form1'])
    permitted={'MyRequest','MyGroups','Discovery','Button2'}
    for name,node in controls_old.items():
        if name not in permitted:
            old=deepcopy(node);new=deepcopy(controls_new.get(name))
            if old.get('Children'):
                # Child subtrees are compared individually, so ancestor wrappers
                # compare their properties/variant only around intentional nav.
                old.pop('Children',None)
                if new is not None:new.pop('Children',None)
            check('registration control preserved:'+name,old==new)
    check('legacy test button removed','Button2' not in controls_new)
    check('App source preserved',before['Src/App.pa.yaml']==after['Src/App.pa.yaml'])
    old_discovery=all_controls(yaml.safe_load(before['Src/scrDiscovery.pa.yaml']))
    new_discovery=all_controls(yaml.safe_load(after['Src/scrDiscovery.pa.yaml']))
    for name,node in old_discovery.items():
        old=deepcopy(node);new=deepcopy(new_discovery.get(name))
        if name=='lblDiscoveryTitle':
            old['Properties'].pop('Width',None)
            if new:new['Properties'].pop('Width',None)
        check('working Discovery control preserved:'+name,old==new)
    for name,data in before.items():
        if name.startswith(('Controls/','Resources/')) or name in ['Header.json','References/Templates.json','References/Themes.json','References/ModernThemes.json']:
            check('native cache/resource preserved:'+name,after.get(name)==data)
    before_props,after_props=(json.loads(d['Properties.json']) for d in [before,after])
    check('app identity/non-flow properties preserved',all(after_props[k]==v for k,v in before_props.items() if k!='LocalConnectionReferences'))
    old_data,new_data=(json.loads(d['References/DataSources.json'])['DataSources'] for d in [before,after])
    check('existing SharePoint/sample sources preserved',[d for d in old_data if d['Type']!='ServiceInfo']==[d for d in new_data if d['Type']!='ServiceInfo'])
    old_refs,new_refs=(json.loads(p['LocalConnectionReferences']) for p in [before_props,after_props])
    old_sp=next(d for d in old_refs.values() if d.get('dataSources')==['Participants'])
    new_sp=next(d for d in new_refs.values() if d.get('dataSources')==['Participants'])
    check('existing participant connection preserved',all(new_sp[k]==v for k,v in old_sp.items() if k!='dependents'))
    screen_docs={n:yaml.safe_load(data) for n,data in after.items() if re.match(r'Src/[^_].*\.pa\.yaml$',n) and n!='Src/App.pa.yaml'}
    expected={'MainScreen1','scrDiscovery','scrRequests'}
    if 'Src/scrMyGroups.pa.yaml' in after:expected.add('scrMyGroups')
    check('expected screen set',set(s for d in screen_docs.values() for s in d.get('Screens',{}))==expected)
    check('screen order includes every screen',yaml.safe_load(after['Src/_EditorState.pa.yaml'])['EditorState']['ScreensOrder']==['MainScreen1','scrDiscovery','scrRequests']+(['scrMyGroups'] if 'scrMyGroups' in expected else []))
    proven_choices=set(re.findall(r'Choices\(\[@Participants\]\.[^)]+\)',before['Src/MainScreen1.pa.yaml'].decode()))
    all_names=[];calls=[];count=0
    for file,doc in screen_docs.items():
        all_names+=list(all_controls(doc))
        for name,prop,formula in formulas(doc):
            formula_sanity(formula);count+=1
            masked=re.sub(r'"(?:""|[^"])*"','',formula)
            check('Canvas equality operator:'+name+'.'+prop,'==' not in masked)
            for lookup in re.findall(r'Choices\(\[@Participants\]\.[^)]+\)',formula):
                check('existing proven lookup:'+name+'.'+prop,lookup in proven_choices)
            for flow,arity in run_calls(formula):
                spec=next(iter(flows[flow]['trigger'].values()))['inputs']['schema']
                check(f'Run arity:{name}.{prop}/{flow}',len(spec.get('required',[]))<=arity<=len(spec['properties']))
                calls.append(flow)
        if file!='Src/MainScreen1.pa.yaml':
            rendered='\n'.join(value for _,prop,value in formulas(doc) if prop in ['Text','Default','HtmlText'])
            for private in ['accountKey','Participantaccount','WriteOwner','SendOperationKey','MembershipKey','expectedETag','varGrpDiagnostic','varReqDiagnostic']:
                check('no private display:'+file+'/'+private,private not in rendered)
            source='\n'.join(v for _,_,v in formulas(doc))
            check('no direct list writes:'+file,not re.search(r'\b(Patch|Remove|SubmitForm|UpdateIf|RemoveIf)\s*\(',source))
    check('global control names unique',len(all_names)==len(set(all_names)))
    service={d['Name']:d for d in new_data if d['Type']=='ServiceInfo'}
    check('exact flow sources match invocation set',set(service)==set(calls))
    for name,ds in service.items():
        check('deployed flow IDs:'+name,ds['FlowNameId']==ds['WorkflowEntityId']==flows[name]['id'])
        xml=ET.fromstring(ds['WadlMetadata']['WadlXml']);ns={'w':'http://wadl.dev.java.net/2009/02','s':'http://schemas.microsoft.com/MicrosoftProjectSiena/WADL/2014/11'}
        request=xml.findall('.//w:request/w:representation/w:param',ns)
        schema=next(iter(flows[name]['trigger'].values()))['inputs']['schema']
        check('exact input order:'+name,[p.attrib['name'] for p in request]==list(schema['properties']))
        types={p.attrib['name']:p.attrib['type'] for p in request}
        check('input types:'+name,all(types[k]==('xs:double' if v['type']=='number' else 'xs:string') for k,v in schema['properties'].items()))
        result=xml.findall('.//s:object[@name="ResponseActionOutput"]/s:property',ns)
        check('exact output shape:'+name,{p.attrib['name'] for p in result}==set(next(iter(flows[name]['responses'].values()))['properties']))
    for key,ref in new_refs.items():
        check('connection dependency:'+key,all(d in new_refs for d in ref.get('dependencies',{}).values()))
        check('connection dependents:'+key,all(d in new_refs for d in ref.get('dependents',[])))
    check('PAC loads source overlay',json.loads(after['packed.json'])['LoadConfiguration']['LoadFromYaml'] is True)
    return {'artifactVersion':'Integrated-v2' if 'scrMyGroups' in expected else 'Requests-v1','sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
        'baseAppSha256':BASE_SHA,'coreZipSha256':CORE_SHA,'testCount':len(checks),'allPassed':all(c['passed'] for c in checks),
        'formulaSanityCount':count,'flowCallCount':len(calls),'boundFlows':sorted(service),'controlCount':len(all_names),'checks':checks,
        'powerFxCompilation':'NOT RUN: local checks do not compile/type-check Power Fx',
        'nativeImport':'NOT RUN','nativeActions':'NOT RUN','publishedAppVersion':None,'ordinaryParticipantAccess':'DEFERRED',
        'schemaChanges':0,'backendChanges':0,'newConnectors':0,'note':'Source overlays are authoritative on Studio edit; original cached AppCheckerResult/Controls are not new compilation proof.'}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--base-app',required=True);p.add_argument('--core-solution',required=True);p.add_argument('--app',required=True);p.add_argument('--report',required=True);a=p.parse_args()
    result=verify(a.base_app,a.core_solution,a.app);Path(a.report).write_bytes((json.dumps(result,indent=2)+'\n').encode())
    print(json.dumps({k:result[k] for k in ['testCount','allPassed','formulaSanityCount','boundFlows','sha256']}));
    if not result['allPassed']:
        print(json.dumps([c for c in result['checks'] if not c['passed']],indent=2));raise SystemExit(1)
