from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


class DocConversionError(RuntimeError):
    """旧版 Word 文档无法安全转换。"""


@dataclass
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
        timeout_seconds: float = 120,
        temp_root: str | Path | None = None,
    ):
        converter = Path(executable) if executable is not None else bundled_converter_path()
        self.converter_path = converter
        self.command_prefix = list(command_prefix) if command_prefix else [str(converter)]
        self.timeout_seconds = float(timeout_seconds)
        self.temp_root = Path(temp_root) if temp_root is not None else None

    def _conversion_environment(self) -> dict[str, str]:
        environment = os.environ.copy()
        runtime_dir = self.converter_path.parent.parent / "System64"
        if runtime_dir.is_dir():
            current_path = environment.get("PATH", "")
            environment["PATH"] = (
                os.pathsep.join((str(runtime_dir), current_path))
                if current_path
                else str(runtime_dir)
            )
        return environment

    def _run_conversion(
        self,
        source: Path,
        output_dir: Path,
        profile_dir: Path,
        format_name: str,
    ) -> tuple[int, str]:
        output_dir.mkdir(parents=True, exist_ok=True)
        profile_dir.mkdir(parents=True, exist_ok=True)
        command = [
            *self.command_prefix,
            "--headless",
            "--nologo",
            "--nodefault",
            "--nolockcheck",
            "--nofirststartwizard",
            f"-env:UserInstallation={profile_dir.resolve().as_uri()}",
            "--convert-to",
            format_name,
            "--outdir",
            str(output_dir),
            str(source),
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
            env=self._conversion_environment(),
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
        details = (stderr or stdout).strip()
        if not details:
            details = (
                f"转换组件无法启动（退出代码 {process.returncode}），"
                "安装包可能不完整或系统组件不兼容"
            )
        return process.returncode, details

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
        output_dir.mkdir()
        try:
            shutil.copy2(source_path, source_copy)
            return_code, direct_details = self._run_conversion(
                source_copy,
                output_dir,
                workspace / "profile-direct",
                "docx:Office Open XML Text",
            )
            destination = output_dir / f"{source_copy.stem}.docx"
            if return_code != 0 or not destination.exists() or destination.stat().st_size == 0:
                shutil.rmtree(output_dir, ignore_errors=True)
                output_dir.mkdir()
                normalized_dir = workspace / "normalized"
                odt_code, odt_details = self._run_conversion(
                    source_copy,
                    normalized_dir,
                    workspace / "profile-odt",
                    "odt",
                )
                normalized = normalized_dir / f"{source_copy.stem}.odt"
                if odt_code != 0 or not normalized.exists() or normalized.stat().st_size == 0:
                    details = odt_details or direct_details
                    raise DocConversionError(f"无法转换旧版 Word 文件：{details[:240]}")
                docx_code, docx_details = self._run_conversion(
                    normalized,
                    output_dir,
                    workspace / "profile-docx",
                    "docx:Office Open XML Text",
                )
                if docx_code != 0 or not destination.exists() or destination.stat().st_size == 0:
                    details = docx_details or direct_details
                    raise DocConversionError(f"无法转换旧版 Word 文件：{details[:240]}")
            return ConvertedDocument(destination, workspace)
        except DocConversionError:
            shutil.rmtree(workspace, ignore_errors=True)
            raise
        except (OSError, subprocess.SubprocessError) as exc:
            shutil.rmtree(workspace, ignore_errors=True)
            raise DocConversionError(f"无法转换旧版 Word 文件：{exc}") from exc
