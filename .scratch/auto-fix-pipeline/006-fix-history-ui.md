---
title: 修复历史查看 UI
status: open
labels:
  - ready-for-human
created: 2026-07-09
---

## Parent

- [自动 Git Commit & Push](.scratch/auto-fix-pipeline/003-git-commit-push.md)

## What to build

在 Dashboard 中新增自动修复历史界面，支持查看修复状态、diff、手动回滚。

需要：

1. **API 端点 `GET /api/auto-fix/logs`**：
   - 分页查询修复历史
   - 过滤：`?status=verified|failed|rolled_back`
   - 返回：patch_id、error_fingerprint、modified_files、status、created_at

2. **API 端点 `GET /api/auto-fix/logs/{patch_id}`**：
   - 返回详细：diff、before/after 内容、验证结果、commit hash

3. **前端页面 `/admin/auto-fix`**：
   - 修复列表：时间倒序，显示错误类型、状态、文件数
   - 详情视图：点击查看 diff（类似 GitHub PR diff）
   - 回滚按钮：手动触发回滚
   - 分支状态：显示 auto-fix 分支是否已合并

4. **权限控制**：
   - 仅管理员可访问
   - 回滚操作需二次确认

设计决策需人类确认：
- UI 放在哪个导航位置？
- 是否需要"合并到 main"按钮？
- 是否需要批量回滚功能？

不在此 issue 范围内：
- Git commit —— #003
- 回滚机制 —— #004

## Acceptance criteria

- [ ] `GET /api/auto-fix/logs` 端点返回修复历史列表
- [ ] `GET /api/auto-fix/logs/{patch_id}` 返回详细 diff
- [ ] 前端 `/admin/auto-fix` 页面显示修复列表
- [ ] 点击修复可查看 before/after diff
- [ ] 有"回滚"按钮，点击后二次确认再执行
- [ ] 回滚后 UI 显示已回滚状态

## Blocked by

- [自动 Git Commit & Push](.scratch/auto-fix-pipeline/003-git-commit-push.md)
- [回滚机制](.scratch/auto-fix-pipeline/004-rollback-mechanism.md)