// Shared authored-text tooltip for source annotations and procedure nodes.
export function explainScholarObject(host,element,text){
  element.setAttribute('aria-description',text || '');
  const hide=()=>host.querySelector('.scholar-tooltip')?.remove();
  const show=()=>{
    hide();const tip=document.createElement('div');
    tip.className='scholar-tooltip';tip.textContent=text;tip.setAttribute('role','tooltip');
    host.append(tip);const rect=element.getBoundingClientRect();
    tip.style.left=Math.max(8,Math.min(rect.left,window.innerWidth-340))+'px';
    tip.style.top=Math.max(8,rect.top-tip.getBoundingClientRect().height-8)+'px';
  };
  element.addEventListener('pointerenter',show);element.addEventListener('focus',show);
  element.addEventListener('pointerleave',hide);element.addEventListener('blur',hide);
}
