# 飞书卡片 JSON 2.0 规范参考

## 卡片整体结构

```json
{
  "schema": "2.0",
  "config": {
    "wide_screen_mode": true
  },
  "header": {
    "title": {"content": "标题", "tag": "plain_text"},
    "subtitle": {"content": "副标题", "tag": "plain_text"},
    "template": "blue",
    "ud_icon": {"tag": "standard_icon", "token": "icon_name"}
  },
  "body": {
    "direction": "vertical",
    "padding": "12px 12px 12px 12px",
    "elements": [...]
  }
}
```

**关键：JSON 2.0 用 `body.elements`，不是顶层的 `elements`！**

## 可用颜色（header.template）

| 颜色 | 值 |
|------|-----|
| 蓝色 | `blue` |
| 浅蓝 | `wathet` |
| 青绿 | `turquoise` |
| 绿色 | `green` |
| 黄色 | `yellow` |
| 橙色 | `orange` |
| 红色 | `red` |
| 胭脂红 | `carmine` |
| 紫罗兰 | `violet` |
| 紫色 | `purple` |
| 靛蓝 | `indigo` |
| 灰色 | `grey` |
| 默认 | `default` |

## body.elements 支持的组件

### markdown（富文本）

```json
{
  "tag": "markdown",
  "content": "支持完整 Markdown 语法",
  "text_align": "left"
}
```

支持语法：h1-h6、加粗、斜体、删除线、超链接、代码块、有序/无序列表、引用、图片、分割线、飞书表情、标签、管道表格（最多4个/元素，5行/表）

### table（结构化表格）

```json
{
  "tag": "table",
  "page_size": 10,
  "row_height": "low",
  "header_style": {
    "text_align": "left",
    "background_style": "grey",
    "bold": true
  },
  "columns": [
    {"name": "col_name", "display_name": "显示名", "data_type": "text"}
  ],
  "rows": [
    {"col_name": "值"}
  ]
}
```

**data_type 可选值：** `text`、`lark_md`、`markdown`、`number`、`options`、`persons`、`date`

**header_style.background_style：** `grey`、`blue`、`green`、`yellow`、`red`、`violet`、`default`

> ⚠️ **列字段注意事项（2026-07-06 经验总结）**
> 飞书 API table 列只接受以下合法字段：`name`（必填，列唯一标识）、`display_name`（必填，显示名称）、`data_type`（必填，列类型）。
> ❌ **不支持 `width` 字段**：传入整数 `"width": 100` 会报错 `200621: expected string for width, but: 100`，传入字符串也大概率无效。
> ❌ **不支持其他非标准字段**：飞书 API 对列字段有严格校验，多余字段会触发 230099（JSON 格式错误）。
> **正确做法：列只传三个字段：**
> ```python
> columns.append({
>     "name": "col_0",
>     "display_name": "列名",
>     "data_type": "text"   # 或 lark_md / number
> })
> ```
> ✅ `send_card.py` 的 `parse_pipe_table` 函数已是正确参考实现，直接复用。

### hr（分割线）

```json
{"tag": "hr"}
```

### button（按钮，可选）

```json
{
  "tag": "button",
  "text": {"tag": "plain_text", "content": "按钮文字"},
  "type": "default",
  "size": "medium",
  "behaviors": [{"type": "open_url", "default_url": "https://..."}]
}
```

> ⚠️ **header 图标字段(2026-10-11 实测)**:JSON 2.0 下自定义图标用 `"icon": {"tag": "standard_icon", "token": "..."}`。
> 文档旧写法 `ud_icon` 会被 API 拒绝:`200621 unknown property: ud_icon`(实测于本机)。

## 限制汇总

| 项目 | 限制 |
|------|------|
| 卡片请求体 | 30 KB |
| 组件总数 | 200 个 |
| table 组件 | 5 个/卡片 |
| 每个 table 列数 | 50 列 |
| 每个 table 每页行数 | 10 行（page_size 1-10） |
| markdown 内管道表格 | 4 个/markdown 元素 |
| 管道表格每表可见行 | 5 行（超出自动分页） |
| 标题后缀标签 | 3 个 |

### collapsible_panel（折叠面板）

```json
{
  "tag": "collapsible_panel",
  "expanded": false,
  "header": {
    "title": {
      "tag": "plain_text",
      "content": "面板标题（点击展开）"
    },
    "background_color": "grey",
    "padding": "4px 8px 4px 8px",
    "vertical_align": "center"
  },
  "elements": [
    {"tag": "markdown", "content": "折叠内容..."}
  ]
}
```

- `expanded`: true=展开, false=折叠（默认false）
- `header.title`: 标题，支持 `plain_text` 和 `markdown`
- `header.background_color`: 标题区背景色
- `header.icon`: 可选前缀图标，`tag: "standard_icon"`, `token: "icon_token"`, `color: "orange"`
- `header.icon_position`: 图标位置，默认 `"right"`
- `header.icon_expanded_angle`: 展开时图标旋转角度，默认180，负值逆时针
- `elements[]`: 面板内容，支持任意展示组件，**不支持 form 组件**
- `background_color`: 面板背景色
- `border.color`: 边框颜色, `border.corner_radius`: 圆角
- 容器嵌套最多5层，建议不在折叠面板内嵌套多层组件
- **仅支持 JSON 代码构建，不支持卡片搭建工具**

## JSON 2.0 不支持的组件

- ❌ `note` 标签（会报错 code=200861）
- ❌ 旧版 `elements` 顶层结构（必须用 `body.elements`）
