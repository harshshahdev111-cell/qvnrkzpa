"""Create a consistent SQLite backup for the read-only Vercel pilot."""

import gzip
import os
import sqlite3
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env", override=False)
source = Path(os.environ.get("DATABASE_PATH", ROOT / "backend" / "db.sqlite3"))
if not source.is_file():
    raise SystemExit("Import Elexon history locally before preparing the deployment")
destination = ROOT / "backend" / "data" / "pilot.sqlite3"
destination.parent.mkdir(exist_ok=True)
with sqlite3.connect(f"file:{source.as_posix()}?mode=ro", uri=True) as current:
    with sqlite3.connect(destination) as snapshot:
        current.backup(snapshot)
        print("Snapshot prepared:")
        for table in ("wind_actual", "wind_forecast", "wind_importrun"):
            count = snapshot.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            if not count:
                raise SystemExit(f"Import data first: snapshot contains no {table} rows")
            print(f"  {table}: {count}")

compressed = destination.with_suffix(".sqlite3.gz")
compressed.write_bytes(gzip.compress(destination.read_bytes(), mtime=0))
print(f"Compressed deployment snapshot: {compressed.stat().st_size} bytes")
