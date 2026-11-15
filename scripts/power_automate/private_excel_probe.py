"""#48 owner-private Excel read proof. No participant writes or identity export.

Owner selects the document library/file/table on the supplied Read_workbook
action once in the native designer. The workbook itself never leaves the tenant.
"""
from __future__ import annotations
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4
from zipfile import ZipFile, ZIP_DEFLATED
from .build_import_probe import build_package as base_package
from .activation_graph import analyze
from .schema_audit import measure, ALL

ROOT=Path(__file__).resolve().parents[2]
NAME='TandemPrivateExcelReadProbe'
CONNECTOR='shared_excelonlinebusiness'
API='/providers/Microsoft.PowerApps/apis/'+CONNECTOR
EMAIL='Email'
OTHER='Please leave your name and Email'
SECURE={'secureData':{'properties':['inputs','outputs']}}
SECURE_INPUTS={'secureData':{'properties':['inputs']}}


def validate_secure_data(action_map):
    """Native Compose/ParseJson/Response only support Secure Inputs.

    For these three action types, Secure Inputs also conceals their outputs.
    Downstream row-bearing actions still need their own explicit protection.
    """
    for name,action in action_map.items():
        properties=set(action.get('runtimeConfiguration',{}).get('secureData',{}).get('properties',[]))
        if not properties<={'inputs','outputs'}:raise ValueError('Unsupported secureData values: '+name)
        if action['type'] in {'Compose','ParseJson','Response'} and 'outputs' in properties:
            raise ValueError('Secure Outputs is unsupported for '+action['type']+': '+name)
        validate_secure_data(action.get('actions',{}))
        validate_secure_data(action.get('else',{}).get('actions',{}))


def actions(site,build_id):
    result={
        'Read_workbook':{'type':'OpenApiConnection','runAfter':{},'runtimeConfiguration':deepcopy(SECURE),
            'inputs':{'host':{'apiId':API,'connectionName':CONNECTOR,'operationId':'GetItems'},
                      'parameters':{'source':site,'drive':'SELECT_DOCUMENT_LIBRARY','file':'SELECT_PRIVATE_WORKBOOK','table':'Table1','$top':251},
                      'authentication':"@parameters('$authentication')",'retryPolicy':{'type':'none'}}},
        'Private_rows':{'type':'ParseJson','runAfter':{'Read_workbook':['Succeeded']},'runtimeConfiguration':deepcopy(SECURE_INPUTS),
            'inputs':{'content':"@body('Read_workbook')?['value']",'schema':{'type':'array','maxItems':251,'items':{'type':'object'}}}},
    }
    # Queries carry complete private rows internally, so secure BOTH directions.
    for name,where in [
        ('Private_email_present',f"and(not(empty(trim(string(item()?['{EMAIL}'])))),not(equals(toLower(trim(string(item()?['{EMAIL}']))),'anonymous')))"),
        ('Private_identity_text_present',f"not(empty(trim(string(item()?['{OTHER}']))))")]:
        result[name]={'type':'Query','runAfter':{'Private_rows':['Succeeded']},'runtimeConfiguration':deepcopy(SECURE),
                      'inputs':{'from':"@body('Private_rows')",'where':'@'+where}}
    count="length(coalesce(body('Private_rows'),json('[]')))"
    read_ok="equals(actions('Read_workbook')?['status'],'Succeeded')"
    parsed="equals(actions('Private_rows')?['status'],'Succeeded')"
    bound="and(less("+count+",251),empty(body('Read_workbook')?['@odata.nextLink']),empty(body('Read_workbook')?['odata.nextLink']))"
    expected="equals("+count+",coalesce(triggerBody()?['ExpectedRows'],206))"
    first="first(union(coalesce(body('Private_rows'),json('[]')),createArray(json('{}'))))"
    columns=f"and(contains({first},'{EMAIL}'),contains({first},'{OTHER}'))"
    inspected="and(equals(actions('Private_email_present')?['status'],'Succeeded'),equals(actions('Private_identity_text_present')?['status'],'Succeeded'))"
    complete=f'and({read_ok},{parsed},{inspected},{bound},{expected},{columns})'
    result['Private_read_report']={'type':'Compose','runAfter':{n:ALL for n in ['Private_rows','Private_email_present','Private_identity_text_present']},
        'inputs':{'kind':NAME,'schemaVersion':1,'sourceTicket':48,'packageBuildId':build_id,
                  'runReference':"@workflow()?['run']?['name']",'success':'@'+complete,
                  'excelStatusCode':"@coalesce(outputs('Read_workbook')?['statusCode'],0)",
                  'code':f"@if(not({read_ok}),'EXCEL_READ_FAILED',if(not({parsed}),'INVALID_TABLE_RESPONSE',if(not({inspected}),'PRIVATE_INSPECTION_FAILED',if(not({bound}),'INCOMPLETE_OR_TOO_LARGE',if(not({expected}),'ROW_COUNT_MISMATCH',if(not({columns}),'IDENTITY_HEADERS_MISMATCH','OK'))))))",
                  'rowCount':'@'+count,'expectedRows':"@coalesce(triggerBody()?['ExpectedRows'],206)",
                  'identityHeadersPresent':'@'+columns,
                  'rowsWithEmailText':"@length(coalesce(body('Private_email_present'),json('[]')))",
                  'rowsWithOtherIdentityText':"@length(coalesce(body('Private_identity_text_present'),json('[]')))",
                  'participantWrites':0,'identityValuesIncluded':False,
                  'accountResolution':'NOT_ATTEMPTED','importDryRun':'NOT_RUN','importApply':'NOT_RUN'}}
    return result


def build_package(output):
    output=Path(output);paths=[output,output.with_suffix('.definition.json'),output.with_suffix('.review.json')]
    if any(p.exists() for p in paths):raise FileExistsError('Preserve existing versioned package and sidecars')
    site=json.loads((ROOT/'config/batch_schema_contract.json').read_text(encoding='utf-8'))['site']
    with TemporaryDirectory(prefix='tandem-private-excel-') as directory:
        base=Path(directory)/'base.zip';doc=base_package(base)
        with ZipFile(base) as z:entries={n:json.loads(z.read(n)) for n in z.namelist()}
    display_name=NAME+' v2'
    props=doc['properties'];props['displayName']=display_name
    props['connectionReferences']={CONNECTOR:{'connectionName':'IMPORT_SELECT_EXISTING_EXCEL_CONNECTION','source':'Embedded','id':API,
        'tier':'NotSpecified','apiName':'excelonlinebusiness','isProcessSimpleApiReferenceConversionAlreadyDone':False}}
    definition=props['definition']
    definition['triggers']={'manual':{'type':'Request','kind':'Button','inputs':{'schema':{'type':'object','properties':{
        'ExpectedRows':{'type':'integer','minimum':1,'maximum':250,'default':206,'title':'ExpectedRows','x-ms-content-hint':'NUMBER'}},'required':[]}},
        'runtimeConfiguration':{'concurrency':{'runs':1}}}}
    definition['actions']=actions(site,doc['name'])
    validate_secure_data(definition['actions'])
    metrics=measure(definition['actions'])
    if analyze(definition):raise ValueError('Invalid dependency graph')
    manifest=entries['manifest.json'];resource=next(k for k,v in manifest['resources'].items() if v['type']=='Microsoft.Flow/flows')
    api_key,connection_key=str(uuid4()),str(uuid4())
    manifest['details'].update(displayName=display_name+'-package',description='#48 owner-private read proof v2; native-compatible ParseJson Secure Inputs; no participant writes. Native recheck pending.')
    manifest['resources'][resource]['details']['displayName']=display_name
    manifest['resources'][resource]['dependsOn']=[api_key,connection_key]
    manifest['resources'][api_key]={'id':API,'name':CONNECTOR,'type':'Microsoft.PowerApps/apis','suggestedCreationType':'Existing','details':{'displayName':'Excel Online (Business)'},'configurableBy':'System','hierarchy':'Child','dependsOn':[]}
    manifest['resources'][connection_key]={'type':'Microsoft.PowerApps/apis/connections','suggestedCreationType':'Existing','creationType':'Existing',
        'details':{'displayName':'Select existing owner Excel Online (Business) connection'},'configurableBy':'User','hierarchy':'Child','dependsOn':[api_key]}
    for name in list(entries):
        if name.endswith('/definition.json'):entries[name]=doc
        elif name.endswith('/apisMap.json'):entries[name]={CONNECTOR:api_key}
        elif name.endswith('/connectionsMap.json'):entries[name]={CONNECTOR:connection_key}
    output.parent.mkdir(parents=True,exist_ok=True)
    with ZipFile(output,'x',ZIP_DEFLATED) as z:
        for name,value in entries.items():z.writestr(name,json.dumps(value,indent=2)+'\n')
    review={'sourceTicket':48,'artifactVersion':'v2','packageBuildId':doc['name'],'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),**metrics,
        'purpose':'Private read proof only; not the revised importer. No participant/list/account writes.',
        'connection':'Existing owner Excel Online (Business), Embedded; no SharePoint or other connection required for this probe.',
        'configurationRequired':{'action':'Read_workbook','location':site,'documentLibrary':'Select actual library in designer',
            'file':'Choose original workbook privately using file picker','table':'Choose actual source table; Table1 is only the anonymized-source default'},
        'inputs':{'ExpectedRows':'206 for original reviewed dataset; actual expected count required, maximum250'},
        'outputs':'Private_read_report Compose only: counts/status/error codes. Do not share private action settings or raw workbook rows.',
        'privacy':'Read_workbook and both row queries explicitly secure inputs/outputs. Private_rows uses supported Secure Inputs only, which also hides ParseJson outputs per Microsoft semantics. Report contains counts/codes only; native masking recheck pending.',
        'supersedes':'v1 save failed with InvalidSecureDataConfiguration on Private_rows ParseJson outputs. No private read PASS is transferred.',
        'nativeImport':'NOT RUN','nativeFileConfiguration':'NOT RUN','nativeExcelRead':'NOT RUN',
        'limitations':['Connection Connected does not prove file access, DLP or source/table mapping.',
            'Read access may require workbook edit permission according to Microsoft connector documentation; do not grant it automatically.',
            'No workbook row modifications requested; Excel connector may still record a service-managed file version.',
            'Original expected row count,251-row cap and nextlink checks reject incomplete/mismatched datasets.',
            'Email-text counts do not prove valid/resolved accounts or import readiness.'],
        'instructions':['Import as Create as new; select existing Excel connection. Keep helper owner-operated.',
            'Edit supplied Read_workbook action: select Tandem site,actual Document Library,private workbook and Table. No new actions are needed.',
            'Save and run with ExpectedRows206 (or verified actual count). Share only Private_read_report outputs.',
            'Expect success=true,code=OK,rowCount=206,identityValuesIncluded=false,participantWrites=0. Any failure stops dependent import work.',
            'Do not run Apply on the old v1 importer for this private route. Disable/remove only this disposable probe after evidence is retained.'],
        'driftReview81':'New input-adapter read proof only. No shared/core schema/rules/IO/package/app changes. All identity resolution and participant writes remain unimplemented/unverified for private route.'}
    paths[1].write_bytes((json.dumps(doc,indent=2)+'\n').encode())
    paths[2].write_bytes((json.dumps(review,indent=2)+'\n').encode())
    return doc,review


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    _,review=build_package(args.output)
    print(json.dumps({k:review[k] for k in ['packageBuildId','sha256','actions','maximumActionDepth','nativeExcelRead']}))
