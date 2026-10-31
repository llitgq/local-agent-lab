# 管道表格（Pipe Table）Pitfalls

## `|` 管道符导致单元格数据截断

**现象**：表格某列内容包含 `|` 时，列数据被截断或错位。

**根因**：`send_card.py` 的 `parse_pipe_table` 函数使用 `dl.split("|")` 切分单元格。内容中的 `|` 会被误当成分隔符。

**修复**：表格单元格内容中禁止使用半角 `|`。替换方案：
- `·`（中间点）— 最推荐，视觉上简洁
- `｜`（全角竖线）— 语义最接近
- `—`（em dash）— 适合分隔并列内容
- `/` 或 `&` — 适合并列关系

**示例**：
```
# ❌ 错误 — 穿衣建议列被截断
| 建议 | 薄外套|长裤，带伞 |

# ✅ 正确 — 用 · 替代 |
| 建议 | 薄外套·长裤，带伞 |
```

## 手动构建 Table 组件 JSON 时加 `width` 导致发送失败（2026-07-06 发现）

**现象**：手动构建卡片 JSON 调用飞书 API，报 `code=230099, ext=200621: expected string for width, but: 100`。

**根因**：飞书 `table` 组件的列对象不支持 `width` 字段（或要求为字符串但行为未定义）。`send_card.py` 的 `parse_pipe_table` 已正确只输出 `name`/`display_name`/`data_type` 三个字段。

**修复**：手动构建列时**不传 width**：
```python
# ❌ 导致 230099/200621 失败
columns.append({"name": "col_0", "display_name": "日期", "data_type": "text", "width": 100})

# ✅ 正确
columns.append({"name": "col_0", "display_name": "日期", "data_type": "text"})
```

## 其他注意事项

- 管道表格最多 4 个/markdown 元素，每表最多 5 行可见（超出自动分页）
- 表格最多 5 个/卡片
- `parse_pipe_table` 会去除首尾的 `|`，所以 `| a | b |` 和 `a | b` 等价
