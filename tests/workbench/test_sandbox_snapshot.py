"""Regression coverage for the read-only static Scholar Sandbox export."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from source_adapters import corpus_index, corpus_review
from tools.parser_inspector.review_panel import composition_choices, question_options
from workbench import review_jobs
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
    def test_export_is_byte_deterministic_and_does_not_mutate_research_store(self):
        before = _research_store_digests()
        first = build_snapshot(ROOT)
        first_bytes = serialize_snapshot(first).encode("utf-8")
        second = build_snapshot(ROOT)
        self.assertEqual(first_bytes, serialize_snapshot(second).encode("utf-8"))
        self.assertEqual(before, _research_store_digests())
        with tempfile.TemporaryDirectory() as temporary:
            output = export_snapshot(first, Path(temporary) / "snapshot.json")
            self.assertEqual(output.read_bytes(), first_bytes)

    def test_snapshot_keeps_existing_source_graph_and_question_addresses(self):
        snapshot = build_snapshot(ROOT)
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
