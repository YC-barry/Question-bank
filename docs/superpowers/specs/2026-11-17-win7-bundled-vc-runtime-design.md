# Win7 内置 VC++ 运行库修复设计

## 意图

修复 `1.6.0-win7-rc1` 在干净的 Windows 7 SP1 x64 上导入旧版 Word 时，LibreOffice 因找不到 `MSVCP140_ATOMIC_WAIT.dll` 而无法启动的问题。新候选版必须完全离线工作，不要求单位电脑额外安装 `VC_redist.x64.exe`，也不从网络下载 DLL。

## 已确认根因

官方 LibreOffice x64 MSI 的提取目录已经包含完整的 x64 VC++ 运行库，位于 `App/libreoffice/System64`；其中 `msvcp140_atomic_wait.dll` 的 PE 架构是 `0x8664`。当前转换代码直接启动 `program/soffice.exe`，但没有把同一 LibreOffice 根目录下的 `System64` 加入子进程 DLL 搜索路径。开发电脑已有系统级 VC++ 运行库，所以测试通过；单位的干净 Win7 没有该系统级运行库，Windows 加载器因此终止 `soffice.bin`。

## 目标

- 转换子进程优先从安装包内的 `App/libreoffice/System64` 加载 x64 VC++ DLL。
- 安装和运行不需要管理员权限，不修改 Windows 系统目录，不额外安装 VC++ 运行库。
- 构建阶段验证 `msvcp140_atomic_wait.dll`、`msvcp140.dll`、`vcruntime140.dll` 和 `vcruntime140_1.dll` 等关键文件确实进入最终应用目录。
- 当转换器仍无法启动时，错误信息包含退出代码和“安装包可能不完整”的明确诊断，不再只显示“转换组件返回错误”。
- 版本升级为 `1.6.0-win7-rc2`，重新生成中文安装器，并将最终安装器额外复制到仓库内的 `KuishuQuiz-Win7` 目录。
- 用现有三份真实 `.doc` 重跑转换与解析验收，并完成应用启动、静默安装和卸载验证。

## 非目标

- 不从第三方 DLL 网站下载单个运行库文件。
- 不在目标电脑静默安装或升级系统级 `VC_redist`。
- 不改变 Win10/11 现代版，也不共享其数据目录。
- 不改动历史 `rc1` 设计和实施计划中的版本记录。

## 方案比较

### 方案 A：为转换子进程注入自带 `System64` 路径（采用）

根据 `soffice.exe` 的实际位置推导 LibreOffice 根目录，把存在的 `System64` 置于子进程 `PATH` 最前端。Windows 加载器因此能找到 MSI 自带且版本匹配的全部 x64 VC++ DLL。此方案完全离线、无需提权、不复制重复 DLL，并保持运行库只对转换进程可见。

### 方案 B：把 `System64` DLL 复制进 `program`

加载规则简单，但会复制和散落同一批 DLL，增加版本漂移及后续 LibreOffice 升级时的维护风险。

### 方案 C：在安装器中运行 `VC_redist.x64.exe`

这是微软标准的系统级部署方式，但需要管理员权限并修改单位电脑；当前最新运行库不再支持 Win7，还必须固定历史安装包。它不符合“复制一个离线安装器即可使用”的目标。

## 详细设计

`DocConversionService` 保存传入的转换器路径。每次创建 LibreOffice 子进程时复制当前环境；如果转换器根目录存在 `System64`，就把该绝对路径放到 `PATH` 首位。只加入 `System64`，不加入包含 x86 DLL 的 `System`。测试用假转换器没有该目录时，环境保持原样。

转换失败且标准输出、标准错误均为空时，错误详情改为包含十六进制/十进制退出代码的中文诊断。现有两阶段 `doc -> docx`、`doc -> odt -> docx` 回退逻辑保持不变。

`packaging/build.ps1` 在复制并裁剪 LibreOffice 后验证关键 x64 运行库文件；任一缺失立即终止构建。版本号在应用、Inno Setup、构建脚本、README 和对应测试中统一改为 `1.6.0-win7-rc2`。成功生成安装器后保留根目录副本，并额外复制到 `KuishuQuiz-Win7/KuishuQuiz-Win7-Setup-1.6.0-win7-rc2.exe`。

## 测试与验收

- 单元测试先证明转换子进程能看到以 `System64` 开头的 `PATH`，并验证缺失运行库时不会伪造该路径。
- 单元测试验证无输出的非零退出会给出退出代码诊断。
- 打包测试验证 rc2 文件名、关键 DLL 构建门禁和同目录发布副本。
- 全量 pytest 必须通过。
- 构建后检查应用、Python、Qt、LibreOffice 和关键 VC++ DLL 均为 x64。
- 使用初级、中级、高级三份真实 `.doc` 进行转换解析，错误级问题必须为 0。
- 最终安装器完成启动、安装、独立数据目录与卸载冒烟验证。

## 风险与控制

- 如果 Windows 7 加载器不接受通过 `PATH` 提供的运行库，真实 Win7 仍会失败；构建后需把 rc2 带回同一台单位电脑运行 `soffice.com --headless --version` 作为最终环境验收。
- `KuishuQuiz-Win7` 当前也被用作本机安装目录，卸载会删除其中额外放入的安装器；生成后应先复制安装器到U盘或其他发布目录。
