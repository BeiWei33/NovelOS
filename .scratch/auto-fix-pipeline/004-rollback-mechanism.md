---
title: 回滚机制
status: done
labels:
  - ready-for-agent
created: 2026-07-09
---

## Parent

- [代码 Patch 生成器](.scratch/auto-fix-pipeline/002-patch-generator.md)

## What to build

实现一键回滚机制，当修复导致问题时可快速恢复原状态。

流程：
1. `auto_fix_backup` 表存储每次修复前的文件原内容
2. 回滚 API：`POST /api/auto-fix/rollback/{patch_id}`
3. 执行回滚：
   - 从 backup 表读取原内容
   - 写回文件系统
   - 执行 `git checkout` 撤销 commit（或 `git revert`）
   - 删除 auto-fix 分支（如有）
4. 记录回滚日志到 `auto_fix_log.rollback_at`

触发回滚场景：
- 修复后测试失败（自动触发 —— #005）
- 人工在 UI 点击"回滚"按钮（#006）
- 新错误与修复相关（相关性分析触发）

不在此 issue 范围内：
- Patch 生成 —— #002
- Git commit —— #003
- 自动验证触发回滚 —— #005

## Acceptance criteria

- [ ] `POST /api/auto-fix/rollback/{patch_id}` 端点可触发回滚
- [ ] 回滚从 `auto_fix_backup` 恢复原文件内容
- [ ] Git 回滚使用 `git revert`（保留历史）或 `git reset --hard`（配置可选）
- [ ] 回滚后删除 `auto-fix/{patch_id}` 分支
- [ ] 回滚结果记录到 `auto_fix_log.rollback_at`
- [ ] 回滚失败时报警（通知运维）

## Blocked by

- [代码 Patch 生成器](.scratch/auto-fix-pipeline/002-patch-generator.md)