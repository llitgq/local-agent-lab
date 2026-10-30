# Local Agent Lab

[中文版](README.zh.md)

Hands-on field notes about running AI agents locally — research ideas, portable skills, and an honest log of every pitfall I hit. One pitfall, one file, added the moment it's discovered.

## What's inside

| Path | What it holds |
|---|---|
| [`notes/`](notes/) | Research and ideas on local agents — one topic per numbered file |
| [`skills/`](skills/) | Self-written skills that passed the portability gates |
| [`pitfalls/`](pitfalls/) | The pitfall log — one file per mistake, numbered, nothing too small |

## The three portability gates

A skill earns its place in `skills/` only if it passes:

1. **Zero hardcoded paths** — everything goes through `$HOME` or arguments
2. **Environment contract** — its README states dependencies and where it was tested
3. **Self-check** — ships a one-shot script that verifies the environment

Anything that fails the gates doesn't get thrown away — it becomes a pitfall entry instead.

## Conventions

- English is the default; every page has a link to its Chinese counterpart (`.zh.md`)
- Pitfalls follow [`pitfalls/_template.md`](pitfalls/_template.md) — symptom, root cause, fix, prevention
- Nothing is too small to log

## License

[MIT](LICENSE)
