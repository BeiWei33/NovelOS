---
title: Workflow 暂停/恢复机制
status: open
labels:
  - ready-for-agent
created: 2026-07-09
---

## Parent

- [ChapterWorkflow 全流程](.scratch/chapter-workflow/012-chapter-workflow.md)

## What to build

实现 ChapterWorkflow 的暂停/恢复机制，支持长时间运行的 workflow 中断后从断点恢复，而非从头开始。

当前 `ChapterWorkflowEngine` 已有 `_rollback()` 但无暂停/恢复。

需要实现：

1. **持久化 Workflow State**：
   - 每个步骤完成后将当前状态持久化到数据库或 Redis
   - 状态包括：current_step、completed_steps、scene_ids、错误列表
   - 使用 Redis 缓存（快速） + DB 持久化（可靠）

2. **暂停逻辑**：
   - `pause()` 方法：完成当前 step 后停止，不继续下一步
   - 自动暂停：API 超时或任务超时时自动暂停
   - 前端"暂停"按钮（可选，延后）

3. **恢复逻辑**：
   - `resume()` 方法：从 last_completed_step 的下一步继续
   - 恢复时重建上下文（重新读取 DB 而非重新 LLM 调用）
   - 场景已写入的跳过重写，只写入未完成的

4. **API 端点**：
   - `GET /workflow/status/{chapter_id}` — 查询当前 workflow 状态
   - `POST /workflow/pause/{chapter_id}` — 暂停
   - `POST /workflow/resume/{chapter_id}` — 恢复

5. **超时保护**：
   - 单步超时（如 LLM 调用超过 60s）自动进入暂停
   - 可配置超时时间

不在此 issue 范围内：
- ChapterFactsAggregator —— #003
- ChapterMemoryUpdater —— #004

## Acceptance criteria

- [ ] Workflow 状态持久化到 DB/Redis
- [ ] `pause()` 在完成当前 step 后停止
- [ ] `resume()` 从断点恢复，不重复已完成的步骤
- [ ] 恢复时已写入的场景不重新生成
- [ ] 3 个 API 端点可查询/暂停/恢复
- [ ] 单步超时自动暂停

## Blocked by

None - can start immediately