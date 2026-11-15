# Test9 Local Data Controls Implementation Plan

**Goal:** Add independently scoped local-data deletion/reset controls and produce a verified test9 Windows executable.

**Tech Stack:** Python 3.12+, PySide6 6.9.2, SQLite schema v4, pytest/pytest-qt, PyInstaller, Inno Setup 6

**Spec:** `docs/superpowers/specs/2026-11-14-test9-local-data-controls-design.md`

### Task 1: Schema v4 and database operations

- Add failing migration and deletion-scope tests.
- Add `app_settings`, repeatable v3-to-v4 migration, wrong-book clear, history clear, and overview reset APIs.
- Apply the overview cutoff to all dashboard queries.
- Run focused database tests.

### Task 2: Settings user interface

- Add failing pytest-qt tests for three actions, cancellation, backup-first ordering, messages, and refresh signal.
- Add a “本地学习数据” card and scoped confirmation handlers.
- Connect Settings changes to `MainWindow.refresh_all`.
- Run focused UI tests.

### Task 3: Test9 identity and documentation

- Update package, application, installer, README, user manual, and changelog version references to test9.
- Document each deletion scope and automatic safety backup.

### Task 4: Verification and packaging

- Run the complete pytest suite and report all skips/failures.
- Restore local packaging dependencies without committing them.
- Build portable EXE and Inno Setup installer.
- Smoke-launch the packaged EXE with an isolated local app-data directory.
- Copy source/portable/installer deliverables to `D:\工具\刷题软件\test9` and record SHA-256 hashes.
