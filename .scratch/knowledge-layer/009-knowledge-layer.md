---
title: Knowledge Layer Retriever
status: open
labels:
  - ready-for-agent
created: 2026-07-08
---

## What to build

实现 Knowledge Layer 的多个 Retriever。它们是 Prompt Builder 的数据源，读取 Projection 表，返回 `KnowledgeObject`。

需要实现：

- **SceneRetriever**：基于 embedding 向量相似度检索相关场景（用于 Writer Skill 的场景历史）
- **FactRetriever**：基于 SQL 查询事实投影表，按 actor/target 过滤
- **CharacterRetriever**：从 character_state_projection 查询角色当前状态和弧光摘要
- **RelationshipRetriever**：查询关系投影表，获取角色间信任/情感/恐惧分数
- **TimelineRetriever**：按章节/场景/序号查询时间线投影

所有 Retriever 统一返回 `KnowledgeObject`（type + payload + confidence）。

## Acceptance criteria

- [ ] 每个 Retriever 独立实现，可单独调用
- [ ] 统一返回 KnowledgeObject 结构
- [ ] SceneRetriever 使用 pgvector 做相似度搜索
- [ ] Retriever 按 confidence 排序结果
- [ ] 单元测试覆盖每个 Retriever 的基本查询

## Blocked by

- [场景数据管道](.scratch/scene-data-pipeline/008-scene-data-pipeline.md)