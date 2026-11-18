from types import SimpleNamespace

import pytest

from scripts import promote


def run(f1, latency):
    return SimpleNamespace(info=SimpleNamespace(run_id='test-run', status='FINISHED'), data=SimpleNamespace(
        metrics={'f1':f1,'auc':0.8,'p95_latency_ms':latency},
        params={'model':'candidate','data_sha256':'abc'},tags={'model_uri':'models:/test'}))


def test_gate_excludes_slow_candidate(monkeypatch):
    monkeypatch.setattr(promote.mlflow,'search_runs',lambda **kwargs:[run(0.9,100),run(0.7,5)])
    assert promote.best_candidate('test')['f1'] == 0.7


def test_gate_rejects_all_slow_candidates(monkeypatch):
    monkeypatch.setattr(promote.mlflow,'search_runs',lambda **kwargs:[run(0.9,100)])
    with pytest.raises(SystemExit,match='BLOCKED'):
        promote.best_candidate('test')


def test_worse_model_does_not_promote(monkeypatch,tmp_path):
    import json
    baseline=tmp_path/'champion.json'
    baseline.write_text(json.dumps({'model':'champion','f1':0.7,'p95_latency_ms':5}))
    monkeypatch.setattr('sys.argv',['promote','--champion-file',str(baseline)])
    monkeypatch.setattr(promote,'best_candidate',lambda batch:{'model':'weak','f1':0.4,'p95_latency_ms':1})
    monkeypatch.setattr(promote,'promote',lambda candidate:pytest.fail('Blocked model must not be promoted'))
    assert promote.main() == 1

