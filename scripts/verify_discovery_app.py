"""Check #16 package preservation and contract wiring; not a Power Fx compiler."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
from zipfile import ZipFile


def formula_sanity(formula):
    """Catch malformed separators/delimiters; deliberately not type checking."""
    assert not re.search(r',\s*As\s', formula), 'record alias must follow its table expression'
    stack=[];quoted=False;i=0
    while i<len(formula):
        c=formula[i]
        if c=='"':
            if quoted and i+1<len(formula) and formula[i+1]=='"':
                i+=2;continue
            quoted=not quoted
        elif not quoted:
            if c in '([{':stack.append(c)
            elif c in ')]}':
                assert stack and stack.pop()=={')':'(',']':'[','}':'{'}[c], 'unbalanced delimiter'
        i+=1
    assert not stack and not quoted, 'unterminated expression'


def verify(original, candidate):
    with ZipFile(original) as z:
        assert z.testzip() is None
        before={n:z.read(n) for n in z.namelist()}
    with ZipFile(candidate) as z:
        assert z.testzip() is None
        after={n:z.read(n) for n in z.namelist()}
    checks=[]
    def check(name, test):
        checks.append({'case':name,'passed':bool(test)})
    for name in before:
        if name not in ['Src/MainScreen1.pa.yaml','Src/scrDiscovery.pa.yaml',
                        'Properties.json','References/DataSources.json']:
            check('preserved:'+name, before[name]==after[name])
    def without_entry(data):
        s=data.decode().replace('\r\n','\n')
        return re.sub(r'(?s)                              - Discovery:.*?(?=                              - SubmitFormButton1:)', '',s)
    check('registration changes restricted to Discovery entry',without_entry(before['Src/MainScreen1.pa.yaml'])==without_entry(after['Src/MainScreen1.pa.yaml']))
    old,new=(json.loads(d['Properties.json']) for d in [before,after])
    check('app identity and all non-flow properties preserved',all(new[k]==v for k,v in old.items() if k!='LocalConnectionReferences'))
    old_refs,new_refs=(json.loads(p['LocalConnectionReferences']) for p in [old,new])
    targets={'TandemDiscovery','TandemSendRequest','TandemSendGroupJoinRequest'}
    for key,ref in old_refs.items():
        if not set(ref.get('dataSources',[]))&targets and ref.get('dataSources')!=['Participants']:
            check('unrelated connection:'+key, new_refs.get(key)==ref)
    p_old=next(x for x in old_refs.values() if x.get('dataSources')==['Participants'])
    p_new=next(x for x in new_refs.values() if x.get('dataSources')==['Participants'])
    check('SharePoint binding unchanged',all(p_new[k]==v for k,v in p_old.items() if k!='dependents'))
    sources=json.loads(after['References/DataSources.json'])['DataSources']
    root=Path(__file__).resolve().parents[1]
    review=json.loads((root/'artifacts/core_batch/v1.0.0.1/TandemCoreBatch-v1.review.json').read_text())
    io=json.loads((root/'artifacts/core_batch/v1.0.0.1/flow-io.json').read_text())
    for name in targets:
        d=next(x for x in sources if x['Name']==name)
        check(name+':current core workflow',d['FlowNameId']==review['flows'][name]['id']==d['WorkflowEntityId'])
        xml=ET.fromstring(d['WadlMetadata']['WadlXml'])
        ns={'w':'http://wadl.dev.java.net/2009/02','s':'http://schemas.microsoft.com/MicrosoftProjectSiena/WADL/2014/11'}
        inputs={x.attrib['name'] for x in xml.findall('.//w:request/w:representation/w:param',ns)}
        outputs={x.attrib['name'] for x in xml.findall('.//s:object[@name="ResponseActionOutput"]/s:property',ns)}
        check(name+':inputs',inputs==set(next(iter(io[name]['trigger'].values()))['inputs']['schema']['properties']))
        check(name+':outputs',outputs==set(next(iter(io[name]['responses'].values()))['properties']))
    check('PAC YAML loading enabled',json.loads(after['packed.json'])['LoadConfiguration']['LoadFromYaml'] is True)
    s=after['Src/scrDiscovery.pa.yaml'].decode().replace('\r\n','\n')
    formulas=[json.loads(m[1]) for m in re.finditer(r'^\s+\w+: ("=.*")$',s,re.M)]
    assert formulas, 'no generated screen formulas'
    for formula in formulas:formula_sanity(formula)
    for forbidden in ['User().Email','Participantaccount','accountKey','WinningOperationKey','SourceRequestId']:
        check('no Discovery display:'+forbidden,forbidden not in s)
    result={'sourceTicket':16,'candidateVersion':'Discovery-v1',
            'sourceSha256':hashlib.sha256(Path(original).read_bytes()).hexdigest(),
            'candidateSha256':hashlib.sha256(Path(candidate).read_bytes()).hexdigest(),
            'testCount':len(checks),'allPassed':all(x['passed'] for x in checks),'checks':checks,
            'sourceFormulaSanity':{'checked':len(formulas),'result':'PASS: delimiters, quoting and alias separators only; not compilation'},
            'packager':'Microsoft.PowerApps.CLI.Tool 2.15.1 / canvas SourceCode',
            'powerFxCompilation':'NOT RUN: requires Power Apps Studio',
            'tenantFlowBinding':'NOT RUN','nativeImport':'NOT RUN','publishedVersion':None,
            'ordinaryParticipantAccess':'DEFERRED','runtimeFlowsChanged':0,
            'note':'PAC source overlay loads on Studio edit; Controls JSON and AppCheckerResult are the original cached files, not a new compilation result.'}
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('original');p.add_argument('candidate');p.add_argument('--report',required=True);a=p.parse_args()
    result=verify(a.original,a.candidate)
    Path(a.report).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['testCount','allPassed','candidateSha256','nativeImport']}))
    raise SystemExit(0 if result['allPassed'] else 1)
