# 岿枢题典 test8 接力验收记录

日期：2026-11-13

## 源码来源与目录

- 来源压缩包：`D:\Relax\xwechat_files\wxid_0p4aor0lql8422_09a0\msg\file\2026-11\test7.7z`
- 使用的源码目录：压缩包内 `test7/Question-Bank-source-1.5.0-test7`
- 新开发目录：`E:\工作\题库\test8`
- 未覆盖原有 `E:\工作\test7`，也未从安装包或便携版反编译源码。

## 接管时已阅读

- `README.md`
- `CHANGELOG.md`
- `docs/handoffs/KuishuQuiz-handoff-2026-11-12.md`
- `docs/用户手册.md`
- `docs/superpowers/specs` 下全部现有设计文档
- `third_party/README.md`
- 现有源码模块、测试入口、打包配置与依赖声明

## test8 首个修复

首次按 README 执行 `python -m venv .venv` 和 `pip install -e ".[dev]"` 时，依赖解析成功，但最新的 PySide6 6.12.0 在本机 Anaconda Python 3.13.9 环境导入 `PySide6.QtCore` 失败。

排查结果：

- Windows 11 x64 与 Python 版本均在工程声明范围内。
- PySide6 6.12.0 的 `Qt6Core.dll` 依赖 `icuuc.dll`，该 wheel 未在当前环境提供匹配的 ICU DLL。
- 本机 Anaconda 自带的 ICU 导出符号与 Qt 6.12 所需入口不匹配。
- 在相同 Python、相同源码下仅切换为 PySide6 6.9.2 后，`QtCore` 可正常导入，完整测试通过。

因此 test8 将 PySide6 固定为 6.9.2，并同步推进版本：

- 用户版本：`1.5.1-test8`
- Python 包版本：`1.5.1.dev8`
- 安装器版本：`1.5.1-test8`
- 计划安装包名：`KuishuQuiz-Setup-1.5.1-test8.exe`

涉及文件：

- `pyproject.toml`
- `requirements-lock.txt`
- `src/offline_quiz/__init__.py`
- `packaging/offline_quiz.iss`
- `README.md`
- `CHANGELOG.md`
- `tests/test_app.py`

## 验证结果

环境：Windows 11 x64、Python 3.13.9、PySide6 6.9.2。

- `pip check`：通过，无依赖冲突。
- 包元数据：`offline-quiz 1.5.1.dev8`。
- 全量测试：`109 passed, 3 skipped in 11.62s`。
- 三项跳过原因：自动化测试仍引用旧电脑的 `D:\工具\题库\机修钳工理论知识*.doc`。
- 隔离数据目录启动：通过；窗口标题“岿枢题典”，版本 `1.5.1-test8`，主窗口 980×752，SQLite 数据库可创建，Qt 事件循环正常退出。

本机存在三份真实旧版 Word 样本，因此又使用现有便携版 LibreOffice 做了显式路径端到端验收：

| 文件 | 解析题量 | 填空 | 判断 | 单选 | 简答 | 计算 | 资源 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 机修钳工理论知识初级.doc | 771 | 211 | 188 | 200 | 120 | 52 | 15 |
| 机修钳工理论知识中级.doc | 987 | 276 | 262 | 254 | 145 | 50 | 18 |
| 机修钳工理论知识高级.doc | 812 | 199 | 240 | 198 | 125 | 50 | 9 |

三份文档均满足最低题量，覆盖五类题型，无解析错误，关键首题答案与图片资源断言通过。源文档只读，转换在临时目录完成。

## 当前限制与下一步

- test8 纯源码目录没有内置 LibreOffice Portable；真实 `.doc` 验收借用了现有便携版中的转换器。
- 本机未发现 Inno Setup 6，因此尚未生成 test8 安装包。
- Word、Excel、PPT 固定模板、刷题、100 分试卷、评分、答案审查、错题和历史等逻辑已由现有自动化测试覆盖；本轮没有新增未指定的业务功能。
- 下一项功能开发应继续在 `E:\工作\题库\test8` 完成；发布 test9 时新建目录，不能覆盖 test8。
