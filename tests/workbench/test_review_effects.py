"""Persisted K2 effects through real source adapters, service and exact executor.

Run with -m tests.workbench.test_review_effects to write .cache/k2bc/probe-effects.json. Every job
and source modification lives in a TemporaryDirectory, never the user's store.
"""
import copy
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from adjudication.anchors import anchor_for
from adjudication.term_claims import compose_term_interpretation
from analysis_parser import lexical
from source_adapters import corpus_review
from tools.parser_inspector.review_panel import release_interpretation_events
from workbench import review_jobs, service


ROOT = Path(__file__).resolve().parents[2]
ACTOR = {'type': 'scripted_fixture', 'id': 'k2bc-service-probe'}
EVIDENCE = {}
SYNTHETIC = {
    900: '以日率乘月率',
    901: '置甲量減一，名為乙量',
    902: '章月五。推天正術。置章月減一，名為乙量。推冬至術。置章月減一，名為丙量',
}


def selection(primary, contexts=()):
    return {'source_id': 'sifen', 'primary_unit_ids': [f'sifen:section:{primary}'],
            'context_unit_ids': [f'sifen:section:{n}' for n in contexts],
            'provided_scope': {'tradition': 'Han_Si_fen_li'}, 'selected_profiles': []}


def snapshot(response, execution=None):
    graph = response.get('graph')
    out = {'revision': response['job']['revision'], 'freshness': response['freshness'],
           'source_selection': response['job']['source_selection'],
           'question_count': len(response.get('questions', [])),
           'questions': [{'kind': q['kind'], 'quote': q['anchor']['quote'], 'title': q['title']}
                         for q in response.get('questions', [])],
           'history_count': len(response['job']['session']['decisions'])}
    if graph:
        out.update(event_counts=dict(Counter(e['kind'] for e in graph['events'])),
            constructions=[{'kind': c['kind'], 'quote': c['text'],
                            'slots': {k: v.get('text') for k, v in c.get('slots', {}).items()}}
                           for c in graph['construction_candidates'] if c['kind'] in ('load', 'multiply', 'divide', 'name')],
            quantities=[{k: v[k] for k in ('id', 'labels', 'unit', 'quantity_kind', 'representation',
                                          'coordinate_kind', 'index_base', 'step_unit', 'reference_origin',
                                          'counting_boundary', 'adjudication_decision_refs') if k in v}
                        for v in graph['value_instances'] if v.get('labels') or v.get('coordinate_kind')],
            imports=graph.get('program', {}).get('linked', {}).get('imports', []),
            managed_scopes=graph.get('managed_scopes', []),
            diagnostics=[d.get('kind') for d in graph.get('diagnostics', [])],
            decision_status=response['compilation']['replay']['decision_status'])
    if response.get('effects'):
        out['effects'] = {k: response['effects'][k] for k in ('baseline', 'structure_changed', 'message_en', 'evidence_changed')}
        out['effect_counts'] = {k: {change: len(rows) for change, rows in response['effects'][k].items()}
                                for k in ('grammar', 'quantity_semantics', 'documents', 'bindings')}
    if execution:
        out['execution'] = {k: execution[k] for k in ('schema', 'job_id', 'revision', 'branch_id', 'job_digest',
            'analysis_identity', 'inputs', 'status', 'named_outputs', 'unresolved')}
    return out


class ReviewEffectTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'config').mkdir()
        shutil.copyfile(ROOT / 'config/calendrical-ir-pipeline.json', self.root / 'config/calendrical-ir-pipeline.json')
        canonical = (ROOT / 'calendars-四分历.md').read_text(encoding='utf-8')
        text = canonical + '\n\n' + '\n\n'.join(f'{n}\t{text}' for n, text in SYNTHETIC.items()) + '\n'
        (self.root / 'calendars-四分历.md').write_text(text, encoding='utf-8')
        corpus_review.regenerate(self.root)

    def create(self, section, contexts=(), job_id='probe'):
        return service.create_review_job(self.root, job_id, selection(section, contexts))

    def apply(self, response, decisions=(), management_events=()):
        return service.apply_review_job_changes(self.root, response['job']['job_id'], decisions=decisions,
            management_events=management_events, expected_revision=response['job']['revision'],
            expected_digest=response['job_digest'])

    def row(self, response, identifier, action, anchor, payload, depends_on=()):
        row = service.review_decision(response, action, anchor, payload, ACTOR,
                                      'K2 source-bound service effect probe', depends_on=depends_on)
        row['decision_id'] = identifier
        return row

    def answer(self, response, question, option, identifier):
        row = self.row(response, identifier, option['action'], question['anchor'], option['payload'])
        events = [self.management(response, question, option, facet, identifier + '-' + facet)
                  for facet in option.get('management_facets', [])]
        return self.apply(response, [row], events)

    def management(self, response, question, option, facet, identifier, action='manage'):
        return {'event_id': identifier, 'action': action, 'target': question['anchor'], 'facet': facet,
                'branch_id': response['branch_id'], 'actor': ACTOR, 'created_at': '2026-09-20T00:00:00Z',
                'reason': 'Explicit ownership for this source quantity', 'semantic_target': option['semantic_target']}

    def retract(self, response, identifier, target, retraction_id):
        return self.apply(response, [self.row(response, retraction_id, 'retract', target, {'decision_id': identifier})])

    def execute(self, response, inputs):
        return service.execute_review_job(self.root, response['job']['job_id'], inputs,
            expected_revision=response['job']['revision'], expected_digest=response['job_digest'])

    def declare_root(self, response, name):
        question = next(q for q in response['questions'] if any(
            o['action'] == 'declare_parameter' and o['payload'].get('name') == name for o in q['options']))
        option = next(o for o in question['options'] if o['action'] == 'declare_parameter')
        return self.answer(response, question, option, 'external-' + str(response['job']['revision']))

    def counting(self, response, unit, doc_id=None):
        question = next(q for q in response['questions'] if q['kind'] == 'counting_convention'
                        and (doc_id is None or q['anchor']['doc_id'] == doc_id))
        option = next(o for o in question['options'] if o.get('payload', {}).get('facets', {}).get('step_unit') == unit)
        return question, option

    def scripted_counting_option(self, response, question, unit):
        """Synthetic probes supply their coordinate explicitly; production must not infer a 蔀."""
        construction = question['anchor']
        formal = question['evidence']['construction']['slots']['value']['text']
        address = {'definition_anchor': construction, 'construction_anchor': construction,
                   'construction_role': 'load', 'semantic_role': 'load', 'input_slot': 'value',
                   'formal': formal, 'branch_id': response['branch_id'], 'invocation_path': [construction]}
        facets = {'coordinate_kind': 'ordinal', 'index_base': 1, 'reference_origin': 'current_bu_start',
                  'counting_boundary': 'start_of_current_' + unit, 'step_unit': unit}
        return {'action': 'set_quantity_semantics',
                'payload': {'contract_version': '2.0', 'semantic_input': address, 'facets': facets},
                'management_facets': list(facets),
                'semantic_target': service.normalize_decision_target(
                    'set_quantity_semantics', {'semantic_input': address}, [construction])}

    def test_B1_B2_boundaries_and_local_interpretation_modes_have_real_effects(self):
        baseline = self.create(900)
        original_terms = copy.deepcopy(lexical.TERMS)
        source = baseline['effective_packet']
        first, second = anchor_for(source, 'sifen:900', 1, 3), anchor_for(source, 'sifen:900', 4, 6)
        boundaries = [self.row(baseline, ident, 'set_term_boundary', anchor, {'contract_version': '1.0', 'branch_id': 'main'})
                      for ident, anchor in [('left-boundary', first), ('right-boundary', second)]]
        self.assertFalse(any(c['kind'] == 'multiply' for c in baseline['graph']['construction_candidates']))
        bounded = self.apply(baseline, boundaries)
        multiply = next(c for c in bounded['graph']['construction_candidates'] if c['kind'] == 'multiply')
        self.assertEqual({key: multiply['slots'][key]['text'] for key in ('left', 'right')}, {'left': '日率', 'right': '月率'})
        self.assertEqual(sum(e['kind'] == 'multiply' for e in bounded['graph']['events']), 1)
        question = next(q for q in bounded['questions'] if q['kind'] == 'term_interpretation' and q['anchor']['quote'] == '日率')
        adopted_option = next(o for o in question['options'] if o['payload'].get('claim', {}).get('origin') == 'machine_adoption')
        adopted = self.answer(bounded, question, adopted_option, 'adopt-sense')
        reviewed_multiply = next(c for c in adopted['graph']['construction_candidates'] if c['kind'] == 'multiply')
        senses = reviewed_multiply['attributes']['reviewed_term_interpretations']
        self.assertEqual(senses[0]['slot'], 'left')
        self.assertEqual(senses[0]['expression'], adopted_option['payload']['claim']['expression'])
        self.assertEqual([e['kind'] for e in bounded['graph']['events']], [e['kind'] for e in adopted['graph']['events']])
        cleared = self.retract(adopted, 'adopt-sense', first, 'clear-adoption')
        question = next(q for q in cleared['questions'] if q['kind'] == 'term_interpretation' and q['anchor']['quote'] == '日率')
        reject = next(o for o in question['options'] if o['payload'].get('claim', {}).get('origin') == 'machine_rejection')
        rejected = self.answer(cleared, question, reject, 'reject-senses')
        self.assertEqual(rejected['compilation']['replay']['effective']['term_interpretations'][0]['claim']['origin'], 'machine_rejection')
        cleared = self.retract(rejected, 'reject-senses', first, 'clear-rejection')
        claim = compose_term_interpretation(first, 'main', adopted_option['payload']['claim']['expression'])
        composed = self.apply(cleared, [self.row(cleared, 'compose', 'set_term_interpretation', first, {'claim': claim})])
        self.assertEqual(composed['compilation']['replay']['effective']['term_interpretations'][0]['claim']['origin'], 'human_composition')
        self.assertEqual(len(composed['graph']['events']), len(bounded['graph']['events']))
        cleared = self.retract(composed, 'compose', first, 'clear-composition')
        restored = self.apply(cleared, [self.row(cleared, 'release-left', 'retract', first, {'decision_id': 'left-boundary'}),
            self.row(cleared, 'release-right', 'retract', second, {'decision_id': 'right-boundary'})])
        self.assertFalse(any(c['kind'] == 'multiply' for c in restored['graph']['construction_candidates']))
        self.assertEqual(lexical.TERMS, original_terms)
        EVIDENCE['B1'] = {'source': SYNTHETIC[900], 'synthetic': True, 'before': snapshot(baseline),
                          'after': snapshot(bounded), 'retracted': snapshot(restored), 'global_lexicon_unchanged': True}
        EVIDENCE['B2'] = {'adopted_expression': adopted_option['payload']['claim']['expression'],
            'slot': 'left', 'adopted': snapshot(adopted), 'rejected': snapshot(rejected), 'human_composed': snapshot(composed),
            'claim_origins': {'adopted': adopted_option['payload']['claim']['origin'],
                'rejected': rejected['compilation']['replay']['effective']['term_interpretations'][0]['claim']['origin'],
                'composed': composed['compilation']['replay']['effective']['term_interpretations'][0]['claim']['origin']},
            'numeric_operations_added_by_interpretation': 0}

    def test_C2_C7_C9_neutral_management_last_question_and_reviewed_execution(self):
        response = self.create(901)
        baseline = self.declare_root(response, '甲量')
        self.assertEqual(len(baseline['questions']), 1)
        question = next(q for q in baseline['questions'] if q['kind'] == 'counting_convention')
        option = self.scripted_counting_option(baseline, question, 'month')
        numeric_baseline = self.execute(baseline, {'甲量': 5})
        self.assertEqual(numeric_baseline['named_outputs']['main:乙量'], 4)
        self.assertEqual(next(v['unit'] for v in baseline['graph']['value_instances'] if '乙量' in v['labels']), 'year')
        event = self.management(baseline, question, option, 'coordinate_kind', 'manage-ordinal')
        managed = self.apply(baseline, management_events=[event])
        numeric_managed = self.execute(managed, {'甲量': 5})
        self.assertNotIn('main:乙量', numeric_managed['named_outputs'])
        self.assertEqual(managed['graph']['managed_scopes'][0]['status'], 'unresolved')
        positive = self.answer(managed, question, option, 'month-ordinal')
        numeric_positive = self.execute(positive, {'甲量': 5})
        self.assertEqual(numeric_positive['status'], 'executed')
        self.assertEqual(numeric_positive['named_outputs']['main:乙量'], 4)
        value = next(v for v in positive['graph']['value_instances'] if '乙量' in v['labels'])
        self.assertEqual((value['unit'], value['coordinate_kind'], value['index_base']), ('month', 'elapsed', 0))
        self.assertFalse(positive['questions'])
        self.assertTrue(positive['effects']['quantity_semantics']['added'])
        self.assertTrue(positive['job']['session']['decisions'])
        self.assertIn('syntax', positive['graph'])
        retracted = self.retract(positive, 'month-ordinal', question['anchor'], 'retract-month')
        self.assertEqual(len(retracted['questions']), 1)
        self.assertTrue(service.review_execution_stale(numeric_positive, retracted))
        numeric_retracted = self.execute(retracted, {'甲量': 5})
        self.assertNotIn('main:乙量', numeric_retracted['named_outputs'])
        releases = release_interpretation_events(
            review_jobs.management_state(retracted['job']), response['branch_id'], ACTOR,
            'Release this interpretation takeover', '2026-09-20T00:00:00Z')
        self.assertEqual(len(releases), 5)
        restored = self.apply(retracted, management_events=releases)
        self.assertEqual(restored['job']['revision'], retracted['job']['revision'] + 1)
        numeric_restored = self.execute(restored, {'甲量': 5})
        self.assertEqual(numeric_restored['named_outputs']['main:乙量'], 4)
        self.assertEqual(next(v['unit'] for v in restored['graph']['value_instances'] if '乙量' in v['labels']), 'year')
        self.assertEqual(review_jobs.load_job(self.root, 'probe'), restored['job'])
        EVIDENCE['C2'] = {'source': SYNTHETIC[901], 'synthetic': True,
            'unmanaged': snapshot(baseline, numeric_baseline), 'managed_undecided': snapshot(managed, numeric_managed),
            'approved': snapshot(positive, numeric_positive), 'retracted': snapshot(retracted, numeric_retracted),
            'unmanaged_again': snapshot(restored, numeric_restored)}
        EVIDENCE['C7'] = {'questions_before': 1, 'questions_after': 0, 'questions_after_retraction': 1,
            'effects_available': bool(positive['effects']), 'history_entries_after_answer': len(positive['job']['session']['decisions']),
            'inspection_graph_preserved': True, 'ui_visibility_requires_browser_verification': True}
        EVIDENCE['C9'] = {'execution': snapshot(positive, numeric_positive)['execution'],
                          'stale_after_retraction': True, 'rerun': snapshot(retracted, numeric_retracted)['execution']}

    def test_C1_real_sifen_year_coordinate_retains_source_arithmetic(self):
        before = self.create(38, [15, 16])
        question, option = self.counting(before, 'year')
        after = self.answer(before, question, option, 'year-ordinal')
        numeric = self.execute(after, {'入蔀年': 5})
        subs = [e for e in after['graph']['events'] if e['kind'] == 'subtract' and e['rule_id'] == 'V3_ORDINAL']
        self.assertEqual(len(subs), 1)
        value = next(v for v in after['graph']['value_instances'] if v['id'] == subs[0]['writes']['result'])
        self.assertEqual((value['unit'], value['coordinate_kind'], value['index_base']), ('year', 'elapsed', 0))
        self.assertEqual(numeric['values'][value['id']], 4)
        EVIDENCE['C1'] = {'source_unit': 'sifen:section:38', 'before': snapshot(before), 'after': snapshot(after, numeric),
            'source_subtract_operations': 1, 'elapsed_years': 4, 'input_ordinal': 5}

    def test_C3_one_producer_two_calls_have_isolated_quantity_reads(self):
        before = self.create(902)
        question = next(q for q in before['questions'] if q['kind'] == 'counting_convention')
        option = self.scripted_counting_option(before, question, 'month')
        after = self.answer(before, question, option, 'consumer-A-month')
        numeric = self.execute(after, {})
        graph = after['graph']; values = {v['id']: v for v in graph['value_instances']}
        subs = [e for e in graph['events'] if e['kind'] == 'subtract']
        self.assertEqual([values[e['writes']['result']]['unit'] for e in subs], ['month', 'year'])
        self.assertNotEqual(subs[0]['call_id'], subs[1]['call_id'])
        shared = next(e['writes']['result'] for e in graph['events'] if e['kind'] == 'parameter')
        view = next(e for e in graph['events'] if e['rule_id'] == 'REVIEW_QUANTITY_READ')
        other_load = [e for e in graph['events'] if e['kind'] == 'load'][1]
        self.assertEqual(view['reads']['value'], shared)
        self.assertEqual(other_load['reads']['value'], shared)
        self.assertNotIn('coordinate_kind', values[shared])
        self.assertEqual((numeric['named_outputs']['main:乙量'], numeric['named_outputs']['main:丙量']), (4, 4))
        EVIDENCE['C3'] = {'source': SYNTHETIC[902], 'synthetic': True, 'before': snapshot(before), 'after': snapshot(after, numeric),
            'shared_producer_value': shared, 'consumer_call_ids': [e['call_id'] for e in subs],
            'result_units': ['month', 'year'], 'producer_metadata_unchanged': True}

    def test_C4_context_source_binding_retraction_and_context_withdrawal(self):
        before = self.create(39, [14, 15, 16, 19])
        doc = service.review_context_document(self.root, 'sifen', 'sifen:section:38')
        anchor = anchor_for(before['effective_packet'], 'sifen:39', 0, 5)
        attached = self.apply(before, [self.row(before, 'attach-38', 'attach_context', anchor, {'document': doc})])
        form = next(f for f in attached['review_forms'] if f['formal'] == '入蔀積月')
        producer = next(p for p in form['producers'] if p['anchor']['doc_id'] == 'sifen:38' and p['output_port'] == '積月')
        payload = {'consumer_definition_anchor': form['consumer_anchor'], 'formal': form['formal'],
                   'producer_definition_anchor': producer['anchor'], 'output_port': producer['output_port']}
        binding = self.row(attached, 'bind-month', 'bind_value', form['anchors'][0], payload)
        self.assertIn('attach-38', binding['depends_on'])
        bound = self.apply(attached, [binding])
        imports = bound['graph']['program']['linked']['imports']
        self.assertTrue(any(i.get('formal') == '入蔀積月' and i.get('selection_reason') == 'reviewed producer/port constraint' for i in imports))
        quantity_anchor = anchor_for(bound['effective_packet'], 'sifen:39', 6, 11)
        quantity_payload = {'semantic_input': {'definition_anchor': form['consumer_anchor'], 'construction_anchor': quantity_anchor,
            'construction_role': 'load', 'semantic_role': 'load', 'input_slot': 'value', 'formal': '入蔀積月',
            'branch_id': 'main', 'invocation_path': [form['consumer_anchor']]}, 'facets': {'unit': 'month'}}
        dependent = self.apply(bound, [self.row(bound, 'dependent-month-kind', 'set_quantity_semantics', quantity_anchor,
                                               quantity_payload, depends_on=['bind-month'])])
        self.assertTrue(any('dependent-month-kind' in v.get('adjudication_decision_refs', []) for v in dependent['graph']['value_instances']))
        retracted = self.retract(dependent, 'bind-month', form['anchors'][0], 'retract-binding')
        self.assertFalse(retracted['compilation']['replay']['effective']['bindings'])
        self.assertEqual(retracted['compilation']['replay']['decision_status']['dependent-month-kind']['status'], 'needs_revalidation')
        self.assertFalse(retracted['compilation']['replay']['effective']['quantity_semantics'])
        rebound = self.apply(retracted, [self.row(retracted, 'bind-month-again', 'bind_value', form['anchors'][0], payload)])
        withdrawn = self.retract(rebound, 'attach-38', anchor, 'withdraw-context')
        self.assertEqual(withdrawn['compilation']['replay']['decision_status']['bind-month-again']['status'], 'needs_revalidation')
        self.assertFalse(withdrawn['compilation']['replay']['effective']['bindings'])
        self.assertNotIn('sifen:38', [d['doc_id'] for d in withdrawn['effective_packet'].get('context_documents', [])])
        EVIDENCE['C4'] = {'before': snapshot(before), 'attached': snapshot(attached), 'bound': snapshot(bound),
            'dependent_interpretation': snapshot(dependent),
            'binding_retracted': snapshot(retracted), 'context_withdrawn': snapshot(withdrawn),
            'binding_depends_on_context': True, 'binding_retraction_invalidates_dependent_interpretation': True}

    def test_C5_real_month_day_relation_and_fraction_numerator(self):
        before = self.create(39, [14, 15, 16, 19, 38])
        question = next(q for q in before['questions'] if q['kind'] == 'reviewed_relation')
        option = next(o for o in question['options'] if o['action'] == 'approve_reviewed_relation')
        after = self.answer(before, question, option, 'month-day-relation')
        numeric = self.execute(after, {'入蔀年': 2})
        division = next(e for e in after['graph']['events'] if e['kind'] == 'divmod'
                        and e['source_spans'][0]['doc_id'] == 'sifen:39' and e['source_spans'][0]['start'] == 18)
        values = {v['id']: v for v in after['graph']['value_instances']}
        remainder = values[division['writes']['remainder']]
        self.assertEqual(numeric['event_results'][division['id']], {'quotient': 354, 'remainder': 348})
        self.assertEqual(remainder['unit'], 'day_fraction')
        self.assertEqual(remainder['representation']['denominator_id'], division['reads']['divisor'])
        self.assertEqual(numeric['values'][division['reads']['divisor']], 940)
        self.assertTrue(any(q['value'] == 348 and q['representation'].get('denominator_value') == 940
                            for q in numeric['output_quantities'].values()))
        self.assertIn('month-day-relation', remainder['adjudication_decision_refs'])
        self.assertEqual([e['kind'] for e in before['graph']['events']], [e['kind'] for e in after['graph']['events']])
        parameter_values = {e['attributes']['name']: e['attributes']['value'] for e in after['graph']['events']
                            if e['kind'] == 'parameter' and e['attributes']['name'] in ('蔀日', '蔀月')}
        multiply = next(e for e in after['graph']['events'] if e['kind'] == 'multiply'
                        and e['source_spans'][0]['doc_id'] == 'sifen:39')
        self.assertEqual(parameter_values, {'蔀月': 940, '蔀日': 27759})
        self.assertEqual(numeric['event_results'][multiply['id']]['result'], 333108)
        EVIDENCE['C5'] = {'source_unit': 'sifen:section:39', 'before': snapshot(before), 'after': snapshot(after, numeric),
            'existing_arithmetic_preserved': True, 'whole_days': 354, 'remainder_numerator': 348,
            'remainder_denominator': 940, 'remainder_unit': 'day_fraction', 'interpretation': '354 whole days plus 348/940 day',
            'parameter_values': parameter_values, 'multiply_result': 333108,
            'source_operations': [{k: e[k] for k in ('id', 'kind', 'reads', 'writes', 'source_spans', 'call_id')}
                                  for e in (multiply, division)]}

    def test_C8_old_runtime_job_read_export_only_and_fresh_same_selection(self):
        current = self.create(901, job_id='old-job')
        old = copy.deepcopy(current['job'])
        old['session']['identity_locks']['engine']['sha256'] = 'pre-BC-runtime-identity'
        review_jobs.write_job_atomic(self.root, old)
        path = review_jobs.job_path(self.root, 'old-job'); before_bytes = path.read_bytes()
        stale = service.compile_review_job(self.root, 'old-job')
        self.assertEqual(stale['freshness']['status'], 'stale')
        self.assertIsNone(stale['graph'])
        self.assertEqual(json.loads(review_jobs.export_job(stale['job'])), old)
        with self.assertRaisesRegex(ValueError, 'runtime_identity_changed'):
            self.execute(stale, {})
        fresh = service.create_review_job(self.root, 'fresh-job', copy.deepcopy(old['source_selection']))
        self.assertEqual(fresh['freshness']['status'], 'current')
        self.assertFalse(fresh['job']['session']['decisions'])
        self.assertNotEqual(fresh['job']['session']['identity_locks'], old['session']['identity_locks'])
        self.assertEqual(path.read_bytes(), before_bytes)
        EVIDENCE['C8'] = {'old': snapshot(stale), 'fresh': snapshot(fresh), 'same_source_selection': True,
            'old_job_bytes_unchanged': True, 'old_execution_rejected': True, 'export_preserves_identity': True,
            'automatic_decision_migration': False, 'old_identity_is_simulated_in_isolated_job': True}


if __name__ == '__main__':
    run = unittest.main(exit=False)
    if run.result.wasSuccessful():
        destination = ROOT / '.cache' / 'k2bc' / 'probe-effects.json'
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps({'schema': 'K2BCProbeEffects/1',
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'method': 'Real corpus adapters and persisted temporary ReviewJobs; service API; existing exact executor; no compiler mocks.',
            'probes': EVIDENCE}, ensure_ascii=False, indent=2), encoding='utf-8')
        print('Evidence: ' + str(destination))
    raise SystemExit(not run.result.wasSuccessful())
