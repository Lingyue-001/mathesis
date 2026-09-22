# Precompiled Scholar Sandbox Scenario for Han Si-fen li §38

## Purpose

Publish a conference-safe, static interactive demonstration of the current Han Si-fen li §38 Inspector at `/mathesis/inspector/`.  The page must show real changes to the annotation projection and Procedure Model after a limited set of review confirmations, without exposing a Python backend in the browser.

The presentation is a finite, precompiled demonstration.  It is not a browser implementation of parsing, compilation, execution, semantic closure, or review adjudication.

## Scope and invariants

The implementation may change the static-export pipeline, static Inspector JavaScript, static Inspector tests, and committed static data.  It must preserve the current local research Inspector and all parser, compiler, Domain Kernel, Program IR, executor, review, ScholarSourceProjection, and Procedure Model semantics.

Each display state must be the complete result of replaying an actual `ReviewJob` through the existing Python compiler.  The browser may select among those complete exported states only.  It must never calculate a successor model, change graph facts, generate a decision, call `/api/adjudication/*`, or describe a local draft as compiled.

The existing local-draft features remain available for choices outside the demonstration path.  They continue to be browser-local, importable/exportable, retractable, and visibly marked `Draft review · not recompiled`.

## Scenario data contract

Add a deterministic outer document with schema `ScholarSandboxScenario/1`.  It is stored at the existing committed static data location, replacing the single baseline snapshot file used by `/inspector/`.

The document contains:

- `schema`: `ScholarSandboxScenario/1`.
- `scenario_id`: SHA-256 of the canonical document without `scenario_id`.
- `source`: identity for Han Si-fen li §38.
- `initial_state_id`: `baseline`.
- `states`: a mapping of state ID to a complete `ScholarSandboxSnapshot/1`.
- `transitions`: a finite list of permitted successor transitions.

A transition contains a stable transition ID, its source and destination state IDs, the exact exported question ID and option ID that enable it, a human-readable record of the decision, and provenance identifying the Python compiler export.  It does not contain a browser-executable rule.

Every embedded state remains valid `ScholarSandboxSnapshot/1` data: source, projection, renderer presentation, questions and options, reviewed decisions/status/history, ProcedureModel, selected-object presentation data, corpus data, and labels.  Snapshot IDs keep their existing canonical-hash rule.  Scenario and snapshot IDs are deterministic across fresh equivalent exports.

## Fixed §38 path

The public scenario contains exactly this linear, precompiled path:

1. `baseline` — current accepted §38 analysis with no demonstration decision.
2. `ordinal-reviewed` — submit the existing one-based ordinal decision for `入蔀年`.
3. `zhang-yue-attached` — submit the exact parameter declaration attachment for `章月` from §16.
4. `zhang-fa-attached` — submit the exact parameter declaration attachment for `章法` from §15.

The exporter discovers the relevant question and option from current recorded semantic metadata and exact document identity; it does not depend on fragile UI labels or hard-coded option IDs.  It applies the chosen option with the existing review-decision and compiler path.  It may normalize scenario-only decision IDs and timestamps before replay solely to make the export deterministic; the normalized records must still be valid ordinary review decisions accepted by the existing compiler.

No §38-specific semantic rule may be added.  If a state leaves `積月`, `閏餘`, or any other interpretation unresolved, the exported state must show that unresolved result exactly.

## Exporter behavior

Extend the existing `workbench/sandbox_snapshot.py` export path rather than creating a second analysis pipeline.  Factor its response-to-snapshot conversion so the baseline and every successor are built from the same current compiler response.

The scenario exporter starts from a disposable in-memory ReviewJob/session for §38.  It applies each transition using existing decision/replay/compiler functions and exports the returned response.  It must not modify the tracked public ReviewJob, canonical source data, `.cache`, or the committed corpus data.

The output is written to a tracked static data path already copied by Eleventy.  Public data stays human-readable UTF-8 JSON and uses relative/base-aware asset loading.

## Static Inspector behavior

On load, the static Inspector accepts `ScholarSandboxScenario/1`, selects `initial_state_id`, and renders its embedded snapshot through the existing source annotation and Procedure Model renderers.

For a question/option that is an outgoing transition from the active state, the primary action is `Confirm`.  Confirm atomically replaces the active complete snapshot with the named successor, re-renders source, graph, selected-object details, questions, review history, and the workspace’s source-derived controls, and records a concise state note identifying the precompiled successor.  Selection is retained only when its object/facet/question IDs exist in the successor; otherwise it is cleared safely.

The page offers `Reset demonstration` to return to the baseline state.  Reset only changes in-memory scenario state; it does not clear local drafts.

For all other option selections, current draft controls remain.  Their copy continues to say `Save as draft` or `Add context as draft` as applicable.  There is no fake Execute, compile, re-run, backend request, or claim that an unsupported draft changed the model.

The existing review history for each state is displayed as exported data.  A confirmed transition therefore makes the resulting real decision and its compiler-derived status/history visible instead of removing the question merely because the browser changed a local control.

## Selected Source Object presentation

Scenario snapshots carry the current Python-authored selected-object presentation data, including the fixed four analysis layers and cross-layer references.  The static renderer consumes that presentation data rather than re-inferring relations from source strings.  This keeps public output aligned with the local Inspector’s canonical-ID-only relation traversal.

The static renderer keeps the current approved UI copy and layout.  The scenario feature adds only functional controls needed to distinguish a precompiled confirmation from an uncompiled local draft.

## Validation

Python tests must prove:

- the scenario export is deterministic and has valid scenario and state hashes;
- every successor equals a separately replayed and compiled ReviewJob response for the same recorded decisions;
- the transition sequence is baseline → ordinal → §16 `章月` attachment → §15 `章法` attachment;
- no exporter path edits the tracked public ReviewJob;
- unresolved semantic results remain unresolved where the generic Kernel has no registered relation;
- existing snapshot and local Inspector regression tests remain green.

Static browser tests, served from a production Eleventy `dist` build under `/mathesis/`, must prove:

- all CSS, JS, data and the Inspector route load without console errors;
- Annotated Source and Procedure Model render at the baseline and each successor;
- clicking a path option and `Confirm` switches to the matching precompiled successor and visibly updates source/model/history from exported data;
- `Reset demonstration` restores baseline;
- a non-path option saves as a browser-local draft, survives reload, and does not alter the active snapshot/model;
- import/export and Unicode term-boundary local drafts remain correct;
- no request targets `/api/adjudication/*`;
- 1440 px, 768 px, and 390 px have no page-level horizontal overflow; graph-only horizontal scrolling remains permitted.

The release check runs `NODE_ENV=production npm run build`, serves `dist` at a `/mathesis/` path, repeats static browser acceptance, and reruns the local Inspector interaction regression.  Only after those checks pass may the committed public snapshot replace the prior one and be pushed to `main` for the existing GitHub Pages deployment workflow.

## Out of scope

This change does not add new historical interpretations, generic semantic rules, direct browser compilation, server endpoints, live shared review records, or a replacement for the local research Inspector.  It does not restore `/adjudication/`, which was intentionally removed from public navigation.
