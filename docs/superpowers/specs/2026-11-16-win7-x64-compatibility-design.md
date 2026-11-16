# Windows 7 x64 Compatibility Edition Design

## Intent

在独立的 `Question-bank - win7` 仓库副本中制作岿枢题典 Win7 兼容版。现代版继续使用 Python 3.12、PySide6/Qt 6 和新版 LibreOffice，不在本项目中修改；兼容版面向 Windows 7 SP1 x64，同时允许在 Windows 10/11 x64 上运行。

## Goals

- 保留现有题库导入、考试、刷题、评分、错题、历史、解析资料、模板、备份与恢复功能。
- 保持现有 SQLite 数据库结构和备份格式，避免仅为系统兼容而改变业务数据。
- 使用 Win7 可运行的 Python、Qt、文档转换和打包依赖，生成独立的 64 位安装包。
- 让 Win7 版拥有独立的应用名称、安装目录、安装器 AppId 和构建产物名称，避免覆盖现代版。
- README、第三方说明和安装器准确标明最低系统、补丁前提、依赖版本及已验证范围。

## Non-goals

- 不支持 Windows 7 32 位、Vista、XP 或未安装 SP1 的 Windows 7。
- 不把现代版降级，也不要求两个仓库长期共用完全相同的依赖。
- 不新增业务功能，不借迁移机会改数据库表结构或重做界面。
- 不承诺未打补丁的原始 Win7 SP1 镜像可以直接运行。

## Compatibility Baseline

- Python：CPython 3.8.10 x64，使用仍提供官方 Windows 安装程序且支持 Win7 的 3.8 系列基线。
- Qt 绑定：PySide2 5.15.2.1 x64；其 PyPI wheel 覆盖 CPython 3.8 和 Windows x86-64。
- LibreOffice：优先使用 LibreOffice Portable 25.2.7 x64，它属于移除 Win7 支持之前的最后一个 25.2 维护版本；在真实 Win7 上验证失败时，回退到较早、仍受 Win7 支持的稳定版本。
- 其他运行与测试依赖：选择各自支持 Python 3.8 的最后适用版本，全部精确锁定并记录来源与 SHA-256。
- 系统最低要求：Windows 7 SP1 x64，并至少安装 KB4490628（服务堆栈）、2019-09-23 或更新版本的 KB4474419（SHA-2）以及 KB2999226（Universal CRT），随后完成重启；Visual C++ 运行环境以候选包实机启动结果确定是否还需随包处理。

## Application Changes

### Qt compatibility

- 把产品代码和测试中的 `PySide6` 导入迁移到 `PySide2`。
- 将 Qt 6 的 `exec()` 调用适配为 Qt 5 可用的事件循环和对话框调用方式。
- 把 `QSvgWidget` 从 Qt 6 的 `QtSvgWidgets` 位置适配到 Qt 5 的 `QtSvg`。
- 在创建 `QApplication` 前配置 Qt 5 高分屏属性，随后检查字体、表格、滚动区域、阴影、SVG 和绘图控件。
- 不建立同时加载 PySide2/PySide6 的运行时兼容层；该仓库只构建 PySide2 版，以降低打包和测试复杂度。

### Python and dependency compatibility

- 将 `requires-python` 改为 Python 3.8 兼容范围。
- 移除所有 Python 3.9 及以上才支持的语法或标准库用法；以现有测试锁定行为。
- 更新 `pyproject.toml`、锁定文件、pytest 配置和 egg-info/生成元数据，禁止残留 PySide6 声明。
- 在全新 Python 3.8.10 x64 虚拟环境中解析并锁定依赖，不复用现代版虚拟环境。

### Document conversion

- 替换 `third_party/libreoffice` 中的现代 LibreOffice Portable；该大型二进制仍不提交 Git。
- 更新第三方下载说明、版本、校验值和许可证记录。
- 使用真实初级、中级、高级 `.doc` 题库对比转换后的题目数、题型、答案、解析、图片和公式。
- `.docx`、`.xlsx`、`.pptx` 继续由 Python 库解析，并执行现有导入测试与模板回归测试。

## Packaging and Installation

- PyInstaller 必须在 Python 3.8 x64 环境中构建；构建机上的依赖二进制不得要求 Win8/10 API。
- PyInstaller spec 改为 PySide2 排除项并保留现有资源、LibreOffice 和许可证文件。
- Inno Setup 设置最低系统为 Windows 7 SP1、限定 64 位，并使用独立 AppId、安装目录和输出名，例如 `KuishuQuiz-Win7-Setup-*`。
- Win7 版保留每用户安装；若真实 Win7 缺少 Universal CRT，则优先记录并检查必需系统补丁。只有在确认许可证、静默安装和管理员权限策略后，才考虑随安装包携带微软运行库安装程序。
- 安装器不得宣称支持未经真实机器验证的系统组合。

## Data and Coexistence

- 数据库 schema、备份格式和业务语义保持不变，已有备份可用于迁移验证。
- 安装目录、安装器身份和本地数据目录均与现代版隔离；Win7 版使用独立的 `%LOCALAPPDATA%\OfflineQuiz-Win7`，允许两版安装、运行和卸载时互不覆盖或误删数据。
- 从现代版迁移数据必须通过“手动备份—恢复”显式完成，不自动读取或写入现代版数据目录。恢复前仍由现有安全备份机制保护目标数据库。
- Win7 版卸载器只能询问并删除 `OfflineQuiz-Win7`，不得删除现代版的 `OfflineQuiz`。
- 如果未来现代版升级数据库 schema，Win7 版必须增加版本拒绝或迁移策略，不能假设永久双向兼容。

## Error Handling

- 启动失败必须保留可诊断日志，区分缺少系统补丁、运行库、Qt 插件和 LibreOffice 启动失败。
- 文档转换失败继续按单文件报告，不破坏其他导入任务或已有题库。
- 若依赖在 Win7 上无法可靠运行，构建标记为候选版，不得仅凭 Win10 测试标记为 Win7 正式版。

## Approaches Considered

### 1. 一个安装包覆盖 Win7 至 Win11

所有用户都使用 Python 3.8、Qt 5 和旧 LibreOffice。发布简单，但会把现代系统永久绑定到停止维护的旧依赖，安全与后续开发成本最高，因此未选。

### 2. 同一仓库维护双依赖、生成两个安装包

业务代码共享，通过兼容层同时测试 PySide2 和 PySide6。减少代码复制，但构建矩阵、Qt 差异和每次发布的回归成本较高，且现有现代版已单独备份，因此本次不选。

### 3. 独立 Win7 兼容仓库副本

现代版保持原技术栈，`Question-bank - win7` 固定旧依赖并独立发布。会产生后续功能同步成本，但隔离清晰、不会降低现代版安全基线，也是用户选定的方案。

## Verification

自动验证包括完整 pytest 套件、依赖元数据检查、禁止 PySide6 残留、离屏 Qt UI 测试、PyInstaller 构建和安装器生成。

人工验证至少包括：

- 在全新 Windows 7 SP1 x64 实机或可信虚拟机上安装、首次启动、退出、再次启动和卸载。
- 在 Windows 10/11 x64 上确认兼容版仍可安装和运行。
- 导入真实 `.doc` 题库以及模板 `.docx`、`.xlsx`、`.pptx`，核对题目、答案、图片和公式。
- 完成练习、100 分试卷、主观题确认、历史回看、错题、解析资料、备份和恢复流程。
- 检查 100%、125%、150% 缩放和常见中文字体环境。
- 记录 EXE、安装包、第三方二进制的版本与 SHA-256。

仓库上级目录现有的初级、中级、高级真实 `.doc` 文件作为首轮权威样本；迁移前先用现代版记录导入统计和关键内容作为对照。最终 Win7 启动与安装验收在用户提供的 Win7 SP1 x64 实机或可信虚拟机上完成；如果该环境暂不可用，交付物保持“候选版”标记。

只有自动测试通过且真实 Win7 验证完成，README 才能把产物称为 Win7 正式兼容版；此前一律称为候选版。

## Risks and Maintenance

- Windows 7、Python 3.8 和开源 PySide2/Qt 5 基线均已停止常规安全维护，尤其不应导入来源不明的 Office 文件。
- LibreOffice 25.2 已结束维护；锁定它是兼容性选择，不代表它仍安全受支持。
- 未来从现代版同步功能时，必须单独评估 Python 3.8 和 Qt 5 可用性，不能直接复制依赖或 Qt 6 专属代码。
- 没有持续可用的 Win7 测试环境时，不能对后续版本持续作兼容保证。
