# 🛠️ Feishu Card Interceptor

[中文版](README-中文.md)

> Status: 🚧 being packaged — coming soon

## One line

An interception layer over the agent's output: **any message containing a table is converted and sent as a Feishu (Lark) card.**

## Why it exists

Feishu doesn't use card messages by default, so agent-produced tables arrive as a blob of raw Markdown — unreadable and ugly. This tool pairs your agent with Feishu and cards up every table output.

## Requirement

Feishu is your messaging endpoint.

## Related pitfall

See [0005 · Feishu card interception](../../pitfalls-踩坑录/0005-feishu-card-intercept-飞书卡片拦截.md)
