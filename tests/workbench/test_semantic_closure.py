from copy import deepcopy
import unittest

from adjudication import compile_reviewed, new_session, append_decision
from adjudication.anchors import anchor_for
from adjudication.term_claims import compose_term_interpretation
from tests.adjudication.test_term_claims import packet
from tests.adjudication.test_acceptance_core import decision
from workbench.annotation_projection import project_scholar_source, diff_scholar_source
from workbench.question_presenter import build_questions
from workbench.scholar_renderer import build_renderer_model, selection_details
from workbench.procedure_model import build_procedure_model


def identity_case():
    p = packet('置章月，名為積月')
    s = new_session(p, 'closure-test')
    a = anchor_for(p, 'p', 1, 3)
    expression = {'op': 'concept', 'concept_id': 'time.lunation'}
    # Use a real source-applicable registered expression from the actual UI.
    baseline = compile_reviewed(p, s)
    q = next(q for q in build_questions(p, baseline, []) if q['decision_target']['start'] == 1 and q['kind'] == 'term_interpretation')
    option = next(o for o in q['options'] if o['payload'].get('claim', {}).get('expression'))
    append_decision(s, decision(p, 'meaning', 'set_term_interpretation', a, option['payload']), packet=p)
    return p, s, a


class ClosureProjectionTests(unittest.TestCase):
    def test_real_replay_conflicting_reviews_remain_visible_and_do_not_propagate(self):
        p = packet('置入蔀年，名為積月')
        s = new_session(p, 'real-conflict')
        q = next(q for q in build_questions(p, compile_reviewed(p, s), []) if q['kind'] == 'term_interpretation' and q['anchor']['start'] == 1)
        options = [o for o in q['options'] if o.get('payload', {}).get('claim', {}).get('origin') == 'machine_adoption']
        self.assertGreaterEqual(len(options), 2)
        for i, option in enumerate(options[:2]):
            append_decision(s, decision(p, 'conflict-' + str(i), option['action'], q['anchor'], option['payload']), packet=p)
        compiled = compile_reviewed(p, s)
        self.assertEqual({v['status'] for v in compiled['replay']['decision_status'].values()}, {'conflicted'})
        self.assertTrue(compiled['semantic_closure']['conflicts'])
        self.assertFalse(any(a['usable'] and a['authority'] == 'derived' for a in compiled['semantic_closure']['assertions']))
        qs = [q for q in build_questions(p, compiled, []) if q['kind'] == 'semantic_conflict']
        self.assertTrue(qs)
        self.assertEqual({o['payload']['decision_id'] for o in qs[0]['options'] if o['action'] == 'retract'}, {'conflict-0', 'conflict-1'})

    def test_supported_conflict_has_real_question_and_retract_action(self):
        p, s, a = identity_case()
        c = compile_reviewed(p, s)
        row = next(r for r in c['semantic_closure']['assertions'] if r['authority'] == 'reviewed')
        c['semantic_closure']['conflicts'].append({'id': 'test-conflict', 'target': row['target'],
            'facet': 'expression', 'reason': 'explicit_rejection', 'assertion_ids': [row['id']], 'decision_ids': ['meaning']})
        q = next(q for q in build_questions(p, c, []) if q['kind'] == 'semantic_conflict')
        self.assertTrue(any(o['action'] == 'retract' and o['payload']['decision_id'] == 'meaning' for o in q['options']))
        projection = project_scholar_source(p, c, [q])
        self.assertTrue(any(f['facet'] == 'semantic_conflict' for f in projection['review_facets']))

    def test_identity_derives_named_term_and_resolves_real_question(self):
        p, s, anchor = identity_case()
        compiled = compile_reviewed(p, s)
        qs = build_questions(p, compiled, [])
        projection = project_scholar_source(p, compiled, qs)
        derived = next(t for t in projection['terms'] if t['surface'] == '積月')
        self.assertTrue(derived['derived_assertions'])
        self.assertFalse(derived['reviewed_claims'])
        self.assertFalse(any(q['kind'] == 'term_interpretation' and q['decision_target']['start'] == 6 for q in qs))
        model = build_renderer_model(p, projection, qs)
        self.assertEqual(model['objects'][derived['id']]['gloss']['kind'], 'derived')
        details = selection_details(model, derived['id'])
        self.assertTrue(details['semantic_provenance'])
        self.assertTrue(any(d.get('object_id') for row in details['semantic_provenance'] for d in row['dependencies']))
        procedure = build_procedure_model(projection)
        self.assertTrue(any(n.get('semantic_summary') for n in procedure['nodes']))

    def test_retraction_restores_question_and_projection(self):
        p, s, a = identity_case()
        before = compile_reviewed(p, s)
        q1 = build_questions(p, before, [])
        p1 = project_scholar_source(p, before, q1)
        append_decision(s, decision(p, 'retract-meaning', 'retract', a, {'decision_id': 'meaning'}), packet=p)
        after = compile_reviewed(p, s)
        q2 = build_questions(p, after, [])
        p2 = project_scholar_source(p, after, q2)
        self.assertGreater(len(q2), len(q1))
        self.assertFalse(p2['semantic_closure']['assertions'])
        delta = diff_scholar_source(p1, p2)
        self.assertGreater(delta['summary']['derived_assertions_removed'], 0)
        self.assertEqual(after['semantic_closure'], compile_reviewed(p, s)['semantic_closure'])

    def test_internal_id_renumbering_keeps_public_closure_identity(self):
        p, s, _ = identity_case()
        c = compile_reviewed(p, s)
        original = project_scholar_source(p, c, [])['semantic_closure']
        # Recursive replacement mimics fresh compiler value/event allocation.
        ids = {r['id']: 'renumbered-' + r['id'] for layer in ('events', 'value_instances') for r in c['graph'][layer]}
        def replace(v):
            if isinstance(v, dict): return {k: replace(x) for k,x in v.items()}
            if isinstance(v, list): return [replace(x) for x in v]
            return ids.get(v, v) if isinstance(v, str) else v
        changed = project_scholar_source(p, replace(c), [])['semantic_closure']
        self.assertEqual(original, changed)
