"""Build React for Django's CDN static prefix and verify the pilot snapshot."""

import gzip
import gzip
import os
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main():
    snapshot = ROOT / "backend" / "data" / "pilot.sqlite3"
    compressed = snapshot.with_suffix(".sqlite3.gz")
    if not snapshot.is_file() and compressed.is_file():
        with gzip.open(compressed, "rb") as source, snapshot.open("wb") as target:
            shutil.copyfileobj(source, target)
    compressed = snapshot.with_suffix(".sqlite3.gz")
    if compressed.is_file():
        with gzip.open(compressed, "rb") as source, snapshot.open("wb") as target:
            shutil.copyfileobj(source, target)
    if not snapshot.is_file():
        raise RuntimeError(
            "Missing backend/data/pilot.sqlite3. Run scripts/prepare_vercel.py "
            "after importing the historical Elexon data."
        )
    with sqlite3.connect(f"file:{snapshot.as_posix()}?mode=ro", uri=True) as connection:
        for table in ("wind_actual", "wind_forecast", "wind_importrun"):
            count = connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            if not count:
                raise RuntimeError(f"The deployment snapshot has no {table} records")
            print(f"Snapshot: {table} = {count}", flush=True)
    npm = shutil.which("npm")
    if npm is None:
        raise RuntimeError("Node.js and npm are required to build the portal")
    frontend = ROOT / "frontend"
    subprocess.run([npm, "ci", "--ignore-scripts"], cwd=frontend, check=True)
    subprocess.run(
        [npm, "run", "build"], cwd=frontend, check=True, env={**os.environ, "VERCEL": "1"}
    )
    shutil.copytree(frontend / "dist", ROOT / "backend" / "public", dirs_exist_ok=True)
    subprocess.run(
        [sys.executable, str(ROOT / "backend" / "manage.py"), "collectstatic", "--noinput"],
        check=True,
        env={**os.environ, "DJANGO_SETTINGS_MODULE": "config.vercel_settings"},
    )


if __name__ == "__main__":
    main()
