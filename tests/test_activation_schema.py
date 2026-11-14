"""Guard equivalence and fail-closed execution of connector-safe Parse JSON."""
from copy import deepcopy
import json
from pathlib import Path
import random
import re
from lxml import etree
import pytest
from scripts.power_automate import activation_schema as native
from scripts.power_automate.solution_source import walk
from core_native_backend import ParentRunner


PATTERNS=[native.UUID,native.ETAG,native.WEAK_ETAG,native.MEMBER,native.PERSONAL]
VALID=['01234567-abcd-ABCD-1234-0123456789af','01234567-abcd-abcd-1234-0123456789af',
       '"1"','"000"','W/"12"','request:1:participant:2',
       'personal:123:01234567-abcd-abcd-1234-0123456789af']


@pytest.mark.parametrize('pattern',PATTERNS)
def test_xpath_matches_original_regex_including_boundaries_and_mutations(pattern):
    rng=random.Random(81)
    samples=['','*','0','-1','""','W/""','request:01:participant:2','request:1:participant:0']
    for value in VALID:
        samples += [value, value+'\n',value+'\r\n',value+'\n\n',' '+value,value+' ',value.upper(),value.lower()]
        for i in range(len(value)):
            samples += [value[:i]+value[i+1:],value[:i]+'z'+value[i+1:],value[:i]+':'+value[i:]]
    samples += [''.join(rng.choice('0123456789abcdefABCDEF-:"W/requestpicol ') for _ in range(rng.randrange(65))) for _ in range(400)]
    query=etree.XPath(native.predicate(pattern))
    for value in samples:
        node=etree.Element('v');node.text=value
        assert bool(query(node)) == bool(re.search(pattern,value)),(pattern,repr(value))


def parser(array=False):
    row={'type':'object','required':['__metadata','token'], 'properties':{
        '__metadata':{'type':'object','required':['etag'],'properties':{'etag':{'type':'string','pattern':native.ETAG}}},
        'token':{'type':'string','pattern':native.UUID}}}
    schema={'type':'array','items':row} if array else row
    return {'Read':{'type':'Compose','inputs':'@triggerBody()'},
            'Row':{'type':'ParseJson','inputs':{'content':"@outputs('Read')",'schema':schema},'runAfter':{'Read':['Succeeded']}},
            'Effect':{'type':'Compose','inputs':"@body('Row')",'runAfter':{'Row':['Succeeded']}}}


class NoIO:
    def request(self,*args):raise AssertionError('No connector may run')


@pytest.mark.parametrize('array',[False,True])
@pytest.mark.parametrize('invalid',['none','tag','uuid','type','missing','newline'])
def test_lowered_graph_preserves_body_and_blocks_followup_on_bad_values(array,invalid):
    actions=parser(array);native.lower(actions)
    row={'__metadata':{'etag':'"123"'},'token':VALID[0],'unrelated':'<b>plain text</b>'}
    if invalid=='tag':row['__metadata']['etag']='*'
    if invalid=='uuid':row['token']='invalid'
    if invalid=='type':row['token']=42
    if invalid=='missing':del row['token']
    if invalid=='newline':row['token']+='\n'
    data=[deepcopy(row),deepcopy(row)] if array else row
    runner=ParentRunner(NoIO());runner.run(actions,{'triggerBody':data,'items':{}})
    if invalid in ['none','newline']:
        assert runner.action_states['Effect']=='Succeeded'
        assert runner.outputs['Effect']==data
    else:
        assert runner.action_states['Effect']=='Skipped'
        assert runner.action_states['Row'] in ['Failed','Skipped']


def test_array_one_bad_record_rejects_all_and_empty_array_remains_valid():
    actions=parser(True);native.lower(actions)
    for data,expected in [([],True),([{'__metadata':{'etag':'"1"'},'token':VALID[0]}, {'__metadata':{'etag':'*'},'token':VALID[0]}],False)]:
        runner=ParentRunner(NoIO());runner.run(actions,{'triggerBody':data,'items':{}})
        assert (runner.action_states['Effect']=='Succeeded') is expected


def test_no_patterns_or_unknown_patterns_are_silently_weakened():
    actions=parser();before=deepcopy(actions);changes=native.lower(actions)
    assert len(changes)==1 and len(actions)==len(before)+2
    assert not native.has_patterns(actions)
    assert actions['Row_NativeShape']['runAfter']==before['Row']['runAfter']
    assert actions['Row']['inputs']['schema']['required']==before['Row']['inputs']['schema']['required']
    assert native.lower(actions)==[]
    for spec in [{'type':'string','pattern':'unknown'}, {'type':['string','null'],'pattern':native.UUID}]:
        bad={'type':'object','required':['x'],'properties':{'x':spec}}
        with pytest.raises(ValueError):native.split_schema(bad)


def test_all_delivered_pattern_parsers_lower_within_structure_limits():
    root=Path(__file__).resolve().parents[1]
    from scripts.power_automate.schema_audit import measure
    for path in (root/'artifacts/core_batch/v1.0.0.1/definitions').glob('*.json'):
        doc=json.loads(path.read_text());actions=doc['properties']['definition']['actions'];native.lower(actions)
        assert not native.has_patterns(actions)
        size=measure(actions);assert size['actions']<=500 and size['maximumActionDepth']<=8
        for name,a in walk(actions):
            for value in [a.get('inputs',{}).get('content') if isinstance(a.get('inputs'),dict) else None]:
                if isinstance(value,str):assert len(value)<8192,(path.name,name,len(value))
