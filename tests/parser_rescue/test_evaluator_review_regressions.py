"""T5 evaluator fix round 1: independent counterexamples, A3 or synthetic only."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
HERE=ROOT/'evaluation/rescue-v3_1'
# Import retained helpers without running their log-writing main functions.
sys.path.insert(0,str(HERE/'reviews/evaluator_t5_initial'))
import probes
import extended_probes as extended
scoring=probes.scoring
runtime=probes.runtime
prospective=probes.prospective


class EvaluatorReviewRegressions(unittest.TestCase):
    def test_registered_A3_remains_assessable(self):
        for name,count in [('A01',114),('A02',83),('A03',91),('A04',81)]:
            with self.subTest(name=name):
                result=probes.score(name)
                self.assertEqual(result['relations'],{'TP':count,'FP':0,'FN':0})
                self.assertTrue(result['chain'])

    def test_named_method_return_is_not_any_return(self):
        for name in ['A01','A02','A04']:
            with self.subTest(name=name):
                result=probes.score(name,probes.method_returns_swap,True)
                self.assertFalse(result['passed'])
                self.assertFalse(result['chain'])

    def test_auxiliary_method_requires_semantics_and_trace(self):
        result=probes.score('A04',probes.corrupt_witness,True)
        self.assertFalse(result['passed'])
        self.assertFalse(result['chain'])
        self.assertGreater(result['relations']['FP'],0)

    def test_method_body_needs_applicable_source(self):
        result=probes.score('A02',extended.replace_body_source,True)
        self.assertFalse(result['passed'])
        self.assertFalse(result['chain'])

    def test_duplicate_graph_id_is_not_silently_collapsed(self):
        result=probes.score('A03',probes.duplicate_id_wrong_first)
        self.assertFalse(result['passed'])
        self.assertTrue(result['source_errors'])
        self.assertGreater(result['relations']['FP'],0)

    def test_alias_cannot_discard_conflicting_unit(self):
        result=extended.identity_alias_probe()
        self.assertFalse(result['passed'])
        self.assertGreater(result['relations']['FN'],0)

    def test_execution_values_alone_do_not_establish_chain(self):
        result=probes.score('A03',probes.no_execution_trace)
        self.assertFalse(result['chain'])

    def test_executor_control_must_equal_scored_control(self):
        result=extended.repeat_probe()
        self.assertNotEqual(result['before'],result['after'])
        self.assertFalse(result['passed'])
        self.assertGreater(result['relations']['FN'],0)
        self.assertGreater(result['relations']['FP'],0)

    def test_nested_kind_diagnostics_block_but_benign_info_does_not(self):
        for value in [[{'kind':'incomplete_construction'}],{'kind':'UnsupportedConstruction'},
                      {'severity':'warning','unresolved':['bad']},{'status':'ok','errors':['bad']},
                      {'severity':'info','children':[{'kind':'UnresolvedReference'}]}]:
            with self.subTest(value=value):
                self.assertTrue(scoring.blocking_diagnostics({'diagnostics':value}))
        self.assertFalse(scoring.blocking_diagnostics({'diagnostics':{'severity':'info','message':'annotation'}}))

    def test_fixed_registration_requires_every_predicate_once(self):
        _,_,ref=probes.synthetic_fixture();ref=scoring.normalized(ref)
        for mode in ['omit','duplicate','wrong_owner']:
            altered=copy.deepcopy(ref)
            if mode=='omit':altered['policy']['fixed_atoms'].pop()
            elif mode=='duplicate':
                atom=copy.deepcopy(altered['policy']['fixed_atoms'][0]);atom['atom_id']='fresh-id';altered['policy']['fixed_atoms'].append(atom)
            else:altered['policy']['fixed_atoms'][0]['obligation_id']='no-such-obligation'
            altered['policy']['fixed_atom_count']=len(altered['policy']['fixed_atoms'])
            with self.subTest(mode=mode),self.assertRaises(ValueError):scoring.register(altered)

    def test_reference_support_is_not_caller_declared(self):
        _,_,ref=probes.synthetic_fixture()
        ref['policy']['supported_actions']=['not_supported_anywhere']
        ref['policy']['obligations']['syn.1']['events'][0]['kind']='not_supported_anywhere'
        with self.assertRaises(ValueError):scoring.register(ref)
        result=scoring.evaluate(*probes.synthetic_fixture()[:2],ref,track='B')
        self.assertEqual(result['relations']['FN'],result['gold_atom_count'])
        self.assertTrue(result['reference_unsupported'])

    def test_unknown_reference_field_and_action_port_reject(self):
        for mode in ['field','port']:
            _,_,ref=probes.synthetic_fixture();pred=ref['policy']['obligations']['syn.1']['events'][0]
            if mode=='field':pred['unimplemented_contract']={'pretend':True}
            else:pred['reads']['third']={'literal':3}
            with self.subTest(mode=mode),self.assertRaises(ValueError):scoring.register(ref)

    def test_manifest_only_cannot_qualify_a_batch(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory);freeze=path/'metadata';freeze.mkdir()
            (freeze/'manifest.json').write_bytes(runtime._json_bytes(runtime.manifest(ROOT)))
            with self.assertRaises(ValueError):prospective.lock_batch(path/'batch',freeze,[],[])

    def test_manifest_cannot_claim_closed_without_required_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'analysis_parser').mkdir();(root/'analysis_parser/core.py').write_text('x=1\n')
            record=runtime.manifest(root)
            self.assertFalse(record['closed_behavior_inventory'])
            self.assertTrue(runtime.verify(root,record))

    def test_goal_and_structure_contracts_are_machine_checkable(self):
        packet,_,_=probes.synthetic_fixture()
        entry={'payload':{'packet':packet,'inputs':{}},'chain_contract':{'required_exports':[{'label':'x','unit':'day'}],'root':'missing'},'structural_contract':{'fake':True}}
        with self.assertRaises(ValueError):prospective.validate_goal_contracts(entry)

    def test_certificate_evidence_resolves_sources_files_and_identifiers(self):
        packet,_,ref=probes.synthetic_fixture();anchor=ref['cards'][0]['obligations'][0]['anchor']
        entry={'payload':{'packet':packet,'inputs':{'epoch_elapsed_years':0}},'reference':ref,'combination':'synthetic-composition',
               'chain_contract':{'required_exports':[{'label':'answer','unit':'day'}],'root':'epoch_elapsed_years'},
               'structural_contract':{'frames':[{'kind':'ProcedureDef','goal_surface':'answer','doc_id':'test'}],'predicates':[{'kind':'Multiply','anchor':anchor}]}}
        frozen=runtime.manifest(ROOT);known={x['path']:x['sha256'] for x in frozen['files']}
        paths=['evaluation/rescue-v3_1/grammar_inventory.json','evaluation/rescue-v3_1/contracts/scoring_support.json',
               'analysis_parser/program_ir.py','analysis_parser/control_ir.py','analysis_parser/operations.py',
               'analysis_parser/inputs.py','analysis_parser/resources.py','evaluation/rescue-v3_1/runtime_protocol.py',
               'evaluation/rescue-v3_1/fixed_scoring.py','evaluation/rescue-v3_1/evidence_contracts.py',
               'evaluation/rescue-v3_1/contracts/selection_policy.json']
        production=json.loads((HERE/'grammar_inventory.json').read_text())['productions'][0]['production_id']
        atoms=[a['predicate_path'] for a in scoring.register(ref)['atoms']]
        evidence={'source_spans':[anchor],'frozen_files':[{'path':p,'sha256':known[p]} for p in paths],
                  'production_ids':[production],'support_ids':['action:multiply'],'atom_paths':atoms,
                  'root_inputs':entry['payload']['inputs'],'selected_profiles':[],
                  'combination':entry['combination'],'description':'Independent synthetic schema validation; not a historical qualification.'}
        entry['certificates']={key:{'passed':True,'evidence':copy.deepcopy(evidence)} for key in prospective.CERTIFICATES}
        prospective.validate_certificates(entry,frozen)
        for mutation in ['string','span','hash','production','support','atom','root','unit','structure']:
            changed=copy.deepcopy(entry)
            if mutation=='string':changed['certificates']['lexical_construction']['evidence']='NOT_A_SOURCE_OR_FROZEN_IDENTIFIER'
            elif mutation=='span':changed['certificates']['program_control']['evidence']['source_spans'][0]['quote']='unrelated'
            elif mutation=='hash':changed['certificates']['program_control']['evidence']['frozen_files'][0]['sha256']='0'*64
            elif mutation=='production':changed['certificates']['lexical_construction']['evidence']['production_ids']=['NOT_A_PRODUCTION']
            elif mutation=='support':changed['certificates']['frozen_scoring_support']['evidence']['support_ids']=['action:not_supported_anywhere']
            elif mutation=='atom':changed['certificates']['frozen_scoring_support']['evidence']['atom_paths'].pop()
            elif mutation=='root':changed['chain_contract']['root']='missing_input'
            elif mutation=='unit':changed['chain_contract']['required_exports'][0]['unit']='fake'
            else:changed['structural_contract']={'fake':True}
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):prospective.validate_certificates(changed,frozen)

    def test_frozen_action_ports_keep_atom_count_under_mutation(self):
        # Independent public action contract examples. These are relation tests,
        # not claimed executable source procedures or historical qualifications.
        examples={
            'literal':('', 'result'), 'parameter':('', 'result'), 'input':('', 'result'),
            'alias':('value','result'), 'load':('value','result'),
            'add':('left right','result'), 'multiply':('left right','result'), 'subtract':('left right','result'),
            'divmod':('dividend divisor','quotient remainder'), 'cycle_reduce':('dividend divisor','quotient remainder'),
            'count':('offset origin cycle','result'), 'threshold':('value lower upper','result'),
            'method_call':('offset origin cycle','result remainder'), 'year_scan':('months','years remainder months_removed'),
            'interval_scale':('value factor','result'), 'framed_origin':('head epoch','result'),
            'initial_instant':('head epoch ordinal denominator','day_offset fraction'),
            'select':('divisor local0 local1 local2 head0 head1 head2','index local head'),
            'lookup':('row column','head_day head_year'), 'rescale':('value old_denominator new_denominator factor','result'),
            'fraction':('whole numerator denominator','result'),
            'convert':('numerator denominator rate_numerator rate_denominator output_denominator','result'),
            'repeat':('initial increment threshold','state count'), 'cycle_lift':('whole elapsed_years factor','result'),
            'epoch_frame':('epoch_elapsed local_elapsed','result'),
            'event_sequence':('whole numerator denominator increment_whole increment_numerator increment_denominator epoch','result'),
            'boundary_call':('has_intercalation moon_events qi_events','result'), 'query':('','')}
        self.assertEqual(set(examples),set(scoring.SUPPORT['actions']))
        for kind,(read_names,write_names) in examples.items():
            packet,report,ref=probes.synthetic_fixture();anchor=ref['cards'][0]['obligations'][0]['anchor']
            report={'events':[],'value_instances':[]};reads={};selectors={}
            for i,port in enumerate(read_names.split()):
                vid='input.'+port;eid='producer.'+port
                report['events'].append({'id':eid,'kind':'literal','reads':{},'writes':{'result':vid},'attributes':{'value':i+1},'source_spans':[anchor]})
                report['value_instances'].append({'id':vid,'producer':eid,'output_port':'result','unit':'day'})
                reads[port]=vid;selectors[port]={'literal':i+1}
            writes={port:'out.'+port for port in write_names.split()}
            main={'id':'main','kind':kind,'reads':reads,'writes':writes,'source_spans':[anchor]}
            report['events'].append(main)
            for port,vid in writes.items():report['value_instances'].append({'id':vid,'producer':'main','output_port':port,'unit':'day'})
            pred={'kind':kind,'reads':selectors,'writes':{p:{'unit':'day'} for p in writes}}
            ref['policy']['obligations']['syn.1']['events']=[pred]
            baseline=scoring.evaluate(packet,report,ref)
            self.assertTrue(baseline['all_obligations_passed'],kind)
            for direction,ports in [('reads',reads),('writes',writes)]:
                for port in ports:
                    altered=copy.deepcopy(report);altered['events'][-1][direction][port]='missing.value'
                    result=scoring.evaluate(packet,altered,ref)
                    with self.subTest(kind=kind,direction=direction,port=port):
                        self.assertFalse(result['all_obligations_passed'])
                        self.assertGreater(result['relations']['FN'],0)
                        self.assertEqual(result['relations']['TP']+result['relations']['FN'],baseline['gold_atom_count'])
            wrong=copy.deepcopy(report);wrong['events'][-1]['kind']='not_supported_anywhere'
            result=scoring.evaluate(packet,wrong,ref)
            self.assertEqual(result['relations']['FN'],baseline['gold_atom_count'],kind)

    def test_duplicate_values_and_execution_steps_reject(self):
        def duplicate_value(raw):raw['report']['value_instances'].insert(0,copy.deepcopy(raw['report']['value_instances'][0]))
        self.assertFalse(probes.score('A03',duplicate_value)['chain'])
        def duplicate_step(raw):raw['execution']['execution_trace'].append(copy.deepcopy(raw['execution']['execution_trace'][0]))
        self.assertFalse(probes.score('A03',duplicate_step)['chain'])

    def test_B_unsupported_nested_contract_keeps_denominator(self):
        packet,report,ref=probes.synthetic_fixture()
        ref['policy']['contracts']={'gap':{'type':'unknown_contract','obligation_ids':['syn.1'],'requirements':{'unknown':True}}}
        result=scoring.evaluate(packet,report,ref,track='B')
        self.assertTrue(result['reference_unsupported'])
        self.assertGreater(result['relations']['FN'],0)
        self.assertEqual(result['relations']['TP']+result['relations']['FN'],result['gold_atom_count'])

    def test_qualification_order_and_page_exposures_are_complete(self):
        # Frozen candidate metadata only: no new source bodies are accessed.
        policy=json.loads((HERE/'contracts/selection_policy.json').read_text())
        universe=sorted(json.loads((ROOT/policy['candidate_universe']).read_text())['candidate_universe'],key=prospective.candidate_order)
        paths=list(dict.fromkeys([*policy['inherited_exposure'],'evaluation/handoff-v3/exposure_registry_merged.json']))
        excluded={c['id'] for c in universe if c.get('exposed') or c.get('source_unavailable')}
        for path in paths:excluded.update(json.loads((ROOT/path).read_text()).get('procedure_ids',[]))
        frozen=runtime.manifest(ROOT);known={f['path']:f['sha256'] for f in frozen['files']}
        frozen_paths=[policy['candidate_universe'],*paths,'evaluation/rescue-v3_1/contracts/selection_policy.json']
        log={'schema_version':'rescue-qualification-log-1','parser_runs_before_lock':0,'seed':policy['seed'],
             'frozen_inputs':[{'path':p,'sha256':known[p]} for p in frozen_paths],'A_reviews':[],'B_selection':[]}
        entries=[];exposed=set(excluded)
        for track,count in [('A',4),('B',4)]:
            for _ in range(count):
                candidate=next(c for c in universe if c['id'] not in exposed)
                pages=set(candidate['source_locator']['pdf_pages'])
                touched={c['id'] for c in universe if pages.intersection(c['source_locator']['pdf_pages'])}
                row={'candidate_id':candidate['id'],'decision':'qualified','reason':'Synthetic metadata protocol test only',
                     'read_pages':sorted(pages),'context_candidate_ids':[],'exposed_candidate_ids':sorted(touched)}
                log['A_reviews' if track=='A' else 'B_selection'].append(row)
                entries.append({'candidate_id':candidate['id'],'track':track,'source_locator':candidate['source_locator']})
                exposed.update(touched)
        prospective.validate_qualification_log(entries,log,frozen)
        for mutation in ['empty','missing','order','exposure','frozen_hash']:
            changed=copy.deepcopy(log)
            if mutation=='empty':changed={}
            elif mutation=='missing':changed['A_reviews'].pop(0)
            elif mutation=='order':changed['A_reviews'][0],changed['A_reviews'][1]=changed['A_reviews'][1],changed['A_reviews'][0]
            elif mutation=='exposure':changed['A_reviews'][0]['exposed_candidate_ids']=[]
            else:changed['frozen_inputs'][0]['sha256']='0'*64
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):prospective.validate_qualification_log(entries,changed,frozen)

    def test_method_formal_type_matches_actual_endpoint(self):
        def wrong_actual_type(raw):
            report=raw['report'];call=next(e for e in report['events'] if e['kind']=='method_call')
            definitions={m['id']:m for m in report['method_library']};method=definitions[call['attributes']['target']]
            formal=next(k for k,v in method['formal_inputs'].items() if v.get('source_label')=='元月')
            vid=call['reads'][formal]
            next(v for v in report['value_instances'] if v['id']==vid)['unit']='day'
        result=probes.score('A02',wrong_actual_type)
        self.assertFalse(result['passed'])
        self.assertFalse(result['chain'])

    def test_instance_cannot_shadow_global_value_or_repair_corrupt_producer(self):
        for corrupt in (False,True):
            payload,raw,ref,contract=probes.load('A02')
            original=next(v for v in raw['report']['value_instances'] if v['id']=='v55')
            duplicate=copy.deepcopy(original)
            if corrupt:original['producer']='NONEXISTENT_PRODUCER'
            raw['report']['method_instances'][0]['value_instances'].append(duplicate)
            graph=scoring.Graph(payload['packet'],raw['report'])
            scored=scoring.evaluate(payload['packet'],raw['report'],ref,execution=raw['execution'],auxiliary=raw)
            chain=probes.assess(payload['packet'],raw['report'],raw['execution'],scored,contract,scoring.Graph)
            with self.subTest(corrupt=corrupt):
                self.assertTrue(graph.source_errors)
                self.assertEqual(graph.values['v55']['producer'],original['producer'])
                self.assertFalse(scored['all_obligations_passed'])
                self.assertFalse(chain['full_chain_passed'])
                self.assertGreater(scored['relations']['FP'],0)
                self.assertEqual(scored['relations']['TP']+scored['relations']['FN'],83)

    def test_instance_cannot_shadow_prior_instance_value(self):
        payload,raw,ref,contract=probes.load('A04')
        first,second=raw['report']['method_instances'][:2]
        duplicate=copy.deepcopy(first['value_instances'][0]);second['value_instances'].append(duplicate)
        graph=scoring.Graph(payload['packet'],raw['report'])
        self.assertTrue(graph.source_errors)
        self.assertEqual(graph.values[duplicate['id']],first['value_instances'][0])
        result=scoring.evaluate(payload['packet'],raw['report'],ref,execution=raw['execution'],auxiliary=raw)
        self.assertFalse(result['all_obligations_passed'])
        self.assertFalse(probes.assess(payload['packet'],raw['report'],raw['execution'],result,contract,scoring.Graph)['full_chain_passed'])

    def test_instance_value_table_contains_only_its_unique_produced_values(self):
        for mode in ['foreign_producer','unclaimed_body_port','empty_id','duplicate_local']:
            payload,raw,_,_=probes.load('A02');instance=raw['report']['method_instances'][0]
            extra=copy.deepcopy(instance['value_instances'][0])
            if mode=='foreign_producer':extra.update(id='namespaced.unowned',producer=raw['report']['events'][0]['id'])
            elif mode=='unclaimed_body_port':extra['id']='namespaced.unclaimed'
            elif mode=='empty_id':extra['id']=''
            instance['value_instances'].append(extra)
            with self.subTest(mode=mode):self.assertTrue(scoring.Graph(payload['packet'],raw['report']).source_errors)

    def test_independent_namespaced_instances_keep_their_real_returns(self):
        # Existing executable fixture, cloned by renaming instance identities;
        # shared formal inputs and method definition remain legitimate.
        spec=importlib.util.spec_from_file_location('independent_method_fixture',ROOT/'tests/parser_rescue/test_method_evidence.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        packet,report=module.fixture();first=report['method_instances'][0]
        call=copy.deepcopy(report['events'][-1]);instance=copy.deepcopy(first)
        mapping={v['id']:'second.namespace.'+v['id'] for v in first['value_instances']}
        mapping.update({e['id']:'second.namespace.'+e['id'] for e in first['events']})
        mapping.update({v:'second.namespace.'+v for v in call['writes'].values()});mapping[call['id']]='second.call'
        def rename(value):
            if isinstance(value,str):return mapping.get(value,value)
            if isinstance(value,list):return [rename(v) for v in value]
            if isinstance(value,dict):return {mapping.get(k,k):rename(v) for k,v in value.items()}
            return value
        second_call=rename(call);second_instance=rename(instance)
        report['events'].append(second_call);report['method_instances'].append(second_instance)
        outputs=[v for v in report['value_instances'] if v['producer']==call['id']]
        report['value_instances'].extend(rename(v) for v in outputs)
        graph=scoring.Graph(packet,report)
        self.assertFalse(graph.source_errors)
        self.assertEqual(graph.root('out.day'),'unique.day')
        self.assertEqual(graph.root('second.namespace.out.day'),'second.namespace.unique.day')
        execution=probes.execute(report,{})
        self.assertFalse(execution['unresolved'])
        self.assertEqual(execution['values']['out.day'],execution['values']['second.namespace.out.day'])


if __name__=='__main__':unittest.main()
