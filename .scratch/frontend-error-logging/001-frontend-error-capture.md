---
title: 前端错误捕获与结构化
status: done
labels:
  - ready-for-agent
created: 2026-07-09
---

## What to build

在前端实现统一的错误捕获机制，将分散在各处的 `console.error(e)` 和 `try/catch` 块改为结构化的错误对象。

当前前端代码直接 `console.error(e)` 打印原始异常，缺乏：
- 错误分类（API 错误 / 网络错误 / 业务逻辑错误 / 渲染错误）
- 上下文信息（哪个页面、哪个操作、用户 ID、时间戳）
- 错误指纹（用于去重和聚合）

需要：

1. **ErrorType 类型定义**：
```typescript
type ErrorType = "api" | "network" | "validation" | "render" | "unknown"
type ErrorSeverity = "info" | "warning" | "error" | "fatal"

interface StructuredError {
  type: ErrorType
  severity: ErrorSeverity
  message: string
  stack?: string
  context: {
    page: string
    action: string
    timestamp: string
    userId?: string
    novelId?: string
    chapterId?: string
    sceneId?: string
  }
  originalError?: unknown
}
```

2. **`captureError(error, context)` 函数** — 统一捕获并结构化错误

3. **全局错误边界** — React Error Boundary 捕获渲染错误

4. **全局未捕获错误处理器** — `window.onerror` 和 `unhandledrejection`

不在此 issue 范围内：
- 错误上报到后端 —— #002
- 错误存储 —— #003

## Acceptance criteria

- [ ] `captureError(error, context)` 函数定义在 `src/lib/error.ts`
- [ ] 所有现有 `console.error(e)` 调用改为 `captureError(e, { page, action })`
- [ ] React Error Boundary 包裹根组件，捕获渲染错误
- [ ] `window.onerror` 和 `unhandledrejection` 注册全局处理器
- [ ] 错误对象包含 type、severity、message、context 字段
- [ ] 开发环境下仍打印到 console（便于调试）

## Blocked by

None - can start immediately