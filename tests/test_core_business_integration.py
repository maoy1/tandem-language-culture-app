"""Interoperate delivered parent graphs over one row store and the real child.

These cases run in the combined checkout; single-ticket branches explicitly
skip missing consumers. Final assembly independently requires all twelve.
"""
import hashlib
import json
from pathlib import Path
import pytest

from scripts.power_automate import shared_validation as shared, batch_schema, core_solution
from scripts.power_automate import compatibility
from core_native_backend import seed, Connection, ParentRunner

COMPONENTS = {
    'send': 'artifacts/send_request/TandemSendRequest-v4-shared.solution-parent.json',
    'inbox': 'artifacts/my_requests/TandemMyRequests-v7-introduction-target.definition.json',
    'cancel': 'artifacts/cancel_request/TandemCancelRequest-v4.definition.json',
    'discovery': 'artifacts/tandem_discovery/TandemDiscovery-shared.definition.json',
    'respond': 'artifacts/respond_request/TandemRespondRequest-11.2.0.definition.json',
    'groups': 'artifacts/my_groups/TandemMyGroups-v2.definition.json',
    'group_send': 'artifacts/group_send/TandemSendGroupJoinRequest-v1.solution-parent.json',
    'leave': 'artifacts/leave_group/TandemLeaveGroup-v1.definition.json',
}
OLD_BUILD = 'c79b7b64-b3ce-4de3-aa74-0ed62bca1524'
LOCAL_BUILD = 'local-linked-core-build'
INTENT = '11111111-2222-4333-8444-555555555555'


def invoke(db, name, actor, body):
    path = shared.ROOT / COMPONENTS[name]
    if not path.exists(): pytest.skip('Consumer not present on this focused branch; run combined checkout')
    document = json.loads(path.read_text(encoding='utf-8-sig'))
    actions = core_solution.bind_shared_build(document['properties']['definition']['actions'], OLD_BUILD, LOCAL_BUILD)
    child = shared.definition_actions(batch_schema.baseline(), LOCAL_BUILD,
        hashlib.sha256(Path(compatibility.__file__).read_bytes()).hexdigest())
    connection = Connection(db, actor=actor, child_actions=child)
    runner = ParentRunner(connection)
    runner.run(actions, {'items': {}, 'triggerBody': body})
    assert runner.response is not None, {k: v for k, v in runner.action_states.items() if v == 'Failed'}
    return runner.response, runner


def test_delivered_send_inboxes_cancel_and_historical_replay_share_rows():
    db = seed()
    sent, _ = invoke(db, 'send', 1, {'number': 1, 'number_1': 2, 'text': INTENT})
    assert sent['success'] and sent['resultcode'] == 'SAVED', sent
    request_id = int(sent['requestid'])
    for actor in [1, 2]:
        inbox, _ = invoke(db, 'inbox', actor, {'number': actor})
        assert inbox['resultcode'] == 'OK', inbox
        rows = json.loads(inbox['requestsjson'])
        assert len(rows) == 1 and rows[0]['status'] == 'Pending'
    cancelled, _ = invoke(db, 'cancel', 1, {'number': 1, 'number_1': request_id})
    assert cancelled['success'] and cancelled['resultcode'] == 'CANCELLED', cancelled
    row = db.tables['requests'][0]
    assert row['Status'] == 'Cancelled' and row['OperationComplete'] is True
    assert row['ConnectionKey'] == 'history:request:' + str(request_id)
    db.tables['participants'][0]['ParticipationStatus'] = 'Paused'
    replay, _ = invoke(db, 'send', 1, {'number': 1, 'number_1': 2, 'text': INTENT})
    assert replay['resultcode'] == 'REPLAY' and replay['status'] == 'Cancelled', replay
    history, _ = invoke(db, 'inbox', 2, {'number': 2})
    assert history['resultcode'] == 'OK' and json.loads(history['requestsjson'])[0]['status'] == 'Cancelled'
    assert len(db.tables['requests']) == 1
    assert {entry['role'] for entry in db.log} == {'requests'}
    assert not any(word in json.dumps(history) for word in ['PRIVATE_EMAIL', 'Claims', 'ConnectionKey', 'SendOperationKey'])


def test_delivered_discovery_and_send_agree_on_unavailable_target():
    db = seed()
    discovered, _ = invoke(db, 'discovery', 1, {'number': 1})
    assert discovered['resultcode'] == 'OK', discovered
    assert 2 in [row['profileId'] for row in json.loads(discovered['candidatesjson'])]
    db.tables['participants'][1]['ParticipationStatus'] = 'Paused'
    sent, _ = invoke(db, 'send', 1, {'number': 1, 'number_1': 2, 'text': INTENT})
    assert sent['resultcode'] == 'TARGET_UNAVAILABLE_OR_INCOMPATIBLE' and not db.log, sent


def test_delivered_send_spoofed_actor_cannot_write():
    db = seed()
    response, _ = invoke(db, 'send', 1, {'number': 2, 'number_1': 3, 'text': INTENT})
    assert not response['success'] and not db.log


def test_delivered_send_reconciles_lost_success_and_never_posts_twice():
    db = seed(); db.fault = lambda role, patch: 'after' if role == 'requests' else None
    sent, _ = invoke(db, 'send', 1, {'number': 1, 'number_1': 2, 'text': INTENT})
    assert sent['resultcode'] == 'SAVED', sent
    replay, _ = invoke(db, 'send', 1, {'number': 1, 'number_1': 2, 'text': INTENT})
    assert replay['resultcode'] == 'REPLAY' and replay['requestid'] == sent['requestid']
    assert len(db.tables['requests']) == len(db.log) == 1


def accepted_group(db):
    sent, _ = invoke(db, 'send', 1, {'number': 1, 'number_1': 2, 'text': INTENT})
    assert sent['resultcode'] == 'SAVED', sent
    response, runner = invoke(db, 'respond', 2, {'number': 2, 'number_1': int(sent['requestid']),
        'text': 'Accept', 'text_1': 'Practice', 'text_2': 'Language', 'number_2': 3,
        'text_3': '[1]', 'text_4': '[]', 'text_5': '22222222-2222-4333-8444-555555555555'})
    assert response['success'], (response, [n for n, state in runner.action_states.items() if state == 'Failed'])
    assert len(db.tables['groups']) == 1 and len(db.tables['members']) == 2
    return db.tables['groups'][0]['Id']


def test_personal_accept_group_reader_group_send_cancel_and_leave_interoperate():
    db = seed(); group_id = accepted_group(db)
    own, _ = invoke(db, 'groups', 1, {'number': 1})
    assert own['resultcode'] == 'OK', own
    group = json.loads(own['groupsjson'])[0]
    assert group['groupId'] == group_id and group['memberCount'] == 2 and group['freeSlots'] == 1
    assert group['membershipId'] == next(m['Id'] for m in db.tables['members'] if m['ParticipantId'] == 1)
    join, _ = invoke(db, 'group_send', 3, {'number': group_id,
        'text': '33333333-2222-4333-8444-555555555555', 'text_1': 'Hello from participant 3'})
    assert join['success'] and join['status'] == 'Pending', join
    assert len(db.tables['members']) == 2
    inbox, _ = invoke(db, 'inbox', 1, {'number': 1})
    assert inbox['resultcode'] == 'OK', inbox
    incoming = next(r for r in json.loads(inbox['requestsjson']) if r['requestId'] == int(join['requestid']))
    assert incoming['introduction'] == 'Hello from participant 3'
    cancelled, _ = invoke(db, 'cancel', 3, {'number': 3, 'number_1': int(join['requestid'])})
    assert cancelled['resultcode'] == 'CANCELLED', cancelled
    db.tables['participants'][0]['ParticipationStatus'] = 'Paused'
    db.tables['participants'][0]['OpenToConnections'] = False
    left, runner = invoke(db, 'leave', 1, {'number': 1, 'number_1': group_id, 'number_2': group['membershipId'],
        'text': '44444444-2222-4333-8444-555555555555'})
    assert left['success'], (left, [n for n, state in runner.action_states.items() if state == 'Failed'])
    assert db.tables['groups'][0]['State'] == 'Open'
    assert len(db.tables['members']) == 2 and next(m for m in db.tables['members'] if m['ParticipantId'] == 1)['MembershipStatus'] == 'Left'
    after, _ = invoke(db, 'groups', 1, {'number': 1})
    assert after['resultcode'] == 'OK' and after['groupstatus'] == 'Waiting' and after['groupsjson'] == '[]', after
    assert not any(entry['role'] in ['participants', 'language', 'culture', 'timezone'] for entry in db.log)
