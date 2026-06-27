#!/bin/sh
# pre-commit hook：確保筆記在進版控前已完成 note-checker 查證與 note-linker 串連。
# 安裝方式：執行 scripts/install-hooks.sh（只需一次）。

SUBJECTS="國文 英文 數學 物理 化學 生物 地球科學 歷史 地理 公民與社會"
FAILED=0

for file in $(git diff --cached --name-only); do
  # 只處理 .md 檔
  case "$file" in *.md) ;; *) continue ;; esac

  dirname=$(dirname "$file")
  basename=$(basename "$file" .md)

  # 只處理十科目錄下的筆記（排除 *MOC.md、_index、_system 等）
  is_subject=0
  for s in $SUBJECTS; do
    [ "$dirname" = "$s" ] && is_subject=1 && break
  done
  [ $is_subject -eq 0 ] && continue

  # 排除 MOC 檔本身
  case "$basename" in *MOC) continue ;; esac

  # ── 條件 A：note-checker 已執行（檢查狀態 ≠ 待檢查）──────────────
  if grep -q "^檢查狀態: 待檢查" "$file" 2>/dev/null; then
    echo ""
    echo "⚠️  $file"
    echo "   內容尚未查證（檢查狀態: 待檢查）"
    echo "   請在 Claude Code 裡執行："
    echo "     請用 note-checker 校驗 $file"
    FAILED=1
  fi

  # ── 條件 B：note-linker 已執行（科目MOC 有 [x] [[主題]]）─────────
  moc="${dirname}/${dirname}MOC.md"
  if ! grep -qF "[x] [[$basename]]" "$moc" 2>/dev/null; then
    echo ""
    echo "⚠️  $file"
    echo "   尚未串連知識地圖（${moc} 找不到 [x] [[$basename]]）"
    echo "   請在 Claude Code 裡執行："
    echo "     請用 note-linker 串連 $file"
    FAILED=1
  fi
done

if [ $FAILED -eq 1 ]; then
  echo ""
  echo "────────────────────────────────────────────────"
  echo "❌ 提交暫停：請先在 Claude Code 完成以上 QA 步驟，再重新 git commit。"
  echo "   （確定要略過品質檢查：git commit --no-verify，不建議）"
  echo "────────────────────────────────────────────────"
  exit 1
fi

exit 0
