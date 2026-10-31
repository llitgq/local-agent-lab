# 批量 PATCH 精修样式 — 可复用模板
#
# 场景：文档已有纯文本块，需要逐块逐词添加加粗/背景色样式。
# 不删除不重建，直接 PATCH 现有块。
#
# 用法：
#   1. GET /blocks 获取所有文本块的 block_id 和内容
#   2. 为每个块编写 [(content, style), ...] 规则
#   3. 调用 batch_patch() 批量执行

import requests
import time
import json

# === 认证 ===
env_path = ""  # 留空=自动发现（env > HERMES_HOME/.env）
app_id = app_secret = ""
with open(env_path, "r") as f:
    for line in f:
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            if k == "FEISHU_APP_ID": app_id = v
            elif k == "FEISHU_APP_SECRET": app_secret = v

token_url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
resp = requests.post(token_url, json={"app_id": app_id, "app_secret": app_secret})
tenant_token = resp.json().get("tenant_access_token", "")
doc_id = "YOUR_DOC_ID"
headers = {"Authorization": f"Bearer {tenant_token}", "Content-Type": "application/json"}

# === 样式快捷函数 ===
N = lambda: {}                                      # 普通文字
B = lambda: {"bold": True}                           # 仅加粗
BG = lambda c: {"bold": True, "background_color": c} # 加粗+背景色
# 背景色值: 1=红 2=紫 3=橙 4=青 5=绿 6=粉 7=蓝

# === 获取所有文本块 ===
def get_text_blocks(doc_id, headers):
    url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/blocks?page_size=500"
    resp = requests.get(url, headers=headers)
    blocks = resp.json()["data"]["items"]
    text_blocks = []
    for b in blocks:
        if b['block_type'] == 2:
            text = "".join(
                el.get('text_run', {}).get('content', '')
                for el in b['text']['elements']
            )
            text_blocks.append({"id": b['block_id'], "text": text})
    return text_blocks

# === 按内容搜索 block_id（推荐！不要硬编码 block_id）===
def find_block_id(doc_id, headers, search_text):
    """通过内容文本搜索 block_id，避免硬编码出错"""
    blocks = get_text_blocks(doc_id, headers)
    for tb in blocks:
        if search_text in tb['text']:
            return tb['id']
    return None

# === PATCH 单个块 ===
def patch_block(block_id, elements, doc_id, headers):
    url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/blocks/{block_id}"
    payload = {"update_text_elements": {"elements": [
        {"text_run": {"content": c, "text_element_style": s}} for c, s in elements
    ]}}
    r = requests.patch(url, headers=headers, json=payload)
    try:
        return r.json().get("code") == 0
    except:
        return False

# === 批量 PATCH ===
def batch_patch(updates, doc_id, headers, delay=0.08):
    """updates: [(block_id, [(content, style), ...]), ...]"""
    ok = fail = 0
    failed_ids = []
    for block_id, elements in updates:
        if patch_block(block_id, elements, doc_id, headers):
            ok += 1
        else:
            fail += 1
            failed_ids.append(block_id)
        time.sleep(delay)
    # 重试失败的（可能是限频）
    if failed_ids:
        time.sleep(2)
        retry_map = dict(updates)
        for bid in failed_ids:
            time.sleep(0.15)
            if patch_block(bid, retry_map[bid], doc_id, headers):
                ok += 1
                fail -= 1
    print(f"完成: ✅{ok} ❌{fail}")
    return ok, fail

# === 统计样式覆盖率 ===
def count_styles(doc_id, headers):
    blocks = get_text_blocks(doc_id, headers)
    # 重新获取完整块信息（含样式）
    url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/blocks?page_size=500"
    resp = requests.get(url, headers=headers)
    all_blocks = resp.json()["data"]["items"]
    
    bold_count = bg_count = styled_blocks = text_total = 0
    for b in all_blocks:
        if b['block_type'] == 2:
            text_total += 1
            has_style = False
            for el in b['text']['elements']:
                if 'text_run' in el:
                    style = el['text_run'].get('text_element_style', {})
                    if style.get('bold'):
                        bold_count += 1
                        has_style = True
                    if style.get('background_color'):
                        bg_count += 1
                        has_style = True
            if has_style:
                styled_blocks += 1
    print(f"文本块: {text_total}, 有样式: {styled_blocks} ({styled_blocks*100//text_total}%)")
    print(f"加粗片段: {bold_count}, 背景色片段: {bg_count}")

# ============================================================
# 使用示例
# ============================================================
if __name__ == "__main__":
    # 1. 获取所有文本块
    text_blocks = get_text_blocks(doc_id, headers)
    for i, tb in enumerate(text_blocks):
        print(f"[{i:3d}] {tb['id']}: {tb['text'][:80]}")

    # 2. 编写样式规则（逐词精修）
    #    关键：分析每句话的真正重点，只给关键词加样式
    updates = [
        # 示例：用一个特征词搜索 block_id，而不是硬编码
        (find_block_id(doc_id, headers, "常考题型包括"), [
            ("📌 可能性推理的常考题型包括", N()),
            ("削弱型、加强型、前提型、结论型、解释型、评价型", B()),
            ("，其中", N()),
            ("削弱型和加强型", BG(5)),  # 绿色=加强方法
            ("是", N()),
            ("重点题型", B()),
            ("。", N()),
        ]),
        # ... 更多块
    ]

    # 3. 批量执行
    batch_patch(updates, doc_id, headers)

    # 4. 验证
    count_styles(doc_id, headers)
