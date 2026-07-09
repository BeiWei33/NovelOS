---
title: Chapter CRUD + 前端导航
status: done
labels:
  - ready-for-agent
created: 2026-07-08
completed: 2026-07-09
---

## What to build

实现 Chapter 的完整 CRUD 流程，并构建小说详情页的章节导航。

后端已有 `chapters.py` 路由和 `crud.py` 中的对应函数。前端需要：

- 小说详情页：左侧章节列表（序号 + 标题），右侧内容区
- 新建章节：自动分配 order，输入标题
- 点击章节在右侧显示章节详情（场景列表占位）
- 删除章节

## Acceptance criteria

- [ ] 进入小说详情页，左侧显示章节列表（空状态提示）
- [ ] 新建章节按钮，输入标题后创建，列表自动刷新
- [ ] 点击章节，右侧显示章节详情（摘要/一致性/事实等 JSON 展示 + 场景列表空占位）
- [ ] 删除章节按钮，确认后删除并刷新

## Blocked by

- [Novel CRUD](.scratch/novel-crud/002-novel-crud.md)