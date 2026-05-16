"""
Migrate data from local SQLite (telecom_outage.db) to a PostgreSQL database.

Usage:
    python migrate_sqlite_to_postgres.py --pg-url "postgresql://user:pass@host/dbname"

The local SQLite path defaults to ./telecom_outage.db
"""
import argparse
import json
import sqlite3
import sys

from sqlalchemy import create_engine, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import sessionmaker

TABLES_IN_ORDER = [
    "operators",
    "regions",
    "raw_data",
    "outages",
    "user_reports",
    "users",
    "scraper_runs",
]


def chunked(items: list[dict], size: int):
    for idx in range(0, len(items), size):
        yield items[idx : idx + size]


def sqlite_rows(sqlite_path: str, table: str) -> list[dict]:
    conn = sqlite3.connect(sqlite_path)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.execute(f"SELECT * FROM {table}")
        return [dict(r) for r in cur.fetchall()]
    except sqlite3.OperationalError:
        return []
    finally:
        conn.close()


def migrate(sqlite_path: str, pg_url: str):
    pg_engine = create_engine(pg_url)

    # Import models so Base.metadata includes all tables.
    sys.path.insert(0, ".")
    from scrapers.db.connection import Base
    import scrapers.db.models  # noqa: F401

    print("Initialising PostgreSQL schema...")
    Base.metadata.create_all(bind=pg_engine)
    print("Schema ready.")

    Session = sessionmaker(bind=pg_engine)
    db = Session()

    for table in TABLES_IN_ORDER:
        rows = sqlite_rows(sqlite_path, table)
        if not rows:
            print(f"  {table}: 0 rows (skipped)")
            continue

        table_obj = Base.metadata.tables.get(table)
        if table_obj is None:
            print(f"  {table}: missing in SQLAlchemy metadata (skipped)")
            continue

        cols = list(rows[0].keys())
        for row in rows:
            # Parse JSON strings that PostgreSQL expects as dicts/lists
            for col in cols:
                val = row[col]
                if isinstance(val, str):
                    try:
                        parsed = json.loads(val)
                        if isinstance(parsed, (dict, list)):
                            row[col] = parsed
                    except (json.JSONDecodeError, ValueError):
                        pass

        attempted = 0
        skipped = 0
        stmt = pg_insert(table_obj).on_conflict_do_nothing()
        for batch in chunked(rows, 1000):
            attempted += len(batch)
            try:
                db.execute(stmt, batch)
                db.commit()
            except Exception as exc:
                db.rollback()
                # Fall back to row-by-row for this batch to maximize salvage.
                for row in batch:
                    try:
                        db.execute(pg_insert(table_obj).values(**row).on_conflict_do_nothing())
                        db.commit()
                    except Exception as row_exc:
                        db.rollback()
                        skipped += 1
                        print(f"    !! row skipped in {table}: {row_exc}")

        print(f"  {table}: {attempted} attempted, {skipped} skipped")

    # Reset sequences so auto-increment IDs don't clash
    with pg_engine.connect() as conn:
        for table in TABLES_IN_ORDER:
            try:
                conn.execute(
                    text(
                        f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), "
                        f"COALESCE(MAX(id), 1)) FROM {table}"
                    )
                )
                conn.commit()
            except Exception:
                conn.rollback()

    db.close()
    print("\nMigration complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--sqlite", default="telecom_outage.db", help="Path to SQLite file"
    )
    parser.add_argument(
        "--pg-url", required=True, help="PostgreSQL connection string"
    )
    args = parser.parse_args()

    migrate(args.sqlite, args.pg_url)
