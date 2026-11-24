import subprocess

import pytest

from cooperalink.acquisition import dry_run_source
from cooperalink.domain import DataContractError


def test_dry_run_bounded_query(monkeypatch):
    calls = []
    def run(command, **kwargs):
        calls.append((command, kwargs))
        return subprocess.CompletedProcess(command, 0, '', 'Query successfully validated. Assuming the tables are not modified, running this query will process 1,234 bytes of data.')
    monkeypatch.setattr(subprocess, 'run', run)
    result = dry_run_source('2020-01-01', '2021-01-01', project='test-project', maximum_bytes_billed=2000)
    command, options = calls[0]
    assert '--dry_run' in command
    assert '--use_legacy_sql=false' in command
    assert '--parameter=start_dateadded:INT64:20200101000000' in command
    assert '--parameter=end_dateadded:INT64:20210101000000' in command
    assert '--maximum_bytes_billed=2000' in command
    assert "EventCode = '061'" in options['input']
    assert result['estimated_bytes'] == 1234
    assert result['executed'] is False


def test_invalid_bounds_or_execution_never_call_bq(monkeypatch):
    monkeypatch.setattr(subprocess, 'run', lambda *a, **k: pytest.fail('unexpected call'))
    for kwargs in ({'start': '2021-01-01', 'end': '2020-01-01'}, {'start': '2019-01-01', 'end': '2020-01-01'}, {'start': '2020-01-01', 'end': '2021-01-01', 'execute': True}, {'start': '2020-01-01', 'end': '2021-01-01', 'maximum_bytes_billed': 0}):
        with pytest.raises(DataContractError):
            dry_run_source(**kwargs)
