"""Prepare five Studio property pastes for #103; never repack the native app."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

import yaml

SOURCE_SHA = '673bff977448c4d31390c806681b96fc3d3bc056094d6e61b0e972868c8466ae'
OLD_GUARD = 'Form1.Unsaved || newMode || IsBlank(RecordsGallery1.Selected.ID)'
NEW_GUARD = 'Form1.Mode <> FormMode.View || IsBlank(RecordsGallery1.Selected.ID)'


def prepare(source, output):
    source, output = Path(source), Path(output)
    if hashlib.sha256(source.read_bytes()).hexdigest() != SOURCE_SHA:
        raise ValueError('Expected the accepted native-repaired app export')
    with ZipFile(source) as z:
        assert z.testzip() is None
        document = yaml.safe_load(z.read('Src/MainScreen1.pa.yaml'))
    controls = {}
    def visit(children):
        for row in children:
            name, node = next(iter(row.items()))
            controls[name] = node
            visit(node.get('Children', []))
    visit(document['Screens']['MainScreen1'].get('Children', []))
    props = lambda name: controls[name]['Properties']
    patches = {}
    for name in ['Discovery', 'MyRequest', 'MyGroups']:
        before = props(name)['OnSelect']
        assert before.count(OLD_GUARD) == 1, name
        after = before.replace(OLD_GUARD, NEW_GUARD, 1)
        assert after.replace(NEW_GUARD, OLD_GUARD, 1) == before
        patches[name + '.OnSelect'] = after
    success = props('Form1')['OnSuccess'].rstrip().rstrip(';')
    assert 'SubmitForm(' not in success and 'ViewForm(' not in success
    patches['Form1.OnSuccess'] = success + ';\nUpdateContext({ editMode: false, newMode: false });\nViewForm(Form1)'
    cancel = props('ResetFormButton1')['OnSelect'].rstrip().rstrip(';')
    assert 'ResetForm(Form1)' in cancel and 'editMode: false' in cancel and 'newMode: false' in cancel
    patches['ResetFormButton1.OnSelect'] = cancel + ';\nViewForm(Form1)'
    assert len(patches) == 5
    # No navigation body, save submission, validation, failure handler, actor /
    # intent guard, catalogue or identity property is replaced by this handoff.
    assert props('Form1')['OnFailure'] == '=Notify(Form1.Error, NotificationType.Error)'
    output.mkdir(parents=True, exist_ok=True)
    files = {}
    for name, formula in patches.items():
        path = output / (name + '.fx')
        data = (formula.removeprefix('=') + '\n').encode('utf8')
        path.write_bytes(data)
        files[path.name] = hashlib.sha256(data).hexdigest()
    report = {'issue': 103, 'version': 'registration-mode-fix-v1', 'sourceSha256': SOURCE_SHA,
              'method': 'five native Studio property pastes; no app repacking',
              'properties': list(patches), 'fileSha256': files,
              'localVerification': 'PASS: exact guard-only navigation delta; original success/cancel behavior retained before View transition; failure/submission/catalogue/identity properties untouched',
              'nativeAcceptance': 'NOT RUN', 'shared81Impact': 'UI form state/navigation only; no schema/shared rules/flow contracts or packages changed'}
    (output / 'verification.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf8')
    archive = output / 'TandemRegistrationModeFix-v1.zip'
    with ZipFile(archive, 'w', ZIP_DEFLATED) as z:
        for path in sorted(output.iterdir()):
            if path.is_file() and path.suffix in ['.fx', '.md', '.json']:
                z.write(path, path.name)
    with ZipFile(archive) as z:
        assert z.testzip() is None
        for name, sha in files.items():
            assert hashlib.sha256(z.read(name)).hexdigest() == sha
    return {'patchFiles': len(files), 'zipSha256': hashlib.sha256(archive.read_bytes()).hexdigest(), **report}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.source, args.output), indent=2))
