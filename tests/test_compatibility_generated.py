"""Independent small WDL-subset execution check; not tenant certification.

Exercises emitted references, scoping, normalization and loops against fixed
expected fixtures, rather than only evaluating the source expression tree.
"""
import json
import re
from copy import deepcopy
from scripts.power_automate import build_compatibility_proof as proof


class Runner:
    def __init__(self):self.outputs={};self.variables={}
    def body(self,name):return self.outputs[name]

    def expr(self,text,context):
        tokens=re.findall(r"'(?:[^']|'')*'|-?\d+|[A-Za-z_][A-Za-z0-9_]*|[^\s]",text.lstrip('@'))
        at=0
        def value():
            nonlocal at
            t=tokens[at];at+=1
            if t.startswith("'"):result=t[1:-1].replace("''", "'")
            elif re.fullmatch(r'-?\d+',t):result=int(t)
            elif t in ['true','false','null']:result={'true':True,'false':False,'null':None}[t]
            else:
                assert tokens[at]=='(';at+=1;args=[]
                while tokens[at]!=')':
                    args.append(value())
                    if tokens[at]==',':at+=1
                at+=1
                def union(a,b):return list(dict.fromkeys(a+b))
                funcs={'body':self.body,'outputs':lambda n:self.outputs[n],
                    'variables':lambda n:self.variables[n],'item':lambda:context['item'],
                    'items':lambda n:context['items'][n],
                    'and':lambda *v:all(v),'or':lambda *v:any(v),'not':lambda v:not v,
                    'equals':lambda a,b:a==b,'greater':lambda a,b:a>b,'greaterOrEquals':lambda a,b:a>=b,
                    'lessOrEquals':lambda a,b:a<=b,'less':lambda a,b:a<b,'length':len,'empty':lambda v:v is None or v==[] or v=='',
                    'if':lambda c,a,b:a if c else b,'contains':lambda a,b:b in a,'union':union,
                    'intersection':lambda a,b:[v for v in union(a,a) if v in b],
                    'coalesce':lambda *v:next((x for x in v if x is not None),None),
                    'replace':lambda s,old,new:s.replace(old,new),'trim':lambda s:s.strip(),'toLower':lambda s:s.lower(),'json':json.loads,
                    'first':lambda a:a[0],'workflow':lambda:{'run':{'name':'local-subset-not-a-tenant-run'}},
                    'concat':lambda *a:''.join(str(x) for x in a),'int':int,
                    'string':lambda v:json.dumps(v,separators=(',',':')) if isinstance(v,(dict,list,bool)) else str(v),
                    'add':lambda a,b:a+b,'div':lambda a,b:a//b,'mod':lambda a,b:a%b,
                    'actions':lambda n:{'status':getattr(self,'action_states',{}).get(n,'Skipped')},
                    'triggerBody':lambda:context.get('triggerBody',{})}
                result=funcs[t](*args)
            while at<len(tokens) and tokens[at]=='?':
                at+=1;assert tokens[at]=='[';at+=1;key=value();assert tokens[at]==']';at+=1
                result=result.get(key) if result is not None else None
            return result
        result=value();assert at==len(tokens),(text,tokens[at:]);return result

    def inputs(self,v,ctx):
        if isinstance(v,str) and v.startswith('@'):return self.expr(v,ctx)
        if isinstance(v,dict):return {k:self.inputs(x,ctx) for k,x in v.items()}
        if isinstance(v,list):return [self.inputs(x,ctx) for x in v]
        return v

    def run(self,actions,ctx=None):
        ctx=ctx or {'items':{}};done=set();todo=dict(actions)
        while todo:
            ready=[n for n,a in todo.items() if set(a.get('runAfter',{}))<=done]
            assert ready,'Invalid dependency graph'
            for n in ready:
                a=todo.pop(n);kind=a['type'];inp=a.get('inputs',{})
                if kind=='Compose':self.outputs[n]=self.inputs(inp,ctx)
                elif kind=='ParseJson':self.outputs[n]=self.inputs(inp['content'],ctx)
                elif kind in ['Query','Select']:
                    rows=self.inputs(inp['from'],ctx);result=[]
                    for item in rows:
                        inner={**ctx,'item':item}
                        if kind=='Query':
                            if self.expr(inp['where'],inner):result.append(item)
                        else:result.append(self.inputs(inp['select'],inner))
                    self.outputs[n]=result
                elif kind=='InitializeVariable':
                    for var in inp['variables']:self.variables[var['name']]=deepcopy(var['value'])
                elif kind=='SetVariable':self.variables[inp['name']]=self.inputs(inp['value'],ctx)
                elif kind=='AppendToArrayVariable':self.variables[inp['name']].append(self.inputs(inp['value'],ctx))
                elif kind=='If':
                    branch=a['actions'] if self.expr(a['expression'],ctx) else a['else']['actions']
                    self.run(branch,ctx)
                elif kind=='Foreach':
                    for item in self.expr(a['foreach'],ctx):self.run(a['actions'],{**ctx,'items':{**ctx['items'],n:item}})
                elif kind=='Terminate':raise AssertionError(inp)
                else:raise AssertionError('Unsupported test action '+kind)
                done.add(n)


def test_generated_flow_scoping_and_results_match_all_fixtures():
    fixtures=json.loads((proof.ROOT/'tests/fixtures/compatibility_v1.json').read_text(encoding='utf-8'))
    runner=Runner();runner.run(proof.definition_actions(fixtures,'local-fixture','source-hash'))
    report=runner.outputs['Proof_report']
    assert report['allPassed'] and report['testCount']==39
    assert report['failedCases']==[]
    assert runner.outputs['Shared_Profiles'][0]['accountKey']=='synthetic-1'
    assert runner.outputs['Shared_Profiles'][13]['learnIds']==[]
