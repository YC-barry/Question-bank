$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$ExecutionRoot = $ProjectRoot
$MappedDrive = $null
$InstallerFileName = "KuishuQuiz-Win7-Setup-1.6.0-win7-rc1.exe"

if ($ProjectRoot -match '[^\x00-\x7F]') {
    $MappedDrive = @("W:", "V:", "U:", "T:") |
        Where-Object { -not (Test-Path "$_\") } |
        Select-Object -First 1
    if (-not $MappedDrive) {
        throw "An unused drive letter is required to build Qt 5 from a non-ASCII project path."
    }
    & subst.exe $MappedDrive $ProjectRoot
    if ($LASTEXITCODE -ne 0) { throw "Unable to create the temporary ASCII build path." }
    $ExecutionRoot = "$MappedDrive\"
}

$Python = Join-Path $ExecutionRoot ".venv\Scripts\python.exe"
$BuildPath = Join-Path $ExecutionRoot "build"
$DistPath = Join-Path $ExecutionRoot "dist"
$AppDistPath = Join-Path $DistPath "KuishuQuiz-Win7"
$InstallerPath = Join-Path $DistPath "installer\$InstallerFileName"
$RootInstallerPath = Join-Path $ExecutionRoot $InstallerFileName
$LocalLibreOfficeRoot = Join-Path $ExecutionRoot "third_party\libreoffice"
$LibreOfficePath = Join-Path $LocalLibreOfficeRoot "App\libreoffice\program\soffice.exe"

Push-Location $ExecutionRoot
try {
    if (-not (Test-Path $LibreOfficePath)) {
        throw "LibreOffice offline converter is missing: $LibreOfficePath"
    }
    $env:QT_QPA_PLATFORM = "offscreen"
    $TestTemp = Join-Path $env:TEMP "offlinequiz-win7-build-tests"
    & $Python -m pytest -p no:cacheprovider --basetemp=$TestTemp
    if ($LASTEXITCODE -ne 0) { throw "Automated tests failed" }

    Remove-Item -Recurse -Force $BuildPath -ErrorAction SilentlyContinue
    Remove-Item -Recurse -Force $AppDistPath -ErrorAction SilentlyContinue
    Push-Location (Join-Path $ExecutionRoot "packaging")
    try {
        & $Python -m PyInstaller --noconfirm --clean --distpath $DistPath --workpath $BuildPath "offline_quiz.spec"
        if ($LASTEXITCODE -ne 0) { throw "Application packaging failed" }
    }
    finally {
        Pop-Location
    }

    $PackagedThirdPartyPath = Join-Path $AppDistPath "_internal\third_party"
    New-Item -ItemType Directory -Path $PackagedThirdPartyPath -Force | Out-Null
    Copy-Item -LiteralPath $LocalLibreOfficeRoot `
        -Destination (Join-Path $PackagedThirdPartyPath "libreoffice") `
        -Recurse `
        -Force
    $PackagedLibreOffice = Join-Path $PackagedThirdPartyPath "libreoffice\App\libreoffice"
    & (Join-Path $ExecutionRoot "packaging\trim_libreoffice_languages.ps1") -LibreOfficeRoot $PackagedLibreOffice

    $InnoCandidates = @(
        "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
        "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
        "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
    )
    $Inno = $InnoCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
    if ($Inno) {
        & $Inno (Join-Path $ExecutionRoot "packaging\offline_quiz.iss")
        if ($LASTEXITCODE -ne 0) { throw "Installer generation failed" }
        if (-not (Test-Path $InstallerPath)) { throw "Installer output is missing: $InstallerPath" }
        Copy-Item -LiteralPath $InstallerPath -Destination $RootInstallerPath -Force
        Write-Host "Installer created: $RootInstallerPath"
    }
    else {
        throw "Inno Setup 6 is required to create the standalone installer."
    }
}

finally {
    Pop-Location
    if ($MappedDrive) {
        & subst.exe $MappedDrive /d
    }
}
