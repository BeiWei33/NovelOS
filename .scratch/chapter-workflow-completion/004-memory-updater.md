---
title: ChapterMemoryUpdater
status: done
labels:
  - ready-for-agent
created: 2026-07-09
---

## Parent

- [ChapterWorkflow 全流程](.scratch/chapter-workflow/012-chapter-workflow.md)

## What to build

实现 ChapterMemoryUpdater，在 ChapterFactsAggregator 完成后更新 Chapter 级记忆。

当前 ChapterWorkflow 完全没有执行 MemoryUpdater 步骤。

需要实现：

1. **MemoryUpdater 逻辑**：
   - 接收 ChapterFactsAggregator 的输出（`chapter.chapter_facts`）
   - 更新 4 个记忆字段：
     - `relationship_changes` — 角色关系变化摘要
     - `world_changes` — 世界观状态变化摘要
     - `timeline_changes` — 时间线推进摘要
     - `new_information` — 新信息摘要
   - 使用 LLM 将原始 facts 压缩为人类可读的摘要

2. **集成到 ChapterWorkflow**：在 `_step_artifacts()` 之后、`_step_summary()` 之前执行

3. **API 端点**：`POST /skills/update-memory/{chapter_id}` 可单独触发

不在此 issue 范围内：
- ChapterFactsAggregator —— #003（强依赖）
- ChapterSummary —— #001

## Acceptance criteria

- [ ] 接收 ChapterFactsAggregator 的输出作为输入
- [ ] LLM 将 raw facts 压缩为 4 个摘要字段
- [ ] 更新 `chapter.chapter_facts` 的 4 个字段
- [ ] 集成到 ChapterWorkflow 中
- [ ] 单独 API 端点可触发
- [ ] 摘要保留关键信息但去除冗余

## Blocked by

- [ChapterFactsAggregator](.scratch/chapter-workflow-completion/003-facts-aggregator.md)