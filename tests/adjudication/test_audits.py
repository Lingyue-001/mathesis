import hashlib
import unittest

from adjudication.anchors import anchor_for
from adjudication.coverage import build_coverage_ledger
from adjudication.review_queue import build_review_queue
from adjudication.trace import build_reconstruction_trace


PACKET = {'schema_version': '3.0', 'packet_id': 'audit', 'primary_documents': [{
    'doc_id': 'p', 'reading_id': 'p.r', 'text': '甲乙。',
    'text_sha256': hashlib.sha256('甲乙。'.encode()).hexdigest(),
    'edition_transcription': '甲乙。', 'edition_edits': [],
}]}


class TestAudits(unittest.TestCase):
    def test_ledger_supports_overlapping_layers_and_marks_gap_partial(self):
        span = anchor_for(PACKET, 'p', 0, 1)
        graph = {'events': [{'id': 'e1', 'kind': 'literal', 'reads': {}, 'writes': {'result': 'v1'},
                             'source_spans': [span], 'scope': {}, 'attributes': {}}],
                 'value_instances': [{'id': 'v1', 'producer': 'e1', 'output_port': 'result',
                                      'unit': 'integer', 'scale': 1, 'source_spans': [span]}],
                 'diagnostics': [], 'unresolved': []}
        ledger = build_coverage_ledger(PACKET, graph, effective={'noncomputational': []})
        self.assertEqual(ledger['graph_status'], 'partial')
        self.assertTrue(any(item['layer'] == 'operation' for item in ledger['accounts']))
        self.assertTrue(ledger['unresolved_required_spans'])

    def test_trace_has_producers_consumers_and_comparison_status(self):
        span = anchor_for(PACKET, 'p', 0, 1)
        graph = {'events': [
            {'id': 'e1', 'kind': 'literal', 'reads': {}, 'writes': {'result': 'v1'}, 'source_spans': [span], 'scope': {}, 'attributes': {'value': 2}},
            {'id': 'e2', 'kind': 'load', 'reads': {'value': 'v1'}, 'writes': {'result': 'v2'}, 'source_spans': [span], 'scope': {}, 'attributes': {}},
        ], 'value_instances': [
            {'id': 'v1', 'producer': 'e1', 'output_port': 'result', 'unit': 'integer', 'scale': 1, 'source_spans': [span]},
            {'id': 'v2', 'producer': 'e2', 'output_port': 'result', 'unit': 'integer', 'scale': 1, 'source_spans': [span]},
        ]}
        trace = build_reconstruction_trace(graph)
        self.assertEqual(trace['steps'][0]['derived_outputs'][0]['producer']['event_id'], 'e1')
        self.assertEqual(trace['steps'][0]['derived_outputs'][0]['downstream_consumers'][0]['event_id'], 'e2')
        self.assertEqual(trace['steps'][0]['comparison']['status'], 'unavailable')

    def test_review_queue_reports_missing_input_and_unknown_quantity(self):
        graph = {'diagnostics': [{'kind': 'missing_import', 'formal': '甲', 'source_spans': []}],
                 'unresolved': [], 'value_instances': [{'id': 'v1', 'producer': 'e1', 'unit': 'unknown', 'resolution_status': 'unknown'}]}
        queue = build_review_queue(graph, replay={'decision_status': {}})
        self.assertEqual({item['kind'] for item in queue['items']}, {'missing_input', 'quantity_semantics'})
