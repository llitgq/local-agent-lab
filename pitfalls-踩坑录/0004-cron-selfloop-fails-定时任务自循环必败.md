---
id: 0004
date: 2026-10-30
environment: OpenClaw / Hermes 定时任务
category: workflow
severity: major
---

[中文版](0004-cron-selfloop-fails-定时任务自循环必败-中文.md)

## Symptom

Trying to make scheduled tasks self-loop for long-running work. Many attempts, all ending in failure: a hardcoded task only fires at fixed times, and at that moment you have no idea whether tokens or quota remain.

## Root cause

"Scheduling" and "execution" were welded together in dead time — no state awareness, no failure fallback.

## Fix

Switch to jobs (task lists): decompose the task into detailed steps, each with a regression check; verify quota and state before executing.

## Prevention (one line)

Let scheduled tasks wake things up — let the test-backed job chain do the work.
