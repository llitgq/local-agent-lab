# feishu-pro 配置向导（agent 执行手册）

> **本文件是给 agent 的执行指令**。目标：把 feishu-pro 在当前环境配置到可用，并可选地安装进 agent 自己的 skill 目录。
>
> ## 铁律（每一步都适用）
> 1. **每个自动扫描/推断出来的值（APP ID、secret、chat_id、路径、已存在的 skill），必须原样展示给用户并获其确认后才能使用或写入**。扫描可能出错，宁可多问一句。
> 2. **只展示，不擅自写入**。所有写操作（写 .env、写 state、安装、注入 memory）前，先展示"我将写入 X 到 Y"，用户点头才执行。
> 3. **凭证脱敏展示**：secret 只显示前 4 位 + `****`。
> 4. 用户说"停下"立即停，已完成步骤的状态如实汇报。

## 第 0 步：环境盘点（只读）

向用户汇报以下扫描结果（每一项都标明来源）：

- 找到的凭证候选：依次检查 `$HERMES_HOME/.env`、`~/.hermes/.env`、`~/.hermes-new/.env`、当前目录 `.env`、环境变量 `FEISHU_APP_ID`。列出**来源路径 + app_id + secret 脱敏**。一个环境可能有多个飞书 app（不同 agent 各一个），**拿错 app 卡片会发到别的窗口**。
- python3 版本；`lark_oapi` 是否可导入（cards 需要；bitable/calendar 纯标准库不需要）。
- 本 skill 目录绝对路径（下文记为 `$FEISHU_PRO`，所有文档示例中的 `<feishu-pro>` 均替换为它）。

**确认闸门**：把盘点结果给用户看，问"用哪个 app 继续，或新建？"（多候选时逐个确认排除）

## 第 1 步：飞书 App 确定

两种情况：

**A. 复用现有 app**（第 0 步已确认哪个）→ 跳到第 2 步。

**B. 新建 app** → 指导用户：
1. 打开 https://open.feishu.cn/app → 创建企业自建应用
2. 拿到 `App ID`（`cli_` 开头）和 `App Secret`
3. **提醒：app 需要发布版本并available，机器人能力需开启**（用户在后台操作，agent 不代办）

## 第 2 步：开通权限 scope（按启用的功能域）

先问用户：**要启用哪些功能域？**（卡片 / 多维表格 / 日历 / 文档编辑 / 群聊；公式无需权限）

然后给出对应 scope 清单，指导用户到 `https://open.feishu.cn/app/{APP_ID}/auth` 开通（**应用身份**一侧）：

| 功能域 | scope | 说明 |
|---|---|---|
| 卡片 cards | `im:message:send_as_bot` | 以机器人身份发消息 |
| 多维表格 bitable | `bitable:app:readonly`（读）/ `bitable:app`（读写） | |
| 日历 calendar | `calendar:calendar` + `calendar:calendar:create` + `im:chat:readonly` + `im:chat` | init 需要 IM 权限获取聊天成员，只开日历会报"获取聊天成员失败" |
| 文档 doc-edit | `docx:document:readonly`（读）/ `docx:document`（读写） | |
| 群聊 group | `im:chat` + `im:chat:readonly` + `contact:user.id:readonly` | |

报错 `99991672` = scope 没开或没开应用身份那一侧。

## 第 3 步：凭证落位

与用户确认写入位置（推荐 `.env` 文件，来源单一可查）：

```
FEISHU_APP_ID=cli_xxxx
FEISHU_APP_SECRET=xxxx
FEISHU_DM_CHAT_ID=oc_xxxx    # 可选：默认发送目标，向用户确认 chat_id 归属
```

写入前展示完整内容 + 目标路径；写入后**读回验证**并再次脱敏展示。

## 第 4 步：依赖确认（仅 cards 需要）

需要 `lark_oapi`。展示将执行的命令（`pip3 install lark-oapi` 或 Hermes venv 的 pip），用户确认后执行。

## 第 5 步：连通性自检

```bash
python3 "$FEISHU_PRO/scripts/smoke_test.py" --token-only
```

输出会标明**凭证来源**和 token 结果。失败则按 `references/credentials.md` 排查（app secret invalid → 凭证错；99991672 → scope）。

**可选**（用户明确同意后才发）：`--send-card --chat-id oc_xxx` 发一张测试卡片到指定会话，用户在飞书里确认收到且表格渲染正常。

## 第 6 步：日历初始化（仅当启用日历域，且用户同意现在配）

按 `calendar/PROTOCOL.md` 的初始化流程执行，要点：

1. 向用户呈现三个方案（**A 新建应用专属日历（推荐）** / B 接管已有 / C 个人主日历不推荐），用户选择
2. 选 A：确认日历名称 → 确认 chat_id（展示来源）→ `python3 "$FEISHU_PRO/calendar/scripts/calendar_tool.py" init --name "..." --chat-id "oc_..."`
3. 成功后**提醒用户**：飞书"日历助手"会推送授权通知，点链接订阅日历
4. 选 B：与用户逐字段确认 `calendar_id` 后写入 `calendar/scripts/calendar_state.json`

也可以跳过本步，日后再初始化（第一次说"提醒我…"时会自动触发初始化流程）。

## 第 7 步：安装到 agent（可选，也可以留在原地直接用）

```bash
bash "$FEISHU_PRO/scripts/install.sh"            # dry-run，只打印计划
bash "$FEISHU_PRO/scripts/install.sh" --apply    # 用户看过 dry-run 并确认后执行
```

安装器行为：检测候选目标（Hermes 各实例 / Claude Code / 自定义路径）→ 列出目标里**已存在的飞书 skill**（按名字匹配）→ dry-run 展示"装到哪、替换什么、备份到哪" → `--apply` 时先打包备份再替换/安装。**已存在的旧飞书 skill 会被移到备份目录而非删除**。

替换后需重启对应 agent/网关才生效——提示用户，由用户决定何时重启。

## 第 8 步：路由规则注入（SOUL / Memory）

生成本安装的路由片段，**逐条展示给用户确认**后，按目标 agent 的机制写入（Hermes 走 memory 写入审批；其他 agent 按其 memory/SOUL 机制）。模板（按实际启用的域裁剪）：

```markdown
## 飞书路由规则
- 回复内容包含表格或重要报告时，必须用 feishu-pro cards 分支发卡片（send_card 的 smart_send），禁止纯文本表格
- 飞书文档读写 → feishu-pro doc-edit 分支
- 多维表格操作 → feishu-pro bitable 分支
- 日程/提醒/日历 → feishu-pro calendar 分支（日历状态: <feishu-pro路径>/calendar/scripts/calendar_state.json）
- 群聊管理 → feishu-pro group 分支
```

- card-first 是否启用（"所有重要回复必走卡片"还是"仅含表格时走卡片"）由用户选择，写进片段
- 片段里写**绝对路径**（agent 跨会话使用时相对路径不可靠）

## 第 9 步：终验清单

逐项让用户对 agent 说测试语句，验证路由：

| 测试语句 | 期望 |
|---|---|
| "发一张带表格的测试卡片" | 收到 interactive 卡片，表格渲染正常 |
| "提醒我明天上午 10 点喝水"（若配了日历） | 日历创建成功 + 回执含时间 |
| "把这个 markdown 写到文档 xxx"（若配了 doc-edit） | 走 doc-edit 分支而非发卡片 |

全部通过 → 配置完成，向用户汇报存档信息：凭证位置、启用的域、日历 ID、备份位置。
