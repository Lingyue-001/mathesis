# Semantic Closure v0 implementation plan

> Execution: inline, using executing-plans and test-driven-development. The user explicitly authorized revision followed by implementation. No commit, push, or public snapshot replacement.

**Goal:** deterministic typed propagation with inspectable, retractable provenance, separating quantity facts from lexical interpretations.

**Architecture:** a pure adjudication sidecar consumes current graph and replay-reduced decisions. Registered rules produce finite facts; no Kernel candidate creates authority. Existing compiler numerical behavior, IR, executor, replay, Kernel and Scholar object identities stay intact. Share the existing ordinal transition predicate with closure. Questions consume closure before projection; shared renderer/export consume the resulting projection.

**Spec:** the user's Semantic Closure v0 attachment plus all five accepted audit corrections and the subsequent quantity/Term separation. Those corrections supersede candidate-uniqueness promotion.

**Tech stack:** Python unittest, Streamlit, shared ES modules, Playwright, Eleventy.

## Constraints

- No procedure, tradition, source surface, historical answer or operation-sequence template in rule applicability.
- Every derived assertion is entailed by a registered rule from independent reviewed/derived/canonical premises. Compatibility, uniqueness and lexical coverage confer no authority.
- Quantity facets and Term expressions are different assertion targets. Missing expression coverage is unresolved, not contradiction.
- Keep reviewed assertions separate; conflicts retain both sides and block their dependent conclusions.
- Rebuild a finite deterministic fixed point from active decisions on each compile. No cycle self-support; no stale cache.
- Disposable ReviewJobs only for interaction benchmarks. Do not replace `static/data/inspector/sifen-38.snapshot.json` without explicit final-state approval.
- No browser inference, new dependencies, corpus data edits, commit or push. Preserve pre-existing `AGENTS.md` changes.

## Review focus

1. Exact occurrence consumed more than once: diagnostic instead of leaking a local review into a shared producer.
2. Late-discovered contradiction: invalidate already-derived descendants, including across aliases.
3. Kernel truncation/rejection/unknown metadata: never manufacture certainty or resurrect rejected meanings.
4. Recompile changes internal IDs: public references use existing Scholar objects and ports.
5. Static draft edits: published closure/provenance and question inventory remain immutable.

## Task 1 — pure closure and exact graph bridge

Files: new `adjudication/semantic_closure.py`, shared `analysis_parser/semantic_rules.py`, existing `analysis_parser/scoped.py`, `adjudication/compiler.py`, new `tests/adjudication/test_semantic_closure.py`.

- [x] Write and run failing synthetic tests for identity, ordinal conversion, renaming, same-shape incompatible metadata, candidate non-authority, ambiguity, conflict quarantine, cycles, retraction and exact-port isolation.
- [x] Implement `compute_semantic_closure(graph, effective, *, conflicted_decisions=())` returning `SemanticClosure/1` with `assertions`, `conflicts`, `unresolved`; each assertion has kind, target, facet/value, authority, rule and typed dependencies.
- [x] Seed only exact active review addresses and term slots. Propagate through load/alias; reuse ordinal transition; transfer an existing quantity expression through exact naming only.
- [x] Wire after final reviewed lowering; run pure tests and existing quantity tests. No semantic IR changes.

## Task 2 — questions and projection

Files: `workbench/question_presenter.py`, `workbench/annotation_projection.py`, new projection tests.

- [x] Failing tests: quantity-derived does not resolve lexical meaning; entailed expression does; rejection/conflict keeps a review question; replay/retraction restores questions.
- [x] Reconcile exact occurrence expressions independently of candidate generation. Add per-assertion projection with stable Scholar references and quantity port facts, without changing reviewed_claims or IDs.
- [x] Extend existing before/after diff with derived additions/removals and actual automatically resolved question count.
- [x] Run §38 golden and §15 invariant tests; baseline without decisions remains stable.

## Task 3 — shared Inspector presentation and static export

Files: `workbench/scholar_renderer.py`, `workbench/procedure_model.py`, `tools/parser_inspector/review_panel.py`, shared renderer modules, `src/js/scholar-sandbox.mjs`, `workbench/sandbox_snapshot.py` as needed.

- [x] Failing presentation tests: separate interpretation/quantity sections, authored labels, clickable dependencies, graph topology unchanged.
- [x] Render derived/reviewed/conflict in text; show provenance with Scholar/source links and technical evidence. Add computed change summary.
- [x] Carry the same compiled data into snapshot and public UI. Draft handlers do not change it.
- [x] Keep public snapshot bytes unchanged; exercise candidate export in temporary artifacts.

## Task 4 — integration and acceptance

- [x] Disposable §38 count review then Term review, inspect real consequences and missing generic relations; retract and reload.
- [x] Synthetic source with true identity-derived Term demonstrates disappearing meaning question and visible provenance.
- [x] Existing adjudication/service, renderer, Procedure Model and local Inspector regressions. Four legacy Workbench failures reproduced on HEAD and documented separately.
- [x] Production Eleventy build and ordinary static `/mathesis/` browser acceptance at 1440/768/390; screenshots of propagation and provenance. No backend requests/static inference.
- [x] Fresh final review, fix material findings, report evidence and honest partial benchmark result. No commit or push.

## Execution ledger

- Baseline verified: `42fe05fa95cbd2727e3eb732c741e2ceb502a4c7`; only tracked pre-existing modification is AGENTS.md.
- Existing ordinal positive/incomplete-input tests passed during audit. Existing lowering repeats reviewed metadata across values; closure must seed from active review addresses, never from the legacy reviewed_quantity flag alone.
- Ruling: work in the user's current local Inspector workspace, preserve unrelated files; do not create a separate checkout that would leave their local preview on the old implementation.
- Review fixes: supply replay-conflict evidence separately; quarantine per facet; preserve review-origin assertion identity; select a grounded primary proof. Independent reviewer verified the fixes.
- Ruling: snapshot regression uses freshly created disposable jobs rather than relying on a now-stale private presentation job. The real private job and tracked public snapshot remain byte-identical.
- Ruling: old adjacent alias test now expects deterministic interpretation inheritance, while asserting the second occurrence receives no human decision. Its rejection branch remains occurrence-local.
- Verification and exact changed-file manifest: `docs/semantic-closure-v0.md`. No new propagation rule depends on procedure vocabulary or corpus identity.
