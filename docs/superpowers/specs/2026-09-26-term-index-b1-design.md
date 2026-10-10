# Term Index B1 Design

**Status:** Approved architecture for B1 implementation.

## Purpose and boundary

B1 adds a stable, read-only `TermIndex/1` data boundary. It implements only a
testable Python builder and deterministic JSON export. It does not connect the
Inspector, a public/static page, a parser, a compiler, the Domain Kernel, a
review store, or corpus writeback.

The sole input is one or more valid `ScholarSourceProjection/1` mappings.
`workbench.term_index` must not import or query raw parser structures, compiler
graphs, Domain Kernel internals, review sessions, corpus files, or R1--R4.

## Public interface

```python
build_term_index(projections) -> dict
serialize_term_index(index) -> str
export_term_index(index, path) -> Path
```

`build_term_index` is pure: it does not mutate its inputs or write files.
`serialize_term_index` creates deterministic readable UTF-8 JSON. Only the
explicit `export_term_index` call writes, to the caller-provided path.

## Identity and source admission

Each input Projection identifies one source:

```text
projection_source_identity = source_id + unit_id + doc_id + reading_id
```

Each Term occurrence identifies one exact lexical occurrence:

```text
occurrence_identity = projection_source_identity + Unicode [start,end)
```

`text_sha256` remains copied freshness/version metadata, not identity. A build
rejects duplicate `projection_source_identity` values. This prevents two
contextual snapshots of the same source from becoming falsely separate corpus
instances, even if their Term lists differ.

## TermIndex/1 shape

The result has `schema: "TermIndex/1"`, a sorted list of admitted Projection
sources, and a sorted list of exact-form entries. An entry is grouped only by
exact Unicode `surface`, with no normalization, lemma, variant matching, or
semantic promotion.

Each entry contains:

```text
surface
occurrence_classification: maximal | component | both
counts:
  maximal_occurrences
  component_occurrences
  appears_in_compounds
occurrences
direct_parent_occurrences
compound_ancestor_occurrences
```

Each occurrence retains its full identity, source anchor, exact surface,
Projection `display_level`, snapshot-local Projection Term ID, and copied
occurrence-local semantic material. The latter is only material already
exposed by the Projection: candidates and their status axes, reviewed claims,
semantic and derived assertions, semantic conflicts, decision references,
review facets, and candidate evidence. B1 does not interpret these values or
create an entry-level epistemic status.

`maximal` and `component` are occurrence roles copied from the Projection.
`both` is an entry aggregate only: it means that the entry contains at least
one occurrence of each role.

## Recorded composition only

For every Projection, B1 constructs directed child-to-parent links only from
the union of each Term's `children` and `composition_alternatives`. A parent
is de-duplicated even when several alternatives name the same child.

For an entry, `direct_parent_occurrences` contains its distinct immediate
recorded parents. `compound_ancestor_occurrences` is the recursive transitive
closure through those recorded links; therefore a component can show both a
near compound and every recorded outer compound that contains it. `appears_in_compounds`
is the cardinality of this ancestor set. No relation may be inferred from
substring matching, matching surfaces, adjacency, or text containment.

If a recorded composition link names a non-admitted Term ID, the Projection is
invalid for this consumer and the builder fails explicitly. It must never
invent the missing occurrence or relation.

## Validation and determinism

The builder validates the input schema, a list of Term rows, required
source/anchor identity fields, Unicode code-point half-open spans, matching
source/anchor document-reading identities, admitted roles, unique source
identities, and recorded composition references.
Output ordering is deterministic by exact Unicode surface and complete identity.
Serialization uses readable UTF-8 and stable key ordering. Export tests use a
temporary directory; no source, corpus, review, or cache artifact is written.

## B1 test matrix

Synthetic tests establish schema validation, exact-form grouping, repeated
surfaces with distinct identities, `maximal`/`component`/entry-level `both`,
direct and recursive recorded composition, de-duplication across alternatives,
status preservation, determinism, explicit export, and input immutability.

Real-projection regression is fixed to these three existing snapshots only:

```text
Case A: build_term_index([§38 no-context, §39])
Case B: build_term_index([§38 + §15 context, §39])
Negative: build_term_index([§38 no-context, §38 + §15 context])
          -> reject duplicate projection_source_identity
```

The matrix verifies cross-source aggregation and prevents duplicate contextual
snapshots from being treated as two corpus sources. It is not a full-corpus
scan, unseen-corpus evaluation, or K4 claim.

## Explicit exclusions

B1 adds no Inspector integration, public/static interface, glossary,
normalization, ranking, confidence score, semantic promotion, automatic Kernel
or parser promotion, reading selection, unified authorization gate, K3 cleanup,
K4 evaluation, parser, executor, review store, or corpus modification.
