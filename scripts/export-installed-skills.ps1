param(
    [string]$CodexSkillsRoot = (Join-Path $env:USERPROFILE '.codex\skills'),
    [switch]$ForceExport
)

. "$PSScriptRoot\_common.ps1"

$repoRoot = Get-RepoRoot -ScriptRoot $PSScriptRoot
$manifest = Get-SkillManifest -RepoRoot $repoRoot

foreach ($item in $manifest) {
    $sourceDir = Join-Path $CodexSkillsRoot $item.skillDir
    $targetDir = Join-Path $repoRoot ("skills\" + $item.skillDir)

    if (!(Test-Path -LiteralPath $sourceDir)) {
        throw "Installed skill not found: $sourceDir"
    }

    if ((Test-Path -LiteralPath $targetDir) -and !$ForceExport) {
        Write-Host ("Skipped repository skill {0}. Add -ForceExport to overwrite files." -f $item.skillDir)
        continue
    }

    New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
    Get-ChildItem -LiteralPath $sourceDir -Force | Copy-Item -Destination $targetDir -Recurse -Force
    Write-Host ("Exported {0} -> {1}" -f $item.skillDir, $targetDir)
}
