---
title: StoryPlanner 知识注入验证与完善
status: open
labels:
  - ready-for-agent
created: 2026-07-09
---

## Parent

- [StoryPlanner Skill](.scratch/story-planner/011-story-planner.md)

## What to build

验证并完善 `build_story_planner_context` 函数，确保 StoryPlanner 在规划场景时正确注入角色状态、世界观、风格等知识。

当前 StoryPlanner 规划场景时，需要从 Knowledge Layer 读取：
- `scene_history` — 已写场景的历史
- `character_state` — 角色当前状态
- `world_state` — 世界观状态

需要实现：

1. **验证当前实现**：
   - 检查 `build_story_planner_context` 是否实际调用了 Knowledge Layer retrievers
   - 检查返回的 context 是否包含角色、世界观等结构化数据
   - 如果缺失，补充调用

2. **Context 结构标准化**：
```yaml
context:
  goal: "..."
  theme: "..."
  chapter_summary: "..."      # 前几章摘要
  characters:
    - name, state, arc_summary
  world_state:
    - key facts
  recent_events:
    - type, actor, summary
```

3. **前端验证 UI**：
   - 在"规划整章"弹窗中显示"已加载的知识"概览
   - 显示角色数量、世界观关键设定等（帮助用户确认知识是否正确注入）

不在此 issue 范围内：
- Knowledge Layer 本身的改进（已有）
- SceneWriter context 改进

## Acceptance criteria

- [ ] `build_story_planner_context` 验证通过：正确注入角色状态和世界观知识
- [ ] 如果缺失，补充 retriever 调用
- [ ] Context 结构标准化，包含 characters、world_state、recent_events
- [ ] 前端"规划整章"弹窗显示已加载的知识概览
- [ ] 单元测试验证 context 构建

## Blocked by

- [Knowledge Layer Retriever](.scratch/knowledge-layer/009-knowledge-layer.md)
- [StoryPlanner Skill](.scratch/story-planner/011-story-planner.md)