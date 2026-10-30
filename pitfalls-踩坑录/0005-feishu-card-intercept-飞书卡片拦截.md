---
id: 0005
date: 2026-10-30
environment: 飞书 / 智能体消息输出
category: env
severity: minor
---

[中文版](0005-feishu-card-intercept-飞书卡片拦截-中文.md)

## Symptom

Tables output by the agent arrive in Feishu/Lark as raw Markdown — unreadable. WeChat endpoints are the same.

## Root cause

Feishu doesn't enable card messages by default and its settings are incomplete; the agent's config side and the output side never formed a linkage.

## Fix

Add an interception layer: any output containing tables is converted and sent as a Feishu card (interceptor tool to be published in `skills-技能分享/`).

## Prevention (one line)

When wiring up a new messaging endpoint, send one rich-text probe first — see what it actually looks like on the other side.
