# GEMINI.md

This file provides guidance to Antigravity (AGY) when working in this repository.

## What this repo is

A **Traditional-Chinese (Taiwan) Obsidian knowledge base** of study notes for the 學測 (Taiwan senior-high college entrance exam), generated and quality-controlled by AI agents. There is **no build, test, or lint step** — the "product" is Markdown notes plus the agent pipeline that produces them. All content and communication is in 繁體中文（台灣用語）.

Subjects (each a top-level directory): 國文 / 英文 / 數學 / 物理 / 化學 / 生物 / 地球科學 / 歷史 / 地理 / 公民與社會.

## The core workflow: `learn-pipeline` skill

`.agents/skills/learn-pipeline/SKILL.md` orchestrates a 4-stage pipeline; each stage uses a dedicated skill and its output feeds the next:

1. **科目教學 skill** (`tutor-<subject>`, e.g. `tutor-math`) → generates a teaching draft with all template sections. Maps 科目→skill per the table in `learn-pipeline`. Unknown subject → tell the user what's supported and stop.
2. **`note-writer`** → formats the draft into the template and writes `<科目>/<主題>.md`. **Formatting only — it never judges correctness.** If the file already exists it refuses to overwrite; ask the user before overwriting.
3. **`note-checker`** → web-searches to verify hard facts, then sets `檢查狀態` / `信心度` and fills 待確認項. This is the anti-hallucination line of defense.
4. **`note-linker`** → adds cross-subject `[[...]]` links and updates the subject `<subject>MOC.md` and `_index/主題地圖.md`.

When editing an existing note directly (not via the learn pipeline), run these skills manually as needed:
- **`note-checker`** — if you introduced or changed any hard facts (formulas, dates, 課綱 scope).
- **`note-linker`** — if you added, removed, or renamed any `[[...]]` cross-links, or if the note's topic name changed. `note-linker` is **not triggered automatically** on file save; it only runs as step 4 of the learn pipeline. Skipping it leaves the MOC and graph out of sync.

When running `note-linker` on an existing note, it must check for the three MOC-linking failure modes (see `note-linker` skill § MOC 連結三陷阱) in addition to its normal cross-link scan.

## Two layers of agent definitions — don't confuse them

- **`_system/agents/`** — *design-time* definitions: pedagogical archetypes and the per-subject teaching-team specs. Source of truth for *how* each subject teaches. Edit here to change teaching style.
- **`.agents/skills/`** — *executable* skills that the pipeline actually invokes. Keep these in sync with the `_system/` specs.

## Non-negotiable disciplines (this is the project's whole point)

- **Generation and QA are separate.** Tutor skills and `note-writer` must not fact-check; `note-checker` must not invent content. Never collapse these roles.
- **Never fabricate.** Unknown facts get marked `（待查）` and pushed to 待確認項 — not guessed. `note-checker` verifies formulas, dates, 課綱 scope etc. by actually searching the web, not from memory.
- **Honesty over false confidence.** Every note carries `信心度` (高/中/低) and `檢查狀態`; surface `待人工複核` items to the user truthfully. The 💡「為什麼要學」motivation claims must be real, not exaggerated.
- **No real-teacher impersonation.** Agents emulate public *pedagogical archetypes* (故事派/口訣派/圖像派…) only — never a named real teacher. See `_system/agents/名師風格Agent總則.md`.

## Note conventions (`_system/規範/`)

- **Filename = topic name**, no volume/number suffix (volume goes in frontmatter). One concept = one file; relate subtopics via `## sections` or links, never duplicates.
- **Links** use bare topic names `[[主題]]` (e.g. `[[向量]]`) — **never a `科目-` prefix**. Filenames carry no subject, so a prefixed link like `[[數學-向量]]` fails to resolve and breaks the graph. Use `[[科目/主題]]` only to disambiguate same-named topics across subjects. Link only when reading A genuinely requires B.
- **Template** (`_system/templates/主題筆記模板.md`) — section order and emoji headings are fixed and must stay parseable by `note-checker`. 💡「為什麼要學？（Start with Why）」comes first, right after the title.
- **Mermaid — flowchart**: node labels containing Chinese, brackets, or punctuation must use `ID["label"]` syntax (bracket + quote). Example: `A["矩陣乘法（AB≠BA）"]`. **Mermaid — mindmap**: child nodes use **plain text only** (indentation + text, no brackets, no quotes). Bare `"text"` (quote-only, no bracket) is wrong for mindmap — it renders as `&quot;text&quot;`. Root node uses `root["label"]`. For formula nodes that can't be expressed as plain text, `ID["formula"]` (with an explicit node ID prefix, e.g. `L1["aᵐ × aⁿ = aᵐ⁺ⁿ"]`) is valid — only bare `"text"` without an ID prefix causes the entity-escaping bug. Never use U+2212 `−` in any Mermaid node; use ASCII `-` instead. Copy draft Mermaid verbatim; never invent a diagram the draft didn't include.
- **Self-test** requires ≥3 questions; if the draft lacks them, mark `待補` — don't fabricate answers.
- Each subject directory has a `<subject>MOC.md` (subject entry map); `_index/主題地圖.md` is the whole-library entry point.

## Frontmatter checklist fields

`note-writer` sets `檢查狀態: 待檢查` and leaves `信心度` blank. `note-checker` updates them to `已檢查`/`待人工複核` and `高/中/低`, working through `_system/規範/內容檢查清單.md` (hard facts → analogies → 課綱/exam → structure → typos → Mermaid).
