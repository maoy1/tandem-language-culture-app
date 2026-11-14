"""Interoperate delivered parent graphs over one row store and the real child.

These cases run in the combined checkout; single-ticket branches explicitly
skip missing consumers. Final assembly independently requires all twelve.
"""
import hashlib
import json
from copy import deepcopy
from functools import lru_cache
import os
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile
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
    'update': 'artifacts/update_group/TandemUpdateGroup-v1.parent.json',
    'group_respond': 'artifacts/group_response/TandemRespondGroupJoinRequest.definition.json',
}
OLD_BUILD = 'c79b7b64-b3ce-4de3-aa74-0ed62bca1524'
LOCAL_BUILD = 'local-linked-core-build'
INTENT = '11111111-2222-4333-8444-555555555555'
FLOW_NAMES = {
    'send': 'TandemSendRequest', 'inbox': 'TandemMyRequests', 'cancel': 'TandemCancelRequest',
    'discovery': 'TandemDiscovery', 'respond': 'TandemRespondRequest', 'groups': 'TandemMyGroups',
    'group_send': 'TandemSendGroupJoinRequest', 'leave': 'TandemLeaveGroup',
    'update': 'TandemUpdateGroup', 'group_respond': 'TandemRespondGroupJoinRequest',
}


@lru_cache(maxsize=2)
def packaged_graphs(zip_path):
    """Read actual packaged JSON/identities once; never reconstruct/rebind it.

    TANDEM_CORE_ZIP selects this mode for the SAME E2E cases. Component mode
    below remains useful before assembly. No ZIP extraction/import or writes.
    """
    with ZipFile(zip_path) as archive:
        assert archive.testzip() is None, 'Corrupt core ZIP'
        custom = ET.fromstring(archive.read('customizations.xml'))
        documents, ids = {}, {}
        for node in custom.findall('./Workflows/Workflow'):
            name = node.attrib['Name']
            id_ = node.attrib['WorkflowId'].strip('{}').lower()
            assert name not in documents and id_ not in ids.values(), 'Duplicate packaged workflow identity'
            documents[name] = json.loads(archive.read(node.findtext('JsonFileName').lstrip('/')))
            ids[name] = id_
    child = documents['TandemValidateContext']['properties']['definition']['actions']
    child_id = ids['TandemValidateContext']
    child_build = child['Validation_report']['inputs']['packageBuildId']
    assert isinstance(child_build, str) and child_build, 'Missing packaged shared build'
    for document in documents.values():
        for _, action in core_solution.walk(document['properties']['definition']['actions']):
            if action['type'] == 'Workflow':
                assert action['inputs']['host']['workflowReferenceName'].lower() == child_id, 'Unresolved packaged child'
    return documents, ids, child, child_id, child_build


def invoke(db, name, actor, body):
    zip_path = os.environ.get('TANDEM_CORE_ZIP')
    if zip_path:
        documents, ids, child, child_id, child_build = packaged_graphs(str(Path(zip_path).resolve()))
        flow_name = FLOW_NAMES[name]
        assert flow_name in documents, 'Missing packaged consumer: ' + flow_name
        actions = documents[flow_name]['properties']['definition']['actions']
        connection = Connection(db, actor=actor, child_actions=child, child_id=child_id, child_build=child_build)
    else:
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


def group_edit(db, group_id, actor, intent, state, capacity=3, name='Practice'):
    """A fresh UI-style edit snapshot, not a direct domain write."""
    group = next(g for g in db.tables['groups'] if g['Id'] == group_id)
    return {'actorId': actor, 'groupId': group_id, 'expectedETag': group['__metadata']['etag'],
            'intentId': intent, 'edits': {'Title': name, 'Purpose': '', 'Capacity': capacity, 'State': state}}


def join_request(db, group_id):
    result, _ = invoke(db, 'group_send', 3, {'number': group_id,
        'text': '33333333-2222-4333-8444-555555555555', 'text_1': 'Please join the practice'})
    assert result['success'] and result['status'] == 'Pending', result
    return int(result['requestid'])


def test_group_update_closed_blocks_send_reopen_allows_send_and_replay_keeps_current_state():
    db = seed(); group_id = accepted_group(db)
    db.tables['participants'][0]['ParticipationStatus'] = 'Paused'
    db.tables['participants'][0]['OpenToConnections'] = False
    closed_payload = group_edit(db, group_id, 1, '55555555-2222-4333-8444-555555555555', 'Closed', name='Closed practice')
    closed, _ = invoke(db, 'update', 1, {'text': json.dumps(closed_payload)})
    assert closed['success'] and closed['resultcode'] == 'UPDATED', closed
    own, _ = invoke(db, 'groups', 2, {'number': 2})
    displayed = json.loads(own['groupsjson'])[0]
    assert displayed['state'] == 'Closed' and displayed['name'] == 'Closed practice'
    assert displayed['memberCount'] == 2 and displayed['freeSlots'] == 1
    blocked, _ = invoke(db, 'group_send', 3, {'number': group_id,
        'text': '66666666-2222-4333-8444-555555555555', 'text_1': ''})
    assert not blocked['success'] and blocked['resultcode'] == 'GROUP_UNAVAILABLE', blocked
    assert len(db.tables['requests']) == 1 and len(db.tables['members']) == 2
    reopened, _ = invoke(db, 'update', 2, {'text': json.dumps(group_edit(db, group_id, 2,
        '77777777-2222-4333-8444-555555555555', 'Open', name='Reopened practice'))})
    assert reopened['success'], reopened
    # Update authority is membership-based, while a new join still requires
    # an available focus sharer. Restore the only language1 sharer fixture.
    db.tables['participants'][0]['ParticipationStatus'] = 'Active'
    db.tables['participants'][0]['OpenToConnections'] = True
    request_id = join_request(db, group_id)
    current = deepcopy(db.tables['groups'])
    replay, _ = invoke(db, 'update', 1, {'text': json.dumps(closed_payload)})
    assert replay['success'] and replay['resultcode'] == 'REPLAY', replay
    assert db.tables['groups'] == current and len(db.tables['members']) == 2
    assert next(r for r in db.tables['requests'] if r['Id'] == request_id)['Status'] == 'Pending'


def test_group_update_stale_snapshot_cannot_overwrite_other_member_edit():
    db = seed(); group_id = accepted_group(db)
    stale = group_edit(db, group_id, 1, '55555555-2222-4333-8444-555555555555', 'Closed', name='Stale title')
    saved, _ = invoke(db, 'update', 2, {'text': json.dumps(group_edit(db, group_id, 2,
        '77777777-2222-4333-8444-555555555555', 'Open', name='Current title'))})
    assert saved['success'], saved
    rejected, _ = invoke(db, 'update', 1, {'text': json.dumps(stale)})
    assert not rejected['success'], rejected
    group = next(g for g in db.tables['groups'] if g['Id'] == group_id)
    assert group['Title'] == 'Current title' and group['State'] == 'Open'
    assert len(db.tables['members']) == 2


def test_group_join_accept_updates_member_reader_then_closed_leave_stays_closed_and_replay_is_historical():
    db = seed(); group_id = accepted_group(db)
    request_id = join_request(db, group_id)
    db.tables['participants'][1]['ParticipationStatus'] = 'Paused'
    db.tables['participants'][1]['OpenToConnections'] = False
    body = {'number': request_id, 'text': 'Accept', 'text_1': '88888888-2222-4333-8444-555555555555'}
    accepted, _ = invoke(db, 'group_respond', 2, body)
    assert accepted['success'] and accepted['resultcode'] == 'ACCEPTED', accepted
    assert len(db.tables['groups']) == 1 and len(db.tables['members']) == 3
    request = next(r for r in db.tables['requests'] if r['Id'] == request_id)
    assert request['OperationComplete'] is True and request['ConnectionKey'] == 'history:request:' + str(request_id)
    own, _ = invoke(db, 'groups', 3, {'number': 3})
    assert own['resultcode'] == 'OK', own
    joined = json.loads(own['groupsjson'])[0]
    assert joined['groupId'] == group_id and joined['memberCount'] == 3 and joined['freeSlots'] == 0
    closed, _ = invoke(db, 'update', 1, {'text': json.dumps(group_edit(db, group_id, 1,
        '99999999-2222-4333-8444-555555555555', 'Closed'))})
    assert closed['success'], closed
    left, _ = invoke(db, 'leave', 3, {'number': 3, 'number_1': group_id, 'number_2': joined['membershipId'],
        'text': 'aaaaaaaa-2222-4333-8444-555555555555'})
    assert left['success'], left
    before = deepcopy(db.tables['members'])
    replay, _ = invoke(db, 'group_respond', 2, body)
    assert replay['success'] and replay['resultcode'] == 'ACCEPTED', replay
    assert db.tables['members'] == before
    assert db.tables['groups'][0]['State'] == 'Closed'
    assert next(m for m in db.tables['members'] if m['ParticipantId'] == 3)['MembershipStatus'] == 'Left'
    remaining, _ = invoke(db, 'groups', 1, {'number': 1})
    group = json.loads(remaining['groupsjson'])[0]
    assert group['memberCount'] == 2 and group['freeSlots'] == 1 and group['state'] == 'Closed'


def test_group_join_decline_requires_member_but_not_open_state_or_requester_availability():
    db = seed(); group_id = accepted_group(db); request_id = join_request(db, group_id)
    closed, _ = invoke(db, 'update', 1, {'text': json.dumps(group_edit(db, group_id, 1,
        '99999999-2222-4333-8444-555555555555', 'Closed'))})
    assert closed['success'], closed
    db.tables['participants'][2]['ParticipationStatus'] = 'Paused'
    before = deepcopy(db.tables['members'])
    denied, _ = invoke(db, 'group_respond', 3, {'number': request_id, 'text': 'Decline',
        'text_1': 'bbbbbbbb-2222-4333-8444-555555555555'})
    assert not denied['success'], denied
    declined, _ = invoke(db, 'group_respond', 1, {'number': request_id, 'text': 'Decline',
        'text_1': 'cccccccc-2222-4333-8444-555555555555'})
    assert declined['success'] and declined['resultcode'] == 'DECLINED', declined
    assert db.tables['members'] == before
    request = next(r for r in db.tables['requests'] if r['Id'] == request_id)
    assert request['Status'] == 'Declined' and request['OperationComplete']
    assert db.tables['groups'][0]['State'] == 'Closed'
