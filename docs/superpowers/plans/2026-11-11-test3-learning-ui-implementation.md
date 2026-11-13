# test3 Learning UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a no-login, fully offline `test3` release with a dashboard-style main window, driving-exam-inspired practice flow, specialty filters, wrong-question practice, and a substantially larger answer review area.

**Architecture:** Preserve the existing SQLite and quiz services. Add focused reusable widgets for navigation statistics and answer review, then compose them in `ui.py`; extend only the setup-page filter payload and wrong-question entry point. Use Qt style sheets and object properties for visual states rather than external UI dependencies.

**Tech Stack:** Python 3.12, PySide6, SQLite, pytest, pytest-qt, PyInstaller, Inno Setup.

**Spec:** `docs/superpowers/specs/2026-11-11-test3-learning-ui-design.md`

## Global Constraints

- No login, accounts, network calls, synchronization, ads, or cloud services.
- Existing database and imported question data must remain compatible.
- Continue supporting Excel, Word, PPT, and legacy `.doc` imports.
- Publish only to a new `D:\工具\刷题软件\test3`; do not overwrite `test1` or `test2`.
- Keep Windows 10/11 x64 and Simplified Chinese as the release target.

## Review Focus

- Empty database: dashboard shows zeros and quick actions do not crash.
- 1366×768 display: quiz controls and the 240-pixel answer panel remain reachable.
- Long correct answers/solutions: review content wraps and scrolls instead of clipping.
- Exam mode: no correct answer is shown before final submission.
- No wrong questions: wrong-question practice gives a clear Chinese message and creates no session.

---

### Task 1: Dashboard and navigation shell

**Files:**
- Create: `src/offline_quiz/widgets/stat_card.py`
- Modify: `src/offline_quiz/ui.py`
- Test: `tests/test_learning_ui.py`

**Interfaces:**
- Consumes: `Database.get_banks()`, `Database.list_questions()`, `Database.list_sessions()`.
- Produces: `HomePage.refresh() -> None`, `HomePage.navigate_requested: Signal(str)`, and stable `MainWindow.navigate(key: str) -> None`.

- [ ] Write failing tests asserting the dashboard zero state, populated statistics, seven navigation destinations, and quick-action navigation signals.
- [ ] Run `pytest -q tests/test_learning_ui.py` and verify the new classes/behavior fail.
- [ ] Implement `StatCard`, `HomePage`, the left-side navigation shell, and the new blue/card visual system while preserving access to all existing pages.
- [ ] Run `pytest -q tests/test_learning_ui.py tests/test_ui.py` and verify all navigation and legacy UI tests pass.

### Task 2: Specialty filters and wrong-question practice

**Files:**
- Modify: `src/offline_quiz/ui.py`
- Test: `tests/test_learning_ui.py`
- Test: `tests/test_quiz_services.py`

**Interfaces:**
- Consumes: existing `QuizService.create_session(filters, count, mode)` support for `question_types`, `tag`, and `wrong_only`.
- Produces: `SessionSetupPage.filters() -> dict[str, Any]` and `WrongPage.start_wrong_practice() -> None`.

- [ ] Write failing tests asserting selected question type/tag values reach the session filters and wrong practice passes `wrong_only=True`.
- [ ] Run the targeted tests and verify failures occur before implementation.
- [ ] Add question-type and tag controls, a concise specialty-practice description, and the wrong-practice button with an empty-state warning.
- [ ] Run targeted UI/service tests and verify the selected filters return only matching questions.

### Task 3: Large answer review component

**Files:**
- Create: `src/offline_quiz/widgets/answer_review.py`
- Modify: `src/offline_quiz/ui.py`
- Test: `tests/test_learning_ui.py`

**Interfaces:**
- Consumes: `GradeResult`, user answer, and the current `Question`.
- Produces: `AnswerReviewPanel.show_result(question, grade, user_answer) -> None`, `clear_result() -> None`, and `minimumHeight() >= 240` while visible.

- [ ] Write failing tests for hidden initial state, visible 240-pixel panel after sequential submission, larger correct-answer typography, long-text wrapping/scrolling, and no answer leakage in exam mode.
- [ ] Run the targeted tests and verify the missing component/layout failures.
- [ ] Implement the scrollable result card with result, score, user answer, correct answer, explanation/solution, and media support.
- [ ] Replace the small feedback `QLabel` in `QuizDialog` with the panel and set the question/result splitter ratio to approximately 60/40 after submission.
- [ ] Run targeted tests and verify all answer-review assertions pass.

### Task 4: Quiz progress and question navigator

**Files:**
- Create: `src/offline_quiz/widgets/question_navigator.py`
- Modify: `src/offline_quiz/ui.py`
- Test: `tests/test_learning_ui.py`

**Interfaces:**
- Consumes: question count, current index, `session.answers`, `session.results`, and `QuizMode`.
- Produces: `QuestionNavigator.jump_requested: Signal(int)` and `set_state(current, answered, correct, wrong, enabled) -> None`.

- [ ] Write failing tests for progress-bar values, exam jump behavior, sequential locked future questions, and answer-state coloring properties.
- [ ] Run the targeted tests and verify failures.
- [ ] Implement the numbered grid, progress header, stable bottom controls, and mode-specific jump rules.
- [ ] Run UI and quiz-service tests and verify navigation never changes grading behavior.

### Task 5: Visual regression, documentation, and test3 release

**Files:**
- Modify: `README.md`
- Modify: `CHANGELOG.md`
- Modify: `packaging/offline_quiz.iss`
- Modify: `.superpowers/sdd/2026-11-11-test3-learning-ui-implementation/progress.md`
- Test: entire `tests/` suite.

**Interfaces:**
- Consumes: completed Tasks 1–4.
- Produces: `dist/installer/OfflineQuiz-Setup-1.2.0-test3.exe` and the immutable delivery directory `D:\工具\刷题软件\test3`.

- [ ] Render the main window, empty dashboard, sequential question, and submitted-answer state offscreen at 1366×768; inspect PNGs for clipping, weak contrast, and unreachable controls.
- [ ] Correct any visual defects with focused regression tests.
- [ ] Update version/release notes and set the installer output name to `OfflineQuiz-Setup-1.2.0-test3.exe`.
- [ ] Run the full pytest suite, `compileall`, and dependency integrity checks.
- [ ] Build the directory-style app and Inno Setup installer; hidden-start the packaged app and verify it responds.
- [ ] Use the packaged LibreOffice converter to import a real mechanic `.doc` and verify the known question count with zero error-level issues.
- [ ] Copy installer, SHA-256 file, three templates, manual, README, changelog, and notices into a newly created `test3` directory only after confirming it does not exist.
- [ ] Re-hash the delivered installer, re-import all delivered templates, verify the file count, and confirm `test1` and `test2` still exist.

