import json
from zipfile import ZipFile
import pytest
from scripts.power_automate import build_coordination_preflight as preflight
from scripts.power_automate.schema_audit import measure


def test_only_two_metadata_gets_no_fixture_or_production_reads():
    a=preflight.actions(preflight.SITE,'test');calls=[x for x in a.values() if x['type']=='OpenApiConnection']
    assert len(calls)==2
    assert {c['inputs']['parameters']['parameters/uri'] for c in calls}=={'_api/web?$select=Id','_api/web/EffectiveBasePermissions'}
    assert all(c['inputs']['parameters']['parameters/method']=='GET' for c in calls)
    assert all('parameters/body' not in c['inputs']['parameters'] for c in calls)


def test_report_gate_includes_all_permission_bits_and_no_false_write_claim():
    a=preflight.actions(preflight.SITE,'test');f=a['Permission_flags']['inputs'];r=a['Preflight_report']['inputs']
    assert all(str(v) in json.dumps(f) for v in [1,2,4,2048])
    assert all(key in r['fixturePermissionGatePassed'] for key in f)
    assert r['readOnly'] and not r['fixtureCreated'] and r['writes']==0
    assert all(v==['Succeeded'] for x in a.values() for v in x.get('runAfter',{}).values())


def test_no_response_concurrency_and_measured_limits():
    a=preflight.actions(preflight.SITE,'test');assert measure(a)=={'actions':5,'maximumActionDepth':1}
    assert not any(x['type'] in ['Response','Foreach'] for x in a.values())


def test_package_maps_existing_connection_and_keeps_new_flow(tmp_path):
    p=tmp_path/'test.zip';r=preflight.build_package(p)
    assert r['readOnly'] and r['writes']==0 and r['actions']==5
    with ZipFile(p) as z:
        manifest=json.loads(z.read('manifest.json'))
        flow=next(x for x in manifest['resources'].values() if x['type']=='Microsoft.Flow/flows')
        connection=next(x for x in manifest['resources'].values() if x['type']=='Microsoft.PowerApps/apis/connections')
        assert flow['suggestedCreationType']=='New' and connection['suggestedCreationType']=='Existing'
        doc=json.loads(z.read(next(n for n in z.namelist() if n.endswith('/definition.json'))))
        assert doc['properties']['displayName']==preflight.NAME
        assert not any('runtimeConfiguration' in t for t in doc['properties']['definition']['triggers'].values())
    with pytest.raises(FileExistsError):preflight.build_package(p)
