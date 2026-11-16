# 第三方组件说明

本文件对应岿枢题典 Windows 7 SP1 x64 候选版。固定构建基线为 Python 3.8.10、PySide2 5.15.2.1 和 LibreOffice 25.2.7；目标系统需要 KB4490628、KB4474419、KB2999226，用户数据目录为 `%LOCALAPPDATA%\OfflineQuiz-Win7\data`。

## LibreOffice Portable 25.2.7 Multilingual All (Windows x86-64)

用途：在完全离线环境中把旧版 Word `.doc` 临时副本转换为 `.docx`，供题库解析器读取。程序使用隔离的临时配置目录，不修改源文件，也不启用在线更新。

- 获取地址：`https://mirrors.ibiblio.org/libreoffice/portable/25.2.7/LibreOfficePortablePrevious_25.2.7_MultilingualAll.paf.exe`
- 安装源 SHA-256：`60FCD0F2329D1FE3CE0C9A673C41A8C03B3E24DF76C82142DF5F2FBF5F42EA0A`
- Authenticode 签名者：`RARE IDEAS, LLC`

LibreOffice 及其第三方组件的许可证和声明随安装目录一并提供：

- `third_party/libreoffice/App/libreoffice/LICENSE.html`
- `third_party/libreoffice/App/libreoffice/license.txt`
- `third_party/libreoffice/App/libreoffice/NOTICE`
- `third_party/libreoffice/Other/Source/License.txt`

LibreOffice 是独立的第三方自由软件项目。本软件仅调用其无界面转换能力。

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
