---
title: 代码 Patch 生成器
status: done
labels:
  - ready-for-agent
created: 2026-07-09
---

## Parent

- [错误分析与修复决策器](.scratch/auto-fix-pipeline/001-error-analyzer.md)

## What to build

根据修复策略生成代码 diff，直接写入本地文件系统。

流程：
1. 从待修复队列获取 `fix_strategy` 和 `affected_files`
2. LLM 读取相关文件内容，生成修复代码
3. 应用修改到文件系统（使用 Edit tool 的逻辑）
4. 输出：
   - `patch_applied: true`
   - `modified_files: [{ path, before, after }]`
   - `patch_id: uuid` — 用于后续回滚

安全措施：
- 每次修复前备份原文件内容到 `auto_fix_backup` 表
- Patch 仅修改前端代码（`.ts`, `.tsx`, `.js`, `.jsx`）
- 不修改 `node_modules`、`.env`、数据库迁移文件
- 单次修复最多修改 3 个文件

不在此 issue 范围内：
- Git commit —— #003
- 回滚机制 —— #004
- 验证 —— #005

## Acceptance criteria

- [ ] `PatchGenerator` 根据 `fix_strategy` 生成代码修改
- [ ] 修改前备份原内容到 `auto_fix_backup` 表
- [ ] 仅修改 `.ts/.tsx/.js/.jsx` 文件
- [ ] 单次修复最多修改 3 个文件
- [ ] Patch 结果写入 `auto_fix_log` 表
- [ ] 生成唯一 `patch_id` 供回滚使用

## Blocked by

- [错误分析与修复决策器](.scratch/auto-fix-pipeline/001-error-analyzer.md)