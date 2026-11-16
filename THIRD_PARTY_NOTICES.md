# 第三方组件说明

本文件对应岿枢题典 Windows 7 SP1 x64 候选版。固定构建基线为 Python 3.8.10、PySide2 5.15.2.1 和 LibreOffice 25.2.7；目标系统需要 KB4490628、KB4474419、KB2999226，用户数据目录为 `%LOCALAPPDATA%\OfflineQuiz-Win7\data`。

## LibreOffice 25.2.7.2 (Windows x86-64)

用途：在完全离线环境中把旧版 Word `.doc` 临时副本转换为 `.docx`，供题库解析器读取。程序使用隔离的临时配置目录，不修改源文件，也不启用在线更新。

安装源是多语言完整版；最终安装包只保留 LibreOffice 的通用运行组件和简体中文语言资源，其他语言资源及无界面转换不需要的帮助模块会在构建时从打包副本中删除。

- 获取地址：`https://downloadarchive.documentfoundation.org/libreoffice/old/25.2.7.2/win/x86_64/LibreOffice_25.2.7.2_Win_x86-64.msi`
- 安装源 SHA-256：`9FDD22F8EA7A92A67DE5BEAA08588EF6DA58C1930AC86FD57C46B0C6D7CA9D34`
- Authenticode 签名者：`The Document Foundation`

LibreOffice 及其第三方组件的许可证和声明随安装目录一并提供：

- `third_party/libreoffice/App/libreoffice/LICENSE.html`
- `third_party/libreoffice/App/libreoffice/license.txt`
- `third_party/libreoffice/App/libreoffice/NOTICE`

LibreOffice 是独立的第三方自由软件项目。本软件仅调用其无界面转换能力。

## Inno Setup 简体中文翻译

用途：让安装和卸载向导只显示简体中文。语言文件来自 Inno Setup 官方源码仓库，由 Zhenghan Yang 维护。

- 来源：`https://github.com/jrsoftware/issrc/blob/main/Files/Languages/ChineseSimplified.isl`
- 下载文件 SHA-256：`E0B0B350E2245F3C5E65586DFE43D574F6E7F06F2261149ABA284954B3FC9A8D`
- 本地文件：`packaging/ChineseSimplified.isl`

## unDraw Graduation Illustration

用途：学习首页的本地 SVG 主视觉，主色已调整为恒枢题典冰蓝配色。

- 来源：https://undraw.co/illustration/graduation_u7uc
- 许可：https://undraw.co/license
- 作者：Katerina Limpitsouni

unDraw 允许在个人和商业项目中免费使用、复制和修改其插画，无需署名；不得将插画作为素材包重新分发或用于训练人工智能模型。

## Lucide Icons

用途：导航、统计卡片、快捷入口、答题状态和设置操作的本地 SVG 图标。

- 项目：https://lucide.dev/
- 许可：ISC License

Copyright (c) 2026 Lucide Icons and Contributors

Permission to use, copy, modify, and/or distribute this software for any purpose with or without fee is hereby granted, provided that the above copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
