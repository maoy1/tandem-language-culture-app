"""Protocol-reference schedules; actual SharePoint fixture proof is separate."""
from copy import deepcopy
from itertools import permutations
import pytest
from scripts.power_automate.coordination import Protocol,Store,Conflict,Busy,Duplicate,SupportRequired,connection_key,membership_key,operation_key,conditional_merge


def pending(p,key='send:1:intent',target=2,kind='person',sender=1):return p.send(key,kind,sender,target)['requestId']


def seeded_group(p,capacity=3,state='Open'):
    q=pending(p)
    p.receipt('initial',{'kind':'accept','request':q})
    request=p.store.read('requests',q);p.decide(q,'Accepted',request['Version'],'initial')
    group=p.ensure_new_group('initial',q,capacity)
    p.claim('initial','attempt-initial',group['ID'],group['Version'])
    for actor in [1,2]:p.ensure_member('initial','attempt-initial',q,group['ID'],actor)
    p.finish_accept('initial','attempt-initial',q,group['ID'],[1,2])
    if state!='Open':
        g=p.store.read('groups',group['ID']);p.store.cas('groups',g['ID'],g['Version'],{'State':state})
    return group['ID']


def prepare_join(p,g,actor):
    q=pending(p,f'send:{actor}:join',g,'group',actor);key=f'accept:{q}:intent'
    p.receipt(key,{'kind':'accept','request':q,'group':g,'participant':actor})
    return q,key


def test_stable_keys_and_payload_freezing():
    assert connection_key('person',2,1)==connection_key('person',1,2)
    assert connection_key('group',2,1)!=connection_key('group',1,2)
    assert membership_key(7,9)=='request:7:participant:9'
    assert operation_key('leave',9,'intent')=='leave:9:intent'
    p=Protocol();p.receipt('key',{'group':1})
    with pytest.raises(Conflict,match='PAYLOAD_MISMATCH'):p.receipt('key',{'group':2})


def test_duplicate_pending_reverse_send_and_late_send_retry():
    p=Protocol();first=p.send('send1','person',1,2)
    assert p.send('send1','person',1,2)==first
    assert p.send('send2','person',2,1)['result']=='EXISTING_CONNECTION'
    q=p.store.read('requests',first['requestId']);p.decide(q['ID'],'Cancelled',q['Version'],'cancel1')
    fresh=p.send('send3','person',1,2)
    assert fresh['requestId']!=first['requestId']
    assert p.send('send1','person',1,2)==first
    assert len(p.store.tables['requests'])==2


@pytest.mark.parametrize('first,second',[('Accepted','Cancelled'),('Cancelled','Accepted'),('Accepted','Declined'),('Declined','Accepted'),('Accepted','Accepted')])
def test_same_pending_version_only_one_terminal_decision_wins(first,second):
    p=Protocol();q=pending(p);v=p.store.read('requests',q)['Version']
    p.decide(q,first,v,'winner')
    with pytest.raises(Conflict):p.decide(q,second,v,'loser')
    assert p.store.read('requests',q)['Status']==first
    assert p.store.read('requests',q)['WinningOperationKey']=='winner'


@pytest.mark.parametrize('order',[(3,4),(4,3)])
def test_distinct_requests_compete_for_one_slot(order):
    p=Protocol();g=seeded_group(p);jobs={a:prepare_join(p,g,a) for a in order}
    original=p.store.read('groups',g)['Version'];winner,loser=order
    q,k=jobs[winner];p.claim(k,'winner',g,original)
    q2,k2=jobs[loser]
    with pytest.raises(Busy):p.claim(k2,'loser',g,original)
    p.reserve_join(k,'winner',q,g,p.store.read('requests',q)['Version'])
    p.ensure_member(k,'winner',q,g,winner);p.finish_accept(k,'winner',q,g,[winner])
    with pytest.raises(Conflict):p.claim(k2,'loser',g,original)
    p.claim(k2,'loser',g,p.store.read('groups',g)['Version'])
    with pytest.raises(Conflict,match='FULL'):p.reserve_join(k2,'loser',q2,g,p.store.read('requests',q2)['Version'])
    p.reject_before_domain_write(k2,'loser',g,'FULL')
    assert p.count(g)==3 and p.store.read('requests',q2)['Status']=='Pending'
    assert len([r for r in p.store.tables['members'].values() if r['ParticipantId'] in order])==1


@pytest.mark.parametrize('crash_after',[0,1,2])
def test_partial_new_group_never_operational_and_retry_never_duplicates(crash_after):
    p=Protocol();q=pending(p);key='accept';p.receipt(key,{'kind':'accept','request':q})
    p.decide(q,'Accepted',p.store.read('requests',q)['Version'],key)
    g=p.ensure_new_group(key,q);p.claim(key,'same-live-attempt',g['ID'],g['Version'])
    for actor in [1,2][:crash_after]:p.ensure_member(key,'same-live-attempt',q,g['ID'],actor)
    assert not p.store.read('groups',g['ID'])['SetupComplete']
    assert not any(p.operational_member(r) for r in p.store.tables['members'].values())
    with pytest.raises(SupportRequired):p.success(key,g['ID'])
    assert p.ensure_new_group(key,q)['ID']==g['ID']
    with pytest.raises(Busy):p.claim(key,'another-attempt',g['ID'],p.store.read('groups',g['ID'])['Version'])
    for actor in [1,2]:p.ensure_member(key,'same-live-attempt',q,g['ID'],actor)
    result=p.finish_accept(key,'same-live-attempt',q,g['ID'],[1,2])
    assert result==p.success(key,g['ID'])
    assert len(p.store.tables['groups'])==1 and len(p.store.tables['members'])==2
    assert all(p.operational_member(r) for r in p.store.tables['members'].values())


def test_uncertain_write_holds_owner_no_ttl_steal_and_no_false_success():
    p=Protocol();g=seeded_group(p);q,k=prepare_join(p,g,3)
    p.claim(k,'attempt1',g,p.store.read('groups',g)['Version']);p.uncertain(k)
    with pytest.raises(SupportRequired):p.reject_before_domain_write(k,'attempt1',g,'timeout')
    with pytest.raises(SupportRequired):p.release_completed(k,g)
    with pytest.raises(Busy):p.claim(k,'attempt2',g,p.store.read('groups',g)['Version'])
    with pytest.raises(SupportRequired):p.success(k,g)
    assert p.store.read('groups',g)['WriteOwner']['attempt']=='attempt1'


def test_provisional_join_counts_for_capacity_and_is_hidden_until_commit():
    p=Protocol();g=seeded_group(p);q,k=prepare_join(p,g,3)
    p.claim(k,'a',g,p.store.read('groups',g)['Version']);p.reserve_join(k,'a',q,g,p.store.read('requests',q)['Version'])
    row=p.ensure_member(k,'a',q,g,3)
    assert p.count(g)==3 and not p.operational_member(row)
    assert p.send('new-send','group',3,g)['result']=='EXISTING_CONNECTION'
    with pytest.raises(SupportRequired):p.success(k,g)
    p.finish_accept(k,'a',q,g,[3]);assert p.operational_member(row)


def test_leave_preserves_closed_state_and_never_reactivates_old_episode():
    p=Protocol();g=seeded_group(p,state='Closed');row=next(iter(p.store.tables['members'].values()))
    p.receipt('leave',{'kind':'leave','member':row['ID']});p.claim('leave','a',g,p.store.read('groups',g)['Version'])
    result=p.leave('leave','a',g,row['ID'])
    assert p.store.read('groups',g)['State']=='Closed' and p.count(g)==1
    assert p.success('leave',g)==result and p.store.read('members',row['ID'])['Status']=='Left'
    with pytest.raises(Conflict):p.claim('leave','again',g,p.store.read('groups',g)['Version'])
    assert len(p.store.tables['members'])==2


def test_capacity_writer_and_join_share_same_guard():
    p=Protocol();g=seeded_group(p);q,k=prepare_join(p,g,3)
    p.receipt('update',{'kind':'update','capacity':2});v=p.store.read('groups',g)['Version']
    p.claim('update','u',g,v)
    with pytest.raises(Busy):p.claim(k,'a',g,v)
    p.update_group('update','u',g,2,'Open')
    p.claim(k,'a',g,p.store.read('groups',g)['Version'])
    with pytest.raises(Conflict,match='FULL'):p.reserve_join(k,'a',q,g,p.store.read('requests',q)['Version'])
    assert p.count(g)==2


def test_ended_final_and_capacity_never_below_count():
    p=Protocol();g=seeded_group(p,state='Ended');p.receipt('update',{'kind':'update'})
    p.claim('update','u',g,p.store.read('groups',g)['Version'])
    with pytest.raises(Conflict,match='ENDED'):p.update_group('update','u',g,3,'Open')
    with pytest.raises(Conflict,match='CAPACITY'):p.valid_capacity('Language',1,2)
    assert p.store.read('groups',g)['State']=='Ended'


def test_completed_receipt_prevents_stale_update_replay():
    p=Protocol();g=seeded_group(p);p.receipt('old',{'kind':'update','state':'Closed'})
    p.claim('old','o',g,p.store.read('groups',g)['Version']);p.update_group('old','o',g,3,'Closed')
    p.receipt('new',{'kind':'update','state':'Ended'});p.claim('new','n',g,p.store.read('groups',g)['Version']);p.update_group('new','n',g,3,'Ended')
    assert p.success('old',g)['result']=='UPDATED'
    with pytest.raises(Conflict,match='COMPLETE'):p.claim('old','stale',g,p.store.read('groups',g)['Version'])
    assert p.store.read('groups',g)['State']=='Ended'


def test_completed_but_release_failed_can_finalize_without_new_domain_writes():
    p=Protocol();g=seeded_group(p);p.receipt('op',{'kind':'update'})
    p.claim('op','a',g,p.store.read('groups',g)['Version'])
    receipt=p.store.find('receipts','OperationKey','op')[0];p._complete_receipt(receipt,{'result':'UPDATED','groupId':g})
    with pytest.raises(SupportRequired,match='RELEASE_PENDING'):p.success('op',g)
    before=deepcopy(p.store.tables['members']);p.release_completed('op',g)
    assert p.success('op',g)['result']=='UPDATED' and p.store.tables['members']==before


def test_cancel_wins_before_accept_never_adds_member():
    p=Protocol();g=seeded_group(p);q,k=prepare_join(p,g,3)
    p.claim(k,'a',g,p.store.read('groups',g)['Version']);v=p.store.read('requests',q)['Version']
    p.decide(q,'Cancelled',v,'cancel')
    with pytest.raises(Conflict):p.reserve_join(k,'a',q,g,v)
    with pytest.raises(Conflict):p.ensure_member(k,'a',q,g,3)
    p.reject_before_domain_write(k,'a',g,'CANCELLED')
    assert p.count(g)==2 and p.store.read('requests',q)['Status']=='Cancelled'


def test_unique_terminal_event_not_exactly_once_external_delivery_claim():
    p=Protocol();q=pending(p);v=p.store.read('requests',q)['Version'];p.decide(q,'Declined',v,'decline')
    with pytest.raises(Conflict):p.notification_event(q)
    receipt=p.receipt('decline',{'kind':'decline','request':q});p._complete_receipt(receipt,{'result':'DECLINED','requestId':q})
    a=p.notification_event(q);b=p.notification_event(q)
    assert a['ID']==b['ID'] and len(p.store.tables['events'])==1
    assert a['Delivery']=='NotAttempted' # Channel/delivery retry decisions remain #49/#21.


def test_only_request_parties_can_receive_membership_results():
    p=Protocol();g=seeded_group(p);q,k=prepare_join(p,g,3)
    p.claim(k,'a',g,p.store.read('groups',g)['Version']);p.reserve_join(k,'a',q,g,p.store.read('requests',q)['Version'])
    with pytest.raises(Conflict,match='PARTY'):p.ensure_member(k,'a',q,g,999)
    p.ensure_member(k,'a',q,g,3)
    with pytest.raises(SupportRequired,match='PARTIES'):p.finish_accept(k,'a',q,g,[3,3])


def test_failed_receipt_after_domain_write_cannot_be_rejected_and_unlocked(monkeypatch):
    p=Protocol();g=seeded_group(p);p.receipt('update',{'kind':'update'})
    p.claim('update','a',g,p.store.read('groups',g)['Version'])
    def failure(*args):raise RuntimeError('receipt write failed')
    monkeypatch.setattr(p,'_complete_receipt',failure)
    with pytest.raises(RuntimeError):p.update_group('update','a',g,3,'Closed')
    with pytest.raises(SupportRequired):p.reject_before_domain_write('update','a',g,'failed')
    assert p.store.read('groups',g)['State']=='Closed'
    assert p.store.read('groups',g)['WriteOwner'] is not None


def test_definite_stopped_prefix_supports_new_user_retry_without_duplicate_setup():
    p=Protocol();q=pending(p);key='accept';p.receipt(key,{'kind':'accept','request':q})
    p.decide(q,'Accepted',p.store.read('requests',q)['Version'],key)
    g=p.ensure_new_group(key,q);p.claim(key,'old',g['ID'],g['Version'])
    p.ensure_member(key,'old',q,g['ID'],1)
    # Simulate a known failure before dispatching the next membership write.
    p.pause_known_prefix(key,'old',g['ID'])
    with pytest.raises(Conflict,match='SEALED'):p.claim(key,'old',g['ID'],p.store.read('groups',g['ID'])['Version'])
    p.claim(key,'new',g['ID'],p.store.read('groups',g['ID'])['Version'])
    for actor in [1,2]:p.ensure_member(key,'new',q,g['ID'],actor)
    p.finish_accept(key,'new',q,g['ID'],[1,2])
    assert len(p.store.tables['groups'])==1 and len(p.store.tables['members'])==2
    assert p.success(key,g['ID'])['result']=='ACCEPTED'


def test_unknown_outcome_cannot_enter_normal_retry_or_steal_owner():
    p=Protocol();g=seeded_group(p);q,k=prepare_join(p,g,3)
    p.claim(k,'old',g,p.store.read('groups',g)['Version']);p.uncertain(k)
    with pytest.raises(SupportRequired,match='UNKNOWN'):p.pause_known_prefix(k,'old',g)
    with pytest.raises(Busy):p.claim(k,'new',g,p.store.read('groups',g)['Version'])


def test_conditional_helper_rejects_wildcard_and_disables_automatic_write_retry():
    with pytest.raises(ValueError):conditional_merge('site','uri','*',{})
    action=conditional_merge('site','uri',"@body('Read_revision')?['d']?['__metadata']?['etag']",{'Status':'Accepted'})
    assert action['inputs']['retryPolicy']=={'type':'none'}
    assert action['inputs']['parameters']['parameters/headers']['IF-MATCH']!='*'


def test_all_70_two_acceptor_order_preserving_interleavings():
    def schedules(a,b):
        if not a:yield b;return
        if not b:yield a;return
        for tail in schedules(a[1:],b):yield [a[0]]+tail
        for tail in schedules(a,b[1:]):yield [b[0]]+tail
    all_schedules=list(schedules([(3,i) for i in range(4)],[(4,i) for i in range(4)]))
    assert len(all_schedules)==70
    for schedule in all_schedules:
        p=Protocol();g=seeded_group(p);jobs={a:prepare_join(p,g,a) for a in [3,4]}
        v=p.store.read('groups',g)['Version'];stopped=set();completed=[]
        for actor,step in schedule:
            if actor in stopped:continue
            q,k=jobs[actor];attempt=str(actor)
            try:
                if step==0:p.claim(k,attempt,g,v)
                elif step==1:p.reserve_join(k,attempt,q,g,p.store.read('requests',q)['Version'])
                elif step==2:p.ensure_member(k,attempt,q,g,actor)
                else:p.finish_accept(k,attempt,q,g,[actor]);completed.append(actor)
            except Conflict:stopped.add(actor)
            assert p.count(g)<=3
            assert len([m for m in p.store.tables['members'].values() if m['ParticipantId'] in [3,4]])<=1
        assert len(completed)==1 and p.count(g)==3
