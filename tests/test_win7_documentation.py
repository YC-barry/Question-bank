from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCUMENTS = [
    ROOT / "README.md",
    ROOT / "third_party" / "README.md",
    ROOT / "THIRD_PARTY_NOTICES.md",
]
REQUIRED_COMPATIBILITY_FACTS = [
    "Windows 7 SP1 x64",
    "Python 3.8.10",
    "PySide2 5.15.2.1",
    "LibreOffice 25.2.7",
    "KB4490628",
    "KB4474419",
    "KB2999226",
    "OfflineQuiz-Win7",
    "候选版",
]


def test_win7_compatibility_and_candidate_status_are_documented_consistently():
    for path in DOCUMENTS:
        content = path.read_text(encoding="utf-8")
        for fact in REQUIRED_COMPATIBILITY_FACTS:
            assert fact in content, f"{path.name} is missing {fact}"
        assert "26.2.4" not in content


def test_libreoffice_restore_instructions_record_verified_download():
    content = (ROOT / "third_party" / "README.md").read_text(encoding="utf-8")

    assert "LibreOfficePortablePrevious_25.2.7_MultilingualAll.paf.exe" in content
    assert "60FCD0F2329D1FE3CE0C9A673C41A8C03B3E24DF76C82142DF5F2FBF5F42EA0A" in content
    assert "RARE IDEAS, LLC" in content

