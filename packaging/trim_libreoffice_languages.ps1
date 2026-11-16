param(
    [Parameter(Mandatory = $true)]
    [string]$LibreOfficeRoot
)

$ErrorActionPreference = "Stop"
$ResolvedRoot = (Resolve-Path -LiteralPath $LibreOfficeRoot).Path
$Soffice = Join-Path $ResolvedRoot "program\soffice.exe"

if ((Split-Path -Leaf $ResolvedRoot) -ne "libreoffice" -or -not (Test-Path -LiteralPath $Soffice -PathType Leaf)) {
    throw "Refusing to trim an invalid LibreOffice bundle: $ResolvedRoot"
}

$RootPrefix = $ResolvedRoot.TrimEnd("\") + "\"

function Assert-BundlePath([string]$Path) {
    $FullPath = [System.IO.Path]::GetFullPath($Path)
    if (-not $FullPath.StartsWith($RootPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to modify a path outside the LibreOffice bundle: $FullPath"
    }
}

function Remove-DirectoriesExcept([string]$Path, [string[]]$Keep) {
    if (-not (Test-Path -LiteralPath $Path -PathType Container)) { return }
    Assert-BundlePath $Path
    Get-ChildItem -LiteralPath $Path -Directory | Where-Object { $Keep -notcontains $_.Name } | ForEach-Object {
        Assert-BundlePath $_.FullName
        Remove-Item -LiteralPath $_.FullName -Recurse -Force
    }
}

function Remove-FilesExcept([string]$Path, [string[]]$Keep) {
    if (-not (Test-Path -LiteralPath $Path -PathType Container)) { return }
    Assert-BundlePath $Path
    Get-ChildItem -LiteralPath $Path -File | Where-Object { $Keep -notcontains $_.Name } | ForEach-Object {
        Assert-BundlePath $_.FullName
        Remove-Item -LiteralPath $_.FullName -Force
    }
}

function Remove-MatchingFilesExcept([string]$Path, [string]$Filter, [string[]]$Keep) {
    if (-not (Test-Path -LiteralPath $Path -PathType Container)) { return }
    Assert-BundlePath $Path
    Get-ChildItem -LiteralPath $Path -File -Filter $Filter | Where-Object { $Keep -notcontains $_.Name } | ForEach-Object {
        Assert-BundlePath $_.FullName
        Remove-Item -LiteralPath $_.FullName -Force
    }
}

Remove-DirectoriesExcept (Join-Path $ResolvedRoot "program\resource") @("common", "zh_CN")

$RegistryRoot = Join-Path $ResolvedRoot "share\registry"
Remove-MatchingFilesExcept $RegistryRoot "Langpack-*.xcd" @("Langpack-zh-CN.xcd")
Remove-MatchingFilesExcept $RegistryRoot "cjk_*.xcd" @("cjk_zh-CN.xcd")

$RegistryResources = Join-Path $ResolvedRoot "share\registry\res"
if (Test-Path -LiteralPath $RegistryResources -PathType Container) {
    Assert-BundlePath $RegistryResources
    Get-ChildItem -LiteralPath $RegistryResources -File | Where-Object { $_.Name -notlike "*zh-CN.xcd" } | ForEach-Object {
        Assert-BundlePath $_.FullName
        Remove-Item -LiteralPath $_.FullName -Force
    }
}

$Extensions = Join-Path $ResolvedRoot "share\extensions"
if (Test-Path -LiteralPath $Extensions -PathType Container) {
    Assert-BundlePath $Extensions
    Get-ChildItem -LiteralPath $Extensions -Force | ForEach-Object {
        Assert-BundlePath $_.FullName
        Remove-Item -LiteralPath $_.FullName -Recurse -Force
    }
}

Remove-FilesExcept (Join-Path $ResolvedRoot "share\autocorr") @("acor_zh-CN.dat")
Remove-DirectoriesExcept (Join-Path $ResolvedRoot "share\autotext") @("common", "zh-CN")
Remove-FilesExcept (Join-Path $ResolvedRoot "readmes") @("readme_zh-CN.txt")
Remove-FilesExcept (Join-Path $ResolvedRoot "share\fingerprint") @("zh-Hans.lm")
Remove-FilesExcept (Join-Path $ResolvedRoot "share\numbertext") @("Suzhou.sor", "zh.sor")
Remove-MatchingFilesExcept (Join-Path $ResolvedRoot "share\Scripts\python\LibreLogo") `
    "LibreLogo_*.properties" @("LibreLogo_zh_CN.properties")
Remove-MatchingFilesExcept (Join-Path $ResolvedRoot "share\basic\Depot") `
    "Lang_*.xba" @("Lang_zh.xba")

$Wordbook = Join-Path $ResolvedRoot "share\wordbook"
if (Test-Path -LiteralPath $Wordbook -PathType Container) {
    Assert-BundlePath $Wordbook
    Remove-Item -LiteralPath $Wordbook -Recurse -Force
}

$Help = Join-Path $ResolvedRoot "help"
if (Test-Path -LiteralPath $Help -PathType Container) {
    Assert-BundlePath $Help
    Remove-Item -LiteralPath $Help -Recurse -Force
}

Get-ChildItem -LiteralPath $ResolvedRoot -File -Filter "*.msi" | ForEach-Object {
    Assert-BundlePath $_.FullName
    Remove-Item -LiteralPath $_.FullName -Force
}

$UnexpectedLocaleFiles = @(
    Get-ChildItem -LiteralPath $RegistryRoot -File -Filter "Langpack-*.xcd" -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -ne "Langpack-zh-CN.xcd" }
    Get-ChildItem -LiteralPath $RegistryRoot -File -Filter "cjk_*.xcd" -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -ne "cjk_zh-CN.xcd" }
    Get-ChildItem -LiteralPath (Join-Path $ResolvedRoot "share\fingerprint") -File -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -ne "zh-Hans.lm" }
    Get-ChildItem -LiteralPath (Join-Path $ResolvedRoot "share\numbertext") -File -ErrorAction SilentlyContinue |
        Where-Object { @("Suzhou.sor", "zh.sor") -notcontains $_.Name }
    Get-ChildItem -LiteralPath (Join-Path $ResolvedRoot "share\Scripts\python\LibreLogo") `
        -File -Filter "LibreLogo_*.properties" -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -ne "LibreLogo_zh_CN.properties" }
    Get-ChildItem -LiteralPath (Join-Path $ResolvedRoot "share\basic\Depot") `
        -File -Filter "Lang_*.xba" -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -ne "Lang_zh.xba" }
)
if ($UnexpectedLocaleFiles.Count -gt 0) {
    $UnexpectedNames = ($UnexpectedLocaleFiles | ForEach-Object { $_.FullName }) -join "; "
    throw "Unexpected non-Simplified-Chinese resources remain in the packaged bundle: $UnexpectedNames"
}

Write-Host "LibreOffice packaging resources trimmed to Simplified Chinese."
