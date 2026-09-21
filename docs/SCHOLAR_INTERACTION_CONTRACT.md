# Scholar Interaction Contract v1

Status: **pre-renderer interaction contract**
Depends on: `ScholarSourceProjection/1` contract revision 1.1
Scope: scholar-facing judgment, change inspection, and interaction wiring only.

This contract does **not** create a second semantic projection. `ScholarSourceProjection/1` remains the sole scholar-facing semantic snapshot.

The final renderer will consume:

```text
ScholarSourceProjection/1
+ existing QuestionPresenter questions
+ ReviewJob/replay state
+ ScholarSourceDiff/1 (derived read-only transition view)
```

The renderer must not parse source text, generate questions, infer actions, or reconstruct semantic links.

---

## 0. Goals

A historical researcher must be able to answer, directly from the scholar-facing view:

1. What does the machine currently recognize at the Term / Construction / Step / Flow levels?
2. Which exact part is still pending human judgment?
3. Which existing question and options govern that judgment?
4. After a decision, what changed in the scholar projection?
5. Which current objects carry explicit human-decision provenance, and which remain machine-derived?
6. Can the researcher inspect evidence without the UI inventing additional semantics?

Three interfaces therefore need to be frozen before the final renderer:

```text
A. scholar object ↔ existing review question
B. before ↔ after scholar diff
C. scholar object ↔ explicit decision provenance
```

---

# 1. Object ↔ review-question binding

## 1.1 Existing question system remains authoritative

Question wording, options, payloads, decision targets, and actions continue to come only from:

```text
workbench/question_presenter.py
existing ReviewJob/service submission path
```

`ScholarSourceProjection` must **not** duplicate:

```text
question text
radio options
decision payload construction
decision validation
```

The renderer resolves `question_id` against the existing question collection.

---

## 1.2 Extend top-level `review_facets[]`

The existing top-level facet record remains the canonical scholar-review bridge.

Each facet record must expose:

```json
{
  "facet_key": "stable deterministic key",
  "object_id": "primary scholar object",
  "related_object_ids": [],
  "facet": "source_supply",
  "status": "pending",
  "question_id": "existing question id or null",
  "decision_id": null,
  "action": null,
  "semantic_target": null,
  "semantic_key": {},
  "evidence": []
}
```

No new question schema is created.

### `facet_key`

Stable identity is derived from canonical semantic identity, not question wording or random UI state.

Use:

```text
object_id
+ facet
+ normalized semantic_target when present
+ otherwise stable semantic_key identity
```

Question IDs may disappear after resolution; `facet_key` must remain usable for before/after comparison when the semantic facet persists.

---

## 1.3 Primary object vs related objects

`object_id` is the primary source-facing location of the question.

`related_object_ids[]` exposes the other scholar objects directly governed by the same issue.

This prevents the renderer from traversing arbitrary graph structure to discover relevance.

### Required V1 mappings

#### Term meaning / boundary

```text
primary: exact Term occurrence
related: []
```

#### Source supply

When an exact source Term occurrence exists:

```text
primary: Term occurrence
related: corresponding Flow
```

Example:

```text
term:sifen:38:19-21  (章法)
↔ flow:sifen:38:章法
```

If no exact Term object exists but a source-supply Flow exists, Flow may be the primary object.

#### Quantity meaning

Primary remains the exact Construction/occurrence currently used by the question system.

Related Step IDs may be included only when the normalized semantic target and native Construction→Step relation identify them deterministically.

If not deterministic, leave `related_object_ids` empty. Do not guess.

#### Reviewed relation / source context

Related objects may be supplied only from canonical IDs already present in the reviewed graph or projection.

---

## 1.4 Renderer rule

A click on any object MUST find its review state only through:

```text
review_facets where
  object_id == clicked_id
  OR clicked_id in related_object_ids
```

If the resulting facet has:

```text
question_id != null
```

the renderer opens the exact existing question.

If:

```text
question_id == null
decision_id != null
```

the renderer shows the reviewed decision/history, not a fabricated new question.

The renderer never infers `source_supply` by walking:

```text
Flow → Step → Term → question
```

---

# 2. Explicit decision provenance on scholar objects

## 2.1 Purpose

A scholar must be able to distinguish:

```text
machine-derived current object
```

from:

```text
current object that carries explicit reviewed-decision provenance
```

without claiming more causality than the canonical graph records.

---

## 2.2 `decision_refs`

Term / Construction / Step / Flow objects may expose:

```json
"decision_refs": [
  {
    "decision_id": "D17",
    "action": "set_term_boundary",
    "basis": "explicit"
  }
]
```

Only emit a `decision_ref` when an existing canonical object or reviewed claim explicitly carries that decision identity.

Allowed sources include, where present:

### Term

```text
reviewed term-boundary / term-interpretation claim decision_id
candidate authorization_refs that are actual review decision IDs
```

### Construction

```text
candidate.attributes.decision_id
candidate.attributes.resegmentation_decision_id
other explicitly named reviewed-decision reference fields already emitted by the compiler
```

### Step / output

```text
event/value metadata explicitly carrying review decision IDs
reviewed quantity metadata with explicit decision refs
```

### Flow

```text
reviewed binding/import evidence explicitly carrying decision identity
```

Do **not** reconstruct provenance from:

```text
surface spelling
same source span
selection_reason prose
the fact that an object appeared after a decision
```

If no native decision identity is present:

```text
decision_refs = []
```

or omit the field.

---

## 2.3 Provenance is not transition causality

`decision_refs` means:

> this current canonical object explicitly carries this review decision identity.

It does **not** mean:

> this decision is the sole historical or computational cause of the object.

Transition causality is handled separately by ScholarSourceDiff.

---

# 3. ScholarSourceDiff/1

`ScholarSourceDiff/1` is a read-only comparison of **two ScholarSourceProjection snapshots**.

It is not another parser, semantic graph, or persisted truth.

Recommended API:

```python
diff_scholar_source(before_projection, after_projection, *, trigger=None)
```

It may live beside `annotation_projection.py` or in a tiny dedicated module, but it must consume projections only and import no parser/compiler/Domain-Kernel semantic logic.

---

## 3.1 Source precondition

Normal interaction diff requires the same focused source occurrence:

```text
source_id
unit_id
doc_id
text
```

If the focused source changes, either:

```text
raise ValueError("scholar_diff_source_changed")
```

or return one explicit source-change diagnostic.

Do not pretend two different source texts are an ordinary review transition.

A changed `reading_id` with identical source text must still be surfaced as source identity change unless explicitly allowed by the caller.

---

## 3.2 Trigger metadata

The caller may supply the exact action being previewed/applied:

```json
{
  "trigger": {
    "decision_id": "D17",
    "action": "set_term_boundary",
    "mode": "trial"
  }
}
```

Allowed modes:

```text
trial
saved
retracted
management
context
```

This metadata means only:

> this before→after transition was observed while applying this trigger.

The diff must not infer a trigger from changed objects.

---

## 3.3 Stable comparison surface

Diff must compare scholar-semantic fields, not volatile native IDs.

Ignore changes that exist only in:

```text
value_id
event_id
call_id
opaque definition IDs
hashes
cache paths
evidence ordering
question wording
```

Retain changes in:

### Terms

```text
presence
display_level
children
composition_alternatives
semantic candidate expression/status/rule
reviewed claims / explicit decision refs
```

### Constructions

```text
presence
construction_kind
public_kind
parse_status
slots and their source spans
explicit decision refs
```

### Steps

```text
presence
operation
construction_ids
input roles and scholar references
output ports/labels/quantity semantics
judgment
explicit decision refs
```

### Flows

```text
presence
formal
consumer Step IDs
status
producer source stable identity
selected/output port
explicit decision refs
```

### Review facets

Identity:

```text
facet_key
```

Compare:

```text
presence
primary object
related objects
status
question_id presence/absence
decision_id
action
```

Question IDs themselves are references, not semantic prose.

### Links

Identity remains:

```text
relation + from_id + to_id + role + ordinal
```

Compare basis if it changes.

---

## 3.4 Diff output

```json
{
  "schema": "ScholarSourceDiff/1",
  "source": {
    "source_id": "sifen",
    "unit_id": "sifen:section:38",
    "doc_id": "sifen:38"
  },
  "trigger": null,
  "layers": {
    "terms": {
      "added": [],
      "removed": [],
      "changed": []
    },
    "constructions": {
      "added": [],
      "removed": [],
      "changed": []
    },
    "steps": {
      "added": [],
      "removed": [],
      "changed": []
    },
    "flows": {
      "added": [],
      "removed": [],
      "changed": []
    },
    "review_facets": {
      "added": [],
      "removed": [],
      "changed": []
    },
    "links": {
      "added": [],
      "removed": [],
      "changed": []
    }
  },
  "summary": {
    "semantic_change_count": 0
  }
}
```

For object layers:

```json
{
  "id": "flow:sifen:38:章法",
  "changed_fields": [
    {
      "path": "status",
      "before": "unresolved_source",
      "after": "linked_source"
    }
  ]
}
```

For facets/links, use their canonical identity key.

No natural-language historical interpretation is generated by the diff.

---

# 4. Required interaction behavior

## 4.1 Attach §15 to Proc.38

Before:

```text
章法 Flow = unresolved_source
章法 source_supply = pending
```

After:

```text
章法 Flow = linked_source
producer_source = §15
章法 source_supply pending facet disappears/resolves
章法 term_meaning remains pending
```

Scholar diff MUST show:

```text
Terms: no semantic object change
Constructions: no semantic object change
Steps: no semantic object change
Flow 章法: changed
Review facet source_supply: removed/resolved
```

Native value/event ID shifts must not appear.

---

## 4.2 Boundary-enabled grammar/Step

Use the existing B1-style synthetic case.

Before:

```text
operand occurrence not admitted / construction unresolved
no multiply Step
```

After exact reviewed boundary:

```text
Term occurrence added/reviewed
Multiply Construction becomes available
Multiply Step becomes available
```

Diff records these additions.

If the resulting construction/event explicitly carries the boundary decision ID, `decision_refs` reflects it.

If it does not, the diff may still say:

```text
appeared in transition triggered by D17
```

but the snapshot must not invent `decision_refs`.

---

## 4.3 Runtime value permission

Before:

```text
Flow status = unresolved_source
source_supply facet = pending
```

After `declare_parameter`:

```text
Flow status = runtime_value_permitted
source_supply facet = reviewed
```

No historical-source label is introduced.

---

# 5. Renderer interaction boundary

After this contract passes, the final renderer may do only:

```text
render ScholarSourceProjection objects
render ScholarSourceDiff changes
look up existing QuestionPresenter question by question_id
submit the selected existing option through existing service
refresh projection + diff
```

It must not:

```text
create question wording
create options/actions
guess related objects
guess decision provenance
compare raw graph IDs
infer historical source categories
perform source parsing
```

---

# 6. Compatibility

The current `project_annotations()` remains a legacy Inspector adapter derived from `ScholarSourceProjection/1`.

Do not make it a second interaction truth.

The final renderer should consume `ScholarSourceProjection/1` directly.

R1–R4 remain Evidence/Inspection.

---

# 7. Renderer gate

Do not start the final layered renderer until all of the following pass:

1. fixed-expression Construction projection;
2. compatible-producer Flow ambiguity fix;
3. source-supply Term↔Flow `related_object_ids`;
4. deterministic `facet_key`;
5. decision provenance projection from explicit native refs only;
6. deterministic `ScholarSourceDiff/1`;
7. §15 context diff regression;
8. B1 boundary-enabled Term→Construction→Step diff regression;
9. runtime-value diff regression;
10. existing Proc.38 full golden and §15 context invariant remain unchanged.

Once these pass, the renderer can be treated as presentation/interaction work rather than another semantic-design phase.
