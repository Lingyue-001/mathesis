# Source-question workflow and deterministic rule trace

Local implementation and acceptance, 2026-09-22. Base HEAD: `42fe05fa95cbd2727e3eb732c741e2ceb502a4c7`.

The checkout already contained uncommitted Semantic Closure and other local work. Those changes were preserved. This pass changes the local Scholar Inspector source-review workflow and audit metadata; it does not change parser rules, graph topology, execution meaning, Domain Kernel knowledge, or decision payload contracts. Nothing was committed, pushed, deployed, or promoted to the tracked public snapshot.

## Reused backend products

The existing backend supplied all required pieces: `source_supply` facet identities; canonical formal/consumer imports; Flow status; linker candidate compatibility; effective units and text; `parameter_index`; literal occurrence search; `attach_context`, `bind_value`, and `declare_parameter`; exact source anchors and decision references.

Current Question now owns the source decision:

1. Exact parameter declarations remain visible, including an explicit no-match state. Exact declaration spans come from the existing parameter extractor in an optional presentation mode; its default output is unchanged. Full unit text is disclosed separately.
2. Canonical producer candidates remain visible, including the empty state. The native form consults the canonical import's compatibility evidence when the diagnostic contains only unfiltered candidate IDs. Text search never supplies a producer.
3. Other exact occurrences remain visible as compact section/type/quote popover rows. Only the declaration's own span is excluded: a later use in the same unit remains listed. Full chunks are never expanded inline before the decision controls.
4. Source resolution offers supported bindings, additional source material, and leaving the issue unresolved. Every valid source-supply question can offer context, independently of compiler action suggestions. A stale/invalid decision anchor cannot enable it.
5. Additional material can be browsed across all effective chunks or filtered by a literal substring. Each choice exposes its identity, type, and full effective text. An empty search disables saving.
6. Execution fallback is a separate secondary radio group, labelled `Supply a runtime test value for “{formal}”`. Both groups are visible without a “Decision area” switch; selecting either clears the other. Its existing payload merely permits a runtime input; it does not assert historical provenance or meaning.
7. Choices/search are unsaved until the single Current Question `Confirm and re-run` action submits the existing contract. Selected Source Object remains inspection/reference, with no independent context-save control.

Corpus rendering is shared between Current Question and Selected Source Object. Meaning questions retain their original evidence display; this pass does not claim a rule trace for every other question family.

## Presentation correction: fixed local hierarchy

Selected Source Object always renders four containers in the order Terms, Constructions, Steps, Flows, followed by review/provenance. These are architecture names, not new visible headings. Existing field labels remain; an empty layer explicitly reports that nothing is recorded. The selected object is bold and bordered within its layer. Object names in the other layers select that recorded object without writing a decision.

`scholar_renderer.procedure_context` joins recorded IDs only: component parents, slot links, construction realizations, Step construction IDs, input Term/Flow IDs, output label Term IDs, and Flow consumer/producer Step IDs. Its finite expansion closes only construction–realization edges. Upstream input Steps remain references, preventing an entire procedure from expanding recursively into the pane. Output Terms connect to recorded naming constructions. Text, spans, and matching strings never create relations.

The conditional material picker uses literal search across the available source corpora, then the section selector, a short selected-draft preview with optional full text, and `draft · not attached`. Searching, inspecting a popover, changing radio groups, and selecting objects do not persist. Only the selected option's assertions are displayed.

Source choices start unselected. A presentation-only generation guard rejects Confirm clicks from a render that predates a radio change, clears both groups, and requires a fresh selection. This prevents a rapid source/runtime switch from submitting an obsolete context attachment. The runtime option cannot carry the previous picker's context document. Both a coalesced AppTest event and an un-waited real-browser switch/Confirm sequence cover this regression with disposable jobs.

The correction is limited to `workbench/scholar_renderer.py`, `tools/parser_inspector/review_panel.py`, their renderer/panel/browser tests, and this report. It does not change the existing trace records, question title templates, decision payloads, parser, graph, public snapshot, or static JavaScript renderer.

Acceptance artifacts: `tmp/scholar-renderer-v02/source-review-acceptance.json`, `source-question-{1440,768,390}.png`, and `four-layer-{term,construction,step,flow}-{1440,768,390}.png`. The focused browser suite verifies order, exclusive source/runtime selection, first-question-viewport decision controls, click-to-inspect full chunks, four-object selection, overflow, and no ReviewJob writes. Pure renderer tests verify the shared §38 context, explicit naming relations, and exclusion of an unrelated object with identical text and span.

Correction verification: 75 targeted unit/AppTests passed (`test_review_panel`, `test_inspector`, `test_scholar_renderer`, `test_source_review`, `test_question_presenter`); all 22 existing browser regression groups passed; the focused 1440/768/390 hierarchy and rapid-confirm browser suite passed with zero page errors. The latter's inspection stage leaves job bytes unchanged; its separate rapid-confirm case intentionally saves only a runtime permission in a disposable job. The tracked public snapshot remains Git blob `51b2e99e2b35bee7c7823a88bf17446a17552ab0`.

## Audit schema and executable linkage

`RuleTrace/1` records `rule_id`, `stage`, `conditions`, `matched`, `result`, `subject`, and `implementation`. Each condition contains its actual and expected values, operator, and evaluated match. The same returned boolean is consumed by the real branch. Native Python call sites remain authoritative; there is no external rule configuration, inference engine, source-code guessing, or generated explanation prose.

| Rule | Executed implementation |
| --- | --- |
| LINK-IMPORT-01 | `analysis_parser/program_ir.py::link_entry` |
| REVIEW-MISSING-INPUT-01 | `adjudication/review_queue.py::build_review_queue` |
| SOURCE-SUPPLY-01 | `workbench/question_presenter.py::_source_supply_target` |
| PARAMETER-DECLARATION-EXACT-01 | `source_adapters/corpus_index.py::source_review_evidence` |
| EXACT-OCCURRENCE-01 | Same query, with per-unit literal match observations |
| SOURCE-CONTEXT-01 | `workbench/question_presenter.py::build_questions` |
| SOURCE-BIND-01 | `workbench/service.py::_review_forms` |
| RUNTIME-INPUT-01 | `workbench/service.py::_review_forms` |
| SCHOLAR-OPTION-01 | `workbench/question_presenter.py::_offered_action`; records the existing native resolving-action gate separately from underlying eligibility |
| REVIEW-DEFER-01 | `workbench/question_presenter.py::_question`; unconditional availability of leaving a source issue open |

Linker audit records leave through an optional side channel and live on the reviewed compilation, never inside graph IR. Queue/form/question records carry audit metadata outside the stable Scholar semantic projection. The Why UI shows the condition table, result, evidence identities, a compact formation path, and actual source disclosure.

Implementation provenance includes repository-relative file, Python symbol, HEAD revision, exact file SHA-256, committed/working-tree state, and mechanically obtained source lines. An uncommitted file is explicitly marked `working_tree`; its HEAD is not presented as proof that the displayed source was committed. Tests compare the bytes, source lines, and Git state directly.

## Actual §38 example

Fresh disposable ReviewJob, no attached context:

```text
formal: 入蔀年
consumer: def-2e26c7772103b8a537d4
display anchor: sifen:38 [6, 9), Unicode code points

LINK-IMPORT-01 → missing_import
REVIEW-MISSING-INPUT-01 → missing_input, blocking
SOURCE-SUPPLY-01 → source_supply

Exact parameter declarations: no_match, 0
Other exact occurrences: fact, 3
  §38 [6, 9), §41 [9, 12), §45 [6, 9)
Canonical producer: no_match
Attach context: available_action
Runtime test input: fallback_action
```

These are observations from the generic rules. Production source-review helpers contain no procedure/surface whitelist. Tests also exercise neutral terms, false runtime eligibility, rejected canonical producers, missing compiler suggestions, invalid anchors, and a declaration followed by another use in the same chunk. Historical interpretations were not added.

## Verification

Use `tools/parser_inspector/.venv/Scripts/python.exe -X utf8` as `PY` below. System Python lacks Streamlit; Windows non-UTF-8 execution also breaks existing fixtures that omit an explicit encoding.

| Command | Result |
| --- | --- |
| `PY -m unittest tests.workbench.test_source_review tests.workbench.test_question_presenter` | 24 passed |
| `PY -m unittest tests.workbench.test_source_review tests.workbench.test_scholar_source_projection tests.workbench.test_scholar_source_diff` | 51 passed before the additional meaning-evidence guard test |
| `PY -m unittest tools.parser_inspector.test_review_panel tools.parser_inspector.test_inspector` | 26 passed |
| `PY -m unittest discover -s tests/adjudication -p 'test_*.py'` | 140 passed |
| `PY -m unittest discover -s tests/parser_v3 -p 'test_*.py'` | 98 passed |
| `PY -m unittest discover -s tests/workbench -p 'test_*.py'` | 164 run, 160 passed, 4 existing errors |
| `PY -m unittest discover -s tests -p 'test_*.py'` | 88 run, 85 passed, 3 existing errors |
| `node tests/workbench/scholar-renderer-browser.mjs` | 22 full real-browser check groups passed, 1440/768/390, disposable ReviewJobs, no page errors |
| `SOURCE_REVIEW_ONLY=1 node tests/workbench/scholar-renderer-browser.mjs` | Final source zero-state, real condition table and source disclosure passed at 1440/768/390; viewing leaves stored decisions unchanged |

The Workbench errors are the previously identified HTTP fixtures lacking a site index (`test_http_decision_endpoint_appends_then_recompiles_instead_of_accepting_a_graph`, `test_ontology_http_and_workbench_share_live_registry`) and legacy ontology labels (`test_actual_authored_candidate_does_not_claim_rule_or_human_trial`, `test_actual_resegment_and_retract_states_have_language`). The top-level errors are `test_status_endpoint_checks_saved_real_result_against_current_units` (same HTTP fixture issue), and two Pattern importer frozen-input checks: `test_annotation_files_are_actually_opened_only_after_both_compiles`, `test_clean_processes_are_byte_identical_and_preserve_compiler_before_import`. They fail on the already changed `analysis_parser/ontology.py` frozen hash; that file was not modified in this pass. These failures are not counted as passing.

The projection golden/context invariants, parser execution tests, real context attachment, existing producer binding, runtime permission, reload and retract paths remain covered. Independent read-only review found declaration-span/deduplication and provenance-test gaps; these were corrected and rechecked.

Evidence/screenshots: `tmp/scholar-renderer-v02/acceptance.json`, `source-review-acceptance.json`, `source-question-1440.png`, `source-question-768.png`, `source-question-390.png`, `source-controls-390.png`, and `source-why-390.png`.

## Boundaries and remaining publication work

All requested source rules have a mechanically connected trace. An indexed declaration with unavailable exact grounding is explicitly labelled as such, rather than assigning the first matching word an invented declaration span.

Decision schemas and replay semantics are unchanged. Existing engine-version locks still apply: editing the linker file changes its engine hash, so an old locked research job can require explicit revalidation. No private job was silently migrated or overwritten. Replay/retract tests use disposable jobs with the current engine.

This deliverable is the local Inspector workflow. A future static export can carry the new question/audit metadata through the existing snapshot exporter, but the public JavaScript workflow and tracked snapshot were not promoted in this pass. There is no claim that the GitHub Pages or Netlify page now shows this UI.

## Exact files touched in this pass

```text
analysis_parser/rule_trace.py                 (new)
analysis_parser/program_ir.py
adjudication/compiler.py
adjudication/review_queue.py
source_adapters/corpus_index.py
workbench/service.py
workbench/question_presenter.py
workbench/scholar_renderer.py
tools/parser_inspector/review_panel.py
tests/workbench/test_source_review.py         (new)
tests/workbench/test_scholar_renderer.py
tests/workbench/scholar-renderer-browser.mjs
tools/parser_inspector/test_review_panel.py
docs/source-question-rule-trace.md            (new)
```

Other dirty files belong to earlier work, including `AGENTS.md`, Semantic Closure, and the static sandbox. Private NOTE/LOG files were not changed.
