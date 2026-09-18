"""Artifact freshness is about consumed units, not corpus review timestamps."""
import unittest
from tests import test_segmentation_review as fixtures
from source_adapters import corpus


class DependencyTests(unittest.TestCase):
    setUp = fixtures.ReviewTests.setUp
    state = fixtures.ReviewTests.state
    act = fixtures.ReviewTests.act
    unit = fixtures.ReviewTests.unit
    def test_unit_hash_excludes_accept_and_actor_but_includes_type(self):
        unit = self.unit(38)
        import hashlib
        selection = {'unit_id': unit['id'], 'sha256': hashlib.sha256(unit['text_original'].encode()).hexdigest()}
        document = lambda: corpus._document_from_unit({'id': 'sifen'}, self.state()['effective'], selection)
        before = document()
        self.act('accept', unit)
        self.assertEqual(before, document())
        self.act('set_type', unit, type='discourse')
        self.assertNotEqual(before['source']['unit_index_sha256'], document()['source']['unit_index_sha256'])

    def test_dependency_dag_is_local_transitive_and_survives_reload(self):
        from source_adapters import dependencies as dep
        def packet(section, context=()):
            import hashlib
            units = [self.unit(i) for i in (section, *context)]
            docs = [corpus._document_from_unit({'id': 'sifen'}, self.state()['effective'],
                    {'unit_id': u['id'], 'sha256': hashlib.sha256(u['text_original'].encode()).hexdigest()}) for u in units]
            return {'primary_documents': docs[:1], 'context_documents': docs[1:]}
        records = []
        for section in (38, 39, 40):
            parser = dep.artifact('parser', {'section': section}, packet=packet(section))
            graph = dep.artifact('graph', {'graph': section}, parents=[parser])
            execution = dep.artifact('execution', {'result': section}, parents=[graph])
            records.extend([parser, graph, execution])
        comparison = dep.artifact('comparison', {}, parents=[records[1], records[4]])
        contextual = dep.artifact('parser', {}, packet=packet(40, (39,)))
        records.extend([comparison, contextual])
        import json
        records = json.loads(json.dumps(records))  # same contract in an exported result
        self.act('accept', self.unit(39))
        self.assertTrue(all(r['status'] == 'valid' for r in dep.validate(self.root, records)))
        self.act('set_type', self.unit(39), type='discourse')
        statuses = dep.validate(self.root, records)
        self.assertEqual([r['status'] for r in statuses],
                         ['valid']*3 + ['stale']*3 + ['valid']*3 + ['stale', 'stale'])
        self.assertTrue(any('upstream' in reason for reason in statuses[4]['reasons']))
        # Removed IDs after merge/split cannot accidentally remain valid.
        self.act('merge_down', self.unit(38))
        self.assertEqual(dep.validate(self.root, records)[0]['status'], 'stale')

    def test_real_inspector_metadata_refresh_does_not_modify_raw_outputs(self):
        from tools.parser_inspector import runner
        from unittest.mock import patch
        import json
        packet = corpus.build_source_packet(self.root, corpus.list_procedures(self.root)[0]['id'])['source_packet']
        with patch.object(runner, 'OUTPUT', self.root / 'output/current'):
            result = runner.run(packet, 'compile', root=self.root)
            self.assertTrue(result['run.json'].get('artifacts'))
            unchanged = (runner.OUTPUT / 'run.json').read_bytes()
            runner.refresh_dependencies(self.root)
            self.assertEqual((runner.OUTPUT / 'run.json').read_bytes(), unchanged)
            before = {p.name: p.read_bytes() for p in runner.OUTPUT.glob('*.json') if p.name != 'run.json'}
            self.act('set_type', self.unit(38), type='discourse')
            state = runner.refresh_dependencies(self.root)
            self.assertTrue(any(r['status'] == 'stale' for r in state['freshness']))
            self.assertEqual(before, {p.name: p.read_bytes() for p in runner.OUTPUT.glob('*.json') if p.name != 'run.json'})
            self.assertEqual(json.loads((runner.OUTPUT / 'run.json').read_bytes()), state)

    def test_real_workbench_graph_and_execution_carry_dependencies(self):
        from workbench.service import compile_procedure
        from source_adapters import dependencies as dep
        procedure_id = corpus.list_procedures(self.root)[0]['id']
        result = compile_procedure(self.root, procedure_id, {})
        records = result.get('artifacts', [])
        self.assertEqual([r['kind'] for r in records], ['parser', 'graph', 'execution'])
        self.act('set_type', self.unit(38), type='discourse')
        self.assertEqual([r['status'] for r in dep.validate(self.root, records)], ['stale']*3)

    def test_status_endpoint_checks_saved_real_result_against_current_units(self):
        import json
        import threading
        from urllib.request import Request, urlopen
        from workbench.api import make_server
        from workbench.service import analyze_procedure
        site = self.root / 'site'
        (site / 'adjudication').mkdir(parents=True)
        (site / 'adjudication/index.html').write_text('Workbench', encoding='utf-8')
        server = make_server(self.root, 0, site)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            result = analyze_procedure(self.root, 'sifen-3-5')
            self.act('set_type', self.unit(38), type='discourse')
            body = json.dumps({'procedure_id': 'sifen-3-5', 'artifacts': result['artifacts']}).encode()
            request = Request(f'http://127.0.0.1:{server.server_port}/api/artifacts/status',
                              data=body, headers={'Content-Type': 'application/json'})
            with urlopen(request) as response:
                self.assertEqual([r['status'] for r in json.load(response)['freshness']], ['stale', 'stale'])
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

    def test_missing_parent_or_cycle_never_claims_valid(self):
        from source_adapters import dependencies as dep
        parent = dep.artifact('parser', {})
        child = dep.artifact('graph', {}, parents=[parent])
        self.assertEqual(dep.validate(self.root, [child])[0]['status'], 'stale')
        parent['parents'] = [child['id']]
        self.assertTrue(all(r['status'] == 'stale' for r in dep.validate(self.root, [parent,child])))
        with self.assertRaises(ValueError):
            dep.validate(self.root, [{'id': 'malformed'}])
