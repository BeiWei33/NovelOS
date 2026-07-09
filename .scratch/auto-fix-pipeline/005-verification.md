---
title: 修复结果验证
status: done
labels:
  - ready-for-agent
created: 2026-07-09
---

## Parent

- [代码 Patch 生成器](.scratch/auto-fix-pipeline/002-patch-generator.md)

## What to build

修复后自动运行测试和类型检查，失败则触发回滚。

流程：
1. Patch 应用后，执行验证：
   - TypeScript 类型检查：`npm run typecheck` 或 `tsc --noEmit`
   - ESLint 检查：`npm run lint`
   - 单元测试：`npm run test`（如有）
   - 前端构建：`npm run build`
2. 验证结果：
   - 全部通过：标记 `verified: true`，允许 commit
   - 任一失败：标记 `verified: false`，触发回滚
3. 验证超时：配置最大等待时间（如 5 分钟），超时视为失败

配置：
- 可配置验证步骤（跳过测试、仅类型检查等）
- 可配置验证超时时间
- 可配置失败后的行为（回滚 / 标记待人工处理 / 仅报警）

不在此 issue 范围内：
- Patch 生成 —— #002
- 回滚机制 —— #004（但验证失败会调用回滚）

## Acceptance criteria

- [ ] Patch 应用后自动运行 `tsc --noEmit` 类型检查
- [ ] 自动运行 `npm run lint` ESLint 检查
- [ ] 自动运行 `npm run test` 单元测试（可配置跳过）
- [ ] 自动运行 `npm run build` 前端构建（可配置跳过）
- [ ] 任一验证失败则触发回滚 API
- [ ] 验证结果记录到 `auto_fix_log.verified`

## Blocked by

- [代码 Patch 生成器](.scratch/auto-fix-pipeline/002-patch-generator.md)
- [回滚机制](.scratch/auto-fix-pipeline/004-rollback-mechanism.md)