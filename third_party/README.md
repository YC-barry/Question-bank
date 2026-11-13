# 第三方本地打包依赖

本目录中的 LibreOffice Portable 只用于把旧版 `.doc` 题库离线转换为可解析格式。它不会被提交到 GitHub，因为其展开目录包含超过 GitHub 普通仓库单文件限制的二进制文件。

在一台新电脑上重新打包前：

1. 下载 `LibreOfficePortable_26.2.4_MultilingualStandard.paf.exe`：
   <https://mirrors.ibiblio.org/libreoffice/portable/26.2.4/LibreOfficePortable_26.2.4_MultilingualStandard.paf.exe>
2. 校验安装文件 SHA-256：
   `4BDE93374AEF4409243505B20D16561A4628AC7591457DD01FC6E1CCF571BA65`
3. 将其解压或安装到当前目录的 `libreoffice` 子目录。
4. 确认以下文件存在：
   `third_party/libreoffice/App/libreoffice/program/soffice.exe`
5. 安装 Inno Setup 6，然后在项目根目录执行：
   `powershell -ExecutionPolicy Bypass -File .\packaging\build.ps1`

许可信息和来源记录见项目根目录的 `THIRD_PARTY_NOTICES.md`。已经生成的安装包可直接使用，不要求目标电脑单独安装 LibreOffice。
