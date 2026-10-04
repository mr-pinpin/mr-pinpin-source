"""Pure bounded business descriptor and JSON validation; no transport or Store access."""
import copy
import json
import math
import re
from model import StudioError
PROTOCOL = 'pinpin-business-json-v1'
HASH = re.compile(r'^[a-f0-9]{64}$')
OP = re.compile(r'^[a-z][a-z0-9]*(?:[.-][a-z0-9]+)*$')
RESERVED = {'conversation','runtime','transport','authority','kernel','agent','fleet','account','credentials','filesystem'}
FORBIDDEN = {'path','filepath','storagepath','url','endpoint','route','transport','credentials','constructor','prototype'}
MAX_REQUEST = 1024 * 1024

def fail(message, status=400):
    raise StudioError(message, 'business_contract', status)

def integer(value, low, high):
    return type(value) is int and low <= value <= high

def bounded_json(value, maximum):
    # Reject oversize scalar strings before JSONEncoder allocates escaped strings.
    def inspect(v, depth=0):
        if depth > 16: fail('JSON nesting exceeds bound', 413)
        if v is None or type(v) is bool: return
        if type(v) in (int, float):
            if not math.isfinite(v): fail('Nonfinite JSON number')
            return
        if isinstance(v, str):
            if len(v) > maximum: fail('JSON response exceeds bound', 413)
            return
        if isinstance(v, (dict, list)):
            if len(v) > maximum: fail('JSON container exceeds bound', 413)
            if isinstance(v, dict):
                for key, val in v.items():
                    if not isinstance(key, str): fail('JSON keys must be strings')
                    inspect(key, depth+1); inspect(val, depth+1)
            else:
                for item in v: inspect(item, depth+1)
            return
        fail('Non-JSON business result')
    inspect(value)
    chunks=[]; total=0
    for chunk in json.JSONEncoder(ensure_ascii=False, allow_nan=False, separators=(',',':')).iterencode(value):
        # Encode in bounded slices rather than making a full unbounded UTF-8 buffer.
        for start in range(0,len(chunk),4096):
            raw=chunk[start:start+4096].encode('utf-8'); total+=len(raw)
            if total>maximum: fail('JSON response exceeds bound', 413)
            chunks.append(raw)
    return b''.join(chunks)

def validate_schema(node, depth=0, budget=None):
    if budget is None: budget=[0]
    budget[0]+=1
    if not isinstance(node,dict) or depth>8 or budget[0]>256: fail('Invalid bounded schema')
    allowed={'id':{'type','maxLength'},'hash':{'type'},'enum':{'type','values'},'text':{'type','maxLength'},'integer':{'type','minimum','maximum'},'number':{'type','minimum','maximum'},'boolean':{'type'},'array':{'type','maxItems','items'},'object':{'type','fields','required'}}.get(node.get('type'))
    if allowed is None or set(node)-allowed: fail('Unknown schema field')
    kind=node['type']
    if kind in ('id','text') and not integer(node.get('maxLength'),1,160 if kind=='id' else 16000): fail('Unbounded string schema')
    if kind=='enum' and (not isinstance(node.get('values'),list) or not 1<=len(node['values'])<=32 or any(not isinstance(v,str) or len(v)>160 for v in node['values'])): fail('Invalid enum')
    if kind in ('number','integer'):
        lo,hi=node.get('minimum'),node.get('maximum')
        if type(lo) not in (int,float) or type(hi) not in (int,float) or not math.isfinite(lo) or not math.isfinite(hi) or lo>hi or (kind=='integer' and (type(lo) is not int or type(hi) is not int or abs(lo)>9007199254740991 or abs(hi)>9007199254740991)): fail('Invalid numeric schema')
    if kind=='array':
        if not integer(node.get('maxItems'),1,512): fail('Unbounded array')
        validate_schema(node.get('items'),depth+1,budget)
    if kind=='object':
        fields,required=node.get('fields'),node.get('required')
        if not isinstance(fields,dict) or len(fields)>64 or not isinstance(required,list) or len(required)>64 or any(not isinstance(k,str) for k in required) or len(set(required))!=len(required) or set(required)-set(fields): fail('Invalid object schema')
        for key,val in fields.items():
            if not re.fullmatch(r'[A-Za-z][A-Za-z0-9]{0,63}',key) or key.lower() in FORBIDDEN: fail('Forbidden request selector')
            validate_schema(val,depth+1,budget)

def value_valid(node,value):
    kind=node['type']
    if kind=='id': return isinstance(value,str) and len(value)<=node['maxLength'] and bool(re.fullmatch(r'[A-Za-z0-9_.-]+',value))
    if kind=='hash': return isinstance(value,str) and bool(HASH.fullmatch(value))
    if kind=='text': return isinstance(value,str) and len(value)<=node['maxLength']
    if kind=='enum': return isinstance(value,str) and value in node['values']
    if kind=='boolean': return type(value) is bool
    if kind in ('number','integer'):
        if type(value) not in ((int,) if kind=='integer' else (int,float)): return False
        if type(value) is int and abs(value)>9007199254740991: return False
        return math.isfinite(value) and node['minimum']<=value<=node['maximum']
    if kind=='array': return isinstance(value,list) and len(value)<=node['maxItems'] and all(value_valid(node['items'],v) for v in value)
    if kind=='object': return isinstance(value,dict) and not set(value)-set(node['fields']) and not set(node['required'])-set(value) and all(value_valid(node['fields'][k],v) for k,v in value.items())
    return False

def metadata(operations, sha):
    if not isinstance(sha,str) or not HASH.fullmatch(sha) or not isinstance(operations,list) or len(operations)>64: fail('Invalid capability registry')
    seen=set()
    for op in operations:
        if not isinstance(op,dict) or set(op)-{'id','effect','method','request','maxRequestBytes','maxResponseBytes','timeoutMs'}: fail('Unknown descriptor field')
        identifier=op.get('id')
        if not isinstance(identifier,str) or len(identifier)>80 or not OP.fullmatch(identifier) or re.split('[.-]',identifier)[0] in RESERVED or identifier in seen: fail('Invalid operation ID')
        seen.add(identifier)
        if op.get('effect') not in ('read','mutation') or op.get('method')!='POST' or not integer(op.get('maxRequestBytes'),1,MAX_REQUEST) or not integer(op.get('maxResponseBytes'),1,1024*1024) or not integer(op.get('timeoutMs'),1,10000) or (not isinstance(op.get('request'),dict) or op['request'].get('type')!='object'): fail('Invalid descriptor bounds')
        validate_schema(op['request'])
    result={'schemaVersion':1,'protocol':PROTOCOL,'businessHash':sha,'operations':copy.deepcopy(operations)}
    bounded_json(result,65536)
    return result
