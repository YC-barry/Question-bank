# 岿枢题典

面向 Windows 10/11 x64 的本地题库、考试与刷题工具。程序不需要联网，不上传题库、答案或成绩。

## 已实现功能

- 直接导入机修钳工旧版 Word `.doc`，也支持固定模板的 `.docx`、`.xlsx` 和 `.pptx`。
- 支持填空、判断、选择、简答、计算五大类题型（模板仍兼容多选题）。
- 随机抽题组成总分精确为 100 分的试卷；客观题自动评分，简答和计算题先给建议分再由用户确认。
- 交卷后逐题回看用户答案、正确答案、得分和解析。
- 按导入顺序从头到尾刷题；判断题点击选项后立即批改，其他题提交后显示结果和正确答案。
- 保存考试记录与错题，支持标记已掌握。
- 本地 SQLite 存储、自动备份、手动备份与恢复。
- 显示题目中的图片和公式，并把附件保存在历史快照中。
- 在设置页一键导出包含五类题型示例的 Excel、Word、PPT 模板。
- 全新学习首页、左侧导航、专项筛选、错题强化、题号导航和大尺寸答案解析区。
- 无需登录或注册；所有功能继续保持完全离线。

## 本地开发

需要 Python 3.12：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m offline_quiz.app
```

运行测试：

```powershell
$env:QT_QPA_PLATFORM="offscreen"
.\.venv\Scripts\python.exe -m pytest
```

## Windows 打包

安装 Inno Setup 6，并按 [`third_party/README.md`](third_party/README.md) 准备好本地 LibreOffice Portable 后运行：

```powershell
.\packaging\build.ps1
```

脚本先运行测试，再生成 `dist\KuishuQuiz` 应用目录，并在 Inno Setup 可用时生成 `dist\installer\KuishuQuiz-Setup-1.5.1-test8.exe`。

> GitHub 仓库只保存可维护的源码、测试、打包脚本和界面素材。虚拟环境、构建产物、用户题库数据库以及体积过大的 LibreOffice 二进制文件均不会提交。

## 格式边界

程序不使用 AI，也不从普通文章、扫描件或任意排版课件中自动生成题目。旧版 `.doc` 仅识别机修钳工题库的五章节结构；其他 Word、Excel 和 PPT 应使用设置页导出的固定模板。原文缺少答案或只有图片公式时会明确标记为待人工补充，不会伪造答案或直接判零分。
