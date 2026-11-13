# 岿枢题典 test4 接力 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将交接包中的深色模式与品牌修复正式合并到源码，构建并交付可覆盖升级的 `test4` 安装包。

**Architecture:** 以源码中的全局 QSS 和品牌常量为唯一运行时来源；安装器使用 `KuishuQuiz.exe` 和中文快捷方式，但保留旧数据目录与 AppId。交接数据库只验证不分发。

**Tech Stack:** Python 3.12、PySide6、SQLite、pytest/pytest-qt、PyInstaller、Inno Setup

**Spec:** `docs/superpowers/specs/2026-11-12-kuishuquiz-handoff-design.md`

## Global Constraints

- 完全离线、无需登录，支持 Windows 10/11 x64。
- 用户可见版本为 `1.3.0-test4`，包版本为 `1.3.0.dev4`。
- 实际 EXE 为 `KuishuQuiz.exe`，用户可见名称为“岿枢题典”。
- 保留 `%LOCALAPPDATA%\OfflineQuiz\data` 和原 Inno Setup `AppId`。
- 不覆盖现有用户数据库，不把交接数据库放进安装包。
- 发布到新的 `D:\工具\刷题软件\test4`，保留 test1/test2/test3。

## Review Focus

- Windows 深色模式继承浅色文字时，白色输入控件和表格仍可读。
- 下拉弹出列表独立于 QComboBox 本体时也有明确前景色和白色背景。
- 品牌替换不能改动旧数据目录，否则现有题库会像“丢失”。
- 安装器快捷方式必须指向实际存在的 `KuishuQuiz.exe`。
- 安装包不能包含交接数据库或用户练习记录。

---

### Task 1: 深色模式安全样式与运行时品牌

**Files:**
- Create: `src/offline_quiz/branding.py`
- Modify: `src/offline_quiz/ui.py`
- Modify: `src/offline_quiz/app.py`
- Modify: `src/offline_quiz/templates.py`
- Modify: `src/offline_quiz/__init__.py`
- Test: `tests/test_brand_and_theme.py`
- Test: `tests/test_app.py`

**Interfaces:**
- Produces: `PRODUCT_NAME = "岿枢题典"` and a dark-mode-safe `APP_STYLE`.
- Preserves: `data_directory()` continues to resolve through `OfflineQuiz/data`.

- [ ] Write failing tests for explicit QWidget/input/popup/table colors, runtime product name, template branding, version, and legacy data directory.
- [ ] Run the focused tests and confirm failure against test3.
- [ ] Add the brand constant, update user-visible strings, and add the four dark-mode-safe QSS rules without weakening the existing sidebar-specific rules.
- [ ] Run the focused tests and then the full suite.

### Task 2: 打包名称、升级兼容与发布文档

**Files:**
- Modify: `packaging/offline_quiz.spec`
- Modify: `packaging/offline_quiz.iss`
- Modify: `packaging/build.ps1`
- Modify: `pyproject.toml`
- Modify: `README.md`
- Modify: `CHANGELOG.md`
- Modify: `docs/用户手册.md`
- Create: `.qa_tools/verify_test4_release.py`

**Interfaces:**
- Consumes: Task 1 product name and `1.3.0-test4` version.
- Produces: `dist/KuishuQuiz/KuishuQuiz.exe` and `dist/installer/KuishuQuiz-Setup-1.3.0-test4.exe`.

- [ ] Write a release-artifact verifier that launches the packaged `KuishuQuiz.exe`, checks the test4 installer name, and rejects any packaged `.db` file; run it first and confirm failure because test4 artifacts do not exist.
- [ ] Update PyInstaller, Inno Setup, build script, package metadata and user-facing documentation.
- [ ] Build once, run the artifact verifier, then run the full suite.

### Task 3: 交接数据安全验证与发布构建

**Files:**
- Create: `docs/handoffs/KuishuQuiz-handoff-2026-11-12.md`
- Create: `dist/release_templates/SHA256-test4.txt`
- Create: `D:\工具\刷题软件\test4\*`

**Interfaces:**
- Consumes: Task 2 installer configuration and the handoff database as read-only input.
- Produces: immutable test4 delivery without any user database.

- [ ] Record the handoff findings and verify the database read-only: integrity `ok`, counts 1/771/15/2/20/19.
- [ ] Build with `packaging/build.ps1` and verify the generated application directory and installer.
- [ ] Smoke-test packaged startup and import the real mechanic `.doc` with the bundled converter.
- [ ] Verify the installer and release directory contain no `.db`, calculate SHA-256, copy templates/manual/release notes to test4, and confirm test1/test2/test3 remain.
- [ ] Run the final full suite, compileall and dependency check.
