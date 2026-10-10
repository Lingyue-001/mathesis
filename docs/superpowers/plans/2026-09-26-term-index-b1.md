# Term Index B1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the read-only Python `TermIndex/1` builder and deterministic JSON export from `ScholarSourceProjection/1` inputs.

**Architecture:** `workbench.term_index` is an independent consumer with a pure builder and explicit serializer/exporter. It groups exact Unicode forms while preserving full source-and-span occurrence identity, copies only Projection-exposed local semantic material, and computes composition ancestry only from recorded Projection links.

**Tech Stack:** Python standard library (`copy`, `json`, `pathlib`), existing `unittest` test suite, existing source Projection test helpers.

**Spec:** `docs/superpowers/specs/2026-09-26-term-index-b1-design.md`

## Global Constraints

- Consume `ScholarSourceProjection/1` only; do not import parser, compiler, Domain Kernel, review-store, or corpus code from `workbench.term_index`.
- Implement no Inspector/public/static UI integration, no semantic promotion or interpretation, and no K3/K4 work.
- `projection_source_identity` is `source_id + unit_id + doc_id + reading_id`; reject duplicates in one build. `text_sha256` is metadata only.
- `occurrence_identity` is the source identity plus Unicode `[start,end)`; exact Unicode `surface` is grouping/display only.
- Preserve `maximal` and `component` occurrences; derive entry-level `both` only from their aggregate presence.
- Derive direct parents and transitive compound ancestors only through recorded `children` and `composition_alternatives`; no string-based inference.
- Copy Projection-exposed occurrence-local status/semantic fields exactly; never create entry-level epistemic status or a confidence score.
- Builder is pure; only explicit export writes a caller-selected file. Do not modify corpus/source data, parser/compiler/Kernel semantics, review records, NOTE, or LOG files.
- Work in the existing user-authorized workspace; do not create a worktree, commit, or push.

## Review Focus

1. Duplicate contextual snapshots of one source must fail at source-identity admission, not be silently de-duplicated; covered by Task 2.
2. The same exact surface in distinct sources/spans must remain distinct occurrences while one exact-form entry groups them; covered by Task 1.
3. Nested components must include all recorded outer ancestors, but never acquire links from surface containment; covered by Task 2.
4. Candidate statuses, Kernel axes, claims, assertions, and decision references must be copied per occurrence without an entry-level synthesis; covered by Task 3.
5. The fixed §38/§39 matrix must exercise two legal cross-source builds and the contextual-snapshot rejection without becoming full-corpus/K4 evaluation; covered by Task 4.

---

### Task 1: Define exact-form entries and occurrence records

**Files:**
- Create: `tests/workbench/test_term_index.py`
- Create: `workbench/term_index.py`

**Interfaces:**
- Consumes: iterable of `ScholarSourceProjection/1` mappings.
- Produces: `build_term_index(projections) -> dict` with `schema`, `sources`, and exact-surface `entries`.

- [x] **Step 1: Write failing synthetic tests for schema admission, exact-form grouping, full distinct occurrences, roles/counts, stable ordering, and input immutability.**

Use minimal two-source Projection fixtures with repeated exact surface and one different surface. Assert one exact-form entry retains two full identities, only its two roles determine `both`, and the input deep copy remains equal.

- [x] **Step 2: Run the new test module and verify the intended missing-module/API failure.**

Run: `tools/parser_inspector/.venv/Scripts/python.exe -X utf8 -B -m unittest tests.workbench.test_term_index -q`

Expected: FAIL because `workbench.term_index` / `build_term_index` does not yet exist.

- [x] **Step 3: Implement the smallest pure `build_term_index(projections)` in `workbench/term_index.py`.**

Validate `ScholarSourceProjection/1`, collect required source and anchor identity fields, deep-copy admitted term-local records, group only exact `surface`, derive `maximal`/`component` counts and entry-level `both`, and sort deterministically. Do not add composition or export behavior yet.

- [x] **Step 4: Run the new module and the existing Projection regression.**

Run: `tools/parser_inspector/.venv/Scripts/python.exe -X utf8 -B -m unittest tests.workbench.test_term_index tests.workbench.test_scholar_source_projection -q`

Expected: PASS.

### Task 2: Enforce source identity and recorded composition ancestry

**Files:**
- Modify: `tests/workbench/test_term_index.py`
- Modify: `workbench/term_index.py`

**Interfaces:**
- Consumes: Task 1 occurrence records and each projected Term's `children` / `composition_alternatives`.
- Produces: `direct_parent_occurrences`, `compound_ancestor_occurrences`, and `counts.appears_in_compounds`; `ValueError` for duplicate source identity or unresolved recorded child IDs.

- [x] **Step 1: Write failing tests for immediate-parent de-duplication, nested recorded ancestry, absence of substring-derived links, duplicate projection-source rejection, and unknown child-ID rejection.**

Use a synthetic `入蔀積月 -> 積月 -> 月` chain with repeated alternatives. Assert `月` has `積月` as a direct parent, both `積月` and `入蔀積月` as ancestors, and `appears_in_compounds == 2`. Add an adjacent/same-surface term without a recorded link and assert it is absent.

- [x] **Step 2: Run the new composition/identity tests and verify they fail for unimplemented behavior.**

Run: `tools/parser_inspector/.venv/Scripts/python.exe -X utf8 -B -m unittest tests.workbench.test_term_index -q`

Expected: FAIL on the new direct/ancestor identity assertions.

- [x] **Step 3: Extend `build_term_index` with recorded-link resolution and transitive parent closure.**

Resolve child Projection Term IDs only within their owning Projection, union `children` with every `composition_alternatives` list, and walk only those child-to-parent edges. Reject duplicate `source_id/unit_id/doc_id/reading_id` before collection; reject an unresolved linked child rather than inferring it.

- [x] **Step 4: Run the focused module and existing component/composition Projection tests.**

Run: `tools/parser_inspector/.venv/Scripts/python.exe -X utf8 -B -m unittest tests.workbench.test_term_index tests.workbench.test_scholar_source_projection -q`

Expected: PASS.

### Task 3: Preserve local semantic material and export deterministically

**Files:**
- Modify: `tests/workbench/test_term_index.py`
- Modify: `workbench/term_index.py`

**Interfaces:**
- Consumes: completed `TermIndex/1` dictionaries.
- Produces: `serialize_term_index(index) -> str` and `export_term_index(index, path) -> Path`.

- [x] **Step 1: Write failing tests that one occurrence retains copied Projection candidates/status axes, reviewed claims, semantic/derived assertions, decision references, and review facets without changing a same-surface peer.**

Also assert serialization is readable/stable, export round-trips in `TemporaryDirectory`, and invalid `TermIndex/1` input is rejected by serializer/exporter.

- [x] **Step 2: Run the module and verify the semantic-preservation/export assertions fail.**

Run: `tools/parser_inspector/.venv/Scripts/python.exe -X utf8 -B -m unittest tests.workbench.test_term_index -q`

Expected: FAIL because semantic copy fields and serializer/exporter are absent.

- [x] **Step 3: Implement only Projection-field copying plus deterministic serializer/exporter.**

Deep-copy the specified existing Term fields verbatim into each occurrence. Use `json.dumps(..., ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)` plus a final newline; exporter writes only the given `Path` with UTF-8/newline normalization.

- [x] **Step 4: Run focused B1 and existing semantic-closure tests.**

Run: `tools/parser_inspector/.venv/Scripts/python.exe -X utf8 -B -m unittest tests.workbench.test_term_index tests.workbench.test_semantic_closure -q`

Expected: PASS.

### Task 4: Fix the real-projection regression matrix and audit boundary

**Files:**
- Modify: `tests/workbench/test_term_index.py`

**Interfaces:**
- Consumes: existing test/projection paths for §38 no-context, §38 + §15 context, and §39.
- Produces: B1 regression coverage without any corpus scan, UI integration, or source write.

- [x] **Step 1: Write integration tests for the three fixed matrix cases.**

Build Case A from `[§38 no-context, §39]` and Case B from `[§38 + §15 context, §39]`; assert source identities, aggregate behavior, and per-occurrence semantic data remain explicit. Build the negative pair `[§38 no-context, §38 + §15 context]` and assert duplicate projection-source rejection.

- [x] **Step 2: Run the integration tests after wiring the real fixture matrix.**

Run: `tools/parser_inspector/.venv/Scripts/python.exe -X utf8 -B -m unittest tests.workbench.test_term_index.TermIndexIntegrationTests -q`

Expected: PASS; this is a regression-only task. The underlying builder behavior was already established through Task 1--3 RED→GREEN tests.

- [x] **Step 3: Wire the tests through existing projection helpers only.**

Generate the three snapshots by existing test/projection paths. Do not persist them, scan unrelated corpus units, or change packet, compilation, review, source, or semantic code.

- [x] **Step 4: Run B1, preflight-relevant, and full-suite verification; audit the diff.**

Run: `tools/parser_inspector/.venv/Scripts/python.exe -X utf8 -B -m unittest tests.workbench.test_term_index tests.workbench.test_scholar_source_projection tests.workbench.test_semantic_closure tests.domain_kernel.test_engine tests.adjudication.test_term_claims -q`

Expected: PASS.

Run: `tools/parser_inspector/.venv/Scripts/python.exe -X utf8 -B -m unittest discover -s tests -q`

Expected: record all outcomes; do not repair known unrelated baseline failures outside B1 scope.

Run: `git diff --check` and `git diff --name-only`

Expected: no parser/compiler/Kernel/corpus/UI path changes; only B1 module/tests/spec/plan/contract changes plus pre-existing user changes.

## Self-Review

- Spec coverage: Tasks 1--4 implement the pure builder, identity boundary, recorded ancestry, local semantic preservation, deterministic export, and the fixed real-projection matrix.
- Step scan: every implementation increment begins with a specific failing test and ends with a named verification command.
- Type consistency: all tasks use the same `build_term_index`, `serialize_term_index`, and `export_term_index` interfaces; entries carry the exact names defined by the design.
- Review focus: each identity, grouping, ancestry, semantic-locality, and real-matrix risk has a focused test in its owning task.
- Proportion: B1 adds one consumer module and one test module only; no UI, parser, compiler, Kernel, or corpus work is authorized.

### Task 5: Apply independent-review corrections

**Files:**
- Modify: `workbench/term_index.py`
- Modify: `tests/workbench/test_term_index.py`
- Modify: `docs/term-index-v1-contract.md`
- Modify: `docs/superpowers/specs/2026-09-26-term-index-b1-design.md`

**Interfaces:**
- Consumes: independent review of B1 against the approved contract.
- Produces: complete occurrence-local Projection preservation and stable invalid-input failures.

- [x] **Step 1: Add RED coverage for Projection `semantic_conflicts` and `evidence` preservation.**

- [x] **Step 2: Deep-copy those two existing occurrence-local Projection fields and verify synthetic plus real matrix coverage.**

- [x] **Step 3: Add RED coverage for non-list Terms and invalid Unicode/source anchors.**

- [x] **Step 4: Validate these inputs with explicit `ValueError` and run the complete B1 module.**

- [x] **Step 5: Align contract/spec implementation status and copied-field/validation descriptions.**
