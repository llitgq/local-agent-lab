# 📝 00 · Prologue: Two Years, from Chatbox to Agent

[中文版](00-prologue-引子-中文.md)

> This is not a tutorial — it's a running log of my two years of tinkering. If you're on the same road, I hope it saves you a few of the detours I took.
>
> 2026-10-30

## 🌱 Background: It started with complaining about AI

After GPT launched, I lived inside conversational AI. The earliest stage was honestly frustrating — I kept complaining about AI's limitations, about how it couldn't really *do* anything for me. Then I dug into this thing called "prompting", watched some courses and videos, and finally found the door.

## 🐣 Stage 1: Ask whatever comes to mind

My beginner phase: throw one sentence at it, get an answer back. Not exactly useless — but **too shallow** to meet my needs.

## 📏 Stage 2: Learning to write requirements

Then I learned to spell out **task boundaries**: what to do, what not to do, what to output, what not to output — plus constraints, limits, and some proper terminology. Same model, better question, instantly better answers.

## 🧱 Stage 3: Structured prompts

Next came **structured prompting**: a role + background context + constraints + output format. Honestly, it's fundamentally the same as the previous stage — just more meticulous. I'd draft an outline first, then fill it in. My go-to pattern was `Task / Background / Output` — what people call personal prompting.

## 🧠 Stage 4: Controlling context

Then, **context engineering**: step by step control over context in a long conversation — what to keep, what to throw away, saving the model's "memory space". Add chain-of-thought (making it decompose into steps before answering) and tree-of-thought techniques. By this point, the gap from my one-shot question days was **enormous** — output multiplied several times over.

## 🤖 Stage 5: Agents, and the wall I couldn't get past

The real wall appeared when **OpenClaw first launched**.

My strength was writing extremely rigorous process specs — capital accumulated from the prompting era. But in the agent era, I suddenly couldn't pivot: the old AI was conversational; now I had to **decompose its identity definition into countless parts**. Before, AI couldn't operate a computer — it could only produce text and videos, while real workflows were stitched together manually, with scripts, with RPA tools like YingDao. Now it **actually could act on its own — but it acted terribly**.

I gave it complete specifications. I wanted it smart, crisp, and to stop bouncing tasks back to me. It just wouldn't happen — it couldn't meaningfully finish tasks or workflows. Only later did I understand: I hadn't narrowed the problem — **years of conversational AI had boxed in my own thinking**. I simply didn't know how to write an agent's identity definition. That wall cost me one to two weeks.

## 🌀 Stage 6: "Dumber the longer you use it", and the `/new` epiphany

Getting past that wall didn't mean smooth sailing. Countless reinstalls, research, reinstall, research. Then I hit the next problem: **an agent gets dumber the longer you use it** — context piles up. So I studied multi-agent setups — and each agent still carried heavy context. Still dumber and dumber.

Out of necessity, I built a pile of auxiliary tools and helper agents around OpenClaw: context managers, prompt chains, workflow scaffolds. And **the single most important discovery: `/new`** — open a fresh window and start clean. Funny thing: if I had started with a conversation-window tool like Claude Code, I'd probably have understood this from day one. I just didn't make the connection back then.

## 🕊️ Today: a peaceful division of labor

These days I've merged OpenClaw, Hermes, and Claude Code into a relatively peaceful state:

- ✍️ **Writing skills, defining processes** → Claude Code
- ⚙️ **Executing workflows, running scheduled tasks, daily conversation** → agents with external reach like Feishu integration (OpenClaw / Hermes)
- 💼 **My actual office work** → still Claude Code

## 🔜 Next up

This was just the prologue — the story of how I spent two years tinkering. From the next post on, I'll genuinely look back and break it down: **if you start this road from zero, how should you take the first few steps — to minimize cost and maximize results.**

---

⬆️ [Back to index](../README.md) · ➡️ [Next: 01 · The Ideal First Step](01-first-step-理想的第一步.md)
