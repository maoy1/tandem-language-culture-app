"""#11 native personal response. Local generator only; no Python runtime."""
from copy import deepcopy
import argparse
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile, ZIP_DEFLATED
from xml.etree import ElementTree as ET

from . import discovery_flow as d
from .schema_audit import measure, ALL
from .build_import_probe import build_package as legacy_envelope
from .solution_source import inspect_caller_export, invoker_parent_document

ROOT = Path(__file__).resolve().parents[2]
NAME = 'TandemRespondRequest'
VERSION = '11.1.0'
BUILD = '94e47272-28bc-4529-bb2f-521b90e43011'
FLOW_ID = 'fd170a11-2aec-4bab-a3f1-38ed38f23211'
CHILD = 'e9aa88eb-a666-4df1-b088-176be7bcd00d'
SHARED_BUILD = 'c79b7b64-b3ce-4de3-aa74-0ed62bca1524'
SITE = 'https://reedelsevier.sharepoint.com/sites/OG-TandemOrg'
RECEIPTS = "_api/web/lists/getbytitle('TandemOperationReceipts')"
INPUTS = ['number', 'number_1', 'text', 'text_1', 'text_2', 'number_2', 'text_3', 'text_4']
SCHEMA_INPUTS = {
    'number': {'type': 'integer', 'minimum': 1},
    'number_1': {'type': 'integer', 'minimum': 1},
    'text': {'type': 'string', 'enum': ['Accept', 'Decline']},
    'text_5': {'type': 'string', 'minLength': 36, 'maxLength': 36,
               'pattern': '^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'},
}


def load(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


def raw(n):
    return "body('" + n + "')?['d']"


def field(n, f):
    return raw(n) + "?['" + f + "']"


def rows(n):
    return raw(n) + "?['results']"


def safe_first(n):
    return "first(union(coalesce(" + rows(n) + ",json('[]')),createArray(json('{}'))))"


def same(a, b):
    return 'equals(' + a + ',' + b + ')'


def both(*parts):
    return 'and(' + ','.join(parts) + ')'


def string(s):
    return "'" + s.replace("'", "''") + "'"


def ref(base, id_):
    return d.cat(base + '/items(', '@string(' + id_ + ')', ')')


def schema_input():
    snapshot = load('config/participant_response_flow.snapshot.json')
    trigger = deepcopy(snapshot['definition']['triggers'])
    props = trigger['manual']['inputs']['schema']['properties']
    if list(props) != INPUTS:
        raise ValueError('Legacy trigger changed; review mapping')
    props['text_5'] = {'title': 'IntentId', 'type': 'string',
                      'description': 'Retain one GUID per explicit response, including retries.',
                      'x-ms-content-hint': 'TEXT', 'x-ms-dynamically-added': True}
    trigger['manual']['inputs']['schema']['required'].append('text_5')
    return trigger


class Builder:
    def __init__(self):
        people = load('config/tenant_schema_mapping.json')['lists']
        groups = load('config/group_schema_mapping.json')['lists']
        requests = next(x for x in load('config/shared_validation_schema.json')['lists'] if x['role'] == 'requests')
        self.base = {k: "_api/web/lists(guid'" + v['listId'] + "')" for k, v in {**people, **groups, 'requests': requests}.items()}
        self.base['receipts'] = RECEIPTS
        self.actions = {}
        self.target = self.actions
        self.previous = None

    def add(self, name, action, all_after=False):
        if name in self.target:
            raise ValueError('Duplicate action ' + name)
        action['runAfter'] = {self.previous: list(ALL) if all_after else ['Succeeded']} if self.previous else {}
        self.target[name] = action
        self.previous = name
        return name

    def compose(self, name, value):
        return self.add(name, d.compose(value))

    def set(self, name, variable, value):
        return self.add(name, d.setvar(variable, value))

    def gate(self, name, predicate, code):
        # A failed built-in action stops this scope, preserving all history.
        return self.add(name, d.condition(predicate, {}, {
            name + '_code': d.setvar('Code', code),
            name + '_stop': d.compose('@div(1,0)', name + '_code')}))

    def http(self, name, uri, method='GET', body=None, etag=None, all_after=False):
        headers = {'Accept': 'application/json;odata=verbose'}
        if method != 'GET':
            headers['Content-Type'] = 'application/json;odata=verbose'
        if etag is not None:
            headers.update({'X-HTTP-Method': 'MERGE', 'IF-MATCH': '@' + etag})
        params = {'dataset': SITE, 'parameters/method': method, 'parameters/uri': uri, 'parameters/headers': headers}
        if body is not None:
            params['parameters/body'] = body
        result = self.add(name, {'type': 'OpenApiConnection', 'inputs': {
            'host': {'apiId': '/providers/Microsoft.PowerApps/apis/shared_sharepointonline',
                     'connectionName': 'shared_sharepointonline', 'operationId': 'HttpRequest'},
            'parameters': params, 'retryPolicy': {'type': 'none'}}}, all_after)
        if all_after:
            # Reconcile an attempted write, never resume a skipped stage after
            # an earlier validation/identity failure.
            for statuses in self.target[name]['runAfter'].values():
                statuses.remove('Skipped')
        return result

    def post(self, name, role, value):
        body = {'__metadata': {'type': '@' + field('Meta_' + role, 'ListItemEntityTypeFullName')}, **value}
        self.http(name, self.base[role] + '/items', 'POST', body)

    def merge(self, name, role, row, value):
        body = {'__metadata': {'type': '@' + field(row, '__metadata') + "?['type']"}, **value}
        self.http(name, ref(self.base[role], field(row, 'Id')), 'POST', body,
                  field(row, '__metadata') + "?['etag']")

    def collection(self, name, role, filter_, bound=2, all_after=False):
        self.http(name, d.cat(self.base[role] + '/items?$filter=', '@' + filter_, '&$top=' + str(bound + 1)),
                  all_after=all_after)
        self.gate(name + '_complete', d.complete(name, bound), 'INCOMPLETE_READ')

    def scope(self, name, callback, all_after=False):
        parent, previous = self.target, self.previous
        self.target, self.previous = {}, None
        callback()
        inside = self.target
        self.target, self.previous = parent, previous
        self.add(name, {'type': 'Scope', 'actions': inside}, all_after)

    def branch(self, name, test, yes, no=None):
        parent, previous = self.target, self.previous
        self.target, self.previous = {}, None
        yes()
        yes_actions = self.target
        self.target, self.previous = {}, None
        if no:
            no()
        no_actions = self.target
        self.target, self.previous = parent, previous
        self.add(name, d.condition(test, yes_actions, no_actions))

    def request_identity(self, row):
        return both(same(field(row, 'RequestType'), "'Personal'"),
                    same(field(row, 'TargetGroupId'), 'null'),
                    same(field(row, 'RecipientParticipantId'), "triggerBody()?['number']"),
                    same(field(row, 'SenderParticipantId'), "outputs('Initial_request')?['SenderParticipantId']"),
                    same(field(row, 'RecipientParticipantId'), "outputs('Initial_request')?['RecipientParticipantId']"))

    def accepted(self, row, complete_=False):
        return both(self.request_identity(row), same(field(row, 'Status'), "'Accepted'"),
                    same(field(row, 'WinningOperationKey'), "outputs('Operation_key')"),
                    same(field(row, 'OperationComplete'), 'true' if complete_ else 'false'))

    def authorize(self):
        self.add('Input', d.parse('@triggerBody()', {'type': 'object', 'required': list(SCHEMA_INPUTS), 'properties': SCHEMA_INPUTS}))
        self.http('Read_invoker', '_api/web/currentuser?$select=Id')
        self.gate('Invoker_valid', "greater(coalesce(" + field('Read_invoker', 'Id') + ',0),0)', 'CALLER_UNAVAILABLE')
        self.collection('Own_profile', 'participants',
                        "concat('ParticipantaccountId eq ',string(" + field('Read_invoker', 'Id') + '))', 2)
        self.gate('Own_profile_matches', both(same('length(' + rows('Own_profile') + ')', '1'),
                       same(safe_first('Own_profile') + "?['Id']", "triggerBody()?['number']")), 'UNAUTHORIZED')
        self.http('Read_request', ref(self.base['requests'], "triggerBody()?['number_1']"))
        self.compose('Initial_request', '@' + raw('Read_request'))
        self.gate('Personal_recipient', both(self.request_identity('Read_request'),
                    "greater(coalesce(" + field('Read_request', 'SenderParticipantId') + ',0),0)',
                    "not(equals(" + field('Read_request', 'SenderParticipantId') + ",triggerBody()?['number']))"), 'UNAUTHORIZED')
        self.compose('Operation_key', "@concat('respond:',string(triggerBody()?['number']),':',toLower(triggerBody()?['text_5']))")
        self.compose('Attempt', '@guid()')
        self.compose('Owner_token', "@concat(outputs('Operation_key'),':',outputs('Attempt'))")
        self.branch('Parse_accept_inputs_only', "equals(triggerBody()?['text'],'Accept')", self.accept_inputs)
        # Decline never parses unused acceptance JSON.
        self.compose('Typed_intent', {
            'kind': 'PersonalResponse', 'version': 1, 'actorId': "@triggerBody()?['number']",
            'requestId': "@triggerBody()?['number_1']", 'senderId': '@' + field('Read_request', 'SenderParticipantId'),
            'decision': "@triggerBody()?['text']",
            **{key: "@if(equals(triggerBody()?['text'],'Accept'),triggerBody()?['" + source + "']," + empty + ')'
               for key, source, empty in [('groupName', 'text_1', "''"), ('exchangeType', 'text_2', "''"),
                                          ('capacity', 'number_2', '0')]},
            'languageFocusIds': "@if(equals(triggerBody()?['text'],'Accept'),body('Language_focus'),json('[]'))",
            'cultureFocusIds': "@if(equals(triggerBody()?['text'],'Accept'),body('Culture_focus'),json('[]'))"})
        for role in ['receipts', 'groups', 'members']:
            self.http('Meta_' + role, self.base[role] + '?$select=Id,Title,ListItemEntityTypeFullName')
            self.gate('Meta_' + role + '_valid', "not(empty(" + field('Meta_' + role, 'ListItemEntityTypeFullName') + '))', 'SCHEMA_UNAVAILABLE')
        self.gate('Receipt_title', same(field('Meta_receipts', 'Title'), "'TandemOperationReceipts'"), 'SCHEMA_UNAVAILABLE')

    def receipt_lookup(self, name, all_after=False):
        self.collection(name, 'receipts', "concat('OperationKey eq ''',outputs('Operation_key'),'''')", 1, all_after)

    def receipt_setup(self):
        self.receipt_lookup('Find_receipt')
        def create():
            self.post('Create_receipt', 'receipts', {
                'OperationKey': "@outputs('Operation_key')", 'IntentJson': "@string(outputs('Typed_intent'))",
                'Complete': False, 'Uncertain': False, 'Retryable': False, 'DomainEffects': False,
                'AttemptToken': '', 'SealedAttempts': '[]', 'Stage': 'Prepared'})
        self.branch('Receipt_absent', same('length(' + rows('Find_receipt') + ')', '0'), create)
        self.receipt_lookup('Receipt_readback', True)
        self.gate('Receipt_unique', same('length(' + rows('Receipt_readback') + ')', '1'), 'RECEIPT_UNAVAILABLE')
        self.compose('Receipt', '@' + safe_first('Receipt_readback'))
        self.set('Save_receipt_id', 'ReceiptId', "@outputs('Receipt')?['Id']")
        self.add('Parse_frozen_intent', d.parse("@outputs('Receipt')?['IntentJson']", {'type': 'object'}))
        self.gate('Intent_matches', same("body('Parse_frozen_intent')", "outputs('Typed_intent')"), 'INTENT_CONFLICT')
        self.add('Parse_sealed_attempts', d.parse("@if(empty(outputs('Receipt')?['SealedAttempts']),'[]',outputs('Receipt')?['SealedAttempts'])",
                  {'type': 'array', 'items': {'type': 'string'}, 'maxItems': 3}))

    def claim(self):
        self.gate('Receipt_available', both("not(equals(outputs('Receipt')?['Uncertain'],true))",
            "not(equals(outputs('Receipt')?['Complete'],true))",
            "or(empty(outputs('Receipt')?['AttemptToken']),and(equals(outputs('Receipt')?['Retryable'],true),contains(body('Parse_sealed_attempts'),outputs('Receipt')?['AttemptToken'])))",
            "less(length(body('Parse_sealed_attempts')),3)"), 'PROCESSING_OR_ASSISTANCE')
        self.http('Receipt_before_claim', ref(RECEIPTS, "variables('ReceiptId')"))
        self.gate('Receipt_revision_unchanged', same(field('Receipt_before_claim', '__metadata') + "?['etag']",
                                                    "outputs('Receipt')?['__metadata']?['etag']"), 'RECEIPT_RACE')
        self.merge('Claim_receipt', 'receipts', 'Receipt_before_claim',
                   {'AttemptToken': "@outputs('Attempt')", 'Retryable': False, 'Uncertain': False, 'Stage': 'Running'})
        self.http('Receipt_claim_readback', ref(RECEIPTS, "variables('ReceiptId')"))
        self.gate('Receipt_owned', same(field('Receipt_claim_readback', 'AttemptToken'), "outputs('Attempt')"), 'RECEIPT_RACE')
        self.set('We_claimed_receipt', 'Claimed', True)
        # A sealed attempt has no outstanding writes. If its release failed,
        # finalize only that exact token after winning the new receipt CAS.
        self.branch('Finalize_sealed_release',
                    "and(equals(triggerBody()?['text'],'Accept'),equals(outputs('Receipt')?['Retryable'],true))",
                    self.release_sealed)
        self.branch('Run_decision', "equals(triggerBody()?['text'],'Decline')", self.decline, self.accept)

    def release_sealed(self):
        self.collection('Sealed_source_group', 'groups', "concat('SourceRequestId eq ',string(triggerBody()?['number_1']))", 1)
        def release():
            self.set('Sealed_existing_group_id', 'GroupId', '@' + safe_first('Sealed_source_group') + "?['Id']")
            self.set('Sealed_existing_release_token', 'ReleaseToken',
                     "@concat(outputs('Operation_key'),':',outputs('Receipt')?['AttemptToken'])")
            self.release('Previous_sealed')
        self.branch('Sealed_source_exists', same('length(' + rows('Sealed_source_group') + ')', '1'), release)

    def record_effect(self, prefix):
        n = prefix + '_receipt_effect_revision'
        self.http(n, ref(RECEIPTS, "variables('ReceiptId')"))
        self.gate(prefix + '_effect_owner', same(field(n, 'AttemptToken'), "outputs('Attempt')"), 'RECEIPT_RACE')
        self.merge(prefix + '_record_domain_effect', 'receipts', n, {'DomainEffects': True, 'Stage': 'Decision'})

    def decision(self, accepted):
        name = 'Accept' if accepted else 'Decline'
        self.http(name + '_request_fresh', ref(self.base['requests'], "triggerBody()?['number_1']"))
        def pending():
            self.gate(name + '_pending_identity', both(self.request_identity(name + '_request_fresh'),
                "empty(" + field(name + '_request_fresh', 'WinningOperationKey') + ')',
                "not(equals(" + field(name + '_request_fresh', 'OperationComplete') + ',true))'), 'REQUEST_CONFLICT')
            value = {'Status': 'Accepted' if accepted else 'Declined', 'WinningOperationKey': "@outputs('Operation_key')",
                     'OperationComplete': not accepted}
            if not accepted:
                value['ConnectionKey'] = "@concat('history:',string(triggerBody()?['number_1']))"
            self.merge(name + '_pending_CAS', 'requests', name + '_request_fresh', value)
        self.branch(name + '_pending', same(field(name + '_request_fresh', 'Status'), "'Pending'"), pending)
        self.http(name + '_decision_readback', ref(self.base['requests'], "triggerBody()?['number_1']"), all_after=True)
        predicate = self.accepted(name + '_decision_readback') if accepted else both(
            self.request_identity(name + '_decision_readback'), same(field(name + '_decision_readback', 'Status'), "'Declined'"),
            same(field(name + '_decision_readback', 'WinningOperationKey'), "outputs('Operation_key')"),
            same(field(name + '_decision_readback', 'OperationComplete'), 'true'),
            same(field(name + '_decision_readback', 'ConnectionKey'), "concat('history:',string(triggerBody()?['number_1']))"))
        self.gate(name + '_won', predicate, 'DECISION_CONFLICT')

    def decline(self):
        self.record_effect('Decline')
        self.decision(False)
        self.set('Declined_result', 'Result', {'success': True, 'message': 'Declined', 'groupid': 0,
                    'resultcode': 'DECLINED', 'operationkey': "@outputs('Operation_key')"})
        self.finalize('Decline')

    def validation(self, prefix):
        for label, key in [('Sender', 'SenderParticipantId'), ('Recipient', 'RecipientParticipantId')]:
            self.http(prefix + '_' + label, ref(self.base['participants'], "outputs('Initial_request')?['" + key + "']"))
        for role in ['language', 'culture', 'timezone']:
            self.http(prefix + '_' + role, self.base[role] + '/items?$top=5001')
            self.gate(prefix + '_' + role + '_complete', d.complete(prefix + '_' + role, 5000), 'INCOMPLETE_CATALOGUE')
            self.add(prefix + '_Active_' + role, d.query('@' + rows(prefix + '_' + role), "equals(item()?['Active'],true)"))
            self.add(prefix + '_' + role + '_ids', d.select('@body(' + string(prefix + '_Active_' + role) + ')', "@item()?['Id']"))
        self.add(prefix + '_Any', d.query('@' + rows(prefix + '_language'), "equals(toLower(coalesce(item()?['ISOcode'],'')),'any')"))
        self.gate(prefix + '_Any_unique', 'lessOrEquals(length(body(' + string(prefix + '_Any') + ')),1)', 'CATALOGUE_INTEGRITY')
        profiles = []
        for label in ['Sender', 'Recipient']:
            n = prefix + '_' + label
            profiles.append({
                'profileId': '@' + field(n, 'Id'), 'accountKey': '@string(' + field(n, 'ParticipantaccountId') + ')',
                'status': '@' + field(n, 'Status'), 'participationStatus': '@' + field(n, 'ParticipationStatus'),
                'openToConnections': '@' + field(n, 'OpenToConnections'), 'timezoneId': '@' + field(n, 'TimezoneId'),
                **{k: '@' + field(n, actual) + "?['results']" for k, actual in [
                    ('teachIds', 'TeachlanguagesId'), ('learnIds', 'LearnlanguagesId'),
                    ('shareCultureIds', 'ShareCulturesId'), ('learnCultureIds', 'LearnCulturesId')]}})
            self.gate(n + '_identity', both('greater(coalesce(' + field(n, 'ParticipantaccountId') + ',0),0)',
                same(field(n, 'Id'), "outputs('Initial_request')?['" + ('SenderParticipantId' if label == 'Sender' else 'RecipientParticipantId') + "']"),
                same(field(n, 'ParticipantaccountId'), field('Read_invoker', 'Id')) if label == 'Recipient' else 'true'), 'PROFILE_IDENTITY')
        context = {
            'contractVersion': 1, 'rulesVersion': 1, 'profiles': profiles,
            'catalogues': {**{k: '@body(' + string(prefix + '_' + role + '_ids') + ')' for k, role in [
                ('languageIds', 'language'), ('cultureIds', 'culture'), ('timezoneIds', 'timezone')]},
                'anyLanguageId': "@first(union(body('" + prefix + "_Any'),createArray(json('{}'))))?['Id']"}}
        self.shared(prefix + '_Pair', {
            **deepcopy(context), 'mode': 'PAIR',
            'leftId': "@outputs('Initial_request')?['SenderParticipantId']",
            'rightId': "@outputs('Initial_request')?['RecipientParticipantId']"})
        self.gate(prefix + '_Pair_eligible', same("body('" + prefix + "_Pair_result')?['result']?['eligible']", 'true'), 'INELIGIBLE')
        self.shared(prefix + '_Group', {
            **deepcopy(context), 'mode': 'GROUP',
            'candidateId': "@outputs('Initial_request')?['RecipientParticipantId']",
            'group': {
                'groupId': 1, 'exchangeType': "@triggerBody()?['text_2']", 'state': 'Closed', 'setupComplete': False,
                'capacity': "@triggerBody()?['number_2']", 'focusSharersAvailable': False,
                'languageFocusIds': "@body('Language_focus')", 'cultureFocusIds': "@body('Culture_focus')",
                'memberProfileIds': "@createArray(outputs('Initial_request')?['SenderParticipantId'],outputs('Initial_request')?['RecipientParticipantId'])"}})
        # Initial creation is not an admission to a published group.
        # GROUP compatible is intentionally false; purpose/capacity cover both
        # proposed members. PAIR supplies explicit current availability for each.
        self.gate(prefix + '_Purpose_capacity', both(
            same("body('" + prefix + "_Group_result')?['result']?['purposeValid']", 'true'),
            same("body('" + prefix + "_Group_result')?['result']?['capacityValid']", 'true')), 'INVALID_GROUP_PURPOSE')

    def shared(self, name, payload):
        self.compose(name + '_payload', payload)
        self.add(name, {'type': 'Workflow', 'inputs': {'host': {'workflowReferenceName': CHILD},
                    'body': {'text': "@string(outputs('" + name + "_payload'))"}, 'retryPolicy': {'type': 'none'}}})
        self.gate(name + '_transport', both(same("body('" + name + "')?['success']", 'true'),
              same("body('" + name + "')?['resultcode']", "'OK'")), 'SHARED_VALIDATION_FAILED')
        self.add(name + '_result', d.parse("@body('" + name + "')?['resultjson']", {'type': 'object'}))
        self.gate(name + '_versions', both(same("body('" + name + "_result')?['contractVersion']", '1'),
                same("body('" + name + "_result')?['rulesVersion']", '1'),
                same("body('" + name + "_result')?['code']", "'OK'"),
                same("body('" + name + "_result')?['authorizesAction']", 'false')), 'SHARED_VERSION_MISMATCH')

    def group_matches(self, row, owned=True, complete_=False):
        pieces = [same(field(row, 'SourceRequestId'), "triggerBody()?['number_1']"),
                  same(field(row, 'Title'), "triggerBody()?['text_1']"),
                  same(field(row, 'ExchangeType'), "triggerBody()?['text_2']"),
                  same(field(row, 'Capacity'), "triggerBody()?['number_2']"),
                  same(field(row, 'SetupComplete'), 'true' if complete_ else 'false'),
                  same('length(' + field(row, 'LanguageFocusId') + "?['results'])", "length(body('Language_focus'))"),
                  same('length(intersection(' + field(row, 'LanguageFocusId') + "?['results'],body('Language_focus')))", "length(body('Language_focus'))"),
                  same('length(' + field(row, 'CultureFocusId') + "?['results'])", "length(body('Culture_focus'))"),
                  same('length(intersection(' + field(row, 'CultureFocusId') + "?['results'],body('Culture_focus')))", "length(body('Culture_focus'))")]
        if owned:
            pieces.append(same(field(row, 'WriteOwner'), "outputs('Owner_token')"))
        return both(*pieces)

    def ensure_group(self):
        self.collection('Find_group', 'groups', "concat('SourceRequestId eq ',string(triggerBody()?['number_1']))", 1)
        def create():
            self.post('Create_group', 'groups', {'Title': "@triggerBody()?['text_1']", 'SourceRequestId': "@triggerBody()?['number_1']",
                'ExchangeType': "@triggerBody()?['text_2']", 'Capacity': "@triggerBody()?['number_2']",
                'LanguageFocusId': {'results': "@body('Language_focus')"}, 'CultureFocusId': {'results': "@body('Culture_focus')"},
                'State': 'Closed', 'SetupComplete': False, 'WriteOwner': "@outputs('Owner_token')"})
        self.branch('Group_absent', same('length(' + rows('Find_group') + ')', '0'), create)
        self.collection('Group_by_source', 'groups', "concat('SourceRequestId eq ',string(triggerBody()?['number_1']))", 1, True)
        self.gate('One_source_group', same('length(' + rows('Group_by_source') + ')', '1'), 'GROUP_CREATE_UNCERTAIN')
        self.set('Save_group_id', 'GroupId', '@' + safe_first('Group_by_source') + "?['Id']")
        self.http('Group_for_claim', ref(self.base['groups'], "variables('GroupId')"))
        self.gate('Group_intent_matches', both(self.group_matches('Group_for_claim', False),
                    same(field('Group_for_claim', 'State'), "'Closed'"),
                    'or(empty(' + field('Group_for_claim', 'WriteOwner') + '),' +
                    same(field('Group_for_claim', 'WriteOwner'), "outputs('Owner_token')") + ')'), 'GROUP_CONFLICT')
        self.merge('Claim_group', 'groups', 'Group_for_claim', {'WriteOwner': "@outputs('Owner_token')"})
        self.http('Group_claimed', ref(self.base['groups'], "variables('GroupId')"))
        self.gate('Group_owned', self.group_matches('Group_claimed'), 'GROUP_BUSY')

    def ensure_member(self, label, party):
        key = "concat('request:',string(triggerBody()?['number_1']),':participant:',string(outputs('Initial_request')?['" + party + "']))"
        self.collection(label + '_find', 'members', "concat('MembershipKey eq '''," + key + ",'''')", 1)
        def create():
            self.http(label + '_guard', ref(self.base['groups'], "variables('GroupId')"))
            self.gate(label + '_owned', self.group_matches(label + '_guard'), 'GROUP_BUSY')
            self.post(label + '_create', 'members', {'GroupId': "@variables('GroupId')",
                    'ParticipantId': "@outputs('Initial_request')?['" + party + "']", 'MembershipKey': '@' + key,
                    'MembershipStatus': 'Active', 'JoinedAt': '@utcNow()'})
        self.branch(label + '_absent', same('length(' + rows(label + '_find') + ')', '0'), create)
        self.collection(label + '_readback', 'members', "concat('MembershipKey eq '''," + key + ",'''')", 1, True)
        # Only a definite rejection followed by complete absence read is a safe
        # stopped prefix. Timeouts/5xx/failed reads never enable takeover.
        def stopped():
            self.set(label + '_retry_boundary', 'RetryBoundary', True)
        status = "outputs('" + label + "_create')?['statusCode']"
        definite = 'contains(createArray(400,401,403,404,409,412,422),' + status + ')'
        self.branch(label + '_definite_stopped', both(same('length(' + rows(label + '_readback') + ')', '0'), definite), stopped)
        self.gate(label + '_exact', both(same('length(' + rows(label + '_readback') + ')', '1'),
            same(safe_first(label + '_readback') + "?['GroupId']", "variables('GroupId')"),
            same(safe_first(label + '_readback') + "?['ParticipantId']", "outputs('Initial_request')?['" + party + "']"),
            same(safe_first(label + '_readback') + "?['MembershipKey']", key),
            same(safe_first(label + '_readback') + "?['MembershipStatus']", "'Active'"),
            "not(empty(" + safe_first(label + '_readback') + "?['JoinedAt']))",
            'empty(' + safe_first(label + '_readback') + "?['LeftAt'])"), 'MEMBERSHIP_CONFLICT_OR_UNCERTAIN')

    def verify_members(self, prefix):
        self.collection(prefix + '_members', 'members', "concat('GroupId eq ',string(variables('GroupId')))", 2)
        self.add(prefix + '_matching_members', d.query('@' + rows(prefix + '_members'), both(
            same("item()?['MembershipStatus']", "'Active'"), "empty(item()?['LeftAt'])", "not(empty(item()?['JoinedAt']))",
            "contains(createArray(outputs('Initial_request')?['SenderParticipantId'],outputs('Initial_request')?['RecipientParticipantId']),item()?['ParticipantId'])",
            same("item()?['MembershipKey']", "concat('request:',string(triggerBody()?['number_1']),':participant:',string(item()?['ParticipantId']))"))))
        self.add(prefix + '_member_ids', d.select('@' + rows(prefix + '_members'), "@item()?['ParticipantId']"))
        self.gate(prefix + '_two_members', both(same('length(' + rows(prefix + '_members') + ')', '2'),
            same("length(body('" + prefix + "_matching_members'))", '2'),
            same("length(union(body('" + prefix + "_member_ids'),body('" + prefix + "_member_ids')))", '2')), 'MEMBERSHIP_READBACK')

    def accept_inputs(self):
        self.gate('Group_name', "and(not(empty(trim(triggerBody()?['text_1']))),lessOrEquals(length(triggerBody()?['text_1']),255))", 'INVALID_NAME')
        self.add('Capacity', d.parse("@triggerBody()?['number_2']", {'type': 'integer', 'minimum': 2, 'maximum': 10}))
        for n, source in [('Language_focus', 'text_3'), ('Culture_focus', 'text_4')]:
            self.add(n, d.parse("@triggerBody()?['" + source + "']", {'type': 'array', 'maxItems': 100,
                                            'items': {'type': 'integer', 'minimum': 1}}))
            self.gate(n + '_unique', same("length(body('" + n + "'))", "length(union(body('" + n + "'),body('" + n + "')))"), 'DUPLICATE_FOCUS')

    def accept(self):
        self.validation('Initial')
        self.record_effect('Accept')
        self.decision(True)
        self.ensure_group()
        self.ensure_member('Sender_member', 'SenderParticipantId')
        self.ensure_member('Recipient_member', 'RecipientParticipantId')
        self.verify_members('Before_commit')
        self.validation('Fresh')
        # Compare the versions used for evaluation, retaining parent freshness.
        for label in ['Sender', 'Recipient']:
            self.http('Last_' + label, ref(self.base['participants'], field('Fresh_' + label, 'Id')))
            self.gate('Last_' + label + '_unchanged', same(field('Last_' + label, '__metadata') + "?['etag']",
                       field('Fresh_' + label, '__metadata') + "?['etag']"), 'STALE_PROFILE')
        self.http('Request_before_publish', ref(self.base['requests'], "triggerBody()?['number_1']"))
        self.gate('Accepted_incomplete_owned', self.accepted('Request_before_publish'), 'REQUEST_COMMIT_CONFLICT')
        self.http('Group_before_publish', ref(self.base['groups'], "variables('GroupId')"))
        self.gate('Group_publish_owned', self.group_matches('Group_before_publish'), 'GROUP_COMMIT_CONFLICT')
        self.merge('Publish_group', 'groups', 'Group_before_publish', {'SetupComplete': True,
                    'State': "@if(greater(triggerBody()?['number_2'],2),'Open','Closed')"})
        self.http('Group_publish_readback', ref(self.base['groups'], "variables('GroupId')"))
        self.gate('Published_group_exact', both(self.group_matches('Group_publish_readback', True, True),
            same(field('Group_publish_readback', 'State'), "if(greater(triggerBody()?['number_2'],2),'Open','Closed')")), 'GROUP_PUBLISH_READBACK')
        self.merge('Complete_request', 'requests', 'Request_before_publish', {'OperationComplete': True,
                    'ConnectionKey': "@concat('history:',string(triggerBody()?['number_1']))"})
        self.http('Committed_request', ref(self.base['requests'], "triggerBody()?['number_1']"))
        self.gate('Committed_request_exact', both(self.accepted('Committed_request', True),
                same(field('Committed_request', 'ConnectionKey'), "concat('history:',string(triggerBody()?['number_1']))")), 'REQUEST_COMMIT_READBACK')
        self.verify_members('Committed')
        self.http('Committed_group', ref(self.base['groups'], "variables('GroupId')"))
        self.gate('Committed_group_exact', both(self.group_matches('Committed_group', True, True),
            same(field('Committed_group', 'State'), "if(greater(triggerBody()?['number_2'],2),'Open','Closed')")), 'GROUP_COMMIT_READBACK')
        self.set('Accepted_result', 'Result', {'success': True, 'message': 'Accepted', 'groupid': "@variables('GroupId')",
                    'resultcode': 'ACCEPTED', 'operationkey': "@outputs('Operation_key')"})
        self.finalize('Accept')

    def release(self, prefix):
        self.http(prefix + '_group', ref(self.base['groups'], "variables('GroupId')"))
        def owned():
            self.merge(prefix + '_release', 'groups', prefix + '_group', {'WriteOwner': ''})
        self.branch(prefix + '_has_our_token', same(field(prefix + '_group', 'WriteOwner'), "variables('ReleaseToken')"), owned)
        self.http(prefix + '_released_readback', ref(self.base['groups'], "variables('GroupId')"), all_after=True)
        self.gate(prefix + '_release_verified', 'not(equals(' + field(prefix + '_released_readback', 'WriteOwner') + ",variables('ReleaseToken')))", 'RELEASE_UNCERTAIN')

    def finalize(self, prefix):
        n = prefix + '_receipt_to_complete'
        self.http(n, ref(RECEIPTS, "variables('ReceiptId')"))
        self.gate(prefix + '_receipt_complete_owner', same(field(n, 'AttemptToken'), "outputs('Attempt')"), 'RECEIPT_RACE')
        self.merge(prefix + '_complete_receipt', 'receipts', n, {
            'ResultJson': "@string(variables('Result'))", 'Complete': True, 'Uncertain': False,
            'Retryable': False, 'Stage': 'Complete'})
        read = prefix + '_receipt_completed_readback'
        self.http(read, ref(RECEIPTS, "variables('ReceiptId')"))
        self.gate(prefix + '_receipt_completed_exact', both(same(field(read, 'Complete'), 'true'),
            same(field(read, 'IntentJson'), "string(outputs('Typed_intent'))"),
            same(field(read, 'ResultJson'), "string(variables('Result'))")), 'RECEIPT_COMMIT_READBACK')
        if prefix == 'Accept':
            self.set('Current_release_token', 'ReleaseToken', "@outputs('Owner_token')")
            self.release('Final')
        self.set(prefix + '_response_success', 'Success', True)

    def replay(self):
        self.add('Saved_result', d.parse("@outputs('Receipt')?['ResultJson']", {
            'type': 'object', 'required': ['success', 'message', 'groupid', 'resultcode', 'operationkey'],
            'properties': {'success': {'type': 'boolean'}, 'message': {'type': 'string'}, 'groupid': {'type': 'integer', 'minimum': 0},
                           'resultcode': {'type': 'string'}, 'operationkey': {'type': 'string'}}}))
        self.gate('Saved_result_valid', both(same("body('Saved_result')?['success']", 'true'),
               same("body('Saved_result')?['operationkey']", "outputs('Operation_key')")), 'RECEIPT_CORRUPT')
        self.set('Historical_result', 'Result', "@body('Saved_result')")
        self.set('Historical_group', 'GroupId', "@body('Saved_result')?['groupid']")
        def release():
            self.set('Saved_release_token', 'ReleaseToken', "@concat(outputs('Operation_key'),':',outputs('Receipt')?['AttemptToken'])")
            self.release('Replay')
        self.branch('Replay_release_only', "greater(variables('GroupId'),0)", release)
        self.set('Replay_success', 'Success', True)

    def catch(self):
        # Only the positively established member-create rejection boundary may
        # seal/release. A generic catch never guesses that a timeout had no effect.
        def own():
            self.http('Catch_receipt', ref(RECEIPTS, "variables('ReceiptId')"))
            def mark():
                def seal():
                    self.merge('Seal_attempt', 'receipts', 'Catch_receipt', {
                        'Retryable': True, 'Uncertain': False, 'Stage': 'Retryable',
                        'SealedAttempts': "@string(union(body('Parse_sealed_attempts'),createArray(outputs('Attempt'))))"})
                    def release():
                        self.set('Sealed_release_token', 'ReleaseToken', "@outputs('Owner_token')")
                        self.release('Sealed')
                    self.branch('Sealed_group_exists', "greater(variables('GroupId'),0)", release)
                def uncertain():
                    self.merge('Mark_uncertain', 'receipts', 'Catch_receipt', {
                        'Retryable': False, 'Uncertain': True, 'Stage': 'Uncertain'})
                self.branch('Known_stopped_prefix', "equals(variables('RetryBoundary'),true)", seal, uncertain)
            self.branch('Catch_current_incomplete', both(
                same(field('Catch_receipt', 'AttemptToken'), "outputs('Attempt')"),
                'not(equals(' + field('Catch_receipt', 'Complete') + ',true))'), mark)
        self.branch('Catch_owned_receipt', "and(equals(variables('Claimed'),true),equals(variables('Success'),false))", own)

    def build(self):
        for name, type_, value in [('Code', 'string', 'PROCESSING_OR_ASSISTANCE'), ('Result', 'object', {}),
                ('Success', 'boolean', False), ('ReceiptId', 'integer', 0), ('GroupId', 'integer', 0),
                ('Claimed', 'boolean', False), ('RetryBoundary', 'boolean', False), ('ReleaseToken', 'string', '')]:
            self.add('Initialize_' + name, {'type': 'InitializeVariable', 'inputs': {'variables': [{'name': name, 'type': type_, 'value': value}]}})
        def operation():
            self.authorize()
            self.receipt_setup()
            self.branch('Completed_receipt', "equals(outputs('Receipt')?['Complete'],true)", self.replay, self.claim)
        self.scope('Respond_operation', operation)
        self.scope('Record_stopped_outcome', self.catch, True)
        properties = {'success': 'boolean', 'message': 'string', 'groupid': 'number', 'resultcode': 'string', 'operationkey': 'string'}
        body = {
            'success': "@variables('Success')",
            'message': "@if(variables('Success'),variables('Result')?['message'],'Response not completed. Refresh My requests; retry with the same IntentId. An uncertain attempt may need assistance.')",
            'groupid': "@if(variables('Success'),variables('Result')?['groupid'],0)",
            'resultcode': "@if(variables('Success'),variables('Result')?['resultcode'],variables('Code'))",
            'operationkey': "@coalesce(outputs('Operation_key'),'')"}
        self.add('Respond_to_a_Power_App_or_flow', {'type': 'Response', 'kind': 'PowerApp', 'inputs': {
            'statusCode': 200, 'body': body, 'schema': {'type': 'object', 'properties': {
                k: {'title': k, 'type': v, 'x-ms-content-hint': {'boolean': 'BOOLEAN', 'number': 'NUMBER', 'string': 'TEXT'}[v],
                    'x-ms-dynamically-added': True} for k, v in properties.items()}}}}, True)
        measure(self.actions)
        return self.actions


def build(output, native_source):
    output = Path(output)
    if any(output.with_suffix(s).exists() for s in ['.zip', '.definition.json', '.review.json']):
        raise FileExistsError(output)
    seed = inspect_caller_export(native_source, SITE, SHARED_BUILD)
    if seed['receipt']['sharedChildId'] != CHILD:
        raise ValueError('Wrong production child')
    actions = Builder().build()
    doc = invoker_parent_document(seed, schema_input(), actions)
    doc['name'] = FLOW_ID
    doc['id'] = '/providers/Microsoft.Flow/flows/' + FLOW_ID
    doc['type'] = 'Microsoft.Flow/flows'
    doc['properties']['displayName'] = NAME
    doc['properties']['definition']['contentVersion'] = VERSION + '.0'
    solution_doc = deepcopy(doc)
    # Child-reference resolution under legacy import is a native gate.
    with TemporaryDirectory() as temp:
        base = Path(temp) / 'envelope.zip'
        legacy_envelope(base, sharepoint_site=SITE)
        with ZipFile(base) as archive:
            entries = {n: json.loads(archive.read(n)) for n in archive.namelist()}
    prefix = next(n.rsplit('/', 1)[0] for n in entries if n.endswith('/definition.json'))
    # The legacy container uses its observed legacy reference shape. Preserve
    # explicit Invoker and native Raw authentication, with no embedded fallback.
    legacy_ref = entries[prefix + '/definition.json']['properties']['connectionReferences']
    legacy_ref['shared_sharepointonline']['source'] = 'Invoker'
    doc['properties']['connectionReferences'] = legacy_ref
    entries[prefix + '/definition.json'] = doc
    manifest = entries['manifest.json']
    manifest['details'].update(displayName=NAME + ' ' + VERSION, description='Issue 11 native personal response. Existing Invoker SharePoint and shared validator. NOT imported/tested.')
    for resource in manifest['resources'].values():
        if resource['type'] == 'Microsoft.Flow/flows':
            resource['details']['displayName'] = NAME
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, 'x', ZIP_DEFLATED) as archive:
        for n, value in entries.items():
            archive.writestr(n, json.dumps(value, indent=2) + '\n')
    output.with_suffix('.definition.json').write_text(json.dumps(doc, indent=2) + '\n', encoding='utf-8', newline='\n')
    # Parent-only unmanaged Solution retains the actually observed connection
    # reference / Workflow envelope. Never bundle or update the shared child.
    solution_path = output.with_name(output.stem + '.solution.zip')
    if solution_path.exists():
        raise FileExistsError(solution_path)
    with ZipFile(native_source) as source:
        custom = ET.fromstring(source.read('customizations.xml'))
        solution = ET.fromstring(source.read('solution.xml'))
        types = source.read('[Content_Types].xml')
    workflows = custom.find('Workflows')
    template = deepcopy(next(n for n in workflows if n.attrib.get('Name') == 'Tandem81CallerProbe'))
    workflows.clear()
    template.attrib.update(WorkflowId='{' + FLOW_ID + '}', Name=NAME)
    workflow_path = 'Workflows/' + NAME + '-' + FLOW_ID.upper() + '.json'
    template.find('JsonFileName').text = '/' + workflow_path
    template.find('StateCode').text = '0'
    template.find('StatusCode').text = '1'
    for label in template.findall('./LocalizedNames/LocalizedName'):
        label.set('description', NAME)
    workflows.append(template)
    manifest_node = solution.find('SolutionManifest')
    manifest_node.find('UniqueName').text = 'TandemRespondRequest11'
    manifest_node.find('Version').text = '1.0.0.0'
    for label in manifest_node.findall('./LocalizedNames/LocalizedName'):
        label.set('description', NAME + ' ' + VERSION)
    for label in manifest_node.findall('./Descriptions/Description'):
        label.set('description', 'Issue 11 parent only; existing shared child required. Native integration NOT RUN.')
    components = manifest_node.find('RootComponents')
    components.clear()
    ET.SubElement(components, 'RootComponent', {'type': '29', 'id': '{' + FLOW_ID + '}', 'behavior': '0'})
    missing = manifest_node.find('MissingDependencies')
    if missing is not None:
        manifest_node.remove(missing)
    solution_doc = {'schemaVersion': '1.0.0.0', 'properties': {
        'connectionReferences': solution_doc['properties']['connectionReferences'],
        'definition': solution_doc['properties']['definition'], 'templateName': None}}
    with ZipFile(solution_path, 'x', ZIP_DEFLATED) as archive:
        archive.writestr('[Content_Types].xml', types)
        archive.writestr('customizations.xml', ET.tostring(custom, encoding='utf-8', xml_declaration=True))
        archive.writestr('solution.xml', ET.tostring(solution, encoding='utf-8', xml_declaration=True))
        archive.writestr(workflow_path, json.dumps(solution_doc, indent=2) + '\n')
    review = {'sourceTicket': 11, 'version': VERSION, 'packageBuildId': BUILD, 'flowId': FLOW_ID,
              **measure(actions), 'limits': {'actions': 500, 'maximumActionDepth': 8},
              'packageSha256': hashlib.sha256(output.read_bytes()).hexdigest(),
              'definitionSha256': hashlib.sha256(output.with_suffix('.definition.json').read_bytes()).hexdigest(),
              'generatorSha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'solutionSha256': hashlib.sha256(solution_path.read_bytes()).hexdigest(),
              'solutionScope': 'Parent only; shared child not bundled or changed; existing connection-reference component retained.',
              'triggerSource': 'config/participant_response_flow.snapshot.json; NOT certified export',
              'nativeEnvelope': seed['receipt'], 'sharedContractVersion': 1, 'sharedRulesVersion': 1,
              'nativeIntegration': 'NOT RUN', 'authorityProof': 'NOT RUN',
              'legacyChildReferenceImport': 'NOT RUN; stop if existing child cannot be resolved; no connector/runtime workaround'}
    output.with_suffix('.review.json').write_text(json.dumps(review, indent=2) + '\n', encoding='utf-8', newline='\n')
    return review


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native-source', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=ROOT / 'artifacts/respond_request/TandemRespondRequest-11.1.0.zip')
    args = parser.parse_args()
    print(json.dumps(build(args.output, args.native_source), indent=2))
