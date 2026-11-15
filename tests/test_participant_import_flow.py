"""Execute emitted #48 helper graph against a stateful fake SharePoint boundary.

Local graph tests only, not certification of Power Automate or tenant permissions.
"""
from copy import deepcopy
import json
from pathlib import Path
import re
from zipfile import ZipFile
import pytest
from core_native_backend import ParentRunner
from scripts.power_automate import participant_import as flow
from scripts.power_automate.activation_graph import analyze
from scripts.power_automate.activation_schema import has_patterns
from scripts.power_automate.schema_audit import measure

MAPPING=json.loads((flow.ROOT/'config/tenant_schema_mapping.json').read_text())
SITE=json.loads((flow.ROOT/'config/batch_schema_contract.json').read_text())['site']


def payload():
    return {'kind':'TandemParticipantImportPlan','contractVersion':1,'sourceTicket':48,
            'sourceSha256':'a'*64,'targetSite':SITE,'readyForApply':True,'rows':[{
                'sourceKey':'response:1','accountLogin':'i:0#.f|membership|person@example.org',
                'sharepointUserId':17,'Title':'Example Person','teachIds':[],'learnIds':[7],
                'shareCultureIds':[],'learnCultureIds':[],'ParticipationStatus':'Paused','OpenToConnections':False}]}


class Tenant:
    def __init__(self):
        self.rows=[];self.posts=[];self.mode='ok';self.paged=False;self.read_fail=False
        self.users=[{'Id':17,'LoginName':'i:0#.f|membership|person@example.org','Email':'person@example.org','Title':'Example Person'}]
        self.catalogues={'language':[{'Id':7,'Title':'French','Active':True}],'culture':[],'timezone':[]}

    def request(self,p):
        assert p['dataset']==SITE
        uri=p['parameters/uri'];method=p['parameters/method']
        def response(body,status=200):return {'statusCode':status,'body':deepcopy(body)}
        if self.read_fail:return response({'error':'READ_FAILED'},503)
        if 'siteusers/getbyid(' in uri:
            user_id=int(re.search(r'getbyid\((\d+)\)',uri)[1])
            found=[u for u in self.users if u['Id']==user_id]
            return response(found[0] if found else {},200 if found else 404)
        if uri.startswith('_api/web/siteusers?'):return response({'value':self.users})
        role=next((r for r in ('participants','language','culture','timezone') if MAPPING['lists'][r]['listId'] in uri),None)
        assert role,uri
        if '/fields(' in uri:
            return response({'InternalName':'Participantaccount','TypeAsString':'User','EnforceUniqueValues':True,'ReadOnlyField':False})
        if '?$select=ListItemEntityTypeFullName' in uri:return response({'ListItemEntityTypeFullName':'SP.Data.ParticipantsListItem'})
        if method=='POST':
            assert role=='participants' and uri.endswith('/items')
            row=deepcopy(p['parameters/body']);self.posts.append(row)
            if self.mode=='reject':return response({'error':'temporary'},502)
            row['Id']=100+len(self.rows);self.rows.append(row)
            return response({'Id':row['Id']},502 if self.mode=='unknown_commit' else 201)
        assert method=='GET'
        if role=='participants':
            match=re.search(r'ParticipantaccountId eq (\d+)',uri)
            return response({'value':[r for r in self.rows if not match or r['ParticipantaccountId']==int(match[1])]})
        body={'value':self.catalogues[role]}
        if self.paged:body['odata.nextLink']='https://example.invalid/next'
        return response(body)


class Runner(ParentRunner):
    def extra_functions(self,context):
        return {**super().extra_functions(context),'setProperty':lambda value,key,item:{**value,key:item}}


def execute(server=None,plan=None,apply=False,blank=False):
    server=server or Tenant();runner=Runner(server)
    runner.run(flow.definition(SITE,MAPPING,'local-test'),{'items':{},'triggerBody':{
        'PlanJson':'' if blank else json.dumps(payload() if plan is None else plan),'ApplyChanges':apply}})
    report=runner.outputs['Snapshot_report' if blank else 'Import_report']
    assert isinstance(report,dict),runner.action_states
    return report,server,runner


def test_snapshot_empty_lists_are_complete_and_zero_writes():
    report,server,_=execute(blank=True)
    assert report['collectionComplete'] is True and report['participants']==[] and report['culture']==[]
    assert not server.posts and report['runReference']=='local-subset-not-a-tenant-run'


@pytest.mark.parametrize('failure',['paged','read_fail'])
def test_snapshot_failure_or_paging_is_not_partial_success(failure):
    server=Tenant();setattr(server,failure,True)
    report,_,_=execute(server,blank=True)
    assert report['collectionComplete'] is False and not server.posts


def test_dry_run_never_posts_and_reports_every_row():
    report,server,_=execute()
    assert report['allPassed'] is True and report['writesCount']==report['writeAttempts']==0
    assert [r['status'] for r in report['rows']]==['VALIDATED_NEW'] and not server.posts


def test_create_then_repeat_preserves_existing_profile_without_overwrite():
    report,server,_=execute(apply=True)
    assert report['allPassed'] is True and report['writesCount']==1
    assert server.rows[0]['ParticipationStatus']=='Paused' and server.rows[0]['OpenToConnections'] is False
    assert server.rows[0]['LearnlanguagesId']=={'results':[7]}
    assert 'Status' not in server.posts[0] and 'Comments' not in server.posts[0]
    server.rows[0]['Comments']='Subsequent self-service edit'
    second,_,_=execute(server,apply=True)
    assert second['allPassed'] is True and second['writesCount']==0 and len(server.posts)==1
    assert second['rows'][0]['status']=='SKIPPED_EXISTING' and second['rows'][0]['participantId']==100
    assert server.rows[0]['Comments']=='Subsequent self-service edit'


@pytest.mark.parametrize('change',['ready','target','duplicate','identity','catalogue','empty','hash','sourcekey','type'])
def test_invalid_plan_never_reaches_any_write(change):
    plan=payload()
    if change=='ready':plan['readyForApply']=False
    if change=='target':plan['targetSite']='https://other.invalid'
    if change=='duplicate':plan['rows'].append({**plan['rows'][0],'sourceKey':'response:2'})
    if change=='identity':plan['rows'][0]['accountLogin']='another-person'
    if change=='catalogue':plan['rows'][0]['learnIds']=[9999]
    if change=='empty':plan['rows'][0]['learnIds']=[]
    if change=='hash':plan['sourceSha256']='x'*64
    if change=='sourcekey':plan['rows'][0]['sourceKey']='bad-prefix'
    if change=='type':plan['rows'][0]['OpenToConnections']='true'
    report,server,_=execute(plan=plan,apply=True)
    assert report['allPassed'] is False and report['writeAttempts']==0 and not server.posts


def test_later_invalid_row_blocks_entire_plan_before_first_write():
    plan=payload();plan['rows'].append({**plan['rows'][0],'sourceKey':'response:2','sharepointUserId':999,'accountLogin':'missing-person'})
    report,server,_=execute(plan=plan,apply=True)
    assert not report['allPassed'] and not server.posts
    assert [r['status'] for r in report['preflightRows']]==['VALIDATED_NEW','REJECTED']


@pytest.mark.parametrize('mode',['reject','unknown_commit'])
def test_502_is_never_success_even_when_a_row_is_visible_and_is_reported_once(mode):
    server=Tenant();server.mode=mode
    report,_,_=execute(server,apply=True)
    assert report['allPassed'] is False and report['writesCount']==0 and report['unknown'] is True
    assert len(server.posts)==1 and len(report['rows'])==1
    assert report['rows'][0]['status']=='UNKNOWN' and report['writeAttempts']==1


def test_packaged_graph_has_native_structure_guards_and_only_one_write_endpoint(tmp_path):
    path=tmp_path/'helper.zip';document,review=flow.build_package(path)
    actions=document['properties']['definition']['actions']
    assert not analyze(document['properties']['definition'])
    assert measure(actions)['maximumActionDepth']<=8 and review['actions']<=500
    assert not has_patterns(actions)
    assert document['properties']['connectionReferences']['shared_sharepointonline']['source']=='Embedded'
    with ZipFile(path) as z:
        assert z.testzip() is None
        assert any(n.endswith('/definition.json') for n in z.namelist())
    with pytest.raises(FileExistsError):flow.build_package(path)
