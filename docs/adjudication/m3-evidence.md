# M3 browser workbench evidence

M3 extends the existing Procedure Workbench. It does not change Pattern Lab, `analysis_parser/`, the v3.1 executor, or M4 primitive families.

## Implemented evidence chain

`source_adapters/corpus.py` builds SourcePacket 3.0 from the actual registered corpus. `workbench.service.open_adjudication()` creates or accepts an `AdjudicationSession`, calls `compile_reviewed()`, turns the result into a `ReviewedProcedureBundle`, and projects it for the browser. `workbench.api` exposes this only through loopback same-origin endpoints. A browser decision is appended through `append_decision()` and recompiles; no request accepts a graph.

The page exposes two distinct views:

- System processing records: source/scope, lexical/syntax, procedure/control, quantity/binding, graph/coverage, and review. Their states come from the returned compiler products.
- Research structure: L0–L3 source evidence, hierarchy, typed graph, coverage ledger, trace, and review questions. Source, step, graph node, and question all use source anchors/object links.

The registered procedures are `sifen-3-5` (the previously exposed executable local procedure) and `sifen-3-7-alternative` (actual 四分历 §40, deliberately retained as a review-hole example). They use the same corpus adapter and page path.

## Test IDs and results

| Requirement area | Actual test / evidence | Result |
|---|---|---|
| M3-A stages, projection, two corpus targets | `tests.workbench.test_adjudication_workflow.ReviewedWorkbenchTests.test_open_adjudication_returns_real_reviewed_products_and_stages`; `test_same_adapter_exposes_a_second_real_procedure_with_a_review_hole` | pass |
| Reviewed API never accepts a browser-supplied graph | `test_http_decision_endpoint_appends_then_recompiles_instead_of_accepting_a_graph` | pass |
| Local grammatical-function correction | `tests.adjudication.test_m3_local_revision` (4 tests) | pass |
| M2 regression contracts, stale/retract, branch isolation | `tests.adjudication.test_session_replay`; `tests.adjudication.test_m21_correctness` | pass |
| Existing corpus/service/projection/same-origin guardrails | `tests.workbench.test_smoke`; `tests.workbench.test_projection` | pass |
| Actual browser workflow | `tests/workbench/adjudication-browser.mjs` | pass on `http://127.0.0.1:8790/adjudication/?actor=scripted_browser` |
| Existing Workbench and Pattern Lab entry | `tests/workbench/browser-smoke.mjs` | pass on the same server |

The M3 browser test records actor `scripted_fixture`, not human. It verifies source selection, six returned stage records, layer switching, review question display, local lexical decision and recompilation, reload persistence, resegmentation then retract restoration, branch creation, export/import, a second real procedure, and astral/combining/newline/repeated/multi-span code-point coordinates.

## Deliberate limits

- Browser session persistence is a versioned, one-key `localStorage` record. It is atomically replaced and server-revalidated on reload/import; it is not a shared session directory or deployment service.
- The UI offers the existing `load` and `name` registry forms plus review actions, binding, scope, profile, context, root parameter, unresolved, and extension request. It does not yet generate a complete form for every registry operation signature.
- The local lexical-role action is scoped source evidence. It is deliberately not a global dictionary update and does not create a graph operation by itself.
- Numerical reconstruction calls `/api/adjudication/execute`, which recompiles then executes the reviewed graph currently in the session; it remains auxiliary to the structural review.
- Comparison status is explicitly `unavailable`; dual reviewed graph comparison and primitive expansion remain M4 work.

## M3.1 consistency repair evidence (2026-09-17)

The independent audit's 14 counterexamples and five positive controls now run
against the current repository as `tests/adjudication/test_m31_consistency.py`.
The audit ZIP's executable is a frozen snapshot, so it remains historical
evidence rather than an authority on current source behavior.

| Shared repair | Current evidence |
|---|---|
| One versioned decision payload and semantic target contract; atomic candidate/manual edits | 6 counterexamples and all 5 positive controls pass |
| One reviewed syntax snapshot for context, Program IR, methods, controls, graph, and projection | 3 syntax/context counterexamples pass |
| One emission-time quantity metadata finalizer | 2 metadata counterexamples pass |
| Structural audit-derived closure and explicit ontology-extension review outcome | 2 closure/extension counterexamples pass |
| Idempotent context document attachment; failed saved-session replay stays preserved in the browser | 1 attachment counterexample; `adjudication-browser.mjs` interception test pass |

Final local validation: M3.1 19/19; adjudication 71/71; parser 61/61;
parser-v3 94/94; rescue 78/78 (including engineering 35/35); Workbench 19/19;
reconciliation 5/5; both Workbench/Pattern Lab browser smoke tests; and Eleventy
build all pass. `set_scope` was also replayed through the reviewed service using
an existing canonical anchor; it produced the current reviewed graph without a
browser graph payload.
