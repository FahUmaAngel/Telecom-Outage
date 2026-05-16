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

    # Import models so create_all knows about them
    sys.path.insert(0, ".")
    from scrapers.db.init_db import init_db

    print("Initialising PostgreSQL schema + seed data...")
    init_db()
    print("Schema ready.")

    Session = sessionmaker(bind=pg_engine)
    db = Session()

    for table in TABLES_IN_ORDER:
        rows = sqlite_rows(sqlite_path, table)
        if not rows:
            print(f"  {table}: 0 rows (skipped)")
            continue

        # Build column list from first row
        cols = list(rows[0].keys())
        col_list = ", ".join(f'"{c}"' for c in cols)
        placeholders = ", ".join(f":{c}" for c in cols)

        inserted = 0
        skipped = 0
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

            try:
                db.execute(
                    text(
                        f"INSERT INTO {table} ({col_list}) "
                        f"VALUES ({placeholders}) "
                        f"ON CONFLICT DO NOTHING"
                    ),
                    row,
                )
                inserted += 1
            except Exception as exc:
                db.rollback()
                skipped += 1
                print(f"    !! row skipped in {table}: {exc}")
                db = Session()  # fresh session after rollback

        db.commit()
        print(f"  {table}: {inserted} inserted, {skipped} skipped")

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
