"""
Import data previously written by export_db.py.

    python scripts/import_db.py [--file export/data.json]

The file is treated as untrusted input: only the app's own tables and
columns are accepted, values go through parameterised inserts (no SQL is
built from the file), and everything is inserted in one transaction, so
either all rows load or none do. Uses ADMIN_DATABASE_URL.
"""
import argparse
import json
from pathlib import Path

import _bootstrap  # noqa: F401

from models.database import Base, create_tables, get_engine


class ImportRejected(ValueError):
    """The input file doesn't match the app's schema."""


def validate(data: object) -> dict[str, list[dict]]:
    if not isinstance(data, dict):
        raise ImportRejected("data.json must be an object mapping table names to lists of rows")
    unknown = set(data) - set(Base.metadata.tables)
    if unknown:
        raise ImportRejected(f"unknown tables: {sorted(unknown)}")
    for name, rows in data.items():
        if not isinstance(rows, list) or not all(isinstance(r, dict) for r in rows):
            raise ImportRejected(f"{name}: expected a list of row objects")
        columns = set(Base.metadata.tables[name].columns.keys())
        for row in rows:
            extra = set(row) - columns
            if extra:
                raise ImportRejected(f"{name}: unknown columns {sorted(extra)}")
    return data


def import_data(path: Path) -> int:
    data = validate(json.loads(path.read_text()))
    create_tables()
    total = 0
    with get_engine(read_only=False).begin() as conn:  # one transaction: all or nothing
        for table in Base.metadata.sorted_tables:  # parents before children
            rows = data.get(table.name) or []
            if rows:
                conn.execute(table.insert(), rows)
                total += len(rows)
    return total


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--file", default="export/data.json", type=Path)
    args = parser.parse_args(argv)
    try:
        print(f"Imported {import_data(args.file)} rows from {args.file}")
    except ImportRejected as exc:
        print(f"Import rejected: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
