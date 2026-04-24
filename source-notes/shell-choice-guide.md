# Shell Choice Guide

## Purpose

Generic guidance for choosing between PowerShell, Git Bash, and other shells on Windows-oriented projects.

Use placeholders below and resolve real paths from the active project context.

## Inputs To Confirm

- Current workspace root: `<project-root>`
- Target shell: PowerShell, Git Bash, WSL, or another shell
- Command type: file operations, Git operations, package scripts, R/Python execution, or Windows COM automation
- Path constraints: spaces, non-ASCII characters, brackets, ampersands, or long paths

## Decision Rules

1. Use PowerShell for Windows-native automation, COM automation, registry access, `.ps1` scripts, and paths that need `-LiteralPath`.
2. Use Git Bash for POSIX-style scripts, common Unix tooling, and repositories whose scripts assume Bash syntax.
3. Prefer the shell already used by the project scripts unless there is a clear compatibility issue.
4. Do not hard-code absolute paths. Derive paths from the current workspace or ask the user for the missing root.
5. Quote paths defensively and use structured argument passing where possible.

## Generic Examples

PowerShell:

```powershell
Set-Location -LiteralPath '<project-root>'
& '<tool-executable>' '<script-path>' --input '<input-file>' --output '<output-dir>'
```

Git Bash:

```bash
cd '<project-root>'
./scripts/run.sh --input '<input-file>' --output '<output-dir>'
```

## Safety Notes

- Avoid command strings that concatenate untrusted paths.
- Use `-LiteralPath` for PowerShell file operations when paths may contain special characters.
- Before recursive delete or move operations, verify the resolved target is inside the intended workspace.

