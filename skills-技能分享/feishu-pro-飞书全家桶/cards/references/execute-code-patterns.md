# execute_code 调用 Skill 模板的模式

## 问题

`execute_code` 运行在沙箱中，无法 import 任何 Skill/Plugin 目录下的模块：

```python
# ❌ 报错: ModuleNotFoundError: No module named 'templates'
from templates.send_card import smart_send
```

## 解决方案：内联模式（推荐）

将 `send_card.py` 的函数定义完整内联到 `execute_code` 脚本中：

```python
from hermes_tools import execute_code

# 1. 先通过 skill_view 读取 send_card.py 内容
# 2. 将其中所有函数定义粘贴到代码字符串中
# 3. 调用时直接使用

code = '''
import json, os, re, sys
from pathlib import Path
# ... send_card.py 的所有函数定义 ...

text = "## 标题\\n| 列1 | 列2 |\\n|---|---|\\n| a | b |"
title = "卡片标题"
receive_id = "oc_xxx"

result = smart_send(text=text, title=title, receive_id=receive_id)
print(json.dumps(result, ensure_ascii=False))
'''

result = execute_code(code=code)
```

**优点**：完全自包含，不依赖文件路径
**缺点**：脚本较长（~400 行）

## 替代方案：terminal 执行独立脚本

```python
# 用一个独立 .py 脚本，存放在已知路径
from hermes_tools import write_file, terminal, read_file

script_content = """
import sys
sys.path.insert(0, "<feishu-pro>/cards/templates")
from send_card import smart_send
import json

text = sys.argv[1]  # 或从 stdin 读取
title = sys.argv[2]
receive_id = sys.argv[3]

result = smart_send(text=text, title=title, receive_id=receive_id)
print(json.dumps(result, ensure_ascii=False))
"""

# 写入临时文件
write_file("/tmp/send_premarket_card.py", script_content)

# 用 terminal 执行（可访问完整文件系统）
terminal("<hermes venv>/bin/python3 /tmp/send_premarket_card.py")
```

**优点**：不需要内联，保持 send_card.py 独立维护
**缺点**：需要写临时文件，依赖绝对路径

## 选择指南

| 场景 | 推荐方案 |
|------|---------|
| 单次调用、文本固定 | 内联模式（直接粘贴函数） |
| 多次调用、文本变化 | terminal + 临时脚本 |
| cron 定时任务 | 内联模式（最可靠） |
| 跨 profile 复用 | terminal + 临时脚本 |

## 现成可复用的内联模板

在 `qyq-panqianget-v2` 的 cron 任务中，已将 send_card.py 逻辑（clean_fullwidth、parse_pipe_table、markdown 转 JSON、lark_oapi 发送）完整内联。实际验证输出为 `{"success": true, "cards_sent": 1, "message_ids": ["om_..."]}`。

如需在类似场景使用，建议先 `skill_view("tools-feishu-cards", file_path="templates/send_card.py")` 读取最新版本函数定义，再粘贴到 `execute_code` 脚本中。
