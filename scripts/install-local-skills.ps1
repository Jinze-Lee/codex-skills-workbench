param(
    [string]$CodexSkillsRoot = (Join-Path $env:USERPROFILE '.codex\skills'),
    [switch]$ForceInstall
)

. "$PSScriptRoot\_common.ps1"

$repoRoot = Get-RepoRoot -ScriptRoot $PSScriptRoot
$manifest = Get-SkillManifest -RepoRoot $repoRoot

New-Item -ItemType Directory -Path $CodexSkillsRoot -Force | Out-Null

foreach ($item in $manifest) {
    $sourceDir = Join-Path $repoRoot ("skills\" + $item.skillDir)
    $targetDir = Join-Path $CodexSkillsRoot $item.skillDir

    if (!(Test-Path -LiteralPath $sourceDir)) {
        throw "Skill directory not found: $sourceDir"
    }

    if ((Test-Path -LiteralPath $targetDir) -and !$ForceInstall) {
        Write-Host ("Skipped existing skill {0}. Add -ForceInstall to overwrite files." -f $item.skillDir)
        continue
    }

    New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
    Get-ChildItem -LiteralPath $sourceDir -Force | Copy-Item -Destination $targetDir -Recurse -Force
    Write-Host ("Installed {0} -> {1}" -f $item.skillDir, $targetDir)
}
