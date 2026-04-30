# Keyword Literature Download

## 用途

这个 skill 用于根据任意关键词批量检索英文或中文学术文献，生成候选文献表，并下载当前网络环境中可合法访问的 PDF。它适合综述准备、课题摸底、研究方向扫描、方法资料收集和批量文献初筛。

## 核心流程

1. 读取 `references/config_template.json` 或用户提供的自定义配置文件。
2. 根据 `queries` 调用 PubMed/PMC、Europe PMC、Crossref 和 OpenAlex。
3. 合并原始 API 结果，生成不预先去重的候选表。
4. 根据 `include_terms`、`secondary_terms`、`exclude_terms`、文献类型和开放访问标记计算优先级。
5. 并发下载可直接访问的 PDF。
6. 对 HTML/XML 等非 PDF 内容只缓存到 `download_work/non_pdf_payloads/`，不写入 PDF 输出目录。
7. 在续跑阶段从缓存 HTML 中尝试二次追踪 PDF 链接。
8. 对 PDF 按 DOI、标题标准化和文件哈希去重。
9. 保留候选表、下载日志、二次追踪日志、去重清单和汇总报告。

## 使用约束

- 只下载合法开放访问的文件，不绕过付费墙。
- PDF 输出目录必须只包含通过 PDF 签名检查的 `.pdf` 文件。
- 下载失败、断链、限流、付费墙和超时都要写入日志。
- 不要把 HTML/XML 声称为 PDF。
- 不要在公开配置或文档中写入个人路径、桌面路径、用户名、机构私有目录或非公开数据文件名。

## 常用命令

启动新任务：

```powershell
python .\scripts\run_keyword_harvest_no_dedup.py `
  --output-root ".\runs" `
  --config ".\my_topic_config.json" `
  --run-name "my_topic_001" `
  --pdf-output-dir ".\pdfs\my_topic" `
  --download-workers 8
```

续跑、HTML 二次追 PDF、去重：

```powershell
python .\scripts\continue_download_and_dedup.py `
  --run-root ".\runs\my_topic_001" `
  --retry-failed
```

## 输出

- `keyword_research_candidate_table.csv`
- `keyword_research_high_priority.csv`
- `keyword_research_medium_priority.csv`
- `download_logs/keyword_research_download_log.csv`
- `download_logs/keyword_research_html_second_pass.csv`
- `download_work/non_pdf_payloads/`
- `keyword_research_dedup_manifest.csv`
- `downloaded_pdfs_deduplicated/`
- `keyword_research_harvest_summary.md`
