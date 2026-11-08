"""#47 protocol/reference model and generated conditional-write helpers.

No deployed Python runtime. The model assumes atomic per-row CAS/unique keys;
it proves protocol schedules, not native SharePoint cross-list deployment.
"""
from copy import deepcopy
import hashlib
import json

VERSION=1
TERMINAL={'Accepted','Declined','Cancelled'}


class Conflict(Exception):pass
class Busy(Conflict):pass
class Duplicate(Conflict):pass
class SupportRequired(Conflict):pass


def fingerprint(payload):
    return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def operation_key(kind,actor_id,intent_id):
    if kind not in {'send','accept','decline','cancel','update','leave'}:raise ValueError('Unknown operation')
    if type(actor_id) is not int or actor_id<=0 or not isinstance(intent_id,str) or not intent_id.strip():raise ValueError('Invalid operation reference')
    return f'{kind}:{actor_id}:{intent_id.strip()}'


def connection_key(kind,sender_id,target_id):
    if any(type(v) is not int or v<=0 for v in [sender_id,target_id]):raise ValueError('Invalid connection reference')
    if kind=='person':return 'open:person:'+':'.join(map(str,sorted([sender_id,target_id])))
    if kind=='group':return f'open:group:{target_id}:participant:{sender_id}'
    raise ValueError('Unknown connection kind')


def membership_key(request_id,participant_id):return f'request:{request_id}:participant:{participant_id}'


class Store:
    """Isolated fixture store: native single-row primitives are explicit axioms."""
    UNIQUE={'receipts':['OperationKey'],'requests':['SendOperationKey','ConnectionKey'],
            'groups':['SourceRequestId'],'members':['MembershipKey'],'events':['EventKey']}
    def __init__(self):self.tables={t:{} for t in self.UNIQUE};self.next_id={t:1 for t in self.UNIQUE}
    def read(self,table,row_id):return deepcopy(self.tables[table][row_id])
    def find(self,table,field,value):return [deepcopy(r) for r in self.tables[table].values() if r.get(field)==value]
    def create(self,table,values):
        self._unique(table,values)
        row={'ID':self.next_id[table],'Version':1,**deepcopy(values)}
        self.next_id[table]+=1;self.tables[table][row['ID']]=row;return deepcopy(row)
    def _unique(self,table,values,except_id=None):
        for field in self.UNIQUE[table]:
            if field not in values or values[field] is None:continue
            if any(r['ID']!=except_id and r.get(field)==values[field] for r in self.tables[table].values()):raise Duplicate(field)
    def cas(self,table,row_id,version,patch):
        old=self.tables[table][row_id]
        if type(version) is not int or old['Version']!=version:raise Conflict('STALE_VERSION')
        new={**old,**deepcopy(patch)};self._unique(table,new,row_id);new['Version']+=1
        self.tables[table][row_id]=new;return deepcopy(new)


class Protocol:
    def __init__(self,store=None):self.store=store or Store()
    def receipt(self,key,payload):
        found=self.store.find('receipts','OperationKey',key);digest=fingerprint(payload)
        if found:
            if found[0]['PayloadHash']!=digest:raise Conflict('OPERATION_KEY_PAYLOAD_MISMATCH')
            return found[0]
        return self.store.create('receipts',{'OperationKey':key,'PayloadHash':digest,'Payload':payload,
            'Complete':False,'Result':None,'Uncertain':False,'DomainEffects':False,'Retryable':False,'SealedAttempts':[]})
    def _domain_effect(self,key):
        receipts=self.store.find('receipts','OperationKey',key)
        if receipts:
            r=receipts[0]
            self.store.cas('receipts',r['ID'],r['Version'],{'DomainEffects':True})
    def send(self,key,kind,sender,target):
        if kind=='person' and sender==target:raise Conflict('SELF_REQUEST')
        payload={'kind':kind,'sender':sender,'target':target};receipt=self.receipt(key,payload)
        if receipt['Complete']:return deepcopy(receipt['Result'])
        existing=self.store.find('requests','SendOperationKey',key)
        if existing:
            request=existing[0]
        else:
            try:request=self.store.create('requests',{'SendOperationKey':key,'ConnectionKey':connection_key(kind,sender,target),
                'Kind':kind,'SenderParticipantId':sender,'TargetId':target,
                'Status':'Pending','OperationComplete':False,'WinningOperationKey':None,'GroupId':target if kind=='group' else None})
            except Duplicate:
                found=self.store.find('requests','ConnectionKey',connection_key(kind,sender,target))
                if not found:raise
                return {'result':'EXISTING_CONNECTION','requestId':found[0]['ID'],'status':found[0]['Status']}
        result={'result':'PENDING','requestId':request['ID']};self._complete_receipt(receipt,result);return result
    def _complete_receipt(self,receipt,result):
        current=self.store.read('receipts',receipt['ID'])
        return self.store.cas('receipts',current['ID'],current['Version'],{'Complete':True,'Result':result,'Uncertain':False})
    def claim(self,key,attempt,group_id,version):
        receipt=self.store.find('receipts','OperationKey',key)
        if len(receipt)!=1:raise Conflict('RECEIPT_REQUIRED')
        if receipt[0]['Complete']:raise Conflict('OPERATION_COMPLETE_USE_SAVED_RESULT')
        if attempt in receipt[0]['SealedAttempts']:raise Conflict('ATTEMPT_SEALED_NO_FURTHER_WRITES')
        if len(receipt[0]['SealedAttempts'])>=3:raise SupportRequired('BOUNDED_RETRY_LIMIT')
        group=self.store.read('groups',group_id)
        token={'operation':key,'attempt':attempt}
        if group['WriteOwner']==token:return group
        if group['WriteOwner'] is not None:raise Busy('GROUP_BUSY_NO_LEASE_STEAL')
        saved=self.store.cas('groups',group_id,version,{'WriteOwner':token})
        current=self.store.read('receipts',receipt[0]['ID'])
        self.store.cas('receipts',current['ID'],current['Version'],{'Retryable':False})
        return saved
    def owned(self,key,attempt,group_id):
        receipt=self.store.find('receipts','OperationKey',key)
        if receipt and attempt in receipt[0]['SealedAttempts']:raise Conflict('ATTEMPT_SEALED_NO_FURTHER_WRITES')
        group=self.store.read('groups',group_id)
        if group['WriteOwner']!={'operation':key,'attempt':attempt}:raise Busy('NOT_OWNER')
        return group
    def decide(self,request_id,decision,version,key,authorized=True):
        if not authorized:raise Conflict('NOT_AUTHORIZED')
        if decision not in TERMINAL:raise ValueError(decision)
        request=self.store.read('requests',request_id)
        if request['Status']!='Pending':raise Conflict('ALREADY_DECIDED')
        patch={'Status':decision,'WinningOperationKey':key,'OperationComplete':decision!='Accepted'}
        if decision!='Accepted':patch['ConnectionKey']=f'history:request:{request_id}'
        saved=self.store.cas('requests',request_id,version,patch)
        self._domain_effect(key)
        return saved
    def reserve_join(self,key,attempt,request_id,group_id,version,eligible=True):
        self.owned(key,attempt,group_id);group=self.store.read('groups',group_id)
        if not eligible or group['State']!='Open' or not group['SetupComplete']:raise Conflict('UNAVAILABLE')
        if self.count(group_id)>=group['Capacity']:raise Conflict('FULL')
        return self.decide(request_id,'Accepted',version,key)
    def ensure_new_group(self,key,request_id,capacity=3,exchange_type='Language'):
        request=self.store.read('requests',request_id)
        if request['Status']!='Accepted' or request['WinningOperationKey']!=key:raise Conflict('WINNING_ACCEPT_REQUIRED')
        existing=self.store.find('groups','SourceRequestId',request_id)
        if existing:
            g=existing[0]
            if g['Capacity']!=capacity or g['ExchangeType']!=exchange_type:raise Conflict('FROZEN_GROUP_INTENT_MISMATCH')
            return g
        self.valid_capacity(exchange_type,capacity,0)
        saved=self.store.create('groups',{'SourceRequestId':request_id,'ExchangeType':exchange_type,
            'Capacity':capacity,'State':'Closed','SetupComplete':False,'WriteOwner':None})
        self._domain_effect(key)
        return saved
    def count(self,group_id):
        # Includes provisional rows and paused participants: no capacity from filtering.
        return len([r for r in self.store.tables['members'].values() if r['GroupId']==group_id and r['Status']=='Active'])
    @staticmethod
    def valid_capacity(kind,capacity,count):
        if type(capacity) is not int or kind not in ['Language','Culture','Combined'] or capacity<2 or capacity>(3 if kind=='Language' else 10) or capacity<count:raise Conflict('CAPACITY_INVALID')
    def ensure_member(self,key,attempt,request_id,group_id,participant):
        group=self.owned(key,attempt,group_id);request=self.store.read('requests',request_id)
        if request['Status']!='Accepted' or request['WinningOperationKey']!=key:raise Conflict('WINNING_ACCEPT_REQUIRED')
        allowed={request['SenderParticipantId']} if request['Kind']=='group' else {request['SenderParticipantId'],request['TargetId']}
        if participant not in allowed:raise Conflict('REQUEST_PARTY_MISMATCH')
        if request['Kind']=='group' and request['GroupId']!=group_id:raise Conflict('REQUEST_GROUP_MISMATCH')
        if request['Kind']=='person' and group['SourceRequestId']!=request_id:raise Conflict('SOURCE_REQUEST_MISMATCH')
        unique_key=membership_key(request_id,participant);existing=self.store.find('members','MembershipKey',unique_key)
        if existing:
            row=existing[0]
            if row['GroupId']!=group_id or row['ParticipantId']!=participant or row['Status']!='Active':raise SupportRequired('EPISODE_MISMATCH_NEVER_REACTIVATE')
            return row
        if any(r['GroupId']==group_id and r['ParticipantId']==participant and r['Status']=='Active' for r in self.store.tables['members'].values()):raise Conflict('ALREADY_MEMBER')
        if self.count(group_id)>=group['Capacity']:raise Conflict('FULL')
        saved=self.store.create('members',{'MembershipKey':unique_key,'GroupId':group_id,'ParticipantId':participant,
            'RequestId':request_id,'Status':'Active'})
        self._domain_effect(key)
        return saved
    def operational_member(self,row):
        group=self.store.read('groups',row['GroupId']);request=self.store.read('requests',row['RequestId'])
        return row['Status']=='Active' and group['SetupComplete'] and request['Status']=='Accepted' and request['OperationComplete']
    def finish_accept(self,key,attempt,request_id,group_id,participants):
        group=self.owned(key,attempt,group_id);request=self.store.read('requests',request_id)
        if request['Status']!='Accepted' or request['WinningOperationKey']!=key:raise Conflict('WINNING_ACCEPT_REQUIRED')
        expected={request['SenderParticipantId']} if request['Kind']=='group' else {request['SenderParticipantId'],request['TargetId']}
        if set(participants)!=expected or len(participants)!=len(expected):raise SupportRequired('EXPECTED_PARTIES_MISMATCH')
        found=[]
        for p in participants:
            rows=self.store.find('members','MembershipKey',membership_key(request_id,p))
            if len(rows)!=1 or rows[0]['GroupId']!=group_id or rows[0]['Status']!='Active':raise SupportRequired('INCOMPLETE_MEMBERSHIP_RESULT')
            found.append(rows[0]['ID'])
        self.valid_capacity(group['ExchangeType'],group['Capacity'],self.count(group_id))
        if not group['SetupComplete'] and (group['SourceRequestId']!=request_id or len(set(participants))!=2 or self.count(group_id)!=2):raise SupportRequired('INCOMPLETE_NEW_GROUP')
        self.store.cas('requests',request_id,request['Version'],{'OperationComplete':True,'ConnectionKey':f'history:request:{request_id}','GroupId':group_id})
        if not group['SetupComplete']:
            group=self.store.cas('groups',group_id,group['Version'],{'SetupComplete':True,'State':'Open' if self.count(group_id)<group['Capacity'] else 'Closed'})
        receipt=self.store.find('receipts','OperationKey',key)[0]
        self._complete_receipt(receipt,{'result':'ACCEPTED','requestId':request_id,'groupId':group_id,'membershipIds':found})
        self.release_completed(key,group_id)
        return self.success(key,group_id)
    def release_completed(self,key,group_id):
        receipt=self.store.find('receipts','OperationKey',key)[0]
        if not receipt['Complete']:raise SupportRequired('NO_RELEASE_INCOMPLETE_OR_UNCERTAIN')
        group=self.store.read('groups',group_id)
        if group['WriteOwner'] is not None and group['WriteOwner']['operation']==key:
            self.store.cas('groups',group_id,group['Version'],{'WriteOwner':None})
    def success(self,key,group_id=None):
        receipt=self.store.find('receipts','OperationKey',key)[0]
        if not receipt['Complete']:raise SupportRequired('NOT_COMPLETE')
        if group_id is not None:
            owner=self.store.read('groups',group_id)['WriteOwner']
            if owner is not None and owner['operation']==key:raise SupportRequired('COMMITTED_RELEASE_PENDING')
        return deepcopy(receipt['Result'])
    def uncertain(self,key):
        receipt=self.store.find('receipts','OperationKey',key)[0]
        return self.store.cas('receipts',receipt['ID'],receipt['Version'],{'Uncertain':True})
    def reject_before_domain_write(self,key,attempt,group_id,reason):
        self.owned(key,attempt,group_id);receipt=self.store.find('receipts','OperationKey',key)[0]
        if receipt['Uncertain'] or receipt['DomainEffects'] or any(q.get('WinningOperationKey')==key for q in self.store.tables['requests'].values()):
            raise SupportRequired('CANNOT_RELEASE_UNCERTAIN_OR_ACCEPTED_SETUP')
        self._complete_receipt(receipt,{'result':'REJECTED','reason':reason})
        self.release_completed(key,group_id)
        return self.success(key,group_id)
    def pause_known_prefix(self,key,attempt,group_id):
        """Called only at a stopped, definite-error boundary, no outstanding I/O.

        Native consumers must positively establish that condition. Unknown HTTP
        outcomes cannot call this method; they retain the owner for reconciliation.
        """
        self.owned(key,attempt,group_id);receipt=self.store.find('receipts','OperationKey',key)[0]
        if receipt['Uncertain']:raise SupportRequired('UNKNOWN_WRITE_CANNOT_SEAL')
        self.store.cas('receipts',receipt['ID'],receipt['Version'],{
            'Retryable':True,'SealedAttempts':receipt['SealedAttempts']+[attempt]})
        self.release_retryable(key,group_id)
    def release_retryable(self,key,group_id):
        receipt=self.store.find('receipts','OperationKey',key)[0];group=self.store.read('groups',group_id)
        if not receipt['Retryable'] or receipt['Uncertain']:raise SupportRequired('NOT_SAFE_RETRY_BOUNDARY')
        if group['WriteOwner'] is not None:
            if group['WriteOwner']['operation']!=key or group['WriteOwner']['attempt'] not in receipt['SealedAttempts']:raise Busy('OWNER_NOT_SEALED')
            self.store.cas('groups',group_id,group['Version'],{'WriteOwner':None})
    def leave(self,key,attempt,group_id,member_id):
        self.owned(key,attempt,group_id);member=self.store.read('members',member_id)
        if member['GroupId']!=group_id:raise Conflict('WRONG_GROUP')
        if member['Status']=='Active' and not self.operational_member(member):raise Conflict('SETUP_INCOMPLETE')
        if member['Status']=='Active':
            self.store.cas('members',member_id,member['Version'],{'Status':'Left'})
            self._domain_effect(key)
        receipt=self.store.find('receipts','OperationKey',key)[0];self._complete_receipt(receipt,{'result':'LEFT','membershipId':member_id})
        self.release_completed(key,group_id);return self.success(key,group_id)
    def update_group(self,key,attempt,group_id,capacity,state):
        group=self.owned(key,attempt,group_id)
        if not group['SetupComplete']:raise Conflict('SETUP_INCOMPLETE')
        if group['State']=='Ended' and state!='Ended':raise Conflict('ENDED_IS_FINAL')
        if state not in ['Open','Closed','Ended']:raise ValueError('Invalid state')
        self.valid_capacity(group['ExchangeType'],capacity,self.count(group_id))
        self.store.cas('groups',group_id,group['Version'],{'Capacity':capacity,'State':state})
        self._domain_effect(key)
        receipt=self.store.find('receipts','OperationKey',key)[0];self._complete_receipt(receipt,{'result':'UPDATED','groupId':group_id})
        self.release_completed(key,group_id);return self.success(key,group_id)
    def notification_event(self,request_id):
        request=self.store.read('requests',request_id)
        if request['Status'] not in TERMINAL or not request['OperationComplete']:raise Conflict('NOT_COMMITTED')
        receipt=self.store.find('receipts','OperationKey',request['WinningOperationKey'])
        if len(receipt)!=1 or not receipt[0]['Complete']:raise Conflict('RECEIPT_NOT_COMMITTED')
        key=f"request:{request_id}:terminal:{request['Status']}"
        existing=self.store.find('events','EventKey',key)
        return existing[0] if existing else self.store.create('events',{'EventKey':key,'Delivery':'NotAttempted'})


def conditional_merge(site,uri,etag,body,previous=None):
    if not isinstance(etag,str) or etag in ['', '*']:raise ValueError('Exact read ETag expression/value required')
    return {'type':'OpenApiConnection','runAfter':{previous:['Succeeded']} if previous else {},'inputs':{
        'host':{'apiId':'/providers/Microsoft.PowerApps/apis/shared_sharepointonline','connectionName':'shared_sharepointonline','operationId':'HttpRequest'},
        'authentication':"@parameters('$authentication')",'retryPolicy':{'type':'none'},'parameters':{
            'dataset':site,'parameters/method':'POST','parameters/uri':uri,
            'parameters/headers':{'Accept':'application/json;odata=verbose','Content-Type':'application/json;odata=verbose','X-HTTP-Method':'MERGE','IF-MATCH':etag},
            'parameters/body':deepcopy(body)}}}
