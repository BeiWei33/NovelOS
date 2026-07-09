---
title: Character 详情编辑页面
status: done
labels:
  - ready-for-human
created: 2026-07-09
---

## What to build

创建独立的人物详情页，支持编辑角色的完整属性，包括性格标签、目标、恐惧、习惯、说话风格等。

当前人物只有创建弹窗（name 输入框）和列表显示，没有编辑功能。

需要：

1. **后端补充**：
   - `PUT /characters/{id}` 端点（已在 #002 中实现，此处复用）

2. **前端人物详情页**（新路由 `/novels/[id]/characters/[characterId]`）：
   - 展示所有字段并可编辑
   - 字段：
     - 姓名（input）
     - 年龄（number input）
     - 职业（input）
     - 性格标签（tag input，可添加/删除）
     - 目标（textarea）
     - 恐惧（textarea）
     - 习惯（tag input）
     - 说话风格（select 或 input）
     - 创建时间、更新时间

3. **从人物列表跳转到详情**：
   - 点击人物名称跳转到详情页
   - 编辑后返回列表，自动刷新

4. **人物弧光展示**（可选）：
   - 显示人物在小说中的出场场景列表
   - 显示人物状态变化历史（来自 character_state_projection）

设计决策需人类确认：
- 是否需要独立路由，还是直接弹窗编辑？
- 是否需要显示人物弧光？

## Acceptance criteria

- [ ] 人物详情页 `/novels/[id]/characters/[characterId]` 可用
- [ ] 所有人物字段可编辑并保存
- [ ] 从人物列表可点击跳转到详情页
- [ ] 保存后返回列表，列表自动刷新

## Blocked by

- [Character 编辑功能](.scratch/frontend-ux-improvements/002-character-edit.md)