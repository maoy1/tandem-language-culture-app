from copy import deepcopy
import json
from zipfile import ZipFile
import pytest
from scripts.power_automate import compatibility as rules
from scripts.power_automate import build_compatibility_proof as proof


@pytest.fixture
def fixture_data():
    return json.loads((proof.ROOT/'tests/fixtures/compatibility_v1.json').read_text(encoding='utf-8'))


def test_all_independent_expected_fixtures(fixture_data):
    results=proof.local_results(fixture_data)
    assert len(results)==39
    assert all(r['passed'] for r in results),[r for r in results if not r['passed']]


def walk(actions,path=()):
    for n,a in actions.items():
        yield path+(n,),a,len(path)+1
        yield from walk(a.get('actions',{}),path+(n,))
        yield from walk(a.get('else',{}).get('actions',{}),path+(n,))


def test_rules_emit_no_raw_personal_identity_and_no_ui_logic(fixture_data):
    actions=proof.definition_actions(fixture_data,'synthetic-build','hash')
    projection=actions['For_each_case']['actions']['Case_kind']['actions']['Person_result']['inputs']
    assert set(projection)=={'eligible','fitType','canLearnLanguageIds','canShareLanguageIds','canLearnCultureIds','canShareCultureIds'}
    assert 'accountKey' not in projection
    assert 'Comments' not in json.dumps(actions) and 'DisplayName' not in json.dumps(actions)
    assert not any(a['type']=='OpenApiConnection' for _,a,_ in walk(actions))


@pytest.mark.parametrize('field,value',[
    ('teachIds',['1']),('learnIds',[True]),('shareCultureIds',[-1]),('learnCultureIds',[999]),
    ('timezoneId',999),('openToConnections',None),('participationStatus',None),('accountKey','  '),('profileId',True)])
def test_bad_profile_input_rejected_instead_of_coerced(fixture_data,field,value):
    data=deepcopy(fixture_data['profiles']);data[0][field]=value
    with pytest.raises(ValueError):rules.normalize_profiles(data,rules.normalize_catalogues(fixture_data['catalogues']))


def test_null_optional_fields_dedup_and_optional_timezone(fixture_data):
    cat=rules.normalize_catalogues(fixture_data['catalogues']);normalized=rules.normalize_profiles(fixture_data['profiles'],cat)
    assert normalized[13]['teachIds']==[2] and normalized[13]['learnIds']==[]
    assert normalized[0]['accountKey']=='synthetic-1' and normalized[0]['timezoneId'] is None
    assert normalized[12]['learnIds']==[]


def test_duplicate_canonical_identity_and_batch_limit_are_rejected(fixture_data):
    cat=rules.normalize_catalogues(fixture_data['catalogues']);data=deepcopy(fixture_data['profiles'])
    data[1]['accountKey']='  synthetic-1 '
    with pytest.raises(ValueError,match='Duplicate canonical'):rules.normalize_profiles(data,cat)
    with pytest.raises(ValueError,match='batch'):rules.normalize_profiles(data*501,cat)


def test_ineligible_person_has_no_matching_detail_projection(fixture_data):
    results={r['id']:r for r in proof.local_results(fixture_data)}
    for case in ['PAIR_PAUSED','PAIR_CLOSED','PAIR_REVIEW','PAIR_INACTIVE','PAIR_SELF']:
        r=results[case]['actual'];assert not r['eligible'] and r['fitType'] is None
        assert all(r[k]==[] for k in r if k.endswith('Ids'))


def test_distinct_sharer_learner_and_every_focus_required(fixture_data):
    rule=rules.distinct_relationship()
    assert not rule.evaluate({'sharers':[1],'learners':[1]})
    assert rule.evaluate({'sharers':[1,2],'learners':[1]})
    assert not rule.evaluate({'sharers':[],'learners':[1]})
    results={r['id']:r['actual'] for r in proof.local_results(fixture_data)}
    assert results['GROUP_COMBINED_SPLIT_ROLES']['compatible']
    assert not results['GROUP_UNSUPPORTED_DECLARED_FOCUS']['purposeValid']
    assert not results['GROUP_UNRELATED_EXISTING_MEMBER']['purposeValid']


def test_group_state_and_membership_are_not_changed_by_matching(fixture_data):
    original=deepcopy(fixture_data);results={r['id']:r['actual'] for r in proof.local_results(fixture_data)}
    assert fixture_data==original
    for name in ['GROUP_CLOSED','GROUP_ENDED','GROUP_FULL_OPEN','GROUP_SETUP_INCOMPLETE',
                 'GROUP_SHARER_AVAILABILITY_UNVERIFIED','GROUP_PAUSED_MEMBER_NOT_DROPPED_FROM_COUNT']:
        assert not results[name]['compatible']


def test_normalization_flow_rejects_bad_data_before_consumer(fixture_data):
    a=rules.normalization_actions('Contract',"@outputs('Raw_profiles')","@outputs('Raw_catalogues')")
    assert a['Contract_Parse_profiles']['inputs']['schema']['items']['properties']['openToConnections']['type']=='boolean'
    guard=a['Contract_Require_valid_input'];expr=guard['expression']
    assert 'Contract_Invalid_profiles' in expr and 'Contract_Keys_accountKey' in expr and 'Contract_Keys_profileId' in expr
    assert guard['else']['actions']['Contract_Reject_input']['inputs']['runStatus']=='Failed'
    assert a['Contract_Catalogues']['runAfter']=={'Contract_Require_valid_input':['Succeeded']}
    with pytest.raises(ValueError):rules.normalization_actions('bad prefix','x','y')


def test_harness_serializes_array_accumulators_and_never_returns_false_success(fixture_data):
    a=proof.definition_actions(fixture_data,'id','hash')
    loops=[action for _,action,_ in walk(a) if action['type']=='Foreach']
    assert len(loops)==3
    assert all(v['runtimeConfiguration']['concurrency']['repetitions']==1 for v in loops)
    assert a['Proof_report']['runAfter']=={'Failed_cases':['Succeeded']}
    assert 'equals(length' in a['Proof_report']['inputs']['allPassed']
    assert a['Require_all_passed']['else']['actions']['Fail_proof']['inputs']['runStatus']=='Failed'
    assert all(states==['Succeeded'] for _,action,_ in walk(a) for states in action.get('runAfter',{}).values())


def test_import_package_is_connector_free_bounded_and_hashes_source(tmp_path,fixture_data):
    p=tmp_path/'proof.zip';review=proof.build_package(p)
    assert review['connectors']==review['writes']==review['liveReads']==0
    assert review['actions']<=500 and review['maximumActionDepth']<=8
    assert review['caseCount']==39 and review['tenantResult']=='NOT_IMPORTED_NOT_TESTED'
    with ZipFile(p) as z:
        assert json.loads(z.read(next(n for n in z.namelist() if n.endswith('/connectionsMap.json'))))=={}
        d=json.loads(z.read(next(n for n in z.namelist() if n.endswith('/definition.json'))))
        assert d['properties']['connectionReferences']=={}
        assert not any(a['type']=='OpenApiConnection' for _,a,_ in walk(d['properties']['definition']['actions']))
    with pytest.raises(FileExistsError):proof.build_package(p)
