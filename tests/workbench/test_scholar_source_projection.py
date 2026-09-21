"""Authored Proc.38 golden for the one scholar-facing projection."""
import json
from pathlib import Path
import unittest
from copy import deepcopy

from adjudication import append_decision, compile_reviewed, new_session
from adjudication.anchors import anchor_for
from domain_kernel.engine import suggest_packet_semantics
from tests.adjudication.test_acceptance_core import packet as synthetic_packet, decision
from source_adapters.corpus import build_source_packet_from_units
from workbench.question_presenter import build_questions
from workbench.service import _review_forms


class ScholarSourceProjectionTests(unittest.TestCase):
    def fixture(self, name='proc38-golden-projection.json'):
        return json.loads((Path(__file__).parents[1] / 'fixtures' / 'scholar_source_projection'
                           / name).read_text(encoding='utf-8'))

    def project(self, packet, session=None, questions=None, decisions=None, **kwargs):
        from workbench.annotation_projection import project_scholar_source
        session = session or new_session(packet, 'projection-regression')
        compilation = compile_reviewed(packet, session)
        questions = (build_questions(packet, compilation, _review_forms(packet, compilation))
                     if questions is None else questions)
        return project_scholar_source(packet, compilation, questions,
            session['decisions'] if decisions is None else decisions,
            compilation['replay']['decision_status'], **kwargs), compilation, questions

    def test_context_declaration_has_a_real_source_flow(self):
        packet = build_source_packet_from_units('.', 'sifen', ['sifen:section:38'], ['sifen:section:15'], {})
        actual, compilation, _ = self.project(packet)
        flow = next(row for row in actual['flows'] if row['formal'] == '章法')
        self.assertEqual(flow['status'], 'linked_source')
        self.assertEqual(flow['producer_source']['doc_id'], 'sifen:15')
        self.assertEqual(flow['producer_source']['unit_id'], 'sifen:section:15')
        producer = next(row for row in compilation['graph']['program']['definitions']
                        if row['source_spans'][0]['doc_id'] == 'sifen:15')
        self.assertEqual(flow['selected_definition_id'], producer['id'])
        self.assertEqual(flow['output_port'], 'result')
        self.assertEqual(flow['selected_port'], 'result')

    def test_replayed_attachment_uses_the_effective_packet_source(self):
        from adjudication.effective_packet import derive_packet
        base = build_source_packet_from_units('.', 'sifen', ['sifen:section:38'], [], {})
        context = build_source_packet_from_units('.', 'sifen', ['sifen:section:15'], [], {})['primary_documents'][0]
        session = new_session(base, 'attached-15')
        append_decision(session, decision(base, 'attach-15', 'attach_context', anchor_for(base, 'sifen:38', 0, 4),
                                         {'document': context}), packet=base)
        compilation = compile_reviewed(base, session)
        effective = derive_packet(base, compilation['replay']['effective']['contexts'])
        questions = build_questions(effective, compilation, _review_forms(effective, compilation))
        from workbench.annotation_projection import project_scholar_source
        actual = project_scholar_source(effective, compilation, questions, session['decisions'],
                                        compilation['replay']['decision_status'])
        flow = next(row for row in actual['flows'] if row['formal'] == '章法')
        self.assertEqual(flow['status'], 'linked_source')
        self.assertEqual(flow['producer_source']['doc_id'], 'sifen:15')
        self.assertFalse(any(f.get('action') == 'declare_parameter' for f in actual['review_facets']))

    def test_real_reviewed_import_binding_preserves_selected_definition_and_port(self):
        packet = build_source_packet_from_units('.', 'sifen', ['sifen:section:39'],
                                               ['sifen:section:38', 'sifen:section:15'],
                                               {'tradition': 'Han_Si_fen_li'})
        session = new_session(packet, 'bound-source')
        compilation = compile_reviewed(packet, session)
        form = next(row for row in _review_forms(packet, compilation) if row.get('formal') == '入蔀積月')
        producer = next(row for row in form['producers'] if row['anchor']['doc_id'] == 'sifen:38'
                        and row['output_port'] == '積月')
        payload = {'consumer_definition_anchor': form['consumer_anchor'], 'formal': form['formal'],
                   'producer_definition_anchor': producer['anchor'], 'output_port': producer['output_port']}
        append_decision(session, decision(packet, 'bind-month', 'bind_value', form['consumer_anchor'], payload), packet=packet)
        actual, compilation, _ = self.project(packet, session)
        self.assertEqual(compilation['replay']['decision_status']['bind-month']['status'], 'active')
        native = next(row for row in compilation['graph']['program']['linked']['imports']
                      if row['formal'] == '入蔀積月')
        flow = next(row for row in actual['flows'] if row['formal'] == native['formal']
                    and row['consumer_definition_id'] == native['consumer_definition_id'])
        self.assertEqual(flow['status'], 'linked_source')
        self.assertEqual(flow['selected_definition_id'], native['selected_definition_id'])
        self.assertEqual(flow['output_port'], native['selected_port'])
        self.assertEqual(flow['selected_port'], '積月')
        self.assertEqual(flow['selection_reason'], 'reviewed producer/port constraint')
        self.assertEqual(flow['producer_source']['doc_id'], 'sifen:38')
        self.assertTrue(flow['consumer_step_ids'])
        from workbench.annotation_projection import project_annotations
        annotations = project_annotations(packet, compilation,
            build_questions(packet, compilation, _review_forms(packet, compilation)), session['decisions'],
            compilation['replay']['decision_status'])
        self.assertFalse(any('Runtime value' in facet['label'] for row in annotations for facet in row['facets']))

    def test_source_identity_and_kernel_children_and_provenance(self):
        packet = build_source_packet_from_units('.', 'sifen', ['sifen:section:38'], [], {})
        actual, _, _ = self.project(packet)
        self.assertEqual(actual['source']['source_id'], 'sifen')
        self.assertEqual(actual['source']['unit_id'], 'sifen:section:38')
        candidates = {row['id']: row for row in suggest_packet_semantics(packet)['sifen:38']['candidates']}
        projected = {candidate['candidate_id']: candidate for term in actual['terms']
                     for candidate in term['semantic_candidates']}
        admitted = {(row['source_anchor']['start'], row['source_anchor']['end']) for row in actual['terms']}
        expected = {ident: row for ident, row in candidates.items()
                    if (row['span']['start'], row['span']['end']) in admitted}
        self.assertEqual(set(projected), set(expected))
        self.assertNotIn('天正術', {row['surface'] for row in actual['terms']})
        for ident, native in expected.items():
            self.assertEqual(projected[ident]['child_ids'], native['child_ids'])
            self.assertEqual(projected[ident]['provenance_ids'], native['provenance_ids'])
        root = next(row for row in actual['terms'] if row['surface'] == '入蔀年')
        self.assertTrue(root['children'])
        children = {row['id']: row for row in actual['terms']}
        self.assertEqual([children[ident]['surface'] for ident in root['children']], ['入', '蔀', '年'])
        self.assertTrue(all(children[ident]['display_level'] == 'component' for ident in root['children']))
        self.assertEqual(next(row for row in actual['terms'] if row['surface'] == '蔀年')['display_level'], 'component')
        self.assertTrue(all(candidate['authorization_status'] == 'not_authorized'
                            for candidate in root['semantic_candidates']))

    def test_one_term_decision_does_not_review_other_occurrences(self):
        packet = build_source_packet_from_units('.', 'sifen', ['sifen:section:38'], [], {})
        initial, _, questions = self.project(packet)
        target = next(q for q in questions if q['kind'] == 'term_interpretation' and q['anchor']['quote'] == '章法')
        option = next(o for o in target['options'] if o['action'] == 'set_term_interpretation')
        row = decision(packet, 'only-zhangfa', option['action'], target['decision_target'], option['payload'])
        # Also test an old displayed question set: the completed occurrence must
        # match its exact target, not every question of the same facet family.
        session = new_session(packet, 'one-term')
        append_decision(session, row, packet=packet)
        for qs in (questions, None):
            actual, _, _ = self.project(packet, session, questions=qs)
            status = {(f['object_id'], f['facet']): f['status'] for f in actual['review_facets']}
            self.assertEqual(status[('term:sifen:38:19-21', 'term_meaning')], 'reviewed')
            self.assertEqual(status[('term:sifen:38:13-15', 'term_meaning')], 'pending')

    def test_same_formal_in_two_consumers_keeps_scope(self):
        packet = synthetic_packet('推天正術。置章月減一。推冬至術。置章月減一。')
        _, _, questions = self.project(packet)
        sources = [q for q in questions if q['semantic_key'].get('issue_family') == 'source_supply']
        self.assertEqual(len(sources), 2)
        option = next(o for o in sources[0]['options'] if o['action'] == 'declare_parameter')
        row = decision(packet, 'first-only', option['action'], sources[0]['decision_target'], option['payload'])
        actual, _, _ = self.project(packet, questions=questions, decisions=[row])
        status = {f['question_id']: f['status'] for f in actual['review_facets'] if f.get('question_id')}
        self.assertEqual(status[sources[0]['id']], 'reviewed')
        self.assertEqual(status[sources[1]['id']], 'pending')
        flows = actual['flows']
        self.assertEqual(len({f['id'] for f in flows}), 2)
        self.assertEqual(sorted(f['status'] for f in flows), ['runtime_value_permitted', 'unresolved_source'])

    def test_other_branch_and_inactive_decisions_do_not_review_current_terms(self):
        packet = build_source_packet_from_units('.', 'sifen', ['sifen:section:38'], [], {})
        _, compilation, questions = self.project(packet)
        target = next(q for q in questions if q['kind'] == 'term_interpretation' and q['anchor']['quote'] == '章法')
        option = next(o for o in target['options'] if o['action'] == 'set_term_interpretation')
        row = decision(packet, 'foreign', option['action'], target['decision_target'], option['payload'])
        from workbench.annotation_projection import project_scholar_source
        for branch, status in [('other', 'active'), ('main', 'stale'), ('main', 'conflicted'), ('main', 'retracted')]:
            row['branch_id'] = branch
            actual = project_scholar_source(packet, compilation, questions, [row], {'foreign': {'status': status}})
            self.assertTrue(all(f['status'] == 'pending' for f in actual['review_facets']))

    def test_quantity_review_matches_the_normalized_invocation_target(self):
        packet = build_source_packet_from_units('.', 'sifen', ['sifen:section:38'], [], {})
        _, _, questions = self.project(packet)
        original = next(q for q in questions if q['kind'] == 'counting_convention')
        other = deepcopy(original)
        other['id'] = 'other-invocation'
        for option in other['options']:
            if option['action'] == 'set_quantity_semantics':
                option['payload']['semantic_input']['invocation_path'] = [anchor_for(packet, 'sifen:38', 0, 4)]
        option = next(o for o in original['options'] if o['action'] == 'set_quantity_semantics')
        row = decision(packet, 'original-invocation', option['action'], original['decision_target'], option['payload'])
        actual, _, _ = self.project(packet, questions=[original, other], decisions=[row])
        status = {f['question_id']: f['status'] for f in actual['review_facets'] if f.get('question_id')}
        self.assertEqual(status[original['id']], 'reviewed')
        self.assertEqual(status['other-invocation'], 'pending')

    def test_projection_is_read_only(self):
        packet = build_source_packet_from_units('.', 'sifen', ['sifen:section:38'], ['sifen:section:15'], {})
        session = new_session(packet, 'read-only')
        compilation = compile_reviewed(packet, session)
        questions = build_questions(packet, compilation, _review_forms(packet, compilation))
        before = deepcopy((packet, compilation, questions, session))
        from workbench.annotation_projection import project_scholar_source
        project_scholar_source(packet, compilation, questions, session['decisions'], compilation['replay']['decision_status'])
        self.assertEqual((packet, compilation, questions, session), before)

    def test_proc39_retains_canonical_construction_types(self):
        packet = build_source_packet_from_units('.', 'sifen', ['sifen:section:39'], [], {})
        actual, compilation, _ = self.project(packet)
        syntax = {row['id']: row for row in compilation['graph']['syntax']['nodes']}
        projected = {row['evidence'][0]['syntax_node_id']: row for row in actual['constructions']}
        for native in compilation['graph']['construction_candidates']:
            self.assertIn(native['node_id'], projected)
            self.assertEqual(projected[native['node_id']]['public_kind'], syntax[native['node_id']]['kind'])
        self.assertIn('cycle_divide', {row['construction_kind'] for row in actual['constructions']})
        self.assertTrue(any(row['operation'] == 'divmod' for row in actual['steps']))
        events = {row['id']: row for row in compilation['graph']['events']}
        for step in actual['steps']:
            self.assertEqual(step['operation'], events[step['evidence'][0]['event_id']]['kind'])

    def test_lexical_and_reviewed_boundary_terms_survive_without_compounds(self):
        packet = synthetic_packet('日。陌生量。')
        session = new_session(packet, 'boundary-only')
        target = anchor_for(packet, 'p', 2, 5)
        append_decision(session, decision(packet, 'boundary', 'set_term_boundary', target,
                        {'contract_version': '1.0', 'branch_id': 'main'}), packet=packet)
        actual, _, _ = self.project(packet, session)
        self.assertIn('日', {row['surface'] for row in actual['terms']})
        self.assertIn('陌生量', {row['surface'] for row in actual['terms']})

    def test_proc38_full_authored_golden_exact_equality(self):
        from workbench.annotation_projection import project_scholar_source, stable_golden_view

        fixture = json.loads((Path(__file__).parents[1] / 'fixtures' / 'scholar_source_projection'
                              / 'proc38-golden-projection.json').read_text(encoding='utf-8'))
        packet = build_source_packet_from_units('.', 'sifen', ['sifen:section:38'], [], {})
        compilation = compile_reviewed(packet, new_session(packet, 'proc38-scholar-golden'))
        questions = build_questions(packet, compilation, _review_forms(packet, compilation))
        actual = project_scholar_source(packet, compilation, questions,
                                        compilation['replay']['effective'].get('decisions', []),
                                        compilation['replay']['decision_status'])
        self.assertEqual(actual['schema'], 'ScholarSourceProjection/1')
        self.assertEqual(actual['projection_diagnostics'], [])
        stable = stable_golden_view(actual)
        self.assertEqual(stable, fixture['expected'])
        for name, count in fixture['expected_counts'].items():
            self.assertEqual(len(actual[name]), count, name)

    def test_section15_focused_context_invariant(self):
        from workbench.annotation_projection import stable_golden_view
        fixture = self.fixture('proc38-section15-context-invariant.json')
        packet = build_source_packet_from_units('.', 'sifen', ['sifen:section:38'], ['sifen:section:15'], {})
        actual, _, _ = self.project(packet)
        stable = stable_golden_view(actual)
        expected = deepcopy(self.fixture()['expected'])
        patch = deepcopy(fixture['expected_flow_patch'])
        flow_id = patch.pop('flow_id')
        next(row for row in expected['flows'] if row['id'] == flow_id).update(patch)
        expected['review_facets'] = [row for row in expected['review_facets']
                                    if row not in fixture['facet_invariants']['must_be_absent']]
        self.assertEqual(stable, expected)
        for name, count in fixture['expected_counts'].items():
            self.assertEqual(len(actual[name]), count, name)
        self.assertEqual(actual['projection_diagnostics'], [])

    def test_canonical_links_merge_all_candidate_evidence(self):
        packet = build_source_packet_from_units('.', 'sifen', ['sifen:section:38'], [], {})
        actual, _, _ = self.project(packet)
        keys = [(r['relation'], r['from_id'], r['to_id'], r.get('role'), r.get('ordinal'))
                for r in actual['links']]
        self.assertEqual(len(keys), len(set(keys)))
        ids = {r['id'] for layer in ('terms', 'constructions', 'steps', 'flows') for r in actual[layer]}
        self.assertTrue(all(r['from_id'] in ids and r['to_id'] in ids for r in actual['links']))
        term = next(r for r in actual['terms'] if r['id'] == 'term:sifen:38:13-15')
        for ordinal, child in enumerate(term['children']):
            link = next(r for r in actual['links'] if r['relation'] == 'has_component'
                        and r['from_id'] == term['id'] and r['to_id'] == child and r['ordinal'] == ordinal)
            self.assertEqual(link['evidence'], [{'candidate_id': c['candidate_id'], 'child_id': c['child_ids'][ordinal]}
                                               for c in term['semantic_candidates']])

    def test_link_merge_uses_identity_not_basis_and_retains_roles_and_ordinals(self):
        from workbench.annotation_projection import _canonical_links
        base = {'relation': 'has_component', 'from_id': 'parent', 'to_id': 'child', 'ordinal': 0}
        rows = [{**base, 'basis': 'structurally_derived', 'evidence': [{'path': 'a'}]},
                {**base, 'basis': 'explicit', 'evidence': [{'path': 'b'}, {'path': 'a'}]},
                {**base, 'ordinal': 1, 'basis': 'explicit'},
                {**base, 'role': 'other', 'basis': 'explicit'}]
        original = deepcopy(rows)
        merged = _canonical_links(rows)
        self.assertEqual(len(merged), 3)
        link = next(r for r in merged if r['ordinal'] == 0 and 'role' not in r)
        self.assertEqual(link['basis'], 'explicit')
        self.assertEqual(link['evidence'], [{'path': 'a'}, {'path': 'b'}])
        self.assertEqual(rows, original)

    def test_stable_view_never_hides_duplicate_canonical_links(self):
        from workbench.annotation_projection import stable_golden_view
        packet = build_source_packet_from_units('.', 'sifen', ['sifen:section:38'], [], {})
        actual, _, _ = self.project(packet)
        actual['links'].append(deepcopy(actual['links'][0]))
        self.assertEqual(len(stable_golden_view(actual)['links']), len(actual['links']))
        self.assertNotEqual(stable_golden_view(actual), self.fixture()['expected'])

    def test_computational_unknown_and_reviewed_heading_are_admitted(self):
        packet = synthetic_packet('推天正術。置陌生量減一。')
        actual, _, _ = self.project(packet)
        self.assertIn('陌生量', {r['surface'] for r in actual['terms']})
        self.assertNotIn('天正術', {r['surface'] for r in actual['terms']})
        session = new_session(packet, 'review-heading')
        append_decision(session, decision(packet, 'heading', 'set_term_boundary', anchor_for(packet, 'p', 1, 4),
                        {'contract_version': '1.0', 'branch_id': 'main'}), packet=packet)
        actual, _, _ = self.project(packet, session)
        term = next(r for r in actual['terms'] if r['surface'] == '天正術')
        self.assertIn('term_boundary', term['review_facets'])

    def test_focus_filters_context_steps_flows_and_all_references(self):
        from workbench.annotation_projection import project_scholar_source
        packet = build_source_packet_from_units('.', 'sifen', ['sifen:section:39'],
                                               ['sifen:section:38', 'sifen:section:15'], {})
        for focus in ('sifen:39', 'sifen:38', 'sifen:15'):
            actual, _, _ = self.project(packet, focus_doc_id=focus)
            self.assertEqual(actual['source']['doc_id'], focus)
            self.assertTrue(all(r['source_anchor']['doc_id'] == focus for r in actual['terms']))
            for layer in ('constructions', 'steps'):
                self.assertTrue(all(a['doc_id'] == focus for r in actual[layer] for a in r['source_anchors']))
            ids = {r['id'] for layer in ('terms', 'constructions', 'steps', 'flows') for r in actual[layer]}
            steps = {r['id'] for r in actual['steps']}
            for flow in actual['flows']:
                self.assertTrue(flow['consumer_step_ids'])
                self.assertLessEqual(set(flow['consumer_step_ids']), steps)
                self.assertTrue(flow['producer_step_id'] is None or flow['producer_step_id'] in steps)
            self.assertTrue(all(f['object_id'] in ids for f in actual['review_facets']))
            self.assertTrue(all(l['from_id'] in ids and l['to_id'] in ids for l in actual['links']))
            for step in actual['steps']:
                for item in step['inputs']:
                    for key in ('term_id', 'flow_id', 'from_step_id'):
                        self.assertTrue(key not in item or item[key] in ids)
        compilation = compile_reviewed(packet, new_session(packet, 'invalid-focus'))
        with self.assertRaises(ValueError):
            project_scholar_source(packet, compilation, focus_doc_id='absent')

    def test_mixed_document_event_is_omitted_with_diagnostic(self):
        from workbench.annotation_projection import project_scholar_source
        packet = build_source_packet_from_units('.', 'sifen', ['sifen:section:38'], ['sifen:section:15'], {})
        _, compilation, questions = self.project(packet)
        event = next(e for e in compilation['graph']['events'] if e['kind'] == 'multiply')
        event['source_spans'].append(anchor_for(packet, 'sifen:15', 0, 5))
        actual = project_scholar_source(packet, compilation, questions)
        self.assertNotIn(event['id'], {r['evidence'][0]['event_id'] for r in actual['steps']})
        self.assertTrue(any(d['kind'] == 'cross_document_step_not_projectable' and d['event_id'] == event['id']
                            for d in actual['projection_diagnostics']))
        self.assertNotIn('章月', {f['formal'] for f in actual['flows']})

    def test_missing_focused_import_binding_is_diagnosed_without_emitting_empty_flow(self):
        from workbench.annotation_projection import project_scholar_source
        packet = build_source_packet_from_units('.', 'sifen', ['sifen:section:38'], [], {})
        _, compilation, questions = self.project(packet)
        for call in compilation['graph']['program']['calls']:
            call.get('formal_bindings', {}).pop('章法', None)
        actual = project_scholar_source(packet, compilation, questions)
        self.assertNotIn('章法', {f['formal'] for f in actual['flows']})
        self.assertTrue(any(d['kind'] == 'flow_input_unlinked' and d['formal'] == '章法'
                            for d in actual['projection_diagnostics']))

    def test_unknown_children_and_distinct_compositions_are_preserved(self):
        from unittest.mock import patch
        from workbench.annotation_projection import project_scholar_source
        packet = synthetic_packet('甲乙丙。丁。')
        compilation = compile_reviewed(packet, new_session(packet, 'composition'))
        # Inject a Kernel result at its read-only boundary to exercise a valid
        # shape absent from the current Proc.38 examples; never alter Kernel rules.
        def candidate(ident, start, end, children=(), domain=False):
            return {'id': ident, 'span': anchor_for(packet, 'p', start, end), 'child_ids': list(children),
                    'expression': {'op': 'concept', 'concept_id': 'time.year'} if domain else {'op': 'unknown'},
                    'rule_id': ident, 'support_status': 'proposed', 'constraint_status': 'compatible',
                    'authorization_status': 'not_authorized', 'provenance_ids': []}
        candidates = [candidate('root-a', 0, 3, ['middle'], True), candidate('root-b', 0, 3, [], True),
                      candidate('middle', 0, 2, ['leaf'], True), candidate('leaf', 0, 1), candidate('unrelated', 4, 5)]
        with patch('workbench.annotation_projection.suggest_packet_semantics',
                   return_value={'p': {'candidates': candidates, 'regions': []}}):
            actual = project_scholar_source(packet, compilation)
        terms = {t['id']: t for t in actual['terms']}
        self.assertEqual(set(terms), {'term:p:0-3', 'term:p:0-2', 'term:p:0-1'})
        root = terms['term:p:0-3']
        self.assertEqual(root['children'], [])
        self.assertCountEqual(root['composition_alternatives'], [['term:p:0-2'], []])
        self.assertEqual(terms['term:p:0-2']['children'], ['term:p:0-1'])
        self.assertEqual(terms['term:p:0-1']['display_level'], 'component')

    def test_retracted_heading_boundary_does_not_grant_admission(self):
        packet = synthetic_packet('推天正術。')
        session = new_session(packet, 'heading-retract')
        target = anchor_for(packet, 'p', 1, 4)
        append_decision(session, decision(packet, 'heading', 'set_term_boundary', target,
                        {'contract_version': '1.0', 'branch_id': 'main'}), packet=packet)
        append_decision(session, decision(packet, 'retract-heading', 'retract', target,
                                         {'decision_id': 'heading'}), packet=packet)
        actual, compilation, _ = self.project(packet, session)
        self.assertNotEqual(compilation['replay']['decision_status']['heading']['status'], 'active')
        self.assertNotIn('天正術', {t['surface'] for t in actual['terms']})

    def test_stable_view_orders_objects_without_mutating_projection(self):
        from workbench.annotation_projection import stable_golden_view
        packet = build_source_packet_from_units('.', 'sifen', ['sifen:section:38'], [], {})
        actual, _, _ = self.project(packet)
        for layer in ('terms', 'constructions', 'steps', 'flows', 'review_facets', 'links'):
            actual[layer].reverse()
        for term in actual['terms']:
            term['semantic_candidates'].reverse()
        before = deepcopy(actual)
        self.assertEqual(stable_golden_view(actual), self.fixture()['expected'])
        self.assertEqual(actual, before)

    def test_C5_kernel_fixed_expression_is_a_suggested_construction_only(self):
        from workbench.annotation_projection import project_scholar_source
        from unittest.mock import patch
        packet = synthetic_packet('實如法而一。')
        kernel = suggest_packet_semantics(packet)
        native = next(c for c in kernel['p']['fixed_expression_candidates'] if c['rule_id'] == 'C08')
        actual, compilation, _ = self.project(packet)
        fixed = [c for c in actual['constructions'] if c.get('origin') == 'domain_kernel_fixed_expression']
        self.assertEqual(len(fixed), 1)
        row = fixed[0]
        self.assertEqual((row['surface'], row['rule_id'], row['parse_status'], row['proposal']),
                         ('實如法而一', 'C08', 'suggested', 'division_construction'))
        self.assertEqual(row['span'], [native['span']['start'], native['span']['end']])
        self.assertIsNone(row['public_kind'])
        self.assertFalse(any(d.get('construction_id') == row['id'] for d in actual['projection_diagnostics']))
        kernel['p']['fixed_expression_candidates'] = []
        with patch('workbench.annotation_projection.suggest_packet_semantics', return_value=kernel):
            without = project_scholar_source(packet, compilation)
        self.assertEqual(actual['steps'], without['steps'])
        self.assertNotIn(row['id'], {c['id'] for c in without['constructions']})

    def test_C6_flow_ambiguity_counts_only_compatible_producers(self):
        from workbench.annotation_projection import project_scholar_source
        packet = build_source_packet_from_units('.', 'sifen', ['sifen:section:38'], [], {})
        _, compilation, questions = self.project(packet)
        imported = next(r for r in compilation['graph']['program']['linked']['imports'] if r['formal'] == '章法')
        imported['candidates'] = ['producer-a', 'producer-b', 'producer-c']
        for count, reason, expected in [(0, None, 'unresolved_source'), (1, None, 'unresolved_source'),
                                        (2, None, 'ambiguous_source'),
                                        (0, 'multiple source producers', 'ambiguous_source')]:
            with self.subTest(count=count, reason=reason):
                imported['candidate_evidence'] = [{'definition_id': ident, 'compatible': i < count}
                                                  for i, ident in enumerate(imported['candidates'])]
                imported['selection_reason'] = reason
                actual = project_scholar_source(packet, compilation, questions)
                self.assertEqual(next(f['status'] for f in actual['flows'] if f['formal'] == '章法'), expected)


if __name__ == '__main__':
    unittest.main()
