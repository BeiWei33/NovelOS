---
title: 错误查看 UI（Dashboard）
status: open
labels:
  - ready-for-human
created: 2026-07-09
---

## What to build

在 Dashboard 中新增错误日志查看界面，支持开发者/运维查看前端错误。

需要：

1. **API 端点 `GET /api/errors`**：
   - 分页查询：`?page=1&limit=50`
   - 过滤：`?type=api&severity=error&since=2026-07-01`
   - 聚合：按 fingerprint 分组统计错误数量

2. **前端页面 `/admin/errors`**：
   - 错误列表：时间倒序，显示 type、severity、message、context
   - 过滤面板：按 type、severity、时间范围筛选
   - 详情弹窗：点击查看完整 stack 和 context
   - 聚合视图：显示错误趋势图（可选）

3. **权限控制**：
   - 仅管理员或 debug 模式下可访问
   - 生产环境可通过环境变量开关

设计决策需要人类确认：
- 错误页面放在哪个导航位置？
- 是否需要错误趋势图表？
- 是否需要"标记为已处理"功能？

不在此 issue 范围内：
- 错误存储 —— #003

## Acceptance criteria

- [ ] `GET /api/errors` 端点支持分页和过滤
- [ ] 前端 `/admin/errors` 页面显示错误列表
- [ ] 点击错误可查看详情（stack、context）
- [ ] 支持按 type、severity、时间过滤
- [ ] 权限控制：非管理员不可访问

## Blocked by

- [错误存储到后端数据库](.scratch/frontend-error-logging/003-error-storage.md)