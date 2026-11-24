import pytest

from cooperalink.checkpoints import checkpoint
from cooperalink.domain import DataContractError


def test_reuse_and_identity(tmp_path):
    calls = []
    def compute():
        calls.append(1)
        return [{'status': 'ok', 'score': 0.3}]
    args = (tmp_path, 'arima', '2024-01-01', 0)
    assert checkpoint(*args, {'input': 'a'}, compute) == ([{'status': 'ok', 'score': 0.3}], False)
    assert checkpoint(*args, {'input': 'a'}, compute)[1] is True
    assert checkpoint(*args, {'input': 'b'}, compute)[1] is False
    assert len(calls) == 2


def test_failed_rows_are_retried_and_corruption_rejected(tmp_path):
    args = (tmp_path, 'arima', '2024-01-01', 0, {'input': 'a'})
    assert checkpoint(*args, lambda: [{'status': 'failed'}])[1] is False
    assert checkpoint(*args, lambda: [{'status': 'ok'}]) == ([{'status': 'ok'}], False)
    assert checkpoint(*args, lambda: pytest.fail('unexpected compute'))[1] is True
    files = list(tmp_path.rglob('*.json'))
    assert len(files) >= 2
    for path in files:
        if 'failure' not in path.name:
            path.write_text('{')
    with pytest.raises(DataContractError):
        checkpoint(*args, lambda: pytest.fail('unexpected compute'))
