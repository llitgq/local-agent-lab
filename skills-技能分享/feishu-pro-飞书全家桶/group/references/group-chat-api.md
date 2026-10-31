# 飞书群组 API 参考

来源：https://open.feishu.cn/document/server-docs/group-chat/group-members/set-group-manager

---

## 指定群管理员

**POST** `/open-apis/im/v1/chats/{chat_id}/managers/add_managers`

将群内指定的用户或机器人设置为群管理员。仅群主可操作。

### 请求参数

| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| chat_id | path | string | 是 | 群 ID，仅支持 group/topic 模式 |
| member_id_type | query | string | 否 | ID 类型：`open_id`（默认）/ `union_id` / `user_id` / `app_id` |

**请求体：**

```json
{
  "manager_ids": ["ou_xxxxx"]
}
```

- 用户：`member_id_type=open_id`，值填 `ou_xxxxx`
- 机器人：`member_id_type=app_id`，值填 `cli_xxxxx`（应用 App ID）

### 限制

- 普通群最多 10 个管理员，超大群最多 20 个
- 单次请求最多指定 5 个机器人
- manager_ids 最大长度 50

### 权限

- `im:chat`（获取与更新群组信息）**或**
- `im:chat.manager`（添加/删除群管理员）

### cURL 示例

```bash
curl -X POST 'https://open.feishu.cn/open-apis/im/v1/chats/oc_xxxxx/managers/add_managers?member_id_type=app_id' \
  -H 'Authorization: Bearer t-xxxxx' \
  -H 'Content-Type: application/json' \
  -d '{"manager_ids": ["cli_xxxxx"]}'
```

### 响应

```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "chat_managers": ["ou_xxxxx"],
    "chat_bot_managers": ["cli_xxxxx"]
  }
}
```

### 错误码

| HTTP | 错误码 | 描述 |
|------|--------|------|
| 400 | 232001 | 请求参数无效 |
| 400 | 232009 | 群组已解散 |
| 400 | 232011 | 操作者不在群组中 |
| 400 | 232019 | 触发群限流 |
| 400 | 232024 | 机器人对用户没有可见性 |
| 400 | 232025 | 机器人能力未启用 |
| 400 | 232027 | 成员 ID 列表为空或无效 |
| 400 | 232033 | 外部群不支持操作 |
| 400 | 232034 | 应用未安装或未启用 |
| 400 | 232038 | 操作者不是群主 |
| 400 | 232040 | 群管理员已达上限 |

---

## 删除群管理员

**POST** `/open-apis/im/v1/chats/{chat_id}/managers/delete_managers`

参数与「指定群管理员」相同。仅群主可操作。

---

## 获取群信息

**GET** `/open-apis/im/v1/chats/{chat_id}`

返回群名称、描述、群主 ID、chat_mode（group/topic）等。

---

## 拉入群聊

**POST** `/open-apis/im/v1/chats/{chat_id}/members/batch_add`

```json
{
  "member_ids": ["ou_xxxxx"],
  "member_id_type": "open_id"
}
```

机器人用 `member_id_type=app_id`，值填 `cli_xxxxx`。

---

## 判断是否在群里

**GET** `/open-apis/im/v1/chats/{chat_id}/members/is_in_chat?member_id_type=open_id&member_id=ou_xxxxx`

---

## 获取群成员列表

**GET** `/open-apis/im/v1/chats/{chat_id}/members?page_size=50&member_id_type=open_id`
