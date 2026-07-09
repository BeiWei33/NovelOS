---
title: Rewrite Samples + Embedding 检索
status: done
labels:
  - ready-for-agent
created: 2026-07-08
completed: 2026-07-09
---

## What to build

实现 RewriteSample 系统和 embedding 驱动的情境检索。

需要：

- 新增 `rewrite_sample` 表（input, output, tag, embedding）
- 生成 RewriteSample 的 embedding（复用 embedding 服务）
- 场景写作时：根据当前场景的意图/情绪/风格，检索 top-3 最相似的 RewriteSample，注入 Writer 的 prompt

核心价值：让 AI 参考"好例子"写作，而非只靠 prompt 指令。

## Acceptance criteria

- [ ] RewriteSample 表迁移和模型
- [ ] 创建/管理 RewriteSample 的 CRUD API
- [ ] Embedding 自动生成（存表时）
- [ ] Writer Skill prompt 中自动注入 top-3 相似样本
- [ ] 前端管理页面：添加样例、打 tag、预览 embedding

## Blocked by

- [Knowledge Layer Retriever](.scratch/knowledge-layer/009-knowledge-layer.md)