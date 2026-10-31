#!/usr/bin/env bash
# feishu-pro 安装器：装到目标 agent 的 skill 目录；发现已有飞书 skill 时备份后替换。
# 默认 dry-run 只打印计划；--apply 才实际执行。
set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APPLY=0
TARGET=""

usage() { echo "用法: install.sh [--apply] [--target <skills目录>]   (默认 dry-run)"; exit 1; }
while [[ $# -gt 0 ]]; do
  case "$1" in
    --apply) APPLY=1 ;;
    --target) TARGET="$2"; shift ;;
    -h|--help) usage ;;
    *) usage ;;
  esac
  shift
done

# 候选目标发现（只列真实存在的 skills 目录）
declare -a CANDIDATES=()
add_candidate() { [[ -d "$1" ]] && CANDIDATES+=("$1"); }
[[ -n "${HERMES_HOME:-}" ]] && add_candidate "$HERMES_HOME/skills"
add_candidate "$HOME/.hermes-new/skills"
add_candidate "$HOME/.hermes/skills"
for p in "$HOME"/.hermes/profiles/*/skills; do add_candidate "$p"; done
add_candidate "$HOME/.claude/skills"

if [[ -n "$TARGET" ]]; then
  [[ -d "$TARGET" ]] || { echo "目标目录不存在: $TARGET"; exit 2; }
  DEST="$TARGET"
else
  echo "== 检测到的候选 skill 目录 =="
  i=1
  for c in "${CANDIDATES[@]:-}"; do
    [[ -z "$c" ]] && continue
    echo "  [$i] $c"
    i=$((i+1))
  done
  [[ ${#CANDIDATES[@]} -eq 0 ]] && { echo "未发现任何候选目录，用 --target <目录> 指定"; exit 2; }
  echo "输入编号选择安装目标（或 q 退出）: "
  read -r sel
  [[ "$sel" == "q" ]] && exit 0
  DEST="${CANDIDATES[$((sel-1))]}" || { echo "无效选择"; exit 2; }
fi

echo
echo "== 安装目标: $DEST =="

# 已存在的飞书 skill（按名字匹配，将被替换）
FEISHU_PATTERN='feishu-cards*|tools-feishu*|tools-feishu|feishu-calendar|feishu-bitable|s-feishu-card*|feishu-pro'
REPLACED=()
shopt -s nullglob
for d in "$DEST"/*/; do
  name="$(basename "$d")"
  if [[ "$name" == "Always" || "$name" == .* ]]; then continue; fi
  if echo "$name" | grep -qiE "^(${FEISHU_PATTERN})$"; then
    [[ "$d" == "$SRC/" ]] && continue   # 源即目标，跳过
    REPLACED+=("$name")
  fi
done

TS="$(date +%Y%m%d-%H%M%S)"
BACKUP_DIR="$DEST/.feishu-pro-backup-$TS"

echo "== 计划 =="
echo "  1. 安装: $SRC -> $DEST/feishu-pro"
if [[ ${#REPLACED[@]} -gt 0 ]]; then
  echo "  2. 替换以下已有飞书 skill（移动到 $BACKUP_DIR/，不删除）:"
  for r in "${REPLACED[@]}"; do echo "       - $r"; done
else
  echo "  2. 未发现已有飞书 skill，无需替换"
fi
echo "  3. 后续（手动）: 重启对应 agent/网关；按 SETUP.md 第 8 步注入路由规则"
echo

if [[ $APPLY -eq 0 ]]; then
  echo "DRY-RUN：以上仅为计划，未做任何改动。确认无误后执行: bash '$0' --apply --target '$DEST'"
  exit 0
fi

echo "确认执行以上计划？(yes/no)"
read -r ans
[[ "$ans" == "yes" ]] || { echo "已取消"; exit 1; }

mkdir -p "$BACKUP_DIR"
for r in "${REPLACED[@]:-}"; do
  [[ -z "$r" ]] && continue
  mv "$DEST/$r" "$BACKUP_DIR/$r"
  echo "已备份替换: $r -> $BACKUP_DIR/$r"
done
rm -rf "$DEST/feishu-pro"
cp -R "$SRC" "$DEST/feishu-pro"
find "$DEST/feishu-pro" -name ".DS_Store" -delete
echo
echo "安装完成: $DEST/feishu-pro"
[[ ${#REPLACED[@]} -gt 0 ]] && echo "被替换 skill 备份在: $BACKUP_DIR（确认新版正常后可自行删除）"
echo "下一步: 1) 重启对应 agent/网关  2) 按 SETUP.md 第 8 步注入路由规则  3) 按 SETUP.md 第 9 步终验"
