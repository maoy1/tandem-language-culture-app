"""#48 one-time local Excel preparation / optional create-only SharePoint load.

Standard library only. Default: private local files, no network. --apply requires
an existing approved SharePoint access token in an environment variable; this
script does not register an application, request consent or acquire credentials.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from xml.etree import ElementTree as ET
from zipfile import ZipFile, BadZipFile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
VERSION = '2.0.0'
SITE = 'https://reedelsevier.sharepoint.com/sites/OG-TandemOrg'
PARTICIPANTS = 'fd3adf46-f81d-4a7b-a80c-567fde0175dc'
CATALOGUES = {'language': '3c1fcd2b-ce62-4af0-a96d-9b0d7502cb63',
              'culture': 'cf7ed5b4-2e11-4a0a-a417-6c63ed60f614'}
COLUMNS = ['Title', 'Participantaccount', 'Teachlanguages', 'Learnlanguages',
           'ShareCultures', 'LearnCultures', 'Learningfocus', 'ParticipationStatus', 'OpenToConnections']
DESTINATIONS = {'language': ('Learnlanguages', 'Teachlanguages'),
                'culture': ('LearnCultures', 'ShareCultures')}
HEADERS = {'D': 'Email', 'G': 'Please leave your name and Email',
           'P': 'Which Language/Culture would you like to learn?',
           'Q': 'Which Language/Culture would you like to learn?2',
           'R': 'Which Language/Culture would you love to share?'}
EMAIL = re.compile(r"(?<![\w.+%-])[A-Za-z0-9._%+'-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}(?![\w.-])")
NS = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
REL = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'


class ImportProblem(ValueError):
    """An operator message containing no source identity values or server body."""


def key(value):
    return str(value or '').strip().lower()


def configuration(path=None):
    candidates = [Path(path)] if path else [HERE/'profile-value-map.json', ROOT/'config/participant_excel_value_mapping.json']
    found = next((p for p in candidates if p.is_file()), None)
    if found is None:
        raise ImportProblem('Keep profile-value-map.json beside this script, or use --mapping PATH.')
    data = json.loads(found.read_text(encoding='utf-8-sig'))
    if data.get('kind') != 'TandemParticipantExcelValueMapping' or data.get('reviewed') is not True:
        raise ImportProblem('Expected the reviewed #48 profile-value mapping.')
    return data


def workbook(path, sheet=None):
    """Read values only. Keep worksheet/data row numbers; never open an identity file remotely."""
    with ZipFile(path) as z:
        if sum(i.file_size for i in z.infolist()) > 100_000_000:
            raise ImportProblem('Workbook exceeds the 100 MB uncompressed limit.')
        if any(n.startswith('xl/externalLinks/') for n in z.namelist()):
            raise ImportProblem('Use an export without external workbook links.')
        def xml(name):
            raw = z.read(name)
            if b'<!DOCTYPE' in raw.upper() or b'<!ENTITY' in raw.upper():
                raise ImportProblem('Unexpected XML entity declaration.')
            return ET.fromstring(raw)
        strings = []
        if 'xl/sharedStrings.xml' in z.namelist():
            strings = [''.join(n.text or '' for n in s.iter('{'+NS['s']+'}t')) for s in xml('xl/sharedStrings.xml')]
        sheets = xml('xl/workbook.xml').findall('s:sheets/s:sheet', NS)
        choices = [s for s in sheets if sheet is None or s.get('name') == sheet]
        if len(choices) != 1:
            raise ImportProblem('Select the worksheet with --sheet NAME.')
        links = {r.get('Id'): r.get('Target') for r in xml('xl/_rels/workbook.xml.rels') if r.get('TargetMode') != 'External'}
        target = links[choices[0].get('{'+REL+'}id')]
        target = target.lstrip('/') if target.startswith('/') else 'xl/'+target
        if '..' in PurePosixPath(target).parts:
            raise ImportProblem('Unexpected workbook worksheet path.')
        rows = {}
        for r in xml(target).findall('s:sheetData/s:row', NS):
            cells = {}
            for c in r.findall('s:c', NS):
                if c.find('s:f', NS) is not None:
                    raise ImportProblem('Use a values-only export; formula cells are not imported.')
                col = re.sub(r'\d', '', c.get('r', ''))
                value = c.findtext('s:v', '', NS)
                if c.get('t') == 's':
                    value = strings[int(value)] if value else ''
                elif c.get('t') == 'inlineStr':
                    value = ''.join(n.text or '' for n in c.iter('{'+NS['s']+'}t'))
                if value.strip():
                    cells[col] = value.strip()
            if cells:
                rows[int(r.get('r'))] = cells
        if not rows or min(rows) != 1:
            raise ImportProblem('Expected column headers on worksheet row 1.')
        header_key = lambda value: ' '.join(str(value or '').split()).lower()
        if any(header_key(rows[1].get(col)) != header_key(name) for col, name in HEADERS.items()):
            raise ImportProblem('Workbook columns do not match the original Tandem export.')
        end = max(rows)
        if end > 10001:
            raise ImportProblem('Maximum 10,000 data rows per local import file.')
        return [(i-1, i, rows.get(i, {})) for i in range(2, end+1)]


def address(values):
    # Both columns contribute: conflicting explicit addresses are never silently chosen.
    candidates = {m.lower() for col in ('D', 'G') for m in EMAIL.findall(values.get(col, ''))}
    return next(iter(candidates)) if len(candidates) == 1 else ''


def prepare(source, mapping, skip_rows=0):
    records = []
    for data_row, excel_row, raw in source[skip_rows:]:
        issues = []
        email = address(raw)
        if not email:
            issues.append('MISSING_OR_AMBIGUOUS_EMAIL')
        title = raw.get('E', '').strip()
        if key(title) == 'anonymous':
            title = ''
        row = {c: '' for c in COLUMNS}
        row.update(Title=title or email, Participantaccount=email,
                   Learningfocus=raw.get('N', ''), ParticipationStatus='Active', OpenToConnections='Yes')
        selected = {c: [] for c in ['Teachlanguages', 'Learnlanguages', 'ShareCultures', 'LearnCultures']}
        unmapped = []
        for col, role in [('P', 'learn'), ('Q', 'learn'), ('R', 'share')]:
            value = raw.get(col, '')
            if not value.strip():
                continue
            spec = mapping['mappings'][role].get(key(value))
            if not spec or spec['status'] != 'MAPPED':
                issues.append('UNMAPPED_SELECTION_'+col)
                unmapped.append({'column': col, 'value': value})
                continue  # Preserve the other source cells' valid mappings.
            for cat, destinations in DESTINATIONS.items():
                dest = destinations[0 if role == 'learn' else 1]
                for label in spec[cat+'Titles']:
                    if label not in selected[dest]:
                        selected[dest].append(label)
        if not any(selected.values()):
            issues.append('NO_MAPPED_PROFILE_SELECTIONS')
        for col, labels in selected.items():
            row[col] = '; '.join(labels)
        records.append({'dataRow': data_row, 'excelRow': excel_row, 'fields': row,
                        'issues': issues, 'unmapped': unmapped})
    counts = Counter(r['fields']['Participantaccount'] for r in records if r['fields']['Participantaccount'])
    for r in records:
        if counts[r['fields']['Participantaccount']] > 1:
            r['issues'].append('DUPLICATE_SOURCE_EMAIL')
    return records


def excel_safe(value):
    """Prevent source text becoming a formula when an operator opens the CSV."""
    text = str(value or '')
    return "'"+text if text.lstrip().startswith(('=', '+', '-', '@')) or text.startswith(('\t', '\r')) else text


def from_csv(path):
    records = []
    with Path(path).open(encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != COLUMNS:
            raise ImportProblem('Expected the generated participants.csv column headers, unchanged.')
        for index, row in enumerate(reader, 1):
            if None in row or any(v is None for v in row.values()):
                raise ImportProblem('Malformed participant CSV row.')
            clean = {k: v[1:] if v.startswith("'") and excel_safe(v[1:]) == v else v for k, v in row.items()}
            records.append({'dataRow': index, 'excelRow': None, 'fields': clean, 'issues': [], 'unmapped': []})
    # These are positions in the corrected CSV, not original Excel row numbers.
    counts = Counter(key(r['fields']['Participantaccount']) for r in records if r['fields']['Participantaccount'])
    for r in records:
        if counts[key(r['fields']['Participantaccount'])] > 1:
            r['issues'].append('DUPLICATE_SOURCE_EMAIL')
    return records


class SharePointError(Exception):
    def __init__(self, status=0):
        self.status = status
        super().__init__('SHAREPOINT_HTTP_'+str(status) if status else 'SHAREPOINT_CONNECTION_FAILED')


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None  # Never forward a bearer token to another destination.


class SharePoint:
    def __init__(self, token):
        self.token = token
        self.opener = urllib.request.build_opener(NoRedirect)

    def request(self, path, method='GET', payload=None, etag=None):
        if not path.startswith('_api/'):
            raise ImportProblem('Only relative SharePoint REST paths are allowed.')
        url = SITE+'/'+urllib.parse.quote(path, safe="/?$=&(),':%")
        headers = {'Authorization': 'Bearer '+self.token, 'Accept': 'application/json;odata=nometadata'}
        if etag:
            if etag=='*':raise ImportProblem('Wildcard migration writes are not allowed.')
            headers.update({'If-Match':etag,'X-HTTP-Method':'MERGE'})
        data = None
        if payload is not None:
            headers['Content-Type'] = 'application/json;odata=verbose'
            data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        try:
            with self.opener.open(urllib.request.Request(url, data=data, headers=headers, method=method), timeout=60) as response:
                content = response.read(10_000_001)
                if len(content) > 10_000_000:
                    raise SharePointError()
                parsed = json.loads(content) if content else {}
                parsed=parsed.get('d', parsed)
                if isinstance(parsed,dict) and response.headers.get('ETag'):
                    parsed['_etag']=response.headers.get('ETag')
                return response.status, parsed
        except urllib.error.HTTPError as e:
            # Do not persist raw connector/server errors, which can contain identities/tokens.
            raise SharePointError(e.code) from None
        except (urllib.error.URLError, TimeoutError, OSError, ValueError):
            raise SharePointError() from None

    def rows(self, path, bound=5000):
        _, data = self.request(path)
        rows = data.get('value', data.get('results'))
        if not isinstance(rows, list) or len(rows) >= bound or any(data.get(k) for k in ('@odata.nextLink', 'odata.nextLink', '__next')):
            raise ImportProblem('INCOMPLETE_SHAREPOINT_READ')
        return rows


def list_base(id_):
    return "_api/web/lists(guid'"+id_+"')"


def apply(records, sp, checkpoint=None):
    """Called only with --apply. No updates/deletes/role assignments or automatic retries."""
    _, actor = sp.request('_api/web/currentuser?$select=Id')
    if type(actor.get('Id')) is not int:
        raise ImportProblem('SHAREPOINT_SIGN_IN_NOT_VERIFIED')
    base = list_base(PARTICIPANTS)
    _, account_field = sp.request(base+"/fields/getbyinternalnameortitle('Participantaccount')?$select=TypeAsString,EnforceUniqueValues")
    if account_field.get('TypeAsString') != 'User' or account_field.get('EnforceUniqueValues') is not True:
        raise ImportProblem('PARTICIPANT_ACCOUNT_MUST_REMAIN_UNIQUE_PERSON_FIELD')
    _, info = sp.request(base+'?$select=ListItemEntityTypeFullName')
    entity_type = info.get('ListItemEntityTypeFullName')
    if not isinstance(entity_type, str) or not entity_type:
        raise ImportProblem('MISSING_LIST_ITEM_ENTITY_TYPE')
    catalogues = {role: sp.rows(list_base(id_)+'/items?$select=Id,Title,Active&$top=5000') for role, id_ in CATALOGUES.items()}
    profile_count=len(sp.rows(base+'/items?$select=Id&$top=501',bound=501))
    results = []
    for record in records:
        fields = record['fields']; email = key(fields['Participantaccount'])
        outcome = {'dataRow': record['dataRow'], 'status': 'MANUAL_REVIEW', 'code': '', 'participantId': None}
        results.append(outcome)
        if not EMAIL.fullmatch(email) or 'DUPLICATE_SOURCE_EMAIL' in record['issues']:
            outcome['code'] = 'FIX_EMAIL_OR_DUPLICATE_SOURCE'; continue
        attempted = False
        try:
            # Actual Person value is a resolved SharePoint user ID, never a fabricated email-as-ID.
            _, user = sp.request('_api/web/ensureuser', 'POST', {'logonName': email})
            uid = user.get('Id')
            if type(uid) is not int or uid <= 0 or key(user.get('Email')) != email:
                outcome['code'] = 'ACCOUNT_NOT_EXACTLY_RESOLVED'; continue
            uri = base+'/items?$select=Id,ParticipantaccountId&$filter=ParticipantaccountId eq '+str(uid)+'&$top=2'
            existing = sp.rows(uri, bound=2)
            if existing:
                outcome.update(status='EXISTING_PRESERVED', code='EXISTING_PRESERVED', participantId=existing[0]['Id']); continue
            payload = {'__metadata': {'type': entity_type}, 'Title': fields['Title'] or user.get('Title') or email,
                       'ParticipantaccountId': uid, 'Learningfocus': fields['Learningfocus'],
                       'ParticipationStatus': fields['ParticipationStatus'], 'OpenToConnections': key(fields['OpenToConnections']) in ('yes', 'true', '1')}
            if len(payload['Title']) > 255 or payload['ParticipationStatus'] not in ('Active', 'Paused', 'Inactive'):
                outcome['code'] = 'FIX_TITLE_OR_PARTICIPATION'; continue
            if key(fields['OpenToConnections']) not in ('yes', 'true', '1', 'no', 'false', '0'):
                outcome['code'] = 'FIX_OPEN_TO_CONNECTIONS'; continue
            invalid = False
            for cat, destinations in DESTINATIONS.items():
                for dest in destinations:
                    ids = []
                    for label in filter(None, (s.strip() for s in fields[dest].split(';'))):
                        matches = [c for c in catalogues[cat] if c.get('Active') is True and key(c.get('Title')) == key(label)]
                        if len(matches) != 1:
                            invalid = True; break
                        if matches[0]['Id'] not in ids:
                            ids.append(matches[0]['Id'])
                    payload[dest+'Id'] = {'results': ids}
            if invalid or not any(payload[d+'Id']['results'] for pair in DESTINATIONS.values() for d in pair):
                outcome['code'] = 'FIX_CATALOGUE_SELECTIONS'; continue
            if profile_count>=500:
                outcome['code']='CURRENT_APP_PROFILE_READ_BOUND';continue
            outcome.update(status='UNKNOWN', code='WRITE_STARTED_NOT_YET_CONFIRMED')
            if checkpoint:
                checkpoint(results)  # Durable evidence before the request can create a row.
            attempted = True
            code, created = sp.request(base+'/items', 'POST', payload)
            saved = sp.rows(uri, bound=2)
            if code != 201 or len(saved) != 1 or created.get('Id') != saved[0].get('Id'):
                outcome.update(status='UNKNOWN', code='CREATE_UNCONFIRMED'); break
            outcome.update(status='CREATED', code='CREATED', participantId=created['Id'])
            profile_count+=1
        except (SharePointError, ValueError) as e:
            if isinstance(e, SharePointError) and e.status in (401, 403):
                outcome.update(status='UNKNOWN' if attempted else 'STOPPED', code='SHAREPOINT_AUTHORIZATION_FAILED'); break
            outcome.update(status='UNKNOWN' if attempted else 'MANUAL_REVIEW', code='CREATE_UNCONFIRMED' if attempted else 'ACCOUNT_OR_READ_FAILED')
            if attempted:
                break  # Reconcile an uncertain write before attempting more rows.
        finally:
            if checkpoint:
                checkpoint(results)
    if checkpoint:
        checkpoint(results)
    return results


def write_outputs(folder, records, summary, outcomes=None):
    folder.mkdir(parents=True, exist_ok=False)
    with (folder/'participants.csv').open('x', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, COLUMNS); writer.writeheader()
        writer.writerows({k: excel_safe(v) for k, v in r['fields'].items()} for r in records)
    with (folder/'manual-review.csv').open('x', encoding='utf-8-sig', newline='') as f:
        columns = ['DataRow', 'ExcelRow', 'Email', 'Issues', 'UnmappedSourceValues']
        writer = csv.DictWriter(f, columns); writer.writeheader()
        for r in records:
            if r['issues']:
                writer.writerow(dict(zip(columns, map(excel_safe, [r['dataRow'], r['excelRow'] or '', r['fields']['Participantaccount'],
                    '; '.join(r['issues']), json.dumps(r['unmapped'], ensure_ascii=False)]))))
    if outcomes is not None:
        (folder/'apply-results.private.json').write_text(json.dumps(outcomes, indent=2)+'\n', encoding='utf-8')
    (folder/'summary.json').write_text(json.dumps(summary, indent=2)+'\n', encoding='utf-8')


def main(argv=None):
    try:
        from . import matching_workbook_import as matching
    except ImportError:
        import matching_workbook_import as matching
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--workbook', type=Path); source.add_argument('--prepared-csv', type=Path)
    source.add_argument('--prepared-bundle',type=Path,help='Reviewed combined participants/groups/memberships CSV folder')
    parser.add_argument('--sheet'); parser.add_argument('--skip-rows', type=int, default=0)
    parser.add_argument('--mapping', type=Path)
    parser.add_argument('--scope',choices=['all','active'],default='all',help='Matching workbook: default all three current tabs, never safety copy')
    parser.add_argument('--output', type=Path, help='New private output folder; default: dated folder beside input; never overwritten')
    parser.add_argument('--apply', action='store_true', help='Create missing profiles using an existing approved SharePoint token')
    parser.add_argument('--token-env', default='TANDEM_SP_ACCESS_TOKEN')
    args = parser.parse_args(argv)
    if args.skip_rows < 0:
        parser.error('--skip-rows must be zero or greater')
    if (args.prepared_csv or args.prepared_bundle) and args.skip_rows:
        parser.error('--skip-rows applies to the original workbook only')
    if args.apply and args.workbook:
        parser.error('First prepare the workbook; --apply reads your reviewed --prepared-csv or --prepared-bundle')
    if args.output is None:
        args.output = (args.prepared_bundle or (args.prepared_csv or args.workbook).parent)/('Tandem-import-'+datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
    if args.output.exists():
        parser.error('Use a new output directory to preserve earlier results and manual corrections')
    try:
        bundle=None
        if args.prepared_bundle:
            bundle=matching.read_bundle(args.prepared_bundle,sys.modules[__name__]);records=bundle['participants']
        elif args.prepared_csv:
            records=from_csv(args.prepared_csv)
        else:
            with ZipFile(args.workbook) as z:
                matching_format=any(key(s.get('name')) in matching.SHEETS for s in ET.fromstring(z.read('xl/workbook.xml')).findall('s:sheets/s:sheet',NS))
            if matching_format:
                sheets=matching.read_sheets(args.workbook,sys.modules[__name__])
                if args.sheet:
                    sheets=[s for s in sheets if s['name']==args.sheet]
                    if not sheets:raise ImportProblem('Choose an existing current tab; safety copies are excluded.')
                bundle=matching.prepare(sheets,configuration(args.mapping),sys.modules[__name__],args.scope,args.skip_rows);records=bundle['participants']
            else:
                records=prepare(workbook(args.workbook, args.sheet), configuration(args.mapping), args.skip_rows)
        input_file = args.prepared_csv or args.workbook or args.prepared_bundle/'participants.csv'
        summary = {'kind': 'TandemOneTimePythonImport', 'version': VERSION, 'sourceTicket': 48,
                   'mode': 'APPLY' if args.apply else 'PREPARE_ONLY', 'sourceSha256': hashlib.sha256(input_file.read_bytes()).hexdigest(),
                   'skipRows': args.skip_rows, 'rowCount': len(records), 'rowsWithEmail': sum(bool(r['fields']['Participantaccount']) for r in records),
                   'rowsNeedingReview': sum(bool(r['issues']) for r in records), 'participantWrites': 0,
                   'accountResolution': 'NOT_ATTEMPTED', 'ordinaryUserAccessVerified': False}
        if bundle:
            summary={**summary,**matching.summary(bundle,VERSION),'mode':'APPLY' if args.apply else 'PREPARE_ONLY',
                     'rowCount':len(records),'skipRows':args.skip_rows}
        outcomes = None
        if args.apply:
            token = os.environ.get(args.token_env, '').strip()
            if not token:
                raise ImportProblem('No SharePoint token supplied. Preparation needs no sign-in; direct Apply needs an existing tenant-approved SharePoint token in '+args.token_env+'. No new app/consent is created by this script.')
            # Reserve a writable output location before any tenant side effect.
            if bundle:matching.write_bundle(args.output,bundle,{**summary,'complete':False},sys.modules[__name__])
            else:write_outputs(args.output, records, {**summary, 'complete': False}, [])
            def checkpoint(current):
                path = args.output/'apply-results.private.json'
                temp = args.output/'apply-results.private.tmp'
                with temp.open('w',encoding='utf-8') as f:
                    json.dump(current,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
                os.replace(temp,path)
            outcomes = apply(records, SharePoint(token), checkpoint)
            summary.update(accountResolution='ATTEMPTED', participantWrites=sum(r['status'] == 'CREATED' for r in outcomes),
                           participantWriteAttempts=sum(r['status'] in ('CREATED','UNKNOWN') for r in outcomes),
                           outcomes=dict(Counter(r['status'] for r in outcomes)), processedRows=len(outcomes),
                           complete=len(outcomes) == len(records) and not any(r['status'] in ('UNKNOWN', 'STOPPED') for r in outcomes))
            # Keep participant results truthful even if group preflight fails or
            # the operator interrupts the second stage.
            (args.output/'summary.json').write_text(json.dumps({**summary,'complete':False if bundle else summary['complete']},indent=2)+'\n',encoding='utf-8')
            if bundle and summary['complete']:
                def group_checkpoint(current):
                    path=args.output/'group-results.private.json';temp=args.output/'group-results.private.tmp'
                    with temp.open('w',encoding='utf-8') as f:
                        json.dump(current,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
                    os.replace(temp,path)
                groups=matching.apply_groups(bundle,outcomes,SharePoint(token),sys.modules[__name__],group_checkpoint)
                summary.update(groupOutcomes=dict(Counter(g['status'] for g in groups)),
                    groupWrites=sum(g['confirmedCreates']['groups'] for g in groups),
                    membershipWrites=sum(g['confirmedCreates']['members'] for g in groups),
                    migrationRequestWrites=sum(g['confirmedCreates']['requests'] for g in groups),groupsProcessed=len(groups),
                    groupWriteAttempts=sum(sum(g['writeAttempts'].values())+g['patchAttempts'] for g in groups),
                    complete=len(groups)==len(bundle['groups']) and not any(g['status'] in ('UNKNOWN','STOPPED') for g in groups))
        if args.apply:
            (args.output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
        else:
            if bundle:matching.write_bundle(args.output,bundle,summary,sys.modules[__name__])
            else:write_outputs(args.output, records, summary)
        print(json.dumps(summary, indent=2))  # Counts only, no identity values or token.
        return 2 if args.apply and not summary['complete'] else 0
    except (ValueError, SharePointError, OSError, KeyError, IndexError, BadZipFile, ET.ParseError) as e:
        if args.apply and 'summary' in locals() and args.output.exists():
            summary['complete']=False
            summary['stopped']=True
            try:
                (args.output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
            except OSError:
                pass  # Durable pre-write journals remain the recovery evidence.
        # Source filenames and server bodies may contain identities. Keep terminal errors generic.
        print(str(e) if isinstance(e, (ImportProblem, SharePointError)) else 'Could not read/write the local input or output. Check the selected file and permissions.', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
