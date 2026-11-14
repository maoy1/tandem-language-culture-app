"""Fixture axioms only; business interoperability runs through emitted parents."""
import pytest
from core_native_backend import predicate, seed, Connection, ROLES, ParentRunner


@pytest.mark.parametrize('expression,expected', [
    ("SenderParticipantId eq 1 and RecipientParticipantId eq 2", True),
    ("(SenderParticipantId eq 2 and RecipientParticipantId eq 1) or (SenderParticipantId eq 1 and RecipientParticipantId eq 2)", True),
    ("Status eq 'Accepted' or OperationComplete eq true", False),
    ("TargetGroupId eq null and Status ne 'Accepted'", True)])
def test_transport_filter_subset(expression, expected):
    assert predicate(expression, {'SenderParticipantId': 1, 'RecipientParticipantId': 2,
        'Status': 'Pending', 'OperationComplete': False, 'TargetGroupId': None}) is expected


def test_transport_uniqueness_and_exact_etag_boundary():
    db = seed(); connection = Connection(db)
    uri = "_api/web/lists(guid'" + ROLES['requests'] + "')/items"
    body = {'SenderParticipantId': 1, 'RecipientParticipantId': 2, 'Status': 'Pending',
            'SendOperationKey': 'personal:1:fixture', 'ConnectionKey': 'open:person:1:2'}
    request = {'parameters/uri': uri, 'parameters/method': 'POST', 'parameters/body': body}
    assert connection.request(request)['statusCode'] == 201
    assert connection.request(request)['statusCode'] == 502 and len(db.tables['requests']) == 1
    request.update({'parameters/uri': uri + '(1)', 'parameters/body': {'Status': 'Cancelled'},
                    'parameters/headers': {'IF-MATCH': '"0"', 'X-HTTP-Method': 'MERGE'}})
    assert connection.request(request)['statusCode'] == 412
    request['parameters/headers']['IF-MATCH'] = '"1"'
    assert connection.request(request)['statusCode'] == 204
    assert db.tables['requests'][0]['Status'] == 'Cancelled'


@pytest.mark.parametrize('expression,expected', [
    ("@substring('11111111-2222-4333-8444-555555555555',8,1)", '-'),
    ("@split('request:7:participant:2',':')?[1]", '7'),
    ("@split('request:7',':')?[5]", None),
    ("@utcNow()", '2026-11-14T12:00:00Z'),
    ("@utcNow('yyyy-MM-ddTHH:mm:ssZ')", '2026-11-14T12:00:00Z')])
def test_native_scalar_and_array_primitives_used_by_delivered_flows(expression, expected):
    runner = ParentRunner(Connection(seed()))
    assert runner.expr(expression, {'items': {}}) == expected
