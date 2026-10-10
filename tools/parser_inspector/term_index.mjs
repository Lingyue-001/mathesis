const FILTERS=new Set(['All','Maximal','Component','Both']);
export const SURFACE_FILTER_LABEL='Filter surface forms';

function requireTermIndex(index){
  if(!index || index.schema!=='TermIndex/1' || !Array.isArray(index.entries)){
    throw new Error('term_index_component_requires_v1');
  }
}

function roleMatches(entry,filter){
  const role=entry.occurrence_classification;
  if(filter==='All')return true;
  if(filter==='Both')return role==='both';
  if(filter==='Maximal')return role==='maximal'||role==='both';
  return role==='component'||role==='both';
}

/** Pure entry selection: exact Unicode form data, never a semantic inference. */
export function filterEntries(index,{query='',filter='All'}={}){
  requireTermIndex(index);
  if(!FILTERS.has(filter))throw new Error('term_index_unknown_filter');
  const form=String(query);
  return index.entries.filter(entry=>roleMatches(entry,filter)&&entry.surface.includes(form));
}

export function selectedEntry(index,surface){
  requireTermIndex(index);
  return index.entries.find(entry=>entry.surface===surface)||null;
}

/** The shell owns navigation; the component discloses no semantic/review state. */
export function navigationEvent(occurrence,nonce=crypto.randomUUID()){
  return {identity:{...occurrence.identity},source_anchor:{...occurrence.source_anchor},nonce};
}

export function restoreSearchFocus(host,start,end){
  const search=host.querySelector('.term-index-search');
  if(!search)return;
  search.focus();
  if(typeof search.setSelectionRange==='function')search.setSelectionRange(start,end);
}

function element(tag,className,text){
  const node=document.createElement(tag);
  if(className)node.className=className;
  if(text!==undefined)node.textContent=text;
  if(tag==='button')node.type='button';
  return node;
}

function compactJson(value){
  return JSON.stringify(value,null,2);
}

function occurrenceLabel(occurrence){
  const identity=occurrence.identity||{};
  const span=identity.start!==undefined?` [${identity.start},${identity.end})`:'';
  return `${occurrence.surface||''} · ${occurrence.display_level||'occurrence'} · ${identity.source_id||''}/${identity.unit_id||''}${span}`;
}

function appendJsonDetail(parent,label,value){
  if(value===undefined||value===null||(Array.isArray(value)&&!value.length))return;
  const detail=element('details','term-index-json');
  detail.append(element('summary','',label));
  detail.append(element('pre','',compactJson(value)));
  parent.append(detail);
}

/**
 * Render a read-only TermIndex/1. `onNavigate` receives identity + source
 * anchor only; it cannot access Annotated Source or review session state.
 */
export function renderTermIndex(host,index,{onNavigate}={}){
  requireTermIndex(index);
  let query='',filter='All',selectedSurface=null;
  const redraw=({searchSelection=null}={})=>{
    host.replaceChildren();
    const root=element('section','term-index');
    root.setAttribute('aria-label','Term Index');
    const controls=element('div','term-index-controls');
    const search=element('input','term-index-search');
    search.type='search';search.placeholder=SURFACE_FILTER_LABEL;search.value=query;
    search.setAttribute('aria-label',SURFACE_FILTER_LABEL);
    search.oninput=()=>{
      const start=search.selectionStart??search.value.length;
      const end=search.selectionEnd??start;
      query=search.value;redraw({searchSelection:[start,end]});
    };
    controls.append(search);
    const filterRow=element('div','term-index-filters');
    for(const label of ['All','Maximal','Component','Both']){
      const button=element('button','term-index-filter',label);
      button.classList.toggle('active',filter===label);
      button.setAttribute('aria-pressed',String(filter===label));
      button.onclick=()=>{filter=label;redraw();};
      filterRow.append(button);
    }
    controls.append(filterRow);root.append(controls);
    const entries=filterEntries(index,{query,filter});
    const body=element('div','term-index-body');
    const list=element('nav','term-index-list');list.setAttribute('aria-label','Term entries');
    if(!entries.length)list.append(element('p','term-index-empty','No exact-form entries match.'));
    for(const entry of entries){
      const button=element('button','term-index-entry',entry.surface);
      button.classList.toggle('active',selectedSurface===entry.surface);
      button.append(element('span','term-index-role',entry.occurrence_classification));
      button.onclick=()=>{selectedSurface=entry.surface;redraw();};
      list.append(button);
    }
    body.append(list);
    const detail=element('article','term-index-detail');
    const entry=selectedSurface?selectedEntry(index,selectedSurface):null;
    if(!entry){
      detail.append(element('p','term-index-empty','Select an entry to inspect its occurrence-local evidence.'));
    }else{
      detail.append(element('h3','',entry.surface));
      detail.append(element('p','term-index-role-summary',entry.occurrence_classification));
      const counts=element('dl','term-index-counts');
      for(const [label,value] of [
        ['Maximal occurrences',entry.counts?.maximal_occurrences||0],
        ['Component occurrences',entry.counts?.component_occurrences||0],
        ['Appears in compounds',entry.counts?.appears_in_compounds||0],
      ]){counts.append(element('dt','',label),element('dd','',String(value)));}
      detail.append(counts);
      appendJsonDetail(detail,'Direct parent occurrences',entry.direct_parent_occurrences);
      appendJsonDetail(detail,'Compound ancestor occurrences',entry.compound_ancestor_occurrences);
      const heading=element('h4','','Occurrences');detail.append(heading);
      const occurrences=element('div','term-index-occurrences');
      for(const occurrence of entry.occurrences||[]){
        const row=element('section','term-index-occurrence');
        const button=element('button','term-index-occurrence-link',occurrenceLabel(occurrence));
        button.onclick=()=>onNavigate?.(navigationEvent(occurrence));
        row.append(button);
        // These values are copied from the Projection; the UI gives them no new status.
        for(const key of ['semantic_candidates','reviewed_claims','semantic_assertions','derived_assertions','semantic_conflicts','decision_refs','review_facets','evidence']){
          appendJsonDetail(row,key.replaceAll('_',' '),occurrence[key]);
        }
        occurrences.append(row);
      }
      detail.append(occurrences);
    }
    body.append(detail);root.append(body);host.append(root);
    if(searchSelection)restoreSearchFocus(host,...searchSelection);
  };
  redraw();
}

export default function({parentElement,data,setStateValue}){
  const host=parentElement.querySelector('.term-index');
  renderTermIndex(host,data?.index,{onNavigate:event=>setStateValue('navigate',event)});
}
