"""#14 TandemLeaveGroup. Local packaging only; emitted runtime is Power Automate."""
from copy import deepcopy
import argparse
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4, UUID
from zipfile import ZipFile, ZIP_DEFLATED

from . import discovery_flow as d
from .schema_audit import ALL, measure
from .build_import_probe import build_package as envelope
from .solution_source import RAW_INVOKER

ROOT = Path(__file__).resolve().parents[2]
NAME = 'TandemLeaveGroup'
VERSION = '14.1.1'
RECEIPT_TITLE = 'TandemOperationReceipts'
SITE = 'https://reedelsevier.sharepoint.com/sites/OG-TandemOrg'
REQUESTS = '3d17485d-1dac-41f0-a1af-24e45daa4567'
API = '/providers/Microsoft.PowerApps/apis/shared_sharepointonline'
GUID = {'type': 'string', 'minLength': 36, 'maxLength': 36,
        'pattern': '^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'}
INT = {'type': 'integer', 'minimum': 1, 'maximum': 2147483647}
META = {'type': 'object', 'required': ['etag', 'type'], 'properties': {
    'etag': {'type': 'string', 'pattern': '^"[0-9]+"$'},
    'type': {'type': 'string', 'minLength': 1}}}
INPUTS = {'number': INT, 'number_1': INT, 'number_2': INT, 'text': GUID}


def obj(props):
    return {'type': 'object', 'required': list(props), 'properties': props}


MEMBER = obj({'Id': INT, 'GroupId': INT, 'ParticipantId': INT,
              'MembershipStatus': {'type': 'string', 'enum': ['Active', 'Left']},
              'MembershipKey': {'type': 'string', 'minLength': 1},
              'JoinedAt': {'type': 'string', 'minLength': 1},
              'LeftAt': {'type': ['string', 'null']}, '__metadata': META})
GROUP = obj({'Id': INT, 'Capacity': {'type': 'number', 'minimum': 2, 'maximum': 10},
             'State': {'type': 'string', 'enum': ['Open', 'Closed', 'Ended']},
             'SetupComplete': {'type': 'boolean'}, 'SourceRequestId': {'type': 'number', 'minimum': 1, 'maximum': 2147483647},
             'WriteOwner': {'type': ['string', 'null'], 'maxLength': 255}, '__metadata': META})
REQUEST = obj({'Id': INT, 'Status': {'type': 'string'},
               'OperationComplete': {'type': 'boolean'},
               'RequestType': {'type': 'string', 'enum': ['Personal', 'Group']},
               'SenderParticipantId': {'type': 'number', 'minimum': 1, 'maximum': 2147483647},
               'RecipientParticipantId': {'type': ['number', 'null']},
               'TargetGroupId': {'type': ['integer', 'null']}})
RECEIPT = obj({'Id': INT, 'OperationKey': {'type': 'string'}, 'IntentJson': {'type': 'string'},
               'ResultJson': {'type': ['string', 'null']}, 'Complete': {'type': 'boolean'},
               'AttemptToken': GUID, 'Uncertain': {'type': 'boolean'},
               'Retryable': {'type': 'boolean'}, 'DomainEffects': {'type': 'boolean'},
               'Stage': {'type': 'string'}, '__metadata': META})
RESULT = obj({'kind': {'type': 'string', 'enum': ['LeaveGroup']},
              'operationkey': {'type': 'string'}, 'groupid': INT, 'membershipid': INT,
              'status': {'type': 'string', 'enum': ['Left']},
              'leftat': {'type': 'string', 'minLength': 1},
              'membercount': {'type': 'integer', 'minimum': 0, 'maximum': 2000},
              'freeslots': {'type': 'integer', 'minimum': 0, 'maximum': 10},
              'groupstate': GROUP['properties']['State']})
RESULT['additionalProperties'] = False


def field(name, key):
    return "body('" + name + "')?['" + key + "']"


def rows(name):
    return "body('" + name + "')?['d']?['results']"


def both(*parts):
    return 'and(' + ','.join(parts) + ')'


def eq(a, b):
    return 'equals(' + a + ',' + b + ')'


def load_source(path):
    path = Path(path)
    if path.suffix.lower() == '.zip':
        with ZipFile(path) as z:
            names = [n for n in z.namelist() if n.endswith('/definition.json')]
            if len(names) != 1:
                raise ValueError('Exactly one legacy source flow required')
            return json.loads(z.read(names[0]))
    return json.loads(path.read_text(encoding='utf-8'))


def source_adapter(source, people):
    """Accept the observed legacy Get_item binding; never copy its operation."""
    props = source['properties']
    ref = props['connectionReferences']['shared_sharepointonline']
    if ref.get('source') != 'Invoker':
        raise ValueError('Invoker required; no owner fallback')
    candidates = []
    def walk(block):
        for a in block.values():
            yield a
            yield from walk(a.get('actions', {}))
            yield from walk(a.get('else', {}).get('actions', {}))
    for a in walk(props['definition']['actions']):
        p = a.get('inputs', {})
        if (a.get('type') == 'OpenApiConnection' and
                p.get('parameters', {}).get('table', '').strip('{}').lower()
                == people['lists']['participants']['listId']):
            candidates.append(p)
    if not candidates:
        raise ValueError('Missing legacy participant Get_item binding')
    p = candidates[0]
    if (p['host'].get('apiId') != API or p['host'].get('connectionName') != 'shared_sharepointonline'
            or p['authentication'] != {'type': 'Raw', 'value': RAW_INVOKER}
            or p['parameters']['dataset'] != SITE):
        raise ValueError('Unverified SharePoint site/connector/Raw Invoker binding')
    return SITE, deepcopy(p['authentication'])


def trigger(source):
    if next(iter(source['properties']['definition']['triggers'].values())).get('kind') != 'PowerAppV2':
        raise ValueError('PowerAppV2 source required')
    titles = {'number': 'ParticipantId', 'number_1': 'GroupId',
              'number_2': 'MembershipId', 'text': 'IntentId'}
    return {'manual': {'type': 'Request', 'kind': 'PowerAppV2', 'inputs': {'schema': {
        'type': 'object', 'required': list(titles), 'properties': {
            n: {'type': 'string' if n == 'text' else 'number', 'title': t,
                'x-ms-content-hint': 'TEXT' if n == 'text' else 'NUMBER',
                'x-ms-dynamically-added': True} for n, t in titles.items()}}}}}


class Builder:
    def __init__(self, source, people, groups, build_id):
        self.site, self.auth = source_adapter(source, people)
        self.build_id = str(build_id)
        self.binding = groups.get('lists', {}).get('receipts', {})
        # Target selection is not tenant schema verification. Parent Setup+Audit
        # must pass before enabling business flows; the same import works after setup.
        pinned = self.binding.get('listId')
        self.receipt_id = str(UUID(pinned)) if pinned is not None else None
        if self.receipt_id == '00000000-0000-0000-0000-000000000000':
            raise ValueError('Zero GUID is not a receipt binding')
        ids = {'people': people['lists']['participants']['listId'],
               'groups': groups['lists']['groups']['listId'],
               'members': groups['lists']['members']['listId'],
               'requests': REQUESTS}
        if self.receipt_id:
            ids['receipts'] = self.receipt_id
        self.base = {k: "_api/web/lists(guid'" + str(UUID(v)) + "')" for k, v in ids.items()}
        if len(set(self.base.values())) != len(ids):
            raise ValueError('Receipt/domain list identities must be distinct')
        if self.receipt_id is None:
            self.base['receipts'] = "_api/web/lists/getbytitle('" + RECEIPT_TITLE + "')"
        self.target = {}
        self.previous = None

    def add(self, name, action, settled=False):
        action['runAfter'] = {self.previous: ['Succeeded', 'Failed', 'TimedOut'] if settled else ['Succeeded']} if self.previous else {}
        self.target[name] = action
        self.previous = name

    def compose(self, name, value):
        self.add(name, d.compose(value))

    def set(self, name, variable, value):
        self.add(name, d.setvar(variable, value))

    def gate(self, name, predicate, code):
        self.add(name, d.condition(predicate, {}, {
            name + '_code': d.setvar('Code', code),
            name + '_stop': d.compose('@div(1,0)', name + '_code')}))

    def parse(self, name, content, schema):
        self.add(name, d.parse(content, schema))

    def branch(self, name, predicate, yes, no=lambda: None):
        parent, prev = self.target, self.previous
        self.target, self.previous = {}, None
        yes()
        y = self.target
        self.target, self.previous = {}, None
        no()
        n = self.target
        self.target, self.previous = parent, prev
        self.add(name, d.condition(predicate, y, n))

    def http(self, name, uri, method='GET', payload=None, etag=None, settled=False):
        headers = {'Accept': 'application/json;odata=verbose'}
        if method != 'GET':
            headers['Content-Type'] = 'application/json;odata=verbose'
        if etag:
            headers.update({'X-HTTP-Method': 'MERGE', 'IF-MATCH': '@' + etag})
        params = {'dataset': self.site, 'parameters/method': method,
                  'parameters/uri': uri, 'parameters/headers': headers}
        if payload is not None:
            params['parameters/body'] = payload
        self.add(name, {'type': 'OpenApiConnection', 'inputs': {'parameters': params,
            'host': {'apiId': API, 'connectionName': 'shared_sharepointonline', 'operationId': 'HttpRequest'},
            'authentication': deepcopy(self.auth), 'retryPolicy': {'type': 'none'}}}, settled)

    def item(self, name, role, id_, schema, settled=False):
        self.http(name + '_get', d.cat(self.base[role] + '/items(', '@string(' + id_ + ')', ')'), settled=settled)
        self.parse(name, "@body('" + name + "_get')?['d']", schema)

    def merge(self, name, role, row, values):
        self.set(name + '_code', 'Code', 'RELEASE_PENDING' if name=='Release_group' else 'OUTCOME_UNKNOWN')
        self.set(name + '_mark', 'WriteAttempted', True)
        self.http(name, d.cat(self.base[role] + '/items(', '@string(' + field(row, 'Id') + ')', ')'),
                  'POST', {'__metadata': {'type': '@' + field(row, '__metadata') + "?['type']"}, **values},
                  field(row, '__metadata') + "?['etag']")

    def collection(self, name, role, filter_, bound, schema=None, settled=False):
        self.http(name, d.cat(self.base[role] + '/items?$filter=', '@' + filter_, '&$top=' + str(bound + 1)), settled=settled)
        self.gate(name + '_bound', d.complete(name, bound), 'INCOMPLETE_READ')
        if schema:
            self.parse(name + '_rows', '@' + rows(name), {'type': 'array', 'maxItems': bound, 'items': schema})

    def same_member(self, row, earlier='Member_initial'):
        keys = ['Id', 'GroupId', 'ParticipantId', 'MembershipKey', 'JoinedAt']
        return both(*(eq(field(row, k), field(earlier, k)) for k in keys))

    def committed(self, prefix, member, group):
        self.gate(prefix + '_group_ready', both(eq(field(group, 'SetupComplete'), 'true'),
            eq(field(group, 'SourceRequestId'), 'int(' + field(group, 'SourceRequestId') + ')')), 'PROVISIONAL_MEMBERSHIP')
        self.compose(prefix + '_key_parts', "@split(" + field(member, 'MembershipKey') + ",':')")
        self.gate(prefix + '_key_shape', "equals(length(outputs('" + prefix + "_key_parts')),4)", 'MEMBERSHIP_INTEGRITY')
        self.parse(prefix + '_request_id', "@int(outputs('" + prefix + "_key_parts')?[1])", INT)
        rid = "body('" + prefix + "_request_id')"
        self.gate(prefix + '_key_canonical', eq(field(member, 'MembershipKey'),
                  "concat('request:',string(" + rid + "),':participant:',string(body('Input')?['number']))"), 'MEMBERSHIP_INTEGRITY')
        self.item(prefix + '_source', 'requests', 'int(' + field(group, 'SourceRequestId') + ')', REQUEST)
        self.item(prefix + '_request', 'requests', rid, REQUEST)
        src, req = prefix + '_source', prefix + '_request'
        actor = "body('Input')?['number']"
        personal = both(eq(field(req, 'RequestType'), "'Personal'"), eq(field(req, 'Id'), field(group, 'SourceRequestId')),
                        eq(field(req, 'TargetGroupId'), 'null'),
                        "or(" + eq(field(req, 'SenderParticipantId'), actor) + ',' + eq(field(req, 'RecipientParticipantId'), actor) + ')')
        joined = both(eq(field(req, 'RequestType'), "'Group'"), eq(field(req, 'TargetGroupId'), field(group, 'Id')),
                      eq(field(req, 'SenderParticipantId'), actor), eq(field(req, 'RecipientParticipantId'), 'null'))
        self.gate(prefix + '_commit', both(
            eq(field(group, 'SetupComplete'), 'true'),
            eq(field(src, 'Id'), field(group, 'SourceRequestId')),
            eq(field(src, 'RequestType'), "'Personal'"), eq(field(src, 'TargetGroupId'), 'null'),
            "greater(coalesce(" + field(src, 'RecipientParticipantId') + ',0),0)',
            "not(" + eq(field(src, 'SenderParticipantId'), field(src, 'RecipientParticipantId')) + ')',
            eq(field(src, 'Status'), "'Accepted'"), eq(field(src, 'OperationComplete'), 'true'),
            eq(field(req, 'Id'), rid), eq(field(req, 'Status'), "'Accepted'"),
            eq(field(req, 'OperationComplete'), 'true'), 'or(' + personal + ',' + joined + ')'), 'PROVISIONAL_MEMBERSHIP')

    def group_stable(self, row, earlier, token=True):
        fields = ['Id', 'Capacity', 'State', 'SourceRequestId', 'SetupComplete']
        predicates = [eq(field(row, k), field(earlier, k)) for k in fields]
        if token:
            predicates.append(eq(field(row, 'WriteOwner'), "outputs('Owner_token')"))
        return both(*predicates)

    def receipt_read(self, prefix, settled=False):
        self.collection(prefix, 'receipts', "concat('OperationKey eq ''',outputs('Operation_key'),'''')", 1, settled=settled)

    def receipt_parse(self, name, read):
        self.gate(name + '_one', 'equals(length(' + rows(read) + '),1)', 'OUTCOME_UNKNOWN')
        self.parse(name, '@first(' + rows(read) + ')', RECEIPT)
        self.parse(name + '_intent', '@' + field(name, 'IntentJson'), obj({
            'kind': {'type': 'string', 'enum': ['LeaveGroup']}, 'version': {'type': 'integer', 'enum': [1]},
            'actorId': INT, 'groupId': INT, 'membershipId': INT}))
        self.gate(name + '_matches', both(eq(field(name, 'OperationKey'), "outputs('Operation_key')"),
            "equals(body('" + name + "_intent'),outputs('Intent'))"), 'INTENT_CONFLICT')

    def existing(self):
        self.receipt_parse('Existing_receipt', 'Find_receipt')
        self.gate('Existing_complete', both(eq(field('Existing_receipt', 'Complete'), 'true'),
            eq(field('Existing_receipt', 'DomainEffects'), 'true'), eq(field('Existing_receipt', 'Uncertain'), 'false'),
            eq(field('Existing_receipt', 'Stage'), "'Complete'"), eq(field('Existing_receipt', 'Retryable'), 'false')), 'OUTCOME_UNKNOWN')
        self.parse('Saved_result', '@' + field('Existing_receipt', 'ResultJson'), RESULT)
        self.gate('Saved_result_binding', both(eq(field('Saved_result', 'operationkey'), "outputs('Operation_key')"),
            eq(field('Saved_result', 'groupid'), "body('Input')?['number_1']"),
            eq(field('Saved_result', 'membershipid'), "body('Input')?['number_2']"),
            eq(field('Member_initial', 'MembershipStatus'), "'Left'"),
            eq(field('Member_initial', 'LeftAt'), field('Saved_result', 'leftat'))), 'RECEIPT_INTEGRITY')
        self.set('Use_saved_result', 'SavedResult', "@body('Saved_result')")
        self.set('Use_old_token', 'ReleaseToken', "@concat(outputs('Operation_key'),':'," + field('Existing_receipt', 'AttemptToken') + ')')
        self.set('Mark_replay', 'Replay', True)
        self.set('Existing_ready', 'ReceiptReady', True)

    def count(self, prefix):
        self.collection(prefix, 'members', "concat('GroupId eq ',string(body('Input')?['number_1']))", 2000, MEMBER)
        self.add(prefix + '_active', d.query('@' + rows(prefix), "equals(item()?['MembershipStatus'],'Active')"))
        self.add(prefix + '_own', d.query("@body('" + prefix + "_active')", "equals(item()?['ParticipantId'],body('Input')?['number'])"))
        self.add(prefix + '_foreign', d.query('@' + rows(prefix), "not(equals(item()?['GroupId'],body('Input')?['number_1']))"))
        self.gate(prefix + '_group', "equals(length(body('" + prefix + "_foreign')),0)", 'MEMBERSHIP_INTEGRITY')
        # Every physical Active row counts, even one lacking a committed request.

    def fresh(self):
        self.gate('New_active', both(eq(field('Member_initial', 'MembershipStatus'), "'Active'"),
                                    'empty(' + field('Member_initial', 'LeftAt') + ')'), 'ALREADY_LEFT')
        self.compose('Attempt_uuid', '@guid()')
        self.compose('Owner_token', "@concat(outputs('Operation_key'),':',outputs('Attempt_uuid'))")
        self.gate('Owner_token_bound', "lessOrEquals(length(outputs('Owner_token')),255)", 'INVALID_INPUT')
        self.set('Create_receipt_code', 'Code', 'OUTCOME_UNKNOWN')
        self.set('Create_receipt_mark', 'WriteAttempted', True)
        self.http('Create_receipt', self.base['receipts'] + '/items', 'POST', {
            '__metadata': {'type': '@' + field('Receipt_metadata', 'ListItemEntityTypeFullName')},
            'OperationKey': "@outputs('Operation_key')", 'IntentJson': "@string(outputs('Intent'))",
            'Complete': False, 'Uncertain': False, 'Retryable': False, 'DomainEffects': False,
            'AttemptToken': "@outputs('Attempt_uuid')", 'SealedAttempts': '[]', 'Stage': 'Running'})
        self.receipt_read('Created_readback', settled=True)
        self.receipt_parse('Owned_receipt', 'Created_readback')
        self.gate('Own_attempt', both(eq(field('Owned_receipt', 'AttemptToken'), "outputs('Attempt_uuid')"),
            eq(field('Owned_receipt', 'Complete'), 'false'), eq(field('Owned_receipt', 'Uncertain'), 'false'),
            eq(field('Owned_receipt', 'DomainEffects'), 'false'), eq(field('Owned_receipt', 'Stage'), "'Running'")), 'OUTCOME_UNKNOWN')
        self.item('Group_claim', 'groups', "body('Input')?['number_1']", GROUP)
        self.gate('Claim_group_identity', both(eq(field('Group_claim', 'Id'), field('Group_initial', 'Id')),
            eq(field('Group_claim', 'Capacity'), 'int(' + field('Group_claim', 'Capacity') + ')')), 'GROUP_INTEGRITY')
        self.gate('Group_available', 'empty(' + field('Group_claim', 'WriteOwner') + ')', 'GROUP_BUSY')
        self.merge('Claim_group', 'groups', 'Group_claim', {'WriteOwner': "@outputs('Owner_token')"})
        self.item('Group_live', 'groups', "body('Input')?['number_1']", GROUP, settled=True)
        self.gate('Claim_proved', self.group_stable('Group_live', 'Group_claim'), 'GROUP_BUSY_OR_UNKNOWN')
        self.item('Member_live', 'members', "body('Input')?['number_2']", MEMBER)
        self.gate('Live_member', both(self.same_member('Member_live'),
            eq(field('Member_live', 'MembershipStatus'), "'Active'"), 'empty(' + field('Member_live', 'LeftAt') + ')'), 'MEMBERSHIP_CHANGED')
        self.committed('Live', 'Member_live', 'Group_live')
        self.count('Before_members')
        self.gate('One_active_episode', both("equals(length(body('Before_members_own')),1)",
            "equals(first(body('Before_members_own'))?['Id'],body('Input')?['number_2'])"), 'MEMBERSHIP_INTEGRITY')
        self.compose('Left_at', "@utcNow('yyyy-MM-ddTHH:mm:ssZ')")
        self.merge('Leave_CAS', 'members', 'Member_live', {'MembershipStatus': 'Left', 'LeftAt': "@outputs('Left_at')"})
        self.item('Member_after', 'members', "body('Input')?['number_2']", MEMBER, settled=True)
        self.gate('Leave_proved', both(self.same_member('Member_after'),
            eq(field('Member_after', 'MembershipStatus'), "'Left'"), eq(field('Member_after', 'LeftAt'), "outputs('Left_at')")), 'OUTCOME_UNKNOWN')
        self.item('Group_after', 'groups', "body('Input')?['number_1']", GROUP)
        self.gate('Group_unchanged', self.group_stable('Group_after', 'Group_live'), 'OUTCOME_UNKNOWN')
        self.count('After_members')
        self.gate('Count_proved', both(
            "equals(length(body('After_members_active')),sub(length(body('Before_members_active')),1))",
            "equals(length(body('After_members_own')),0)"), 'OUTCOME_UNKNOWN')
        self.compose('New_result', {'kind': 'LeaveGroup', 'operationkey': "@outputs('Operation_key')",
            'groupid': "@body('Input')?['number_1']", 'membershipid': "@body('Input')?['number_2']",
            'status': 'Left', 'leftat': "@outputs('Left_at')", 'groupstate': '@' + field('Group_after', 'State'),
            'membercount': "@length(body('After_members_active'))",
            'freeslots': "@if(greater(length(body('After_members_active')),int(" + field('Group_after', 'Capacity') +
                         ")),0,sub(int(" + field('Group_after', 'Capacity') + "),length(body('After_members_active'))))"})
        self.set('Set_new_result', 'SavedResult', "@outputs('New_result')")
        self.merge('Complete_receipt', 'receipts', 'Owned_receipt', {
            'Complete': True, 'ResultJson': "@string(outputs('New_result'))", 'DomainEffects': True,
            'Stage': 'Complete', 'Uncertain': False, 'Retryable': False})
        self.receipt_read('Completed_readback', settled=True)
        self.receipt_parse('Completed_receipt', 'Completed_readback')
        self.parse('Completed_result', '@' + field('Completed_receipt', 'ResultJson'), RESULT)
        self.gate('Completion_proved', both(
            eq(field('Completed_receipt', 'Complete'), 'true'),
            eq(field('Completed_receipt', 'DomainEffects'), 'true'),
            eq(field('Completed_receipt', 'Stage'), "'Complete'"),
            eq(field('Completed_receipt', 'AttemptToken'), "outputs('Attempt_uuid')"),
            eq(field('Completed_receipt', 'Uncertain'), 'false'),
            "equals(body('Completed_result'),outputs('New_result'))"), 'OUTCOME_UNKNOWN')
        self.set('Release_new_token', 'ReleaseToken', "@outputs('Owner_token')")
        self.set('New_ready', 'ReceiptReady', True)

    def release(self):
        self.merge('Release_group', 'groups', 'Group_release', {'WriteOwner': ''})
        self.item('Group_released', 'groups', "body('Input')?['number_1']", GROUP, settled=True)
        self.gate('Release_proved', both(eq(field('Group_released', 'Id'), "body('Input')?['number_1']"),
            'not(' + eq(field('Group_released', 'WriteOwner'), "variables('ReleaseToken')") + ')'), 'RELEASE_PENDING')
        self.set('Release_verified', 'ReleaseProved', True)

    def work(self):
        self.set('Input_code', 'Code', 'INVALID_INPUT')
        self.parse('Input', '@triggerBody()', {**obj(INPUTS), 'additionalProperties': False})
        self.set('Read_code', 'Code', 'READ_OR_DATA_FAILED')
        self.http('Read_invoker', '_api/web/currentuser?$select=Id')
        self.parse('Invoker', "@body('Read_invoker')?['d']", obj({'Id': INT}))
        self.collection('Own_profile', 'people', "concat('ParticipantaccountId eq ',string(body('Invoker')?['Id']))", 1)
        self.gate('Actor_matches', both('equals(length(' + rows('Own_profile') + '),1)',
            "equals(first(" + rows('Own_profile') + ")?['Id'],body('Input')?['number'])"), 'UNAUTHORIZED')
        self.item('Member_initial', 'members', "body('Input')?['number_2']", MEMBER)
        self.gate('Own_episode', both(eq(field('Member_initial', 'ParticipantId'), "body('Input')?['number']"),
            eq(field('Member_initial', 'GroupId'), "body('Input')?['number_1']"),
            eq(field('Member_initial', 'Id'), "body('Input')?['number_2']")), 'NOT_MEMBER')
        self.item('Group_initial', 'groups', "body('Input')?['number_1']", GROUP)
        self.gate('Group_identity', both(eq(field('Group_initial', 'Id'), "body('Input')?['number_1']"),
            eq(field('Group_initial', 'Capacity'), 'int(' + field('Group_initial', 'Capacity') + ')')), 'GROUP_INTEGRITY')
        self.committed('Initial', 'Member_initial', 'Group_initial')
        self.compose('Operation_key', "@concat('leave:',string(body('Input')?['number']),':',toLower(body('Input')?['text']))")
        self.compose('Intent', {'kind': 'LeaveGroup', 'version': 1, 'actorId': "@body('Input')?['number']",
            'groupId': "@body('Input')?['number_1']", 'membershipId': "@body('Input')?['number_2']"})
        self.http('Receipt_type', self.base['receipts'] + '?$select=Id,Title,ListItemEntityTypeFullName')
        self.parse('Receipt_metadata', "@body('Receipt_type')?['d']", obj({
            'Id': {**GUID, **({'enum': [self.receipt_id]} if self.receipt_id else {})},
            'Title': {'type': 'string', 'enum': [RECEIPT_TITLE]},
            'ListItemEntityTypeFullName': {'type': 'string', 'minLength': 1}}))
        self.receipt_read('Find_receipt')
        self.branch('Existing_intent', 'equals(length(' + rows('Find_receipt') + '),1)', self.existing, self.fresh)
        # Preserve the preceding failure Code without a self-referencing SetVariable.
        self.add('Require_receipt_ready', d.condition("variables('ReceiptReady')", {}, {
            'Require_receipt_ready_stop': d.compose('@div(1,0)')}))
        self.target['Require_receipt_ready']['runAfter'] = {'Existing_intent': ['Succeeded', 'Failed', 'TimedOut']}
        self.set('Release_code', 'Code', 'RELEASE_PENDING')
        self.item('Group_release', 'groups', "body('Input')?['number_1']", GROUP)
        self.gate('Release_identity', eq(field('Group_release', 'Id'), "body('Input')?['number_1']"), 'GROUP_INTEGRITY')
        self.branch('Release_matching_old_token',
                    eq(field('Group_release', 'WriteOwner'), "variables('ReleaseToken')"), self.release,
                    lambda: self.set('Old_token_absent', 'ReleaseProved', True))
        self.gate('Require_release_proved', "variables('ReleaseProved')", 'RELEASE_PENDING')
        self.target['Require_release_proved']['runAfter'] = {'Release_matching_old_token': ['Succeeded', 'Failed', 'TimedOut']}
        self.set('Success_code', 'Code', 'LEFT')

    def build(self):
        for name, typ, value in [('Code', 'string', 'READ_OR_DATA_FAILED'), ('SavedResult', 'object', {}),
                                 ('ReleaseToken', 'string', ''), ('Replay', 'boolean', False),
                                 ('WriteAttempted', 'boolean', False), ('ReceiptReady', 'boolean', False),
                                 ('ReleaseProved', 'boolean', False)]:
            self.add('Initialize_' + name, {'type': 'InitializeVariable', 'inputs': {
                'variables': [{'name': name, 'type': typ, 'value': value}]}})
        parent, prev = self.target, self.previous
        self.target, self.previous = {}, None
        self.work()
        work = self.target
        self.target, self.previous = parent, prev
        self.add('Leave_work', {'type': 'Scope', 'actions': work})
        response = {'success': "@equals(variables('Code'),'LEFT')", 'resultcode': "@variables('Code')",
            'message': "@if(equals(variables('Code'),'LEFT'),'You have left this group. Refresh your groups.','The leave could not be confirmed. Refresh and retain the same intent for retry.')",
            'resultjson': "@if(equals(variables('Code'),'LEFT'),string(variables('SavedResult')),'{}')",
            'replay': "@and(equals(variables('Code'),'LEFT'),variables('Replay'))",
            'writeattempted': "@variables('WriteAttempted')",
            'outcomeunknown': "@and(not(equals(variables('Code'),'LEFT')),variables('WriteAttempted'))",
            'runreference': "@workflow()?['run']?['name']", 'buildid': self.build_id,
            'mode': 'OWNER_PREVIEW_PENDING_ACCESS_PROOF'}
        props = {k: {'type': 'boolean' if k in ['success', 'replay', 'writeattempted', 'outcomeunknown'] else 'string',
                     'title': k, 'x-ms-dynamically-added': True,
                     'x-ms-content-hint': 'BOOLEAN' if k in ['success', 'replay', 'writeattempted', 'outcomeunknown'] else 'TEXT'}
                 for k in response}
        self.add('Respond_to_a_Power_App_or_flow', {'type': 'Response', 'kind': 'PowerApp', 'inputs': {
            'statusCode': 200, 'schema': obj(props), 'body': response}})
        self.target['Respond_to_a_Power_App_or_flow']['runAfter'] = {'Leave_work': ALL}
        measure(self.target)
        return self.target


def build_actions(source, people, groups, build_id):
    return Builder(source, people, groups, build_id).build()


def build_package(source, output, *, groups=None, build_id=None):
    source, output = Path(source), Path(output)
    if any(output.with_suffix(s).exists() for s in ['.zip', '.definition.json', '.review.json']):
        raise FileExistsError(output)
    original = load_source(source)
    people = json.loads((ROOT / 'config/tenant_schema_mapping.json').read_text())
    groups = groups or json.loads((ROOT / 'config/group_schema_mapping.json').read_text())
    build_id = str(build_id or uuid4())
    b = Builder(original, people, groups, build_id)
    actions = b.build()
    with TemporaryDirectory() as tmp:
        seed = Path(tmp) / 'envelope.zip'
        envelope(seed, sharepoint_site=b.site)
        with ZipFile(seed) as z:
            entries = {n: json.loads(z.read(n)) for n in z.namelist()}
    doc = next(v for n, v in entries.items() if n.endswith('/definition.json'))
    doc['properties']['displayName'] = NAME + ' ' + VERSION
    doc['properties']['definition'].update(triggers=trigger(original), actions=actions)
    ref = deepcopy(original['properties']['connectionReferences']['shared_sharepointonline'])
    ref['connectionName'] = 'IMPORT_SELECT_EXISTING_SHAREPOINT_CONNECTION'
    doc['properties']['connectionReferences'] = {'shared_sharepointonline': ref}
    entries['manifest.json']['details'].update(displayName=NAME + ' ' + VERSION,
        description='Issue 14 owner preview; Exact receipt title or pinned GUID; parent Setup+Audit before enabling. Create as new.')
    for res in entries['manifest.json']['resources'].values():
        if res['type'] == 'Microsoft.Flow/flows':
            res['details']['displayName'] = NAME + ' ' + VERSION
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, 'x', ZIP_DEFLATED) as z:
        for n, v in entries.items():
            z.writestr(n, json.dumps(v, indent=2) + '\n')
    review = {'sourceTicket': 14, 'version': VERSION, 'buildId': build_id, 'flowId': doc['name'],
        **measure(actions), 'sourceSha256': hashlib.sha256(source.read_bytes()).hexdigest(),
        'generatorSha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'packageSha256': hashlib.sha256(output.read_bytes()).hexdigest(),
        'connectionSource': 'Invoker', 'rawAuthenticationPreserved': True, 'ownerFallback': False,
        'tenantSchemaVerified': False, 'receiptBinding': 'GUID' if b.receipt_id else 'EXACT_TITLE',
        'receiptListId': b.receipt_id, 'receiptListTitle': RECEIPT_TITLE,
        'enablementPrerequisite': 'Parent Setup Apply + complete Audit PASS before enabling business flows; no rebuild required',
        'sharedCalls': 0, 'writeRetries': 'none', 'domainWrite': 'Only own Active membership -> Left/LeftAt',
        'guardToken': 'OperationKey + colon + attempt UUID <=255; opaque across writers',
        'solutionAssembly': 'PARENT_PENDING', 'native': 'NOT RUN', 'ordinaryUserAccess': 'DEFERRED_NOT_VERIFIED'}
    output.with_suffix('.definition.json').write_bytes((json.dumps(doc, indent=2) + '\n').encode())
    output.with_suffix('.review.json').write_bytes((json.dumps(review, indent=2) + '\n').encode())
    return review


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, default=ROOT / 'artifacts/tandem_discovery/TandemDiscovery-v2.definition.json')
    p.add_argument('--output', type=Path, default=ROOT / 'artifacts/leave_group/TandemLeaveGroup-v1.zip')
    p.add_argument('--groups', type=Path, help='Optional pinned groups mapping including lists.receipts.listId; default is exact title')
    args = p.parse_args()
    print(json.dumps(build_package(args.source, args.output,
        groups=json.loads(args.groups.read_text()) if args.groups else None), indent=2))


if __name__ == '__main__':
    main()
