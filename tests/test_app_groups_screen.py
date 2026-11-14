"""#68 source/contract regression gates; these do not compile or execute Power Fx."""
import json
from pathlib import Path
import re

from scripts import app_groups_screen as ui
from scripts.build_discovery_app import dump_yaml
from scripts.verify_discovery_app import formula_sanity
from scripts.power_automate.my_groups_flow import public_group_schema
from scripts.power_automate.update_group_flow import input_schema


ROOT = Path(__file__).resolve().parents[1]


def controls():
    found = {}

    def visit(items):
        for item in items:
            for name, node in item.items():
                assert name not in found, f'Duplicate control: {name}'
                found[name] = node
                visit(node.get('Children', []))

    visit(ui.screen()['Screens'][ui.SCREEN_NAME]['Children'])
    return found


def formulae():
    return [p for node in controls().values() for p in node['Properties'].values()]


def test_flow_calls_match_packaged_input_order_and_output_keys():
    io = json.loads((ROOT / 'artifacts/core_batch/v1.0.0.1/flow-io.json').read_text())
    source = '\n'.join(formulae())
    assert set(ui.FLOW_NAMES) == set(re.findall(r'(Tandem\w+)\.Run\(', source))
    expected = {
        'TandemMyGroups': [('number', 'number')],
        'TandemUpdateGroup': [('text', 'string')],
        'TandemLeaveGroup': [('number', 'number'), ('number_1', 'number'), ('number_2', 'number'), ('text', 'string')],
    }
    for flow, signature in expected.items():
        schema = io[flow]['trigger']['manual']['inputs']['schema']
        assert [(key, prop['type']) for key, prop in schema['properties'].items()] == signature
    for variable, flow in [('varGrpRead', 'TandemMyGroups'), ('varGrpUpdateResponse', 'TandemUpdateGroup'), ('varGrpLeaveResponse', 'TandemLeaveGroup')]:
        outputs = next(iter(io[flow]['responses'].values()))['properties']
        assert set(re.findall(rf'{variable}\.(\w+)', source)) <= outputs.keys()
    assert 'TandemLeaveGroup.Run(varGrpFrozen.actorId, varGrpFrozen.groupId, varGrpFrozen.membershipId, varGroupsIntent)' in ui.SEND


def test_read_projection_matches_approved_public_schema_without_private_display():
    schema = public_group_schema()['properties']
    read_fields = set(re.findall(r'grpRow\.Value\.(\w+)', ui.LOAD))
    member_fields = set(re.findall(r'grpMember\.Value\.(\w+)', ui.LOAD))
    assert read_fields <= schema.keys()
    assert member_fields <= schema['members']['items']['properties'].keys()
    assert {'groupId', 'membershipId', 'expectedETag', 'members'} <= read_fields
    assert {'displayName', 'comments', 'learningFocus', 'timeZone', 'teachLanguages', 'learnLanguages', 'shareCultures', 'learnCultures'} <= member_fields
    rendered = '\n'.join(p for node in controls().values() for key, p in node['Properties'].items() if key in ('Text', 'Default'))
    for private in ('membershipId', 'expectedETag', 'requestJson', 'FirstError', 'varGrpDiagnostic', 'ParticipantAccount', 'WriteOwner', 'email'):
        assert private not in rendered
    assert 'DisplayMode.View' in controls()['grpDetails']['Properties']['DisplayMode']
    assert 'TextMode.MultiLine' in controls()['grpDetails']['Properties']['Mode']


def test_update_payload_has_exact_server_allowlist_and_cas_snapshot():
    payload = ui.SAVE.split('requestJson: JSON({', 1)[1].split('JSONFormat.Compact', 1)[0]
    envelope, edits = payload.split('edits: {')
    assert set(re.findall(r'(\w+):', envelope)) | {'edits'} == set(input_schema()['properties'])
    assert set(re.findall(r'(\w+):', edits)) == set(input_schema()['properties']['edits']['properties'])
    assert 'expectedETag: varGrpEditing.expectedETag' in payload
    assert 'intentId: varGroupsIntent' in payload
    assert 'JSONFormat.Compact' in ui.SAVE
    assert 'grpList.Selected.state <> "Ended"' in controls()['grpEdit']['Properties']['DisplayMode']


def test_pending_intent_is_not_mutated_by_refresh_or_retry_failures():
    # Isolate the operation, excluding its successful authoritative refresh.
    operation = ui.SEND.replace(ui.LOAD, '')
    assert 'varAppActorId' not in operation
    assert 'grpList.Selected' not in operation
    assert '.Text' not in operation
    assert 'GUID()' not in operation
    assert 'Set(varGrpFrozen' not in operation
    assert 'Set(varGroupsIntent' not in ui.LOAD
    assert 'Set(varGrpFrozen' not in ui.LOAD
    assert operation.count('Set(varGroupsIntent, Blank())') == 1
    # A cleared UUID occurs only in the success arm, before its refresh; errors
    # retain the frozen record and offer an explicit same-operation retry.
    assert ui.SEND.index('If(varGrpSuccess = true,') < ui.SEND.index('Set(varGroupsIntent, Blank())') < ui.SEND.index(ui.LOAD)
    assert 'Set(varGroupsIntent' not in ui.SEND.split(ui.LOAD, 1)[1]
    # Refresh can select another group; success names the completed frozen intent.
    success_message = 'Set(varGrpOutcome, If(varGrpFrozen.kind = "Edit", "Changes saved for " & varGrpFrozen.name & ".", "Left " & varGrpFrozen.name & "."))'
    assert success_message in ui.SEND
    assert ui.SEND.index('If(varGrpSuccess = true,') < ui.SEND.index(success_message) < ui.SEND.index(ui.LOAD)
    assert controls()['grpRetry']['Properties']['OnSelect'] == '=' + ui.SEND
    assert ui.PENDING == '!IsBlank(varGroupsIntent)'
    assert ui.BUSY == 'varGrpBusy || varGrpSending'
    assert ui.MODAL == '!IsBlank(varGrpDialog)'


def test_direct_preview_guard_status_errors_and_personal_availability():
    assert ui.LOAD.index('If(IsBlank(varAppActorId) || varAppActorId <= 0,') < ui.LOAD.index('TandemMyGroups.Run(')
    assert 'Set(varGrpStatus, varGrpRead.groupstatus)' in ui.LOAD
    assert 'Set(varGrpStatus, "")' in ui.LOAD
    assert 'Set(varGrpLoaded, false)' in ui.LOAD
    assert 'Reset(grpList)' in ui.LOAD
    assert ui.LOAD.index('Set(varGrpStatus, varGrpRead.groupstatus)') < ui.LOAD.index('Set(varGrpLoaded, true)')
    assert 'varGrpLoaded' in controls()['grpEdit']['Properties']['DisplayMode']
    assert 'varGrpLoaded' in controls()['grpEmpty']['Properties']['Visible']
    assert 'Open your own saved registration' in ui.LOAD
    assert 'Set(varGrpDiagnostic, FirstError.Message)' in ui.LOAD
    assert 'Set(varGrpDiagnostic, FirstError.Message)' in ui.SEND
    source = '\n'.join(formulae())
    assert 'ParticipationStatus' not in source
    assert 'OpenToConnections' not in source
    assert 'Paused' not in source


def _response_guard(formula, response):
    """Evaluate only the small boolean response predicates, not Power Fx actions.

    Missing Boolean outputs map to None: explicit IsBlank guards must prevent a
    no-write exit for missing evidence. Real response fields are typed booleans.
    """
    expression = re.sub(r'varGrp\w+Response\.(\w+)', lambda m: repr(response.get(m[1])), formula)
    expression = re.sub(r'\bfalse\b', 'False', expression).replace('&&', ' and ')
    expression = expression.replace('!IsBlank(', 'not IsBlank(').replace(' = ', ' == ')
    return bool(eval(expression.replace('\n', ' '), {'__builtins__': {}, 'IsBlank': lambda value: value is None or value == ''}, {}))


def test_revise_is_bounded_to_explicit_no_domain_evidence():
    # #13's five codes originate before its domain edit. Receipt/release and
    # unknown outcomes have different codes; no generic non-success reset is safe.
    allowed = {'REVISION_CONFLICT', 'GROUP_BUSY', 'GROUP_ENDED_FINAL', 'CAPACITY_INVALID', 'CAPACITY_CHANGED_OR_INVALID'}
    for field in ('success', 'resultcode'):
        assert f'!IsBlank(varGrpUpdateResponse.{field})' in ui.UPDATE_CAN_REVISE
    for field in ('success', 'writeattempted', 'outcomeunknown'):
        assert f'!IsBlank(varGrpLeaveResponse.{field})' in ui.LEAVE_CAN_REVISE
        assert f'varGrpLeaveResponse.{field} = false' in ui.LEAVE_CAN_REVISE
    assert set(re.findall(r'"([A-Z_]+)"', ui.UPDATE_CAN_REVISE)) == allowed
    for code in allowed | {'UPDATED', 'REPLAY', 'OUTCOME_UNKNOWN', 'READ_OR_DATA_FAILED', 'RELEASE_FAILED', 'RECEIPT_FAILED', '', None}:
        for success in (True, False, None):
            assert _response_guard(ui.UPDATE_CAN_REVISE, {'success': success, 'resultcode': code}) == (success is False and code in allowed)
    # #14 supplies explicit write evidence: all three flags must be present and
    # false. Missing flags, ambiguous writes and success cannot permit replacement.
    for success in (True, False, None):
        for attempted in (True, False, None):
            for unknown in (True, False, None):
                response = {'success': success, 'writeattempted': attempted, 'outcomeunknown': unknown}
                assert _response_guard(ui.LEAVE_CAN_REVISE, response) == (success is False and attempted is False and unknown is False)
    for guard in (ui.UPDATE_CAN_REVISE, ui.LEAVE_CAN_REVISE):
        assert not _response_guard(guard, {})
    assert ui.SEND.index('Set(varGrpCanRevise, false)') < ui.SEND.index('TandemUpdateGroup.Run(')
    assert ui.SEND.index('TandemUpdateGroup.Run(') < ui.SEND.index('Set(varGrpCanRevise, ' + ui.UPDATE_CAN_REVISE)
    assert ui.SEND.index('TandemLeaveGroup.Run(') < ui.SEND.index('Set(varGrpCanRevise, ' + ui.LEAVE_CAN_REVISE)
    error_arm = ui.SEND.rsplit('Set(varGrpDiagnostic, FirstError.Message)', 1)[0]
    assert error_arm.rstrip().endswith('Set(varGrpCanRevise, false);')
    assert ui.REVISE.startswith('If(varGrpCanRevise = true && !IsBlank(varGroupsIntent) && !varGrpBusy && !varGrpSending,')
    assert ui.REVISE.index('Set(varGroupsIntent, Blank())') < ui.REVISE.index(ui.LOAD)
    assert 'Set(varGrpCanRevise, false)' in ui.REVISE
    assert 'Set(varGrpFrozen' not in ui.REVISE
    assert 'GUID()' not in ui.REVISE
    assert 'confirmed.' not in ui.REVISE
    assert controls()['grpRevise']['Properties']['OnSelect'] == '=' + ui.REVISE


def test_capacity_guidance_uses_approved_bounds_and_reader_snapshot_only():
    assert 'exchangeType: Text(grpRow.Value.exchangeType)' in ui.LOAD
    for bound in ('Value(grpCapacity.Text) >= 2', 'Value(grpCapacity.Text) <= 10',
                  'Value(grpCapacity.Text) >= varGrpEditing.memberCount',
                  'If(varGrpEditing.exchangeType = "Language", Value(grpCapacity.Text) <= 3, true)',
                  'Mod(Value(grpCapacity.Text), 1) = 0'):
        assert bound in ui._GUIDANCE
    assert ui._GUIDANCE in ui.SAVE
    assert ui._GUIDANCE in controls()['grpSave']['Properties']['DisplayMode']
    # These are snapshot guidance, never live authority or an alternate service
    # call: stale membership, focus and capacity are still checked by #13.
    assert '.Run(' not in ui._GUIDANCE
    assert 'varGrpEditing' not in ui.SEND.replace(ui.LOAD, '')
    assert controls()['grpEditGuidance']['Properties']['Text'] == '="Capacity cannot be below current membership. Refresh if someone else changes the group. Ending is final."'


def test_source_tree_is_namespaced_serializable_and_delimiters_balanced():
    assert dump_yaml(ui.screen()).startswith('Screens:\n  scrMyGroups:')
    assert all(name.startswith('grp') for name in controls())
    assert all(not raw.startswith('=') for raw in (ui.LOAD, ui.SEND, ui.SAVE, ui.LEAVE, ui.REVISE))
    assert controls()['grpHeading']['Properties']['Width'] == '=Parent.Width - 640'
    for formula in formulae():
        assert formula.startswith('=')
        assert '==' not in formula, 'Power Fx equality uses a single equals sign'
        formula_sanity(formula)
        # Ignore Power Fx double-quoted strings and escaped double quotes.
        stripped = re.sub(r'"(?:""|[^\"])*"', '', formula)
        stack = []
        for char in stripped:
            if char in '([{':
                stack.append(char)
            elif char in ')]}':
                assert stack and stack.pop() == {')': '(', ']': '[', '}': '{'}[char], formula
        assert not stack, formula
        assert all(v.startswith('varGrp') or v in ('varAppActorId', 'varGroupsIntent') for v in re.findall(r'\bvar\w+', formula))
