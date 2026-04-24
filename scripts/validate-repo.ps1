. "$PSScriptRoot\_common.ps1"

$repoRoot = Get-RepoRoot -ScriptRoot $PSScriptRoot
$manifest = Get-SkillManifest -RepoRoot $repoRoot
$errors = New-Object System.Collections.Generic.List[string]

foreach ($item in $manifest) {
    $sourcePath = Join-Path $repoRoot ("source-notes\" + $item.sourceFile)
    $skillDir = Join-Path $repoRoot ("skills\" + $item.skillDir)
    $skillMd = Join-Path $skillDir 'SKILL.md'
    $sourceNote = Join-Path $skillDir 'references\source-note.md'

    if (!(Test-Path -LiteralPath $sourcePath)) {
        $errors.Add("Missing source note: $sourcePath")
    }
    if (!(Test-Path -LiteralPath $skillDir)) {
        $errors.Add("Missing skill directory: $skillDir")
    }
    if (!(Test-Path -LiteralPath $skillMd)) {
        $errors.Add("Missing SKILL.md: $skillMd")
    }
    if (!(Test-Path -LiteralPath $sourceNote)) {
        $errors.Add("Missing bundled source note: $sourceNote")
    }

    if (Test-Path -LiteralPath $skillMd) {
        $content = Get-Content -LiteralPath $skillMd -Raw
        if ($content -notmatch [regex]::Escape("name: " + $item.skillName)) {
            $errors.Add("SKILL.md name does not match manifest for: " + $item.skillDir)
        }
    }
}

if ($errors.Count -gt 0) {
    Write-Host "Validation failed:"
    foreach ($errorItem in $errors) {
        Write-Host ("- " + $errorItem)
    }
    exit 1
}

Write-Host ("Validation passed. {0} skills are ready." -f $manifest.Count)

