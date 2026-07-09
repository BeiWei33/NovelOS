---
title: 前端模型选择 UI
status: done
labels:
  - ready-for-agent
created: 2026-07-09
completed: 2026-07-09
---

## What to build

在前端提供模型选择界面，让用户能够在运行 Skill 前选择使用哪个 Provider / Model。

功能包括：

1. **API 端点** — `GET /api/providers` 返回可用 provider 列表及每个 provider 支持的模型（可从配置或 provider API 获取）

2. **API 端点** — `GET /api/profiles` 返回当前所有 profile 配置

3. **Skill 执行时传入覆盖** — `POST /api/skills/scene-writer/:scene_id` 接受可选的 `profile_override` 参数：
```json
{
  "provider": "glm-5.2",
  "model": "glm-5.2-chat",
  "temperature": 0.8
}
```

4. **前端 UI 组件** — 在场景编辑器 "AI 写场景" 按钮附近添加模型选择下拉：
   - Provider 选择（OpenAI / GLM-5.2 / Ollama / ...）
   - Model 选择（根据 provider 动态更新）
   - Temperature slider（可选）
   - 记住上次选择（localStorage）

5. **全局默认设置页** — 在 Dashboard 设置中可配置默认 provider/model

需要设计决策：
- 模型列表从哪里获取？（硬编码 / provider API / 配置文件）
- 是否需要 per-novel / per-chapter 的模型偏好？

不在此 issue 范围内：
- 后端 provider/profile 配置机制 —— #3, #4
- 非 OpenAI-compatible provider —— #6

## Acceptance criteria

- [ ] `GET /api/providers` 返回可用 provider 列表
- [ ] `GET /api/profiles` 返回 profile 配置
- [ ] Skill API 支持运行时 profile 覆盖
- [ ] 场景编辑器有 Provider/Model 选择下拉
- [ ] 选择后调用 Skill 时传入覆盖的 profile
- [ ] 用户选择保存到 localStorage

## Blocked by

- [ExecutionProfile 配置化](.scratch/multi-provider-support/004-execution-profile-config.md)