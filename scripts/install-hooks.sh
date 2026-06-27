#!/bin/sh
# 一鍵安裝 git pre-commit hook（只需執行一次）。
# 用途：確保每次 git commit 前，筆記都已完成 note-checker 查證與 note-linker 串連。

set -e

REPO_ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$REPO_ROOT"

HOOK_SRC=".claude/hooks/pre-commit.sh"
HOOK_DST=".git/hooks/pre-commit"

# 若尚未 git init，自動初始化
if [ ! -d ".git" ]; then
  echo "ℹ️  尚未初始化版控，執行 git init..."
  git init
  echo "✅ git 版控已初始化"
fi

# 安裝 hook
cp "$HOOK_SRC" "$HOOK_DST"
chmod +x "$HOOK_DST"

echo ""
echo "✅ Pre-commit hook 安裝完成！"
echo ""
echo "   往後每次 git commit 前，系統會自動確認："
echo "   ・筆記已通過 note-checker 內容查證"
echo "   ・筆記已由 note-linker 串連到知識地圖"
echo ""
echo "   若有筆記還沒做 QA，commit 會暫停並告訴你要跑哪個步驟。"
