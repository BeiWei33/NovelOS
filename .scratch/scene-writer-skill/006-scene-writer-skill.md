---
title: SceneWriter Skill
status: open
labels:
  - ready-for-agent
created: 2026-07-08
---

## What to build

实现第一个 AI Skill：SceneWriter。覆盖从 SkillManifest 到 LLM 调用到结果写回 Scene 的完整链路。

需要：

- 定义 `SceneWriter` 的 `SkillManifest`（role: scene-writer, knowledge: scene_history, world_state, character_state, rewrite_samples）
- 实现 `Skill` 基类和 `SceneWriterSkill` 子类
- 实现 `ExecutionProfile` 从 YAML/配置读取（provider, model, temperature）
- 实现 OpenAI LLM 调用适配器
- 在 UI 场景编辑器中添加"AI 写场景"按钮
- 调用后端 API → 执行 Skill → 将生成的 SceneDocument 写回 → 刷新编辑器

## Acceptance criteria

- [ ] SceneWriter SkillManifest 可被系统正确加载
- [ ] 场景编辑器中有"AI 写场景"按钮
- [ ] 点击后调用后端 `/skills/scene-writer/:scene_id` 端点
- [ ] Skill 从 SceneDocument、Character、World、Style 组装 prompt
- [ ] LLM 返回合法的 SceneDocument（blocks 数组）
- [ ] 结果写回 scene.document，version+1，provenance 记录执行信息
- [ ] 编辑器自动刷新显示 AI 生成的内容

## Blocked by

- [Scene Editor](.scratch/scene-editor/005-scene-editor.md)
- [Character / World / Style CRUD](.scratch/character-world-style-crud/004-character-world-style-crud.md)