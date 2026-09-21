import renderSource from './inspector/source_annotation.mjs';
import {renderProcedureModel} from './inspector/procedure_model.mjs';
import {createDraftState,selectOption,upsertDraft,retractDraft,exportDrafts,importDrafts,
  loadDrafts,saveDrafts,makeSourceAnchor} from './scholar-sandbox-drafts.mjs';

const root=document.querySelector('#scholar-sandbox');
const $=id=>document.getElementById(id);
const make=(tag,text,cls)=>{const el=document.createElement(tag);if(text!==undefined)el.textContent=text;if(cls)el.className=cls;return el;};
const paragraph=(parent,text,muted=false)=>{if(text!==undefined&&text!==null&&text!=='')parent.append(make('p',String(text),muted?'research-muted':''));};
const action=(parent,text,handler)=>{const button=make('button',text,'research-button');button.type='button';button.addEventListener('click',()=>attempt(handler));parent.append(button);return button;};
const evidence=(parent,title,value)=>{const detail=make('details',undefined,'research-fold');detail.append(make('summary',title),make('pre',JSON.stringify(value,null,2)));parent.append(detail);return detail;};
const field=(parent,label,control)=>{const wrapper=make('label',label,'research-field');control.setAttribute('aria-label',label);wrapper.append(control);parent.append(wrapper);return control;};
const choices=(select,rows,value)=>{select.replaceChildren(...rows.map(([id,label])=>{const option=make('option',label);option.value=id;return option;}));if(value!==undefined)select.value=value;};
const error=message=>{$('sandbox-error').textContent=message;$('sandbox-error').hidden=!message;};
const attempt=fn=>{try{error('');return fn();}catch(e){error(e.message||String(e));}};
function download(filename,value){const url=URL.createObjectURL(new Blob([typeof value==='string'?value:JSON.stringify(value,null,2)],{type:'application/json'}));const link=make('a');link.href=url;link.download=filename;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}

let snapshot,drafts,storageBlocked=false,selected=null,facetKey=null,questionId=null,editingId=null;
let draftExpression=null;
let draftPresentationKey='';
let workspace='parser',view='source',sourceData,disposeSource,corpusId,unitIndex=0;
const workspaceNames={parser:'Parser Stages',segmentation:'Segmentation Review',corpus:'Corpus Browser'};
const objectName=row=>row?(snapshot.labels?.objects?.[row.id]||row.surface||row.formal||row.operation||row.id):'';
const roleName=role=>snapshot.labels?.roles?.[role]||role||'';
const currentQuestion=()=>snapshot.questions.find(q=>q.id===questionId);
const questionDraft=id=>id?drafts.decisions.find(d=>d.question_id===id):undefined;
const draftChoice=draft=>snapshot.questions.find(q=>q.id===draft.question_id)?.options.find(o=>o.id===draft.option_id)?.label||draft.kind;

function commitDraftState(next){
  if(storageBlocked)throw Error('Stored drafts could not be read and have been retained. Import a valid draft file before replacing them.');
  saveDrafts(snapshot,next,localStorage);drafts=next;renderDrafts();renderDetails();updateQuestionDraft();refreshDraftPresentation();
}
function focusQuestion(){const heading=$('current-question-heading');heading.focus({preventScroll:true});heading.scrollIntoView({block:'start'});}
function updateQuestionDraft(){
  const host=$('question-draft-summary');if(!host)return;
  const draft=questionDraft(questionId);host.hidden=!draft;
  host.textContent=draft?'Saved draft: '+draftChoice(draft)+' · not recompiled. The snapshot question remains unresolved.':'';
}
function refreshDraftPresentation(force=false){
  const key=JSON.stringify(drafts.decisions.filter(d=>d.question_id));
  if(!force&&key===draftPresentationKey)return;
  draftPresentationKey=key;
  // Presentation overlay only. Canonical statuses, source, model and snapshot
  // stay unchanged; the shared renderer still lays out the existing badges.
  sourceData.render=structuredClone(snapshot.renderer);
  for(const row of [...sourceData.render.terms,...sourceData.render.constructions]){
    for(const facet of row.badges||[]){
      const draft=questionDraft(facet.question_id);if(!draft)continue;
      facet.label+=' · draft';
      facet.hover+='\nLocal draft: '+draftChoice(draft)+'\nNot recompiled; snapshot status unchanged.';
    }
  }
  mountSource();
}
function sidebar(open){$('workspace-sidebar').hidden=!open;$('expand-workspace').hidden=open;$('expand-workspace').setAttribute('aria-expanded',String(open));root.classList.toggle('sidebar-collapsed',!open);}
function setWorkspace(next){
  workspace=next;$('workspace-title').textContent=workspaceNames[next];
  for(const key of Object.keys(workspaceNames))$(key+'-workspace').hidden=key!==next;
  root.querySelectorAll('[data-workspace]').forEach(button=>{if(button.dataset.workspace===next)button.setAttribute('aria-current','page');else button.removeAttribute('aria-current');});
  if(next!=='parser')renderCorpus();
  if(matchMedia('(max-width:800px)').matches)sidebar(false);
}
function showView(next){
  view=next;$('annotated-view').hidden=next!=='source';$('graph-view').hidden=next!=='graph';
  root.querySelectorAll('[data-view]').forEach(button=>button.setAttribute('aria-pressed',String(button.dataset.view===next)));
  syncSelection();renderDetails();
}
function syncSelection(){
  sourceData.focus=selected;sourceData.facet_key=facetKey;
  root.querySelectorAll('.source [data-object-id]').forEach(el=>el.classList.toggle('focus',el.dataset.objectId===selected&&!el.classList.contains('facet')));
  root.querySelectorAll('.source .facet').forEach(el=>el.classList.toggle('active',el.dataset.facetKey===facetKey));
  root.querySelectorAll('.procedure-node').forEach(el=>{const active=!!selected&&el.dataset.objectId===selected;el.classList.toggle('active',active);el.setAttribute('aria-pressed',String(active));});
}
function choose(click){
  selected=click.object_id;facetKey=click.facet_key||null;questionId=click.question_id||null;editingId=null;
  syncSelection();renderDetails();renderQuestion();
}
function mountSource(){
  disposeSource?.();
  disposeSource=renderSource({parentElement:$('source-host'),data:sourceData,setStateValue:(key,value)=>{
    if(key==='clicked')choose(value);
    if(key==='clicked'&&value.question_id)focusQuestion();
    if(key==='selection'){$('boundary-start').value=value[0];$('boundary-end').value=value[1];updateBoundary();}
  }});
  syncSelection();
}
function anchorText(parent,anchor){
  const p=make('p',undefined,'research-anchor');
  if(anchor.doc_id===snapshot.source.doc_id){const chars=Array.from(snapshot.source.text);p.append(document.createTextNode(chars.slice(0,anchor.start).join('')),make('mark',chars.slice(anchor.start,anchor.end).join('')),document.createTextNode(chars.slice(anchor.end).join('')));}
  else p.textContent=anchor.quote||'';
  parent.append(p);
}
function renderDetails(){
  const host=$('selection-detail');host.replaceChildren();
  const details=(facetKey?snapshot.details.facets[facetKey]:snapshot.details.objects[selected])||snapshot.details.objects[selected];
  if(!details?.selected){paragraph(host,'Select a term, construction, or step in the source.',true);return;}
  const row=details.selected;paragraph(host,objectName(row));
  if(view==='graph'){
    const node=snapshot.procedure_model.nodes.find(n=>n.selection_object_id===selected);
    if(node){paragraph(host,node.status_label||node.status,true);for(const anchor of node.source_anchors||[])anchorText(host,anchor);if(node.anchor_scope==='supporting_step')paragraph(host,'Supporting Step source; no separate exact anchor is recorded.',true);}
  }
  if(row.gloss){
    paragraph(host,row.gloss.kind==='reviewed'?'Current interpretation · reviewed':'Machine suggestions · unranked',true);
    for(const label of row.gloss.labels||[row.gloss.label])paragraph(host,'• '+label);
  }
  for(const facet of details.facets||[]){
    const record=make('div',undefined,'research-record');paragraph(record,(facet.label||facet.facet)+' · '+facet.status,true);
    const draft=questionDraft(facet.question_id);if(draft)paragraph(record,'Local draft: '+draftChoice(draft)+' · not recompiled.',true);
    if(facet.question_id)action(record,'Review',()=>{choose({object_id:selected,facet_key:facet.facet_key,question_id:facet.question_id});focusQuestion();});
    host.append(record);
  }
  if(details.composition?.length||details.uses?.length||details.steps?.length||details.named_outputs?.length)paragraph(host,'Local computational context',true);
  if(details.composition?.length){paragraph(host,'Term composition',true);for(const part of details.composition)paragraph(host,part.surface+' · '+(part.gloss.labels||[part.gloss.label]).join(' / '));}
  for(const use of details.uses||[]){paragraph(host,'Used in · '+roleName(use.role),true);paragraph(host,use.construction.surface);}
  for(const slot of row.slots||[]){paragraph(host,'Construction slot · '+roleName(slot.name),true);paragraph(host,slot.surface);}
  for(const naming of details.naming||[]){paragraph(host,'Textual naming',true);paragraph(host,naming.surface);}
  for(const naming of details.named_outputs||[]){paragraph(host,'Computational role',true);paragraph(host,objectName(naming.step)+' → '+roleName(naming.port));}
  for(const step of details.steps||[]){
    paragraph(host,'Computational step · '+objectName(step),true);
    for(const input of step.inputs||[]){
      const target=snapshot.renderer.objects[input.term_id]||snapshot.renderer.objects[input.from_step_id];
      const text=target?((input.from_step_id?'from ':'')+objectName(target)):(input.literal!==undefined?String(input.literal):input.surface_reference||'local source grounding unavailable');
      paragraph(host,roleName(input.role)+' → '+text);
    }
    for(const output of step.outputs||[])paragraph(host,roleName(output.port)+' → '+(output.labels?.join(' / ')||'unnamed result'));
  }
  for(const flow of details.flows||[]){paragraph(host,flow.formal+' · '+flow.display_status,true);if(flow.producer_source?.sections?.length)paragraph(host,'Historical source · §'+flow.producer_source.sections.join(', §'),true);}
  if(details.context_requirement){paragraph(host,'Construction context requirement');paragraph(host,'Cause · '+details.context_requirement.cause,true);paragraph(host,'Missing inputs · '+details.context_requirement.missing_inputs.join(', '),true);}
  if(details.source_assistance){
    paragraph(host,'Canonical producer candidates');
    for(const candidate of details.source_assistance.candidates)paragraph(host,candidate.label);
    if(!details.source_assistance.candidates.length)paragraph(host,'No canonical producer candidate is currently recorded.',true);
    paragraph(host,'Search hints — not yet linked',true);
    for(const [title,key] of [['Registered parameter/declaration hits','registered'],['Other exact source occurrences','other']]){
      paragraph(host,title);
      for(const hit of details.source_assistance[key]||[]){
        const detail=make('details',undefined,'research-fold');detail.append(make('summary','Inspect · §'+hit.sections.join(', §')+' · '+hit.quote));
        paragraph(detail,hit.text);
        const context=snapshot.context_catalog.find(c=>c.unit_id===hit.unit_id&&c.source_id===snapshot.source.source_id);
        const option=currentQuestion()?.options.find(o=>o.action==='attach_context');
        if(context&&option)action(detail,'Add context as draft',()=>saveQuestionDraft(currentQuestion(),option,context.id));
        host.append(detail);
      }
    }
  }
  evidence(host,'Why / Evidence',{object:row,facet:details.facet,question_id:questionId,explicit_decision_refs:row.decision_refs||[]});
}
function renderQuestion(){
  const host=$('question-detail');host.replaceChildren();const q=currentQuestion();
  if(!q){
    const facet=snapshot.renderer.facets.find(f=>f.facet_key===facetKey);
    const decision=facet?.decision_id&&snapshot.review.decisions.find(d=>d.decision_id===facet.decision_id);
    if(decision){paragraph(host,'Reviewed decision · exported snapshot',true);paragraph(host,decision.reason||decision.action);evidence(host,'Recorded decision',decision);}
    else paragraph(host,'Select a question badge to inspect its existing options.',true);
    return;
  }
  const navigation=make('div',undefined,'research-actions');host.append(navigation);
  const list=snapshot.renderer.facets.filter(f=>snapshot.questions.some(q=>q.id===f.question_id));
  const index=list.findIndex(f=>f.facet_key===facetKey);
  const navigate=delta=>{const next=list[index+delta];choose({object_id:next.object_id,facet_key:next.facet_key,question_id:next.question_id});};
  action(navigation,'Previous',()=>navigate(-1)).disabled=index<=0;
  action(navigation,'Next pending',()=>navigate(1)).disabled=index<0||index>=list.length-1;
  paragraph(host,q.title);
  const saved=make('p',undefined,'research-muted');saved.id='question-draft-summary';saved.setAttribute('role','status');host.append(saved);updateQuestionDraft();
  const options=make('fieldset',undefined,'research-options');options.append(make('legend','Interpretation'));host.append(options);
  for(const option of q.options){
    const label=make('label'),input=document.createElement('input');input.type='radio';input.name='sandbox-option';input.value=option.id;
    input.checked=drafts.selected_options[q.id]===option.id;
    input.addEventListener('change',()=>attempt(()=>{commitDraftState(selectOption(snapshot,drafts,q.id,option.id));renderOption(q,option);}));
    label.append(input,document.createTextNode(option.label));options.append(label);
  }
  host.append(make('div',undefined,'question-option-fields'));host.lastChild.id='option-fields';
  const option=q.options.find(o=>o.id===drafts.selected_options[q.id]);if(option)renderOption(q,option);
  evidence(host,'Why these options?',q.evidence||q);
}
function renderOption(question,option){
  const host=$('option-fields');host.replaceChildren();draftExpression=null;
  paragraph(host,'This choice is local. Saving a draft does not recompile or validate the analysis.',true);
  const existing=drafts.decisions.find(d=>d.id===editingId)||drafts.decisions.find(d=>d.question_id===question.id);
  if(option.requires_context_picker||option.action==='attach_context'){
    const picker=field(host,'Additional context',make('select'));picker.id='draft-context';
    choices(picker,snapshot.context_catalog.map(c=>[c.id,c.label]),existing?.context_id||snapshot.context_catalog[0]?.id);
  }
  if(option.mode==='compose'||option.id==='local-compose'){
    renderComposition(host,snapshot.presentation_registry.compose_by_question[question.id],existing?.inputs?.expression);
    paragraph(host,'Recorded as a local interpretation draft. It has not been recompiled or validated.',true);
  }
  for(const assertion of option.assertions||[])paragraph(host,'• '+assertion,true);
  const reason=field(host,'Draft note',make('textarea'));reason.id='draft-note';reason.value=existing?.reason||'';
  action(host,option.action==='attach_context'?'Add context as draft':'Save as draft',()=>saveQuestionDraft(question,option,$('draft-context')?.value));
  const status=make('p',undefined,'research-muted');status.id='draft-save-status';status.setAttribute('role','status');host.append(status);
}
function renderComposition(host,tree,existing){
  // The export supplies the entire bounded choice tree from the research UI.
  // Browser code only records choices; it has no registry inference or compiler.
  const preview=make('p',undefined,'research-muted');
  const build=(parent,rows,path,saved,onChange)=>{
    const picker=field(parent,'Composition '+path,make('select'));
    const initial=rows.find(row=>row.expression?row.expression.concept_id===saved?.concept_id:row.op===saved?.op)||rows[0];
    choices(picker,rows.map(row=>[row.id,row.label]),initial?.id);
    const children=make('div');parent.append(children);
    const state={expression:null,label:''};
    const update=()=>{
      children.replaceChildren();const row=rows.find(row=>row.id===picker.value);
      if(!row){onChange();return;}
      if(row.expression){state.expression=structuredClone(row.expression);state.label=row.label;}
      else{
        state.expression={op:row.op,arguments:{}};const slots={};
        const refresh=()=>{for(const [slot,value] of Object.entries(slots))state.expression.arguments[slot]=value.expression;
          state.label=row.op+'('+Object.entries(slots).map(([slot,value])=>slot+'='+value.label).join(', ')+')';onChange();};
        for(const [slot,options] of Object.entries(row.arguments))slots[slot]=build(children,options,path+'.'+slot,saved?.op===row.op?saved.arguments?.[slot]:null,refresh);
        refresh();
      }
      onChange();
    };
    picker.onchange=update;update();return state;
  };
  if(!tree.length){paragraph(host,'The current registry cannot express a local composition here.',true);return;}
  let state;const refresh=()=>{if(state){draftExpression=state.expression;preview.textContent='Preview: '+state.label;}};
  state=build(host,tree,'meaning',existing,refresh);host.append(preview);refresh();
}
function saveQuestionDraft(question,option,contextId){
  const target=question.decision_target||question.anchor||question.display_anchor;
  const anchor=makeSourceAnchor(snapshot,target.start,target.end);
  const prior=drafts.decisions.find(d=>d.id===editingId)||drafts.decisions.find(d=>d.question_id===question.id);
  const record={kind:option.action==='attach_context'?'context':'option',status:'draft',question_id:question.id,option_id:option.id,
    anchor,reason:$('draft-note')?.value||'',inputs:{}};
  if(prior)record.id=prior.id;
  if(selected)record.object_id=selected;if(facetKey)record.facet_key=facetKey;
  if(contextId)record.context_id=contextId;
  if(option.mode==='compose'){
    if(!draftExpression)throw Error('No registered composition is available for this question.');
    record.inputs.expression=structuredClone(draftExpression);
  }
  commitDraftState(upsertDraft(snapshot,selectOption(snapshot,drafts,question.id,option.id),record));editingId=null;
  if($('draft-save-status'))$('draft-save-status').textContent='Saved as local draft.';
}
function updateBoundary(){
  const start=Number($('boundary-start').value),end=Number($('boundary-end').value);
  try{const anchor=makeSourceAnchor(snapshot,start,end);$('boundary-quote').textContent=anchor.quote+' · ['+start+', '+end+')';$('save-boundary').disabled=false;}
  catch{$('boundary-quote').textContent='Select a nonempty range in the source.';$('save-boundary').disabled=true;}
}
function renderDrafts(){
  $('draft-status').hidden=!drafts.decisions.length;
  const host=$('local-drafts');host.replaceChildren();
  if(!drafts.decisions.length)paragraph(host,'No local draft decisions.',true);
  for(const draft of drafts.decisions){
    const row=make('section',undefined,'research-record');
    const q=snapshot.questions.find(q=>q.id===draft.question_id),option=q?.options.find(o=>o.id===draft.option_id);
    paragraph(row,draft.kind==='term_boundary'?'Term boundary · '+draft.anchor.quote:option?.label||draft.kind);
    paragraph(row,'Draft · '+draft.anchor.quote+' · ['+draft.anchor.start+', '+draft.anchor.end+')',true);
    if(draft.reason)paragraph(row,draft.reason,true);
    const controls=make('div',undefined,'research-actions');row.append(controls);
    action(controls,'Edit draft',()=>{
      editingId=draft.id;setWorkspace('parser');showView('source');
      if(draft.kind==='term_boundary'){
        sourceData.adjust=true;$('adjust-boundary').checked=true;$('boundary-draft').hidden=false;
        $('boundary-start').value=draft.anchor.start;$('boundary-end').value=draft.anchor.end;mountSource();updateBoundary();$('boundary-draft').scrollIntoView({block:'center'});
      }else{
        commitDraftState(selectOption(snapshot,drafts,draft.question_id,draft.option_id));
        selected=draft.object_id||null;facetKey=draft.facet_key||null;questionId=draft.question_id;
        syncSelection();renderDetails();renderQuestion();focusQuestion();
      }
    });
    action(controls,'Retract draft',()=>commitDraftState(retractDraft(snapshot,drafts,draft.id)));
    host.append(row);
  }
}
function renderReviewHistory(){
  const host=$('review-history');host.replaceChildren();paragraph(host,'Recorded in the exported snapshot. Browser drafts do not change this history.',true);
  const decisions=snapshot.review.decisions||[];
  if(!decisions.length)paragraph(host,'No saved decisions in this snapshot.',true);
  for(const decision of decisions){
    const row=make('section',undefined,'research-record');paragraph(row,(decision.targets||[]).map(t=>t.quote).join(' · '));
    paragraph(row,decision.reason||decision.action);paragraph(row,snapshot.review.status?.[decision.decision_id]?.status||'Recorded in snapshot',true);
    evidence(row,'Decision evidence',decision);host.append(row);
  }
  evidence(host,'Snapshot review records',snapshot.review);
}
function unitLabel(unit){return '§'+unit.sections.join(',')+' · '+unit.text_original.split(/[，。；：！？、,.!?;:\r\n]/u)[0];}
function typeBadge(unit){const presentation=snapshot.labels.unit_types?.[unit.type];const badge=make('span',presentation?.label||unit.type);if(presentation?.style)badge.setAttribute('style',presentation.style);return badge;}
function renderCorpus(){
  const corpus=snapshot.corpora.find(c=>c.id===corpusId)||snapshot.corpora[0];if(!corpus)return;
  corpusId=corpus.id;for(const key of ['segmentation-source','corpus-source'])choices($(key),snapshot.corpora.map(c=>[c.id,c.label]),corpusId);
  unitIndex=Math.min(unitIndex,Math.max(0,corpus.effective.length-1));
  choices($('segmentation-unit'),corpus.effective.map((u,i)=>[String(i),unitLabel(u)]),String(unitIndex));
  const progress=corpus.review_status||{};$('segmentation-progress').textContent='Review progress: '+(progress.reviewed??0)+' / '+(progress.total??corpus.effective.length)+' · Modified: '+(progress.modified??0)+' · Accepted unchanged: '+(progress.accepted??0);
  $('previous-unit').disabled=unitIndex===0;$('next-unit').disabled=unitIndex>=corpus.effective.length-1;
  const unit=corpus.effective[unitIndex],panels=$('segmentation-panels');panels.replaceChildren();
  if(unit){
    const spans=unit.source_spans||[];
    const original=corpus.auto.filter(u=>(u.source_spans||[]).some(a=>spans.some(b=>a.start<b.end&&b.start<a.end)));
    for(const [label,units] of [['AUTO · machine source units',original],['EFFECTIVE · current segmentation',[unit]]]){
      const panel=make('section',undefined,'research-panel');panel.append(make('h2',label));
      for(const item of units){const card=make('div',undefined,'research-source-card');card.append(typeBadge(item));paragraph(card,item.text_original);panel.append(card);evidence(panel,'Detection, relations and review evidence',{detection:item.detection,relations:item.relations,human_review:item.human_review,review_queue:item.review_queue});}
      panels.append(panel);
    }
  }
  $('segmentation-history').replaceChildren();evidence($('segmentation-history'),'Recorded segmentation history',corpus.history||[]);
  const host=$('corpus-content');host.replaceChildren();
  for(const unit of corpus.effective){const section=make('section');section.dataset.unitId=unit.id;section.append(typeBadge(unit),make('small',' §'+unit.sections.join(', ')));paragraph(section,unit.text_original);host.append(section);}
}

async function start(){
  const response=await fetch(root.dataset.snapshotUrl);if(!response.ok)throw Error('Snapshot could not be loaded ('+response.status+').');
  snapshot=await response.json();if(snapshot.schema!=='ScholarSandboxSnapshot/1')throw Error('Unsupported Inspector snapshot.');
  root.dataset.snapshotId=snapshot.snapshot_id;
  try{drafts=loadDrafts(snapshot,localStorage);}catch(e){drafts=createDraftState(snapshot);storageBlocked=true;error('Stored drafts were retained: '+e.message);}
  sourceData={text:snapshot.source.text,render:snapshot.renderer,language:'en',focus:null,facet_key:null,adjust:false,changed_ids:[]};
  $('sandbox-loading').hidden=true;$('parser-workspace').hidden=false;
  choices($('source-document'),[[snapshot.source.doc_id,snapshot.source.doc_id]]);
  choices($('parser-source'),snapshot.corpora.filter(c=>c.id===snapshot.source.source_id).map(c=>[c.id,c.label]));
  $('snapshot-description').textContent='Han Si-fen li §38 · exported review '+(snapshot.provenance.review_job_id||'')+' · revision '+(snapshot.provenance.revision??'');
  $('graph-status').textContent='Data-flow status: '+snapshot.procedure_model.status;
  refreshDraftPresentation(true);renderProcedureModel($('procedure-host'),snapshot.procedure_model,{onSelect:choose});
  renderDrafts();renderReviewHistory();corpusId=snapshot.source.source_id;renderCorpus();
  $('collapse-workspace').onclick=()=>sidebar(false);$('expand-workspace').onclick=()=>sidebar(true);
  const mobile=matchMedia('(max-width:800px)');sidebar(!mobile.matches);mobile.addEventListener('change',event=>sidebar(!event.matches));
  root.querySelectorAll('[data-workspace]').forEach(button=>button.onclick=()=>setWorkspace(button.dataset.workspace));
  root.querySelectorAll('[data-view]').forEach(button=>button.onclick=()=>showView(button.dataset.view));
  $('adjust-boundary').onchange=()=>{sourceData.adjust=$('adjust-boundary').checked;$('boundary-draft').hidden=!sourceData.adjust;editingId=null;mountSource();updateBoundary();};
  for(const key of ['boundary-start','boundary-end'])$(key).oninput=updateBoundary;
  $('save-boundary').onclick=()=>attempt(()=>{
    const record={kind:'term_boundary',status:'draft',anchor:makeSourceAnchor(snapshot,Number($('boundary-start').value),Number($('boundary-end').value)),reason:'',inputs:{}};
    if(editingId&&drafts.decisions.some(d=>d.id===editingId&&d.kind==='term_boundary'))record.id=editingId;
    commitDraftState(upsertDraft(snapshot,drafts,record));editingId=null;
  });
  $('export-drafts').onclick=()=>attempt(()=>download('scholar-sandbox-drafts.json',exportDrafts(snapshot,drafts)));
  $('export-snapshot').onclick=()=>download('sifen-38.snapshot.json',snapshot);
  $('export-model').onclick=()=>download('sifen-38.procedure-model.json',snapshot.procedure_model);
  $('import-drafts').onchange=async()=>{
    const file=$('import-drafts').files[0];if(!file)return;
    try{error('');if(file.size>5*1024*1024)throw Error('Draft import exceeds 5 MB limit.');const next=importDrafts(snapshot,await file.text());saveDrafts(snapshot,next,localStorage);drafts=next;storageBlocked=false;renderDrafts();renderDetails();renderQuestion();refreshDraftPresentation();$('draft-io-status').textContent='Drafts imported.';}
    catch(e){error('Draft import rejected; existing drafts retained. '+e.message);}
    finally{$('import-drafts').value='';}
  };
  for(const key of ['segmentation-source','corpus-source'])$(key).onchange=()=>{corpusId=$(key).value;unitIndex=0;renderCorpus();};
  $('segmentation-unit').onchange=()=>{unitIndex=Number($('segmentation-unit').value);renderCorpus();};
  $('previous-unit').onclick=()=>{unitIndex--;renderCorpus();};$('next-unit').onclick=()=>{unitIndex++;renderCorpus();};
  $('browse-corpus').onclick=()=>setWorkspace('corpus');$('back-to-segmentation').onclick=()=>setWorkspace('segmentation');
  root.dataset.ready='true';
}
start().catch(e=>{error(e.message||String(e));$('sandbox-loading').hidden=true;});
