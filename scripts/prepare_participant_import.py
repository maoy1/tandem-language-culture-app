"""Read-only Excel inspection and reviewed #48 import-plan preparation.

Python is optional local preparation only. Tenant reads/writes use the separate
standard-SharePoint Power Automate helper. Never uploads or changes the workbook.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import unicodedata
from xml.etree import ElementTree as ET
from zipfile import ZipFile

NS={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
REL='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
SITE='https://reedelsevier.sharepoint.com/sites/OG-TandemOrg'
EXPECTED={'A':'ID','D':'Email','E':'Name','G':'Please leave your name and Email',
          'N':'Is your learning focus:', 'P':'Which Language/Culture would you like to learn?',
          'Q':'Which Language/Culture would you like to learn?2',
          'R':'Which Language/Culture would you love to share?'}
EMAIL=re.compile(r'(?<![\w.+-])[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}(?![\w.-])')


def norm(value):
    return ' '.join(unicodedata.normalize('NFKC',str(value or '')).split()).casefold()


def digest(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def read_workbook(path, sheet=None):
    """Small bounded OOXML reader; no formula evaluation or external links."""
    path=Path(path)
    with ZipFile(path) as z:
        if sum(i.file_size for i in z.infolist())>25_000_000:raise ValueError('Workbook exceeds 25 MB uncompressed')
        strings=[]
        if 'xl/sharedStrings.xml' in z.namelist():
            strings=[''.join(t.text or '' for t in item.iter('{'+NS['s']+'}t')) for item in ET.fromstring(z.read('xl/sharedStrings.xml'))]
        links={r.attrib['Id']:r.attrib['Target'] for r in ET.fromstring(z.read('xl/_rels/workbook.xml.rels')) if r.get('TargetMode')!='External'}
        sheets=ET.fromstring(z.read('xl/workbook.xml')).findall('s:sheets/s:sheet',NS)
        selected=[s for s in sheets if sheet is None or s.get('name')==sheet]
        if len(selected)!=1:raise ValueError('Select exactly one worksheet with --sheet')
        selected=selected[0];target=links[selected.get('{'+REL+'}id')]
        target=target.lstrip('/') if target.startswith('/') else 'xl/'+target
        if '..' in PurePosixPath(target).parts:raise ValueError('Unexpected worksheet path')
        xml=ET.fromstring(z.read(target));rows=[];formula_cells=[]
        for row in xml.findall('s:sheetData/s:row',NS):
            values={}
            for c in row.findall('s:c',NS):
                address=c.get('r','');col=re.sub(r'\d','',address)
                if c.find('s:f',NS) is not None:formula_cells.append(address)
                value=c.findtext('s:v','',NS)
                if c.get('t')=='s':value=strings[int(value)] if value else ''
                elif c.get('t')=='inlineStr':value=''.join(t.text or '' for t in c.iter('{'+NS['s']+'}t'))
                if value:values[col]=value.strip()
            if values:rows.append({'excelRow':int(row.get('r')), 'values':values})
        if not rows:raise ValueError('Empty worksheet')
        headers=rows.pop(0)['values']
        for col,name in EXPECTED.items():
            if norm(headers.get(col))!=norm(name):raise ValueError(f'Unexpected column {col}; expected {name}')
        if len(rows)>250:raise ValueError('Maximum 250 source responses per reviewed batch')
        if formula_cells:raise ValueError('Formula cells require a values-only reviewed export; cached values are not trusted')
        profile_hash=digest([{'id':r['values'].get('A'),'profile':{c:r['values'].get(c,'') for c in 'HNOPQR'}} for r in rows])
        return {'sourceSha256':hashlib.sha256(path.read_bytes()).hexdigest(),'profileRowsSha256':profile_hash,
                'sheet':selected.get('name'),'headers':headers,'rows':rows,
                'externalLinks':any(n.startswith('xl/externalLinks/') for n in z.namelist()),
                'tables':[n for n in z.namelist() if re.fullmatch(r'xl/tables/table\d+\.xml',n)]}


def source_email(values):
    # Email column first; free-text identity can supply one explicit address.
    candidates={m.casefold() for col in ('D','G') for m in EMAIL.findall(values.get(col,''))}
    return next(iter(candidates)) if len(candidates)==1 else None


def inspect(book):
    rows=book['rows'];ids=Counter(r['values'].get('A','') for r in rows)
    return {'kind':'TandemParticipantWorkbookInspection','sourceTicket':48,
            'sourceSha256':book['sourceSha256'],'profileRowsSha256':book['profileRowsSha256'],
            'sheet':book['sheet'],'responseCount':len(rows),'sourceRange':f"A1:U{max((r['excelRow'] for r in rows),default=1)}",
            'identityColumnNonblank':{col:sum(bool(r['values'].get(col)) for r in rows) for col in ('D','E','G')},
            'rowsWithOneExplicitEmail':sum(source_email(r['values']) is not None for r in rows),
            'rowsWithoutProfileDetails':sum(not any(r['values'].get(c) for c in 'NOPQR') for r in rows),
            'duplicateResponseIds':{k:v for k,v in ids.items() if v>1},'missingResponseIds':ids.get('',0),
            'profileValues':{role:sorted({r['values'].get(c) for r in rows for c in columns if r['values'].get(c)}) for role,columns in [('learn','PQ'),('share','R')]},
            'ignoredSourceColumns':['B','C','F','H','I','J','K','L','M','S','T'],
            'notes':['Source ID is a response key, never a SharePoint Participant ID.',
                     'No timezone is inferred from city/country; no group-size preference is imported.',
                     'Reconfirmation-only responses need the older source or explicit exclusion.',
                     'Historical availability, culture roles and free text require review; no fuzzy matching.',
                     'Comments are not copied without an explicit per-row opt-in.'],
            'readOnly':True,'writes':0,'externalLinks':book['externalLinks'],'tableCount':len(book['tables'])}


def mapping_template(book):
    report=inspect(book)
    return {'kind':'TandemParticipantImportMapping','contractVersion':1,
            'profileRowsSha256':book['profileRowsSha256'],
            'availabilityPolicy':{'reviewed':False,'ParticipationStatus':None,'OpenToConnections':None},
            'learn':{value:{'reviewed':False,'languageIds':[],'cultureIds':[]} for value in report['profileValues']['learn']},
            'share':{value:{'reviewed':False,'languageIds':[],'cultureIds':[]} for value in report['profileValues']['share']},
            'rows':{r['values'].get('A',f"missing:{r['excelRow']}"):{'identityEmail':None,'exclude':False,'reason':'','includeComments':False} for r in book['rows']}}


def positive_id(value):return type(value) is int and value>0


def catalogue_ids(snapshot,role):
    result=set()
    for row in snapshot[role]:
        value=row.get('Id',row.get('ID'))
        if positive_id(value) and row.get('Active') is True:result.add(value)
    return result


def plan(book,mapping,snapshot):
    if mapping.get('kind')!='TandemParticipantImportMapping' or mapping.get('contractVersion')!=1:raise ValueError('Unsupported mapping contract')
    if mapping.get('profileRowsSha256')!=book['profileRowsSha256']:raise ValueError('Profile rows changed; regenerate and review mappings')
    if snapshot.get('kind')!='TandemParticipantImportSnapshot' or snapshot.get('collectionComplete') is not True or snapshot.get('targetSite')!=SITE:
        raise ValueError('Need a complete current import-helper snapshot from the intended site')
    for role in ('language','culture','users','participants'):
        if not isinstance(snapshot.get(role),list):raise ValueError('Snapshot missing '+role)
    languages,cultures=catalogue_ids(snapshot,'language'),catalogue_ids(snapshot,'culture')
    responses=Counter(r['values'].get('A','') for r in book['rows']);prepared=[];outcomes=[]
    for source in book['rows']:
        raw=source['values'];key=raw.get('A','');override=mapping.get('rows',{}).get(key,{})
        result={'sourceKey':'response:'+key,'excelRow':source['excelRow'],'errors':[]};errors=result['errors']
        if not key or responses[key]!=1:errors.append('MISSING_OR_DUPLICATE_RESPONSE_ID')
        if override.get('exclude') is True and override.get('reviewed') is True and str(override.get('reason','')).strip() and not errors:
            result.update(status='EXCLUDED_REVIEWED',reason=override['reason']);outcomes.append(result);continue
        email=override.get('identityEmail') or source_email(raw)
        users=[u for u in snapshot['users'] if email and norm(u.get('Email'))==norm(email)]
        if len(users)!=1 or not positive_id(users[0].get('Id',users[0].get('ID'))) or not users[0].get('LoginName'):
            errors.append('IDENTITY_NOT_UNIQUELY_RESOLVED');user={}
        else:user=users[0]
        user_id=user.get('Id',user.get('ID'))
        existing=[r for r in snapshot['participants'] if user_id and r.get('ParticipantaccountId')==user_id]
        result['sharepointUserId']=user_id
        if len(existing)>1:errors.append('DUPLICATE_TARGET_ACCOUNT')
        if len(existing)==1 and not errors:
            result.update(status='EXISTING_PRESERVED',participantId=existing[0].get('Id',existing[0].get('ID')));outcomes.append(result);continue
        fields={'teachIds':[],'learnIds':[],'shareCultureIds':[],'learnCultureIds':[]}
        for column,role,lang,culture in [('P','learn','learnIds','learnCultureIds'),('Q','learn','learnIds','learnCultureIds'),('R','share','teachIds','shareCultureIds')]:
            value=raw.get(column,'')
            if not value:continue
            match=mapping.get(role,{}).get(value,{})
            if match.get('reviewed') is not True:
                errors.append('UNREVIEWED_SELECTION:'+column);continue
            for name,dest,allowed in [('languageIds',lang,languages),('cultureIds',culture,cultures)]:
                ids=match.get(name,[])
                if not isinstance(ids,list) or not all(positive_id(i) and i in allowed for i in ids):errors.append('INVALID_OR_INACTIVE_CATALOGUE:'+column+':'+name)
                else:fields[dest]+=ids
            if not match.get('languageIds') and not match.get('cultureIds') and not match.get('reason'):errors.append('EMPTY_MAPPING_NEEDS_REASON:'+column)
        fields={k:sorted(set(v)) for k,v in fields.items()}
        if not any(fields.values()):errors.append('NO_PROFILE_SELECTIONS')
        policy=override.get('availabilityPolicy',mapping.get('availabilityPolicy',{}))
        if policy.get('reviewed') is not True or policy.get('ParticipationStatus') not in ('Active','Paused','Inactive') or type(policy.get('OpenToConnections')) is not bool:
            errors.append('AVAILABILITY_POLICY_NOT_REVIEWED')
        title=user.get('Title')
        if not isinstance(title,str) or not title.strip() or len(title)>255:errors.append('INVALID_ACCOUNT_DISPLAY_NAME')
        if errors:result['status']='BLOCKED'
        else:
            row={'sourceKey':result['sourceKey'],'accountLogin':user['LoginName'],'sharepointUserId':user_id,'Title':title,**fields,
                 'ParticipationStatus':policy['ParticipationStatus'],'OpenToConnections':policy['OpenToConnections'],'Learningfocus':raw.get('N','')}
            if override.get('includeComments') is True:row['Comments']=raw.get('U','')
            prepared.append(row);result['status']='READY_CREATE'
        outcomes.append(result)
    accounts=Counter(r.get('sharepointUserId') for r in outcomes if r.get('sharepointUserId'))
    duplicate_accounts={k for k,v in accounts.items() if v>1}
    for result in outcomes:
        if result.get('sharepointUserId') in duplicate_accounts:
            result['status']='BLOCKED';result['errors'].append('DUPLICATE_SOURCE_ACCOUNT_RECONCILE')
    prepared=[r for r in prepared if r['sharepointUserId'] not in duplicate_accounts]
    counts=dict(Counter(r['status'] for r in outcomes))
    envelope={'kind':'TandemParticipantImportPlan','contractVersion':1,'sourceTicket':48,'sourceSha256':book['sourceSha256'],
              'targetSite':SITE,'readyForApply':bool(prepared) and not counts.get('BLOCKED',0),'rows':prepared}
    return envelope,{'kind':'TandemParticipantImportPreparation','sourceTicket':48,'sourceSha256':book['sourceSha256'],
                     'snapshotSha256':digest(snapshot),'responseCount':len(book['rows']),'counts':counts,'rows':outcomes,
                     'readyForApply':envelope['readyForApply'],'writes':0,'nativeImport':'NOT RUN'}


def save(path,data):
    path=Path(path)
    if path.exists():raise FileExistsError('Preserve existing output: '+str(path))
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('mode',choices=['inspect','plan'])
    parser.add_argument('--workbook',type=Path,required=True);parser.add_argument('--sheet');parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--mapping',type=Path);parser.add_argument('--snapshot',type=Path);args=parser.parse_args()
    book=read_workbook(args.workbook,args.sheet)
    if args.mode=='inspect':
        report=inspect(book);save(args.output/'inspection.json',report);save(args.output/'mapping-template.json',mapping_template(book))
        print(json.dumps({k:report[k] for k in ['responseCount','rowsWithOneExplicitEmail','rowsWithoutProfileDetails','sourceSha256','writes']}))
    else:
        if not args.mapping or not args.snapshot:parser.error('plan requires --mapping and --snapshot')
        payload,report=plan(book,json.loads(args.mapping.read_text(encoding='utf-8-sig')),json.loads(args.snapshot.read_text(encoding='utf-8-sig')))
        save(args.output/'import-plan.json',payload);save(args.output/'preparation-report.json',report)
        print(json.dumps({'readyForApply':payload['readyForApply'],'counts':report['counts'],'writes':0}))


if __name__=='__main__':main()
