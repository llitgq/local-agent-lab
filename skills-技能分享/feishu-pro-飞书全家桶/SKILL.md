---
name: feishu-pro
description: "飞书全家桶伞技能：卡片发送（含折叠面板）、多维表格 bitable、日历日程、docx 文档编辑、LaTeX 公式、群聊管理。统一认证 + 模式路由，零硬编码路径，可移植到任意 agent（Hermes / Claude Code / 其他）。首次使用先读 SETUP.md 完成配置。触发词：飞书、feishu、larksuite、发卡片、发消息、发通知、发报告、飞书卡片、表格卡片、markdown转卡片、折叠面板、smart_send、写文档、编辑文档、读文档、docx、创建文档、多维表格、bitable、记录、查记录、日历、日程、提醒我、安排会议、删日程、calendar、公式、LaTeX、KaTeX、飞书群、群聊权限、机器人管理、230035。"
version: "2.0.0"
author: 山丁 + feishu-pro 整合
metadata:
  hermes:
    tags: [feishu, lark, cards, bitable, calendar, docx, latex, group, umbrella]
---

# feishu-pro — 飞书 API 伞技能

本 skill 是多个飞书子域的统一入口。先在这里拿认证方法 + 判定模式，再进入对应子目录读 PROTOCOL.md 执行。

**首次使用（或换环境）必读 `SETUP.md`**——分步配置向导，每一步都有用户确认闸门。

## 🔑 共享认证（所有子域通用）

凭证三级发现（全部脚本已内置同一顺序）：

1. **调用参数**显式传入 `app_id` / `app_secret`（最高优先级）
2. **环境变量** `FEISHU_APP_ID` + `FEISHU_APP_SECRET`
3. **凭证文件**：`$HERMES_HOME/.env`（未设 HERMES_HOME 时依次找安装目录、`~/.hermes/.env`、当前目录 `.env`）

获取 token：

```
POST https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal
Body: {"app_id": "...", "app_secret": "..."}
```

后续请求 Header：`Authorization: Bearer <token>`。

**踩坑必读**（详见 `references/credentials.md`）：
- Hermes 凭证过滤：代码中含 `SECRET`/`PASSWORD`/`TOKEN` 关键词的行会被替换成 `***` 导致语法错误 → 用两步法（terminal 先提取凭证到 /tmp JSON，脚本再读）
- cron 环境 `HOME` 指向 profile home，`os.path.expanduser("~")` 不可靠 → 用绝对路径
- 权限错误 `99991672` → 到 `https://open.feishu.cn/app/{APP_ID}/auth` 开 scope，注意区分应用身份/用户身份

## 🧭 模式路由

| 用户要做什么 | 模式 | 协议文件 |
|------|------|------|
| 发消息/发表格/发报告到飞书会话（markdown → interactive 卡片） | **卡片** | `cards/PROTOCOL.md` |
| 卡片需要折叠面板/分层展开内容 | **卡片 v2** | `cards/templates/send_card_v2.py`（`[collapse:标题]` 语法，嵌套最多 5 层） |
| 对飞书**文档**（feishu.cn/docx/xxx）读取/写入/编辑 | **docx 编辑** | `doc-edit/PROTOCOL.md` |
| 读写**多维表格**记录、字段、视图、公式列 | **bitable** | `bitable/PROTOCOL.md` |
| 创建/查询/修改/删除**日历日程**、提醒 | **日历** | `calendar/PROTOCOL.md` |
| 中文数学/经济公式转飞书 LaTeX | **公式** | `formulas/PROTOCOL.md` |
| 飞书**群聊**权限、机器人管理、群发故障排查 | **群聊** | `group/PROTOCOL.md` |

### 高频歧义判定

- 用户分享**文档链接**（`feishu.cn/docx/xxx`）并要求"建立/写入/编辑" → **docx 编辑**，不是发卡片
- 回复内容含表格/标题/代码块 → **卡片**（若本安装启用了 card-first 策略，见路由配置）
- 用户说"提醒我/安排/日程" → **日历**；日历未初始化时先走 `calendar/PROTOCOL.md` 的初始化流程
- `smart_send` 的正文参数是 `text` 不是 `content`

## 📦 目录结构

每个子目录是自包含包（内部相对引用保持不变）：

```
feishu-pro/
├── SKILL.md            # 本文件（认证 + 路由）
├── SETUP.md            # 分步配置向导（首次使用必读，含确认闸门）
├── cards/              # 卡片：PROTOCOL + send_card.py + send_card_v2.py(折叠) + references
├── bitable/            # 多维表格：PROTOCOL + feishu_bitable.py + references
├── calendar/           # 日历：PROTOCOL + calendar_tool.py + state
├── doc-edit/           # docx 文档编辑：PROTOCOL + 批量 patch + pptx 提取
├── formulas/           # LaTeX/KaTeX 公式转换
├── group/              # 群聊管理与故障排查
├── references/         # 跨子域通用参考（凭证发现、Hermes 踩坑）
└── scripts/            # smoke_test.py（配置自检）+ install.sh（安装器）
```

## 路由规则（可配置项）

以下规则由 `SETUP.md` 配置阶段决定是否注入目标 agent 的 memory/SOUL：

- **card-first 策略**：所有发给用户的重要回复（含表格/报告）必须走卡片，禁止纯文本表格
- 各功能域 → 本 skill 对应分支的映射
- 日历 `calendar_id` 等实例状态的位置

注入前必须经用户逐条确认（见 SETUP.md 第 8 步）。
