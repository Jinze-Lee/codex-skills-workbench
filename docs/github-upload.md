# GitHub Upload Guide

这个仓库已经在本地初始化为 Git 仓库，默认分支是 `main`。

## 1. 确认 Git 能访问仓库

如果 Git 提示 `dubious ownership`，可以把仓库目录加入安全名单：

```powershell
git config --global --add safe.directory "<repo-root>"
```

其中 `<repo-root>` 替换为当前仓库的实际路径。

## 2. 配置提交身份

如果还没有配置 Git 提交身份，先运行：

```powershell
git config --global user.name "<name>"
git config --global user.email "<email>"
```

如果你只想对这个仓库生效，把 `--global` 去掉。

## 3. 做第一次提交

```powershell
git status
git add .
git commit -m "Add Codex skills workbench"
```

## 4. 连接 GitHub 仓库

在 GitHub 新建一个空仓库后，把下面的地址换成目标仓库地址：

```powershell
git remote add origin https://github.com/<account>/<repo>.git
git push -u origin main
```

后续更新时：

```powershell
git add .
git commit -m "Update skills"
git push
```
