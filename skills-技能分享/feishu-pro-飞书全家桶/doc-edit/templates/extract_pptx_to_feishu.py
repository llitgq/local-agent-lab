#!/usr/bin/env python3
"""
模板：从 PPTX 提取文本内容，写入飞书文档对应标题下。
用法：修改 DOC_ID、PPTX_PATH、HEADING_CONTENT_MAP 后执行。
"""
import os, json, requests
from pptx import Presentation

# ===== 配置区 =====
DOC_ID = "docxxxxxxxxxxxxxxxxxxxxx"  # 飞书文档 ID
PPTX_PATH = "/path/to/file.pptx"          # PPTX 文件路径
ENV_PATH = ""  # 留空=自动发现（env > HERMES_HOME/.env）；或写绝对路径

# 标题关键词 → 对应的文本列表（从 PPTX 提取后手动填入）
# 键名必须与文档中标题块的文本完全一致
HEADING_CONTENT_MAP = {
    "加强型与削弱型": [
        "加强、削弱三要素：论据、结论、论证",
        "内容行...",
    ],
    "立体图形": [
        "一、空间折叠",
        "内容行...",
    ],
}

# ===== 认证 =====
def get_token_and_headers():
    app_id = app_secret = ""
    with open(ENV_PATH, "r") as f:
        for line in f:
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                if k == "FEISHU_APP_ID": app_id = v
                elif k == "FEISHU_APP_SECRET": app_secret = v

    token_url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    resp = requests.post(token_url, json={"app_id": app_id, "app_secret": app_secret})
    tenant_token = resp.json()["tenant_access_token"]
    return f"Bearer {tenant_token}", {"Authorization": f"Bearer {tenant_token}", "Content-Type": "application/json"}

# ===== PPTX 提取 =====
def extract_pptx(path):
    prs = Presentation(path)
    slides = []
    for i, slide in enumerate(prs.slides, 1):
        texts = []
        for shape in slide.shapes:
            if shape.has_text_frame:
                for para in shape.text_frame.paragraphs:
                    t = para.text.strip()
                    if t: texts.append(t)
            elif shape.shape_type == 6:
                for sub in shape.shapes:
                    if sub.has_text_frame:
                        for para in sub.text_frame.paragraphs:
                            t = para.text.strip()
                            if t: texts.append(t)
        if texts:
            slides.append({"slide": i, "texts": texts})
    return slides

# ===== 块操作 =====
def make_text(content):
    return {"block_type": 2, "text": {"elements": [{"text_run": {"content": content, "text_element_style": {}}}]}}

def insert_blocks(doc_id, parent_block_id, texts, headers, batch_size=40):
    inserted = 0
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        children = [make_text(t) for t in batch]
        url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/blocks/{parent_block_id}/children"
        payload = {"index": inserted, "children": children}
        resp = requests.post(url, headers=headers, json=payload)
        if resp.json().get("code") != 0:
            print(f"  ERROR: {resp.json().get('msg')}")
            return False
        inserted += len(batch)
    return True

# ===== 获取标题映射 =====
def get_heading_map(doc_id, headers):
    blocks_url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/blocks?page_size=500"
    resp = requests.get(blocks_url, headers=headers)
    blocks = resp.json()["data"]["items"]
    heading_map = {}
    TEXT_KEYS = ['text', 'heading1', 'heading2', 'heading3']
    for b in blocks:
        if b["block_type"] in [3, 4, 5]:
            text = ""
            for key in TEXT_KEYS:
                if key in b:
                    for el in b[key].get('elements', []):
                        if 'text_run' in el:
                            text += el['text_run'].get('content', '')
            heading_map[text] = b["block_id"]
    return heading_map

# ===== 主流程 =====
if __name__ == "__main__":
    token, headers = get_token_and_headers()
    print(f"Token: {'OK' if token else 'FAIL'}")

    # 提取 PPTX（调试用，正式使用时直接填 HEADING_CONTENT_MAP）
    if os.path.exists(PPTX_PATH):
        slides = extract_pptx(PPTX_PATH)
        print(f"Extracted {len(slides)} slides from PPTX")

    # 获取标题映射
    heading_map = get_heading_map(DOC_ID, headers)
    print(f"Found {len(heading_map)} headings in document")
    for k, v in heading_map.items():
        print(f"  '{k}' -> {v}")

    # 写入内容
    for heading_text, texts in HEADING_CONTENT_MAP.items():
        if heading_text not in heading_map:
            print(f"WARNING: heading '{heading_text}' not found in document, skipping")
            continue
        block_id = heading_map[heading_text]
        ok = insert_blocks(DOC_ID, block_id, texts, headers)
        print(f"{'OK' if ok else 'FAIL'}: {heading_text} ({len(texts)} blocks)")
