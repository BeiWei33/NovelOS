---
title: 去AI味 + 一致性检查 Pipeline
status: done
labels:
  - ready-for-agent
created: 2026-07-08
completed: 2026-07-09
---

## What to build

在 SceneWriter 输出初稿后，串行执行两个质量步骤：

1. **SceneEditor（去AI味）**：带规则集的 AI 编辑 Skill，清除 AI 写作痕迹
   - Rule001：禁止总结情绪（show don't tell）
   - Rule002：禁止解释主题
   - Rule003：动作替代心理描写
   - 输出为 Patch（增量修改），不重写全文

2. **ConsistencyChecker**：检查场景内容的一致性
   - 人物年龄/名字/标签是否错误
   - 时间线是否冲突
   - 世界观规则是否违反
   - 输出 issues 列表 + 自动修复建议

UI 上实现"一键润色"按钮，触发 Pipeline 并逐步展示进度。

## Acceptance criteria

- [ ] SceneEditor Skill 加载去AI味规则集
- [ ] Editor 输出 Patch（增量修改），而非全文重写
- [ ] 场景编辑器中有"润色"按钮，触发去AI味 + 一致性检查
- [ ] 一致性检查结果（issues/fixed/warnings）写入 scene.body_history
- [ ] 前端展示检查结果摘要

## Blocked by

- [SceneWriter Skill](.scratch/scene-writer-skill/006-scene-writer-skill.md)