import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from cooperalink.artifacts import write_json
from cooperalink.models import load_timestral, forecast_classical


def main():
    adapter, provenance = load_timestral()
    counts = np.asarray([[0] * 90, [2] * 90, list(range(90))], dtype=float)
    results = {}
    for name, covariates in [('timestral_count_only', None), ('timestral_graph', np.zeros((3, 90, 2)))]:
        result = adapter.forecast(counts, covariates)
        results[name] = {'status': result['status'], 'error': result['error'], 'shape': list(result['forecast'].shape), 'finite': bool(np.isfinite(result['forecast']).all())}
    for name in ('arima', 'prophet'):
        result = forecast_classical(name, counts, '2023-01-01')
        results[name] = {'status': result['status'], 'error': result['error'], 'shape': list(result['forecast'].shape), 'finite': bool(np.isfinite(result['forecast']).all()), 'warnings': result['warnings'], 'diagnostics': result['diagnostics']}
    complete = all(result['shape'] == [3, 30] and result['finite'] and all(status != 'failed' for status in result['status']) for result in results.values())
    write_json(ROOT / 'outputs/verification/models-smoke.json', {'genuine_smoke_complete': complete, 'provenance': provenance, 'results': results})
    print('genuine_smoke_complete:', complete)
    return 0 if complete else 1


if __name__ == '__main__':
    raise SystemExit(main())
