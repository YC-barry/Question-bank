# -*- mode: python ; coding: utf-8 -*-
a = Analysis(
    ["launcher.py"],
    pathex=["../src"],
    binaries=[],
    datas=[
        (
            "../third_party/libreoffice/App/libreoffice",
            "third_party/libreoffice/App/libreoffice",
        ),
        ("../src/offline_quiz/visual_assets", "offline_quiz/visual_assets"),
        ("../THIRD_PARTY_NOTICES.md", "."),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "PySide2.QtWebEngineCore",
        "PySide2.QtWebEngineWidgets",
        "numpy",
        "pandas",
        "pytest",
    ],
    noarchive=False,
    optimize=1,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="KuishuQuiz-Win7",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="KuishuQuiz-Win7",
)
