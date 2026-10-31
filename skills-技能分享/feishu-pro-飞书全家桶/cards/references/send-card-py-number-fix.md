# `send_card.py` 模板修复：`number` data_type 导致 code=230099

## 问题现象

`send_card.py` 的 `parse_pipe_table` 函数在转换含数字的表格列时，会自动推断 `data_type: "number"`。但单元格值仍为字符串类型（如 "74.32"、"63.38"）。飞书 API 对 `number` 类型严格校验，要求值的类型与 schema 严格匹配，导致：

```
飞书 API 返回：code=230099, msg=table rows is invalid, row idx:1, column idx:2
```

## 触发条件

表格含以下内容的列时会触发：
- 纯数字（如收盘价 "74.32"、涨跌额 "-3.26"）
- 含百分号（如 "-1.45%"）
- 含前导零（如股票代码 "002046"）

## 修复位置

文件：`templates/send_card.py`  
函数：`parse_pipe_table`  
位置：`# 推断 data_type` 部分（约第 170 行附近）

## 修复代码

**原始代码（v2.0.x）：**
```python
    # 推断 data_type
    for i, col in enumerate(columns):
        all_numeric = True
        has_markdown_link = False
        for row in rows:
            val = row[col["name"]]
            if val and not re.match(r'^-?\d+\.?\d*$', val):
                all_numeric = False
            if re.search(r'\[.+?\]\(.+?\)', val):
                has_markdown_link = True
        if has_markdown_link:
            col["data_type"] = "lark_md"
        elif all_numeric and any(row[col["name"]] for row in rows):
            col["data_type"] = "number"
```

**修复后代码（v2.1.0）：**
```python
    # 推断 data_type（v2.1.0: 默认全部使用 "text"，不再自动推断 "number"）
    # 原因：飞书 API 对 data_type "number" 严格校验，字符串形式的数字（如 "74.32"）会触发 code=230099
    for i, col in enumerate(columns):
        has_markdown_link = False
        for row in rows:
            val = row[col["name"]]
            if re.search(r'\[.+?\]\(.+?\)', val):
                has_markdown_link = True
                break
        if has_markdown_link:
            col["data_type"] = "lark_md"
        # 否则保持 "text"（默认值）
```

## 关键变更

1. **移除** `all_numeric` 逻辑 — 不再将纯数字列设为 `"number"`
2. **保留** `"lark_md"` 推断 — 含 Markdown 链接的列仍使用 `"lark_md"`
3. **默认** `"text"` — 所有其他列使用 `"text"`

## 影响范围

- 股票代码列（如 "002046"）不会因前导零被误判为数字
- 涨跌幅列（如 "-1.45%"）不会因百分号被误判为数字
- 收盘价列（如 "74.32"）不会因字符串形式被 API 拒绝

## 手动修复方法

如果模板未升级到 v2.1.0，发送前可强制修改 JSON：

```python
for card in cards:
    for elem in card.get("body", {}).get("elements", []):
        if elem.get("tag") == "table":
            for col in elem["columns"]:
                if col["data_type"] == "number":
                    col["data_type"] = "text"
```
