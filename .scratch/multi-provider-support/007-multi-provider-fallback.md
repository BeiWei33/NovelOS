---
title: 多 Provider Fallback 机制
status: done
labels:
  - ready-for-agent
created: 2026-07-09
completed: 2026-07-09
---

## What to build

实现多 provider 容错与 fallback 机制，当主 provider 不可用时自动切换到备用 provider。

场景：
- OpenAI API 超时或限流 → 自动切换到 DeepSeek
- 主 provider 账号余额不足 → 使用备用 provider
- 网络问题导致特定 provider 不可达 → 尝试其他 provider

实现方式：

1. **FallbackPolicy 配置**：
```yaml
fallback:
  enabled: true
  chains:
    default:
      - openai
      - glm-5.2
      - ollama
    premium:
      - openai
      - anthropic
```

2. **ProviderRouter 增强**：
   - `execute_with_fallback(messages, profile, fallback_chain)` 方法
   - 捕获 adapter 抛出的异常（超时、rate limit、API error）
   - 按 fallback chain 顺序重试下一个 provider
   - 记录 fallback 事件到日志

3. **错误分类**：
   - 可重试错误：超时、rate limit、5xx 错误
   - 不可重试错误：认证失败、无效请求 —— 直接抛出，不触发 fallback

4. **监控与告警**：
   - 记录每次 fallback 事件
   - 可选：发送通知（webhook / Slack）

5. **Scene.provenance 记录**：
   - 若发生 fallback，记录实际使用的 provider/model

不在此 issue 范围内：
- 执行 profile 配置化 —— #4
- 前端 UI —— #5

## Acceptance criteria

- [ ] `FallbackPolicy` 配置支持定义 fallback chain
- [ ] `ProviderRouter.execute_with_fallback()` 实现自动重试逻辑
- [ ] 只有可重试错误触发 fallback，认证错误直接抛出
- [ ] Fallback 事件记录到日志
- [ ] Scene.provenance 记录实际使用的 provider
- [ ] 可通过配置开关启用/禁用 fallback

## Blocked by

- [ExecutionProfile 配置化](.scratch/multi-provider-support/004-execution-profile-config.md)