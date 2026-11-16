from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_pyinstaller_outputs_isolated_win7_executable():
    spec = (ROOT / "packaging" / "offline_quiz.spec").read_text(encoding="utf-8")

    assert 'name="KuishuQuiz-Win7"' in spec
    assert '"PySide2.QtWebEngineCore"' in spec
    assert '"PySide2.QtWebEngineWidgets"' in spec
    assert 'name="KuishuQuiz"' not in spec


def test_inno_installer_targets_win7_sp1_x64_and_isolated_paths():
    installer = (ROOT / "packaging" / "offline_quiz.iss").read_text(encoding="utf-8")

    assert '#define MyAppName "岿枢题典（Win7 兼容版）"' in installer
    assert '#define MyAppVersion "1.6.0-win7-rc1"' in installer
    assert '#define MyAppExeName "KuishuQuiz-Win7.exe"' in installer
    assert "AppId={{2036CD91-3AF2-410A-9C3D-6C73893BDB4B}" in installer
    assert "MinVersion=6.1sp1" in installer
    assert "ArchitecturesAllowed=x64compatible" in installer
    assert "ArchitecturesInstallIn64BitMode=x64compatible" in installer
    assert "PrivilegesRequired=lowest" in installer
    assert r"DefaultDirName={localappdata}\Programs\KuishuQuiz-Win7" in installer
    assert r'Source: "..\dist\KuishuQuiz-Win7\*"' in installer
    assert r"{localappdata}\OfflineQuiz-Win7" in installer
    assert r"{localappdata}\OfflineQuiz')," not in installer


def test_build_requires_and_copies_finished_installer_to_repository_root():
    build = (ROOT / "packaging" / "build.ps1").read_text(encoding="utf-8")

    assert '"KuishuQuiz-Win7"' in build
    assert '"KuishuQuiz-Win7-Setup-1.6.0-win7-rc1.exe"' in build
    assert "Inno Setup 6 is required" in build
    assert "Copy-Item" in build
    assert "$RootInstallerPath" in build

