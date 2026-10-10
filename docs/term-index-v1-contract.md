# Term Index v1 Contract

Status: **B1 contract; the read-only Python builder and JSON export are implemented, with no UI integration.**

This contract freezes what a future Term Index may consume from the current K2 boundary. It does not add parser recognition, a glossary, an ontology, a review workflow, or an execution path.

## 1. Sole canonical input

```text
Term Index v1
    ↑
ScholarSourceProjection/1
```

The Index reads only a valid `ScholarSourceProjection/1` snapshot. It must not read, combine, or use as a fallback:

```text
analysis_parser.lexical.TERMS
pipeline.UNITS
ROLE_ALIASES
R1/R2 internal structures
raw Domain Kernel bundles
raw reviewed graph
raw review-session records
```

R1--R4 remain Inspection / Evidence. They do not become Index canonical data. If a future Index needs a fact not exposed by the Projection, that is a Projection-contract question; it is not permission for the Index to reach behind the boundary.

## 2. Projection-source identity, occurrence identity, and admission

Every input Projection has one logical source identity:

```text
projection_source_identity = source_id + unit_id + doc_id + reading_id
```

Every admitted Term occurrence has the more specific identity:

```text
occurrence_identity = projection_source_identity + Unicode [start,end)
```

The source identity comes from `projection.source`; the exact Unicode span and surface come from the individual projected Term. `text_sha256` is version/freshness metadata only and is not part of either logical identity. One Index build must reject duplicate `projection_source_identity` inputs, rather than treating alternate snapshots of one source as separate corpus material. The Projection Term ID may be retained as its snapshot-local reference, but surface spelling is never a scholarly occurrence identity.

All admitted Projection Terms are indexed. This includes a maximal term and the component spans that the Projection has retained for recorded composition. The Index does not add a span because it looks technical, is a substring, occurs adjacent to another string, or appears in an external lexicon.

## 3. Occurrence role and exact-form entries

Each Index occurrence retains the Projection's role:

```text
maximal
component
```

`both` is an entry-level aggregate label only. An exact-form entry is `both` when its distinct admitted occurrences include at least one `maximal` and at least one `component` occurrence. It is never assigned to one occurrence.

An Index entry groups by exact Unicode `surface` form only. It does not normalize traditional/simplified forms, variants, lemma, morphology, or near-matches. Thus `積月`, `积月`, `月`, and `月份` remain separate entries.

For every entry, v1 reports three separate counts over distinct occurrence identities:

```text
maximal_occurrences
component_occurrences
appears_in_compounds
```

Each entry records two distinct composition relations, both keyed by distinct Term occurrence identities:

```text
direct_parent_occurrences
compound_ancestor_occurrences
```

`direct_parent_occurrences` contains the recorded immediate parents whose `children` or `composition_alternatives` contains an occurrence in the entry. `compound_ancestor_occurrences` is the transitive closure of that same recorded parent/child relation: it includes direct parents and every recorded outer parent reachable through those links. The Index never creates a link from substring, surface containment, adjacency, or any other string inference. A parent is counted once even when multiple semantic or composition alternatives contain that child.

`appears_in_compounds` is the number of distinct `compound_ancestor_occurrences`, not merely the immediate-parent count. A composition relation is evidence of recorded construction only; it is not a statement that the child has one global lexical meaning.

## 4. Meaning, status, and facts stay local

The Index may display each occurrence's existing Projection material, including semantic candidates, reviewed claims, semantic/derived assertions and conflicts, explicit decision references, review facets, and source-linked composition evidence. Candidate-level status and the existing Kernel axes remain attached to the occurrence and candidate that expose them:

```text
status
support_status
constraint_status
authorization_status
```

The Index must not synthesize a single confidence score or a new status taxonomy. A status such as `derived` or `authorized` is displayed only when the Projection itself exposes it in the relevant occurrence-local record; it is never inferred from a matching surface or from another occurrence.

Likewise, a scoped numerical statement belongs to the Projection occurrence, its source identity, and the recorded construction/flow evidence. For example, a future display may distinguish the lexical component `蔀`, the term `蔀月`, and a source-scoped fact about a particular `蔀月`; it must not collapse them into an unqualified dictionary assertion.

## 5. Read-only boundary and exclusions

Term Index v1 is read-only. It must not write to, promote into, or otherwise change:

```text
Domain Kernel
parser lexicon
compiler semantics
review store
source data
```

The following remain out of scope before or within Term Index v1:

```text
reading-selection workflow
unified authorization gate
legacy hardcode cleanup
ontology learning
automatic promotion into Kernel
unseen-corpus evaluation
new parser
new executor
new review store
lemma/variant normalization
candidate ranking
global semantic promotion
```

Any future “Promote to Kernel” action is a separate, explicit scholarly workflow. It is not an Index side effect.

## 6. A0 baseline evidence

The following audit-only evidence records the preflight starting point; it is not a gold standard and does not replace the existing fixtures.

- `.cache/term-index-preflight/2026-09-26-baseline.json`: main and working HEAD commits, initial working-tree status, protected-file SHA-256 values, and the initial test command/result.
- `.cache/term-index-preflight/proc38.no-context.json`: current §38 Projection.
- `.cache/term-index-preflight/proc38.with-section15.json`: current §38 + §15 Projection.
- `.cache/term-index-preflight/proc39.json`: current §39 Projection.

## 7. Gate A

### 2026-09-26 evaluation

**Result: PASS.**

1. The consumer ledger and generated reference record the three implemented
   K2 capabilities; the additive K2 documentation notes use the same status.
2. `reading_selection` remains planned; unified authorization and legacy
   cleanup remain K3; unseen-corpus evaluation remains K4.
3. Sections 1--3 fix the canonical input, full occurrence identity, all-span
   admission, separate maximal/component counts, and recorded-only compound
   membership.
4. Fresh verification ran 60 selected ScholarSourceProjection, Domain Kernel,
   term-claim, and semantic-closure tests with `OK`; the generated-document
   check also passed.
5. The protected-file comparison reports 42 protected semantic files changed:
   `[]`. The tracked diff contains only allowed manifest/documentation paths
   plus pre-existing user changes; no corpus/source or semantic implementation
   change is present. Audit evidence remains ignored under
   `.cache/term-index-preflight/`.

Gate A closes the K2-to-Term-Index preparation stage only. It does not begin
Term Index implementation or K3.

Term Index implementation may begin only when this checklist has a recorded pass in the 2026-09-26 preflight addendum:

1. consumer ledger and K2 documentation agree on implemented capabilities;
2. reading selection, unified authorization, legacy cleanup, and unseen evaluation have explicit retained scope labels;
3. `ScholarSourceProjection/1` is the only canonical Index input;
4. full source-and-span occurrence identity is retained;
5. all admitted lexical forms are indexed with separate maximal/component counts and recorded-only compound membership;
6. the §38, §38 + §15, §39, Domain Kernel, term-claim, semantic-closure, and ScholarSourceProjection regressions retain current behavior; and
7. the preflight diff contains only manifest, documentation, contract, and audit evidence changes, with no corpus/source or semantic implementation edits.

Until all seven conditions have fresh evidence, this contract authorizes no Term Index code and no K3 work.
