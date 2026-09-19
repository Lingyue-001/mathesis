# Parser Inspector Context and Stages Implementation Plan

**Goal:** Deliver source-backed declarations and upstream procedure outputs as actual reviewed compiler inputs in Parser Inspector, with durable analyses, staged review, recompilation, undo and restoration.

**Architecture:** Keep one production parser and exact executor. Corpus discovery produces an evidence catalogue, independent of selection; analysis selections feed the existing adjudication compiler and Workbench response builder. Inspector consumes one rebuilt response for all panels. Native runner remains a separate automatic baseline.

**Tech Stack:** Python, existing parser/adjudication/Workbench modules, Streamlit, unittest and browser verification.

**Spec:** User-supplied `C:/Users/DELL/Downloads/MATHesis_Codex_Context_Stages_2026-09-19.md` (2026-09-19), replacing older A+B/context requirements.

## Constraints and execution

- No destructive Git/filesystem operations, canonical source changes, frozen evidence changes, or loss of historical research decisions.
- Start at `2973dc7014cca300768f54cc9e28139387ac4ef8`; existing untracked Cullen PDF remains untouched.
- Existing local workspace is the delivery location because the live Inspector and human records are here. User explicitly authorizes autonomous development, verification and normal batch commits.
- A → B → C → D: write failing tests, implement, verify, commit each batch. Independent inspection may proceed while A is implemented; later batches do not commit before A.
- Use subagent-driven-development for the bounded segmentation/migration implementation and independent review; controller owns integration. No additional approval for authorized routine work. Ask only about non-unique human migration or research semantics.
- NOTE/LOG updated before each requested batch commit; do not commit private records.

## A — segmentation proposals and migration

Files: `source_adapters/corpus_index.py`, `corpus_review.py`, dedicated migration module if needed, existing extraction command, segmentation UI, corpus tests.

- [x] Test nonoverlapping longest-first `cue_count`, separate parameter exclusions, 夜半 counterexample, real §35–36 and §57–58, independent 求 units and planetary records.
- [x] Compute physical spans and evidence once; retain contextual follow-up proposals without forced merging.
- [x] Generate exact-anchor auto difference and affected review/selection/artifact report before migration. Archive original bytes; preserve effective reviewed regions, original history, historical restore/undo semantics.
- [x] Verify real human records, preset packets, isolated migration tests and native runner; commit A.

## B — source-wide resource discovery

Files: `source_adapters/resources.py`, tests, Inspector resource display (D integration).

- [ ] Test all effective units, internal declarations, multiple same-name resources, isolated scan failures, provenance offsets and stable resource addresses.
- [ ] Reuse documents/tokenize/parse_syntax/compile_context/static_interface. Separate mentions, definitions, ports and runtime values. Record full coverage and ingestion exclusions.
- [ ] Search exact/normalized/registered aliases/fuzzy; preserve scopes, evidence and review separately. No full-source execution or global numerical environment.
- [ ] Verify and commit B.

## C — dynamic analyses and actual Context compilation

Files: `workbench/analysis.py` (persistence/orchestration), `source_adapters/corpus.py`, narrow adjudication/Program IR interfaces, `workbench/service.py`, tests.

- [ ] Test dynamic §39 Primary, §38 積月 with explicit 入蔀積月 mapping, §15/16 declarations, external 入蔀年, prefix execution and input changes; external-input alternative; duplicate/scoped ambiguity.
- [ ] Save versioned selections, contracts, decisions, resources and dependencies. Retain archived session/model versions and source locks. Selective freshness uses selected units.
- [ ] Apply declarations only at adopted resource spans; explicit consumer/provider/port mappings enter normal linker. No graph patching or reuse of old numeric results.
- [ ] Provide explicit independent/follow-up procedure choice, actual recompilation, partial target execution and recursive requirements/cycles.
- [ ] Reuse Workbench execution with dynamic saved input contracts; verify legacy tests and commit C.

## D — usable staged Inspector loop

Files: `tools/parser_inspector/analysis_review.py`, `app.py`, reusable registry search/form APIs, tests and delivery documentation.

- [ ] Test source/scope → lexical/construction → hierarchy/bindings → graph/execution confirmations with version locks and selective downstream invalidation.
- [ ] Browse effective units and resources; adopt/reject/map/select producer or external input with reasons; show recursive needs and current adoption/binding/use status.
- [ ] Generate all supported construction forms from backend registry with typed slots. Support local sense/alias search and reverse lookup, existing executable types and ExtensionRequired.
- [ ] Persist actor/reason/before/after, undo/restore; rebuild every panel from one response. Keep JSON in debug expander and automatic/reviewed outputs distinct.
- [ ] Real browser: Primary → Context → stages → binding/construction edit → changed graph/requirements/output → undo → refresh recovery. Required review controls formal export.
- [ ] Run appropriate parser/adjudication/Workbench/Inspector regressions and site build; independently review; document entry, provenance, numerical/research limits; commit D.

## Initial inspection evidence

- Existing Inspector calls native runner only; Workbench `_reviewed_response` already provides projections, presentation and review queue from `compile_reviewed`.
- `execute_adjudication` currently requires preset registry input contracts; dynamic selection must remove that dependency through a shared narrow execution function.
- Local sifen auto has 86 units, five reviewed units and 15 events. Santong and Jiuzhi have no recorded segmentation decisions. §49–50 is reviewed as one effective unit; preserve this explicit state despite new machine separation.
- No saved session JSON found in repository output inventory; existing browser-local Workbench sessions must remain untouched and retain strict stale handling.
