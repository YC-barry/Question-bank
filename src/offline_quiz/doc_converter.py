from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


class DocConversionError(RuntimeError):
    """旧版 Word 文档无法安全转换。"""


@dataclass(slots=True)
class ConvertedDocument:
    path: Path
    _workspace: Path

    def cleanup(self) -> None:
        shutil.rmtree(self._workspace, ignore_errors=True)

    def __enter__(self) -> "ConvertedDocument":
        return self

    def __exit__(self, *_args) -> None:
        self.cleanup()


def bundled_converter_path() -> Path:
    if getattr(sys, "frozen", False):
        root = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    else:
        root = Path(__file__).resolve().parents[2]
    return (
        root
        / "third_party"
        / "libreoffice"
        / "App"
        / "libreoffice"
        / "program"
        / "soffice.exe"
    )


class DocConversionService:
    def __init__(
        self,
        *,
        executable: str | Path | None = None,
        command_prefix: list[str] | None = None,
        timeout_seconds: float = 60,
        temp_root: str | Path | None = None,
    ):
        converter = Path(executable) if executable is not None else bundled_converter_path()
        self.command_prefix = list(command_prefix) if command_prefix else [str(converter)]
        self.timeout_seconds = float(timeout_seconds)
        self.temp_root = Path(temp_root) if temp_root is not None else None

    def convert(self, source: str | Path) -> ConvertedDocument:
        source_path = Path(source)
        if not source_path.exists():
            raise DocConversionError("旧版 Word 文件不存在")
        if source_path.suffix.lower() != ".doc":
            raise DocConversionError("只能转换扩展名为 .doc 的旧版 Word 文件")
        if self.temp_root is not None:
            self.temp_root.mkdir(parents=True, exist_ok=True)
        workspace = Path(
            tempfile.mkdtemp(prefix="offline-quiz-doc-", dir=self.temp_root)
        )
        source_copy = workspace / source_path.name
        output_dir = workspace / "converted"
        profile_dir = workspace / "profile"
        output_dir.mkdir()
        profile_dir.mkdir()
        try:
            shutil.copy2(source_path, source_copy)
            command = [
                *self.command_prefix,
                "--headless",
                "--nologo",
                "--nodefault",
                "--nolockcheck",
                "--nofirststartwizard",
                f"-env:UserInstallation={profile_dir.resolve().as_uri()}",
                "--convert-to",
                "docx:Office Open XML Text",
                "--outdir",
                str(output_dir),
                str(source_copy),
            ]
            creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=creation_flags,
            )
            try:
                stdout, stderr = process.communicate(timeout=self.timeout_seconds)
            except subprocess.TimeoutExpired as exc:
                process.terminate()
                try:
                    process.communicate(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.communicate()
                raise DocConversionError("转换旧版 Word 文件超时，请检查文件是否损坏") from exc
            if process.returncode != 0:
                details = (stderr or stdout or "转换组件返回错误").strip()
                raise DocConversionError(f"无法转换旧版 Word 文件：{details[:240]}")
            destination = output_dir / f"{source_copy.stem}.docx"
            if not destination.exists() or destination.stat().st_size == 0:
                raise DocConversionError("无法转换旧版 Word 文件：未生成有效的 .docx 文件")
            return ConvertedDocument(destination, workspace)
        except DocConversionError:
            shutil.rmtree(workspace, ignore_errors=True)
            raise
        except (OSError, subprocess.SubprocessError) as exc:
            shutil.rmtree(workspace, ignore_errors=True)
            raise DocConversionError(f"无法转换旧版 Word 文件：{exc}") from exc
