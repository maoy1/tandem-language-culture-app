"""Read-only activation graph audit; Python is optional local tooling only.

Checks exact action dependencies and a separate case-folded projection. A cycle
in the latter is a name-collision hazard, NOT proof that the tenant resolves
action names without case. Report both so a native error is never invented.
Variable reads depend on initialization, not every later write (which would
invent cycles in normal mutable-variable workflows). No runtime certification.

python -B -m scripts.power_automate.activation_graph <definition.json-or-directory>
Exit 1 means findings, including conservative case-only naming hazards.
"""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import re


CALL = re.compile(r"([A-Za-z_][A-Za-z_0-9]*)\s*\(\s*'((?:[^']|'')*)'")
ACTION_FUNCTIONS = {'body', 'outputs', 'actions', 'result'}


def expression_calls(value):
    """Extract literal first arguments, ignoring WDL quoted string contents."""
    if isinstance(value, dict):
        for child in value.values():
            yield from expression_calls(child)
    elif isinstance(value, list):
        for child in value:
            yield from expression_calls(child)
    elif isinstance(value, str) and value.startswith('@') and not value.startswith('@@'):
        i = 0
        while i < len(value):
            if value[i] == "'":
                i += 1
                while i < len(value):
                    if value[i] == "'":
                        i += 1
                        if i < len(value) and value[i] == "'":
                            i += 1
                            continue
                        break
                    i += 1
                continue
            match = CALL.match(value, i)
            if match:
                yield match[1].lower(), match[2].replace("''", "'")
                i = match.end()
            else:
                i += 1


def walk(actions, parents=(), location='actions'):
    for name, action in actions.items():
        here = location + '/' + name
        yield name, action, parents, here
        children = parents + (name,)
        yield from walk(action.get('actions', {}), children, here + '/actions')
        yield from walk(action.get('else', {}).get('actions', {}), children, here + '/else/actions')
        for case, value in action.get('cases', {}).items():
            yield from walk(value.get('actions', {}), children, here + '/cases/' + case + '/actions')
        yield from walk(action.get('default', {}).get('actions', {}), children, here + '/default/actions')


def find_cycles(graph):
    """Return deterministic DFS witnesses; edges point to prerequisites."""
    active, done, stack, cycles = set(), set(), [], []

    def visit(node):
        if node in active:
            cycles.append(stack[stack.index(node):] + [node])
            return
        if node in done:
            return
        active.add(node)
        stack.append(node)
        for target in sorted(graph.get(node, ())):
            visit(target)
        stack.pop()
        active.remove(node)
        done.add(node)

    for node in sorted(graph):
        visit(node)
    return cycles


def analyze(document):
    definition = document.get('properties', {}).get('definition', document)
    rows = list(walk(definition['actions']))
    nodes = {name: (action, parents, location) for name, action, parents, location in rows}
    groups, initializers, graph = defaultdict(list), defaultdict(list), defaultdict(set)
    findings = []
    for name, action, parents, location in rows:
        groups[name.casefold()].append((name, location))
        if action['type'] == 'InitializeVariable':
            for variable in action['inputs']['variables']:
                initializers[variable['name']].append(name)
    for group in groups.values():
        if len(group) > 1:
            code = 'DUPLICATE_ACTION_NAME' if len({n for n, _ in group}) < len(group) else 'CASE_ONLY_ACTION_COLLISION'
            findings.append({'code': code, 'actions': [n for n, _ in group],
                             'paths': [p for _, p in group]})

    def edge(name, phase, target, target_phase='end'):
        graph[(name, phase)].add((target, target_phase))

    for name, action, parents, location in rows:
        edge(name, 'end', name, 'start')
        if parents:
            edge(name, 'start', parents[-1], 'start')
            edge(parents[-1], 'end', name)
        for target in action.get('runAfter', {}):
            if target not in nodes or nodes[target][2].rsplit('/', 1)[0] != location.rsplit('/', 1)[0]:
                findings.append({'code': 'INVALID_RUN_AFTER_SCOPE', 'action': name, 'target': target})
            edge(name, 'start', target)
        own = {k: v for k, v in action.items() if k not in ('actions', 'else', 'cases', 'default', 'runAfter')}
        if action['type']=='SetVariable':
            variable=action['inputs']['name']
            if any(function=='variables' and target.casefold()==variable.casefold()
                   for function,target in expression_calls(action['inputs']['value'])):
                findings.append({'code':'SELF_VARIABLE_UPDATE','action':name,'variable':variable})
        for function, target in expression_calls(own):
            if function in ACTION_FUNCTIONS:
                if target not in nodes:
                    findings.append({'code': 'MISSING_ACTION', 'action': name, 'target': target})
                edge(name, 'start', target)
            elif function in ('items', 'iterationindexes'):
                expected_type = 'Foreach' if function == 'items' else 'Until'
                if target not in parents or nodes[target][0]['type'].lower() != expected_type.lower():
                    findings.append({'code': 'INVALID_LOOP_REFERENCE', 'action': name, 'target': target})
            elif function == 'variables':
                if target not in initializers:
                    findings.append({'code': 'MISSING_VARIABLE', 'action': name, 'target': target})
                for initializer in initializers[target]:
                    edge(name, 'start', initializer)
    exact = find_cycles(graph)
    for cycle in exact:
        findings.append({'code': 'DEPENDENCY_CYCLE', 'cycle': [f'{n}:{p}' for n, p in cycle]})
    folded = defaultdict(set)
    for (name, phase), targets in graph.items():
        folded[(name.casefold(), phase)].update((n.casefold(), p) for n, p in targets)
    if not exact:
        for cycle in find_cycles(folded):
            findings.append({'code': 'CASE_FOLDED_DEPENDENCY_CYCLE',
                             'cycle': [f'{n}:{p}' for n, p in cycle],
                             'nativeConfirmed': False})
    return findings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path', type=Path)
    args = parser.parse_args()
    paths = sorted(args.path.glob('*.json')) if args.path.is_dir() else [args.path]
    if not paths:
        parser.error('No JSON definitions found')
    reports = [{'file': str(path), 'findings': analyze(json.loads(path.read_text(encoding='utf-8-sig')))}
               for path in paths]
    print(json.dumps(reports, indent=2))
    return int(any(report['findings'] for report in reports))


if __name__ == '__main__':
    raise SystemExit(main())
