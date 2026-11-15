"""#48 source preservation, identity and mapping failure boundaries."""
from copy import deepcopy
import json
from zipfile import ZipFile
from xml.etree import ElementTree as ET
import pytest
from scripts import prepare_participant_import as importer


def fixtures():
    book={'sourceSha256':'a'*64,'profileRowsSha256':'b'*64,'sheet':'Sheet1','headers':importer.EXPECTED,
          'externalLinks':False,'tables':[], 'rows':[{'excelRow':2,'values':{'A':'1','D':'person@example.org','P':'French','N':'Mainly language skills','U':'Private old comment'}}]}
    mapping=importer.mapping_template(book)
    mapping['learn']['French']={'reviewed':True,'languageIds':[7],'cultureIds':[]}
    mapping['availabilityPolicy']={'reviewed':True,'ParticipationStatus':'Paused','OpenToConnections':False}
    snapshot={'kind':'TandemParticipantImportSnapshot','collectionComplete':True,'targetSite':importer.SITE,
              'language':[{'Id':7,'Title':'French','Active':True}],'culture':[],
              'users':[{'Id':17,'LoginName':'i:0#.f|membership|person@example.org','Email':'person@example.org','Title':'Example Person'}], 'participants':[]}
    return book,mapping,snapshot


def test_exact_reviewed_plan_preserves_source_and_does_not_publish_comments():
    book,mapping,snapshot=fixtures();original=deepcopy(book)
    plan,report=importer.plan(book,mapping,snapshot)
    assert book==original
    assert plan['readyForApply'] is True and report['writes']==0
    row=plan['rows'][0]
    assert row['learnIds']==[7] and row['ParticipationStatus']=='Paused' and row['OpenToConnections'] is False
    assert 'Comments' not in row and 'TimezoneId' not in row and 'Status' not in row
    assert row['sharepointUserId']==17 and row['sourceKey']=='response:1'


@pytest.mark.parametrize('problem',['no_identity','multiple_users','unreviewed','inactive','bad_id','availability','no_selection'])
def test_blocks_ambiguous_or_unreviewed_data(problem):
    book,mapping,snapshot=fixtures()
    if problem=='no_identity':book['rows'][0]['values']['D']=''
    if problem=='multiple_users':snapshot['users'].append(deepcopy(snapshot['users'][0]))
    if problem=='unreviewed':mapping['learn']['French']['reviewed']=False
    if problem=='inactive':snapshot['language'][0]['Active']=False
    if problem=='bad_id':mapping['learn']['French']['languageIds']=[True]
    if problem=='availability':mapping['availabilityPolicy']['reviewed']=False
    if problem=='no_selection':book['rows'][0]['values'].pop('P')
    plan,report=importer.plan(book,mapping,snapshot)
    assert not plan['readyForApply'] and report['counts']['BLOCKED']==1 and report['writes']==0


def test_existing_accounts_preserved_without_overwrite_or_reconfirmation():
    book,mapping,snapshot=fixtures();snapshot['participants']=[{'Id':38,'ParticipantaccountId':17}]
    mapping['availabilityPolicy']['reviewed']=False
    plan,report=importer.plan(book,mapping,snapshot)
    assert plan['rows']==[] and report['counts']=={'EXISTING_PRESERVED':1}
    assert report['rows'][0]['participantId']==38


def test_same_account_in_two_responses_is_never_silently_last_wins():
    book,mapping,snapshot=fixtures();second=deepcopy(book['rows'][0]);second['excelRow']=3;second['values']['A']='2';book['rows'].append(second)
    plan,report=importer.plan(book,mapping,snapshot)
    assert not plan['readyForApply'] and plan['rows']==[]
    assert report['counts']=={'BLOCKED':2}
    assert all('DUPLICATE_SOURCE_ACCOUNT_RECONCILE' in r['errors'] for r in report['rows'])


def test_reconfirmation_needs_explicit_exclusion_with_reason():
    book,mapping,snapshot=fixtures();book['rows'][0]['values']={'A':'1','H':'Yes'}
    mapping['rows']['1'].update(exclude=True,reviewed=True,reason='Older full response will be handled separately')
    plan,report=importer.plan(book,mapping,snapshot)
    assert plan['rows']==[] and report['counts']=={'EXCLUDED_REVIEWED':1}


@pytest.mark.parametrize('key,value',[('collectionComplete',False),('targetSite','https://elsewhere.example'),('kind','unknown')])
def test_rejects_wrong_or_incomplete_snapshot(key,value):
    book,mapping,snapshot=fixtures();snapshot[key]=value
    with pytest.raises(ValueError):importer.plan(book,mapping,snapshot)


def test_mapping_bound_to_profile_rows_not_identity_redaction():
    book,mapping,snapshot=fixtures();book['profileRowsSha256']='changed'
    with pytest.raises(ValueError,match='Profile rows changed'):importer.plan(book,mapping,snapshot)


def test_outputs_never_overwrite_operator_edits(tmp_path):
    p=tmp_path/'mapping.json';importer.save(p,{'reviewed':True})
    with pytest.raises(FileExistsError):importer.save(p,{'reviewed':False})
    assert json.loads(p.read_text())=={'reviewed':True}


def workbook(path,formula=False):
    ns=importer.NS['s'];root=ET.Element('{'+ns+'}worksheet');data=ET.SubElement(root,'{'+ns+'}sheetData')
    for num,values in [(1,importer.EXPECTED),(2,{'A':'1','D':'p@example.org','P':'French'})]:
        row=ET.SubElement(data,'{'+ns+'}row',r=str(num))
        for col,text in values.items():
            c=ET.SubElement(row,'{'+ns+'}c',r=col+str(num),t='inlineStr');inline=ET.SubElement(c,'{'+ns+'}is');ET.SubElement(inline,'{'+ns+'}t').text=text
            if formula and num==2 and col=='P':ET.SubElement(c,'{'+ns+'}f').text='EXTERNAL()'
    with ZipFile(path,'w') as z:
        z.writestr('xl/workbook.xml',f'<workbook xmlns="{ns}" xmlns:r="{importer.REL}"><sheets><sheet name="Sheet1" sheetId="1" r:id="rId1"/></sheets></workbook>')
        z.writestr('xl/_rels/workbook.xml.rels','<Relationships><Relationship Id="rId1" Target="worksheets/sheet1.xml"/></Relationships>')
        z.writestr('xl/worksheets/sheet1.xml',ET.tostring(root))


def test_reads_inline_strings_without_modifying_source(tmp_path):
    p=tmp_path/'source.xlsx';workbook(p);original=p.read_bytes();book=importer.read_workbook(p)
    assert book['rows'][0]['values']['P']=='French' and p.read_bytes()==original


def test_rejects_formula_caches(tmp_path):
    p=tmp_path/'source.xlsx';workbook(p,True)
    with pytest.raises(ValueError,match='Formula cells'):importer.read_workbook(p)
