function Get-RepoRoot {
    param(
        [string]$ScriptRoot
    )

    return (Resolve-Path -LiteralPath (Join-Path $ScriptRoot '..')).Path
}

function Get-SkillManifest {
    param(
        [string]$RepoRoot
    )

    $manifestPath = Join-Path $RepoRoot 'manifests\skills.json'
    if (!(Test-Path -LiteralPath $manifestPath)) {
        throw "Manifest not found: $manifestPath"
    }

    return Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
}

function Copy-DirectoryContents {
    param(
        [Parameter(Mandatory = $true)][string]$Source,
        [Parameter(Mandatory = $true)][string]$Destination
    )

    if (!(Test-Path -LiteralPath $Source)) {
        throw "Source directory not found: $Source"
    }

    New-Item -ItemType Directory -Path $Destination -Force | Out-Null
    Get-ChildItem -LiteralPath $Source -Force | Copy-Item -Destination $Destination -Recurse -Force
}
