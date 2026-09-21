// Real browser acceptance over current-tree Python + isolated ReviewJob stores.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import net from 'node:net';
import {spawn} from 'node:child_process';
import {once} from 'node:events';
import {fileURLToPath} from 'node:url';
import {chromium} from 'playwright';

const repo=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const output=path.join(repo,'tmp/scholar-renderer-v02');
const procedureOutput=path.join(repo,'tmp/procedure-model-v1');
await fs.mkdir(output,{recursive:true});
await fs.mkdir(procedureOutput,{recursive:true});
const scratch=await fs.mkdtemp(path.join(output,'run-'));
const root=path.join(scratch,'source'); await fs.mkdir(root);
const python=path.join(repo,'tools/parser_inspector/.venv/Scripts/python.exe');
let child,browser,page,serverLog='';
const checks=[];
async function runPython(code,...args){
  const process=spawn(python,['-X','utf8','-B','-c',code,...args],{cwd:repo,windowsHide:true});
  let result='';process.stdout.on('data',d=>result+=d);process.stderr.on('data',d=>result+=d);
  assert.equal((await once(process,'exit'))[0],0,result);return result;
}
async function settled(){
  await page.waitForFunction(()=>document.querySelector('[data-testid="stApp"]')?.getAttribute('data-test-script-state')==='notRunning');
  assert.equal(await page.locator('[data-testid="stException"]').count(),0,await page.locator('[data-testid="stException"]').allTextContents());
}
async function snapshot(name,hoverTarget=null,directory=output){
  await page.setViewportSize({width:1450,height:1800});
  await page.locator('[data-testid="stMain"]').evaluate(el=>el.scrollTop=0);
  await page.mouse.move(0,0);
  // Streamlit expanders animate independently of Python's script state.
  await page.waitForTimeout(250);
  if(hoverTarget){
    await hoverTarget.hover();
    assert.equal(await page.getByRole('tooltip').innerText(),await hoverTarget.getAttribute('aria-description'));
  }
  await page.screenshot({path:path.join(directory,name+'.png'),fullPage:true});
  await page.setViewportSize({width:1450,height:1050});
}
async function clickObject(id){
  await page.locator('.source .char[data-object-id="'+id+'"]').first().click();
  await page.getByRole('heading',{name:'Selected source object',exact:true}).waitFor();
  await page.waitForTimeout(350);await settled();
}
async function clickFacet(id,family){
  await page.locator('.source .facet[data-object-id="'+id+'"][data-facet="'+family+'"]').first().click();
  await page.waitForTimeout(350);await settled();
}
try{
  await runPython(
    "from pathlib import Path; import sys; from tests.workbench.test_review_jobs import isolated_source, SELECTION; from workbench import service; r=Path(sys.argv[1]); isolated_source(r); [service.create_review_job(r,j,{**SELECTION,'primary_unit_ids':['sifen:section:38'],'provided_scope':{}}) for j in ('renderer-browser','renderer-context-browser')]",
    root);
  const host=path.join(scratch,'host.py');
  await fs.writeFile(host,[
    'import sys',
    'sys.path.insert(0, '+JSON.stringify(repo.replaceAll('\\','/'))+')',
    'import streamlit as st',
    'from tools.parser_inspector.review_panel import render',
    "st.set_page_config(layout='wide')",
    'render('+JSON.stringify(root.replaceAll('\\','/'))+')',
  ].join('\n'),'utf8');
  const socket=net.createServer();socket.listen(0,'127.0.0.1');await once(socket,'listening');
  const port=socket.address().port;await new Promise(resolve=>socket.close(resolve));
  child=spawn(python,['-X','utf8','-B','-m','streamlit','run',host,'--server.address','127.0.0.1',
    '--server.port',String(port),'--server.headless','true','--server.fileWatcherType','none',
    '--browser.gatherUsageStats','false'],{cwd:repo,windowsHide:true});
  child.stdout.on('data',d=>serverLog+=d);child.stderr.on('data',d=>serverLog+=d);
  for(let i=0;i<100;i++){
    try{if((await fetch('http://127.0.0.1:'+port+'/_stcore/health')).ok)break;}catch{}
    await new Promise(resolve=>setTimeout(resolve,100));
  }
  browser=await chromium.launch({headless:true});
  page=await browser.newPage({viewport:{width:1450,height:1050}});
  const pageErrors=[];page.on('pageerror',e=>pageErrors.push(String(e)));
  await page.goto('http://127.0.0.1:'+port+'?review_job=renderer-browser');
  await page.locator('.source .char').first().waitFor();await settled();
  assert.equal(await page.locator('.source .facet.active,.source .focus').count(),0,'initial reading view must not select a question or object');
  assert.ok(await page.locator('.source-row').count()>1);
  assert.equal(await page.locator('.source').evaluate(el=>el.scrollWidth>el.clientWidth+1),false);
  const source=await page.locator('.glyphs:not(.probe)').allTextContents();
  assert.equal(source.join(''),'推天正術，置入蔀年減一，以章月乘之，滿章法得一，名為積月，不滿為閏餘，十二以上，其歲有閏。');
  assert.equal(await page.locator('.glyphs .facet,.glyphs .term-gloss').count(),0);
  const exported=path.join(repo,'.cache/procedure-model/proc38.procedure-model.json');
  await runPython("import sys; from workbench import service; from workbench.annotation_projection import project_scholar_source; from workbench.procedure_model import build_procedure_model, export_procedure_model; r=service.compile_review_job(sys.argv[1],'renderer-browser'); p=project_scholar_source(r['effective_packet'],r['compilation'],r['questions'],r['session']['decisions'],r['compilation']['replay']['decision_status']); export_procedure_model(build_procedure_model(p), sys.argv[2])",root,exported);
  const procedure=JSON.parse(await fs.readFile(exported,'utf8'));
  const jobBytesBefore=await runPython("import sys; from pathlib import Path; from workbench.review_jobs import job_path; print(job_path(Path(sys.argv[1]),'renderer-browser').read_text(encoding='utf-8'))",root);
  await page.getByText('Procedure Model',{exact:true}).click();
  await page.locator('.procedure-node').first().waitFor();await settled();
  assert.equal(await page.locator('.procedure-node').count(),procedure.nodes.length);
  assert.equal(await page.locator('.procedure-edge').count(),procedure.edges.length);
  assert.equal(await page.locator('.procedure-node.unresolved_input').count(),3);
  assert.equal(await page.getByRole('button',{name:'Confirm and re-run',exact:true}).count(),0);
  const downloadPromise=page.waitForEvent('download');
  await page.getByText('Download Procedure Model JSON',{exact:true}).click();
  const download=await downloadPromise;
  assert.equal(await fs.readFile(await download.path(),'utf8'),await fs.readFile(exported,'utf8'));
  await snapshot('01-proc38-procedure-model',null,procedureOutput);
  const graphDivide=page.locator('.procedure-node[data-operation="divmod"]');
  await graphDivide.hover();
  assert.ok((await page.getByRole('tooltip').innerText()).includes('Produces separate quotient and remainder outputs'));
  await graphDivide.click();await page.waitForTimeout(350);await settled();
  assert.ok((await page.locator('.k2-evidence mark').allTextContents()).includes('滿章法得一'));
  await snapshot('02-divmod-source-context',null,procedureOutput);
  await page.getByText('Annotated Source',{exact:true}).click();
  await page.locator('.source .step-token.focus').first().waitFor();await settled();
  assert.equal(await page.locator('.source .step-token.focus[data-object-id="step:sifen:38:18-23:divmod:0"]').count(),3);
  await page.getByText('Procedure Model',{exact:true}).click();
  await page.locator('.procedure-node[data-operation="divmod"].active').waitFor();
  await page.locator('.procedure-node[data-object-id="term:sifen:38:19-21"]').click();
  await page.waitForTimeout(350);await settled();
  assert.ok((await page.locator('.k2-evidence mark').allTextContents()).includes('章法'));
  await snapshot('03-unresolved-source',null,procedureOutput);
  const jobBytesAfter=await runPython("import sys; from pathlib import Path; from workbench.review_jobs import job_path; print(job_path(Path(sys.argv[1]),'renderer-browser').read_text(encoding='utf-8'))",root);
  assert.equal(jobBytesAfter,jobBytesBefore,'graph exploration must not mutate the ReviewJob');
  // Load the exact exported JSON in a static page, with no Streamlit adapter or save service.
  const staticPage=await browser.newPage();
  staticPage.on('pageerror',e=>pageErrors.push(String(e)));
  await staticPage.route('http://procedure.test/**',async route=>{
    const name=new URL(route.request().url()).pathname.slice(1);
    if(name==='model.json')return route.fulfill({contentType:'application/json',body:await fs.readFile(exported,'utf8')});
    if(['procedure_model.mjs','scholar_ui.mjs','procedure_model.css','scholar_ui.css'].includes(name)){
      return route.fulfill({contentType:name.endsWith('.mjs')?'text/javascript':'text/css',body:await fs.readFile(path.join(repo,'tools/parser_inspector',name),'utf8')});
    }
    return route.fulfill({contentType:'text/html',body:'<link rel="stylesheet" href="/scholar_ui.css"><link rel="stylesheet" href="/procedure_model.css"><div id="model"></div><script type="module">import {renderProcedureModel} from "/procedure_model.mjs"; renderProcedureModel(document.querySelector("#model"),await (await fetch("/model.json")).json());</script>'});
  });
  await staticPage.goto('http://procedure.test/');
  await staticPage.locator('.procedure-node[data-operation="divmod"]').click();
  assert.ok((await staticPage.locator('.procedure-source-context mark').allTextContents()).includes('滿章法得一'));
  assert.equal(await staticPage.getByText('Confirm and re-run',{exact:true}).count(),0);
  await staticPage.close();
  await page.getByText('Annotated Source',{exact:true}).click();
  await page.locator('.source .char').first().waitFor();await settled();
  checks.push('Procedure Model: current pure JSON, exact download, 13 nodes/12 edges, source selection round-trip, ontology hover, byte-identical ReviewJob, static renderer works without review controls');
  async function checkTopBadges(){
    assert.ok(await page.locator('.source .facet').evaluateAll(els=>els.every(el=>{
      const row=el.closest('.source-row'),box=el.getBoundingClientRect();
      const glyphs=row.querySelector('.glyphs').getBoundingClientRect();
      return el.closest('.badge-layer')&&box.bottom<=glyphs.top&&box.left>=glyphs.left-1&&box.right<=glyphs.right+1;
    })), 'all facets must remain above their source row');
    assert.ok(await page.locator('.source-row').evaluateAll(rows=>rows.every(row=>{
      const boxes=Array.from(row.querySelectorAll('.facet'),el=>el.getBoundingClientRect());
      return boxes.every((a,i)=>boxes.slice(i+1).every(b=>a.right<=b.left||b.right<=a.left||a.bottom<=b.top||b.bottom<=a.top));
    })), 'Term and Construction badges must not overlap');
  }
  await checkTopBadges();
  const countBadge=page.locator('.facet[data-object-id="construction:sifen:38:5-11:load"][data-facet="quantity_meaning"]');
  async function checkLoadBadgesInline(){
    const boxes=await page.locator('.facet[data-object-id="construction:sifen:38:5-11:load"],.facet[data-object-id="term:sifen:38:6-9"]').evaluateAll(els=>els.map(el=>{
      const r=el.getBoundingClientRect();return {top:r.top,left:r.left,right:r.right};
    }));
    assert.equal(boxes.length,3);
    assert.ok(boxes.every(b=>Math.abs(b.top-boxes[0].top)<1),'source, meaning and count badges must share one line');
    const count=await countBadge.boundingBox();
    const rail=await page.locator('.rail[data-object-id="construction:sifen:38:5-11:load"]').boundingBox();
    assert.ok(count.x>=rail.x&&count.x+count.width<=rail.x+rail.width+1,'count stays over its owning Construction span');
  }
  await checkLoadBadgesInline();
  const countKey=await countBadge.getAttribute('data-facet-key');
  const countTitle=await countBadge.getAttribute('aria-description');
  await clickFacet('construction:sifen:38:5-11:load','quantity_meaning');
  await page.locator('[data-testid="stMarkdownContainer"]').getByText(countTitle,{exact:true}).waitFor();
  assert.equal(await countBadge.getAttribute('data-facet-key'),countKey);
  assert.ok(await countBadge.evaluate(el=>el.classList.contains('active')&&getComputedStyle(el).outlineStyle==='none'&&getComputedStyle(el).borderTopWidth==='1px'));
  assert.equal(await page.locator('.rail.focus[data-object-id="construction:sifen:38:5-11:load"]').count(),1);
  await checkTopBadges();
  await page.mouse.move(0,0);
  await page.locator('.source-row').filter({has:countBadge}).screenshot({path:path.join(output,'06-count-top-active.png')});
  await page.setViewportSize({width:950,height:1050});
  await page.waitForTimeout(250);await checkTopBadges();await checkLoadBadgesInline();
  await page.setViewportSize({width:1450,height:1050});
  await page.waitForTimeout(250);
  checks.push('all facets share top collision layout at desktop/narrow widths; count retains Load ownership and exact question with single-border active state');
  await snapshot('01-proc38-overview');
  checks.push('wrapping / exact text / glyph-only layer / no horizontal overflow');

  const geometry=async()=>page.locator('.rail').evaluateAll(els=>els.map(el=>{
    const r=el.getBoundingClientRect();return [el.dataset.objectId,r.x,r.width];
  }));
  const before=await geometry();
  assert.equal(await page.locator('.source .term-gloss,.source .inline-note').count(),0);
  assert.equal(await page.locator('.source [title]').count(),0);
  await page.locator('.char[data-object-id="term:sifen:38:6-9"]').first().hover();
  assert.ok((await page.getByRole('tooltip').innerText()).includes('2 machine suggestions'));
  assert.ok((await page.getByRole('tooltip').innerText()).includes('civil years'));
  await snapshot('00-term-machine-hover',page.locator('.char[data-object-id="term:sifen:38:6-9"]').first());
  await page.getByRole('tooltip').evaluate(el=>el.textContent='A deliberately very long hover '.repeat(12));
  assert.deepEqual(await geometry(),before);
  assert.ok(await page.locator('.rail').evaluateAll(els=>els.every(el=>{
    const row=el.closest('.source-row'),rect=el.getBoundingClientRect();
    const first=row.querySelector('.char[data-offset="'+el.dataset.start+'"]').getBoundingClientRect();
    const last=row.querySelector('.char[data-offset="'+(Number(el.dataset.end)-1)+'"]').getBoundingClientRect();
    return Math.abs(rect.left-first.left)<1&&Math.abs(rect.right-last.right)<1;
  })));
  await page.reload();await page.locator('.source .char').first().waitFor();await settled();
  checks.push('no inline Term gloss or native tooltip; custom hover lists suggestions without moving rail geometry');
  await clickObject('term:sifen:38:19-21');
  await page.getByText('Review overview',{exact:true}).waitFor();
  assert.equal(await page.getByRole('heading',{name:'Current question',exact:true}).count(),0);
  await snapshot('02-zhangfa-review-overview');
  await clickFacet('term:sifen:38:19-21','term_meaning');
  await page.getByRole('heading',{name:'Current question',exact:true}).waitFor();
  await snapshot('03-zhangfa-exact-meaning');
  checks.push('bare Term gives review overview; badge gives exact existing question');
  await clickObject('term:sifen:38:6-9');
  const tokens=await page.locator('.step-token').evaluateAll(els=>els.map(el=>[el.getAttribute('aria-label'),Number(el.dataset.start),Number(el.dataset.end)]));
  assert.ok(tokens.some(t=>JSON.stringify(t)===JSON.stringify(['load',5,6])));
  assert.ok(tokens.some(t=>JSON.stringify(t)===JSON.stringify(['input',6,9])));
  assert.ok(tokens.some(t=>JSON.stringify(t)===JSON.stringify(['subtract 1',9,11])));
  assert.ok(tokens.some(t=>JSON.stringify(t)===JSON.stringify(['multiply',15,16])));
  await page.locator('.source-row').filter({has:page.locator('.step-token[aria-label="load"]')}).screenshot({path:path.join(output,'06-load-input-subtract.png')});
  assert.ok(tokens.some(t=>t[0]==='operand'));
  assert.ok(tokens.some(t=>t[0]==='previous result'));
  assert.ok(tokens.some(t=>t[0]==='lower bound'&&t[1]===35&&t[2]===37));
  assert.ok(tokens.some(t=>t[0]==='test ≥'&&t[1]===37&&t[2]===39));
  assert.equal(tokens.filter(t=>t[0]==='test ≥').length,1);
  assert.ok(!tokens.some(t=>t[1]>=40&&t[1]<44));
  assert.ok(!tokens.some(t=>['left','right','prior / right','×','÷','threshold'].includes(t[0])));
  await page.locator('.source-row').filter({has:page.locator('.step-token[aria-label="multiply"]')}).screenshot({path:path.join(output,'07-multiply.png')});
  await page.locator('.source-row').filter({has:page.locator('.step-token[aria-label="test ≥"]')}).screenshot({path:path.join(output,'08-threshold.png')});
  const divideRail=page.locator('.rail[data-object-id="construction:sifen:38:18-23:divide"]').first();
  assert.ok((await divideRail.getAttribute('aria-description')).includes('An expression that divides by a specified divisor'));
  await snapshot('09-construction-hover',divideRail);
  const divideStep=page.locator('.step-token[aria-label="divide with remainder"]').first();
  assert.ok((await divideStep.getAttribute('aria-description')).includes('Produces separate quotient and remainder outputs'));
  await snapshot('09-step-hover',divideStep);
  await page.mouse.move(0,0);
  checks.push('separate load / input / subtract and multiply operation cue');

  await clickObject('term:sifen:38:26-28');
  const right=page.locator('[data-testid="stColumn"]').nth(1);
  const visibleText=await right.locator('[data-testid="stMarkdownContainer"]').filter({visible:true}).allTextContents();
  assert.ok(visibleText.join(' ').includes('積'));
  assert.ok(!visibleText.join(' ').includes('Search hints'));
  assert.ok(!visibleText.join(' ').includes('章法 · unresolved'));
  assert.ok(!visibleText.join(' ').includes('term:sifen'));
  await snapshot('05-accumulated-months-local');
  for(const id of ['term:sifen:38:26-28','term:sifen:38:32-34']){
    assert.equal(await page.locator('.source .facet[data-object-id="'+id+'"][data-facet="term_meaning"]').count(),1);
    await clickFacet(id,'term_meaning');
    await page.getByRole('heading',{name:'Current question',exact:true}).waitFor();
    assert.equal(await page.getByRole('button',{name:'Confirm and re-run',exact:true}).count(),1);
  }
  await snapshot('05-named-remainder-meaning');
  await page.getByRole('button',{name:'Confirm and re-run',exact:true}).click();
  await page.getByRole('heading',{name:'Last change',exact:true}).waitFor();await settled();
  checks.push((await runPython(
    "import sys; from workbench import service; r=service.compile_review_job(sys.argv[1],'renderer-browser'); d=r['session']['decisions'][-1]; assert d['action']=='set_term_interpretation'; assert d['targets'][0]['start']==32 and d['targets'][0]['end']==34; assert r['compilation']['replay']['decision_status'][d['decision_id']]['status']=='active'; assert any(q['kind']=='term_interpretation' and q['anchor']['start']==26 for q in r['questions']); print('named-output interpretation saved through existing action; other named output remains pending')",root)).trim());
  checks.push('both named outputs expose real term_meaning badges and existing interpretation options');
  checks.push('積月 selection is local with component labels and no unrelated source help');
  await clickFacet('term:sifen:38:19-21','source_supply');
  await page.getByText('Canonical producer candidates',{exact:true}).waitFor();
  await page.getByText('Inspect · §15 · 章法',{exact:true}).click();
  await page.getByRole('button',{name:'Add as context & re-run',exact:true}).waitFor();
  await snapshot('04-zhangfa-source-supply');
  checks.push('source badge selects existing source question and gates search assistance');
  // Save a real term interpretation first; its explicit refs must not spread to Steps.
  await clickFacet('term:sifen:38:19-21','term_meaning');
  await page.getByRole('button',{name:'Confirm and re-run',exact:true}).click();
  await page.getByRole('heading',{name:'Last change',exact:true}).waitFor();await settled();
  await snapshot('10-post-confirm');
  assert.ok(await page.locator('.char[data-interpretation="reviewed"]').count()>0);
  await page.locator('.char[data-interpretation="reviewed"]').first().hover();
  assert.ok((await page.getByRole('tooltip').innerText()).includes('Reviewed interpretation'));
  await snapshot('10-reviewed-term-hover',page.locator('.char[data-interpretation="reviewed"]').first());
  const validation=await runPython(
    "import sys; from workbench import service; from workbench.annotation_projection import project_scholar_source; r=service.compile_review_job(sys.argv[1],'renderer-browser'); p=project_scholar_source(r['effective_packet'],r['compilation'],r['questions'],r['session']['decisions'],r['compilation']['replay']['decision_status']); assert r['job']['revision']==3; assert not any(s['decision_refs'] for s in p['steps']); print('real decisions saved, no invented step provenance')",
    root);
  checks.push(validation.trim());
  await clickFacet('term:sifen:38:19-21','source_supply');
  await page.getByRole('radio',{name:'Provide “章法” for this standalone numerical check',exact:true}).check({force:true});
  await page.getByRole('button',{name:'Confirm and re-run',exact:true}).click();
  await page.locator('.source .facet[data-facet="construction_context_requirement"]').waitFor();await settled();
  await clickFacet('construction:sifen:38:18-23:divide','construction_context_requirement');
  await page.getByText('Construction context requirement',{exact:true}).waitFor();
  assert.equal(await page.getByText('Search hints — not yet linked',{exact:true}).count(),0);
  await snapshot('11-divmod-context');
  checks.push('C3 context question is separate from reviewed runtime source supply');
  // Object selection clears the old facet and cannot bounce back on a rerun.
  await clickObject('term:sifen:38:26-28');
  await page.locator('.st-key-k2_adjust').click();await page.waitForTimeout(350);await settled();
  assert.equal(await page.getByText('Construction context requirement',{exact:true}).count(),0);
  checks.push('atomic selection clears stale facet across reruns');
  await page.goto('http://127.0.0.1:'+port+'?review_job=renderer-context-browser');
  await page.locator('.source .char').first().waitFor();await settled();
  await clickFacet('term:sifen:38:19-21','source_supply');
  await page.getByText('Inspect · §15 · 章法',{exact:true}).click();
  await page.getByRole('button',{name:'Add as context & re-run',exact:true}).click();
  await page.getByRole('heading',{name:'Last change',exact:true}).waitFor();await settled();
  checks.push((await runPython(
    "import sys; from workbench import service; r=service.compile_review_job(sys.argv[1],'renderer-context-browser'); assert r['job']['revision']==2; assert [d['action'] for d in r['session']['decisions']]==['attach_context']; assert any(d['doc_id']=='sifen:15' for d in r['effective_packet']['context_documents']); print('Inspect attachment saved only attach_context; backend recompiled without a bind_value decision')",root)).trim());
  await snapshot('12-context-attached');
  assert.deepEqual(pageErrors,[]);
  await fs.writeFile(path.join(output,'acceptance.json'),JSON.stringify({status:'passed',checks,root},null,2));
  console.log(JSON.stringify({status:'passed',checks,output}));
}catch(error){
  if(page)await snapshot('failure').catch(()=>{});
  await fs.writeFile(path.join(output,'server.log'),serverLog);
  throw error;
}finally{
  await browser?.close();
  if(child&&child.exitCode===null)child.kill();
}
