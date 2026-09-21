# Procedure Model v1 — implementation and acceptance

Date: 2026-09-21. Baseline: accepted Scholar Renderer v0.2, including unified
top badges, horizontal collision placement and initially unselected reading view.

## Handoff review

`ProcedureModel_v1_Codex_Handoff.md` matches the existing projected §38
dependencies: load → subtract → multiply → divmod; distinct quotient and
remainder; the remainder enters threshold, whose projected judgment is 其歲有閏.
No semantic-core change is needed. The implementation is generic; §38 is an
acceptance case, not a construction rule or a claim of corpus-wide validation.

Two source-precision qualifications are explicit in the implementation:

- Literal values are recorded on Step inputs, but do not currently carry their
  own source anchors. Literal nodes expose the exact **supporting Step** anchor,
  with `anchor_scope: supporting_step`. They do not claim that the whole clause
  is the literal's exact span. Hover explains this limitation.
- The projected threshold supplies a `lower` input but no separately exported
  comparison operator. The model labels it with the authored “Test threshold”
  and “Lower bound”; it does not reparse 以上 to create a new comparator field.

Existing projected Constructions are read only to locate the explicitly linked
Judgment anchor. They never become invented arithmetic operations. No parser,
compiler, Kernel, executor, Program IR or ScholarSourceProjection contract edits.

## Exact files changed in this pass

New:

- `workbench/procedure_model.py` — pure model builder, deterministic serializer,
  explicit export helper.
- `tools/parser_inspector/procedure_model.mjs` — reusable ES-module SVG graph
  renderer and generic topology layout; thin Streamlit adapter.
- `tools/parser_inspector/procedure_model.css` — graph node/edge presentation.
- `tools/parser_inspector/scholar_ui.mjs` — shared authored-text hover helper.
- `tools/parser_inspector/scholar_ui.css` — shared tooltip style.
- `tests/workbench/test_procedure_model.py` — synthetic contracts and §38 checks.
- `docs/procedure-model-v1-acceptance.md` — this report.

Modified:

- `tools/parser_inspector/review_panel.py` — view switch, read-only graph details,
  exact JSON download, shared Scholar selection handler.
- `tools/parser_inspector/source_annotation.py` — component registration and
  shared UI asset packaging for Streamlit.
- `tools/parser_inspector/source_annotation.mjs` — reuse the extracted hover helper.
- `tools/parser_inspector/source_annotation.css` — move tooltip style to shared CSS.
- `tests/workbench/scholar-renderer-browser.mjs` — graph, export, selection and
  standalone static acceptance added to the existing renderer browser suite.
- `tests/workbench/scholar-renderer-layout.test.mjs` — cyclic/disconnected topology
  layout and determinism, alongside the existing source layout tests.

## ProcedureModel/1

Top-level fields:

| Field | Meaning |
| --- | --- |
| `schema` | `ProcedureModel/1` |
| `source` | Projected source identity, exact source text and hash when supplied |
| `status` | `complete` or `incomplete` for recorded data-flow, not historical validation |
| `nodes` | Operation, input_quantity, unresolved_input, literal, named_quantity, quantity, judgment |
| `edges` | Recorded producer/consumer relationships and output-port identity |
| `source_index` | Scholar object ID → model node IDs and canonical anchors |
| `gaps` | Unresolved Flow states, missing ports, projection diagnostics, cycles or empty model |
| `summary` | Counts of nodes, edges, Steps, unresolved Flows and supporting-anchor nodes |

Every node carries `id`, `type`, `label`, `scholar_object_ids`,
`selection_object_id`, `source_anchors`, `anchor_scope`, and `decision_refs`.
Operation nodes also carry the registered operation code and authored ontology
definition. Input nodes retain Flow status and public producer-source metadata.
Term candidate statuses and counts of existing reviewed claims are copied into
`interpretations`; they never confer human authorship on adjacent Steps.

Each edge has `from`, `to`, `role`, `label`, `definition`,
`source_object_ids`, and `output_port` where known. Display uses authored port
labels; positional operand codes remain available in hover/Evidence.

### Derivation

1. Each projected Step produces one operation node with its original Scholar ID.
2. Explicit named outputs produce distinct nodes keyed by Step ID and output
   port. Quotient and remainder never merge, even with equal display labels.
3. Unnamed multi-port outputs remain distinct quantities. A single unnamed
   output can be represented by a direct edge from its producing operation.
4. Each Flow supplies an input node. Its Step input references determine the
   consumer roles; `producer_step_id` links a local producer if explicitly present.
   External producer identity stays as source metadata rather than an invented
   expanded subprocedure.
5. Literal nodes come from explicit Step input literal values. A referenced
   producer port is used only if explicit or uniquely determined by a single
   output; ambiguity creates an unresolved input, never a guessed remainder.
6. A recorded predicate judgment becomes a terminal display node, supported by
   the linked Judgment Construction when available. Naming Constructions are
   not arithmetic nodes.

Internal `vN`, `eN`, syntax-node, definition and session IDs are not exported as
model identities. Genuine explicit decision references are retained on their
own objects. Changing only internal value/event IDs leaves the model identical.

### Incompleteness

Unresolved/ambiguous source and runtime permission remain distinct. Runtime
permission alone does not establish a historical producer. Any such Flow,
unresolved output port, diagnostic, cycle or empty Step set makes this view
incomplete. All available nodes/edges still render. `complete` asserts only that
this projected model has no recorded gaps; it does not validate historical truth
or assert that every possible computation was discovered.

## UI and source linking

The existing Inspector contains `Annotated Source | Procedure Model`. There is
no separate demo application. Nodes differ in border/shape and label as well as
subdued color; unresolved inputs are dashed, literals compact, and judgments
double-bordered. Operation hover reads the existing ontology definition.

Graph clicks write the existing `k2_scholar_selected` Scholar ID and clear the
old question facet. The right pane uses the existing validated source-evidence
formatter to highlight the canonical anchor. Switching back focuses the same
Term, Construction or Step. Transport click nonces are tracked per component
to prevent replay of an old click when switching views; object identity is shared.

Graph exploration has no Confirm/recompile controls. Existing session/history/
management controls remain in their original Inspector locations. Browser checks
compare ReviewJob file bytes before and after graph exploration.

## Export and static use

Demo snapshot: `.cache/procedure-model/proc38.procedure-model.json`.
The Inspector's “Download Procedure Model JSON” returns exactly
`serialize_procedure_model(build_procedure_model(projection))`.

```python
from workbench.procedure_model import build_procedure_model, export_procedure_model

model = build_procedure_model(scholar_projection)
export_procedure_model(model, '.cache/procedure-model/procedure.procedure-model.json')
```

A later static site serves the same module and styles without Python or
Streamlit. With no callback supplied, the module provides local node selection,
source highlighting and expandable Evidence. No save/recompile UI is created.

```html
<link rel="stylesheet" href="/assets/scholar_ui.css">
<link rel="stylesheet" href="/assets/procedure_model.css">
<div id="procedure"></div>
<script type="module">
  import {renderProcedureModel} from '/assets/procedure_model.mjs';
  const model = await (await fetch('/data/procedure.procedure-model.json')).json();
  renderProcedureModel(document.querySelector('#procedure'), model);
</script>
```

Serve `scholar_ui.mjs` alongside `procedure_model.mjs`. The acceptance test
exercises this exact static path on an ordinary HTTP origin, including source
selection, independently of Streamlit.

## Validation and artifacts

Final result: **111 Python tests passed**, **4 Node layout tests passed**, and
the full browser acceptance passed. All **42 protected files** match the existing
pre-renderer SHA-256 baseline. Live Inspector remains at
`http://127.0.0.1:8507/?review_job=scholar-renderer-correction-20260920`.

- 11 Procedure Model tests: synthetic arbitrary labels/IDs, port separation,
  exact anchors, input immutability, real provenance only, runtime/source
  distinction, internal-ID invariance, missing/ambiguous ports, cycles,
  deterministic export, ontology text, no §38 lexical rules, and real §38 graph.
- Existing full golden equality and §15 invariant remain exact; no fixtures changed.
- Existing source renderer and review workflow browser acceptance still runs,
  including actual term decisions, stale-facet behavior and attach_context.
- Browser acceptance checks all 13 §38 nodes and 12 edges, graph↔source selection,
  ontology hover, JSON download byte equality, ReviewJob immutability and static loading.
- Source layout and graph layout tests cover Unicode, source geometry,
  disconnected/cyclic records and deterministic placement.

Commands:

```powershell
tools/parser_inspector/.venv/Scripts/python.exe -X utf8 -B -m unittest tests.workbench.test_procedure_model tests.workbench.test_question_presenter tests.workbench.test_scholar_renderer tests.workbench.test_scholar_source_projection tests.workbench.test_scholar_source_diff tests.workbench.test_annotation_projection tests.parser_v3.test_reviewed_syntax_grounding tools.parser_inspector.test_review_panel -q
node --test tests/workbench/scholar-renderer-layout.test.mjs
node tests/workbench/scholar-renderer-browser.mjs
```

Screenshots:

- [Full §38 model](../tmp/procedure-model-v1/01-proc38-procedure-model.png)
- [DivMod with source context](../tmp/procedure-model-v1/02-divmod-source-context.png)
- [Unresolved 章法](../tmp/procedure-model-v1/03-unresolved-source.png)

Browser evidence: `tmp/scholar-renderer-v02/acceptance.json` (the existing suite,
now extended with Procedure Model checks). Protected-file verification uses the
existing `tmp/scholar-renderer-v02/protected-sha256.json` baseline.

## Remaining projection limits

- Literal anchors and explicit comparator detail are qualified above.
- External producer internals and omitted/unlowered semantics cannot be expanded
  beyond what this focused Scholar projection records. Projection diagnostics
  remain visible model gaps; no raw graph inspection or source reparsing fills them.
- This is L2 quantity/dependency presentation. No strategy labels, historical
  transformations, pairwise comparison, K3 or K4 are inferred.
