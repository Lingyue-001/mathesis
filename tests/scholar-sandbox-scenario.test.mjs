import test from 'node:test';
import assert from 'node:assert/strict';
import {validateScenario, initialScenarioState, transitionFor, applyTransition} from '../src/js/scholar-sandbox-scenario.mjs';

const snapshot=id=>({schema:'ScholarSandboxSnapshot/1',snapshot_id:id,
  source:{doc_id:'sifen:38',reading_id:'default',source_id:'sifen',unit_id:'sifen:section:38',text:'入蔀年',text_sha256:'source'},
  provenance:{revision:1},corpora:[],context_catalog:[],labels:{objects:{},roles:{},unit_types:{}},presentation_registry:{compose_by_question:{}},
  renderer:{objects:{},facets:[],terms:[],constructions:[],steps:[],flows:[]},projection:{},procedure_model:{nodes:[],edges:[]},details:{objects:{},facets:{}},
  review:{decisions:[]},questions:[{id:'q',options:[{id:'o'}]}]});
const fixture=()=>({schema:'ScholarSandboxScenario/1',scenario_id:'demo',initial_state_id:'baseline',
  states:{baseline:snapshot('a'),next:snapshot('b')},
  transitions:[{id:'t',from_state_id:'baseline',to_state_id:'next',question_id:'q',option_id:'o'}]});

test('exact outgoing choices select complete immutable snapshots and reset baseline',()=>{
  const scenario=fixture(), before=structuredClone(scenario);
  validateScenario(scenario);
  assert.equal(initialScenarioState(scenario).state_id,'baseline');
  assert.equal(transitionFor(scenario,'baseline','q','o').id,'t');
  assert.equal(transitionFor(scenario,'baseline','q','other'),null);
  assert.equal(applyTransition(scenario,'baseline','t').snapshot,scenario.states.next);
  assert.throws(()=>applyTransition(scenario,'next','t'),/not outgoing/);
  assert.deepEqual(scenario,before);
});

for(const [name,mutate] of [
  ['missing initial state',s=>{s.initial_state_id='missing';}],
  ['missing successor',s=>{s.transitions[0].to_state_id='missing';}],
  ['duplicate transition',s=>{s.transitions.push({...s.transitions[0]});}],
  ['cycle',s=>{s.transitions.push({id:'cycle',from_state_id:'next',to_state_id:'baseline',question_id:'q',option_id:'o'});}],
  ['unreachable state',s=>{s.states.orphan=snapshot('c');}],
  ['unknown option',s=>{s.transitions[0].option_id='unknown';}],
  ['missing presentation',s=>{delete s.states.next.renderer;}],
  ['wrong schema',s=>{s.states.next.schema='fake';}],
  ['changed source',s=>{s.states.next.source.text_sha256='other';}],
  ['changed source document',s=>{s.states.next.source.doc_id='other';}],
  ['missing corpora',s=>{delete s.states.next.corpora;}],
  ['missing provenance',s=>{delete s.states.next.provenance;}],
  ['missing labels',s=>{delete s.states.next.labels;}],
  ['missing context catalog',s=>{delete s.states.next.context_catalog;}],
  ['missing composition registry',s=>{delete s.states.next.presentation_registry;}],
  ['missing annotation terms',s=>{delete s.states.next.renderer.terms;}],
])test('rejects '+name,()=>{const s=fixture();mutate(s);assert.throws(()=>validateScenario(s));});
