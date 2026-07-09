---
title: 章节详情页
status: done
labels:
  - ready-for-human
created: 2026-07-09
---

## What to build

创建一个独立的章节详情页，展示章节的摘要、一致性评分、facts 概览等信息。

当前章节详情页就是场景编辑器页面，没有章节级别的概览信息。

需要：

1. **章节概览页面**（新路由 `/novels/[id]/chapters/[chapterId]/overview`）：
   - 章节标题和基本信息
   - 三级摘要（one_line / one_paragraph / one_page）
   - 一致性评分（颜色编码 + 问题列表）
   - 章节 facts 概览（relationship_changes、world_changes 等）
   - 场景列表（带规划 goal 和状态）

2. **Tab 切换**：章节详情页内可切换"概览"和"场景编辑器"视图

3. **章节操作**：
   - "一键生成整章"按钮（已存在，强化展示）
   - "重新生成摘要"按钮
   - "查看一致性报告"按钮

4. **编辑章节规划**：
   - 显示和编辑 chapter.planning（goal、theme）
   - 显示 scene_plan 列表

设计决策需人类确认：
- 概览页默认显示还是折叠？
- 是否需要"章节树"概览图？
- 是否需要导出功能？

## Acceptance criteria

- [ ] `/novels/[id]/chapters/[chapterId]/overview` 页面可用
- [ ] 显示三级摘要（one_line / one_paragraph / one_page）
- [ ] 显示一致性评分和问题列表
- [ ] 显示章节 facts 概览
- [ ] 可在概览页和场景编辑器之间切换
- [ ] 显示章节规划和 scene_plan 列表

## Blocked by

- [Chapter Summary 三级摘要（LLM 实现）](.scratch/chapter-workflow-completion/001-chapter-summary-llm.md)
- [Consistency Score 计算](.scratch/chapter-workflow-completion/002-consistency-score.md)
- [ChapterFactsAggregator](.scratch/chapter-workflow-completion/003-facts-aggregator.md)