---
title: 场景规划编辑器
status: open
labels:
  - ready-for-agent
created: 2026-07-09
---

## What to build

在场景编辑器中增加场景规划（planning）编辑面板，让用户可编辑场景的叙事目标、冲突、赌注、转折点、结局、伏笔。

当前场景编辑器只编辑 document blocks，没有显示/编辑 scene.planning 字段的 UI。

需要：

1. **后端 API**：`GET /scenes/{id}/planning` 和 `PUT /scenes/{id}/planning`（或复用现有 `PUT /scenes/{id}`）

2. **前端规划面板**：
   - 在场景编辑器右侧或底部增加"场景规划"折叠面板
   - 编辑字段：
     - 目标（goal）— textarea
     - 冲突（conflict）— textarea
     - 赌注（stakes）— textarea
     - 转折点（turning_point）— textarea
     - 结局（ending）— textarea
     - 伏笔（foreshadow）— textarea
   - 保存后更新 scene.planning

3. **"AI 规划"按钮**：
   - 调用 `POST /skills/plan-scene/{scene_id}` 用 AI 自动填充
   - 填充后刷新规划面板

4. **规划状态展示**：
   - 场景列表中显示规划 goal 作为场景标签
   - 未规划的场景显示"未规划"标签

不在此 issue 范围内：
- 导航树（#005）
- AI 生成入口（#004）

## Acceptance criteria

- [ ] 场景编辑器右侧/底部显示规划折叠面板
- [ ] 6 个规划字段可编辑和保存
- [ ] "AI 规划"按钮调用 StoryPlanner 自动填充
- [ ] 场景列表中显示规划 goal 作为标签
- [ ] 未规划的场景显示"未规划"标记

## Blocked by

None - can start immediately