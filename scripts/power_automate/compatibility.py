"""Issue 9: one rule tree evaluated locally and compiled into Power Automate.

Python is a build/test tool only. Generated expressions/actions are the runtime.
"""
from __future__ import annotations
from copy import deepcopy
from dataclasses import dataclass
import re

VERSION = 1
ROLE_FIELDS = ('teachIds','learnIds','shareCultureIds','learnCultureIds')
MAX_PROFILES = 500
ANY_LANGUAGE_POLICY = 'deferred_exclude_from_matching_and_focus'


def unique(values): return list(dict.fromkeys(values))


@dataclass(frozen=True)
class Expr:
    op: str
    args: tuple

    def evaluate(self, context):
        if self.op=='ref':
            value=context[self.args[0]]
            for key in self.args[1:]: value=value[key]
            return value
        if self.op=='lit': return self.args[0]
        values=[a.evaluate(context) for a in self.args]
        fns={
            'and':lambda *v:all(v),'or':lambda *v:any(v),'not':lambda v:not v,
            'equals':lambda a,b:a==b,'greater':lambda a,b:a>b,
            'greaterOrEquals':lambda a,b:a>=b,'lessOrEquals':lambda a,b:a<=b,
            'empty':lambda v:v is None or v=='' or v==[],
            'length':len,'contains':lambda a,b:b in a,
            'union':lambda a,b:unique(a+b),
            'intersection':lambda a,b:[x for x in unique(a) if x in b],
            'if':lambda c,a,b:a if c else b,
        }
        return fns[self.op](*values)

    def wdl(self, bindings):
        if self.op=='ref': return bindings[self.args[0]]+''.join("?['"+k+"']" for k in self.args[1:])
        if self.op=='lit':
            v=self.args[0]
            if v is True:return 'true'
            if v is False:return 'false'
            if v is None:return 'null'
            if v==[]:return "json('[]')"
            if isinstance(v,int):return str(v)
            return "'"+str(v).replace("'","''")+"'"
        return self.op+'('+','.join(a.wdl(bindings) for a in self.args)+')'


def ref(*path): return Expr('ref',path)
def lit(value): return Expr('lit',(value,))
def op(name,*args): return Expr(name,tuple(a if isinstance(a,Expr) else lit(a) for a in args))
def conjunction(*args): return op('and',*args)
def disjunction(*args): return op('or',*args)


def role_overlap(profile,group):
    return disjunction(*[op('not',op('empty',op('intersection',ref(profile,field),ref(group,focus))))
        for field,focus in [('teachIds','languageFocusIds'),('learnIds','languageFocusIds'),
                            ('shareCultureIds','cultureFocusIds'),('learnCultureIds','cultureFocusIds')]])


def available(profile):
    return conjunction(op('equals',ref(profile,'status'),'Active'),
        op('equals',ref(profile,'participationStatus'),'Active'),
        op('equals',ref(profile,'openToConnections'),True),
        op('not',op('empty',ref(profile,'accountKey'))),
        disjunction(*[op('not',op('empty',ref(profile,f))) for f in ROLE_FIELDS]))


def pair_rules():
    overlaps={
        'canLearnLanguageIds':op('intersection',ref('left','learnIds'),ref('right','teachIds')),
        'canShareLanguageIds':op('intersection',ref('left','teachIds'),ref('right','learnIds')),
        'canLearnCultureIds':op('intersection',ref('left','learnCultureIds'),ref('right','shareCultureIds')),
        'canShareCultureIds':op('intersection',ref('left','shareCultureIds'),ref('right','learnCultureIds'))}
    has_language=disjunction(*[op('not',op('empty',overlaps[f])) for f in ['canLearnLanguageIds','canShareLanguageIds']])
    has_culture=disjunction(*[op('not',op('empty',overlaps[f])) for f in ['canLearnCultureIds','canShareCultureIds']])
    eligible=conjunction(available('left'),available('right'),
        op('not',op('equals',ref('left','profileId'),ref('right','profileId'))),
        op('not',op('equals',ref('left','accountKey'),ref('right','accountKey'))),
        disjunction(has_language,has_culture))
    fit_type=op('if',eligible,op('if',conjunction(has_language,has_culture),'Combined',op('if',has_language,'Language','Culture')),None)
    return {'eligible':eligible,'fitType':fit_type,
        **{k:op('if',eligible,v,[]) for k,v in overlaps.items()}}


def distinct_relationship():
    return conjunction(op('not',op('empty',ref('sharers'))),op('not',op('empty',ref('learners'))),
        op('greater',op('length',op('union',ref('sharers'),ref('learners'))),1))


def member_supports_focus(field):
    return conjunction(op('equals',ref('member','status'),'Active'),op('contains',ref('member',field),ref('focus')))


def group_rules():
    language=op('not',op('empty',ref('group','languageFocusIds')))
    culture=op('not',op('empty',ref('group','cultureFocusIds')))
    type_valid=disjunction(
        conjunction(op('equals',ref('group','exchangeType'),'Language'),language,op('not',culture)),
        conjunction(op('equals',ref('group','exchangeType'),'Culture'),culture,op('not',language)),
        conjunction(op('equals',ref('group','exchangeType'),'Combined'),language,culture))
    known_focus=conjunction(*[op('equals',op('length',op('intersection',ref('group',f),ref('catalogues',c))),op('length',ref('group',f)))
        for f,c in [('languageFocusIds','concreteLanguageIds'),('cultureFocusIds','cultureIds')]])
    unique_members=op('equals',op('length',ref('group','memberProfileIds')),
                      op('length',op('union',ref('group','memberProfileIds'),ref('group','memberProfileIds'))))
    members_found=op('equals',op('length',ref('members')),op('length',ref('group','memberProfileIds')))
    purpose=conjunction(type_valid,known_focus,unique_members,members_found,
        op('empty',ref('unsupportedFocuses')),op('empty',ref('unrelatedMembers')))
    capacity=conjunction(op('greaterOrEquals',ref('group','capacity'),2),
        op('lessOrEquals',ref('group','capacity'),op('if',op('equals',ref('group','exchangeType'),'Language'),3,10)),
        op('greaterOrEquals',ref('group','capacity'),op('length',ref('group','memberProfileIds'))))
    candidate_participates=conjunction(op('equals',ref('candidate','status'),'Active'),role_overlap('candidate','group'))
    compatible=conjunction(purpose,capacity,candidate_participates,available('candidate'),
        op('equals',ref('group','state'),'Open'),op('equals',ref('group','setupComplete'),True),
        op('equals',ref('group','focusSharersAvailable'),True),
        op('greater',ref('group','capacity'),op('length',ref('group','memberProfileIds'))),
        op('not',op('contains',ref('group','memberProfileIds'),ref('candidate','profileId'))))
    return {'purposeValid':purpose,'capacityValid':capacity,'candidateParticipates':candidate_participates,'compatible':compatible}


def _ids(value,label):
    if value is None:return []
    if not isinstance(value,list) or any(type(v) is not int or v<=0 for v in value):
        raise ValueError(label+' must contain positive integer IDs')
    return unique(value)


def normalize_catalogues(raw):
    if 'anyLanguageId' not in raw:raise ValueError('Adapter must declare anyLanguageId (null when absent)')
    result={k:_ids(raw[k],k) for k in ['languageIds','cultureIds','timezoneIds']}
    any_id=raw.get('anyLanguageId')
    if any_id is not None and (type(any_id) is not int or any_id<=0):raise ValueError('Invalid anyLanguageId')
    result['anyLanguageId']=any_id
    result['concreteLanguageIds']=[v for v in result['languageIds'] if v!=any_id]
    return result


def normalize_profiles(raw,catalogues):
    if not isinstance(raw,list) or len(raw)>MAX_PROFILES:raise ValueError('Profile batch limit exceeded or invalid array')
    normalized=[]
    for p in raw:
        if type(p.get('profileId')) is not int or p['profileId']<=0:raise ValueError('Invalid profileId')
        if not isinstance(p.get('accountKey'),str) or not p['accountKey'].strip():raise ValueError('Missing accountKey')
        if not isinstance(p.get('status'),str) or not p['status'].strip():raise ValueError('Missing validation status')
        if p.get('participationStatus') not in ['Active','Paused','Inactive']:raise ValueError('Missing/invalid participationStatus')
        if type(p.get('openToConnections')) is not bool:raise ValueError('Missing/invalid openToConnections')
        q={k:p[k] for k in ['profileId','status','participationStatus','openToConnections']}
        q['accountKey']=p['accountKey'].strip().lower()
        for f in ROLE_FIELDS:
            values=_ids(p.get(f),f); allowed=catalogues['languageIds' if f in ROLE_FIELDS[:2] else 'cultureIds']
            if any(v not in allowed for v in values):raise ValueError('Unknown/inactive catalogue ID: '+f)
            q[f]=[v for v in values if not(f in ROLE_FIELDS[:2] and v==catalogues['anyLanguageId'])]
        zone=p.get('timezoneId')
        if zone is not None and (type(zone) is not int or zone not in catalogues['timezoneIds']):raise ValueError('Invalid optional timezoneId')
        q['timezoneId']=zone
        normalized.append(q)
    if len({p['profileId'] for p in normalized})!=len(normalized):raise ValueError('Duplicate profileId')
    if len({p['accountKey'] for p in normalized})!=len(normalized):raise ValueError('Duplicate canonical accountKey')
    return normalized


def evaluate_pair(left,right):return {k:r.evaluate({'left':left,'right':right}) for k,r in pair_rules().items()}


def evaluate_group(group,profiles,candidate,catalogues):
    members=[p for p in profiles if p['profileId'] in group['memberProfileIds']]
    unsupported=[]
    for focus_field,share,learn in [('languageFocusIds','teachIds','learnIds'),('cultureFocusIds','shareCultureIds','learnCultureIds')]:
        for focus in group[focus_field]:
            c={'sharers':[p['profileId'] for p in members if member_supports_focus(share).evaluate({'member':p,'focus':focus})],
               'learners':[p['profileId'] for p in members if member_supports_focus(learn).evaluate({'member':p,'focus':focus})]}
            if not distinct_relationship().evaluate(c):unsupported.append(focus)
    unrelated=[p for p in members if not conjunction(op('equals',ref('member','status'),'Active'),role_overlap('member','group')).evaluate({'member':p,'group':group})]
    ctx={'group':group,'members':members,'candidate':candidate,'catalogues':catalogues,
         'unsupportedFocuses':unsupported,'unrelatedMembers':unrelated}
    return {k:r.evaluate(ctx) for k,r in group_rules().items()}


def raw_profile_schema():
    props={'profileId':{'type':'integer','minimum':1},'accountKey':{'type':'string'},'status':{'type':'string','minLength':1},
        'participationStatus':{'type':'string','enum':['Active','Paused','Inactive']},'openToConnections':{'type':'boolean'},
        'timezoneId':{'type':['integer','null'],'minimum':1}}
    props.update({k:{'type':['array','null'],'items':{'type':'integer','minimum':1}} for k in ROLE_FIELDS})
    return {'type':'array','maxItems':MAX_PROFILES,'items':{'type':'object',
        'required':['profileId','accountKey','status','participationStatus','openToConnections'],'properties':props}}


def group_schema():
    props={'groupId':{'type':'integer','minimum':1},'exchangeType':{'type':'string'},
        'state':{'type':'string','enum':['Open','Closed','Ended']},'capacity':{'type':'integer'},
        'setupComplete':{'type':'boolean'},'focusSharersAvailable':{'type':'boolean'}}
    props.update({k:{'type':'array','items':{'type':'integer','minimum':1}} for k in ['languageFocusIds','cultureFocusIds','memberProfileIds']})
    return {'type':'object','required':list(props),'properties':props}


def compose(inputs,previous=None):return {'type':'Compose','inputs':inputs,'runAfter':{previous:['Succeeded']} if previous else {}}


def query(source,where,previous=None):
    return {'type':'Query','inputs':{'from':source,'where':'@'+where},'runAfter':{previous:['Succeeded']} if previous else {}}


def normalization_actions(prefix,raw_profiles,raw_catalogues,previous=None):
    """Raw inputs must be outputs/body expressions from trusted server adapters.

    Throws at runtime on malformed input or duplicate identity; does not authorize
    caller IDs. Any language is accepted as known but excluded from matching.
    """
    if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*',prefix):raise ValueError('Invalid action prefix')
    n=lambda s:prefix+'_'+s
    a={n('Parse_profiles'):{'type':'ParseJson','inputs':{'content':raw_profiles,'schema':raw_profile_schema()},'runAfter':{previous:['Succeeded']} if previous else {}}}
    cat_schema={'type':'object','required':['languageIds','cultureIds','timezoneIds','anyLanguageId'],'properties':{
        **{k:{'type':'array','items':{'type':'integer','minimum':1}} for k in ['languageIds','cultureIds','timezoneIds']},
        'anyLanguageId':{'type':['integer','null'],'minimum':1}}}
    a[n('Parse_catalogues')]={'type':'ParseJson','inputs':{'content':raw_catalogues,'schema':cat_schema},'runAfter':{n('Parse_profiles'):['Succeeded']}}
    cat="body('"+n('Parse_catalogues')+"')"
    a[n('Concrete_languages')]=query('@'+cat+"?['languageIds']","not(equals(item(),"+cat+"?['anyLanguageId']))",n('Parse_catalogues'))
    checks=["not(empty(trim(item()?['accountKey'])))","not(empty(trim(item()?['status'])))"]
    for f in ROLE_FIELDS:
        ids="union(coalesce(item()?['"+f+"'],json('[]')),coalesce(item()?['"+f+"'],json('[]')))"
        key='languageIds' if f in ROLE_FIELDS[:2] else 'cultureIds'
        checks.append("equals(length(intersection("+ids+','+cat+"?['"+key+"'])),length("+ids+'))')
    checks.append("or(equals(item()?['timezoneId'],null),contains("+cat+"?['timezoneIds'],item()?['timezoneId']))")
    a[n('Invalid_profiles')]=query("@body('"+n('Parse_profiles')+"')",'not(and('+','.join(checks)+'))',n('Concrete_languages'))
    selection={k:"@item()?['"+k+"']" for k in ['profileId','status','participationStatus','openToConnections','timezoneId']}
    selection['accountKey']="@toLower(trim(item()?['accountKey']))"
    for f in ROLE_FIELDS:
        allowed="body('"+n('Concrete_languages')+"')" if f in ROLE_FIELDS[:2] else cat+"?['cultureIds']"
        selection[f]="@intersection(union(coalesce(item()?['"+f+"'],json('[]')),coalesce(item()?['"+f+"'],json('[]'))),"+allowed+')'
    a[n('Profiles')]={'type':'Select','inputs':{'from':"@body('"+n('Parse_profiles')+"')",'select':selection},'runAfter':{n('Invalid_profiles'):['Succeeded']}}
    prev=n('Profiles')
    for key in ['accountKey','profileId']:
        name=n('Keys_'+key); a[name]={'type':'Select','inputs':{'from':"@body('"+n('Profiles')+"')",'select':"@item()?['"+key+"']"},'runAfter':{prev:['Succeeded']}};prev=name
    valid=["empty(body('"+n('Invalid_profiles')+"'))"]
    for key in ['accountKey','profileId']:
        ids="body('"+n('Keys_'+key)+"')";valid.append('equals(length('+ids+'),length(union('+ids+','+ids+')))')
    a[n('Require_valid_input')]={'type':'If','expression':'@and('+','.join(valid)+')','runAfter':{prev:['Succeeded']},'actions':{},'else':{'actions':{
        n('Reject_input'):{'type':'Terminate','inputs':{'runStatus':'Failed','runError':{'code':'INVALID_COMPATIBILITY_INPUT','message':'Malformed, unknown/inactive ID, duplicate identity or incomplete adapter input.'}},'runAfter':{}}}}}
    a[n('Catalogues')]=compose({'concreteLanguageIds':"@body('"+n('Concrete_languages')+"')",'cultureIds':'@'+cat+"?['cultureIds']"},n('Require_valid_input'))
    return a


def pair_expression_projection(left,right):
    return {k:'@'+v.wdl({'left':left,'right':right}) for k,v in pair_rules().items()}


def group_action_fragment(prefix,group,members,candidate,catalogues,focus_checks_variable,previous=None):
    """Embed in a sequential caller scope; initialize/reset focus_checks_variable.

    Returns rules only. Adapter supplies fresh active membership IDs, count and
    focusSharersAvailable evidence; unknown evidence must be false, not assumed.
    """
    n=lambda s:prefix+'_'+s
    actions={};prev=previous
    for kind,focus_field,share,learn in [('Language','languageFocusIds','teachIds','learnIds'),('Culture','cultureFocusIds','shareCultureIds','learnCultureIds')]:
        loop=n(kind+'_focus'); inner={};last=None
        for role,field in [('Sharers',share),('Learners',learn)]:
            q=n(kind+'_'+role)
            inner[q]=query('@'+members,member_supports_focus(field).wdl({'member':'item()','focus':"items('"+loop+"')"}),last)
            ids=n(kind+'_'+role+'_ids');inner[ids]={'type':'Select','inputs':{'from':"@body('"+q+"')",'select':"@item()?['profileId']"},'runAfter':{q:['Succeeded']}};last=ids
        bindings={k:"body('"+n(kind+'_'+s+'_ids')+"')" for k,s in [('sharers','Sharers'),('learners','Learners')]}
        inner[n(kind+'_Check')]={'type':'AppendToArrayVariable','inputs':{'name':focus_checks_variable,'value':{
            'kind':kind,'focusId':"@items('"+loop+"')",'supported':'@'+distinct_relationship().wdl(bindings)}},'runAfter':{last:['Succeeded']}}
        actions[loop]={'type':'Foreach','foreach':'@'+group+"?['"+focus_field+"']",'actions':inner,
            'runtimeConfiguration':{'concurrency':{'repetitions':1}},'runAfter':{prev:['Succeeded']} if prev else {}};prev=loop
    actions[n('Unsupported')]=query("@variables('"+focus_checks_variable+"')","not(equals(item()?['supported'],true))",prev)
    actions[n('Unrelated_members')]=query('@'+members,'not('+conjunction(op('equals',ref('member','status'),'Active'),role_overlap('member','group')).wdl({'member':'item()','group':group})+')',n('Unsupported'))
    bindings={'group':group,'members':members,'candidate':candidate,'catalogues':catalogues,
              'unsupportedFocuses':"body('"+n('Unsupported')+"')",'unrelatedMembers':"body('"+n('Unrelated_members')+"')"}
    actions[n('Result')]=compose({k:'@'+r.wdl(bindings) for k,r in group_rules().items()},n('Unrelated_members'))
    return actions
