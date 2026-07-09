---
title: 错误上报 API 端点
status: done
labels:
  - ready-for-agent
created: 2026-07-09
---

## What to build

在后端新增 API 端点，接收前端上报的错误日志。

需要：

1. **`POST /api/errors` 端点** — 接收前端错误上报
   - 请求体：StructuredError 对象
   - 认证：可选（允许未认证用户上报，用于调试登录问题）
   - 响应：`{ "received": true }`

2. **请求体验证** — Pydantic schema 校验错误结构

3. **速率限制** — 防止错误风暴导致后端过载
   - 同一 IP 每分钟最多 100 条错误
   - 同一 fingerprint 每分钟最多 10 条（去重）

4. **敏感信息过滤** — 移除可能包含的 token、密码等

不在此 issue 范围内：
- 前端捕获逻辑 —— #001
- 数据库存储 —— #003

## Acceptance criteria

- [ ] `POST /api/errors` 端点可接收错误上报
- [ ] Pydantic schema 校验请求体结构
- [ ] 速率限制：同一 IP 每分钟最多 100 条
- [ ] 错误 fingerprint 去重（同一错误不重复写入）
- [ ] 敏感字段（password, token, api_key）自动脱敏
- [ ] 无认证或认证失败时仍可上报（用于调试登录问题）

## Blocked by

- [前端错误捕获与结构化](.scratch/frontend-error-logging/001-frontend-error-capture.md)