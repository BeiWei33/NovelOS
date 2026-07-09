---
title: 错误存储到后端数据库
status: done
labels:
  - ready-for-agent
created: 2026-07-09
---

## What to build

将前端上报的错误持久化到数据库，支持后续查询和分析。

需要：

1. **`frontend_error` 表**：
```sql
CREATE TABLE frontend_error (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  type VARCHAR(50) NOT NULL,
  severity VARCHAR(20) NOT NULL,
  message TEXT NOT NULL,
  stack TEXT,
  fingerprint VARCHAR(64) NOT NULL,  -- 用于去重
  context JSONB NOT NULL,
  user_id UUID,
  ip_address VARCHAR(45),
  user_agent TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_frontend_error_created_at ON frontend_error(created_at DESC);
CREATE INDEX idx_frontend_error_fingerprint ON frontend_error(fingerprint);
CREATE INDEX idx_frontend_error_type ON frontend_error(type);
```

2. **Alembic 迁移** — 创建表

3. **写入逻辑** — API 端点接收后写入数据库

4. **自动清理** — 保留最近 30 天错误，过期自动删除
   - 可通过 cron job 或 PostgreSQL TTL 实现

不在此 issue 范围内：
- API 端点 —— #002
- 查看界面 —— #004

## Acceptance criteria

- [ ] `frontend_error` 表通过 Alembic 迁移创建
- [ ] `POST /api/errors` 将错误写入数据库
- [ ] 索引支持按时间、fingerprint、type 查询
- [ ] 自动清理 30 天前的错误记录
- [ ] 写入时不阻塞响应（可考虑异步写入）

## Blocked by

- [错误上报 API 端点](.scratch/frontend-error-logging/002-error-report-api.md)