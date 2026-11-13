from __future__ import annotations

import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import time


PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_DIR = PROJECT_ROOT / "dist" / "KuishuQuiz"
APP_EXE = APP_DIR / "KuishuQuiz.exe"
RELEASE_VERSION = os.environ.get("KUISHU_RELEASE_VERSION", "1.5.0-test6")
INSTALLER = PROJECT_ROOT / "dist" / "installer" / f"KuishuQuiz-Setup-{RELEASE_VERSION}.exe"


def verify_release() -> None:
    if not APP_EXE.is_file():
        raise AssertionError(f"packaged application is missing: {APP_EXE}")
    if not INSTALLER.is_file():
        raise AssertionError(f"installer is missing: {INSTALLER}")
    leaked_databases: list[Path] = []
    for database in APP_DIR.rglob("*.db"):
        try:
            connection = sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True)
            try:
                tables = {
                    row[0]
                    for row in connection.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    )
                }
            finally:
                connection.close()
        except sqlite3.DatabaseError:
            continue
        if {"banks", "questions"}.issubset(tables):
            leaked_databases.append(database)
    if leaked_databases:
        raise AssertionError(f"user database leaked into application package: {leaked_databases}")

    with tempfile.TemporaryDirectory(prefix="kuishuquiz-smoke-") as local_app_data:
        environment = os.environ.copy()
        environment["LOCALAPPDATA"] = local_app_data
        environment["QT_QPA_PLATFORM"] = "offscreen"
        process = subprocess.Popen([str(APP_EXE)], env=environment)
        try:
            time.sleep(4)
            if process.poll() is not None:
                raise AssertionError(f"packaged application exited early with code {process.returncode}")
        finally:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=10)


if __name__ == "__main__":
    try:
        verify_release()
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
    print(f"PASS: {RELEASE_VERSION} packaged application and installer verified")
