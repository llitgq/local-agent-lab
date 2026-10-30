# 📝 02 · The Ideal Second Step: Master the Config Before the Work

[中文版](02-second-step-理想的第二步-中文.md)

> Everyone plays with a freshly installed agent the same way — chat a bit, see if it can do this, do that. That novelty phase is unavoidable. But after it, what should you research next? My answer runs against intuition: **not what the agent can do for you — but the config itself.**
>
> 2026-10-30

## ⚙️ Study the config, not "what can it do for me"

- Get clear on **every config option**: what each one does, what changing it affects
- **How to hook up an API**, **how to swap free models** — if you're on free models, "swap model, swap API" is your single most frequent operation
- You can let a free agent operate this for you, but be prepared: **it will burn a lot of time and tokens**. Chewing through the config early on saves you countless detours later

I'm the cautionary tale again: I once wrote **three or four skills** just to avoid reading the config and editing the model settings. All that dodging, and the root cause was simply that I never mastered the config.

## 👤 user / memory / Skills: one at a time

After config comes getting your **user profile and memory** written properly.

Then, skills. My rule: **every skill you add, you should be able to state its purpose — what it does, and when to use it.** Never download a pile of skills without knowing what they need or how they run. Piled-up skills aren't assets — they're liabilities.

## 🔗 Tool integration: don't let the output side lag

I've seen this everywhere — in communities, among friends: the Feishu/Lark side receives text that has **zero linkage with the agent's configured output**; tables in WeChat still render as raw Markdown. Feishu gets much better once configured, but its own settings are incomplete — by default it won't use Feishu cards, which is a pain.

So I built a small tool for this (will publish later): agent + Feishu, plus an interception layer — **any output containing tables is sent as a Feishu card**. Works as long as Feishu is your messaging endpoint.

## 🧩 Don't rush into multi-agent

One agent can do a lot. My advice: **define broad categories, not narrow ones.** Not "diet assistant + workout assistant + sleep assistant" — one "life assistant" that contains fitness, diet, and the rest. Split too fine, and management overhead eats the benefit.

## 💻 Feel out your machine's limits

I'm no hardware expert. At first I assumed the Mac mini's memory was too small to run any local model — turns out **local image recognition, OCR, and audio-to-text all run fine**, as long as you pick the right parameter scale. Don't overestimate your machine, but don't underestimate it either.

## ⏰ Scheduled tasks: from dead loops to jobs

I wrestled for a long time trying to make **scheduled tasks self-loop**: a hardcoded scheduled task only fires at fixed times, and you have no idea whether the AI still has tokens left at that moment. Many attempts, **all ending in failure**.

The right path turned out to be **jobs (task lists)**: break a task into multiple detailed steps, where **every small step comes with a regression check**. That matters — it costs somewhat more tokens, but the reliability is in a different league.

## 🧪 Try multiple apps; don't chain yourself to one tree

Don't stick with a single local agent. **OpenClaw, Claude Code Desktop, Claude Code CLI** — install and use them all.

I had two biases against Claude Code at first: easy to get banned, and a hassle to hook up. Both turned out wrong — download Claude Code Desktop or the CLI, add **CC Switch**, and you can route Claude Code to your own API with no genuinely hard steps.

An honest reflection: I wasted far, far too long inside OpenClaw and Hermes. Claude Code may not be the strongest at conversation, but **once it's connected to an API model, its ability to get things done jumps a whole class** — when you're actually sitting at your desk, it's the one that genuinely works for you, with solid output.

## 🎯 The one-line summary

Step two = master the config + write user/memory well + few but precise skills + broad categories + know your machine's limits + job-ify scheduled tasks + try multiple apps sideways. **Arm yourself first — then send the agent onto the field.**

## ✅ Checklist

- [ ] Walk through every config option; know what each one controls
- [ ] Rehearse one model swap / API swap (top operation for free-tier users)
- [ ] Write your user profile and memory properly
- [ ] First batch of skills ≤ 3, each with a clear "what it does, when to use it"
- [ ] Set assistants by broad category (life/work/study), not fine-grained
- [ ] Try one small local model: vision / OCR / audio-to-text
- [ ] Convert one scheduled task into a job (decomposed steps + regression checks)
- [ ] Spend one real day each on OpenClaw / Claude Code Desktop / CLI

---

⬆️ [Back to index](../README.md) · ⬅️ [Previous: 01 · The Ideal First Step](01-first-step-理想的第一步.md) · ➡️ Next: to be continued
