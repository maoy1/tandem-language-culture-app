"""Package safety/guard tests. These do not simulate SharePoint or prove tenant execution."""
import json
from zipfile import ZipFile
import pytest
from scripts.power_automate import schema_setup as setup
from scripts.power_automate.schema_audit import measure


@pytest.fixture
def document(tmp_path):
    return setup.build_package(tmp_path/'setup.zip','https://example.sharepoint.com/sites/Tandem')[0]


def walk(actions,path=()):
    for name,a in actions.items():
        yield path+(name,),a
        yield from walk(a.get('actions',{}),path+(name,))
        yield from walk(a.get('else',{}).get('actions',{}),path+(name,'else'))


def test_explicit_apply_and_verified_preflight_gate_every_write(document):
    d=document['properties']['definition'];gate=d['actions']['Apply_only_when_ready']
    assert "equals(triggerBody()?['boolean'],true)" in gate['expression']
    assert "equals(outputs('Preflight_ready'),true)" in gate['expression']
    assert d['triggers']['manual']['inputs']['schema']['properties']['boolean']['default'] is False
    writes=[(path,a) for path,a in walk(d['actions']) if isinstance(a.get('inputs'),dict) and a['inputs'].get('parameters',{}).get('parameters/method')=='POST']
    assert len(writes)==5
    assert all(path[:2]==('Apply_only_when_ready','Apply_setup') for path,a in writes)
    assert all(a['inputs']['retryPolicy']=={'type':'none'} for path,a in writes)


def test_no_profile_rows_or_permission_operations_are_generated(document):
    for path,a in walk(document['properties']['definition']['actions']):
        p=a.get('inputs',{}).get('parameters',{}) if isinstance(a.get('inputs'),dict) else {}
        uri=p.get('parameters/uri','');method=p.get('parameters/method')
        if method=='POST':assert '/fields' in uri and '/items' not in uri
        assert method not in ['PATCH','DELETE']
        assert not ('/items' in uri and setup.LISTS['participants'] in uri)
        assert not any(x in uri.lower() for x in ['roleassignments','breakroleinheritance','resetroleinheritance'])


def test_preflight_verifies_permissions_field_identity_values_and_bounds(document):
    actions=document['properties']['definition']['actions']['Preflight']['actions']
    expression=actions['Preflight_ready']['inputs']
    for role in setup.LISTS:
        assert f"body('Read_{role}_permissions')" in expression
        assert "2048" in expression
        assert f"body('Read_{role}_fields')?['@odata.nextLink']" in expression
    for role in ['language','timezone']:
        assert f"empty(body('Invalid_{role}_values'))" in expression
        assert f"union(body('Keys_{role}'),body('Keys_{role}'))" in expression
    for name in setup.NEW:assert f"body('Candidates_{name}')" in expression and f"body('Valid_{name}')" in expression


def test_fresh_readback_and_no_rollback_claim(document):
    actions=document['properties']['definition']['actions']
    writes=actions['Apply_only_when_ready']['actions']['Apply_setup']['actions']
    assert all('Verify_'+role+'_fields' in writes for role in setup.LISTS)
    assert 'Setup_verified' in writes
    r=actions['Setup_report']['inputs']
    assert "equals(outputs('Setup_verified'),true)" in r['setupVerified']
    assert 'FAILED_OR_PENDING_READBACK' in r['result'] and 'BLOCKED_PREFLIGHT' in r['result']
    assert 'Never claim rollback' in r['recovery']


def test_already_correct_settings_are_skipped(document):
    writes=document['properties']['definition']['actions']['Apply_only_when_ready']['actions']['Apply_setup']['actions']
    for name in setup.NEW:assert writes['Ensure_'+name]['expression']==f"@empty(body('Candidates_{name}'))"
    for role,name,i,s in setup.UPDATES:assert writes['Ensure_'+role+'_'+name]['expression']==f"@empty(body('Valid_{role}_{name}'))"


def test_manifest_new_flow_existing_connection_and_metrics(tmp_path):
    path=tmp_path/'setup.zip';doc,r=setup.build_package(path,'https://example.sharepoint.com/sites/Tandem')
    assert r['actions']<500 and r['maximumActionDepth']<8
    assert measure(doc['properties']['definition']['actions'])=={k:r[k] for k in ['actions','maximumActionDepth']}
    with ZipFile(path) as z:
        assert z.testzip() is None
        manifest=json.loads(z.read('manifest.json'))
    flow=next(v for v in manifest['resources'].values() if v['type']=='Microsoft.Flow/flows')
    assert flow['suggestedCreationType']=='New'
    connection=next(v for v in manifest['resources'].values() if v['type']=='Microsoft.PowerApps/apis/connections')
    assert connection['creationType']=='Existing'
    with pytest.raises(FileExistsError):setup.build_package(path,'https://example.sharepoint.com/sites/Tandem')


def test_choice_validation_tolerates_nonchoice_fields_without_xml_null(document):
    actions=document['properties']['definition']['actions']['Preflight']['actions']
    assert "xml(coalesce(item()?['SchemaXml'],'<Field/>'))" in actions['Valid_ParticipationStatus']['inputs']['where']


def test_exact_bounded_mutation_scope():
    assert len(setup.NEW)==2 and len(setup.UPDATES)==3
    assert set(setup.NEW)=={'ParticipationStatus','OpenToConnections'}
    assert [x[1] for x in setup.UPDATES]==['Title','Title','IANA_ID']
    assert all(x[0] in ['language','timezone'] for x in setup.UPDATES)


def test_synchronous_response_has_no_request_trigger_concurrency(document):
    # Regression for tenant InvalidConcurrencyConfiguration on the original setup ZIP.
    definition=document['properties']['definition']
    assert definition['actions']['Respond']['type']=='Response'
    assert definition['actions']['Respond'].get('operationOptions')!='Asynchronous'
    for trigger in definition['triggers'].values():
        if trigger['type']=='Request':
            assert 'concurrency' not in trigger.get('runtimeConfiguration',{})
