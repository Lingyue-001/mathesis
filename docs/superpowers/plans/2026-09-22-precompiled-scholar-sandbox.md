# Precompiled Scholar Sandbox Scenario Implementation Plan

> Execution amendment (2026-09-22): the user approved uninterrupted Native execution and explicitly prohibited commit, push, and deployment. All commit/release/remote smoke-test steps below are omitted. Work stays in the accepted current workspace, preserving prior uncommitted Inspector changes. Evidence is recorded in `tmp/precompiled-sandbox/REPORT.md` and `.superpowers/sdd/2026-09-22-precompiled-scholar-sandbox/progress.md`.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish a static, conference-safe §38 Inspector whose three approved review confirmations switch among complete snapshots produced by the existing Python compiler.

**Architecture:** `workbench/sandbox_snapshot.py` becomes the single exporter for both an individual `ScholarSandboxSnapshot/1` and a finite `ScholarSandboxScenario/1`.  Its scenario states are assembled from disposable, in-memory review sessions and the existing review-decision/replay/compiler path.  The static Inspector loads the scenario, uses a small pure scenario-state helper to select a complete embedded snapshot, and continues to use the existing source, Procedure Model, drafts, and workspace renderers.

**Tech Stack:** Python 3/unittest; existing adjudication and workbench compiler services; ES modules; Eleventy 2; Playwright; GitHub Pages project path `/mathesis/`.

**Spec:** [Precompiled Scholar Sandbox Scenario for Han Si-fen li §38](../specs/2026-09-22-precompiled-scholar-sandbox-design.md)

## Execution result (2026-09-22)

The original step checklist below is retained as the reviewed plan. Final execution status:

- [x] Task 1: complete snapshot conversion and Python-authored four-layer presentation.
- [x] Task 2: deterministic scenario; all four snapshots equal independently persisted real compiler transactions.
- [x] Task 3: pure validated state transitions; malformed/cyclic/missing successors rejected.
- [x] Task 4: static Confirm/reset, full rendering updates, snapshot-bound drafts, tab reload persistence.
- [x] Task 5: production `/mathesis/` static browser acceptance, zero API/asset/console errors, 1440/768/390 screenshots.
- [x] Task 6 (local portion): 4 exporter tests, 60 local Inspector tests, 26 Node tests, full local browser interaction regression, build and compile checks passed.
- Commit, push, deployment and remote URL testing: omitted by the user's latest instruction.

Interface corrections: use the existing `_option_submission` for both decisions and management events; preserve `--job-id` and add explicit `--scenario`; retain Snapshot/1 loading for existing regression fixtures. Generate a candidate first, accept it over a static origin, then replace the tracked data and repeat production acceptance. Storage failure must not block precompiled Confirm. See `tmp/precompiled-sandbox/REPORT.md` for files, evidence, screenshots and limits.

## Global Constraints

- Preserve parser, compiler, Domain Kernel, Program IR, executor, review, ScholarSourceProjection, and Procedure Model semantics.
- Generate every state by replaying an ordinary valid review decision through the current Python compiler; JavaScript only selects an exported state.
- Public path is `/mathesis/inspector/`; assets must remain Eleventy-base-aware and work under `/mathesis/`.
- No request may target `/api/adjudication/*`; do not expose fake Execute, compile, or re-run controls.
- Keep non-scenario choices as browser-local `Draft review · not recompiled` records with import/export/retract behavior.
- Do not alter canonical data including `src/data.json`, tracked public ReviewJobs, or the intentionally removed `/adjudication/` route.
- Use the approved sequence only: `baseline` → `ordinal-reviewed` → `zhang-yue-attached` → `zhang-fa-attached`.
- Retain the approved Inspector shell, scope note, and frozen selected-object UI copy; add only state-transition controls required by the specification.

## Review Focus

- A successor must come from an independently compiled response, not merely a changed decision list; Task 2 pins the full exported projection/model/history to independent replay.
- An existing draft must not be silently discarded or marked compiled when the active scenario state changes; Task 4 tests state-partitioned draft preservation and immutable snapshot data.
- The `章月` and `章法` choices must identify their exact §16/§15 document metadata rather than localized UI labels; Task 2 tests metadata-based discovery.
- Invalid, cyclic, missing, or non-linear transitions must be rejected before rendering; Task 3 tests the pure scenario validator.
- Production paths and narrow screens must load all data and remain usable without an API; Task 5 runs `/mathesis/` static-origin browser acceptance at 1440, 768, and 390 px.

---

### Task 1: Factor complete snapshot construction and export selected-object sections

**Files:**
- Modify: `workbench/sandbox_snapshot.py:24-213`
- Modify: `tests/workbench/test_sandbox_snapshot.py:1-112`

**Interfaces:**
- Consumes: an existing current compiler response shaped like `service.compile_review_job(root, job_id)`.
- Produces: `build_snapshot_from_response(root: Path, response: dict) -> dict` and a `ScholarSandboxSnapshot/1` that includes `details.objects[object_id]["selected_source_sections"]`.
- Preserves: `build_snapshot(root=".", job_id=DEFAULT_JOB_ID) -> dict`, `serialize_snapshot(snapshot) -> str`, and `export_snapshot(snapshot, output) -> Path`.

- [ ] **Step 1: Write the failing snapshot-presentation test**

```python
def test_snapshot_includes_the_python_authored_fixed_selected_object_sections(self):
    snapshot = build_snapshot(self.root)
    detail = next(iter(snapshot["details"]["objects"].values()))
    self.assertEqual(
        [section["key"] for section in detail["selected_source_sections"]],
        ["terms", "constructions", "steps", "flows"],
    )
    self.assertEqual(
        detail["selected_source_sections"],
        selected_source_object_sections(snapshot["renderer"], detail["selected"]["id"]),
    )
```

Add `selected_source_object_sections` to the imports in the test module.

- [ ] **Step 2: Run the test to verify it fails**

Run: `tools/parser_inspector/.venv/Scripts/python.exe -m unittest tests.workbench.test_sandbox_snapshot.SandboxSnapshotTests.test_snapshot_includes_the_python_authored_fixed_selected_object_sections -v`

Expected: FAIL because the detail has no `selected_source_sections` key.

- [ ] **Step 3: Implement one response-to-snapshot conversion function**

In `workbench/sandbox_snapshot.py`, import `selected_source_object_sections` and extract the body that starts with `projection = project_scholar_source(...)` into:

```python
def build_snapshot_from_response(root, response):
    """Serialize one already-current compiler response without mutating it."""
    root = Path(root).resolve()
    if response.get("freshness", {}).get("status") != "current":
        raise ValueError("sandbox_snapshot_requires_current_review_job")
    # Preserve the current projection/renderer/question construction exactly.
    # For each object detail, add the Python-authored presentation array:
    # detail["selected_source_sections"] = selected_source_object_sections(renderer, object_id)
    # Compute snapshot_id from the finished unsigned object as build_snapshot does today.
```

Make `build_snapshot` compile the named job and delegate to this function.  Do not create a second projection or Procedure Model path.

- [ ] **Step 4: Run the focused exporter suite**

Run: `tools/parser_inspector/.venv/Scripts/python.exe -m unittest tests.workbench.test_sandbox_snapshot -v`

Expected: PASS, including byte determinism, read-only store digests, and the new selected-object-section assertion.

- [ ] **Step 5: Commit the focused exporter refactor**

```bash
git add workbench/sandbox_snapshot.py tests/workbench/test_sandbox_snapshot.py
git commit -m "Export complete scholar snapshot presentation"
```

### Task 2: Build deterministic, real-compiler §38 scenario states

**Files:**
- Modify: `workbench/sandbox_snapshot.py:24-213`
- Modify: `tests/workbench/test_sandbox_snapshot.py:1-160`
- Create: `static/data/inspector/sifen-38.snapshot.json`

**Interfaces:**
- Consumes: `build_snapshot_from_response(root, response)`, `service._packet_for_job`, `service._job_response`, `service.review_decision`, and `adjudication.append_decision`.
- Produces: `SCENARIO_SCHEMA = "ScholarSandboxScenario/1"`, `build_scenario(root=".") -> dict`, `serialize_scenario(scenario) -> str`, `export_scenario(scenario, output) -> Path`, and `DEFAULT_SCENARIO_OUTPUT = Path("static/data/inspector/sifen-38.snapshot.json")`.
- State shape: `{"schema", "scenario_id", "source", "initial_state_id", "states", "transitions"}`; each `states[id]` is a valid full snapshot.

- [ ] **Step 1: Write failing tests for linear deterministic scenario output**

```python
def test_scenario_is_deterministic_and_has_only_the_approved_path(self):
    first = build_scenario(self.root)
    second = build_scenario(self.root)
    self.assertEqual(serialize_scenario(first), serialize_scenario(second))
    self.assertEqual(first["schema"], "ScholarSandboxScenario/1")
    self.assertEqual(first["initial_state_id"], "baseline")
    self.assertEqual(
        [(row["from_state_id"], row["to_state_id"]) for row in first["transitions"]],
        [("baseline", "ordinal-reviewed"),
         ("ordinal-reviewed", "zhang-yue-attached"),
         ("zhang-yue-attached", "zhang-fa-attached")],
    )
    self.assertEqual(set(first["states"]),
                     {"baseline", "ordinal-reviewed", "zhang-yue-attached", "zhang-fa-attached"})
    for snapshot in first["states"].values():
        self.assertEqual(snapshot["schema"], "ScholarSandboxSnapshot/1")
        self.assertEqual(serialize_snapshot(snapshot), canonical_json(snapshot))
```

Add a second test that derives an independent in-memory compiler response for each transition and asserts equality of the exported successor’s `projection`, `procedure_model`, `questions`, and `review` fields.

- [ ] **Step 2: Run the new scenario tests to verify they fail**

Run: `tools/parser_inspector/.venv/Scripts/python.exe -m unittest tests.workbench.test_sandbox_snapshot.SandboxSnapshotTests.test_scenario_is_deterministic_and_has_only_the_approved_path -v`

Expected: FAIL because `build_scenario` does not yet exist.

- [ ] **Step 3: Add an in-memory review-session adapter that uses existing adjudication logic**

In `workbench/sandbox_snapshot.py`, add a private helper that creates a local job dictionary without `review_jobs.write_job_atomic`:

```python
def _scenario_response(root, source_selection, decisions=()):
    packet = service._packet_for_job(root, source_selection, "sandbox-scenario")
    job = {
        "schema": "ReviewJob/1", "job_id": "sandbox-scenario", "revision": 1,
        "source_selection": deepcopy(source_selection),
        "base_packet_identity": service.packet_identity(packet),
        "analysis_inputs_digest": service._analysis_inputs_digest(packet),
        "session": new_session(packet, "review:sandbox-scenario"),
        "branch_id": "main", "management_events": [],
        "created_at": "2026-09-22T00:00:00+00:00", "updated_at": "2026-09-22T00:00:00+00:00",
    }
    for decision in decisions:
        append_decision(job["session"], decision, packet=packet)
        job["revision"] += 1
    return service._job_response(root, job, packet)
```

Use existing imports rather than copying compiler logic.  If a helper is private today, keep it private and add no public service API unless direct use is impossible.

- [ ] **Step 4: Implement metadata-based decision discovery and the scenario exporter**

Build each decision from the current response’s question options, never from its visible label:

```python
def _scenario_option(response, *, predicate):
    for question in response["questions"]:
        for option in question.get("options", []):
            if predicate(question, option):
                return question, option
    raise ValueError("sandbox_scenario_option_not_found")
```

Use predicates that identify:

```python
# ordinal: the 入蔀年 counting-convention option whose payload records base 1/ordinal.
# 章月: attach_context option with exact_declaration.unit_id == "sifen:section:16".
# 章法: attach_context option with exact_declaration.unit_id == "sifen:section:15".
```

Call `service.review_decision` with the selected question target/payload and a fixed scenario actor/reason.  Replace only `decision_id` and `created_at` with stable values such as `scenario:ordinal-reviewed` and the fixed ISO timestamp before applying it to the in-memory session.  Preserve the decision action, targets, payload, evidence refs, reason, branch, and dependencies exactly.

For each transition, append the new valid decision, call `_scenario_response`, convert it with `build_snapshot_from_response`, and store the complete snapshot.  Store the question/option IDs from the predecessor state and a deep-copied decision record in the transition.  Hash the unsigned scenario with the existing canonical JSON function and reject any schema, state, transition, or hash mismatch in `serialize_scenario`.

- [ ] **Step 5: Prove exporter safety and unresolved semantics**

Add tests that capture `review_jobs.job_path(ROOT, DEFAULT_JOB_ID)` before/after scenario generation, and that assert unchanged bytes.  In the final state, inspect the relevant `projection["semantic_closure"]["unresolved"]` records and assert that no §38-only inference turns unresolved `積月` or `閏餘` into a reviewed/derived Term interpretation unless the current generic compiler already did so.

Run: `tools/parser_inspector/.venv/Scripts/python.exe -m unittest tests.workbench.test_sandbox_snapshot -v`

Expected: PASS, with the public ReviewJob unchanged.

- [ ] **Step 6: Export the tracked public scenario and validate its JSON**

Run:

```bash
tools/parser_inspector/.venv/Scripts/python.exe -m workbench.sandbox_snapshot --root . --output static/data/inspector/sifen-38.snapshot.json
node -e "const fs=require('fs'); const s=JSON.parse(fs.readFileSync('static/data/inspector/sifen-38.snapshot.json','utf8')); if(s.schema!=='ScholarSandboxScenario/1') throw Error(s.schema); console.log(s.scenario_id, Object.keys(s.states));"
```

Expected: one UTF-8 tracked JSON scenario with four complete states and the three fixed transitions.

- [ ] **Step 7: Commit scenario export and tests**

```bash
git add workbench/sandbox_snapshot.py tests/workbench/test_sandbox_snapshot.py static/data/inspector/sifen-38.snapshot.json
git commit -m "Export precompiled scholar inspector scenario"
```

### Task 3: Add a pure static scenario-state helper

**Files:**
- Create: `src/js/scholar-sandbox-scenario.mjs`
- Create: `tests/scholar-sandbox-scenario.test.mjs`

**Interfaces:**
- Consumes: parsed `ScholarSandboxScenario/1` JSON and the current state ID/question ID/option ID.
- Produces: `validateScenario(scenario)`, `initialScenarioState(scenario)`, `transitionFor(scenario, stateId, questionId, optionId)`, and `applyTransition(scenario, stateId, transitionId)`.
- Returns: `{state_id, snapshot, transition}`; it never changes a snapshot, graph, decision, or local storage.

- [ ] **Step 1: Write failing Node tests for validation and state movement**

```javascript
import test from 'node:test';
import assert from 'node:assert/strict';
import {applyTransition, initialScenarioState, transitionFor, validateScenario}
  from '../src/js/scholar-sandbox-scenario.mjs';

const scenario = {
  schema: 'ScholarSandboxScenario/1', scenario_id: 'scenario-1', initial_state_id: 'baseline',
  states: {baseline: {schema: 'ScholarSandboxSnapshot/1', snapshot_id: 'a'}, next: {schema: 'ScholarSandboxSnapshot/1', snapshot_id: 'b'}},
  transitions: [{id: 't1', from_state_id: 'baseline', to_state_id: 'next', question_id: 'q1', option_id: 'o1'}],
};

test('only an exact outgoing option can reach its precompiled successor', () => {
  validateScenario(scenario);
  assert.equal(initialScenarioState(scenario).state_id, 'baseline');
  assert.equal(transitionFor(scenario, 'baseline', 'q1', 'o1').id, 't1');
  assert.equal(transitionFor(scenario, 'baseline', 'q1', 'other'), null);
  assert.equal(applyTransition(scenario, 'baseline', 't1').snapshot.snapshot_id, 'b');
});

test('rejects a missing state, non-outgoing transition, duplicate ID, and non-snapshot node', () => {
  assert.throws(() => validateScenario({...scenario, initial_state_id: 'missing'}), /initial_state_id/);
  assert.throws(() => applyTransition(scenario, 'next', 't1'), /not outgoing/);
  assert.throws(() => validateScenario({...scenario, transitions: [...scenario.transitions, {...scenario.transitions[0]}]}), /duplicate transition/);
  assert.throws(() => validateScenario({...scenario, states: {baseline: {schema: 'wrong'}}}), /ScholarSandboxSnapshot/);
});
```

- [ ] **Step 2: Run the Node test to verify it fails**

Run: `node --test tests/scholar-sandbox-scenario.test.mjs`

Expected: FAIL with module-not-found.

- [ ] **Step 3: Implement strict, non-mutating validation**

Implement the four exported functions in `src/js/scholar-sandbox-scenario.mjs`.  Validate exact schema names, a nonempty string ID for every state/transition, valid transition endpoints, unique transition IDs, and complete Snapshot/1 states.  `transitionFor` returns only a transition whose `from_state_id`, `question_id`, and `option_id` all match.  `applyTransition` must call `transitionFor` semantics via the transition ID and throw when the active state cannot use it.  Return references only; do not write any JSON, DOM, storage, or network code.

- [ ] **Step 4: Run the scenario-helper test suite**

Run: `node --test tests/scholar-sandbox-scenario.test.mjs`

Expected: PASS.

- [ ] **Step 5: Commit the pure static state helper**

```bash
git add src/js/scholar-sandbox-scenario.mjs tests/scholar-sandbox-scenario.test.mjs
git commit -m "Add static scholar scenario state helper"
```

### Task 4: Switch the static Inspector between complete snapshots

**Files:**
- Modify: `src/js/scholar-sandbox.mjs:1-359`
- Modify: `src/inspector.liquid:8-83`
- Modify: `tests/scholar-sandbox-drafts.test.mjs:1-210`

**Interfaces:**
- Consumes: the helper from Task 3 and `ScholarSandboxScenario/1` at `data-snapshot-url`.
- Produces: `setActiveScenarioState(nextState)` inside the Inspector module and a `#scenario-status` state note plus `#reset-demonstration` button.
- Preserves: existing workspace navigation, source ↔ graph selection, boundary drafts, draft import/export/retract, and static browser controls.

- [ ] **Step 1: Write failing draft partition tests**

Extend the draft helper tests with a source fixture that varies only `snapshot_id`.  Assert that the existing `draftStorageKey(snapshot)` binds a draft to the active full snapshot and that a baseline draft remains loadable after a separate successor snapshot’s empty draft state is created:

```javascript
test('scenario state changes do not erase baseline browser drafts', () => {
  const baseline = snapshot({snapshot_id: 'baseline'});
  const successor = snapshot({snapshot_id: 'successor'});
  const storage = new MemoryStorage();
  const saved = saveDrafts(baseline, upsertDraft(baseline, createDraftState(baseline), optionRecord(baseline)), storage);
  saveDrafts(successor, createDraftState(successor), storage);
  assert.deepEqual(loadDrafts(baseline, storage), saved);
  assert.deepEqual(loadDrafts(successor, storage), createDraftState(successor));
});
```

- [ ] **Step 2: Run the focused draft test**

Run: `node --test tests/scholar-sandbox-drafts.test.mjs`

Expected: PASS before integration because the invariant is already provided by snapshot-bound storage.  Record this as a preservation test, not a code change to the draft schema.

- [ ] **Step 3: Implement scenario-aware loading and atomic state replacement**

At startup, fetch and validate `ScholarSandboxScenario/1`; reject the old single snapshot schema with a clear static error because the committed public data must now be a scenario.  Keep these module-level values:

```javascript
let scenario, scenarioStateId, snapshot, drafts;

function setActiveScenarioState(nextState, {announce = true} = {}) {
  scenarioStateId = nextState.state_id;
  snapshot = nextState.snapshot;
  root.dataset.snapshotId = snapshot.snapshot_id;
  drafts = loadDrafts(snapshot, localStorage);
  selected = snapshot.renderer.objects[selected] ? selected : null;
  facetKey = snapshot.details.facets[facetKey] ? facetKey : null;
  questionId = snapshot.questions.some(q => q.id === questionId) ? questionId : null;
  sourceData = {text: snapshot.source.text, render: structuredClone(snapshot.renderer), language: 'en', focus: selected, facet_key: facetKey, adjust: false, changed_ids: []};
  refreshDraftPresentation(true);
  renderProcedureModel($("procedure-host"), snapshot.procedure_model, {onSelect: choose});
  renderDetails(); renderQuestion(); renderReviewHistory(); renderCorpus();
  $("scenario-status").textContent = announce ? "Precompiled successor loaded." : "";
}
```

Preserve a baseline draft in its baseline storage bucket and a successor draft in its successor bucket.  Never copy draft decisions across snapshot IDs because their question/option identities may differ.

In `renderQuestion`, use `transitionFor(scenario, scenarioStateId, question.id, option.id)`.  When present, show `Confirm` and call `applyTransition` then `setActiveScenarioState`; otherwise keep the existing `Save as draft`/`Add context as draft` behavior.  Do not show `Confirm` for attachment search/picker intermediary actions.  Do not create a client-side decision object or modify `snapshot.review`.

- [ ] **Step 4: Render Python-authored selected-object sections instead of re-inferring relations**

Replace the static relation-by-relation details dump with `details.selected_source_sections`.  Render the four arrays in their stored order, using their stored title, description, empty copy, item attributes, and selected flags.  The static module may create DOM elements, but it must not calculate term/construction/step/flow links from strings or IDs.  Keep existing semantic provenance and facet/question records after the four stored sections.

- [ ] **Step 5: Add the minimal approved static controls**

In `src/inspector.liquid`, insert directly below `#draft-status`:

```html
<p id="scenario-status" class="research-muted" role="status" hidden></p>
<button id="reset-demonstration" type="button" class="research-button" hidden>Reset demonstration</button>
```

Show `Reset demonstration` only after the active state differs from `baseline`; hide it at baseline.  The button calls `setActiveScenarioState(initialScenarioState(scenario), {announce: false})`.  It must not clear local storage.

- [ ] **Step 6: Run static unit and syntax checks**

Run:

```bash
node --check src/js/scholar-sandbox.mjs
node --test tests/scholar-sandbox-drafts.test.mjs tests/scholar-sandbox-scenario.test.mjs
```

Expected: PASS.  The tests must show local drafts remain snapshot-bound and uncompiled.

- [ ] **Step 7: Commit the static scenario integration**

```bash
git add src/js/scholar-sandbox.mjs src/inspector.liquid tests/scholar-sandbox-drafts.test.mjs
git commit -m "Switch inspector through precompiled scenarios"
```

### Task 5: Extend production static-browser acceptance for scenario transitions

**Files:**
- Modify: `tests/scholar-sandbox-browser.mjs:1-260`
- Modify: `tests/workbench/semantic-closure-static.mjs:1-76` only if its snapshot assumption prevents a scenario page from loading

**Interfaces:**
- Consumes: `dist`, `/mathesis/inspector/`, and the committed `ScholarSandboxScenario/1` public data.
- Produces: acceptance JSON and 1440/768/390 screenshots under `tmp/static-scholar-sandbox/`.

- [ ] **Step 1: Write failing browser assertions for the real precompiled path**

After parsing the data response, assert scenario schema and choose each transition from its predecessor snapshot:

```javascript
const scenario = JSON.parse(await fs.readFile('static/data/inspector/sifen-38.snapshot.json', 'utf8'));
assert.equal(scenario.schema, 'ScholarSandboxScenario/1');
let stateId = scenario.initial_state_id;
for (const transition of scenario.transitions) {
  assert.equal(transition.from_state_id, stateId);
  const before = scenario.states[stateId];
  await page.locator('.source .facet[data-facet-key="'+facetForQuestion(before, transition.question_id)+'"]').first().click();
  const option = before.questions.find(q => q.id === transition.question_id).options.find(o => o.id === transition.option_id);
  await page.getByRole('radio', {name: option.label, exact: true}).check();
  await page.getByRole('button', {name: 'Confirm', exact: true}).click();
  await page.getByText('Precompiled successor loaded.', {exact: true}).waitFor();
  stateId = transition.to_state_id;
  assert.equal(await page.locator('#scholar-sandbox').getAttribute('data-snapshot-id'), scenario.states[stateId].snapshot_id);
}
```

Add deep checks that the current rendered source equals each successor `source.text`, Procedure Model node/edge counts equal the successor’s `procedure_model`, and review history includes the successor’s exported decisions.

- [ ] **Step 2: Run the browser test to verify it fails**

Run:

```bash
$env:NODE_ENV='production'; $env:GITHUB_ACTIONS='true'; npm run build
node tests/scholar-sandbox-browser.mjs
```

Expected: FAIL because the current public file is Snapshot/1 and the static page has no `Confirm` transition.

- [ ] **Step 3: Implement browser helpers and scenario checks**

Add a `facetForQuestion(snapshot, questionId)` helper that selects only a recorded renderer facet; do not derive it from text.  After each confirmation, call the existing `render()` wait helper and assert both annotated source text and graph counts against the successor state.  Assert `Reset demonstration` restores baseline snapshot ID, base review history, and source text.

For an option without `transitionFor`, save a draft, reload, and verify: its active snapshot ID, source text, Procedure Model node/edge counts, and exported review history remain unchanged.  Retain current import/export and Unicode-code-point boundary assertions.  Continue collecting console errors, failed assets, and requests; assert `api`, `failed`, and `errors` are empty and Inspector copy has no fake backend controls.

At each width `1440`, `768`, and `390`, assert no page-level horizontal overflow, source/question/details controls are visible and usable, and Procedure Model horizontal overflow is contained by its graph element instead of the document.

- [ ] **Step 4: Run full production static acceptance**

Run:

```bash
$env:NODE_ENV='production'; $env:GITHUB_ACTIONS='true'; npm run build
node tests/scholar-sandbox-browser.mjs
```

Expected: PASS with acceptance JSON and desktop/tablet/mobile source/graph screenshots in `tmp/static-scholar-sandbox/`.

- [ ] **Step 5: Commit browser acceptance**

```bash
git add tests/scholar-sandbox-browser.mjs tests/workbench/semantic-closure-static.mjs
git commit -m "Verify static inspector scenario transitions"
```

### Task 6: Regress local research mode and release the validated public data

**Files:**
- Modify only as generated and verified in earlier tasks: `static/data/inspector/sifen-38.snapshot.json`
- Modify local-only status files when present: `NOTE_当前需求清单和待办_Current_Status_and_Todo.md`, `LOG_已完成改动和复盘_Completed_Changes_and_Retrospective.md`

**Interfaces:**
- Consumes: all committed work from Tasks 1–5.
- Produces: a passing local Inspector regression, production build evidence, a selective release commit/push, and GitHub Pages deployment confirmation for `https://lingyue-001.github.io/mathesis/inspector/`.

- [ ] **Step 1: Run local Python and Inspector regressions**

Run:

```bash
tools/parser_inspector/.venv/Scripts/python.exe -m unittest tests.workbench.test_sandbox_snapshot tests.workbench.test_scholar_renderer tests.workbench.test_source_review tools.parser_inspector.test_review_panel -v
tools/parser_inspector/.venv/Scripts/python.exe -m compileall -q workbench tools/parser_inspector
```

Expected: all named tests pass and compileall has no errors.  Do not modify a tracked ReviewJob to make a test pass.

- [ ] **Step 2: Run final production static acceptance from clean build output**

Run:

```bash
Remove-Item -Recurse -Force dist -ErrorAction SilentlyContinue
$env:NODE_ENV='production'; $env:GITHUB_ACTIONS='true'; npm run build
node tests/scholar-sandbox-browser.mjs
```

Expected: `dist/mathesis`-prefixed Inspector assets load; all scenario/draft/responsive assertions pass with zero API requests and zero console errors.

- [ ] **Step 3: Inspect staged scope before release**

Run:

```bash
git diff --check
git status --short
git diff --cached --name-only
```

Expected: only Task 1–5 files plus the approved static scenario are staged or committed.  Do not add pre-existing unrelated dirty files, zip files, local server logs, or canonical data.

- [ ] **Step 4: Update local completed-work log and current-status note**

When the local NOTE/LOG files exist, record the completed static scenario export, real compiler successor evidence, static production acceptance, and remaining deployment status.  Use the existing logging convention with `infra, project-docs`; do not add these ignored local files to Git.

- [ ] **Step 5: Create one final selective release commit if needed and push `main`**

```bash
git add -- workbench/sandbox_snapshot.py tests/workbench/test_sandbox_snapshot.py src/js/scholar-sandbox-scenario.mjs src/js/scholar-sandbox.mjs src/inspector.liquid tests/scholar-sandbox-scenario.test.mjs tests/scholar-sandbox-drafts.test.mjs tests/scholar-sandbox-browser.mjs tests/workbench/semantic-closure-static.mjs static/data/inspector/sifen-38.snapshot.json
git commit -m "Publish precompiled §38 inspector scenario"
git push origin main
```

If the earlier task commits already contain all listed files, make no empty commit; push the verified commit range.  The push triggers the existing `.github/workflows/eleventy.yml` GitHub Pages workflow.

- [ ] **Step 6: Smoke-test the deployed site after the Pages workflow completes**

Open `https://lingyue-001.github.io/mathesis/inspector/`, repeat baseline load, one `Confirm` transition, reset, and a mobile-width no-overflow check.  Confirm that all Inspector assets resolve below `/mathesis/` and no `/api/adjudication/*` request is made.

- [ ] **Step 7: Report release evidence**

Report exact changed files, scenario/schema details, local compiler regression result, production build result, static-browser acceptance JSON and screenshots, pushed commit, deployed route, and any remaining deployment blocker.
