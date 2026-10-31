---
name: tools-feishu-doc-edit
description: 飞书文档（docx）编辑 API — 认证、读取块结构、创建/删除/更新块、批量操作。当用户要求"写入文档""建立大纲""编辑飞书文档"时使用本 Skill，不要发飞书卡片。
version: "1.0.0"
triggers:
  - 用户要求编辑飞书文档
  - 用户要求写入飞书文档
  - 用户要求建立大纲到飞书文档
  - 用户给飞书文档链接要求修改内容
  - 飞书文档 docx API
  - feishu document edit
  - 写入飞书文档块
related_skills:
  - tools-feishu-cards
  - tools-feishu-bitable
  - feishu-doc-gongshi
---

# 飞书文档编辑（docx API）

通过飞书开放平台 docx/v1 API 直接编辑飞书文档内容：读取块结构、创建标题/正文/列表等块、批量删除块。

**⚠️ 核心区分**：用户说"写入文档""建立大纲""编辑文档"时，意思是**直接修改飞书文档内容**（本文档所述），不是发飞书卡片（见 `tools-feishu-cards`）。搞混会导致用户不满。

---

## 第一部分：认证

### 获取 tenant_access_token

```python
import requests

env_path = "<凭证文件绝对路径，发现顺序见 references/credentials.md>"
app_id = ""
app_secret = ""
with open(env_path, "r") as f:
    for line in f:
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            if k == "FEISHU_APP_ID":
                app_id = v
            elif k == "FEISHU_APP_SECRET":
                app_secret = v

token_url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
resp = requests.post(token_url, json={"app_id": app_id, "app_secret": app_secret})
tenant_token = resp.json()["tenant_access_token"]

headers = {
    "Authorization": f"Bearer {tenant_token}",
    "Content-Type": "application/json"
}
```

**注意**：`execute_code` 中 `os.path.expanduser("~")` 在 cron 环境下可能指向 profile home 目录。直接用绝对路径读取 `.env` 最可靠。

---

## 第二部分：文档块结构

### 获取文档信息和块列表

```python
doc_id = "从文档 URL 中提取"  # 如 TKcNdVkJGo4p9uxRioKcNLOEn0f

# 获取文档信息
doc_url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}"
resp = requests.get(doc_url, headers=headers)
doc_info = resp.json()["data"]["document"]

# 获取所有块
blocks_url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/blocks?page_size=500"
resp = requests.get(blocks_url, headers=headers)
blocks = resp.json()["data"]["items"]
```

### 块类型映射

| block_type | 类型 | JSON key | 说明 |
|------------|------|----------|------|
| 1 | Page | — | 文档根块，block_id = doc_id |
| 2 | Text | `text` | 普通正文 |
| 3 | Heading1 | `heading1` | 一级标题 |
| 4 | Heading2 | `heading2` | 二级标题 |
| 5 | Heading3 | `heading3` | 三级标题 |
| 6 | Heading4 | `heading4` | 四级标题 |
| 7 | Heading5 | `heading5` | 五级标题 |
| 8 | Heading6 | `heading6` | 六级标题 |
| 9 | Heading7 | `heading7` | 七级标题 |
| 10 | Heading8 | `heading8` | 八级标题 |
| 11 | Heading9 | `heading9` | 九级标题 |
| 12 | Bullet | `bullet` | 无序列表 |
| 13 | Ordered | `ordered` | 有序列表 |
| 14 | Code | `code` | 代码块 |
| 15 | Quote | `quote` | 引用 |
| 17 | Todo | `todo` | 待办 |
| 19 | Divider | `divider` | 分割线 |
| 22 | Image | `image` | 图片 |

### 块的文本结构

所有含文本的块（text, heading1-9, bullet, ordered, code, quote, todo）结构相同：

```json
{
  "block_type": 3,
  "heading1": {
    "elements": [
      {
        "text_run": {
          "content": "标题文字",
          "text_element_style": {}
        }
      }
    ]
  }
}
```

### 提取块的文本内容（辅助函数）

```python
TEXT_KEYS = ['text', 'heading1', 'heading2', 'heading3', 'heading4',
             'heading5', 'heading6', 'heading7', 'heading8', 'heading9',
             'bullet', 'ordered', 'code', 'quote', 'todo']

def get_block_text(block):
    for key in TEXT_KEYS:
        if key in block:
            return ''.join(
                el.get('text_run', {}).get('content', '')
                for el in block[key].get('elements', [])
            )
    return ""
```

---

## 第三部分：创建块

### 创建子块

在指定父块下创建子块（通常父块是文档根块，block_id = doc_id）。

```python
create_url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/blocks/{doc_id}/children"

def make_heading(block_type, heading_key, content):
    return {
        "block_type": block_type,
        heading_key: {
            "elements": [{"text_run": {"content": content, "text_element_style": {}}}]
        }
    }

def h1(text): return make_heading(3, "heading1", text)
def h2(text): return make_heading(4, "heading2", text)
def h3(text): return make_heading(5, "heading3", text)

def text_block(text):
    return {
        "block_type": 2,
        "text": {
            "elements": [{"text_run": {"content": text, "text_element_style": {}}}]
        }
    }

# 一次可以创建多个块
payload = {
    "index": 0,  # 插入位置，0 = 最前面
    "children": [h1("标题一"), h2("标题二"), h3("标题三"), text_block("正文内容")]
}

resp = requests.post(create_url, headers=headers, json=payload)
result = resp.json()
# result["data"]["children"] 包含创建的块信息（含 block_id）
```

### 带样式的文本

`text_element_style` 支持以下样式：

```python
# 加粗
{"bold": True}

# 斜体
{"italic": True}

# 下划线
{"underline": True}

# 行内代码
{"inline_code": True}

# 删除线
{"strikethrough": True}

# 文字背景色（背景色高亮）—— 重要！
{"background_color": 5}  # 数字 1-7 对应不同颜色

# 链接
{"link": {"url": "https://example.com"}}

# 合并多个样式
{"bold": True, "background_color": 5, "italic": True}
```

#### background_color 颜色值映射

| 值 | 颜色 | 推荐用途 |
|----|------|----------|
| 1 | 红色 | 削弱方法、注意事项、排除项 |
| 2 | 紫色 | 特殊标注 |
| 3 | 橙色 | 口诀、关键结论 |
| 4 | 青色 | 核心概念、定义特征 |
| 5 | 绿色 | 加强方法、解题技巧 |
| 6 | 粉色 | 补充标注 |
| 7 | 蓝色 | 定义、特征、概念引入 |

**⚠️ background_color 的值是数字（1-7），不是十六进制颜色码。** 早期尝试用 `"#FFFF00"` 格式会静默失败。

### 一个块中包含多种样式

```python
def styled_text_block(segments):
    """segments: [{"text": "...", "style": {...}}, ...]"""
    elements = []
    for seg in segments:
        elements.append({
            "text_run": {
                "content": seg["text"],
                "text_element_style": seg.get("style", {})
            }
        })
    return {
        "block_type": 2,
        "text": {"elements": elements}
    }

# 示例：加粗"重要" + 普通文字
block = styled_text_block([
    {"text": "重要", "style": {"bold": True}},
    {"text": "：这是正文内容", "style": {}}
])
```

---

## 第四部分：删除块

### 批量删除（按索引范围）

```python
delete_url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/blocks/{doc_id}/children/batch_delete"

# 删除 index 28 到 34（不含 34）的子块
payload = {
    "start_index": 28,
    "end_index": 34
}

resp = requests.delete(delete_url, headers=headers, json=payload)
result = resp.json()
```

**⚠️ Pitfall：batch_delete 必须用 `start_index` + `end_index`，不能传 `block_ids` 列表。** 传 `block_ids` 会报 `field validation failed: start_index is required`。需要先通过 `GET /blocks` 获取根块的 `children` 列表，数出要删除的索引范围。

### 清空整个文档

```python
# 先获取根块的 children 数量
blocks_url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/blocks?page_size=500"
resp = requests.get(blocks_url, headers=headers)
blocks = resp.json()["data"]["items"]

root_block = next(b for b in blocks if b["block_type"] == 1)
child_count = len(root_block.get("children", []))

if child_count > 0:
    delete_url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/blocks/{doc_id}/children/batch_delete"
    payload = {"start_index": 0, "end_index": child_count}
    requests.delete(delete_url, headers=headers, json=payload)
```

---

## 第五部分：更新块内容（PATCH — 逐词精修样式）

### 核心理念：读-改-补，不要删-建

当文档已有内容需要修改样式时，**用 PATCH 更新现有块，不要删除后重建**。删除重建会丢失 block_id、打乱文档结构、且效率低。PATCH 可以精确到**词级**控制每个 text_run 的样式。

### PATCH API 用法

```python
block_id = "要更新的块 ID"
update_url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/blocks/{block_id}"

payload = {
    "update_text_elements": {
        "elements": [
            {"text_run": {"content": "新内容", "text_element_style": {}}}
        ]
    }
}

resp = requests.patch(update_url, headers=headers, json=payload)
```

### 逐词精修样式（关键技巧）

一个块可以包含多个 text_run，每个 text_run 有独立的 `text_element_style`。将一句话拆分成多个 text_run，即可对每个词/短语单独设置样式：

```python
N = lambda: {}          # 普通文字
B = lambda: {"bold": True}           # 仅加粗
BG = lambda c: {"bold": True, "background_color": c}  # 加粗+背景色

def patch_block(block_id, elements, doc_id, headers):
    """elements: [(content, style), ...]"""
    url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/blocks/{block_id}"
    payload = {"update_text_elements": {"elements": [
        {"text_run": {"content": c, "text_element_style": s}} for c, s in elements
    ]}}
    r = requests.patch(url, headers=headers, json=payload)
    return r.json().get("code") == 0

# 示例：一句话中精确标记关键词
patch_block("doxcnXXX", [
    ("📌 可能性推理的常考题型包括", N()),           # 普通
    ("削弱型、加强型、前提型", B()),                 # 加粗
    ("，其中", N()),                                # 普通
    ("削弱型和加强型", BG(5)),                       # 加粗+绿色背景（加强方法）
    ("是", N()),                                    # 普通
    ("重点题型", B()),                              # 加粗
    ("。", N()),                                    # 普通
], doc_id, headers)
```

### 批量 PATCH（逐块修改样式）

```python
import time

def batch_patch(updates, doc_id, headers, delay=0.08):
    """updates: [(block_id, [(content, style), ...]), ...]"""
    ok = fail = 0
    for block_id, elements in updates:
        url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/blocks/{block_id}"
        payload = {"update_text_elements": {"elements": [
            {"text_run": {"content": c, "text_element_style": s}} for c, s in elements
        ]}}
        try:
            r = requests.patch(url, headers=headers, json=payload)
            if r.json().get("code") == 0:
                ok += 1
            else:
                fail += 1
        except:
            fail += 1
        time.sleep(delay)  # 防限频
    return ok, fail
```

**完整可复用脚本**：`references/batch-patch-styling.py` — 含认证、按内容搜索 block_id（避免硬编码出错）、批量 PATCH + 自动重试失败块、样式覆盖率统计。

### 背景色语义化约定（学习笔记专用）

用户学习笔记中背景色的含义约定，后续写入/修改时统一遵循：

| 背景色 | 值 | 用途 | 例子 |
|--------|-----|------|------|
| 🟢 绿色 | 5 | 加强方法、解题技巧 | "解释因果"、"搭桥"、"缺啥补啥" |
| 🔴 红色 | 1 | 削弱方法、注意事项、排除项 | "因果倒置"、"无关选项"、"刀子方向不可改变" |
| 🔵 蓝色 | 7 | 定义、特征、核心概念 | "必要条件"、"截面"、"全部求同" |
| 🟠 橙色 | 4 | 口诀、关键结论 | "轮廓定视角，线条找对应"、"0也是一个要素" |

---

## 第六部分：完整工作流 — 重写文档大纲

```python
def rewrite_document(doc_id, headers, new_blocks):
    """清空文档并写入新内容"""
    # 获取当前 children 数量
    blocks_url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/blocks?page_size=500"
    resp = requests.get(blocks_url, headers=headers)
    blocks = resp.json()["data"]["items"]
    root = next(b for b in blocks if b["block_type"] == 1)
    child_count = len(root.get("children", []))

    # 清空
    if child_count > 0:
        delete_url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/blocks/{doc_id}/children/batch_delete"
        requests.delete(delete_url, headers=headers,
                        json={"start_index": 0, "end_index": child_count})

    # 写入
    create_url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/blocks/{doc_id}/children"
    resp = requests.post(create_url, headers=headers,
                         json={"index": 0, "children": new_blocks})
    return resp.json()
```

---

## 第七部分：用户格式偏好

### 标题与结构
- **去掉冗余编号**：不要写"第X章""第X节"，直接用标题文字 + 标题层级（H1/H2/H3）体现分级
- **标题层级清晰**：篇 → H1，章 → H2，节 → H3
- **子层级用 H4/H5**：如"（一）常见加强项"→ H4，"1.解释因果"→ H5

### 内容保留
- **不删减文字**：用户明确要求"不要删减文字"时，讲义/资料内容原样写入

### ⚠️ 样式精修哲学（用户强烈偏好 — 违反会被批评）

用户对加粗和背景色的使用有严格要求：**精确到词级，不要整句糊上去**。

**核心原则：**
1. **分析每句话的真正重点**：一句话中可能只有2-3个词是关键，其余是解释性文字。只给那2-3个词加粗/加背景色。
2. **加粗 ≠ 整句加粗**：加粗用于标记关键术语、方法名、题型名称，不是给整句话标记重点。
3. **背景色更克制**：背景色用于最核心的考点（每句话最多1-2个词组），不是给整段文字染色。
4. **普通文字要有**：一句话中大部分文字应该是普通样式，只有关键词带样式。如果一句话90%都是加粗，等于没有加粗。

**反例（❌ 错误做法）：**
```
📌 可能性推理的常考题型包括削弱型、加强型、前提型、结论型、解释型、评价型，其中削弱型和加强型是重点题型。
→ 整句加粗 + 整句背景色 = 看不出重点
```

**正例（✅ 正确做法）：**
```
📌 可能性推理的常考题型包括 [削弱型、加强型、前提型、结论型、解释型、评价型](加粗)，其中 [削弱型和加强型](加粗+绿底) 是 [重点题型](加粗)。
→ 六种题型加粗，削弱加强额外绿底，重点题型加粗，其余普通
```

**判断标准**：修改后，打开文档扫一眼，重点词是否**一目了然**？如果满屏都是加粗/背景色，说明没有真正分析重点。

---

## 第八部分：在特定标题下插入内容

标题块（Heading1-9）支持 children，可以直接在标题块下创建子内容块。这是将讲义内容放到对应章节标题下的关键操作。

```python
# 1. 获取所有块，建立 标题文本 → block_id 映射
blocks_url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/blocks?page_size=500"
resp = requests.get(blocks_url, headers=headers)
blocks = resp.json()["data"]["items"]

heading_map = {}
for b in blocks:
    if b["block_type"] in [3, 4, 5, 6, 7, 8, 9, 10, 11]:  # Heading1-9
        text = get_block_text(b)
        heading_map[text] = b["block_id"]

# 2. 在"加强型与削弱型"标题下插入内容
target_id = heading_map["加强型与削弱型"]
create_url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/blocks/{target_id}/children"
payload = {"index": 0, "children": [text_block("内容1"), text_block("内容2")]}
resp = requests.post(create_url, headers=headers, json=payload)
```

### 批量插入（超过 40 个块时分批）

飞书 API 单次创建块有数量限制，超过时需分批插入：

```python
def insert_blocks(doc_id, parent_block_id, texts, headers, batch_size=40):
    """分批插入文本块到指定父块下"""
    inserted = 0
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        children = [make_text(t) for t in batch]
        url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/blocks/{parent_block_id}/children"
        payload = {"index": inserted, "children": children}
        resp = requests.post(url, headers=headers, json=payload)
        if resp.json().get("code") != 0:
            return False
        inserted += len(batch)
    return True
```

### 流水账追加模式（标题作分节容器，最新在上）

把标题块当"分节容器"：H2=分类节，条目作为标题的 children 插入。**新条目 POST 到该标题 children 的 `index=0`，即实现"最新在最上"**，同节旧条目自动下移，互不影响。适合错题库、流水笔记类"文档当数据库"用法（2026-09 错题归档文档验证：H1模块 → H2题型节 → H3条目+记录块，15块一次 POST 成功）。注意 divider 不能作标题 children，条目间分隔靠下一级标题块。

---

## 第九部分：从 PPTX 提取内容写入文档

### 安装依赖

```bash
cd ~/.hermes/hermes-agent && uv pip install python-pptx
```

**注意**：`pip` 命令在此环境不存在，用 `uv pip install` 代替。

### 提取 PPTX 文本

```python
from pptx import Presentation

def extract_pptx(path):
    prs = Presentation(path)
    slides = []
    for i, slide in enumerate(prs.slides, 1):
        texts = []
        for shape in slide.shapes:
            if shape.has_text_frame:
                for para in shape.text_frame.paragraphs:
                    text = para.text.strip()
                    if text:
                        texts.append(text)
            elif shape.shape_type == 6:  # group shape
                for sub in shape.shapes:
                    if sub.has_text_frame:
                        for para in sub.text_frame.paragraphs:
                            text = para.text.strip()
                            if text:
                                texts.append(text)
        if texts:
            slides.append({"slide": i, "texts": texts})
    return slides
```

### 写入文档的流程

1. 提取 PPTX 每张幻灯片的文本
2. 对照文档大纲标题，将每张幻灯片的内容对应到正确的标题块
3. 用 `insert_blocks()` 在对应标题块下批量写入
4. **原样保留文字，不删减、不摘要**

- `templates/extract_pptx_to_feishu.py` — PPTX 提取文本写入飞书文档的完整模板脚本

---

## 第十部分：Pitfalls

| 问题 | 原因 | 修复 |
|------|------|------|
| `feishu_doc_read` 工具报 "not in a Feishu comment context" | 该工具仅在飞书评论上下文中可用 | 直接用 requests 调 docx/v1 API |
| `batch_delete` 报 `field validation failed: start_index is required` | 传了 `block_ids` 列表，但 API 要求 `start_index` + `end_index` | 改用索引范围删除 |
| `execute_code` 中 `os.path.expanduser("~")` 路径错误 | cron 环境下 HOME 指向 profile home | 直接用绝对路径（发现顺序见 references/credentials.md） |
| 创建块后文档底部残留旧内容 | 新块从 index=0 插入，旧块被推到后面 | 创建前先清空文档，或创建后按索引删除尾部旧块 |
| 文档 URL 中的 doc_id 提取 | URL 格式 `https://xxx.feishu.cn/docx/<doc_id>` | 取 `/docx/` 后面的路径段 |
| 用户说"写入文档"但 agent 发了飞书卡片 | 混淆了"编辑文档"和"发卡片"两个概念 | "写入文档/建立大纲/编辑文档" = 用 docx API 编辑文档内容；"发卡片/发消息" = 用 interactive card |
| Python 字符串含中文引号 `""` 导致 SyntaxError | 中文引号 `"` (U+201C) 和 `"` (U+201D) 在 Python 字符串中被解释为字符串边界 | 用 unicode 转义 `\u201c` `\u201d`，或用不同引号包裹（外层双引号时内层用单引号） |
| `pip: command not found` | hermes-agent venv 中没有 pip 命令 | 用 `uv pip install python-pptx` 代替 |
| `ModuleNotFoundError: No module named 'pptx'` | python-pptx 未安装 | `cd ~/.hermes/hermes-agent && uv pip install python-pptx` |
| 大量文本块一次性插入失败 | API 单次创建块数量限制 | 分批插入，每批 ≤40 个块（见第九部分 `insert_blocks`） |
| 新块插入后旧内容残留在文档底部 | 新块从 index=0 插入，旧块被推到后面 | 创建前先清空文档，或创建后用 batch_delete 按索引删除尾部旧块 |
| PATCH 返回 `1770002: not found` | 频率过高被限流，或 block_id 错误 | 加 `time.sleep(0.08-0.15)` 间隔；若仍失败，用 GET /blocks 搜索内容文本确认 block_id 是否变化 |
| block_id 写错一个字符导致 PATCH 404 | 从控制台复制 block_id 时可能看错字符（如 `f` vs `h`） | 不要硬编码 block_id；每次 PATCH 前用 GET /blocks 按内容文本搜索获取最新 block_id |
| `execute_code` 中 `\\u{1F4CC}` 报 SyntaxError | Python 不支持 `\\u{XXXX}` 语法（这是 Rust/JS 语法） | 直接写 emoji 字符（如 📌），或用 `\\U0001F4CC`（大写 U + 8位十六进制） |
| 批量 PATCH 中含中文引号的块报 `invalid param` | 中文引号 `\\u201c` `\\u201d` 在 Python 字符串拼接中可能干扰 JSON 序列化 | 用 `json.dumps()` 时设 `ensure_ascii=False`；或在 text_run content 中用 `\\u201c` / `\\u201d` 转义 |
| 用户批评"整句加粗/整句背景色，看不出重点" | 没有逐词分析重点，而是粗暴地给整句加样式 | 用 PATCH 逐词精修：分析每句话的真正关键词，只给关键词加粗/背景色（见第七部分"样式精修哲学"） |
| 用户要求修改样式时清空重建而非 PATCH | 没意识到 PATCH 可以精确到词级修改现有块 | **读-改-补 > 删-建**：GET 现有块 → PATCH 修改 text_run 样式，不删除不重建（见第五部分） |
| 新建空文档自带 1 个空文本占位块（block_type=2、text 为空），首次搭结构会残留 | 飞书新建 docx 默认有一个空段落 | 初始化前先 GET /blocks 检查根 children，batch_delete 清掉空占位块再建结构；结构写完后再 GET /blocks 按 block_type+文本遍历 children 树验证层级是否齐全（2026-09 验证） |
| `POST /children` 插入 `divider` 块（block_type 19）返回 `1770001 invalid param` | divider 块只能存在于文档根层（Page 的直接子块），不能作为 Heading 或其他块的 children 插入 | **替代方案**：用一条带样式的文本块模拟分隔线，如 `{"text": "━━━━━━━━━━━━━━━", "style": {"background_color": 4}}` 或用 bullet 块 `{"text": "—"}` 做视觉分隔。已在「查找细节」章节验证可行。 |
| `POST `/children/batch_create` 返回 404 | 该端点**不存在**。飞书 docx API 没有 `batch_create` 后缀 | 正确端点是 `POST /blocks/{parent_id}/children`，body 中带 `{"index": N, "children": [...]}`。见第八部分正确用法。**每次写块都只用 `/children`，永不用 `/batch_create`。** |
| `background_color` 传 hex 字符串如 `"#FFFF00"` | 早期版本的误传。API 静默忽略无效值 | `background_color` **必须是数字 1-7**，对应：1=红 2=紫 3=橙 4=青 5=绿 6=粉 7=蓝。详见第三部分颜色值映射表。**任何地方看到 `#RRGGBB` 格式都是错的。** |
| 跨 session 复用硬编码 block_id 导致 404 | block_id 在不同会话/时间可能变化，或之前记录的是截断值 | **永远不要硬编码 block_id**。每次操作前用 `GET /blocks` 按**内容文本搜索**获取最新 block_id（见第八部分示例）。 |
| `text_element_style` 中 `}}` 导致 Python SyntaxError | `execute_code` 中嵌套 JSON 字典时 `}}` 被解析器截断 | 将 style 提取为单独变量：`style = {"bold": True, "background_color": 5}; return {"text_run": {"content": text, "text_element_style": style}}` |
| 单行嵌套 JSON 丢闭合大括号 | 把多层嵌套字典写在一行时，容易漏掉一个 `}`。Python 报错信息很迷惑（`']' does not match '{'`，指向错误位置） | 写完后用 `line.count('{') vs line.count('}')` 验证；复杂结构拆成多行；提取为变量减少嵌套 |
| 中文引号 `\u201c` `\u201d` 在 Python 字符串中被当字符串边界 | PPT 内容含中文引号 `"..."`，在 Python 双引号字符串中会被解释为字符串结束符 | 用转义 `\u201c` `\u201d`；或用单引号包裹含中文引号的字符串；中文省略号 `\u2026` 用 `\u2026\u2026` 转义（write_file lint 会误报） |
| 单行函数定义漏写 `}` | 5层嵌套的 `{}` 极易少写一个，如 `h4` 函数写成 `return {"block_type": 6, "heading4": {"elements": [{"text_run": {"content": text, "text_element_style": {}}]}}` —— 5个 `{` 但只有4个 `}` | **排查**：`line.count('{')` vs `line.count('}')` 比差值。**预防**：深层嵌套拆成多行或用变量逐步构建，不要写一行。Python 3.11 的错误信息会指向错误位置的列号，跟随 `^` 箭头定位。 |
| 插入块时用根 doc_id 作 parent，但返回「找不到 insert_before 块」 | 标题块可以是其他标题块的子块（如 H3 是 H2 的 child），`find_index_in_parent` 必须在**实际 parent** 的 children 列表中查找 | 先查 `block_map[child_id][parent_id]` 获取实际 parent，再用该 parent 的 children 列表找 index。部分 heading 有大量 children（如 H3 有 69 个 child），部分 heading children=0 |
| 批量顺序插入多个块后，后续块的 index 错位 | 每次插入后后续块 index 递增，先插 idx=7 再插 idx=18 会变成 idx=19 | 两种解法：(a) 每次插入后 GET /blocks 刷新 block_map；(b) **从后往前插**（先插大 index 再插小 index），前面 index 不受影响 |
| GET /blocks?page_size=500 的 items 列表中找不到某个块 | API 分页限制或块在子块 children 中 | 用 GET /blocks/{block_id} 单独获取（即使不在列表中也能正常返回），用于验证块是否存在 |
