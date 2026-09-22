# Semantic Closure v0 — local acceptance

Baseline: `42fe05fa95cbd2727e3eb732c741e2ceb502a4c7`.
No commit, push, deployment, public snapshot replacement, corpus writeback, or modification of an existing scholarly ReviewJob.

## Contract and epistemic boundary

`SemanticClosure/1` is a read-only compiler sidecar with `assertions`, `conflicts`, `unresolved`, and the registered rule labels. Every recompile reconstructs it from the current graph, active replay facts, and separately supplied replay-conflict evidence.

`SemanticAssertion/1` records:

- `id`, `kind` (`quantity` or `term`), exact `target`, `facet`, and `value`;
- `authority` (`reviewed` or `derived`), `status`, and `usable`;
- `rule_id`, typed `depends_on`, alternative `proofs` with usability;
- `source_anchors` and projected `object_refs`.

Graph targets address a value/output port or a particular consumer input port. A graph-bound expression is still a graph assertion. A Term assertion addresses an exact occurrence; only an independently supported expression plus an exact naming rule establishes its derived interpretation. Knowing a unit or coordinate does not establish a lexical expression.

Kernel candidates retain their existing authority/support/authorization fields. Compatibility, uniqueness, absence of alternatives, and vocabulary coverage never generate a fact. There is no candidate-elimination inference. A candidate may remain suggested even when only one exists. Different unsupported expressions are an equivalence/coverage diagnostic, not automatically a formal contradiction.

Reviewed records with different decision origins retain distinct assertion identities, even when their values agree. Conflicted replay records remain visible but do not seed propagation. Conflicts quarantine the affected target/facet and grounded descendants; an unrelated supported facet remains usable. An explicit rejection cannot be silently resurrected as a derived interpretation.

## Rules and exact linkage

| Rule | Premise and conclusion |
| --- | --- |
| `SEM_TERM_SLOT` | Exact reviewed Term occurrence, selected syntax slot and one actual consumer/naming event → graph-bound expression at that local port/value. |
| `SEM_INPUT_VALUE` | A supported producer value fact → the exact consuming input port. |
| `SEM_IDENTITY_LOAD` | A supported input fact → result of a value-preserving load. |
| `SEM_IDENTITY_ALIAS` | A supported input fact → result of a value-preserving alias. |
| `SEM_ORDINAL_TO_ELAPSED` | Complete reviewed/derived ordinal coordinate, base 1, exact literal 1, compatible known unit/representation → elapsed coordinate, base 0. |
| `SEM_NAMES_OUTPUT` | An already supported graph expression plus the exact alias/naming syntax → the named Term expression. |

The ordinal predicate is extracted into `analysis_parser/semantic_rules.py` and shared with existing lowering. Numerical execution behavior is unchanged. No multiplication, division, historical cycle value, or conversion meaning is invented.

Term bridges use selected `node_id`, exact nominal slot anchors, operation kind, and read/write ports. An ambiguous/missing mapping produces `term_graph_link_not_unique`; there is no surface fallback. A reviewed consumer Term never mutates a shared producer. `name` and `remainder_name` follow their actual alias input value; quotient and remainder are not conflated.

Facts deduplicate in a finite positive saturation. No rule grows expression trees or computes unbounded numbers. Grounded dependency reachability invalidates conflicted descendants. The primary displayed proof uses a shortest grounded dependency path, so a cycle cannot provide its own authority or become the displayed justification.

Scholar projection remaps graph event/value references to existing Scholar objects, operation occurrences, and ports. Internal ID renumbering preserves public closure identities. Reviewed claims are not populated with derived records.

## Inspector and static behavior

- Derived Term annotations have a textual `derived` badge and authored expression hover.
- Selected objects distinguish interpretation from quantity properties; input/output port labels distinguish ordinal input from elapsed output.
- Provenance dependencies navigate to the existing Scholar object. Rules and full structured evidence remain inspectable.
- Procedure Model adds semantic summaries without changing nodes/edges or their identities.
- Questions are removed by QuestionPresenter only for an entailed Term expression. Quantity facts alone leave meaning questions present.
- Independent conflicts produce real review questions with existing retract actions. No automatic correction of a human decision occurs.
- Last-change summaries count actual before/after projection additions, removals, Term interpretations, and automatically resolved questions.
- Existing `ScholarSandboxSnapshot/1` export already carries the projection, renderer, details, and Procedure Model. Its additive fields preserve closure without a second exporter or schema fork.
- Static drafts preserve published closure and question inventory. No JavaScript inference, compile, execute, or API requests were added.

The public snapshot remains byte-identical to HEAD (Git blob `51b2e99e2b35bee7c7823a88bf17446a17552ab0`). Candidate snapshots exist only in `tmp/semantic-closure/`. They are disposable test decisions, not an accepted public scholarly state.

## Actual benchmark results

| Disposable case | Before | After reviews | After retract |
| --- | ---: | ---: | ---: |
| Real §38 | 9 questions | 8 after count; 7 after chapter-month Term review | Tested separately for identity closure below |
| Synthetic identity/naming source | 3 questions | 1 question | 3 questions; 0 derived assertions |

§38 supports the reviewed one-based 入蔀年 → source subtract-one → derived elapsed-year coordinate. It produces **no derived Term interpretation** in this interaction sequence. The two removed questions are answered directly by the scholar; no additional meaning question disappears automatically.

積月 and 閏餘 remain unresolved. The missing information is a registered typed relation connecting the reviewed operand expression, multiplication, divisor and distinct output ports. The current scope concept supplies no numerical cycle length, conversion factor, origin, or producer binding. The implementation reports the missing arithmetic semantic relation rather than asserting a specific historical value or answer.

The positive naming screenshot is a **fabricated §901 test source**, `置章月，名為積月。`, used to exercise identity propagation. It is not a reading of §38 and does not claim that the historical 積月 has that interpretation. Its reduction from 3 to 1 comprises one direct human answer and one automatically derived naming interpretation.

Evidence:

- `tmp/semantic-closure/benchmark.json`: exact §38 closure, provenance and 9→8→7 counts.
- `tmp/semantic-closure/invalidation.json`: 3→1→3 and zero remaining derived facts.
- `tmp/semantic-closure/benchmark.snapshot.json`, `identity.snapshot.json`: candidate static exports.
- `tmp/scholar-renderer-v02/acceptance.json`: full local browser interaction results and original research-job byte preservation.
- `tmp/static-scholar-sandbox/acceptance.json`: existing public snapshot with production assets.
- `tmp/semantic-closure/static-benchmark/acceptance.json`, `static-identity/acceptance.json`: candidate compiled states with production assets, draft/reload immutability, zero console/asset/API errors.

Screenshots:

- `tmp/semantic-closure/01-ordinal-elapsed-provenance.png`: real §38 quantity propagation.
- `tmp/semantic-closure/02-derived-term-desktop.png`: synthetic naming and derived provenance.
- `tmp/semantic-closure/static-identity/source-1440.png`, `source-390.png`: production static desktop/mobile provenance.
- `tmp/semantic-closure/static-benchmark/graph-1440.png`, `graph-390.png`: compiled §38 Procedure Model.

## Verification

- New closure/projection tests: **17 passed**. Artificial vocabulary/renaming, incompatible same-shape graph, single-candidate non-authority, exact naming entailment, preserved ambiguity, conflict quarantine, independently supported equal facets, genuine replay conflicts, explicit rejection, unseeded cycles, reload/retraction, port distinction, stable public identities, and UI provenance are covered.
- Full adjudication + Workbench Python run: **295 tests; 291 passed, 4 existing errors**. This includes §38 golden, §15 context invariant, ReviewJob service, Procedure Model, and exporter regressions.
- Each of those four errors was reproduced using HEAD versions of changed Python modules, without reverting the working tree. Two old HTTP fixtures lack the required site index; two legacy presentation paths lack ontology labels for `ReviewedCandidate` and `ReviewedSlotMissingExactGrounding`. Evidence: `tmp/semantic-closure/baseline-regression.txt`. They are not counted as passing and are outside the closure implementation.
- Local Inspector AppTest suites: **25 passed**.
- Node draft/layout suites: **12 passed**.
- Full local renderer/browser suite: **22 check groups passed**, including real count/meaning decisions, source↔graph selection, context, Unicode boundary correction, reload, retract, and closure at 1440/768/390.
- `NODE_ENV=production`, `GITHUB_ACTIONS=true`, `npm run build`: passed, 100 copied files / 15 pages.
- Ordinary static HTTP under `/mathesis/`: existing public snapshot suite passed (12 groups); both candidate snapshot closure suites passed at 1440/768/390. No Python server is used for static acceptance.
- Independent code review identified replay-conflict visibility, overly broad quarantine, and review-origin/proof identity risks. Those were fixed and the reviewer verified the fixes without finding another important issue.

Compiler version locks now include the shared transition predicate and closure module. Existing locked research jobs can therefore be stale under the new engine, as intended. They were preserved, not silently migrated. New disposable jobs exercised the current compiler. A final accepted scholarly ReviewJob and explicit approval are still required before regenerating the tracked public snapshot.

## Exact implementation files

Production:

```text
adjudication/compiler.py
adjudication/session.py
adjudication/semantic_closure.py
analysis_parser/scoped.py
analysis_parser/semantic_rules.py
workbench/annotation_projection.py
workbench/semantic_projection.py
workbench/semantic_presentation.py
workbench/question_presenter.py
workbench/scholar_renderer.py
workbench/procedure_model.py
tools/parser_inspector/review_panel.py
tools/parser_inspector/procedure_model.mjs
src/js/scholar-sandbox.mjs
```

Tests:

```text
tests/adjudication/test_semantic_closure.py
tests/workbench/test_semantic_closure.py
tests/workbench/test_question_presenter.py
tests/workbench/test_sandbox_snapshot.py
tests/workbench/scholar-renderer-browser.mjs
tests/workbench/semantic-closure-static.mjs
tests/scholar-sandbox-browser.mjs
```

Documentation: this report and `docs/superpowers/plans/2026-09-21-semantic-closure.md`.
The pre-existing `AGENTS.md` change and unrelated local artifacts are outside this work.
