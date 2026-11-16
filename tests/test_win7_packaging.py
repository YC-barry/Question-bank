from __future__ import annotations

from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]


def test_pyinstaller_outputs_isolated_win7_executable():
    spec = (ROOT / "packaging" / "offline_quiz.spec").read_text(encoding="utf-8")

    assert 'name="KuishuQuiz-Win7"' in spec
    assert '"PySide2.QtWebEngineCore"' in spec
    assert '"PySide2.QtWebEngineWidgets"' in spec
    assert 'name="KuishuQuiz"' not in spec
    assert "third_party/libreoffice" not in spec


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
    assert '[Languages]' in installer
    assert 'Name: "chinesesimplified"' in installer
    assert 'MessagesFile: "ChineseSimplified.isl"' in installer
    translation = ROOT / "packaging" / "ChineseSimplified.isl"
    assert translation.is_file()
    assert "LanguageName=简体中文" in translation.read_text(encoding="utf-8")


def test_build_requires_and_copies_finished_installer_to_repository_root():
    build = (ROOT / "packaging" / "build.ps1").read_text(encoding="utf-8")

    assert '"KuishuQuiz-Win7"' in build
    assert '"KuishuQuiz-Win7-Setup-1.6.0-win7-rc1.exe"' in build
    assert "Inno Setup 6 is required" in build
    assert "Copy-Item" in build
    assert "$RootInstallerPath" in build
    assert "trim_libreoffice_languages.ps1" in build
    assert "Copy-Item -LiteralPath $LocalLibreOfficeRoot" in build
    assert "$PackagedThirdPartyPath" in build


def test_libreoffice_packaging_copy_keeps_only_simplified_chinese_resources(tmp_path):
    libreoffice = tmp_path / "App" / "libreoffice"
    for relative in (
        "program/resource/common",
        "program/resource/zh_CN",
        "program/resource/fr",
        "share/registry/res",
        "share/registry",
        "share/extensions/dict-fr",
        "share/autocorr",
        "share/autotext/common",
        "share/autotext/zh-CN",
        "share/autotext/fr",
        "share/fingerprint",
        "share/numbertext",
        "share/Scripts/python/LibreLogo",
        "share/basic/Depot",
        "share/wordbook",
        "help/media/icon-themes/cmd/32/ar",
        "readmes",
    ):
        (libreoffice / relative).mkdir(parents=True, exist_ok=True)
    (libreoffice / "program" / "soffice.exe").write_bytes(b"stub")
    (libreoffice / "LibreOffice_25.2.7.2_Win_x86-64.msi").write_bytes(b"installer")
    (libreoffice / "program/resource/fr/messages.mo").write_text("fr", encoding="utf-8")
    (libreoffice / "program/resource/zh_CN/messages.mo").write_text("zh", encoding="utf-8")
    (libreoffice / "share/registry/res/registry_fr.xcd").write_text("fr", encoding="utf-8")
    (libreoffice / "share/registry/res/registry_zh-CN.xcd").write_text("zh", encoding="utf-8")
    (libreoffice / "share/registry/Langpack-fr.xcd").write_text("fr", encoding="utf-8")
    (libreoffice / "share/registry/Langpack-zh-TW.xcd").write_text("zh-TW", encoding="utf-8")
    (libreoffice / "share/registry/Langpack-zh-CN.xcd").write_text("zh-CN", encoding="utf-8")
    (libreoffice / "share/registry/cjk_zh-TW.xcd").write_text("zh-TW", encoding="utf-8")
    (libreoffice / "share/registry/cjk_zh-CN.xcd").write_text("zh-CN", encoding="utf-8")
    (libreoffice / "share/registry/base.xcd").write_text("common", encoding="utf-8")
    (libreoffice / "share/extensions/dict-fr/fr.dic").write_text("fr", encoding="utf-8")
    (libreoffice / "share/autocorr/acor_fr.dat").write_text("fr", encoding="utf-8")
    (libreoffice / "share/autocorr/acor_zh-CN.dat").write_text("zh", encoding="utf-8")
    (libreoffice / "share/autotext/common/standard.bau").write_text("common", encoding="utf-8")
    (libreoffice / "share/autotext/zh-CN/standard.bau").write_text("zh", encoding="utf-8")
    (libreoffice / "share/autotext/fr/standard.bau").write_text("fr", encoding="utf-8")
    (libreoffice / "share/fingerprint/en.lm").write_text("en", encoding="utf-8")
    (libreoffice / "share/fingerprint/zh-Hant.lm").write_text("zh-Hant", encoding="utf-8")
    (libreoffice / "share/fingerprint/zh-Hans.lm").write_text("zh-Hans", encoding="utf-8")
    (libreoffice / "share/numbertext/en.sor").write_text("en", encoding="utf-8")
    (libreoffice / "share/numbertext/zh.sor").write_text("zh", encoding="utf-8")
    (libreoffice / "share/numbertext/Suzhou.sor").write_text("zh", encoding="utf-8")
    (libreoffice / "share/Scripts/python/LibreLogo/LibreLogo.py").write_text("common", encoding="utf-8")
    (libreoffice / "share/Scripts/python/LibreLogo/LibreLogo_fr.properties").write_text("fr", encoding="utf-8")
    (libreoffice / "share/Scripts/python/LibreLogo/LibreLogo_zh_TW.properties").write_text("zh-TW", encoding="utf-8")
    (libreoffice / "share/Scripts/python/LibreLogo/LibreLogo_zh_CN.properties").write_text("zh-CN", encoding="utf-8")
    (libreoffice / "share/basic/Depot/CommonLang.xba").write_text("common", encoding="utf-8")
    (libreoffice / "share/basic/Depot/Lang_en.xba").write_text("en", encoding="utf-8")
    (libreoffice / "share/basic/Depot/Lang_tw.xba").write_text("zh-TW", encoding="utf-8")
    (libreoffice / "share/basic/Depot/Lang_zh.xba").write_text("zh-CN", encoding="utf-8")
    (libreoffice / "share/wordbook/en-US.dic").write_text("en", encoding="utf-8")
    (libreoffice / "help/media/icon-themes/cmd/32/ar/defaultbullet.svg").write_text(
        "ar", encoding="utf-8"
    )
    (libreoffice / "readmes/readme_fr.txt").write_text("fr", encoding="utf-8")
    (libreoffice / "readmes/readme_zh-CN.txt").write_text("zh", encoding="utf-8")

    completed = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(ROOT / "packaging" / "trim_libreoffice_languages.ps1"),
            "-LibreOfficeRoot",
            str(libreoffice),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert (libreoffice / "program/resource/common").is_dir()
    assert (libreoffice / "program/resource/zh_CN").is_dir()
    assert not (libreoffice / "program/resource/fr").exists()
    assert (libreoffice / "share/registry/res/registry_zh-CN.xcd").is_file()
    assert not (libreoffice / "share/registry/res/registry_fr.xcd").exists()
    assert (libreoffice / "share/registry/Langpack-zh-CN.xcd").is_file()
    assert (libreoffice / "share/registry/cjk_zh-CN.xcd").is_file()
    assert (libreoffice / "share/registry/base.xcd").is_file()
    assert not (libreoffice / "share/registry/Langpack-fr.xcd").exists()
    assert not (libreoffice / "share/registry/Langpack-zh-TW.xcd").exists()
    assert not (libreoffice / "share/registry/cjk_zh-TW.xcd").exists()
    assert not any((libreoffice / "share/extensions").iterdir())
    assert (libreoffice / "share/autocorr/acor_zh-CN.dat").is_file()
    assert not (libreoffice / "share/autocorr/acor_fr.dat").exists()
    assert (libreoffice / "share/autotext/common").is_dir()
    assert (libreoffice / "share/autotext/zh-CN").is_dir()
    assert not (libreoffice / "share/autotext/fr").exists()
    assert [path.name for path in (libreoffice / "share/fingerprint").iterdir()] == ["zh-Hans.lm"]
    assert sorted(path.name for path in (libreoffice / "share/numbertext").iterdir()) == [
        "Suzhou.sor",
        "zh.sor",
    ]
    assert sorted(path.name for path in (libreoffice / "share/Scripts/python/LibreLogo").iterdir()) == [
        "LibreLogo.py",
        "LibreLogo_zh_CN.properties",
    ]
    assert sorted(path.name for path in (libreoffice / "share/basic/Depot").iterdir()) == [
        "CommonLang.xba",
        "Lang_zh.xba",
    ]
    assert not (libreoffice / "share/wordbook").exists()
    assert (libreoffice / "readmes/readme_zh-CN.txt").is_file()
    assert not (libreoffice / "readmes/readme_fr.txt").exists()
    assert not (libreoffice / "help").exists()
    assert not (libreoffice / "LibreOffice_25.2.7.2_Win_x86-64.msi").exists()

