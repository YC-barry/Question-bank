# 旧版 Word 五类题型 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让离线题库助手直接导入用户提供的三份旧版 `.doc`，识别填空、判断、选择、简答、计算五类题，完成客观题自动评分与主观题人工复核，并交付 `test1` 安装包。

**Architecture:** 随程序分发 LibreOffice Portable，由独立转换服务把 `.doc` 副本转换为 `.docx`；章节解析器顺序读取 OOXML 正文和媒体，按标题与题号生成统一题目模型。SQLite 迁移到版本 2，题目媒体独立保存；主观题评分输出自动建议，最终成绩由复核后的得分生成。

**Tech Stack:** Python 3.12、PySide6、SQLite、python-docx、LibreOffice Portable、PyInstaller、Inno Setup、pytest、pytest-qt。

**Spec:** `docs/superpowers/specs/2026-11-11-doc-five-types-design.md`

## Global Constraints

- 仅支持简体中文 Windows 10/11 x64，运行、转换和评分完全离线。
- 用户电脑不要求安装 Python、Office、WPS 或 LibreOffice。
- 源 `.doc` 始终只读，转换和解析只操作临时副本。
- 保留现有 `.xlsx`、`.docx`、`.pptx` 导入和四类题判分行为。
- 首次交付复制到 `D:\工具\刷题软件\test1`；后续版本目录递增且不覆盖旧目录。
- 工作区不是 Git 仓库；每个任务以 RED→GREEN 测试输出和计划状态记录代替提交。
- LibreOffice 使用官方稳定的 Windows x86-64 可再分发版本，交付许可证、第三方声明和源代码获取说明。

## Review Focus

- 损坏、密码保护或转换超时的 `.doc` 必须给出中文错误，终止子进程并且不留下半份题库；Task 1 的故障测试覆盖。
- 章节顺序改变、重复题号和全角标点不能导致跨章节串题；Task 2 的高级模板与异常编号测试覆盖。
- 题目间的图片、旧式公式和 OLE 转换结果必须关联到正确题目并进入历史快照；Task 3 的媒体顺序与删除后回看测试覆盖。
- 计算题含多个结果、不同单位或“答：略”时不能错误地自动判零分；Task 4 的待确认与数值容差测试覆盖。
- 版本 1 数据库升级失败时必须恢复原库，旧题和历史仍可查看；Task 3 的迁移回滚测试覆盖。

---

### Task 1: 旧版 DOC 离线转换服务

**Files:**
- Create: `src/offline_quiz/doc_converter.py`
- Create: `tests/test_doc_converter.py`
- Create: `third_party/libreoffice/README.md`
- Modify: `src/offline_quiz/import_service.py`
- Modify: `packaging/offline_quiz.spec`
- Modify: `packaging/build.ps1`

**Interfaces:**
- Produces: `DocConversionService.convert(source: Path) -> ConvertedDocument`，其中 `ConvertedDocument.path: Path`、`cleanup() -> None`。
- Produces: `DocConversionError`，包含面向用户的中文消息。
- Consumes: 打包目录中的 `third_party/libreoffice/LibreOfficePortable.exe` 或其等价无界面启动器。

- [ ] **Step 1: 写转换服务失败测试**

新增 `test_convert_uses_isolated_copy_and_returns_docx`、`test_timeout_terminates_only_spawned_process_and_cleans_temp`、`test_corrupt_and_password_protected_doc_raise_chinese_error`、`test_converter_path_with_chinese_characters`；用伪转换进程固定输入输出，不依赖本机 Office。

- [ ] **Step 2: 运行 Task 1 测试并确认 RED**

Run: `.\.venv\Scripts\python.exe -m pytest -q tests\test_doc_converter.py`

Expected: 因 `DocConversionService` 不存在而失败。

- [ ] **Step 3: 实现转换服务**

实现 `ConvertedDocument`、`DocConversionError` 和 `DocConversionService`；使用 `subprocess.Popen` 参数数组、独立用户配置目录、60 秒超时、显式进程句柄和临时目录清理。只复制源文件，不修改或锁定原文件。

- [ ] **Step 4: 接入导入路由和构建资源**

让 `ImportService.preview(.doc)` 调用转换服务后交给章节式 `.docx` 导入器；构建脚本校验便携组件和许可证存在，PyInstaller/Inno Setup 把组件作为目录资源打包。

- [ ] **Step 5: 运行 Task 1 和原导入测试**

Run: `.\.venv\Scripts\python.exe -m pytest -q tests\test_doc_converter.py tests\test_importers.py`

Expected: 全部通过。

### Task 2: 五章节模板解析器

**Files:**
- Create: `src/offline_quiz/sectioned_word_importer.py`
- Create: `tests/test_sectioned_word_importer.py`
- Modify: `src/offline_quiz/importers.py`
- Modify: `src/offline_quiz/domain.py`

**Interfaces:**
- Consumes: `ConvertedDocument.path`。
- Produces: `SectionedWordImporter.parse(path: Path, bank_name: str | None = None) -> ImportResult`。
- Produces: `QuestionType.SHORT_ANSWER`、`QuestionType.CALCULATION`。
- Produces: 每题的 `answer`、`solution`、`requires_manual_review` 和顺序媒体引用。

- [ ] **Step 1: 写章节和答案变体失败测试**

以最小 `.docx` 夹具覆盖五类标题任意顺序、`1、/1.`、中文英文括号、判断答案前后置、选择括号答案和“答案：A”、简答“答：”、计算“解：/答：略”、重复题号警告及章节缺失。

- [ ] **Step 2: 运行 Task 2 测试并确认 RED**

Run: `.\.venv\Scripts\python.exe -m pytest -q tests\test_sectioned_word_importer.py`

Expected: 因导入器和新题型不存在而失败。

- [ ] **Step 3: 实现顺序正文读取与章节切分**

实现 OOXML 正文事件流，保留段落、表格、换行和媒体的相对顺序；章节通过题型标题匹配，不依赖初中高级的章节排序。

- [ ] **Step 4: 实现五类题解析**

按题号边界拆分，客观题从原文移除答案形成题干；填空把答案位置替换为 `____`；简答保存标准答案；计算分别保存题干、解题过程和最终答案，无法可靠提取结果时设置 `requires_manual_review=True`。

- [ ] **Step 5: 运行 Task 2 测试及全量导入测试**

Run: `.\.venv\Scripts\python.exe -m pytest -q tests\test_sectioned_word_importer.py tests\test_importers.py tests\test_templates.py`

Expected: 全部通过。

### Task 3: 数据库迁移与题目媒体

**Files:**
- Create: `src/offline_quiz/media.py`
- Create: `tests/test_database_migration_v2.py`
- Modify: `src/offline_quiz/domain.py`
- Modify: `src/offline_quiz/database.py`
- Modify: `src/offline_quiz/backup.py`
- Modify: `tests/test_database.py`

**Interfaces:**
- Produces: `QuestionAsset(mime_type: str, data: bytes, position: int, alt_text: str = "")`。
- Produces: `Question.solution: str`、`Question.assets: list[QuestionAsset]`、`Question.requires_manual_review: bool`。
- Produces: schema version `2` 和 `question_assets` 表；题目快照用 base64 保存媒体副本。

- [ ] **Step 1: 写 v1→v2 迁移和媒体持久化失败测试**

覆盖旧库原题与历史保留、媒体顺序往返、删除题目后历史快照仍含媒体、迁移失败自动恢复、外键清理和无媒体旧题兼容。

- [ ] **Step 2: 运行迁移测试并确认 RED**

Run: `.\.venv\Scripts\python.exe -m pytest -q tests\test_database_migration_v2.py`

Expected: schema version 或字段缺失导致失败。

- [ ] **Step 3: 实现显式 v2 迁移**

把 `_initialize()` 改为版本化迁移；在单事务内为题目增加主观题字段并创建媒体表。迁移前由启动流程备份，失败时恢复原数据库且不更新版本号。

- [ ] **Step 4: 实现媒体入库与历史快照**

题目新增、覆盖、编辑和导入事务同时写入媒体；`Question.snapshot()` 编码必要媒体，`get_session()` 解码供界面显示。

- [ ] **Step 5: 运行数据库和备份测试**

Run: `.\.venv\Scripts\python.exe -m pytest -q tests\test_database.py tests\test_database_migration_v2.py tests\test_quiz_services.py`

Expected: 全部通过。

### Task 4: 主观题初判与最终得分

**Files:**
- Create: `src/offline_quiz/subjective_grading.py`
- Create: `tests/test_subjective_grading.py`
- Modify: `src/offline_quiz/domain.py`
- Modify: `src/offline_quiz/grading.py`
- Modify: `src/offline_quiz/quiz_service.py`
- Modify: `src/offline_quiz/database.py`
- Modify: `tests/test_quiz_services.py`

**Interfaces:**
- Produces: `SubjectiveSuggestion(status, suggested_points, confidence, reasons, requires_confirmation)`。
- Produces: `SubjectiveGradingService.suggest(question: Question, user_answer: str) -> SubjectiveSuggestion`。
- Produces: `QuizService.finalize_subjective(session, adjustments: dict[int, int]) -> SessionResult`，调整分数必须在 `0..question.points`。

- [ ] **Step 1: 写主观题评分失败测试**

覆盖简答关键短语完全/部分/无关，空答案；计算结果相同但表达格式不同，单位兼容与不兼容，默认相对误差，多个结果，“答：略”和无法提取时必须待人工确认；覆盖越界人工分数和整卷复核原子提交。

- [ ] **Step 2: 运行主观评分测试并确认 RED**

Run: `.\.venv\Scripts\python.exe -m pytest -q tests\test_subjective_grading.py`

Expected: 服务和复核接口不存在。

- [ ] **Step 3: 实现简答与计算建议算法**

简答使用归一化关键片段覆盖率和字符二元组相似度；计算从最终答案优先提取十进制、科学计数法、百分数和常用工程单位，无法可靠比较时返回待人工确认而不是零分。

- [ ] **Step 4: 实现会话复核状态和最终成绩事务**

客观题交卷即确定；主观题保存自动建议但保持未完成。所有主观题得到人工分数后，单事务写入最终分数、完成时间、错题状态和历史记录。

- [ ] **Step 5: 运行评分与会话测试**

Run: `.\.venv\Scripts\python.exe -m pytest -q tests\test_domain_and_grading.py tests\test_subjective_grading.py tests\test_quiz_services.py`

Expected: 全部通过。

### Task 5: 五类题作答、媒体显示与人工复核界面

**Files:**
- Create: `src/offline_quiz/widgets/media_view.py`
- Create: `src/offline_quiz/widgets/subjective_review.py`
- Create: `tests/test_subjective_ui.py`
- Modify: `src/offline_quiz/ui.py`
- Modify: `tests/test_ui.py`

**Interfaces:**
- Consumes: `Question.assets`、`Question.solution`、`SubjectiveSuggestion`、`QuizService.finalize_subjective(...)`。
- Produces: `SubjectiveReviewDialog`，输出 `dict[question_id, final_points]` 或取消。

- [ ] **Step 1: 写界面失败测试**

覆盖简答/计算多行输入、图片缩放预览、考试提交后必须先复核、正确/部分/错误快捷按钮、分数上下限、取消复核不完成会话、顺序刷题单题复核和历史回看媒体。

- [ ] **Step 2: 运行 UI 测试并确认 RED**

Run: `$env:QT_QPA_PLATFORM='offscreen'; .\.venv\Scripts\python.exe -m pytest -q tests\test_subjective_ui.py`

Expected: 新控件不存在。

- [ ] **Step 3: 扩展题目组件和回看**

`QuestionWidget` 对简答、计算使用多行输入；媒体控件安全解码并等比例显示；回看页显示标准答案、解题过程、自动建议和最终得分。

- [ ] **Step 4: 实现考试与顺序刷题复核流程**

考试交卷后列出全部主观题，未确认时禁止生成最终成绩；顺序模式每题立即显示建议、答案和人工得分控件。导入预览显示五类数量、媒体数和警告。

- [ ] **Step 5: 运行全部 UI 测试**

Run: `$env:QT_QPA_PLATFORM='offscreen'; .\.venv\Scripts\python.exe -m pytest -q tests\test_ui.py tests\test_subjective_ui.py`

Expected: 全部通过。

### Task 6: 三份真实题库验收、离线打包与 test1 交付

**Files:**
- Create: `tests/test_real_mechanic_doc_acceptance.py`
- Create: `THIRD_PARTY_NOTICES.md`
- Modify: `packaging/offline_quiz.iss`
- Modify: `packaging/build.ps1`
- Modify: `README.md`
- Modify: `docs/用户手册.md`
- Modify: `CHANGELOG.md`

**Interfaces:**
- Consumes: 前五个任务的稳定接口。
- Produces: `D:\工具\刷题软件\test1\OfflineQuiz-Setup-1.1.0-test1.exe` 及说明、许可证、校验值。

- [ ] **Step 1: 写真实文档验收测试并确认 RED**

测试在三个源文件存在时逐一转换，断言发现五类章节、每类题数大于零，并抽查已观察到的首题答案；不存在时显式 skip，发布验收时禁止 skip。

- [ ] **Step 2: 使用三份源文件运行验收并修正解析差异**

Run: `.\.venv\Scripts\python.exe -m pytest -q tests\test_real_mechanic_doc_acceptance.py`

Expected: 三份文件全部导入、无错误级问题，五类题均非空；不得修改源文件哈希。

- [ ] **Step 3: 更新说明、许可证和版本号**

说明 `.doc` 支持边界、主观题初判含义、人工复核方法、数据迁移和 SmartScreen 提示；记录 LibreOffice 版本、许可证和源代码获取地址。

- [ ] **Step 4: 运行完整验证**

Run: `$env:QT_QPA_PLATFORM='offscreen'; .\.venv\Scripts\python.exe -m pytest -q`

Run: `.\.venv\Scripts\python.exe -m compileall -q src tests`

Run: `.\.venv\Scripts\python.exe -m pip check`

Expected: 全部退出码为 0，真实文档验收未跳过。

- [ ] **Step 5: 构建并安装冒烟测试**

运行 `packaging\build.ps1`，在临时目录静默安装；断网状态启动，导入三份 `.doc`，完成至少一题客观题和一题主观题复核，再静默卸载。确认用户数据保留选项和恢复模式不退化。

- [ ] **Step 6: 发布 test1**

先确认 `D:\工具\刷题软件\test1` 不存在；创建目录并复制安装包、用户手册、更新记录、第三方声明和 `SHA256.txt`。若目录已存在则停止并报告，不覆盖任何文件。
