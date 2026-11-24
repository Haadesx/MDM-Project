import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

from cooperalink.artifacts import file_hash, read_json, write_json
from cooperalink.models import TIMESTRAL_SOURCE_REVISION, TIMESTRAL_WEIGHTS_REVISION
from cooperalink.pipeline import code_identity


def main():
    verification = ROOT / 'outputs' / 'verification'
    verification.mkdir(parents=True, exist_ok=True)
    python = ROOT / '.venv' / 'bin' / 'python'
    cli = ROOT / '.venv' / 'bin' / 'cooperalink'
    identity = code_identity()
    lock_hash = file_hash(ROOT / 'uv.lock')
    commands = {
        'pytest': [str(python), '-m', 'pytest', '-q'],
        'compileall': [str(python), '-m', 'compileall', '-q', 'src', 'scripts'],
        'demo': [str(cli), 'demo', '--config', 'config/demo.json', '--output', 'outputs/demo'],
        'demo_multiyear': [str(cli), 'demo', '--config', 'config/demo.json', '--multiyear', '--output', 'outputs/demo_multiyear'],
    }
    results = {}
    environment = os.environ.copy()
    environment.update({'OMP_NUM_THREADS': '4', 'OPENBLAS_NUM_THREADS': '4', 'MKL_NUM_THREADS': '4'})
    for name, command in commands.items():
        log = verification / f'{name}.log'
        try:
            with log.open('w', encoding='utf-8') as output:
                result = subprocess.run(command, cwd=ROOT, env=environment, stdout=output, stderr=subprocess.STDOUT, check=False)
            results[name] = {'command': command, 'returncode': result.returncode, 'log': str(log.relative_to(ROOT))}
        except OSError as exc:
            log.write_text(str(exc) + '\n', encoding='utf-8')
            results[name] = {'command': command, 'returncode': None, 'log': str(log.relative_to(ROOT))}
    unchanged = code_identity() == identity and file_hash(ROOT / 'uv.lock') == lock_hash
    engineering = unchanged and all(results[name]['returncode'] == 0 for name in ('pytest', 'compileall'))
    import pyarrow.parquet as pq
    demo_checks = {}
    evidence_paths = [verification / f'{name}.log' for name in commands]
    for name, expected in (('demo', 36), ('demo_multiyear', 504)):
        directory = ROOT / 'outputs' / name
        try:
            completion = read_json(directory / 'completion.json')
            prediction_path = directory / 'predictions.parquet'
            count = pq.read_metadata(prediction_path).num_rows
            valid = (results[name]['returncode'] == 0 and completion.get('demo_complete') is True
                     and completion.get('research_complete') is False and count == expected
                     and (directory / 'report.md').is_file() and (directory / 'report.html').is_file())
            demo_checks[name] = {'valid': valid, 'prediction_count': count, 'expected_count': expected}
            if prediction_path.is_file():
                evidence_paths.append(prediction_path)
        except (OSError, ValueError, KeyError):
            demo_checks[name] = {'valid': False, 'prediction_count': None, 'expected_count': expected}
    demo = unchanged and all(item['valid'] for item in demo_checks.values())
    smoke_path = verification / 'models-smoke.json'
    smoke_complete = False
    try:
        smoke = read_json(smoke_path)
        provenance, smoke_results = smoke['provenance'], smoke['results']
        smoke_complete = (smoke.get('genuine_smoke_complete') is True
                          and provenance['source_revision'] == TIMESTRAL_SOURCE_REVISION
                          and provenance['weights_revision'] == TIMESTRAL_WEIGHTS_REVISION
                          and provenance['checkpoint'] == 'mistralai/Timestral-209M'
                          and provenance['dtype'] == 'torch.float32'
                          and provenance['symmetric_averaging'] is True and provenance['clip_nonnegative'] is True
                          and all(smoke_results[name]['shape'] == [3, 30] and smoke_results[name]['finite'] is True
                                  and smoke_results[name]['status'] == ['ok'] * 3
                                  for name in ('timestral_count_only', 'timestral_graph'))
                          and all(smoke_results[name]['shape'] == [3, 30] and smoke_results[name]['finite'] is True
                                  and smoke_results[name]['status'] == ['constant_series', 'constant_series', 'ok']
                                  for name in ('arima', 'prophet')))
        evidence_paths.append(smoke_path)
    except (OSError, ValueError, KeyError, TypeError):
        pass
    evidence = {str(path.relative_to(ROOT)): file_hash(path) for path in sorted(evidence_paths)}
    receipt = {'code_hash': identity, 'lock_sha256': lock_hash, 'engineering_complete': engineering,
               'demo_complete': demo, 'genuine_smoke_complete': smoke_complete,
               'source_unchanged': unchanged, 'checks': results, 'demo_checks': demo_checks, 'evidence_sha256': evidence}
    write_json(verification / 'quality.json', receipt)
    print(json.dumps({'engineering_complete': engineering, 'demo_complete': demo, 'receipt': str((verification / 'quality.json').relative_to(ROOT))}))
    return 0 if engineering and demo and smoke_complete else 1


if __name__ == '__main__':
    raise SystemExit(main())
