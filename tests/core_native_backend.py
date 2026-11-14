"""Local transport fixture for emitted flows, not an implementation of business rules.

Only SharePoint row reads, native-style unique keys/ETags and child transport are
modeled here. Domain decisions execute the generated Power Automate graphs.
"""
from copy import deepcopy
import json
import re
from urllib.parse import parse_qs, urlsplit
from uuid import uuid4

from scripts.power_automate import shared_validation as shared
from test_shared_validation import ChildRunner, NoIO

PEOPLE = json.loads((shared.ROOT / 'config/tenant_schema_mapping.json').read_text())
GROUPS = json.loads((shared.ROOT / 'config/group_schema_mapping.json').read_text())
ROLES = {**{k: v['listId'] for k, v in PEOPLE['lists'].items()},
         **{k: v['listId'] for k, v in GROUPS['lists'].items()},
         'requests': '3d17485d-1dac-41f0-a1af-24e45daa4567',
         'receipts': 'f0000000-0000-4000-8000-000000000081'}
TITLES = {'participants': 'Participants', 'language': 'Language catalogue', 'culture': 'Culture catalogue',
          'timezone': 'Time zone catalogue', 'groups': 'Groups', 'members': 'Group Members',
          'requests': 'Connection Requests', 'receipts': 'TandemOperationReceipts'}
TYPES = {'participants': 'SP.Data.ParticipantsListItem', 'groups': 'SP.Data.GroupsListItem',
         'members': 'SP.Data.Group_x0020_MembersListItem', 'requests': 'SP.Data.Connection_x0020_RequestsListItem',
         'receipts': 'SP.Data.TandemOperationReceiptsListItem'}


def property_value(row, key):
    if key in ['ID', 'Id']: return row.get('Id', row.get('ID'))
    return row.get(key)


def predicate(text, row):
    """Small OData comparison subset emitted by the repository's adapters."""
    if not text: return True
    tokens = re.findall(r"'(?:[^']|'')*'|\(|\)|-?\d+(?:\.\d+)?|[A-Za-z_][A-Za-z0-9_/]*", text)
    position = 0
    def take():
        nonlocal position
        value = tokens[position]; position += 1; return value
    def value(token):
        if token.startswith("'"): return token[1:-1].replace("''", "'")
        if token in ['true', 'false', 'null']: return {'true': True, 'false': False, 'null': None}[token]
        if re.fullmatch(r'-?\d+(\.\d+)?', token): return float(token) if '.' in token else int(token)
        return property_value(row, token)
    def compare():
        if tokens[position] == '(':
            take(); result = disjunction(); assert take() == ')'; return result
        left, op, right = value(take()), take(), value(take())
        if op == 'eq': return left == right
        if op == 'ne': return left != right
        if op == 'gt': return left is not None and right is not None and left > right
        if op == 'ge': return left is not None and right is not None and left >= right
        if op == 'lt': return left is not None and right is not None and left < right
        if op == 'le': return left is not None and right is not None and left <= right
        raise AssertionError('Unsupported native filter operator: ' + op)
    def conjunction():
        result = compare()
        while position < len(tokens) and tokens[position] == 'and':
            take(); other = compare(); result = result and other
        return result
    def disjunction():
        result = conjunction()
        while position < len(tokens) and tokens[position] == 'or':
            take(); other = conjunction(); result = result or other
        return result
    result = disjunction()
    assert position == len(tokens), ('Unconsumed native filter', text)
    return result


class Database:
    UNIQUE = {'requests': ['SendOperationKey', 'ConnectionKey'], 'groups': ['SourceRequestId'],
              'members': ['MembershipKey'], 'receipts': ['OperationKey']}
    def __init__(self):
        self.tables = {role: [] for role in TITLES}
        self.log = []
        self.fault = None
        self.before_write = None

    def insert(self, role, fields):
        defaults = {'requests': {'RecipientParticipantId': None, 'TargetGroupId': None,
                    'WinningOperationKey': None, 'OperationComplete': False, 'Introduction': None},
                    'groups': {'Purpose': None, 'WriteOwner': None, 'SetupComplete': False,
                               'LanguageFocusId': {'results': []}, 'CultureFocusId': {'results': []}},
                    'members': {'LeftAt': None},
                    'receipts': {'Complete': False, 'Uncertain': False, 'Retryable': False, 'DomainEffects': False,
                                 'ResultJson': None, 'AttemptToken': None, 'SealedAttempts': None, 'Stage': None}}
        row = {**deepcopy(defaults.get(role, {})), **deepcopy(fields),
               'Id': max([r['Id'] for r in self.tables[role]], default=0) + 1}
        row.setdefault('Created', '2026-11-14T12:00:00Z')
        row['__metadata'] = {'etag': '"1"', 'type': TYPES.get(role, 'SP.Data.CatalogueListItem')}
        self.tables[role].append(row)
        return row

    def collision(self, role, patch, old=None):
        return any(patch.get(key) is not None and any(r is not old and r.get(key) == patch[key]
                   for r in self.tables[role]) for key in self.UNIQUE.get(role, []))


class Connection:
    def __init__(self, database, actor=1, child_build='c79b7b64-b3ce-4de3-aa74-0ed62bca1524', child_actions=None,
                 child_id='e9aa88eb-a666-4df1-b088-176be7bcd00d'):
        self.db, self.actor, self.child_build = database, actor, child_build
        self.child_calls = []
        self.child_actions, self.child_id = child_actions, child_id

    @staticmethod
    def response(data, code=200): return {'statusCode': code, 'body': {'d': deepcopy(data)}}

    def request(self, params):
        if '_workflow' in params:
            call = params['_workflow']; self.child_calls.append(deepcopy(call))
            assert call['host']['workflowReferenceName'] == self.child_id, 'Wrong shared child target'
            child = ChildRunner(NoIO())
            baseline = json.loads((shared.ROOT / 'config/shared_validation_schema.json').read_text())
            child.run(self.child_actions or shared.definition_actions(baseline, self.child_build, 'local-rules'),
                      {'items': {}, 'triggerBody': call['body']})
            return {'statusCode': 200, 'body': child.response}
        uri = params.get('parameters/uri')
        if uri is None:
            role = next(k for k, id_ in ROLES.items() if id_ == params['table'].strip('{}').lower())
            rows = deepcopy(self.db.tables[role])
            def connector_row(original):
                row = deepcopy(original); row['ID'] = row['Id']
                if role == 'participants':
                    for name in ['Status', 'ParticipationStatus']:
                        if isinstance(row.get(name), str): row[name] = {'Value': row[name]}
                    for name in ['Teachlanguages', 'Learnlanguages', 'ShareCultures', 'LearnCultures']:
                        row[name + '#Id'] = row.get(name + 'Id', {}).get('results', [])
                    row['Timezone'] = None if row.get('TimezoneId') is None else {'Id': row['TimezoneId']}
                return row
            if 'id' in params:
                row = next((r for r in rows if r['Id'] == params['id']), None)
                if row is None: return self.response({}, 404)
                return {'statusCode': 200, 'body': connector_row(row)}
            rows = [row for row in rows if predicate(params.get('$filter', ''), row)]
            top = int(params.get('$top', 5000))
            return {'statusCode': 200, 'body': {'value': [connector_row(r) for r in rows[:top]],
                **({'@odata.nextLink': 'fixture-next-page'} if len(rows) > top else {})}}
        if '/currentuser' in uri.lower(): return self.response({'Id': self.actor * 101})
        query = {k: v[0] for k, v in parse_qs(urlsplit(uri).query).items()}
        def selected(value):
            if not value or '$select' not in query: return value
            keys = {part.split('/')[0] for part in query['$select'].split(',')} | {'__metadata'}
            return {key: value[key] for key in keys if key in value}
        role = next((k for k, id_ in ROLES.items() if id_ in uri.lower()), None)
        if role is None:
            found = re.search(r"getbytitle\('([^']+)'\)", uri, re.I)
            role = next((k for k, title in TITLES.items() if found and found[1] == title), None)
        assert role, ('Unknown SharePoint list', uri)
        match = re.search(r'/items\((\d+)\)', uri, re.I)
        row = next((r for r in self.db.tables[role] if match and r['Id'] == int(match[1])), None)
        method = params.get('parameters/method', 'GET')
        if method == 'GET':
            if '/items' not in uri:
                return self.response({'Id': ROLES.get(role, 'fixture-receipt-id'), 'Title': TITLES[role],
                                      'BaseTemplate': 100, 'ListItemEntityTypeFullName': TYPES.get(role, 'SP.Data.CatalogueListItem')})
            if match: return self.response(selected(row) or {}, 200 if row else 404)
            rows = [r for r in self.db.tables[role] if predicate(query.get('$filter', ''), r)]
            if '$orderby' in query:
                for term in reversed(query['$orderby'].split(',')):
                    parts = term.strip().split(); key = parts[0]
                    rows.sort(key=lambda r: property_value(r, key), reverse=len(parts) > 1 and parts[1] == 'desc')
            top = int(query.get('$top', 5000))
            return self.response({'results': [selected(r) for r in rows[:top]],
                                  **({'__next': 'fixture-next-page'} if len(rows) > top else {})})
        assert method in ['POST', 'PATCH', 'MERGE'], method
        patch = deepcopy(params['parameters/body'])
        if isinstance(patch, str): patch = json.loads(patch)
        if '__metadata' in patch: assert patch['__metadata']['type'] == TYPES.get(role, 'SP.Data.CatalogueListItem'), 'Wrong native item entity type'
        patch.pop('__metadata', None)
        if self.db.before_write:
            hook, self.db.before_write = self.db.before_write, None
            hook(role, patch)
        fault = self.db.fault(role, patch) if self.db.fault else None
        if fault == 'before': return self.response({'error': 'simulated unavailable'}, 503)
        if match:
            if row is None: return self.response({}, 404)
            headers = {k.lower(): v for k, v in params.get('parameters/headers', {}).items()}
            assert headers.get('if-match') != '*', 'Wildcard business write forbidden'
            if headers.get('if-match') != row['__metadata']['etag']: return self.response({}, 412)
            if self.db.collision(role, patch, row): return self.response({}, 502)
            row.update(patch)
            version = int(row['__metadata']['etag'].strip('"')) + 1
            row['__metadata']['etag'] = '"' + str(version) + '"'
        else:
            if self.db.collision(role, patch):
                return self.response({'error': {'innerError': {'errors': ['-2130575169', 'Microsoft.SharePoint.SPDuplicateValuesFoundException']}}}, 502)
            row = self.db.insert(role, patch)
        self.db.log.append({'role': role, 'id': row['Id'], 'patch': patch})
        if fault == 'after': return self.response({'error': 'simulated lost success response'}, 502)
        if match: return {'statusCode': 204, 'body': None}
        return self.response(row, 201)


class ParentRunner(ChildRunner):
    def extra_functions(self, context):
        def utc_now(format=None):
            assert format in [None, 'yyyy-MM-ddTHH:mm:ssZ'], 'Unsupported fixture date format'
            return '2026-11-14T12:00:00Z'
        return {'guid': lambda: str(uuid4()), 'utcNow': utc_now,
                'split': lambda value, separator: value.split(separator), 'join': lambda values, separator: separator.join(values),
                'startsWith': lambda value, prefix: value.startswith(prefix), 'endsWith': lambda value, suffix: value.endswith(suffix),
                'skip': lambda values, count: values[count:], 'take': lambda values, count: values[:count],
                'mul': lambda a, b: a * b,
                'string': lambda value: '' if value is None else json.dumps(value, separators=(',', ':')) if isinstance(value, (dict, list, bool)) else str(value)}

    def parse_content(self, value, schema):
        value = super().parse_content(value, schema)
        def bounded(item, spec):
            if isinstance(item, str):
                assert len(item) <= spec.get('maxLength', 10 ** 9), 'native maximum string length'
                if 'pattern' in spec: assert re.search(spec['pattern'], item), 'native string pattern'
            if isinstance(item, list):
                assert len(item) >= spec.get('minItems', 0)
                for entry in item: bounded(entry, spec.get('items', {}))
            if isinstance(item, dict):
                for key, child in spec.get('properties', {}).items():
                    if key in item: bounded(item[key], child)
        bounded(value, schema)
        return value

    def run(self, actions, ctx=None):
        actions = deepcopy(actions)
        for action in actions.values():
            if action['type'] == 'Workflow':
                action['type'] = 'OpenApiConnection'
                action['inputs'] = {'parameters': {'_workflow': action['inputs']}}
            elif action['type'] in ['IncrementVariable', 'DecrementVariable']:
                inputs = action['inputs']; amount = inputs.get('value', 1)
                operand = amount[1:] if isinstance(amount, str) and amount.startswith('@') else json.dumps(amount)
                op = 'add' if action['type'] == 'IncrementVariable' else 'sub'
                action['type'] = 'SetVariable'
                action['inputs'] = {'name': inputs['name'], 'value': '@' + op + "(variables('" + inputs['name'] + "')," + operand + ')'}
        return super().run(actions, ctx)


def seed():
    db = Database()
    for i, teach, learn in [(1, [1], [2]), (2, [2], [1]), (3, [], [1]), (4, [2], [])]:
        db.insert('participants', {'ParticipantaccountId': i * 101,
            'Participantaccount': {'Id': i * 101, 'Claims': 'trusted-' + str(i), 'DisplayName': 'Person ' + str(i),
                                   'Title': 'Person ' + str(i), 'Email': 'PRIVATE_EMAIL'},
            'Status': 'Active', 'ParticipationStatus': 'Active', 'OpenToConnections': True,
            'TeachlanguagesId': {'results': teach}, 'LearnlanguagesId': {'results': learn},
            'ShareCulturesId': {'results': []}, 'LearnCulturesId': {'results': []},
            'TimezoneId': None, 'Learningfocus': '', 'Comments': ''})
    for i, title, code in [(1, 'English', 'en'), (2, 'French', 'fr'), (99, 'Any language', 'any')]:
        db.insert('language', {'Id': i, 'Title': title, 'ISOcode': code, 'Active': True})['Id'] = i
    db.insert('culture', {'Title': 'Culture A', 'CultureKey': 'a', 'Active': True})
    db.insert('timezone', {'Title': 'London', 'IANA_ID': 'Europe/London', 'Active': True})
    return db
