"""Combined #48 migration: synthetic workbook and stateful fake SharePoint only."""
from copy import deepcopy
import csv
import json
from pathlib import Path
import re
from xml.etree import ElementTree as ET
from zipfile import ZipFile
import pytest
from scripts import import_participants_once as api
from scripts import matching_workbook_import as flow
from core_native_backend import ParentRunner

MAP=api.configuration()


def record(i,group='French 1',status='active - matched',email=None):
    return {'sheet':'active','excelRow':i+1,'raw':{'A':str(i),'B':group,'D':email or f'person{i}@example.org',
        'E':f'Fictional person {i}','I':'French','J':'Conversation','K':'English','O':status}}


def bundle(count=3):
    return flow.prepare([{'name':'active','rows':[record(i) for i in range(1,count+1)]}],MAP,api)


def workbook(path):
    ns=api.NS['s'];headers={'A':'ID','B':'Group','D':'Email','E':'Name','I':'Which\xa0Language/Culture would you like to learn?',
        'J':'Is your learning focus:','K':'Which\xa0Language/Culture would you love to share?','O':'Outcome status 2025'}
    payloads={}
    for index,name in enumerate(['active','paused','non active','unadjusted list - safety copy'],1):
        root=ET.Element('{'+ns+'}worksheet');data=ET.SubElement(root,'{'+ns+'}sheetData')
        head={**headers,'B':'Group that they left'} if name=='non active' else headers
        raw=record(index)['raw']
        for number,values in [(1,head),(2,raw),(75,{})]:
            row=ET.SubElement(data,'{'+ns+'}row',r=str(number))
            for col,text in values.items():
                cell=ET.SubElement(row,'{'+ns+'}c',r=col+str(number),t='inlineStr')
                ET.SubElement(ET.SubElement(cell,'{'+ns+'}is'),'{'+ns+'}t').text=text
                if name.startswith('unadjusted') and number==2:ET.SubElement(cell,'{'+ns+'}f').text='SHOULD_NEVER_READ_BACKUP'
        payloads['xl/worksheets/sheet'+str(index)+'.xml']=ET.tostring(root)
    names=['active','paused','non active','unadjusted list - safety copy']
    with ZipFile(path,'x') as z:
        z.writestr('xl/workbook.xml',f'<workbook xmlns="{ns}" xmlns:r="{api.REL}"><sheets>'+''.join(f'<sheet name="{name}" sheetId="{i}" r:id="r{i}"/>' for i,name in enumerate(names,1))+'</sheets></workbook>')
        z.writestr('xl/_rels/workbook.xml.rels','<Relationships>'+''.join(f'<Relationship Id="r{i}" Target="worksheets/sheet{i}.xml"/>' for i in range(1,5))+'</Relationships>')
        for name,data in payloads.items():z.writestr(name,data)


def test_matching_reader_ignores_backup_and_formatted_blank_tails(tmp_path):
    p=tmp_path/'matching.xlsx';workbook(p)
    sheets=flow.read_sheets(p,api)
    assert [s['name'] for s in sheets]==['active','paused','non active']
    assert [len(s['rows']) for s in sheets]==[1,1,1]
    redacted=flow.read_sheets(p,api,redact_identities=True)
    assert all('D' not in r['raw'] and 'E' not in r['raw'] for s in redacted for r in s['rows'])


def test_external_link_parts_are_ignored_without_following_them(tmp_path):
    p=tmp_path/'matching.xlsx';workbook(p)
    with ZipFile(p,'a') as z:z.writestr('xl/externalLinks/externalLink1.xml','<never-fetch/>')
    assert flow.read_sheets(p,api)[0]['externalLinkPartsIgnored']==1


def test_all_current_tabs_map_status_and_do_not_turn_paused_people_into_left_members():
    paused=record(4);paused['sheet']='paused';paused['raw']['O']='pause'
    left=record(5);left['sheet']='non active';left['raw']['O']='stopped'
    b=flow.prepare([{'name':'active','rows':[record(1),record(2)]},{'name':'paused','rows':[paused]},
                    {'name':'non active','rows':[left]}],MAP,api)
    assert [p['fields']['ParticipationStatus'] for p in b['participants']]==['Active','Active','Paused','Inactive']
    assert [p['fields']['OpenToConnections'] for p in b['participants']]==['Yes','Yes','No','No']
    assert [m['MembershipStatus'] for m in b['memberships']]==['Active','Active','REVIEW','Left']
    assert b['groups'][0]['ImportApproved']=='No' and b['groups'][0]['State']=='Closed'


def test_multiple_group_cells_split_without_inventing_memberships_for_waiting_people():
    r=record(1,group='F: Finnish|G: German;\nFrench 1')
    b=flow.prepare([{'name':'active','rows':[r,record(2,group='French 1',status='change group')]}],MAP,api)
    assert len(b['groups'])==3 and len(b['memberships'])==4
    assert b['memberships'][-1]['MembershipStatus']=='REVIEW'


def test_supported_groups_closed_and_oversized_language_group_review_only():
    a=bundle(2);b=bundle(5)
    assert a['groups'][0]['State']=='Closed' and a['groups'][0]['ImportApproved']=='Yes'
    assert b['groups'][0]['ImportApproved']=='No' and b['groups'][0]['Capacity']==''
    assert len(b['memberships'])==5 and 'OVER_CAPACITY' in b['groups'][0]['ReviewNotes']


def test_group_keys_are_stable_and_do_not_merge_reused_letter_with_different_focus():
    assert flow.migration_key('Y: German')==flow.migration_key(' Y:   GERMAN ')
    assert flow.migration_key('C: French-English')!=flow.migration_key('C: Chinese 1')


def test_group_and_participant_bundle_roundtrip_and_missing_reference_rejected(tmp_path):
    b=bundle(3);folder=tmp_path/'out';flow.write_bundle(folder,b,flow.summary(b,'2.0.0'),api)
    loaded=flow.read_bundle(folder,api)
    assert loaded['groups']==b['groups'] and loaded['memberships']==b['memberships']
    assert [p['importKey'] for p in loaded['participants']]==[p['importKey'] for p in b['participants']]
    text=(folder/'memberships.csv').read_text(encoding='utf-8-sig').replace('legacy:1','missing-ref')
    (folder/'memberships.csv').write_text(text,encoding='utf-8-sig')
    with pytest.raises(ValueError,match='missing group or participant'):flow.read_bundle(folder,api)


def test_matching_cli_auto_detects_and_has_zero_network(tmp_path,capsys,monkeypatch):
    p=tmp_path/'matching.xlsx';workbook(p);output=tmp_path/'out'
    monkeypatch.setattr(api,'SharePoint',lambda *_:pytest.fail('Preparation must not use network'))
    assert api.main(['--workbook',str(p),'--output',str(output)])==0
    report=json.loads(capsys.readouterr().out)
    assert report['participantCount']==3 and report['sourceTabs']==['active','paused','non active']
    assert report['groupWrites']==report['membershipWrites']==0
    assert '@' not in json.dumps(report)
    assert (output/'groups.csv').exists() and (output/'memberships.csv').exists()


class SharePoint:
    def __init__(self):
        self.tables={flow.GROUPS:[],flow.MEMBERS:[],flow.REQUESTS:[]};self.log=[];self.fault=None;self.unique=True
        self.types={id_:'SP.Data.'+str(i)+'Item' for i,id_ in enumerate(self.tables,1)}

    def request(self,path,method='GET',payload=None,etag=None):
        self.log.append((method,path,deepcopy(payload)))
        id_=next((k for k in self.tables if k in path),None)
        if not id_:raise AssertionError(path)
        if '/fields/' in path:return 200,{'EnforceUniqueValues':self.unique}
        if '?$select=ListItemEntityTypeFullName' in path:return 200,{'ListItemEntityTypeFullName':self.types[id_]}
        m=re.search(r'/items\((\d+)\)',path)
        if method=='GET':
            assert m,path
            row=next(r for r in self.tables[id_] if r['Id']==int(m[1]))
            return 200,deepcopy(row)
        if m:
            row=next(r for r in self.tables[id_] if r['Id']==int(m[1]))
            assert etag==row['_etag'] and etag!='*'
            if self.fault=='publish' and payload.get('SetupComplete') is True:raise api.SharePointError(502)
            row.update({k:v for k,v in payload.items() if k!='__metadata'});row['_etag']='"2"'
            return 204,{}
        assert method=='POST'
        if self.fault=='member' and id_==flow.MEMBERS:raise api.SharePointError(502)
        row={k:v for k,v in payload.items() if k!='__metadata'}
        row.update(Id=len(self.tables[id_])+1,_etag='"1"')
        self.tables[id_].append(row)
        # Assert every staged request already follows the actual native request key contract.
        if id_==flow.REQUESTS:check_request(row)
        if self.fault=='lost-group' and id_==flow.GROUPS:raise api.SharePointError(502)
        return 201,deepcopy(row)

    def rows(self,path,bound=5000):
        for role,id_ in api.CATALOGUES.items():
            if id_ in path:return [{'Id':1,'Title':'English','Active':True},{'Id':2,'Title':'French','Active':True}] if role=='language' else []
        id_=next(k for k in self.tables if k in path)
        result=self.tables[id_]
        match=re.search(r'\$filter=(\w+) eq (?:\x27([^\x27]*)\x27|(\d+))',path)
        if match:
            value=match[2] if match[2] is not None else int(match[3])
            result=[r for r in result if r.get(match[1])==value]
        assert len(result)<bound
        return deepcopy(result)


def check_request(row):
    """Execute the actual packaged MyRequests invariant, including staged rows."""
    path=api.ROOT/'artifacts/core_batch/v1.0.0.2/definitions/TandemMyRequests.json'
    doc=json.loads(path.read_text(encoding='utf-8'))
    from scripts.power_automate.activation_graph import walk
    expression=next(a['expression'] for name,a,_,_ in walk(doc['properties']['definition']['actions']) if name=='Request_integrity')
    runner=ParentRunner(None)
    assert runner.expr(expression,{'items':{'Validate_requests':row}}),row


def apply_bundle(b,sp=None):
    sp=sp or SharePoint()
    participants=[{'dataRow':i,'status':'EXISTING_PRESERVED','participantId':100+i} for i in range(1,len(b['participants'])+1)]
    return flow.apply_groups(b,participants,sp,api),sp


def test_group_import_commits_native_keys_and_three_members_then_preserves_replay_edits():
    b=bundle(3);report,sp=apply_bundle(b)
    assert report[0]['status']=='CREATED' and report[0]['confirmedCreates']=={'groups':1,'members':3,'requests':2}
    group=sp.tables[flow.GROUPS][0];assert group['SetupComplete'] is True and group['State']=='Closed'
    for m in sp.tables[flow.MEMBERS]:
        assert re.fullmatch(r'request:\d+:participant:\d+',m['MembershipKey'])
        assert m['MembershipStatus']=='Active' and m['LeftAt'] is None and m['JoinedAt']
    for r in sp.tables[flow.REQUESTS]:
        check_request(r)
        assert r['OperationComplete'] and r['ConnectionKey']=='history:request:'+str(r['Id'])
        assert 'historical migration' in r['Title']
    group['Title']='Member-edited title';group['State']='Open'
    again,_=apply_bundle(b,sp)
    assert again[0]['status']=='EXISTING_PRESERVED' and group['Title']=='Member-edited title'
    assert group['State']=='Open' and len(sp.tables[flow.MEMBERS])==3


@pytest.mark.parametrize('fault',['member','lost-group','publish'])
def test_unknown_group_write_stops_unpublished_and_never_automatically_resumes(fault):
    b=bundle(2);sp=SharePoint();sp.fault=fault
    report,_=apply_bundle(b,sp)
    assert report[0]['status']=='UNKNOWN'
    assert all(g['SetupComplete'] is False for g in sp.tables[flow.GROUPS])
    before=len(sp.log);sp.fault=None;again,_=apply_bundle(b,sp)
    assert again[0]['code']=='PARTIAL_MIGRATION_REQUIRES_RECONCILIATION'
    assert not any(method=='POST' for method,_,_ in sp.log[before:])


def test_missing_members_and_oversized_group_cannot_create_requests_or_group():
    b=bundle(5);b['groups'][0]['ImportApproved']='Yes';b['groups'][0]['Capacity']='3'
    report,sp=apply_bundle(b)
    assert report[0]['status']=='MANUAL_REVIEW' and not any(method=='POST' for method,_,_ in sp.log)
    b=bundle(2);sp=SharePoint()
    result=flow.apply_groups(b,[{'dataRow':1,'status':'EXISTING_PRESERVED','participantId':1}],sp,api)
    assert result[0]['code']=='RESOLVE_ALL_GROUP_MEMBERS' and not any(method=='POST' for method,_,_ in sp.log)


def test_former_members_left_is_preserved_and_paused_membership_requires_explicit_review():
    b=bundle(2);b['memberships'][1]['MembershipStatus']='Left'
    report,sp=apply_bundle(b)
    assert report[0]['status']=='CREATED'
    assert next(m for m in sp.tables[flow.MEMBERS] if m['MembershipStatus']=='Left')['LeftAt']
    b=bundle(2);b['memberships'][1]['MembershipStatus']='REVIEW'
    report,sp=apply_bundle(b)
    assert report[0]['status']=='MANUAL_REVIEW' and not any(method=='POST' for method,_,_ in sp.log)


def test_imported_group_is_visible_through_actual_packaged_my_groups_graph():
    from core_native_backend import seed,Connection
    report,sp=apply_bundle(bundle(3));assert report[0]['status']=='CREATED'
    db=seed()
    for i,p in enumerate(db.tables['participants'][:3],101):p['Id']=i
    for role,id_ in [('groups',flow.GROUPS),('members',flow.MEMBERS),('requests',flow.REQUESTS)]:
        rows=deepcopy(sp.tables[id_])
        for r in rows:r['__metadata']={'etag':r.pop('_etag')}
        db.tables['members' if role=='members' else role]=rows
    path=api.ROOT/'artifacts/core_batch/v1.0.0.2/definitions/TandemMyGroups.json'
    actions=json.loads(path.read_text(encoding='utf-8'))['properties']['definition']['actions']
    runner=ParentRunner(Connection(db,actor=1))
    runner.run(actions,{'items':{},'triggerBody':{'number':101}})
    assert runner.response['resultcode']=='OK',runner.response
    groups=json.loads(runner.response['groupsjson'])
    assert len(groups)==1 and groups[0]['memberCount']==3 and groups[0]['state']=='Closed'


def test_cli_bundle_apply_reports_all_created_lists_and_checkpoint_results(tmp_path,monkeypatch,capsys):
    b=bundle(3);source=tmp_path/'prepared';flow.write_bundle(source,b,flow.summary(b,'2.0.0'),api)
    sp=SharePoint();monkeypatch.setenv('TANDEM_SP_ACCESS_TOKEN','PRIVATE_TOKEN');monkeypatch.setattr(api,'SharePoint',lambda _:sp)
    def participants(records,server,checkpoint):
        rows=[{'dataRow':i,'status':'EXISTING_PRESERVED','participantId':100+i} for i in range(1,4)]
        checkpoint(rows);return rows
    monkeypatch.setattr(api,'apply',participants)
    output=tmp_path/'applied'
    assert api.main(['--prepared-bundle',str(source),'--apply','--output',str(output)])==0
    summary=json.loads(capsys.readouterr().out)
    assert summary['complete'] and summary['groupWrites']==1 and summary['membershipWrites']==3 and summary['migrationRequestWrites']==2
    assert '@' not in json.dumps(summary) and 'PRIVATE_TOKEN' not in json.dumps(summary)
    journal=json.loads((output/'group-results.private.json').read_text())
    assert journal[0]['status']=='CREATED' and journal[0]['writeAttempts']['members']==3


def test_group_preflight_failure_does_not_erase_completed_participant_count(tmp_path,monkeypatch,capsys):
    b=bundle(2);source=tmp_path/'prepared';flow.write_bundle(source,b,flow.summary(b,'2.0.0'),api)
    sp=SharePoint();sp.unique=False
    monkeypatch.setenv('TANDEM_SP_ACCESS_TOKEN','PRIVATE_TOKEN');monkeypatch.setattr(api,'SharePoint',lambda _:sp)
    def participants(records,server,checkpoint):
        rows=[{'dataRow':1,'status':'CREATED','participantId':101},{'dataRow':2,'status':'EXISTING_PRESERVED','participantId':102}]
        checkpoint(rows);return rows
    monkeypatch.setattr(api,'apply',participants);output=tmp_path/'applied'
    assert api.main(['--prepared-bundle',str(source),'--apply','--output',str(output)])==1
    summary=json.loads((output/'summary.json').read_text())
    assert summary['participantWrites']==1 and not summary['complete'] and summary['stopped']


def test_partial_first_group_stops_before_any_second_group_writes():
    b=flow.prepare([{'name':'active','rows':[record(1),record(2),record(3,group='English 2'),record(4,group='English 2')]}],MAP,api)
    sp=SharePoint();sp.fault='member';first,_=apply_bundle(b,sp)
    assert first[0]['status']=='UNKNOWN' and len(first)==1
    sp.fault=None;before=len(sp.log);second,_=apply_bundle(b,sp)
    assert second[0]['status']=='STOPPED' and len(second)==1
    assert not any(method=='POST' for method,_,_ in sp.log[before:])


def test_rejected_membership_dates_cannot_start_group_writes():
    b=bundle(2);b['memberships'][0]['JoinedAt']='2020-01-01'  # No timezone.
    report,sp=apply_bundle(b)
    assert report[0]['status']=='MANUAL_REVIEW' and not any(m=='POST' for m,_,_ in sp.log)


def test_portable_delivery_runs_without_repository_imports(tmp_path):
    import subprocess,sys
    folder=api.ROOT/'artifacts/participant_import/python/v2'
    source=tmp_path/'matching.xlsx';workbook(source);output=tmp_path/'out'
    result=subprocess.run([sys.executable,str(folder/'import_participants_once.py'),'--workbook',str(source),'--output',str(output)],
                          cwd=tmp_path,capture_output=True,text=True,encoding='utf-8')
    assert result.returncode==0,result.stderr
    summary=json.loads(result.stdout)
    assert summary['version']=='2.0.0' and summary['participantCount']==3
    assert (output/'groups.csv').exists() and (output/'memberships.csv').exists()
