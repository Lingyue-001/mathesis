# Term Index Inspector Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a read-only, corpus-level `Term Index` view to the local Inspector without changing the `TermIndex/1` contract or semantic producers.

**Architecture:** The top-level Inspector branches to Term Index before source selection or any ReviewJob flow. Its controller-bound baseline collector reads registered current-effective corpus units and generates in-memory `ScholarSourceProjection/1` values before one B1 build. A standalone component consumes only `TermIndex/1`; the shell records navigation targets but never implicitly opens a source or creates a ReviewJob.

**Tech Stack:** Python standard library and existing unittest/AppTest harness; Streamlit components v2; existing local ES modules/CSS; B1 `workbench.term_index`.

**Spec:** `docs/superpowers/specs/2026-09-26-term-index-inspector-design.md`

## Global Constraints

- Keep `workbench.term_index` as a pure `ScholarSourceProjection/1` consumer; do not change `TermIndex/1`.
- Corpus collection is baseline-only: do not select, merge, or create saved ReviewJobs or review branches.
- Use every registered current-effective corpus unit that can project; source selection only affects Annotated Source, never Index scope.
- Cache only in Inspector session state. Its key must derive from actual included effective unit identities and their effective/source freshness/version fingerprints plus the direct analysis/Kernel/Projection/TermIndex producer identity.
- Component input is `TermIndex/1` only; it cannot read Projection, corpus, ReviewJob, Annotated Source, or review state.
- Preserve exact-form/no-normalization, occurrence-local status/evidence, and recorded-only composition semantics from B1.
- Foreign occurrence navigation must never implicitly switch source or create a job; no public/static page, exports, K3/K4, or semantic/corpus/review writes.
- Work in the existing user-authorized workspace; do not create a worktree, commit, or push.

## Review Focus

1. A cache keyed only by source selection, corpus state, or an arbitrary timestamp would retain a stale corpus index after producer changes; Task 1 pins corpus and producer identities.
2. Multiple saved jobs/branches must never become a corpus reviewed-state policy by accident; Task 1 proves the collector has no ReviewJob calls or writes.
3. Component-only forms must stay browseable under every default/list filter; Task 2 pins All/Maximal/Component/Both behavior.
4. A component must not reach behind `TermIndex/1` for source/review data; Task 2 pins its data contract and static imports.
5. Opening Term Index or clicking an occurrence must not make Inspector select a source, resolve, or create a ReviewJob; Task 3 pins this independent branch.

---

### Task 1: Build the read-only baseline corpus Index collector

**Files:**
- Create: `workbench/term_index_corpus.py`
- Create: `tests/workbench/test_term_index_corpus.py`

**Interfaces:**
- Consumes: registered source list plus current non-stale `corpus_review` effective unit state.
- Produces: `collect_baseline_term_index(root) -> dict` with `index: TermIndex/1`, `fingerprint`, `included`, and `unavailable`; no persistence.

- [x] **Step 1: Write failing tests for current-effective source admission, deterministic included-unit fingerprinting, duplicate Projection-source rejection before B1 ingestion, unavailable-source reporting, admitted-unit fail-closed projection errors, and no filesystem/review-job mutation.**

Use temporary registered effective fixtures or controlled existing adapter seams. Assert changing one included unit/freshness value changes the fingerprint, while an unrelated Inspector selection value cannot affect it.

- [x] **Step 2: Run the collector tests and verify missing-module/API failure.**

Run: `tools/parser_inspector/.venv/Scripts/python.exe -X utf8 -B -m unittest tests.workbench.test_term_index_corpus -q`

Expected: FAIL because `workbench.term_index_corpus` is absent.

- [x] **Step 3: Implement the minimal collector.**

Read only current effective corpus-review workspaces, construct one source packet per effective unit, use a fresh in-memory session and existing Projection path, validate unique Projection source identity, then call `build_term_index` once. Produce a deterministic fingerprint over actual included unit identity plus effective/source version fields and the direct analysis/Kernel/Projection/TermIndex producer identity; never call ReviewJob resolver/create/write functions.

- [x] **Step 4: Run collector plus B1 tests.**

Run: `tools/parser_inspector/.venv/Scripts/python.exe -X utf8 -B -m unittest tests.workbench.test_term_index_corpus tests.workbench.test_term_index -q`

Expected: PASS.

### Task 2: Add the TermIndex-only local component

**Files:**
- Modify: `tools/parser_inspector/source_annotation.py`
- Create: `tools/parser_inspector/term_index.mjs`
- Create: `tools/parser_inspector/term_index.css`
- Create: `tests/workbench/term-index-component.test.mjs`

**Interfaces:**
- Consumes: `term_index_component(index, *, key)` where `index['schema'] == 'TermIndex/1'`.
- Produces: local render state and a navigation event containing only `identity`, `source_anchor`, and nonce.

- [x] **Step 1: Write failing Node tests for exact Unicode query, `All`/`Maximal`/`Component`/`Both` filters, component-only entry retention, deterministic entry selection, complete entry details, invalid-schema rejection, and navigation payload isolation.**

Use a synthetic multi-source `TermIndex/1`; assert no test input includes a Projection or review object.

- [x] **Step 2: Run the Node test and verify the missing module/export failure.**

Run: `node --test tests/workbench/term-index-component.test.mjs`

Expected: FAIL because the component module/helper is absent.

- [x] **Step 3: Implement the component and its Python wrapper.**

Reuse the existing component asset loader. The wrapper accepts a complete `TermIndex/1`, rejects another schema, and passes no raw source/review state. Render an accessible master/detail list with search, the four filters, counts, parent/ancestor evidence, and occurrence-local fields. Emit only the selected occurrence identity and copied anchor.

- [x] **Step 4: Run Node component tests and existing component-layout tests.**

Run: `node --test tests/workbench/term-index-component.test.mjs tests/workbench/scholar-renderer-layout.test.mjs`

Expected: PASS.

### Task 3: Wire the third Inspector view and safe navigation

**Files:**
- Modify: `tools/parser_inspector/review_panel.py`
- Modify: `tools/parser_inspector/test_review_panel.py`

**Interfaces:**
- Consumes: Task 1 structured collection and Task 2 component navigation event.
- Produces: `Term Index` selector branch, session-only cache refresh/rebuild, and a read-only occurrence navigation target.

- [x] **Step 1: Write failing AppTest/unit tests for the third selector option, corpus collector independence from current source selection, cache invalidation on effective fingerprint change, explicit refresh, and target-only no-write navigation.**

Snapshot ReviewJob/corpus-review bytes around the interaction; use an injected collector fixture to avoid a full corpus compile in ordinary AppTest.

- [x] **Step 2: Run those tests and verify missing selector/cache/navigation behavior fails.**

Run: `tools/parser_inspector/.venv/Scripts/python.exe -X utf8 -B -m unittest tools.parser_inspector.test_review_panel -q`

Expected: FAIL on `Term Index` selector and navigation assertions.

- [x] **Step 3: Add only the controller/shell branch.**

Branch from the top-level Inspector selector to `Term Index` before source selection, ReviewJob resolution, compilation, session controls, or the 7:3 source layout. Obtain the baseline collection through session cache keyed by corpus plus producer fingerprint. Render unavailable/error metadata explicitly. Consume component events once by nonce by storing/rendering the navigation target only; do not invoke source selection, ReviewJob resolution, or review writes.

- [x] **Step 4: Run Inspector AppTest and focused collector/component suites.**

Run: `tools/parser_inspector/.venv/Scripts/python.exe -X utf8 -B -m unittest tools.parser_inspector.test_review_panel tests.workbench.test_term_index_corpus tests.workbench.test_term_index -q`

Expected: PASS.

### Task 4: Prove corpus-level integration and preserve deferred boundaries

**Files:**
- Modify: `tests/workbench/test_term_index_corpus.py`
- Modify: `tools/parser_inspector/test_review_panel.py`

**Interfaces:**
- Consumes: real current-effective registered corpus state and the complete local UI wiring.
- Produces: regression evidence for baseline corpus scope, cache invalidation, and no semantics/review/static expansion.

- [x] **Step 1: Write real-corpus integration coverage.**

Assert the collector's input list equals the available current-effective units, is independent of focus selection, produces a multi-Projection `TermIndex/1`, and labels it baseline. Assert no saved reviewed state is selected or merged.

- [x] **Step 2: Run the real-corpus integration test against the existing collector wiring.**

Run: `tools/parser_inspector/.venv/Scripts/python.exe -X utf8 -B -m unittest tests.workbench.test_term_index_corpus -q`

Expected: FAIL until the integration assertions are wired to the real collector.

- [x] **Step 3: Wire existing current-effective fixtures/paths only.**

Do not generate source/corpus data, persist Index JSON, create ReviewJobs, or extend into reviewed-state selection.

- [x] **Step 4: Run final verification and audit scope.**

Run: `tools/parser_inspector/.venv/Scripts/python.exe -X utf8 -B -m unittest tests.workbench.test_term_index tests.workbench.test_term_index_corpus tests.workbench.test_scholar_source_projection tests.workbench.test_semantic_closure tools.parser_inspector.test_review_panel -q`

Expected: PASS.

Run: `node --test tests/workbench/term-index-component.test.mjs tests/workbench/scholar-renderer-layout.test.mjs`

Expected: PASS.

Run: `tools/parser_inspector/.venv/Scripts/python.exe -X utf8 -B -m unittest discover -s tests -q`

Expected: record known unrelated baseline outcomes without repairing them in this stage.

Run: `git diff --check` and `git status --short`

Expected: no changes to parser/compiler/Kernel/corpus/review semantics, no public/static artifacts, and no `TermIndex/1` contract change.

## Self-Review

- Spec coverage: Tasks 1--4 cover baseline corpus collection, effective-unit cache invalidation, a TermIndex-only component, third local view, safe navigation, and all acceptance criteria.
- Step scan: every behavior addition begins with a named failing test and ends with an explicit focused verification.
- Type consistency: Task 1 produces `index/fingerprint/included/unavailable`; Task 2 consumes `TermIndex/1`; Task 3 only joins those interfaces through the Inspector shell.
- Review focus: stale cache, accidental reviewed-state selection, component-only filtering, raw-input leakage, and foreign-navigation writes each have a named owning task.
- Proportion: this plan creates one collector and one component pair; it does not add a static site, a new semantic path, or a reviewed-state policy.
