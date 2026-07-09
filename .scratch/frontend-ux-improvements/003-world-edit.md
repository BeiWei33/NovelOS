---
title: World 编辑功能（CRUD 完善）
status: open
labels:
  - ready-for-agent
created: 2026-07-09
---

## What to build

补充 World 的编辑功能。当前只能创建和删除，无法编辑世界观配置。

需要：

1. **后端 `PUT /worlds/{id}`** 端点：
   - 支持更新 name、config（JSONB）
   - 只更新提供的字段，未提供的保持原值（partial update）

2. **前端编辑弹窗**：
   - 在世界观列表项上增加"编辑"按钮
   - 弹窗编辑 name 和 config：
     - 名称（input）
     - 配置（JSON 编辑器或结构化表单）
   - 保存后刷新列表

不在此 issue 范围内：
- Character 编辑（#002）
- 世界观详情页面

## Acceptance criteria

- [ ] `PUT /worlds/{id}` 端点可用，支持 partial update
- [ ] 前端世界观列表项显示"编辑"按钮
- [ ] 编辑弹窗包含名称和配置字段
- [ ] 保存后列表刷新显示更新内容
- [ ] 编辑失败时显示错误提示

## Blocked by

None - can start immediately