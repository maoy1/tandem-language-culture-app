"""Bulk PAIRS must preserve the existing single-pair business rule exactly."""
from copy import deepcopy
from scripts.power_automate import shared_validation as shared
from scripts.power_automate.schema_audit import measure
from test_shared_validation import execute, request, FIXTURES


def test_bulk_pair_results_equal_existing_pair_mode_without_self():
    payload = request(mode='PAIRS', leftId=1)
    result = execute(payload)
    assert result['code'] == 'OK'
    actual = result['result']['pairs']
    expected = []
    for profile in payload['profiles']:
        response = execute({**payload, 'mode': 'PAIR', 'rightId': profile['profileId']})
        if response['result']['eligible']:
            expected.append({'profileId': profile['profileId'], **response['result']})
    assert actual == expected
    assert not any(p['profileId'] == 1 for p in actual)


def test_bulk_rejects_missing_actor_and_does_not_default_null_availability():
    assert execute(request(mode='PAIRS', leftId=99999))['code'] == 'PROFILE_NOT_FOUND'
    payload = request(mode='PAIRS', leftId=1)
    for row in payload['profiles']: row['participationStatus'] = None
    result = execute(payload)
    assert result['code'] == 'OK' and result['result']['pairs'] == []


def test_bulk_mode_does_not_change_flow_structure_limits():
    from test_shared_validation import BASELINE
    assert measure(shared.definition_actions(BASELINE, 'test', 'test'))['maximumActionDepth'] <= 8
