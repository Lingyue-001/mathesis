# Context stages — Batch A segmentation and migration

2026-09-19. Implementation and verified migration; no canonical calendar text, Cullen text, evaluation evidence, changed by this batch. Existing private NOTE/LOG record the authorized batch progress before commit.

## Rules and entry points

`source_adapters/corpus_index.py` counts cues left to right, longest at each position, without overlap. `cue_count()` retains threshold four. `求` is a procedure marker rather than a density cue; separate parameter-name exclusions retain `求` and allow declarations such as `日餘，百六十八。`.

Physical spans and their boundary events are computed once. `夜半` alone no longer proposes a join; the real §35–36 and §57–58 incomplete joins remain. Segmentation Review displays the actual left/right source text and matched conditions. `步術` remains an observed procedure marker; repeated planetary parameter fields retain planet scope and motion records remain reference candidates.

Initial `求` paragraphs remain separate automatic units. Adjacent procedure + `求` produces an evidence-bearing `confirm_followup_grouping` proposal, with independent/follow-up choices; the proposal does not establish base, parent, or data dependency. Reviewed effective boundaries remain the downstream source selection. Explicit anchored procedure choices now rebuild Program IR before linking. Follow-ups select and restore the actual parent base, including when another dependency executes between base and query; independent choices create an independent definition. A different parent/base is rejected rather than assigned invented semantics.

The existing extraction command supports:

```powershell
python scripts/corpus/extract_sifen_units.py --source-id sifen --migration-report
python scripts/corpus/extract_sifen_units.py --source-id sifen --migrate-rules
```

Normal regeneration refuses a changed rule version until migration. No parallel extraction command was added. `corpus_migration.py` handles the separate archival/translation responsibility; `corpus_review.py` retains the transaction and history APIs.

## Exact-span migration evidence

Reports were written before authoritative replacement. The original `auto.json`, `overrides.json`, `effective.json`, and `manifest.json` were archived as exact bytes in each source's `migrations/<original revision>/` directory. Archive files and reports are write-once: conflicting existing bytes block migration. Stored hashes protect historical baselines on load. These archived bytes are runtime provenance and must be tracked without Git newline conversion.

| Source | Automatic units before → after | Effective units before → after | Preserved history events |
| --- | --- | --- | --- |
| sifen | 86 → 98 | 86 → 97 | 15 |
| santong | 171 → 172 | 171 → 172 | 0 |
| jiuzhi | 79 → 79 | 79 → 79 | 0 |

The exact reports and archived baselines are linked from:

- [Sifen report](../../corpus-review/sifen/migration-report.json)
- [Santong report](../../corpus-review/santong/migration-report.json)
- [Jiuzhi report](../../corpus-review/jiuzhi/migration-report.json)

All five original sifen reviewed effective regions preserve their unit IDs, source spans, text, types, anchored relations, compiler-input hashes, and complete human-review records. §49–50 remains one reviewed effective unit through an explicit merge override even though the new machine proposes two units. §51 retains its reviewed relation target covering both §§49–50. The old §23 type override becomes redundant because the new machine recognizes its parameter declaration; its original bytes and history remain archived. The five reviewed effective regions correspond to six annotated new automatic units because the original §49–50 review spans two new proposals; this is not a new human review action.

All 15 history entries remain unchanged. All 30 historical before/after states were compared with pre-migration replay and matched. Historical views use the archived baseline applicable to the event. Undo and regional restoration translate only the event's connected source region against the current automatic partition; unrelated current units and review records remain intact. An isolated copy of the actual workspace passed undo of revision 15 and restoration to revision 15 after; the live workspace still has 15 events. Review found and corrected an initial whole-snapshot undo that incorrectly reinstated unrelated old machine groups. The regression now compares every unaffected unit's exact compiler-input hash and review records before/after archived undo, using both a synthetic changed partition and the immutable real revision-15 archive.

No fuzzy text migration occurs. A new machine unit crossing reviewed and unreviewed regions produces a specific pending question and leaves authoritative files intact. Source-byte changes remain blocked by the source lock.

## Selections, artifacts, and limits

The report inventories configuration, local output stores, corpus workspaces, and `tools/parser_inspector/output`, including all 13 existing `output/current` JSON artifacts and the preset selection manifest. The two preset source packets (`sifen-3-5`, `sifen-3-7-alternative`) still select the same units and text hashes; no preset manifest edit was needed. Ten unreviewed sifen effective units have changed identities, boundaries, or relation targets and are listed in the report.

Existing output files were retained. Browser-local sessions cannot be enumerated by a filesystem inventory; they remain subject to strict source and compiler-identity checks when reused. The controller's compiler change changes engine identity: old compiled sessions are not silently relocked. This batch does not interpret or validate the new grouping candidates as historical computations.

## Verification

Failing regressions were observed before implementation for cue overlap, parameter exclusion, nighttime continuation, duplicate physical-span calculation, forced query merging, the migration entry point, and visible boundary evidence.

```powershell
tools/parser_inspector/.venv/Scripts/python.exe -m unittest tests.test_corpus_index tests.test_segmentation_review tests.test_corpus_migration tests.test_corpus_segmentation_rules
# 48 passed, including Streamlit AppTest interactions.
tools/parser_inspector/.venv/Scripts/python.exe -m unittest tests.test_corpus_dependencies tools.parser_inspector.test_inspector
# 13 passed, including native runner compatibility and selective artifact freshness.
```

The tests use temporary workspaces. The former `test_corpus_index` setup that regenerated the live research workspace was replaced with an isolated fixture. Historical data tests cover archive bytes, unchanged original history, all historical sides, undo/restoration, unrelated new work, repeat-migration no-op, archive tampering, and nonunique migration refusal. `git diff --check` passed. Streamlit emits its standard bare-test-context warning; no test failed.

Final independent review passed 62 scoped tests and 79 adjudication regressions. Parser rescue (78) and parser v3 (94) also passed. Eight procedure-choice tests cover recompilation, retraction, same-document ownership, explicit base scheduling and runtime snapshot restoration.
