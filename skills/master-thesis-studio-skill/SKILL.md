---
name: master-thesis-studio-skill
描述: "仅当用户明确写出 `$master-thesis-studio-skill`，或明确说明要使用 master-thesis-studio-skill / Master Thesis Studio 这个 Skill 时使用。不要因用户只是提到硕士论文、东南大学、Word 模板、DOCX 生成或论文写作而自动使用。"
description: Use this skill only when the user explicitly invokes `$master-thesis-studio-skill` or explicitly asks to use the master-thesis-studio-skill / Master Thesis Studio skill. Do not auto-select this skill for general thesis writing, Southeast University formatting, Word templates, DOCX generation, or academic drafting requests.
---

## UTF-8 Reading Guard

Most instructions in this skill are Chinese and all Markdown/JSON files are UTF-8. If Chinese text appears garbled, do not edit or reason from the garbled output. Re-read files with an explicit UTF-8 command:

```bash
python -c "from pathlib import Path; import sys; sys.stdout.reconfigure(encoding='utf-8'); print(Path('SKILL.md').read_text(encoding='utf-8'))"
```

For short targeted reads, prefer Python over PowerShell `Get-Content`:

```bash
python -c "from pathlib import Path; p=Path('references/writing_workflow.md'); print(p.read_text(encoding='utf-8'))"
```

Load only the needed reference file. Do not bulk-read every Markdown file unless the task is a full Skill audit.

## Activation Guard

This skill is opt-in only.

- Use this skill only if the current user message explicitly includes `$master-thesis-studio-skill`, or explicitly says to use the master-thesis-studio-skill / Master Thesis Studio skill.
- Do not use this skill merely because the user mentions a master's thesis, Southeast University, Word templates, `.docx`, academic writing, formatting, or document generation.
- If the user discusses thesis/Word work without explicitly opting in, answer normally or ask whether they want to use this skill; do not silently activate this workflow.


# Master Thesis Studio

这是一个面向中文硕士论文写作与 Word 自动生成的显式调用 Skill。它把论文写作流程拆成两层：

1. **写作组织层**：问诊、确认题目、大纲、章节计划、资产清单、写作边界和中文学术表达。
2. **Word/XML 执行层**：用内置脚本把 Markdown 写入 Flat OPC XML，再生成新的 DOCX。

除非用户明确要求快速演示，否则必须先确认项目事实和写作边界，再写正文或生成 Word。

## 总原则

- 所有新生成的论文标题、章节标题、正文、图题、表题、摘要、说明文字默认使用中文。英文只保留在模型名、算法名、指标名、数据集名、代码路径、文件名和必要术语中。
- 不编造真实文献、实验结果、样本量、指标或数据来源。没有依据时写“待补充”“待确认”或使用占位符。
- 不覆盖原始 Word 模板。原始模板固定保存在 `01_template/original_template.docx`。
- 模板来源可以是内置示例模板，也可以是用户上传或指定的 Word 模板。内置模板为 `examples/Template.docx`；用户模板支持 `.docx` 和 `.dotx`。
- 初始化时如果用户未指定模板，脚本默认使用 `examples/Template.docx`；如果用户提供模板路径，必须把该路径传给 `--template`。
- 新 DOCX 只写入 `10_output/`。XML 中间态只写入 `09_state/`。
- 创建新论文项目时，必须先新建一个独立项目文件夹，并把该文件夹作为论文项目根目录；不要直接在 Skill 根目录、工作区根目录或桌面散落运行初始化。
- 初始化和后续生成命令应在该论文项目文件夹内运行，项目参数使用 `.`；调用脚本时使用 Skill 中 `scripts/` 的绝对路径，或明确从 Skill 根目录传入项目绝对路径。
- 用户提供已有 Word 时，先确认是否需要反解析。反解析是可选入口，不是必经流程；如果用户只想把该 Word 作为格式模板，可以只初始化模板，不抽取正文内容。
- 写回 Word 前必须检查章节 Markdown、占位符、参考文献、图表和状态文件是否一致。
- 修改占位符、XML 写回、参考文献或章节 Markdown 规则前，先阅读对应 `references/` 文件。

## 第一次响应

第一次使用本 Skill 时，不要直接写论文。先用简短问题确认：

- 论文题目是否已确定，是否需要辅助拟题。
- 学科方向、研究对象、核心方法、创新点是否已确定。
- 当前阶段：未开始、已有想法、已有部分章节、已有完整初稿、只需格式化输出。
- 用户希望的模式：快速初稿、边确认边写、续写已有内容、根据代码/数据转写、只做 Word 写回。
- 已有资产：Word、Markdown、PDF、笔记、参考文献、代码、数据、图片、表格、公式、实验记录。
- 如果已有 Word：它是“格式模板”“已有论文内容”还是“两者都是”；是否希望反解析章节、图、表、公式到项目目录。
- 如果执行反解析：反解析后想做什么，例如只盘点资产、继续写作、修订润色、补缺失章节、重新导出 Word，或做 round-trip 校验。
- 是否允许模拟数据、示例图表或示例实验结果。不允许时只能基于用户材料写作。
- 使用哪个模板：内置东南大学风格示例 `examples/Template.docx`，还是用户上传/指定的 Word `.docx` 或 `.dotx` 模板。

确认结果必须同步写入：

- `00_project/project_manifest.md`
- `00_project/thesis_master_index.md`
- `00_project/decisions_log.md`
- `09_state/project_state.json`

## 阶段执行表

| 阶段 | 先阅读什么 | 更新或生成什么 | 执行什么脚本 |
| --- | --- | --- | --- |
| 0. 判断项目状态 | 项目根目录、`00_project/`、`09_state/project_state.json`、`03_chapters/` | 判断是新项目、续写项目还是只需导出；如果是新项目，先创建独立项目文件夹并进入该文件夹 | 无 |
| 1. 初始化工作区 | 用户给定模板路径；未给定时默认模板 `examples/Template.docx` | 在当前论文项目文件夹内生成 `00_project/`、`01_template/`、`03_chapters/`、`04_figures/`、`05_tables/`、`06_code/`、`07_data/`、`08_refs/`、`09_state/`、`10_output/` | 在项目文件夹内运行：`python <skill_dir>/scripts/init_thesis_workspace.py .`，或使用用户模板：`python <skill_dir>/scripts/init_thesis_workspace.py . --template <word_template.docx>` |
| 1A. 可选反解析已有 Word | 用户确认该 Word 是已有论文内容且希望抽取内容 | `03_chapters/` 章节草稿、`04_figures/` 真实图片、`05_tables/` 表格 `.md/.csv`、`09_state/reverse_parse_assets.json`、反解析报告 | `python <skill_dir>/scripts/reverse_parse_docx.py <project_dir> --docx <user.docx>` |
| 2. 转换模板 | `01_template/original_template.docx` | `01_template/template.flat.xml` | `python scripts/flat_opc_converter.py toxml <input.docx> <output.xml>` |
| 3. 解析模板结构 | `references/xml_mapping_spec.md`、`01_template/template.flat.xml` | `09_state/parsed_structure.json` | `python scripts/parse_template_xml.py <template.flat.xml> <parsed_structure.json>` |
| 4. 生成项目控制文件 | `references/writing_workflow.md`、`assets/project_state.schema.json` | `00_project/*.md`、初始 `03_chapters/chXX_plan.md`、`03_chapters/chXX_draft.md`、`09_state/project_state.json` | `python scripts/generate_planning_files.py <project_dir>` |
| 5. 启动问诊和资产盘点 | `references/writing_workflow.md`、已有 `00_project/*.md`、各资产 manifest | 更新 project manifest、master index、decisions log、figures/tables/code/data manifest | 通常无脚本，必要时手动编辑 Markdown |
| 6. 章节计划 | `references/writing_workflow.md` 的章节计划规则、`00_project/thesis_master_index.md`、相关资产 | `03_chapters/chXX_plan.md` | 通常无脚本 |
| 7. 章节正文 Markdown | `03_chapters/chXX_plan.md`、`references/writing_workflow.md`、`references/placeholders.md`、相关 `08_refs/`、`06_code/`、`07_data/`、`04_figures/`、`05_tables/` | `03_chapters/chXX_draft.md` 或兼容命名的 `ch*.md` | 通常无脚本 |
| 8. 参考文献处理 | `references/reference_rules.md`、`08_refs/` | 规范化引用占位符和参考文献对象 | `python scripts/reference_tools.py format <refs.json> --style "GB/T 7714"` |
| 9. Markdown 写入 XML | `references/placeholders.md`、`references/xml_mapping_spec.md`、`03_chapters/`、`09_state/project_state.json` | `09_state/current_working.xml`、XML 快照、`09_state/current_content_manifest.json` | `python scripts/apply_markdown_to_xml.py <project_dir> --out 09_state/current_working.xml` |
| 10. 生成 Word | `09_state/current_working.xml` | `10_output/thesis_draft_v1.docx` 或用户指定文件名 | `python scripts/build_new_docx.py <project_dir> --name thesis_draft_v1.docx` |
| 11. 校验输出 | `references/xml_mapping_spec.md`、`09_state/current_working.xml`、`10_output/` | 确认 XML 是 Flat OPC、章节数正确、DOCX 可重建 | `python scripts/validate_xml_docx.py <project_dir>` |

## 目录职责

- `00_project/project_manifest.md`：项目事实、写作模式、用户状态、资产、缺失项和假设。
- `00_project/thesis_master_index.md`：总大纲、章节状态、术语表、开放问题。
- `00_project/decisions_log.md`：用户确认、重要假设、写作边界和变更记录。
- `03_chapters/`：章节计划和章节正文 Markdown。
- `04_figures/figures_manifest.md`：图片文件、图题、来源、章节映射、状态。
- `05_tables/tables_manifest.md`：表格/数据来源、表题、章节映射、状态。
- `06_code/code_manifest.md`：代码资产、可支撑的方法描述、实现细节和实验流程。
- `07_data/data_manifest.md`：数据集、实验结果、指标、日志和可支撑结论。
- `08_refs/`：参考文献、文献笔记、检索记录和引用元数据。
- `09_state/project_state.json`：脚本写回使用的结构化项目状态。
- `09_state/current_working.xml`：当前可生成 DOCX 的 Flat OPC XML。
- `09_state/reverse_parse_assets.json`：可选反解析生成的真实图、表资源清单和可用性标记。
- `10_output/`：最终生成的 DOCX。

## 何时阅读 References

- 需要问诊、选择写作模式、制定大纲、规划章节或写中文学术正文时，先读 `references/writing_workflow.md`。
- 需要使用或修改 `[[FIG:...]]`、`[[TBL:...]]`、`[[EQ:...]]`、`[[SYM:...]]`、`[[REF:...]]`、`[[REF_FIG:...]]`、`[[REF_TBL:...]]` 时，先读 `references/placeholders.md`。
- 需要处理参考文献格式、引用占位符、GB/T 7714 或 Word 交叉引用时，先读 `references/reference_rules.md`。
- 需要解析模板、反解析已有 Word、修改 XML 写回逻辑、处理标题样式、页眉页脚、分节符、图、表、公式或 DOCX 生成时，先读 `references/xml_mapping_spec.md`。
- 需要直接编辑 `09_state/project_state.json` 时，先读 `assets/project_state.schema.json`。

## 章节 Markdown 规范

### 文件命名

推荐命名：

- `03_chapters/ch01_plan.md`
- `03_chapters/ch01_draft.md`
- `03_chapters/ch02_plan.md`
- `03_chapters/ch02_draft.md`

兼容命名：

- `03_chapters/ch1_intro.md`
- `03_chapters/ch2_literature.md`
- `03_chapters/ch3_method.md`
- `03_chapters/ch4_experiments.md`
- `03_chapters/ch5_conclusion.md`

`scripts/apply_markdown_to_xml.py` 的读取规则：

1. 优先读取 `03_chapters/ch*_draft.md`。
2. 如果没有 `_draft.md`，读取 `03_chapters/ch*.md`，但排除 `*_plan.md`。
3. 按文件名中的章节数字排序。
4. 根据 Markdown 的 `#`、`##`、`###` 重建一级、二级、三级标题结构。
5. 顶层 `# 第X章 标题` 只作为文件导航，写入 Word 时不会作为正文段落重复写入。

### 章节正文结构

新生成章节正文时使用中文标题，结构如下：

```markdown
# 第1章 绪论
<!-- chapter_id: ch_1 -->

## 1.1 研究背景

这里写中文正文。正文应说明问题背景、研究意义和已有材料依据。

## 1.2 国内外研究现状

这里写中文正文。需要引用但暂无文献时，使用 [[REF:KEYWORD_PLACEHOLDER: 关键词]]。

### 1.2.1 某类方法

这里写三级小节正文。

## 1.3 本文主要工作

- 使用中文列出本文工作。
- 不写没有依据的实验指标。
```

章节 Markdown 的规则：

- 标题和正文默认中文。不要新生成 `Chapter 1 Introduction` 这类英文标题，除非用户明确要求英文论文。
- 二级标题使用 `##`，三级标题使用 `###`。不要在正文段落里伪造标题。
- 不要手写最终 Word 中的图号、表号、公式号或参考文献编号。
- 可以在 Markdown 中写 `第1章`、`1.1` 方便阅读；写入 Word 时默认去掉手动编号，避免模板自动编号重复。
- 已确认正文写入 `chXX_draft.md`。章节目标、素材、待补问题写入 `chXX_plan.md`，不要混在正文草稿里。
- 如果用户已有英文标题或英文草稿，先确认是翻译成中文还是保留原文。

## 占位符规范

写正文时使用这些占位符，不要硬编码编号：

- `[[FIG:图的稳定描述]]`：生成图片占位和图题。
- `[[TBL:表的稳定描述]]`：生成表题和真实 Word 表格。
- `[[EQ:公式]]`：生成显示公式和章内编号。
- `[[SYM:公式或符号]]`：生成行内数学符号。
- `[[REF:n]]`：生成参考文献交叉引用。
- `[[REF:KEYWORD_PLACEHOLDER: 关键词]]`：文献未补齐时的临时引用。
- `[[REF_FIG:图的稳定描述]]`：正文中引用图。
- `[[REF_TBL:表的稳定描述]]`：正文中引用表。
- `[[CODE:路径或说明]]`：标记代码资产需求。
- `[[DATA:路径或说明]]`：标记数据资产需求。

`[[TABLE:...]]`、`[[FIGURE:...]]`、`[[EQUATION:...]]` 可以被脚本兼容为 `[[TBL:...]]`、`[[FIG:...]]`、`[[EQ:...]]`，但新写内容必须使用标准形式。

## 写作模式

- **从零生成初稿**：先读 `references/writing_workflow.md`，确认题目、方法、创新点、真实性边界，再生成大纲、计划和中文初稿。
- **边做边写**：先写章节计划和资产 TODO，稳定章节可先写，实验结果、指标和图表缺失处标记待补。
- **续写已有论文**：先确认是否反解析已有 Word。若用户同意，运行反解析并让用户查看 `03_chapters/`、`04_figures/`、`05_tables/` 后，再决定续写、润色、补章节或导出。
- **资产转写论文**：先读 `06_code/`、`07_data/`、`04_figures/`、`05_tables/` 和 manifest，确认资产含义，再转写为方法、实验或结果分析。
- **格式整理与 Word 输出**：先清洗 Markdown、规范占位符和引用，再执行 XML 写回、DOCX 生成和校验。
- **已有 Word 资产盘点**：只抽取章节、图、表、公式和 manifest，不直接重写正文。适合用户想先了解已有论文可复用内容的情况。
- **Round-trip 校验**：反解析后再写回 Word，对比章节、图、表、公式和资源数量。适合验证模板兼容性或脚本改动。

## 模板选择

- 内置模板是 `examples/Template.docx`，文件格式是 Word `.docx`。它来自东南大学风格论文模板的改造版本。
- 用户可以改用自己的 Word 模板。支持 `.docx` 和 `.dotx`；不传 `--template` 时自动使用内置 `examples/Template.docx`。
- 如果用户上传了模板，先取得本机可访问的绝对路径，再运行初始化命令：`python <skill_dir>/scripts/init_thesis_workspace.py . --template <user_template.docx>`。
- 用户提供已有 Word 时，先区分它是“格式模板”还是“已有论文内容”。只作为格式模板时，用 `--template` 初始化；要抽取正文/图表/公式时，再使用 `reverse_parse_docx.py`。
- 初始化脚本会把选定模板复制到项目内的 `01_template/original_template.docx`，并把来源记录到 `09_state/template_source.json` 和 `09_state/project_state.json`。

## 写作要求

- 使用中文硕士论文语体：客观、克制、准确、逻辑清楚。
- 第一章和第二章优先依据 `08_refs/`、用户笔记和已有论文内容。
- 第三章优先依据代码、系统设计、算法流程、公式和用户确认的方法描述。
- 第四章优先依据真实数据、实验日志、指标表和图表。没有数据时不得编造结论。
- 第五章总结要与前文工作一致，不扩大贡献，不新增未出现的方法或实验。
- 术语必须一致。用户自定义模块名要写成“本文提出/设计/称为”，不要伪装成领域通用术语。
- 不确定内容要标记“待确认”或“待补充”，并记录到 `00_project/project_manifest.md` 或对应章节计划。

## 脚本命令

推荐流程：先创建一个新的论文项目文件夹，进入该文件夹，再运行初始化和后续命令。这样 `00_project/`、`03_chapters/`、`10_output/` 等目录都会生成在这个项目文件夹里。

脚本需要 Python 包 `lxml`。如果当前 `python` 缺少 `lxml`，先改用已经安装 `lxml` 的 Python 解释器，或在目标解释器中安装 `lxml` 后再运行。

```bash
mkdir <project_dir>
cd <project_dir>
python <skill_dir>/scripts/init_thesis_workspace.py .
```

默认命令会使用内置 `examples/Template.docx`。如果用户选择自己的 Word 模板，传入用户模板路径：

```bash
python <skill_dir>/scripts/init_thesis_workspace.py . --template <user_template.docx>
```

如果用户提供的是已有论文内容，并且明确希望解析它，可以直接运行可选反解析入口：

```bash
python <skill_dir>/scripts/reverse_parse_docx.py <project_dir> --docx <user_thesis.docx>
```

反解析完成后先让用户选择下一步：只查看资产、继续写作、修订润色、补缺失章节、重新导出 Word，或执行 round-trip 校验。不要默认立刻重写全文。

在项目文件夹内运行时，项目参数使用 `.`，脚本路径使用 Skill 的绝对路径：

```bash
python <skill_dir>/scripts/flat_opc_converter.py toxml 01_template/original_template.docx 01_template/template.flat.xml
python <skill_dir>/scripts/parse_template_xml.py 01_template/template.flat.xml 09_state/parsed_structure.json
python <skill_dir>/scripts/generate_planning_files.py .
python <skill_dir>/scripts/apply_markdown_to_xml.py . --out 09_state/current_working.xml
python <skill_dir>/scripts/build_new_docx.py . --name thesis_draft_v1.docx
python <skill_dir>/scripts/validate_xml_docx.py .
python <skill_dir>/scripts/reference_tools.py format <refs.json> --style "GB/T 7714"
```

也可以在 Skill 根目录运行脚本，但必须把 `<project_dir>` 写成论文项目文件夹的绝对路径，不要省略项目路径。

可选命令：

```bash
python scripts/embed_figures_docx.py <input.docx> <output.docx> <figure1.svg> [figure2.svg ...]
python scripts/reverse_parse_docx.py <project_dir> --docx <user_thesis.docx>
```

不要直接运行 `scripts/word_xml_core.py`，它是公共脚本导入的内部 Word/XML 引擎。

## Word 生成前检查

运行 `apply_markdown_to_xml.py` 前检查：

- `03_chapters/` 至少有可读取的章节正文 Markdown。
- `chXX_plan.md` 和 `chXX_draft.md` 责任分明，计划不混入最终正文。
- 占位符使用标准形式，必要时已阅读 `references/placeholders.md`。
- 参考文献未补齐处使用 `[[REF:KEYWORD_PLACEHOLDER: 关键词]]`。
- 图表、代码、数据资产已在对应 manifest 中记录。
- 如果项目来自反解析，检查 `09_state/reverse_parse_assets.json` 中图、表是否为 `usable=true`；只把可用资源当作真实资产。
- `09_state/project_state.json` 结构合法，必要时参考 `assets/project_state.schema.json`。

运行 `apply_markdown_to_xml.py` 后检查：

- `09_state/current_content_manifest.json` 中的 `draft_files` 不是空数组。
- `09_state/current_working.xml` 存在，且是 Flat OPC XML。
- `python scripts/validate_xml_docx.py <project_dir>` 输出的章节数符合预期。

运行 `build_new_docx.py` 后检查：

- 新文件位于 `10_output/`。
- 文件名不是 `original_template.docx`。
- 校验通过后，向用户报告生成路径、读取了哪些章节文件、是否有待补资产。

## 常见问题排查

- 如果生成了 DOCX 但内容还是模板，先看 `09_state/current_content_manifest.json` 的 `draft_files` 是否为空。
- 如果 `draft_files` 为空，检查章节正文是否命名为 `ch*.md`，且不是 `*_plan.md`。
- 如果只有一章，检查 `09_state/project_state.json` 是否仍是模板解析出的旧结构；重新运行 `apply_markdown_to_xml.py` 会根据当前 Markdown 重建章节结构。
- 如果 Word 没有出现表格，检查是否使用了标准 `[[TBL:...]]` 或 Markdown 表格。
- 如果反解析后的公式变成空泛占位，重新运行最新版 `reverse_parse_docx.py`；正常结果应是 `[[EQ:真实公式]]` 或 `[[SYM:真实符号]]`，不应只有 `[[EQ:公式]]`。
- 如果引用显示异常，检查是否使用了 `[[REF:n]]` 或 `[[REF:KEYWORD_PLACEHOLDER: 关键词]]`，并阅读 `references/reference_rules.md`。
- 如果公式中残留反斜杠命令，检查公式是否超出 `references/placeholders.md` 支持的有限 LaTeX 语法。

## 安全规则

- 永不覆盖 `01_template/original_template.docx`。
- 每次写回 XML 前，如果 `09_state/current_working.xml` 已存在，保留时间戳快照。
- 写回失败时保留 Markdown、manifest、`project_state.json` 和上一个 XML 快照。
- 只在用户确认或任务明确要求时生成最终 DOCX。
- 对用户未确认的数据、结论、文献和创新点保持保守表达。


## Word/XML 写回规则

- 保留模板中的目录、表格目录和插图目录字段，不要删除或重建这些 front matter 字段。正文写回只替换摘要内容；目录、表格目录和插图目录依赖 Word 的 `w:updateFields=true` 和 dirty field 标记刷新。
