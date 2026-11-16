# Windows 7 x64 Compatibility Edition Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Windows 7 SP1 x64 candidate edition of 岿枢题典, preserve all existing behavior, and place its standalone installer EXE in the `Question-bank - win7` repository root.

**Architecture:** This repository becomes a frozen legacy build using CPython 3.8.10, PySide2/Qt 5.15.2.1, and LibreOffice Portable 25.2.7. It uses distinct product, installer, executable, and local-data identities while retaining database schema 4 and the existing backup format.

**Tech Stack:** Python 3.8.10 x64, PySide2 5.15.2.1, SQLite, LibreOffice Portable 25.2.7, PyInstaller, Inno Setup 6, pytest/pytest-qt.

**Spec:** `docs/superpowers/specs/2026-11-16-win7-x64-compatibility-design.md`

## Global Constraints

- Target Windows 7 SP1 x64 through Windows 11 x64; do not support 32-bit Windows.
- Use Python 3.8.10 x64 and PySide2 5.15.2.1; no product or test source may import PySide6.
- Keep SQLite schema version 4 and the current backup format unchanged.
- Use `%LOCALAPPDATA%\OfflineQuiz-Win7\data`, never `%LOCALAPPDATA%\OfflineQuiz`.
- Use a new installer AppId and install directory; uninstall may delete only `OfflineQuiz-Win7`.
- Name the candidate `1.6.0-win7-rc1`; do not call it final before real Win7 acceptance.
- Build an onedir application and copy standalone installer `KuishuQuiz-Win7-Setup-1.6.0-win7-rc1.exe` to the repository root.
- Require Win7 SP1 x64 with KB4490628, KB4474419 (2019-09-23 or later), and KB2999226.

## Review Focus

- Both editions installed: install, data, and uninstall paths remain isolated; Tasks 2 and 3 pin this behavior.
- Qt startup: high-DPI flags are set before `QApplication`; Task 1 tests the bootstrap order.
- Qt 5 differences: SVG imports, enum spellings, and modal event loops work under PySide2; Task 1 runs all UI tests.
- Clean Win7: missing SHA-2/UCRT prerequisites produce documented action rather than a false compatibility claim; Tasks 3 and 4 pin the prerequisites.
- Root EXE: it is the complete Inno installer, not an orphaned onedir launcher; Tasks 3 and 5 verify this.

---

### Task 1: Python 3.8 and PySide2 Runtime Migration

**Files:**
- Create: `tests/test_win7_runtime_contract.py`
- Modify: `pyproject.toml`
- Modify: `requirements-lock.txt`
- Modify: `.gitignore`
- Modify: `src/offline_quiz/app.py`
- Modify: `src/offline_quiz/assets.py`
- Modify: `src/offline_quiz/theme.py`
- Modify: `src/offline_quiz/ui.py`
- Modify: `src/offline_quiz/widgets/*.py`
- Modify: UI tests importing PySide6 or using Qt 6-only spellings
- Refresh: `src/offline_quiz.egg-info/*`

**Interfaces:**
- Produces: `configure_qt_for_win7() -> None`, called before `QApplication(sys.argv)`, setting `Qt.AA_EnableHighDpiScaling` and `Qt.AA_UseHighDpiPixmaps` when present.
- Produces: `requires-python = ">=3.8,<3.9"`, `PySide2==5.15.2.1`, `openpyxl==3.1.5`, `python-docx==1.1.2`, `python-pptx==1.0.2`, `pytest==8.3.5`, plus exact Python 3.8-compatible pins resolved for pytest-qt, PyInstaller, build dependencies, and transitives.

- [ ] **Step 1: Bootstrap the local Python 3.8 test runner**

Download the official CPython 3.8.10 x64 installer, verify its signature/hash, install into ignored `.python38`, create `.venv`, install only `pytest==8.3.5`, and confirm `.\.venv\Scripts\python.exe --version` prints `Python 3.8.10`.

- [ ] **Step 2: Write the failing static runtime contract**

Create a test that reads source/config text without importing the application. It must assert the Python range and PySide2 pin, assert `configure_qt_for_win7()` appears before `QApplication(` in `main`, and scan `src`, `tests` (excluding the contract test itself), `pyproject.toml`, `requirements-lock.txt`, and `packaging/offline_quiz.spec` for the forbidden Qt 6 package name.

- [ ] **Step 3: Run the contract and verify failure**

Run: `.\.venv\Scripts\python.exe -m pytest tests\test_win7_runtime_contract.py -q`
Expected: FAIL on Python 3.12 and Qt 6 declarations.

- [ ] **Step 4: Migrate metadata and Qt code**

Change imports to PySide2, import `QSvgWidget` from `PySide2.QtSvg`, replace modal/event-loop `.exec()` with `.exec_()`, adapt enum spellings revealed by tests, and add the pre-application high-DPI bootstrap. Pin the declared dependencies and ignore `.python38/`.

- [ ] **Step 5: Install the complete editable environment and freeze pins**

Run `.\.venv\Scripts\python.exe -m pip install --upgrade "pip<25"` and `.\.venv\Scripts\python.exe -m pip install -e ".[dev]"`; record the resolved exact versions in `requirements-lock.txt` and refresh egg-info.

- [ ] **Step 6: Run contract and complete suite**

Run: `$env:QT_QPA_PLATFORM="offscreen"; .\.venv\Scripts\python.exe -m pytest`
Expected: PASS, with real document tests skipped only if their sources are absent.

- [ ] **Step 7: Commit**

Stage the listed runtime/config/test files and commit `feat: migrate legacy build to PySide2`.

### Task 2: Win7 Product Identity and Data Isolation

**Files:**
- Modify: `src/offline_quiz/branding.py`
- Modify: `src/offline_quiz/__init__.py`
- Modify: `src/offline_quiz/app.py`
- Modify: `tests/test_app.py`
- Modify: `tests/test_brand_and_theme.py`

**Interfaces:**
- Produces: `PRODUCT_NAME = "岿枢题典（Win7 兼容版）"`, `EXECUTABLE_BASENAME = "KuishuQuiz-Win7"`, `DATA_DIRECTORY = "OfflineQuiz-Win7"`, `__version__ = "1.6.0-win7-rc1"`.
- Preserves: `prepare_database(data_dir: Path)` and database/backup formats.

- [ ] **Step 1: Write failing identity tests**

Assert the exact four values above and assert `data_directory()` resolves to `tmp_path / "OfflineQuiz-Win7" / "data"` when `LOCALAPPDATA=tmp_path`.

- [ ] **Step 2: Run focused tests and verify failure**

Run: `.\.venv\Scripts\python.exe -m pytest tests\test_app.py tests\test_brand_and_theme.py -q`
Expected: FAIL on old version/product/data identity.

- [ ] **Step 3: Implement identity and isolation**

Set the exact constants, consume `DATA_DIRECTORY` in `data_directory()`, and leave schema/backup code unchanged.

- [ ] **Step 4: Run focused tests and full suite**

Run the focused command, then `$env:QT_QPA_PLATFORM="offscreen"; .\.venv\Scripts\python.exe -m pytest`.
Expected: PASS.

- [ ] **Step 5: Commit**

Stage the five listed files and commit `feat: isolate Windows 7 edition identity`.

### Task 3: Win7 Packaging and Root Installer Contract

**Files:**
- Create: `tests/test_win7_packaging.py`
- Modify: `packaging/offline_quiz.spec`
- Modify: `packaging/offline_quiz.iss`
- Modify: `packaging/build.ps1`
- Modify: `.gitignore`

**Interfaces:**
- Consumes: `KuishuQuiz-Win7` and `1.6.0-win7-rc1` from Task 2.
- Produces: `dist/KuishuQuiz-Win7/KuishuQuiz-Win7.exe`, `dist/installer/KuishuQuiz-Win7-Setup-1.6.0-win7-rc1.exe`, and ignored root copy `KuishuQuiz-Win7-Setup-1.6.0-win7-rc1.exe`.

- [ ] **Step 1: Write failing static packaging tests**

Assert a new AppId, `MinVersion=6.1sp1`, x64-only settings, Win7 names/paths, deletion limited to `{localappdata}\OfflineQuiz-Win7`, PySide2 exclusions, and a final `Copy-Item` from completed installer to repository root.

- [ ] **Step 2: Run packaging test and verify failure**

Run: `.\.venv\Scripts\python.exe -m pytest tests\test_win7_packaging.py -q`
Expected: FAIL on modern AppId/names/path and absent minimum OS/root copy.

- [ ] **Step 3: Implement packaging isolation**

Update the spec; assign a fresh Inno AppId; set `MinVersion=6.1sp1`, x64-only identity, per-user installation, isolated uninstall deletion, and copy only the finished standalone installer to root. Ignore the root installer pattern.

- [ ] **Step 4: Run packaging test and full suite**

Run the focused command and then the complete offscreen suite.
Expected: PASS.

- [ ] **Step 5: Commit**

Stage packaging, ignore, and test files and commit `build: add isolated Windows 7 installer`.

### Task 4: LibreOffice 25.2.7 and Compatibility Documentation

**Files:**
- Create: `tests/test_win7_documentation.py`
- Modify: `tests/test_real_mechanic_doc_acceptance.py`
- Modify: `README.md`
- Modify: `third_party/README.md`
- Modify: `THIRD_PARTY_NOTICES.md`
- Local ignored: `third_party/downloads/LibreOfficePortable_25.2.7_*.paf.exe`
- Local ignored: `third_party/libreoffice/**`

**Interfaces:**
- Produces: `third_party/libreoffice/App/libreoffice/program/soffice.exe` from the 25.2.7 family and documents its exact URL, SHA-256, signature, licenses, prerequisites, isolated data path, and candidate status.

- [ ] **Step 1: Write failing documentation contract**

Assert all three documents name Win7 SP1 x64, Python 3.8.10, PySide2 5.15.2.1, LibreOffice 25.2.7, KB4490628, KB4474419, KB2999226, `OfflineQuiz-Win7`, and candidate status; assert no 26.2.4 instruction remains.

- [ ] **Step 2: Run documentation test and verify failure**

Run: `.\.venv\Scripts\python.exe -m pytest tests\test_win7_documentation.py -q`
Expected: FAIL on modern documentation.

- [ ] **Step 3: Download, verify, and expand LibreOffice Portable**

Use the official 25.2.7 portable mirror, compute SHA-256, verify the PortableApps Authenticode signature, expand into `third_party/libreoffice`, and verify `soffice.exe --version` reports 25.2.7.

- [ ] **Step 4: Update docs and real sample locations**

Document build commands, KBs, isolated data/migration, candidate/security limitations, URL/hash/licenses; point the real `.doc` acceptance cases at the three samples in the repository's parent directory without committing those documents.

- [ ] **Step 5: Run documentation, real document, and full tests**

Run the documentation test, `tests\test_real_mechanic_doc_acceptance.py`, then the full offscreen suite.
Expected: PASS with all three real `.doc` cases executed rather than skipped.

- [ ] **Step 6: Commit**

Stage the five tracked files and commit `docs: document Windows 7 candidate requirements`.

### Task 5: Build, Smoke Test, and Deliver Root EXE

**Files:**
- Generated ignored: `dist/KuishuQuiz-Win7/**`
- Generated ignored: `dist/installer/KuishuQuiz-Win7-Setup-1.6.0-win7-rc1.exe`
- Generated ignored: `KuishuQuiz-Win7-Setup-1.6.0-win7-rc1.exe`

**Interfaces:**
- Produces: the root standalone installer requested by the user, application onedir output, hashes, and smoke evidence.

- [ ] **Step 1: Run the release build**

Run: `powershell -ExecutionPolicy Bypass -File .\packaging\build.ps1`
Expected: tests pass; PyInstaller and ISCC succeed; root installer exists.

- [ ] **Step 2: Inspect architecture, versions, and hashes**

Verify Python/Qt/application/LibreOffice binaries are x64; record file versions and SHA-256 for root installer and application EXE.

- [ ] **Step 3: Smoke launch the onedir application**

Launch with isolated `LOCALAPPDATA`, confirm the main window, confirm data only below `OfflineQuiz-Win7`, and exit cleanly.

- [ ] **Step 4: Smoke install the root installer**

Perform a per-user install, launch, confirm bundled LibreOffice is reachable, uninstall, and confirm modern-edition paths remain untouched.

- [ ] **Step 5: Run final verification**

Run full pytest, `git diff --check`, `git status --short`, artifact existence/size/hash checks, and a scan proving no PySide6, 26.2.4, modern AppId, or modern data-deletion reference remains in Win7 product paths.

- [ ] **Step 6: Label delivery honestly**

Until a real Win7 SP1 x64 machine passes installation, startup, `.doc` conversion, backup/restore, and uninstall, keep the root EXE labeled `rc1` and hand off the remaining acceptance checklist.
