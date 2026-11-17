$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$ExecutionRoot = $ProjectRoot
$MappedDrive = $null
$InstallerFileName = "KuishuQuiz-Win7-Setup-1.6.0-win7-rc2.exe"

function Get-PeMachine {
    param([Parameter(Mandatory = $true)][string]$Path)

    $Bytes = [System.IO.File]::ReadAllBytes($Path)
    if ($Bytes.Length -lt 64 -or $Bytes[0] -ne 0x4D -or $Bytes[1] -ne 0x5A) {
        throw "Not a valid PE file: $Path"
    }
    $PeOffset = [System.BitConverter]::ToInt32($Bytes, 0x3C)
    if ($PeOffset -lt 0 -or $PeOffset + 6 -gt $Bytes.Length) {
        throw "Invalid PE header offset: $Path"
    }
    if (
        $Bytes[$PeOffset] -ne 0x50 -or
        $Bytes[$PeOffset + 1] -ne 0x45 -or
        $Bytes[$PeOffset + 2] -ne 0x00 -or
        $Bytes[$PeOffset + 3] -ne 0x00
    ) {
        throw "Invalid PE signature: $Path"
    }
    return [System.BitConverter]::ToUInt16($Bytes, $PeOffset + 4)
}

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
$ReleaseInstallerPath = Join-Path $ExecutionRoot "KuishuQuiz-Win7\$InstallerFileName"
$LocalLibreOfficeRoot = Join-Path $ExecutionRoot "third_party\libreoffice"
$LibreOfficePath = Join-Path $LocalLibreOfficeRoot "App\libreoffice\program\soffice.exe"

Push-Location $ExecutionRoot
try {
    if (-not (Test-Path $LibreOfficePath)) {
        throw "LibreOffice offline converter is missing: $LibreOfficePath"
    }
    $env:QT_QPA_PLATFORM = "offscreen"
    $env:QT_QPA_PLATFORM_PLUGIN_PATH = Join-Path $ExecutionRoot ".venv\Lib\site-packages\PySide2\plugins\platforms"
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

    $RuntimeDirectory = Join-Path $PackagedLibreOffice "System64"
    $RequiredRuntimeFiles = @(
        "msvcp140.dll",
        "msvcp140_atomic_wait.dll",
        "vcruntime140.dll",
        "vcruntime140_1.dll"
    )
    foreach ($RuntimeFile in $RequiredRuntimeFiles) {
        $RuntimePath = Join-Path $RuntimeDirectory $RuntimeFile
        if (-not (Test-Path -LiteralPath $RuntimePath -PathType Leaf)) {
            throw "Required bundled x64 runtime is missing: $RuntimePath"
        }
        $Machine = Get-PeMachine -Path $RuntimePath
        if ($Machine -ne 0x8664) {
            throw ("Bundled runtime is not x64 (machine 0x{0:X4}): {1}" -f $Machine, $RuntimePath)
        }
    }

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
        New-Item -ItemType Directory -Path (Split-Path -Parent $ReleaseInstallerPath) -Force | Out-Null
        Copy-Item -LiteralPath $InstallerPath -Destination $ReleaseInstallerPath -Force
        Write-Host "Installer created: $RootInstallerPath"
        Write-Host "Offline delivery copy created: $ReleaseInstallerPath"
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
