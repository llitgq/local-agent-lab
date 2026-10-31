# feishu-pro / cards — Markdown 自动转飞书卡片

把 Markdown 文本自动转换为飞书 `interactive` 卡片（JSON 2.0 schema）：表格、标题、代码块、全角半角清洗、超长自动拆分为多卡片。**纯脚本实现，无 plugin 依赖**，任何能跑 python 的 agent 都能用。

> 历史说明：老版本配有 v0.15 Hermes 运行时钩子 plugin（`feishu-table-card`，自动拦截含表格回复）。feishu-pro 不移植 plugin 机制（新版本兼容性未验证），统一走**脚本显式调用**；如需"回复含表格必走卡片"的行为，由路由规则注入实现（见 `../SETUP.md` 第 8 步）。

## 组件

```
cards/
├── PROTOCOL.md              # 完整使用协议（Agent 主要读这个）
├── README.md                # 本文档
├── references/              # 踩坑与规范文档（card-spec、折叠面板、错误码等）
└── templates/
    ├── send_card.py         # v1 核心：markdown→卡片，smart_send 入口
    ├── send_card_v2.py      # v2 折叠面板增强：[collapse:标题] 语法，嵌套≤5层
    ├── feishu_card_utils.py # 卡片构建工具集
    └── utils.py             # 路径推断、凭证读取
```

## 快速开始

```python
import sys
sys.path.insert(0, "<feishu-pro>/cards/templates")
from send_card import smart_send

# markdown 自动转卡片并发送；凭证按 references/credentials.md 三级发现
result = smart_send(text="# 标题\n|列1|列2|\n|--|--|\n|a|b|", chat_id="oc_xxx")
```

依赖：`lark_oapi`（`pip install lark-oapi`；Hermes 环境用其 venv 的 python）。

## 发送目标 chat_id 发现

1. 调用参数显式传入
2. `.env` 的 `FEISHU_DM_CHAT_ID`
3. 当前会话上下文

## 折叠面板（v2）

在 markdown 中使用扩展语法，`send_card_v2.py` 处理：

```
[collapse:点开看详情]
这里的内容默认收起
[/collapse]

[collapse+:默认展开的内容]
...
[/collapse]
```

支持嵌套（最多 5 层）。详见 `references/collapsible-panel.md`。
