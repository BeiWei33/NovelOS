---
title: GLM-5.2 Adapter 实现
status: done
labels:
  - ready-for-agent
created: 2026-07-09
completed: 2026-07-09
---

## What to build

实现 DeepSeek Adapter，支持通过 DeepSeek API 调用 DeepSeek 模型（如 glm-5.2-chat、glm-5.2-reasoner）。

GLM-5.2 兼容 OpenAI 的 chat completions 接口格式，因此 `GLM-5.2Adapter` 可以复用 `OpenAIAdapter` 的实现逻辑，仅需：

1. 在 `Settings` 中添加 `DEEPSEEK_API_KEY` 和 `DEEPSEEK_BASE_URL`（默认 `https://api.glm-5.2.com`）
2. 新建 `DeepSeekAdapter(ProviderAdapter)` — 接受 `ProviderConfig`，使用 `openai` SDK 但指向 GLM-5.2 endpoint
3. 在 `app startup` 或 `ProviderRouter` 初始化时注册 `"glm-5.2"` provider
4. 在 `.env.example` 和文档中记录 DeepSeek 配置方式

意图：用户设置好 API key 后，在 ExecutionProfile 中将 provider 设为 `"deepseek"`、model 设为 `"glm-5.2-chat"` 即可使用。

不在此 issue 范围内：
- 抽象层重构（依赖 #1）
- 用户自定义 provider 注册（#3）
- ExecutionProfile 配置化（#4）

## Acceptance criteria

- [ ] `.env` 中设置 `DEEPSEEK_API_KEY` 后，provider 名 `"deepseek"` 可路由到 GLM-5.2Adapter
- [ ] `DEEPSEEK_BASE_URL` 可自定义（默认 `https://api.deepseek.com`）
- [ ] `ExecutionProfile(provider="glm-5.2", model="glm-5.2-chat")` 调用成功返回 LLM 响应
- [ ] 非流式 chat completions 正常工作（NovelOS 目前只用非流式）
- [ ] 错误处理：API key 为空时给出清晰错误信息
- [ ] `.env.example` 新增 DeepSeek 配置示例

## Blocked by

- [Provider Adapter 抽象层完善](.scratch/multi-provider-support/001-provider-adapter-refactor.md)