. "$PSScriptRoot\_common.ps1"

$repoRoot = Get-RepoRoot -ScriptRoot $PSScriptRoot
$manifest = Get-SkillManifest -RepoRoot $repoRoot

$manifest | Select-Object `
    @{Name='Category'; Expression={$_.category}}, `
    @{Name='SourceFile'; Expression={$_.sourceFile}}, `
    @{Name='DisplayName'; Expression={$_.displayName}}, `
    @{Name='CodexInvocation'; Expression={'$' + $_.skillName}}, `
    @{Name='SkillDir'; Expression={$_.skillDir}}, `
    @{Name='UseWhen'; Expression={$_.useWhen}} |
    Format-Table -AutoSize
