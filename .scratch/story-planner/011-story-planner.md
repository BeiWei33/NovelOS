---
title: StoryPlanner Skill
status: open
labels:
  - ready-for-agent
created: 2026-07-08
---

## What to build

实现 StoryPlanner Skill：

- 输入：用户提供的 goal + theme（或自动从 Chapter Summary 推断）
- 输出：`scene_plan: [{goal, conflict, stakes, turning_point, ending, foreshadow}]` 
- Knowledge 需求：scene_history, character_state, world_state
- 用于 ChapterWorkflow 的第一步

前端实现"规划本场景"和"规划整章"两种模式。

## Acceptance criteria

- [ ] StoryPlanner 接收 goal/theme 输入
- [ ] 输出符合 ScenePlanning 结构的场景列表
- [ ] 单场景规划模式：填充当前 Scene 的 planning 字段
- [ ] 整章规划模式：生成 scene_plan 写入 Chapter.planning
- [ ] 使用 Prompt Builder 系统组装 prompt

## Blocked by

- [Prompt Builder & Context Assembler](.scratch/prompt-builder/010-prompt-builder.md)