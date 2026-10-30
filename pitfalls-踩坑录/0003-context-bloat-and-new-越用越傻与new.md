---
id: 0003
date: 2026-10-30
environment: OpenClaw / Hermes / 任意长会话智能体
category: workflow
severity: major
---

[中文版](0003-context-bloat-and-new-越用越傻与new-中文.md)

## Symptom

The agent gets dumber the longer you use it. Moving to multi-agent doesn't help — each agent carries heavy context too, still dumber and dumber.

## Root cause

Context keeps piling up: the longer the history, the more the model's effective attention gets diluted.

## Fix

`/new` — open a fresh window and restart clean. Narrow each session's task boundary, and sink important conclusions into memory/files instead of leaving them in the conversation.

## Prevention (one line)

Treat a session as a workbench, not an archive — clear it when the work is done.
