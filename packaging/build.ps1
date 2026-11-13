$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$BuildPath = Join-Path $ProjectRoot "build"
$DistPath = Join-Path $ProjectRoot "dist"
$AppDistPath = Join-Path $DistPath "KuishuQuiz"
$LibreOfficePath = Join-Path $ProjectRoot "third_party\libreoffice\App\libreoffice\program\soffice.exe"

Push-Location $ProjectRoot
try {
    if (-not (Test-Path $LibreOfficePath)) {
        throw "LibreOffice offline converter is missing: $LibreOfficePath"
    }
    $env:QT_QPA_PLATFORM = "offscreen"
    & $Python -m pytest
    if ($LASTEXITCODE -ne 0) { throw "Automated tests failed" }

    Remove-Item -Recurse -Force $BuildPath -ErrorAction SilentlyContinue
    Remove-Item -Recurse -Force $AppDistPath -ErrorAction SilentlyContinue
    Push-Location (Join-Path $ProjectRoot "packaging")
    try {
        & $Python -m PyInstaller --noconfirm --clean --distpath $DistPath --workpath $BuildPath "offline_quiz.spec"
        if ($LASTEXITCODE -ne 0) { throw "Application packaging failed" }
    }
    finally {
        Pop-Location
    }

    $InnoCandidates = @(
        "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
        "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
        "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
    )
    $Inno = $InnoCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
    if ($Inno) {
        & $Inno (Join-Path $ProjectRoot "packaging\offline_quiz.iss")
        if ($LASTEXITCODE -ne 0) { throw "Installer generation failed" }
        Write-Host "Installer created in dist\installer"
    }
    else {
        Write-Warning "Inno Setup 6 was not found. The portable application was created in dist\KuishuQuiz. Install Inno Setup and rerun this script to create setup.exe."
    }
}

finally {
    Pop-Location
}
