# Maintenance Workflow

这个仓库把“可编辑的源 Markdown”和“Codex 可安装 skill 包”分开管理。

## 推荐维护方式

平时只改 `source-notes/`。

改完后运行：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\sync-source-to-skills.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\validate-repo.ps1
```

如果需要让 Codex 立即使用更新后的 skill，再运行：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install-local-skills.ps1 -ForceInstall
```

## 关键映射

所有映射都在 `manifests/skills.json` 里。

- `category` 是给人阅读和筛选用的功能分类。
- `sourceFile` 是 `source-notes/` 里的源 Markdown 文件名。
- `displayName` 是给人看的标题。
- `skillName` 是 `SKILL.md` frontmatter 里的 `name`，也是 Codex 中建议写成 `$skillName` 的调用名。
- `skillDir` 是 `skills/` 下面的目录名。
- `useWhen` 是帮助读者判断什么时候调用这个 skill 的一句话说明。

## 从本地 Codex 反向导出

如果你先在本地 Codex skills 目录里改了某个 skill，可以运行：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\export-installed-skills.ps1 -ForceExport
```

这会把本地已安装的 skill 包同步回仓库的 `skills/`。

## 触发策略

当前这些 skill 的 `description` 都写成“只有用户明确调用 `$skillName` 时才使用”。这能降低 Codex 因主题相似而自动选中它们的概率。
