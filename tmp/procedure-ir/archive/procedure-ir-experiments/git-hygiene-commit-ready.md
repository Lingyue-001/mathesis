# Git Hygiene Commit-Ready Checklist

Generated: 2026-06-22

## recommended_git_add_source_code

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

## recommended_git_add_config

- `config/cullen-mini-gold-benchmark.json`
- `config/sifen-target-family-gold.candidate.json`

## recommended_git_add_docs

- `scripts/scripts-note.md`

## do_not_add_generated_tmp

- all generated `tmp/procedure-ir/*.json`
- all generated `tmp/procedure-ir/*.md`
- especially:
  - reconstruction outputs
  - reconstruction audits
  - phase baseline reports
  - architecture snapshot
  - hygiene plan
  - this commit-ready checklist

## do_not_add_large_binary

- `The Foundations of Celestial Reckoning. Three ancient Chinese astronomical systems (Christopher Cullen) (Z-Library).pdf`

## needs_human_review_before_add

- `AGENTS.md`
- `package.json`
- `config/calendrical-ir-pipeline.json`
- `scripts/build-procedure-ir.mjs`
- `The Foundations of Celestial Reckoning. Three ancient Chinese astronomical systems (Christopher Cullen) (Z-Library).pdf`

## Human Review Diff Summary

- `AGENTS.md`
  Adds stage-specific Cullen-first rules, red lines, and clean-code/minimal-change governance.
- `package.json`
  Adds many Cullen pipeline npm scripts across extract/build/align/audit/query categories.
- `config/calendrical-ir-pipeline.json`
  Registers Cullen artifact paths under the Cullen input and adds a `cullen_oracle` output entry.
- `scripts/build-procedure-ir.mjs`
  Large refactor toward shared helpers, executable step IR parsing, validation grounding, and expanded output semantics.
- `The Foundations of Celestial Reckoning. Three ancient Chinese astronomical systems (Christopher Cullen) (Z-Library).pdf`
  Binary changed; no content-level summary performed.

## Command Suggestions Only

No Git commands were executed in this turn. If the current classification is accepted, the minimal add sequence would be:

```bash
git add .gitignore
git add scripts/align-cullen-procedure-ir.mjs scripts/assimilate-cullen.mjs scripts/audit-cullen-anchor-quality.mjs scripts/audit-cullen-chapter-coverage.mjs scripts/audit-cullen-led-source-reconstruction.mjs scripts/audit-cullen-oracle.mjs scripts/audit-cullen-procedure-anchors.mjs scripts/audit-cullen-procedure-completeness.mjs scripts/audit-cullen-target-span-alignment.mjs scripts/audit-sifen-target-family-candidates.mjs scripts/audit-source-cullen-alignment.mjs scripts/build-cullen-chunks.mjs scripts/build-cullen-search-index.mjs scripts/cullen-oracle-common.mjs scripts/cullen-procedure-anchor-common.mjs scripts/cullen-procedure-inventory-common.mjs scripts/extract-cullen-claims.mjs scripts/extract-cullen-pages.mjs scripts/extract_cullen_pages.py scripts/procedure-ir-common.mjs scripts/query-cullen-page.mjs scripts/query-cullen-proc.mjs scripts/query-cullen-source.mjs scripts/source-cullen-alignment-common.mjs
git add config/cullen-mini-gold-benchmark.json config/sifen-target-family-gold.candidate.json
git add scripts/scripts-note.md
```
