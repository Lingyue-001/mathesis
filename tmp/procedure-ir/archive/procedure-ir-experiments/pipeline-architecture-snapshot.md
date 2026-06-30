# Pipeline Architecture Snapshot

Generated: 2026-06-22T20:18:30.157Z

## Mainline

```text
raw sources / Cullen PDF
→ Cullen pages
→ Cullen chunks
→ Cullen claims
→ Cullen Proc anchors
→ Cullen-led source reconstruction
→ Phase 1 baseline
→ Phase 2A Procedure IR pilot
```

Assessment: the repo now has a recognizable single Cullen-first mainline, but the implementation surface is still fragmented across many untracked scripts, and `build:procedure-ir` appears broader than one stage should be.

## NPM Scripts

### Setup

| script | purpose | main input | main output | modifies canonical files | safe to rerun |
|---|---|---|---|---|---|
| `setup:mac` | Provision local Mac environment | repo + host env | installed tooling | no | usually yes, host-side |
| `setup:windows` | Provision local Windows environment | repo + host env | installed tooling | no | usually yes, host-side |
| `verify:install` | Validate local environment | local runtimes + repo | terminal verification | no | yes |

### Extract

| script | purpose | main input | main output | modifies canonical files | safe to rerun |
|---|---|---|---|---|---|
| `extract:cullen-pages` | Extract Cullen PDF pages | Cullen PDF | page artifacts | no | yes |
| `extract:cullen-claims` | Extract Cullen claims | pages/chunks | claim artifacts | no | yes |

### Build

| script | purpose | main input | main output | modifies canonical files | safe to rerun |
|---|---|---|---|---|---|
| `build:cullen-chunks` | Build Cullen chunks | Cullen pages | chunk artifacts | no | yes |
| `build:cullen-search-index` | Build Cullen search index | pages/chunks/claims | index artifacts | no | yes |
| `build:procedure-ir` | Build source-side Procedure IR | source spans + config + alignments | Procedure IR artifacts | likely no, but scope is broad | unclear without finer split |
| `build:ctext-cache` | Build CText cache candidate/published artifacts | CText results + mapped text | cache JSON | yes when promoted | yes with care |
| `build` | Build Eleventy site | site source | static site output | no | yes |

### Align

| script | purpose | main input | main output | modifies canonical files | safe to rerun |
|---|---|---|---|---|---|
| `align:cullen-procedure-ir` | Align Cullen structures with Procedure IR | Cullen pipeline outputs + Procedure IR | alignment artifacts | no | yes |
| `assimilate:cullen` | Integrate Cullen-derived stage outputs | Cullen data + pipeline config | integrated artifacts | likely no, but name is broad | unclear |
| `promote:ctext-cache` | Publish cache candidate | candidate cache | static cache | yes | yes, but publishes state |

### Audit

`audit:cullen-chapter-coverage`, `audit:cullen-procedure-completeness`, `audit:cullen-procedure-anchors`, `audit:cullen-anchor-quality`, `audit:cullen-target-span-alignment`, `audit:sifen-target-family-candidates`, `audit:source-cullen-alignment`, `audit:cullen-led-source-reconstruction`, `audit:cullen-oracle`, `test:ctext-stats-parser`

Shared characteristics:

- purpose: validate pipeline outputs or benchmark status
- main input: staged Cullen/source artifacts
- main output: reports, diagnostics, terminal summaries
- modifies canonical files: no
- safe to rerun: yes

### Query

| script | purpose | main input | main output | modifies canonical files | safe to rerun |
|---|---|---|---|---|---|
| `query:cullen-page` | inspect Cullen page data | page artifacts | terminal output | no | yes |
| `query:cullen-proc` | inspect Proc-level data | anchor/inventory artifacts | terminal output | no | yes |
| `query:cullen-source` | inspect source-side matches | alignment artifacts | terminal output | no | yes |

### Site / Dev

| script | purpose | main input | main output | modifies canonical files | safe to rerun |
|---|---|---|---|---|---|
| `generate:debug-flags-doc` | generate docs | debug flag source | generated docs | yes | yes |
| `generate:log-by-tag` | generate docs | LOG markdown | generated log view | yes | yes |
| `start:ctext-proxy` | run proxy service | local runtime + server code | running local server | no | yes |
| `prestart` | generate docs before serve | debug/log sources | generated docs | yes | yes |
| `start` | run Eleventy dev server | site source | running dev server | no | yes |
| `prebuild` | generate docs before build | debug/log sources | generated docs | yes | yes |

### Unclear Or Overloaded

- `assimilate:cullen`: name suggests multi-stage integration rather than one narrow responsibility.
- `build:procedure-ir`: current diff size and repo state suggest overloaded responsibility.
- `build:ctext-cache` / `promote:ctext-cache`: build and publish semantics sit very close together.
- `prestart` / `prebuild`: generation side effects are mixed into site/dev entrypoints.

## Field Semantics

| field | type | meaning |
|---|---|---|
| `cullen_chinese_raw_bounded_text` | canonical evidence | Raw bounded Cullen Chinese evidence for preservation and review. |
| `cullen_chinese_quoted_text` | canonical evidence | Human-readable canonical Cullen quote. |
| `cullen_chinese_match_key` | derived matching field | Match-only derivative; must not overwrite the quote. |
| `quote_integrity_status` | gate / recommendation | Integrity gate for whether quote preservation remains trustworthy. |
| `primary_source_span_id` | derived matching field | Current best source span candidate. |
| `context_source_span_ids` | derived matching field | Adjacent context spans around the primary span. |
| `relationship_type` | audit-only diagnostic | Shape of the Cullen/source alignment relationship. |
| `writeback_recommendation` | gate / recommendation | Conservative recommendation for later writeback planning. |
| `safe_with_context` | gate / recommendation | Positive gated state with mandatory context retention. |
| `safe_to_write_back` | gate / recommendation | Strongest positive recommendation, still not automatic writeback. |
| `blocker_reason` | audit-only diagnostic | Concrete reason a Proc remains blocked or review-only. |
| `A_confirmed` | gate / recommendation | Stable benchmark grounding tier used as a regression gate. |
| `human_*` | manual review field | Human-authored fields that automation must not overwrite. |
| `final/gold` | manual review field | Locked/gold artifacts that this stage must not generate or replace. |

## Gates

- `quote_integrity gate`
  Quote must preserve Cullen evidence. Failures or unresolved human-check cases must not be treated as clean positives.
- `safe_with_context gate`
  Requires `quote_integrity_status = pass` and only adjacent, non-competing context windows around a clear primary span.
- `Phase 2A entry gate`
  Reconstruction stable, translation bleed zero, `Proc. 3.2 -> sifen:L66`, all `safe_with_context` integrity-clean, `A_confirmed` stable, and at least four positive pilot examples available.
- `A_confirmed gate`
  Benchmark stability must not be changed during freeze/hygiene work.
- `writeback red lines`
  No anchor writeback, no changes to `claims` / `human_*` / `final/gold`, no source-side blind keyword scan.

## Architecture Read

- Current architecture is mostly a single mainline.
- `package.json` script surface is growing quickly.
- `scripts/build-procedure-ir.mjs` looks responsibility-heavy.
- `audit` / `build` / `query` duties are conceptually separable, but operational sprawl is already visible.
