---
title: Character / World / Style CRUD
status: done
labels:
  - ready-for-agent
created: 2026-07-08
completed: 2026-07-09
---

## What to build

实现人物、世界观、风格的 CRUD 页面。后端已有路由。

前端需要三个独立管理页面，通过 Tab 切换：

- **人物管理**：列表 + 创建表单（姓名、年龄、职业、性格标签、目标、恐惧、习惯、说话风格）
- **世界观管理**：列表 + 创建表单（名称 + 配置 JSON 编辑器）
- **风格管理**：列表 + 创建表单（名称 + profile JSON 编辑器）

所有操作绑定到当前选中的 Novel。

## Acceptance criteria

- [ ] 小说详情页中新增"人物/世界观/风格"三个 Tab
- [ ] 人物列表显示所有人物，支持创建和删除
- [ ] 世界观列表支持创建和删除
- [ ] 风格列表支持创建和删除
- [ ] 列表切换平滑，数据随 Novel 切换自动更新

## Blocked by

- [Novel CRUD](.scratch/novel-crud/002-novel-crud.md)