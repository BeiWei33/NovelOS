---
title: 自定义 Provider 注册机制
status: open
labels:
  - ready-for-agent
created: 2026-07-09
---

## What to build

实现配置驱动的 Provider 注册机制，使用户能够通过 YAML 文件或环境变量注册任意 OpenAI-compatible 的 LLM endpoint（如 Ollama、vLLM、自建代理、其他云服务商）。

当前系统只有 OpenAI 和 DeepSeek 两个 provider 需要硬编码在代码中。用户可能需要：
- 使用本地 Ollama（`http://localhost:11434/v1`）
- 使用 vLLM / TGI 自托管模型
- 使用其他 OpenAI-compatible API（如 Moonshot、通义千问等）

实现方式：

1. **`providers.yaml` 配置格式**（可选）：
```yaml
providers:
  ollama:
    base_url: http://localhost:11434/v1
    api_key: ollama  # Ollama 不需要真实 key
    default_model: llama3
  moonshot:
    base_url: https://api.moonshot.cn/v1
    api_key: ${MOONSHOT_API_KEY}
    default_model: moonshot-v1-8k
```

2. **环境变量驱动**（备选/优先）：
```
PROVIDER_OLLAMA_BASE_URL=http://localhost:11434/v1
PROVIDER_OLLAMA_API_KEY=ollama
PROVIDER_OLLAMA_DEFAULT_MODEL=llama3
```

3. **在 `main.py` lifespan 或 `ProviderRouter` 初始化时** 读取配置并注册所有 provider

4. **OpenAI-compatible adapter 工厂** — 给定 ProviderConfig，生成一个可用的 adapter 实例

不在此 issue 范围内：
- 非 OpenAI-compatible 的 provider（如 Anthropic native SDK）—— #6
- ExecutionProfile 配置化 —— #4
- 前端 UI —— #5

## Acceptance criteria

- [ ] `providers.yaml` 存在时，系统自动注册其中定义的所有 provider
- [ ] 环境变量 `PROVIDER_<NAME>_BASE_URL` 格式可注册 provider（无 YAML 时）
- [ ] 注册的 provider 可通过 `ExecutionProfile(provider="ollama", model="llama3")` 调用
- [ ] 无效配置（缺少 base_url）在启动时报错，而非运行时
- [ ] `router.list_providers()` 返回所有已注册的 provider 名称
- [ ] 文档说明如何添加自定义 provider

## Blocked by

- [Provider Adapter 抽象层完善](.scratch/multi-provider-support/001-provider-adapter-refactor.md)