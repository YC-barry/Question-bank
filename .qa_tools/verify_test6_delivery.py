from __future__ import annotations

import hashlib
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from offline_quiz.importers import ExcelImporter, PowerPointImporter, WordImporter


VERSION = "1.5.0-test6"
EXPECTED_FILES = {
    f"KuishuQuiz-Setup-{VERSION}.exe",
    "SHA256.txt",
    "更新记录.md",
    "用户手册.md",
    "第三方组件说明.md",
    "项目说明.md",
    "题库模板.docx",
    "题库模板.pptx",
    "题库模板.xlsx",
}


def verify_delivery(directory: Path) -> None:
    names = {path.name for path in directory.iterdir() if path.is_file()}
    if names != EXPECTED_FILES:
        raise AssertionError(f"delivery files differ: {sorted(names ^ EXPECTED_FILES)}")
    installer = directory / f"KuishuQuiz-Setup-{VERSION}.exe"
    digest = hashlib.sha256(installer.read_bytes()).hexdigest().upper()
    manifest = (directory / "SHA256.txt").read_text(encoding="utf-8").strip()
    if manifest != f"{digest}  {installer.name}":
        raise AssertionError("SHA256 manifest does not match installer")
    if list(directory.rglob("*.db")):
        raise AssertionError("delivery must not contain a quiz database")
    templates = {
        "题库模板.xlsx": ExcelImporter(),
        "题库模板.docx": WordImporter(),
        "题库模板.pptx": PowerPointImporter(),
    }
    for filename, importer in templates.items():
        result = importer.parse(directory / filename)
        errors = [issue for issue in result.issues if issue.severity == "错误"]
        if errors or len(result.questions) != 5:
            raise AssertionError(
                f"{filename}: questions={len(result.questions)}, errors={errors[:3]}"
            )
    print(f"PASS: {directory} has 9 files, matching SHA-256, no DB, templates 5/5/5")


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "dist" / "release-test6"
    verify_delivery(target)
