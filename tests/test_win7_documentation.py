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

    assert "LibreOffice_25.2.7.2_Win_x86-64.msi" in content
    assert "9FDD22F8EA7A92A67DE5BEAA08588EF6DA58C1930AC86FD57C46B0C6D7CA9D34" in content
    assert "The Document Foundation" in content

