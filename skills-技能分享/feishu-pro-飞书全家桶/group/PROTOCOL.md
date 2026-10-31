---
name: tools-feishu-group
description: "飞书群聊管理 — 群组权限、机器人群管理、常见错误码（230035 等）排查与修复。通用型，不含业务配置。"
version: "1.1.0"
triggers:
  - 群聊 权限
  - 机器人 管理员
  - 飞书群
  - 230035
  - send message permission deny
  - 群组 API
  - feishu group chat
related_skills:
  - tools-feishu-bitable
  - tools-feishu-cards
  - tools-feishu-calendar
---

# 飞书群聊管理与故障排查

通用飞书群聊操作指南 — 群组权限管理、机器人入群/设管理员、常见错误码排查。**不含业务配置，所有 Agent 可复用。**

---

## 1. 群组管理 API

### 1.1 前提条件

- 应用需开启**机器人能力**
- 操作者（调用 API 的身份）必须是**群主**
- 需要权限 scope：`im:chat`（获取与更新群组信息）或 `im:chat.manager`（添加/删除群管理员）

### 1.2 认证

**⚠️ 关键区别：**

| API 类型 | 所需 Token | 说明 |
|----------|-----------|------|
| 读取群信息、拉人入群、发送消息 | `tenant_access_token` | 机器人自身身份即可 |
| **添加/删除群管理员** | **`user_access_token`（群主）** | **`tenant_access_token` 会返回 232038** |

> **常见错误：** 用 `tenant_access_token` 调用 `add_managers` API 会返回 `232038 (not owner)`，因为 tenant token 代表机器人身份，而群主通常是用户。**必须使用群主的 `user_access_token` 才能操作。**

如果无法获取群主的 user_access_token，只能让群主在飞书客户端手动操作：群设置 → 群管理 → 将机器人设为「管理员」。

### 1.3 核心端点

#### 指定群管理员

```
POST https://open.feishu.cn/open-apis/im/v1/chats/{chat_id}/managers/add_managers
Query: member_id_type=app_id（设置机器人时）或 open_id（设置用户时）
Body: {"manager_ids": ["cli_xxxxx 或 ou_xxxxx"]}
```

**关键参数：**
- `member_id_type=app_id` — 传入机器人的 App ID（`cli_xxxx` 格式）
- `member_id_type=open_id` — 传入用户的 open_id（`ou_xxxx` 格式）
- 普通群最多 10 个管理员，超大群最多 20 个
- 单次最多指定 5 个机器人

#### 删除群管理员

```
POST https://open.feishu.cn/open-apis/im/v1/chats/{chat_id}/managers/delete_managers
```

#### 获取群信息

```
GET https://open.feishu.cn/open-apis/im/v1/chats/{chat_id}
```

返回群名称、描述、头像、群主 ID、权限配置等。

#### 将用户或机器人拉入群聊

```
POST https://open.feishu.cn/open-apis/im/v1/chats/{chat_id}/members/batch_add
Body: {"member_ids": ["ou_xxxxx 或 cli_xxxxx"], "member_id_type": "open_id 或 app_id"}
```

#### 判断机器人是否在群里

```
GET https://open.feishu.cn/open-apis/im/v1/chats/{chat_id}/members/is_in_chat?member_id_type=open_id&member_id=ou_xxxxx
```

---

## 2. 常见错误码

### 2.1 ❌ 230035 — Send Message Permission deny

**现象：** 机器人收到消息、生成了回复，但发送时被拒绝，日志显示：
```
WARNING: [Feishu] Send failed: [230035] Send Message Permission deny. — trying plain-text fallback
ERROR: [Feishu] Fallback send also failed: [230035] Send Message Permission deny.
```

**根因：** 群聊设置了发言权限限制（如「仅管理员可发言」），而机器人不是群管理员。

**注意：** Hermes 可能将此错误包装为 `HTTP 429` 或 `Insufficient balance` 等误导信息，**不要被迷惑，先查日志确认真实错误码。**

**修复（二选一）：**
1. **通过 API 将机器人设为管理员**（见 §1.3 指定群管理员）
2. **在飞书客户端手动设置：** 群设置 → 群管理 → 将机器人角色设为「管理员」

### 2.2 ❌ 232038 — Operator is not chat owner

**含义：** 操作者不是群主，没有权限添加/删除管理员。

### 2.3 ❌ 232040 — Chat managers reached limit

**含义：** 群管理员人数达到上限（普通群 10 / 超大群 20）。

### 2.4 ❌ 232025 — Bot ability not activated

**含义：** 应用未启用机器人能力。需在开发者后台 → 应用能力 → 添加「机器人」能力。

### 2.5 ❌ 232011 — Operator not in chat

**含义：** 调用 API 的机器人或用户不在群中。需要先拉入群。

### 2.6 ❌ 99991663 — Tenant token invalid

**含义：** Token 过期或无效。重新获取 tenant_access_token。

### 2.7 ❌ 99991672 — Permission scope missing (Access denied)

**含义：** 应用缺少所需 API scope。需在飞书开发者后台启用。

**常见场景：** 用 `user_access_token` 调用 `add_managers` 时，需要 `im:chat` 或 `im:chat.managers:write_only` scope。错误信息示例：
```
Access denied. One of the following scopes is required: [im:chat, im:chat.managers:write_only]
```

**修复步骤：**
1. 打开飞书开发者后台 → 应用 → 权限管理
2. 添加 `im:chat` 或 `im:chat.managers:write_only` 权限
3. **重新发布应用版本**
4. **⚠️ 重新获取 `user_access_token`**（旧 token 不包含新添加的 scope，必须重新授权）

### 2.8 🚫 Bot 在群里完全没反应（无 230035、无任何报错）

**现象：** 机器人在群里，用户 @ 它或发消息，但机器人完全没有反应。日志里没有任何 230035 错误，也没有任何群消息记录。

**根因（WindClaw/OpenClaw）：** `groupPolicy` 默认为 `"allowlist"`，但 allowlist 为空。这意味着**群消息在 OpenClaw 策略层就被拦截了，根本不会传递给 bot。**

**诊断步骤：**
1. 检查 WindClaw/OpenClaw 日志中是否有群消息的 conversationType 记录
2. 查看 `openclaw.json` 的 `channels.feishu.accounts.<id>` 配置
3. 如果 `groupPolicy` 未设置或为 `"allowlist"`，且 `groups`/`allowFrom` 为空 → 确认此问题

**修复：**

| 需求 | 配置 |
|------|------|
| 所有群都能收到消息，不需要 @ | `"groupPolicy": "open"`（同时 `requireMention` 默认变为 `false`） |
| 仅特定群，不需要 @ | `"groupPolicy": "allowlist"` + `"groups": ["oc_xxx"]` + `"requireMention": false` |
| 仅特定群，需要 @ | `"groupPolicy": "allowlist"` + `"groups": ["oc_xxx"]` |

**`requireMention` 默认逻辑**：当 `groupPolicy === "open"` 时默认 `false`，否则默认 `true`。

**配置文件示例：**
```json
"channels": {
  "feishu": {
    "enabled": true,
    "accounts": {
      "main": {
        "enabled": true,
        "appId": "cli_xxx",
        "connectionMode": "websocket",
        "domain": "feishu",
        "dmPolicy": "open",
        "groupPolicy": "open"
      }
    }
  }
}
```

**⚠️ 与 230035 的区别**：230035 是 bot 收到了消息但**发送被拒**；本场景是消息**从未到达 bot**（无报错、无日志）。

### 2.9 🤐 Bot 收到消息但 LLM 返回 NO_REPLY（沉默模式）

**现象：** 机器人在群里，`groupPolicy` 配置正确（`"open"`），websocket 连接正常，但没有回复任何消息。Bot 说"看不到自己被拉入群聊"。

**根因：** 消息**确实到达了 bot**，策略层也放行了，session 也创建了，但 **LLM 模型对每条群消息都输出了 `NO_REPLY`**（选择不回复）。外部表现与 §2.8 完全一致 — 都是"bot 在群里但没反应"。

**如何区分（与 §2.8）：**

| 检查点 | §2.8 策略层拦截 | §2.9 NO_REPLY 沉默 |
|--------|-----------------|-------------------|
| session 文件存在 | ❌ 无 session | ✅ session 存在 |
| session 里消息记录 | ❌ 空 | ✅ 有 `[user]` 消息 + `[assistant] NO_REPLY` |
| 日志中群消息记录 | ❌ 无 | ✅ 有 `dispatching to agent` 记录 |

**诊断步骤（需要访问 Bot 文件系统）：**

**方法一：检查 session 文件（最可靠）**
1. 找到 Bot 的 session 存储目录（Hermes: `~/.hermes/profiles/<profile>/sessions/`，OpenClaw: `<user-dir>/openclaw/agents/main/sessions/`）
2. 搜索 `sessions.json` 中是否包含目标群 chat_id
3. 如果找到 session，查看对应的 `.jsonl` 文件
4. 如果看到 `[assistant] NO_REPLY` → 确认是 LLM 沉默模式

**方法二：检查 gateway 日志**
1. 搜索日志中群 chat_id 的出现
2. 如果有 `dispatching to agent` + `dispatch complete` 但无实际回复内容 → NO_REPLY

**修复方向：**
- 这是 **LLM 模型层**问题，不是配置问题
- 尝试换模型（模型可能对群聊消息缺乏响应训练）
- 检查 system prompt 是否要求"仅在 @ 时回复"之类的限制
- 检查 `requireMention` 是否生效（虽然 `groupPolicy: "open"` 时默认 `false`，但可能被显式覆盖）

**⚠️ 关键教训：** 当 §2.9 的 API 诊断确认"群侧一切正常"后，**不要默认是 `groupPolicy` 问题**。应该先检查 session 文件确认消息是否真的到达了 bot。`groupPolicy` 检查应作为第二步而非第一步。

### 2.11 📡 Gateway WebSocket 故障 — 消息丢失或长时间不响应

两种模式，症状相似但根因不同：

#### 模式 A：短暂断连（消息中间丢几条）

**现象：** Bot 平时正常响应群消息，但某一条（或某一段时间内的）消息完全没回复。群配置正确（`require_mention: false`），无 230035 错误，后续消息又恢复正常。

**根因：** Gateway 的飞书 websocket 连接短暂断开，断连期间的消息不会被补推。重连后只接收新消息，丢失的中间消息永远收不到。Lark SDK 日志会显示 `receive message loop exit, err: no close frame received or sent`。

#### 模式 B：WebSocket 僵尸连接（静默死亡，长时间不收消息）⚠️ 更常见

**现象：** Bot 突然不再响应群消息，**持续很长时间**（数小时到 24h+）。DM 消息可能仍然能收到。`gateway.log` 中完全没有目标消息的记录。**无任何报错、无 disconnect 日志。** `gateway_state.json` 显示 `connected` 看似正常。

**根因：** Lark SDK 的 WebSocket 连接进入**僵尸状态**——底层 TCP/心跳已断，但 SDK 层面未检测到断开，没有触发 `receive message loop exit`，gateway 认为自己仍然在线。**飞书侧不再向这个连接推送消息，但重连也不会发生。**

**历史规律：** WS 连接每 15-19 小时可能出现一次 `no close frame` 断连。模式 B 是断连检测失败的变体——SDK 没有正确识别心跳超时。

**⚠️ 关键诊断信号：`gateway_state.json` 的 `updated_at`**

```bash
# 检查飞书平台状态的上次更新时间
python3 -c "import json; d=json.load(open('<HERMES_HOME>/gateway_state.json')); print(d['platforms']['feishu'])"
# 如果 updated_at 距今超过数小时 → WS 可能已进入僵尸状态
```

`updated_at` 只在 WS connect/disconnect 时更新。如果连接是真的活跃的，它虽然不一定频繁更新，但如果配合"长时间无 raw message 收到"就是僵尸连接的强信号。

**诊断步骤（区分 A / B）：**

```bash
PROFILE=<HERMES_HOME>

# 1. 搜索目标消息是否被 gateway 收到
grep "消息关键词" $PROFILE/logs/gateway.log

# 2. 查看该群的最近消息接收记录
grep "<chat_id>" $PROFILE/logs/gateway.log | grep "group message received" | tail -10

# 3. 查看该时间段的 raw message（所有来源）
awk '/YYYY-MM-DD HH:MM/,/YYYY-MM-DD HH:MM/' $PROFILE/logs/gateway.log | grep "raw message"

# 4. 查看 Lark SDK WS 生命周期日志
grep "\[Lark\]" $PROFILE/logs/gateway.log

# 5. 检查 gateway_state.json 飞书 updated_at
cat $PROFILE/gateway_state.json | python3 -m json.tool | grep -A5 feishu
```

| 检查点 | 模式 A（短暂断连） | 模式 B（僵尸连接） |
|--------|-------------------|-------------------|
| Lark SDK 日志 | ✅ 有 `receive message loop exit` | ❌ 无 exit 日志 |
| `gateway_state.json` | 会更新（disconnect + reconnect） | `updated_at` 停滞不变 |
| 丢失持续时间 | 短（几秒到几分钟） | 长（数小时到 24h+） |
| DM 消息 | 同样丢失 | 可能仍能收到（飞书 DM 可能有重试） |
| 修复方式 | 自动重连（通常很快恢复） | **必须手动 `/restart` gateway** |

**修复（模式 B）：**
```bash
# 在群里发 /restart，或直接重启 gateway
```

**与其他场景的区分：**

| 检查点 | §2.8 策略拦截 | §2.9 NO_REPLY | §2.11 模式 A | **§2.11 模式 B** |
|--------|--------------|---------------|-------------|-----------------|
| 配置 `require_mention` | ❌ 被 allowlist 拦截 | ✅ 正常 | ✅ 正常 | ✅ 正常 |
| gateway 日志有该消息 | ❌ 无 | ✅ 有 dispatch 记录 | ❌ 无 | **❌ 无** |
| 前后消息是否正常 | ❌ 全部不响应 | ❌ 全部 NO_REPLY | ✅ 前后正常，仅丢中间 | **❌ 长时间全部丢失** |
| gateway_state updated_at | — | — | 会更新 | **停滞不变** |
| Lark SDK exit 日志 | — | — | ✅ 有 | **❌ 无** |

**长期建议：** Hermes gateway 应增加 idle-heartbeat 检测——如果超过 N 小时未收到任何 raw message，主动重连 WS。当前只能靠人工 `/restart` 恢复。

---

### 2.10 🔍 诊断流程：Bot 说自己不在群里 / 看不到群聊

**场景：** 用户报告某个机器人被拉入群聊但机器人声称看不到自己在群里。需要快速判断是群侧问题还是 Bot 侧配置问题。

**诊断清单（用 tenant_access_token 即可完成）：**

| 步骤 | API | 目的 | 判断 |
|------|-----|------|------|
| 1 | `GET /im/v1/chats/{chat_id}` | 获取群信息 | 看 `bot_count`、`bot_manager_id_list`（含 app_id）、`owner_id` |
| 2 | `GET /im/v1/chats/{chat_id}/members/is_in_chat?member_id_type=app_id&member_id=cli_xxx` | 确认 Bot 是否在群里 | `is_in_chat: true/false` |
| 3 | 对比步骤 1 的 `bot_manager_id_list` | 确认是否已设管理员 | 在列表中 = 管理员 ✅ |

**判断逻辑：**
- 步骤 2 返回 `false` → Bot 确实不在群里，需要先拉入
- 步骤 2 返回 `true` 且步骤 1 的 `bot_manager_id_list` 包含该 app_id → **群侧一切正常，问题在 Bot 自身**

**群侧正常后的进一步诊断（Bot 侧）：**
1. 检查 Bot 的 `openclaw.json` / `config.yaml` 中 `groupPolicy`（见 §2.8）
2. **如果 `groupPolicy` 也是 `open`** → 检查 session 文件确认是否有 `NO_REPLY`（见 §2.9）
   - 找 session：`grep -r "oc_xxx" <bot-data-dir>/ --include="*.json" -l`
   - 看 `.jsonl` 中是否出现 `[assistant] NO_REPLY`
3. `NO_REPLY` → LLM 模型问题，换模型或调 system prompt
4. 无 session → 才是策略层拦截，修 `groupPolicy`

**注意：** 成员列表 `GET /im/v1/chats/{chat_id}/members?member_id_type=app_id` 会返回 400 错误，不支持 app_id 类型。**不要用这个接口查机器人成员**，改用 `is_in_chat` 接口。

---

## 3. Pitfalls 速查

| # | 问题 | 解决方案 |
|---|------|---------|
| 1 | **230035 发送失败** | 机器人不是群管理员，群设置了发言限制 → 设为管理员 |
| 2 | **230035 被伪装成 429/余额不足** | 先查日志确认真实错误码，不要被包装信息误导 |
| 3 | **232038 用 tenant_token 调 add_managers** | **add_managers 必须用群主的 user_access_token，tenant_token 代表机器人身份不是群主** |
| 4 | **member_id_type 选错** | 机器人用 `app_id`（`cli_xxx`），用户用 `open_id`（`ou_xxx`） |
| 5 | **Token 过期** | 重新获取 tenant_access_token |
| 6 | **新增 scope 后 user_token 仍报 99991672** | **旧 token 不包含新 scope，必须重新授权获取新 user_access_token** |
| 7 | **user_access_token 获取方式** | 飞书开放平台 → API 调试台 → 选应用 → 凭证类型选 user_access_token → 个人授权 |
| 8 | **成员列表 `member_id_type=app_id` 返回 400** | 成员列表 API 不支持 app_id 类型，查机器人成员用 `is_in_chat` 接口（见 §2.10） |
| 9 | **群侧正常 + `groupPolicy: open` 但 bot 仍沉默** | 先查 session 文件确认是否有 `NO_REPLY`（见 §2.9），不要默认是配置问题 |
| 10 | **LLM 对群消息返回 NO_REPLY** | 换模型 / 调 system prompt / 检查 `requireMention` 是否被显式覆盖 |
| 11 | **单条/短时间消息丢失，其他正常** | `grep "消息关键词" gateway.log`，若完全无记录 + Lark SDK 有 `exit` 日志 → WS 短暂断连丢消息（§2.11 模式 A） |
| 12 | **群消息长时间完全不响应，无报错** | 查 `gateway_state.json` 的 `updated_at`，若停滞不变 + Lark SDK 无 `exit` 日志 → **僵尸 WS 连接**，需 `/restart` gateway（§2.11 模式 B） |
| 13 | **区分 WS 故障模式** | 模式 A：有 `receive message loop exit` 日志，短时间丢消息；模式 B：无 exit 日志，`updated_at` 停滞，长时间不响应。模式 B 需手动 restart |

---

## 4. 参考文档

- 群组 API 文档：`references/group-chat-api.md` — 完整 API 端点、请求/响应示例、错误码列表
- （特定用户部署记录未随 feishu-pro 分发）
- NO_REPLY 诊断案例：`references/noreply-diagnosis.md` — 本次排查完整路径（session 文件定位、NO_REPLY 识别）
- WebSocket 僵尸连接诊断：`references/zombie-ws-diagnosis.md` — WS 假活状态的完整排查案例（gateway_state.json updated_at 信号、诊断命令）
