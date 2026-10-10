# Term Index Inspector Integration Design

**Status:** Approved design for the local Inspector integration stage.

## Purpose and scope

This stage adds a third, local Inspector view named `Term Index`. It displays a
baseline corpus-level `TermIndex/1` and does not create a public/static page.
It is a read-only consumer of the B1 contract: it neither changes Term Index
aggregation nor adds parser, compiler, Kernel, corpus, or review semantics.

The component is deliberately corpus-capable. Its canonical interface is:

```text
term_index_component(TermIndex/1)
```

The component must not assume that its index came from the current Inspector
source or from one Projection. The first controller happens to supply a
corpus-level index assembled from many Projections; a later corpus source can
therefore use the same component unchanged.

## Baseline corpus projection scope

The v1 corpus index includes every registered source unit that has a current,
non-stale effective corpus-review state and can generate a Projection. The
collector enumerates registered sources, reads their effective units, and for
each unique `source_id + unit_id + doc_id + reading_id` generates an in-memory,
baseline `ScholarSourceProjection/1`. It then makes one call to
`build_term_index(projections)`.

The collector must not use the Inspector's currently selected source as its
scope. It must not select, merge, or create saved ReviewJobs, and it must not
combine review branches. Existing code has no unique corpus-level canonical
reviewed-state resolver: the current job resolver is selection-local, chooses
the newest matching job, and creates a job when none exists. Therefore saved
reviewed-state corpus integration is explicitly deferred to a later, separate
stage.

Each included unit is identified and versioned in the cache key by its current
effective corpus identity plus source/effective freshness metadata. The key
must include source ID, effective unit ID, source span/reading identity, and a
fingerprint derived from the current effective corpus-review state (including
its revision/source version). It also includes a producer identity: the
existing parser/runtime identity plus a deterministic fingerprint of every
Python/JSON file beneath the active analysis, adjudication, Kernel,
source-adapter, workbench, and configuration producer roots. A change to
either the admitted corpus state or those producers invalidates the session
cache automatically. Inspector source selection alone does not invalidate it.

Registered sources without a current effective state are visibly reported as
unavailable and are not silently represented as included. Failure to project
an otherwise admitted effective unit fails the collection rather than presenting
an incomplete result as a complete corpus index.

## Components and data flow

```text
registered current-effective corpus units
  -> read-only baseline Projection collector
  -> build_term_index(all collected ScholarSourceProjection/1 values)
  -> session-only cached TermIndex/1
  -> term_index_component(TermIndex/1)
  -> navigation identity + copied source anchor event
  -> Inspector shell
```

`workbench.term_index` remains the B1 pure builder and receives only
Projections. A separate controller-bound collector may read the existing
registry/effective corpus state and invoke the existing in-memory Projection
path. It does not become an alternate parser/compiler or a second semantic
model.

The component receives only `TermIndex/1` plus normal component lifecycle
parameters such as a Streamlit key. It never reads Projection, raw corpus,
Annotated Source state, review state, or a ReviewJob. It emits at most an
opaque navigation record containing one occurrence's complete identity and
copied `source_anchor`.

## Local Inspector behavior

The top-level Inspector selector offers `Term Index` alongside `Annotated
Source` and `Procedure Model`. The Term Index branch is selected before source
selection, ReviewJob resolution/creation, compilation, and the source-panel
7:3 layout. It is read-only and has no review controls, semantic recompilation,
JSON persistence, or export action.

The component provides:

- literal Unicode surface-form substring filtering;
- `All`, `Maximal`, `Component`, and `Both` entry filters;
- deterministic entry list ordering from `TermIndex/1`, with optional
  maximal-first default presentation that never hides component-only entries;
- selected-entry detail with the three counts, direct parent occurrences,
  compound ancestor occurrences, and all source-distinct occurrences;
- occurrence-local candidates, statuses/axes, claims, assertions, conflicts,
  decision references, facets, and evidence exactly as carried by `TermIndex/1`.

An occurrence click does not manipulate Inspector state directly. Because the
independent view has no selected source Projection, the shell records/displays
its navigation target and source identity only. It must not implicitly select a
source, resolve/create/open a ReviewJob, or write review data. An explicit
source-opening workflow is deferred.

## Error handling and cache lifecycle

The collector produces a structured read-only result containing the index,
included-source/unit summary, deterministic input fingerprint, and explicit
unavailable-source reasons. The shell caches this result in Streamlit session
state only. If the fingerprint changes, it rebuilds before rendering; an
explicit refresh discards only the session cache and rebuilds from the same
read-only inputs.

If no current effective units are available, or an admitted unit fails to
project, the Term Index view reports the condition and does not render a
partial corpus result as complete. Component input with a schema other than
`TermIndex/1` is rejected locally and cannot trigger fallback reads.

## Acceptance criteria

1. The local Inspector exposes a third `Term Index` view; no public/static
   page or static data artifact is added.
2. Its component accepts a complete synthetic multi-source `TermIndex/1`
   without access to Projection/raw corpus/review inputs, and the same code
   supports a future corpus-level index unchanged.
3. `All`, `Maximal`, `Component`, and `Both` filters retain component-only
   forms as first-class browseable entries; exact Unicode search does not
   normalize or infer forms.
4. The displayed entry details preserve B1 counts, direct/ancestor relations,
   occurrence identity, and occurrence-local semantic material without any
   entry-level epistemic status.
5. The baseline collector assembles all available current-effective units,
   de-duplicates Projection source identity before B1 ingestion, and does not
   depend on the current Inspector source selection or job.
6. Changing an included effective-unit identity/freshness fingerprint or an
   analysis/Kernel/Projection/TermIndex producer identity rebuilds the session
   cache; changing only current Inspector selection does not.
7. Collection never creates or mutates ReviewJobs, corpus-review records,
   parser/compiler/Kernel data, or source data. Missing/stale sources are
   explicit; admitted-unit projection failure is fail-closed.
8. Navigation target display creates no source selection, job resolution,
   ReviewJob write, or source switch.
9. Existing B1, ScholarSourceProjection, semantic-closure, and Inspector
   review-panel tests remain green.

## Deferred boundaries

This stage does not change the `TermIndex/1` contract, add corpus-level
reviewed-state selection, normalize variants/lemmas, rank candidates, promote
terms, write to Kernel/parser/review state, enter K3/K4, change corpus/parser/
compiler/Kernel semantics, or build a public/static page. Corpus reviewed-state
integration and explicit cross-source Inspector opening are separate future
decisions.
