# ============================================================
# tools-feishu-cards-v2 / templates/send_card_v2.py
# Markdown → 飞书卡片（JSON 2.0 interactive）自动转换 + 发送
# v2 新增：collapsible_panel（折叠面板）支持
# ============================================================
# 调用入口：smart_send_v2(text, title, receive_id, ...)
# ============================================================

import os
import re
import json
import sys
import uuid
from pathlib import Path

# ---- 依赖 ----
# lark_oapi SDK（Hermes 已内置）
# 动态推断 Hermes 路径
_hermes_home = os.environ.get("HERMES_HOME", "")
if _hermes_home and ("/profiles/" in _hermes_home or "\\profiles\\" in _hermes_home):
    _hermes_agent = str(Path(_hermes_home).parent.parent)
else:
    _hermes_agent = str(Path.home() / ".hermes" / "hermes-agent")

if _hermes_agent not in sys.path:
    sys.path.insert(0, _hermes_agent)

import lark_oapi as lark
from lark_oapi.api.im.v1 import CreateMessageRequest, CreateMessageRequestBody

# ============================================================
# 配置区
# ============================================================

COLORS = ["blue", "turquoise", "violet", "green", "indigo", "orange"]

DEFAULT_MAX_CARD_SIZE    = 30000   # 30KB
MAX_TABLES_PER_CARD      = 5
MAX_ELEMENTS_PER_CARD    = 200
MAX_COLUMNS_PER_TABLE    = 50
MAX_PAGE_SIZE            = 10
MAX_NESTED_COLLAPSIBLES  = 5       # 折叠面板最大嵌套深度

# ============================================================
# 0. 折叠面板语法解析
# ============================================================

# 语法：
#   [collapse:标题]          → 折叠面板，默认收起
#   [collapse+:标题]         → 折叠面板，默认展开
#   [/collapse]              → 折叠面板结束
#   内容可以是任意 Markdown（段落、表格、代码块、列表等）

_COLLAPSE_OPEN_RE  = re.compile(r'^\s*\[collapse([+]?):(.+?)\]\s*$')
_COLLAPSE_CLOSE_RE = re.compile(r'^\s*\[/collapse\]\s*$')


def parse_collapsible_blocks(text: str) -> list:
    """
    第一遍扫描：将文本中的 [collapse:...][/collapse] 提取为结构化嵌套元素。
    
    返回列表，每项是以下类型之一：
    - {"type": "raw", "content": "未被折叠包裹的原始 Markdown"}
    - {"type": "collapse", "expanded": bool, "title": str, "body": str}
    
    body 内可能嵌套更深的 [collapse:...][/collapse]，递归处理在 parse_markdown_v2 中完成。
    """
    lines = text.split("\n")
    result = []
    raw_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]
        m = _COLLAPSE_OPEN_RE.match(line)
        if m:
            # 遇到折叠开始标记
            expanded = bool(m.group(1))  # "+" 表示展开
            title = m.group(2).strip()
            
            # 收集之前的 raw
            if raw_lines:
                result.append({"type": "raw", "content": "\n".join(raw_lines)})
                raw_lines = []
            
            # 找到匹配的 [/collapse]
            depth = 1
            body_lines = []
            i += 1
            while i < len(lines) and depth > 0:
                inner = lines[i]
                if _COLLAPSE_OPEN_RE.match(inner):
                    depth += 1
                elif _COLLAPSE_CLOSE_RE.match(inner):
                    depth -= 1
                    if depth == 0:
                        break
                body_lines.append(inner)
                i += 1
            
            result.append({
                "type": "collapse",
                "expanded": expanded,
                "title": title,
                "body": "\n".join(body_lines)
            })
            i += 1  # 跳过 [/collapse]
        else:
            raw_lines.append(line)
            i += 1
    
    if raw_lines:
        result.append({"type": "raw", "content": "\n".join(raw_lines)})
    
    return result


# ============================================================
# 1. 全角半角自动清洗（沿用 v1）
# ============================================================

def _looks_like_table_line(line: str) -> bool:
    stripped = line.strip()
    return bool(stripped) and stripped.startswith("|") and "|" in stripped[1:]


def clean_fullwidth(text: str) -> str:
    text = text.replace("\uff5c", "|")    # ｜ → |
    text = text.replace("\uff0d", "-")     # － → -
    text = text.replace("\u3000", " ")     # 　 → (space)

    lines = text.split("\n")
    result = []
    prev_is_table = False

    for i, line in enumerate(lines):
        curr_is_table = _looks_like_table_line(line)

        if curr_is_table and not prev_is_table:
            if result and result[-1].strip():
                result.append("")

        result.append(line)

        if prev_is_table and not curr_is_table:
            if line.strip():
                result.pop()
                result.append("")
                result.append(line)

        prev_is_table = curr_is_table

    return "\n".join(result)


# ============================================================
# 2. Markdown 解析（v2 增强：识别折叠面板元素）
# ============================================================

def is_table_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    if not stripped.startswith("|"):
        return False
    return "|" in stripped[1:]


def is_separator_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped.startswith("|"):
        return False
    cells = [c.strip() for c in stripped.split("|") if c.strip()]
    return all(re.match(r'^:?-+:?$', c) for c in cells)


def _split_table_row(line: str) -> list:
    parts = line.split("\\|")
    result = []
    for part in parts:
        sub_parts = part.split("|")
        if sub_parts:
            result.append(sub_parts[0])
        result.extend(sub_parts[1:])
    return [c.strip() for c in result]


def parse_pipe_table(lines: list) -> dict:
    if len(lines) < 2:
        return None

    header_line = lines[0].strip()
    if header_line.startswith("|"):
        header_line = header_line[1:]
    if header_line.endswith("|"):
        header_line = header_line[:-1]
    headers = _split_table_row(header_line)
    headers = [h.strip() for h in headers if h.strip()]

    data_lines = lines[2:]

    columns = []
    for i, h in enumerate(headers):
        columns.append({
            "name": f"col_{i}",
            "display_name": h,
            "data_type": "text"
        })

    rows = []
    for dl in data_lines:
        dl = dl.strip()
        if dl.startswith("|"):
            dl = dl[1:]
        if dl.endswith("|"):
            dl = dl[:-1]
        cells = _split_table_row(dl)
        cells = [c.strip() for c in cells]
        row = {}
        for i in range(len(columns)):
            val = cells[i] if i < len(cells) else ""
            val = val.replace("\\|", "|")
            row[columns[i]["name"]] = val
        rows.append(row)

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

    return {
        "tag": "table",
        "page_size": min(len(rows), MAX_PAGE_SIZE),
        "row_height": "low",
        "header_style": {
            "text_align": "left",
            "background_style": "grey",
            "bold": True
        },
        "columns": columns,
        "rows": rows
    }


def parse_markdown(text: str) -> list:
    """
    v2 核心：将 Markdown 文本解析为元素列表。
    新增支持 collapsible_panel 类型。
    
    元素类型：
    - {"type": "paragraph", "content": str}     — 普通文本/标题/列表/引用/代码块
    - {"type": "table", "content": dict}        — 管道表格（结构化 JSON）
    - {"type": "hr", "content": None}           — 分割线
    - {"type": "collapse", "expanded": bool, "title": str, "elements": list}  — 折叠面板（递归）
    """
    # 第一步：提取折叠块结构
    blocks = parse_collapsible_blocks(text)
    
    elements = []
    for block in blocks:
        if block["type"] == "collapse":
            # 递归解析折叠内部内容
            inner_elements = _parse_markdown_lines(block["body"].split("\n"), depth=1)
            elements.append({
                "type": "collapse",
                "expanded": block["expanded"],
                "title": block["title"],
                "elements": inner_elements
            })
        elif block["type"] == "raw":
            # 解析普通 Markdown
            raw_elements = _parse_markdown_lines(block["content"].split("\n"), depth=0)
            elements.extend(raw_elements)
    
    return elements


def _parse_markdown_lines(lines: list, depth: int) -> list:
    """
    解析普通 Markdown 行（不含折叠语法）。
    depth 用于控制折叠嵌套深度。
    """
    elements = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # 空行
        if not line.strip():
            i += 1
            continue

        # 分割线
        if line.strip() in ("---", "***", "___"):
            elements.append({"type": "hr", "content": None})
            i += 1
            continue

        # 代码块
        if line.strip().startswith("```"):
            code_lines = [line]
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            if i < len(lines):
                code_lines.append(lines[i])
                i += 1
            elements.append({"type": "paragraph", "content": "\n".join(code_lines)})
            continue

        # 折叠面板（嵌套递归）
        if depth < MAX_NESTED_COLLAPSIBLES:
            m = _COLLAPSE_OPEN_RE.match(line)
            if m:
                expanded = bool(m.group(1))
                title = m.group(2).strip()
                body_lines = []
                nest_depth = 1
                i += 1
                while i < len(lines) and nest_depth > 0:
                    inner = lines[i]
                    if _COLLAPSE_OPEN_RE.match(inner):
                        nest_depth += 1
                    elif _COLLAPSE_CLOSE_RE.match(inner):
                        nest_depth -= 1
                        if nest_depth == 0:
                            break
                    body_lines.append(inner)
                    i += 1
                
                inner_elements = _parse_markdown_lines(body_lines, depth + 1)
                elements.append({
                    "type": "collapse",
                    "expanded": expanded,
                    "title": title,
                    "elements": inner_elements
                })
                i += 1
                continue

        # 管道表格
        if is_table_line(line):
            table_lines = []
            while i < len(lines) and is_table_line(lines[i]):
                table_lines.append(lines[i])
                i += 1
            table_obj = parse_pipe_table(table_lines)
            if table_obj:
                elements.append({"type": "table", "content": table_obj})
            else:
                elements.append({"type": "paragraph", "content": "\n".join(table_lines)})
            continue

        # 普通段落
        para_lines = [line]
        i += 1
        while i < len(lines):
            next_line = lines[i]
            if not next_line.strip():
                break
            if next_line.strip() in ("---", "***", "___"):
                break
            if next_line.strip().startswith("```"):
                break
            if is_table_line(next_line):
                break
            if depth < MAX_NESTED_COLLAPSIBLES and _COLLAPSE_OPEN_RE.match(next_line.strip()):
                break
            para_lines.append(next_line)
            i += 1

        elements.append({"type": "paragraph", "content": "\n".join(para_lines)})

    return elements


# ============================================================
# 3. 构建卡片 JSON（v2 增强：支持 collapsible_panel）
# ============================================================

def extract_first_heading(text: str) -> str:
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("#") and not stripped.startswith("##"):
            title = stripped.lstrip("#").strip()
            if title:
                return title
    return ""


def _table_to_pipe_markdown(table_obj: dict) -> str:
    """将 table 对象降级为 markdown 管道语法文本"""
    cols = table_obj["columns"]
    rows = table_obj["rows"]
    header = "| " + " | ".join(c["display_name"] for c in cols) + " |"
    sep = "| " + " | ".join("---" for _ in cols) + " |"
    data_lines = []
    for row in rows:
        data_lines.append("| " + " | ".join(row.get(c["name"], "") for c in cols) + " |")
    return header + "\n" + sep + "\n" + "\n".join(data_lines)


def build_card_element(elem: dict, table_count: int = 0, inside_collapse: bool = False) -> tuple:
    """
    将单个解析元素转换为飞书卡片组件。
    返回 (component_dict_or_None, new_table_count)
    
    v2 新增：collapse 类型 → collapsible_panel 组件
    
    inside_collapse=True 时，table 自动降级为 markdown 管道文本
    （飞书 collapsible_panel 内部不支持 table 组件，ErrCode: 200621）
    """
    if elem["type"] == "hr":
        return {"tag": "hr"}, table_count
    
    elif elem["type"] == "table":
        # 折叠内部或卡片级表格超限 → 降级为 markdown 管道语法
        if inside_collapse or table_count >= MAX_TABLES_PER_CARD:
            pipe_text = _table_to_pipe_markdown(elem["content"])
            return {"tag": "markdown", "content": pipe_text}, table_count
        else:
            return elem["content"], table_count + 1
    
    elif elem["type"] == "collapse":
        # 递归构建内部元素（折叠内部 table 必须降级）
        inner_components = []
        inner_table_count = 0
        for child in elem["elements"]:
            comp, inner_table_count = build_card_element(child, inner_table_count, inside_collapse=True)
            if comp:
                inner_components.append(comp)
        
        panel = {
            "tag": "collapsible_panel",
            "expanded": elem["expanded"],
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": elem["title"]
                }
            },
            "elements": inner_components
        }
        return panel, table_count
    
    elif elem["type"] == "paragraph":
        return {"tag": "markdown", "content": elem["content"]}, table_count
    
    return None, table_count


def build_card(elements: list, title: str, template_color: str = "blue") -> dict:
    """
    v2：将元素列表组装为完整卡片 JSON 2.0。
    支持合并相邻 markdown、插入 table、hr、collapsible_panel。
    """
    card_elements = []
    md_parts = []

    def flush_md():
        nonlocal md_parts
        if md_parts:
            card_elements.append({
                "tag": "markdown",
                "content": "\n\n".join(md_parts)
            })
            md_parts = []

    table_count = 0
    for elem in elements:
        comp, table_count = build_card_element(elem, table_count)
        
        if comp is None:
            continue
        
        # 合并相邻 markdown
        if comp.get("tag") == "markdown":
            md_parts.append(comp["content"])
        else:
            flush_md()
            card_elements.append(comp)
    
    flush_md()

    # 去掉与卡片标题重复的一级标题
    if card_elements and card_elements[0].get("tag") == "markdown":
        first_md = card_elements[0]["content"]
        first_line = first_md.split("\n")[0].strip()
        if first_line.startswith("#") and not first_line.startswith("##"):
            clean_title = first_line.lstrip("#").strip()
            if clean_title == title:
                remaining = "\n".join(first_md.split("\n")[1:]).strip()
                if remaining:
                    card_elements[0]["content"] = remaining
                else:
                    card_elements.pop(0)

    card = {
        "schema": "2.0",
        "config": {"wide_screen_mode": True},
        "header": {
            "title": {"content": title, "tag": "plain_text"},
            "template": template_color,
        },
        "body": {
            "direction": "vertical",
            "elements": card_elements
        }
    }
    return card


# ============================================================
# 4. 限制检查
# ============================================================

def check_limits(card: dict) -> dict:
    card_json_str = json.dumps(card, ensure_ascii=False)
    size = len(card_json_str.encode("utf-8"))

    elements = card.get("body", {}).get("elements", [])
    elem_count = len(elements)
    table_count = sum(1 for e in elements if e.get("tag") == "table")

    errors = []
    if size > DEFAULT_MAX_CARD_SIZE:
        errors.append(f"JSON 大小 {size} 字节超过限制 {DEFAULT_MAX_CARD_SIZE}")
    if table_count > MAX_TABLES_PER_CARD:
        errors.append(f"表格数 {table_count} 超过限制 {MAX_TABLES_PER_CARD}")
    if elem_count > MAX_ELEMENTS_PER_CARD:
        errors.append(f"组件数 {elem_count} 超过限制 {MAX_ELEMENTS_PER_CARD}")

    return {
        "ok": len(errors) == 0,
        "size": size,
        "tables": table_count,
        "elements": elem_count,
        "error": "; ".join(errors) if errors else None
    }


# ============================================================
# 5. 拆分逻辑
# ============================================================

def _count_raw_tables(elements: list) -> int:
    return sum(1 for e in elements if e["type"] == "table")


def _count_raw_collapses(elements: list) -> int:
    """统计顶层折叠面板数量"""
    return sum(1 for e in elements if e["type"] == "collapse")


def _estimate_card_size(elements: list, title: str) -> int:
    text_size = 0
    for e in elements:
        if e["type"] == "table":
            cols = e["content"].get("columns", [])
            rows = e["content"].get("rows", [])
            text_size += sum(len(c["display_name"]) for c in cols)
            for row in rows:
                text_size += sum(len(str(v)) for v in row.values())
            text_size += 200
        elif e["type"] == "paragraph" and e["content"]:
            text_size += len(e["content"])
        elif e["type"] == "collapse":
            # 折叠面板：标题 + 内部内容 + 结构开销
            text_size += len(e["title"]) + 150  # 结构开销
            for child in e["elements"]:
                if child["type"] == "paragraph" and child["content"]:
                    text_size += len(child["content"])
                elif child["type"] == "table":
                    cols = child["content"].get("columns", [])
                    rows = child["content"].get("rows", [])
                    text_size += sum(len(c["display_name"]) for c in cols)
                    for row in rows:
                        text_size += sum(len(str(v)) for v in row.values())
                    text_size += 200
                elif child["type"] == "collapse":
                    text_size += 200  # 嵌套折叠的额外开销
        else:
            text_size += 20
    return text_size + len(title) + 500


def split_elements(elements: list, title: str) -> list:
    """
    v2 拆分逻辑：支持在 collapse 边界拆分（不拆开 collapse 内部）。
    """
    est_size = _estimate_card_size(elements, title)
    raw_tables = _count_raw_tables(elements)

    if raw_tables <= MAX_TABLES_PER_CARD and est_size <= DEFAULT_MAX_CARD_SIZE:
        test_card = build_card(elements, title, "blue")
        check = check_limits(test_card)
        if check["ok"]:
            return [elements]

    # 逐元素累积，遇到超限则拆分
    result = []
    current_chunk = []

    for elem in elements:
        test_chunk = current_chunk + [elem]
        chunk_tables = _count_raw_tables(test_chunk)
        chunk_size = _estimate_card_size(test_chunk, title)

        if chunk_tables > MAX_TABLES_PER_CARD or chunk_size > DEFAULT_MAX_CARD_SIZE:
            if current_chunk:
                result.append(current_chunk)
            current_chunk = [elem]
        else:
            current_chunk.append(elem)

    if current_chunk:
        result.append(current_chunk)

    return result


# ============================================================
# 6. 发送到飞书（沿用 v1）
# ============================================================

def send_to_feishu(card: dict, receive_id: str, receive_id_type: str = "chat_id",
                   app_id: str = None, app_secret: str = None) -> dict:
    _app_id = app_id or os.environ.get("FEISHU_APP_ID", "")
    _app_secret = app_secret or os.environ.get("FEISHU_APP_SECRET", "")

    if not _app_id or not _app_secret:
        # 凭证文件候选顺序遵循 references/credentials.md 规范:
        # 1) $HERMES_HOME/.env(当前实例根,含 default 非 profile 部署)
        # 2) ~/.hermes/.env(老式安装兜底)
        env_candidates = []
        hermes_home = os.environ.get("HERMES_HOME", "")
        if hermes_home:
            env_candidates.append(os.path.join(hermes_home, ".env"))
        env_candidates.append(os.path.expanduser("~/.hermes/.env"))

        for env_path in env_candidates:

            if os.path.exists(env_path):
                with open(env_path, "r") as f:
                    for line in f:
                        line = line.strip()
                        if "=" in line and not line.startswith("#"):
                            k, v = line.split("=", 1)
                            if k == "FEISHU_APP_ID" and not _app_id:
                                _app_id = v
                            elif k == "FEISHU_APP_SECRET" and not _app_secret:
                                _app_secret = v

    if not _app_id or not _app_secret:
        return {
            "success": False,
            "message_id": None,
            "error": "缺少 app_id 或 app_secret"
        }

    try:
        client = (
            lark.Client.builder()
            .app_id(_app_id)
            .app_secret(_app_secret)
            .domain(lark.FEISHU_DOMAIN)
            .log_level(lark.LogLevel.WARNING)
            .build()
        )

        card_str = json.dumps(card, ensure_ascii=False)

        body = (
            CreateMessageRequestBody.builder()
            .receive_id(receive_id)
            .msg_type("interactive")
            .content(card_str)
            .uuid(str(uuid.uuid4()))
            .build()
        )

        request = (
            CreateMessageRequest.builder()
            .receive_id_type(receive_id_type)
            .request_body(body)
            .build()
        )

        response = client.im.v1.message.create(request)

        response_code = getattr(response, 'code', None)
        is_success = response.success() or (response_code == 0)

        if is_success:
            msg_id = response.data.message_id if response.data else None
            return {"success": True, "message_id": msg_id, "error": None}
        else:
            error_msg = f"code={response.code}, msg={response.msg}"
            return {"success": False, "message_id": None, "error": error_msg}

    except Exception as e:
        return {"success": False, "message_id": None, "error": str(e)}


# ============================================================
# 7. 总入口
# ============================================================

def smart_send_v2(text: str, title: str, receive_id: str,
                  receive_id_type: str = "chat_id",
                  app_id: str = None, app_secret: str = None,
                  max_card_size: int = DEFAULT_MAX_CARD_SIZE) -> dict:
    """
    v2 总入口：一次性完成 清洗 → 解析（含折叠） → 转换 → 判定 → 拆分 → 发送

    参数：
        text:             Markdown 文本内容（支持 [collapse:标题]...[/collapse] 语法）
        title:            卡片标题
        receive_id:       目标聊天窗口 ID
        receive_id_type:  "chat_id" 或 "open_id"
        app_id:           飞书 App ID（可选）
        app_secret:       飞书 App Secret（可选）
        max_card_size:    单张卡片最大字节数（默认 30000）

    返回：
        {
            "success": bool,
            "cards_sent": int,
            "message_ids": [str, ...],
            "cards": [dict, ...],
            "collapse_count": int,   # 折叠面板总数
            "error": str or None,
            "suggestion": str or None
        }
    """
    global DEFAULT_MAX_CARD_SIZE
    DEFAULT_MAX_CARD_SIZE = max_card_size

    # 1. 清洗
    cleaned = clean_fullwidth(text)

    # 2. 确定标题
    if not title:
        title = extract_first_heading(cleaned)
    if not title:
        first_line = cleaned.strip().split("\n")[0][:20]
        title = first_line + ("..." if len(first_line) >= 20 else "")

    # 3. 解析（含折叠面板）
    elements = parse_markdown(cleaned)

    if not elements:
        return {
            "success": False,
            "cards_sent": 0,
            "message_ids": [],
            "cards": [],
            "collapse_count": 0,
            "error": "解析后无内容",
            "suggestion": "请检查 Markdown 文本是否为空"
        }

    # 统计折叠面板
    collapse_count = _count_collapses_recursive(elements)

    # 4. 拆分
    chunks = split_elements(elements, title)

    # 5. 构建卡片并发送
    cards = []
    message_ids = []
    errors = []

    for idx, chunk in enumerate(chunks):
        if idx == 0:
            card_title = title
        else:
            card_title = f"{title}（续 {idx + 1}）"

        color = COLORS[idx % len(COLORS)]
        card = build_card(chunk, card_title, color)
        cards.append(card)

        check = check_limits(card)
        if not check["ok"]:
            errors.append(f"卡片 {idx + 1} 限制检查失败: {check['error']}")
            continue

        result = send_to_feishu(card, receive_id, receive_id_type, app_id, app_secret)
        if result["success"]:
            message_ids.append(result["message_id"])
        else:
            errors.append(f"卡片 {idx + 1} 发送失败: {result['error']}")
            break

    success = len(errors) == 0 and len(message_ids) > 0
    return {
        "success": success,
        "cards_sent": len(message_ids),
        "message_ids": message_ids,
        "cards": cards,
        "collapse_count": collapse_count,
        "error": "; ".join(errors) if errors else None,
        "suggestion": "如果仍然失败，可尝试缩减内容或减少折叠面板数量" if errors else None
    }


def _count_collapses_recursive(elements: list) -> int:
    """递归统计所有层级的折叠面板数量"""
    count = 0
    for e in elements:
        if e["type"] == "collapse":
            count += 1
            count += _count_collapses_recursive(e["elements"])
    return count


# ============================================================
# 8. 辅助函数：纯构建（不发送）
# ============================================================

def build_card_from_markdown(text: str, title: str, template_color: str = "blue") -> dict:
    """
    纯构建：将 Markdown（含折叠语法）转换为卡片 JSON，不发送。
    适用于调用方想自行发送的场景。
    
    参数：
        text:           Markdown 文本
        title:          卡片标题
        template_color: 颜色（blue/turquoise/violet/green/indigo/orange）
    
    返回：
        完整卡片 JSON dict
    """
    cleaned = clean_fullwidth(text)
    if not title:
        title = extract_first_heading(cleaned)
    if not title:
        first_line = cleaned.strip().split("\n")[0][:20]
        title = first_line + ("..." if len(first_line) >= 20 else "")
    
    elements = parse_markdown(cleaned)
    return build_card(elements, title, template_color)


def build_collapsible_panel(title: str, elements: list, expanded: bool = False) -> dict:
    """
    手动构建单个折叠面板组件。
    适用于调用方自行组装 card JSON 的场景。
    
    参数：
        title:     面板标题
        elements:  面板内部组件列表（markdown/table/hr/collapsible_panel）
        expanded:  是否默认展开
    
    返回：
        collapsible_panel 组件 dict
    """
    return {
        "tag": "collapsible_panel",
        "expanded": expanded,
        "header": {
            "title": {
                "tag": "plain_text",
                "content": title
            }
        },
        "elements": elements
    }


def markdown_element(content: str) -> dict:
    """构建 markdown 组件的快捷函数"""
    return {"tag": "markdown", "content": content}


def table_element(columns: list, rows: list) -> dict:
    """
    构建 table 组件的快捷函数。
    
    columns: [{"name": "col_0", "display_name": "列名", "data_type": "text"}]
    rows: [{"col_0": "值", "col_1": "值"}]
    """
    return {
        "tag": "table",
        "page_size": min(len(rows), MAX_PAGE_SIZE),
        "row_height": "low",
        "header_style": {
            "text_align": "left",
            "background_style": "grey",
            "bold": True
        },
        "columns": columns,
        "rows": rows
    }


def hr_element() -> dict:
    """构建 hr 组件的快捷函数"""
    return {"tag": "hr"}


# ============================================================
# 9. 调用示例
# ============================================================
#
# === 方式 A：Markdown 折叠语法（推荐，最简单） ===
#
# result = smart_send_v2(
#     text="""
# ## 每日资讯
#
# 重点新闻摘要...
#
# [collapse+:🔴 特别重要 (2条)]
# **央行宣布降准50个基点**
# 自下月起，大型银行存款准备金率下调...
#
# **证监会优化IPO审核流程**
# 新规将缩短审核周期至3个月...
# [/collapse]
#
# [collapse:🟡 重要 (3条)]
# **券商板块集体上涨**
# 国泰海通合并预期持续发酵...
#
# **新能源车销量创新高**
# 比亚迪单月交付突破30万辆...
#
# **半导体国产替代加速**
# 中芯国际扩产计划获批...
# [/collapse]
#
# [collapse:🟢 普通 (5条)]
# 其他常规新闻...
# [/collapse]
# """,
#     title="📰 7月5日 每日资讯",
#     receive_id="oc_xxx",
# )
# print(json.dumps(result, ensure_ascii=False, indent=2))
#
#
# === 方式 B：手动构建（适合复杂动态卡片） ===
#
# from send_card_v2 import (
#     build_collapsible_panel, markdown_element, table_element, hr_element
# )
# 
# card = {
#     "schema": "2.0",
#     "config": {"wide_screen_mode": True},
#     "header": {
#         "title": {"content": "手动构建卡片", "tag": "plain_text"},
#         "template": "blue"
#     },
#     "body": {
#         "direction": "vertical",
#         "elements": [
#             markdown_element("正文内容..."),
#             build_collapsible_panel(
#                 "折叠标题",
#                 [markdown_element("折叠内容...")],
#                 expanded=False
#             ),
#         ]
#     }
# }
# # 然后用 lark SDK 发送
