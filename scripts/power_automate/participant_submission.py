"""Build #61 from an inspected legacy export; local packaging only."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4
from zipfile import ZIP_DEFLATED, ZipFile

from .build_import_probe import build_package as probe_package

ROOT = Path(__file__).resolve().parents[2]
CONNECTOR = 'shared_sharepointonline'
API = '/providers/Microsoft.PowerApps/apis/'+CONNECTOR
NAME = 'Tandem – Participant submission v2'
FIELDS = ['Teachlanguages', 'Learnlanguages', 'ShareCultures', 'LearnCultures']


def walk(actions, depth=1):
    for name, action in actions.items():
        yield name, action, depth
        yield from walk(action.get('actions', {}), depth+1)
        yield from walk(action.get('else', {}).get('actions', {}), depth+1)


def gate(definition):
    rows = list(walk(definition['actions']))
    metrics = {'actionDefinitions':len(rows), 'maximumNesting':max(r[2] for r in rows)}
    if metrics['actionDefinitions'] > 500 or metrics['maximumNesting'] > 8:
        raise ValueError('Flow exceeds 500 actions / 8 nesting levels')
    return metrics


def source_definition(source):
    with ZipFile(source) as archive:
        names = [n for n in archive.namelist() if n.endswith('/definition.json')]
        if len(names) != 1:
            raise ValueError('Expected exactly one exported flow')
        doc = json.loads(archive.read(names[0]))
    definition = doc['properties']['definition']
    if len(definition['triggers']) != 1:
        raise ValueError('Expected single SharePoint event trigger')
    trigger = next(iter(definition['triggers'].values()))
    host = trigger['inputs']['host']
    if host['operationId'] != 'GetOnUpdatedItems' or host['connectionName'] != CONNECTOR:
        raise ValueError('Unsupported trigger/connection; inspect before packaging')
    if trigger.get('conditions') or trigger.get('runtimeConfiguration'):
        raise ValueError('Nonbaseline trigger settings need explicit review')
    current = definition['actions'].get('Get_item', {})
    p = current.get('inputs', {}).get('parameters', {})
    if p.get('id') != "@triggerBody()?['ID']" or current['inputs']['host']['operationId'] != 'GetItem':
        raise ValueError('Current-item reference differs from inspected source')
    if any(p.get(k) != trigger['inputs']['parameters'].get(k) for k in ['dataset','table']):
        raise ValueError('Current read and event mapping differ')
    return doc


def after(name): return {name:['Succeeded']} if name else {}


def http(site, uri, previous=None, body=None, etag=None):
    params = {'dataset':site, 'parameters/method':'GET' if body is None else 'POST',
              'parameters/uri':uri, 'parameters/headers':{'Accept':'application/json;odata=verbose'}}
    if body is not None:
        params['parameters/headers'].update({'Content-Type':'application/json;odata=verbose',
                                            'X-HTTP-Method':'MERGE', 'IF-MATCH':etag})
        params['parameters/body'] = body
    return {'type':'OpenApiConnection','runAfter':after(previous),'inputs':{
        'parameters':params,'host':{'apiId':API,'connectionName':CONNECTOR,'operationId':'HttpRequest'},
        'authentication':"@parameters('$authentication')",'retryPolicy':{'type':'none'}}}


def compose(value, previous=None):
    return {'type':'Compose','inputs':value,'runAfter':after(previous)}


def parse(content, schema, previous):
    return {'type':'ParseJson','inputs':{'content':content,'schema':schema},'runAfter':after(previous)}


def condition(expr, yes, no=None, previous=None):
    return {'type':'If','expression':'@'+expr,'actions':yes,
            'else':{'actions':no or {}},'runAfter':after(previous)}


def failed(code):
    return {'type':'Terminate','inputs':{'runStatus':'Failed','runError':{'code':code,'message':code}},'runAfter':{}}


def build_definition(original, mapping, build_id):
    trigger = next(iter(original['properties']['definition']['triggers'].values()))
    params = trigger['inputs']['parameters']; site = params['dataset']; people = mapping['lists']['participants']['listId']
    if params['table'].lower() != people.lower():
        raise ValueError('Source participant list differs from verified schema')
    for field in FIELDS+['Participantaccount','Timezone','Status']:
        if not any(f['internalName']==field for f in mapping['lists']['participants']['fields'].values()):
            raise ValueError('Verified field missing: '+field)
    base = f"_api/web/lists(guid'{people}')/items("
    item_uri = "@concat('"+base.replace("'","''")+"',string(triggerBody()?['ID']),')')"
    selected = 'Id,ParticipantaccountId,TimezoneId,Status,'+','.join(f+'Id' for f in FIELDS)
    read_uri = item_uri[:-1]+",'?$select="+selected+"')"
    actions = {'Read_current':http(site,read_uri)}
    id_schema = {'type':'integer','minimum':1}
    props = {'Id':id_schema,'ParticipantaccountId':{'type':['integer','null']},
             'TimezoneId':{'type':['integer','null']},'Status':{'type':['string','null']},
             '__metadata':{'type':'object','required':['etag','type'],'properties':{
                 'etag':{'type':'string','minLength':1},'type':{'type':'string','minLength':1}}}}
    for f in FIELDS:
        props[f+'Id']={'type':'object','required':['results'],'properties':{
            'results':{'type':'array','items':id_schema}}}
    actions['Current_item'] = parse("@body('Read_current')?['d']",{'type':'object','required':list(props),'properties':props},'Read_current')
    previous='Current_item'
    for role in ['language','culture','timezone']:
        list_id=mapping['lists'][role]['listId']
        n='Read_'+role
        actions[n]=http(site,f"_api/web/lists(guid'{list_id}')/items?$select=Id,Active&$top=5000",previous)
        schema={'type':'object','required':['results'],'properties':{
            '__next':{'type':['string','null']},'results':{'type':'array','items':{
                'type':'object','required':['Id','Active'],'properties':{'Id':id_schema,'Active':{'type':'boolean'}}}}}}
        p='Parsed_'+role; actions[p]=parse(f"@body('{n}')?['d']",schema,n)
        q='Active_'+role; actions[q]={'type':'Query','runAfter':after(p),'inputs':{
            'from':f"@body('{p}')?['results']",'where':"@equals(item()?['Active'],true)"}}
        s='IDs_'+role; actions[s]={'type':'Select','runAfter':after(q),'inputs':{
            'from':f"@body('{q}')",'select':"@item()?['Id']"}}
        previous=s
    complete=[f"empty(body('Parsed_{r}')?['__next'])" for r in ['language','culture','timezone']]
    complete += ["equals(body('Current_item')?['Id'],int(triggerBody()?['ID']))",
                 "not(equals(body('Current_item')?['__metadata']?['etag'],'*'))"]
    actions['Require_complete_reads']=condition('and('+','.join(complete)+')',{},
        {'Fail_incomplete_reads':failed('INCOMPLETE_OR_MISMATCHED_READ')},previous)
    actions['Selected_language']=compose("@union(body('Current_item')?['TeachlanguagesId']?['results'],body('Current_item')?['LearnlanguagesId']?['results'])",'Require_complete_reads')
    actions['Selected_culture']=compose("@union(body('Current_item')?['ShareCulturesId']?['results'],body('Current_item')?['LearnCulturesId']?['results'])",'Selected_language')
    valid=["greater(coalesce(body('Current_item')?['ParticipantaccountId'],0),0)",
           "or(not(empty(outputs('Selected_language'))),not(empty(outputs('Selected_culture'))))",
           "or(equals(body('Current_item')?['TimezoneId'],null),contains(body('IDs_timezone'),body('Current_item')?['TimezoneId']))"]
    for role in ['language','culture']:
        valid.append(f"equals(length(intersection(outputs('Selected_{role}'),body('IDs_{role}'))),length(outputs('Selected_{role}')))" )
    actions['Profile_valid']=compose('@and('+','.join(valid)+')','Selected_culture')
    actions['Desired_status']=compose("@if(outputs('Profile_valid'),'Active','Needs review')",'Profile_valid')
    body={'__metadata':{'type':"@body('Current_item')?['__metadata']?['type']"},'Status':"@outputs('Desired_status')"}
    patch=http(site,item_uri,body=body,etag="@body('Current_item')?['__metadata']?['etag']")
    verify=http(site,read_uri,'Update_validation_status')
    check=condition("equals(body('Verify_status')?['d']?['Status'],outputs('Desired_status'))",{},
        {'Fail_readback':failed('STATUS_READBACK_MISMATCH')},'Verify_status')
    actions['Status_changed']=condition("not(equals(body('Current_item')?['Status'],outputs('Desired_status')))",{
        'Update_validation_status':patch,'Verify_status':verify,'Require_status_readback':check},previous='Desired_status')
    actions['Validation_report']=compose({'kind':'ParticipantSubmissionValidation','schemaVersion':1,'sourceTicket':61,
        'packageBuildId':build_id,'runReference':"@workflow()?['run']?['name']",'itemId':"@body('Current_item')?['Id']",
        'valid':"@outputs('Profile_valid')",'status':"@outputs('Desired_status')",
        'statusChanged':"@not(equals(body('Current_item')?['Status'],outputs('Desired_status')))",
        'result':"@if(equals(body('Current_item')?['Status'],outputs('Desired_status')),'NO_CHANGE','STATUS_UPDATED')"},'Status_changed')
    definition=deepcopy(original['properties']['definition'])
    definition['actions']=actions
    # Preserve actual event name, recurrence, splitOn and exact site/list/ID semantics.
    definition['triggers']=deepcopy(original['properties']['definition']['triggers'])
    gate(definition)
    return definition


def build_package(source, output, mapping_path=None):
    source,output=Path(source),Path(output)
    if output.exists(): raise FileExistsError(output)
    mapping=json.loads(Path(mapping_path or ROOT/'config/tenant_schema_mapping.json').read_text(encoding='utf-8'))
    original=source_definition(source); build_id=str(uuid4())
    definition=build_definition(original,mapping,build_id)
    site=next(iter(definition['triggers'].values()))['inputs']['parameters']['dataset']
    with TemporaryDirectory() as temp:
        probe=Path(temp)/'probe.zip'; probe_package(probe,sharepoint_site=site)
        with ZipFile(probe) as archive: entries={n:json.loads(archive.read(n)) for n in archive.namelist()}
    name=next(n for n in entries if n.endswith('/definition.json'))
    document=entries[name]; document['properties']['displayName']=NAME; document['properties']['definition']=definition
    manifest=entries['manifest.json']; manifest['details'].update(displayName='TandemParticipantSubmission-v2',description='Issue 61 event-driven validation; controlled cutover required; changed Status only.')
    for resource in manifest['resources'].values():
        if resource['type']=='Microsoft.Flow/flows': resource['details']['displayName']=NAME
    output.parent.mkdir(parents=True,exist_ok=True)
    with ZipFile(output,'x',ZIP_DEFLATED) as archive:
        for n,payload in entries.items(): archive.writestr(n,json.dumps(payload,indent=2)+'\n')
    review={'sourceTicket':61,'packageBuildId':build_id,'sourceExportSha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'packageSha256':hashlib.sha256(output.read_bytes()).hexdigest(),'displayName':NAME,
        'sourceTriggerPreserved':definition['triggers']==original['properties']['definition']['triggers'],
        'sourceConnectionNamesCopied':False,'importMode':'Create as new; select existing SharePoint connection; stop old validator before import',
        'tenantResult':'NOT_IMPORTED_NOT_TESTED','appFeedback':'Existing asynchronous save; actual feedback binding not yet inspected',**gate(definition)}
    output.with_suffix('.definition.json').write_text(json.dumps(document,indent=2)+'\n',encoding='utf-8')
    output.with_suffix('.review.json').write_text(json.dumps(review,indent=2)+'\n',encoding='utf-8')
    return review


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',required=True,type=Path); parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args(); print(json.dumps(build_package(args.source,args.output),indent=2))


if __name__=='__main__': main()
