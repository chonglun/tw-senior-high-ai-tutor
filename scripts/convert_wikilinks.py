#!/usr/bin/env python3
"""
convert_wikilinks.py — Obsidian WikiLinks → Standard Markdown Links

Scans the vault, builds a {topic_name: file_path} index, then converts
all [[topic]] WikiLinks to [topic](relative/path.md) in-place.

Unresolved links (notes not yet created) become plain text.
Code blocks, inline code, and YAML frontmatter are preserved untouched.

Usage:
    python scripts/convert_wikilinks.py [vault_root] [--dry-run]

Examples:
    python scripts/convert_wikilinks.py .              # convert in-place
    python scripts/convert_wikilinks.py . --dry-run    # preview changes
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

# Directories to skip entirely (not user-facing content)
SKIP_DIRS = {
    '.obsidian', '.git', '.agents', '.claude', '.gemini',
    '_system', 'docs', 'scripts', '.github',
}

# WikiLink pattern: [[topic name]]
# Group 1: inline code (preserve as-is)
# Group 2: full WikiLink
# Group 3: topic name inside [[ ]]
WIKILINK_RE = re.compile(r'(`[^`]+`)|(\[\[([^\]\|]+)\]\])')

# Fenced code block opener/closer
FENCE_OPEN_RE = re.compile(r'^(`{3,}|~{3,})')
FENCE_CLOSE_RE = re.compile(r'^(`{3,}|~{3,})\s*$')


def build_index(vault_root: Path) -> dict[str, Path]:
    """
    Scan all .md files under vault_root and build a lookup table:
    {file_stem: relative_path_from_vault_root}

    Skips directories listed in SKIP_DIRS.
    Warns on duplicate topic names (shouldn't happen per project rules).
    """
    index: dict[str, Path] = {}

    for md_file in vault_root.rglob('*.md'):
        rel = md_file.relative_to(vault_root)

        # Skip excluded directories
        if any(part in SKIP_DIRS for part in rel.parts):
            continue

        stem = md_file.stem
        if stem in index:
            print(f"⚠️  重複主題名: {stem}")
            print(f"   既有: {index[stem]}")
            print(f"   新的: {rel}")
        index[stem] = rel

    return index


def compute_relative_path(from_file: Path, to_file: Path) -> str:
    """
    Compute the relative path from from_file's directory to to_file.
    Both paths are relative to vault root.

    Example:
        from_file = Path('數學/矩陣.md')
        to_file   = Path('物理/等加速度運動.md')
        result    = '../物理/等加速度運動.md'
    """
    from_dir = from_file.parent
    rel = os.path.relpath(to_file, from_dir)
    # Normalize to forward slashes (for Windows compat, though CI is Linux)
    return rel.replace(os.sep, '/')


def convert_line(
    line: str,
    current_file: Path,
    index: dict[str, Path],
    stats: dict,
) -> str:
    """
    Convert WikiLinks in a single line, preserving inline code.

    - Resolved [[topic]] → [topic](relative/path.md)
    - Unresolved [[topic]] → topic (plain text)
    - `code with [[topic]]` → preserved as-is
    """

    def replacer(match: re.Match) -> str:
        # Group 1: inline code — keep untouched
        if match.group(1):
            return match.group(1)

        topic = match.group(3)

        if topic in index:
            target_path = index[topic]
            rel_path = compute_relative_path(current_file, target_path)
            stats['resolved'] += 1
            return f'[{topic}]({rel_path})'
        else:
            # Unresolved — strip [[ ]] to leave plain text
            stats['unresolved'] += 1
            stats['unresolved_topics'].add(topic)
            return topic

    return WIKILINK_RE.sub(replacer, line)


def convert_file(
    filepath: Path,
    vault_root: Path,
    index: dict[str, Path],
    stats: dict,
    dry_run: bool = False,
) -> list[tuple[int, str, str]] | None:
    """
    Convert all WikiLinks in a single file.

    Skips:
    - YAML frontmatter (between --- delimiters at file start)
    - Fenced code blocks (``` or ~~~)
    - Inline code (backtick-delimited)

    Returns list of (line_number, before, after) changes in dry-run mode.
    """
    rel_path = filepath.relative_to(vault_root)

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # State tracking
    in_frontmatter = False
    fence_char: str | None = None  # '`' or '~' when inside a code fence
    fence_len: int = 0             # number of fence characters that opened

    new_lines: list[str] = []
    changes: list[tuple[int, str, str]] = []

    for i, line in enumerate(lines):
        stripped = line.rstrip('\n')

        # --- YAML frontmatter ---
        if i == 0 and stripped == '---':
            in_frontmatter = True
            new_lines.append(line)
            continue

        if in_frontmatter:
            if stripped == '---':
                in_frontmatter = False
            new_lines.append(line)
            continue

        # --- Fenced code blocks ---
        if fence_char is None:
            # Check for opening fence
            m = FENCE_OPEN_RE.match(stripped)
            if m:
                fence_char = m.group(1)[0]
                fence_len = len(m.group(1))
                new_lines.append(line)
                continue
        else:
            # Check for closing fence (same char, same or longer length)
            m = FENCE_CLOSE_RE.match(stripped)
            if m and m.group(1)[0] == fence_char and len(m.group(1)) >= fence_len:
                fence_char = None
                fence_len = 0
            new_lines.append(line)
            continue

        # --- Normal line: convert WikiLinks ---
        converted = convert_line(line, rel_path, index, stats)

        if converted != line:
            changes.append((i + 1, line.rstrip('\n'), converted.rstrip('\n')))

        new_lines.append(converted)

    # Write back (unless dry-run)
    if not dry_run and changes:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)

    stats['files_processed'] += 1
    if changes:
        stats['files_modified'] += 1

    return changes if dry_run else None


def get_processable_files(vault_root: Path) -> list[Path]:
    """Get all .md files that should be processed (excluding SKIP_DIRS)."""
    files: list[Path] = []
    for md_file in vault_root.rglob('*.md'):
        rel = md_file.relative_to(vault_root)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        files.append(md_file)
    return sorted(files)


def main():
    # Parse arguments
    args = sys.argv[1:]
    dry_run = '--dry-run' in args
    args = [a for a in args if a != '--dry-run']
    vault_root = Path(args[0]).resolve() if args else Path('.').resolve()

    mode = '🔍 DRY RUN（預覽模式）' if dry_run else '🔧 CONVERT（就地轉換）'
    print(f"{'=' * 60}")
    print(f"  WikiLink → Standard Markdown Link Converter")
    print(f"  Mode: {mode}")
    print(f"  Vault: {vault_root}")
    print(f"{'=' * 60}\n")

    # Step 1: Build index
    index = build_index(vault_root)
    print(f"📇 索引建立完成: {len(index)} 個主題\n")

    # Step 2: Get files
    files = get_processable_files(vault_root)
    print(f"📄 待處理檔案: {len(files)} 個\n")

    # Step 3: Convert
    stats = {
        'files_processed': 0,
        'files_modified': 0,
        'resolved': 0,
        'unresolved': 0,
        'unresolved_topics': set(),
    }

    for filepath in files:
        changes = convert_file(filepath, vault_root, index, stats, dry_run=dry_run)

        if dry_run and changes:
            rel = filepath.relative_to(vault_root)
            print(f"── {rel} ──")
            for line_no, before, after in changes:
                print(f"  L{line_no}:")
                print(f"    - {before}")
                print(f"    + {after}")
            print()

    # Step 4: Report
    print(f"\n{'=' * 60}")
    print(f"  結果統計")
    print(f"{'=' * 60}")
    print(f"  處理檔案數:    {stats['files_processed']}")
    print(f"  修改檔案數:    {stats['files_modified']}")
    print(f"  成功轉換連結:  {stats['resolved']}")
    print(f"  未解析 → 純文字: {stats['unresolved']}")

    if stats['unresolved_topics']:
        print(f"\n  📝 未解析的主題 ({len(stats['unresolved_topics'])} 個):")
        for topic in sorted(stats['unresolved_topics']):
            print(f"     • {topic}")

    print()

    # Step 5: Residual check (only in convert mode)
    if not dry_run:
        remaining = 0
        for filepath in files:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            remaining += len(re.findall(r'\[\[[^\]]+\]\]', content))

        if remaining > 0:
            print(f"  ⚠️  殘留 WikiLinks (可能在 code block 中): {remaining}")
        else:
            print(f"  ✅ 無殘留 WikiLinks（code block 外）")

    return 0


if __name__ == '__main__':
    sys.exit(main())
