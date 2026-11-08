"""Connector-free #9 synthetic proof. No live inputs, reads or writes."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED,ZipFile
from .build_import_probe import build_package as envelope
from .schema_audit import measure
from . import compatibility as rules

ROOT=Path(__file__).resolve().parents[2]
NAME='TandemCompatibilityProof'


def local_results(fixtures):
    cat=rules.normalize_catalogues(fixtures['catalogues'])
    profiles=rules.normalize_profiles(fixtures['profiles'],cat)
    lookup={p['profileId']:p for p in profiles};results=[]
    for case in fixtures['cases']:
        if case['kind']=='person':actual=rules.evaluate_pair(lookup[case['leftId']],lookup[case['rightId']])
        else:actual=rules.evaluate_group(case['group'],profiles,lookup[case['candidateId']],cat)
        results.append({'id':case['id'],'passed':actual==case['expected'],'actual':actual,'expected':case['expected']})
    return results


def append_result(actual,previous):
    return {'type':'AppendToArrayVariable','runAfter':{previous:['Succeeded']},'inputs':{'name':'TestResults','value':{
        'id':"@items('For_each_case')?['id']",'kind':"@items('For_each_case')?['kind']",
        'passed':f"@equals({actual},items('For_each_case')?['expected'])",'actual':'@'+actual,
        'expected':"@items('For_each_case')?['expected']"}}}


def definition_actions(fixtures,build_id,source_sha):
    actions={'Raw_profiles':rules.compose(fixtures['profiles']),
             'Raw_catalogues':rules.compose(fixtures['catalogues'],'Raw_profiles')}
    actions.update(rules.normalization_actions('Shared',"@outputs('Raw_profiles')","@outputs('Raw_catalogues')",'Raw_catalogues'))
    actions['Fixture_cases']=rules.compose(fixtures['cases'],'Shared_Catalogues')
    actions['Initialize_focus_checks']={'type':'InitializeVariable','inputs':{'variables':[{'name':'FocusChecks','type':'array','value':[]}]},'runAfter':{'Fixture_cases':['Succeeded']}}
    actions['Initialize_results']={'type':'InitializeVariable','inputs':{'variables':[{'name':'TestResults','type':'array','value':[]}]},'runAfter':{'Initialize_focus_checks':['Succeeded']}}
    people={
        'Find_left':rules.query("@body('Shared_Profiles')","equals(item()?['profileId'],items('For_each_case')?['leftId'])"),
        'Find_right':rules.query("@body('Shared_Profiles')","equals(item()?['profileId'],items('For_each_case')?['rightId'])",'Find_left'),
        'Person_result':rules.compose(rules.pair_expression_projection("first(body('Find_left'))","first(body('Find_right'))"),'Find_right')}
    people['Append_person_result']=append_result("outputs('Person_result')",'Person_result')
    groups={'Parse_group':{'type':'ParseJson','inputs':{'content':"@items('For_each_case')?['group']",'schema':rules.group_schema()},'runAfter':{}},
        'Find_members':rules.query("@body('Shared_Profiles')","contains(body('Parse_group')?['memberProfileIds'],item()?['profileId'])",'Parse_group'),
        'Find_candidate':rules.query("@body('Shared_Profiles')","equals(item()?['profileId'],items('For_each_case')?['candidateId'])",'Find_members')}
    groups.update(rules.group_action_fragment('Group',"body('Parse_group')","body('Find_members')","first(body('Find_candidate'))","outputs('Shared_Catalogues')",'FocusChecks','Find_candidate'))
    groups['Append_group_result']=append_result("outputs('Group_Result')",'Group_Result')
    actions['For_each_case']={'type':'Foreach','foreach':"@outputs('Fixture_cases')",'runAfter':{'Initialize_results':['Succeeded']},
        'runtimeConfiguration':{'concurrency':{'repetitions':1}},'actions':{
            'Reset_focus_checks':{'type':'SetVariable','inputs':{'name':'FocusChecks','value':[]},'runAfter':{}},
            'Case_kind':{'type':'If','expression':"@equals(items('For_each_case')?['kind'],'person')",'runAfter':{'Reset_focus_checks':['Succeeded']},'actions':people,'else':{'actions':groups}}}}
    actions['Failed_cases']=rules.query("@variables('TestResults')","not(equals(item()?['passed'],true))",'For_each_case')
    passed="and(empty(body('Failed_cases')),equals(length(variables('TestResults')),length(outputs('Fixture_cases'))))"
    actions['Proof_report']=rules.compose({'kind':NAME,'schemaVersion':1,'sourceTicket':9,'rulesVersion':rules.VERSION,
        'packageBuildId':build_id,'sourceSha256':source_sha,'runReference':"@workflow()?['run']?['name']",
        'syntheticOnly':True,'connectors':0,'writes':0,'testCount':"@length(variables('TestResults'))",
        'allPassed':'@'+passed,'failedCases':"@body('Failed_cases')",'results':"@variables('TestResults')"},'Failed_cases')
    actions['Require_all_passed']={'type':'If','expression':'@'+passed,'runAfter':{'Proof_report':['Succeeded']},'actions':{},'else':{'actions':{
        'Fail_proof':{'type':'Terminate','inputs':{'runStatus':'Failed','runError':{'code':'COMPATIBILITY_PROOF_FAILED','message':'See Proof_report failedCases; no live data accessed.'}},'runAfter':{}}}}}
    measure(actions)
    return actions


def build_package(output,fixture_path=None):
    output=Path(output)
    if any(p.exists() for p in [output,output.with_suffix('.definition.json'),output.with_suffix('.review.json')]):raise FileExistsError(output)
    fixture_path=Path(fixture_path or ROOT/'tests/fixtures/compatibility_v1.json')
    fixtures=json.loads(fixture_path.read_text(encoding='utf-8'))
    results=local_results(fixtures)
    if any(not r['passed'] for r in results):raise ValueError('Fixture mismatch: '+','.join(r['id'] for r in results if not r['passed']))
    source_sha=hashlib.sha256(Path(rules.__file__).read_bytes()).hexdigest()
    with TemporaryDirectory() as temp:
        base=Path(temp)/'base.zip';doc=envelope(base)
        with ZipFile(base) as archive:entries={n:json.loads(archive.read(n)) for n in archive.namelist()}
    doc['properties']['displayName']=NAME
    doc['properties']['definition']['actions']=definition_actions(fixtures,doc['name'],source_sha)
    metrics=measure(doc['properties']['definition']['actions'])
    for name in entries:
        if name.endswith('/definition.json'):entries[name]=doc
    entries['manifest.json']['details'].update(displayName=NAME+'-package',description='Issue 9 disposable synthetic contract proof. No connectors, live input, reads or writes.')
    resource=next(r for r in entries['manifest.json']['resources'].values() if r['type']=='Microsoft.Flow/flows');resource['details']['displayName']=NAME
    output.parent.mkdir(parents=True,exist_ok=True)
    with ZipFile(output,'x',ZIP_DEFLATED) as archive:
        for n,p in entries.items():archive.writestr(n,json.dumps(p,indent=2)+'\n')
    review={'sourceTicket':9,'flowName':NAME,'packageBuildId':doc['name'],'rulesVersion':rules.VERSION,'sourceSha256':source_sha,
        'fixturesSha256':hashlib.sha256(fixture_path.read_bytes()).hexdigest(),'packageSha256':hashlib.sha256(output.read_bytes()).hexdigest(),
        **metrics,'limits':{'actions':500,'nesting':8},'syntheticOnly':True,'productionFlow':False,'connectors':0,'liveReads':0,'writes':0,
        'caseCount':len(results),'localExpectedResults':'PASS','tenantResult':'NOT_IMPORTED_NOT_TESTED','anyLanguagePolicy':rules.ANY_LANGUAGE_POLICY}
    output.with_suffix('.definition.json').write_bytes((json.dumps(doc,indent=2)+'\n').encode('utf-8'))
    output.with_suffix('.review.json').write_bytes((json.dumps(review,indent=2)+'\n').encode('utf-8'))
    return review


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args();print(json.dumps(build_package(args.output),indent=2))


if __name__=='__main__':main()
