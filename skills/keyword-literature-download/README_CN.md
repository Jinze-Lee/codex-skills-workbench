# 关键词文献检索与 PDF 下载 Skill

这是一个可复用的 Codex skill，用来围绕任意英文或中文关键词批量检索学术文献，生成候选文献表，并尽可能下载合法开放访问的 PDF。它适合文献初筛、课题开题、综述准备、研究方向摸底、方法学资料收集等场景。

这个工具只使用 PubMed/PMC、Europe PMC、Crossref 和 OpenAlex 等公开学术接口，以及接口返回的开放链接；它不会绕过付费墙，也不会把 HTML/XML 文件伪装成 PDF。

## 功能概览

- 按自定义关键词同时检索多个学术数据源。
- 生成未去重的候选文献表，便于先尽量收全。
- 根据标题、摘要、文献类型和关键词命中情况给候选文献打优先级。
- 并发下载可合法访问的 PDF。
- 保证 PDF 输出目录只保存真实 PDF 文件。
- 将 HTML/XML 辅助文件缓存到单独目录，后续再尝试从网页中追踪 PDF 链接。
- 记录成功、失败、付费墙、断链、限流、超时等下载状态。
- 对最终 PDF 按 DOI、标题和文件哈希去重。

## 目录结构

```text
keyword-literature-download/
  SKILL.md
  README.md
  references/
    config_template.json
    prompt_template.md
  scripts/
    run_keyword_harvest_no_dedup.py
    continue_download_and_dedup.py
  literature_harvest/
    scripts/
      search_pubmed.py
      search_europepmc.py
      search_crossref.py
      search_openalex.py
      merge_and_deduplicate.py
      download_fulltexts.py
      harvest_utils.py
```

## 安装方式

把整个 `keyword-literature-download` 文件夹复制到你的 Codex skills 目录下即可。不同系统的 skills 目录位置可能不同，常见形式是：

```text
<codex-home>/skills/keyword-literature-download/
```

安装后，在 Codex 对话里显式调用：

```text
$keyword-literature-download 搜索 climate change carbon nitrogen cycling 相关英文文献，并把 PDF 放到指定文件夹
```

也可以不通过 Codex，直接在终端里运行 `scripts/` 下的 Python 脚本。

## 运行环境

建议准备：

- Python 3.10 或更高版本。
- `pandas` Python 包。
- 能访问 PubMed、Europe PMC、Crossref、OpenAlex 和常见出版商页面的网络环境。

如果缺少 `pandas`，可以在你的 Python 环境里安装：

```powershell
python -m pip install pandas
```

macOS/Linux 可使用同样命令；下文示例以 PowerShell 为主，路径请按自己的系统调整。

## 第一步：复制配置模板

不要直接改模板文件。建议先复制一份：

```powershell
Copy-Item .\references\config_template.json .\my_topic_config.json
```

然后编辑 `my_topic_config.json`。

最常改的字段有四组：

- `queries`：真正发送给数据库的检索式。
- `include_terms`：核心主题词，命中后优先级会更高。
- `secondary_terms`：辅助相关词，用于提高相关性判断。
- `exclude_terms`：需要排除或降权的词，例如 editorial、commentary、patent。

一个简化例子：

```json
{
  "include_terms": [
    "global change",
    "carbon cycle",
    "nitrogen cycle"
  ],
  "secondary_terms": [
    "soil carbon",
    "nitrogen deposition",
    "warming"
  ],
  "exclude_terms": [
    "editorial",
    "commentary",
    "news"
  ],
  "queries": [
    {
      "name": "global_change_cn",
      "query": "global change carbon nitrogen cycling ecosystem"
    },
    {
      "name": "warming_soil_cn",
      "query": "warming soil carbon nitrogen microbial"
    }
  ]
}
```

实际使用时保留模板中的其他字段即可。

## 第二步：启动一次新检索和下载

命令格式：

```powershell
python .\scripts\run_keyword_harvest_no_dedup.py `
  --output-root ".\runs" `
  --config ".\my_topic_config.json" `
  --run-name "my_topic_001" `
  --pdf-output-dir ".\pdfs\my_topic" `
  --download-workers 8
```

参数说明：

- `--output-root`：保存候选表、日志、缓存和汇总报告的父目录。
- `--config`：你复制并编辑后的配置文件。
- `--run-name`：本次任务的运行目录名，建议每次不同。
- `--pdf-output-dir`：PDF 专用目录，只会写入通过 PDF 签名检查的 `.pdf` 文件。
- `--download-workers`：并发下载线程数，网络不稳定时可调小。

运行后会生成：

```text
runs/my_topic_001/
  keyword_research_candidate_table.csv
  keyword_research_high_priority.csv
  keyword_research_medium_priority.csv
  keyword_research_harvest_summary.md
  download_logs/
  download_work/non_pdf_payloads/
```

PDF 会保存到你通过 `--pdf-output-dir` 指定的目录。

## 第三步：中断后续跑、二次追 PDF、去重

大批量下载中断很正常。续跑命令：

```powershell
python .\scripts\continue_download_and_dedup.py `
  --run-root ".\runs\my_topic_001" `
  --retry-failed
```

这个脚本会继续做三件事：

1. 重试未成功下载 PDF 的记录。
2. 从 `download_work/non_pdf_payloads/` 中缓存的 HTML 页面寻找 PDF 链接。
3. 生成去重后的 PDF 文件夹和去重清单。

续跑后重点查看：

```text
runs/my_topic_001/
  download_logs/keyword_research_download_log.csv
  download_logs/keyword_research_html_second_pass.csv
  keyword_research_dedup_manifest.csv
  downloaded_pdfs_deduplicated/
```

如果第一步已经把 PDF 输出到外部目录，续跑脚本会读取运行设置并继续使用同一个 PDF 目录；也可以重新传入 `--pdf-output-dir` 覆盖。

## 输出文件怎么看

- `keyword_research_candidate_table.csv`：全部候选文献，包含标题、作者、年份、期刊、DOI、摘要、关键词命中、优先级、下载状态等。
- `keyword_research_high_priority.csv`：高相关候选文献。
- `keyword_research_medium_priority.csv`：中等相关候选文献。
- `download_logs/keyword_research_download_log.csv`：每条记录的下载结果。
- `download_logs/keyword_research_html_second_pass.csv`：HTML 二次追踪 PDF 的结果。
- `download_work/non_pdf_payloads/`：HTML/XML 辅助缓存，不是 PDF 文献库。
- `keyword_research_dedup_manifest.csv`：每个 PDF 的哈希、DOI、标题标准化结果和保留/重复判断。
- `downloaded_pdfs_deduplicated/`：去重后保留的 PDF 副本。

## 下载状态含义

- `success`：已下载真实 PDF。
- `non_pdf_saved`：拿到 HTML/XML，已缓存到辅助目录。
- `inaccessible`：可能遇到权限、订阅或付费墙限制。
- `broken_link`：链接失效。
- `rate_limited`：访问过快，被接口或站点限流。
- `metadata_only`：保留元数据，但当前没有拿到可用全文文件。

## 使用建议

如果想“尽量收全”，第一轮把 `queries` 写宽一点，`include_terms` 和 `secondary_terms` 覆盖主要同义词，下载后再人工筛选。

如果想“噪音少一点”，减少宽泛词，增加限定词，例如研究对象、生态系统类型、方法、地区、时间尺度或关键变量。

建议每个主题新建一个独立 `run-name`，不要覆盖旧任务；这样候选表、日志和去重清单都能完整保留。

## 合规边界

这个 skill 只下载当前网络环境中可合法访问的 PDF。遇到订阅限制、机构权限、购买页面或付费墙时，它会记录失败原因并保留元数据，不会尝试绕过访问控制。

## 给其他 AI/agent 的提示词

`references/prompt_template.md` 里有一份可直接复用的提示词模板。把你的主题关键词、输出目录和配置要求填进去，就可以交给其他 agent 按同一流程执行。
