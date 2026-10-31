---
name: feishu-pro-calendar
description: "飞书日历操作。通过飞书 API 管理应用拥有的共享日历：日程增删改查。首次使用需交互式初始化（询问用户日历名称并确认），之后所有会话共享同一份日历状态。触发词：日历、日程、会议、安排、提醒我、calendar、appointment。"
version: "1.1.0"
triggers:
  - 用户提到日历、日程、会议、安排、提醒
  - 用户要求创建/查询/修改/删除日程
---

# 飞书日历

通过飞书 API 管理一个由应用拥有的共享日历。一次安装一份日历状态（`calendar_state.json` 与脚本同目录）。

## 前提

- 凭证已按 `../references/credentials.md` 三级发现配置
- 飞书应用已开通日历相关权限（见文末 scope 表）

## 脚本路径

```
TOOL=<feishu-pro 安装目录>/calendar/scripts/calendar_tool.py
```

> **路径解析注意**：Hermes `execute_code` 沙箱与 cron 环境中 `~`/`expanduser` 可能展开到错误目录。**任何环境都优先用解析后的绝对路径**调用（例如安装目录为 `/Users/xxx/agent/skills/feishu-pro` 时，TOOL 即 `/Users/xxx/agent/skills/feishu-pro/calendar/scripts/calendar_tool.py`）。纯标准库实现，系统 `python3` 即可运行，无需 venv。

## 操作流程

### 第一步：检查是否已初始化

收到任何日历相关请求时，**先执行**：

```bash
python3 "$TOOL" status
```

- 返回 `"initialized": true` → 直接跳到「日常操作」
- 返回 `"initialized": false` → 执行「首次初始化」

### 首次初始化（每一步都要用户确认）

**步骤 1：向用户确认日历方案**

三种方案，向用户说明并让用户选择：

| 方案 | 说明 | 适用 |
|------|------|------|
| **A. 新建应用专属日历（推荐）** | `init` 一步创建，agent 写入的日程全部进这个独立日历，不污染个人日历 | 绝大多数场景 |
| B. 接管已有共享日历 | 用户已有想共用的日历，确认其 `calendar_id` 后手工写入 state 文件 | 已有团队日历 |
| C. 写个人主日历 | 不推荐：需要额外 ACL 授权且会混入个人日程 | 特殊需求 |

选 A 时**询问并确认日历名称**（如 "Agent 助手日历"）。

**步骤 2：获取 chat_id（方案 A 需要）**

从以下来源依次查找飞书 DM 的 chat_id（`oc_` 开头），并**向用户展示找到的值请其确认**：
1. 当前会话上下文中的 chat_id
2. `.env` 中的 `FEISHU_DM_CHAT_ID`
3. 直接询问用户

**步骤 3：执行初始化**

```bash
python3 "$TOOL" init --name "用户确认的日历名称" --chat-id "oc_xxxxxxxxxxxx"
```

**步骤 4：告知用户**

> 告诉用户日历创建成功。飞书"日历助手"机器人会自动推送一条授权通知，用户点击通知中的链接即可查看和订阅该日历。

方案 B：与用户逐字段确认后，将 `calendar_id` / `calendar_name` 写入 `scripts/calendar_state.json` 并置 `"initialized": true`。

### 日常操作

#### 查询日程（默认未来 7 天）

```bash
python3 "$TOOL" list
python3 "$TOOL" list --days 14    # 指定天数
```

#### 创建日程

```bash
python3 "$TOOL" create \
  --title "日程标题" \
  --when "2026-06-04 10:00" \
  --minutes 60 \
  --desc "描述内容" \
  --location "地点"
```

`--minutes` 与 `--end` 二选一；都不给则默认 1 小时。`--desc` / `--location` 可选。

```bash
python3 "$TOOL" create --title "标题" --when "2026-06-04 10:00" --end "2026-06-04 11:30"
```

#### 删除日程

```bash
python3 "$TOOL" delete --event-id "事件ID"
```

#### 重置（删除日历并清空状态，下次重新初始化）

```bash
python3 "$TOOL" reset --confirm
```

## 输出格式

所有命令返回 JSON，统一包含 `"ok": true/false`。`list` 返回 `"events"` 数组，每个事件含 `event_id`、`title`、`description`、`location`、`start`、`end`、`status`、`link`。

## 注意事项

- `--when` / `--end` 格式：`YYYY-MM-DD HH:MM`（24 小时制）
- ACL 授权和 `calendar_id` 永不过期，初始化只需一次
- 状态持久化在脚本同目录的 `calendar_state.json`；**该文件含实例数据，复制 skill 到新环境时必须重置**
- 初始化失败按返回的 error 排查（多数是 scope 未开全，见下表）

### 初始化所需权限（应用身份）

首次 `init` 除日历权限外还需要 IM 权限（获取聊天成员信息）。只开日历权限就跑 init 会报"获取聊天成员失败"：

| 权限 | 用途 |
|------|------|
| `calendar:calendar` | 日历读写 |
| `calendar:calendar:create` | 创建日历 |
| `im:chat:readonly` | 读取群信息 |
| `im:chat` | 群管理读写 |
