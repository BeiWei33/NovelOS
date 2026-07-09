---
title: 非 OpenAI-compatible Provider 支持
status: open
labels:
  - ready-for-agent
created: 2026-07-09
---

## What to build

实现对非 OpenAI-compatible API 的 Provider 支持，包括 Anthropic Claude、Ollama native API、Google Gemini 等。

这些 provider 不兼容 OpenAI 的 chat completions 格式，需要各自实现 adapter：

1. **AnthropicAdapter** — 使用 `anthropic` Python SDK
   - 支持 Claude Opus、Sonnet、Haiku 系列模型
   - 处理 Anthropic 特有的 messages 格式（system 参数分离、content blocks）
   - 配置：`ANTHROPIC_API_KEY`

2. **OllamaNativeAdapter** — 使用 Ollama native API (`/api/chat` 或 `/api/generate`)
   - 支持本地模型，无需 API key
   - 处理 Ollama 的流式/非流式响应格式
   - 配置：`OLLAMA_HOST`（默认 `http://localhost:11434`）

3. **统一的 ProviderAdapter 接口验证** — 确保所有 adapter 的 `chat()` 方法行为一致：
   - 输入：`messages: list[dict]`（OpenAI 格式）
   - 输出：`str`（生成的文本）
   - 在 adapter 内部完成格式转换

可选扩展（不在本 issue 范围）：
- Google Gemini adapter
- AWS Bedrock adapter
- Azure OpenAI adapter

不在此 issue 范围内：
- 配置化注册机制 —— #3
- 前端 UI —— #5

## Acceptance criteria

- [ ] `AnthropicAdapter` 实现并注册，可通过 `provider="anthropic"` 调用
- [ ] `OllamaNativeAdapter` 实现并注册，可通过 `provider="ollama-native"` 调用
- [ ] `requirements.txt` 新增 `anthropic` 依赖
- [ ] Anthropic API key 配置 `ANTHROPIC_API_KEY`
- [ ] Ollama host 配置 `OLLAMA_HOST`
- [ ] 所有 adapter 的 `chat()` 接受标准 messages 格式并返回字符串
- [ ] 错误处理：API 不可用时给出清晰错误信息

## Blocked by

- [Provider Adapter 抽象层完善](.scratch/multi-provider-support/001-provider-adapter-refactor.md)