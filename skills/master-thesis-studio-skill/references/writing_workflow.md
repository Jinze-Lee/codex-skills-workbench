# Writing Workflow

Use this workflow when the user asks to create, continue, revise, or export a master's thesis. This file is the main writing prompt for the Skill. Scripts handle Word/XML execution; this workflow handles dialogue, academic planning, and Markdown drafting.

## Core Principle

先问清楚，再写。先形成项目事实和资产清单，再进入提纲和章节草稿。所有确认过的信息都要落到 Markdown 或 `project_state.json`，不要只停留在对话里。

## Intake Questions

Start every new project by collecting these facts:

- 论文题目：是否已经确定；是否需要辅助拟题。
- 学科方向：专业、研究领域、应用场景。
- 研究对象：数据、系统、算法、实验对象或工程对象。
- 核心方法：已有方法、拟使用模型、创新模块、技术路线。
- 当前阶段：完全未开始、已有想法、已有部分章节、已有完整初稿、只需格式化输出。
- 期望模式：快速完整初稿、边确认边写、续写已有内容、根据代码/数据转写、只做 Word 写回。
- 已有资产：Word、Markdown、PDF、笔记、参考文献、代码、数据、图片、表格、公式、实验记录。
- 若已有 Word：确认它是格式模板、已有论文内容，还是二者兼有；询问是否需要反解析章节、图、表、公式。
- 若用户选择反解析：先问反解析后想做什么，是资产盘点、继续写作、修订润色、补缺失章节、重新导出 Word，还是 round-trip 校验。
- 缺失资产：还需要哪些实验、图表、公式、文献或章节说明。
- 真实性边界：是否允许模拟数据、示例图表、示例实验结果；不允许时必须只基于用户资产写作。
- 模板来源：默认使用 Skill 附带的东南大学风格 Word `.docx` 模板 `examples/Template.docx`，也可使用用户上传或指定的 Word `.docx/.dotx` 模板。

## Writing Modes

### Mode A: 从零生成初稿

Use when the user only has a title, direction, or rough idea. Confirm the topic, method, innovation point, chapter structure, and whether example experiments are allowed. Then draft a complete but clearly marked initial version.

### Mode B: 边做边写

Use when the user is still doing experiments, writing code, collecting data, or revising ideas. Create chapter plans and asset TODOs first. Draft stable sections such as background and related work, while marking method, experiment, and result sections as待补.

### Mode C: 续写已有论文

Use when the user has existing Word, Markdown, or partial chapters. Ask whether to reverse parse the Word first. If yes, parse the existing content, preserve usable parts, identify gaps, then continue chapter by chapter. Do not rewrite everything unless the user asks.

### Mode D: 资产转写论文

Use when the user has code, data, logs, tables, or figures. First explain what the asset appears to prove, then convert it into method description, experiment setup, result analysis, or innovation discussion. Do not invent metrics not present in the asset.

### Mode E: 格式整理与 Word 输出

Use when content is already mostly finished. Focus on Markdown cleanup, placeholder normalization, references, figure/table/formula consistency, and safe Word generation.

### Mode F: 已有 Word 资产盘点

Use when the user wants to understand what an existing Word contains before deciding what to do. Run reverse parsing, then summarize reusable chapters, usable figures, usable tables, formulas, references, and gaps. Stop for user direction before rewriting or exporting.

### Mode G: Round-trip 校验

Use when the user wants to verify the Word/XML pipeline or a script change. Reverse parse the source Word, write Markdown back to XML, build a new DOCX, embed extracted figures, and compare chapter titles, tables, drawings, media files, figure captions, table captions, and formulas.

## Outline Framework

The default master's thesis structure is:

1. 第1章 绪论：研究背景、意义、国内外研究现状、研究内容、创新点、论文结构。
2. 第2章 相关理论与研究现状：核心概念、理论基础、主流方法、关键技术、评价指标。
3. 第3章 研究方法与系统/模型设计：总体框架、关键模块、算法流程、公式推导、实现细节。
4. 第4章 实验设计与结果分析：数据、环境、指标、对比实验、消融实验、可视化、结果讨论。
5. 第5章 总结与展望：工作总结、不足、未来方向。

Only change this framework after confirming with the user.

## Chapter Planning

Before drafting a chapter, create or update `03_chapters/chXX_plan.md` with:

- 本章目标：这一章在论文中解决什么问题。
- 二级/三级标题：标题必须先确认。
- 本章输入资产：参考文献、代码、数据、图、表、公式、已有文字。
- 本章待补资产：缺失材料和需要用户确认的问题。
- 写作依据：哪些内容来自用户材料，哪些来自参考文献，哪些是示例或推断。
- 输出要求：本章预计字数、图表、公式、引用数量和写作重点。

## Asset Discipline

- 参考文献放在 `08_refs/`，第一章和第二章优先依据这些文献写作。
- 代码放在 `06_code/`，用于转写方法、实现细节、实验流程和创新点。
- 数据放在 `07_data/`，用于转写数据集、实验设置、指标和结果分析。
- 图片放在 `04_figures/`，图题和正文引用用占位符管理。
- 表格放在 `05_tables/`，表题和正文引用用占位符管理。
- 反解析得到的图、表必须查看 manifest 中的 `usable` 状态。只有 `usable=true` 的资源可以作为真实图表依据。
- 反解析得到的公式应保留为 `[[EQ:真实公式]]` 或 `[[SYM:真实符号]]`；如果只得到 `[[EQ:公式]]`，说明需要重新解析或人工补公式内容。
- 所有资产要在对应 manifest 中记录状态：已有、待补、已采用、需确认。

## Terminology Rules

- 严禁创造学术领域不存在的词汇或把普通描述包装成“公认术语”。
- 术语来源只能是：用户提供材料、参考文献、学科通用表达、用户明确命名的本文方法。
- 如果需要给创新模块命名，必须写成“本文设计的……”或“本文称其为……”，不要暗示该名称已经是领域通用概念。
- 对不确定术语使用保守表达，例如“可称为”“本文将其定义为”“在本文实验语境下”。
- 专业名词前后保持一致；同一概念不要反复换名字。

## Academic Style

- 使用硕士论文中文学术语体，客观、准确、克制。
- 避免口语化表达、宣传式表达、过度绝对化表达。
- 结论必须有依据。没有实验或文献支撑时，使用“可能”“有助于”“在一定程度上”等审慎表述。
- 长短句交替：长句用于交代背景、机制和因果关系；短句用于总结发现、承接段落和强调结论。
- 每段要有明确中心句，避免堆砌概念。
- 第一章重视问题提出和研究意义；第二章重视已有方法和本文工作的位置；第三章重视方法逻辑；第四章重视实验依据；第五章重视总结和边界。

## Reference-Driven Drafting

- 写第一章和第二章前，优先读取 `08_refs/` 中的参考文献清单、metadata、用户笔记或检索记录。
- 如果用户未提供参考文献，不要编造真实文献条目。可以生成 `[[REF:KEYWORD_PLACEHOLDER: 关键词]]`，并标记需要补文献。
- 文献综述要围绕“问题-方法-不足-本文切入点”展开，不要只罗列作者和年份。
- 正文引用使用 `[[REF:n]]`，不要手写 `[1]`。

## Drafting Rules

- Output only the current section's prose unless the user asks for headings.
- Do not invent lower-level headings inside a confirmed section.
- If a Markdown draft includes `# 第X章 标题`, treat it as file navigation only. The XML writer must not write that line into the Word body.
- Do not rely on manual numbering in headings. Writeback strips prefixes such as `第5章`, `第五章`, `1.1`, and `2.3.1` unless `keepHeadingNumbers` is explicitly enabled.
- Preserve all placeholders exactly.
- Do not hard-code figure/table/formula/reference numbers in prose.
- Use `[[REF_FIG:...]]` and `[[REF_TBL:...]]` for figure/table references.
- Use `[[FIG:...]]`, `[[TBL:...]]`, `[[EQ:...]]`, `[[SYM:...]]`, and `[[REF:n]]` for structured academic elements.
- Avoid spaces between Chinese text and adjacent English terms or numbers. Keep spaces inside English phrases, for example `Mamba Context Block`.

## Existing Word Reverse Parse

Reverse parsing is optional. Use it only when the user wants to reuse or inspect existing Word content, not merely because a `.docx` path exists.

Recommended dialogue after reverse parsing:

- “我已经把 Word 解析成章节、图、表、公式和资源清单。你想先查看资产，还是继续写作/润色/补章节/重新导出 Word？”
- “哪些内容必须保留，哪些内容可以重写？”
- “是否需要执行 round-trip 校验，确认解析出来的内容能重新生成 Word？”

Expected outputs:

- `03_chapters/chXX_draft.md`: chapter text with `[[FIG:...]]`, `[[TBL:...]]`, `[[EQ:...]]`, and `[[SYM:...]]`.
- `04_figures/`: extracted real embedded images, plus `figures_manifest.md`.
- `05_tables/`: extracted real Word tables as `.md` and `.csv`, plus `tables_manifest.md`.
- `09_state/reverse_parse_assets.json`: structured asset mapping and usability flags.
- `00_project/reverse_parse_report.md`: summary of the parse.

After reverse parsing, choose one of the normal modes rather than following a fixed path:

- asset review only;
- continue or revise existing chapters;
- rewrite selected sections;
- supplement missing figures, tables, formulas, references, code, or data;
- export a new Word;
- run round-trip validation.

## Markdown Files

- `00_project/project_manifest.md`: project facts, user status, writing mode, assets, and assumptions.
- `00_project/thesis_master_index.md`: visible outline and chapter status.
- `00_project/writing_progress.md`: chapter progress.
- `00_project/decisions_log.md`: decisions, user confirmations, and assumptions.
- `03_chapters/chXX_plan.md`: chapter plan.
- `03_chapters/chXX_draft.md`: confirmed draft content.
