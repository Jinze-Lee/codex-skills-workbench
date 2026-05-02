# Master Thesis Studio Skill

## 用途

这个 skill 用于中文硕士论文写作、章节管理和 Word `.docx` 自动生成。它适合需要把论文题目、章节计划、参考文献、图表、公式、代码、数据和 Word 模板组织到一个可追溯项目目录中的场景。

## 触发方式

这个 skill 只能显式调用。用户必须写出 `$master-thesis-studio-skill`，或明确说明要使用 `master-thesis-studio-skill` / `Master Thesis Studio`。不要因为用户只是提到硕士论文、Word、东南大学模板、DOCX 生成或学术写作就自动启用。

## 核心流程

1. 先确认题目、学科方向、研究对象、核心方法、已有资产和写作边界。
2. 初始化独立论文项目目录，生成 `00_project/`、`03_chapters/`、`04_figures/`、`05_tables/`、`08_refs/`、`09_state/` 和 `10_output/`。
3. 选择模板：默认使用内置 `examples/Template.docx`，也可以传入用户自己的 `.docx` 或 `.dotx` Word 模板。
4. 将章节正文保存在 Markdown 中，图表、公式、参考文献和交叉引用使用显式占位符。
5. 将 Word 模板转换为 Flat OPC XML，解析模板结构，再把 Markdown 内容写回 XML。
6. 构建新的 `.docx` 到 `10_output/`，不覆盖原始模板。
7. 可选反解析已有 Word，抽取章节、图片、表格和公式，供后续续写、修订或 round-trip 校验。

## 主要能力

- 使用 manifest 管理论文事实、章节状态、参考文献、图、表、代码、数据和待补材料。
- 支持 `[[FIG:...]]` 图片占位与图题。
- 支持 `[[TBL:...]]` 与 Markdown 表格，生成真实 Word 三线表。
- 支持 `[[EQ:...]]` 显示公式、`[[SYM:...]]` 行内公式或符号，并尽量写成 Word OMML。
- 支持 `[[REF:n]]`、`[[REF_FIG:...]]`、`[[REF_TBL:...]]` 等引用和交叉引用。
- 保留模板中的标题、正文、图题、表题、参考文献、目录字段、页眉页脚和分节结构。
- 支持用户自选 `.docx` / `.dotx` 模板，模板来源会记录到项目状态文件中。

## 使用约束

- 不编造真实文献、实验结果、样本量、指标或数据来源。
- 不覆盖 `01_template/original_template.docx`。
- 新生成的 Word 只写入 `10_output/`，XML 中间态只写入 `09_state/`。
- 用户给出已有 Word 时，先区分它是格式模板、已有论文内容，还是两者都是。
- 反解析已有 Word 是可选入口，只有在用户明确需要抽取内容时才执行。

## 常用命令

初始化新项目，使用内置模板：

```powershell
python <skill_dir>\scripts\init_thesis_workspace.py .
```

初始化新项目，使用用户自己的 Word 模板：

```powershell
python <skill_dir>\scripts\init_thesis_workspace.py . --template <user_template.docx>
```

写回并生成 Word：

```powershell
python <skill_dir>\scripts\apply_markdown_to_xml.py . --out 09_state\current_working.xml
python <skill_dir>\scripts\build_new_docx.py . --name thesis_draft_v1.docx
python <skill_dir>\scripts\validate_xml_docx.py .
```

可选反解析已有 Word：

```powershell
python <skill_dir>\scripts\reverse_parse_docx.py <project_dir> --docx <user_thesis.docx>
```
