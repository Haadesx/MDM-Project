import hashlib
import json
import re
import subprocess
from datetime import date
from pathlib import Path

from .domain import DataContractError


def dry_run_source(start: str, end: str, project: str | None = None, maximum_bytes_billed: int | None = None, execute: bool = False) -> dict:
    if execute:
        raise DataContractError('This source adapter only permits dry runs')
    try:
        first, last = date.fromisoformat(start), date.fromisoformat(end)
    except (TypeError, ValueError) as exc:
        raise DataContractError('Bounds must be ISO dates') from exc
    if first.isoformat() != start or last.isoformat() != end or not (date(2020, 1, 1) <= first < last <= date(2025, 1, 1)):
        raise DataContractError('Bounds must be within 2020-01-01 to 2025-01-01 and increasing')
    if maximum_bytes_billed is not None and (type(maximum_bytes_billed) is not int or maximum_bytes_billed <= 0):
        raise DataContractError('maximum_bytes_billed must be a positive integer')
    if project is not None and (not isinstance(project, str) or not re.fullmatch(r'[a-z][a-z0-9-]{4,28}[a-z0-9]', project)):
        raise DataContractError('Invalid Google Cloud project ID')
    query = (Path(__file__).resolve().parents[2] / 'sql' / 'extract_061.sql').read_text(encoding='utf-8')
    command = ['bq', '--format=json']
    if project:
        command.append(f'--project_id={project}')
    command += ['query', '--dry_run', '--use_legacy_sql=false',
                f'--parameter=start_dateadded:INT64:{first:%Y%m%d}000000',
                f'--parameter=end_dateadded:INT64:{last:%Y%m%d}000000']
    if maximum_bytes_billed is not None:
        command.append(f'--maximum_bytes_billed={maximum_bytes_billed}')
    try:
        result = subprocess.run(command, input=query, text=True, capture_output=True, check=True)
    except (OSError, subprocess.CalledProcessError) as exc:
        raise DataContractError(f'BigQuery dry run failed: {exc}') from exc
    estimate = None
    try:
        response = json.loads(result.stdout)
        estimate = int(response['statistics']['query']['totalBytesProcessed'])
    except (ValueError, KeyError, TypeError):
        match = re.search(r'process\s+([\d,]+)\s+bytes', result.stdout + '\n' + result.stderr, re.IGNORECASE)
        if match:
            estimate = int(match.group(1).replace(',', ''))
    return {'command': command, 'query_sha256': hashlib.sha256(query.encode()).hexdigest(),
            'start': start, 'end': end, 'estimated_bytes': estimate, 'executed': False,
            'stdout': result.stdout, 'stderr': result.stderr}
