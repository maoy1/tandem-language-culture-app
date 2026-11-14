"""Execute emitted #7 parent with actual packaged #81 child, fake SharePoint only."""
from copy import deepcopy
import json
from pathlib import Path
import pytest
from scripts.power_automate import discovery_shared_consumer as consumer
from scripts.power_automate.schema_audit import measure
from test_discovery_flow import Fake, PEOPLE, GROUPS, source, profile
from test_shared_validation import ChildRunner, NoIO

from scripts.power_automate import shared_validation as shared
BASELINE=json.loads((consumer.ROOT/'config/shared_validation_schema.json').read_text())
CHILD=shared.definition_actions(BASELINE,'batch-test-build','rules-hash')


class Backend:
    def __init__(self,server,alter=None):self.server=server;self.calls=[];self.alter=alter
    def request(self,p):
        if '_workflow' not in p:return self.server.request(p)
        assert p['_workflow']['host']=={'workflowReferenceName':consumer.CHILD_ID}
        payload=p['_workflow']['body'];self.calls.append(json.loads(payload['text']))
        child=ChildRunner(NoIO());child.run(deepcopy(CHILD),{'items':{},'triggerBody':payload})
        response=deepcopy(child.response)
        if self.alter:self.alter(response,self.calls[-1])
        return {'statusCode':200,'body':response}


class ParentRunner(ChildRunner):
    def run(self,actions,ctx=None):
        # Interpreter transport extension only: route native Workflow inputs to
        # the real child action graph; never substitute a rule implementation.
        adapted=deepcopy(actions)
        for a in adapted.values():
            if a['type']=='Workflow':
                a['type']='OpenApiConnection';a['inputs']={'parameters':{'_workflow':a['inputs']}}
        return super().run(adapted,ctx)


def execute(server=None,actor=1,alter=None):
    backend=Backend(server or Fake(),alter);runner=ParentRunner(backend,actor)
    runner.run(consumer.build_actions(source(),PEOPLE,GROUPS,'test-build'))
    return runner,backend


def test_populated_people_real_child_projection_and_optional_zone():
    r,b=execute();assert r.response['resultcode']=='OK'
    rows=json.loads(r.response['candidatesjson']);assert [p['profileId'] for p in rows]==[2,3]
    assert rows[0]['fitType']=='Language'
    assert rows[0]['profile']['timeZone']=={'id':None,'label':None,'ianaId':None}
    assert rows[0]['profile']['comments']=='Approved comments'
    assert [c['mode'] for c in b.calls]==['NORMALIZE','PAIRS']
    assert not any(s in json.dumps(r.response) for s in ['PRIVATE_','accountKey','Claims','trusted-'])


def test_culture_only_and_any_not_wildcard():
    s=Fake();s.profiles=[profile(1,share=[1]),profile(2,culture=[1]),profile(3,[99],[99])]
    r,b=execute(s);rows=json.loads(r.response['candidatesjson'])
    assert r.response['resultcode']=='OK' and [p['profileId'] for p in rows]==[2] and rows[0]['fitType']=='Culture'


@pytest.mark.parametrize('actor,own',[(2,1),(1,2)])
def test_wrong_reference_stops_before_candidate_or_child_reads(actor,own):
    s=Fake();s.own_id=own;r,b=execute(s,actor)
    assert r.response['resultcode']=='UNAUTHORIZED_PROFILE' and not b.calls
    assert 'GetItems' not in s.queries and 'GetItem' not in s.queries


@pytest.mark.parametrize('field,value',[('ParticipationStatus',{'Value':'Paused'}),('ParticipationStatus',None),('OpenToConnections',False),('Status',{'Value':'Needs review'})])
def test_candidate_unavailable_excluded_without_writes(field,value):
    s=Fake();s.profiles[1][field]=value;before=deepcopy(s.profiles);r,b=execute(s)
    assert r.response['resultcode']=='OK'
    assert [p['profileId'] for p in json.loads(r.response['candidatesjson'])]==[3]
    assert s.profiles==before


@pytest.mark.parametrize('change',['valid','closed','full','member','uncommitted','duplicate','missingProfile','pausedSharer','left','invalidFocus'])
def test_group_current_commitment_capacity_and_real_child(change):
    s=Fake();s.valid_group()
    if change=='closed':s.groups[0]['State']='Closed'
    if change=='full':s.groups[0]['Capacity']=2
    if change=='member':s.members[1]['ParticipantId']=1;s.members[1]['MembershipKey']='request:70:participant:1'
    if change=='uncommitted':s.requests[0]['OperationComplete']=False
    if change=='duplicate':s.members.append(deepcopy(s.members[0]))
    if change=='missingProfile':s.profiles.pop()
    if change=='pausedSharer':s.profiles[1]['ParticipationStatus']={'Value':'Paused'}
    if change=='left':s.members[0]['MembershipStatus']='Left'
    if change=='invalidFocus':s.groups[0]['LanguageFocusId']={'results':[2]}
    before=deepcopy((s.groups,s.members,s.requests));r,b=execute(s)
    assert r.response['resultcode']=='OK',r.action_states
    rows=json.loads(r.response['groupsjson']);assert bool(rows)==(change=='valid')
    if rows:
        assert rows[0]['memberCount']==2 and rows[0]['freeSlots']==1
        assert [m['displayName'] for m in rows[0]['members']]==['Person 2','Person 3']
    assert (s.groups,s.members,s.requests)==before
    assert not any('/fields?' in str(q) for q in s.queries)


@pytest.mark.parametrize('role',['profiles','language','groups','members','requests'])
def test_incomplete_read_returns_no_partial_results(role):
    s=Fake();s.valid_group();s.paged=role;r,b=execute(s)
    assert r.response['resultcode']!='OK' and r.response['candidatesjson']==r.response['groupsjson']=='[]'


@pytest.mark.parametrize('fault',['version','failed','malformed','code','eligibleFalse'])
def test_child_failure_and_success_does_not_imply_eligibility(fault):
    def alter(response,request):
        if request['mode']!='PAIRS':return
        v=json.loads(response['resultjson'])
        if fault=='version':v['rulesVersion']=2
        if fault=='failed':response['success']=False
        if fault=='code':response['resultcode']='INVALID_INPUT'
        if fault=='eligibleFalse':
            for pair in v['result']['pairs']:pair['eligible']=False
        response['resultjson']='broken' if fault=='malformed' else json.dumps(v)
    r,b=execute(alter=alter)
    if fault=='eligibleFalse':assert r.response['resultcode']=='OK' and r.response['candidatesjson']=='[]'
    else:assert r.response['resultcode']!='OK' and r.response['candidatesjson']==r.response['groupsjson']=='[]'


def test_emitted_parent_gate_connections_no_writes_no_embedded_rules():
    a=consumer.build_actions(source(),PEOPLE,GROUPS,'test');metrics=measure(a)
    assert metrics['actions']<=500 and metrics['maximumActionDepth']<=8
    text=json.dumps(a)
    assert 'workflowReferenceName' in text and consumer.CHILD_ID in text
    assert 'Shared_Invalid_profiles' not in text and 'Group_fit_Unrelated_members' not in text
    assert '/fields?' not in text and 'SCHEMA' not in text
    def walk(actions):
        for action in actions.values():
            yield action
            for container in [action.get('actions',{}),action.get('else',{}).get('actions',{})]:yield from walk(container)
    for action in walk(a):
        if action['type']=='OpenApiConnection':assert action['inputs']['parameters'].get('parameters/method','GET')=='GET'

@pytest.mark.parametrize('value',[None,'missing','yes'])
def test_missing_or_malformed_commit_rows_fail_without_partial_people(value):
    s=Fake();s.valid_group()
    if value=='missing':del s.requests[0]['OperationComplete']
    else:s.requests[0]['OperationComplete']=value
    r,b=execute(s)
    assert r.response['resultcode']!='OK' and r.response['candidatesjson']==r.response['groupsjson']=='[]'


@pytest.mark.parametrize('case',['test_failed_backend_read_sanitizes_response','test_oversized_response_returns_explicit_bound',
 'test_invalid_noninteger_reference_cannot_read_data','test_stale_invalid_candidate_catalogue_selection_is_excluded',
 'test_group_work_budget_stops_large_focus_loops','test_unexpected_structured_note_cannot_escape_public_projection'])
def test_existing_independent_discovery_expectations_against_real_child(case,monkeypatch):
    import test_discovery_flow as old
    monkeypatch.setattr(old,'execute',lambda server=None,actor=1:execute(server,actor)[0])
    getattr(old,case)()


def test_component_builder_preserves_trigger_and_invoker_without_source_identity(tmp_path):
    from zipfile import ZipFile
    original=source();original['name']='PRIVATE_SOURCE_ID'
    original['properties']['definition']['metadata']={'creator':'PRIVATE_CREATOR'}
    original['properties']['connectionReferences']['shared_sharepointonline']['connectionName']='PRIVATE_CONNECTION'
    src=tmp_path/'native.zip'
    with ZipFile(src,'w') as z:z.writestr('Microsoft.Flow/flows/native/definition.json',json.dumps(original))
    output=tmp_path/'parent.json';review=consumer.build_package(src,output)
    doc=json.loads(output.read_text());assert doc['properties']['definition']['triggers']==original['properties']['definition']['triggers']
    assert not any(s in output.read_text() for s in ['PRIVATE_SOURCE_ID','PRIVATE_CREATOR','PRIVATE_CONNECTION'])
    assert doc['properties']['connectionReferences']['shared_sharepointonline']['source']=='Invoker'
    assert review['actions']<=500 and review['maximumActionDepth']<=8 and not review['ordinaryUserAccessVerified']
    with pytest.raises(FileExistsError):consumer.build_package(src,output)
    original['properties']['connectionReferences']['shared_sharepointonline']['source']='Embedded'
    with pytest.raises(ValueError,match='Invoker'):consumer.build_actions(original,PEOPLE,GROUPS,'reject')


def test_committed_artifact_metrics_and_child_fingerprint():
    import hashlib
    artifact=consumer.ROOT/'artifacts/tandem_discovery/TandemDiscovery-shared.definition.json'
    review=json.loads(artifact.with_suffix('.review.json').read_text())
    doc=json.loads(artifact.read_text());assert hashlib.sha256(artifact.read_bytes()).hexdigest()==review['definitionSha256']
    # Native envelope differs from synthetic input; structure and exact deployed
    # child graph fingerprint remain independently checked.
    assert measure(doc['properties']['definition']['actions'])=={k:review[k] for k in ['actions','maximumActionDepth']}
    assert hashlib.sha256((consumer.ROOT/'scripts/power_automate/shared_validation.py').read_bytes()).hexdigest()==review['sharedChildSourceSha256']
    assert review['requiredSharedModes']==['NORMALIZE','PAIRS','GROUP']

@pytest.mark.parametrize('kind',['profiles','renderedPeople','childRequest'])
def test_search_and_child_request_budgets_never_return_partial_arrays(kind):
    s=Fake()
    if kind=='profiles':s.profiles=[profile(i,[2],[1]) for i in range(1,502)]
    elif kind=='renderedPeople':s.profiles=[profile(1,[1],[2])]+[profile(i,[2],[1]) for i in range(2,53)]
    else:s.profiles[0]['Participantaccount']['Claims']='a'*250001
    r,b=execute(s)
    assert r.response['resultcode']!='OK' and r.response['candidatesjson']==r.response['groupsjson']=='[]'
    if kind in ['profiles','childRequest']:assert not b.calls


def test_bulk_child_failure_returns_no_partial_results():
    def alter(response,request):
        if request['mode']=='PAIRS':response['success']=False
    r,b=execute(alter=alter)
    assert len(r.variables['People'])==0
    assert r.response['resultcode']!='OK' and r.response['candidatesjson']==r.response['groupsjson']=='[]'


def test_group_evaluation_success_is_not_join_eligibility():
    s=Fake();s.valid_group()
    def alter(response,request):
        if request['mode']=='GROUP':
            value=json.loads(response['resultjson']);value['result']['compatible']=False;response['resultjson']=json.dumps(value)
    r,b=execute(s,alter=alter)
    assert r.response['resultcode']=='OK' and r.response['groupsjson']=='[]'


def test_component_generator_receipt_fingerprint():
    import hashlib
    review=json.loads((consumer.ROOT/'artifacts/tandem_discovery/TandemDiscovery-shared.definition.review.json').read_text())
    assert hashlib.sha256(Path(consumer.__file__).read_bytes()).hexdigest()==review['generatorSha256']


def test_candidate_set_uses_one_bulk_pair_child_call():
    s=Fake();s.profiles=s.profiles[:2]+[profile(i,teach=[1]) for i in range(3,35)]
    runner,backend=execute(s)
    assert runner.response['resultcode']=='OK'
    assert [c['mode'] for c in backend.calls]==['NORMALIZE','PAIRS']
    assert [p['profileId'] for p in json.loads(runner.response['candidatesjson'])]==[2]
