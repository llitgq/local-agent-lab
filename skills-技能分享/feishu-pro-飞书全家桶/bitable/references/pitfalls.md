# 飞书 Bitable 踩坑记录

## 1. write_file 工具会损坏含 URL 的 .py 文件

`write_file` 工具在写入 Python 文件时，会截断类似 URL 的字符串（如飞书 API 地址 `https://open.feishu.cn/...`）。写入后返回 `bytes_written` 看起来成功，但文件内容被静默截断。

**修复：** 编辑含 URL 的 .py 文件时，必须使用：
- `terminal` 的 heredoc：`cat > file << 'EOF'` ... `EOF`
- `execute_code`：`open(path, "w").write(content)`

**绝对不要用 `write_file` 写含飞书 API URL 的 .py 文件。**

写完后务必用 `read_file` 验证前几行内容是否正确。此问题已多次触发，不可忽视。

## 2. 飞书情绪分字段返回 string 类型

即使在飞书 UI 上看起来是数字，API 返回的是 `"6"`（字符串）不是 `6`（整数）。读取时需要类型转换：

```python
if isinstance(score, str) and score.strip().isdigit():
    score = int(score)
```

## 3. 飞书 API 排序不支持中文字段名

使用 sort 参数时传中文字段名会返回 `InvalidSort` 错误，传 field_id 也可能失败。

**修复：** 去掉 sort 参数，使用 `page_size=500` 取全部记录，然后在代码中排序或取 `items[-1]`。

## 4. execute_code 沙盒的 cwd 不是项目目录

在 `execute_code` 中使用 `sys.path.insert` 时必须用绝对路径，不能使用相对路径。

```python
# ❌ 错误
sys.path.insert(0, "scripts")
# ✅ 正确
sys.path.insert(0, "<你的脚本目录>")
```

## 5. QWeather API Key 返回 403

从和风天气 Web 控制台获取的 API Key 在直接 HTTP 调用时返回 403 Invalid Host。可能原因：
- Key 是 Web API 专用的，需要 JWT 认证而非直接传 key
- `devapi.qweather.com` 域名对当前 key 无权限

**替代方案：** 使用 wttr.in（免费、无需 key），通过 `curl` 命令调用以绕过系统 Python 3.9 的 SSL 版本限制。
