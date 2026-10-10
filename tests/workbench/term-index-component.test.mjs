import test from 'node:test';
import assert from 'node:assert/strict';
import {filterEntries, selectedEntry, navigationEvent, SURFACE_FILTER_LABEL, restoreSearchFocus} from '../../tools/parser_inspector/term_index.mjs';

const occurrence=(surface,role,start)=>({
  identity:{source_id:'sifen',unit_id:'sifen:'+start,doc_id:'sifen:'+start,reading_id:'r'+start,start,end:start+1},
  source_anchor:{doc_id:'sifen:'+start,reading_id:'r'+start,start,end:start+1,quote:surface,offset_unit:'unicode_code_point'},
  surface,display_level:role,semantic_candidates:[{status:'suggested'}],evidence:[{candidate_id:'c'+start}],
});

const index={schema:'TermIndex/1',entries:[
  {surface:'月',occurrence_classification:'both',counts:{maximal_occurrences:1,component_occurrences:1,appears_in_compounds:2},
    occurrences:[occurrence('月','maximal',1),occurrence('月','component',2)],direct_parent_occurrences:[],compound_ancestor_occurrences:[]},
  {surface:'積',occurrence_classification:'component',counts:{maximal_occurrences:0,component_occurrences:1,appears_in_compounds:1},
    occurrences:[occurrence('積','component',3)],direct_parent_occurrences:[],compound_ancestor_occurrences:[]},
  {surface:'章法',occurrence_classification:'maximal',counts:{maximal_occurrences:1,component_occurrences:0,appears_in_compounds:0},
    occurrences:[occurrence('章法','maximal',4)],direct_parent_occurrences:[],compound_ancestor_occurrences:[]},
]};

test('filters exact-form entries without hiding component-only forms',()=>{
  assert.deepEqual(filterEntries(index,{query:'',filter:'All'}).map(e=>e.surface),['月','積','章法']);
  assert.deepEqual(filterEntries(index,{query:'',filter:'Maximal'}).map(e=>e.surface),['月','章法']);
  assert.deepEqual(filterEntries(index,{query:'',filter:'Component'}).map(e=>e.surface),['月','積']);
  assert.deepEqual(filterEntries(index,{query:'',filter:'Both'}).map(e=>e.surface),['月']);
  assert.deepEqual(filterEntries(index,{query:'月',filter:'All'}).map(e=>e.surface),['月']);
});

test('selects complete entry details and emits only navigation identity and anchor',()=>{
  const entry=selectedEntry(index,'月');
  assert.equal(entry.counts.appears_in_compounds,2);
  assert.equal(entry.occurrences[1].semantic_candidates[0].status,'suggested');
  const event=navigationEvent(entry.occurrences[1],'test-nonce');
  assert.deepEqual(Object.keys(event).sort(),['identity','nonce','source_anchor']);
  assert.equal(event.identity.doc_id,'sifen:2');
  assert.equal(event.source_anchor.quote,'月');
  assert.equal(event.semantic_candidates,undefined);
});

test('rejects a non-TermIndex component payload',()=>{
  assert.throws(()=>filterEntries({schema:'Other/1'},{query:'',filter:'All'}),/term_index_component_requires_v1/);
});

test('labels substring search honestly and restores its focus after a redraw',()=>{
  assert.equal(SURFACE_FILTER_LABEL,'Filter surface forms');
  const input={focused:false,range:null,focus(){this.focused=true;},setSelectionRange(start,end){this.range=[start,end];}};
  restoreSearchFocus({querySelector:selector=>selector==='.term-index-search'?input:null},2,4);
  assert.equal(input.focused,true);
  assert.deepEqual(input.range,[2,4]);
});
