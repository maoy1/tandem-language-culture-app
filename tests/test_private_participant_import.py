"""Execute emitted #48 graph; fictional transport only, no tenant certification."""
from copy import deepcopy
import json
import re
from zipfile import ZipFile
import pytest
from core_native_backend import ParentRunner
from scripts.power_automate import private_participant_import as flow

SITE='https://example.sharepoint.com/sites/tandem'
MAPPING=json.loads((flow.ROOT/'config/tenant_schema_mapping.json').read_text())
VALUES=json.loads((flow.ROOT/'config/participant_excel_value_mapping.json').read_text())


def source(email='private@example.org',learn='French',share='English',other=''):
    return {'Email':email,'Please leave your name and Email':other,
            flow.HEADERS['learn']:learn,flow.HEADERS['learn2']:'',flow.HEADERS['share']:share,
            'Is your learning focus:':'Conversation','PRIVATE_SECRET':'do not report'}


class Tenant:
    def __init__(self,rows=None):
        self.rows=rows if rows is not None else [source()]
        self.people=[];self.posts=[];self.calls=[];self.ensures=[]
        self.lookup_fail=False;self.lookup_email=None;self.fault=None;self.paged=False
        self.excel_fail=False
        self.read_fail=False;self.unique=True;self.rename=False;self.person_changed=False
        self.catalogues={'language':[{'Id':1,'Title':'English','Active':True},{'Id':2,'Title':'French','Active':True}],
                         'culture':[{'Id':7,'Title':'India','Active':True}]}
        self.users={};self.lookups=0

    def person(self,email):
        if email not in self.users:
            self.users[email]={'Id':50+len(self.users),'LoginName':'i:0#.f|membership|'+email,'Email':email,'Title':'PRIVATE_NAME'}
        return self.users[email]

    def request(self,p):
        self.calls.append(deepcopy(p))
        def response(body,status=200):return {'statusCode':status,'body':deepcopy(body)}
        if '$skip' in p:
            if self.excel_fail:return response({'error':'PRIVATE_EXCEL_ERROR'},403)
            rows=self.rows[p['$skip']:p['$skip']+p['$top']]
            return response({'value':rows,**({'@odata.nextLink':'PRIVATE_FILE'} if self.paged else {})})
        if 'searchValue' in p:
            self.lookups+=1
            if self.lookup_fail:return response({'error':'PRIVATE_ACCOUNT'},404)
            u=self.person(p['searchValue'])
            return response({'Email':self.lookup_email or u['Email'],'Claims':u['LoginName']+('changed' if self.person_changed and self.lookups>1 else ''),'DisplayName':u['Title']})
        uri=p['parameters/uri'];method=p['parameters/method']
        if self.read_fail:return response({'error':'PRIVATE_ERROR'},403)
        if uri=='_api/web/ensureuser':
            assert method=='POST'
            claims=p['parameters/body']['logonName'];u=next(u for u in self.users.values() if u['LoginName']==claims)
            self.ensures.append(claims)
            return response(u)
        role=next((r for r in ('participants','language','culture') if MAPPING['lists'][r]['listId'] in uri),None)
        assert role,uri
        if '/fields(' in uri:return response({'InternalName':'Participantaccount','TypeAsString':'User','ReadOnlyField':False,'EnforceUniqueValues':self.unique})
        if '?$select=ListItemEntityTypeFullName' in uri:return response({'ListItemEntityTypeFullName':'SP.Data.ParticipantsListItem'})
        if role!='participants':
            rows=deepcopy(self.catalogues[role])
            if self.rename and self.ensures:
                for r in rows:r['Title']='Changed'
            return response({'value':rows})
        if method=='POST':
            payload=deepcopy(p['parameters/body']);self.posts.append(payload)
            if self.fault=='before':return response({'error':'PRIVATE_WRITE_ERROR'},502)
            if any(r['ParticipantaccountId']==payload['ParticipantaccountId'] for r in self.people):return response({},502)
            u=next(u for u in self.users.values() if u['Id']==payload['ParticipantaccountId'])
            row={**payload,'Id':100+len(self.people),'Participantaccount':{'Name':u['LoginName']}}
            self.people.append(row)
            return response({'Id':row['Id']},502 if self.fault=='after' else 201)
        match=re.search(r'ParticipantaccountId eq (\d+)',uri)
        return response({'value':[r for r in self.people if not match or r['ParticipantaccountId']==int(match[1])]})


class Runner(ParentRunner):
    def __init__(self,server):
        super().__init__(server);self.scoped_results={}

    def extra_functions(self,context):
        return {**super().extra_functions(context),'range':lambda start,count:list(range(start,start+count)),
                'result':lambda name:deepcopy(self.scoped_results.get(name,[]))}

    def run(self,actions,ctx=None):
        # Native foreach references belong to the current iteration. The common
        # subset runner otherwise leaves skipped descendants from a prior one.
        if 'Prepare_one' in actions or 'Apply_one' in actions:
            for name,_,_,_ in flow.walk(actions):
                self.outputs[name]=None;self.action_states[name]='Skipped'
        result=super().run(actions,ctx)
        if 'Prepared_record' in actions:
            self.scoped_results.setdefault('Prepare_rows',[]).append({'name':'Prepared_record',
                'status':self.action_states.get('Prepared_record','Skipped'),
                'outputs':deepcopy(self.outputs['Prepared_record'])})
        return result


def execute(tenant=None,apply=False,skip=0,expected=None):
    t=tenant or Tenant();r=Runner(t)
    expected=max(0,len(t.rows)-skip) if expected is None else expected
    graph=flow.actions(SITE,MAPPING,VALUES,'local-build')
    r.run(graph,{'items':{},'triggerBody':{'ApplyChanges':apply,'SkipRows':skip,'ExpectedRows':expected}})
    assert isinstance(r.outputs['Import_report'],list),r.action_states
    report=r.outputs['Import_report'][0]
    serialized=json.dumps(report)
    for private in ('private@example','PRIVATE_','membership','Claims','@'):
        assert private not in serialized
    # No identities may reach unsupported variable history, even temporarily.
    assert 'PRIVATE_' not in json.dumps(r.variables) and 'membership' not in json.dumps(r.variables)
    assert 'private@example.org' not in json.dumps(r.variables)
    return report,t,r


def test_dry_run_resolves_privately_and_makes_no_explicit_writes():
    report,t,r=execute()
    assert report['complete'] and report['code']=='OK',r.action_states
    assert report['readyCount']==1 and report['processedRows']==1
    assert report['rows']==[{'dataRow':1,'status':'READY_CREATE','code':'READY_CREATE'}]
    assert not t.posts and not t.ensures and report['accountRegistrationAttempts']==0
    assert not any(p.get('parameters/method')=='POST' for p in t.calls)


def test_apply_then_replay_preserves_existing_profile_and_new_defaults():
    report,t,r=execute(apply=True)
    assert report['complete'] and report['createdCount']==1,r.action_states
    row=t.people[0]
    assert row['ParticipationStatus']=='Active' and row['OpenToConnections'] is True
    assert row['TeachlanguagesId']=={'results':[1]} and row['LearnlanguagesId']=={'results':[2]}
    assert 'Status' not in row and 'Comments' not in row and 'TimezoneId' not in row
    row['Comments']='PRIVATE_LATER_EDIT';row['ParticipationStatus']='Paused'
    second,_,_=execute(t,apply=True)
    assert second['existingCount']==1 and second['createdCount']==0 and len(t.posts)==1
    assert row['Comments']=='PRIVATE_LATER_EDIT' and row['ParticipationStatus']=='Paused'


@pytest.mark.parametrize('other',['PRIVATE_NAME (private@example.org)','private@example.org','PRIVATE_NAME, private@example.org','PRIVATE_NAME <private@example.org>','mailto:private@example.org'])
def test_mixed_identity_fallback_is_automatic(other):
    report,_,_=execute(Tenant([source(email='anonymous',other=other)]))
    assert report['readyCount']==1 and report['blockedCount']==0


@pytest.mark.parametrize('email,other',[
    ('one@example.org','two@example.org'),('bad@@example.org',''),('@example.org',''),
    ('p@example.org.',''),('p@invalid',''),('',''),('p@.example.org',''),('p@ex!ample.org','')])
def test_missing_ambiguous_or_bad_email_never_searches_or_writes(email,other):
    report,t,_=execute(Tenant([source(email=email,other=other)]),apply=True)
    assert report['blockedCount']==1 and t.lookups==0 and not t.posts and not t.ensures


@pytest.mark.parametrize('mode',['lookup_fail','lookup_email','unknown_selection','no_profile','duplicate','wrong_person'])
def test_row_exceptions_are_sanitized_and_never_written(mode):
    t=Tenant()
    if mode=='lookup_fail':t.lookup_fail=True
    if mode=='lookup_email':t.lookup_email='different@example.org'
    if mode=='unknown_selection':t.rows[0][flow.HEADERS['learn']]='Unreviewed new language'
    if mode=='no_profile':t.rows[0][flow.HEADERS['learn']]='';t.rows[0][flow.HEADERS['share']]=''
    if mode=='duplicate':t.rows.append(source())
    if mode=='wrong_person':t.person_changed=True
    report,t,_=execute(t,apply=True)
    assert report['complete'] and report['blockedCount']==len(t.rows) and not t.posts


def test_partial_valid_rows_import_while_exceptions_remain_explicit():
    t=Tenant([source(),source(email='invalid')])
    report,_,_=execute(t,apply=True)
    assert report['complete'] and report['code']=='COMPLETED_WITH_EXCEPTIONS'
    assert report['createdCount']==report['blockedCount']==1 and report['processedRows']==2


def test_duplicate_account_with_rejected_selection_cannot_import_other_response():
    t=Tenant([source(),source(learn='Unreviewed selection')])
    report,_,_=execute(t,apply=True)
    assert report['complete'] and report['blockedCount']==2 and not t.posts


def test_culture_only_supported_without_inferred_language_or_timezone():
    t=Tenant([source(learn='',share='Indian culture, especially south indian.')])
    report,_,_=execute(t,apply=True)
    assert report['createdCount']==1
    assert t.posts[0]['ShareCulturesId']=={'results':[7]} and t.posts[0]['TeachlanguagesId']=={'results':[]}


@pytest.mark.parametrize('fault',['before','after'])
def test_failed_write_is_unknown_once_and_never_automatically_retried(fault):
    t=Tenant();t.fault=fault
    report,_,_=execute(t,apply=True)
    assert report['complete'] and report['unknownCount']==1 and report['createdCount']==0
    assert report['code']=='UNKNOWN_WRITE' and len(t.posts)==1 and len(report['rows'])==1


@pytest.mark.parametrize('mode',['excel_fail','paged','read_fail','unique','headers','mismatch','overflow'])
def test_prerequisite_failure_blocks_entire_batch(mode):
    t=Tenant();expected=1
    if mode in ('excel_fail','paged','read_fail'):setattr(t,mode,True)
    if mode=='unique':t.unique=False
    if mode=='headers':del t.rows[0][flow.HEADERS['learn']]
    if mode=='mismatch':expected=2
    if mode=='overflow':t.rows=t.rows*251;expected=250
    report,t,_=execute(t,apply=True,expected=expected)
    assert not report['complete'] and report['code'] in {'INCOMPLETE_SOURCE_WINDOW','SOURCE_HEADERS_MISMATCH','SHAREPOINT_PREREQUISITES_FAILED','EXCEL_READ_FAILED'} and not t.posts and not t.ensures


@pytest.mark.parametrize('skip,expected',[(206,1),(207,0)])
def test_skip206_reads_only_selected_tail_and_reports_absolute_data_row(skip,expected):
    t=Tenant([source(email='invalid')]*206+[source()])
    report,_,_=execute(t,skip=skip,expected=expected)
    assert report['complete'] and report['readyCount']==expected and report['processedRows']==expected
    if expected:assert report['rows'][0]['dataRow']==207


def test_catalogue_rename_between_plan_and_apply_blocks_create():
    t=Tenant();t.rename=True
    report,_,_=execute(t,apply=True)
    assert report['blockedCount']==1 and report['createdCount']==0 and not t.posts


@pytest.mark.parametrize('options',[{'SkipRows':-1},{'SkipRows':1.5},{'SkipRows':'PRIVATE_VALUE'},
    {'ExpectedRows':251},{'ExpectedRows':'PRIVATE_VALUE'},{'ApplyChanges':'PRIVATE_VALUE'}])
def test_invalid_options_do_not_read_or_echo_private_text(options):
    t=Tenant();r=Runner(t)
    r.run(flow.actions(SITE,MAPPING,VALUES,'test'),{'items':{},'triggerBody':{'SkipRows':0,'ExpectedRows':1,'ApplyChanges':False,**options}})
    report=r.outputs['Import_report'][0]
    assert report['code']=='INVALID_READ_OPTIONS' and not report['complete'] and not t.calls
    assert 'PRIVATE_' not in json.dumps(report)


def test_package_structure_security_connections_and_no_overwrite(tmp_path):
    path=tmp_path/'private.zip';doc,review=flow.build_package(path)
    a=doc['properties']['definition']['actions']
    assert not flow.analyze(doc['properties']['definition']) and not flow.has_patterns(a)
    assert flow.measure(a)=={'actions':121,'maximumActionDepth':7}
    flow.excel.validate_secure_data(a);flow.excel.validate_excel_template(a)
    assert set(doc['properties']['connectionReferences'])=={'shared_excelonlinebusiness','shared_sharepointonline'}
    for name,node,_,_ in flow.walk(a):
        if name=='Workbook_configuration':continue  # Public file-selection placeholders only.
        if node['type'] in ('Scope','If','Foreach','InitializeVariable','SetVariable','AppendToArrayVariable'):
            assert 'secureData' not in node.get('runtimeConfiguration',{})
            if node['type']=='AppendToArrayVariable':
                assert node['inputs']['name'] in {'Outcomes','Eligible','AccountAttempts',*flow.TARGETS}
                value=node['inputs']['value']
                if isinstance(value,dict):assert set(value)<={'dataRow','status','code'}
            continue
        expected={'inputs'} if node['type'] in ('Compose','ParseJson') or name=='Import_report' else {'inputs','outputs'}
        assert set(node['runtimeConfiguration']['secureData']['properties'])==expected,name
        if node['type']=='OpenApiConnection' and node['inputs']['parameters'].get('parameters/method')=='POST':
            assert node['inputs']['retryPolicy']=={'type':'none'}
    with ZipFile(path) as z:
        assert not z.testzip()
        for n in z.namelist():json.loads(z.read(n))
    assert review['nativeApply']=='NOT RUN'
    with pytest.raises(FileExistsError):flow.build_package(path)
