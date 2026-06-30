# Procedure IR Experiment Archive

These scripts are archived experiments from the Cullen/Sifen Procedure IR exploration.
They are not part of the current stable debugging surface.

Current reason for archiving:
- `align-sifen-clauses.mjs` produced useful diagnostics, but simple Proc-level cases can still shift alignment when a source title phrase appears before the operative clauses.
- `audit-sifen-candidate-evidence.mjs` introduced a quantitative scoring idea, but its current scoring can conflate broad reusable schemas with weak evidence.
- `profile-sifen-corpus.mjs` and `discover-sifen-templates.mjs` remain useful exploratory tools, but they depend on chunk quality and should be rerun only after the chunk schema is stable.
- `pilot-sifen-proc35-*` scripts were single-Proc trials, useful as proof-of-concept notes but not stable pipeline stages.
- `generate-phase2a-*` scripts belong to the earlier Phase 2A pilot and are not part of the current chunk-schema stabilization work.

Do not treat outputs from these scripts as gold or as stable algorithm reconstruction evidence.
If one of these ideas becomes part of the main workflow, promote it back deliberately with a fresh script name and audit.
