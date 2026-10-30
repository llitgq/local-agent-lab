---
id: 0003
date: 2026-10-30
environment: OpenClaw / Hermes / 任意长会话智能体
category: workflow
severity: major
---

[English](0003-context-bloat-and-new-越用越傻与new.md)

## 症状

Agent 越用越傻。改多 Agent 也救不了——每个 Agent 的上下文也不小，照样越用越傻。

## 根因

上下文持续堆积：历史越长，模型的有效注意力越被稀释。

## 解法

`/new` 新开窗口，干干净净重来。收窄每次会话的任务边界；重要结论沉淀到 memory/文件里，而不是留在对话里。

## 怎么防（一句话）

把会话当工作台，别当档案柜——干完活就清台。
