# Static Scholar Sandbox v0.1

The public Inspector is an interactive, static mirror of the current Han Si-fen li §38 research Inspector. Its canonical route is `/inspector/`; the GitHub Pages project URL will be `https://lingyue-001.github.io/mathesis/inspector/`.

`Parser Stages` is the default workspace. `Segmentation Review` and `Corpus Browser` display the exported auto/effective units and recorded history for all three available corpora. Segmentation is read-only in this public version. The intentionally removed `/adjudication/` page is not restored or redirected.

## Data and renderer contract

The public analysis input is `static/data/inspector/sifen-38.snapshot.json`, a UTF-8 `ScholarSandboxSnapshot/1` document. It is versioned public demo data, independent of `.cache` and Python at build/runtime.

| Field | Content |
| --- | --- |
| `snapshot_id` | SHA-256 of sorted, indented UTF-8 JSON plus trailing newline, excluding this field |
| `source`, `provenance` | Exact source text, document/reading/hash identity, canonical code-point anchor, source-unit provenance and current ReviewJob revision |
| `projection` | Existing `ScholarSourceProjection/1` |
| `renderer`, `details`, `labels` | Existing scholar presentation, authored badges/hover text, object/facet selection details and display labels |
| `questions` | Current questions and the same deduplicated options as the research Inspector |
| `presentation_registry.compose_by_question` | Precomputed bounded composition choices from the shared research UI helper |
| `review` | Actual exported decisions, statuses and review history; empty records stay empty |
| `procedure_model` | Existing `ProcedureModel/1`, retaining canonical source/object addresses |
| `context_catalog`, `corpora` | Already available context documents and auto/effective segmentation workspaces |

The exporter reads the current local ReviewJob `scholar-renderer-correction-20260920` through the existing service and projection functions. It does not mutate that job or corpus review stores. This snapshot contains revision 1 and no saved scholarly decisions; it does not manufacture reviewed status.

Eleventy copies `source_annotation`, `scholar_ui` and `procedure_model` JavaScript/CSS directly from `tools/parser_inspector/`. Streamlit keeps its existing adapters. The static adapter renders exported data only; it does not tokenize, parse, compile, execute or infer scholarly meaning. Composition controls consume an exported choice tree shared with the research UI, without implementing a second Kernel or validator.

## Draft contract

`ScholarSandboxDrafts/1` is separate from the snapshot. It contains `snapshot_id`, source identity, `selected_options` and `decisions`. Each decision has a stable ID, `status: "draft"`, a kind (`option`, `context`, or `term_boundary`), an exact canonical source anchor, input values and a note. Question/option/object/facet/context references address existing snapshot records; backend decision payloads remain in the unchanged snapshot.

Offsets are half-open Unicode code-point ranges, matching Python source anchors, rather than JavaScript UTF-16 positions. Anchors contain `doc_id`, `reading_id`, `source_sha256`, `start`, `end`, `quote` and `offset_unit: "unicode_code_point"`.

Saved drafts persist under a snapshot-specific `localStorage` key and show `Draft review · not recompiled`. Users can edit/retract local records and export/import JSON. Imports check structure, source identity and exact source spans; these checks are not semantic validation. Wrong-snapshot or invalid-span imports preserve existing drafts. Corrupt stored drafts are retained and reported rather than silently discarded. Import size is limited to 5 MB.

Saving a question draft adds `· draft` to its existing Annotated Source badge and shows the saved choice in Current question and Selected details. This is a separate presentation overlay; canonical facet status remains pending until actual research-mode review. Reload restores it, and retraction removes it. Source text, source spans, semantic interpretation, the Procedure Model, canonical review history and exported analysis remain unchanged. There are no compile/execute/re-run buttons or `/api/adjudication/*` requests.

Current question appears before Selected source object. Review buttons and source question badges focus the exact current question, including on narrow screens. The local research Inspector uses the same question-first ordering when a question is active.

Draft export is not yet an automatic ReviewJob import. To inspect a new choice through the existing backend, make that choice in the local research Inspector and use Confirm and re-run. A meaning decision records a term interpretation; it does not by itself provide a numerical value, historical producer, conversion or new graph binding. Compilation can report supported structural/type/replay checks and calculation results, but does not prove that a historical interpretation is correct.

## Reproduce the build and acceptance

Ordinary production build, using PowerShell:

```powershell
$env:NODE_ENV = 'production'
npm.cmd run build
```

GitHub Pages-equivalent path prefix (GitHub Actions sets `GITHUB_ACTIONS` automatically):

```powershell
$env:NODE_ENV = 'production'
$env:GITHUB_ACTIONS = 'true'
npm.cmd run build
node tests/scholar-sandbox-browser.mjs
```

The browser suite serves `dist` from an ordinary Node HTTP server mounted at `/mathesis/`, with no application backend. It checks shared source/graph rendering and selection; all question options; local option/context/composition/span drafts; reload, edit and retraction; JSON round trips and rejected imports; immutable snapshot download; zero missing assets/API requests/console errors; and all three workspaces at 1440, 768 and 390 px. Screenshots and `acceptance.json` are written to `tmp/static-scholar-sandbox/`.

Other focused checks:

```powershell
node --test tests/scholar-sandbox-drafts.test.mjs tests/workbench/scholar-renderer-layout.test.mjs
node --test tests/public-navigation.test.mjs
node tests/workbench/scholar-renderer-browser.mjs
node tests/segmentation-review-browser.mjs
tools/parser_inspector/.venv/Scripts/python.exe -X utf8 -B -m unittest tests.workbench.test_sandbox_snapshot tools.parser_inspector.test_review_panel tools.parser_inspector.test_inspector tests.workbench.test_scholar_renderer tests.workbench.test_scholar_source_projection tests.workbench.test_procedure_model
```

The navigation test builds its own root-prefix `dist`. Rebuild with `GITHUB_ACTIONS=true` before running Pages static acceptance afterward.

Regeneration is a research-machine operation requiring the current local ReviewJob and segmentation workspaces, while deployment consumes the checked-in snapshot without them:

```powershell
tools/parser_inspector/.venv/Scripts/python.exe -X utf8 -B -m workbench.sandbox_snapshot
```

## Files introduced or edited for packaging

- `.eleventy.js` — shared renderer passthrough copies.
- `src/layouts/base.liquid` — Inspector navigation and self-contained Inspector asset mode.
- `src/css/research.css` — reusable workspace/form classes.
- `src/css/inspector.css` — Inspector-specific layout constraints.
- `src/inspector.liquid` — static Inspector shell and three workspaces.
- `src/js/scholar-sandbox.mjs` — static presentation adapter and interactions.
- `src/js/scholar-sandbox-drafts.mjs` — separate browser draft storage/import/export.
- `tools/parser_inspector/review_panel.py` — shared question-option/composition-choice helpers and question-first presentation.
- `tools/parser_inspector/test_review_panel.py` — question/selection ordering regression.
- `workbench/sandbox_snapshot.py` — deterministic read-only export.
- `static/data/inspector/sifen-38.snapshot.json` — public demo artifact.
- `tests/workbench/test_sandbox_snapshot.py` — export identity/determinism/no-mutation checks.
- `tests/scholar-sandbox-drafts.test.mjs` — source-bound draft tests.
- `tests/scholar-sandbox-browser.mjs` — actual production/static browser acceptance.
- `tests/public-navigation.test.mjs` — canonical navigation and intentional Workbench removal.
- `docs/superpowers/plans/2026-09-21-static-scholar-sandbox.md` — implementation/acceptance plan.
- `docs/static-scholar-sandbox.md` — this contract and reproduction guide.

Earlier outer-UI changes and other pre-existing working-tree changes are separate from this packaging list. No commit, push or deployment is part of this pass. A smoke test on the real GitHub Pages URL remains a post-deployment step.

## Local acceptance — 2026-09-21

| Check | Result |
| --- | --- |
| Ordinary production build | Passed |
| Pages-equivalent production build | Passed; 100 copied assets, 15 generated pages |
| Ordinary static HTTP `/mathesis/inspector/` | Passed; 12 acceptance groups, 0 console errors, 0 failed assets, 0 API requests |
| Responsive source, graph and all workspaces | Passed at 1440, 768 and 390 px |
| Local Inspector browser regression | Passed, including actual decisions/recompile/retract/context/Unicode boundaries against isolated research stores |
| Segmentation Review browser regression | Passed |
| Snapshot, renderer, projection and model Python tests | 59 passed |
| Review-panel Python tests | 17 passed |
| Inspector Python tests | 8 passed |
| Draft, layout and navigation Node tests | 13 passed |

Snapshot ID: `b5da90ad385381b8a75554b9513b54bb1881280e55d93f5611658c3564eeee90` (4,314,700 bytes).

Evidence: [static acceptance JSON](../tmp/static-scholar-sandbox/acceptance.json), [desktop page](../tmp/static-scholar-sandbox/parser-stages-1440.png), [mobile page](../tmp/static-scholar-sandbox/parser-stages-390.png), [mobile source](../tmp/static-scholar-sandbox/source-viewport-390.png), [mobile question and draft controls](../tmp/static-scholar-sandbox/question-viewport-390.png). Additional workspace/model screenshots are in the same directory.

An initial combined Python run encountered a concurrently edited test importing a not-yet-written display helper, plus a 3-second AppTest startup timeout. After the independent helper appeared and the UI tests were run separately, both affected suites passed. No unrelated changes were reverted.

No remaining local packaging blocker was found. This is local production/static acceptance, not a claim that the page is deployed. No commit, push or deployment was performed.

Source-label/picker correction: the static export now calls the same `review_source_display_label` helper as the local Inspector. Parser Stages, Segmentation Review, Corpus Browser and the context catalog therefore use `Santong li · 三統曆`, `Sifen li · 四分曆`, and `Jiuzhi li · 九執曆`, with no hardcoded simplified parser-source label. Shared select styling uses browser-supported customizable pickers to keep the menu and selected background at the field width, with native fallback where unsupported. Production browser acceptance also checks repeated opening, keyboard selection, and 12 consecutive frames of open-option alignment at each viewport. [Desktop open picker](../tmp/static-scholar-sandbox/parser-section-open-1440.png) · [Mobile open picker](../tmp/static-scholar-sandbox/parser-section-open-390.png).
