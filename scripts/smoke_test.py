import json
import sys
import urllib.request
from pathlib import Path

base=(sys.argv[1] if len(sys.argv)>1 else 'http://localhost:8000').rstrip('/')
health=json.load(urllib.request.urlopen(base+'/health',timeout=5))
request=urllib.request.Request(base+'/predict',data=Path('sample_request.json').read_bytes(),headers={'Content-Type':'application/json'})
prediction=json.load(urllib.request.urlopen(request,timeout=5))
assert health['status']=='ok'
assert health['model_version'] and health['mlflow_run_id']
assert 0 <= prediction['churn_probability'] <= 1
print(json.dumps({'health':health,'prediction':prediction},indent=2))
print('PASS: smoke test ok')
