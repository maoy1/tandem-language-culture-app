"""Lower connector-incompatible Parse JSON patterns to built-in XPath guards.

The original action name/body and schema failure path stay stable. The typed
shape is parsed first, then only the patterned strings are projected to XML.
Unknown/optional/nullable patterns fail the build rather than dropping a guard.
No connectors, regex service, child runtime or extra control nesting is added.
"""
from copy import deepcopy
import re
from .schema_audit import wdl_string

UUID = '^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'
ETAG = '^"[0-9]+"$'
WEAK_ETAG = '^(W/)?"[0-9]+"$'
MEMBER = '^request:[1-9][0-9]*:participant:[1-9][0-9]*$'
PERSONAL = '^personal:[1-9][0-9]*:[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'


def uuid_test(value, lower=False):
    chars='0123456789abcdef' + ('' if lower else 'ABCDEF')
    tests=[f'string-length({value})=36', f"translate({value},'{chars}','')='----'"]
    tests += [f"substring({value},{i},1)='-'" for i in [9,14,19,24]]
    return '('+' and '.join(tests)+')'


def positive(value):
    return f"(string-length({value})>0 and contains('123456789',substring({value},1,1)) and translate({value},'0123456789','')='')"


def etag_test(value):
    return f'''(string-length({value})>=3 and substring({value},1,1)='"' and substring({value},string-length({value}),1)='"' and translate(substring({value},2,string-length({value})-2),'0123456789','')='')'''


def _predicate(pattern, value='.'):
    if pattern==UUID:return uuid_test(value)
    if pattern==ETAG:return etag_test(value)
    if pattern==WEAK_ETAG:
        return '('+etag_test(value)+f" or (starts-with({value},'W/') and "+etag_test(f'substring({value},3)')+'))'
    if pattern==MEMBER:
        left=f"substring-before(substring-after({value},'request:'),':participant:')"
        right=f"substring-after({value},':participant:')"
        return f"({value}=concat('request:',{left},':participant:',{right}) and {positive(left)} and {positive(right)})"
    if pattern==PERSONAL:
        left=f"substring-before(substring-after({value},'personal:'),':')"
        right=f"substring-after(substring-after({value},'personal:'),':')"
        return f"({value}=concat('personal:',{left},':',{right}) and {positive(left)} and {uuid_test(right,lower=True)})"
    raise ValueError('Unsupported native pattern; retain guard and define a lowering: '+pattern)


def predicate(pattern, value='.'):
    # JSON.NET/.NET regex '$' also matches immediately before one final LF.
    # Preserve that existing regex behavior instead of silently changing inputs.
    prefix=f'substring({value},1,string-length({value})-1)'
    return '('+_predicate(pattern,value)+f" or (substring({value},string-length({value}),1)='\n' and "+_predicate(pattern,prefix)+'))'


def split_schema(schema):
    """Return typed schema plus required singleton/root-array string paths."""
    clean=deepcopy(schema);found=[]
    array=clean.get('type')=='array'
    def visit(s,path=(),required=True):
        if not isinstance(s,dict) or not has_patterns(s):return
        if 'patternProperties' in s:raise ValueError('patternProperties needs an explicit native lowering')
        if 'pattern' in s:
            pattern=s.pop('pattern')
            if s.get('type')!='string' or not required:
                raise ValueError('Only required non-null string patterns have a native lowering')
            predicate(pattern)
            found.append((path,pattern))
        for key,child in s.get('properties',{}).items():
            if not re.fullmatch('[A-Za-z_][A-Za-z0-9_]*',key):raise ValueError('Unexpected schema property path: '+key)
            visit(child,path+(key,),required and key in s.get('required',[]))
        if isinstance(s.get('items'),dict):
            if path:raise ValueError('Nested patterned arrays require an explicit lowering')
            visit(s['items'],path,required)
        for keyword in ['allOf','anyOf','oneOf','not']:
            if keyword in s:raise ValueError('Composed pattern schema requires an explicit lowering')
    # Only walk schemas containing patterns. Existing complex non-pattern schemas
    # are untouched and need not fit this intentionally bounded adapter.
    if has_patterns(clean):visit(clean)
    return clean,found,array


def has_patterns(value):
    if isinstance(value,dict):return any(k in ['pattern','patternProperties'] or has_patterns(v) for k,v in value.items())
    if isinstance(value,list):return any(has_patterns(v) for v in value)
    return False


def lower(actions):
    """Mutate a definition before assembly and return its auditable change list."""
    changes=[];names=set()
    def inventory(block):
        for n,a in block.items():
            if n in names:raise ValueError('Duplicate action name: '+n)
            names.add(n)
            for child in children(a):inventory(child)
    inventory(actions)
    def visit(block):
        for name,action in list(block.items()):
            for child in children(action):visit(child)
            if action.get('type')!='ParseJson':continue
            clean,patterns,array=split_schema(action['inputs']['schema'])
            if not patterns:continue
            if clean.get('type') not in ['object','array']:
                raise ValueError('Pattern parser must reject boolean false at root')
            shape=name+'_NativeShape';projection=name+'_NativePatternValues'
            if shape in names or projection in names:raise ValueError('Native guard action name collision: '+name)
            names.update([shape,projection])
            old=deepcopy(action);old['inputs']['schema']=clean
            source='item()' if array else f"body('{shape}')"
            values={f'v{i}':'@'+source+''.join("?['"+k+"']" for k in path) for i,(path,_) in enumerate(patterns)}
            projected={'type':'Select','inputs':{'from':f"@body('{shape}')",'select':values}} if array else {'type':'Compose','inputs':values}
            projected['runAfter']={shape:['Succeeded']}
            rows=f"body('{projection}')" if array else f"outputs('{projection}')"
            xml=f"xml(json(concat('{{\"root\":{{\"row\":',string({rows}),'}}}}')))"
            tests=[f'count(/root/row/v{i}[not({predicate(pattern)})])=0' for i,(_,pattern) in enumerate(patterns)]
            # Projection fields are required by the preceding typed shape parser.
            # JSON->XML serializes root arrays as repeated row elements.
            xpath=' and '.join('('+test+')' for test in tests)
            block[shape]=old;block[projection]=projected
            action['inputs']={'content':f"@if(xpath({xml},{wdl_string(xpath)}),body('{shape}'),false)",'schema':deepcopy(clean)}
            action['runAfter']={projection:['Succeeded']}
            changes.append({'action':name,'shape':shape,'projection':projection,'patterns':[{'path':list(p),'pattern':r} for p,r in patterns]})
    visit(actions)
    return changes


def children(action):
    return [action.get('actions',{}),action.get('else',{}).get('actions',{}),action.get('default',{}).get('actions',{})]+[c.get('actions',{}) for c in action.get('cases',{}).values()]
