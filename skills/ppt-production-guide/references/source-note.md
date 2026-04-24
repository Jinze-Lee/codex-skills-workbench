# PPT Production Guide

## Purpose

Generic workflow for producing PowerPoint decks from analysis outputs, image folders, and structured notes.

Use placeholders below and resolve source folders from the active project context.

## Inputs To Confirm

- Output deck path: `<output-deck.pptx>`
- Image or table sources: `<figure-dir>`, `<table-dir>`
- Slide size: widescreen 16:9, standard 4:3, or custom dimensions
- Generation method: PowerPoint COM automation, `python-pptx`, R `officer`, or manual assembly
- Visibility requirement: background generation or visible desktop PowerPoint automation
- Interactive build preference: ask whether the user wants to see PowerPoint open and build slides step by step
- Image-wall layout: user-defined rows, columns, margins, gaps, repeated panels, titles, captions, and fit mode

## Workflow

1. Ask whether the user wants visible desktop PowerPoint generation before choosing the deck-building method.
2. Collect all source figures and tables into a manifest with titles, captions, and intended slide order.
3. Decide slide dimensions before placing images.
4. Use a consistent coordinate system and margins.
5. Insert each figure with aspect-ratio preservation unless cropping is explicitly desired.
6. Add concise captions or interpretation notes next to or below each figure.
7. For image walls, compute layout from user-provided rows, columns, spacing, and available slide area.
8. Save the deck and optionally export previews or PDFs for QA.
9. Verify slide count, image placement, and readability on a representative screen.

## Visible Build Prompt

When the task involves generating or updating a PowerPoint deck, ask a short yes/no question before implementation:

```text
Do you want PowerPoint to open visibly and show slides/images being inserted step by step?
```

If the user says yes, use PowerShell as the main controller and automate the installed Microsoft PowerPoint desktop app through COM. If the user says no, choose the simplest appropriate background method, such as `python-pptx`, R `officer`, or invisible COM automation.

## Visible PowerPoint COM Pattern

Use this pattern when the user wants to watch the build process:

```powershell
$powerPoint = New-Object -ComObject PowerPoint.Application
$powerPoint.Visible = $true
$presentation = $powerPoint.Presentations.Add()

# Add slides, text boxes, images, tables, and layout elements here.
# Keep short pauses optional so the user can see each insertion when requested.

$presentation.SaveAs('<output-deck.pptx>')
```

If the workflow needs a command-shell launcher, keep PowerShell as the automation script and use a minimal `.cmd` wrapper only to start it:

```cmd
@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0build_visible_ppt.ps1" %*
```

Do not use `cmd` as the PowerPoint automation layer. The actual PowerPoint interaction should happen through PowerShell and the PowerPoint COM object.

## Custom Image Wall

Do not assume a fixed `2 x 3` grid. Ask for or infer the layout from the task:

- Slide size: `<slide-width>` by `<slide-height>`
- Rows: `<rows>`
- Columns: `<columns>`
- Margin: `<margin>`
- Gap: `<gap>`
- Images per slide: `<rows> * <columns>`
- Repeat count: `<repeat-count>` when the user wants the same panel repeated
- Fit mode: contain, cover, crop-to-fill, or preserve original aspect ratio
- Caption mode: none, per-image label, short interpretation, or slide-level note

Common examples:

- `2 x 3` for six medium figures per slide
- `1 x 2` for two wide comparison figures
- `3 x 2` for six portrait figures
- `3 x 3` for compact overview pages
- `1 x 1` for full-slide figure review

When the user specifies layout details, follow them exactly unless they make the slide unreadable. If the layout is not specified, choose rows and columns based on image aspect ratios, expected reading order, and slide size.

## PowerPoint COM Note

After asking the visible-build question, use visible PowerPoint desktop automation and set `Application.Visible = $true` when the user chooses to watch the build process. Otherwise, choose the simplest project-appropriate deck generation method.

