"""One-time Python importer: fictional identities and a fake SharePoint boundary."""
from copy import deepcopy
import csv
import json
from pathlib import Path
import re
from zipfile import ZipFile
import pytest
from scripts import import_participants_once as script
from test_prepare_participant_import import workbook as synthetic_workbook

MAP = script.configuration()


def raw(email='person@example.org', learn='French', share='English', **extra):
    return {'D':email,'E':'Example Name','P':learn,'R':share,'N':'Conversation',**extra}


def rows(*values):
    return [(i,i+1,value) for i,value in enumerate(values,1)]


def test_prepare_puts_email_in_person_column_and_maps_all_known_fields():
    record=script.prepare(rows(raw(Q='German',U='PRIVATE_NOTE',J='London')),MAP)[0]
    f=record['fields']
    assert f['Participantaccount']=='person@example.org'
    assert f['Title']=='Example Name' and f['Teachlanguages']=='English' and f['Learnlanguages']=='French; German'
    assert f['ParticipationStatus']=='Active' and f['OpenToConnections']=='Yes'
    assert f['Learningfocus']=='Conversation' and 'Comments' not in f and 'Timezone' not in f and 'Status' not in f
    assert not record['issues']


@pytest.mark.parametrize('identity',['Example Name (person@example.org)','person@example.org','Name, person@example.org','Name <person@example.org>'])
def test_email_extracted_automatically_from_mixed_identity_text(identity):
    assert script.prepare(rows(raw(email='anonymous',G=identity)),MAP)[0]['fields']['Participantaccount']=='person@example.org'


def test_conflicting_addresses_are_left_for_manual_correction():
    record=script.prepare(rows(raw(G='someoneelse@example.org')),MAP)[0]
    assert record['fields']['Participantaccount']=='' and 'MISSING_OR_AMBIGUOUS_EMAIL' in record['issues']


def test_partial_mapping_keeps_other_cells_and_reports_original_unmapped_value():
    record=script.prepare(rows(raw(learn='Unknown mixed choice',Q='French')),MAP)[0]
    assert record['fields']['Learnlanguages']=='French' and record['fields']['Teachlanguages']=='English'
    assert record['unmapped']==[{'column':'P','value':'Unknown mixed choice'}]
    assert 'UNMAPPED_SELECTION_P' in record['issues']


def test_culture_only_and_empty_profile_are_kept_in_local_file_for_manual_review():
    a,b=script.prepare(rows(raw(learn='',share='Indian culture, especially south indian.'),raw(learn='',share='')),MAP)
    assert a['fields']['ShareCultures']=='India' and a['fields']['Teachlanguages']==''
    assert 'NO_MAPPED_PROFILE_SELECTIONS' in b['issues']


def test_duplicate_source_account_is_explicit_and_skip_is_optional():
    source=rows(*[raw() for _ in range(207)])
    assert all('DUPLICATE_SOURCE_EMAIL' in r['issues'] for r in script.prepare(source,MAP))
    tail=script.prepare(source,MAP,206)
    assert len(tail)==1 and tail[0]['dataRow']==207 and tail[0]['excelRow']==208
    assert 'DUPLICATE_SOURCE_EMAIL' not in tail[0]['issues']
    assert script.prepare(source,MAP,207)==[]


def test_xlsx_read_is_values_only_and_preserves_input_hash(tmp_path):
    path=tmp_path/'test.xlsx';synthetic_workbook(path)
    before=path.read_bytes()
    parsed=script.workbook(path)
    assert parsed[0]==(1,2,{'A':'1','D':'p@example.org','P':'French'})
    assert path.read_bytes()==before
    synthetic_workbook(path,formula=True)
    with pytest.raises(ValueError,match='values-only'):script.workbook(path)


def test_original_forms_export_nonbreaking_spaces_in_headers(tmp_path):
    source=tmp_path/'ascii.xlsx';synthetic_workbook(source)
    with ZipFile(source) as z:entries={n:z.read(n) for n in z.namelist()}
    target=tmp_path/'forms.xlsx'
    with ZipFile(target,'x') as z:
        for name,data in entries.items():
            z.writestr(name,data.replace(b'Which Language',b'Which\xc2\xa0Language'))
    assert script.workbook(target)[0][2]['P']=='French'


def test_csv_outputs_are_excel_safe_and_roundtrip_manual_corrections(tmp_path):
    rec=script.prepare(rows(raw(E='=HYPERLINK("bad")',learn='Unknown',share='')),MAP)
    out=tmp_path/'private';script.write_outputs(out,rec,{'rowCount':1})
    with (out/'participants.csv').open(encoding='utf-8-sig',newline='') as f:
        saved=list(csv.DictReader(f))
    assert saved[0]['Title'].startswith("'=")
    reread=script.from_csv(out/'participants.csv')
    assert reread[0]['fields']['Title']==rec[0]['fields']['Title']
    assert 'Unknown' in (out/'manual-review.csv').read_text(encoding='utf-8-sig')
    with pytest.raises(FileExistsError):script.write_outputs(out,rec,{})


class FakeSharePoint:
    def __init__(self):
        self.calls=[];self.people=[];self.mode='ok';self.unique=True

    def request(self,path,method='GET',payload=None):
        self.calls.append((method,path,deepcopy(payload)))
        if path.startswith('_api/web/currentuser'):return 200,{'Id':9}
        if '/fields/' in path:return 200,{'TypeAsString':'User','EnforceUniqueValues':self.unique}
        if '?$select=ListItemEntityTypeFullName' in path:return 200,{'ListItemEntityTypeFullName':'SP.Data.ParticipantsListItem'}
        if path=='_api/web/ensureuser':
            if self.mode=='account':raise script.SharePointError(400)
            return 200,{'Id':17,'Email':'different@example.org' if self.mode=='wrong_email' else payload['logonName'],'Title':'Resolved Name'}
        assert method=='POST' and path.endswith('/items')
        if self.mode=='auth':raise script.SharePointError(403)
        if self.mode=='reject':raise script.SharePointError(502)
        if any(r['ParticipantaccountId']==payload['ParticipantaccountId'] for r in self.people):raise script.SharePointError(502)
        row={**payload,'Id':100+len(self.people)};self.people.append(row)
        if self.mode=='lost':raise script.SharePointError(502)
        return 201,{'Id':row['Id']}

    def rows(self,path,bound=5000):
        self.calls.append(('GET',path,None))
        for role,id_ in script.CATALOGUES.items():
            if id_ in path:
                return [{'Id':1,'Title':'English','Active':True},{'Id':2,'Title':'French','Active':True}] if role=='language' else [{'Id':7,'Title':'India','Active':True}]
        return deepcopy(self.people)


def test_apply_creates_correct_person_lookup_ids_and_replay_preserves_edits():
    source=script.prepare(rows(raw()),MAP);sp=FakeSharePoint()
    result=script.apply(source,sp)
    assert result[0]['status']=='CREATED'
    created=sp.people[0]
    assert created['ParticipantaccountId']==17 and 'Participantaccount' not in created
    assert created['LearnlanguagesId']=={'results':[2]} and created['TeachlanguagesId']=={'results':[1]}
    assert created['ParticipationStatus']=='Active' and created['OpenToConnections'] is True and 'Status' not in created
    created['Title']='User edit';created['Comments']='PRIVATE_LATER_EDIT'
    second=script.apply(source,sp)
    assert second[0]['status']=='EXISTING_PRESERVED' and created['Title']=='User edit'
    assert len([c for c in sp.calls if c[0]=='POST' and c[1].endswith('/items')])==1


@pytest.mark.parametrize('mode,status',[('account','MANUAL_REVIEW'),('wrong_email','MANUAL_REVIEW'),('reject','UNKNOWN'),('lost','UNKNOWN'),('auth','UNKNOWN')])
def test_account_failures_are_manual_and_unknown_writes_stop_without_retry(mode,status):
    sp=FakeSharePoint();sp.mode=mode
    records=script.prepare(rows(raw(),raw(email='second@example.org')),MAP)
    result=script.apply(records,sp)
    assert result[0]['status']==status
    assert len([c for c in sp.calls if c[0]=='POST' and c[1].endswith('/items')])<=1
    if status=='UNKNOWN':assert len(result)==1


def test_duplicate_source_and_invalid_profile_never_create():
    sp=FakeSharePoint();records=script.prepare(rows(raw(),raw()),MAP)
    assert all(r['status']=='MANUAL_REVIEW' for r in script.apply(records,sp))
    assert not sp.people
    records=script.prepare(rows(raw(learn='',share='')),MAP)
    assert script.apply(records,sp)[0]['code']=='FIX_CATALOGUE_SELECTIONS' and not sp.people


def test_cli_default_has_no_network_and_prints_no_identity_values(tmp_path,capsys,monkeypatch):
    path=tmp_path/'input.xlsx';synthetic_workbook(path)
    monkeypatch.setattr(script,'SharePoint',lambda *_:pytest.fail('Default must not authenticate or use network'))
    assert script.main(['--workbook',str(path),'--output',str(tmp_path/'out')])==0
    stdout=capsys.readouterr().out
    assert '@' not in stdout and json.loads(stdout)['mode']=='PREPARE_ONLY'
    assert (tmp_path/'out/participants.csv').exists()


def test_cli_apply_without_token_stops_before_writes(tmp_path,capsys,monkeypatch):
    source=tmp_path/'prepared';script.write_outputs(source,script.prepare(rows(raw()),MAP),{})
    monkeypatch.delenv('TANDEM_SP_ACCESS_TOKEN',raising=False)
    assert script.main(['--prepared-csv',str(source/'participants.csv'),'--output',str(tmp_path/'out'),'--apply'])==1
    assert 'No SharePoint token' in capsys.readouterr().err


def test_checkpoint_records_uncertain_write_before_network_call():
    sp=FakeSharePoint();checkpoints=[]
    original=sp.request
    def request(path,method='GET',payload=None):
        if method=='POST' and path.endswith('/items'):
            assert checkpoints[-1][0]['status']=='UNKNOWN'
            assert checkpoints[-1][0]['code']=='WRITE_STARTED_NOT_YET_CONFIRMED'
        return original(path,method,payload)
    sp.request=request
    script.apply(script.prepare(rows(raw()),MAP),sp,lambda values:checkpoints.append(deepcopy(values)))
    assert checkpoints[-1][0]['status']=='CREATED'


def test_apply_output_directory_exists_before_tenant_access(tmp_path,monkeypatch,capsys):
    source=tmp_path/'prepared';script.write_outputs(source,script.prepare(rows(raw()),MAP),{})
    path=source/'participants.csv';output=tmp_path/'out'
    monkeypatch.setenv('TANDEM_SP_ACCESS_TOKEN','PRIVATE_TOKEN')
    sp=FakeSharePoint();original=sp.request
    def request(*args,**kwargs):
        assert (output/'participants.csv').exists() and (output/'summary.json').exists()
        return original(*args,**kwargs)
    sp.request=request;monkeypatch.setattr(script,'SharePoint',lambda token:sp)
    assert script.main(['--prepared-csv',str(path),'--output',str(output),'--apply'])==0
    report=json.loads((output/'summary.json').read_text())
    assert report['participantWrites']==1 and report['complete']
    assert 'PRIVATE_TOKEN' not in capsys.readouterr().out


def test_workbook_cannot_be_applied_before_preparing_and_reviewing_csv(tmp_path):
    with pytest.raises(SystemExit):
        script.main(['--workbook',str(tmp_path/'input.xlsx'),'--apply'])


def test_delivery_launcher_has_literal_windows_paths_and_no_control_character_escapes():
    folder=script.ROOT/'artifacts/participant_import/python/v1'
    launcher=(folder/'Run-prepare.cmd').read_text(encoding='utf-8')
    guide=(folder/'README.md').read_text(encoding='utf-8')
    assert r'C:\projects\small_projects\tandem-language-culture-app\.venv\Scripts\python.exe' in launcher
    assert r'C:\private\new-version.xlsx' in guide
    assert not any(ord(c)<32 and c not in '\r\n' for c in launcher+guide)
