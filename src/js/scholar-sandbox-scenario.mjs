// Select complete Python-compiled states. No review or graph computation runs here.
export function validateScenario(scenario) {
  const require=(condition,message)=>{if(!condition)throw Error('Invalid Inspector scenario: '+message);};
  require(scenario?.schema==='ScholarSandboxScenario/1','schema');
  require(typeof scenario.scenario_id==='string'&&scenario.scenario_id.length>0,'scenario_id');
  const {states,transitions,initial_state_id:initial}=scenario;
  require(states&&typeof states==='object'&&!Array.isArray(states),'states');
  require(Object.hasOwn(states,initial),'initial_state_id');
  require(Array.isArray(transitions),'transitions');
  const identity=states[initial]?.source;
  for(const [id,snapshot] of Object.entries(states)) {
    require(id&&snapshot?.schema==='ScholarSandboxSnapshot/1','ScholarSandboxSnapshot/1');
    require(typeof snapshot.snapshot_id==='string'&&snapshot.snapshot_id.length>0,'snapshot_id');
    require(snapshot.renderer?.objects&&Array.isArray(snapshot.renderer.facets)&&snapshot.projection
      &&Array.isArray(snapshot.questions)&&snapshot.details?.objects&&snapshot.details?.facets
      &&Array.isArray(snapshot.procedure_model?.nodes)&&Array.isArray(snapshot.procedure_model?.edges)
      &&Array.isArray(snapshot.review?.decisions),'complete snapshot presentation');
    require(['terms','constructions','steps','flows'].every(key=>Array.isArray(snapshot.renderer[key]))
      &&Array.isArray(snapshot.corpora)&&Array.isArray(snapshot.context_catalog)
      &&snapshot.labels?.objects&&snapshot.labels?.roles&&snapshot.labels?.unit_types
      &&snapshot.provenance&&typeof snapshot.provenance==='object'
      &&snapshot.presentation_registry?.compose_by_question,'required presentation fields');
    require(['doc_id','reading_id','source_id','unit_id','text','text_sha256'].every(key=>
      typeof snapshot.source?.[key]==='string'&&snapshot.source[key].length>0
      &&snapshot.source[key]===identity?.[key]),'source identity');
  }
  let current=initial;
  const visited=new Set([initial]),ids=new Set();
  for(const row of transitions) {
    require(typeof row.id==='string'&&row.id&&!ids.has(row.id),'duplicate transition or missing id');
    require(row.from_state_id===current&&Object.hasOwn(states,row.to_state_id)&&!visited.has(row.to_state_id),'linear transition');
    const question=states[current].questions.find(q=>q.id===row.question_id);
    require(question?.options.some(o=>o.id===row.option_id),'unknown question/option');
    ids.add(row.id);visited.add(row.to_state_id);current=row.to_state_id;
  }
  require(visited.size===Object.keys(states).length,'unreachable state');
  return scenario;
}

export function initialScenarioState(scenario) {
  return {state_id:scenario.initial_state_id,snapshot:scenario.states[scenario.initial_state_id],transition:null};
}

export function transitionFor(scenario,stateId,questionId,optionId) {
  return scenario?.transitions.find(row=>row.from_state_id===stateId&&row.question_id===questionId&&row.option_id===optionId)||null;
}

export function applyTransition(scenario,stateId,transitionId) {
  const transition=scenario.transitions.find(row=>row.id===transitionId&&row.from_state_id===stateId);
  if(!transition)throw Error('Scenario transition is not outgoing from the current state.');
  return {state_id:transition.to_state_id,snapshot:scenario.states[transition.to_state_id],transition};
}
