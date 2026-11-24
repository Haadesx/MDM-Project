import csv
import hashlib
import json
import os
from contextlib import contextmanager
from pathlib import Path
from tempfile import NamedTemporaryFile


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


def file_hash(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


@contextmanager
def atomic_path(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(dir=path.parent, prefix=".tmp-", suffix=path.suffix, delete=False) as stream:
        temp = Path(stream.name)
    try:
        yield temp
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, value):
    with atomic_path(path) as temp:
        temp.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def write_csv(path, rows):
    with atomic_path(path) as temp, temp.open("w", newline="", encoding="utf-8") as stream:
        if rows:
            writer = csv.DictWriter(stream, list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)


def write_parquet(path, rows):
    import pyarrow as pa
    import pyarrow.parquet as pq

    table = rows if isinstance(rows, pa.Table) else pa.Table.from_pylist(rows)
    with atomic_path(path) as temp:
        pq.write_table(table, temp)


def read_parquet(path, filters=None):
    import pyarrow.parquet as pq

    return pq.read_table(path, filters=filters).to_pylist()
