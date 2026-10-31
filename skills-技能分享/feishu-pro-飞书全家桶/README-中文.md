# 🛠️ feishu-pro · 飞书全家桶

[English](README.md)

> 一个 Skill 打通飞书六大域：**卡片发送（含折叠面板）、多维表格、日历日程、文档编辑、LaTeX 公式、群聊管理**。统一认证 + 模式路由，装一次全都能用。

## 🧩 通用性：一个 Skill，三个智能体

基于 **Agent Skills 开放标准**（SKILL.md，仅需 `name` + `description` 两个必填字段，渐进加载），在以下环境实测可用：

| 智能体 | 放哪里 |
|---|---|
| Claude Code | `~/.claude/skills/feishu-pro/` |
| OpenClaw | 兼容 Claude Code 技能目录 |
| Hermes | `skills/Always/feishu-pro/` |
| 其他任何支持 SKILL.md 标准的智能体 | 对应 skills 目录 |

零硬编码路径 + 三级凭证发现（参数 → 环境变量 → `.env` 文件），跨机器、跨系统拷走即用。自带 `install.sh` 安装器：自动探测目标智能体 → dry-run 展示计划 → 确认后安装，旧版本自动备份不删除。

## 📦 六大功能域

| 域 | 能干什么 | 额外依赖 |
|---|---|---|
| 🃏 cards | markdown → 交互卡片发送，含折叠面板嵌套 5 层 | `lark_oapi` |
| 📊 bitable | 多维表格读写：记录/字段/视图/公式列 | 纯标准库 |
| 📅 calendar | 日程创建/查询/修改/删除/提醒 | 纯标准库 |
| 📝 doc-edit | 飞书文档读取/写入/编辑 | 纯标准库 |
| ∑ formulas | 中文数学/经济公式 → 飞书 LaTeX | 无 |
| 👥 group | 群聊权限、机器人管理、错误码排查 | 无 |

## ⚙️ 配置阶段详解（首次使用必读）

完整向导见 [SETUP.md](SETUP.md)（给智能体的执行手册，含确认闸门）。人读版流程如下：

**第 1 步 · 环境盘点**——智能体只读扫描：找到的凭证候选（来源 + app_id + secret 脱敏显示）、python3 版本、`lark_oapi` 是否可用。多候选时逐个确认用哪个 app（**拿错 app 卡片会发到别的窗口**）。

**第 2 步 · 飞书 App 确定**——复用现有，或到 open.feishu.cn/app 新建企业自建应用，拿到 `App ID`（cli_ 开头）+ `App Secret`。应用需发布版本并开启机器人能力。

**第 3 步 · 开权限 scope**——按启用的功能域到应用后台开通（注意开**应用身份**那一侧）。速查：卡片 `im:message:send_as_bot`；多维表格 `bitable:app`；日历 `calendar:calendar` 等 4 项；文档 `docx:document`；群聊 `im:chat` 等 3 项。报 `99991672` 就是 scope 没开对。

**第 4 步 · 凭证落位**——写入 `.env` 三行：`FEISHU_APP_ID` / `FEISHU_APP_SECRET` / 可选 `FEISHU_DM_CHAT_ID`（默认发送目标）。写入前展示完整内容，写入后读回验证。

**第 5 步 · 依赖安装**——仅 cards 域需要 `pip3 install lark-oapi`，其余域纯标准库零依赖。

**第 6 步 · 连通性自检**——跑 `scripts/smoke_test.py --token-only`，输出凭证来源 + token 结果；可选发一张测试卡片到指定会话，亲眼确认表格渲染正常。

**第 7 步 · 日历初始化**（仅启用日历域时）——三选一：A 新建应用专属日历（推荐）/ B 接管已有日历 / C 用个人主日历（不推荐）。初始化后飞书"日历助手"会推授权链接，点一下订阅即可。

**第 8 步 · 安装到智能体**（可选）——`install.sh` 先 dry-run 打印计划（装到哪、替换什么、备份到哪），你看过确认后 `--apply` 执行。装完重启对应智能体生效。

**第 9 步 · 路由规则注入**——把"什么情况走哪个域"写进智能体的 memory/SOUL，例如 **card-first 策略：所有含表格的回复必须走卡片，禁止纯文本表格**。逐条确认后才写入。

**第 10 步 · 终验**——三句测试语跑通即配置完成：「发一张带表格的测试卡片」「提醒我明天上午 10 点喝水」「把这个 markdown 写到文档 xxx」。

## 🔒 安全设计

- 每个自动扫描的值（ID/secret/路径）**必须用户确认后才使用**
- secret 只显示前 4 位，写入前展示、写入后回读
- 所有替换操作先 dry-run，旧文件移入备份目录而非删除

## 📜 License

MIT
