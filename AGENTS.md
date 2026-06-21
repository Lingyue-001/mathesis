# AGENTS Instructions

## Startup Context Rule
At the start of every new Codex session in this repository, read these files first before any edits:
1. `NOTE_当前需求清单和待办_Current_Status_and_Todo.md`
2. `LOG_已完成改动和复盘_Completed_Changes_and_Retrospective.md`
3. `README.md`

## Purpose Split
- `NOTE_当前需求清单和待办_Current_Status_and_Todo.md`:
  only current status, open issues, and prioritized todos.
- `LOG_已完成改动和复盘_Completed_Changes_and_Retrospective.md`:
  only completed changes, implementation steps, and retrospectives.

## Logging Convention
When adding a completed event to log, use one entry per event with:
0. Tags / 标签（1-2 tags, comma separated; from allowed tag list below）
1. Time
2. 需求明确 / Goal
3. 操作 / Actions
4. 解决 / Outcome
5. 复盘 / Retrospective

Allowed tags:
- `ctext`
- `transcriptions`
- `search`
- `data`
- `infra`
- `project-docs`

## Documentation Update Confirmation Rule
- Do not update `NOTE_当前需求清单和待办_Current_Status_and_Todo.md` or `LOG_已完成改动和复盘_Completed_Changes_and_Retrospective.md` until the user explicitly confirms the proposed change is acceptable in that turn, unless the user explicitly asks to update these files immediately.
- If the user asks to commit/push the current turn's changes, treat that as approval for this turn's implemented updates/plan, and update NOTE/LOG accordingly before commit.
- Before commit/push, record completed progress and retrospective notes in the appropriate NOTE/LOG files for that turn.

## UI Change Confirmation Rule
- Suggestions are encouraged, but any visible UI appearance change that is not a direct functional bug fix must be explicitly communicated to the user and confirmed before code is changed.
- Do not silently add or adjust visual effects, decorative styles, layout changes, or debug-facing UI text without prior user confirmation.

## UI Reuse and CSS Governance Rule
- Reuse existing global UI classes, shared JS helpers, and formatter functions before adding page-specific classes or one-off code.
- For repeated UI patterns such as cards, panels, tables, detail panes, animations, naming formats, and measurement displays, create or extend a reusable component/class/helper first; page-specific CSS should only set layout variables, behavior hooks, or genuinely local constraints.
- Keep implementation minimal and classified: design tokens and reusable components belong in global CSS/JS; page-specific files should not duplicate card layouts, popup content templates, animation systems, or formatter logic.
- If a new style or interaction seems useful beyond one page, name it generically and document it through reusable classes instead of creating a single-use selector.
- Preserve interaction state when possible. If a UI pattern is already open or partially transitioned, continue from the current state instead of re-rendering from zero or replaying the full entrance animation. For master/detail interactions, the first open may shift the whole layout, but subsequent record switches should reuse the open layout and animate only the outgoing/incoming detail content.

## Human-Readable Data Rule
- For project-authored JSON, Markdown, and source data files, write Chinese, Sanskrit, romanization, names, titles, and other scholarly text directly in human-readable form whenever the file encoding supports it.
- Do not intentionally write non-ASCII text as JSON Unicode escape sequences such as `\u820a\u5510\u66f8` unless the escape form is required by an external tool or data interchange constraint.
- Prefer readable source data such as `"舊唐書"` over escaped equivalents, because these files are edited and reviewed by humans.

## Transcription HTML UI Guardrail
For any newly imported transcription HTML page under `src/transcriptions/tei_hanshu/`:
1. Keep the project top header/navigation bar visible at the top.
2. Add a visible back button (prefer: back to transcriptions list; fallback to browser history back).

## Data Safety Guardrail (High Priority)
- For node-entry discussions and UI iteration, changes must stay in display/render logic only.
- Do **not** modify or delete canonical data source files such as `src/data.json` unless the user explicitly asks for data-layer edits in that turn.
- Search matching behavior may evolve in code, but underlying JSON records must be preserved as source of truth.

## Commit Message Convention (Codex Auto Push)
- For Codex-generated auto-push commits, do **not** use `feat:` as the message prefix.
- End commit messages with: `Implemented with Codex assistance.`
- If Codex directly performs the push, end the commit message with: `(with Codex)`.
