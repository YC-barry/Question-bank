# 第三方本地打包依赖

本目录中的 LibreOffice 25.2.7.2 x64 只用于把旧版 `.doc` 题库离线转换为可解析格式。它不会被提交到 GitHub，因为其展开目录包含超过 GitHub 普通仓库单文件限制的二进制文件。

该依赖属于岿枢题典 Windows 7 SP1 x64 候选版的固定构建基线：Python 3.8.10、PySide2 5.15.2.1、LibreOffice 25.2.7。目标 Win7 系统还需要 KB4490628、KB4474419 和 KB2999226；用户数据与现代版隔离在 `%LOCALAPPDATA%\OfflineQuiz-Win7\data`。

在一台新电脑上重新打包前：

1. 从 The Document Foundation 官方历史站下载 `LibreOffice_25.2.7.2_Win_x86-64.msi`：
   <https://downloadarchive.documentfoundation.org/libreoffice/old/25.2.7.2/win/x86_64/LibreOffice_25.2.7.2_Win_x86-64.msi>
2. 校验安装文件 SHA-256：
   `9FDD22F8EA7A92A67DE5BEAA08588EF6DA58C1930AC86FD57C46B0C6D7CA9D34`
   Authenticode 状态应为有效，签名者应为 `The Document Foundation`。
3. 使用 MSI 管理模式解包，不需要安装到系统：
   `msiexec.exe /a LibreOffice_25.2.7.2_Win_x86-64.msi TARGETDIR=<临时目录> /qn`
   将临时目录中的完整内容放到 `third_party/libreoffice/App/libreoffice`。
4. 确认以下文件存在：
   `third_party/libreoffice/App/libreoffice/program/soffice.exe`
5. 安装 Inno Setup 6，然后在项目根目录执行：
   `powershell -ExecutionPolicy Bypass -File .\packaging\build.ps1`

官方 MSI 包含多语言资源以便固定来源和校验值；构建脚本只精简生成目录中的副本，保留通用运行组件和简体中文资源，删除其他语言资源、无界面转换不需要的帮助模块及管理解包残留的 MSI，不修改本目录中的原始依赖。

许可信息和来源记录见项目根目录的 `THIRD_PARTY_NOTICES.md`。已经生成的安装包可直接使用，不要求目标电脑单独安装 LibreOffice；在真实 Win7 SP1 x64 设备验收通过前，应继续按候选版管理。
