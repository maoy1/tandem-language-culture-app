"""Local source/IO regressions for #67; these do not certify native Power Fx."""
import json
from pathlib import Path
import re
import unittest

from scripts import app_requests_screen as app


def controls():
    def descend(children):
        for entry in children:
            for name, spec in entry.items():
                yield name, spec
                yield from descend(spec.get('Children', []))
    return dict(descend(app.screen()['Screens'][app.SCREEN_NAME]['Children']))


def tokens(formula):
    """Mask string literals, allowing doubled Power Fx quote escaping."""
    return re.sub(r'"(?:[^"]|"")*"', lambda m: ' ' * len(m[0]), formula)


def calls(formula):
    masked = tokens(formula)
    for match in re.finditer(r'(Tandem\w+)\.Run\(', masked):
        depth, commas, index = 1, 0, match.end()
        while depth:
            ch = masked[index]
            if ch == '(':
                depth += 1
            elif ch == ')':
                depth -= 1
            elif ch == ',' and depth == 1:
                commas += 1
            index += 1
        yield match[1], commas + 1


class RequestsSourceTests(unittest.TestCase):
    def test_generated_control_tree_and_formula_delimiters(self):
        items = controls()
        self.assertGreater(len(items), 30)
        self.assertTrue(all(name.startswith('req') for name in items))
        for name, spec in items.items():
            for prop, value in spec['Properties'].items():
                self.assertTrue(value.startswith('='), (name, prop))
                stack = []
                for ch in tokens(value):
                    if ch in '([{':
                        stack.append(ch)
                    elif ch in ')]}':
                        self.assertTrue(stack, (name, prop, value))
                        self.assertEqual(stack.pop(), {')': '(', ']': '[', '}': '{'}[ch], (name, prop))
                self.assertEqual(stack, [], (name, prop))

    def test_every_flow_call_and_response_property_matches_deployed_io(self):
        root = Path(__file__).resolve().parents[1]
        io = json.loads((root / 'artifacts/core_batch/v1.0.0.1/flow-io.json').read_text())
        formulas = '\n'.join(v for spec in controls().values() for v in spec['Properties'].values())
        for name, count in calls(formulas):
            trigger = next(iter(io[name]['trigger'].values()))
            self.assertEqual(count, len(trigger['inputs']['schema']['properties']), name)
        variables = {'varReqReadResponse': 'TandemMyRequests', 'varReqCancelResponse': 'TandemCancelRequest',
                     'varReqPersonalResponse': 'TandemRespondRequest', 'varReqGroupResponse': 'TandemRespondGroupJoinRequest'}
        for var, name in variables.items():
            output = next(iter(io[name]['responses'].values()))['properties']
            self.assertLessEqual(set(re.findall(var + r'\.(\w+)', formulas)), set(output), name)
        self.assertEqual(set(app.FLOW_NAMES), set(variables.values()))
        self.assertEqual(list(calls(app.PERSONAL_CALL)), [('TandemRespondRequest', 9)])
        self.assertIn('varReqIntentLanguages, varReqIntentCultures, varRequestsIntent', app.PERSONAL_CALL)

    def test_load_preserves_unresolved_intent_and_guards_direct_preview(self):
        self.assertFalse(app.LOAD.startswith('='))
        self.assertNotIn('Set(varRequestsIntent,', app.LOAD)
        self.assertNotIn('Set(varReqIntentActor,', app.LOAD)
        self.assertLess(app.LOAD.index('IsBlank(varAppActorId)'), app.LOAD.index('TandemMyRequests.Run'))
        self.assertIn('varAppActorId <= 0', app.LOAD)
        self.assertIn('Set(varReqDiagnostic, FirstError.Message)', app.LOAD)
        self.assertIn('Clear(reqRows)', app.LOAD)
        self.assertNotIn('OnVisible', app.screen()['Screens'][app.SCREEN_NAME]['Properties'])

    def test_uncertain_retries_use_only_captured_inputs(self):
        retry = controls()['reqRetry']['Properties']['OnSelect']
        self.assertEqual(retry, '=' + app.EXECUTE)
        self.assertNotIn('GUID()', retry)
        invocation = retry.split('If(varReqActionSuccess,', 1)[0]
        for mutable in ['reqName.Text', 'reqLanguages.SelectedItems', 'reqCultures.SelectedItems', 'varReqSelected.requestId']:
            self.assertNotIn(mutable, invocation)
        self.assertNotIn('Set(varReqIntentRequest,', retry)
        self.assertNotIn('Set(varReqIntentActor,', retry)
        self.assertIn('If(varReqActionSuccess,', app.EXECUTE)
        self.assertIn('!varReqCancelResponse.outcomeunknown', app.EXECUTE)
        self.assertIn('varReqCancelResponse.operationcomplete', app.EXECUTE)
        self.assertIn('varReqIntentActor <> varAppActorId', app.EXECUTE)

    def test_existing_catalogues_plain_text_and_navigation_slots(self):
        items = controls()
        self.assertEqual(items['reqLanguages']['Properties']['Items'], "=Choices([@Participants].'Teach languages')")
        self.assertEqual(items['reqCultures']['Properties']['Items'], "=Choices([@Participants].'Cultures I can share')")
        self.assertIn('Text(Value(reqFocus.Id), "0", "en-US")', app.CAPTURE)
        self.assertNotIn('JSON(ForAll', app.CAPTURE)
        self.assertEqual(items['reqDetails']['Properties']['Mode'], '=TextMode.MultiLine')
        self.assertEqual(items['reqDetails']['Properties']['DisplayMode'], '=DisplayMode.View')
        self.assertEqual(items['reqTitle']['Properties']['Width'], '=Parent.Width - 640')
        self.assertEqual(items['reqBack']['Properties']['X'], '=Parent.Width - 300')
        self.assertEqual(items['reqRefresh']['Properties']['X'], '=Parent.Width - 128')
        self.assertEqual(app.PENDING, '!IsBlank(varRequestsIntent)')
        self.assertTrue(app.BUSY and app.MODAL)


if __name__ == '__main__':
    unittest.main()
