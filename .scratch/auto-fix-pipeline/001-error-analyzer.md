---
title: 错误分析与修复决策器
status: done
labels:
  - ready-for-agent
created: 2026-07-09
---

## Parent

- [错误存储到后端数据库](.scratch/frontend-error-logging/003-error-storage.md)

## What to build

实现 AI 驱动的错误分析器，读取 `frontend_error` 表中的错误，判断是否可自动修复，并输出修复策略。

流程：
1. 定时扫描未处理的错误（或监听新错误写入事件）
2. LLM 分析错误信息：message、stack、context、用户环境
3. 输出决策：
   - `can_fix: true/false` — 是否可自动修复
   - `fix_type: "frontend" | "backend" | "config" | "unknown"` — 修复类型
   - `risk_level: "low" | "medium" | "high"` — 风险等级
   - `fix_strategy: string` — 修复策略描述（供 Patch 生成器使用）
   - `affected_files: string[]` — 可能涉及的文件路径

限制范围：
- 仅处理 `type: "api"` 和 `type: "render"` 的前端错误
- 不处理数据库迁移、认证相关错误（风险过高）
- `risk_level: "high"` 的错误不自动修复，标记为需人工处理

不在此 issue 范围内：
- Patch 生成 —— #002
- Git commit —— #003

## Acceptance criteria

- [ ] `ErrorAnalyzer` 类读取未处理的 `frontend_error` 记录
- [ ] LLM 分析返回 `can_fix`、`fix_type`、`risk_level`、`fix_strategy`
- [ ] `can_fix: true` 且 `risk_level: "low"` 的错误进入待修复队列
- [ ] `risk_level: "high"` 或 `fix_type: "unknown"` 的错误标记为需人工处理
- [ ] 分析结果写入 `frontend_error.analysis_result`（JSONB 字段）
- [ ] 同一 fingerprint 的错误只分析一次（去重）

## Blocked by

- [错误存储到后端数据库](.scratch/frontend-error-logging/003-error-storage.md)