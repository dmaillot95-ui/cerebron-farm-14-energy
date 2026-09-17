#!/usr/bin/env python3
import json, os, subprocess, sys, hashlib
from pathlib import Path

PREFERRED=['/generate','/chat','/predict','/respond','/infer','/run']

def run(cmd, timeout=240):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)

def build_payload(spec, prompt):
    payload={}; prompt_set=False
    for p in spec.get('parameters',[]):
        name=p.get('name',''); lname=name.lower(); required=bool(p.get('required',False)); default=p.get('default'); typ=(p.get('type') or {}).get('type')
        if lname in {'message','prompt','text','query','input','instruction','user_message'}:
            payload[name]=prompt; prompt_set=True
        elif lname in {'chat_history','history','messages'}:
            payload[name]=[]
        elif lname in {'max_new_tokens','max_tokens','maximum_new_tokens'}:
            payload[name]=900
        elif lname=='temperature': payload[name]=0.1
        elif lname=='top_p': payload[name]=0.9
        elif lname=='top_k': payload[name]=40
        elif lname in {'system','system_prompt'}:
            payload[name]='Rigorous energy-systems research. CLAIM<=EVIDENCE. SIMULATION!=TEST.'
        elif required and default is None:
            if typ=='string' and not prompt_set:
                payload[name]=prompt; prompt_set=True
            else:
                return None
    return payload if prompt_set else None

def extract_text(raw):
    raw=raw.strip()
    try:
        obj=json.loads(raw)
        if isinstance(obj,dict):
            for k in ('Response','response','text','output','message'):
                if isinstance(obj.get(k),str): return obj[k].strip()
    except Exception:
        pass
    return raw

def invoke(space,prompt):
    info=run(['hf-gradio','info',space],120)
    if info.returncode!=0:
        return False,'',{'stage':'info','error':(info.stderr or info.stdout)[-1200:]}
    try:
        api=json.loads(info.stdout)
    except Exception as e:
        return False,'',{'stage':'decode','error':repr(e)}
    endpoints=list(api.items())
    endpoints.sort(key=lambda kv:(PREFERRED.index(kv[0]) if kv[0] in PREFERRED else 99,kv[0]))
    errors=[]
    for endpoint,spec in endpoints:
        payload=build_payload(spec,prompt)
        if payload is None: continue
        pred=run(['hf-gradio','predict',space,endpoint,json.dumps(payload,ensure_ascii=False)],240)
        if pred.returncode==0 and (pred.stdout or '').strip():
            text=extract_text(pred.stdout)
            if text:
                return True,text,{'stage':'predict','endpoint':endpoint,'sha256':hashlib.sha256(text.encode()).hexdigest()}
        errors.append((pred.stderr or pred.stdout)[-700:])
    return False,'',{'stage':'predict','error':' | '.join(errors[-3:]) or 'No compatible endpoint'}

role=sys.argv[1] if len(sys.argv)>1 else 'ENERGY_ANALYST'
mission=sys.argv[2] if len(sys.argv)>2 else 'Analyze energy systems under evidence constraints.'
spaces=['huggingface-projects/llama-3.2-3B-Instruct','huggingface-projects/gemma-2-9b-it']
space=spaces[sum(ord(c) for c in role)%len(spaces)]
prompt=f'''CEREBRON OMEGA — FARM 14 ENERGY\nROLE: {role}\nMISSION: {mission}\n\nSeparate DATA / MODEL / SIMULATION / TEST / OPERATIONS. Quantify assumptions where possible. Analyze efficiency, reliability, safety, cost, materials, grid constraints, failure modes, validation path and unknowns. REALITY>COHERENCE; CLAIM<=EVIDENCE; SIMULATION!=TEST; UNKNOWN remains UNKNOWN.'''
ok,text,meta=invoke(space,prompt)
record={'role':role,'model':space,'inference_success':bool(ok),'status':'UNREVIEWED_EXTERNAL_AGENT_OUTPUT' if ok else 'EXTERNAL_INFERENCE_FAILED','response':text if ok else None,'meta':meta}
Path('results').mkdir(exist_ok=True)
Path(f'results/{role}.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'role':role,'inference_success':bool(ok),'model':space}))
