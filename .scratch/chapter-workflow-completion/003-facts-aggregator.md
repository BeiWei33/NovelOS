---
title: ChapterFactsAggregator
status: done
labels:
  - ready-for-agent
created: 2026-07-09
completed: 2026-07-09
---

## Parent

- [ChapterWorkflow 全流程](.scratch/chapter-workflow/012-chapter-workflow.md)

## What to build

实现 ChapterFactsAggregator，聚合 Chapter 下所有 Scene 的 facts，去重合并后写入 `chapter.chapter_facts`。

当前 ChapterWorkflow 的 5 步中，第 4 步 Artifacts 后直接跳到 Summary，跳过了 FactsAggregator 和 MemoryUpdater。

需要实现：

1. **FactsAggregator 逻辑**：
   - 读取 Chapter 下所有 Scene 的 scene_artifact.facts
   - 按 fact_type 分组（relationship_changes / world_changes / timeline_changes / new_information）
   - 去重：相同 actor+target+payload 的 fact 只保留一个
   - 冲突检测：同一事实在不同 Scene 中有矛盾 → 标记为冲突
   - 写入 `chapter.chapter_facts`

2. **集成到 ChapterWorkflow**：在 `_step_artifacts()` 之后、`_step_summary()` 之前执行

3. **API 端点**：`POST /skills/aggregate-facts/{chapter_id}` 可单独触发

4. **前端展示**：章节详情页显示 facts 概览（可选）

不在此 issue 范围内：
- ChapterSummary —— #001
- ChapterMemoryUpdater —— #004

## Acceptance criteria

- [ ] 读取所有 Scene 的 artifact facts
- [ ] 按 4 种 fact_type 分组
- [ ] 去重合并：相同 actor+target+payload 只保留最新
- [ ] 冲突检测：矛盾 fact 标记为冲突
- [ ] 写入 `chapter.chapter_facts` 字段
- [ ] 集成到 ChapterWorkflow 中
- [ ] 单独 API 端点可触发聚合

## Blocked by

- [场景数据管道](.scratch/scene-data-pipeline/008-scene-data-pipeline.md)（依赖 scene_artifact 表有数据）