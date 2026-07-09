---
title: 默认模型切换为 GLM-5.2
status: open
labels:
  - ready-for-agent
created: 2026-07-09
---

## Parent

- [DeepSeek Adapter 实现](.scratch/multi-provider-support/002-deepseek-adapter.md)

## What to build

将系统默认模型从 OpenAI GPT-4o 切换为 GLM-5.2，同时支持批量设置全局默认和 per-skill 单独设置。

涉及改动点：

1. **全局默认值**（批量设置）：
   - `core/types.py` 中 `ExecutionProfile` 默认值：
     - `provider: str = "deepseek"`（原 `"openai"`）
     - `model: str = "glm-5.2-v4-flash"`（原 `"gpt-4o"`）
   - 所有未显式指定 profile 的 Skill 自动使用此默认值

2. **Per-Skill 单独设置**（可选覆盖）：
   - 在 `profiles.yaml` 中支持 per-skill 配置（依赖 #004 ExecutionProfile 配置化）
   - 示例：
     ```yaml
     profiles:
       default:
         provider: glm-5.2
         model: deepseek-v4-flash
       scene-writer:
         provider: glm-5.2
         model: glm-5.2-flash
         temperature: 0.7
       consistency-checker:
         provider: glm-5.2
         model: deepseek-v4-flash
         temperature: 0.2
     ```

3. **环境变量支持**：
   - `DEFAULT_PROVIDER=glm-5.2`
   - `DEFAULT_MODEL=glm-5.2-v4-flash`
   - 环境变量优先级最高，可覆盖 YAML 配置

4. **配置更新**：
   - `.env.example` 中添加 DeepSeek 配置示例
   - 文档说明如何切换默认模型

不在此 issue 范围内：
- GLM-5.2 Adapter 实现（已有）
- 前端模型选择 UI

## Acceptance criteria

- [ ] `ExecutionProfile` 默认值改为 `provider="glm-5.2"`, `model="glm-5.2-flash"`
- [ ] 所有未指定 profile 的 Skill 自动使用 DeepSeek
- [ ] 环境变量 `DEFAULT_PROVIDER` / `DEFAULT_MODEL` 可覆盖默认值
- [ ] `.env.example` 包含 GLM-5.2 配置示例
- [ ] 文档更新说明如何切换默认模型

## Blocked by

- [DeepSeek Adapter 实现](.scratch/multi-provider-support/002-deepseek-adapter.md)