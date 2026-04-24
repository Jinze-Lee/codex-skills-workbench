. "$PSScriptRoot\_common.ps1"

$repoRoot = Get-RepoRoot -ScriptRoot $PSScriptRoot
$manifest = Get-SkillManifest -RepoRoot $repoRoot

foreach ($item in $manifest) {
    $sourcePath = Join-Path $repoRoot ("source-notes\" + $item.sourceFile)
    $targetPath = Join-Path $repoRoot ("skills\" + $item.skillDir + "\references\source-note.md")

    if (!(Test-Path -LiteralPath $sourcePath)) {
        throw "Source note not found: $sourcePath"
    }

    $targetDir = Split-Path -Parent $targetPath
    New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
    Copy-Item -LiteralPath $sourcePath -Destination $targetPath -Force

    Write-Host ("Synced {0} -> {1}" -f $item.sourceFile, $item.skillDir)
}

