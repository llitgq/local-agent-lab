#!/usr/bin/env python3
"""feishu-pro 连通性自检：凭证发现 → token 获取 → 可选发测试卡片。

用法:
  python3 smoke_test.py --token-only                 # 只测凭证+token（零副作用）
  python3 smoke_test.py --send-card --chat-id oc_xx  # 额外发一张测试卡片（需用户明确同意）

输出 JSON，含凭证来源（source 字段），便于确认没有拿错 app。
"""
import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent


def discover_credentials():
    """三级发现：环境变量 > HERMES_HOME/.env > 常见 .env 位置。返回 (app_id, secret, source)。"""
    app_id = os.environ.get("FEISHU_APP_ID", "")
    app_secret = os.environ.get("FEISHU_APP_SECRET", "")
    if app_id and app_secret:
        return app_id, app_secret, "environment-variables"

    candidates = []
    hh = os.environ.get("HERMES_HOME", "")
    if hh:
        candidates.append(Path(hh) / ".env")
    candidates += [
        SKILL_ROOT / ".env",
        Path.home() / ".hermes" / ".env",
        Path.home() / ".hermes-new" / ".env",
        Path.cwd() / ".env",
    ]
    for env_path in candidates:
        if not env_path.is_file():
            continue
        found = {}
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            found[k.strip()] = v.strip().strip("\"'")
        if found.get("FEISHU_APP_ID") and found.get("FEISHU_APP_SECRET"):
            return found["FEISHU_APP_ID"], found["FEISHU_APP_SECRET"], str(env_path)
    return "", "", "not-found"


def get_token(app_id, app_secret):
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    body = json.dumps({"app_id": app_id, "app_secret": app_secret}).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read())
    return data


def send_test_card(chat_id):
    sys.path.insert(0, str(SKILL_ROOT / "cards" / "templates"))
    try:
        from send_card import smart_send
    except ImportError as e:
        return {"ok": False, "error": f"导入 send_card 失败: {e}（cards 依赖 lark_oapi，见 SETUP.md 第 4 步）"}
    md = "# feishu-pro 配置成功\n\n| 项目 | 状态 |\n|--|--|\n| 凭证 | OK |\n| Token | OK |\n| 卡片 | 本卡片即为测试 |\n\n[collapse:详情]\nfeishu-pro smoke test\n[/collapse]"
    try:
        return {"ok": True, "result": smart_send(text=md, chat_id=chat_id)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def mask(s):
    return (s[:4] + "****") if len(s) > 4 else "****"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--token-only", action="store_true", help="只测 token，不发卡片")
    ap.add_argument("--send-card", action="store_true", help="发一张测试卡片（需用户同意）")
    ap.add_argument("--chat-id", help="测试卡片目标会话")
    args = ap.parse_args()

    out = {"ok": False}
    app_id, app_secret, source = discover_credentials()
    out["credential_source"] = source
    out["app_id"] = app_id or "(empty)"
    out["app_secret"] = mask(app_secret) if app_secret else "(empty)"
    if not app_id or not app_secret:
        out["error"] = "未发现凭证。按 SETUP.md 第 3 步配置（env 或 .env），或 export FEISHU_APP_ID/FEISHU_APP_SECRET 后重试。"
        print(json.dumps(out, ensure_ascii=False, indent=2))
        sys.exit(2)

    try:
        tok = get_token(app_id, app_secret)
    except Exception as e:
        out["error"] = f"请求失败: {e}"
        print(json.dumps(out, ensure_ascii=False, indent=2))
        sys.exit(3)

    if tok.get("code") != 0:
        out["error"] = f"token 获取失败 code={tok.get('code')} msg={tok.get('msg')}"
        print(json.dumps(out, ensure_ascii=False, indent=2))
        sys.exit(4)
    out["ok"] = True
    out["token_expire"] = tok.get("expire") or tok.get("data", {}).get("expire")

    if args.send_card:
        if not args.chat_id:
            out["card"] = {"ok": False, "error": "缺少 --chat-id"}
            out["ok"] = False
        else:
            out["card"] = send_test_card(args.chat_id)
            out["ok"] = out["card"].get("ok", False)

    print(json.dumps(out, ensure_ascii=False, indent=2))
    sys.exit(0 if out["ok"] else 5)


if __name__ == "__main__":
    main()
