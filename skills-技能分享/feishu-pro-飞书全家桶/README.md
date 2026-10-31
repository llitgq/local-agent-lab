# 🛠️ feishu-pro · The Feishu Full Stack

[中文版](README-中文.md)

> One skill, six Feishu domains: **card sending (with collapsible panels), Bitable, calendar, doc editing, LaTeX formulas, and group management.** Unified auth + mode routing — install once, use everything.

## 🧩 Portability: one skill, three agents

Built on the **Agent Skills open standard** (SKILL.md — only `name` + `description` required, progressive disclosure). Tested working in:

| Agent | Where it goes |
|---|---|
| Claude Code | `~/.claude/skills/feishu-pro/` |
| OpenClaw | Claude Code-compatible skills directory |
| Hermes | `skills/Always/feishu-pro/` |
| Any other SKILL.md-compatible agent | its own skills directory |

Zero hardcoded paths + three-level credential discovery (params → env vars → `.env` file): copy it across machines and systems and it just works. Ships with an `install.sh` installer: auto-detects target agents → dry-run plan → installs on confirmation, backing up (never deleting) old versions.

## 📦 The six domains

| Domain | What it does | Extra deps |
|---|---|---|
| 🃏 cards | markdown → interactive cards, collapsible panels up to 5 levels | `lark_oapi` |
| 📊 bitable | Bitable read/write: records, fields, views, formula columns | stdlib only |
| 📅 calendar | Create/query/edit/delete events and reminders | stdlib only |
| 📝 doc-edit | Read/write/edit Feishu docs (docx) | stdlib only |
| ∑ formulas | Plain-language math/econ formulas → Feishu LaTeX | none |
| 👥 group | Chat permissions, bot management, error-code triage | none |

## ⚙️ The configuration phase (read this first)

The full wizard is [SETUP.md](SETUP.md) (an execution manual for the agent, with confirmation gates). The human-readable flow:

**Step 1 · Environment scan** — the agent scans read-only: credential candidates (source + app_id + masked secret), python3 version, `lark_oapi` availability. With multiple candidates, confirm each (wrong app = cards land in the wrong window).

**Step 2 · Pick your Feishu app** — reuse an existing one, or create an enterprise self-built app at open.feishu.cn/app and grab the `App ID` (starts with cli_) + `App Secret`. The app must be published with the bot capability enabled.

**Step 3 · Enable scopes** — per domain, in the app console, on the **app-identity** side. Quick reference: cards `im:message:send_as_bot`; bitable `bitable:app`; calendar `calendar:calendar` + 3 more; docs `docx:document`; group `im:chat` + 2 more. Error `99991672` = scope missing or wrong side.

**Step 4 · Credentials** — three lines into `.env`: `FEISHU_APP_ID` / `FEISHU_APP_SECRET` / optional `FEISHU_DM_CHAT_ID` (default send target). Full content shown before writing, read-back verified after.

**Step 5 · Dependencies** — only the cards domain needs `pip3 install lark-oapi`; everything else is stdlib.

**Step 6 · Connectivity check** — run `scripts/smoke_test.py --token-only` (prints credential source + token result); optionally send a test card to a chat and eyeball the table rendering.

**Step 7 · Calendar init** (calendar domain only) — pick one: A create a dedicated app calendar (recommended) / B adopt an existing one / C personal primary calendar (not recommended). Feishu's Calendar Assistant pushes an authorization link to subscribe.

**Step 8 · Install into your agent** (optional) — `install.sh` dry-runs the plan (where, what replaces what, where backups go), then `--apply` on your confirmation. Restart the agent afterwards.

**Step 9 · Route injection** — write "which domain handles what" into the agent's memory/SOUL, e.g. the **card-first policy: any reply containing a table must go through cards — plain-text tables forbidden**. Written only after per-line confirmation.

**Step 10 · Final verification** — three test sentences and you're done: "send a test card with a table", "remind me to drink water at 10am tomorrow", "write this markdown into doc xxx".

## 🔒 Safety design

- Every scanned value (ID/secret/path) **requires user confirmation before use**
- Secrets show first 4 chars only; shown before writing, read back after
- All replaces dry-run first; old files moved to backups, never deleted

## 📜 License

MIT
