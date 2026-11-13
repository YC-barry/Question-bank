# test5 题目导航与判断题即时批改 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复题号导航裁切，并为顺序刷题判断题增加点击即批改。

**Architecture:** QuestionNavigator 负责稳定的五列可见布局；QuizDialog 只在 SEQUENTIAL + TRUE_FALSE 条件下将选择事件接入现有提交服务。考试模式和判分服务保持不变。

**Tech Stack:** Python 3.12、PySide6、pytest-qt、PyInstaller、Inno Setup

**Spec:** `docs/superpowers/specs/2026-11-12-test5-navigation-auto-judgment-design.md`

## Global Constraints

- 判断题自动批改仅限顺序刷题。
- 考试模式仍可修改答案，提交试卷前不得显示正确答案。
- 导航保持五列且不得出现横向滚动。
- 新版本独立发布到 test5，不覆盖旧发布目录。

## Review Focus

- 100题以上出现竖向滚动条时，第5列仍完整可见。
- 自动提交不得被同一次点击触发两次。
- 回看已答判断题时不得因恢复选中状态再次提交。
- 考试模式判断题点击后不得提前判分或显示答案。
- 非判断题的手动提交行为不得改变。

---

### Task 1: 题目导航完整显示

**Files:**
- Modify: `src/offline_quiz/widgets/question_navigator.py`
- Test: `tests/test_learning_ui.py`

- [ ] 写入100题导航的失败测试，断言无横向滚动且每行第5个按钮位于视口内。
- [ ] 运行测试确认当前230px布局失败。
- [ ] 扩大导航宽度、固定内容最小宽度并关闭横向滚动。
- [ ] 运行导航测试和全量测试。

### Task 2: 顺序判断题点击即批改

**Files:**
- Modify: `src/offline_quiz/ui.py`
- Test: `tests/test_learning_ui.py`

- [ ] 写入顺序判断题点击后立即产生结果并显示答案的失败测试，以及考试模式不自动批改的保护测试。
- [ ] 运行测试确认顺序模式失败、考试模式保持未批改。
- [ ] 在 `QuizDialog.show_question()` 只为未作答的顺序判断题连接点击提交，并隐藏冗余提交按钮。
- [ ] 运行聚焦测试和全量测试。

### Task 3: test5 打包与交付

**Files:**
- Modify: `src/offline_quiz/__init__.py`
- Modify: `pyproject.toml`
- Modify: `packaging/offline_quiz.iss`
- Modify: `README.md`
- Modify: `CHANGELOG.md`
- Modify: `.qa_tools/verify_test4_release.py`
- Create: `D:\工具\刷题软件\test5\*`

- [ ] 先更新版本测试为 test5 并确认失败，再更新源码版本与打包名称。
- [ ] 将发布检查器参数化为 test5，构建应用和安装包。
- [ ] 渲染长题库刷题界面，视觉确认导航完整和判断题批改区可见。
- [ ] 验证应用启动、真实旧版 Word 导入、模板导入、校验码和旧版本保留。
- [ ] 运行最终全量测试、compileall 和 pip check。

