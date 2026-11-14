"""Static activation hazards, without changing or executing a deployed flow."""
from copy import deepcopy
import json
from pathlib import Path

from scripts.power_automate.activation_graph import analyze, expression_calls


ROOT = Path(__file__).resolve().parents[1]
DEFINITIONS = ROOT / 'artifacts/core_batch/v1.0.0.1/definitions'


def compose(value=0, after=None):
    return {'type': 'Compose', 'inputs': value, 'runAfter': {after: ['Succeeded']} if after else {}}


def codes(actions):
    return {finding['code'] for finding in analyze({'actions': actions})}


def test_current_batch_exposes_three_case_collisions_and_projected_cycle():
    document = json.loads((DEFINITIONS / 'TandemRespondGroupJoinRequest.json').read_text())
    findings = analyze(document)
    assert [f['actions'] for f in findings if f['code'] == 'CASE_ONLY_ACTION_COLLISION'] == [
        ['Initial_request', 'Initial_Request'],
        ['Initial_request_Save', 'Initial_Request_Save'],
        ['Initial_request_Tag', 'Initial_Request_Tag'],
    ]
    assert not any(f['code'] == 'DEPENDENCY_CYCLE' for f in findings)
    projected = [f for f in findings if f['code'] == 'CASE_FOLDED_DEPENDENCY_CYCLE']
    assert projected and all(f['nativeConfirmed'] is False for f in projected)
    assert any('member_type:start' in f['cycle'] and 'initial_request:start' in f['cycle'] for f in projected)


def test_proposed_bootstrap_rename_clears_graph_in_memory_only():
    document = json.loads((DEFINITIONS / 'TandemRespondGroupJoinRequest.json').read_text())
    document = deepcopy(document)
    block = document['properties']['definition']['actions']['Business']['actions']
    rename = {n: n.replace('Initial_request', 'Bootstrap_request') for n in
              ('Initial_request', 'Initial_request_Save', 'Initial_request_Tag')}
    # These names occur only as action keys, runAfter keys and WDL references.
    text = json.dumps(document)
    for old, new in rename.items():
        text = text.replace('"' + old + '"', '"' + new + '"').replace("'" + old + "'", "'" + new + "'")
    assert set(rename) <= set(block)
    assert analyze(json.loads(text)) == []


def test_no_other_batch_graph_findings():
    for path in DEFINITIONS.glob('*.json'):
        if path.stem == 'TandemLeaveGroup':
            assert analyze(json.loads(path.read_text())) == [{'code':'SELF_VARIABLE_UPDATE','action':'Require_receipt_ready_code','variable':'Code'}]
        elif path.stem != 'TandemRespondGroupJoinRequest':
            assert analyze(json.loads(path.read_text())) == [], path.name


def test_repaired_consumer_sources_clear_both_native_hazards():
    for file in ['artifacts/group_response/TandemRespondGroupJoinRequest-activation.definition.json',
                 'artifacts/leave_group/TandemLeaveGroup-v1-activation.definition.json']:
        assert analyze(json.loads((ROOT/file).read_text()))==[]


def test_self_variable_assignment_is_rejected_without_inventing_cross_variable_cycle():
    init={'type':'InitializeVariable','inputs':{'variables':[{'name':'Code','type':'string','value':''}]}}
    actions={'Init':init,'Bad':{'type':'SetVariable','inputs':{'name':'Code','value':"@if(empty(variables('Code')),'FAIL',variables('Code'))"},'runAfter':{'Init':['Succeeded']}}}
    assert codes(actions)=={'SELF_VARIABLE_UPDATE'}
    actions['Bad']={'type':'Compose','inputs':"@variables('Code')",'runAfter':{'Init':['Succeeded']}}
    assert codes(actions)==set()


def test_exact_cycle():
    assert 'DEPENDENCY_CYCLE' in codes({'A': compose(after='B'), 'B': compose(after='A')})


def test_scope_completion_cycle():
    actions = {'Scope': {'type': 'Scope', 'actions': {'Inner': compose("@outputs('Later')")}},
               'Later': compose(after='Scope')}
    assert 'DEPENDENCY_CYCLE' in codes(actions)


def test_items_parent_is_context_not_completion_dependency():
    actions = {'Loop': {'type': 'Foreach', 'foreach': '@createArray(1)',
                        'actions': {'Inner': compose("@items('Loop')")}}}
    assert codes(actions) == set()


def test_cross_loop_reference_and_cross_scope_run_after():
    actions = {'Loop': {'type': 'Foreach', 'foreach': '@createArray(1)',
                        'actions': {'Inner': compose()}},
               'Outer': compose("@items('Loop')", after='Inner')}
    assert codes(actions) == {'INVALID_LOOP_REFERENCE', 'INVALID_RUN_AFTER_SCOPE'}


def test_quoted_rest_items_and_literal_function_text_do_not_add_edges():
    expression = "@concat('_api/items(''fake'')',string(body('Read')?['Id']),')')"
    assert list(expression_calls(expression)) == [('concat', "_api/items('fake')"), ('body', 'Read')]
    assert list(expression_calls("@@outputs('Literal')")) == []
    assert codes({'Read': compose(), 'Next': compose(expression, 'Read')}) == set()


def test_variable_initialization_dependency_not_future_write():
    actions = {'Init': {'type': 'InitializeVariable', 'inputs': {
        'variables': [{'name': 'Counter', 'type': 'integer', 'value': 0}]}},
        'Read': compose("@variables('Counter')", 'Init'),
        'Write': {'type': 'SetVariable', 'inputs': {'name': 'Counter', 'value': 1},
                  'runAfter': {'Read': ['Succeeded']}}}
    assert codes(actions) == set()
    actions['Init']['inputs']['variables'][0]['value'] = "@outputs('Read')"
    assert 'DEPENDENCY_CYCLE' in codes(actions)


def test_exact_duplicate_in_different_scopes_is_not_silently_overwritten():
    assert 'DUPLICATE_ACTION_NAME' in codes({
        'One': {'type': 'Scope', 'actions': {'Repeated': compose()}},
        'Two': {'type': 'Scope', 'actions': {'Repeated': compose()}},
    })
