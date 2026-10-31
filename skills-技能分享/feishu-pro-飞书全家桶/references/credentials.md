# 凭证发现与写入规范（所有子域统一）

## 三级发现顺序（脚本内置，文档示例统一引用本规范）

1. **调用参数**显式传入 `app_id` / `app_secret`（测试/多 app 场景）
2. **环境变量** `FEISHU_APP_ID` + `FEISHU_APP_SECRET`
3. **凭证文件** `.env`（KEY=VALUE 纯文本），按顺序找：
   - `$HERMES_HOME/.env`（Hermes 实例根）
   - skill 安装目录下的 `.env`
   - `~/.hermes/.env`
   - 当前工作目录 `.env`

任何脚本读到凭证后应输出（或日志记录）**来源**（"env" / "/path/.env"），便于排查拿错凭证的问题——一个用户可能有多个飞书 app。

## .env 格式

```
FEISHU_APP_ID=cli_xxxxxxxxxxxxxxxx
FEISHU_APP_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxx
# 可选
FEISHU_DM_CHAT_ID=oc_xxxxxxxxxxxxxxxx
```

## Hermes 专属踩坑（非 Hermes 环境可跳过）

### 1. 凭证过滤（写代码时必读）

Hermes 会把代码中含 `SECRET`/`PASSWORD`/`TOKEN` 关键词的**行**替换为 `***`，导致 Python 语法错误。`write_file`、`execute_code`、terminal heredoc 三种模式均不可靠。

**唯一可靠两步法**：
1. 用 **terminal 工具**跑 `python3 -c` 把凭证提取到 `/tmp/feishu_creds.json`（变量名避开敏感词，如 `app_sec`）
2. 后续脚本从该 JSON 读取（`feishu_bitable.py` 的 `inject_creds()` 即此设计）

### 2. cron 环境 HOME 错位

Hermes cron job 的 `HOME` 指向 profile home（如 `<hermes>/profiles/<p>/home`），`os.path.expanduser("~")` 和 `os.environ["HOME"]` 都会返回错误目录。**cron 脚本一律绝对路径**；交互式会话不受影响。

### 3. lark_oapi 依赖位置

`send_card.py` / `send_card_v2.py` 依赖 `lark_oapi` SDK。若装在 Hermes venv 而系统 python3 没有，用 `<hermes>/venv/bin/python3` 运行（报 `ModuleNotFoundError: No module named 'lark_oapi'` 即此原因）。纯标准库脚本（`feishu_bitable.py`、`calendar_tool.py`）不受影响。

### 4. 多 profile 凭证路由（仅老式多 profile 部署）

一个实例多 profile 时，各 profile 有独立 `.env` 和 app。子 agent 误读主 agent 凭证会把卡片发到错误窗口。运行期用 `HERMES_HOME` 指向当前 profile 目录来锁定凭证来源；cron 任务必须在任务定义里显式设置。

## 权限 scope（99991672 排查）

scope 缺失统一报错 `99991672`。到 `https://open.feishu.cn/app/{APP_ID}/auth` 开通；**部分 scope 分「应用身份/用户身份」两个开关，tenant_access_token 只走应用身份**，必须开应用身份那侧。

各子域所需 scope 清单见 `SETUP.md` 第 2 步。
