"""
Export the schema (DDL) and data (JSON) of the app's tables.

    python scripts/export_db.py [--out export]

Writes <out>/schema.sql and <out>/data.json (the default ./export is gitignored).
Only the tables defined by the app are exported; nothing else is reflected.
"""
import argparse
import json
from pathlib import Path

import _bootstrap  # noqa: F401
from sqlalchemy.schema import CreateTable

from models.database import Base, get_engine


def export(out_dir: Path) -> None:
    engine = get_engine(read_only=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    ddl = "".join(f"{CreateTable(t).compile(dialect=engine.dialect)};\n\n" for t in Base.metadata.sorted_tables)
    (out_dir / "schema.sql").write_text(ddl)

    data = {}
    with engine.connect() as conn:
        for table in Base.metadata.sorted_tables:
            rows = conn.execute(table.select().order_by(*table.primary_key.columns)).mappings()
            data[table.name] = [dict(row) for row in rows]
    (out_dir / "data.json").write_text(json.dumps(data, indent=2, default=str))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", default="export", type=Path, help="output directory (default: ./export)")
    args = parser.parse_args(argv)
    export(args.out)
    print(f"Exported schema.sql and data.json to {args.out}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
