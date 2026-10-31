# execute_code 环境陷阱与飞书卡片调用参考

## 环境路径坑

`execute_code` 沙箱的 `~` 展开到 profile home 目录，不是用户 HOME：

```
expanduser("~") → <profile-home>/.hermes/profiles/<profile>/.env  ❌
```

**正确做法**：用硬编码绝对路径拼接：
```python
home = os.environ.get("HOME", "")  # 仍可能指向 profile home
# 最稳妥：直接硬编码
env_path = "<profile 目录>/.env"
```

## 凭证读取

飞书凭证固定从 `~/.hermes/profiles/life-assistant/.env` 读取，key 为：
- `FEISHU_APP_ID`
- `FEISHU_APP_SECRET`

## query_holdings.py 的 key 映射

`query_holdings.py` 读 `/tmp/feishu_creds.json` 时期望的 key：
- `app_id` → `creds["app_id"]`
- `app_secret` → `creds["app_sec"]`  ← 注意是 `app_sec`，不是 `app_secret`

保存时需用脚本期望的 key：
```python
json.dump({"app_id": app_id, "app_sec": app_secret}, f)
```

## 飞书卡片发送完整模式（已验证成功）

```python
import json, sys

# 1. 读凭证
env_path = "<profile 目录>/.env"
# ... 解析 FEISHU_APP_ID / FEISHU_APP_SECRET

# 2. 加 hermes-agent 到 path
sys.path.insert(0, "<hermes-agent 目录>")

# 3. 加载 send_card.py
card_code = open(".../feishu-cards/templates/send_card.py").read()
exec(compile(card_code, ..., "exec"), globals())

# 4. 调用 smart_send
result = smart_send(
    text=markdown_content,
    title="卡片标题",
    receive_id="oc_xxxxx",
    receive_id_type="chat_id",      # DM 用 chat_id
    app_id=app_id,                  # 必须显式传入
    app_secret=app_secret,          # 必须显式传入
)
```

### 关键约束
- `app_id`/`app_secret` **必须显式传入**，禁止依赖自动发现
- `receive_id_type="chat_id"` 用于 DM 会话
- `send_card.py` 依赖 `lark_oapi`，需在 `sys.path` 中加入 `<hermes-agent 目录>`
- 凭证不支持含引号的值（strip 时已处理）

## 发送目标

当前飞书会话：`oc_xxxxxxxxxxxxxxxxxxxxxx`（DM）
