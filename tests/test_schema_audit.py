"""Meaningful safety/analysis checks; not Power Automate or tenant execution."""
from copy import deepcopy
import json
from pathlib import Path
from uuid import UUID
from xml.etree.ElementTree import Element,SubElement,tostring
from zipfile import ZipFile

import pytest
from scripts.power_automate import schema_audit as audit

ROOT=Path(__file__).resolve().parents[1]


@pytest.fixture
def report():
    schema=audit.expected_schema(ROOT)
    ids={s['name']:str(UUID(int=i+1)) for i,s in enumerate(schema['lists'])}
    lists=[]
    for spec in schema['lists']:
        role=audit.ROLES[spec['name']];fields=[]
        for i,want in enumerate(spec['fields']):
            kind=want['type']+'Multi' if want.get('allowMultiple') else want['type']
            xml=Element('Field',{'Type':kind})
            if want.get('lookupList'):xml.attrib.update(List='{'+ids[want['lookupList']]+'}',ShowField=want['lookupField'])
            if want.get('choices'):
                choices=SubElement(xml,'CHOICES')
                for value in want['choices']:SubElement(choices,'CHOICE').text=value
            fields.append(dict(id=str(UUID(int=100+i)),internalName=want['internalName'],displayName=want.get('displayName',want['internalName']),
                type=kind,required=want.get('required',False),unique=want.get('unique',False),indexed=want['internalName'] in spec.get('indexes',[]),
                defaultValue=want.get('defaultValue'),schemaXml=tostring(xml,encoding='unicode') if want['type'] in ['Lookup','Choice'] else None))
        values=[] if role=='participants' else [dict(id=1,title='Fictional catalogue label',key=role+'-1',active=True)]
        lists.append(dict(role=role,id=ids[spec['name']],title=spec['name'],fields=fields,columnIndex=[],values=values,fieldsTruncated=False,valuesTruncated=False))
    return dict(kind=audit.FLOW_NAME,schemaVersion=1,packageBuildId='fixture',readOnly=True,sourceTicket=66,runReference='fixture-only',collectionComplete=True,lists=lists,errors=[])


def participant(report):return next(x for x in report['lists'] if x['role']=='participants')
def field(report,name):return next(f for f in participant(report)['fields'] if f['internalName']==name)


def test_matching_fixture_is_verified_without_claiming_writes(report):
    result=audit.analyze(report,ROOT)
    assert result['status']=='Verified' and result['findings']==[]
    assert result['changesApplied'] is False


def test_aliases_map_actual_internal_names_instead_of_renaming(report):
    f=field(report,'TeachLanguages');f['internalName']='Teachlanguages'
    culture=next(x for x in report['lists'] if x['role']=='culture')
    next(f for f in culture['fields'] if f['internalName']=='CultureKey')['internalName']='Culture_x0020_key'
    result=audit.analyze(report,ROOT)
    assert result['status']=='Verified'
    assert result['mapping']['participants']['fields']['TeachLanguages']['internalName']=='Teachlanguages'


def test_missing_availability_fields_produces_concrete_findings(report):
    participant(report)['fields']=[f for f in participant(report)['fields'] if f['internalName'] not in ['ParticipationStatus','OpenToConnections']]
    result=audit.analyze(report,ROOT)
    assert result['status']=='Needs change'
    assert {f['field'] for f in result['findings']}=={'ParticipationStatus','OpenToConnections'}


@pytest.mark.parametrize('property,code', [('required','FIELD_REQUIRED'),('unique','FIELD_UNIQUE'),('indexed','FIELD_INDEXED')])
def test_identity_requirements_are_checked(report,property,code):
    field(report,'ParticipantAccount')[property]=False
    assert any(f['code']==code for f in audit.analyze(report,ROOT)['findings'])


def test_optional_zone_and_lookup_multiplicity_are_checked(report):
    field(report,'TimeZone')['required']=True
    field(report,'TeachLanguages')['type']='Lookup'
    result=audit.analyze(report,ROOT)
    assert {f['code'] for f in result['findings']}=={'FIELD_REQUIRED','FIELD_TYPE'}


def test_lookup_target_and_display_field_are_checked(report):
    field(report,'TimeZone')['schemaXml']='<Field List="{00000000-0000-0000-0000-000000000001}" ShowField="Wrong" />'
    codes={f['code'] for f in audit.analyze(report,ROOT)['findings']}
    assert {'LOOKUP_TARGET','LOOKUP_DISPLAY'}<=codes


def test_choice_defaults_values_and_boolean_encoding(report):
    field(report,'OpenToConnections')['defaultValue']='1'
    assert audit.analyze(report,ROOT)['status']=='Verified'
    field(report,'ParticipationStatus')['defaultValue']='Paused'
    field(report,'ParticipationStatus')['schemaXml']='<Field><CHOICES><CHOICE>Active</CHOICE></CHOICES></Field>'
    assert {'FIELD_DEFAULT','FIELD_CHOICES'}<={f['code'] for f in audit.analyze(report,ROOT)['findings']}


@pytest.mark.parametrize('variant',['truncated','read_error','missing_role','ambiguous_field','reused_field','invalid_xml'])
def test_incomplete_or_ambiguous_reports_fail_closed(report,variant):
    if variant=='truncated':report['lists'][0]['valuesTruncated']=True
    if variant=='read_error':report['errors']=[{'role':'language','code':'METADATA_READ_FAILED'}]
    if variant=='missing_role':report['lists']=[x for x in report['lists'] if x['role']!='culture']
    if variant=='ambiguous_field':participant(report)['fields'].append(deepcopy(field(report,'TimeZone')))
    if variant=='reused_field':field(report,'OpenToConnections')['displayName']='Participation status'
    if variant=='invalid_xml':field(report,'TimeZone')['schemaXml']='not xml'
    assert audit.analyze(report,ROOT)['status']=='Blocked'


def test_catalogue_key_integrity_and_active_type(report):
    cat=next(x for x in report['lists'] if x['role']=='culture')
    cat['values'] += [dict(id=2,title='Other',key='CULTURE-1',active='Yes'),dict(id=3,title='Empty',key='',active=False)]
    codes={f['code'] for f in audit.analyze(report,ROOT)['findings']}
    assert {'CATALOGUE_KEY_DUPLICATE','CATALOGUE_KEY_EMPTY','CATALOGUE_ACTIVE'}<=codes


def test_response_action_envelope_and_report_string_are_supported(report):
    wrapped={'statusCode':'200','body':{'success':True,'reportjson':json.dumps(report)}}
    assert audit.analyze(wrapped,ROOT)['status']=='Verified'
    with pytest.raises(ValueError):audit.analyze({'body':{'success':True}},ROOT)


def test_generated_package_uses_existing_connection_and_only_gets(tmp_path):
    path=tmp_path/'audit.zip';doc,review=audit.build_package(path,'https://example.sharepoint.com/sites/Tandem',ROOT)
    assert review['actions']<=500 and review['maximumActionDepth']<=8
    with ZipFile(path) as z:
        assert z.testzip() is None
        manifest=json.loads(z.read('manifest.json'))
    flows=[v for v in manifest['resources'].values() if v['type']=='Microsoft.Flow/flows']
    assert len(flows)==1 and flows[0]['suggestedCreationType']=='New'
    connections=[v for v in manifest['resources'].values() if v['type']=='Microsoft.PowerApps/apis/connections']
    assert len(connections)==1 and connections[0]['creationType']=='Existing'
    assert doc['properties']['connectionReferences']['shared_sharepointonline']['source']=='Embedded'
    serialized=json.dumps(doc)
    assert 'parameters/method": "POST' not in serialized and 'PatchItem' not in serialized and 'DeleteItem' not in serialized
    assert '/items?$select=Id,Title,' in serialized and '&$top=5000' in serialized
    assert "getbytitle('Participants')/items" not in serialized
    assert 'CATALOGUE_TARGET_UNSAFE' in serialized and 'Read_participant_list' in serialized
    assert 'CATALOGUE_COLUMNS_UNRESOLVED' in serialized
    assert doc['properties']['definition']['triggers']['manual']['inputs']['schema']['properties']=={}


def test_user_field_xml_and_defaults_are_not_projected():
    projection=audit.field_projection()
    assert "createArray('Lookup','LookupMulti','Choice','MultiChoice')" in projection['schemaXml']
    assert "createArray('Boolean','Choice')" in projection['defaultValue']
    assert 'User' not in projection['schemaXml'] and 'User' not in projection['defaultValue']


def test_builder_refuses_existing_sidecar_and_zip(tmp_path):
    path=tmp_path/'audit.zip';path.with_suffix('.review.json').write_text('keep')
    with pytest.raises(FileExistsError):audit.build_package(path,'https://example.sharepoint.com',ROOT)
    assert not path.exists()


def test_limit_gate_rejects_oversized_or_deep_flows():
    with pytest.raises(ValueError,match='exceeds limit'):
        audit.measure({f'A{i}':{'type':'Compose','inputs':'x','runAfter':{}} for i in range(501)})
    block={'Leaf':{'type':'Compose','inputs':'x','runAfter':{}}}
    for i in range(8):block={f'Scope{i}':{'type':'Scope','actions':block,'runAfter':{}}}
    with pytest.raises(ValueError,match='exceeds limit'):audit.measure(block)


def test_reference_and_run_after_gate_rejects_invalid_templates():
    with pytest.raises(ValueError,match='Missing action'):
        audit.measure({'A':{'type':'Compose','inputs':"@body('Missing')",'runAfter':{}}})
    with pytest.raises(ValueError,match='Non-sibling'):
        audit.measure({'A':{'type':'Compose','inputs':'x','runAfter':{'Missing':['Succeeded']}}})


def test_sharepoint_computed_title_columns_do_not_hide_real_title(report):
    for cat in report['lists']:
        cat['fields'].extend(dict(internalName=name,displayName='Title',type='Computed',readOnly=True) for name in ['LinkTitle','LinkTitleNoMenu','LinkTitle2'])
    assert audit.analyze(report,ROOT)['status']=='Verified'


def test_existing_iana_display_and_legacy_status_values_are_preserved(report):
    cat=next(x for x in report['lists'] if x['role']=='timezone')
    next(f for f in cat['fields'] if f['internalName']=='IANAId')['internalName']='IANA_ID'
    cat['fields']=[f for f in cat['fields'] if f['internalName']!='WindowsId']
    field(report,'TimeZone')['schemaXml']=field(report,'TimeZone')['schemaXml'].replace('ShowField="Title"','ShowField="IANA_ID"')
    field(report,'Status')['schemaXml']='<Field><CHOICES><CHOICE>Draft</CHOICE><CHOICE>Active</CHOICE><CHOICE>Needs review</CHOICE></CHOICES></Field>'
    result=audit.analyze(report,ROOT)
    assert result['status']=='Verified'
    assert result['mapping']['participants']['fields']['TimeZone']['lookupDisplayField']=='IANA_ID'
