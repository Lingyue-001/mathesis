import copy
import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "evaluation" / "handoff-v3" / "semantic_match.py"
SPEC = importlib.util.spec_from_file_location("semantic_match", MODULE)
semantic_match = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(semantic_match)
evaluate_obligations = semantic_match.evaluate_obligations


def span(start, end, quote="同文"):
    return {
        "doc_id": "D1", "reading_id": "R1", "text_sha256": "hash1",
        "start": start, "end": end, "quote": quote,
    }


def graph(kind="divmod"):
    return {
        "source_documents": [{"doc_id": "D1", "reading_id": "R1", "text_sha256": "hash1"}],
        "events": [{
            "id": "e1", "kind": kind, "reads": {"dividend": "input", "divisor": "cycle"},
            "writes": {"quotient": "q", "remainder": "r"}, "source_spans": [span(0, 2)],
            "scope": {"task": "moon", "query": "base"}, "attributes": {},
        }],
        "values": [
            {"id": "input", "semantic_id": "amount", "source_label": "same", "producer": None, "output_port": None},
            {"id": "cycle", "semantic_id": "month_rate", "source_label": "same", "producer": None, "output_port": None},
            {"id": "q", "semantic_id": "whole", "source_label": "same", "producer": "e1", "output_port": "quotient"},
            {"id": "r", "semantic_id": "fraction", "source_label": "same", "producer": "e1", "output_port": "remainder"},
        ],
        "unresolved": [],
    }


def contract(**overrides):
    predicate = {
        "kind": "divmod", "reads": {"dividend": "amount", "divisor": "month_rate"},
        "writes": {"quotient": "whole", "remainder": "fraction"},
        "scope": {"task": "moon", "query": "base"},
    }
    predicate.update(overrides)
    return (
        {"obligations": [{"id": "O1", "anchor": span(0, 2)}], "coverage": "complete"},
        {"supported_actions": ["divmod", "method_call", "repeat", "convert"],
         "obligations": {"O1": predicate}},
    )


class SemanticMatchTests(unittest.TestCase):
    def evaluate(self, report=None, reference=None, policy=None):
        reference0, policy0 = contract()
        return evaluate_obligations(report or graph(), reference or reference0, policy or policy0)

    def test_repeated_identical_quote_uses_exact_range(self):
        report = graph()
        wrong = copy.deepcopy(report["events"][0]); wrong["id"] = "wrong"; wrong["source_spans"] = [span(4, 6)]
        wrong["writes"] = {"quotient": "r", "remainder": "q"}
        report["events"].insert(0, wrong)
        result = self.evaluate(report)
        self.assertEqual(result["obligations"][0]["matched_event_ids"], ["e1"])
        self.assertTrue(result["full_chain_passed"])

    def test_quotient_remainder_mutation_is_fp_and_fn(self):
        report = graph(); report["events"][0]["writes"] = {"quotient": "r", "remainder": "q"}
        result = self.evaluate(report)
        self.assertEqual(result["layers"]["producer_port"]["FP"], 2)
        self.assertEqual(result["layers"]["producer_port"]["FN"], 2)
        self.assertFalse(result["full_chain_passed"])

    def test_output_identity_rejects_corrupt_writer_metadata_and_ignores_labels(self):
        report = graph()
        report["values"][2]["producer"] = "wrong"
        report["values"][2]["output_port"] = "remainder"
        report["values"][2]["semantic_id"] = None
        report["values"][3]["semantic_id"] = None
        result = self.evaluate(report)
        self.assertEqual(result["obligations"][0]["status"], "fail")
        self.assertGreater(result["layers"]["producer_port"]["FP"], 0)
        self.assertGreater(result["layers"]["producer_port"]["FN"], 0)

    def test_endpoint_selectors_accept_value_id_and_origin_descriptor(self):
        reference, policy = contract(reads={"dividend": {"value_id": "input"}, "divisor": {"value_id": "cycle"}},
                                     writes={"quotient": {"origin": {"anchor": span(0, 2), "kind": "divmod", "port": "quotient"}},
                                             "remainder": {"value_id": "r"}})
        self.assertTrue(self.evaluate(reference=reference, policy=policy)["full_chain_passed"])

    def test_ambiguous_legacy_semantic_id_is_rejected(self):
        report = graph()
        report["values"].append({"id": "other", "semantic_id": "amount", "producer": None, "output_port": None})
        self.assertFalse(self.evaluate(report)["full_chain_passed"])

    def test_method_wrong_target_rejected_despite_same_actuals(self):
        report = graph("method_call")
        report["events"][0]["attributes"]["method_binding"] = {
            "target_method_id": "wrong", "formal_to_actual": {"n": "input"},
            "return_ports": {"quotient": "q", "remainder": "r"}, "body_hash": "body-a",
        }
        reference, policy = contract(kind="method_call", method_binding={
            "target_method_id": "right", "formal_to_actual": {"n": "amount"},
            "return_ports": {"quotient": "whole", "remainder": "fraction"}, "body_hash": "body-a",
        })
        result = self.evaluate(report, reference, policy)
        self.assertEqual(result["layers"]["method_call"]["FP"], 1)
        self.assertEqual(result["layers"]["method_call"]["FN"], 1)

    def test_stop_predicate_mutation_rejected(self):
        report = graph("repeat")
        report["events"][0]["attributes"]["control"] = {
            "stop_predicate": "remaining <= year", "test_position": "post", "counter": "year"
        }
        reference, policy = contract(kind="repeat", control={
            "stop_predicate": "remaining < year", "test_position": "post", "counter": "year"
        })
        result = self.evaluate(report, reference, policy)
        self.assertEqual(result["layers"]["scope_control"]["FP"], 1)
        self.assertEqual(result["layers"]["scope_control"]["FN"], 1)

    def test_missing_unit_rate_rejected(self):
        report = graph("convert")
        report["events"][0]["attributes"]["quantity"] = {"from_unit": "month", "to_unit": "day"}
        reference, policy = contract(kind="convert", quantity={
            "from_unit": "month", "to_unit": "day", "rate_value": "month_rate"
        })
        result = self.evaluate(report, reference, policy)
        self.assertEqual(result["layers"]["scale_rate"]["FN"], 1)
        self.assertFalse(result["full_chain_passed"])

    def test_unknown_reference_action_is_evaluator_unsupported_with_null_scores(self):
        reference, policy = contract(kind="historical_action")
        result = self.evaluate(reference=reference, policy=policy)
        row = result["obligations"][0]
        self.assertEqual(row["status"], "evaluator_unsupported")
        self.assertIsNone(row["scores"])
        self.assertEqual(result["layers"]["producer_port"]["FP"], 0)
        self.assertIsNone(result["full_chain_passed"])

    def test_unrecognized_actual_kind_is_unsupported_without_fp(self):
        report = graph("novel_representation")
        result = self.evaluate(report)
        self.assertEqual(result["obligations"][0]["status"], "evaluator_unsupported")
        self.assertIsNone(result["obligations"][0]["scores"])
        self.assertEqual(result["layers"]["source_identity"]["FP"], 0)
        self.assertIn("divmod", result["supported_actions"])

    def test_unknown_actual_with_unrelated_supported_candidate_stays_unsupported(self):
        report = graph("novel_representation")
        report["events"].append({"id": "repeat", "kind": "repeat", "reads": {}, "writes": {},
                                 "source_spans": [span(0, 2)], "scope": {}, "attributes": {}})
        result = self.evaluate(report)
        self.assertEqual(result["obligations"][0]["status"], "evaluator_unsupported")
        self.assertIsNone(result["obligations"][0]["scores"])
        self.assertEqual(result["layers"]["source_identity"]["FP"], 0)

    def test_scope_mismatch_is_fp_and_fn(self):
        report = graph(); report["events"][0]["scope"]["task"] = "winter"
        result = self.evaluate(report)
        self.assertEqual(result["layers"]["scope_control"]["FP"], 1)
        self.assertEqual(result["layers"]["scope_control"]["FN"], 1)

    def test_same_kind_candidate_selection_is_order_independent(self):
        report = graph()
        wrong = copy.deepcopy(report["events"][0]); wrong["id"] = "a-wrong"; wrong["writes"] = {"quotient": "r", "remainder": "q"}
        report["events"].insert(0, wrong)
        result = self.evaluate(report)
        self.assertTrue(result["full_chain_passed"])
        self.assertEqual(result["obligations"][0]["matched_event_ids"], ["e1"])

    def test_multi_event_obligation_composes_all_policy_predicates(self):
        report = graph()
        report["events"].append({"id": "e2", "kind": "repeat", "reads": {}, "writes": {},
                                 "source_spans": [span(0, 2)], "scope": {"task": "moon"},
                                 "attributes": {"control": {"stop_predicate": "n < 12"}}})
        reference, policy = contract(events=[
            {"kind": "divmod", "writes": {"quotient": {"value_id": "q"}, "remainder": {"value_id": "r"}}},
            {"kind": "repeat", "scope": {"task": "moon"}, "control": {"stop_predicate": "n < 12"}},
        ])
        policy["obligations"]["O1"].pop("kind", None)
        result = self.evaluate(report, reference, policy)
        self.assertTrue(result["full_chain_passed"])
        self.assertEqual(result["obligations"][0]["matched_event_ids"], ["e1", "e2"])

    def test_public_alias_event_normalizes_to_origin_and_port(self):
        report = graph()
        report["events"].append({"id": "alias-e", "kind": "alias", "reads": {"value": "input"},
                                 "writes": {"result": "alias_input"}, "source_spans": [span(0, 2)],
                                 "scope": {"task": "moon", "query": "base"}, "attributes": {}})
        report["values"].append({"id": "alias_input", "source_label": "alias", "producer": "alias-e",
                                 "output_port": "result", "origin_producer": None, "origin_port": None})
        report["events"][0]["reads"]["dividend"] = "alias_input"
        self.assertTrue(self.evaluate(report)["full_chain_passed"])

    def test_distinct_unresolved_statuses_and_incomplete_domain(self):
        for cause, expected in [("parser_error", "parser_error"), ("missing_context", "missing_context"),
                                ("text_ambiguity", "text_ambiguity")]:
            with self.subTest(cause=cause):
                report = graph(); report["events"] = []; report["unresolved"] = [{"cause": cause, "source_spans": [span(0, 2)]}]
                self.assertEqual(self.evaluate(report)["obligations"][0]["status"], expected)
        reference, policy = contract(); reference["coverage"] = "partial"
        self.assertFalse(self.evaluate(reference=reference, policy=policy)["full_chain_passed"])

    def test_unparsed_coverage_and_diagnostics_block_full_chain_and_are_reported(self):
        for report in (
            {**graph(), "unparsed_spans": [span(7, 9)]},
            {**graph(), "coverage": {"total_source_length": 20, "audited_ranges": [[0, 2]],
                                     "unscored_ranges": [[2, 20]], "unparsed_spans": [span(7, 9)]}},
            {**graph(), "diagnostics": {"unparsed_spans": [span(7, 9)]}},
        ):
            with self.subTest(keys=tuple(report.keys())):
                result = self.evaluate(report)
                self.assertFalse(result["full_chain_passed"])
                self.assertEqual(result["coverage"]["unparsed_span_count"], 1)
        report = graph(); report["coverage"] = {"total_source_length": 20, "audited_ranges": [[0, 2]], "unscored_ranges": [[2, 20]]}
        coverage = self.evaluate(report)["coverage"]
        self.assertEqual(coverage["total_source_length"], 20)
        self.assertEqual(coverage["audited_ranges"], [[0, 2]])
        self.assertEqual(coverage["unscored_ranges"], [[2, 20]])

    def test_public_list_diagnostics_block_and_are_reported(self):
        report = graph()
        report["diagnostics"] = [{"cause": "unknown_domain", "source_spans": [span(7, 9)]}]
        coverage = self.evaluate(report)["coverage"]
        self.assertFalse(self.evaluate(report)["full_chain_passed"])
        self.assertEqual(coverage["diagnostic_count"], 1)
        self.assertEqual(coverage["diagnostic_causes"], ["unknown_domain"])
        self.assertEqual(coverage["diagnostic_spans"], [span(7, 9)])


if __name__ == "__main__":
    unittest.main()
