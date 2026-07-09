---
title: 场景数据管道 (Artifact + Projection)
status: done
labels:
  - ready-for-agent
created: 2026-07-08
completed: 2026-07-09
---

## What to build

场景冻结（或编辑后）自动触发数据管道，分两步运行：

1. **ArtifactService**：从 SceneDocument 提取结构化知识
   - facts（事实陈述）
   - narrative_events（叙事事件序列）
   - summary（场景摘要）
   - keywords（关键词列表）
   - emotion_profile（情绪曲线）
   - entities（出现的实体）
   - foreshadow_hints（伏笔线索）
   - timeline_deltas（时间线增量）
   - embedding（语义向量，用于 RAG）

2. **ProjectionBuilder**：从 Artifacts 重建读模型
   - fact_projection
   - character_state_projection
   - relationship_projection
   - timeline_projection
   - retrieval_projection

确保 version 检查：如果 scene.version 与 artifact.scene_version 不匹配，则 artifacts 过期需要重建。

## Acceptance criteria

- [ ] 场景保存后自动/手动触发 ArtifactService
- [ ] 提取的所有字段写入 scene_artifact 表
- [ ] ProjectionBuilder 从 artifact 重建 5 张投影表
- [ ] Version 检查机制：scene.version 变化时标记 artifacts 为 stale
- [ ] UI 上显示"知识状态"：已生成 / 过期 / 未生成

## Blocked by

- [去AI味 + 一致性检查 Pipeline](.scratch/quality-pipeline/007-quality-pipeline.md)