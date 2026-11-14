# Importable Explanations and Readable Review Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add strict, separately importable explanation packages plus sequential auto-advance and a shared per-question exam review.

**Architecture:** Parse DOCX packages into normalized domain records, persist them in schema v3, and resolve explanations dynamically against questions and history snapshots. Keep UI responsibilities in focused package-management and exam-review widgets while retaining grading and exam submission behavior.

**Tech Stack:** Python 3.12+, PySide6 6.9.2, SQLite, python-docx, pytest, pytest-qt

**Spec:** `docs/superpowers/specs/2026-11-14-importable-explanations-review-design.md`

## Global Constraints

- Do not commit the three explanation Word files or extracted explanation data.
- Do not stage `.venv`, caches, temporary test data, databases, build outputs, or generated `egg-info` changes.
- Use exact matching only: subject, level, type, normalized stem fingerprint, and normalized answer.
- Keep `questions.explanation` unchanged and preserve scoring rules.
- Every selected file uses an independent transaction.

## Review Focus

- A renamed but content-identical DOCX must be detected as a duplicate and never silently duplicated.
- A same-stem wrong-answer package entry must be a conflict and must never hide a valid original explanation.
- Unknown-level or non-mechanic banks must stay unmatched even when their stems and answers are identical.
- Deleting the newest package must reveal an older exact match without changing questions, wrong counts, or scores.
- Scheduled sequential navigation must not fire after the user changes position or in exam mode.

---

### Task 1: Explanation parser and normalization

**Files:**
- Create: `src/offline_quiz/explanation_packages.py`
- Create: `tests/test_explanation_packages.py`
- Create: `tests/test_real_explanation_documents.py`

**Interfaces:**
- Produces: `ExplanationPackage`, `ExplanationEntry`, `parse_explanation_docx(path)`, `normalize_stem(...)`, `normalize_answer(...)`, and `classify_mechanic_source(...)`.

- [ ] Write parser/normalization tests, including literal fixture expectations and the three real document counts.
- [ ] Run focused tests and verify failure because the module is absent.
- [ ] Implement the minimal parser and exact normalization API.
- [ ] Run focused tests and the full suite.

### Task 2: Schema v3 and dynamic overlay

**Files:**
- Modify: `src/offline_quiz/database.py`
- Modify: `src/offline_quiz/domain.py`
- Create: `tests/test_explanation_database.py`
- Modify: `tests/test_database_migration_v2.py`

**Interfaces:**
- Consumes: normalization records from Task 1.
- Produces: `import_explanation_package`, `list_explanation_packages`, `delete_explanation_package`, exact overlay on question/session reads, and duplicate lookup.

- [ ] Write failing migration, import-order, conflict, priority, fallback, atomic replacement, and preservation tests.
- [ ] Run focused tests and verify expected schema/API failures.
- [ ] Add repeatable v2-to-v3 migration, indexed tables, transactions, status queries, and overlay resolution.
- [ ] Run focused tests and the full suite.

### Task 3: Import routing and package manager

**Files:**
- Modify: `src/offline_quiz/import_service.py`
- Create: `src/offline_quiz/widgets/explanation_manager.py`
- Modify: `src/offline_quiz/widgets/__init__.py`
- Modify: `src/offline_quiz/ui.py`
- Create: `tests/test_explanation_manager_ui.py`

**Interfaces:**
- Consumes: parser and database APIs from Tasks 1-2.
- Produces: explanation-document recognition plus independent multi-file import/delete UI.

- [ ] Write failing routing and manager behavior tests.
- [ ] Verify failures for missing UI/service APIs.
- [ ] Implement the manager, duplicate replace/cancel prompt, delete warning, and bank-page entry.
- [ ] Run focused tests and the full suite.

### Task 4: Sequential auto-advance

**Files:**
- Modify: `src/offline_quiz/ui.py`
- Modify: `tests/test_learning_ui.py`

**Interfaces:**
- Produces: guarded 350 ms advance after correct non-final sequential answers only.

- [ ] Add failing tests for correct auto-advance, wrong stay, final stay/completion, restored answers, and exam non-interference.
- [ ] Verify timing tests fail against current behavior.
- [ ] Implement minimal guarded `QTimer.singleShot` scheduling in `QuizDialog`.
- [ ] Run focused tests and the full suite.

### Task 5: Shared per-question exam review

**Files:**
- Create: `src/offline_quiz/widgets/exam_review.py`
- Modify: `src/offline_quiz/ui.py`
- Modify: `tests/test_ui.py`
- Create: `tests/test_exam_review.py`

**Interfaces:**
- Produces: `ExamReviewDialog(title, items, parent=None)` used by current submission and history.

- [ ] Add failing tests for layout, navigation colors, controls, content, attachments, and 1366x768 bounds.
- [ ] Verify failures because the component is absent and the old table remains.
- [ ] Implement the scrollable detail card with reused review panel/navigator and replace both call sites.
- [ ] Run focused tests and the full suite.

### Task 6: Documentation and final verification

**Files:**
- Modify: `README.md`
- Modify: `CHANGELOG.md`

- [ ] Document separately imported explanation packages, exact matching, deletion/fallback, sequential behavior, and review layout.
- [ ] Run the three real DOCX acceptance tests and record counts.
- [ ] Run the complete pytest suite and report every failure or skip.
- [ ] Audit `git status` and `git diff`; confirm excluded generated/user artifacts remain unstaged and no DOCX/data was added.
