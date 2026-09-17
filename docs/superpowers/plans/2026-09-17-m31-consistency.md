# M3.1 Consistency Repair Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` task by task, with each behavior first captured as a failing test.

**Goal:** Derive every reviewed interpretation from one current syntax snapshot, so decisions, program/context, graph, validation and projection agree.

**Architecture:** Retain the current parser and executor. Centralize decision payload/semantic-target identity; then make reviewed syntax the shared compiler input, finalize quantity semantics at emission, and derive validation consumers from one report. The Workbench remains a client of reviewed compiler artifacts.

**Tech Stack:** Python standard library, existing parser/adjudication packages, unittest, the existing localhost workbench.

**Spec:** `C:\Users\DELL\Downloads\MATHesis_M3_Combined_Review_2026-09-17.md` and `C:\Users\DELL\Downloads\MATHesis_M3_1_Targeted_Plan_2026-09-17.md`.

## Constraints

- Do not change Pattern Lab, add M4 primitive families, or special-case §40.
- Preserve SourcePacket source identity and the production boundary from evaluation/history artifacts.
- Keep each repair group independently tested and locally committed; do not push.
- Retain scholarly unknowns as explicit partial/Hole states. Do not make invalid structures appear closed.

### Task 1 — Decision contract and atomic reviewed edits

**Files:** `adjudication/decision_contracts.py`, `session.py`, `replay.py`, `anchors.py`, `compiler.py`; `tests/adjudication/test_m31_consistency.py`.

- [x] Import the audit's five positive controls and fourteen desired-contract counterexamples unchanged in meaning.
- [x] Confirm the current tree reproduces 5 passing controls and 14 failures.
- [x] Define one versioned payload/semantic-target contract used by append validation, conflict detection and effective-state keys.
- [x] Make manual replacement validate and construct before it replaces automatic candidates; validate candidate membership from the compiler snapshot.
- [x] Preserve authored candidate sequence independently of decision/object identifiers.
- [x] Verify the six Task-1 counterexamples and existing replay/acceptance regressions, then commit locally.

### Task 2 — One reviewed syntax snapshot

**Files:** existing syntax/context/program/scoped/compiler/projection modules; M3.1 tests.

- [ ] Reproduce and repair reviewed syntax, context declaration, and MethodSlice snapshot divergence.
- [ ] Derive program/context/method/control artifacts from reviewed syntax without parallel rebuild paths.
- [ ] Enforce current-object identity through graph and projection.

### Task 3 — Quantity semantic finalization

**Files:** existing state/scoped/quantity semantics/compiler modules; M3.1 tests.

- [ ] Apply decision and automatic quantity facts at both context and operation emission sites.
- [ ] Derive compatible unit/kind/status together and retain incompatible/unknown states.

### Task 4 — Unified validation and closure

**Files:** existing audit/coverage/validation/review queue/bundle/service modules; M3.1 tests.

- [ ] Make structural audit findings block closure and expose normalized review issues.
- [ ] Represent ExtensionRequest independently from ordinary defer.

### Task 5 — Workbench closure

**Files:** existing Workbench UI/API/service and browser tests.

- [ ] Preserve sessions on transient errors, make existing-context attachment idempotent, and display real action effects.
- [ ] Run two-procedure browser acceptance and full regressions; update evidence and stop before M4.
