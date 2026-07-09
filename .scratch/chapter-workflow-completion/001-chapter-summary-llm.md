---
title: Chapter Summary 三级摘要（LLM 实现）
status: done
labels:
  - ready-for-agent
created: 2026-07-09
completed: 2026-07-09
---

## Parent

- [ChapterWorkflow 全流程](.scratch/chapter-workflow/012-chapter-workflow.md)

## What to build

替换当前 ChapterWorkflow 中 `_step_summary()` 的简单拼接逻辑，改为 LLM 生成真正的三级摘要。

当前实现：简单拼接每个 Scene 的第一个 block 的前 100 字符作为 one_line，前 3 个 block 拼接为 one_paragraph，全部拼接为 one_page。

需要实现：

1. **ChapterSummary 新 Skill**（或复用现有 SummaryExtractor）：
   - 输入：Chapter 下所有 Scene 的 document + scene_plan
   - 输出：三级摘要
     - `one_line`（20-50 字）：一句话概括本章
     - `one_paragraph`（100-200 字）：一段话概述
     - `one_page`（500-800 字）：完整章节摘要

2. **集成到 ChapterWorkflow**：替换 `_step_summary()` 中的简单拼接逻辑

3. **API 端点复用**：`POST /skills/summarize-chapter/{chapter_id}` 可单独调用重新生成摘要

4. **前端展示**：在章节详情页显示三级摘要（展开/折叠 UI）

不在此 issue 范围内：
- ChapterFactsAggregator —— #003
- ChapterMemoryUpdater —— #004

## Acceptance criteria

- [ ] LLM 生成三级摘要替代当前拼接逻辑
- [ ] `one_line` 控制在 20-50 字
- [ ] `one_paragraph` 控制在 100-200 字
- [ ] `one_page` 控制在 500-800 字
- [ ] API 端点可单独调用重新生成摘要
- [ ] 前端章节详情页显示三级摘要（默认折叠，可展开）

## Blocked by

None - can start immediately