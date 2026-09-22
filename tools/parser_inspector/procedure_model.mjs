import {explainScholarObject} from './scholar_ui.mjs';
let graphInstance=0;

// Pure topology layout. Leaves are placed near their first consumer rather
// than on a distant, disconnected-looking bank of inputs. No semantic rules.
export function layoutProcedureModel(model){
  const nodes=new Map(model.nodes.map(n=>[n.id,n]));
  const incoming=new Map(model.nodes.map(n=>[n.id,[]]));
  const outgoing=new Map(model.nodes.map(n=>[n.id,[]]));
  for(const edge of model.edges){
    if(nodes.has(edge.from)&&nodes.has(edge.to)){
      incoming.get(edge.to).push(edge.from);outgoing.get(edge.from).push(edge.to);
    }
  }
  const pending=new Map([...incoming].map(([id,items])=>[id,items.length]));
  const queue=model.nodes.filter(n=>pending.get(n.id)===0).map(n=>n.id), ranks=new Map();
  for(let i=0;i<queue.length;i++){
    const id=queue[i];
    ranks.set(id,Math.max(0,...incoming.get(id).map(from=>(ranks.get(from)||0)+1)));
    for(const target of outgoing.get(id)){
      pending.set(target,pending.get(target)-1);
      if(pending.get(target)===0)queue.push(target);
    }
  }
  const cyclic=model.nodes.filter(n=>!ranks.has(n.id));
  for(const node of cyclic)ranks.set(node.id,Math.max(0,...ranks.values())+1);
  for(const node of model.nodes){
    if(!incoming.get(node.id).length&&outgoing.get(node.id).length&&node.type!=='operation'){
      ranks.set(node.id,Math.max(0,Math.min(...outgoing.get(node.id).map(id=>ranks.get(id)))-1));
    }
  }
  const layers=[];
  for(const node of model.nodes)(layers[ranks.get(node.id)]??=[]).push(node);
  const width=Math.max(740,...layers.map(layer=>(layer?.length||0)*236+64));
  const positions=new Map();
  layers.forEach((layer,rank)=>{
    if(!layer)return;
    const ordered=[...layer].sort((a,b)=>{
      const average=n=>{const xs=incoming.get(n.id).map(id=>positions.get(id)?.x).filter(x=>x!==undefined);return xs.length?xs.reduce((a,b)=>a+b,0)/xs.length:width/2;};
      return average(a)-average(b)||a.id.localeCompare(b.id);
    });
    const operation=ordered.filter(n=>n.type==='operation');
    if(operation.length===1&&ordered.length===2){
      const other=ordered.find(n=>n!==operation[0]);
      positions.set(operation[0].id,{x:width/2,y:rank*110+30,width:192,height:62});
      positions.set(other.id,{x:width/2-236,y:rank*110+30,width:192,height:62});
    }else ordered.forEach((node,i)=>positions.set(node.id,{x:width/2+(i-(ordered.length-1)/2)*236,
      y:rank*110+30,width:192,height:62}));
  });
  for(const node of model.nodes)if(node.type==='literal')positions.get(node.id).width=70;
  return {positions,width,height:Math.max(130,layers.length*110+20),cyclic:cyclic.map(n=>n.id)};
}

export function renderProcedureModel(host,model,{selectedObjectId=null,onSelect=null}={}){
  host.replaceChildren();host.classList.add('procedure-model');
  if(model.schema!=='ProcedureModel/1')throw new Error('Expected ProcedureModel/1');
  const make=(tag,cls,text)=>{const el=document.createElement(tag);el.className=cls;if(text!==undefined)el.textContent=text;return el;};
  const svgEl=(tag,attrs={})=>{const el=document.createElementNS('http://www.w3.org/2000/svg',tag);for(const [key,value] of Object.entries(attrs))el.setAttribute(key,value);return el;};
  const layout=layoutProcedureModel(model);
  const legend=make('div','procedure-legend','Quantity · rounded   /   Operation · rectangular   /   Unresolved source · dashed   /   Judgment · double border');
  host.append(legend);
  if(layout.cyclic.length)host.append(make('p','procedure-warning','Recorded dependencies contain a cycle; all recorded edges are retained.'));
  if(!model.nodes.length){host.append(make('p','procedure-warning','No computational steps are projected for this source.'));return ()=>host.replaceChildren();}
  const canvas=make('div','procedure-canvas');host.append(canvas);
  const svg=svgEl('svg',{viewBox:`0 0 ${layout.width} ${layout.height}`,width:layout.width,height:layout.height,
    role:'group','aria-label':'Source-linked procedure graph'});
  canvas.append(svg);
  const markerId='procedure-arrow-'+(++graphInstance);
  const defs=svgEl('defs'), marker=svgEl('marker',{id:markerId,viewBox:'0 0 10 10',refX:9,refY:5,markerWidth:6,markerHeight:6,orient:'auto-start-reverse'});
  marker.append(svgEl('path',{d:'M 0 0 L 10 5 L 0 10 z',fill:'#8a9398'}));defs.append(marker);svg.append(defs);
  for(const edge of model.edges){
    const a=layout.positions.get(edge.from),b=layout.positions.get(edge.to);if(!a||!b)continue;
    const start=a.y+a.height,end=b.y,mid=(start+end)/2;
    const line=svgEl('path',{d:`M ${a.x} ${start} C ${a.x} ${mid} ${b.x} ${mid} ${b.x} ${end}`,
      class:'procedure-edge','marker-end':`url(#${markerId})`,'data-from':edge.from,'data-to':edge.to,'data-role':edge.role||''});
    svg.append(line);
    explainScholarObject(host,line,[edge.label,'Recorded role: '+(edge.role||'unspecified'),edge.definition,
      edge.output_port?'Output port: '+edge.output_port:null].filter(Boolean).join('\n'));
    const text=svgEl('text',{x:(a.x+b.x)/2,y:mid-5,class:'procedure-edge-label','text-anchor':'middle'});
    text.textContent=edge.label;svg.append(text);
  }
  let detail;
  const showStaticDetail=node=>{
    if(!detail){detail=make('aside','procedure-static-detail');host.append(detail);}
    detail.replaceChildren(make('h3','',node.label));
    for(const anchor of node.source_anchors){
      const p=make('p','procedure-source-context');
      if(anchor.doc_id===model.source.doc_id&&model.source.text){
        const chars=Array.from(model.source.text);
        p.append(document.createTextNode(chars.slice(0,anchor.start).join('')),make('mark','',chars.slice(anchor.start,anchor.end).join('')),
          document.createTextNode(chars.slice(anchor.end).join('')));
      }else p.textContent=(anchor.doc_id||'')+' · '+(anchor.quote||'');
      detail.append(p);
    }
    if(node.anchor_scope==='supporting_step')detail.append(make('p','','Supporting Step source; no separate exact anchor is recorded for this node.'));
    const evidence=make('details',''),summary=make('summary','','Evidence');
    evidence.append(summary,make('pre','',JSON.stringify(node,null,2)));detail.append(evidence);
  };
  for(const node of model.nodes){
    const p=layout.positions.get(node.id);
    const group=svgEl('g',{class:'procedure-node '+node.type,transform:`translate(${p.x-p.width/2} ${p.y})`,
      role:'button',tabindex:0,'aria-label':node.label,'data-node-id':node.id,
      'data-object-id':node.selection_object_id||'','data-node-type':node.type,'data-operation':node.operation||''});
    const selected=selectedObjectId!==null&&node.selection_object_id===selectedObjectId;
    group.classList.toggle('active',selected);group.setAttribute('aria-pressed',String(selected));
    const rounded=['input_quantity','unresolved_input','named_quantity','quantity'].includes(node.type);
    const shape=svgEl('rect',{width:p.width,height:p.height,rx:rounded?14:node.type==='literal'?5:2});
    group.append(shape);
    if(node.type==='judgment')group.append(svgEl('rect',{x:4,y:4,width:p.width-8,height:p.height-8,rx:2,class:'procedure-inner-border'}));
    const label=svgEl('text',{x:p.width/2,y:25,'text-anchor':'middle',class:'procedure-node-label'});label.textContent=node.label;
    if(node.label.length>25){label.setAttribute('textLength',p.width-20);label.setAttribute('lengthAdjust','spacingAndGlyphs');}
    const subtitle=svgEl('text',{x:p.width/2,y:44,'text-anchor':'middle',class:'procedure-node-subtitle'});
    subtitle.textContent=node.semantic_summary || (node.status==='runtime_value_permitted'?'Runtime value · source unresolved':node.status_label||
      ({operation:'Operation',named_quantity:node.output_port,judgment:'Judgment',literal:'Literal',quantity:node.output_port}[node.type]||'Quantity'));
    if(node.semantic_summary?.length>42)subtitle.textContent=node.semantic_summary.slice(0,39)+'…';
    if(subtitle.textContent.length>29){subtitle.setAttribute('textLength',p.width-18);subtitle.setAttribute('lengthAdjust','spacingAndGlyphs');}
    group.append(label,subtitle);svg.append(group);
    const hover=[node.label,node.definition,node.status_label,node.semantic_summary,
      ...(node.interpretations||[]).flatMap(i=>[
        i.reviewed_claim_count?'Term review records: '+i.reviewed_claim_count:null,
        i.candidate_statuses.length?'Machine candidate status: '+i.candidate_statuses.join(', '):null]),
      ...(node.source_anchors||[]).map(a=>a.quote),
      node.anchor_scope==='supporting_step'?'Supporting Step source; exact node anchor unavailable':null].filter(Boolean).join('\n');
    explainScholarObject(host,group,hover);
    const select=()=>{
      if(onSelect)onSelect({object_id:node.selection_object_id,facet_key:null,question_id:null,nonce:crypto.randomUUID()});
      else{
        svg.querySelectorAll('.procedure-node').forEach(el=>{const active=el===group;el.classList.toggle('active',active);el.setAttribute('aria-pressed',String(active));});
        showStaticDetail(node);
      }
    };
    group.addEventListener('click',select);
    group.addEventListener('keydown',event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();select();}});
  }
  return ()=>host.replaceChildren();
}

// Small adapter only. Static sites import renderProcedureModel directly.
export default function({parentElement,data,setStateValue}){
  return renderProcedureModel(parentElement.querySelector('.procedure-model'),data.model,
    {selectedObjectId:data.focus,onSelect:click=>setStateValue('clicked',click)});
}
