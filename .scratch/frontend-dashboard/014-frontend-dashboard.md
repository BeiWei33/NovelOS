---
title: 前端 Dashboard & 导航聚合
status: done
labels:
  - ready-for-agent
created: 2026-07-08
completed: 2026-07-09
---

## What to build

打磨前端整体体验，聚合所有功能到统一的 Dashboard。

- 左侧导航树：Novel → Chapter → Scene（可展开/折叠）
- 右侧主区域根据导航切换不同视图：编辑器 / 章节详情 / 人物管理 / 世界观 / 风格
- 全局搜索：快速跳转到任意 Scene
- 快捷键：保存（Ctrl+S）、新建场景等
- 响应式布局：窄屏时侧边栏可折叠

这是一个打磨切片，不新增功能，只提升可用性。

## Acceptance criteria

- [ ] 导航树完整展示 Novel/Chapter/Scene 层级
- [ ] 点击导航节点切换对应视图
- [ ] 导航树支持拖拽排序（可选）
- [ ] Ctrl+S 保存当前场景
- [ ] 移动端侧边栏可折叠

## Blocked by

- [Character / World / Style CRUD](.scratch/character-world-style-crud/004-character-world-style-crud.md)
- [Scene Editor](.scratch/scene-editor/005-scene-editor.md)