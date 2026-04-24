---
name: ppt-production-guide
description: Follow the bundled PowerPoint production workflow. Use this skill only when the user explicitly invokes `$ppt-production-guide`. Ask whether the user wants visible PowerPoint desktop COM generation before building a deck. Do not auto-select this skill for general PowerPoint, slide, or presentation tasks.
---

# PPT Production Guide

## Overview

Use [references/source-note.md](references/source-note.md) as the source of truth for this skill.

Only use this skill when the user explicitly names `$ppt-production-guide`.

Do not use this skill based on topic similarity alone.

## Workflow

1. Read [references/source-note.md](references/source-note.md) first.
2. Ask whether the user wants visible PowerPoint desktop generation when the task involves creating or updating a deck.
3. If visible generation is requested, use PowerShell as the controller and automate the installed PowerPoint desktop app through COM.
4. Follow the note's layout rules, dimension settings, custom image-wall rules, and production sequence closely.
5. Replace stale image lists, paths, and filenames with current project data instead of copying historical values blindly.
6. Preserve the original PPT construction logic while adapting to the current deliverable.
7. If the note conflicts with the current user request, follow the current request and explain the adjustment.

## Source

- Bundled original note: `references/source-note.md`
- Installed skill name: `$ppt-production-guide`

