from __future__ import annotations

from collections import Counter
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from offline_quiz.database import Database
from offline_quiz.doc_converter import DocConversionService
from offline_quiz.import_service import ImportService


EXPECTED = {
    "机修钳工理论知识初级.doc": 771,
    "机修钳工理论知识中级.doc": 987,
    "机修钳工理论知识高级.doc": 812,
}


def main() -> int:
    converter = (
        ROOT
        / "dist"
        / "KuishuQuiz"
        / "_internal"
        / "third_party"
        / "libreoffice"
        / "App"
        / "libreoffice"
        / "program"
        / "soffice.exe"
    )
    if not converter.is_file():
        raise AssertionError(f"packaged converter missing: {converter}")
    source_dir = Path(r"D:\工具\题库\机修钳工")
    with tempfile.TemporaryDirectory(prefix="test6-real-doc-") as workspace:
        service = ImportService(
            Database(Path(workspace) / "preview.db"),
            doc_converter=DocConversionService(
                executable=converter,
                timeout_seconds=120,
                temp_root=Path(workspace) / "conversion",
            ),
        )
        for filename, expected_count in EXPECTED.items():
            result = service.preview(source_dir / filename)
            errors = [issue for issue in result.issues if issue.severity == "错误"]
            if errors:
                raise AssertionError(f"{filename}: {errors[:3]}")
            if len(result.questions) != expected_count:
                raise AssertionError(
                    f"{filename}: expected {expected_count}, got {len(result.questions)}"
                )
            counts = Counter(question.question_type.value for question in result.questions)
            print(filename, len(result.questions), dict(counts))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
