# collapsible_panel（折叠面板）组件参考

> 2026-07-04 从飞书开放平台文档提取并实测验证

## JSON 2.0 结构

```json
{
  "tag": "collapsible_panel",
  "expanded": false,
  "element_id": "custom_id",
  "header": {
    "title": {"tag": "markdown", "content": "**面板标题**"},
    "background_color": "grey",
    "padding": "4px 0px 4px 8px",
    "vertical_align": "center",
    "width": "auto",
    "icon": {"tag": "standard_icon", "token": "icon_name", "color": "orange"}
  },
  "background_color": "grey",
  "border": {"color": "grey", "corner_radius": "5px"},
  "elements": [{"tag": "markdown", "content": "折叠内容"}]
}
```

## 关键属性

| 字段 | 必填 | 类型 | 默认值 | 说明 |
|------|------|------|--------|------|
| `tag` | 否 | string | / | 固定 `"collapsible_panel"` |
| `expanded` | 否 | Boolean | `false` | `true`=展开, `false`=折叠 |
| `element_id` | 否 | String | 空 | 全局唯一标识，字母开头，≤20字符 |
| `header` | **是** | Object | / | 标题设置 |
| `header.title` | 否 | Object | / | `plain_text` 或 `markdown` |
| `header.background_color` | 否 | String | 透明 | 标题区背景色，不设时继承 `background_color` |
| `header.width` | 否 | String | `fill` | `fill`=等宽, `auto`=自适应, `auto_when_fold`=折叠时自适应 |
| `header.icon` | 否 | Object | / | 标题前缀图标 |
| `background_color` | 否 | String | 透明 | 面板背景色 |
| `border` | 否 | Object | / | `color`+`corner_radius`，默认不显示 |
| `elements` | — | Array | / | 面板内组件，不支持 `form`，最多5层嵌套 |

## 使用限制

- **不支持卡片搭建工具**，只能手写 JSON
- **不支持**内嵌 `form` 组件
- 容器嵌套最多5层
- 建议避免多层嵌套（压缩展示空间）

## 实际使用示例（qyq-panqian 日历卡片）

```python
collapsible("**📌 7月8日 周二**（点击展开）", [
    md("**🌐 中国互联网大会**\n　7月8-10日，北京"),
    md("**🛢️ EIA月度短期能源展望**\n　美国能源信息署公布"),
], expanded=False)
```

实测：2026-07-04 发送成功，飞书客户端正常显示折叠/展开。

## 官方文档

https://open.feishu.cn/document/uAjLw4CM/ukzMukzMukzM/feishu-cards/card-json-v2-components/containers/collapsible-panel
