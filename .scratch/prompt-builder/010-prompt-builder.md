---
title: Prompt Builder & Context Assembler
status: open
labels:
  - ready-for-agent
created: 2026-07-08
---

## What to build

实现四层 Prompt 系统：

1. **SkillManifest**（已有 `core/types.py` 中的 `SkillManifest` dataclass）
2. **ContextAssembler**：根据 Manifest 的 `knowledge` 和 `requires` 声明，调用对应的 Retriever 获取 KnowledgeObject，组装成 Context 切片
3. **Template**：每个 Skill 一个 Jinja2 模板，定义 prompt 结构
4. **Builder**：将 Context + Template 渲染为最终 prompt，发送给 LLM

核心约束：
- 最终 prompt 控制在 2000 token 以内
- Context 按需加载，不污染（只发当前 Skill 需要的切片）
- 无万能 Prompt

## Acceptance criteria

- [ ] ContextAssembler 根据 Manifest 声明自动选择 Retriever
- [ ] 每个 Skill 有独立的 Template 文件
- [ ] Builder 渲染后最终 prompt 长度可配置上限
- [ ] Context 切片可独立开关（DEBUG 模式打印每片 token 数）
- [ ] 重构 SceneWriter Skill 使用本 Prompt 系统

## Blocked by

- [Knowledge Layer Retriever](.scratch/knowledge-layer/009-knowledge-layer.md)