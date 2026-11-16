from __future__ import annotations

from pathlib import Path
import sys
import time

import pytest
from docx import Document

from offline_quiz.database import Database
from offline_quiz.doc_converter import DocConversionError, DocConversionService
from offline_quiz.import_service import ImportService


def _write_converter(tmp_path: Path, body: str) -> Path:
    script = tmp_path / "fake_converter.py"
    script.write_text(body, encoding="utf-8")
    return script


def test_convert_uses_isolated_copy_and_returns_docx(tmp_path):
    converter = _write_converter(
        tmp_path,
        """
from pathlib import Path
import shutil
import sys
args = sys.argv[1:]
out_dir = Path(args[args.index('--outdir') + 1])
source = Path(args[-1])
out_dir.mkdir(parents=True, exist_ok=True)
shutil.copy2(source, out_dir / f'{source.stem}.docx')
""",
    )
    source = tmp_path / "原始题库.doc"
    source.write_bytes(b"original-doc-content")
    original = source.read_bytes()
    work_root = tmp_path / "working"
    service = DocConversionService(
        command_prefix=[sys.executable, str(converter)],
        temp_root=work_root,
    )

    converted = service.convert(source)

    assert converted.path.suffix == ".docx"
    assert converted.path.read_bytes() == original
    assert converted.path.parent != source.parent
    assert source.read_bytes() == original
    converted.cleanup()
    assert not converted.path.parent.exists()


def test_timeout_terminates_spawned_process_and_cleans_temp(tmp_path):
    marker = tmp_path / "must-not-exist.txt"
    converter = _write_converter(
        tmp_path,
        f"""
from pathlib import Path
import time
time.sleep(2)
Path({str(marker)!r}).write_text('late', encoding='utf-8')
""",
    )
    source = tmp_path / "slow.doc"
    source.write_bytes(b"slow")
    work_root = tmp_path / "working"
    service = DocConversionService(
        command_prefix=[sys.executable, str(converter)],
        timeout_seconds=0.1,
        temp_root=work_root,
    )

    with pytest.raises(DocConversionError, match="超时"):
        service.convert(source)

    time.sleep(0.2)
    assert not marker.exists()
    assert not work_root.exists() or not any(work_root.iterdir())


@pytest.mark.parametrize("message", ["corrupt file", "password required"])
def test_failed_conversion_raises_chinese_error_and_cleans_temp(tmp_path, message):
    converter = _write_converter(
        tmp_path,
        f"""
import sys
sys.stderr.write({message!r})
raise SystemExit(2)
""",
    )
    source = tmp_path / "broken.doc"
    source.write_bytes(b"broken")
    work_root = tmp_path / "working"
    service = DocConversionService(
        command_prefix=[sys.executable, str(converter)],
        temp_root=work_root,
    )

    with pytest.raises(DocConversionError, match="无法转换旧版 Word 文件"):
        service.convert(source)

    assert not work_root.exists() or not any(work_root.iterdir())


def test_failed_direct_docx_export_retries_through_odt(tmp_path):
    converter = _write_converter(
        tmp_path,
        """
from pathlib import Path
import shutil
import sys

args = sys.argv[1:]
format_name = args[args.index('--convert-to') + 1]
out_dir = Path(args[args.index('--outdir') + 1])
source = Path(args[-1])
out_dir.mkdir(parents=True, exist_ok=True)

if source.suffix == '.doc' and format_name.startswith('docx'):
    sys.stderr.write('direct OOXML export failed')
    raise SystemExit(9)
if format_name == 'odt':
    shutil.copy2(source, out_dir / f'{source.stem}.odt')
elif source.suffix == '.odt' and format_name.startswith('docx'):
    shutil.copy2(source, out_dir / f'{source.stem}.docx')
else:
    raise SystemExit(10)
""",
    )
    source = tmp_path / "needs-normalization.doc"
    source.write_bytes(b"legacy-content")
    service = DocConversionService(
        command_prefix=[sys.executable, str(converter)],
        temp_root=tmp_path / "working",
    )

    converted = service.convert(source)

    assert converted.path.read_bytes() == b"legacy-content"
    converted.cleanup()


def test_converter_supports_chinese_paths(tmp_path):
    converter = _write_converter(
        tmp_path,
        """
from pathlib import Path
import shutil
import sys
args = sys.argv[1:]
out_dir = Path(args[args.index('--outdir') + 1])
source = Path(args[-1])
out_dir.mkdir(parents=True, exist_ok=True)
shutil.copy2(source, out_dir / f'{source.stem}.docx')
""",
    )
    source_dir = tmp_path / "中文目录"
    source_dir.mkdir()
    source = source_dir / "机修钳工题库.doc"
    source.write_bytes("中文内容".encode("utf-8"))
    service = DocConversionService(
        command_prefix=[sys.executable, str(converter)],
        temp_root=tmp_path / "临时转换",
    )

    converted = service.convert(source)

    assert converted.path.exists()
    assert converted.path.read_bytes() == source.read_bytes()
    converted.cleanup()


def test_import_service_routes_doc_through_converter(tmp_path):
    converted_fixture = tmp_path / "converted.docx"
    document = Document()
    for line in (
        "旧版题库", "一、判断题", "1、示例判断题。（√）",
    ):
        document.add_paragraph(line)
    document.save(converted_fixture)
    converter = _write_converter(
        tmp_path,
        f"""
from pathlib import Path
import shutil
import sys
args = sys.argv[1:]
out_dir = Path(args[args.index('--outdir') + 1])
source = Path(args[-1])
out_dir.mkdir(parents=True, exist_ok=True)
shutil.copy2({str(converted_fixture)!r}, out_dir / f'{{source.stem}}.docx')
""",
    )
    source = tmp_path / "旧版题库.doc"
    source.write_bytes(b"legacy")
    conversion_service = DocConversionService(
        command_prefix=[sys.executable, str(converter)],
        temp_root=tmp_path / "work",
    )
    service = ImportService(
        Database(tmp_path / "quiz.db"),
        doc_converter=conversion_service,
    )

    result = service.preview(source)

    assert result.has_errors is False
    assert result.source_path == str(source)
    assert len(result.questions) == 1
    assert result.questions[0].answer is True


def test_import_service_reports_doc_conversion_error(tmp_path):
    converter = _write_converter(tmp_path, "raise SystemExit(3)")
    source = tmp_path / "损坏.doc"
    source.write_bytes(b"broken")
    service = ImportService(
        Database(tmp_path / "quiz.db"),
        doc_converter=DocConversionService(
            command_prefix=[sys.executable, str(converter)],
            temp_root=tmp_path / "work",
        ),
    )

    result = service.preview(source)

    assert result.has_errors is True
    assert result.issues[0].field == "文件"
    assert "无法转换旧版 Word 文件" in result.issues[0].message
