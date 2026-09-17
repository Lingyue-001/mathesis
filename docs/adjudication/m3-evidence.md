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

## Persisted-session regression after 0cf614b

On the unchanged baseline, a fresh §40 session had four compiler unresolved
records and 13 review questions, including `周天乘減之` at `sifen:40 [9,14)`.
An obsolete saved engine identity reproduced the reported blank page without a
JavaScript exception: `compile_reviewed` stopped at `stale_identity` with
`graph=null` and an empty queue; the service reported `review=completed`; the
browser returned before unhiding its analysis panel, then printed a success
message with zero questions. This was a stale-response/render contract failure,
not evidence that the unsupported constructions had become supported.

Blocked compilation now emits a session revalidation question. The service keeps
the original session and `graph=null`, reports `needs_revalidation`, and supplies
a separately labelled `current_automatic_reference` through the same compiler
with an empty current session. The browser renders that reference read-only,
keeps the saved decisions/identity locks intact, and permits their export.
It does not silently migrate, approve, execute, or edit the stale interpretation.
Manual revalidation/migration of an old session is still required.

`test_stale_session_preserves_decisions_and_exposes_separate_unresolved_reference`
tests stale source and runtime identities, original decision retention, reference
equivalence to a fresh compilation, and execution rejection.
`adjudication-browser.mjs` now tests real §40 content visibility (Source,
Procedure Structure, Typed Graph), the specific unresolved span and question-to-source
navigation, cold reload with stale persisted sessions, original export, read-only
controls, and re-import. Both tests failed on 0cf614b before the fix.

Verification: adjudication 71 (including M3.1 19), Workbench 20, parser 61,
parser-v3 94, rescue 78 (including engineering 35), reconciliation 5, both browser
suites, CText 4, and the Eleventy build passed. The rescue suite still emits its
pre-existing unclosed-fixture ResourceWarning. Browser actors remain
`scripted_fixture`; this is not a human usability trial.

Runtime investigation also found three Workbench processes listening on 8792;
the older instances were stopped and final browser validation used a single
current-code process. Old processes can continue serving older compiler modules
even after a site rebuild; restart the Python service after Python changes.

## M3.2A canonical ontology and scholar language (2026-09-18)

Baseline: `c3e5d2d`. Inventory used imported formal `GRAMMAR`/`EXACT`,
`OPERATION_CONTRACTS`, `ACTIONS`, `QUANTITY_UNITS`, `UNIT_QUANTITY_KINDS` and
actual service/decision results. No Python source-string mining was used.
The two exposed corpus targets initially returned 9 operation kinds, 14 syntax
kinds and 3 question kinds; obsolete identity replay adds the stale-session
question. Real resegmentation additionally exposed `unknown_quantity`; a real
typed-structure decision established the authored-candidate provenance case.

`analysis_parser/ontology.py` contains 441 entries including formal syntax
aliases. The category/code pair is its key. It covers operations/constructions,
quantity kinds/roles/units/representations, issue/cause, decisions, candidate,
review/session/validation/execution/comparison/stage states, profiles, ports and
evidence. Entry fields describe minimum evidence, not replacement executable
signatures. Unknown codes at presentation boundaries fail explicitly.

`workbench/presentation.py` translates existing structured facts only. Queue
severity, actions and source anchors stay equal to the backend originals;
overlapping constructions are labelled nearby evidence, not legal substitutes.
Candidate status does not assert scholarly confirmation. Authored structures
retain their decision origin and actual actor type. Stage artifacts, quantities,
ports, scope, control attributes and stale automatic-reference identity remain
inspectable. Machine identifiers still address objects internally and remain
available in raw graph/stage debug disclosures.

`GET /api/ontology` and the website `/methodology/` use the same registry as the
Workbench view model. JavaScript only renders the labels. Existing controls get
their labels from the API; the output-port field now shows names from existing
output signatures while submitting their unchanged codes. These names do not
certify compatibility. Profile selection retains its empty initial choice.
No CSS/graph geometry, parser/IR/executor rule, Pattern Lab or primitive expansion
was changed.

Seven tests in `tests/workbench/test_presentation.py` cover:

- formal vocabulary/entry completeness and unknown-code rejection;
- semantic goldens and prohibited claims for missing input, unsupported and
  incomplete construction, unknown quantity, stale session, conflicting
  decisions, incompatible binding and extension request;
- both actual corpus outputs, immutable graph/queue inputs, unchanged suggested
  actions, and explicit failure for new unregistered states;
- actual resegmentation/recompilation/retraction and authored-structure actor
  provenance;
- new registry entry propagation, plus a live HTTP reference/Workbench check.

The existing browser acceptance also checks §40's actual unresolved span,
source/structure/graph visibility, stale reference, translated normal text,
Methodology entry count/labels against the live API, and rendering newly supplied
view-model/reference entries without a browser map. The latter renderer
extension is a labelled scripted fixture; the HTTP registry mutation is tested
separately in Python. Neither is a human trial or a historical interpretation.

Verification on this tree:

| Check | Result |
|---|---|
| `unittest discover -s tests/workbench` | 27 passed, including 7 language tests |
| `unittest discover -s tests/adjudication` | 71 passed, including M3.1 19 |
| `unittest discover -s tests/parser` | 61 passed |
| `unittest discover -s tests/parser_v3` | 94 passed |
| `unittest discover -s tests/parser_rescue` | 78 passed, including engineering 35 |
| `unittest discover -s tests/reconciliation` | 5 passed |
| `tests/workbench/adjudication-browser.mjs` | passed in Chromium against localhost |
| `tests/workbench/browser-smoke.mjs` | passed, including Pattern Lab navigation |
| CText parser tests / Eleventy build / whitespace check | 4 passed / passed / passed |

The existing rescue fixture ResourceWarning remains. Coverage is the exposed
Workbench vocabulary plus the formal tables and exercised decision paths; it is
not a claim that every unexposed corpus passage has been interpreted. New visible
codes require authored entries and tests. API error details stay in the debug
console, with a human-readable failure message in the normal view. Existing stale
sessions remain read-only until separately revalidated; language changes do not
migrate them. Local access: `http://127.0.0.1:8792/adjudication/` and
`http://127.0.0.1:8792/methodology/`. No push or M4 work.
