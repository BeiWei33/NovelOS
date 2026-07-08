---
title: ChapterWorkflow 全流程
status: open
labels:
  - ready-for-agent
created: 2026-07-08
---

## What to build

实现完整的 ChapterWorkflow 编排：

```
StoryPlanner → Scene List → foreach Scene (ScenePipeline)
  → ChapterConsistency → ChapterSummarizer → ChapterFactsAggregator → ChapterMemoryUpdater
```

需要：

- **WorkflowEngine**：管理 Workflow 状态机，支持暂停/恢复/回滚
- **ChapterSummary**：生成三级摘要（one_line / one_paragraph / one_page）
- **ChapterFactsAggregator**：聚合所有 Scene 的 facts，去重合并
- **ChapterMemoryUpdater**：更新 Chapter 级记忆

UI 上实现"一键生成整章"按钮，显示进度条和各步骤状态。

## Acceptance criteria

- [ ] 前端有一键生成整章按钮
- [ ] WorkflowEngine 按序执行各步骤
- [ ] 步骤失败时可回滚（不留下半成品）
- [ ] 章节相关字段（summary, consistency, chapter_facts）正确填充
- [ ] 进度实时反馈给前端

## Blocked by

- [场景数据管道](.scratch/scene-data-pipeline/008-scene-data-pipeline.md)
- [StoryPlanner Skill](.scratch/story-planner/011-story-planner.md)