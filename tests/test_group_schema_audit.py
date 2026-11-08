"""#12 generated read-only inspector against bounded fake metadata responses."""
from copy import deepcopy
import json,re
from zipfile import ZipFile
import pytest
from test_coordination_fixture import NativeRunner,walk
from scripts.power_automate import build_group_schema_audit as audit

MAPPING=json.loads((audit.ROOT/'config/tenant_schema_mapping.json').read_text(encoding='utf-8'))


class Metadata:
    def __init__(self):
        self.calls=[];self.mode='normal'
        self.targets=[{'Id':'00000000-0000-0000-0000-000000000012','Title':'Groups','BaseTemplate':100,'ItemCount':3},
                      {'Id':'00000000-0000-0000-0000-000000000013','Title':'Group Members','BaseTemplate':100,'ItemCount':6}]
        self.references=[{'Id':s['listId'],'Title':s['listTitle'],'BaseTemplate':100} for role,s in MAPPING['lists'].items() if role in ['participants','language','culture']]
    def request(self,p):
        assert p['parameters/method']=='GET'
        uri=p['parameters/uri'];assert '/items' not in uri.lower();self.calls.append(uri)
        def response(value,status=200):return {'statusCode':status,'body':deepcopy(value)}
        if uri.startswith('_api/web/lists?$select='):
            if self.mode=='indexFailed':return response({'error':{'message':'DENIED'}},403)
            rows=deepcopy(self.targets)
            if self.mode=='ambiguous':rows.append({**rows[1],'Id':'another-id','Title':'GroupMembers'})
            if self.mode=='missing':rows=rows[:1]
            if self.mode=='wrongTemplate':rows[1]['BaseTemplate']=101
            value={'value':rows}
            if self.mode=='indexPage':value['@odata.nextLink']='next-page'
            if self.mode=='indexNull':value={}
            return response(value)
        match=re.fullmatch(r"_api/web/lists\(guid'([^']+)'\)(.*)",uri);assert match,uri
        target=next(r for r in self.targets+self.references if r['Id']==match[1])
        suffix=match[2]
        if target in self.references:
            if self.mode=='referenceFailed':return response({'error':{'message':'DENIED'}},403)
            return response({} if self.mode=='referenceNull' else target)
        if suffix.startswith('?$select='):return response(target)
        if suffix=='/EffectiveBasePermissions':
            if self.mode=='permissionFailed':return response({'error':{'message':'DENIED'}},403)
            return response({} if self.mode=='permissionNull' else {'High':'0','Low':'2055'})
        assert suffix.startswith('/fields?$select=')
        fields=[{'Id':'title-id','InternalName':'Title','Title':'Name','TypeAsString':'Text','FromBaseType':True,'Required':True,'DefaultValue':None,'SchemaXml':'<Field Type="Text" />'},
                {'Id':'custom-id','InternalName':'Actual_x0020_Internal','Title':'Display label','TypeAsString':'Choice','FromBaseType':False,'Required':False,'DefaultValue':'Closed','SchemaXml':'<Field><CHOICES><CHOICE>Closed</CHOICE></CHOICES></Field>'},
                {'Id':'id','InternalName':'ID','Title':'ID','TypeAsString':'Counter','FromBaseType':True}]
        value={'value':fields}
        if self.mode=='fieldsPage':value['odata.nextLink']='next-page'
        if self.mode=='fieldsNull':value={}
        if self.mode=='fieldsFailed':return response({'error':{'message':'DENIED'}},403)
        return response(value)


def inspect(server):
    runner=NativeRunner(server)
    runner.run(audit.actions(audit.SITE,'fixture-only',MAPPING))
    return runner.outputs['Audit_report']


def test_metadata_collection_preserves_actual_names_and_does_not_claim_schema_pass():
    server=Metadata();report=inspect(server)
    assert report['collectionComplete'] and not report['schemaVerified']
    assert report['readOnly'] and report['rowReads']==report['writes']==0
    assert len(report['lists'])==2 and len(report['referenceLists'])==3
    for row in report['lists']:
        assert [f['internalName'] for f in row['fields']]==['Title','Actual_x0020_Internal']
        assert row['fields'][1]['defaultValue']=='Closed' and row['fields'][1]['schemaXml']
        assert len(row['columnIndex'])==3
        assert row['permissionEvidence']=={'High':'0','Low':'2055'}


@pytest.mark.parametrize('mode',['ambiguous','missing','wrongTemplate','indexPage','indexFailed','indexNull','referenceFailed','referenceNull','fieldsPage','fieldsFailed','fieldsNull','permissionFailed','permissionNull'])
def test_incomplete_or_ambiguous_metadata_never_reports_complete(mode):
    server=Metadata();server.mode=mode
    report=inspect(server)
    assert not report['collectionComplete'] and not report['schemaVerified']
    if mode in ['indexPage','indexFailed']:assert not report['lists']


def test_package_has_only_get_requests_and_no_response_concurrency_conflict(tmp_path):
    path=tmp_path/'audit.zip';review=audit.build_package(path)
    assert review['actions']<=500 and review['maximumActionDepth']<=8
    assert review['writes']==review['rowReads']==0 and review['readOnly']
    with ZipFile(path) as z:
        doc=json.loads(z.read(next(n for n in z.namelist() if n.endswith('/definition.json'))))
        for _,action in walk(doc['properties']['definition']['actions']):
            assert action['type']!='Response'
            if action['type']=='OpenApiConnection':
                p=action['inputs']['parameters'];assert p['parameters/method']=='GET'
                assert '/items' not in p['parameters/uri'].lower()
        assert 'concurrency' not in json.dumps(doc['properties']['definition']['triggers'])
    with pytest.raises(FileExistsError):audit.build_package(path)
