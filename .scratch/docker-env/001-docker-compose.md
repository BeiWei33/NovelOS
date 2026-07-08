---
title: Docker Compose 开发环境
status: open
labels:
  - ready-for-agent
created: 2026-07-08
---

## What to build

编写 `docker-compose.yml` 编排 NovelOS 开发所需的基础设施和服务：

- PostgreSQL 16（含 pgvector 扩展）
- Redis 7
- 后端 FastAPI 服务（热重载）
- 前端 Next.js 服务（热重载）

配置合理的健康检查、卷挂载、环境变量传递和启动顺序依赖。

## Acceptance criteria

- [ ] `docker compose up` 一条命令启动所有服务
- [ ] PostgreSQL 就绪，pgvector 扩展可用
- [ ] Redis 就绪
- [ ] 后端在 localhost:8000 启动，`/health` 返回 ok
- [ ] 前端在 localhost:3000 启动，页面正常渲染
- [ ] `.env.example` 提供默认配置模板

## Blocked by

None - can start immediately