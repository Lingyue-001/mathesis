"""Regression coverage for the read-only static Scholar Sandbox export."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from copy import deepcopy
from unittest.mock import patch

from source_adapters import corpus_index, corpus_review
from tools.parser_inspector.review_panel import composition_choices, question_options
from workbench import review_jobs
from workbench import service
from tests.workbench.test_review_jobs import isolated_source, SELECTION
from workbench.sandbox_snapshot import (
    DEFAULT_JOB_ID,
    build_snapshot,
    export_snapshot,
    serialize_snapshot,
)


ROOT = Path(__file__).resolve().parents[2]


def _digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _research_store_digests():
    """Files the read-only export is allowed to consume, never alter."""
    files = [review_jobs.job_path(ROOT, DEFAULT_JOB_ID)]
    for source in corpus_index.list_review_sources(ROOT):
        files.extend([*corpus_review.paths(ROOT, source["id"]),
                      corpus_review.workspace(ROOT, source["id"]) / "manifest.json"])
    return {path: _digest(path) for path in files}


class SandboxSnapshotTests(unittest.TestCase):
    def test_scenario_is_deterministic_and_matches_real_review_transactions(self):
        from workbench import sandbox_snapshot as exporter
        from adjudication import new_session
        self.assertTrue(hasattr(exporter, 'build_scenario'), 'Precompiled scenario exporter is missing')
        before = _research_store_digests()
        scenario = exporter.build_scenario(self.root)
        self.assertEqual(exporter.serialize_scenario(scenario), exporter.serialize_scenario(exporter.build_scenario(self.root)))
        self.assertEqual(before, _research_store_digests())
        self.assertEqual(scenario['schema'], 'ScholarSandboxScenario/1')
        self.assertEqual(scenario['initial_state_id'], 'baseline')
        self.assertEqual([(t['from_state_id'], t['to_state_id']) for t in scenario['transitions']], [
            ('baseline', 'ordinal-reviewed'), ('ordinal-reviewed', 'zhang-yue-attached'),
            ('zhang-yue-attached', 'zhang-fa-attached')])
        base = scenario['states']['baseline']
        provenance = base['provenance']
        packet = service._packet_for_job(self.root, provenance['source_selection'], provenance['review_job_id'])
        job = {'schema': 'ReviewJob/1', 'job_id': provenance['review_job_id'], 'revision': 1,
               'source_selection': provenance['source_selection'], 'base_packet_identity': provenance['base_packet_identity'],
               'analysis_inputs_digest': provenance['analysis_inputs_digest'],
               'session': new_session(packet, 'review:sandbox-scenario'), 'branch_id': 'main', 'management_events': [],
               'created_at': exporter.SCENARIO_TIME, 'updated_at': exporter.SCENARIO_TIME}
        review_jobs.write_job_atomic(self.root, job)
        response = service.compile_review_job(self.root, job['job_id'])
        self.assertEqual(base, exporter.build_snapshot_from_response(self.root, response))
        for transition in scenario['transitions']:
            with patch('workbench.service._now', return_value=exporter.SCENARIO_TIME):
                response = service.apply_review_job_changes(self.root, job['job_id'],
                    decisions=[transition['decision']], management_events=transition['management_events'],
                    expected_revision=response['job']['revision'], expected_digest=response['job_digest'])
            expected = exporter.build_snapshot_from_response(self.root, response)
            actual = scenario['states'][transition['to_state_id']]
            self.assertEqual(actual, expected, transition['id'])
            self.assertEqual(actual['review']['status'][transition['decision']['decision_id']]['status'], 'active')
        self.assertNotEqual(base['projection'], actual['projection'])
        self.assertNotEqual(base['procedure_model'], actual['procedure_model'])
        for transition, unit, formal in zip(scenario['transitions'][1:], ['sifen:section:16', 'sifen:section:15'], ['章月', '章法']):
            previous = scenario['states'][transition['from_state_id']]
            question = next(q for q in previous['questions'] if q['id'] == transition['question_id'])
            option = next(o for o in question['options'] if o['id'] == transition['option_id'])
            self.assertEqual(option['exact_declaration'], {'unit_id': unit, 'formal': formal})
        broken = deepcopy(scenario)
        broken['states']['baseline']['source']['text'] += '偽'
        with self.assertRaisesRegex(ValueError, 'mismatch'):
            exporter.serialize_scenario(broken)

    def test_snapshot_includes_python_authored_sections_for_objects_and_facets(self):
        from workbench.scholar_renderer import selected_source_object_sections
        snapshot = build_snapshot(self.root)
        for detail in [*snapshot['details']['objects'].values(), *snapshot['details']['facets'].values()]:
            self.assertIn('selected_source_sections', detail)
            self.assertEqual(detail['selected_source_sections'], selected_source_object_sections(
                snapshot['renderer'], detail['selected']['id']))

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        isolated_source(self.root)
        service.create_review_job(self.root, DEFAULT_JOB_ID,
            {**SELECTION, 'primary_unit_ids': ['sifen:section:38'], 'provided_scope': {}})

    def test_export_is_byte_deterministic_and_does_not_mutate_research_store(self):
        before = _research_store_digests()
        first = build_snapshot(self.root)
        first_bytes = serialize_snapshot(first).encode("utf-8")
        second = build_snapshot(self.root)
        self.assertEqual(first_bytes, serialize_snapshot(second).encode("utf-8"))
        self.assertEqual(before, _research_store_digests())
        with tempfile.TemporaryDirectory() as temporary:
            output = export_snapshot(first, Path(temporary) / "snapshot.json")
            self.assertEqual(output.read_bytes(), first_bytes)

    def test_snapshot_keeps_existing_source_graph_and_question_addresses(self):
        snapshot = build_snapshot(self.root)
        source = snapshot["source"]
        self.assertEqual(source["source_id"], "sifen")
        self.assertEqual(source["unit_id"], "sifen:section:38")
        self.assertEqual(source["doc_id"], "sifen:38")
        self.assertEqual(source["anchor"]["doc_id"], source["doc_id"])
        self.assertEqual(source["anchor"]["reading_id"], source["reading_id"])
        self.assertEqual(source["anchor"]["quote"], source["text"])
        self.assertEqual(source["anchor"]["end"], len(source["text"]))
        self.assertEqual(source["source_provenance"]["source_id"], source["source_id"])
        self.assertEqual(source["source_provenance"]["unit_id"], source["unit_id"])
        self.assertEqual(source["text_sha256"], hashlib.sha256(source["text"].encode("utf-8")).hexdigest())

        unsigned = {key: value for key, value in snapshot.items() if key != "snapshot_id"}
        self.assertEqual(snapshot["snapshot_id"], hashlib.sha256(
            (json.dumps(unsigned, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n").encode("utf-8")
        ).hexdigest())
        self.assertEqual(snapshot["procedure_model"]["source"], snapshot["projection"]["source"])

        questions = {question["id"]: question for question in snapshot["questions"]}
        self.assertEqual(len(questions), len(snapshot["questions"]))
        self.assertEqual(set(questions), set(snapshot["renderer"]["questions"]))
        for question_id, question in questions.items():
            self.assertEqual(question["options"], question_options(snapshot["renderer"]["questions"][question_id]))
        compose_by_question = snapshot["presentation_registry"]["compose_by_question"]
        for question in snapshot["questions"]:
            if question["kind"] != "term_interpretation":
                continue
            self.assertEqual(compose_by_question[question["id"]], composition_choices(
                snapshot["renderer"]["questions"][question["id"]]
            ))
        first_tree = next(iter(compose_by_question.values()))
        accumulation = next(row for row in first_tree if row["id"] == "constructor:accumulation")
        self.assertEqual(accumulation["label"], "Accumulated")
        self.assertEqual(accumulation["op"], "accumulation")
        self.assertTrue(any(row["id"] == "constructor:accumulation"
                            for row in accumulation["arguments"]["quantity"]))
        corpus_labels = {corpus["id"]: corpus["label"] for corpus in snapshot["corpora"]}
        self.assertTrue(all(row["label"].startswith(corpus_labels[row["source_id"]] + " · ")
                            for row in snapshot["context_catalog"]))
        for facet in snapshot["renderer"]["facets"]:
            self.assertIn(facet["question_id"], questions)
            detail = snapshot["details"]["facets"][facet["facet_key"]]
            self.assertEqual(detail["facet"]["facet_key"], facet["facet_key"])
        for object_id, detail in snapshot["details"]["objects"].items():
            self.assertEqual(detail["selected"]["id"], object_id)
            self.assertIn(object_id, snapshot["labels"]["objects"])


if __name__ == "__main__":
    unittest.main()
