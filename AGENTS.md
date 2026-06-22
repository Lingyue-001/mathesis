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

## Current-Stage Cullen Rules
These rules apply specifically to the current Cullen-led calibration stage for `三统历` and `四分历`. They are stage-specific, not repository-wide defaults for all future materials.

### Cullen-first Principle
- This stage is an open-book calibration stage anchored on Cullen, not a stage for blind discovery of structure from source text alone.
- Cullen `Proc` blocks, quoted Chinese, English translations, commentary, constant explanations, and algorithm notes are the primary authority for this stage.
- Reconstruction, alignment, audit, and writeback planning must follow this order:

```text
Cullen Proc block
-> Cullen quoted Chinese / translation / commentary
-> source span reconstruction
-> evidence audit
-> conservative writeback plan
```

- Do not degrade or rewrite canonical Cullen text in order to increase match rate.
- Cullen quote is evidence, not a loose search keyword bundle.
- If cleaning is needed for matching, generate derived fields such as `match_key`; do not overwrite the canonical Cullen quote with cleaned content.
- If Cullen evidence, source matching, and heuristic output conflict, prefer Cullen evidence plus human-auditable provenance.
- Do not let source-side keyword scanning reverse or overwrite Cullen-led structure.

### Stage Red Lines
Unless explicitly requested, do not:

```text
write back anchors
change A_confirmed judgment
change claims rules
overwrite human_* fields
generate final/gold/locked gold
return to source-side blind keyword scan
add duplicate commands or duplicate output files
```

- Important changes in this stage must be explained through existing audit outputs, including:

```text
what changed
why it changed
which Proc blocks were affected
which results improved
which risks remain
whether regression stayed stable
```

## Clean Code / Minimal Change Rule
- Prefer reusing, replacing, and simplifying existing code paths.
- Do not keep adding scripts, fields, branches, naming systems, or patch layers when the same goal can be achieved by cleaning up the existing path.
- Before each change, check in this order:

```text
Can an existing command be reused?
Can an existing function be extended?
Can old logic be replaced directly?
Can duplicate logic be deleted or merged?
```

- Only add a new command or file when the work is truly a new standalone stage or a genuinely separate artifact.
- Otherwise, modify the existing pipeline so the codebase stays clean, auditable, and regression-friendly.
- Do not allow multiple parallel logic stacks to accumulate for the same task, such as:

```text
old heuristic path
refined heuristic path
cullen-led path
special-case patch path
temporary fallback path
```

- If new logic replaces old logic, replace it clearly instead of keeping both paths producing similar outputs.
- Every added field or output must have a clear downstream use.
- Temporary debug fields should be removed when finished or kept strictly audit-only.

## Commit Message Convention (Codex Auto Push)
- For Codex-generated auto-push commits, do **not** use `feat:` as the message prefix.
- End commit messages with: `Implemented with Codex assistance.`
- If Codex directly performs the push, end the commit message with: `(with Codex)`.
