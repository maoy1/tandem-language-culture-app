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
