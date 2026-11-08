"""Generated-flow execution against a fake native store; not SharePoint proof."""
from collections import defaultdict
from copy import deepcopy
import json,re
from xml.etree import ElementTree as ET
from zipfile import ZipFile
import pytest
from test_compatibility_generated import Runner
from scripts.power_automate import build_coordination_fixture as fixture
from scripts.power_automate.schema_audit import measure


class FakeSharePoint:
    def __init__(self):self.fixture=None;self.rows={};self.fields=[];self.posts=0;self.calls=[];self.fail_receipt=False;self.fail_absence_read=False;self.low='2055';self.duplicate_mode='direct'
    def response(self,code,data,parameters):
        body={'d':data} if 'verbose' in parameters['parameters/headers'].get('Accept','') else data
        return {'statusCode':code,'body':body}
    def request(self,p):
        uri=p['parameters/uri'];method=p['parameters/method'];body=p.get('parameters/body')
        self.calls.append((method,uri,deepcopy(body)));self.posts+=method=='POST'
        def result(code,data):return self.response(code,data,p)
        if uri=='_api/web?$select=Id':return result(200,{'Id':'synthetic-site'})
        if uri=='_api/web/EffectiveBasePermissions':return result(200,{'High':'0','Low':self.low})
        if uri.startswith('_api/web/lists?$select='):
            return result(200,{'results':[self.fixture] if self.fixture else []})
        if uri=='_api/web/lists' and method=='POST':
            assert self.fixture is None
            self.fixture={'Id':'synthetic-fixture-guid','Title':body['Title'],'Description':body['Description'],
                'BaseTemplate':100,'ItemCount':0,'ListItemEntityTypeFullName':'SP.Data.SyntheticFixtureListItem'}
            self.fields=[{'InternalName':'Title','TypeAsString':'Text','Required':True,'Indexed':False,'EnforceUniqueValues':False}]
            return result(201,self.fixture)
        match=re.fullmatch(r"_api/web/lists\(guid'([^']+)'\)(.*)",uri)
        assert match and self.fixture and match[1]==self.fixture['Id'],uri
        suffix=match[2]
        if suffix.startswith('?$select='):
            self.fixture['ItemCount']=len(self.rows);return result(200,self.fixture)
        if suffix.startswith('/fields?$select='):return result(200,{'results':self.fields})
        if suffix=="/fields/getbyinternalnameortitle('Title')":
            assert method=='POST';self.fields[0].update({k:v for k,v in body.items() if k!='__metadata'});return result(204,{})
        if suffix=='/fields/createfieldasxml':
            attrs=ET.fromstring(body['parameters']['SchemaXml']).attrib
            self.fields.append({'InternalName':attrs['Name'],'TypeAsString':attrs['Type'],
                'Required':attrs['Required']=='TRUE','Indexed':attrs['Indexed']=='TRUE','EnforceUniqueValues':attrs['EnforceUniqueValues']=='TRUE'})
            return result(201,{})
        if suffix.startswith('/items?$filter='):
            criteria=suffix.split('?$filter=',1)[1].split('&',1)[0]
            prefix=re.fullmatch(r"startswith\((\w+),'([^']*)'\)",criteria)
            equal=re.fullmatch(r"(\w+) eq '([^']*)'",criteria)
            assert prefix or equal,criteria
            if self.fail_absence_read and equal and equal[2].endswith(':unique:otherTitle'):return result(500,{'error':{'message':'INJECTED_READ_FAILURE'}})
            matched=[r for r in self.rows.values() if str(r.get((prefix or equal)[1],'' )).startswith(prefix[2]) ] if prefix else [r for r in self.rows.values() if r.get(equal[1])==equal[2]]
            return result(200,{'results':deepcopy(matched)})
        if suffix=='/items' and method=='POST':
            assert body['__metadata']['type']==self.fixture['ListItemEntityTypeFullName']
            assert all(isinstance(body[k],str) and body[k] for k in ['Title','KeyB','Payload'])
            for f in ['Title','KeyB']:
                if any(r[f]==body[f] for r in self.rows.values()):
                    message='The list item could not be added or updated because duplicate values were found in the following field(s) in the list: ['+f+'].'
                    if self.duplicate_mode=='wrapped':
                        return {'statusCode':502,'body':{'error':{'code':502,'message':'BadGateway','innerError':{
                            'status':502,'message':message,'errors':['-2130575169','Microsoft.SharePoint.SPDuplicateValuesFoundException']}}}}
                    if self.duplicate_mode=='generic502':
                        return {'statusCode':502,'body':{'error':{'code':502,'message':'BadGateway'}}}
                    return {'statusCode':400,'body':{'error':{
                        'code':'-2130575169, Microsoft.SharePoint.SPDuplicateValuesFoundException','message':{'value':message}}}}
            i=len(self.rows)+1
            row={k:None for k in ['OwnerToken','Counter','Capacity','Status']}
            row['Complete']=False
            row.update({k:v for k,v in body.items() if k!='__metadata'})
            row.update(Id=i,__metadata={'etag':'"1"','type':self.fixture['ListItemEntityTypeFullName']})
            self.rows[i]=row;return result(201,deepcopy(row))
        item=re.fullmatch(r'/items\((\d+)\)',suffix);assert item,suffix
        row=self.rows[int(item[1])]
        if method=='GET':return result(200,deepcopy(row))
        assert method=='POST'
        if p['parameters/headers']['IF-MATCH']!=row['__metadata']['etag']:return result(412,{'error':{'message':'STALE_ETAG'}})
        if self.fail_receipt and ':Slot:receipt:A' in row['Title'] and body.get('Complete') is True:return result(500,{'error':{'message':'INJECTED_RECEIPT_FAILURE'}})
        row.update({k:v for k,v in body.items() if k!='__metadata'});v=int(row['__metadata']['etag'].strip('"'))+1
        row['__metadata']['etag']='"'+str(v)+'"';return result(204,{})


class NativeRunner(Runner):
    def __init__(self,server,write=True,prefer_b=False,run_name='fake-native-1'):
        super().__init__();self.outputs=defaultdict(lambda:None);self.action_states={};self.server=server;self.write=write;self.prefer_b=prefer_b;self.run_name=run_name
    def body(self,name):
        value=self.outputs[name]
        return value['body'] if isinstance(value,dict) and 'statusCode' in value else value
    def expr(self,text,ctx):
        text=text.replace('workflow()',"json('"+json.dumps({'run':{'name':self.run_name}})+"')")
        return super().expr(text,ctx)
    def run(self,actions,ctx=None):
        ctx=ctx or {'items':{},'triggerBody':{'boolean':self.write}};done={};todo=dict(actions)
        while todo:
            ready=[n for n,a in todo.items() if set(a.get('runAfter',{}))<=set(done)]
            assert ready,'Invalid graph'
            if self.prefer_b:ready.sort(key=lambda n:0 if n.endswith('_B_Writer') else 1)
            for name in ready:
                a=todo.pop(name);kind=a['type'];p=a.get('inputs',{});state='Succeeded'
                if any(done[n] not in allowed for n,allowed in a.get('runAfter',{}).items()):done[name]='Skipped';self.action_states[name]='Skipped';continue
                if kind=='OpenApiConnection':
                    self.outputs[name]=self.server.request(self.inputs(p['parameters'],ctx))
                    if self.outputs[name]['statusCode']>=400:state='Failed'
                elif kind=='Compose':
                    try:self.outputs[name]=self.inputs(p,ctx)
                    except ZeroDivisionError:self.outputs[name]={'error':'INJECTED_STOP'};state='Failed'
                elif kind=='InitializeVariable':
                    for v in p['variables']:self.variables[v['name']]=deepcopy(v['value'])
                elif kind=='SetVariable':self.variables[p['name']]=self.inputs(p['value'],ctx)
                elif kind=='AppendToArrayVariable':self.variables[p['name']].append(self.inputs(p['value'],ctx))
                elif kind in ['Query','Select']:
                    rows=self.inputs(p['from'],ctx);values=[]
                    for row in rows:
                        c={**ctx,'item':row}
                        if kind=='Select':values.append(self.inputs(p['select'],c))
                        elif self.expr(p['where'],c):values.append(row)
                    self.outputs[name]=values
                elif kind=='Foreach':
                    for row in self.inputs(a['foreach'],ctx):self.run(a['actions'],{**ctx,'items':{**ctx['items'],name:row}})
                elif kind=='If':self.run(a['actions'] if self.expr(a['expression'],ctx) else a['else']['actions'],ctx)
                elif kind=='Scope':self.run(a['actions'],ctx)
                elif kind=='Terminate':raise AssertionError(p)
                else:raise AssertionError(kind)
                done[name]=state;self.action_states[name]=state


def walk(actions,path=()):
    for n,a in actions.items():
        yield path+(n,),a
        yield from walk(a.get('actions',{}),path+(n,))
        yield from walk(a.get('else',{}).get('actions',{}),path+(n,))


@pytest.mark.parametrize('prefer_b',[False,True])
def test_generated_fixture_all_ten_checks_for_either_writer_order(prefer_b):
    server=FakeSharePoint();runner=NativeRunner(server,prefer_b=prefer_b)
    runner.run(fixture.Builder(fixture.SITE,'synthetic-build').actions())
    report=runner.outputs['Fixture_report']
    assert report['testCount']==10 and report['allPassed'] and report['failedCases']==[]
    assert server.fixture['Title'].startswith('Tandem47Fixture_')


@pytest.mark.parametrize('write',[False,'true'])
def test_default_or_string_truth_cannot_create_any_fixture(write):
    server=FakeSharePoint();runner=NativeRunner(server,write=write)
    runner.run(fixture.Builder(fixture.SITE,'synthetic-build').actions())
    assert server.fixture is None and server.posts==0
    assert not runner.outputs['Fixture_report']['writeRequested']


def test_same_build_reuses_verified_schema_with_fresh_run_prefix():
    server=FakeSharePoint();a=fixture.Builder(fixture.SITE,'synthetic-build').actions()
    first=NativeRunner(server,run_name='first');first.run(a);before=len(server.rows)
    second=NativeRunner(server,run_name='second');second.run(a)
    assert second.outputs['Fixture_report']['allPassed'] and not second.outputs['Fixture_report']['fixtureCreated']
    assert len(server.rows)==2*before


def test_colliding_untagged_list_is_never_modified():
    server=FakeSharePoint();server.fixture={'Id':'synthetic-fixture-guid','Title':'Tandem47Fixture_syntheticbuild','Description':'NOT OUR FIXTURE','BaseTemplate':100,'ItemCount':0}
    runner=NativeRunner(server)
    with pytest.raises(AssertionError,match='COLLISION'):runner.run(fixture.Builder(fixture.SITE,'synthetic-build').actions())
    assert server.posts==0


def test_revoked_permission_gate_blocks_all_fixture_writes():
    server=FakeSharePoint();server.low='5';runner=NativeRunner(server)
    with pytest.raises(AssertionError,match='NOT_COMPLETE'):runner.run(fixture.Builder(fixture.SITE,'synthetic-build').actions())
    assert server.posts==0 and server.fixture is None
    assert not runner.outputs['Fixture_report']['permissionGatePassed']


def test_nonempty_fixture_with_missing_field_is_not_silently_repaired():
    server=FakeSharePoint();a=fixture.Builder(fixture.SITE,'synthetic-build').actions()
    NativeRunner(server).run(a);posts=server.posts
    server.fields=[f for f in server.fields if f['InternalName']!='Payload']
    with pytest.raises(AssertionError,match='SCHEMA_NOT_VERIFIED'):NativeRunner(server,run_name='second').run(a)
    assert server.posts==posts


def test_receipt_failure_after_data_write_does_not_report_success_or_release():
    server=FakeSharePoint();server.fail_receipt=True;runner=NativeRunner(server)
    with pytest.raises(AssertionError):runner.run(fixture.Builder(fixture.SITE,'synthetic-build').actions())
    assert not runner.outputs['Fixture_report']['allPassed']
    row=next(r for r in server.rows.values() if ':Slot:group' in r['Title'])
    assert row['OwnerToken']=='Slot:A'


def test_failed_absence_read_never_counts_as_verified_zero_rows():
    server=FakeSharePoint();server.fail_absence_read=True;runner=NativeRunner(server)
    with pytest.raises(AssertionError,match='NOT_COMPLETE'):runner.run(fixture.Builder(fixture.SITE,'synthetic-build').actions())
    report=runner.outputs['Fixture_report']
    assert not report['allPassed']
    assert any(c['case']=='UNIQUE_SECONDARY' for c in report['failedCases'])


def test_all_data_writes_are_guarded_and_exact_etag_no_delete_or_permissions():
    a=fixture.Builder(fixture.SITE,'synthetic-build').actions()
    for path,x in walk(a):
        if x['type']=='Foreach':assert isinstance(x['foreach'],str) and x['runtimeConfiguration']['concurrency']['repetitions']==1
        if x['type']!='OpenApiConnection':continue
        p=x['inputs']['parameters'];uri=p['parameters/uri']
        assert p['parameters/method'] in ['GET','POST']
        assert not any(v in uri.lower() for v in ['roleassign','breakrole','resetrole'])
        if p['parameters/method']=='POST':
            assert path[0]=='Run_fixture_when_requested'
            assert x['inputs']['retryPolicy']=={'type':'none'}
            if '/fields' not in uri and p['parameters/headers'].get('X-HTTP-Method')=='MERGE':assert p['parameters/headers']['IF-MATCH']!='*'
    assert 'triggerBody()' in a['Run_fixture_when_requested']['expression']


def test_schema_verified_before_native_rows_and_parallel_barriers():
    a=fixture.Builder(fixture.SITE,'synthetic-build').actions()['Run_fixture_when_requested']['actions']
    assert a['Unique_anchor']['runAfter']=={'Require_fixture_schema':['Succeeded']}
    for prefix in ['Slot','Shrink','Departure']:
        assert a[prefix+'_A_Writer']['runAfter']==a[prefix+'_B_Writer']['runAfter']=={prefix+'_Barrier':['Succeeded']}
        assert set(a[prefix+'_FinalGroup']['runAfter'])=={prefix+'_A_Writer',prefix+'_B_Writer'}
    assert all(v is True for v in [s['unique'] for s in fixture.SPECS if s['name'] in ['Title','KeyB']])


def test_package_bounds_safe_default_and_no_overwrite(tmp_path):
    path=tmp_path/'fixture.zip';review=fixture.build_package(path)
    assert review['actions']<=500 and review['maximumActionDepth']<=8
    assert review['productionWrites']==review['deletes']==review['permissionChanges']==0
    assert review['writeGateDefault'] is False and review['caseCount']==10
    with ZipFile(path) as z:
        doc=json.loads(z.read(next(n for n in z.namelist() if n.endswith('/definition.json'))))
        assert doc['properties']['definition']['triggers']['manual']['inputs']['schema']['properties']['boolean']['default'] is False
        assert measure(doc['properties']['definition']['actions'])['actions']==review['actions']
    with pytest.raises(FileExistsError):fixture.build_package(path)


@pytest.mark.parametrize('prefer_b',[False,True])
def test_wrapped_sharepoint_duplicate_all_ten_cases_pass(prefer_b):
    server=FakeSharePoint();server.duplicate_mode='wrapped'
    runner=NativeRunner(server,prefer_b=prefer_b)
    runner.run(fixture.Builder(fixture.SITE,'synthetic-build').actions())
    report=runner.outputs['Fixture_report']
    assert report['allPassed'] and report['testCount']==10
    duplicates=[r for r in report['results'] if 'nativeErrorCodes' in r['details']]
    assert len(duplicates)==5
    assert all(r['details']['httpStatus']==502 for r in duplicates)


def test_generic_bad_gateway_cannot_pass_duplicate_proof():
    server=FakeSharePoint();server.duplicate_mode='generic502';runner=NativeRunner(server)
    with pytest.raises(AssertionError,match='NOT_COMPLETE'):
        runner.run(fixture.Builder(fixture.SITE,'synthetic-build').actions())
    report=runner.outputs['Fixture_report']
    assert {r['case'] for r in report['failedCases']}=={
        'UNIQUE_PRIMARY','UNIQUE_SECONDARY','KNOWN_PREFIX_REPLAY','LEFT_EPISODE_HISTORY','COMMITTED_EVENT_UNIQUE'}
    assert not report['allPassed']


@pytest.mark.parametrize('status,body,expected',[
    (502,{'error':{'innerError':{'errors':['-2130575169','Microsoft.SharePoint.SPDuplicateValuesFoundException']}}},True),
    (400,{'error':{'code':'-2130575169, Microsoft.SharePoint.SPDuplicateValuesFoundException'}},True),
    (409,{'error':{'code':'-2130575169, Microsoft.SharePoint.SPDuplicateValuesFoundException'}},True),
    (502,{'error':{'message':'BadGateway'}},False),
    (502,{'error':{'innerError':{'errors':['-2130575169']}}},False),
    (502,{'error':{'innerError':{'errors':['Microsoft.SharePoint.SPDuplicateValuesFoundException']}}},False),
    (400,{'error':{'code':'INVALID_FIELD','message':'duplicate values'}},False),
    (409,{'error':{'code':'CONFLICT'}},False),
    (201,{'error':{'innerError':{'errors':['-2130575169','Microsoft.SharePoint.SPDuplicateValuesFoundException']}}},False),
    (503,{'error':{'innerError':{'errors':['-2130575169','Microsoft.SharePoint.SPDuplicateValuesFoundException']}}},False),
    (502,{},False),
])
def test_duplicate_requires_recognized_status_and_native_error(status,body,expected):
    runner=NativeRunner(FakeSharePoint())
    runner.outputs['Attempt']={'statusCode':status,'body':body}
    assert runner.expr('@'+fixture.duplicate('Attempt'),{}) is expected
