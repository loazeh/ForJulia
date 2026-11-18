import json
from pathlib import Path

import mlflow

mlflow.set_tracking_uri('http://host.docker.internal:5000')
runs=mlflow.search_runs(experiment_names=['churn'],output_format='list')
rows=[{'run_id':r.info.run_id,'params':r.data.params,'metrics':r.data.metrics,'tags':r.data.tags} for r in runs]
Path('/work/run_comparison.json').write_text(json.dumps(rows,indent=2))
print(json.dumps(rows,indent=2))
