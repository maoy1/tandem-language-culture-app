"""#47 tagged synthetic native SharePoint fixture; explicit boolean write gate."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED,ZipFile
from .build_import_probe import build_package as envelope
from .schema_audit import measure,wdl_string
from .build_coordination_preflight import SITE,actions as permission_actions

NAME='TandemCoordinationFixture'
ALL=['Succeeded','Failed','Skipped','TimedOut']
SPECS=[{'name':n,'type':t,'required':required,'unique':unique} for n,t,required,unique in [
    ('Title','Text',True,True),('KeyB','Text',True,True),('Payload','Note',True,False),
    ('OwnerToken','Text',False,False),('Counter','Number',False,False),('Capacity','Number',False,False),
    ('Status','Text',False,False),('Complete','Boolean',False,False)]]
CASES=['UNIQUE_PRIMARY','UNIQUE_SECONDARY','STALE_TERMINAL','PARALLEL_TERMINAL',
       'LAST_SLOT_TWO_ACCEPTORS','CAPACITY_VS_JOIN','LEAVE_VS_JOIN','KNOWN_PREFIX_REPLAY',
       'LEFT_EPISODE_HISTORY','COMMITTED_EVENT_UNIQUE']


def raw(v):return v[1:] if isinstance(v,str) and v.startswith('@') else wdl_string(v)
def expr(v):return '@'+v
def cat(*parts):return '@concat('+','.join(raw(p) for p in parts)+')'
def data(n,key=None):return "outputs('"+n+"')?['body']?['d']"+("?['"+key+"']" if key else '')
def rid(n):return expr("coalesce("+data(n,'Id')+','+data(n,'ID')+')')
def etag(n):return expr(data(n)+"?['__metadata']?['etag']")
def status(n):return "int(coalesce(outputs('"+n+"')?['statusCode'],0))"
def ok(n):return "contains(json('[200,201,204]'),"+status(n)+')'
def duplicate(n):
    # Tenant evidence: HttpRequest wraps the native duplicate exception as 502.
    # Status alone (including 400/409) never establishes a unique-key conflict.
    error="outputs('"+n+"')?['body']?['error']"
    codes="coalesce("+error+"?['innerError']?['errors'],json('[]'))"
    native="equals("+error+"?['code'],'-2130575169, Microsoft.SharePoint.SPDuplicateValuesFoundException')"
    wrapped="and(contains("+codes+",'-2130575169'),contains("+codes+",'Microsoft.SharePoint.SPDuplicateValuesFoundException'))"
    return "and(contains(json('[400,409,502]'),"+status(n)+"),or("+native+","+wrapped+"))"


def duplicate_details(n):
    error="outputs('"+n+"')?['body']?['error']"
    return {'httpStatus':expr(status(n)),
        'errorCode':expr(error+"?['code']"),
        'nativeErrorCodes':expr("coalesce("+error+"?['innerError']?['errors'],json('[]'))"),
        'errorMessage':expr("coalesce("+error+"?['innerError']?['message'],"+error+"?['message'],'')")}

def arr(n):return "coalesce("+data(n,'results')+",json('[]'))"
def count(n):return 'length('+arr(n)+')'
def complete(n):return 'and(equals('+status(n)+',200),not(equals('+data(n,'results')+',null)),empty('+data(n,'__next')+'))'
def and_(*tests):return 'and('+','.join(tests)+')'
def success_after(n,all_states=False):return {n:ALL if all_states else ['Succeeded']} if n else {}
def compose(value,previous=None,all_states=False):return {'type':'Compose','inputs':value,'runAfter':success_after(previous,all_states)}
def condition(test,yes,no=None,previous=None,all_states=False):return {'type':'If','expression':expr(test),'actions':yes,'else':{'actions':no or {}},'runAfter':success_after(previous,all_states)}
def fail(code):return {'type':'Terminate','inputs':{'runStatus':'Failed','runError':{'code':code,'message':code}},'runAfter':{}}
def setvar(name,value,previous=None):return {'type':'SetVariable','inputs':{'name':name,'value':value},'runAfter':success_after(previous)}
def append(name,value,previous=None,all_states=False):return {'type':'AppendToArrayVariable','inputs':{'name':name,'value':value},'runAfter':success_after(previous,all_states)}


class Builder:
    def __init__(self,site,build_id):
        self.site=site;self.build_id=build_id
        self.title='Tandem47Fixture_'+build_id.replace('-','')[:16]
        self.tag='Tandem issue 47 synthetic fixture; packageBuildId='+build_id+'; no production data.'
    def http(self,uri,previous=None,body=None,merge_etag=None,metadata=False,all_states=False):
        p={'dataset':self.site,'parameters/method':'GET' if body is None else 'POST','parameters/uri':uri,
           'parameters/headers':{'Accept':'application/json;odata=verbose'}}
        if body is not None:p['parameters/body']=body;p['parameters/headers']['Content-Type']='application/json;odata=verbose'
        if merge_etag is not None:p['parameters/headers'].update({'X-HTTP-Method':'MERGE','IF-MATCH':merge_etag})
        return {'type':'OpenApiConnection','runAfter':success_after(previous,all_states),'inputs':{
            'parameters':p,'host':{'apiId':'/providers/Microsoft.PowerApps/apis/shared_sharepointonline',
            'connectionName':'shared_sharepointonline','operationId':'HttpRequest'},
            'authentication':"@parameters('$authentication')",'retryPolicy':{'type':'none'}}}
    def base(self,suffix=''):
        return cat("_api/web/lists(guid'",expr("variables('FixtureListId')"),"')"+suffix)
    def item(self,row,suffix=''):
        return cat(self.base('/items('),expr('string('+raw(row)+')'),')'+suffix)
    def key(self,value):return cat(expr("outputs('Run_prefix')"),':'+value)
    def create(self,label,keyb=None,previous=None,**fields):
        values={'__metadata':{'type':expr("variables('FixtureEntityType')")},'Title':self.key(label),
                'KeyB':self.key(keyb or 'key:'+label),'Payload':json.dumps({'synthetic':True,'case':label}),**fields}
        return self.http(self.base('/items'),previous,body=values)
    def get(self,row,previous=None,all_states=False):return self.http(self.item(row),previous,all_states=all_states)
    def merge(self,row,read_action,patch,previous=None):
        return self.http(self.item(row),previous,body={'__metadata':{'type':expr("variables('FixtureEntityType')")},**patch},merge_etag=etag(read_action))
    def rows(self,field,value,previous=None,prefix=False,all_states=False):
        filter_expr=('startswith('+field+",'") if prefix else field+" eq '"
        tail="')&$top=100" if prefix else "'&$top=100"
        return self.http(cat(self.base('/items?$filter='+filter_expr),value,tail),previous,all_states=all_states)
    def report(self,case,test,previous,details=None):
        return append('TestResults',{'case':case,'passed':expr(test),'details':details or {}},previous,True)

    def schema_setup(self):
        title_filter="_api/web/lists?$select=Id,Title,Description,BaseTemplate,ItemCount&$filter=Title eq '"+self.title+"'&$top=2"
        a={'Find_fixture':self.http(title_filter)}
        create={'Create_fixture':self.http('_api/web/lists',body={'__metadata':{'type':'SP.List'},'BaseTemplate':100,'Title':self.title,'Description':self.tag}),
                'Save_created_id':setvar('FixtureListId',rid('Create_fixture'),'Create_fixture'),
                'Mark_fixture_created':setvar('FixtureCreated',True,'Save_created_id')}
        existing=and_("equals("+count('Find_fixture')+',1)',"equals(first("+arr('Find_fixture')+")?['Description'],"+wdl_string(self.tag)+')',
                      "equals(first("+arr('Find_fixture')+")?['BaseTemplate'],100)",complete('Find_fixture'))
        a['Locate_or_create']=condition('equals('+count('Find_fixture')+',0)',create,
            {'Require_existing_tag':condition(existing,{'Use_existing_id':setvar('FixtureListId',expr("first("+arr('Find_fixture')+")?['Id']"))},
                {'Reject_fixture_collision':fail('FIXTURE_TITLE_OR_TAG_COLLISION')})},'Find_fixture')
        a['Read_fixture_identity']=self.http(self.base('?$select=Id,Title,Description,BaseTemplate,ItemCount,ListItemEntityTypeFullName'),'Locate_or_create')
        identity=and_('equals('+data('Read_fixture_identity','Id')+",variables('FixtureListId'))",
            'equals('+data('Read_fixture_identity','Title')+','+wdl_string(self.title)+')',
            'equals('+data('Read_fixture_identity','Description')+','+wdl_string(self.tag)+')',
            'equals('+data('Read_fixture_identity','BaseTemplate')+',100)',
            'not(empty('+data('Read_fixture_identity','ListItemEntityTypeFullName')+'))')
        a['Require_fixture_identity']=condition(identity,{}, {'Fail_identity':fail('FIXTURE_IDENTITY_NOT_VERIFIED')},'Read_fixture_identity')
        a['Save_entity_type']=setvar('FixtureEntityType',expr(data('Read_fixture_identity','ListItemEntityTypeFullName')),'Require_fixture_identity')
        fields_suffix='/fields?$select=InternalName,TypeAsString,Required,Indexed,EnforceUniqueValues&$top=5000'
        a['Fields_before']=self.http(self.base(fields_suffix),'Save_entity_type')
        a['Find_title']={'type':'Query','inputs':{'from':expr(arr('Fields_before')),'where':"@equals(item()?['InternalName'],'Title')"},'runAfter':success_after('Fields_before')}
        title_ok=and_("equals(length(body('Find_title')),1)","equals(first(body('Find_title'))?['TypeAsString'],'Text')",
            "equals(first(body('Find_title'))?['Required'],true)","equals(first(body('Find_title'))?['Indexed'],true)","equals(first(body('Find_title'))?['EnforceUniqueValues'],true)")
        title_write=self.http(self.base("/fields/getbyinternalnameortitle('Title')"),body={'__metadata':{'type':'SP.FieldText'},'Required':True,'Indexed':True,'EnforceUniqueValues':True},merge_etag='*',metadata=True)
        a['Ensure_title_key']=condition(title_ok,{}, {'Change_empty_fixture_title':condition('equals('+data('Read_fixture_identity','ItemCount')+',0)',
            {'Configure_title_key':title_write},{'Reject_nonempty_schema_change':fail('NONEMPTY_FIXTURE_TITLE_SCHEMA_MISMATCH')})},'Find_title')
        specs=[]
        for s in SPECS[1:]:
            xml='<Field Name="'+s['name']+'" StaticName="'+s['name']+'" DisplayName="'+s['name']+'" Type="'+s['type']+'" Required="'+('TRUE' if s['required'] else 'FALSE')+'" Indexed="'+('TRUE' if s['unique'] else 'FALSE')+'" EnforceUniqueValues="'+('TRUE' if s['unique'] else 'FALSE')+'"'+(' RichText="FALSE"' if s['type']=='Note' else '')+' />'
            specs.append({**s,'schemaXml':xml})
        fields={'Find_expected_field':{'type':'Query','inputs':{'from':expr(arr('Fields_before')),
            'where':"@equals(item()?['InternalName'],items('Ensure_fields')?['name'])"},'runAfter':{}},
            'Create_field_if_missing':condition("empty(body('Find_expected_field'))",{
                'Only_extend_empty_fixture':condition('equals('+data('Read_fixture_identity','ItemCount')+',0)',{
                  'Create_fixture_field':self.http(self.base('/fields/createfieldasxml'),body={'parameters':{
                    '__metadata':{'type':'SP.XmlSchemaFieldCreationInformation'},'Options':8,
                    'SchemaXml':"@items('Ensure_fields')?['schemaXml']"}})},
                  {'Reject_nonempty_missing_field':append('SchemaErrors',"@concat('missing-field:',items('Ensure_fields')?['name'])")})},previous='Find_expected_field')}
        a['Custom_field_specs']=compose(specs,'Ensure_title_key')
        a['Ensure_fields']={'type':'Foreach','foreach':"@outputs('Custom_field_specs')",'runtimeConfiguration':{'concurrency':{'repetitions':1}},'actions':fields,'runAfter':success_after('Custom_field_specs')}
        a['Fields_after']=self.http(self.base(fields_suffix),'Ensure_fields')
        valid="@and(equals(item()?['InternalName'],items('Verify_fields')?['name']),equals(item()?['TypeAsString'],items('Verify_fields')?['type']),equals(item()?['Required'],items('Verify_fields')?['required']),equals(item()?['EnforceUniqueValues'],items('Verify_fields')?['unique']),or(not(items('Verify_fields')?['unique']),equals(item()?['Indexed'],true)))"
        a['All_field_specs']=compose(SPECS,'Fields_after')
        a['Verify_fields']={'type':'Foreach','foreach':"@outputs('All_field_specs')",'runtimeConfiguration':{'concurrency':{'repetitions':1}},'runAfter':success_after('All_field_specs'),'actions':{
            'Verified_field':{'type':'Query','inputs':{'from':expr(arr('Fields_after')),'where':valid},'runAfter':{}},
            'Remember_field_mismatch':condition("not(equals(length(body('Verified_field')),1))",{
                'Append_schema_error':append('SchemaErrors',"@items('Verify_fields')?['name']",None)},previous='Verified_field')}}
        a['Require_fixture_schema']=condition(and_("empty(variables('SchemaErrors'))",complete('Fields_after'),complete('Fields_before')),{},
            {'Reject_fixture_schema':fail('FIXTURE_FIELD_SCHEMA_NOT_VERIFIED')},'Verify_fields')
        return a

    def unique_cases(self):
        a={'Unique_anchor':self.create('unique:anchor','unique:secondary')}
        a['Duplicate_primary']=self.create('unique:anchor','unique:other','Unique_anchor')
        a['Read_primary_anchor']=self.rows('Title',self.key('unique:anchor'),'Duplicate_primary',all_states=True)
        a['Unique_primary_report']=self.report('UNIQUE_PRIMARY',and_(duplicate('Duplicate_primary'),complete('Read_primary_anchor'),
            'equals('+count('Read_primary_anchor')+',1)',"equals(first("+arr('Read_primary_anchor')+")?['Id'],"+raw(rid('Unique_anchor'))+')'),'Read_primary_anchor',duplicate_details('Duplicate_primary'))
        a['Duplicate_secondary']=self.create('unique:otherTitle','unique:secondary','Unique_primary_report')
        a['Read_secondary_anchor']=self.rows('KeyB',self.key('unique:secondary'),'Duplicate_secondary',all_states=True)
        a['Read_rejected_title']=self.rows('Title',self.key('unique:otherTitle'),'Read_secondary_anchor')
        a['Unique_secondary_report']=self.report('UNIQUE_SECONDARY',and_(duplicate('Duplicate_secondary'),complete('Read_secondary_anchor'),complete('Read_rejected_title'),
            'equals('+count('Read_secondary_anchor')+',1)','equals('+count('Read_rejected_title')+',0)'),'Read_rejected_title',duplicate_details('Duplicate_secondary'))
        return a

    def terminal_cases(self,previous):
        a={'Stale_request':self.create('stale:request',previous=previous,Status='Pending',Complete=False)}
        a['Read_stale_request']=self.get(rid('Stale_request'),'Stale_request')
        a['Accept_current']=self.merge(rid('Stale_request'),'Read_stale_request',{'Status':'Accepted','Complete':False},'Read_stale_request')
        a['Cancel_stale']=self.merge(rid('Stale_request'),'Read_stale_request',{'Status':'Cancelled','Complete':True},'Accept_current')
        a['Read_terminal_after_stale']=self.get(rid('Stale_request'),'Cancel_stale',True)
        a['Stale_terminal_report']=self.report('STALE_TERMINAL',and_(ok('Accept_current'),'equals('+status('Cancel_stale')+',412)',
            'equals('+data('Read_terminal_after_stale','Status')+",'Accepted')",'equals('+data('Read_terminal_after_stale','Complete')+',false)'),'Read_terminal_after_stale')
        a['Race_request']=self.create('decisions:request',previous='Stale_terminal_report',Status='Pending',Complete=False)
        a['Read_decision_barrier']=self.get(rid('Race_request'),'Race_request')
        branch_names=[];statuses=[]
        for tag,decision in [('Accept','Accepted'),('Decline','Declined'),('Cancel','Cancelled')]:
            name='Decision_'+tag;branch_names.append(name);statuses.append(status(name))
            a[name]=self.merge(rid('Race_request'),'Read_decision_barrier',{'Status':decision,'Complete':decision!='Accepted'},'Read_decision_barrier')
        a['Read_decision_winner']=self.get(rid('Race_request'));a['Read_decision_winner']['runAfter']={n:ALL for n in branch_names}
        wins='add(add('+','.join('if('+ok(n)+',1,0)' for n in branch_names[:2])+'),if('+ok(branch_names[2])+',1,0))'
        legal=["or("+ok(n)+',equals('+status(n)+',412))' for n in branch_names]
        winner=["or(not("+ok('Decision_'+tag)+'),equals('+data('Read_decision_winner','Status')+','+wdl_string(decision)+'))' for tag,decision in [('Accept','Accepted'),('Decline','Declined'),('Cancel','Cancelled')]]
        a['Parallel_terminal_report']=self.report('PARALLEL_TERMINAL',and_('equals('+wins+',1)',*legal,*winner),'Read_decision_winner',{'statuses':[expr(s) for s in statuses]})
        return a

    def race(self,prefix,kind,previous):
        n=lambda s:prefix+'_'+s
        a={n('Group'):self.create(prefix+':group',previous=previous,Counter=2,Capacity=3,Status='Open',Complete=True,OwnerToken='')}
        prev=n('Group')
        for tag in ['Base1','Base2']:
            name=n(tag);a[name]=self.create(prefix+':'+tag,prefix+':members:'+tag,prev,Status='Active',Complete=True);prev=name
        for tag in ['A','B']:
            name=n('Request'+tag);a[name]=self.create(prefix+':request:'+tag,prefix+':connection:'+tag,prev,Status='Pending',Complete=False);prev=name
            name=n('Receipt'+tag);a[name]=self.create(prefix+':receipt:'+tag,previous=prev,Status='InProgress',Complete=False);prev=name
            name=n('ReadRequest'+tag);a[name]=self.get(rid(n('Request'+tag)),prev);prev=name
        a[n('Barrier')]=self.get(rid(n('Group')),prev)
        for tag,action_kind in [('A','join'),('B',kind)]:
            ac=n(tag+'_Acquire');scope=n(tag+'_Writer');held=n(tag+'_Held')
            inner={ac:self.merge(rid(n('Group')),n('Barrier'),{'OwnerToken':prefix+':'+tag})}
            own={held:self.get(rid(n('Group')))}
            before=n(tag+'_MembersBefore');own[before]=self.rows('KeyB',self.key(prefix+':members:'),held,prefix=True)
            guard=and_('equals('+data(held,'OwnerToken')+','+wdl_string(prefix+':'+tag)+')',complete(before),
                'equals('+data(held,'Complete')+',true)', 'equals('+count(before)+',2)')
            if action_kind=='join':guard=and_(guard,'equals('+data(held,'Status')+",'Open')",'less('+count(before)+','+data(held,'Capacity')+')')
            work={};last=None
            if action_kind=='join':
                decide=n(tag+'_Decide');work[decide]=self.merge(rid(n('Request'+tag)),n('ReadRequest'+tag),{'Status':'Accepted','Complete':False})
                member_payload=n(tag+'_MemberPayload');work[member_payload]=compose({'synthetic':True,'groupId':rid(n('Group')),'requestId':rid(n('Request'+tag)),'participant':tag},decide)
                member=n(tag+'_Member');work[member]=self.create(prefix+':member:'+tag,prefix+':members:'+tag,member_payload,Status='Active',Complete=False,Payload=expr("string(outputs('"+member_payload+"'))"))
                read_member=n(tag+'_ReadMember');work[read_member]=self.get(rid(member),member)
                verify_member=n(tag+'_VerifyMember');work[verify_member]=condition(and_(
                    'equals('+data(read_member,'Id')+','+raw(rid(member))+')',
                    'equals('+data(read_member,'Title')+','+raw(self.key(prefix+':member:'+tag))+')',
                    'equals('+data(read_member,'Status')+",'Active')",
                    'equals(json('+data(read_member,'Payload')+")?['groupId'],"+raw(rid(n('Group')))+')',
                    'equals(json('+data(read_member,'Payload')+")?['requestId'],"+raw(rid(n('Request'+tag)))+')'),{},
                    {n(tag+'_FailMemberLink'):fail('FIXTURE_MEMBER_LINK_MISMATCH')},read_member)
                read_request=n(tag+'_ReadAccepted');work[read_request]=self.get(rid(n('Request'+tag)),verify_member)
                verify_request=n(tag+'_VerifyAccepted');work[verify_request]=condition(and_(
                    'equals('+data(read_request,'Status')+",'Accepted')",'equals('+data(read_request,'Complete')+',false)'),{},
                    {n(tag+'_FailRequest'):fail('FIXTURE_REQUEST_READBACK_MISMATCH')},read_request)
                committed=n(tag+'_CommitRequest');work[committed]=self.merge(rid(n('Request'+tag)),read_request,{'Complete':True},verify_request)
                last=committed;expected_count=3;new_capacity=3
            elif action_kind=='shrink':
                expected_count=2;new_capacity=2
            else:
                read_member=n(tag+'_ReadLeaveMember');work[read_member]=self.get(rid(n('Base1')))
                left=n(tag+'_Leave');work[left]=self.merge(rid(n('Base1')),read_member,{'Status':'Left'},read_member)
                last=left;expected_count=1;new_capacity=3
            after_members=n(tag+'_MembersAfter');work[after_members]=self.rows('KeyB',self.key(prefix+':members:'),last,prefix=True)
            active=n(tag+'_ActiveAfter');work[active]={'type':'Query','inputs':{'from':expr(arr(after_members)), 'where':"@equals(item()?['Status'],'Active')"},'runAfter':success_after(after_members)}
            verify=n(tag+'_VerifyRows');work[verify]=condition(and_(complete(after_members),'equals(length(body('+wdl_string(active)+')),'+str(expected_count)+')'),{},
                {n(tag+'_FailRows'):fail('FIXTURE_MEMBER_READBACK_MISMATCH')},active)
            save=n(tag+'_SaveGroup');work[save]=self.merge(rid(n('Group')),held,{'Counter':expected_count,'Capacity':new_capacity},verify)
            outcome=n(tag+'_SavedOutcome');work[outcome]=compose({'synthetic':True,'outcome':action_kind,'groupId':rid(n('Group')),
                'requestId':rid(n('Request'+tag)) if action_kind=='join' else None,
                'membershipId':rid(n(tag+'_Member')) if action_kind=='join' else (rid(n('Base1')) if action_kind=='leave' else None)},save)
            read_receipt=n(tag+'_ReadReceipt');work[read_receipt]=self.get(rid(n('Receipt'+tag)),outcome)
            commit_receipt=n(tag+'_CommitReceipt');work[commit_receipt]=self.merge(rid(n('Receipt'+tag)),read_receipt,{'Complete':True,'Status':'Completed','Payload':expr("string(outputs('"+outcome+"'))")},read_receipt)
            rev=n(tag+'_ReleaseRevision');work[rev]=self.get(rid(n('Group')),commit_receipt)
            release=n(tag+'_Release');work[release]=self.merge(rid(n('Group')),rev,{'OwnerToken':''},rev)
            own[n(tag+'_OwnedAndSpace')]=condition(guard,work,{n(tag+'_FailGuard'):fail('FIXTURE_OWNER_OR_CAPACITY_GUARD_FAILED')},before)
            inner[n(tag+'_OwnsGroup')]=condition(ok(ac),own,{},ac,True)
            a[scope]={'type':'Scope','actions':inner,'runAfter':success_after(n('Barrier'))}
        final=n('FinalGroup');a[final]=self.get(rid(n('Group')));a[final]['runAfter']={n('A_Writer'):ALL,n('B_Writer'):ALL}
        members=n('FinalMembers');a[members]=self.rows('KeyB',self.key(prefix+':members:'),final,prefix=True)
        active=n('FinalActive');a[active]={'type':'Query','inputs':{'from':expr(arr(members)),'where':"@equals(item()?['Status'],'Active')"},'runAfter':success_after(members)}
        prev=active
        for tag in ['A','B']:
            for obj in ['Request','Receipt']:
                k=n('Final'+obj+tag);a[k]=self.get(rid(n(obj+tag)),prev);prev=k
        awin=ok(n('A_Acquire'));bwin=ok(n('B_Acquire'))
        tests=['equals(add(if('+awin+',1,0),if('+bwin+',1,0)),1)',
            'or('+awin+',equals('+status(n('A_Acquire'))+',412))','or('+bwin+',equals('+status(n('B_Acquire'))+',412))',
            "empty("+data(final,'OwnerToken')+')',complete(members),
            'equals(length(body('+wdl_string(active)+')),'+data(final,'Counter')+')',
            'lessOrEquals('+data(final,'Counter')+','+data(final,'Capacity')+')',
            'equals('+data(n('FinalReceiptA'),'Complete')+','+awin+')',
            'equals('+data(n('FinalReceiptB'),'Complete')+','+bwin+')',
            'equals('+data(n('FinalRequestA'),'Complete')+','+awin+')']
        for tag,won in [('A',awin),('B',bwin)]:
            tests.append('or(not('+won+'),equals(json(coalesce('+data(n('FinalReceipt'+tag),'Payload')+",'{}'))?['groupId'],"+raw(rid(n('Group')))+'))')
        if kind=='join':tests.append('equals('+data(n('FinalRequestB'),'Complete')+','+bwin+')');tests.append('equals('+data(final,'Counter')+',3)')
        else:
            tests += ['equals('+data(n('FinalRequestB'),'Complete')+',false)',
                      'equals('+data(final,'Counter')+',if('+awin+',3,'+('2' if kind=='shrink' else '1')+'))']
        case={'join':'LAST_SLOT_TWO_ACCEPTORS','shrink':'CAPACITY_VS_JOIN','leave':'LEAVE_VS_JOIN'}[kind]
        a[n('Report')]=self.report(case,and_(*tests),prev,{'actorAStatus':expr(status(n('A_Acquire'))),'actorBStatus':expr(status(n('B_Acquire'))),
            'memberCount':expr(data(final,'Counter')),'capacity':expr(data(final,'Capacity'))})
        return a

    def recovery_cases(self,previous):
        a={'Recovery_request':self.create('recovery:request',previous=previous,Status='Accepted',Complete=False),
           'Recovery_group':self.create('recovery:group',previous='Recovery_request',Status='Closed',Complete=False,Counter=0,Capacity=3,OwnerToken='attempt-old'),
           'Recovery_receipt':self.create('recovery:receipt',previous='Recovery_group',Status='InProgress',Complete=False),
           'Recovery_first':self.create('recovery:member:first','recovery:members:first','Recovery_receipt',Status='Active',Complete=False)}
        a['Recovery_before_group']=self.get(rid('Recovery_group'),'Recovery_first')
        a['Recovery_before_request']=self.get(rid('Recovery_request'),'Recovery_before_group')
        a['Recovery_before_members']=self.rows('KeyB',self.key('recovery:members:'),'Recovery_before_request',True)
        a['Recovery_unpublished']=compose(expr(and_('equals('+data('Recovery_before_group','Complete')+',false)',
            'equals('+data('Recovery_before_request','Complete')+',false)','equals('+count('Recovery_before_members')+',1)')),'Recovery_before_members')
        a['Recovery_injected_stopped_boundary']=compose('@div(1,0)','Recovery_unpublished')
        a['Recovery_read_receipt']=self.get(rid('Recovery_receipt'))
        a['Recovery_read_receipt']['runAfter']={'Recovery_injected_stopped_boundary':['Failed']}
        a['Recovery_seal_attempt']=self.merge(rid('Recovery_receipt'),'Recovery_read_receipt',{'Status':'Retryable','Payload':'{"synthetic":true,"sealedAttempt":"attempt-old","knownStoppedPrefix":true}'},'Recovery_read_receipt')
        a['Recovery_release_old']=self.merge(rid('Recovery_group'),'Recovery_before_group',{'OwnerToken':''},'Recovery_seal_attempt')
        a['Recovery_new_revision']=self.get(rid('Recovery_group'),'Recovery_release_old')
        a['Recovery_claim_new']=self.merge(rid('Recovery_group'),'Recovery_new_revision',{'OwnerToken':'attempt-new'},'Recovery_new_revision')
        a['Recovery_stale_old_attempt']=self.merge(rid('Recovery_group'),'Recovery_before_group',{'OwnerToken':'attempt-old'},'Recovery_claim_new')
        a['Recovery_replay_first']=self.create('recovery:member:first','recovery:members:first','Recovery_stale_old_attempt',Status='Active',Complete=False)
        a['Recovery_replay_first']['runAfter']=success_after('Recovery_stale_old_attempt',True)
        a['Recovery_read_first']=self.get(rid('Recovery_first'),'Recovery_replay_first',True)
        a['Recovery_second']=self.create('recovery:member:second','recovery:members:second','Recovery_read_first',Status='Active',Complete=False)
        a['Recovery_read_members']=self.rows('KeyB',self.key('recovery:members:'),'Recovery_second',True)
        a['Recovery_require_two']=condition(and_(complete('Recovery_read_members'),'equals('+count('Recovery_read_members')+',2)'),{}, {'Fail_recovery_count':fail('FIXTURE_RECOVERY_COUNT_FAILED')},'Recovery_read_members')
        a['Recovery_request_revision']=self.get(rid('Recovery_request'),'Recovery_require_two')
        a['Recovery_commit_request']=self.merge(rid('Recovery_request'),'Recovery_request_revision',{'Complete':True},'Recovery_request_revision')
        a['Recovery_group_revision']=self.get(rid('Recovery_group'),'Recovery_commit_request')
        a['Recovery_commit_group']=self.merge(rid('Recovery_group'),'Recovery_group_revision',{'Complete':True,'Status':'Open','Counter':2},'Recovery_group_revision')
        a['Recovery_receipt_revision']=self.get(rid('Recovery_receipt'),'Recovery_commit_group')
        a['Recovery_commit_receipt']=self.merge(rid('Recovery_receipt'),'Recovery_receipt_revision',{'Complete':True,'Status':'Completed'},'Recovery_receipt_revision')
        a['Recovery_release_revision']=self.get(rid('Recovery_group'),'Recovery_commit_receipt')
        a['Recovery_release_new']=self.merge(rid('Recovery_group'),'Recovery_release_revision',{'OwnerToken':''},'Recovery_release_revision')
        a['Recovery_final_group']=self.get(rid('Recovery_group'),'Recovery_release_new')
        a['Recovery_final_request']=self.get(rid('Recovery_request'),'Recovery_final_group')
        a['Recovery_final_receipt']=self.get(rid('Recovery_receipt'),'Recovery_final_request')
        a['Recovery_report']=self.report('KNOWN_PREFIX_REPLAY',and_("equals(outputs('Recovery_unpublished'),true)",
            "equals(actions('Recovery_injected_stopped_boundary')?['status'],'Failed')",
            'equals('+status('Recovery_stale_old_attempt')+',412)',duplicate('Recovery_replay_first'),
            'equals('+data('Recovery_read_first','Id')+','+raw(rid('Recovery_first'))+')',
            'equals('+data('Recovery_final_group','Complete')+',true)','equals('+data('Recovery_final_request','Complete')+',true)',
            'equals('+data('Recovery_final_receipt','Complete')+',true)',
            'equals('+data('Recovery_final_group','Counter')+',2)','empty('+data('Recovery_final_group','OwnerToken')+')'),'Recovery_final_receipt',
            {**duplicate_details('Recovery_replay_first'),'faultMode':'Intentional non-I/O action failure at known prefix; no network timeout or killed-run claim.'})
        # Historical episode and Closed preservation are a separate fixture.
        a['History_group']=self.create('history:group',previous='Recovery_report',Status='Closed',Counter=1,Capacity=3,Complete=True)
        a['History_member']=self.create('history:member','history:members:episode1','History_group',Status='Active',Complete=True)
        a['History_group_revision']=self.get(rid('History_group'),'History_member')
        a['History_claim']=self.merge(rid('History_group'),'History_group_revision',{'OwnerToken':'history-owner'},'History_group_revision')
        a['History_member_revision']=self.get(rid('History_member'),'History_claim')
        a['History_leave']=self.merge(rid('History_member'),'History_member_revision',{'Status':'Left'},'History_member_revision')
        a['History_replay_create']=self.create('history:member','history:members:episode1','History_leave',Status='Active',Complete=True)
        a['History_after_member']=self.get(rid('History_member'),'History_replay_create',True)
        a['History_count_revision']=self.get(rid('History_group'),'History_after_member')
        a['History_update_count']=self.merge(rid('History_group'),'History_count_revision',{'Counter':0},'History_count_revision')
        a['History_release_revision']=self.get(rid('History_group'),'History_update_count')
        a['History_release']=self.merge(rid('History_group'),'History_release_revision',{'OwnerToken':''},'History_release_revision')
        a['History_after_group']=self.get(rid('History_group'),'History_release')
        a['History_report']=self.report('LEFT_EPISODE_HISTORY',and_(duplicate('History_replay_create'),
            'equals('+data('History_after_member','Status')+",'Left')",'equals('+data('History_after_group','Status')+",'Closed')", 
            'equals('+data('History_after_group','Counter')+',0)',
            'equals('+data('History_after_member','Id')+','+raw(rid('History_member'))+')'),'History_after_group',duplicate_details('History_replay_create'))
        a['Event_before_commit_gate']=compose(expr(and_('equals('+data('Recovery_before_group','Complete')+',true)','equals('+data('Recovery_before_request','Complete')+',true)')),'History_report')
        a['Event_require_commit']=condition(and_('equals('+data('Recovery_final_receipt','Complete')+',true)',
            'equals('+data('Recovery_final_request','Complete')+',true)','equals('+data('Recovery_final_group','Complete')+',true)'),{},
            {'Fail_event_gate':fail('FIXTURE_EVENT_NOT_COMMITTED')},'Event_before_commit_gate')
        a['Event_create']=self.create('event:accepted:recovery','event:accepted:recovery','Event_require_commit',Status='NotDelivered',Complete=True)
        a['Event_replay']=self.create('event:accepted:recovery','event:accepted:recovery','Event_create',Status='NotDelivered',Complete=True)
        a['Event_rows']=self.rows('Title',self.key('event:accepted:recovery'),'Event_replay',all_states=True)
        a['Event_report']=self.report('COMMITTED_EVENT_UNIQUE',and_("equals(outputs('Event_before_commit_gate'),false)",duplicate('Event_replay'),
            complete('Event_rows'),'equals('+count('Event_rows')+',1)','equals('+data('Recovery_final_request','Complete')+',true)',
            'equals('+data('Recovery_final_group','Complete')+',true)'),'Event_rows',{**duplicate_details('Event_replay'),'delivery':'Not attempted; no channel/delivery guarantee.'})
        return a

    def actions(self):
        a=permission_actions(self.site,self.build_id);a.pop('Preflight_report')
        prev='Permission_flags'
        for name,kind,value in [('FixtureListId','string',''),('FixtureEntityType','string',''),('FixtureCreated','boolean',False),('SchemaErrors','array',[]),('TestResults','array',[])]:
            action='Initialize_'+name;a[action]={'type':'InitializeVariable','inputs':{'variables':[{'name':name,'type':kind,'value':value}]},'runAfter':success_after(prev)};prev=action
        a['Run_prefix']=compose("@concat('run:',workflow()?['run']?['name'])",prev)
        native=self.schema_setup();prev='Require_fixture_schema'
        block=self.unique_cases();block['Unique_anchor']['runAfter']=success_after(prev);native.update(block)
        native.update(self.terminal_cases('Unique_secondary_report'))
        prev='Parallel_terminal_report'
        for prefix,kind in [('Slot','join'),('Shrink','shrink'),('Departure','leave')]:
            native.update(self.race(prefix,kind,prev));prev=prefix+'_Report'
        native.update(self.recovery_cases(prev))
        permission="and(not(empty(body('Read_site_identity')?['Id'])),not(empty(outputs('Permission_low'))),"+','.join("equals(outputs('Permission_flags')?['"+k+"'],true)" for k in ['viewItems','addItems','editItems','manageLists'])+')'
        a['Run_fixture_when_requested']=condition(and_("equals(triggerBody()?['boolean'],true)",permission),native,previous='Run_prefix')
        a['Failed_cases']={'type':'Query','inputs':{'from':"@variables('TestResults')",'where':"@not(equals(item()?['passed'],true))"},'runAfter':success_after('Run_fixture_when_requested',True)}
        all_passed=and_("equals(triggerBody()?['boolean'],true)",'equals(length(variables(\'TestResults\')),'+str(len(CASES))+')',"empty(body('Failed_cases'))")
        a['Fixture_report']=compose({'kind':NAME,'schemaVersion':1,'sourceTicket':47,'packageBuildId':self.build_id,
            'runReference':"@workflow()?['run']?['name']",'writeRequested':"@equals(triggerBody()?['boolean'],true)",
            'fixtureCreated':"@variables('FixtureCreated')",'fixtureTitle':self.title,'fixtureListId':"@variables('FixtureListId')",
            'runPrefix':"@outputs('Run_prefix')",'permissionGatePassed':expr(permission),'testCount':"@length(variables('TestResults'))",
            'allPassed':expr(all_passed),'failedCases':"@body('Failed_cases')",'results':"@variables('TestResults')",
            'productionWrites':0,'deletes':0,'scope':'Only this build-tagged synthetic list. Native primitives/selected two-branch races and controlled known-prefix recovery; not all production flow integrations or genuine network-unknown recovery.'},'Failed_cases')
        a['Require_requested_proof']=condition(and_("equals(triggerBody()?['boolean'],true)",'not('+all_passed+')'),
            {'Fail_native_proof':fail('NATIVE_FIXTURE_PROOF_NOT_COMPLETE')},previous='Fixture_report')
        measure(a);return a


def build_package(output,site=SITE):
    output=Path(output)
    if any(p.exists() for p in [output,output.with_suffix('.definition.json'),output.with_suffix('.review.json')]):raise FileExistsError(output)
    with TemporaryDirectory() as tmp:
        base=Path(tmp)/'base.zip';doc=envelope(base,sharepoint_site=site)
        with ZipFile(base) as z:entries={n:json.loads(z.read(n)) for n in z.namelist()}
    builder=Builder(site,doc['name']);doc['properties']['displayName']=NAME+' v2'
    doc['properties']['definition']['triggers']['manual']['inputs']['schema']['properties']={'boolean':{
        'title':'Run fixture writes','type':'boolean','default':False,'x-ms-content-hint':'BOOLEAN','x-ms-dynamically-added':True}}
    doc['properties']['definition']['actions']=builder.actions()
    for n in entries:
        if n.endswith('/definition.json'):entries[n]=doc
    entries['manifest.json']['details'].update(displayName=NAME+'-package',description='Issue 47 native synthetic fixture; boolean write gate defaults false. Creates/reuses tagged fixture only; no production mutations or deletion.')
    for item in entries['manifest.json']['resources'].values():
        if item['type']=='Microsoft.Flow/flows':item['details']['displayName']=NAME+' v2'
    output.parent.mkdir(parents=True,exist_ok=True)
    with ZipFile(output,'x',ZIP_DEFLATED) as z:
        for n,value in entries.items():z.writestr(n,json.dumps(value,indent=2)+'\n')
    review={'sourceTicket':47,'flowName':NAME,'packageBuildId':doc['name'],'fixtureTitle':builder.title,'fixtureTag':builder.tag,
        **measure(doc['properties']['definition']['actions']),'limits':{'actions':500,'nesting':8},'writeGateDefault':False,
        'productionWrites':0,'deletes':0,'permissionChanges':0,'caseCount':len(CASES),'cases':CASES,
        'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'tenantResult':'NOT_IMPORTED_NOT_TESTED',
        'limitations':['Selected native independent-branch races, not all 70 native schedules.','Known-prefix checkpoint is controlled; not a genuine connector timeout/killed-run proof.','Synthetic fixtures do not verify production field/access/caller mapping.','No notification delivery attempted.']}
    output.with_suffix('.definition.json').write_bytes((json.dumps(doc,indent=2)+'\n').encode('utf-8'))
    output.with_suffix('.review.json').write_bytes((json.dumps(review,indent=2)+'\n').encode('utf-8'))
    return review


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    print(json.dumps(build_package(args.output),indent=2))


if __name__=='__main__':main()
