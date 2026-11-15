"""#48 private Excel proof: emitted-graph tests use fictional rows only."""
import json
from zipfile import ZipFile
import pytest
from core_native_backend import ParentRunner
from scripts.power_automate import private_excel_probe as probe
from scripts.power_automate.activation_graph import analyze
from scripts.power_automate.activation_schema import has_patterns
from scripts.power_automate.schema_audit import measure


class Excel:
    def __init__(self,rows=206,error=False,paged=False,headers=True):
        self.rows=[{probe.EMAIL:'PRIVATE_EMAIL@example.org',probe.OTHER:'PRIVATE_NAME PRIVATE_OTHER@example.org','ID':'PRIVATE_SOURCE_ID'} for _ in range(rows)] if headers else [{'wrong':'PRIVATE_VALUE'} for _ in range(rows)]
        self.error=error;self.paged=paged;self.requests=[]

    def request(self,p):
        self.requests.append(p)
        assert set(p)=={'source','drive','file','table','$top'}
        assert p['$top']==251
        if self.error:return {'statusCode':403,'body':{'error':'PRIVATE_ACCOUNT permission error'}}
        body={'value':self.rows}
        if self.paged:body['@odata.nextLink']='PRIVATE_FILE_LINK'
        return {'statusCode':200,'body':body}


def execute(excel=None,expected=206):
    excel=excel or Excel();runner=ParentRunner(excel)
    runner.run(probe.actions('https://example.sharepoint.com/sites/Tandem','local-build'),{'items':{},'triggerBody':{'ExpectedRows':expected}})
    report=runner.outputs['Private_read_report']
    assert isinstance(report,dict),runner.action_states
    assert 'PRIVATE_' not in json.dumps(report)
    assert report['identityValuesIncluded'] is False and report['participantWrites']==0
    return report,runner


def test_complete_read_reports_only_counts_and_not_private_values():
    report,_=execute()
    assert report['success'] is True and report['code']=='OK' and report['rowCount']==206
    assert report['rowsWithEmailText']==report['rowsWithOtherIdentityText']==206


@pytest.mark.parametrize('excel,code',[(Excel(error=True),'EXCEL_READ_FAILED'),(Excel(paged=True),'INCOMPLETE_OR_TOO_LARGE'),
    (Excel(rows=251),'INCOMPLETE_OR_TOO_LARGE'),(Excel(rows=252),'INVALID_TABLE_RESPONSE'),
    (Excel(rows=205),'ROW_COUNT_MISMATCH'),(Excel(headers=False),'IDENTITY_HEADERS_MISMATCH'),(Excel(rows=0),'ROW_COUNT_MISMATCH')])
def test_rejects_incomplete_failed_or_wrong_source_without_disclosing_rows(excel,code):
    report,_=execute(excel)
    assert report['success'] is False and report['code']==code


def test_anonymous_and_mixed_identity_text_are_counted_without_resolving_or_exporting():
    excel=Excel(rows=3)
    excel.rows=[{probe.EMAIL:'anonymous',probe.OTHER:'Private Person (person@example.org)'},
                {probe.EMAIL:'',probe.OTHER:'another@example.org'},
                {probe.EMAIL:'direct@example.org',probe.OTHER:''}]
    report,_=execute(excel,3)
    assert report['success'] is True and report['rowsWithEmailText']==1 and report['rowsWithOtherIdentityText']==2
    assert report['accountResolution']=='NOT_ATTEMPTED'
    assert '@' not in json.dumps(report)


def test_all_private_row_actions_are_secured_and_no_write_operations_exist():
    actions=probe.actions('https://example.sharepoint.com/sites/Tandem','test')
    for name,node in actions.items():
        if name not in {'Private_read_report','Workbook_configuration'}:
            expected={'inputs'} if node['type']=='ParseJson' else {'inputs','outputs'}
            assert set(node['runtimeConfiguration']['secureData']['properties'])==expected
    probe.validate_secure_data(actions)
    reads=[node for node in actions.values() if node['type']=='OpenApiConnection']
    assert len(reads)==1 and reads[0]['inputs']['host']['operationId']=='GetItems'
    assert not has_patterns(actions) and not analyze({'actions':actions})
    assert measure(actions)=={'actions':6,'maximumActionDepth':1}
    probe.validate_excel_template(actions)


def test_actual_v2_import_placeholder_is_rejected_by_new_template_gate():
    path=probe.ROOT/'artifacts/participant_import/private_excel_read/v2/TandemPrivateExcelReadProbe-v2.zip'
    with ZipFile(path) as z:
        doc=json.loads(z.read(next(n for n in z.namelist() if n.endswith('/definition.json'))))
    with pytest.raises(ValueError,match='runtime'):
        probe.validate_excel_template(doc['properties']['definition']['actions'])


def test_unconfigured_template_has_no_invented_file_library_or_table_ids():
    actions=probe.actions('https://example.sharepoint.com/sites/Tandem','test')
    parameters=actions['Read_workbook']['inputs']['parameters']
    assert all(parameters[key].startswith("@variables('WorkbookConfiguration')") for key in ('source','drive','file','table'))
    assert 'SELECT_' not in json.dumps(actions)
    assert actions['Workbook_configuration']['inputs']['variables'][0]['value']['drive']==''


@pytest.mark.parametrize('kind',['ParseJson','Compose','Response'])
def test_native_secure_output_rejection_is_caught_before_packaging(kind):
    with pytest.raises(ValueError,match='Secure Outputs is unsupported'):
        probe.validate_secure_data({'Regression':{'type':kind,'runtimeConfiguration':probe.SECURE}})


def test_actual_failed_v1_package_is_rejected_by_new_native_gate():
    path=probe.ROOT/'artifacts/participant_import/private_excel_read/v1/TandemPrivateExcelReadProbe-v1.zip'
    with ZipFile(path) as z:
        doc=json.loads(z.read(next(n for n in z.namelist() if n.endswith('/definition.json'))))
    with pytest.raises(ValueError,match='Private_rows'):
        probe.validate_secure_data(doc['properties']['definition']['actions'])


def test_internal_inspection_failure_is_not_reported_as_success():
    actions=probe.actions('https://example.sharepoint.com/sites/Tandem','local-build')
    actions['Private_email_present']['inputs']['where']='@div(1,0)'
    runner=ParentRunner(Excel());runner.run(actions,{'items':{},'triggerBody':{'ExpectedRows':206}})
    report=runner.outputs['Private_read_report']
    assert report['success'] is False and report['code']=='PRIVATE_INSPECTION_FAILED'
    assert report['participantWrites']==0 and 'PRIVATE_' not in json.dumps(report).replace('PRIVATE_INSPECTION_FAILED','')


def test_generated_package_requires_existing_excel_connection_and_private_file_selection(tmp_path):
    path=tmp_path/'private.zip';doc,review=probe.build_package(path)
    assert review['nativeExcelRead']=='NOT RUN' and review['actions']==6 and review['maximumActionDepth']==1
    assert doc['properties']['connectionReferences'][probe.CONNECTOR]['source']=='Embedded'
    with ZipFile(path) as z:
        assert z.testzip() is None
        manifest=json.loads(z.read('manifest.json'))
        assert any(v.get('id')==probe.API for v in manifest['resources'].values())
        definition=z.read(next(n for n in z.namelist() if n.endswith('/definition.json'))).decode()
        assert not any(marker in definition for marker in ['PRIVATE_EMAIL','PRIVATE_NAME','PRIVATE_OTHER','PRIVATE_SOURCE_ID','PRIVATE_ACCOUNT'])
    with pytest.raises(FileExistsError):probe.build_package(path)
