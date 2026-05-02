# Codex Skills Workbench

这个仓库用于管理一组从 Markdown 指南整理出来的 Codex skills。

设计目标很简单：

- `source-notes/` 保留源 Markdown 文件，方便继续维护工作流正文。
- `skills/` 保存可以安装到 Codex 的 skill 包。
- `manifests/skills.json` 维护源文件名、展示名、调用名、skill 目录和功能分类。
- `scripts/` 提供同步、安装、导出和检查脚本，方便本地维护并上传 GitHub。

## Repository Layout

```text
codex-skills-workbench/
  source-notes/          # 源 Markdown 指南
  skills/                # 可安装到 <codex-skills-root> 的 skill 包
  manifests/skills.json  # 统一映射表和分类信息
  scripts/               # 本地维护脚本
  docs/                  # 维护说明
```

## Public Template Policy

这个仓库按公开模板维护。`source-notes/` 和 `skills/*/references/source-note.md` 中只保留通用工作流、输入占位符和路径占位符，不包含身份标识、机器盘符、旧项目目录或非公开数据文件名。

更多说明见 [docs/public-template.md](docs/public-template.md)。

## Skill Categories

完整分类说明见 [docs/skill-categories.md](docs/skill-categories.md)。

### Environment And Operations

| Skill | 调用名 | 什么时候用 |
| --- | --- | --- |
| Shell Choice Guide | `$shell-choice-guide` | 判断 Windows、Git、R/Python、文件操作或桌面自动化任务该用哪个 shell。 |
| R Python Runtime Guide | `$r-python-runtime-guide` | 发现和调用 R/Python 运行时，避免写死机器路径。 |
| Method Transfer Guide | `$method-transfer-guide` | 把一个方法、作图模式或自动化流程安全迁移到新项目。 |

### Presentation And Reporting

| Skill | 调用名 | 什么时候用 |
| --- | --- | --- |
| PPT Production Guide | `$ppt-production-guide` | 生成 PowerPoint、构建自定义图墙，并先询问是否要打开 PowerPoint 桌面版显示逐步生成过程。 |
| Literature Synthesis | `$literature-synthesis-guide` | 把文献整理成证据表、主题综合或可引用的叙述性总结。 |
| Master Thesis Studio Skill | `$master-thesis-studio-skill` | 写作和生成中文硕士论文 Word 项目，支持显式调用、自选模板、图表、公式、参考文献和反解析。 |

### Research And Literature

| Skill | 调用名 | 什么时候用 |
| --- | --- | --- |
| Keyword Literature Download | `$keyword-literature-download` | 按关键词检索学术数据库，下载合法开放 PDF，缓存 HTML/XML 辅助文件，并对 PDF 去重。 |

### Plotting And Visualization

| Skill | 调用名 | 什么时候用 |
| --- | --- | --- |
| Plotting Tool Selection | `$plotting-tool-selection` | 判断图该用 R、Python、PowerPoint、矢量工具还是表格软件。 |
| ggplot2 Richtext Fixes | `$ggplot2-richtext-fixes` | 修复 ggplot2 上标、下标、富文本、特殊符号和导出渲染问题。 |
| R Scatter Plot Spec | `$r-scatter-plot-spec` | 做可复现的 R 散点图，包括回归、分组、导出和统计结果。 |
| Trait Environment Scatterplots | `$trait-environment-scatterplots` | 做性状-环境、响应-预测变量或分组散点图，并配套模型解释。 |
| Significance Group Scatter | `$significance-group-scatter` | 在分组散点图里强调有统计支持的组，同时保留其他组作背景。 |
| Raincloud Plot Guide | `$raincloud-plot-guide` | 做雨云图，组合分布、原始点、区间和摘要统计。 |
| Weighted Regression Plot | `$weighted-regression-plot` | 做加权回归图，处理权重含义、不确定性和视觉编码。 |

### Data Processing And Modeling

| Skill | 调用名 | 什么时候用 |
| --- | --- | --- |
| Weighted Data Pipeline | `$weighted-data-pipeline` | 从清洗、合并、权重计算到模型和图表的完整加权数据流程。 |

### Ecology And Evolution

| Skill | 调用名 | 什么时候用 |
| --- | --- | --- |
| Hypervolume Workflow | `$hypervolume-workflow` | 做生态位、性状空间、hypervolume、重叠或质心距离分析。 |
| Phylogeny Workflow | `$phylogeny-workflow` | 匹配性状数据和系统发育树，修剪树、画树或做比较分析。 |

## Skill 中文介绍

### Shell Choice Guide

调用名：`$shell-choice-guide`

这个 skill 用来判断在 Windows 或跨平台项目中应该使用哪一种命令环境。它会根据任务类型选择 PowerShell、Git Bash、WSL 或其他 shell，例如文件操作、Git 命令、R/Python 脚本、`.ps1` 脚本和 PowerPoint COM 自动化。它特别强调路径安全：遇到空格、中文、括号、方括号、`&` 等特殊字符时，要使用合适的引用方式和 PowerShell 的 `-LiteralPath`。

### R Python Runtime Guide

调用名：`$r-python-runtime-guide`

这个 skill 用来规范 R 和 Python 的运行环境发现与调用方式。它不会假设某台机器上的固定解释器路径，而是先检查当前项目里可用的 `Rscript`、`python`、`uv`、虚拟环境或包管理工具，再生成可复现的运行命令。适合需要在不同电脑、不同项目或不同 shell 中稳定运行 R/Python 分析脚本的场景。

### Method Transfer Guide

调用名：`$method-transfer-guide`

这个 skill 用于把一个已有项目中的分析方法、作图风格或自动化流程迁移到另一个项目。它的核心原则是迁移“方法逻辑”，而不是复制旧路径、旧变量名和旧数据假设。它会提醒使用者检查源方法中的变量、单位、分组、阈值、输出结构，再把这些假设映射到新项目中，并先用小样本测试。

### PPT Production Guide

调用名：`$ppt-production-guide`

这个 skill 用于生成和维护 PowerPoint 演示文稿。它支持普通幻灯片、图表汇报页、自定义图片墙、重复图墙页、标题和注释说明。图片墙不固定为 2 行 3 列，而是允许用户自定义行数、列数、边距、间距、适配方式、重复次数和说明文字。做 PPT 前，它会先询问用户是否要打开 PowerPoint 桌面版并可见地显示逐页生成过程；如果用户需要，就使用 PowerShell 控制 PowerPoint COM，让用户看到图片和页面被一步步插入。

### Literature Synthesis

调用名：`$literature-synthesis-guide`

这个 skill 用于文献总结和证据综合。它会先明确研究问题、文献范围、纳入排除标准和输出格式，然后从文献中提取研究对象、方法、样本量、变量、主要结果和局限。输出可以是证据表、主题归纳、研究空白、可引用段落或报告提纲。它强调所有结论都要能追溯到具体文献，不凭空编造引用。

### Master Thesis Studio Skill

调用名：`$master-thesis-studio-skill`

这个 skill 用于中文硕士论文写作、章节管理和 Word `.docx` 自动生成。它只在用户显式写出 `$master-thesis-studio-skill`，或明确说明要使用 Master Thesis Studio 时启用，不会因为普通论文写作或 Word 排版请求而自动触发。它会先确认题目、学科方向、研究对象、已有资产、写作模式和真实性边界，再初始化独立论文项目目录。

它保留论文生成的完整执行链路：使用 Markdown 管理章节正文，用 `[[FIG:...]]`、`[[TBL:...]]`、`[[EQ:...]]`、`[[SYM:...]]`、`[[REF:n]]` 等占位符管理图、表、公式和引用；再把 Word 模板转换为 Flat OPC XML，写回正文结构并生成新的 `.docx`。默认模板是 `examples/Template.docx`，也可以通过 `--template <user_template.docx>` 使用用户自己的 `.docx` 或 `.dotx` 模板。更详细说明见 [skills/master-thesis-studio-skill/README.md](skills/master-thesis-studio-skill/README.md)。

### Keyword Literature Download

调用名：`$keyword-literature-download`

这个 skill 用于围绕任意关键词批量检索学术文献，并尽可能下载当前网络环境中可合法访问的 PDF。它会调用 PubMed/PMC、Europe PMC、Crossref 和 OpenAlex，先生成不预先去重的候选文献表，再根据关键词命中、文献类型、开放访问状态等信息给记录排序，随后并发下载 PDF。下载不到 PDF 但能访问 HTML/XML 时，它会把这些辅助文件放入单独缓存目录，后续再尝试从网页里追踪 PDF 链接；PDF 输出目录始终只保存通过 PDF 签名检查的 `.pdf` 文件。

基本使用方法：

1. 进入 `skills/keyword-literature-download/` 目录。
2. 复制 `references/config_template.json` 为自己的配置文件，例如 `my_topic_config.json`。
3. 修改配置中的 `queries`、`include_terms`、`secondary_terms` 和 `exclude_terms`。
4. 启动新任务：

```powershell
python .\scripts\run_keyword_harvest_no_dedup.py `
  --output-root ".\runs" `
  --config ".\my_topic_config.json" `
  --run-name "my_topic_001" `
  --pdf-output-dir ".\pdfs\my_topic" `
  --download-workers 8
```

5. 中断后续跑、HTML 二次追 PDF、去重：

```powershell
python .\scripts\continue_download_and_dedup.py `
  --run-root ".\runs\my_topic_001" `
  --retry-failed
```

常见输出包括 `keyword_research_candidate_table.csv`、高/中优先级候选表、下载日志、HTML 二次追踪日志、`keyword_research_dedup_manifest.csv` 和去重后的 PDF 文件夹。更详细的中文说明见 [skills/keyword-literature-download/README.md](skills/keyword-literature-download/README.md)。这个 skill 只下载合法开放访问文件，不绕过付费墙；访问失败、断链、限流和超时都会保留在日志中。

### Plotting Tool Selection

调用名：`$plotting-tool-selection`

这个 skill 用来判断一张图应该用什么工具做。统计建模和 tidy 数据图通常优先 R；自动化、图像处理或机器学习流程中的图可以优先 Python；以幻灯片排版为主的内容可以用 PowerPoint；最终精修可交给矢量工具。它适合在动手作图前做路线选择，避免把所有图都强行塞进同一个工具。

### ggplot2 Richtext Fixes

调用名：`$ggplot2-richtext-fixes`

这个 skill 专门处理 `ggplot2` 中的文字渲染问题，例如上标、下标、数学表达式、单位符号、斜体物种名、HTML/Markdown 标签、图例标签和分面标题。它会帮助判断应该使用 `expression()`、`bquote()`、普通 Unicode，还是 `ggtext::element_markdown()` / `geom_richtext()`。它也提醒用户导出设备会影响最终效果，所以批量出图前要先导出小图测试。

### R Scatter Plot Spec

调用名：`$r-scatter-plot-spec`

这个 skill 是可复现 R 散点图的基础规范。它覆盖数据读取、编码、变量检查、缺失值处理、异常值检查、分组样本量、回归线、统计表和图像导出。适合需要稳定批量生成散点图、回归图或分组对比图的场景。它强调图和统计结果应该一起输出，而不是只给一张图片。

### Trait Environment Scatterplots

调用名：`$trait-environment-scatterplots`

这个 skill 用于性状-环境、响应变量-预测变量或分组散点图，不限定于 pH。它会先检查响应变量、预测变量、分组层级、缺失值、异常值和样本量，再选择 pooled regression、grouped regression、mixed model、weighted model、robust model 或非参数平滑。它适合科研作图中需要同时展示原始点、分组、拟合趋势、不确定性和简短解释的场景。

### Significance Group Scatter

调用名：`$significance-group-scatter`

这个 skill 用于“分组散点图 + 显著性强调”。它不会简单地隐藏不显著组，而是保留所有组作为背景，再用颜色、线宽、透明度、标签等方式强调统计支持更强的组。它要求同时输出效应量、不确定性、p 值或置信区间、样本量，并说明显著性判断标准。适合需要讲清楚“哪些组有关系，哪些组只是背景”的图。

### Raincloud Plot Guide

调用名：`$raincloud-plot-guide`

这个 skill 用于制作雨云图，也就是把分布形状、原始观测点、箱线图或区间、均值/中位数等信息组合到一张图里。它会先检查分组样本量、缺失值、是否需要转换或标准化，再决定半眼图、抖动点、箱线图和摘要统计的组合方式。适合展示组间分布差异，而不是只展示均值柱状图。

### Weighted Regression Plot

调用名：`$weighted-regression-plot`

这个 skill 用于加权回归图。它会先确认权重变量代表什么、尺度是否合理、是否存在零权重或负权重，再比较加权模型和必要时的非加权模型。图形上可以使用点大小、透明度、颜色、形状和趋势线表达权重与分组信息。它强调解释时要说清楚“权重越大代表什么”，并避免把相关关系直接解释成因果关系。

### Weighted Data Pipeline

调用名：`$weighted-data-pipeline`

这个 skill 用于完整的加权数据分析流程，而不只是画一张图。它包括建立输入输出清单、去重、变量清理、编码和单位检查、中间指标计算、表格合并、权重提取或计算、加权模型、最终图表和可复现日志。适合多文件、多步骤、多中间结果的分析项目，尤其适合需要把数据处理过程讲清楚、留痕和复用的场景。

### Hypervolume Workflow

调用名：`$hypervolume-workflow`

这个 skill 用于生态位、性状空间或 hypervolume 分析。它会先检查分析单元、变量、分组、缺失值、单位和样本量，再选择 kernel hypervolume、convex hull、PCA/ordination 空间或其他生态位度量方法。典型输出包括清洗后的数据、参数记录、体积或生态位指标、重叠矩阵、质心距离、诊断图和主结果图。它强调结果要结合研究设计解释，不能把体积大小简单理解成绝对好坏。

### Phylogeny Workflow

调用名：`$phylogeny-workflow`

这个 skill 用于系统发育树相关分析。它会帮助读取树文件，标准化树和性状表中的分类单元名称，报告树中有但数据中没有的物种，以及数据中有但树中没有的物种。之后可以进行剪枝、匹配、系统发育树可视化、性状映射、系统发育信号或比较分析。典型输出包括匹配报告、剪枝后的树、匹配后的性状表、结果图和可复现记录。

## Daily Workflow

1. 修改 `source-notes/` 里的源 Markdown。
2. 同步源 Markdown 到对应 skill：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\sync-source-to-skills.ps1
```

3. 检查仓库结构：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\validate-repo.ps1
```

4. 安装到本地 Codex skills 目录：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install-local-skills.ps1 -ForceInstall
```

## Rename A Source Note

如果以后想改源文件名：

1. 直接重命名 `source-notes/` 中的 Markdown 文件。
2. 修改 `manifests/skills.json` 中对应条目的 `sourceFile`。
3. 运行：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\sync-source-to-skills.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\validate-repo.ps1
```

实际 Codex 调用名由 `skillDir` / `skillName` 控制，不会因为源文件名变化而变化。

## Upload To GitHub Later

更详细的步骤见 [docs/github-upload.md](docs/github-upload.md)。

首次推送时可以在这个目录里运行：

```powershell
git add .
git commit -m "Add Codex skills workbench"
git branch -M main
git remote add origin https://github.com/<account>/<repo>.git
git push -u origin main
```
