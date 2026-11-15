"""#48 matching-workbook adapter and reviewed historical group migration.

One-time local utility, not a participant runtime. No credential acquisition.
Migration source/episode rows explicitly attest imported historical membership;
they do not claim an in-app invitation or historic response timestamp.
"""
from collections import Counter, defaultdict
from copy import deepcopy
from datetime import datetime, timezone
import csv
import hashlib
import json
from pathlib import PurePosixPath
import re
from xml.etree import ElementTree as ET
from zipfile import ZipFile

SHEETS={'active':'Active','paused':'Paused','non active':'Inactive'}
PARTICIPANT_META=['ImportKey','SourceSheet','SourceRow','SourceID','ReviewNotes']
GROUP_COLUMNS=['MigrationKey','Title','ExchangeType','LanguageFocus','CultureFocus','Capacity','State','ImportApproved','ReviewNotes']
MEMBER_COLUMNS=['MigrationKey','ParticipantRef','MembershipStatus','JoinedAt','LeftAt','SourceSheet','SourceRow','SourceStatus','ReviewNotes']
GROUPS='4bf1b37f-edce-40c5-8fa0-36543a2d0cd6'
MEMBERS='db611ec3-7fa3-477a-878e-effbbb195cb8'
REQUESTS='3d17485d-1dac-41f0-a1af-24e45daa4567'
DATE_NOTE='Imported from the previous Tandem programme. Where original dates are unknown, membership dates reflect the migration date. This is not a new invitation.'


def read_sheets(path, api, redact_identities=False):
    """Read selected cell values only; optional metadata inspection skips identity cells."""
    n=api.NS;rel=api.REL
    with ZipFile(path) as z:
        if sum(i.file_size for i in z.infolist())>100_000_000:
            raise api.ImportProblem('Workbook exceeds the local uncompressed-size limit.')
        # Ignore unrelated external-link parts entirely; never resolve/fetch them.
        # An actual formula in a selected imported cell is still refused below.
        ignored_links=sum(s.startswith('xl/externalLinks/') and s.endswith('.xml') for s in z.namelist())
        def xml(name):
            raw=z.read(name)
            if b'<!DOCTYPE' in raw.upper() or b'<!ENTITY' in raw.upper():
                raise api.ImportProblem('Unexpected XML entity declaration.')
            return ET.fromstring(raw)
        strings=[''.join(t.text or '' for t in x.iter('{'+n['s']+'}t')) for x in xml('xl/sharedStrings.xml')] if 'xl/sharedStrings.xml' in z.namelist() else []
        def value(c):
            v=c.findtext('s:v','',n)
            if c.get('t')=='s':return strings[int(v)] if v else ''
            if c.get('t')=='inlineStr':return ''.join(t.text or '' for t in c.iter('{'+n['s']+'}t'))
            return v
        links={x.get('Id'):x.get('Target') for x in xml('xl/_rels/workbook.xml.rels') if x.get('TargetMode')!='External'}
        result=[]
        for sheet in xml('xl/workbook.xml').findall('s:sheets/s:sheet',n):
            name=sheet.get('name')
            # Exclude safety copies before reading their worksheet cells.
            if api.key(name) not in SHEETS:continue
            target=links[sheet.get('{'+rel+'}id')]
            target=target.lstrip('/') if target.startswith('/') else 'xl/'+target
            if '..' in PurePosixPath(target).parts:raise api.ImportProblem('Unexpected worksheet path.')
            rows=xml(target).findall('s:sheetData/s:row',n)
            if not rows:continue
            headers={re.sub(r'\d','',c.get('r','')):value(c).strip() for c in rows[0].findall('s:c',n)}
            header=lambda v:' '.join(v.split()).lower()
            required={'A':'ID','B':'Group that they left' if api.key(name)=='non active' else 'Group','D':'Email','E':'Name','J':'Is your learning focus:',
                      'I':'Which Language/Culture would you like to learn?', 'K':'Which Language/Culture would you love to share?',
                      'O':'Outcome status 2025'}
            if any(header(headers.get(k,''))!=header(v) for k,v in required.items()):
                raise api.ImportProblem('A matching-workbook tab has unexpected columns.')
            data=[]
            for row in rows[1:]:
                number=int(row.get('r'))
                if number>10001:raise api.ImportProblem('Maximum 10,000 rows per current tab.')
                cells={}
                for c in row.findall('s:c',n):
                    col=re.sub(r'\d','',c.get('r',''))
                    if col not in {'A','B','D','E','F','I','J','K','O'}:continue
                    if redact_identities and col in {'D','E'}:continue
                    if c.find('s:f',n) is not None:raise api.ImportProblem('Use values only, not formulas, in imported columns.')
                    v=value(c).strip()
                    if v:cells[col]=v
                # Ignore formatted blank tails and marker-only rows, not real responses.
                if not any(cells.get(k) for k in ['A','D','E','F','I','J','K']):continue
                data.append({'sheet':name,'excelRow':number,'raw':cells})
            result.append({'name':name,'rows':data,'externalLinkPartsIgnored':ignored_links})
        if not result:raise api.ImportProblem('No active/paused/non active matching tabs were found.')
        return result


def migration_key(label):
    normalized=' '.join(label.strip().lower().split())
    return 'migration48:group:'+hashlib.sha256(normalized.encode()).hexdigest()[:20]


def split_groups(text):
    return list(dict.fromkeys(x.strip() for x in re.split(r'[;|\r\n]+',text) if x.strip()))


def extra_mappings(mapping, source, api):
    """Extend only explicit catalogue-name lists; no fuzzy/nationality inference."""
    result=deepcopy(mapping)
    languages={api.key(s):s for s in mapping['catalogueEvidence']['activeLanguageTitles'] if api.key(s)!='any language'}
    for row in source:
        for col,role in [('I','learn'),('K','share')]:
            value=row['raw'].get(col,'');normalized=api.key(value)
            if not normalized or normalized in result['mappings'][role]:continue
            tokens=[s.strip() for s in re.split(r'[,;/&\n]+|\s+and\s+',normalized) if s.strip()]
            if tokens and all(t in languages for t in tokens):
                result['mappings'][role][normalized]={'status':'MAPPED','languageTitles':list(dict.fromkeys(languages[t] for t in tokens)),
                    'cultureTitles':[],'reason':'Explicit list of current concrete language catalogue titles.'}
    return result


def prepare(sheets, mapping, api, scope='all', skip_rows=0):
    wanted={'active'} if scope=='active' else set(SHEETS)
    source=[r for s in sheets if api.key(s['name']) in wanted for r in s['rows']]
    source=source[skip_rows:]
    mapping=extra_mappings(mapping,source,api)
    inputs=[(i,r['excelRow'],{'A':r['raw'].get('A',''),'D':r['raw'].get('D',''),'E':r['raw'].get('E',''),
              'P':r['raw'].get('I',''),'R':r['raw'].get('K',''),'N':r['raw'].get('J','')}) for i,r in enumerate(source,1)]
    people=api.prepare(inputs,mapping)
    ids=Counter(api.key(r['raw'].get('A')) for r in source if r['raw'].get('A'))
    memberships=[];labels={};group_issues=defaultdict(list)
    for person,src in zip(people,source):
        raw=src['raw'];sheet=api.key(src['sheet']);sid=raw.get('A','')
        ref='legacy:'+api.key(sid) if sid and ids[api.key(sid)]==1 else 'row:'+sheet+':'+str(src['excelRow'])
        if sid and ids[api.key(sid)]>1:person['issues'].append('DUPLICATE_SOURCE_ID_REVIEW')
        person['fields']['ParticipationStatus']=SHEETS[sheet]
        person['fields']['OpenToConnections']='Yes' if sheet=='active' else 'No'
        status=api.key(raw.get('O'))
        if sheet=='active' and status not in ('active - matched','waiting list',''):
            person['issues'].append('SOURCE_STATUS_NEEDS_REVIEW')
        person.update(importKey=ref,sourceSheet=src['sheet'],sourceID=sid)
        for label in split_groups(raw.get('B','')):
            token=migration_key(label);labels.setdefault(token,label)
            membership='Active' if sheet=='active' and status=='active - matched' else 'Left' if sheet=='non active' else 'REVIEW'
            issues=[] if membership!='REVIEW' else ['CONFIRM_PAUSED_OR_UNCERTAIN_MEMBERSHIP']
            if 'review' in api.key(label):issues.append('AMBIGUOUS_GROUP_LABEL')
            if issues:group_issues[token].extend(issues)
            memberships.append({'MigrationKey':token,'ParticipantRef':ref,'MembershipStatus':membership,
                'JoinedAt':'','LeftAt':'','SourceSheet':src['sheet'],'SourceRow':str(src['excelRow']),
                'SourceStatus':raw.get('O',''),'ReviewNotes':'; '.join(issues)})
    groups=[]
    languages={api.key(s):s for s in mapping['catalogueEvidence']['activeLanguageTitles'] if api.key(s)!='any language'}
    for token,label in labels.items():
        roster=[m for m in memberships if m['MigrationKey']==token]
        active=sum(m['MembershipStatus']=='Active' for m in roster)
        issues=list(dict.fromkeys(group_issues[token]))
        text=re.sub(r'^[A-Za-z]{1,3}\s*:\s*','',label).strip()
        text=re.sub(r'\s+learning\s+group\s*$','',text,flags=re.I)
        text=re.sub(r'\s*\d+\s*$','',text).strip()
        tokens=[api.key(t) for t in re.split(r'[-/+&,]+',text) if t.strip()]
        focus=list(dict.fromkeys(languages[t] for t in tokens if t in languages))
        if not tokens or len(focus)!=len(set(tokens)):issues.append('REVIEW_GROUP_TYPE_OR_FOCUS')
        if active>3:issues.append('LEGACY_LANGUAGE_GROUP_OVER_CAPACITY')
        if len({m['ParticipantRef'] for m in roster})<2:issues.append('NEED_AT_LEAST_TWO_KNOWN_MEMBERS')
        if not active:issues.append('HISTORICAL_GROUP_REVIEW')
        if len({m['ParticipantRef'] for m in roster})!=len(roster):issues.append('DUPLICATE_MEMBER_SOURCE')
        groups.append({'MigrationKey':token,'Title':label,'ExchangeType':'Language' if focus and 'REVIEW_GROUP_TYPE_OR_FOCUS' not in issues else '',
            'LanguageFocus':'; '.join(focus),'CultureFocus':'','Capacity':str(max(2,active)) if active<=3 else '',
            'State':'Closed','ImportApproved':'No' if issues else 'Yes','ReviewNotes':'; '.join(issues)})
    return {'participants':people,'groups':groups,'memberships':memberships,
            'sourceTabs':[s['name'] for s in sheets if api.key(s['name']) in wanted],
            'externalLinkPartsIgnored':max((s.get('externalLinkPartsIgnored',0) for s in sheets),default=0)}


def write_csv(path,columns,records,api,replace_new=False):
    with path.open('w' if replace_new else 'x',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,columns);writer.writeheader()
        writer.writerows({k:api.excel_safe(r.get(k,'')) for k in columns} for r in records)


def write_bundle(folder,bundle,summary,api):
    api.write_outputs(folder,bundle['participants'],summary)
    # Replace only the file just created by write_outputs, adding traceable links.
    rows=[]
    for p in bundle['participants']:
        rows.append({**p['fields'],'ImportKey':p['importKey'],'SourceSheet':p['sourceSheet'],'SourceRow':p['excelRow'],
                     'SourceID':p['sourceID'],'ReviewNotes':'; '.join(p['issues'])})
    write_csv(folder/'participants.csv',api.COLUMNS+PARTICIPANT_META,rows,api,replace_new=True)
    columns=['DataRow','SourceSheet','ExcelRow','ImportKey','Email','Issues','UnmappedSourceValues']
    write_csv(folder/'manual-review.csv',columns,[{'DataRow':p['dataRow'],'SourceSheet':p['sourceSheet'],
        'ExcelRow':p['excelRow'],'ImportKey':p['importKey'],'Email':p['fields']['Participantaccount'],
        'Issues':'; '.join(p['issues']),'UnmappedSourceValues':json.dumps(p['unmapped'],ensure_ascii=False)}
        for p in bundle['participants'] if p['issues']],api,replace_new=True)
    write_csv(folder/'groups.csv',GROUP_COLUMNS,bundle['groups'],api)
    write_csv(folder/'memberships.csv',MEMBER_COLUMNS,bundle['memberships'],api)
    write_csv(folder/'group-review.csv',GROUP_COLUMNS,[g for g in bundle['groups'] if g['ReviewNotes']],api)


def read_bundle(folder,api):
    def read(name,columns):
        with (folder/name).open(encoding='utf-8-sig',newline='') as f:
            reader=csv.DictReader(f)
            if reader.fieldnames!=columns:raise api.ImportProblem('Keep the combined bundle CSV headers unchanged.')
            result=[]
            for row in reader:
                if None in row or any(v is None for v in row.values()):raise api.ImportProblem('Malformed combined CSV row.')
                result.append({k:v[1:] if v.startswith("'") and api.excel_safe(v[1:])==v else v for k,v in row.items()})
            return result
    raw=read('participants.csv',api.COLUMNS+PARTICIPANT_META)
    people=[]
    for i,p in enumerate(raw,1):
        people.append({'dataRow':i,'excelRow':int(p['SourceRow']) if p['SourceRow'].isdigit() else None,
            'fields':{k:p[k] for k in api.COLUMNS},'issues':p['ReviewNotes'].split('; ') if p['ReviewNotes'] else [],'unmapped':[],
            'importKey':p['ImportKey'],'sourceSheet':p['SourceSheet'],'sourceID':p['SourceID']})
        people[-1]['issues']=[v for v in people[-1]['issues'] if v!='DUPLICATE_SOURCE_EMAIL']
    refs=[p['importKey'] for p in people]
    if any(not r for r in refs) or len(refs)!=len(set(refs)):raise api.ImportProblem('Participant ImportKey must be unique and nonblank.')
    emails=Counter(api.key(p['fields']['Participantaccount']) for p in people if p['fields']['Participantaccount'])
    for p in people:
        if emails[api.key(p['fields']['Participantaccount'])]>1:p['issues'].append('DUPLICATE_SOURCE_EMAIL')
    groups=read('groups.csv',GROUP_COLUMNS);members=read('memberships.csv',MEMBER_COLUMNS)
    keys=[g['MigrationKey'] for g in groups]
    if len(keys)!=len(set(keys)) or any(not re.fullmatch(r'migration48:group:[0-9a-f]{20}',k) for k in keys):
        raise api.ImportProblem('Group MigrationKey must be unique, unchanged and valid.')
    if any(m['MigrationKey'] not in keys or m['ParticipantRef'] not in refs for m in members):
        raise api.ImportProblem('Membership refers to a missing group or participant ImportKey.')
    return {'participants':people,'groups':groups,'memberships':members,'sourceTabs':sorted({p['sourceSheet'] for p in people})}


def summary(bundle,version):
    return {'kind':'TandemMatchingWorkbookImport','version':version,'sourceTicket':48,'mode':'PREPARE_ONLY',
        'sourceTabs':bundle['sourceTabs'],'participantCount':len(bundle['participants']),
        'externalLinkPartsIgnored':bundle.get('externalLinkPartsIgnored',0),
        'rowsWithEmail':sum(bool(p['fields']['Participantaccount']) for p in bundle['participants']),
        'participantsNeedingReview':sum(bool(p['issues']) for p in bundle['participants']),
        'groupCount':len(bundle['groups']),'groupsApprovedForImport':sum(g['ImportApproved']=='Yes' for g in bundle['groups']),
        'groupsNeedingReview':sum(bool(g['ReviewNotes']) for g in bundle['groups']),
        'membershipCount':len(bundle['memberships']),'membershipStatuses':dict(Counter(m['MembershipStatus'] for m in bundle['memberships'])),
        'participantWrites':0,'groupWrites':0,'membershipWrites':0,'migrationRequestWrites':0,
        'accountResolution':'NOT_ATTEMPTED','nativeGroupAcceptance':'NOT_RUN','ordinaryUserAccessVerified':False}


def exact_ids(labels,role,catalogues,api):
    values=[]
    for label in filter(None,(s.strip() for s in labels.split(';'))):
        matches=[c for c in catalogues[role] if c.get('Active') is True and api.key(c.get('Title'))==api.key(label)]
        if len(matches)!=1:raise api.ImportProblem('GROUP_CATALOGUE_SELECTION_NOT_UNIQUE')
        if matches[0]['Id'] not in values:values.append(matches[0]['Id'])
    return values


def apply_groups(bundle,participant_results,sp,api,checkpoint=None):
    """Import reviewed groups with canonical native source/episode evidence.

    Existing completed imports are preserved. Never repair or overwrite a
    partially created group automatically: journal + explicit reconciliation.
    """
    result=[]
    by_row={r['dataRow']:r for r in participant_results}
    ref_ids={p['importKey']:by_row[i].get('participantId') for i,p in enumerate(bundle['participants'],1)
             if i in by_row and by_row[i]['status'] in ('CREATED','EXISTING_PRESERVED')}
    catalogues={r:sp.rows(api.list_base(id_)+'/items?$select=Id,Title,Active&$top=5000') for r,id_ in api.CATALOGUES.items()}
    types={}
    for role,id_ in [('groups',GROUPS),('members',MEMBERS),('requests',REQUESTS)]:
        _,value=sp.request(api.list_base(id_)+'?$select=ListItemEntityTypeFullName')
        if not value.get('ListItemEntityTypeFullName'):raise api.ImportProblem('GROUP_LIST_TYPE_UNAVAILABLE')
        types[role]=value['ListItemEntityTypeFullName']
    for id_,field in [(GROUPS,'SourceRequestId'),(MEMBERS,'MembershipKey'),(REQUESTS,'SendOperationKey'),(REQUESTS,'ConnectionKey')]:
        _,meta=sp.request(api.list_base(id_)+"/fields/getbyinternalnameortitle('"+field+"')?$select=EnforceUniqueValues")
        if meta.get('EnforceUniqueValues') is not True:raise api.ImportProblem('MIGRATION_UNIQUE_KEY_NOT_VERIFIED')
    # Preserve native reader headroom, including historical/staged rows.
    existing={role:sp.rows(api.list_base(id_)+'/items?$select=Id&$top='+str(limit+1),bound=limit+1)
              for role,id_,limit in [('groups',GROUPS,100),('members',MEMBERS,2000),('requests',REQUESTS,500)]}
    counts={role:len(rows) for role,rows in existing.items()}
    def find(id_,field,value):
        safe=value.replace("'","''") if isinstance(value,str) else str(value)
        literal="'"+safe+"'" if isinstance(value,str) else safe
        return sp.rows(api.list_base(id_)+'/items?$filter='+field+' eq '+literal+'&$top=2',bound=2)
    def patch(id_,item_id,payload,observed=None):
        uri=api.list_base(id_)+'/items('+str(item_id)+')'
        if observed is None:_,current=sp.request(uri)
        else:current=observed
        etag=current.get('_etag') or current.get('@odata.etag') or current.get('odata.etag') or current.get('__metadata',{}).get('etag')
        if not etag:raise api.ImportProblem('MIGRATION_ETAG_REQUIRED')
        role={GROUPS:'groups',MEMBERS:'members',REQUESTS:'requests'}[id_]
        outcome['patchAttempts']+=1
        if checkpoint:checkpoint(result)
        return sp.request(uri,'POST',{'__metadata':{'type':types[role]},**payload},etag=etag)
    def post(role,id_,payload):
        outcome['writeAttempts'][role]+=1
        if checkpoint:checkpoint(result)
        code,row=sp.request(api.list_base(id_)+'/items','POST',{'__metadata':{'type':types[role]},**payload})
        if code!=201 or type(row.get('Id')) is not int:raise api.ImportProblem('MIGRATION_WRITE_UNCONFIRMED')
        outcome['confirmedCreates'][role]+=1;counts[role]+=1
        if checkpoint:checkpoint(result)
        return row
    timestamp=datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    for group in bundle['groups']:
        outcome={'migrationKey':group['MigrationKey'],'status':'MANUAL_REVIEW','code':'NOT_APPROVED','groupId':None,
                 'writeAttempts':{'groups':0,'members':0,'requests':0},'confirmedCreates':{'groups':0,'members':0,'requests':0},'patchAttempts':0}
        result.append(outcome)
        if api.key(group['ImportApproved'])!='yes':continue
        wrote=False
        try:
            roster=[m for m in bundle['memberships'] if m['MigrationKey']==group['MigrationKey']]
            if len(roster)<2 or any(m['ParticipantRef'] not in ref_ids or m['MembershipStatus'] not in ('Active','Left') for m in roster):
                outcome['code']='RESOLVE_ALL_GROUP_MEMBERS';continue
            ids=[ref_ids[m['ParticipantRef']] for m in roster]
            if len(set(ids))!=len(ids):outcome['code']='DUPLICATE_RESOLVED_GROUP_MEMBER';continue
            active=sum(m['MembershipStatus']=='Active' for m in roster)
            try:capacity=int(group['Capacity'])
            except ValueError:outcome['code']='REVIEW_GROUP_CAPACITY';continue
            typ=group['ExchangeType'];state=group['State']
            if typ not in ('Language','Culture','Combined') or state not in ('Closed','Ended') or not 2<=capacity<=(3 if typ=='Language' else 10) or active>capacity:
                outcome['code']='UNSUPPORTED_GROUP_CAPACITY_TYPE_OR_STATE';continue
            langs=exact_ids(group['LanguageFocus'],'language',catalogues,api)
            cultures=exact_ids(group['CultureFocus'],'culture',catalogues,api)
            if not group['Title'].strip() or len(group['Title'])>255 or not (langs or cultures) or (typ=='Language' and (not langs or cultures)) or (typ=='Culture' and (not cultures or langs)) or (typ=='Combined' and (not langs or not cultures)):
                outcome['code']='REVIEW_GROUP_FOCUS_OR_TITLE';continue
            # Check provided dates before the first write; blank means import time.
            for member in roster:
                joined=datetime.fromisoformat((member['JoinedAt'] or timestamp).replace('Z','+00:00'))
                left=datetime.fromisoformat((member['LeftAt'] or timestamp).replace('Z','+00:00')) if member['MembershipStatus']=='Left' else None
                if joined.tzinfo is None or left is not None and (left.tzinfo is None or left<joined):
                    raise api.ImportProblem('MEMBERSHIP_DATES_NEED_UTC_OFFSET_AND_VALID_ORDER')
                if member['MembershipStatus']=='Active' and member['LeftAt']:raise api.ImportProblem('ACTIVE_MEMBER_MUST_HAVE_BLANK_LEFT_AT')
            token=group['MigrationKey'];source_key=token+':source'
            source=find(REQUESTS,'SendOperationKey',source_key)
            if source:
                old_group=find(GROUPS,'SourceRequestId',source[0]['Id'])
                if old_group and old_group[0].get('SetupComplete') is True and source[0].get('Status')=='Accepted' and source[0].get('OperationComplete') is True:
                    outcome.update(status='EXISTING_PRESERVED',code='COMPLETED_MIGRATION_PRESERVED',groupId=old_group[0]['Id']);continue
                outcome.update(status='STOPPED',code='PARTIAL_MIGRATION_REQUIRES_RECONCILIATION');break
            if counts['groups']+1>100 or counts['members']+len(roster)>2000 or counts['requests']+len(roster)-1>500:
                outcome['code']='IMPORT_WOULD_EXCEED_CURRENT_APP_READ_BOUNDS';continue
            # Stable source pair only establishes migration provenance, not joining order.
            pairs=sorted(zip(roster,ids),key=lambda p:p[0]['ParticipantRef'])
            p1,p2=pairs[0][1],pairs[1][1]
            live='open:person:'+str(min(p1,p2))+':'+str(max(p1,p2))
            if find(REQUESTS,'ConnectionKey',live):outcome['code']='EXISTING_LIVE_REQUEST_REQUIRES_REVIEW';continue
            outcome.update(status='UNKNOWN',code='MIGRATION_WRITE_STARTED')
            if checkpoint:checkpoint(result)
            wrote=True
            # Accepted/incomplete with the native live key is structurally valid
            # throughout staging and never exposes a new Pending approval action.
            source=post('requests',REQUESTS,{'Title':source_key+' — historical migration','RequestType':'Personal',
                'SenderParticipantId':p1,'RecipientParticipantId':p2,'TargetGroupId':None,'Status':'Accepted',
                'SendOperationKey':source_key,'WinningOperationKey':source_key+':attested','OperationComplete':False,'ConnectionKey':live})
            rid=source['Id']
            patch(REQUESTS,rid,{'OperationComplete':True,'ConnectionKey':'history:request:'+str(rid)})
            created=post('groups',GROUPS,{'Title':group['Title'],'ExchangeType':typ,'LanguageFocusId':{'results':langs},
                'CultureFocusId':{'results':cultures},'Capacity':capacity,'State':state,'SourceRequestId':rid,
                'SetupComplete':False,'WriteOwner':'','Purpose':'Legacy migration ('+timestamp[:10]+'). '+DATE_NOTE})
            gid=created['Id'];outcome['groupId']=gid
            for index,(member,pid) in enumerate(pairs):
                episode=rid
                if index>=2:
                    k=token+':member:'+hashlib.sha256(member['ParticipantRef'].encode()).hexdigest()[:16]
                    req=post('requests',REQUESTS,{'Title':k+' — historical migration','RequestType':'Group','SenderParticipantId':pid,
                        'RecipientParticipantId':None,'TargetGroupId':gid,'Status':'Accepted','SendOperationKey':k,
                        'WinningOperationKey':k+':attested','OperationComplete':False,'ConnectionKey':'open:group:'+str(gid)+':participant:'+str(pid)})
                    episode=req['Id'];patch(REQUESTS,episode,{'OperationComplete':True,'ConnectionKey':'history:request:'+str(episode)})
                left=member['MembershipStatus']=='Left'
                post('members',MEMBERS,{'Title':token+':member:'+str(index+1),'GroupId':gid,'ParticipantId':pid,
                    'MembershipStatus':member['MembershipStatus'],'MembershipKey':'request:'+str(episode)+':participant:'+str(pid),
                    'JoinedAt':member['JoinedAt'] or timestamp,'LeftAt':(member['LeftAt'] or timestamp) if left else None})
            # Reread all links and request evidence before publishing the group.
            saved=sp.rows(api.list_base(MEMBERS)+'/items?$filter=GroupId eq '+str(gid)+'&$top=2001',bound=2001)
            if len(saved)!=len(pairs):raise api.ImportProblem('MIGRATION_MEMBERSHIP_READBACK_MISMATCH')
            for member,pid in pairs:
                match=[m for m in saved if m.get('ParticipantId')==pid and m.get('MembershipStatus')==member['MembershipStatus']]
                if len(match)!=1 or not re.fullmatch(r'request:\d+:participant:'+str(pid),match[0].get('MembershipKey','')):
                    raise api.ImportProblem('MIGRATION_MEMBERSHIP_KEY_MISMATCH')
                eid=int(match[0]['MembershipKey'].split(':')[1]);_,req=sp.request(api.list_base(REQUESTS)+'/items('+str(eid)+')')
                if req.get('Status')!='Accepted' or req.get('OperationComplete') is not True or req.get('ConnectionKey')!='history:request:'+str(eid):
                    raise api.ImportProblem('MIGRATION_REQUEST_COMMIT_MISMATCH')
                if eid==rid:
                    if req.get('RequestType')!='Personal' or req.get('SenderParticipantId')!=p1 or req.get('RecipientParticipantId')!=p2 or req.get('TargetGroupId') is not None or req.get('SendOperationKey')!=source_key:
                        raise api.ImportProblem('MIGRATION_SOURCE_PARTIES_MISMATCH')
                elif req.get('RequestType')!='Group' or req.get('SenderParticipantId')!=pid or req.get('RecipientParticipantId') is not None or req.get('TargetGroupId')!=gid:
                    raise api.ImportProblem('MIGRATION_EPISODE_PARTIES_MISMATCH')
                if not match[0].get('JoinedAt') or (member['MembershipStatus']=='Active' and match[0].get('LeftAt')) or (member['MembershipStatus']=='Left' and not match[0].get('LeftAt')):
                    raise api.ImportProblem('MIGRATION_MEMBERSHIP_DATES_MISMATCH')
            _,saved_group=sp.request(api.list_base(GROUPS)+'/items('+str(gid)+')')
            def ids(value):return value.get('results',[]) if isinstance(value,dict) else value
            if saved_group.get('SourceRequestId')!=rid or saved_group.get('ExchangeType')!=typ or saved_group.get('State')!=state or saved_group.get('Capacity')!=capacity or saved_group.get('SetupComplete') is not False or set(ids(saved_group.get('LanguageFocusId',[])))!=set(langs) or set(ids(saved_group.get('CultureFocusId',[])))!=set(cultures):
                raise api.ImportProblem('MIGRATION_GROUP_READBACK_MISMATCH')
            patch(GROUPS,gid,{'SetupComplete':True},observed=saved_group)
            _,published=sp.request(api.list_base(GROUPS)+'/items('+str(gid)+')')
            if published.get('SetupComplete') is not True:raise api.ImportProblem('MIGRATION_PUBLISH_UNCONFIRMED')
            outcome.update(status='CREATED',code='GROUP_AND_MEMBERSHIPS_COMMITTED')
        except (api.SharePointError,ValueError) as error:
            authorization=isinstance(error,api.SharePointError) and error.status in (401,403)
            outcome.update(status='UNKNOWN' if wrote else 'STOPPED' if authorization else 'MANUAL_REVIEW',code='MIGRATION_UNCONFIRMED_STOP' if wrote else 'GROUP_PREFLIGHT_FAILED')
            if wrote or authorization:break
        finally:
            if checkpoint:checkpoint(result)
    return result
