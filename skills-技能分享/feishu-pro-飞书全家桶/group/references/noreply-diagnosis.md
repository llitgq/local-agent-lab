# NO_REPLY 诊断案例

万德 cloud（WindClaw）被拉入群聊「👴 老头推送 ✉️」后声称看不到自己在群里。
群侧一切正常，配置也正确，最终定位为 LLM 返回 NO_REPLY。

## 排查路径

### 1. 飞书 API 侧（群侧）

```
GET /im/v1/chats/oc_xxxxxxxxxxxxxxxxxxxxxx
→ bot_count: "2", bot_manager_id_list: ["cli_a948...", "cli_a94c..."], owner_id: ou_9eca...

GET /im/v1/chats/.../members/is_in_chat?member_id_type=app_id&member_id=cli_xxxxxxxxxxxxxxxx
→ is_in_chat: true
```

结论：群侧正常，两个 bot 都在群里且都是管理员。

### 2. Bot 配置侧

配置文件：`~/.openclaw-windclaw/users/144087993-.../openclaw/openclaw.json`

```json
"channels": {
  "feishu": {
    "accounts": {
      "main": {
        "appId": "cli_xxxxxxxxxxxxxxxx",
        "connectionMode": "websocket",
        "dmPolicy": "open",
        "groupPolicy": "open"    // ← 配置正确
      }
    }
  }
}
```

结论：配置也正常，`groupPolicy: "open"`，websocket 连接活跃。

### 3. Session 文件侧（关键）

定位 session：
```bash
grep -r "oc_f19c" ~/.openclaw-windclaw/ --include="*.json" -l
# → sessions/sessions.json, sidebar-snapshots.json, third-party-transcript-report-state.json
```

sessions.json 中有 session：
```json
"agent:main:feishu:group:oc_xxxxxxxxxxxxxxxxxxxxxx": {
  "chatType": "group",
  "sessionFile": "...153e2d90-...-.jsonl",
  "status": "done"
}
```

查看 .jsonl 内容：
```
[user] 消息内容 (来自 ou_6afd...)
[assistant] NO_REPLY       ← 关键：LLM 选择了不回复
```

### 4. 最终结论

- 消息**到达了** bot（有 session、有 user 消息记录）
- 策略层**放行了**（groupPolicy: open）
- 但 LLM（AliceBase-windclaw）**选择了不回复**（NO_REPLY）
- 这是模型行为问题，非配置问题

## 适用于

- OpenClaw / WindClaw / Hermes 系的 bot
- 任何"bot 在群里但看起来不在"的排查
- 区分三层失败：群侧（API）→ 配置侧（policy）→ 模型侧（NO_REPLY）
