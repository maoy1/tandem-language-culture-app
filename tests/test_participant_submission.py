import json
import re
from copy import deepcopy
from pathlib import Path
from zipfile import ZipFile

import pytest
from scripts.power_automate import participant_submission as flow


@pytest.fixture
def source():
    mapping=json.loads((flow.ROOT/'config/tenant_schema_mapping.json').read_text(encoding='utf-8'))
    params={'dataset':'https://example.sharepoint.com/sites/test','table':mapping['lists']['participants']['listId']}
    return {'properties':{'definition':{'triggers':{'When_an_item_is_created_or_modified':{
        'type':'OpenApiConnection','recurrence':{'frequency':'Minute','interval':1},
        'splitOn':"@triggerOutputs()?['body/value']",'inputs':{'parameters':params,'host':{
            'operationId':'GetOnUpdatedItems','connectionName':flow.CONNECTOR}}}},
        'parameters':{'$authentication':{'type':'SecureObject','defaultValue':{}},'$connections':{'type':'Object','defaultValue':{}}},
        'actions':{'Get_item':{'type':'OpenApiConnection','inputs':{'parameters':{**params,'id':"@triggerBody()?['ID']"},'host':{'operationId':'GetItem'}}}}}}}


@pytest.fixture
def definition(source):
    mapping=json.loads((flow.ROOT/'config/tenant_schema_mapping.json').read_text(encoding='utf-8'))
    return flow.build_definition(source,mapping,'test-build')


def evaluate(expression, bodies, outputs):
    """Tiny independent evaluator for this flow's pure validation expressions only.

    Not a Power Automate runtime/import test. Data accesses are resolved before
    evaluating the fixed generated function expression in a restricted scope.
    """
    pattern=r"(body|outputs)\('([^']+)'\)((?:\?\['[^']+'\])*)"
    def resolve(match):
        value=(bodies if match[1]=='body' else outputs)[match[2]]
        for key in re.findall(r"\?\['([^']+)'\]",match[3]): value=value.get(key)
        return repr(value)
    expr=re.sub(pattern,resolve,expression.lstrip('@'))
    for old,new in [('and','AND'),('or','OR'),('not','NOT'),('if','IF')]:
        expr=re.sub(r'\b'+old+r'\(',new+'(',expr)
    expr=re.sub(r'\bnull\b','None',expr)
    return eval(expr,{'__builtins__':{}},{'AND':lambda *v:all(v),'OR':lambda *v:any(v),'NOT':lambda v:not v,
        'IF':lambda c,a,b:a if c else b,'equals':lambda a,b:a==b,'greater':lambda a,b:a>b,
        'coalesce':lambda *v:next((x for x in v if x is not None),None),'empty':lambda v:not v,
        'contains':lambda a,b:b in a,'length':len,'intersection':lambda a,b:list(set(a)&set(b))})


@pytest.mark.parametrize('languages,cultures,zone,account,expected',[
    ([61],[],None,4,True),([], [5],None,4,True),([61],[5],37,4,True),
    ([],[],None,4,False),([999],[],None,4,False),([],[999],None,4,False),
    ([61,999],[],None,4,False),([61],[],999,4,False),([61],[],None,None,False),
    ([61],[],None,0,False),([61,61],[],None,4,False),
])
def test_validation_rule_on_valid_invalid_and_mixed_ids(definition,languages,cultures,zone,account,expected):
    # Selected_language/culture union actions deduplicate prior to this rule.
    bodies={'Current_item':{'ParticipantaccountId':account,'TimezoneId':zone},
            'IDs_language':[61,84], 'IDs_culture':[5], 'IDs_timezone':[37]}
    outputs={'Selected_language':languages,'Selected_culture':cultures}
    valid=evaluate(definition['actions']['Profile_valid']['inputs'],bodies,outputs)
    assert valid is expected
    outputs['Profile_valid']=valid
    assert evaluate(definition['actions']['Desired_status']['inputs'],bodies,outputs)==('Active' if expected else 'Needs review')


def test_only_conditional_versioned_status_patch_is_possible(definition):
    writes=[]
    for _,action,_ in flow.walk(definition['actions']):
        params=action.get('inputs',{}).get('parameters',{}) if isinstance(action.get('inputs'),dict) else {}
        if params.get('parameters/method')=='POST': writes.append(action)
        assert params.get('parameters/method') not in ['PATCH','DELETE']
    assert len(writes)==1
    patch=writes[0]['inputs']; params=patch['parameters']
    assert set(params['parameters/body'])=={'__metadata','Status'}
    assert params['parameters/headers']['IF-MATCH']=="@body('Current_item')?['__metadata']?['etag']"
    assert params['parameters/headers']['X-HTTP-Method']=='MERGE'
    assert patch['retryPolicy']=={'type':'none'}
    conditional=definition['actions']['Status_changed']
    assert 'not(equals' in conditional['expression']
    assert not conditional['else']['actions']
    assert conditional['actions']['Verify_status']['runAfter']=={'Update_validation_status':['Succeeded']}


def test_failed_incomplete_or_malformed_reads_cannot_report_success(definition):
    actions=definition['actions']; gate=actions['Require_complete_reads']
    assert gate['else']['actions']['Fail_incomplete_reads']['inputs']['runStatus']=='Failed'
    for role in ['language','culture','timezone']:
        assert f"body('Parsed_{role}')?['__next']" in gate['expression']
        schema=actions['Parsed_'+role]['inputs']['schema']
        assert 'results' in schema['required']
        assert schema['properties']['results']['items']['required']==['Id','Active']
    current=actions['Current_item']['inputs']['schema']
    assert all(f+'Id' in current['required'] for f in flow.FIELDS)
    for _,action,_ in flow.walk(actions):
        assert all(states==['Succeeded'] for states in action.get('runAfter',{}).values())
    assert actions['Validation_report']['runAfter']=={'Status_changed':['Succeeded']}


def test_mapping_and_trigger_preserved_and_no_availability_dependency(definition,source):
    assert definition['triggers']==source['properties']['definition']['triggers']
    assert 'ParticipationStatus' not in json.dumps(definition)
    assert 'OpenToConnections' not in json.dumps(definition)
    assert 'group' not in json.dumps(definition).lower()
    assert 'Read_current' in definition['actions']


def test_package_new_ids_no_source_connection_details_and_hashes(tmp_path,source):
    original=tmp_path/'source.zip'
    with ZipFile(original,'w') as z: z.writestr('Microsoft.Flow/flows/old/definition.json',json.dumps(source))
    output=tmp_path/'output.zip'; review=flow.build_package(original,output)
    assert review['sourceTriggerPreserved']
    assert review['tenantResult']=='NOT_IMPORTED_NOT_TESTED'
    assert review['actionDefinitions'] < 500 and review['maximumNesting']<=8
    with ZipFile(output) as z:
        assert len(z.namelist())==5
        manifest=json.loads(z.read('manifest.json'))
        resource=next(x for x in manifest['resources'].values() if x['type']=='Microsoft.Flow/flows')
        assert resource['suggestedCreationType']=='New'
        doc=json.loads(z.read(next(n for n in z.namelist() if n.endswith('/definition.json'))))
        assert doc['properties']['connectionReferences'][flow.CONNECTOR]['connectionName']=='IMPORT_SELECT_EXISTING_SHAREPOINT_CONNECTION'
    with pytest.raises(FileExistsError): flow.build_package(original,output)


def test_changed_source_binding_or_trigger_is_rejected(tmp_path,source):
    source['properties']['definition']['actions']['Get_item']['inputs']['parameters']['id']='wrong'
    p=tmp_path/'source.zip'
    with ZipFile(p,'w') as z: z.writestr('x/definition.json',json.dumps(source))
    with pytest.raises(ValueError,match='Current-item reference'): flow.source_definition(p)


def test_limits_count_all_branches_and_reject_depth():
    with pytest.raises(ValueError): flow.gate({'actions':{f'a{i}':{'type':'Compose'} for i in range(501)}})
    branch={'leaf':{'type':'Compose'}}
    for i in range(8): branch={f'if{i}':{'type':'If','else':{'actions':branch}}}
    with pytest.raises(ValueError): flow.gate({'actions':branch})
