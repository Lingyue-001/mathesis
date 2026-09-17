# M3 Procedure Workbench Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a same-origin, in-site research workbench that exposes reviewed procedural analysis, real review decisions, replay, and persistence without altering Pattern Lab or the production parser.

**Architecture:** Extend the existing `workbench` orchestration API so that it drives `AdjudicationSession` and `compile_reviewed` and returns a deliberately read-only researcher projection. Extend the existing Workbench controller and stateless view helpers; browser state stores a versioned session document and always recompiles through the API. Add the smallest local-lexical-role decision contract to the existing adjudication decision/replay/compiler path, scoped to one anchor and branch.

**Tech Stack:** Python standard-library HTTP server, existing Python parser/adjudication packages, Eleventy static site, browser ES modules, Playwright, unittest.

**Spec:** `docs/adjudication/requirements.md` and the user's M3 specification of 2026-09-17.

## Global Constraints

- Preserve SourcePacket 3.x; AdjudicationSession and ReviewedProcedureBundle remain separately versioned.
- `analysis_parser/` must not depend on evaluation, review output, checkpoint, UI, or history.
- Do not change Pattern Lab state, its six-axis score, or its user behavior.
- Never patch the final graph in the browser; decisions are appended then compiled by `compile_reviewed`.
- Use actual returned analysis products for system-stage records; do not synthesize timed progress or confidence.
- Keep numeric execution auxiliary and do not add M4 primitive families.
- Persist only local session state; corpus remains read-only and API payloads stay loopback/same-origin constrained.

---

### Task 1: M3-A reviewed orchestration and researcher projection

**Files:**
- Modify: `workbench/service.py`, `workbench/projection.py`, `workbench/api.py`
- Modify: `config/workbench-procedures.json`
- Test: `tests/workbench/test_adjudication_workflow.py`

**Interfaces:**
- Produces `open_adjudication(root, procedure_id, session=None, branch_id='main') -> dict`.
- Produces `compile_adjudication(root, procedure_id, session, branch_id='main') -> dict`.
- Both responses contain `source`, `session`, `bundle`, `projection`, and real `stages`.

- [ ] Write failing tests for two registered corpus procedures, reviewed compile output, stage records, source-layer coverage, and HTTP request validation.
- [ ] Implement the two narrow service functions using `new_session`, `compile_reviewed`, `make_bundle`, and `project_graph`; retain existing analysis/execute endpoints.
- [ ] Add safe same-origin API endpoints for opening and recompiling an adjudication session.
- [ ] Extend the projection from IR and reviewed bundle relations only: L0–L3 layers, evidence sources, object/source links, coverage, review queue, trace, and graph/comparison status.
- [ ] Register one additional actual corpus procedure with exact checked source/context hashes, using the same adapter and renderer.
- [ ] Run the focused tests, then all existing workbench and adjudication tests.

### Task 2: M3-B local textual correction and actual review actions

**Files:**
- Modify: `adjudication/session.py`, `adjudication/replay.py`, `adjudication/compiler.py`
- Modify: `workbench/service.py`, `workbench/api.py`
- Test: `tests/adjudication/test_m3_local_revision.py`, `tests/workbench/test_adjudication_workflow.py`

**Interfaces:**
- Adds `set_lexical_role` to `AdjudicationSession 1.1` action contracts.
- The action requires one stable source anchor, a finite local grammatical role, evidence, and remains local to a branch.
- Replaying exposes `effective['lexical_roles']`; reviewed compilation preserves it as syntax evidence without equating it to a graph operation or global lexicon rule.

- [ ] Write counterexample tests proving repeated text at another anchor is unchanged, resegmentation stales a prior local role, and a local function-word annotation does not falsely classify its whole sentence as noncomputational.
- [ ] Implement the minimal versioned validation/replay/compiler evidence overlay in existing adjudication modules.
- [ ] Add service/API action append, branch creation, retract, and recompute paths that call `append_decision`, `create_branch`, and `compile_reviewed` only.
- [ ] Test conflicting decisions, invalid anchors/ports, extension holes, stale dependencies, and deterministic branch replay.

### Task 3: M3 UI linked evidence and processing records

**Files:**
- Modify: `src/adjudication.md`, `src/js/procedure-workbench.js`, `src/js/ui/procedure-view.js`, `src/js/ui/source-links.js`, `src/css/workbench.css`
- Create: `src/js/ui/adjudication-session-store.js`
- Test: `tests/workbench/adjudication-browser.mjs`

**Interfaces:**
- `adjudication-session-store.js` owns versioned local session save/load/export/import only; it owns neither compiler nor page rendering.
- `procedure-workbench.js` owns page state and request sequencing; view modules remain stateless renderers.

- [ ] Write a failing browser test for two procedures, L0–L3 switching, source/structure/graph/question localization, and real stage records.
- [ ] Render the distinct system-processing flow and text-internal procedure hierarchy from returned stage/projection data.
- [ ] Render layered source annotations that preserve code-point offsets, multiline and combining/astral characters, repeated text, multi-span references, and multi-event spans.
- [ ] Render candidate/evidence/review detail and review controls; display semantic names and evidence, never only runtime IDs.
- [ ] Keep raw JSON in a disclosure and numerical execution collapsed auxiliary.
- [ ] Reuse existing site layout/research CSS and do not import `patterns.js`.

### Task 4: M3-C persistence, branches, export, and browser acceptance

**Files:**
- Modify: files from Tasks 1 and 3
- Test: `tests/workbench/adjudication-browser.mjs`, `tests/workbench/test_adjudication_workflow.py`
- Create: `docs/adjudication/m3-evidence.md`
- Modify: `docs/adjudication/requirements.md`, `docs/architecture.md`

- [ ] Write failing browser tests for a real binding/resegmentation/manual construction or local-role decision, retract restoration, branch comparison, stale response protection, close/reopen persistence, and export/import.
- [ ] Implement atomic local session write, import validation via the API, undo/retract, redo by a fresh decision, branch switching, export/import, and rule-proposal export records.
- [ ] Show review, graph, execution, and comparison as separate statuses; mark comparison unavailable where M4 evidence does not exist.
- [ ] Run browser tests against the actual loopback workbench, focused unit tests, legacy workbench tests, adjudication tests, old parser/rescue regression suites, engineering checks, and `npm.cmd run build`.
- [ ] Record exact test evidence and remaining M4 limitations in requirements/architecture/M3 evidence; update ignored NOTE/LOG immediately before the local milestone commit.
- [ ] Commit the complete M3 change locally only using the repository convention; start the loopback service and provide the URL and operator steps for human review.

## Self-review

- M3-A maps source/projection/stage visibility and two actual procedures to Task 1.
- M3-B maps all adjudication actions, objection/local grammar correction, branch and stale semantics to Task 2.
- M3-C maps UI linked navigation, persistence, export/import, security boundaries, Unicode coordinate browser checks, and browser acceptance to Tasks 3–4.
- M4 primitive expansion, dual graph comparison, scholar workload study, rule learning, and deployment remain out of scope.
