---
title: ExecutionProfile 配置化
status: open
labels:
  - ready-for-agent
created: 2026-07-09
---

## What to build

将硬编码在各 Skill 中的 `ExecutionProfile` 改为从配置文件读取，实现 "Switch models by changing YAML only" 的设计目标。

当前每个 Skill 都有类似这样的硬编码：
```python
SKILL_PROFILE = ExecutionProfile(
    provider="openai",
    model="gpt-4o",
    temperature=0.7,
    max_tokens=2048,
)
```

需要改为：

1. **`profiles.yaml` 配置格式**：
```yaml
profiles:
  story-planner:
    provider: openai
    model: gpt-4o
    temperature: 0.7
    max_tokens: 4096
  scene-writer:
    provider: glm-5.2
    model: glm-5.2-chat
    temperature: 0.7
    max_tokens: 8192
  scene-editor:
    provider: openai
    model: gpt-4o
    temperature: 0.3
    max_tokens: 4096
  consistency-checker:
    provider: openai
    model: gpt-4o
    temperature: 0.2
    max_tokens: 2048
```

2. **ProfileRegistry** — 在启动时加载 YAML，按 role 名查找 profile

3. **Skill 改为通过 role 查询 profile** — `profile = registry.get("scene-writer")` 而非硬编码常量

4. **环境变量覆盖支持** — 如 `PROFILE_SCENE_WRITER_MODEL=glm-5.2-chat` 可覆盖 YAML 中的值

5. **向后兼容** — 若无 YAML 配置，使用内置默认值（与现有硬编码一致）

不在此 issue 范围内：
- 前端 UI 选择模型 —— #5
- Multi-provider fallback —— #7

## Acceptance criteria

- [ ] `profiles.yaml` 存在时，Skill 从配置读取 ExecutionProfile
- [ ] `ProfileRegistry.get(role)` 返回对应 role 的 profile
- [ ] 无 YAML 时使用默认 profile（与现有硬编码一致）
- [ ] 环境变量 `PROFILE_<ROLE>_<FIELD>` 可覆盖 YAML 配置
- [ ] 修改 `profiles.yaml` 后重启服务生效，无需改代码
- [ ] 文档说明如何配置 per-skill 的模型

## Blocked by

- [自定义 Provider 注册机制](.scratch/multi-provider-support/003-custom-provider-registration.md)