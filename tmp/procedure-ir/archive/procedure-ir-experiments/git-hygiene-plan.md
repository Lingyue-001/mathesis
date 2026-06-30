# Git Hygiene Plan

Generated: 2026-06-22T20:18:30.157Z

## Untracked File Classification

### `track_source_code`

- `scripts/align-cullen-procedure-ir.mjs`
- `scripts/assimilate-cullen.mjs`
- `scripts/audit-cullen-anchor-quality.mjs`
- `scripts/audit-cullen-chapter-coverage.mjs`
- `scripts/audit-cullen-led-source-reconstruction.mjs`
- `scripts/audit-cullen-oracle.mjs`
- `scripts/audit-cullen-procedure-anchors.mjs`
- `scripts/audit-cullen-procedure-completeness.mjs`
- `scripts/audit-cullen-target-span-alignment.mjs`
- `scripts/audit-sifen-target-family-candidates.mjs`
- `scripts/audit-source-cullen-alignment.mjs`
- `scripts/build-cullen-chunks.mjs`
- `scripts/build-cullen-search-index.mjs`
- `scripts/cullen-oracle-common.mjs`
- `scripts/cullen-procedure-anchor-common.mjs`
- `scripts/cullen-procedure-inventory-common.mjs`
- `scripts/extract-cullen-claims.mjs`
- `scripts/extract-cullen-pages.mjs`
- `scripts/extract_cullen_pages.py`
- `scripts/procedure-ir-common.mjs`
- `scripts/query-cullen-page.mjs`
- `scripts/query-cullen-proc.mjs`
- `scripts/query-cullen-source.mjs`
- `scripts/source-cullen-alignment-common.mjs`

These look like first-class pipeline code, not disposable scratch files.

### `track_config_or_gold_candidate`

- `config/cullen-mini-gold-benchmark.json`
- `config/sifen-target-family-gold.candidate.json`

These appear to be pipeline config / benchmark candidate data, not tmp output.

### `track_documentation`

- `scripts/scripts-note.md`

### `generated_tmp_do_not_track`

All current `tmp/procedure-ir/*.json` and `tmp/procedure-ir/*.md` reports, including:

- reconstruction outputs
- reconstruction audits
- Phase 1 baseline
- this architecture snapshot
- this hygiene plan

These are generated reports and should normally stay out of Git.

### `cache_or_build_output_ignore`

- `tmp/ctext_cache/**`
- `tmp/ctext-static-build/**`
- `dist/**`

### `large_binary_review_needed`

- `The Foundations of Celestial Reckoning. Three ancient Chinese astronomical systems (Christopher Cullen) (Z-Library).pdf`

This is the largest policy decision in the current workspace: keep tracked as a research source, or move to an external acquisition/workflow model.

### `unclear_need_human_decision`

- `AGENTS.md`
- `config/calendrical-ir-pipeline.json`
- `package.json`
- `scripts/build-procedure-ir.mjs`

These are tracked-and-modified files with broad impact or governance implications.

## Output Recommendation Lists

### `files_to_git_add`

Recommended eventual add set:

- the untracked Cullen pipeline scripts/helpers listed under `track_source_code`
- `config/cullen-mini-gold-benchmark.json`
- `config/sifen-target-family-gold.candidate.json`
- `scripts/scripts-note.md`

### `files_to_gitignore`

Recommended ignore targets:

- `tmp/procedure-ir/*.json`
- `tmp/procedure-ir/*.md`
- `tmp/procedure-ir/stabilization-checkpoint/**`
- `tmp/ctext_cache/**`
- `tmp/ctext-static-build/**`
- `dist/**`

### `files_needing_human_decision`

- `AGENTS.md`
- `The Foundations of Celestial Reckoning. Three ancient Chinese astronomical systems (Christopher Cullen) (Z-Library).pdf`
- `config/calendrical-ir-pipeline.json`
- `package.json`
- `scripts/build-procedure-ir.mjs`

### `files_not_to_touch_before_phase2A`

- `tmp/procedure-ir/cullen-led-source-reconstruction.json`
- `tmp/procedure-ir/cullen-led-source-reconstruction-audit.json`
- `tmp/procedure-ir/phase1-cullen-led-calibration-baseline.json`
- `tmp/procedure-ir/phase1-cullen-led-calibration-baseline.md`

These are the current freeze/baseline artifacts and should remain stable until Phase 2A actually begins.

## Special Checks

- Large number of `scripts/*.mjs` files are still untracked: yes, this is the main hygiene problem.
- `tmp/procedure-ir` contains generated reports: yes, these look report-like rather than source-like.
- `config/*.json` roles:
  - `config/calendrical-ir-pipeline.json`: source config
  - `config/cullen-mini-gold-benchmark.json`: benchmark/gold-candidate config
  - `config/sifen-target-family-gold.candidate.json`: candidate config pending review
- Cullen PDF should continue to be Git-tracked: human decision needed
- `package.json` scripts growth: high
- `scripts/build-procedure-ir.mjs` responsibility: appears over-heavy
- `audit` / `build` / `query` boundaries: mostly conceptually separate, but operational sprawl is visible

## Working Read

- Current architecture is single-mainline at the conceptual level.
- Untracked severity is high because the core Cullen pipeline implementation itself is still not cleanly tracked.
- The smallest repairable items in one round are:
  - track the Cullen pipeline scripts/helpers as one batch
  - decide ignore rules for generated tmp reports
  - separate report artifacts from source configs in hygiene guidance

## Before Phase 2A

Must resolve:

- Decide which Cullen pipeline scripts/helpers are first-class tracked source.
- Decide whether the Cullen PDF remains a tracked source artifact.
- Reduce uncertainty around `package.json`, `config/calendrical-ir-pipeline.json`, and `scripts/build-procedure-ir.mjs`.

Can wait until after a small Phase 2A pilot:

- finer npm script taxonomy cleanup
- refactoring of overloaded build/audit boundaries
- non-blocking documentation cleanup for helper/query scripts
