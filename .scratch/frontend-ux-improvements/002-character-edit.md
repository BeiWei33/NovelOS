---
title: Character 编辑功能（CRUD 完善）
status: done
labels:
  - ready-for-agent
created: 2026-07-09
---

## What to build

补充 Character 的编辑功能。当前只能创建和删除，无法编辑已有角色的属性。

需要：

1. **后端 `PUT /characters/{id}`** 端点：
   - 支持更新 name、age、occupation、personality、goal、fear、habit、speech_style
   - 只更新提供的字段，未提供的字段保持原值（partial update）

2. **前端编辑弹窗**：
   - 在角色列表项上增加"编辑"按钮
   - 弹窗显示所有可编辑字段：
     - 姓名（input）
     - 年龄（number input）
     - 职业（input）
     - 性格标签（tag input，可添加/删除）
     - 目标（textarea）
     - 恐惧（textarea）
     - 习惯（tag input）
     - 说话风格（select 或 input）
   - 保存后刷新列表

不在此 issue 范围内：
- World 编辑（#003）
- 角色详情页面（更复杂的角色管理）

## Acceptance criteria

- [ ] `PUT /characters/{id}` 端点可用，支持 partial update
- [ ] 前端角色列表项显示"编辑"按钮
- [ ] 编辑弹窗包含所有角色字段
- [ ] 保存后列表刷新显示更新内容
- [ ] 编辑失败时显示错误提示

## Blocked by

None - can start immediately