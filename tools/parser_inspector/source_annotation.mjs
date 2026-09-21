import {explainScholarObject} from './scholar_ui.mjs';
// Layout only: source offsets are Unicode code points, never JS string indices.
export function sourceRows(chars, widths, available) {
  const rows = [];
  for (let start = 0; start < chars.length;) {
    let end = start, used = 0, boundary = start;
    while (end < chars.length && (end === start || used + widths[end] <= available)) {
      used += widths[end++];
      if ('，。；：、！？,;:\n'.includes(chars[end - 1])) boundary = end;
      if (chars[end - 1] === '\n') break;
    }
    if (end < chars.length && boundary > start) end = boundary;
    rows.push({row_start:start, row_end:end, text:chars.slice(start,end).join('')});
    start = end;
  }
  return rows;
}

export function fragments(objects, row) {
  return objects.flatMap(object => {
    const start=Math.max(object.span[0],row.row_start), end=Math.min(object.span[1],row.row_end);
    return start < end ? [{...object,fragment:[start,end],continued: start > object.span[0]}] : [];
  });
}

export default function({parentElement, data, setStateValue}) {
  const host=parentElement.querySelector('.source');
  const zh=data.language==='zh';
  host.setAttribute('aria-label',zh?'原文标注':'Source annotation');
  const chars=Array.from(data.text || ''), model=data.render || {terms:[],constructions:[],steps:[]};
  let first=null, dragging=false, previousWidth=0;
  const changed=new Set(data.changed_ids || []);
  const make=(tag,cls,text)=>{
    const element=document.createElement(tag);element.className=cls;
    if(text!==undefined)element.textContent=text;
    if(tag==='button')element.type='button';
    return element;
  };
  function choose(object_id, facet=null) {
    setStateValue('clicked',{object_id,facet_key:facet?.facet_key || null,
      question_id:facet?.question_id || null,nonce:crypto.randomUUID()});
  }
  function badge(facet) {
    const button=make('button','facet '+facet.status,facet.label);
    button.dataset.facet=facet.facet;button.dataset.facetKey=facet.facet_key;
    button.dataset.objectId=facet.object_id;explain(button,facet.hover);
    button.setAttribute('aria-label',facet.label);
    if(facet.facet_key===data.facet_key)button.classList.add('active');
    button.onclick=()=>choose(facet.object_id,facet);return button;
  }
  function explain(element,text) {
    explainScholarObject(host,element,text);
  }
  function highlight(a,b) {
    const start=Math.min(a,b),end=Math.max(a,b)+1;
    host.querySelectorAll('.char').forEach(button=>{
      button.classList.toggle('selected',start<=Number(button.dataset.offset)&&Number(button.dataset.offset)<end);
    });
    return [start,end];
  }
  function draw() {
    host.replaceChildren();
    const available=host.clientWidth;
    if(available<=0)return;
    // Measure the same glyph cells used in the visible layer, without annotations.
    const probe=make('div','glyphs probe');
    for(const char of chars)probe.append(make('button','char',char==='\n'?' ':char));
    host.append(probe);
    const widths=Array.from(probe.children).map(node=>node.getBoundingClientRect().width);
    probe.remove();
    const rows=sourceRows(chars,widths,available);
    rows.forEach(row=>{
      const section=make('section','source-row');
      section.dataset.rowStart=row.row_start;section.dataset.rowEnd=row.row_end;
      const badges=make('div','badge-layer'),glyphs=make('div','glyphs');
      const rails=make('div','rail-layer'), steps=make('div','step-layer');
      section.append(badges,glyphs,rails,steps);host.append(section);
      const termFragments=fragments(model.terms,row), constructionFragments=fragments(model.constructions,row);
      const glyphButtons=new Map();
      for(let i=row.row_start;i<row.row_end;i++){
        const button=make('button','char',chars[i]);
        button.dataset.offset=i;button.setAttribute('aria-label',zh?'原文字位 '+i+'：'+chars[i]:'Source character '+i+': '+chars[i]);
        const covering=termFragments.filter(t=>t.fragment[0]<=i&&i<t.fragment[1]);
        if(covering.length){
          button.classList.add('term');button.dataset.objectId=covering[0].id;
          button.dataset.interpretation=covering[0].gloss.kind;
          explain(button,covering[0].hover);
          button.onclick=()=>{if(!data.adjust)choose(covering[0].id);};
          if(covering.some(t=>t.id===data.focus))button.classList.add('focus');
          if(covering.some(t=>changed.has(t.id)))button.classList.add('changed');
        }
        if(data.adjust){
          button.onpointerdown=event=>{event.preventDefault();first=i;dragging=true;highlight(i,i);};
          button.onpointerenter=()=>{if(dragging&&first!==null)highlight(first,i);};
          button.onpointerup=()=>{if(first!==null)setStateValue('selection',highlight(first,i));first=null;dragging=false;};
        }
        glyphButtons.set(i,button);glyphs.append(button);
      }
      function geometry(span){
        const a=glyphButtons.get(span[0]).getBoundingClientRect();
        const b=glyphButtons.get(span[1]-1).getBoundingClientRect();
        return {left:a.left-glyphs.getBoundingClientRect().left,width:b.right-a.left};
      }
      function anchor(element,object){
        const rect=geometry(object.fragment);
        element.style.left=rect.left+'px';element.style.width=rect.width+'px';
        element.dataset.objectId=object.id;
        element.dataset.start=object.fragment[0];element.dataset.end=object.fragment[1];
        if(object.id===data.focus)element.classList.add('focus');
        if(changed.has(object.id))element.classList.add('changed');
        return rect;
      }
      // Labels can occupy more vertical space; they never change glyph positions.
      function placeLabels(layer,entries,maxWidth,withinSpan=false){
        const occupied=[];
        const gap=withinSpan?4:8;
        for(const {element,span} of entries){
          layer.append(element);
          const rect=geometry(span);
          element.style.maxWidth=Math.min(maxWidth,available)+'px';
          const box=element.getBoundingClientRect();
          const preferred=Math.max(0,Math.min(rect.left,available-box.width));
          const limit=withinSpan?Math.max(preferred,Math.min(rect.left+rect.width-box.width,available-box.width)):preferred;
          let left=preferred;
          let top=0;
          for(;;){
            const blockers=occupied.filter(r=>top<r.bottom+3&&top+box.height+3>r.top);
            // Try horizontal room over the owning span before adding a row.
            const positions=[preferred,...blockers.map(r=>r.right+gap)].filter(x=>x>=preferred&&x<=limit).sort((a,b)=>a-b);
            const free=positions.find(x=>!blockers.some(r=>x<r.right+gap&&x+box.width+gap>r.left));
            if(free!==undefined){left=free;break;}
            top=Math.min(...blockers.map(r=>r.bottom+4));
          }
          element.style.left=left+'px';element.style.top=top+'px';
          occupied.push({left,right:left+box.width,top,bottom:top+box.height});
        }
        layer.style.height=(occupied.length?Math.max(...occupied.map(r=>r.bottom))+5:0)+'px';
      }
      const badgeEntries=[];
      for(const term of termFragments){
        const group=make('span','badge-group');for(const f of term.badges||[])group.append(badge(f));
        if(group.childNodes.length)badgeEntries.push({element:group,span:term.fragment});
      }
      for(const construction of constructionFragments){
        if(construction.continued)continue;
        const group=make('span','badge-group');
        for(const facet of construction.badges||[])group.append(badge(facet));
        if(group.childNodes.length)badgeEntries.push({element:group,span:construction.fragment});
      }
      // Visual placement is shared; each badge keeps its canonical facet owner.
      placeLabels(badges,badgeEntries,available,true);
      let railHeight=0;
      const laneEnds=[];
      for(const construction of constructionFragments){
        const rail=make('button','rail',construction.continued?'↳':construction.public_kind || construction.label);
        const rect=anchor(rail,construction);
        const lane=laneEnds.findIndex(end=>end<=rect.left);
        const index=lane<0?laneEnds.length:lane;
        laneEnds[index]=rect.left+rect.width+8;
        rail.style.top=(index*24)+'px';
        explain(rail,construction.hover+(construction.adjudication?'\n'+construction.label:''));
        if(construction.adjudication)rail.classList.add('fixed');
        rail.onclick=()=>choose(construction.id);rails.append(rail);
        railHeight=Math.max(railHeight,(index+1)*24);
      }
      rails.style.height=railHeight+'px';
      const stepEntries=[];
      for(const step of model.steps){
        for(const token of step.presentation||[]){
          for(const part of fragments([{...token,id:step.id}],row)){
            const text=token.label;
            const label=make('button','step-token '+token.role+(token.alignment==='broad'?' broad':''),text);
            label.setAttribute('aria-label',token.label);
            anchor(label,part);label.style.width='auto';label.onclick=()=>choose(step.id);
            label.dataset.alignment=token.alignment;
            explain(label,step.hover+(token.alignment==='broad'?(zh?'\n没有可用的精确提示跨度':'\nExact cue alignment unavailable'):''));
            stepEntries.push({element:label,span:part.fragment});
          }
        }
      }
      placeLabels(steps,stepEntries,104);
    });
  }
  const observer=new ResizeObserver(entries=>{
    const width=Math.round(entries[0].contentRect.width);
    if(width!==previousWidth){previousWidth=width;draw();}
  });
  observer.observe(host);draw();
  const stop=()=>{dragging=false;first=null;};
  parentElement.addEventListener('pointerup',stop);
  return ()=>{observer.disconnect();parentElement.removeEventListener('pointerup',stop);};
}
