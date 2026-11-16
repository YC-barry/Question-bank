# 第三方本地打包依赖

本目录中的 LibreOffice 25.2.7 Portable 只用于把旧版 `.doc` 题库离线转换为可解析格式。它不会被提交到 GitHub，因为其展开目录包含超过 GitHub 普通仓库单文件限制的二进制文件。

该依赖属于岿枢题典 Windows 7 SP1 x64 候选版的固定构建基线：Python 3.8.10、PySide2 5.15.2.1、LibreOffice 25.2.7。目标 Win7 系统还需要 KB4490628、KB4474419 和 KB2999226；用户数据与现代版隔离在 `%LOCALAPPDATA%\OfflineQuiz-Win7\data`。

在一台新电脑上重新打包前：

1. 下载 `LibreOfficePortablePrevious_25.2.7_MultilingualAll.paf.exe`：
   <https://mirrors.ibiblio.org/libreoffice/portable/25.2.7/LibreOfficePortablePrevious_25.2.7_MultilingualAll.paf.exe>
2. 校验安装文件 SHA-256：
   `60FCD0F2329D1FE3CE0C9A673C41A8C03B3E24DF76C82142DF5F2FBF5F42EA0A`
   Authenticode 状态应为有效，签名者应为 `RARE IDEAS, LLC`。
3. 将其解压或安装到当前目录的 `libreoffice` 子目录。
4. 确认以下文件存在：
   `third_party/libreoffice/App/libreoffice/program/soffice.exe`
5. 安装 Inno Setup 6，然后在项目根目录执行：
   `powershell -ExecutionPolicy Bypass -File .\packaging\build.ps1`

许可信息和来源记录见项目根目录的 `THIRD_PARTY_NOTICES.md`。已经生成的安装包可直接使用，不要求目标电脑单独安装 LibreOffice；在真实 Win7 SP1 x64 设备验收通过前，应继续按候选版管理。
