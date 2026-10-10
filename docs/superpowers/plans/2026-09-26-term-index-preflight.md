# Term Index Preflight Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Freeze the K2 baseline and the read-only `ScholarSourceProjection/1` contract that Term Index v1 will consume, without implementing an index or changing semantics.

**Architecture:** The preflight has three artifacts: a reproducible baseline record, a reconciled Domain Kernel consumer ledger, and a Term Index contract. The contract admits all existing Projection Term spans, preserves each exact occurrence and its composition links, and makes no parser, Kernel, compiler, review-store, or corpus write.

**Tech Stack:** Existing Python unittest suites, `domain_kernel.docs` generated reference documentation, Markdown and JSON only.

**Spec:** User-approved Stage A / Term Index v1 requirements (conversation, 2026-09-25--26); the durable specification produced by Task 1 is `docs/term-index-v1-contract.md`.

## Global Constraints

- Do not modify `analysis_parser/`, `adjudication/compiler.py`, `domain_kernel/engine.py`, corpus/source data, human review records, or parser recognition results.
- Protect the current `ScholarSourceProjection/1` behavior with exact §38, §38 + §15, and §39 projection evidence plus the existing Domain Kernel, term-claim, and semantic-closure tests.
- Term Index v1 consumes `ScholarSourceProjection/1` only; R1--R4 are inspection/evidence, never a canonical source.
- Index every admitted Projection Term span. Preserve `maximal`, `component`, and per-entry `both` occurrence classifications separately; never infer an occurrence or composition relation from matching surface strings.
- Define `appears_in_compounds` as the number of distinct parent Term occurrences whose recorded `children` or `composition_alternatives` contain the entry's occurrence; deduplicate multiple alternatives within one parent and never infer membership by substring or string containment.
- Identity is `source_id + unit_id + doc_id + reading_id + Unicode [start,end)`; `surface` is display and exact-form grouping only.
- No normalization, lemma, cross-occurrence meaning promotion, candidate ranking, confidence score, writeback, or automatic Kernel/parser promotion.
- Update the generated `docs/domain-kernel/SCHEMA_REFERENCE.md` whenever its manifest input changes.
- Do not update local NOTE/LOG files unless the user separately requests it or approves a commit/push.

## Review Focus

1. A repeated surface in two documents/readings must remain two occurrences even when its form-group key is identical; pin this contract rule to the baseline projection evidence.
2. A nested span must count as `component` in one occurrence and `maximal` in another, yielding `both` only at the entry aggregate; pin this to existing component/maximal projection tests.
3. Compound membership must follow Projection `children`/`composition_alternatives`, so adjacent or identical strings cannot fabricate a compound relation; pin this to the canonical-link tests.
4. Candidate-level status and Kernel axes must stay occurrence-local; pin this to the one-term-decision isolation test.
5. Changing the consumer ledger must regenerate, not hand-edit, `SCHEMA_REFERENCE.md`; pin this to `domain_kernel.docs --check` and its manifest validation tests.

---

### Task 1: Capture the immutable A0 baseline and author the Term Index v1 contract

**Files:**
- Create: `docs/term-index-v1-contract.md`
- Create (ignored audit evidence): `.cache/term-index-preflight/2026-09-26-baseline.json`
- Create (ignored audit evidence): `.cache/term-index-preflight/proc38.no-context.json`, `.cache/term-index-preflight/proc38.with-section15.json`, `.cache/term-index-preflight/proc39.json`

**Interfaces:**
- Consumes: `workbench.annotation_projection.project_scholar_source()` output whose schema is `ScholarSourceProjection/1`.
- Produces: a read-only ingestion contract for future Term Index code, including exact occurrence identity, all-span admission, `maximal`/`component`/entry-level `both` accounting, exact-form grouping, occurrence-local candidates/statuses/facts, and composition-only compound membership.

- [x] **Step 1: Run the existing projection, Domain Kernel, term-claim, and semantic-closure tests before writing any behavior artifact.**

Run: `tools/parser_inspector/.venv/Scripts/python.exe -X utf8 -B -m unittest tests.workbench.test_scholar_source_projection tests.domain_kernel.test_engine tests.domain_kernel.test_docs tests.adjudication.test_term_claims tests.workbench.test_semantic_closure -q`

Expected: all selected tests pass; a failure stops the preflight and is reported rather than repaired in this stage.

- [x] **Step 2: Generate the three named current Projection records through existing test/projection paths and record the current main commit, working HEAD, protected-file SHA-256s, and test command/result.**

Record the `main` commit separately from `HEAD`; enumerate and hash files under `analysis_parser/`, `domain_kernel/`, `adjudication/`, plus `workbench/annotation_projection.py` and `workbench/semantic_projection.py`. The evidence is audit-only and must not become a new golden standard.

- [x] **Step 3: Write `docs/term-index-v1-contract.md`.**

Define only the future consumer boundary: canonical input, rejected raw inputs, source/occurrence identity, all-admitted-span ingestion, occurrence classification, exact-form entries, three separate aggregate counts (`maximal`, `component`, `appears_in_compounds`), source-derived composition membership, occurrence-local meanings/statuses/facts, read-only direction, and explicit out-of-scope list. Define `appears_in_compounds` as distinct parent Term occurrences, deduplicating alternatives within each parent; state that an entry-level `both` label is derived from the presence of both occurrence roles, not an occurrence role itself.

- [x] **Step 4: Verify contract claims against existing tests and the audit records.**

Run: `tools/parser_inspector/.venv/Scripts/python.exe -X utf8 -B -m unittest tests.workbench.test_scholar_source_projection tests.workbench.test_semantic_closure -q`

Expected: PASS; the recorded §38/§15/§39 outputs identify only current behavior and do not modify fixtures.

### Task 2: Reconcile the Domain Kernel capability ledger and generated reference

**Files:**
- Modify: `domain_kernel/consumer-manifest.json`
- Modify (generated): `docs/domain-kernel/SCHEMA_REFERENCE.md`

**Interfaces:**
- Consumes: actual K2 producers/validators/consumers and existing named effect tests.
- Produces: `DomainKernelConsumers/1` rows with concrete, validated references and non-contradictory status descriptions.

- [x] **Step 1: Verify the ledger's current stale state.**

Run: `tools/parser_inspector/.venv/Scripts/python.exe -X utf8 -B -m domain_kernel.docs --check`

Expected: PASS before edits; the pre-edit manifest still records the three outdated `planned` rows, proving the task is reconciliation rather than behavior repair.

- [x] **Step 2: Update only the three proven K2 rows.**

Set `term_candidate_selection` to `implemented`, with `workbench/question_presenter.py::build_questions` as producer, `adjudication/term_claims.py::revalidate_term_interpretation` as validator, `adjudication/compiler.py::compile_reviewed` as consumer, and exact term-claim effect tests. Set `input_count_coordinates` to `implemented`, with `build_questions`, `adjudication/quantity_targets.py::validate_quantity_facets`, `compile_reviewed`, and exact quantity-target effect tests. Set `automatic_resume` to `implemented` only in its narrow existing sense: saved reviewed decisions are replayed/recompiled through the existing job/session path; use `workbench/service.py::apply_review_job_changes`, `adjudication/replay.py::replay_session`, `compile_reviewed`, and job replay/restart tests. Do not alter `reading_selection` or `unified_authorization_gate`.

- [x] **Step 3: Regenerate `SCHEMA_REFERENCE.md` through the existing generator.**

Run: `tools/parser_inspector/.venv/Scripts/python.exe -X utf8 -B -m domain_kernel.docs`

Expected: only the generated reference file changes to mirror the manifest; no manual edit of generated content.

- [x] **Step 4: Prove ledger integrity and generation consistency.**

Run: `tools/parser_inspector/.venv/Scripts/python.exe -X utf8 -B -m unittest tests.domain_kernel.test_docs tests.adjudication.test_term_claims tests.adjudication.test_quantity_targets tests.workbench.test_review_jobs -q`

Expected: PASS, followed by `tools/parser_inspector/.venv/Scripts/python.exe -X utf8 -B -m domain_kernel.docs --check` with exit code 0.

### Task 3: Add K2 current-status notes and record the Gate A result

**Files:**
- Modify: `docs/domain-kernel/INTEGRATION.md`
- Modify: `docs/k2bc-acceptance.md`
- Modify: `docs/term-index-v1-contract.md`

**Interfaces:**
- Consumes: Task 1 baseline evidence and contract; Task 2 reconciled consumer ledger.
- Produces: one unambiguous stage account: implemented K2 capabilities, retained K3/K4 work, and Gate A pass/fail evidence.

- [x] **Step 1: Add only current-status/supersession notes that resolve contradictions with the K2 acceptance record.**

Do not rewrite, delete, or alter historical acceptance prose. In `INTEGRATION.md`, add a concise current-status/supersession note that identifies implemented K2 local term selection, coordinate interpretation, and reviewed replay/recompilation; retain `reading_selection` and unified authorization as unfinished/K3; retain global hardcode cleanup as K3 and unseen-corpus evaluation as K4. In `k2bc-acceptance.md`, add a dated `2026-09-26` preflight addendum only.

- [x] **Step 2: Add the Term Index preflight boundary to both K2-facing documents.**

Link the contract, state that `ScholarSourceProjection/1` is its sole canonical input, and list prohibited raw sources and the Term Index read-only rule. Do not describe a Term Index aggregator, UI, schema, or promotion workflow as implemented.

- [x] **Step 3: Add the Gate A checklist and its evidence to `docs/term-index-v1-contract.md`.**

The checklist must cover ledger consistency, explicit remaining items, canonical input, full occurrence identity, all-span/maximal-component accounting, no semantic projection change, no semantic-code edits, and the actual command outputs recorded by Task 1--2. A failed test leaves the gate failed and stops before Term Index code.

- [x] **Step 4: Run the complete Stage A verification set and audit the diff scope.**

Run: `tools/parser_inspector/.venv/Scripts/python.exe -X utf8 -B -m unittest tests.workbench.test_scholar_source_projection tests.domain_kernel.test_engine tests.domain_kernel.test_docs tests.adjudication.test_term_claims tests.workbench.test_semantic_closure -q`

Expected: PASS. Then run `git diff --check` and `git diff --name-only`; expected semantic implementation paths are absent, and corpus/source files are absent.

- [x] **Step 5: Commit only if separately authorized.**

Do not commit, push, update NOTE/LOG, or begin Term Index implementation as part of this plan.

## Self-Review

- Spec coverage: Tasks 1--3 cover A0--A4 and all seven Gate A conditions; no Term Index implementation task exists.
- Step scan: each test/generation/document action has one named outcome; no task authorizes semantic code or corpus changes.
- Type consistency: the sole data interface is `ScholarSourceProjection/1`; Task 3 only consumes Task 1 evidence and Task 2 ledger output.
- Review focus: each listed identity, role, composition, status, and generated-document risk maps to a named existing test or check.
- Proportion: the plan specifies documentation and verification work without designing the future aggregator.
