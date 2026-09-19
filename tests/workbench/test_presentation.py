"""Semantic contracts: language must not add facts or change compiler output."""
import copy
import unittest
from pathlib import Path
from unittest.mock import patch
import json
import tempfile
import threading
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[2]


class PresentationTests(unittest.TestCase):
    def test_registry_exhaustiveness_and_entry_contract(self):
        from analysis_parser.ontology import REGISTRY, codes, entry, label_en, INSPECTOR_DEFAULT_CATEGORIES
        from analysis_parser.construction_ir import GRAMMAR, EXACT
        from adjudication.registry import OPERATION_CONTRACTS, QUANTITY_UNITS
        from adjudication.session import ACTIONS
        from analysis_parser.quantity_semantics import UNIT_QUANTITY_KINDS
        for domain, expected in [('construction', {r[0] for r in GRAMMAR} | set(EXACT) | set(OPERATION_CONTRACTS)),
                                 ('syntax', {r[1] for r in GRAMMAR}), ('action', ACTIONS),
                                 ('unit', set(QUANTITY_UNITS) | set(UNIT_QUANTITY_KINDS))]:
            self.assertLessEqual(expected, codes(domain))
        for (domain, code), item in REGISTRY.items():
            self.assertEqual(item['code'], code)
            for field in ('category', 'hierarchy', 'label', 'definition', 'methodology', 'required_fields', 'must_not_infer'):
                self.assertTrue(item[field], (domain, code, field))
            if domain in INSPECTOR_DEFAULT_CATEGORIES:
                self.assertTrue(item['definition_en'], (domain, code, 'definition_en'))
        with self.assertRaisesRegex(ValueError, 'unregistered_ontology_code'):
            entry('review_state', 'new_unregistered_state')

    def test_authored_english_labels_are_available_without_code_generation(self):
        from analysis_parser.ontology import REGISTRY, label_en, TECHNICAL_ONLY_ENGLISH
        unsupported = TECHNICAL_ONLY_ENGLISH
        missing = {(domain, code) for (domain, code), item in REGISTRY.items()
                   if not item['label_en']} - unsupported
        self.assertEqual(missing, set())
        self.assertEqual(label_en('operation', 'divmod'), 'Divide with remainder')
        self.assertEqual(label_en('port', 'dividend'), 'Dividend')
        with self.assertRaisesRegex(ValueError, 'missing_english_label'):
            label_en('action_variant', 'defer:unresolved')
        with self.assertRaisesRegex(ValueError, 'missing_english_label'):
            label_en('profile', 'ST_elapsed')

    def test_semantic_goldens_and_must_not_say(self):
        from workbench.presentation import present_question
        cases = [
            ('missing_input', 'missing_import', '所需输入尚未绑定', ['原文缺失', '作者省略', '输入错误']),
            ('no_legal_candidate', 'unresolved_parser', '当前规则未能解释这段文字', ['原文错误', '无计算意义']),
            ('no_legal_candidate', 'incomplete_construction', '当前构式尚待规则要求的后续部分', ['原文省略', '原文缺少', '作者漏写']),
            ('quantity_semantics', 'unknown_quantity_semantics', '数量含义尚待确定', ['数值错误', '单位错误']),
            ('stale_session', 'stale_identity', '已有审定需要重新核验', ['已完成审定', '决定已应用']),
            ('decision_conflict', ['multiple_active_decisions_for_slot'], '同一判断对象存在冲突决定', ['已自动选择', '后一次有效']),
            ('invalid_review_binding', 'binding_not_structurally_compatible', '指定的绑定未通过后端结构检查', ['原文错误', '已接受绑定', '已修复']),
            ('ontology_extension_required', 'schema_extension_required', '现有类型目录需要扩展', ['已经支持', '图已闭合']),
        ]
        for kind, reason, expected, prohibited in cases:
            with self.subTest(kind=kind, reason=reason):
                row = {'id': 'q', 'kind': kind, 'reason': reason, 'severity': 'blocking',
                       'source_anchors': [], 'suggested_actions': ['defer'], 'affected_outputs': [],
                       'candidate_options': [], 'details': {'missing_or_conflicting_inputs': ['除之']}}
                original = copy.deepcopy(row)
                result = present_question(row)
                self.assertIn(expected, result['text'])
                self.assertEqual(result['actions'][0]['code'], 'defer')
                for phrase in prohibited:
                    self.assertNotIn(phrase, result['text'])
                self.assertEqual(row, original)
        with self.assertRaisesRegex(ValueError, 'unregistered_ontology_code'):
            present_question({**row, 'kind': 'invented_question'})

    def test_real_outputs_and_presentation_do_not_change_structured_facts(self):
        from workbench.service import open_adjudication
        from workbench.presentation import build_presentation
        for ident in ('sifen-3-5', 'sifen-3-7-alternative'):
            response = open_adjudication(ROOT, ident)
            snapshot = copy.deepcopy(response)
            vm = build_presentation(response)
            self.assertTrue(vm['nodes'])
            self.assertTrue(vm['questions'])
            self.assertEqual(response, snapshot)
            self.assertEqual(vm, response['presentation'])
            expected_ports = {port for node in response['projection']['nodes'] for port in node['writes']}
            expected_ports.update(port for frame in response['projection']['frames'] for port in frame.get('return_ports', {}))
            self.assertEqual({item['code'] for item in vm['controls']['binding-port']}, expected_ports)
            for original, shown in zip(response['projection']['review_queue']['items'], vm['questions']):
                self.assertEqual(original['suggested_actions'], [a['code'] for a in shown['actions']])
                self.assertEqual(original['source_anchors'], shown['source_anchors'])
            for path in [('summary', key) for key in ('graph_status', 'review_status', 'execution_status', 'comparison_status')] + [
                    ('projection', 'nodes', 0, 'kind'), ('projection', 'quantities', 0, 'unit'),
                    ('bundle', 'replay', 'status'), ('stages', 0, 'status'),
                    ('graph', 'construction_candidates', 0, 'status'),
                    ('bundle', 'validation', 'valid_for_complete_export')]:
                broken = copy.deepcopy(response)
                owner = broken
                for part in path[:-1]:
                    owner = owner[part]
                owner[path[-1]] = 'new_unregistered_code'
                with self.subTest(path=path), self.assertRaisesRegex(ValueError, 'unregistered_ontology_code'):
                    build_presentation(broken)

    def test_actual_resegment_and_retract_states_have_language(self):
        from workbench.service import open_adjudication, apply_adjudication_decision
        from adjudication.anchors import anchor_for
        opened = open_adjudication(ROOT, 'sifen-3-5')
        packet = opened['source_packet']
        target = anchor_for(packet, 'sifen:38', 12, 17)
        decision = {'decision_id': 'language-segment', 'actor': {'type': 'scripted_fixture', 'id': 'presentation-test'},
                    'created_at': '2026-09-18T00:00:00Z', 'branch_id': 'main', 'action': 'resegment',
                    'targets': [target], 'payload': {'segments': [anchor_for(packet, 'sifen:38', 12, 14), anchor_for(packet, 'sifen:38', 14, 17)]},
                    'evidence_refs': ['source:test'], 'reason': 'language coverage', 'depends_on': []}
        result = apply_adjudication_decision(ROOT, 'sifen-3-5', opened['session'], decision, 'main')
        self.assertTrue(result['presentation']['questions'])
        self.assertTrue(result['presentation']['history'][0]['status'])
        restored = apply_adjudication_decision(ROOT, 'sifen-3-5', result['session'],
                      {**decision, 'decision_id': 'language-retract', 'action': 'retract', 'payload': {'decision_id': decision['decision_id']}}, 'main')
        self.assertEqual(restored['graph']['events'], opened['graph']['events'])
        self.assertIn('已撤销', restored['presentation']['history'][0]['status'])

    def test_ontology_http_and_workbench_share_live_registry(self):
        from workbench.api import make_server
        from analysis_parser.ontology import REGISTRY, entry
        with tempfile.TemporaryDirectory() as directory:
            site = Path(directory)
            (site / 'adjudication').mkdir()
            (site / 'adjudication/index.html').write_text('<html data-baseurl="/">', encoding='utf-8')
            server = make_server(ROOT, 0, site)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            origin = f'http://127.0.0.1:{server.server_port}'
            try:
                changed = {**entry('issue', 'missing_input'), 'label': '目录实时更新的输入问题'}
                new = {**changed, 'code': 'new_runtime_issue'}
                with patch.dict(REGISTRY, {('issue', 'missing_input'): changed, ('issue', new['code']): new}):
                    with urlopen(origin + '/api/ontology') as response:
                        reference = json.load(response)
                    with urlopen(origin + '/api/adjudication/sifen-3-5') as response:
                        analysis = json.load(response)
                    self.assertIn(new, reference['entries'])
                    self.assertIn(changed, reference['entries'])
                    self.assertIn(changed['label'], [q['label'] for q in analysis['presentation']['questions']])
            finally:
                server.shutdown()
                server.server_close()
                thread.join()

    def test_actual_authored_candidate_does_not_claim_rule_or_human_trial(self):
        from workbench.service import open_adjudication, apply_adjudication_decision
        from adjudication.anchors import anchor_for
        opened = open_adjudication(ROOT, 'sifen-3-7-alternative')
        target = anchor_for(opened['source_packet'], 'sifen:40', 9, 14)
        decision = {'decision_id': 'authored-probe', 'actor': {'type': 'scripted_fixture', 'id': 'presentation-test'},
                    'created_at': '2026-09-18T00:00:00Z', 'branch_id': 'main', 'action': 'assemble_known_structure',
                    'targets': [target], 'payload': {'replace_automatic': True, 'candidates': [
                        {'kind': 'load', 'slots': {'value': {'ref_kind': 'source_anchor', 'anchor': target}}}]},
                    'evidence_refs': ['source:test'], 'reason': 'software language test, not scholarly interpretation', 'depends_on': []}
        result = apply_adjudication_decision(ROOT, 'sifen-3-7-alternative', opened['session'], decision, 'main')
        authored = next(c for c in result['presentation']['candidates'] if c['provenance']['attributes'].get('authored_structure'))
        self.assertIn('由审定决定构造', authored['evidence'])
        self.assertIn('脚本验收', authored['evidence'])
        self.assertNotIn('规则识别', authored['evidence'])
        self.assertNotIn('研究者操作', authored['evidence'])

    def test_registry_extension_updates_reference_and_workbench_without_second_mapping(self):
        from analysis_parser.ontology import REGISTRY, entry
        from workbench.presentation import ontology_reference, present_question
        new = {**entry('issue', 'missing_input'), 'code': 'new_review_issue', 'label': '新登记的问题', 'definition': '新登记的定义'}
        with patch.dict(REGISTRY, {('issue', new['code']): new}):
            item = present_question({'kind': new['code'], 'reason': None, 'severity': 'review',
                                     'suggested_actions': [], 'source_anchors': [], 'affected_outputs': []})
            self.assertEqual(item['label'], new['label'])
            self.assertIn(new, ontology_reference()['entries'])

if __name__ == '__main__':
    unittest.main()
