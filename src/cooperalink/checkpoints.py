from pathlib import Path

from .artifacts import digest, read_json, write_json
from .domain import DataContractError


def checkpoint(root: Path, model_id: str, origin: str, batch: int, identity: dict, compute):
    key = {'model_id': model_id, 'origin': origin, 'batch': batch, 'identity': identity}
    key_hash = digest(key)
    path = Path(root) / f'{key_hash}.json'
    if path.exists():
        try:
            envelope = read_json(path)
            payload = envelope['payload']
            if envelope['key'] != key or envelope['digest'] != digest(payload) or not isinstance(payload, list) or not all(isinstance(row, dict) and 'status' in row for row in payload):
                raise ValueError('invalid envelope')
        except (ValueError, TypeError, KeyError, OSError) as exc:
            raise DataContractError(f'Corrupt checkpoint {path}: {exc}') from exc
        if all(row['status'] != 'failed' for row in payload):
            return payload, True
    payload = compute()
    if not isinstance(payload, list) or not all(isinstance(row, dict) and 'status' in row for row in payload):
        raise DataContractError('Checkpoint payload must be a list of status records')
    envelope = {'key': key, 'payload': payload, 'digest': digest(payload)}
    if any(row['status'] == 'failed' for row in payload):
        write_json(Path(root) / f'{key_hash}-failure-{envelope["digest"]}.json', envelope)
    write_json(path, envelope)
    return payload, False
