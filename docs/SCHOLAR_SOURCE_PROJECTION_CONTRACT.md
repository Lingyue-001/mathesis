# ScholarSourceProjection/1 — Contract revision 1.1

Status: final pre-renderer contract hardening.
Scope: read-only scholar projection only. No parser/compiler/executor/Domain Kernel semantic changes.

## 0. Purpose

`ScholarSourceProjection/1` is the single scholar-facing intermediate representation between canonical analysis/review data and the eventual source-annotation UI.

Scholar reading order is:

```text
Source text
→ Term / quantity expression
→ Construction / technical expression
→ Computational step (input → operation → output)
+ Flow / source context
```

Review is a facet overlay, never a fourth/fifth layer.

R1–R4 remain Inspection/Evidence views and are not scholar-facing hierarchy labels.

---

## 1. One focused source document per projection

A projection is always about **one current source document**.

Default focus:
- first `primary_document`.

Optional implementation API:
- `focus_doc_id` may select another document already present in the effective packet.

Top-level `source` identifies exactly that focused document.

### 1.1 What is source-local

The following arrays contain objects whose scholar-facing source occurrence is in the focused document only:

- `terms`
- `constructions`
- `steps`
- `review_facets`
- source-local cross-layer `links`

Context-document terms/constructions must **not** be mixed into the focused source's annotation stack.

### 1.2 What may cross documents

`flows[].producer_source` may identify a declaration/producer in another effective-packet document.

Example:

```text
focus = sifen:38
章法 consumer = §38
producer_source = sifen:15 "章法，十九"
```

This is exactly how external context appears in the §38 projection.

If the scholar opens §15 as the current source, generate a separate focused projection for §15.

### 1.3 Mixed-document events

A computational Step may be projected only when all of its source anchors belong to the focused document.

A mixed-document operation must be omitted and recorded as a projection diagnostic rather than visually assigned to one text.

---

## 2. Term layer admission

The Term layer is for domain-relevant terms / quantities, not every syntax node called `Term`.

A source occurrence in the focused document is admitted when at least one condition holds:

1. it has at least one Domain Kernel semantic candidate whose expression is not `unknown`;
2. it has an active/replayed reviewed term boundary or term interpretation;
3. it fills a `Term` slot in a **non-Heading** selected construction;
4. it is a direct/recursive child required to preserve the ordered composition structure of an admitted Term.

This means a computationally used but semantically unknown occurrence can still appear.

### 2.1 Heading slots are not automatically terms

A `Heading` construction's `marker` / `target` slots do not become scholar Term objects merely because syntax represents them as `Term`.

For Proc.38:

```text
推
天正術
```

remain visible inside the `推天正術` Construction, but do not become Layer-1 Term objects unless independent domain evidence or a reviewed term boundary later justifies them.

### 2.2 Domain-bearing non-slot occurrences remain terms

An occurrence with real Domain Kernel semantic candidates may appear even if it is not a selected construction operand.

For Proc.38 this includes the `歲` and `閏` occurrences in `其歲有閏`.

### 2.3 Components

Composition components are retained as `display_level = component`.

Default source UI shows maximal occurrences first; components appear when the term composition is expanded.

Example:

```text
入蔀年             maximal
├ 入              component
├ 蔀              component
└ 年              component
```

Nested candidates such as `蔀年` may also remain component occurrences when they are canonical Domain Kernel nodes.

### 2.4 Unknown-only Kernel region

A Kernel occurrence whose only semantic expression is `unknown` is not sufficient by itself for Layer-1 admission.

It may still be admitted through a reviewed boundary or a non-Heading computational Term slot.

---

## 3. Term composition and alternatives

Ordered composition comes only from canonical Domain Kernel `child_ids`.

For every candidate, map its ordered child candidate IDs to source-occurrence Term IDs.

`composition_alternatives` preserves distinct ordered occurrence sequences.

`children` may be filled only if all relevant alternatives reduce to the same ordered Term-ID sequence; otherwise:

```text
children = []
composition_alternatives = [ ... distinct alternatives ... ]
```

Semantic alternatives remain unranked. Serialization order exists only for deterministic output.

Stable comparison order for `semantic_candidates`:

```text
(rule_id or "", canonical expression string)
```

This is not a scholarly ranking.

---

## 4. Construction layer

Construction objects come only from existing selected syntax/construction IR or existing fixed-expression candidates.

The scholar projector does not maintain a second whitelist of construction kinds.

`public_kind` is read from the canonical syntax node.

No source regex / string re-parsing is permitted here.

A Heading construction remains a Construction even though its slots may not be Term-layer objects.

---

## 5. Computational Step layer

One real source-linked core operation event = one Step core.

V1 core exclusions remain:

```text
literal
input
alias
unsupported
```

Do not fuse multiple arithmetic events merely for visual convenience.

UI may group Steps later, but the projection preserves event identity.

Naming/alias events are not arithmetic Steps. When native data-flow proves that they name an operation output, project the label onto that Step output.

Example:

```text
divmod.quotient  → 積月
divmod.remainder → 閏餘
```

---

## 6. Flow layer

Flow describes current supply/connectivity, not historical provenance ontology.

Allowed V1 statuses:

```text
linked_source
unresolved_source
ambiguous_source
runtime_value_permitted
local_produced_value
```

K3-only concepts such as “historical external source / historical upstream quantity / system parameter” must not be invented here.

A Flow belongs in the focused projection when its consumer is represented by a focused-source Step.

Its producer may be another document and is represented through `producer_source`.

---

## 7. Review facets

Review remains orthogonal to Term / Construction / Step / Flow.

Facet families include:

```text
term_boundary
term_meaning
quantity_meaning
source_supply
source_context
reviewed_relation
```

The projector must match decisions using normalized semantic target / exact occurrence / consumer / branch information.

It must never use only surface spelling or facet name to mark another occurrence reviewed.

Confirming one facet does not change sibling facets.

---

## 8. Canonical cross-layer links

Scholar UI must not invent cross-layer links.

Current link relations include:

```text
has_component
fills_slot
realizes
names_output
```

Flow already carries canonical ID references in `consumer_step_ids`, `producer_step_id`, and Step inputs' `flow_id`; duplicate Flow-link records are not required in V1.1.

### 8.1 Link identity and deduplication

The canonical identity of a link is:

```text
relation
from_id
to_id
role (if any)
ordinal (if any)
```

`basis` and `evidence` are not separate-link identity.

Therefore multiple semantic alternatives that support the same `has_component` relation must yield **one canonical link**.

Merge all unique evidence records into it.

If duplicate evidence paths provide different basis strengths:

```text
explicit > structurally_derived
```

Keep the strongest basis.

The canonical `projection["links"]` itself must already be deduplicated.
`stable_golden_view()` must not hide duplicate canonical links.

### 8.2 No dangling scholar links

Every `from_id` / `to_id` in `links` must point to an object present in the focused projection.

Because `推` and `天正術` are not Term objects in Proc.38, no `fills_slot` link may target them.

Their slot spans remain available inside the Heading construction itself.

---

## 9. Stable serialization for golden tests

Golden equality tests compare a deterministic semantic view, not volatile implementation IDs.

Stable view includes:

### Source
```text
source_id
unit_id
doc_id
reading_id
text
```

### Term
```text
id
span
surface
display_level
children
composition_alternatives
semantic_candidates:
  expression
  status
  rule_id
```

### Construction
```text
id
span
surface
construction_kind
public_kind
parse_status
slots:
  name
  surface
  span (when available)
```

### Step
```text
id
source_spans
operation
construction_ids
judgment (when present)
inputs (excluding volatile value IDs)
outputs (excluding volatile value IDs)
```

### Flow
```text
id
formal
consumer_step_ids
status
producer_step_id
producer_source stable source identity
selected_port
output_port
```

When `producer_source` is present, stable source identity is limited to:

```text
source_id
unit_id
doc_id
reading_id
sections
source_spans
basis
```

Do not freeze opaque `definition_id`, corpus hashes, filesystem path, or transient cache IDs in the golden.

### Facets
```text
object_id
facet
status
```

### Links
All canonical deduplicated semantic link fields except verbose evidence.

### Ordering

Stable view ordering is deterministic only; it is not a ranking:

- Terms: source start, then longer span first.
- Constructions: source start/end.
- Steps: source start/end/ID.
- Flows: first consumer-step source position.
- Facets: target source position, then object layer, then facet.
- Links: relation class, then from/to/role/ordinal.

---

## 10. Proc.38 expected focused projection

With no context and no human decisions:

```text
focus document: sifen:38

Terms:         19
Constructions:  8
Steps:          5
Flows:          3
Review facets:  7
Links:          26
Diagnostics:    0
```

The 19 terms deliberately exclude heading-only `推` and `天正術`.

The maximal/default-reading terms are:

```text
入蔀年
章月
章法
積月
閏餘
歲
閏
```

The remaining terms preserve the canonical composition components.

### 10.1 §15 context invariant

When §15 `章法，十九` is attached while focus remains §38:

- §38 Term / Construction / Step arrays remain identical to the no-context focused projection.
- No §15 term or construction is inserted into the §38 source stack.
- `flow:sifen:38:章法.status = linked_source`.
- its `producer_source` identifies `sifen:section:15`.
- `selected_port = result`.
- the §38 `source_supply` pending facet for `章法` disappears if the source is actually resolved.
- other independent §38 facets remain.

---

## 11. Projection diagnostics

Evidence insufficiency is not repaired in the projector.

Examples:

```text
slot_source_span_not_unique
event_construction_unlinked
flow_input_unlinked
selected_source_missing
cross_document_step_not_projectable
```

The projector emits a diagnostic and omits the unprovable assertion.

---

## 12. Exact authored golden policy

`proc38-full-golden-v1_1.json` is the full authored semantic expected output after applying this contract.

Required test:

```text
actual = project_scholar_source(...)
stable = stable_golden_view(actual)
assert stable == fixture["expected"]
```

No subset assertion and no “extra objects allowed” policy for Proc.38.

The projector may contain additional verbose `evidence`, native IDs, or debug traces outside stable view, but it may not add/remove scholar objects or semantic relationships without intentionally updating this authored contract/golden.

A context-specific second fixture tests the §15 invariant separately.

---

## 13. Implementation boundary

This hardening pass should stay in the existing scholar projection/test/docs path.

Do not change semantic behavior in:

```text
analysis_parser/construction_ir.py
analysis_parser/scoped.py
analysis_parser/program_ir.py
adjudication/compiler.py
analysis_parser/execution.py
Domain Kernel semantic rules
```

Do not start the final visual renderer until:

1. canonical links are deduplicated;
2. term admission follows §2;
3. projection is focus-document scoped;
4. no-context Proc.38 has exact full-golden equality;
5. §15 context invariant passes.

After those conditions pass, the projection is ready to become the sole data source for the layered annotation UI.
