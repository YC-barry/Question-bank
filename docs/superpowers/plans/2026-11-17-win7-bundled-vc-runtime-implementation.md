# Win7 Bundled VC++ Runtime Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 生成一个不依赖目标电脑预装 VC++ 运行库、可在已满足基础系统补丁的 Windows 7 SP1 x64 上完全离线转换旧版 Word 的 `1.6.0-win7-rc2` 安装包。

**Architecture:** `DocConversionService` 为 LibreOffice 子进程构造隔离环境，将与转换器同一发行包中的 x64 `System64` 置于 `PATH` 首位，使 Windows 加载器使用版本匹配的本地 VC++ DLL。构建脚本验证关键运行库存在且为 x64，再生成 rc2 安装器并复制到根目录和 `KuishuQuiz-Win7` 发布目录。

**Tech Stack:** Python 3.8.10、PySide2 5.15.2.1、LibreOffice 25.2.7.2 x64、PyInstaller 6.16、Inno Setup 6、pytest、PowerShell

**Spec:** `docs/superpowers/specs/2026-11-17-win7-bundled-vc-runtime-design.md`

## Global Constraints

- 目标系统为 Windows 7 SP1 x64；应用、Python、Qt、LibreOffice 与本地 VC++ DLL 都必须为 x64。
- 不联网、不运行系统级 `VC_redist`、不要求管理员权限、不把 DLL 写入 Windows 系统目录。
- 只向转换子进程注入 `App/libreoffice/System64`；不得加入包含 x86 DLL 的 `App/libreoffice/System`。
- 保持 `KuishuQuiz-Win7`、`OfflineQuiz-Win7` 和现代版隔离边界不变。
- 新版本固定为 `1.6.0-win7-rc2`；安装器名固定为 `KuishuQuiz-Win7-Setup-1.6.0-win7-rc2.exe`。
- 最终安装器同时输出到仓库根目录和 `KuishuQuiz-Win7/`；不提交生成物或现有未跟踪安装目录。
- 历史 rc1 设计与实施计划保持原样。

## Review Focus

- 目标环境已有 `PATH` 内容：本地 `System64` 必须置顶且原内容不能丢失；由 Task 1 的真实子进程测试覆盖。
- `System64` 缺失或路径不是 LibreOffice 布局：不得注入不存在的路径；由 Task 1 回归测试覆盖。
- 测试通过 `command_prefix` 使用假转换器：运行库根目录仍以显式 `executable` 推导，不应从 Python 解释器路径误推导；由 Task 1 测试覆盖。
- 转换器无 stdout/stderr 且非零退出：用户必须看到退出代码和安装包完整性提示；由 Task 1 测试覆盖。
- LibreOffice 升级后遗漏或混入 x86 运行库：构建必须在生成安装器前失败；由 Task 2 打包测试和实际 PE 检查覆盖。

---

### Task 1: 为 LibreOffice 子进程加载内置 x64 VC++ 运行库

**Files:**
- Modify: `src/offline_quiz/doc_converter.py`
- Modify: `tests/test_doc_converter.py`

**Interfaces:**
- Consumes: `DocConversionService(executable=None, command_prefix=None, timeout_seconds=120, temp_root=None)` 与 `App/libreoffice/program/soffice.exe` 布局。
- Produces: `DocConversionService._conversion_environment() -> dict`；`_run_conversion(...)` 用该环境启动子进程；静默失败详情包含退出代码。

- [ ] **Step 1: 写入失败测试：真实子进程看到置顶的 `System64`**

在 `tests/test_doc_converter.py` 新增 `test_convert_prepends_bundled_x64_runtime_to_child_path`：创建 `libreoffice/program/soffice.exe` 占位路径及 `libreoffice/System64/msvcp140_atomic_wait.dll`，通过 `executable` 指定该布局、通过 `command_prefix` 运行现有风格的 Python 假转换器；假转换器把子进程 `PATH` 写入生成的 `.docx`，断言第一项是 `System64` 且保留父进程原 `PATH`。

- [ ] **Step 2: 运行测试并确认 RED**

Run: `W:\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp=%TEMP%\oq-vc-red tests\test_doc_converter.py::test_convert_prepends_bundled_x64_runtime_to_child_path`

Expected: FAIL，因为当前 `Popen` 没有传入包含 `System64` 的 `env`。

- [ ] **Step 3: 实现最小运行库环境注入**

在 `DocConversionService.__init__` 保存 `self.converter_path: Path`。新增 `_conversion_environment(self) -> dict`：复制 `os.environ`，计算 `self.converter_path.parent.parent / "System64"`，仅当目录存在时以 `os.pathsep` 置于 `PATH` 首位；`_run_conversion` 把返回值传给 `subprocess.Popen(env=...)`。

- [ ] **Step 4: 运行定向测试并确认 GREEN**

Run: 与 Step 2 相同。

Expected: PASS。

- [ ] **Step 5: 写入失败测试：不存在目录不注入、静默失败可诊断**

新增：
- `test_convert_does_not_inject_missing_runtime_directory`：假转换器记录 `PATH`，断言不存在的 `System64` 未出现且父环境保持不变。
- `test_convert_reports_exit_code_when_converter_fails_silently`：假转换器无输出退出 7，断言 `DocConversionError` 同时包含“退出代码 7”和“安装包可能不完整”。

- [ ] **Step 6: 运行两个测试并确认 RED**

Run: `W:\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp=%TEMP%\oq-vc-red2 tests\test_doc_converter.py -k "missing_runtime or fails_silently"`

Expected: 缺失目录测试 PASS；静默失败测试 FAIL，当前只显示“转换组件返回错误”。

- [ ] **Step 7: 实现退出代码诊断并运行整个转换测试文件**

当 stderr/stdout 均为空时，详情使用 `转换组件无法启动（退出代码 <code>），安装包可能不完整或系统组件不兼容`；保留已有两阶段回退。

Run: `W:\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp=%TEMP%\oq-vc-task1 tests\test_doc_converter.py`

Expected: 全部 PASS。

- [ ] **Step 8: 提交 Task 1**

```powershell
git add src/offline_quiz/doc_converter.py tests/test_doc_converter.py
git commit -m "fix: load bundled x64 runtime for doc conversion"
```

---

### Task 2: 增加打包门禁并发布 rc2

**Files:**
- Modify: `src/offline_quiz/__init__.py`
- Modify: `packaging/build.ps1`
- Modify: `packaging/offline_quiz.iss`
- Modify: `tests/test_app.py`
- Modify: `tests/test_win7_packaging.py`
- Modify: `README.md`
- Modify: `THIRD_PARTY_NOTICES.md`

**Interfaces:**
- Consumes: Task 1 对 `App/libreoffice/System64` 的运行时路径约定。
- Produces: `1.6.0-win7-rc2` 应用身份；构建时存在性/x64 PE 门禁；根目录及 `KuishuQuiz-Win7/` 两份同哈希安装器。

- [ ] **Step 1: 写入失败测试：版本、运行库门禁和发布目录**

更新 `tests/test_app.py` 期待 `__version__ == "1.6.0-win7-rc2"`。更新 `tests/test_win7_packaging.py` 期待 Inno 与构建脚本使用 rc2，并断言构建脚本列出 `msvcp140.dll`、`msvcp140_atomic_wait.dll`、`vcruntime140.dll`、`vcruntime140_1.dll`，检查 PE `0x8664`，且复制到 `KuishuQuiz-Win7` 发布目录。

- [ ] **Step 2: 运行测试并确认 RED**

Run: `W:\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp=%TEMP%\oq-package-red tests\test_app.py tests\test_win7_packaging.py`

Expected: FAIL，当前仍为 rc1 且没有运行库/发布目录门禁。

- [ ] **Step 3: 实现 rc2 和构建门禁**

- 将应用、Inno、构建脚本版本统一改为 `1.6.0-win7-rc2`。
- 在 LibreOffice 复制/裁剪后验证四个关键 DLL 存在，并读取 PE 头确认 Machine 为 `0x8664`；否则抛错停止。
- 创建 `KuishuQuiz-Win7` 发布目录，将完成的安装器复制进去；保留根目录副本。
- README 说明 C++ 运行库已内置、`KB2999226` 是 Win7 系统级 UCRT 前置条件、rc2 输出位置。
- THIRD_PARTY_NOTICES 记录运行库来自官方 LibreOffice x64 MSI 的 `System64`，不额外下载随机 DLL。

- [ ] **Step 4: 运行定向测试并确认 GREEN**

Run: 与 Step 2 相同。

Expected: 全部 PASS。

- [ ] **Step 5: 运行全量测试**

Run: `W:\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp=%TEMP%\oq-vc-full`

Expected: 全部通过；仅允许真实外部资料不存在导致的既有 skip。

- [ ] **Step 6: 提交 Task 2**

```powershell
git add src/offline_quiz/__init__.py packaging/build.ps1 packaging/offline_quiz.iss tests/test_app.py tests/test_win7_packaging.py README.md THIRD_PARTY_NOTICES.md docs/superpowers/specs/2026-11-17-win7-bundled-vc-runtime-design.md docs/superpowers/plans/2026-11-17-win7-bundled-vc-runtime-implementation.md
git commit -m "build: make Win7 converter runtime self-contained"
```

---

### Task 3: 重建并验收 rc2 安装器

**Files:**
- Generated ignored: `dist/KuishuQuiz-Win7/`
- Generated ignored: `dist/installer/KuishuQuiz-Win7-Setup-1.6.0-win7-rc2.exe`
- Generated ignored: `KuishuQuiz-Win7-Setup-1.6.0-win7-rc2.exe`
- Generated ignored: `KuishuQuiz-Win7/KuishuQuiz-Win7-Setup-1.6.0-win7-rc2.exe`

**Interfaces:**
- Consumes: Task 1 的子进程环境和 Task 2 的构建门禁/rc2 名称。
- Produces: 可复制到单位 Win7 的最终离线安装器及完整验证证据。

- [ ] **Step 1: 执行完整构建**

Run: `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\packaging\build.ps1`

Expected: pytest 全绿、PyInstaller 成功、运行库门禁通过、Inno 成功，并在三个约定位置生成同名 rc2 安装器。

- [ ] **Step 2: 审计产物**

检查三份安装器大小与 SHA-256 完全一致；安装器允许未签名但必须明确报告。检查 `KuishuQuiz-Win7.exe`、`python38.dll`、`Qt5Core.dll`、`soffice.exe` 及四个关键 VC++ DLL 的 PE Machine 都为 `0x8664`。确认 `System64` 位于最终 `_internal/third_party/libreoffice/App/libreoffice`。

- [ ] **Step 3: 运行三份真实 `.doc` 转换验收**

使用构建后 LibreOffice 转换初级、中级、高级真实文件并交给 `SectionedWordImporter`。Expected: 分别解析约 771、987、812 题，三者错误级问题均为 0。

- [ ] **Step 4: 执行应用和安装器冒烟测试**

隐藏启动 onedir 应用并等待独立数据目录创建；静默安装到临时目录，确认应用、转换器和 `System64` 存在，启动已安装应用，确认只创建 `OfflineQuiz-Win7` 数据，随后静默卸载且安装目录删除。

Expected: 所有进程退出码为 0或应用保持运行；无 Qt/缺 DLL 弹窗；临时目录可清理。

- [ ] **Step 5: 在当前主机模拟“无系统 VC++ 搜索路径”**

从打包目录运行一个诊断子进程，使用 Task 1 构造的环境启动 `soffice.com --headless --version`，确认输出 LibreOffice 版本；记录 `PATH` 首项为打包 `System64`。此检查证明代码不依赖正常父 `PATH`，但不能替代真实 Win7 最终验收。

- [ ] **Step 6: 最终验证与提交（如有仅验证记录的源码变更）**

Run: `git diff --check`、`git status --short`、全量 pytest。

Expected: 跟踪工作区干净；未跟踪 `KuishuQuiz-Win7/` 不进入提交；最终安装器位于用户指定目录。

