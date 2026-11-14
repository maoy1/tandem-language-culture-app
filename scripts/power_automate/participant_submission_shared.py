"""#61 PROFILE consumer draft; automated Solution binding remains a native gate.

Local build only. Never turn a legacy event owner's connection into Invoker.
"""
from copy import deepcopy
import argparse
import hashlib
import json
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

from . import participant_submission as legacy

ROOT = legacy.ROOT
CHILD = 'e9aa88eb-a666-4df1-b088-176be7bcd00d'
BUILD = 'issue-61-shared-consumer-v1'
LOGICAL_REFERENCE = 'cre46_sharepointonline_a22363a216'


def build_document(original, mapping, build_id=BUILD):
    refs = original['properties']['connectionReferences']
    ref = refs[legacy.CONNECTOR]
    if (set(refs) != {legacy.CONNECTOR} or ref.get('source') != 'Embedded'
            or not ref.get('connectionName') or ref.get('id') != legacy.API):
        raise ValueError('Expected inspected named automated owner binding')
    current = original['properties']['definition']['actions']['Get_item']['inputs']
    auth = current.get('authentication')
    trigger = next(iter(original['properties']['definition']['triggers'].values()))
    if auth != "@parameters('$authentication')" or trigger['inputs'].get('authentication') != auth:
        raise ValueError('Unreviewed automated authentication')
    definition = legacy.build_definition(original, mapping, build_id)
    a = definition['actions']
    for name in ['Selected_language', 'Selected_culture', 'Profile_valid', 'Desired_status']:
        del a[name]
    # Transport parsing and current-read integrity remain parent responsibilities.
    # Content/selection normalization belongs only to the deployed shared child.
    profile = {'profileId': "@body('Current_item')?['Id']",
        'accountKey': "@if(greater(coalesce(body('Current_item')?['ParticipantaccountId'],0),0),string(body('Current_item')?['ParticipantaccountId']),'')",
        'status': "@body('Current_item')?['Status']",
        'participationStatus': None, 'openToConnections': None,
        'timezoneId': "@body('Current_item')?['TimezoneId']"}
    for target, source in zip(['teachIds','learnIds','shareCultureIds','learnCultureIds'], legacy.FIELDS):
        profile[target] = "@body('Current_item')?['" + source + "Id']?['results']"
    a['Profile_request'] = legacy.compose({'contractVersion': 1, 'rulesVersion': 1,
        'mode': 'PROFILE', 'profiles': [profile], 'catalogues': {
            'languageIds': "@body('IDs_language')", 'cultureIds': "@body('IDs_culture')",
            'timezoneIds': "@body('IDs_timezone')", 'anyLanguageId': None}}, 'Require_complete_reads')
    a['Call_profile_child'] = {'type': 'Workflow', 'runAfter': legacy.after('Profile_request'),
        'inputs': {'host': {'workflowReferenceName': CHILD},
                   'body': {'text': "@string(outputs('Profile_request'))"}}}
    scalar = {'contractVersion': {'type':'integer'}, 'rulesVersion': {'type':'integer'},
        'success': {'type':'boolean'}, 'code': {'type':'string'}, 'kind': {'type':'string'},
        'sourceTicket': {'type':'integer'}, 'authorizesAction': {'type':'boolean'},
        'result': {'type':'object','properties': {'valid': {'type':'boolean'}}},
        'packageBuildId': {'type':'string','minLength':1}, 'runReference': {'type':'string','minLength':1},
        **{k: {'type':'integer'} for k in ['connectors','reads','writes']}}
    a['Profile_result'] = legacy.parse("@json(body('Call_profile_child')?['resultjson'])",
        {'type':'object','required':list(scalar),'properties':scalar}, 'Call_profile_child')
    r = "body('Profile_result')"
    checks = [f"equals({r}?['{k}'],{v})" for k,v in [
        ('contractVersion','1'),('rulesVersion','1'),('kind',"'TandemValidateContext'"),
        ('sourceTicket','81'),('authorizesAction','false'),('connectors','0'),('reads','0'),('writes','0')]]
    checks += [f"equals(body('Call_profile_child')?['resultcode'],{r}?['code'])",
               f"equals(body('Call_profile_child')?['success'],{r}?['success'])",
               f"or(and(equals({r}?['code'],'OK'),equals({r}?['success'],true),contains({r}?['result'],'valid')),and(equals({r}?['code'],'INVALID_PROFILE_DATA'),equals({r}?['success'],false),equals({r}?['result'],json('{{}}'))))"]
    a['Require_profile_result'] = legacy.condition('and('+','.join(checks)+')', {},
        {'Fail_profile_result': legacy.failed('SHARED_PROFILE_CONTRACT_FAILED')}, 'Profile_result')
    a['Profile_valid'] = legacy.compose(f"@and(equals({r}?['code'],'OK'),equals({r}?['result']?['valid'],true))", 'Require_profile_result')
    a['Desired_status'] = legacy.compose("@if(outputs('Profile_valid'),'Active','Needs review')", 'Profile_valid')
    a['Validation_report']['inputs'].update(sharedChildId=CHILD, contractVersion=1, rulesVersion=1,
        sharedCode="@body('Profile_result')?['code']", sharedBuildId="@body('Profile_result')?['packageBuildId']",
        sharedRunReference="@body('Profile_result')?['runReference']")
    for _, action, _ in legacy.walk(a):
        if action['type'] == 'OpenApiConnection':
            action['inputs']['authentication'] = deepcopy(auth)
    # A readable, non-deployable candidate must not carry the working flow's ID
    # or migration/creator metadata into an accidental replacement import.
    definition.pop('metadata', None)
    doc = {'properties': {'definition': definition,
        'connectionReferences': deepcopy(refs),
        'displayName': 'Tandem – Participant submission shared consumer DRAFT'}}
    legacy.gate(definition)
    return doc


def automated_solution_document(original, mapping, native_export, build_id=BUILD):
    """Adapt only the legacy automated owner source to a resolved component.

    AUTOMATED_SOURCE_VERIFIED means native *legacy* Embedded source inspected.
    It does NOT assert automatic Solution import/binding/execution proof. The
    caller must retain the accompanying review gate before any deployment.
    No manual Invoker document or Raw token template is used by this adapter.
    """
    receipt=json.loads((ROOT/'artifacts/shared_validation/results/native-sharepoint-solution.analysis.json').read_text())
    if hashlib.sha256(Path(native_export).read_bytes()).hexdigest()!=receipt['sourceExportSha256']:
        raise ValueError('Unreviewed native connection-component export')
    with ZipFile(native_export) as archive:
        custom=ET.fromstring(archive.read('customizations.xml'))
    components=[n for n in custom.findall('./connectionreferences/connectionreference')
        if n.attrib.get('connectionreferencelogicalname')==LOGICAL_REFERENCE]
    if len(components)!=1 or components[0].findtext('connectorid')!=legacy.API:
        raise ValueError('Unresolved automated SharePoint component')
    doc=build_document(original,mapping,build_id)
    trigger=next(iter(doc['properties']['definition']['triggers'].values()))
    if trigger.get('type')!='OpenApiConnection' or trigger['inputs']['host'].get('operationId')!='GetOnUpdatedItems':
        raise ValueError('Expected inspected automated SharePoint event')
    doc['properties']['connectionReferences']={legacy.CONNECTOR:{
        'runtimeSource':'embedded',
        'connection':{'connectionReferenceLogicalName':LOGICAL_REFERENCE},
        'api':{'name':legacy.CONNECTOR}}}
    doc['_connectionEvidence']='AUTOMATED_SOURCE_VERIFIED'
    return doc


def build(source, output, native_export=None):
    source, output = Path(source), Path(output)
    if output.exists():
        raise FileExistsError(output)
    original = legacy.source_definition(source)
    mapping = json.loads((ROOT/'config/tenant_schema_mapping.json').read_text(encoding='utf-8'))
    doc = build_document(original, mapping)
    output.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(doc, indent=2, ensure_ascii=False)+'\n').encode('utf-8')
    output.write_bytes(data)
    review = {'sourceTicket':61, 'packageBuildId':BUILD, 'sharedChildId':CHILD,
        'contractVersion':1, 'rulesVersion':1,
        'sourceExportSha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'definitionSha256':hashlib.sha256(data).hexdigest(),
        'sharedChildSha256':hashlib.sha256((ROOT/'artifacts/shared_validation/TandemSharedValidation81-v2.child.definition.json').read_bytes()).hexdigest(),
        'sourceTriggerPreserved':doc['properties']['definition']['triggers']==original['properties']['definition']['triggers'],
        'sourceConnectionReferencesPreserved':doc['properties']['connectionReferences']==original['properties']['connectionReferences'],
        'binding':'Preserved named legacy Embedded owner reference and $authentication; NOT a Solution automatic-binding proof',
        'nativeResult':'NOT_RUN', 'solutionAssembly':'BLOCKED_NATIVE_AUTOMATIC_OWNER_BINDING_NOT_PROVEN',
        'legacyZip':'NOT_EMITTED: Workflow child requires valid final Solution assembly first',
        **legacy.gate(doc['properties']['definition'])}
    if native_export:
        candidate=automated_solution_document(original,mapping,native_export)
        solution_path=output.with_name(output.name.replace('.definition.json','.solution-source.json'))
        if solution_path.exists():
            raise FileExistsError(solution_path)
        encoded=(json.dumps(candidate,indent=2,ensure_ascii=False)+'\n').encode('utf-8')
        solution_path.write_bytes(encoded)
        review.update(solutionSource=solution_path.name,
            solutionSourceSha256=hashlib.sha256(encoded).hexdigest(),
            solutionComponentExportSha256=hashlib.sha256(Path(native_export).read_bytes()).hexdigest(),
            solutionConnectionReferenceLogicalName=LOGICAL_REFERENCE,
            solutionRuntimeSource='embedded',
            connectionEvidenceMarker='AUTOMATED_SOURCE_VERIFIED',
            markerScope='Native legacy Embedded automated owner source verified ONLY; not native automatic Solution binding proof',
            legacyOwnerReference=deepcopy(original['properties']['connectionReferences'][legacy.CONNECTOR]),
            nativeLegacyOwnerBinding='PASS_EXPORT_INSPECTION; working v2 owner execution retained separately',
            nativeSolutionAutomaticBinding='NOT_RUN',
            deploymentGate='BLOCKED until existing owner connection resolves correctly in final Solution and automatic event smoke passes; no mode switch or new grant',
            solutionAssembly='SOURCE_ADAPTED_FOR_CORE_PACKAGER; final assembled parent NOT_RUN')
    output.with_name(output.name.replace('.definition.json','.review.json')).write_bytes((json.dumps(review,indent=2)+'\n').encode('utf-8'))
    return review


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--native-export',type=Path,help='Inspected native Solution component export; emits separate automated source candidate')
    args=parser.parse_args()
    print(json.dumps(build(args.source,args.output,args.native_export),indent=2))
