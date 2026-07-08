---
title: 风格驱动的编辑器配置
status: open
labels:
  - ready-for-agent
created: 2026-07-08
---

## What to build

将 Novel 的 Style Profile 应用到场景编辑器和 AI 写作过程中。

- 编辑器根据 Style Profile 提供视觉提示（例如 dialog_ratio=0.65 时显示对话比例指示器）
- SceneWriter 的 prompt 中自动注入 Style Profile JSON
- 前端提供 Style Profile 编辑表单（各维度的滑块/选择器）

Style Profile 维度：
- dialog_ratio（对话占比 0-1）
- emotion（implicit / explicit）
- sentence（short / long / mixed）
- description（concrete / abstract）
- psychology（low / high）
- humor（dry / warm / dark / none）
- pace（fast / slow / varied）

## Acceptance criteria

- [ ] Style Profile 可视化编辑表单
- [ ] 编辑器状态栏显示"当前风格"及关键指标
- [ ] SceneWriter 自动加载 Style 注入 prompt
- [ ] 切换风格后编辑器视觉反馈有变化

## Blocked by

- [Scene Editor](.scratch/scene-editor/005-scene-editor.md)
- [Character / World / Style CRUD](.scratch/character-world-style-crud/004-character-world-style-crud.md)