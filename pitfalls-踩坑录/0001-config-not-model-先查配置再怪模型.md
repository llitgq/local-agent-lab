---
id: 0001
date: 2026-10-30
environment: OpenClaw / MiniMax API
category: workflow
severity: minor
---

[中文版](0001-config-not-model-先查配置再怪模型-中文.md)

## Symptom

The model performs terribly — off-target answers, low capability. First instinct: "this model is dumb", time to switch.

## Root cause

The model wasn't dumb. The configuration was wrong.

## Fix

When a model underperforms, do a full config review first; only consider switching models after that.

## Prevention (one line)

Blame the config before you blame the model.
