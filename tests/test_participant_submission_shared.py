"""Execute shipped parent/child graphs with fake SharePoint; no tenant claim."""
from copy import deepcopy
import hashlib
import json
from zipfile import ZipFile

import pytest

from scripts.power_automate import participant_submission_shared as flow
from scripts.power_automate import participant_submission as legacy
from test_discovery_flow import FlowRunner, Terminated
from test_shared_validation import ChildRunner, NoIO

ARTIFACT = flow.ROOT/'artifacts/participant_submission/TandemParticipantSubmission-shared-v1.definition.json'
CHILD = json.loads((flow.ROOT/'artifacts/shared_validation/TandemSharedValidation81-v2.child.definition.json').read_text())
MAPPING = json.loads((flow.ROOT/'config/tenant_schema_mapping.json').read_text(encoding='utf-8'))


class SharePoint:
    def __init__(self):
        self.row = {'Id':38, 'ParticipantaccountId':16, 'TimezoneId':None, 'Status':'Needs review',
            '__metadata':{'etag':'"7"','type':'SP.Data.ParticipantsListItem'},
            **{k+'Id':{'results':[61] if k=='Teachlanguages' else []} for k in legacy.FIELDS},
            'ParticipationStatus':'Paused','OpenToConnections':False,'Comments':'preserve'}
        self.writes=[]
        self.requests=[]
        self.conflict=False
        self.fail_read=False
        self.paged=False
        self.readback_mismatch=False

    def request(self, p):
        self.requests.append(deepcopy(p))
        uri=p['parameters/uri']
        if p['parameters/method']=='POST':
            assert p['parameters/headers']['IF-MATCH']=='"7"'
            assert p['parameters/headers']['X-HTTP-Method']=='MERGE'
            assert set(p['parameters/body'])=={'__metadata','Status'}
            self.writes.append(deepcopy(p))
            if self.conflict:
                return {'statusCode':412,'body':{'error':'stale'}}
            self.row['Status']=p['parameters/body']['Status']
            self.row['__metadata']['etag']='"8"'
            return {'statusCode':204,'body':{}}
        assert p['parameters/method']=='GET'
        role=next((r for r in ['language','culture','timezone'] if MAPPING['lists'][r]['listId'] in uri),None)
        if role:
            rows=[{'Id':61,'Active':True},{'Id':99,'Active':False}] if role=='language' else [{'Id':5,'Active':True}] if role=='culture' else [{'Id':37,'Active':True}]
            d={'results':rows}
            if self.paged:d['__next']='next'
        else:
            if self.fail_read:return {'statusCode':500,'body':{}}
            d=deepcopy(self.row)
            if self.readback_mismatch and self.writes:d['Status']='wrong'
        return {'statusCode':200,'body':{'d':d}}


class ConsumerRunner(FlowRunner):
    """Resolve Workflow at its actual dependency point; retain all runAfter edges.

    Delegate the emitted Workflow boundary to ChildRunner, never to a rule oracle.
    The underlying FlowRunner has no Workflow handler, so a Compose executes the
    returned connector-free child body at precisely that graph node.
    """
    def __init__(self, server, mutate=None, child_failure=False):
        super().__init__(server)
        self.mutate=mutate
        self.child_failure=child_failure
        self.child_calls=0

    def inputs(self, value, ctx):
        if isinstance(value,dict) and value.get('__execute_child__'):
            self.child_calls+=1
            if self.child_failure:raise ValueError('child unavailable')
            payload=super().inputs(value['payload'],ctx)
            child=ChildRunner(NoIO())
            assert child.run(CHILD,{'items':{},'triggerBody':payload})
            result=deepcopy(child.response)
            if self.mutate:result=self.mutate(result)
            return result
        return super().inputs(value,ctx)

    def run(self, actions, ctx=None):
        adapted=deepcopy(actions)
        for action in adapted.values():
            if action['type']=='Workflow':
                assert action['inputs']['host']['workflowReferenceName']==flow.CHILD
                action['type']='Compose'
                action['inputs']={'__execute_child__':True,'payload':action['inputs']['body']}
        return super().run(adapted,ctx)


def run(server=None, **kwargs):
    runner=ConsumerRunner(server or SharePoint(),**kwargs)
    try:runner.run(json.loads(ARTIFACT.read_text(encoding='utf-8'))['properties']['definition']['actions'],
                   {'items':{},'triggerBody':{'ID':38,'Status':'stale event value','TeachlanguagesId':{'results':[999]}}})
    except Terminated:pass
    return runner


@pytest.mark.parametrize('variant,valid',[
    ('valid',True),('culture-only',True),('share-only',True),('null-zone',True),
    ('zone',True),('unknown-language',False),('inactive-language',False),
    ('unknown-culture',False),('unknown-zone',False),('empty',False),
    ('missing-account',False),('duplicates',True),('null-status',True)])
def test_actual_emitted_parent_and_child_content_and_preservation(variant,valid):
    server=SharePoint()
    if variant in ['culture-only','share-only','empty']:
        server.row['TeachlanguagesId']['results']=[]
    if variant=='culture-only':server.row['LearnCulturesId']['results']=[5]
    if variant=='share-only':server.row['ShareCulturesId']['results']=[5]
    if variant=='zone':server.row['TimezoneId']=37
    if variant=='unknown-language':server.row['TeachlanguagesId']['results']=[999]
    if variant=='inactive-language':server.row['TeachlanguagesId']['results']=[99]
    if variant=='unknown-culture':server.row['ShareCulturesId']['results']=[999]
    if variant=='unknown-zone':server.row['TimezoneId']=999
    if variant=='missing-account':server.row['ParticipantaccountId']=None
    if variant=='duplicates':server.row['TeachlanguagesId']['results']=[61,61]
    if variant=='null-status':server.row['Status']=None
    before=deepcopy(server.row)
    runner=run(server)
    assert runner.outputs['Validation_report']['valid'] is valid, runner.action_states
    assert server.row['Status']==('Active' if valid else 'Needs review')
    assert runner.child_calls==1
    assert {k:v for k,v in server.row.items() if k not in ['Status','__metadata']}=={k:v for k,v in before.items() if k not in ['Status','__metadata']}
    assert len(server.writes)==int(before['Status']!=server.row['Status'])
    assert runner.outputs['Validation_report']['sharedBuildId']=='c79b7b64-b3ce-4de3-aa74-0ed62bca1524'


@pytest.mark.parametrize('invalid',[False,True])
def test_one_correction_then_unchanged_no_trigger_write_loop(invalid):
    server=SharePoint()
    if invalid:
        server.row['TeachlanguagesId']['results']=[]
        server.row['Status']='Active'
    first=run(server)
    assert first.outputs['Validation_report']['result']=='STATUS_UPDATED'
    assert len(server.writes)==1
    for _ in range(3):
        followup=run(server)
        assert followup.outputs['Validation_report']['result']=='NO_CHANGE'
        assert followup.action_states['Status_changed']=='Succeeded'
        assert 'Update_validation_status' not in followup.outputs
    assert len(server.writes)==1


@pytest.mark.parametrize('failure',['read','paged','stale','readback','child'])
def test_failures_close_without_success_report(failure):
    server=SharePoint()
    server.fail_read=failure=='read'
    server.paged=failure=='paged'
    server.conflict=failure=='stale'
    server.readback_mismatch=failure=='readback'
    result=run(server,child_failure=failure=='child')
    assert result.outputs['Validation_report'] is None
    assert len(server.writes)==int(failure in ['stale','readback'])
    if failure=='stale':assert server.row['Status']=='Needs review'


def mutate_result(response, change):
    result=json.loads(response['resultjson'])
    if change=='version':result['rulesVersion']=2
    elif change=='authorization':result['authorizesAction']=True
    elif change=='io':result['writes']=1
    elif change=='missing-valid':result['result']={}
    elif change=='valid-type':result['result']['valid']='true'
    elif change=='error':
        result.update(code='INVALID_INPUT',success=False,result={})
        response.update(resultcode='INVALID_INPUT',success=False)
    elif change=='outer-code':response['resultcode']='INVALID_PROFILE_DATA'
    elif change=='outer-success':response['success']=False
    elif change=='malformed':return {**response,'resultjson':'bad-json'}
    response['resultjson']=json.dumps(result)
    return response


@pytest.mark.parametrize('change',['version','authorization','io','missing-valid','valid-type','error','outer-code','outer-success','malformed'])
def test_child_failure_or_untrusted_contract_never_becomes_status(change):
    server=SharePoint()
    runner=run(server,mutate=lambda r:mutate_result(r,change))
    assert runner.outputs['Validation_report'] is None
    assert not server.writes


def test_shipped_binding_and_graph_integrity():
    doc=json.loads(ARTIFACT.read_text(encoding='utf-8'))
    review=json.loads(ARTIFACT.with_name(ARTIFACT.name.replace('.definition.json','.review.json')).read_text())
    assert review['definitionSha256']==hashlib.sha256(ARTIFACT.read_bytes()).hexdigest()
    assert review['sharedChildSha256']==hashlib.sha256((flow.ROOT/'artifacts/shared_validation/TandemSharedValidation81-v2.child.definition.json').read_bytes()).hexdigest()
    assert review['sourceTriggerPreserved'] and review['sourceConnectionReferencesPreserved']
    assert doc['properties']['connectionReferences'][legacy.CONNECTOR]['source']=='Embedded'
    assert doc['properties']['connectionReferences'][legacy.CONNECTOR]['connectionName']=='b7e419509f0f4da89895a5ebd1f3a216'
    definition=doc['properties']['definition']
    assert legacy.gate(definition)=={'actionDefinitions':29,'maximumNesting':3}
    for _,a,_ in legacy.walk(definition['actions']):
        if a['type']=='OpenApiConnection':
            assert a['inputs']['authentication']=="@parameters('$authentication')"
            assert a['inputs']['host']['connectionName']==legacy.CONNECTOR
    text=json.dumps(definition)
    assert 'X-MS-APIM-Tokens' not in text and 'SCHEMA' not in text
    assert 'Selected_language' not in text and 'intersection(' not in text
    original=deepcopy(doc)
    original['properties']['definition']['actions']['Get_item']={'inputs':{'authentication':"@parameters('$authentication')"}}
    original['properties']['connectionReferences'][legacy.CONNECTOR]['source']='Invoker'
    with pytest.raises(ValueError,match='owner binding'):flow.build_document(original,MAPPING)


def legacy_seed():
    doc=json.loads(ARTIFACT.read_text(encoding='utf-8'))
    doc['properties']['definition']['actions']={'Get_item':{'inputs':{'authentication':"@parameters('$authentication')"}}}
    return doc


def test_builder_reproduces_shipped_parent_without_working_flow_identity():
    doc=flow.build_document(legacy_seed(),MAPPING)
    assert doc==json.loads(ARTIFACT.read_text(encoding='utf-8'))
    assert 'name' not in doc and 'id' not in doc
    assert 'metadata' not in doc['properties']['definition']


@pytest.mark.parametrize('change',['blank-connection','wrong-api','raw-auth','trigger-auth'])
def test_automated_owner_binding_rejects_unreviewed_conversion(change):
    doc=legacy_seed()
    if change=='blank-connection':doc['properties']['connectionReferences'][legacy.CONNECTOR]['connectionName']=''
    elif change=='wrong-api':doc['properties']['connectionReferences'][legacy.CONNECTOR]['id']='different'
    elif change=='raw-auth':doc['properties']['definition']['actions']['Get_item']['inputs']['authentication']={'type':'Raw','value':'manual-template'}
    else:next(iter(doc['properties']['definition']['triggers'].values()))['inputs']['authentication']='manual-template'
    with pytest.raises(ValueError):flow.build_document(doc,MAPPING)


@pytest.mark.parametrize('change',['wildcard-etag','missing-etag','wrong-item','malformed-selection'])
def test_operation_time_integrity_remains_in_parent(change):
    server=SharePoint()
    if change=='wildcard-etag':server.row['__metadata']['etag']='*'
    elif change=='missing-etag':del server.row['__metadata']['etag']
    elif change=='wrong-item':server.row['Id']=39
    else:server.row['TeachlanguagesId']['results']=['61']
    result=run(server)
    assert result.outputs['Validation_report'] is None
    assert not server.writes and result.child_calls==0


def test_automated_source_candidate_preserves_owner_auth_and_scopes_marker():
    doc=json.loads(ARTIFACT.with_name(ARTIFACT.name.replace('.definition.json','.solution-source.json')).read_text(encoding='utf-8'))
    legacy_doc=json.loads(ARTIFACT.read_text(encoding='utf-8'))
    assert doc['_connectionEvidence']=='AUTOMATED_SOURCE_VERIFIED'
    assert doc['properties']['definition']==legacy_doc['properties']['definition']
    assert doc['properties']['connectionReferences']=={legacy.CONNECTOR:{
        'runtimeSource':'embedded','connection':{'connectionReferenceLogicalName':flow.LOGICAL_REFERENCE},
        'api':{'name':legacy.CONNECTOR}}}
    review=json.loads(ARTIFACT.with_name(ARTIFACT.name.replace('.definition.json','.review.json')).read_text())
    assert review['nativeSolutionAutomaticBinding']=='NOT_RUN'
    assert 'legacy' in review['markerScope']
    assert review['solutionSourceSha256']==hashlib.sha256(ARTIFACT.with_name(review['solutionSource']).read_bytes()).hexdigest()


@pytest.mark.parametrize('change',[None,'invoker','bad-component','bad-hash','manual-trigger'])
def test_concrete_automated_adapter_resolves_component_without_manual_template(tmp_path,monkeypatch,change):
    from xml.etree import ElementTree as ET
    native=tmp_path/'native.zip'
    custom=ET.Element('ImportExportXml')
    refs=ET.SubElement(custom,'connectionreferences')
    ref=ET.SubElement(refs,'connectionreference',{'connectionreferencelogicalname':flow.LOGICAL_REFERENCE})
    ET.SubElement(ref,'connectorid').text='wrong' if change=='bad-component' else legacy.API
    with ZipFile(native,'w') as z:z.writestr('customizations.xml',ET.tostring(custom))
    receipt=tmp_path/'artifacts/shared_validation/results/native-sharepoint-solution.analysis.json'
    receipt.parent.mkdir(parents=True)
    receipt.write_text(json.dumps({'sourceExportSha256':'wrong' if change=='bad-hash' else hashlib.sha256(native.read_bytes()).hexdigest()}))
    monkeypatch.setattr(flow,'ROOT',tmp_path)
    seed=legacy_seed()
    if change=='invoker':seed['properties']['connectionReferences'][legacy.CONNECTOR]['source']='Invoker'
    if change=='manual-trigger':next(iter(seed['properties']['definition']['triggers'].values()))['type']='Request'
    if change:
        with pytest.raises(ValueError):flow.automated_solution_document(seed,MAPPING,native)
    else:
        result=flow.automated_solution_document(seed,MAPPING,native)
        assert result['_connectionEvidence']=='AUTOMATED_SOURCE_VERIFIED'
        assert result['properties']['connectionReferences'][legacy.CONNECTOR]['runtimeSource']=='embedded'
