# M2 Scholar Adjudication Core evidence

This file is the M2 execution supplement to the requirements matrix. It records
actual test identifiers and commands; it does not claim M3 UI work, M4 primitive
families, comparison, or human-use measurements.

## M2 command and result

```text
python -X utf8 -B -m unittest discover -s tests/adjudication -v
28 tests: OK
```

The command includes a real canonical procedure replay from
`source_adapters.corpus.build_source_packet('.', 'sifen-3-5')`. It starts with
the ordinary automatic v3.1 compile, records two `scripted_fixture` decisions,
and recompiles through `ProgramIndex → link_entry → lower_linked`.

| Requirement IDs | Actual test IDs |
|---|---|
| D01.013–D01.018 | `test_audits.TestAudits.*`; `test_real_procedure.TestRealProcedure.test_H20_H40_real_replay_is_closed_but_execution_is_separate`; `test_validation_metrics.TestValidationMetrics.test_H39_partial_graph_is_exportable_but_not_complete` |
| D02.004–D02.010 | `test_acceptance_core.TestAcceptanceCore.test_H05_H13_manual_segmentation_and_known_structure_use_existing_lowerer`; `test_H06_manual_node_can_have_two_attested_spans`; `test_H07_scope_changes_program_frame_before_linking`; `test_H09_scope_parent_cycle_is_rejected`; `test_H10_linker_obeys_verified_producer_port_constraint` |
| D04.001–D04.006 | `test_session_replay.TestSessionReplay.test_H01_versions_are_separate_from_sourcepacket`; `test_H02_bad_source_anchor_is_stale`; `test_acceptance_core.TestAcceptanceCore.test_H03_same_quote_has_distinct_stable_source_address` |
| D04.007–D04.013 | `test_session_replay.TestSessionReplay.test_H17_replay_is_deterministic`; `test_H18_conflicting_active_slot_requires_resolution`; `test_H19_retract_restores_effective_gap_and_stales_dependent`; `test_branch_isolated_from_main` |
| D04.014–D04.021 | `test_real_procedure.TestRealProcedure.test_H01_empty_review_reuses_automatic_compiler`; `test_H05_H13_manual_segmentation_and_known_structure_use_existing_lowerer`; `test_H10_linker_obeys_verified_producer_port_constraint`; `test_H43_metadata_is_emitted_with_decision_provenance` |
| D04.022–D04.027 | `test_session_replay.TestSessionReplay.test_H17_replay_is_deterministic`; `test_resegmentation_stales_overlapping_downstream_decision`; `test_H16_context_attachment_stales_prior_binding`; `test_H09_scope_parent_cycle_is_rejected` |
| D04.028–D04.029 | `test_real_procedure.TestRealProcedure.test_H43_metadata_is_emitted_with_decision_provenance`; `test_audits.TestAudits.test_trace_has_producers_consumers_and_comparison_status` |
| X01–X04, X12–X13 | `tests/workbench/test_smoke.py::AdapterTests.*`; `test_session_replay.TestSessionReplay.*`; `test_acceptance_core.TestAcceptanceCore.test_H05_H13_manual_segmentation_and_known_structure_use_existing_lowerer` |

## Contract acceptance IDs

| ID | Actual test ID |
|---|---|
| H01 | `test_real_procedure.TestRealProcedure.test_H01_empty_review_reuses_automatic_compiler` |
| H02 | `test_session_replay.TestSessionReplay.test_H02_bad_source_anchor_is_stale` |
| H03 | `test_acceptance_core.TestAcceptanceCore.test_H03_same_quote_has_distinct_stable_source_address` |
| H05 | `test_acceptance_core.TestAcceptanceCore.test_H05_H13_manual_segmentation_and_known_structure_use_existing_lowerer` |
| H06 | `test_acceptance_core.TestAcceptanceCore.test_H06_manual_node_can_have_two_attested_spans` |
| H07 | `test_acceptance_core.TestAcceptanceCore.test_H07_scope_changes_program_frame_before_linking` |
| H08 | `test_acceptance_core.TestAcceptanceCore.test_H08_required_control_cannot_be_noncomputational_for_complete_export` |
| H09 | `test_acceptance_core.TestAcceptanceCore.test_H09_scope_parent_cycle_is_rejected` |
| H10 | `test_acceptance_core.TestAcceptanceCore.test_H10_linker_obeys_verified_producer_port_constraint` |
| H11/H12 | `test_acceptance_core.TestAcceptanceCore.test_H11_H12_candidate_correction_and_truncation_cannot_silently_close` |
| H13 | `test_acceptance_core.TestAcceptanceCore.test_H05_H13_manual_segmentation_and_known_structure_use_existing_lowerer` |
| H14 | `test_validation_metrics.TestValidationMetrics.test_H14_unknown_manual_opcode_requires_schema_extension` |
| H15 | `test_validation_metrics.TestValidationMetrics.test_H15_derived_value_cannot_be_declared_as_parameter` |
| H16 | `test_session_replay.TestSessionReplay.test_H16_context_attachment_stales_prior_binding` |
| H17 | `test_session_replay.TestSessionReplay.test_resegmentation_stales_overlapping_downstream_decision` |
| H18 | `test_session_replay.TestSessionReplay.test_H18_conflicting_active_slot_requires_resolution` |
| H19 | `test_real_procedure.TestRealProcedure.test_H19_retract_restores_automatic_missing_input_gap` |
| H20 | `test_real_procedure.TestRealProcedure.test_H20_H40_real_replay_is_closed_but_execution_is_separate` |
| H21/H22/H23 | `test_acceptance_core.TestAcceptanceCore.test_H21_H22_H23_type_evidence_and_time_origin_guards` |
| H39 | `test_validation_metrics.TestValidationMetrics.test_H39_partial_graph_is_exportable_but_not_complete` |
| H40 | `test_real_procedure.TestRealProcedure.test_H20_H40_real_replay_is_closed_but_execution_is_separate` |
| H43 | `test_real_procedure.TestRealProcedure.test_H43_metadata_is_emitted_with_decision_provenance` |
| H45 | `test_validation_metrics.TestValidationMetrics.test_H45_scripted_metrics_do_not_claim_human_time` |
| H46 | legacy commands below plus `test_real_procedure.TestRealProcedure.test_H01_empty_review_reuses_automatic_compiler` |

## Regression evidence

```text
python -X utf8 -B -m unittest discover -s tests/parser -v          61 OK
python -X utf8 -B -m unittest discover -s tests/parser_v3 -v       94 OK
python -X utf8 -B -m unittest discover -s tests/parser_rescue -v  78 OK
python -X utf8 -B -m unittest discover -s tests/reconciliation -v  5 OK
python -X utf8 -B -m unittest discover -s tests/workbench -v      15 OK
```

All actor records in the M2 real-flow test are `scripted_fixture`; its human
active and reading time are `null`. It is a software acceptance replay, not a
claim of human scholar effort.
