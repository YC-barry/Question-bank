from __future__ import annotations

import importlib
import os
from pathlib import Path
import pkgutil
import subprocess
import sys

import offline_quiz


def test_all_application_modules_import_with_legacy_qt_runtime():
    failures = {}
    module_names = [
        module.name
        for module in pkgutil.walk_packages(
            offline_quiz.__path__, prefix=f"{offline_quiz.__name__}."
        )
    ]

    for module_name in module_names:
        try:
            importlib.import_module(module_name)
        except Exception as exc:  # collect every incompatible import in one run
            failures[module_name] = f"{type(exc).__name__}: {exc}"

    assert failures == {}


def test_win7_qt_bootstrap_enables_high_dpi_before_application_creation():
    source_root = Path(__file__).resolve().parents[1] / "src"
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(source_root)
    command = """
from PySide2.QtCore import Qt
from PySide2.QtWidgets import QApplication
from offline_quiz.app import configure_qt_for_win7

configure_qt_for_win7()
assert QApplication.testAttribute(Qt.AA_EnableHighDpiScaling)
assert QApplication.testAttribute(Qt.AA_UseHighDpiPixmaps)
"""

    completed = subprocess.run(
        [sys.executable, "-c", command],
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr


def test_logging_bootstrap_works_on_python_38(tmp_path):
    source_root = Path(__file__).resolve().parents[1] / "src"
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(source_root)
    command = """
import logging
from pathlib import Path
import sys
from offline_quiz.app import configure_logging

data_dir = Path(sys.argv[1])
configure_logging(data_dir)
logging.info("win7 logging smoke test")
logging.shutdown()
assert (data_dir / "offline-quiz.log").exists()
"""

    completed = subprocess.run(
        [sys.executable, "-c", command, str(tmp_path)],
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
