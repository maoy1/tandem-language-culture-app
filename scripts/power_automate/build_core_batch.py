"""Build #81 from integrated artifacts; no import, activation or deployment.

Run in the combined checkout after all eleven delivered consumers are integrated:
python -m scripts.power_automate.build_core_batch --native-export <native.zip> \
    --output artifacts/core_batch/TandemCoreBatch-v1.zip
Reuse --build-id <UUID> with unchanged inputs for byte-identical ZIP contents.
"""
from copy import deepcopy
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
from uuid import UUID, uuid4
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from . import batch_schema, core_solution, shared_validation as shared
from .solution_source import inspect_caller_export

ROOT = Path(__file__).resolve().parents[2]
OUTPUT_NAME = 'TandemCoreBatch-v1.zip'
NATIVE_SHARED_BUILD = 'c79b7b64-b3ce-4de3-aa74-0ed62bca1524'
# Deliberately no globs, historical fallbacks, sibling-worktree reads or generated
# substitutes: the combined checkout must contain these exact delivered versions.
CONSUMER_ARTIFACTS = {
    'TandemDiscovery': 'artifacts/tandem_discovery/TandemDiscovery-shared.definition.json',
    'TandemParticipantSubmission': 'artifacts/participant_submission/TandemParticipantSubmission-shared-v1.solution-source.json',
    'TandemSendRequest': 'artifacts/send_request/TandemSendRequest-v4-shared.solution-parent.json',
    'TandemMyRequests': 'artifacts/my_requests/TandemMyRequests-v7-introduction-target.definition.json',
    'TandemCancelRequest': 'artifacts/cancel_request/TandemCancelRequest-v4.definition.json',
    'TandemRespondRequest': 'artifacts/respond_request/TandemRespondRequest-11.2.0.definition.json',
    'TandemSendGroupJoinRequest': 'artifacts/group_send/TandemSendGroupJoinRequest-v1.solution-parent.json',
    'TandemRespondGroupJoinRequest': 'artifacts/group_response/TandemRespondGroupJoinRequest.definition.json',
    'TandemMyGroups': 'artifacts/my_groups/TandemMyGroups-v2.definition.json',
    'TandemUpdateGroup': 'artifacts/update_group/TandemUpdateGroup-v1.parent.json',
    'TandemLeaveGroup': 'artifacts/leave_group/TandemLeaveGroup-v1.definition.json',
}
GENERATOR_INPUTS = (
    'scripts/power_automate/build_core_batch.py',
    'scripts/power_automate/core_solution.py',
    'scripts/power_automate/batch_schema.py',
    'scripts/power_automate/shared_validation.py',
    'scripts/power_automate/compatibility.py',
    'scripts/power_automate/solution_source.py',
    'scripts/power_automate/schema_audit.py',
    'scripts/power_automate/discovery_flow.py',
    'config/core_batch_contract.json',
    'config/batch_schema_contract.json',
    'config/shared_validation_schema.json',
    'config/tenant_schema_mapping.json',
    'config/group_schema_mapping.json',
    'artifacts/shared_validation/results/request-mapping.baseline.json',
    'tests/fixtures/compatibility_v1.json',
)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def git(checkout, *args):
    result = subprocess.run(['git', '-C', str(checkout), *args], capture_output=True,
                            text=True, encoding='utf-8', check=False)
    if result.returncode:
        raise ValueError('Cannot inspect combined checkout: ' + result.stderr.strip())
    return result.stdout.strip()


def literal_build_ids(value):
    found = set()
    if isinstance(value, dict):
        for key, child in value.items():
            if key == 'packageBuildId' and isinstance(child, str) and child and not child.startswith('@'):
                found.add(child)
            found.update(literal_build_ids(child))
    elif isinstance(value, list):
        for child in value:
            found.update(literal_build_ids(child))
    return found


def load_consumers(checkout):
    """Fail before creating output if deliveries are absent or not integrated."""
    checkout = Path(checkout)
    expected = set(core_solution.CONTRACT['productionFlows']) - {'TandemValidateContext'}
    if set(CONSUMER_ARTIFACTS) != expected:
        raise ValueError('Consumer registry differs from strict twelve-flow contract')
    missing = [f'{name}: {path}' for name, path in CONSUMER_ARTIFACTS.items()
               if not (checkout / path).is_file()]
    if missing:
        raise ValueError('Core batch incomplete; integrate exact delivered artifacts first:\n' + '\n'.join(missing))
    if git(checkout, 'ls-files', '--unmerged'):
        raise ValueError('Combined checkout has unresolved merges; finish integration before building')
    index = {}
    for line in git(checkout, 'ls-files', '--stage', '--', *CONSUMER_ARTIFACTS.values()).splitlines():
        header, path = line.split('\t', 1)
        _, blob, stage = header.split()
        if stage != '0':
            raise ValueError('Unmerged consumer artifact: ' + path)
        index[path] = blob
    untracked = [path for path in CONSUMER_ARTIFACTS.values() if path not in index]
    if untracked:
        raise ValueError('Consumer artifacts not integrated into Git index: ' + ', '.join(untracked))
    documents, sources = {}, {}
    for name, path in CONSUMER_ARTIFACTS.items():
        data = (checkout / path).read_bytes()
        try:
            doc = json.loads(data.decode('utf-8-sig'))
            definition = doc['properties']['definition']
            if not isinstance(definition['actions'], dict) or not isinstance(definition['triggers'], dict):
                raise ValueError('Expected actions and triggers objects')
            if len(definition['triggers']) != 1:
                raise ValueError('Expected one trigger')
        except (ValueError, KeyError, TypeError) as error:
            raise ValueError(f'Invalid delivered artifact {name}: {path}: {error}') from error
        documents[name] = doc
        sources[name] = {'artifact': path, 'sha256': digest(data), 'indexBlob': index[path],
                         'contentVersion': definition.get('contentVersion'),
                         'sourceBuildIds': sorted(literal_build_ids(definition))}
    return documents, {'sourceCommit': git(checkout, 'rev-parse', '--verify', 'HEAD'),
                       'consumerWorkingTree': git(checkout, 'status', '--porcelain=v1', '--', *CONSUMER_ARTIFACTS.values()).splitlines(),
                       'consumers': sources}


def canonical_zip(source, output):
    """Remove wall-clock ZIP metadata; preserve exact assembled entry bytes."""
    with ZipFile(source) as original, ZipFile(output, 'x', ZIP_DEFLATED, compresslevel=9) as archive:
        if original.testzip():
            raise ValueError('Assembler produced a corrupt archive')
        for name in sorted(original.namelist()):
            info = ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 0
            info.compress_type = ZIP_DEFLATED
            archive.writestr(info, original.read(name), compress_type=ZIP_DEFLATED, compresslevel=9)


def build(native_export, output, *, checkout=None, build_id=None, include_setup=True, include_smoke=True):
    checkout, output = Path(checkout or ROOT).resolve(), Path(output)
    if output.name != OUTPUT_NAME:
        raise ValueError('Use the stable output filename ' + OUTPUT_NAME)
    review_path = output.with_suffix('.review.json')
    if output.exists() or review_path.exists():
        raise FileExistsError('Refusing existing batch output or review: ' + str(output))
    batch_id = str(uuid4()) if build_id is None else str(UUID(str(build_id)))
    documents, provenance = load_consumers(checkout)
    baseline = batch_schema.baseline()
    shared.verify_baseline_sources(baseline)
    rules_hash = digest(Path(shared.rules.__file__).read_bytes())
    seed = inspect_caller_export(native_export, batch_schema.CONTRACT['site'], NATIVE_SHARED_BUILD)
    # Use native child trigger/envelope; never substitute the historical v2 graph
    # for the prospective baseline or forget the current compatibility source hash.
    child = deepcopy(seed['child'])
    child['properties']['definition']['actions'] = shared.definition_actions(baseline, batch_id, rules_hash)
    documents['TandemValidateContext'] = child
    provenance.update(generatorCommit=git(ROOT, 'rev-parse', '--verify', 'HEAD'),
        generatorInputs={path: digest((ROOT / path).read_bytes()) for path in GENERATOR_INPUTS},
        sharedBuildId=batch_id, contractVersion=shared.CONTRACT_VERSION, rulesVersion=shared.rules.VERSION,
        compatibilitySha256=rules_hash, baselineVersion=baseline['baselineVersion'],
        baselineSha256=digest(json.dumps(baseline, sort_keys=True, separators=(',', ':')).encode()),
        baselineRoleCount=len(baseline['roles']), baselineFieldCount=sum(len(s['fields']) for s in baseline['lists']))
    with TemporaryDirectory(prefix='tandem-core-build-') as directory:
        staged = Path(directory) / 'assembled.zip'
        review = core_solution.assemble(native_export, documents, staged,
                                        include_setup=include_setup, include_smoke=include_smoke)
        deterministic = Path(directory) / OUTPUT_NAME
        canonical_zip(staged, deterministic)
        review['sha256'] = digest(deterministic.read_bytes())
        review['buildProvenance'] = provenance
        # Verify files still match the bytes whose provenance was recorded. A
        # sibling can integrate changes concurrently; rebuild instead of mixing them.
        changed = [s['artifact'] for s in provenance['consumers'].values()
                   if digest((checkout / s['artifact']).read_bytes()) != s['sha256']]
        if changed or git(checkout, 'ls-files', '--unmerged'):
            raise ValueError('Consumer integration changed during assembly; retry: ' + ', '.join(changed))
        payloads = [(output, deterministic.read_bytes()),
                    (review_path, (json.dumps(review, indent=2, sort_keys=True) + '\n').encode())]
        output.parent.mkdir(parents=True, exist_ok=True)
        created = []
        try:
            for path, data in payloads:
                with path.open('xb') as stream:
                    created.append(path)
                    stream.write(data)
        except Exception:
            for path in created:
                path.unlink()
            raise
    return review


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native-export', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path, help='Destination named ' + OUTPUT_NAME)
    parser.add_argument('--checkout', type=Path, default=ROOT, help='Combined checkout; no sibling fallback')
    parser.add_argument('--build-id', help='Reuse an explicit UUID for reproducible builds')
    args = parser.parse_args(argv)
    try:
        review = build(args.native_export, args.output, checkout=args.checkout, build_id=args.build_id)
    except (ValueError, OSError) as error:
        parser.error(str(error))
    print(json.dumps({'output': str(args.output), 'sharedBuildId': review['sharedBuildId'],
                      'sha256': review['sha256'], 'productionFlowCount': review['productionFlowCount'],
                      'nativeResult': review['nativeResult']}, indent=2))


if __name__ == '__main__':
    main()
