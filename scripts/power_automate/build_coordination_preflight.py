"""#47 read-only permission preflight; does not create a fixture or alter data."""
import argparse
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED,ZipFile
from .build_import_probe import build_package as envelope
from .schema_audit import get,measure

NAME='TandemCoordinationPreflight'
SITE='https://reedelsevier.sharepoint.com/sites/OG-TandemOrg'


def actions(site,build_id):
    a={'Read_site_identity':get(site,'_api/web?$select=Id'),
       'Read_web_permissions':get(site,'_api/web/EffectiveBasePermissions','Read_site_identity')}
    a['Permission_low']={'type':'Compose','inputs':"@string(coalesce(body('Read_web_permissions')?['Low'],body('Read_web_permissions')?['EffectiveBasePermissions']?['Low'],''))",'runAfter':{'Read_web_permissions':['Succeeded']}}
    complete="and(not(empty(body('Read_site_identity')?['Id'])),not(empty(outputs('Permission_low'))))"
    low="int(if(empty(outputs('Permission_low')),'0',outputs('Permission_low')))"
    flags={key:'@equals(mod(div('+low+','+str(bit)+'),2),1)' for key,bit in [('viewItems',1),('addItems',2),('editItems',4),('manageLists',2048)]}
    a['Permission_flags']={'type':'Compose','inputs':flags,'runAfter':{'Permission_low':['Succeeded']}}
    ready=complete[:-1]+',and('+','.join("equals(outputs('Permission_flags')?['"+k+"'],true)" for k in flags)+'))'
    a['Preflight_report']={'type':'Compose','runAfter':{'Permission_flags':['Succeeded']},'inputs':{
        'kind':NAME,'schemaVersion':1,'sourceTicket':47,'packageBuildId':build_id,'runReference':"@workflow()?['run']?['name']",
        'readOnly':True,'fixtureCreated':False,'writes':0,'permissionMetadataCollected':'@'+complete,
        'fixturePermissionGatePassed':'@'+ready,'permissionFlags':"@outputs('Permission_flags')",
        'scope':'Read site technical ID and effective web permission metadata only. No fixture/production data or schema changed.',
        'nextStep':'Fixture schema/creation and native unique-key/CAS/race proof remain separate and unverified.'}}
    measure(a);return a


def build_package(output,site=SITE):
    output=Path(output)
    if any(p.exists() for p in [output,output.with_suffix('.definition.json'),output.with_suffix('.review.json')]):raise FileExistsError(output)
    with TemporaryDirectory() as temp:
        base=Path(temp)/'base.zip';doc=envelope(base,sharepoint_site=site)
        with ZipFile(base) as z:entries={n:json.loads(z.read(n)) for n in z.namelist()}
    doc['properties']['displayName']=NAME;doc['properties']['definition']['actions']=actions(site,doc['name'])
    for n in entries:
        if n.endswith('/definition.json'):entries[n]=doc
    entries['manifest.json']['details'].update(displayName=NAME+'-package',description='Issue 47 read-only effective permission preflight. No list/schema/item writes; fixture not created.')
    for item in entries['manifest.json']['resources'].values():
        if item['type']=='Microsoft.Flow/flows':item['details']['displayName']=NAME
    output.parent.mkdir(parents=True,exist_ok=True)
    with ZipFile(output,'x',ZIP_DEFLATED) as z:
        for n,value in entries.items():z.writestr(n,json.dumps(value,indent=2)+'\n')
    review={'sourceTicket':47,'packageBuildId':doc['name'],'flowName':NAME,'readOnly':True,'fixtureCreated':False,'writes':0,
        'actions':measure(doc['properties']['definition']['actions'])['actions'],'maximumActionDepth':1,
        'limits':{'actions':500,'nesting':8},'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),
        'connection':'Select existing working SharePoint connection; no new grant/connector/licence.','tenantResult':'NOT_IMPORTED_NOT_TESTED'}
    output.with_suffix('.definition.json').write_bytes((json.dumps(doc,indent=2)+'\n').encode('utf-8'))
    output.with_suffix('.review.json').write_bytes((json.dumps(review,indent=2)+'\n').encode('utf-8'))
    return review


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    print(json.dumps(build_package(args.output),indent=2))


if __name__=='__main__':main()
