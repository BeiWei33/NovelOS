---
title: Provider Adapter 抽象层完善
status: done
labels:
  - ready-for-agent
created: 2026-07-09
completed: 2026-07-09
---

## What to build

重构 ProviderRouter 和 ProviderAdapter 抽象层，使系统能够动态注册多个 LLM provider adapter。

当前 `ProviderRouter` 的 `_adapters` 是硬编码字典，`OpenAIAdapter` 直接读取全局 `settings`。需要：

1. **ProviderConfig 类型** — 新增配置类型，持有一个 provider 所需的 endpoint URL、API key、默认模型等，不在 adapter 中硬引用全局 settings
2. **ProviderAdapter 注册方法** — `ProviderRouter.register(name, adapter, config)`，使 adapter 可在运行时动态注入
3. **OpenAIAdapter 改为接收 config** — 不再从全局 settings 读取 API key / base_url，而是从构造时传入的 ProviderConfig 读取
4. **保留向后兼容** — 迁移过程中确保现有 skill 调用 chain 不需要改动

不在此 issue 范围内：
- 新增其他 provider（如 GLM）——这是 #2
- 改进 ExecutionProfile —— 这是 #4
- 前端 UI 改动

## Acceptance criteria

- [ ] `ProviderConfig` dataclass 定义在 `core/types.py`，包含 `api_key`、`base_url`、`default_model`、`default_max_tokens` 字段
- [ ] `ProviderRouter.register(name, adapter_cls, config)` 可在运行时注册新 provider
- [ ] `OpenAIAdapter` 接受 `ProviderConfig` 而非从全局 `settings` 读取
- [ ] 现有所有 skill 调用 `router.execute()` 的行为不变（profile.provider == "openai" 仍正常工作）
- [ ] `router.list_providers()` 返回已注册的 provider 列表
- [ ] 所有现有测试通过

## Blocked by

None - can start immediately