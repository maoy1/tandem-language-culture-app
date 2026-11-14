"""Execute #11's real generated WDL with a fake SharePoint and real child graph.

These tests prove neither native connector semantics nor tenant authority.
"""
from collections import defaultdict
from copy import deepcopy
import json
import re
from zipfile import ZipFile
from uuid import uuid5, NAMESPACE_URL

import pytest

from scripts.power_automate import respond_request as flow
from scripts.power_automate.schema_audit import measure
from test_discovery_flow import FlowRunner, validate
from test_shared_validation import execute as evaluate_child
from test_coordination_fixture import walk


def profile(id_, teach=None, learn=None, share=None, culture=None, **changes):
    return {
        'Id': id_, 'ParticipantaccountId': id_ + 100, 'Status': 'Active',
        'ParticipationStatus': 'Active', 'OpenToConnections': True, 'TimezoneId': None,
        'TeachlanguagesId': {'results': teach or []}, 'LearnlanguagesId': {'results': learn or []},
        'ShareCulturesId': {'results': share or []}, 'LearnCulturesId': {'results': culture or []},
        **changes}


def input_(**changes):
    return {'number': 38, 'number_1': 70, 'text': 'Accept', 'text_1': 'Practice',
            'text_2': 'Language', 'number_2': 3, 'text_3': '[1]', 'text_4': '[]',
            'text_5': '11111111-2222-4333-8444-555555555555', **changes}


def validate_native(value, schema):
    validate(value, schema)
    if isinstance(value, str):
        assert len(value) <= schema.get('maxLength', 10**9)
        if 'pattern' in schema:
            assert re.fullmatch(schema['pattern'], value)
    elif isinstance(value, dict):
        for key, child in schema.get('properties', {}).items():
            if key in value:
                validate_native(value[key], child)
    elif isinstance(value, list):
        for item in value:
            validate_native(item, schema.get('items', {}))


class SharePoint:
    def __init__(self):
        self.rows = {r: {} for r in flow.Builder().base}
        self.calls = []
        self.member_calls = []
        self.user = 138
        self.hooks = {}
        self.failures = {}
        self.paged = set()
        self.profile_reads = defaultdict(int)
        self.insert('participants', profile(32, [1]))
        self.insert('participants', profile(38, learn=[1]))
        self.insert('requests', {'Id': 70, 'SenderParticipantId': 32, 'RecipientParticipantId': 38,
            'RequestType': 'Personal', 'TargetGroupId': None, 'Status': 'Pending',
            'Title': 'Personal request', 'SendOperationKey': 'personal:32:aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee',
            'ConnectionKey': 'open:person:32:38', 'WinningOperationKey': None, 'OperationComplete': False})
        for role, values in [('language', [{'Id': 1, 'ISOcode': 'en'}, {'Id': 2, 'ISOcode': 'fr'}, {'Id': 99, 'ISOcode': 'any'}]),
                             ('culture', [{'Id': 1, 'CultureKey': 'a'}]), ('timezone', [{'Id': 1}])]:
            for value in values:
                self.insert(role, {**value, 'Active': True})

    def insert(self, role, body):
        id_ = body.get('Id', max(self.rows[role], default=0) + 1)
        row = {'__metadata': {'etag': '"1"', 'type': 'SP.Data.' + role},
               'Id': id_, **{k: deepcopy(v) for k, v in body.items() if k != '__metadata'}}
        self.rows[role][id_] = row
        return deepcopy(row)

    def update(self, role, id_, values):
        row = self.rows[role][id_]
        row.update({k: deepcopy(v) for k, v in values.items() if k != '__metadata'})
        row['__metadata']['etag'] = '"' + str(int(row['__metadata']['etag'].strip('"')) + 1) + '"'

    def request(self, p, action, member=None):
        uri, method = p['parameters/uri'], p['parameters/method']
        body = p.get('parameters/body')
        self.calls.append((action, method, uri, deepcopy(body)))
        if member is not None:
            self.member_calls.append((member, action, method, uri))
        hook_key = (action, member) if (action, member) in self.hooks else action
        failure_key = (action, member) if (action, member) in self.failures else action
        if hook_key in self.hooks:
            self.hooks.pop(hook_key)(self)
        if failure_key in self.failures:
            failure = self.failures[failure_key]
            if callable(failure):
                return failure(self, p)
            return {'statusCode': failure, 'body': {'error': 'injected'}}
        def response(value, status=200):
            return {'statusCode': status, 'body': {'d': deepcopy(value)}}
        if uri == '_api/web/currentuser?$select=Id':
            return response({'Id': self.user})
        bases = flow.Builder().base
        role = next(k for k, b in bases.items() if uri.startswith(b))
        suffix = uri[len(bases[role]):]
        if suffix.startswith('?$select='):
            return response({'Id': 'synthetic-' + role, 'Title': 'TandemOperationReceipts' if role == 'receipts' else role,
                             'ListItemEntityTypeFullName': 'SP.Data.' + role})
        item = re.fullmatch(r'/items\((\d+)\)', suffix)
        if item:
            id_ = int(item[1])
            row = self.rows[role].get(id_)
            if row is None:
                return response({}, 404)
            if method == 'GET':
                if role == 'participants':
                    self.profile_reads[id_] += 1
                return response(row)
            assert method == 'POST' and p['parameters/headers']['X-HTTP-Method'] == 'MERGE'
            assert body['__metadata']['type'] == row['__metadata']['type']
            if p['parameters/headers']['IF-MATCH'] != row['__metadata']['etag']:
                return response({'error': 'STALE_ETAG'}, 412)
            self.update(role, id_, body)
            return response({}, 204)
        if method == 'POST':
            assert suffix == '/items' and body['__metadata']['type'] == 'SP.Data.' + role
            key = {'receipts': 'OperationKey', 'groups': 'SourceRequestId', 'members': 'MembershipKey'}[role]
            if any(x[key] == body[key] for x in self.rows[role].values()):
                return {'statusCode': 502, 'body': {'error': {'code': 502, 'innerError': {
                    'errors': ['-2130575169', 'Microsoft.SharePoint.SPDuplicateValuesFoundException']}}}}
            return response(self.insert(role, body), 201)
        assert suffix.startswith('/items?')
        values = list(self.rows[role].values())
        if '$filter=' in suffix:
            predicate = suffix.split('$filter=')[1].split('&')[0]
            m = re.fullmatch(r"(\w+) eq (?:'([^']*)'|(\d+))", predicate)
            assert m, predicate
            key, text, number = m.groups()
            value = text if text is not None else int(number)
            values = [x for x in values if x.get(key) == value]
        limit = int(suffix.split('$top=')[1].split('&')[0])
        result = {'results': values[:limit]}
        if len(values) > limit or action in self.paged:
            result['__next'] = 'synthetic-next'
        return response(result)


class NativeFlow(FlowRunner):
    """WDL subset interpreter, including failure propagation and actual child."""
    def __init__(self, server, run_name='run-one'):
        super().__init__(server)
        self.run_name = run_name
        self.children = []
        self.errors = {}
        self.member_iterations = []

    def expr(self, text, ctx):
        text = text.replace('workflow()', "json('" + json.dumps({'run': {'name': self.run_name}}) + "')")
        text = text.replace('utcNow()', "'2026-11-14T12:00:00Z'")
        text = text.replace('guid()', "'" + str(uuid5(NAMESPACE_URL, self.run_name)) + "'")
        return super().expr(text, ctx)

    def run(self, actions, ctx=None):
        ctx = ctx or {'items': {}, 'triggerBody': input_()}
        todo, done = dict(actions), {}
        while todo:
            ready = [n for n, a in todo.items() if set(a.get('runAfter', {})) <= set(done)]
            assert ready, 'invalid graph'
            for name in ready:
                a = todo.pop(name)
                if any(done[n] not in allowed for n, allowed in a.get('runAfter', {}).items()):
                    done[name] = self.action_states[name] = 'Skipped'
                    continue
                p, kind, state = a.get('inputs', {}), a['type'], 'Succeeded'
                try:
                    if kind == 'OpenApiConnection':
                        self.outputs[name] = self.server.request(self.inputs(p['parameters'], ctx), name,
                                                                ctx['items'].get('Ensure_initial_members'))
                        if self.outputs[name]['statusCode'] >= 400:
                            state = 'Failed'
                    elif kind == 'Workflow':
                        assert p['host']['workflowReferenceName'] == flow.CHILD
                        request = json.loads(self.inputs(p['body']['text'], ctx))
                        self.children.append(deepcopy(request))
                        result = evaluate_child(request)
                        if hasattr(self.server, 'child_transform'):
                            result = self.server.child_transform(name, result)
                        self.outputs[name] = {'statusCode': 200, 'body': {
                            'success': result['code'] == 'OK', 'resultcode': result['code'], 'resultjson': json.dumps(result)}}
                    elif kind == 'Compose':
                        self.outputs[name] = self.inputs(p, ctx)
                    elif kind == 'ParseJson':
                        value = self.inputs(p['content'], ctx)
                        value = json.loads(value) if isinstance(value, str) else value
                        validate_native(value, p['schema'])
                        self.outputs[name] = value
                    elif kind == 'InitializeVariable':
                        for v in p['variables']:
                            self.variables[v['name']] = deepcopy(v['value'])
                    elif kind == 'SetVariable':
                        self.variables[p['name']] = self.inputs(p['value'], ctx)
                    elif kind == 'IncrementVariable':
                        self.variables[p['name']] += self.inputs(p['value'], ctx)
                    elif kind in ['Query', 'Select']:
                        result = []
                        for row in self.inputs(p['from'], ctx):
                            c = {**ctx, 'item': row}
                            if kind == 'Select':
                                result.append(self.inputs(p['select'], c))
                            elif self.expr(p['where'], c):
                                result.append(row)
                        self.outputs[name] = result
                    elif kind == 'If':
                        if not self.run(a['actions'] if self.expr(a['expression'], ctx) else a['else']['actions'], ctx):
                            state = 'Failed'
                    elif kind == 'Scope':
                        if not self.run(a['actions'], ctx):
                            state = 'Failed'
                    elif kind == 'Foreach':
                        assert a['runtimeConfiguration']['concurrency']['repetitions'] == 1
                        for row in self.inputs(a['foreach'], ctx):
                            # Native outputs inside a foreach refer to the
                            # current repetition, including skipped actions.
                            for path, _ in walk(a['actions']):
                                self.outputs.pop(path[-1], None)
                                self.action_states.pop(path[-1], None)
                            ok = self.run(a['actions'], {**ctx, 'items': {**ctx['items'], name: row}})
                            if not ok:
                                state = 'Failed'
                            self.member_iterations.append((row, ok, deepcopy(self.action_states)))
                    elif kind == 'Response':
                        self.response = self.inputs(p['body'], ctx)
                    else:
                        raise RuntimeError('Unsupported ' + kind)
                except (AssertionError, ZeroDivisionError, TypeError, ValueError, KeyError, IndexError) as error:
                    self.errors[name] = repr(error)
                    state = 'Failed'
                done[name] = self.action_states[name] = state
        return all(s != 'Failed' for s in done.values())


def execute(server=None, payload=None, run_name='run-one'):
    runner = NativeFlow(server or SharePoint(), run_name)
    runner.run(flow.Builder().build(), {'items': {}, 'triggerBody': payload or input_()})
    assert runner.response is not None, runner.errors
    return runner


def assert_success(runner, code='ACCEPTED'):
    assert runner.response['success'], (runner.response, runner.errors,
        {n: s for n, s in runner.action_states.items() if s == 'Failed'})
    assert runner.response['resultcode'] == code


def test_accept_one_group_two_members_and_central_validation():
    r = execute()
    assert_success(r)
    s = r.server
    assert len(s.rows['groups']) == 1 and len(s.rows['members']) == 2
    group = next(iter(s.rows['groups'].values()))
    assert group['SetupComplete'] is True and group['State'] == 'Open' and group['WriteOwner'] == ''
    assert group['SourceRequestId'] == 70
    assert {x['ParticipantId'] for x in s.rows['members'].values()} == {32, 38}
    assert s.rows['requests'][70]['OperationComplete'] is True
    assert [c['mode'] for c in r.children] == ['PAIR', 'GROUP', 'PAIR', 'GROUP']
    assert all(c['contractVersion'] == c['rulesVersion'] == 1 for c in r.children)
    assert all(c['profiles'][0]['timezoneId'] is None for c in r.children)


def test_decline_ignores_unused_acceptance_inputs_and_stops():
    r = execute(payload=input_(text='Decline', text_1='', text_2='', number_2=0, text_3='not json', text_4=''))
    assert_success(r, 'DECLINED')
    assert not r.children and not r.server.rows['groups'] and not r.server.rows['members']
    assert r.server.rows['requests'][70]['Status'] == 'Declined'
    assert r.server.rows['requests'][70]['ConnectionKey'] == 'history:request:70'


@pytest.mark.parametrize('capacity,state', [(2, 'Closed'), (3, 'Open')])
def test_initial_state_from_actual_space(capacity, state):
    r = execute(payload=input_(number_2=capacity))
    assert_success(r)
    assert next(iter(r.server.rows['groups'].values()))['State'] == state


@pytest.mark.parametrize('decision', ['Accept', 'Decline'])
def test_completed_replay_is_historical_and_has_no_business_mutation(decision):
    s = SharePoint()
    payload = input_(text=decision)
    assert_success(execute(s, payload), 'ACCEPTED' if decision == 'Accept' else 'DECLINED')
    if decision == 'Accept':
        group = next(iter(s.rows['groups'].values()))
        s.update('groups', group['Id'], {'State': 'Ended', 'Title': 'Later name'})
    before = deepcopy(s.rows)
    offset = len(s.calls)
    r = execute(s, payload, 'run-two')
    assert_success(r, 'ACCEPTED' if decision == 'Accept' else 'DECLINED')
    assert s.rows == before
    assert not r.children
    assert not [c for c in s.calls[offset:] if c[1] != 'GET']


def test_same_intent_changed_typed_payload_conflicts():
    s = SharePoint()
    assert_success(execute(s))
    r = execute(s, input_(text_1='Other'), 'run-two')
    assert not r.response['success'] and r.response['resultcode'] == 'INTENT_CONFLICT'
    assert len(s.rows['groups']) == 1 and len(s.rows['members']) == 2


@pytest.mark.parametrize('change', [{'number': 32}, {'number': 39}, {'text': 'Cancel'},
                                  {'text_5': "oops' or 1 eq 1"}, {'number_1': 70.5}])
def test_untrusted_or_invalid_references_no_domain_writes(change):
    r = execute(payload=input_(**change))
    assert not r.response['success']
    assert r.server.rows['requests'][70]['Status'] == 'Pending'
    assert not r.server.rows['groups'] and not r.server.rows['receipts']


def test_native_synthetic_38_32_negative_no_shared_success_shortcut():
    s = SharePoint()
    s.update('participants', 32, {'TeachlanguagesId': {'results': []}, 'LearnlanguagesId': {'results': [1]}})
    r = execute(s)
    assert not r.response['success'] and r.response['resultcode'] == 'INELIGIBLE'
    assert s.rows['requests'][70]['Status'] == 'Pending'
    assert not s.rows['groups']


@pytest.mark.parametrize('field,value', [('ParticipationStatus', 'Paused'), ('OpenToConnections', False),
                                       ('Status', 'Needs review'), ('ParticipationStatus', None)])
def test_shared_current_unavailability_rejected(field, value):
    s = SharePoint()
    s.update('participants', 32, {field: value})
    r = execute(s)
    assert not r.response['success'] and not s.rows['groups']


@pytest.mark.parametrize('payload', [
    input_(number_2=4), input_(number_2=2.5), input_(text_3='[99]'),
    input_(text_3='[2]'), input_(text_3='[1,1]'),
    input_(text_2='Culture', text_3='[]', text_4='[1]'),
    input_(text_3='[]'), input_(text_3='broken')])
def test_invalid_capacity_or_group_purpose_does_not_accept(payload):
    r = execute(payload=payload)
    assert not r.response['success']
    assert r.server.rows['requests'][70]['Status'] == 'Pending' and not r.server.rows['groups']


def test_culture_only_supported():
    s = SharePoint()
    s.update('participants', 32, profile(32, share=[1]))
    s.update('participants', 38, profile(38, culture=[1]))
    r = execute(s, input_(text_2='Culture', number_2=10, text_3='[]', text_4='[1]'))
    assert_success(r)


def test_stale_pending_etag_cannot_overwrite_competing_decline():
    s = SharePoint()
    s.hooks['Decision_pending_CAS'] = lambda s: s.update('requests', 70,
        {'Status': 'Declined', 'WinningOperationKey': 'other', 'OperationComplete': True})
    r = execute(s)
    assert not r.response['success'] and r.response['resultcode'] == 'DECISION_CONFLICT'
    assert s.rows['requests'][70]['Status'] == 'Declined' and not s.rows['groups']


def test_accept_race_winner_then_loser_creates_no_second_group():
    s = SharePoint()
    winner = []
    def compete(server):
        winner.append(execute(server, input_(text_5='aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee'), 'other-run'))
    s.hooks['Decision_pending_CAS'] = compete
    r = execute(s)
    assert_success(winner[0])
    assert not r.response['success']
    assert len(s.rows['groups']) == 1 and len(s.rows['members']) == 2


@pytest.mark.parametrize('action', ['Fresh_Sender', 'Last_Sender'])
def test_fresh_or_stale_profile_after_members_does_not_publish(action):
    s = SharePoint()
    s.hooks[action] = lambda s: s.update('participants', 32, {'ParticipationStatus': 'Paused'})
    r = execute(s)
    assert not r.response['success']
    g = next(iter(s.rows['groups'].values()))
    assert not g['SetupComplete'] and g['State'] == 'Closed'
    assert s.rows['requests'][70]['Status'] == 'Accepted' and not s.rows['requests'][70]['OperationComplete']


@pytest.mark.parametrize('action', ['Committed_request', 'Committed_members', 'Committed_group', 'Decision_receipt_completed_readback'])
def test_failed_readback_never_reports_accept_success(action):
    s = SharePoint()
    s.failures[action] = 500
    r = execute(s)
    assert not r.response['success'] and r.response['groupid'] == 0


def test_known_partial_prefix_reuses_one_group_and_first_membership():
    s = SharePoint()
    s.failures[('Member_create', 38)] = 403
    first = execute(s)
    assert not first.response['success']
    receipt = next(iter(s.rows['receipts'].values()))
    assert receipt['Retryable'] and not receipt['Uncertain']
    assert json.loads(receipt['SealedAttempts']) == [str(uuid5(NAMESPACE_URL, 'run-one'))]
    assert len(s.rows['groups']) == len(s.rows['members']) == 1
    s.failures.clear()
    second = execute(s, run_name='run-two')
    assert_success(second)
    assert len(s.rows['groups']) == 1 and len(s.rows['members']) == 2


@pytest.mark.parametrize('code', [408, 429, 500, 502, 504])
def test_unknown_member_write_does_not_seal_or_steal(code):
    s = SharePoint()
    s.failures[('Member_create', 38)] = code
    first = execute(s)
    assert not first.response['success']
    receipt = next(iter(s.rows['receipts'].values()))
    assert receipt['Uncertain'] and not receipt['Retryable']
    before = deepcopy(s.rows)
    s.failures.clear()
    r = execute(s, run_name='run-two')
    assert not r.response['success'] and s.rows == before


def test_completed_receipt_failed_release_replay_only_finalizes_release():
    s = SharePoint()
    s.failures['Final_release'] = 500
    r = execute(s)
    assert not r.response['success']
    assert next(iter(s.rows['receipts'].values()))['Complete']
    s.failures.clear()
    before_members = deepcopy(s.rows['members'])
    r = execute(s, run_name='run-two')
    assert_success(r)
    assert not r.children and s.rows['members'] == before_members
    assert next(iter(s.rows['groups'].values()))['WriteOwner'] == ''


def test_structure_native_only_unique_names_refs_exact_etags_and_limits():
    actions = flow.Builder().build()
    all_ = list(walk(actions))
    names = [path[-1] for path, _ in all_]
    assert len(names) == len(set(names))
    metrics = measure(actions)
    assert metrics['actions'] < 300 and metrics['maximumActionDepth'] <= 8
    loops = [(path, a) for path, a in all_ if a['type'] == 'Foreach']
    assert len(loops) == 1
    assert loops[0][1]['runtimeConfiguration']['concurrency']['repetitions'] == 1
    assert loops[0][1]['foreach'] == "@createArray(outputs('Initial_request')?['SenderParticipantId'],outputs('Initial_request')?['RecipientParticipantId'])"
    assert len([a for _, a in all_ if a['type'] == 'OpenApiConnection'
                and a['inputs']['parameters'].get('parameters/body', {}).get('MembershipStatus') == 'Active']) == 1
    for _, action in all_:
        if action['type'] == 'OpenApiConnection':
            p = action['inputs']['parameters']
            assert action['inputs']['retryPolicy'] == {'type': 'none'}
            if p['parameters/method'] != 'GET' and '/items(' in p['parameters/uri']:
                assert p['parameters/headers']['IF-MATCH'] != '*'
                assert '__metadata' in p['parameters/body']
    serialized = json.dumps(actions)
    refs = re.findall(r"(?:body|outputs|actions)\('([^']+)'\)", serialized)
    assert set(refs) <= set(names)
    def siblings(graph):
        for _, a in graph.items():
            assert set(a.get('runAfter', {})) <= set(graph)
            siblings(a.get('actions', {}))
            siblings(a.get('else', {}).get('actions', {}))
    siblings(actions)
    assert RECEIPT_FIELD_NAMES() <= {'OperationKey', 'IntentJson', 'ResultJson', 'Complete', 'Uncertain',
        'Retryable', 'DomainEffects', 'AttemptToken', 'SealedAttempts', 'Stage'}


def RECEIPT_FIELD_NAMES():
    fields = set()
    for _, action in walk(flow.Builder().build()):
        if action['type'] == 'OpenApiConnection':
            p = action['inputs']['parameters']
            if 'TandemOperationReceipts' in p['parameters/uri'] and 'parameters/body' in p:
                fields |= set(p['parameters/body']) - {'__metadata'}
    return fields


def test_sealed_release_failure_is_finalized_before_reacquire():
    s = SharePoint()
    s.failures.update({('Member_create', 38): 403, 'Sealed_release': 500})
    first = execute(s)
    assert not first.response['success']
    assert next(iter(s.rows['receipts'].values()))['Retryable']
    assert next(iter(s.rows['groups'].values()))['WriteOwner']
    s.failures.clear()
    second = execute(s, run_name='run-two')
    assert_success(second)
    assert len(s.rows['groups']) == 1 and len(s.rows['members']) == 2


def test_three_sealed_attempts_cap_without_takeover():
    s = SharePoint()
    s.failures[('Member_create', 38)] = 403
    for n in range(3):
        assert not execute(s, run_name='attempt-' + str(n)).response['success']
    receipt = next(iter(s.rows['receipts'].values()))
    assert len(json.loads(receipt['SealedAttempts'])) == 3
    before = deepcopy(s.rows)
    s.failures.clear()
    r = execute(s, run_name='attempt-four')
    assert not r.response['success'] and s.rows == before


def test_left_episode_is_not_revived_or_bypassed():
    s = SharePoint()
    s.failures[('Member_create', 38)] = 403
    assert not execute(s).response['success']
    first = next(iter(s.rows['members'].values()))
    s.update('members', first['Id'], {'MembershipStatus': 'Left', 'LeftAt': '2026-11-14T12:01:00Z'})
    s.failures.clear()
    r = execute(s, run_name='run-two')
    assert not r.response['success'] and len(s.rows['members']) == 1
    assert s.rows['members'][first['Id']]['MembershipStatus'] == 'Left'


def test_foreign_group_owner_is_never_cleared():
    s = SharePoint()
    def steal(server):
        g = next(iter(server.rows['groups'].values()))
        server.update('groups', g['Id'], {'WriteOwner': 'foreign:token'})
    s.hooks[('Member_guard', 32)] = steal
    r = execute(s)
    assert not r.response['success'] and not s.rows['members']
    assert next(iter(s.rows['groups'].values()))['WriteOwner'] == 'foreign:token'


def test_stale_group_publish_etag_rejected():
    s = SharePoint()
    def change(server):
        g = next(iter(server.rows['groups'].values()))
        server.update('groups', g['Id'], {'Capacity': 2})
    s.hooks['Publish_group'] = change
    r = execute(s)
    assert not r.response['success']
    assert not next(iter(s.rows['groups'].values()))['SetupComplete']
    assert not s.rows['requests'][70]['OperationComplete']


def test_wrong_source_duplicate_group_does_not_imply_success():
    s = SharePoint()
    def create_foreign(server, p):
        server.insert('groups', {**p['parameters/body'], 'Title': 'Mismatch'})
        return {'statusCode': 502, 'body': {'error': 'wrapped duplicate'}}
    s.failures['Create_group'] = create_foreign
    r = execute(s)
    assert not r.response['success'] and not s.rows['members']
    assert not next(iter(s.rows['groups'].values()))['SetupComplete']


def test_ambiguous_create_reconciles_only_exact_stable_row():
    s = SharePoint()
    def create_saved(server, p):
        server.insert('members', p['parameters/body'])
        return {'statusCode': 504, 'body': {'error': 'transport lost after write'}}
    s.failures[('Member_create', 38)] = create_saved
    r = execute(s)
    assert_success(r)
    assert len(s.rows['members']) == 2


def test_membership_duplicate_wrong_party_is_integrity_error():
    s = SharePoint()
    def create_wrong(server, p):
        server.insert('members', {**p['parameters/body'], 'ParticipantId': 999})
        return {'statusCode': 502, 'body': {'error': 'duplicate'}}
    s.failures[('Member_create', 38)] = create_wrong
    r = execute(s)
    assert not r.response['success']
    assert not next(iter(s.rows['groups'].values()))['SetupComplete']


def test_decline_loses_to_accept_cannot_reverse_or_create_second_group():
    s = SharePoint()
    winner = []
    def compete(server):
        winner.append(execute(server, input_(text_5='aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee'), 'accept-winner'))
    s.hooks['Decision_pending_CAS'] = compete
    r = execute(s, input_(text='Decline'))
    assert_success(winner[0])
    assert not r.response['success'] and s.rows['requests'][70]['Status'] == 'Accepted'
    assert len(s.rows['groups']) == 1 and len(s.rows['members']) == 2


@pytest.mark.parametrize('action', ['Own_profile', 'Find_receipt', 'Initial_language', 'Fresh_culture',
                                  'Before_commit_members', 'Committed_members'])
def test_paged_reads_fail_closed(action):
    s = SharePoint()
    s.paged.add(action)
    r = execute(s)
    assert not r.response['success']
    assert not any(x.get('Complete') for x in s.rows['receipts'].values())


@pytest.mark.parametrize('part', ['Initial_Pair', 'Initial_Group', 'Fresh_Pair', 'Fresh_Group'])
def test_shared_version_mismatch_never_authorizes_write(part):
    s = SharePoint()
    def transform(name, result):
        if name == part:
            result['rulesVersion'] = 99
        return result
    s.child_transform = transform
    r = execute(s)
    assert not r.response['success'] and r.response['resultcode'] == 'SHARED_VERSION_MISMATCH'
    if part.startswith('Initial'):
        assert s.rows['requests'][70]['Status'] == 'Pending'
    assert not any(g['SetupComplete'] for g in s.rows['groups'].values())


def test_recipient_account_rebinding_rejected_on_current_read():
    s = SharePoint()
    s.hooks['Fresh_Recipient'] = lambda server: server.update('participants', 38, {'ParticipantaccountId': 999})
    r = execute(s)
    assert not r.response['success'] and r.response['resultcode'] == 'PROFILE_IDENTITY'
    assert not next(iter(s.rows['groups'].values()))['SetupComplete']


def test_legacy_and_parent_only_solution_package(tmp_path):
    source = flow.Path(r'C:\projects\small_projects\tandem-language-culture-app\artifacts\shared_validation\TandemSharedValidation81_1_0_0_2.zip')
    if not source.exists():
        pytest.skip('Optional uncommitted owner source export unavailable')
    output = tmp_path / 'Respond.zip'
    report = flow.build(output, source)
    with ZipFile(output) as z:
        doc = json.loads(z.read(next(n for n in z.namelist() if n.endswith('/definition.json'))))
    assert doc['properties']['definition']['triggers'] == flow.schema_input()
    assert doc['properties']['connectionReferences']['shared_sharepointonline']['source'] == 'Invoker'
    for _, action in walk(doc['properties']['definition']['actions']):
        if action['type'] == 'OpenApiConnection':
            assert action['inputs']['authentication']['type'] == 'Raw'
    with ZipFile(output.with_name('Respond.solution.zip')) as z:
        assert len([n for n in z.namelist() if n.startswith('Workflows/')]) == 1
        custom = flow.ET.fromstring(z.read('customizations.xml'))
        assert [n.attrib['Name'] for n in custom.findall('./Workflows/Workflow')] == [flow.NAME]
        parent = json.loads(z.read(next(n for n in z.namelist() if n.startswith('Workflows/'))))
        assert parent['properties']['connectionReferences']['shared_sharepointonline']['runtimeSource'] == 'invoker'
        assert flow.CHILD in json.dumps(parent)
    assert report['nativeIntegration'] == 'NOT RUN' and report['authorityProof'] == 'NOT RUN'


@pytest.mark.parametrize('predicate,passes', [('true', True), ('false', False), ('null', False),
                                             ('0', False), ('1', False), ("'true'", False)])
def test_native_assertion_requires_exact_boolean_true(predicate, passes):
    b = flow.Builder()
    b.gate('Assertion', predicate, 'ASSERTION_FAILED')
    b.set('After_assertion', 'Reached', True)
    runner = NativeFlow(SharePoint())
    runner.run(b.actions)
    assert runner.variables.get('Reached', False) == passes
    assert runner.variables['Code'] == 'ASSERTION_FAILED'
    assert len(list(walk({'Assertion': b.actions['Assertion']}))) == 1


@pytest.mark.parametrize('code,retryable', [(403, True), (408, False), (500, False), (504, False)])
def test_first_member_failure_stops_second_iteration_io(code, retryable):
    s = SharePoint()
    s.failures[('Member_create', 32)] = code
    r = execute(s)
    assert not r.response['success']
    assert [i[0] for i in r.member_iterations] == [32, 38]
    assert r.member_iterations[0][1] is False
    assert not any(member == 38 for member, *_ in s.member_calls)
    assert not s.rows['members']
    receipt = next(iter(s.rows['receipts'].values()))
    assert receipt['Retryable'] is retryable and receipt['Uncertain'] is not retryable
    assert r.response['resultcode'] == 'MEMBERSHIP_CONFLICT_OR_UNCERTAIN'
    if retryable:
        s.failures.clear()
        assert_success(execute(s, run_name='retry-first-member'))
        assert len(s.rows['groups']) == 1 and len(s.rows['members']) == 2


def test_first_member_paged_read_stops_second_and_cannot_seal():
    s = SharePoint()
    s.paged.add('Member_readback')
    r = execute(s)
    assert not r.response['success']
    assert not any(member == 38 for member, *_ in s.member_calls)
    assert len(s.rows['members']) == 1
    receipt = next(iter(s.rows['receipts'].values()))
    assert receipt['Uncertain'] and not receipt['Retryable']
    assert not next(iter(s.rows['groups'].values()))['SetupComplete']


def test_second_iteration_has_no_stale_create_output_from_first():
    s = SharePoint()
    s.failures[('Member_create', 38)] = 403
    first = execute(s)
    assert not first.response['success']
    assert 'Member_create' in first.member_iterations[0][2]
    offset = len(s.member_calls)
    s.failures.clear()
    second = execute(s, run_name='retry-existing-first')
    assert_success(second)
    assert not any(member == 32 and name == 'Member_create'
                   for member, name, *_ in s.member_calls[offset:])
    assert second.member_iterations[0][2].get('Member_create') is None
    assert second.member_iterations[1][2]['Member_create'] == 'Succeeded'
    assert len(s.rows['members']) == 2


def test_send10_saved_row_contract_survives_response_and_history():
    s = SharePoint()
    before = deepcopy(s.rows['requests'][70])
    assert before['Title'] == 'Personal request'
    assert before['SendOperationKey'] == 'personal:32:aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee'
    assert before['ConnectionKey'] == 'open:person:32:38'
    assert before['TargetGroupId'] is None and before['WinningOperationKey'] is None
    assert before['Status'] == 'Pending' and before['OperationComplete'] is False
    assert_success(execute(s))
    saved = s.rows['requests'][70]
    for key in ['Title', 'SendOperationKey', 'SenderParticipantId', 'RecipientParticipantId', 'TargetGroupId']:
        assert saved[key] == before[key]
    assert saved['ConnectionKey'] == 'history:request:70'


@pytest.mark.parametrize('change', [
    {'SendOperationKey': None}, {'SendOperationKey': 'personal:32:wrong'},
    {'SendOperationKey': 'personal:38:aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee'},
    {'ConnectionKey': 'personal:32:38'}, {'ConnectionKey': 'open:person:38:32'},
    {'SenderParticipantId': '32'}, {'RecipientParticipantId': '38'},
    {'OperationComplete': None}, {'WinningOperationKey': 'premature-winner'},
])
def test_malformed_send_contract_rejected_before_receipt_or_domain_effect(change):
    s = SharePoint()
    s.update('requests', 70, change)
    before = deepcopy(s.rows)
    r = execute(s)
    assert not r.response['success'] and s.rows == before


@pytest.mark.parametrize('stage', ['Decision_request_fresh', 'Request_before_publish'])
@pytest.mark.parametrize('change', [
    {'SendOperationKey': 'personal:32:aaaaaaaa-bbbb-4ccc-8ddd-ffffffffffff'},
    {'ConnectionKey': 'open:person:38:32'},
    {'RecipientParticipantId': 39},
])
def test_fresh_request_immutable_parties_and_keys_cannot_drift(stage, change):
    s = SharePoint()
    s.hooks[stage] = lambda server: server.update('requests', 70, change)
    r = execute(s)
    assert not r.response['success']
    assert not any(g['SetupComplete'] for g in s.rows['groups'].values())
    if stage == 'Decision_request_fresh':
        assert s.rows['requests'][70]['Status'] == 'Pending'


def test_send10_reverse_direction_keeps_sorted_live_key():
    s = SharePoint()
    s.user = 132
    s.update('requests', 70, {'SenderParticipantId': 38, 'RecipientParticipantId': 32,
                             'SendOperationKey': 'personal:38:aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee'})
    r = execute(s, input_(number=32))
    assert_success(r)
    assert [i[0] for i in r.member_iterations] == [38, 32]
