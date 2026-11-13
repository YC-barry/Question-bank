# test6 学习首页与顺序刷题回看 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为顺序刷题增加可靠回看和题型多选，并用真实历史数据构建现代化学习首页。

**Architecture:** `QuizDialog` 从 `QuizSession.answers` 恢复顺序刷题答案；独立 `QuestionTypeSelector` 负责筛选；`Database.learning_overview()` 通过聚合查询生成首页数据；轻量自绘组件只负责显示。数据库结构保持版本 2。

**Tech Stack:** Python 3.12、PySide6、SQLite、pytest-qt、PyInstaller、Inno Setup

**Spec:** `docs/superpowers/specs/2026-11-12-test6-dashboard-history-design.md`

## Global Constraints

- 应用完全离线，不增加登录、网络请求或外部图表库。
- 旧题回看不得重复保存答题记录或改变错题次数。
- 总体和分类进度按不同题目覆盖率计算，趋势按每日提交次数计算。
- 数据库结构保持版本 2，现有题库、错题和练习记录继续可用。
- test6 发布到新目录，不覆盖 test1 至 test5。

## Review Focus

- 错误答案 `False`、空字符串和多选列表恢复时不能因真假值判断而丢失。
- 恢复判断题选择时不能触发自动批改或生成重复 `session_items`。
- 无题库、无历史、仅一天历史及超过七天历史时统计必须稳定。
- 删除题目后总体进度和分类分母只计算当前题目，趋势仍保留历史活动。
- 1366×768 桌面下首页应可完整滚动，卡片不得互相遮挡。

---

### Task 1: 顺序刷题旧答案回显

**Files:**
- Modify: `src/offline_quiz/ui.py`
- Test: `tests/test_learning_ui.py`

**Interfaces:**
- Consumes: `QuizSession.answers[index]` 和 `QuizSession.results[index]`
- Produces: `QuizDialog.show_question()` 在重建题目控件时恢复顺序答案

- [ ] 写入失败测试：答错第一道判断题、进入第二题、点击题号 1 后仍选中“错”并显示正确答案，数据库答题行数不增加。
- [ ] 运行聚焦测试，确认当前实现未恢复选项。
- [ ] 在连接自动批改事件前恢复 `session.answers`，再锁定已批改题目。
- [ ] 运行聚焦测试与学习界面测试。

### Task 2: 题型多选筛选

**Files:**
- Create: `src/offline_quiz/widgets/question_type_selector.py`
- Modify: `src/offline_quiz/ui.py`
- Test: `tests/test_learning_ui.py`

**Interfaces:**
- Produces: `QuestionTypeSelector.selected_values() -> list[str]`
- Consumes: `SessionSetupPage.filters()["question_types"]`

- [ ] 写入失败测试：默认返回全部题型、可只选判断、可组合选择、不能取消最后一个题型。
- [ ] 运行测试确认组件尚不存在。
- [ ] 实现六个可勾选按钮及选择保护，并替换原题型下拉框。
- [ ] 运行聚焦测试与现有筛选测试。

### Task 3: 学习统计聚合

**Files:**
- Modify: `src/offline_quiz/database.py`
- Test: `tests/test_learning_overview.py`

**Interfaces:**
- Produces: `Database.learning_overview(days: int = 7) -> dict[str, Any]`
- Consumes: 当前题目、最近一次作答结果、`answered_at` 和会话信息

- [ ] 写入失败测试，覆盖空库、重复作答采用最新结果、七日趋势补零和分题型覆盖率。
- [ ] 运行聚焦测试确认方法缺失。
- [ ] 使用 SQLite 聚合查询实现统计，不读取题目正文、答案和附件。
- [ ] 运行聚焦测试和数据库相关测试。

### Task 4: 现代化学习首页

**Files:**
- Create: `src/offline_quiz/widgets/learning_charts.py`
- Modify: `src/offline_quiz/ui.py`
- Test: `tests/test_learning_ui.py`

**Interfaces:**
- Consumes: `Database.learning_overview()`
- Produces: 总体进度环、七日趋势、题型进度条、最近活动和常用功能入口

- [ ] 写入失败测试：空状态、统计刷新、图表数据、常用入口和可滚动首页。
- [ ] 运行聚焦测试确认新版组件缺失。
- [ ] 实现自绘进度环和趋势图，重构 `HomePage` 为滚动卡片布局。
- [ ] 运行学习界面测试并在 1366×768 尺寸渲染截图检查。

### Task 5: test6 发布

**Files:**
- Modify: `src/offline_quiz/__init__.py`
- Modify: `pyproject.toml`
- Modify: `packaging/offline_quiz.iss`
- Modify: `README.md`
- Modify: `CHANGELOG.md`
- Modify: `.qa_tools/verify_test4_release.py`
- Create: `D:\工具\刷题软件\test6\*`

**Interfaces:**
- Produces: `KuishuQuiz-Setup-1.5.0-test6.exe` 与发布校验信息

- [ ] 先将版本测试更新为 test6 并确认失败，再更新版本与文档。
- [ ] 运行全量测试、compileall 和 pip check。
- [ ] 构建目录式应用与 Inno Setup 安装包。
- [ ] 验证打包应用启动、旧数据库兼容、三类模板导入、发布目录完整性和 SHA-256。
- [ ] 保留 test1 至 test5，并把安装包复制到 test6。
