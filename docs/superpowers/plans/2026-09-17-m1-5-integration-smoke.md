# M1.5 Integration Smoke Implementation Plan

Historical M1.5 plan. The user's subsequent M1.5b request replaces the standalone shell with an Eleventy website page and an IR-based procedure analysis view; current behavior and verification are documented in `docs/workbench-smoke.md`.

> Execute inline with test-driven development. This implements the user's approved M1.5 scope and the existing repository architecture; stop for localhost review before M2.

**Goal:** Real repository corpus → SourcePacket 3.0 → unchanged compiler/executor → same-origin local Adjudication Lab shell.

**Architecture:** `source_adapters/corpus.py` reads the registered corpus from `config/calendrical-ir-pipeline.json`. A small procedure registry pins exact source sections, hashes and legal local inputs; it contains no graph, expected answer or copied source text. `workbench/service.py` calls `parse_packet` and `execute`; `workbench/api.py` serves that service and a standalone shell using existing global CSS.

**Tech Stack:** Python 3.11 standard library; browser ES modules; existing MATHesis CSS. No new dependencies or deployment.

**Spec:** User's M1.5 request; `docs/architecture.md`. Initial scope is Cullen Proc. 3.5, 四分历「推天正術」, corpus section 38 with parameter sections 15/16. This is a local procedure taking 入蔀年 (1–76); it does not reconstruct the full upstream chronology. Source remains unchanged, including punctuation. No adjudication session, editing, candidate selection, decisions, replay or primitive expansion.

## Tasks

1. **Adapter:** Write failing tests for exact corpus slices/hash/offsets, changed/missing/duplicate sections, invalid IDs, and a minimal root with no evaluation/history. Implement `list_procedures(root)` and `build_source_packet(root, procedure_id)`. Verify `source_packet` uses 3.0 and every document traces to the actual file's code-point range. Cross-reference fixed procedure identity, not heuristic corpus scanning.
2. **Service/API:** Write failing tests for actual compile/execute (入蔀年=25 → 積月296 / 閏餘16), omitted inputs → missing_inputs, invalid typed inputs, same-origin HTTP and static/path/Host/Origin boundaries. Implement `compile_procedure(root, id, inputs)` and `make_server(root, port)`, plus `python -m workbench.api --port 8789`. HTTP accepts registered procedure IDs only; source text and graphs never arrive from the client.
3. **Shell:** Build `workbench/static/index.html`, `app.js`, `shell.css`. Reuse global `search-page`, `filter-box`, `search-controls`, `entry-card` and section classes. Local CSS only controls layout and graph wrapping. Show source/context, declared local input, status, outputs, unresolved and expandable original graph. Render source with textContent. No Pattern Lab imports or navigation changes.
4. **Verification:** Run the new suite, inherited 61/94/78, engineering35, old-A strict gate and existing website checks. Verify the M1 core and Pattern Lab hashes. Start localhost in a hidden persistent process; actually exercise the browser and API, including missing-input state. Document exact address, steps and scope limitations. Leave changes for user review; do not prune audited M1 assets, commit, push or enter M2 during this smoke review.
