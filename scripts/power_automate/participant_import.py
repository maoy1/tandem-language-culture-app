"""#48 disposable owner-operated snapshot / reviewed CREATE-ONLY import.

Local packaging only: python -m scripts.power_automate.participant_import --output PATH.zip
No artifacts are generated on import. No workbook contents belong in the package.
Import as NEW, select the existing owner SharePoint connection, restrict run access
to the owner operator. Inspect Import_report / Snapshot_report in run history.
Native import, connections and action execution are NOT RUN, including snapshot.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZipFile

from .build_import_probe import build_package as build_probe
from .activation_schema import has_patterns
from .schema_audit import ALL, append, get, measure, wdl_string

ROOT = Path(__file__).resolve().parents[2]
NAME = 'TandemParticipantImportHelper'
BOUND = 5000
LOOKUPS = {'teachIds': 'TeachLanguages', 'learnIds': 'LearnLanguages',
           'shareCultureIds': 'ShareCultures', 'learnCultureIds': 'LearnCultures'}


def plan_schema(site):
    """Shared preparer envelope; all rows are parsed before any tenant write."""
    properties = {
        'sourceKey': {'type': 'string', 'minLength': 10, 'maxLength': 255},
        'accountLogin': {'type': 'string', 'minLength': 1, 'maxLength': 512},
        'sharepointUserId': {'type': 'integer', 'minimum': 1},
        'Title': {'type': 'string', 'maxLength': 255},
        **{key: {'type': 'array', 'maxItems': BOUND, 'uniqueItems': True,
                 'items': {'type': 'integer', 'minimum': 1}} for key in LOOKUPS},
        'ParticipationStatus': {'type': 'string', 'enum': ['Active', 'Paused', 'Inactive']},
        'OpenToConnections': {'type': 'boolean'},
        'Learningfocus': {'type': 'string'}, 'Comments': {'type': 'string'},
    }
    return {'type': 'object', 'additionalProperties': False,
            'required': ['kind', 'contractVersion', 'sourceTicket', 'sourceSha256',
                         'targetSite', 'readyForApply', 'rows'],
            'properties': {
                'kind': {'type': 'string', 'enum': ['TandemParticipantImportPlan']},
                'contractVersion': {'type': 'integer', 'enum': [1]},
                'sourceTicket': {'type': 'integer', 'enum': [48]},
                'sourceSha256': {'type': 'string', 'minLength': 64, 'maxLength': 64},
                'targetSite': {'type': 'string', 'enum': [site]},
                'readyForApply': {'type': 'boolean', 'enum': [True]},
                'rows': {'type': 'array', 'maxItems': 250, 'items': {
                    'type': 'object', 'additionalProperties': False,
                    'required': [k for k in properties if k not in ['Learningfocus', 'Comments']],
                    'properties': properties}}}}


def after(name, statuses=None):
    return {name: statuses or ['Succeeded']} if name else {}


def compose(value, previous=None, statuses=None):
    return {'type': 'Compose', 'inputs': value, 'runAfter': after(previous, statuses)}


def gate(expression, previous=None):
    # A failed assertion stops dependent stages but still allows the report action.
    return {'type': 'ParseJson', 'inputs': {'content': '@' + expression,
            'schema': {'type': 'boolean', 'enum': [True]}}, 'runAfter': after(previous)}


def condition(expression, yes, no=None, previous=None):
    return {'type': 'If', 'expression': '@' + expression, 'actions': yes,
            'else': {'actions': no or {}}, 'runAfter': after(previous)}


def scope(actions, previous=None):
    return {'type': 'Scope', 'actions': actions, 'runAfter': after(previous)}


def query(source, expression, previous=None, statuses=None):
    return {'type': 'Query', 'inputs': {'from': source, 'where': '@' + expression},
            'runAfter': after(previous, statuses)}


def complete(name, bound=BOUND):
    # Conservative: even an exactly-full page is refused. Never silently truncate.
    return (f"and(contains(coalesce(body('{name}'),json('{{}}')),'value'),"
            f"not(equals(body('{name}')?['value'],null)),"
            f"less(length(coalesce(body('{name}')?['value'],json('[]'))),{bound}),"
            f"empty(body('{name}')?['@odata.nextLink']),empty(body('{name}')?['odata.nextLink']),"
            f"empty(body('{name}')?['__next']))")


def page_complete(name, bound=BOUND):
    return complete(name, bound)


def validate_expressions(value):
    """Check quote/delimiter balance before emitting any package (not certification)."""
    if isinstance(value, dict):
        for child in value.values():
            validate_expressions(child)
    elif isinstance(value, list):
        for child in value:
            validate_expressions(child)
    elif isinstance(value, str) and value.startswith('@') and not value.startswith('@@'):
        stack, quoted, index = [], False, 1
        while index < len(value):
            char = value[index]
            if char == "'":
                if quoted and index + 1 < len(value) and value[index + 1] == "'":
                    index += 2
                    continue
                quoted = not quoted
            elif not quoted:
                if char in '([{':
                    stack.append(char)
                elif char in ')]}':
                    if not stack or stack.pop() != {')': '(', ']': '[', '}': '{'}[char]:
                        raise ValueError('Unbalanced expression: ' + value)
            index += 1
        if quoted or stack:
            raise ValueError('Unbalanced expression: ' + value)


def definition(site, mapping, build_id):
    lists = mapping['lists']
    people = lists['participants']
    fields = people['fields']
    field = lambda name: fields[name]['internalName']
    base = lambda role: "_api/web/lists(guid'" + lists[role]['listId'] + "')"
    account = field('ParticipantAccount') + 'Id'
    participant_uri = base('participants') + '/items?$select=Id,' + account
    actions = {}
    for name, value_type, initial in [('Rows', 'array', []), ('Preflight', 'array', []),
                                      ('Attempted', 'boolean', False)]:
        previous = next(reversed(actions), None)
        actions['Initialize_' + name] = {'type': 'InitializeVariable', 'inputs': {
            'variables': [{'name': name, 'type': value_type, 'value': initial}]},
            'runAfter': after(previous)}

    snapshot_reads = {}
    for role in ['language', 'culture', 'timezone', 'participants', 'users']:
        if role == 'users':
            uri = '_api/web/siteusers?$select=Id,LoginName,Email,Title&$top=5000'
        elif role == 'participants':
            uri = participant_uri + '&$top=5000'
        else:
            columns = ['Id', 'Title', lists[role]['fields']['Active']['internalName']]
            columns += {'language': ['ISOCode', 'Aliases'], 'culture': ['CultureKey'], 'timezone': ['IANAId']}[role]
            columns = [lists[role]['fields'].get(k, {}).get('internalName', k) for k in columns]
            uri = base(role) + '/items?$select=' + ','.join(columns) + '&$top=5000'
        snapshot_reads['Snapshot_' + role] = get(site, uri, next(reversed(snapshot_reads), None))
    snap = {
        'Snapshot_readonly_gate': gate("equals(coalesce(triggerBody()?['ApplyChanges'],false),false)"),
        'Snapshot_reads': scope(snapshot_reads, 'Snapshot_readonly_gate'),
    }
    snapshot_complete = "and(equals(actions('Snapshot_reads')?['status'],'Succeeded')," + ','.join(
        page_complete('Snapshot_' + role) for role in ['language', 'culture', 'timezone', 'participants', 'users']) + ')'
    snap['Snapshot_report'] = compose({
        'kind': 'TandemParticipantImportSnapshot', 'schemaVersion': 1, 'sourceTicket': 48,
        'targetSite': site, 'packageBuildId': build_id,
        'runReference': "@workflow()?['run']?['name']",
        'collectionComplete': '@' + snapshot_complete, 'complete': '@' + snapshot_complete,
        'writesCount': 0, 'ownerOperatorOnly': True,
        **{role: f"@coalesce(body('Snapshot_{role}')?['value'],json('[]'))"
           for role in ['language', 'culture', 'timezone', 'participants', 'users']},
    }, 'Snapshot_reads', ALL)

    pre = {'Parse_plan': {'type': 'ParseJson', 'inputs': {
        'content': "@json(triggerBody()?['PlanJson'])", 'schema': plan_schema(site)}, 'runAfter': {}}}
    pre['Hash_document'] = compose({'root': {'hash': "@body('Parse_plan')?['sourceSha256']"}}, 'Parse_plan')
    pre['Bad_source_keys'] = query("@body('Parse_plan')?['rows']",
        "not(and(startsWith(item()?['sourceKey'],'response:'),greater(length(item()?['sourceKey']),9)))", 'Hash_document')
    pre['Envelope_gate'] = gate(
        "and(empty(body('Bad_source_keys')),xpath(xml(outputs('Hash_document')),"
        "'boolean(string-length(/root/hash)=64 and translate(/root/hash,\"0123456789abcdefABCDEF\",\"\")=\"\")'))", 'Bad_source_keys')
    for key in ['sourceKey', 'sharepointUserId', 'accountLogin']:
        pre['Select_' + key] = {'type': 'Select', 'inputs': {
            'from': "@body('Parse_plan')?['rows']", 'select': f"@item()?['{key}']"},
            'runAfter': after(next(reversed(pre)))}
    pre['Unique_plan_gate'] = gate('and(' + ','.join(
        f"equals(length(body('Select_{key}')),length(union(body('Select_{key}'),body('Select_{key}'))))"
        for key in ['sourceKey', 'sharepointUserId', 'accountLogin']) + ')', next(reversed(pre)))
    pre['Read_account_field'] = get(site, base('participants') + "/fields(guid'" +
        fields['ParticipantAccount']['id'] + "')?$select=InternalName,TypeAsString,EnforceUniqueValues,ReadOnlyField",
        'Unique_plan_gate')
    pre['Read_participant_type'] = get(site, base('participants') + '?$select=ListItemEntityTypeFullName', 'Read_account_field')
    for role in ['language', 'culture']:
        name = 'Read_' + role
        pre[name] = get(site, base(role) + '/items?$select=Id,' +
                        lists[role]['fields']['Active']['internalName'] + '&$top=5000', next(reversed(pre)))
        selected = 'Active_' + role
        pre[selected] = query(f"@body('{name}')?['value']",
                              f"equals(item()?['{lists[role]['fields']['Active']['internalName']}'],true)", name)
        pre['Ids_' + role] = {'type': 'Select', 'inputs': {
            'from': f"@body('{selected}')", 'select': "@item()?['Id']"}, 'runAfter': after(selected)}
    pre['Tenant_gate'] = gate('and(' + ','.join([
        "equals(body('Read_account_field')?['EnforceUniqueValues'],true)",
        "equals(body('Read_account_field')?['TypeAsString'],'User')",
        "equals(body('Read_account_field')?['ReadOnlyField'],false)",
        f"equals(body('Read_account_field')?['InternalName'],'{field('ParticipantAccount')}')",
        "not(empty(body('Read_participant_type')?['ListItemEntityTypeFullName']))",
        page_complete('Read_language'), page_complete('Read_culture')]) + ')', next(reversed(pre)))

    def row_loop(prefix, variable, apply=False):
        loop = prefix + '_rows'
        row = f"items('{loop}')"
        def result(status, id_value=None, attempted=False):
            return {'sourceKey': '@' + row + "?['sourceKey']", 'sharepointUserId': '@' + row + "?['sharepointUserId']",
                    'status': status, 'participantId': id_value, 'writeAttempted': attempted}
        user, existing = prefix + '_user', prefix + '_existing'
        body = {user: get(site, "@concat('_api/web/siteusers/getbyid(',string(" + row + "?['sharepointUserId']),')?$select=Id,LoginName')")}
        body[existing] = get(site, "@concat(" + wdl_string(participant_uri + '&$filter=' + account + ' eq ') +
                             f",string({row}?['sharepointUserId']),'&$top=2')", user)
        guards = [f"equals(body('{user}')?['Id'],{row}?['sharepointUserId'])",
                  f"equals(body('{user}')?['LoginName'],{row}?['accountLogin'])",
                  f"not(empty(trim({row}?['Title'])))",
                  f"greater(add(add(length({row}?['teachIds']),length({row}?['learnIds'])),add(length({row}?['shareCultureIds']),length({row}?['learnCultureIds']))),0)",
                  page_complete(existing, 2)]
        for key in LOOKUPS:
            role = 'language' if key in ['teachIds', 'learnIds'] else 'culture'
            ids = ('Apply_ids_' if apply else 'Ids_') + role
            guards.append(f"equals(length(intersection({row}?['{key}'],body('{ids}'))),length({row}?['{key}']))")
        if apply:
            for role in ['language', 'culture']:
                read = 'Apply_catalogue_' + role
                active = 'Apply_active_' + role
                active_field = lists[role]['fields']['Active']['internalName']
                body[read] = get(site, base(role) + '/items?$select=Id,' + active_field + '&$top=5000', next(reversed(body)))
                body[active] = query(f"@body('{read}')?['value']", f"equals(item()?['{active_field}'],true)", read)
                body['Apply_ids_' + role] = {'type': 'Select', 'inputs': {
                    'from': f"@body('{active}')", 'select': "@item()?['Id']"}, 'runAfter': after(active)}
                guards.append(page_complete(read))
        body[prefix + '_row_gate'] = gate('and(' + ','.join(guards) + ')', next(reversed(body)))
        skipped = {prefix + '_skip': append(variable, result('SKIPPED_EXISTING', f"@first(body('{existing}')?['value'])?['Id']"))}
        new = {}
        if not apply:
            new[prefix + '_valid'] = append(variable, result('VALIDATED_NEW'))
        else:
            # Preserve omitted optional text. Never write validation Status: #61 owns it.
            payload = {'__metadata': {'type': "@body('Read_participant_type')?['ListItemEntityTypeFullName']"},
                       field('Title'): '@' + row + "?['Title']", account: '@' + row + "?['sharepointUserId']",
                       field('ParticipationStatus'): '@' + row + "?['ParticipationStatus']",
                       field('OpenToConnections'): '@' + row + "?['OpenToConnections']",
                       **{field(logical) + 'Id': {'results': '@' + row + f"?['{key}']"} for key, logical in LOOKUPS.items()}}
            new['Create_payload'] = compose(payload)
            previous = 'Create_payload'
            for key, logical in [('Learningfocus', 'LearningFocus'), ('Comments', 'Comments')]:
                name = 'Payload_' + key
                new[name] = compose(f"@if(contains({row},'{key}'),setProperty(outputs('{previous}'),'{field(logical)}',{row}?['{key}']),outputs('{previous}'))", previous)
                previous = name
            new['Mark_attempted'] = {'type': 'SetVariable', 'inputs': {'name': 'Attempted', 'value': True}, 'runAfter': after(previous)}
            post = get(site, base('participants') + '/items')
            post['inputs']['parameters'].update({'parameters/method': 'POST',
                'parameters/body': f"@outputs('{previous}')", 'parameters/headers': {
                    'Accept': 'application/json;odata=nometadata', 'Content-Type': 'application/json;odata=verbose'}})
            post['inputs']['retryPolicy'] = {'type': 'none'}
            new['Create_once'] = scope({'Create_participant': post}, 'Mark_attempted')
            new['Reread_account'] = get(site, body[existing]['inputs']['parameters']['parameters/uri'])
            new['Reread_account']['runAfter'] = after('Create_once', ALL)
            new['Reconcile_create'] = gate(page_complete('Reread_account', 2), 'Reread_account')
            success = ("and(equals(actions('Create_participant')?['status'],'Succeeded'),"
                       "equals(outputs('Create_participant')?['statusCode'],201),"
                       "equals(length(body('Reread_account')?['value']),1),"
                       "not(empty(body('Create_participant')?['Id'])),"
                       "equals(body('Create_participant')?['Id'],"
                       "first(body('Reread_account')?['value'])?['Id']))")
            # After ANY failed/ambiguous write, an observed row proves presence only.
            new['Record_create'] = append(variable, result('@if(' + success + ",'CREATED','UNKNOWN')",
                "@if(equals(length(body('Reread_account')?['value']),1),first(body('Reread_account')?['value'])?['Id'],null)", True), 'Reconcile_create')
        body[prefix + '_exists'] = condition(f"equals(length(body('{existing}')?['value']),1)", skipped, new, prefix + '_row_gate')
        loop_actions = {}
        if apply:
            loop_actions[prefix + '_reset'] = {'type': 'SetVariable', 'inputs': {'name': 'Attempted', 'value': False}, 'runAfter': {}}
        loop_actions[prefix + '_check'] = scope(body, next(reversed(loop_actions), None))
        failure = result("@if(variables('Attempted'),'UNKNOWN','REJECTED')" if apply else 'REJECTED',
                         attempted="@variables('Attempted')" if apply else False)
        failure['observedParticipants'] = f"@coalesce(body('{existing}')?['value'],json('[]'))"
        if apply:
            failure['observedAfterWrite'] = "@coalesce(body('Reread_account')?['value'],json('[]'))"
        # A handled failed POST may leave the containing scope Failed even after
        # Record_create appended UNKNOWN. Never append a second report for it.
        loop_actions[prefix + '_reported'] = query('@variables(\'' + variable + '\')',
            f"equals(item()?['sourceKey'],{row}?['sourceKey'])", prefix + '_check', ALL)
        loop_actions[prefix + '_fallback'] = condition(
            f"empty(body('{prefix}_reported'))", {prefix + '_failure': append(variable, failure)},
            previous=prefix + '_reported')
        return {'type': 'Foreach', 'foreach': "@body('Parse_plan')?['rows']", 'actions': loop_actions,
                'runtimeConfiguration': {'concurrency': {'repetitions': 1}}, 'runAfter': {}}

    imp = {'Plan_prerequisites': scope(pre)}
    imp['Preflight_rows'] = row_loop('Preflight', 'Preflight')
    imp['Preflight_rows']['runAfter'] = after('Plan_prerequisites')
    imp['Preflight_errors'] = query("@variables('Preflight')", "equals(item()?['status'],'REJECTED')", 'Preflight_rows', ALL)
    imp['Entire_plan_gate'] = gate("and(equals(actions('Plan_prerequisites')?['status'],'Succeeded'),"
        "equals(actions('Preflight_rows')?['status'],'Succeeded'),empty(body('Preflight_errors')),"
        "equals(length(variables('Preflight')),length(coalesce(body('Parse_plan')?['rows'],json('[]')))))", 'Preflight_errors')
    apply_rows = row_loop('Apply', 'Rows', True)
    imp['Apply_phase'] = condition("equals(coalesce(triggerBody()?['ApplyChanges'],false),true)", {'Apply_rows': apply_rows}, previous='Entire_plan_gate')
    imp['Final_rows'] = compose("@if(and(equals(coalesce(triggerBody()?['ApplyChanges'],false),true),equals(actions('Entire_plan_gate')?['status'],'Succeeded')),variables('Rows'),variables('Preflight'))", 'Apply_phase', ALL)
    for name, expr in [('Failed_rows', "contains(createArray('REJECTED','UNKNOWN'),item()?['status'])"),
                       ('Created_rows', "equals(item()?['status'],'CREATED')"),
                       ('Unknown_rows', "equals(item()?['status'],'UNKNOWN')"),
                       ('Attempted_rows', "equals(item()?['writeAttempted'],true)")]:
        imp[name] = query("@outputs('Final_rows')", expr, next(reversed(imp)))
    imp['Import_report'] = compose({
        'kind': 'TandemParticipantImportReport', 'contractVersion': 1, 'sourceTicket': 48,
        'targetSite': site, 'packageBuildId': build_id,
        'runReference': "@workflow()?['run']?['name']",
        'sourceSha256': "@body('Parse_plan')?['sourceSha256']",
        'applyChanges': "@coalesce(triggerBody()?['ApplyChanges'],false)",
        'preflightPassed': "@equals(actions('Entire_plan_gate')?['status'],'Succeeded')",
        'allPassed': "@and(equals(actions('Entire_plan_gate')?['status'],'Succeeded'),equals(actions('Apply_phase')?['status'],'Succeeded'),empty(body('Failed_rows')),equals(length(outputs('Final_rows')),length(coalesce(body('Parse_plan')?['rows'],json('[]')))))",
        'writesCount': "@length(body('Created_rows'))", 'unknown': "@not(empty(body('Unknown_rows')))",
        'unknownCount': "@length(body('Unknown_rows'))", 'writeAttempts': "@length(body('Attempted_rows'))",
        'rows': "@outputs('Final_rows')", 'preflightRows': "@variables('Preflight')",
        'prerequisiteStatus': "@actions('Plan_prerequisites')?['status']",
        'applyStatus': "@actions('Apply_phase')?['status']",
        'validationStatusOwner': '#61; no validation Status writes',
    }, 'Attempted_rows')
    actions['Mode'] = condition("empty(trim(coalesce(triggerBody()?['PlanJson'],'')))", snap, imp, 'Initialize_Attempted')
    return actions


def build_package(output, root=None):
    root = Path(root) if root else ROOT
    output = Path(output)
    paths = [output, output.with_suffix('.definition.json'), output.with_suffix('.review.json')]
    if any(path.exists() for path in paths):
        raise FileExistsError('Refusing to overwrite package or sidecars')
    mapping_path = root / 'config/tenant_schema_mapping.json'
    mapping = json.loads(mapping_path.read_text(encoding='utf-8'))
    site = json.loads((root / 'config/batch_schema_contract.json').read_text(encoding='utf-8'))['site']
    with TemporaryDirectory(prefix='tandem-participant-envelope-') as tmp:
        base = Path(tmp) / 'base.zip'
        document = build_probe(base, sharepoint_site=site)
        with ZipFile(base) as archive:
            entries = {name: json.loads(archive.read(name)) for name in archive.namelist()}
    document['properties']['displayName'] = NAME
    flow = document['properties']['definition']
    flow['triggers'] = {'manual': {'type': 'Request', 'kind': 'Button', 'inputs': {'schema': {
        'type': 'object', 'properties': {
            'PlanJson': {'type': 'string', 'title': 'PlanJson', 'default': '', 'x-ms-content-hint': 'TEXT'},
            'ApplyChanges': {'type': 'boolean', 'title': 'ApplyChanges', 'default': False, 'x-ms-content-hint': 'BOOLEAN'}},
        'required': []}}, 'runtimeConfiguration': {'concurrency': {'runs': 1}}}}
    flow['actions'] = definition(site, mapping, document['name'])
    if has_patterns(flow['actions']):
        raise ValueError('Native ParseJson pattern is unsupported; use explicit guards')
    validate_expressions(flow)
    metrics = measure(flow['actions'])
    for name in entries:
        if name.endswith('/definition.json'):
            entries[name] = document
    manifest = entries['manifest.json']
    manifest['details'].update(displayName=NAME + '-package', description=(
        '#48 disposable owner-only snapshot / reviewed CREATE-ONLY import; default read-only. '
        'Existing owner SharePoint connection. Native tests NOT RUN.'))
    next(value for value in manifest['resources'].values() if value['type'] == 'Microsoft.Flow/flows')['details']['displayName'] = NAME
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, 'x', ZIP_DEFLATED) as archive:
        for name, value in entries.items():
            archive.writestr(name, json.dumps(value, indent=2) + '\n')
    review = {'sourceTicket': 48, 'packageBuildId': document['name'],
        'sha256': hashlib.sha256(output.read_bytes()).hexdigest(), **metrics,
        'mappingSha256': hashlib.sha256(mapping_path.read_bytes()).hexdigest(),
        'targetSite': site, 'productionFlow': False, 'ownerOperatorOnly': True,
        'connection': 'Select existing owner SharePoint connection; Embedded; no other connectors',
        'inputs': {'PlanJson': 'blank => SNAPSHOT; otherwise reviewed plan_schema(targetSite)', 'ApplyChanges': 'Boolean default false; blank plan + true refused'},
        'outputs': 'Snapshot_report or Import_report Compose in owner run history; source keys and actual IDs',
        'planSchema': plan_schema(site), 'snapshotBound': BOUND, 'planBound': 250,
        'nativeImport': 'NOT RUN', 'nativeConnections': 'NOT RUN', 'nativeActions': 'NOT RUN', 'nativeSnapshot': 'NOT RUN',
        'limitations': ['No workbook mapping or identity guessing; parent owns preparer.',
            'Do not apply until source hash, intended test/live designation and reviewed policy are confirmed.',
            'Owner must verify existing connection/permissions and restrict flow run access before use.',
            'Snapshot includes private account information: owner preparation only, never participant UI.',
            'Full pages/nextlinks fail closed. Catalogue changes after reads are a race; no transaction/rollback.',
            'Unknown writes require manual reconciliation by unique account; never automatic retry.',
            'Imported validation Status remains owned by #61; discoverability is not certified.'],
        'driftReview81': 'No shared production schema/normalization/compatibility changes. Disposable helper consumes verified mapping; no child flow invocation or imported-flow changes.',
        'smokeInstructions': [
            'Owner: import ZIP as NEW; map Embedded reference to existing owner SharePoint connection. Verify owner-only access, permissions and existing #61 behavior first.',
            'Run blank PlanJson / ApplyChanges false. Snapshot_report must have collectionComplete=true and complete=true; preserve build/run reference. Overflow/read failure blocks preparation.',
            'Parent preparer: resolve unique actual users and exact catalogue IDs; supply sourceSha256, exact targetSite and readyForApply=true after review. No workbook is embedded.',
            'Run reviewed PlanJson / ApplyChanges false: expect allPassed=true, writesCount=0; every row VALIDATED_NEW or SKIPPED_EXISTING with ID.',
            'Negative fixtures: duplicate source/account, false readyForApply, wrong target, bad LoginName, inactive/unknown catalogue ID: allPassed=false and zero write attempts.',
            'Owner activates only the reviewed load. Run same plan / ApplyChanges true: CREATED requires 201 plus matching reread ID. Any ambiguous failure is UNKNOWN; preserve report/run outputs, reconcile before another apply.',
            'Repeat reviewed plan: all rows SKIPPED_EXISTING, writesCount=0; verify unchanged saved values. Run #61/app acceptance separately.',
            'Cleanup: disable/delete only this disposable helper after evidence capture. No automatic participant rollback; preserve original workbook and reports.'],
        'acceptance': 'NOT RUN; helper preparation does not certify #48 or release readiness'}
    paths[1].write_text(json.dumps(document, indent=2) + '\n', encoding='utf-8')
    paths[2].write_text(json.dumps(review, indent=2) + '\n', encoding='utf-8')
    return document, review


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    _, review = build_package(args.output)
    print(json.dumps(review, indent=2))


if __name__ == '__main__':
    main()
