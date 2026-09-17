import json, os, sys
from datetime import datetime, timezone

role=sys.argv[1] if len(sys.argv)>1 else 'ENERGY_ANALYST'
mission=sys.argv[2] if len(sys.argv)>2 else 'Analyze energy systems under evidence constraints.'
models=['huggingface-projects/llama-3.2-3B-Instruct','huggingface-projects/gemma-2-9b-it']
record={'role':role,'mission':mission,'models':models,'status':'UNREVIEWED_EXTERNAL_AGENT_OUTPUT','timestamp':datetime.now(timezone.utc).isoformat()}
os.makedirs('results',exist_ok=True)
with open(f'results/{role}.json','w') as f: json.dump(record,f,indent=2)
print(json.dumps(record))
