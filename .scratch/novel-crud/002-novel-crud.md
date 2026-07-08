---
title: Novel CRUD
status: open
labels:
  - ready-for-agent
created: 2026-07-08
---

## What to build

实现 Novel 的完整 CRUD 流程，覆盖后端到前端。

后端已有 `novels.py` 路由和 `crud.py` 中的对应函数。需要验证其正确性，然后构建前端页面：

- 小说列表页（显示所有小说，提供创建、删除操作）
- 创建小说表单（输入标题即可）
- 删除确认

使用 Tailwind 构建简洁 UI。

## Acceptance criteria

- [ ] 前端列表页显示所有小说，按更新时间倒序
- [ ] 点击"新建"按钮弹出创建表单，输入标题后确认，列表自动刷新
- [ ] 每篇小说显示删除按钮，点击后确认删除，列表自动刷新
- [ ] 点击小说标题可进入详情页（暂时显示"章节列表"空白占位）

## Blocked by

None - can start immediately