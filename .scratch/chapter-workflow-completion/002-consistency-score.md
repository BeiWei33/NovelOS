---
title: Consistency Score 计算
status: done
labels:
  - ready-for-agent
created: 2026-07-09
completed: 2026-07-09
---

## Parent

- [ChapterWorkflow 全流程](.scratch/chapter-workflow/012-chapter-workflow.md)

## What to build

基于 ConsistencyChecker 输出的 issues 列表计算真实的一致性评分，替代当前写死的 `score: 100`。

当前实现：`chapter.consistency = {"score": 100, "issues": [], "fixed": []}` — 始终满分。

需要实现：

1. **Score 计算公式**：
   - 基础分 100
   - 每个 error 级别 issue 扣 20 分
   - 每个 warning 级别 issue 扣 5 分
   - 最低 0 分
   - 已修复的 issue 不扣分

2. **集成点**：
   - Quality Pipeline 执行后计算 score
   - ChapterWorkflow `_step_summary()` 中写入真实 score
   - `POST /skills/polish/{scene_id}` 单场景润色后也计算

3. **前端展示**：
   - 场景编辑器中显示一致性评分（颜色编码：绿 > 80，黄 50-80，红 < 50）
   - 章节详情页显示聚合评分

4. **历史追踪**：
   - 每次评分记录到 `scene.body_history.consistency_score`（可选，延后实现）

不在此 issue 范围内：
- ConsistencyChecker 本身的改进（已有）
- ChapterFactsAggregator —— #003

## Acceptance criteria

- [ ] Score 基于 issue 数量和 severity 计算
- [ ] 每个 error 扣 20 分，每个 warning 扣 5 分
- [ ] Quality Pipeline 执行后自动计算并写入
- [ ] ChapterWorkflow 中写入真实 score
- [ ] 前端显示颜色编码的一致性评分
- [ ] 单场景润色后也更新评分

## Blocked by

None - can start immediately