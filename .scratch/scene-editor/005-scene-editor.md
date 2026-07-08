---
title: Scene Editor (TipTap + Domain AST)
status: open
labels:
  - ready-for-agent
created: 2026-07-08
---

## What to build

构建核心场景编辑器。后端已有 Scene CRUD 路由和 `crud.py`。

最重要的切片：实现 TipTap 编辑器直接读写 NovelOS 的 SceneDocument（Domain AST）。

需要：

- 实现自定义 TipTap Node 类型：每种 block type（narration, dialogue, description, inner_monologue, emotion, letter, phone_message, flashback, system_message）渲染为不同样式
- editor 从 `GET /scenes/:id` 加载 blocks，编辑后 `PUT /scenes/:id` 保存
- 块级操作：添加块、删除块、切换块类型
- 场景规划元数据编辑（goal, conflict, stakes 等）
- 版本号显示、保存时 version+1
- 场景列表侧边栏（在章节详情内）

## Acceptance criteria

- [ ] 在章节详情页内，左侧显示该章节的场景列表
- [ ] 点击场景进入编辑器，按 block type 渲染不同样式
- [ ] 可编辑文本内容、切换 block type、添加/删除 block
- [ ] 保存按钮调用 PUT API，version 自增
- [ ] 场景规划元数据可在编辑器中编辑
- [ ] 新增场景按钮

## Blocked by

- [Chapter CRUD + 前端导航](.scratch/chapter-crud/003-chapter-crud.md)