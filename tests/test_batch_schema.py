"""Exercise additive owner setup, read-only audit and repeat behavior."""
from copy import deepcopy
from xml.etree import ElementTree as ET
import pytest

from scripts.power_automate import batch_schema as setup
from scripts.power_automate.schema_audit import measure
from test_shared_validation import ChildRunner
from scripts.power_automate import shared_validation as shared
import json


def native_field(spec):
    return {'InternalName': spec['name'], 'TypeAsString': spec['type'],
            'Required': spec.get('required', False), 'EnforceUniqueValues': spec.get('unique', False),
            'Indexed': spec.get('indexed', False), 'Hidden': False, 'ReadOnlyField': False,
            'DefaultValue': spec.get('default'), 'SchemaXml': setup.field_xml(spec)}


class Tenant:
    def __init__(self, exists=False):
        self.exists = exists
        self.permission = True
        self.rows = 0
        self.fields = [native_field(s) for s in setup.CONTRACT['receipts']['fields']] if exists else []
        self.intro = [native_field(setup.CONTRACT['introduction'])] if exists else []
        self.writes = []
        self.paged = False
        self.fail = None
        self.description = setup.CONTRACT['receipts']['description']
        self.metadata = shared.synthetic_metadata(setup.baseline())['lists']

    def request(self, p):
        uri, method = p['parameters/uri'], p['parameters/method']
        if self.fail and self.fail in uri: return {'statusCode': 503, 'body': {}}
        def response(value): return {'statusCode': 200, 'body': {'d': deepcopy(value)}}
        if 'EffectiveBasePermissions' in uri: return response({'Low': '2048' if self.permission else '0'})
        if method == 'POST':
            self.writes.append(deepcopy(p))
            assert '/items' not in uri and 'role' not in uri.lower()
            if uri == '_api/web/lists': self.exists = True; return response({'Id': 'synthetic-receipt-list'})
            node = ET.fromstring(p['parameters/body']['parameters']['SchemaXml'])
            spec = next(s for s in setup.CONTRACT['receipts']['fields'] + [setup.CONTRACT['introduction']] if s['name'] == node.attrib['Name'])
            (self.intro if setup.CONTRACT['requestsListId'] in uri else self.fields).append(native_field(spec))
            return response({})
        if '/fields?' in uri:
            spec = next((s for s in self.metadata if s['Id'] in uri), None)
            if setup.CONTRACT['requestsListId'] in uri:
                values = [s for s in spec['Fields'] if s['InternalName'] != 'Introduction'] + self.intro
            elif spec: values = spec['Fields']
            else: values = self.fields
            return response({'results': values, **({'__next': 'next-page'} if self.paged else {})})
        if 'getbytitle' in uri:
            return response({'Id': 'synthetic-receipt-list', 'Title': setup.CONTRACT['receipts']['title'], 'BaseTemplate': 100})
        spec = next((s for s in self.metadata if s['Id'] in uri), None)
        if spec: return response({k: spec[k] for k in ['Id', 'Title', 'BaseTemplate', 'ValidationFormula']})
        return response({'results': [{'Id': 'synthetic-receipt-list', 'Title': setup.CONTRACT['receipts']['title'],
                                      'Description': self.description, 'BaseTemplate': 100, 'ItemCount': self.rows}] if self.exists else []})


class AuditRunner(ChildRunner):
    def run(self, actions, ctx=None):
        if 'Call_schema_validator' in actions:
            action = actions['Call_schema_validator']
            payload = self.inputs(action['inputs']['body'], ctx)
            child = ChildRunner(self.server)
            child.run(shared.definition_actions(setup.baseline(), 'synthetic-build', 'rules-hash'),
                      {'items': {}, 'triggerBody': payload})
            self.outputs['Call_schema_validator'] = child.response
            self.action_states['Call_schema_validator'] = 'Succeeded'
            actions = deepcopy(actions); actions.pop('Call_schema_validator')
            for value in actions.values(): value.get('runAfter', {}).pop('Call_schema_validator', None)
        return super().run(actions, ctx)


def execute(tenant, apply=False):
    runner = AuditRunner(tenant)
    runner.run(setup.actions('synthetic-build'), {'items': {}, 'triggerBody': {'boolean': apply}})
    return runner.outputs['Setup_report'], runner


def test_dry_missing_schema_does_not_write_or_claim_ready():
    server = Tenant()
    report, _ = execute(server)
    assert not report['schemaVerified'] and not server.writes
    assert report['differences'][0]['code'] == 'RECEIPT_LIST_MISSING_OR_READ_INCOMPLETE'


def test_apply_creates_only_schema_then_repeat_and_dry_skip_all_writes():
    server = Tenant()
    report, runner = execute(server, True)
    assert report['schemaVerified'], (report, runner.action_states)
    assert len(server.writes) == 12  # one list, ten receipt fields, one optional introduction
    assert report['rowWrites'] == report['deletes'] == report['permissionChanges'] == 0
    before = len(server.writes)
    for apply in (True, False):
        report, _ = execute(server, apply)
        assert report['schemaVerified'] and len(server.writes) == before


def test_revoked_manage_lists_prevents_all_apply_writes():
    server = Tenant(); server.permission = False
    report, _ = execute(server, True)
    assert not report['schemaVerified'] and not server.writes
    assert report['differences'][0]['code'] == 'MANAGE_LISTS_PERMISSION_UNVERIFIED'


def test_nonempty_receipt_list_missing_required_fields_is_not_backfilled():
    server = Tenant(True); server.rows = 2; server.fields.pop(0)
    report, _ = execute(server, True)
    assert not report['schemaVerified'] and not server.writes


@pytest.mark.parametrize('change', ['unique', 'richtext', 'description', 'paging', 'failed-read'])
def test_mismatches_and_incomplete_reads_never_pass_or_convert(change):
    server = Tenant(True)
    if change == 'unique': server.fields[0]['EnforceUniqueValues'] = False
    if change == 'richtext': server.intro[0]['SchemaXml'] = server.intro[0]['SchemaXml'].replace('RichText="FALSE"', 'RichText="TRUE"')
    if change == 'description': server.description = 'Unrelated existing list'
    if change == 'paging': server.paged = True
    if change == 'failed-read': server.fail = '/fields?'
    report, _ = execute(server, True)
    assert not report['schemaVerified'] and not server.writes


def test_structure_and_no_unsafe_updates():
    result = measure(setup.actions('synthetic-build'))
    assert result['actions'] < 150 and result['maximumActionDepth'] <= 8
    assert setup.trigger()['manual']['inputs']['schema']['properties']['boolean']['default'] is False


@pytest.mark.parametrize('change', [None, 'missing-introduction', 'receipt-title', 'receipt-unique', 'richtext'])
def test_batch_schema_extensions_are_checked_by_the_one_shared_child(change):
    baseline = setup.baseline()
    metadata = shared.synthetic_metadata(baseline)
    requests = next(x for x in metadata['lists'] if x['role'] == 'requests')
    receipts = next(x for x in metadata['lists'] if x['role'] == 'receipts')
    if change == 'missing-introduction': requests['Fields'].pop()
    if change == 'receipt-title': receipts['Title'] = 'Unrelated list'
    if change == 'receipt-unique': receipts['Fields'][0]['EnforceUniqueValues'] = False
    if change == 'richtext': requests['Fields'][-1]['SchemaXml'] = '<Field RichText="TRUE" />'
    class NoIO:
        def request(self, _): raise AssertionError('Shared schema child cannot read or write')
    runner = ChildRunner(NoIO())
    runner.run(shared.definition_actions(baseline, 'prospective-build', 'rules-hash'), {'items': {}, 'triggerBody': {
        'text': json.dumps({'contractVersion': 1, 'rulesVersion': 1, 'mode': 'SCHEMA', 'metadata': metadata})}})
    report = json.loads(runner.response['resultjson'])
    assert report['code'] == ('OK' if change is None else 'SCHEMA_MISMATCH'), report
    assert report['result']['allSchema'] and len(report['result']['checkedRoles']) == 8
    assert report['result']['schemaMatches'] == (change is None)
    shared.verify_baseline_sources(baseline)
