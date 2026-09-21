"""Source annotations are a read-only projection of review state."""
import unittest

from adjudication import compile_reviewed, new_session
from tests.adjudication.test_acceptance_core import decision
from source_adapters.corpus import build_source_packet_from_units
from workbench.service import _review_forms


class AnnotationProjectionTests(unittest.TestCase):
    def test_active_term_decision_is_projected_at_its_source_occurrence(self):
        from workbench.annotation_projection import project_annotations
        from workbench.question_presenter import build_questions

        packet = build_source_packet_from_units('.', 'sifen', ['sifen:section:38'], [], {})
        compilation = compile_reviewed(packet, new_session(packet, 'term-projection-proc-38'))
        questions = build_questions(packet, compilation, _review_forms(packet, compilation))
        term = next(q for q in questions if q['kind'] == 'term_interpretation' and q['anchor']['quote'] == '章法')
        decision = {'decision_id': 'term-meaning', 'action': 'set_term_interpretation',
                    'targets': [term['decision_target']], 'payload': {}}
        annotations = project_annotations(packet, compilation, questions, [decision],
                                          {'term-meaning': {'status': 'active'}})
        zhang_fa = next(row for row in annotations if row['display_anchor']['quote'] == '章法')
        self.assertIn(('term_meaning', 'reviewed'), [(row['facet'], row['status']) for row in zhang_fa['facets']])

    def test_confirmed_runtime_value_remains_linked_after_question_is_resolved(self):
        from workbench.annotation_projection import project_annotations
        from workbench.question_presenter import build_questions

        packet = build_source_packet_from_units('.', 'sifen', ['sifen:section:38'], [], {})
        session = new_session(packet, 'resolved-proc-38')
        initial = compile_reviewed(packet, session)
        source = next(q for q in build_questions(packet, initial, _review_forms(packet, initial))
                      if q['kind'] == 'quantity_source' and q['semantic_key'].get('formal') == '章法')
        from adjudication import append_decision
        append_decision(session, decision(packet, 'allow-zhang-fa', 'declare_parameter', source['decision_target'],
            next(o['payload'] for o in source['options'] if o['action'] == 'declare_parameter')), packet=packet)
        compilation = compile_reviewed(packet, session)
        questions = build_questions(packet, compilation, _review_forms(packet, compilation))
        annotations = project_annotations(packet, compilation, questions, session['decisions'],
                                          compilation['replay']['decision_status'])
        zhang_fa = next(row for row in annotations if row['display_anchor']['quote'] == '章法')
        self.assertIn(('source_supply', 'reviewed'), [(row['facet'], row['status']) for row in zhang_fa['facets']])
        self.assertIn(('term_meaning', 'pending'), [(row['facet'], row['status']) for row in zhang_fa['facets']])
        self.assertEqual(zhang_fa['machine_context']['source_status'], 'runtime value permitted')

    def test_active_source_supply_does_not_turn_other_facets_reviewed(self):
        from workbench.annotation_projection import project_annotations
        from workbench.question_presenter import build_questions

        packet = build_source_packet_from_units('.', 'sifen', ['sifen:section:38'], [], {})
        compilation = compile_reviewed(packet, new_session(packet, 'projection-proc-38'))
        questions = build_questions(packet, compilation, _review_forms(packet, compilation))
        source = next(q for q in questions if q['kind'] == 'quantity_source'
                      and q['semantic_key'].get('formal') == '章法')
        decision = {'decision_id': 'source-supply', 'action': 'declare_parameter',
                    'targets': [source['decision_target']],
                    'payload': next(o['payload'] for o in source['options'] if o['action'] == 'declare_parameter')}
        annotations = project_annotations(packet, compilation, questions, [decision],
                                          {'source-supply': {'status': 'active'}})
        zhang_fa = [row for row in annotations if row['display_anchor']['quote'] == '章法']
        self.assertEqual([(facet['facet'], facet['status']) for row in zhang_fa for facet in row['facets']],
                         [('source_supply', 'reviewed'), ('term_meaning', 'pending')])
        self.assertEqual(zhang_fa[0]['machine_context']['roles'], ['divisor'])
        from tools.parser_inspector.source_annotation import marks_for_document
        marks = marks_for_document(packet, 'sifen:38', annotations)
        marker = next(mark for mark in marks if mark['start'] == zhang_fa[0]['display_anchor']['start'])
        self.assertEqual(marker['status'], 'pending')
        self.assertIn('source supply: reviewed', marker['label'])


if __name__ == '__main__':
    unittest.main()
