# Public Template Policy

This repository is intended to be safe to publish as a reusable Codex skills workbench.

## What Was Generalized

- Non-portable absolute paths
- Profile directories and account identifiers
- Non-public project folders
- Historical data file names
- Dataset-specific row counts or local output manifests
- Instructions that only apply to one environment

## What Remains

- Skill package structure
- Invocation names such as `$ppt-production-guide`
- General workflow guidance
- Placeholder paths such as `<project-root>`, `<input-file>`, and `<output-dir>`
- Local installation, export, sync, and validation scripts

## Before Publishing

Run the validation script:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\validate-repo.ps1
```

Optionally scan for non-portable path fragments:

```powershell
Get-ChildItem -Recurse -File |
  Where-Object { $_.FullName -notmatch '\\.git\\' -and $_.FullName -notmatch '\\_scratch\\' } |
  Select-String -Pattern '<local-path>|<account-id>|<secret>' -Encoding UTF8
```
