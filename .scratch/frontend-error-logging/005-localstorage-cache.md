---
title: 本地 localStorage 缓存（离线容错）
status: done
labels:
  - ready-for-agent
created: 2026-07-09
---

## What to build

在前端实现 localStorage 缓存机制，确保网络故障或后端不可用时错误不丢失。

场景：
- 用户网络断开，错误无法上报
- 后端服务重启，短暂不可用
- 用户在移动端，网络不稳定

需要：

1. **`ErrorQueue` 类**：
   - 错误先写入 localStorage 队列
   - 后台上报成功后从队列移除
   - 队列满时丢弃最旧的错误（FIFO，最多 100 条）

2. **离线检测**：
   - 监听 `online` / `offline` 事件
   - 离线时暂停上报，在线时批量重试

3. **重试策略**：
   - 上报失败时指数退避重试（1s, 2s, 4s, 8s...最大 60s）
   - 连续失败 5 次后暂停 5 分钟

4. **页面加载时同步**：
   - 页面加载时检查 localStorage 中是否有未上报错误
   - 有则批量上报

不在此 issue 范围内：
- 错误捕获 —— #001
- 后端存储 —— #003

## Acceptance criteria

- [ ] `ErrorQueue` 实现写入/读取/删除 localStorage 队列
- [ ] 队列最多保留 100 条错误，超出 FIFO 淘汰
- [ ] 离线时错误存入队列，在线时自动上报
- [ ] 上报失败时指数退避重试
- [ ] 页面加载时检查并上报未发送的错误

## Blocked by

- [前端错误捕获与结构化](.scratch/frontend-error-logging/001-frontend-error-capture.md)