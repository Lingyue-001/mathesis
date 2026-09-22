// Real browser acceptance over current-tree Python + isolated ReviewJob stores.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import net from 'node:net';
import {spawn} from 'node:child_process';
import {once} from 'node:events';
import {fileURLToPath} from 'node:url';
import {chromium} from 'playwright';
import {createHash} from 'node:crypto';

const repo=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const output=path.join(repo,'tmp/scholar-renderer-v02');
const procedureOutput=path.join(repo,'tmp/procedure-model-v1');
const shellOutput=path.join(repo,'tmp/inspector-ui');
const closureOutput=path.join(repo,'tmp/semantic-closure');await fs.mkdir(closureOutput,{recursive:true});
await fs.mkdir(shellOutput,{recursive:true});
await fs.mkdir(output,{recursive:true});
await fs.mkdir(procedureOutput,{recursive:true});
const scratch=await fs.mkdtemp(path.join(output,'run-'));
const root=path.join(scratch,'source'); await fs.mkdir(root);
const python=path.join(repo,'tools/parser_inspector/.venv/Scripts/python.exe');
let child,browser,page,serverLog='';
const checks=[];
const presentationPath=path.join(repo,'.local/review-jobs/scholar-renderer-correction-20260920.json');
const presentationBefore=await fs.readFile(presentationPath);
const sha256=bytes=>createHash('sha256').update(bytes).digest('hex');
async function rendered(predicate=()=>true){
  const job=new URL(page.url()).searchParams.get('review_job');
  let value;
  for(let i=0;i<600;i++){
    try{value=JSON.parse(await fs.readFile(path.join(scratch,job+'.rendered.json'),'utf8'));if(predicate(value))return value;}catch{}
    await page.waitForTimeout(100);
  }
  throw Error('Rendered state did not reach expected condition: '+JSON.stringify({revision:value?.job.revision,selected:value?.selected,facet:value?.facet}));
}
async function persisted(job=new URL(page.url()).searchParams.get('review_job')){
  return JSON.parse(await fs.readFile(path.join(root,'.local/review-jobs',job+'.json'),'utf8'));
}
async function saveRevision(revision){
  const state=await rendered(s=>s.job.revision===revision);
  await settled();
  assert.deepEqual((await persisted()).session.decisions,state.job.session.decisions);
  return state;
}
async function expand(label){
  const summary=page.locator('[data-testid="stExpander"] summary').filter({hasText:label}).first();
  if(!await summary.locator('xpath=..').evaluate(el=>el.open))await summary.click();
  // Expander animation and component-triggered reruns finish independently.
  await page.waitForTimeout(500);await settled();
}
async function runPython(code,...args){
  const process=spawn(python,['-X','utf8','-B','-c',code,...args],{cwd:repo,windowsHide:true});
  let result='';process.stdout.on('data',d=>result+=d);process.stderr.on('data',d=>result+=d);
  assert.equal((await once(process,'exit'))[0],0,result);return result;
}
async function settled(){
  await page.waitForFunction(()=>document.querySelector('[data-testid="stApp"]')?.getAttribute('data-test-script-state')==='notRunning'&&!document.querySelector('[data-stale="true"]'));
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
  await rendered(s=>s.selected===id&&!s.facet);
  await page.locator('.source .focus[data-object-id="'+id+'"]').first().waitFor();await settled();
}
async function clickFacet(id,family){
  await page.locator('.source .facet[data-object-id="'+id+'"][data-facet="'+family+'"]').first().click();
  const state=await rendered(s=>s.selected===id&&s.renderer.facets.some(f=>f.object_id===id&&f.facet===family&&f.facet_key===s.facet));
  await settled();
  const facet=state.renderer.facets.find(f=>f.facet_key===state.facet);
  assert.equal(await page.locator('.source .facet.active').count(),1);
  const question=state.questions.find(q=>q.id===facet.question_id);
  if(question){
    await page.locator('[data-testid="stMarkdownContainer"]').getByText(question.title,{exact:true}).waitFor();
    const sourceQuestion=question.semantic_key?.issue_family==='source_supply';
    const area=sourceQuestion ? 'Source resolution' : 'Interpretation';
    const options=await page.locator('[role="radiogroup"][aria-label="'+area+'"] label').allTextContents();
    let shown=[...new Map(question.options.map(o=>[o.id,o])).values()];
    if(sourceQuestion)shown=shown.filter(o=>(o.group==='runtime_fallback')===(area==='Execution fallback'));
    const expected=shown.map(o=>o.label);
    if(question.kind==='term_interpretation')expected.splice(-1,0,'Compose a local interpretation from registered concepts');
    assert.deepEqual(options,expected,'radio labels and values must belong only to the selected question, without duplicate IDs');
  }
  await settled();
}
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
try{
  await runPython(
    "from pathlib import Path; import sys; from tests.workbench.test_review_jobs import isolated_source, SELECTION; from workbench import service; from source_adapters import corpus_review; r=Path(sys.argv[1]); isolated_source(r); source=r/'calendars-四分历.md'; source.write_text(source.read_text(encoding='utf-8')+'\\n\\n900\\t𠀀。以日新率乘章月。\\n\\n901\\t置章月，名為積月。\\n',encoding='utf-8'); corpus_review.regenerate(r); [service.create_review_job(r,j,{**SELECTION,'primary_unit_ids':['sifen:section:38'],'provided_scope':{}}) for j in ('renderer-browser','renderer-context-browser','closure-browser')]; service.create_review_job(r,'closure-identity-browser',{**SELECTION,'primary_unit_ids':['sifen:section:901'],'provided_scope':{}}); service.create_review_job(r,'renderer-boundary-browser',{**SELECTION,'primary_unit_ids':['sifen:section:900'],'provided_scope':{}})",
    root);
  const host=path.join(scratch,'host.py');
  await fs.writeFile(host,[
    'import sys',
    'sys.path.insert(0, '+JSON.stringify(repo.replaceAll('\\','/'))+')',
    'import streamlit as st',
    'from tools.parser_inspector.review_panel import render',
    'from tools.parser_inspector.shell import render_navigation',
    'from tools.parser_inspector.segmentation_review import render as render_segmentation, render_full_text',
    "st.set_page_config(layout='wide')",
    "workspace = render_navigation()",
    "if workspace != 'Parser stages':",
    "    (render_segmentation if workspace == 'Segmentation Review' else render_full_text)("+JSON.stringify(root.replaceAll('\\','/'))+")",
    '    st.stop()',
    "st.session_state.setdefault('k2_actor_id', 'automated_browser_disposable_regression')",
    "st.session_state.setdefault('k2_reason', 'Automated disposable interaction regression')",
    'response = render('+JSON.stringify(root.replaceAll('\\','/'))+')',
    'import json',
    'from pathlib import Path',
    'from workbench.annotation_projection import stable_golden_view',
    'from workbench.procedure_model import build_procedure_model',
    "projection = st.session_state.get('k2_scholar_projection', {})",
    "state = {'job': response['job'], 'questions': response['questions'], 'replay': response['compilation']['replay'], 'projection': projection, 'stable': stable_golden_view(projection), 'renderer': st.session_state.get('k2_scholar_model'), 'model': build_procedure_model(projection), 'selected': st.session_state.get('k2_scholar_selected'), 'facet': st.session_state.get('k2_scholar_facet'), 'adjust': st.session_state.get('k2_adjust', False)}",
    "destination = Path(__file__).parent / (response['job']['job_id'] + '.rendered.json')",
    "destination.write_text(json.dumps(state, ensure_ascii=False), encoding='utf-8')",
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
  if(process.env.SOURCE_REVIEW_ONLY){
    const before=await persisted();
    await clickFacet('term:sifen:38:6-9','source_supply');
    await page.getByText('No exact parameter declaration found in the indexed corpus.',{exact:true}).first().waitFor();
    assert.equal(await page.getByRole('radiogroup',{name:'Decision area',exact:true}).count(),0);
    assert.equal(await page.locator('[data-testid="stExpander"] summary').filter({hasText:'Full source ·'}).count(),0);
    const sourceChoices=page.getByRole('radiogroup',{name:'Source resolution',exact:true});
    const fallbackChoices=page.getByRole('radiogroup',{name:'Execution fallback',exact:true});
    for(const width of [1440,768,390]){
      await page.setViewportSize({width,height:980});await settled();
      const sidebar=page.getByTestId('stSidebar');
      if(width<1000 && await sidebar.getAttribute('aria-expanded')==='true'){
        await page.getByTestId('stSidebarCollapseButton').click();await page.waitForTimeout(350);
      }
      await page.getByRole('heading',{name:'Current question',exact:true}).evaluate(el=>el.scrollIntoView({block:'start'}));
      await page.getByTestId('stMain').evaluate(el=>el.scrollTop-=65);
      const choiceBox=await sourceChoices.boundingBox();
      assert.ok(choiceBox.y>=0 && choiceBox.y+choiceBox.height<980,JSON.stringify({width,choiceBox}));
      assert.equal(await page.getByTestId('stMain').evaluate(el=>el.scrollWidth>el.clientWidth+1),false);
      await page.screenshot({path:path.join(output,'source-question-'+width+'.png')});
      const occurrence=page.getByRole('button',{name:/^§38 · procedure · 入蔀年/}).first();
      await occurrence.click();
      const inspection=page.getByTestId('stPopoverBody');await inspection.waitFor();
      assert.ok((await inspection.innerText()).includes('推天正術'));
      const inspectionBox=await inspection.boundingBox();assert.ok(inspectionBox.x>=0&&inspectionBox.x+inspectionBox.width<=width+1);
      await page.keyboard.press('Escape');await inspection.waitFor({state:'hidden'});
    }
    await fallbackChoices.locator('label').first().evaluate(el=>el.scrollIntoView({block:'center'}));
    await fallbackChoices.locator('label').first().click();await settled();
    await page.waitForFunction(()=>!document.querySelector('[role="radiogroup"][aria-label="Source resolution"] input:checked'));
    assert.equal(await sourceChoices.locator('input:checked').count(),0);
    assert.equal(await page.getByRole('textbox',{name:'Search source chunks (literal text)',exact:true}).count(),0);
    await sourceChoices.evaluate(el=>el.scrollIntoView({block:'center'}));
    await sourceChoices.getByText('Read additional source material',{exact:true}).click();await settled();
    await page.waitForFunction(()=>!document.querySelector('[role="radiogroup"][aria-label="Execution fallback"] input:checked'));
    assert.equal(await fallbackChoices.locator('input:checked').count(),0);
    await expand('Why these options?');
    await expand('Rule · RUNTIME-INPUT-01');
    const why=page.locator('[data-testid="stExpander"]').filter({has:page.locator('summary').filter({hasText:'Rule · RUNTIME-INPUT-01'})}).last();
    await why.getByText('formal in required_formals = True',{exact:true}).waitFor();
    await why.getByText('View source',{exact:true}).click();
    await why.locator('code').waitFor();
    for(const width of [1440,768,390]){
      await page.setViewportSize({width,height:980});await settled();
      await why.locator('summary').first().evaluate(el=>el.scrollIntoView({block:'start'}));
      await page.locator('[data-testid="stMain"]').evaluate(el=>el.scrollTop-=72);
      assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
      await page.screenshot({path:path.join(output,'source-why-'+width+'.png')});
      await page.getByRole('textbox',{name:'Search source chunks (literal text)',exact:true}).scrollIntoViewIfNeeded();
      await page.screenshot({path:path.join(output,'source-controls-'+width+'.png')});
    }
    await page.getByText('Why these options?',{exact:true}).click();await settled();
    const selections=[
      ['term','term:sifen:38:6-9','.char'],
      ['construction','construction:sifen:38:5-11:load','.rail'],
      ['step','step:sifen:38:5-11:load:0','.step-token'],
      ['flow','flow:sifen:38:入蔀年',null],
    ];
    for(const width of [1440,768,390]){
      await page.setViewportSize({width,height:980});
      for(const [kind,id,selector] of selections){
        if(selector)await page.locator('.source '+selector+'[data-object-id="'+id+'"]').first().click();
        else await page.locator('.st-key-procedure-layer-flows').getByRole('button',{name:'入蔀年',exact:true}).click();
        await rendered(s=>s.selected===id&&!s.facet);await settled();
        const layers=page.locator('[class*="st-key-procedure-layer-"]');
        const layerNames=await layers.evaluateAll(nodes=>nodes.map(n=>Array.from(n.classList).find(c=>c.startsWith('st-key-procedure-layer-'))));
        assert.deepEqual(layerNames,['terms','constructions','steps','flows'].map(x=>'st-key-procedure-layer-'+x));
        const termText=await layers.nth(0).innerText();assert.ok(termText.includes('入蔀年'));
        assert.ok((await layers.nth(1).innerText()).includes('置入蔀年減一'));
        assert.ok((await layers.nth(2).innerText()).includes('Subtract'));
        const current=await rendered();
        assert.ok((await layers.nth(3).innerText()).includes(current.renderer.flows.find(f=>f.formal==='入蔀年').display_status));
        assert.equal(await layers.locator('strong').count(),1,'only selected object is emphasized');
        const totalHeight=await layers.evaluateAll(nodes=>nodes.reduce((sum,n)=>sum+n.getBoundingClientRect().height,0));
        await page.setViewportSize({width,height:Math.ceil(totalHeight+600)});
        await page.getByRole('heading',{name:'Selected source object',exact:true}).evaluate(el=>el.scrollIntoView({block:'start'}));
        await page.getByTestId('stMain').evaluate(el=>el.scrollTop-=65);
        assert.equal(await page.getByTestId('stMain').evaluate(el=>el.scrollWidth>el.clientWidth+1),false);
        const lastBox=await layers.last().boundingBox();assert.ok(lastBox.y+lastBox.height<page.viewportSize().height);
        await page.mouse.move(0,0);
        await page.screenshot({path:path.join(output,'four-layer-'+kind+'-'+width+'.png')});
        await page.setViewportSize({width,height:980});
      }
    }
    await clickFacet('term:sifen:38:13-15','source_supply');
    const exactDeclaration=page.getByRole('radio',{name:'Use exact parameter declaration · §16',exact:true});
    await exactDeclaration.waitFor();
    const declarationChunk=page.getByRole('button',{name:/^§16 · parameter · 章月/}).first();
    assert.equal(await declarationChunk.getAttribute('aria-description'),null,'full declaration is click-only, not duplicated in hover');
    await declarationChunk.click();
    const declarationPopover=page.getByTestId('stPopoverBody');await declarationPopover.waitFor();
    assert.equal(await declarationPopover.getByText('章月，二百三十五。',{exact:true}).count(),1);
    await page.keyboard.press('Escape');await declarationPopover.waitFor({state:'hidden'});
    assert.deepEqual(await persisted(),before,'source evidence, Why and browser selection cannot save decisions');
    checks.push('compact source decisions in first question viewport; exact declaration attaches as selectable context; click-only full chunks; mutually exclusive runtime fallback; four canonical layers for Term/Construction/Step/Flow at 1440/768/390; no writes');
    // Deliberately do not wait between changing the radio and pressing Confirm.
    // A stale render may refuse the click, but must never save the old choice.
    await page.goto('http://127.0.0.1:'+port+'?review_job=renderer-context-browser');
    await page.locator('.source .char').first().waitFor();await settled();
    await clickFacet('term:sifen:38:6-9','source_supply');
    await page.getByRole('radiogroup',{name:'Source resolution',exact:true}).getByText('Read additional source material',{exact:true}).click();
    await page.getByRole('textbox',{name:'Search source chunks (literal text)',exact:true}).waitFor();await settled();
    await page.getByRole('radiogroup',{name:'Execution fallback',exact:true}).locator('label').first().click();
    await page.getByRole('button',{name:'Confirm and re-run',exact:true}).click();
    await page.waitForTimeout(1000);await settled();
    let rapid=await persisted();
    assert.ok(rapid.session.decisions.every(d=>d.action==='declare_parameter'),'rapid confirmation must not submit the previous attach choice');
    if(rapid.revision===1){
      assert.equal(await page.getByRole('radiogroup',{name:'Source resolution',exact:true}).locator('input:checked').count(),0);
      assert.equal(await page.getByRole('button',{name:'Confirm and re-run',exact:true}).isDisabled(),true);
      await page.getByRole('radiogroup',{name:'Execution fallback',exact:true}).locator('label').first().click();
      await page.getByRole('button',{name:'Confirm and re-run',exact:true}).waitFor();await settled();
      await page.getByRole('button',{name:'Confirm and re-run',exact:true}).click();
      await saveRevision(2);rapid=await persisted();
    }
    assert.equal(rapid.session.decisions.length,1);
    assert.equal(rapid.session.decisions[0].action,'declare_parameter');
    assert.equal('document' in rapid.session.decisions[0].payload,false);
    checks.push('un-waited source-to-runtime switch plus Confirm never persists obsolete attach choice');
  }else{
  if(!process.env.CLOSURE_ONLY){
  const scope='Full workflow currently demonstrated on Han Sifen li §38; other procedures are included at their present stage of analysis.';
  const shellChecks=[];
  for(const width of [1440,768,390]){
    await page.setViewportSize({width,height:1000});
    await page.waitForTimeout(500);
    for(const workspace of ['Segmentation Review','Corpus Browser','Parser Stages']){
      const sidebar=page.getByTestId('stSidebar');
      if(await sidebar.getAttribute('aria-expanded')==='false')await page.getByTestId('stExpandSidebarButton').click();
      await page.waitForTimeout(400);
      const navigation=sidebar.getByTestId('stRadioOption').filter({hasText:workspace});
      const navBox=await navigation.boundingBox();
      assert.ok(navBox.width>200,JSON.stringify({message:'navigation uses the sidebar row width',width,workspace,navBox}));
      await navigation.click({position:{x:navBox.width-10,y:navBox.height/2}});
      await page.getByRole('heading',{name:workspace,exact:true}).waitFor();await settled();
      if(width<=768 && await sidebar.getAttribute('aria-expanded')==='true')await page.getByTestId('stSidebarCollapseButton').getByRole('button').click();
      await page.waitForTimeout(400);
      assert.deepEqual(await page.locator('h1').allTextContents(),[workspace]);
      assert.equal(await page.getByText(scope,{exact:true}).count(),1);
      const dimensions=await page.evaluate(()=>{
        const main=document.querySelector('[data-testid="stMain"]');
        return {viewport:innerWidth,document:document.documentElement.scrollWidth,main:main.scrollWidth,mainClient:main.clientWidth};
      });
      assert.ok(dimensions.document<=width+1 && dimensions.main<=dimensions.mainClient+1,JSON.stringify({width,workspace,dimensions}));
      const clipped=await page.locator('h1, [data-testid="stCaptionContainer"], [data-testid="stMain"] [data-baseweb="select"], .source .char, .source .facet, .source .rail, .source .step-token').evaluateAll(nodes=>nodes.filter(n=>{
        const r=n.getBoundingClientRect();return r.width && (r.left < -1 || r.right > innerWidth+1);
      }).map(n=>({text:n.textContent,class:n.className,rect:n.getBoundingClientRect().toJSON()})));
      assert.deepEqual(clipped,[],JSON.stringify({width,workspace,clipped}));
      if(workspace==='Parser Stages'){
        assert.equal(await page.locator('.source-row').evaluateAll(rows=>rows.every(row=>{
          const boxes=Array.from(row.querySelectorAll('.facet'),el=>el.getBoundingClientRect());
          return boxes.every((a,i)=>boxes.slice(i+1).every(b=>a.right<=b.left||b.right<=a.left||a.bottom<=b.top||b.bottom<=a.top));
        })),true,'source badges do not overlap');
        if(width<=800){
          const sourceBox=await page.locator('.source').boundingBox();
          const selectedBox=await page.getByRole('heading',{name:'Selected source object',exact:true}).boundingBox();
          assert.ok(selectedBox.y>=sourceBox.y+sourceBox.height,'Selected / Questions stack below source');
        }
      }
      await page.getByRole('heading',{name:workspace,exact:true}).click();
      await page.getByTestId('stMain').evaluate(el=>el.scrollTop=0);
      await page.screenshot({path:path.join(shellOutput,workspace.toLowerCase().replaceAll(' ','-')+'-'+width+'.png'),fullPage:true});
      shellChecks.push({width,workspace,dimensions});
    }
  }
  await fs.writeFile(path.join(shellOutput,'responsive.json'),JSON.stringify(shellChecks,null,2));
  checks.push('all three workspaces: one title and scope note; usable sidebar navigation and collapse; no page overflow or clipped source annotations at 1440/768/390px');
  await page.setViewportSize({width:1450,height:1050});
  if(await page.getByTestId('stSidebar').getAttribute('aria-expanded')==='true')await page.getByTestId('stSidebarCollapseButton').getByRole('button').click();
  await page.locator('.source .char').first().waitFor();await settled();
  assert.equal(await page.locator('.source .facet.active,.source .focus').count(),0,'initial reading view must not select a question or object');
  assert.ok(await page.locator('.source-row').count()>1);
  assert.equal(await page.locator('.source').evaluate(el=>el.scrollWidth>el.clientWidth+1),false);
  const source=await page.locator('.glyphs:not(.probe)').allTextContents();
  assert.equal(source.join(''),'推天正術，置入蔀年減一，以章月乘之，滿章法得一，名為積月，不滿為閏餘，十二以上，其歲有閏。');
  assert.equal(await page.locator('.glyphs .facet,.glyphs .term-gloss').count(),0);
  const initialState=await rendered();
  for(const [selector,id,label] of [
    ['.char','term:sifen:38:19-21','章法'],
    ['.rail','construction:sifen:38:18-23:divide','滿章法得一'],
    ['.step-token','step:sifen:38:18-23:divmod:0','Divide with remainder'],
  ]){
    await page.locator('.source '+selector+'[data-object-id="'+id+'"]').first().click();
    await rendered(s=>s.selected===id&&!s.facet);
    await page.locator('.source '+selector+'.focus[data-object-id="'+id+'"]').first().waitFor();
    await page.locator('[data-testid="stColumn"]').filter({has:page.getByRole('heading',{name:'Selected source object',exact:true})}).getByText(label,{exact:true}).first().waitFor();
  }
  checks.push('Term, Construction and Step clicks select the correct right-pane object and source focus');
  for(const width of [1440,768,390]){
    await page.setViewportSize({width,height:1000});
    await clickFacet('term:sifen:38:6-9','term_meaning');
    const questionBox=page.locator('[data-testid="stColumn"]').filter({has:page.getByRole('heading',{name:'Current question',exact:true})});
    const overflow=await questionBox.locator('button, [data-testid="stRadioOption"]').evaluateAll(nodes=>nodes.filter(n=>{
      const r=n.getBoundingClientRect();return r.width&&(r.left<0||r.right>innerWidth+1||n.scrollWidth>n.clientWidth+1);
    }).map(n=>n.textContent));
    assert.deepEqual(overflow,[],'question options and buttons fit viewport');
    await page.getByTestId('stMain').evaluate(el=>el.scrollTop=0);
    await page.setViewportSize({width,height:width===390?3000:1800});
    await page.screenshot({path:path.join(shellOutput,'annotated-source-question-'+width+'.png'),fullPage:true});
    await page.getByText('Procedure Model',{exact:true}).click();await page.locator('.procedure-node').first().waitFor();await settled();
    assert.equal(await page.getByTestId('stMain').evaluate(el=>el.scrollWidth>el.clientWidth+1),false,'model does not overflow page');
    await page.getByTestId('stMain').evaluate(el=>el.scrollTop=0);
    await page.screenshot({path:path.join(shellOutput,'procedure-model-'+width+'.png'),fullPage:true});
    await page.getByText('Annotated Source',{exact:true}).click();await page.locator('.source .char').first().waitFor();await settled();
  }
  checks.push('question options/buttons fit all three widths; source badges do not overlap; Selected / Questions stack below source; Procedure Model remains contained');
  await page.setViewportSize({width:1450,height:1050});
  await page.locator('.source .step-token[data-object-id="step:sifen:38:18-23:divmod:0"]').first().click();
  await rendered(s=>s.selected==='step:sifen:38:18-23:divmod:0'&&!s.facet);await settled();
  const exported=path.join(repo,'.cache/procedure-model/proc38.procedure-model.json');
  await runPython("import sys; from workbench import service; from workbench.annotation_projection import project_scholar_source; from workbench.procedure_model import build_procedure_model, export_procedure_model; r=service.compile_review_job(sys.argv[1],'renderer-browser'); p=project_scholar_source(r['effective_packet'],r['compilation'],r['questions'],r['session']['decisions'],r['compilation']['replay']['decision_status']); export_procedure_model(build_procedure_model(p), sys.argv[2])",root,exported);
  const procedure=JSON.parse(await fs.readFile(exported,'utf8'));
  const jobBytesBefore=await runPython("import sys; from pathlib import Path; from workbench.review_jobs import job_path; print(job_path(Path(sys.argv[1]),'renderer-browser').read_text(encoding='utf-8'))",root);
  await page.getByText('Procedure Model',{exact:true}).click();
  await page.locator('.procedure-node').first().waitFor();await settled();
  await page.locator('.procedure-node[data-operation="divmod"].active').waitFor();
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
  await graphDivide.click();await page.locator('.k2-evidence mark').getByText('滿章法得一',{exact:true}).waitFor();await settled();
  assert.ok((await page.locator('.k2-evidence mark').allTextContents()).includes('滿章法得一'));
  await snapshot('02-divmod-source-context',null,procedureOutput);
  await page.getByText('Annotated Source',{exact:true}).click();
  await page.locator('.source .step-token.focus').first().waitFor();await settled();
  assert.equal(await page.locator('.source .step-token.focus[data-object-id="step:sifen:38:18-23:divmod:0"]').count(),3);
  await page.getByText('Procedure Model',{exact:true}).click();
  await page.locator('.procedure-node[data-operation="divmod"].active').waitFor();
  await page.locator('.procedure-node[data-object-id="term:sifen:38:19-21"]').click();
  await page.locator('.k2-evidence mark').getByText('章法',{exact:true}).waitFor();await settled();
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
  const beforeOption=await persisted();
  await page.getByText('Reject these suggestions',{exact:true}).click();
  assert.equal(await page.getByRole('radio',{name:'Reject these suggestions',exact:true}).isChecked(),true);
  await page.getByText('Calculation factor associated with the 章 cycle',{exact:true}).click();
  assert.deepEqual(await persisted(),beforeOption,'draft option changes must not save a decision');
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
  const right=page.locator('[data-testid="stColumn"]').filter({has:page.getByRole('heading',{name:'Selected source object',exact:true})});
  await right.locator('.st-key-procedure-layer-terms').getByText('積月',{exact:true}).first().waitFor();
  assert.deepEqual(await right.locator('[class*="st-key-procedure-layer-"] h4').allTextContents(),
    ['Term','Construction','Computational step','Quantity flow']);
  const visibleText=await right.locator('[data-testid="stMarkdownContainer"]').filter({visible:true}).allTextContents();
  assert.ok(visibleText.join(' ').includes('積'));
  assert.ok(!visibleText.join(' ').includes('Search hints'));
  const localFlows=right.locator('.st-key-procedure-layer-flows');
  assert.ok((await localFlows.innerText()).includes('章法'));
  assert.ok((await localFlows.innerText()).includes('unresolved'));
  assert.ok(!visibleText.join(' ').includes('term:sifen'));
  await snapshot('05-accumulated-months-local');
  for(const id of ['term:sifen:38:26-28','term:sifen:38:32-34']){
    assert.equal(await page.locator('.source .facet[data-object-id="'+id+'"][data-facet="term_meaning"]').count(),1);
    await clickFacet(id,'term_meaning');
    await page.getByRole('heading',{name:'Current question',exact:true}).waitFor();
    assert.equal(await page.getByRole('button',{name:'Confirm and re-run',exact:true}).count(),1);
  }
  const beforeMeaning=await rendered();
  await snapshot('05-named-remainder-meaning');
  await page.getByRole('button',{name:'Confirm and re-run',exact:true}).click();
  await page.getByRole('heading',{name:'Last change',exact:true}).waitFor();await settled();
  const afterMeaning=await saveRevision(2);
  assert.equal(afterMeaning.selected,'term:sifen:38:32-34','confirmation must preserve the selected object');
  assert.equal(afterMeaning.questions.some(q=>q.kind==='term_interpretation'&&q.anchor.start===32),false);
  for(const layer of ['constructions','steps','flows','links'])assert.deepEqual(afterMeaning.stable[layer],beforeMeaning.stable[layer],layer+' changed after local meaning review');
  assert.deepEqual(afterMeaning.stable.terms.filter(t=>t.id!=='term:sifen:38:32-34'),beforeMeaning.stable.terms.filter(t=>t.id!=='term:sifen:38:32-34'));
  assert.equal(await page.locator('.char[data-object-id="term:sifen:38:32-34"][data-interpretation="reviewed"]').count(),2);
  assert.equal(await page.getByRole('button',{name:'Confirm and re-run',exact:true}).count(),0,'resolved question must not remain an active form');
  await expand('Decision history and retract');
  await page.getByRole('textbox',{name:'Reason for retracting',exact:true}).waitFor();
  await snapshot('13-reviewed-history');
  checks.push((await runPython(
    "import sys; from workbench import service; r=service.compile_review_job(sys.argv[1],'renderer-browser'); d=r['session']['decisions'][-1]; assert d['action']=='set_term_interpretation'; assert d['targets'][0]['start']==32 and d['targets'][0]['end']==34; assert r['compilation']['replay']['decision_status'][d['decision_id']]['status']=='active'; assert any(q['kind']=='term_interpretation' and q['anchor']['start']==26 for q in r['questions']); print('named-output interpretation saved through existing action; other named output remains pending')",root)).trim());
  checks.push('both named outputs expose real term_meaning badges and existing interpretation options');
  checks.push('積月 selection is local with component labels and no unrelated source help');
  await clickFacet('term:sifen:38:19-21','source_supply');
  await page.getByText('Canonical producer candidates',{exact:true}).first().waitFor();
  await page.getByText('Read additional source material',{exact:true}).click();
  await page.getByRole('textbox',{name:'Search source chunks (literal text)',exact:true}).fill('章法');
  await page.getByRole('textbox',{name:'Search source chunks (literal text)',exact:true}).blur();
  await settled();
  assert.equal(await page.getByRole('button',{name:'Add as context & re-run',exact:true}).count(),0);
  assert.ok(await page.getByText(/^Exact parameter declarations/).count());
  assert.ok(await page.getByText(/^Other exact occurrences/).count());
  await expand('Why these options?');
  await page.getByText('Rule · PARAMETER-DECLARATION-EXACT-01',{exact:true}).click();
  await snapshot('source-rule-declaration');
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
  await page.getByText('Supply a runtime test value for “章法”',{exact:true}).click();
  await page.waitForFunction(()=>!document.querySelector('[role="radiogroup"][aria-label="Source resolution"] input:checked'));
  await settled();
  await page.getByRole('button',{name:'Confirm and re-run',exact:true}).click();
  await page.locator('.source .facet[data-facet="construction_context_requirement"]').waitFor();await settled();
  const runtime=await saveRevision(4);
  assert.equal(runtime.projection.flows.find(f=>f.formal==='章法').status,'runtime_value_permitted');
  await page.getByText('Procedure Model',{exact:true}).click();
  await page.locator('.procedure-node').first().waitFor();
  const runtimeNode=page.locator('.procedure-node[data-object-id="term:sifen:38:19-21"]');
  await runtimeNode.click();await rendered(s=>s.selected==='term:sifen:38:19-21'&&!s.facet);
  await page.getByText('Runtime value permitted',{exact:false}).first().waitFor();
  assert.equal(runtime.model.status,'incomplete');
  await snapshot('14-runtime-incomplete-model');
  await page.getByText('Annotated Source',{exact:true}).click();await page.locator('.source .char').first().waitFor();
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
  // Reload and retract/reconfirm through real controls; keep all decisions inspectable.
  const beforeReload=await persisted();
  await page.reload();await page.locator('.source .char').first().waitFor();
  const reopened=await rendered(s=>s.job.revision===4);
  assert.deepEqual(await persisted(),beforeReload);
  assert.deepEqual(reopened.stable,runtime.stable);
  assert.deepEqual(reopened.model,runtime.model);
  await clickObject('term:sifen:38:32-34');
  assert.equal(await page.getByRole('button',{name:'Confirm and re-run',exact:true}).count(),0);
  await expand('Decision history and retract');
  await page.locator('.st-key-k2_retract_target').getByRole('combobox').click();
  await page.locator('.st-key-k2_retract_target').getByRole('combobox').fill('閏餘');
  await page.getByRole('option').filter({hasText:'Term interpretation · 閏餘'}).click();
  await page.getByRole('textbox',{name:'Reason for retracting',exact:true}).fill('Automated disposable regression: reopen remainder meaning');
  await page.getByRole('textbox',{name:'Reason for retracting',exact:true}).blur();
  await page.getByRole('button',{name:'Retract and re-run',exact:true}).click();
  const retracted=await saveRevision(5);
  const original=beforeReload.session.decisions.find(d=>d.action==='set_term_interpretation'&&d.targets[0].start===32);
  assert.equal(retracted.replay.decision_status[original.decision_id].status,'retracted');
  await clickFacet('term:sifen:38:32-34','term_meaning');
  await page.getByRole('button',{name:'Confirm and re-run',exact:true}).click();
  const replayed=await saveRevision(6);
  assert.equal(replayed.replay.decision_status[replayed.job.session.decisions.at(-1).decision_id].status,'active');
  assert.equal(await page.locator('.char[data-object-id="term:sifen:38:32-34"][data-interpretation="reviewed"]').count(),2);
  await snapshot('15-retract-reconfirm');
  checks.push('reviewed form closes, selected object stays, unrelated objects unchanged; history, query reload and retract/reconfirm replay preserve decisions and model');
  await page.goto('http://127.0.0.1:'+port+'?review_job=renderer-context-browser');
  await page.locator('.source .char').first().waitFor();await settled();
  await clickFacet('term:sifen:38:19-21','source_supply');
  await page.getByText('Read additional source material',{exact:true}).click();
  await page.getByRole('textbox',{name:'Search source chunks (literal text)',exact:true}).fill('章法，十九');
  await page.getByRole('textbox',{name:'Search source chunks (literal text)',exact:true}).blur();
  await settled();
  await page.locator('.st-key-k2_context_unit').getByRole('combobox').click();
  await page.getByRole('option').filter({hasText:'sifen:section:15'}).click();
  for(const width of [1440,768,390]){
    await page.setViewportSize({width,height:980});await settled();
    assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
    await page.getByRole('heading',{name:'Current question',exact:true}).scrollIntoViewIfNeeded();
    await page.screenshot({path:path.join(output,'source-question-'+width+'.png'),fullPage:true});
  }
  await page.setViewportSize({width:1440,height:980});await settled();
  await page.getByRole('button',{name:'Confirm and re-run',exact:true}).click();
  await page.getByRole('heading',{name:'Last change',exact:true}).waitFor();await settled();
  const attached=await saveRevision(2);
  const linked=attached.projection.flows.find(f=>f.formal==='章法');
  assert.equal(linked.status,'linked_source');
  assert.equal(linked.producer_source.doc_id,'sifen:15');
  for(const layer of ['terms','constructions','steps','links'])assert.deepEqual(attached.stable[layer],initialState.stable[layer]);
  await clickObject('term:sifen:38:19-21');
  await page.locator('.st-key-procedure-layer-flows').getByText('linked historical source',{exact:true}).first().waitFor();
  assert.ok((await page.locator('.st-key-procedure-layer-flows').innerText()).includes('章法'));
  assert.equal(await page.locator('.facet[data-object-id="term:sifen:38:19-21"][data-facet="source_supply"]').count(),1,
    'the accepted context decision remains inspectable after attachment');
  await page.locator('.source .facet[data-object-id="term:sifen:38:19-21"][data-facet="source_context"]').first().click();
  await page.getByText('Recorded context ✓',{exact:true}).waitFor();
  await settled();
  assert.equal(await page.getByRole('button',{name:'Confirm and re-run',exact:true}).count(),0,
    'a recorded context answer is history, not another active submit form');
  await page.getByText('Procedure Model',{exact:true}).click();await page.locator('.procedure-node').first().waitFor();
  assert.equal(await page.locator('.procedure-node.unresolved_input').count(),2);
  await snapshot('16-linked-source-model');
  await page.reload();await page.locator('.source .char').first().waitFor();
  assert.deepEqual((await rendered(s=>s.job.revision===2)).model,attached.model);
  checks.push((await runPython(
    "import sys; from workbench import service; r=service.compile_review_job(sys.argv[1],'renderer-context-browser'); assert r['job']['revision']==2; assert [d['action'] for d in r['session']['decisions']]==['attach_context']; assert any(d['doc_id']=='sifen:15' for d in r['effective_packet']['context_documents']); print('Inspect attachment saved only attach_context; backend recompiled without a bind_value decision')",root)).trim());
  await snapshot('12-context-attached');
  checks.push('context attachment changes only the matching Flow/facet; runtime permission, unresolved source and linked historical source stay distinct across reload');
  await page.goto('http://127.0.0.1:'+port+'?review_job=renderer-boundary-browser');
  await page.locator('.source .char').first().waitFor();await settled();
  const beforeBoundary=await rendered();
  assert.equal(beforeBoundary.projection.source.text,'𠀀。以日新率乘章月。');
  assert.equal(beforeBoundary.projection.steps.length,0);
  assert.equal(beforeBoundary.renderer.terms.some(t=>t.id==='term:sifen:900:3-6'),false);
  await page.locator('.st-key-k2_adjust').click();await rendered(s=>s.adjust);await settled();
  const first=page.locator('.source .char[data-offset="3"]'),last=page.locator('.source .char[data-offset="5"]');
  await first.hover();await last.waitFor({state:'visible'});
  const a=await first.boundingBox(),b=await last.boundingBox();
  await page.mouse.move(a.x+a.width/2,a.y+a.height/2);await page.mouse.down();
  await page.mouse.move(b.x+b.width/2,b.y+b.height/2,{steps:5});await page.mouse.up();
  await page.getByText('Selected span: 日新率',{exact:true}).waitFor();
  await page.getByRole('button',{name:'Queue selected term',exact:true}).click();
  await page.getByText('Terms to confirm: 日新率',{exact:true}).waitFor();
  await snapshot('17-unicode-boundary-queued');
  await page.getByRole('button',{name:'Confirm term spans and re-run',exact:true}).click();
  const boundary=await saveRevision(2);
  const boundaryDecision=boundary.job.session.decisions.at(-1),anchor=boundaryDecision.targets[0];
  assert.equal(boundaryDecision.action,'set_term_boundary');
  assert.deepEqual([anchor.doc_id,anchor.start,anchor.end,anchor.quote,anchor.offset_unit],['sifen:900',3,6,'日新率','unicode_code_point']);
  assert.equal(anchor.source_sha256,sha256(Buffer.from(beforeBoundary.projection.source.text)));
  assert.equal(Array.from(beforeBoundary.projection.source.text).slice(anchor.start,anchor.end).join(''),anchor.quote);
  assert.notEqual(beforeBoundary.projection.source.text.slice(anchor.start,anchor.end),anchor.quote,'fixture distinguishes UTF-16 from code points');
  assert.equal(boundary.replay.decision_status[boundaryDecision.decision_id].status,'active');
  const corrected=boundary.projection.terms.find(t=>t.id==='term:sifen:900:3-6');
  assert.ok(corrected.decision_refs.some(r=>r.decision_id===boundaryDecision.decision_id));
  assert.deepEqual(boundary.stable.terms.filter(t=>t.span[0]>=7),beforeBoundary.stable.terms.filter(t=>t.span[0]>=7),'neighbouring 章月 terms must not change');
  const multiply=boundary.projection.steps.find(s=>s.operation==='multiply');
  assert.ok(multiply,'reviewed span must cause actual reviewed reparse');
  assert.ok(multiply.inputs.some(i=>i.term_id==='term:sifen:900:3-6'));
  await page.locator('.source .step-token[aria-label="multiply"]').waitFor();
  await page.locator('.st-key-k2_adjust').click();await rendered(s=>!s.adjust);await settled();
  await clickObject('term:sifen:900:3-6');
  await page.getByText('日新率',{exact:true}).first().waitFor();
  await snapshot('18-unicode-boundary-reparsed');
  const boundaryBytes=await persisted();
  await page.reload();await page.locator('.source .char').first().waitFor();
  assert.deepEqual((await rendered(s=>s.job.revision===2)).stable,boundary.stable);
  assert.deepEqual(await persisted(),boundaryBytes);
  await page.getByText('Procedure Model',{exact:true}).click();await page.locator('.procedure-node[data-operation="multiply"]').waitFor();
  await snapshot('19-unicode-boundary-model-reloaded');
  checks.push('real pointer span edit after astral Unicode saves exact [3,6) 日新率/hash/code-point offsets; reviewed reparse adds Multiply using that term; neighbouring 章月, reload and model verified');
  checks.push((await runPython(
    "import json, sys; from pathlib import Path; from workbench import service; from workbench.annotation_projection import project_scholar_source, stable_golden_view; from workbench.procedure_model import build_procedure_model; root=Path(sys.argv[1]);\nfor job in ('renderer-browser','renderer-context-browser','renderer-boundary-browser'):\n r=service.compile_review_job(root,job); p=project_scholar_source(r['effective_packet'],r['compilation'],r['questions'],r['session']['decisions'],r['compilation']['replay']['decision_status']); visible=json.loads((root.parent/(job+'.rendered.json')).read_text(encoding='utf-8')); assert stable_golden_view(p)==visible['stable']; assert build_procedure_model(p)==visible['model']; assert r['compilation']['replay']['decision_status']==visible['replay']['decision_status']\nprint('all three persisted jobs independently recompile to exactly the projection/model/replay actually rendered in the browser')",root)).trim());
  }
  // Closure benchmark: real decisions, same normal recompile, disposable jobs.
  await page.goto('http://127.0.0.1:'+port+'?review_job=closure-browser');
  await page.locator('.source .char').first().waitFor();await settled();
  const closureBefore=await rendered();
  await clickFacet('construction:sifen:38:5-11:load','quantity_meaning');
  await page.getByRole('button',{name:'Confirm and re-run',exact:true}).click();
  const counted=await saveRevision(2);
  assert.ok(counted.projection.derived_assertions.some(a=>a.facet==='coordinate_kind'&&a.value==='elapsed'));
  assert.equal(counted.projection.derived_assertions.filter(a=>a.kind==='term').length,0);
  await page.locator('.source .step-token[data-object-id="step:sifen:38:5-11:subtract:0"]').first().click();
  await rendered(s=>s.selected==='step:sifen:38:5-11:subtract:0');await settled();
  await page.getByText('Derived quantity properties',{exact:true}).first().waitFor();
  await snapshot('01-ordinal-elapsed-provenance',null,closureOutput);
  await clickFacet('term:sifen:38:13-15','term_meaning');
  await page.getByRole('button',{name:'Confirm and re-run',exact:true}).click();
  const termReviewed=await saveRevision(3);
  for(const start of [26,32])assert.ok(termReviewed.questions.some(q=>q.kind==='term_interpretation'&&q.anchor.start===start));
  assert.ok(termReviewed.projection.semantic_closure.unresolved.some(d=>d.reason==='missing_registered_arithmetic_semantic_relation'));
  await page.reload();await page.locator('.source .char').first().waitFor();await settled();
  assert.deepEqual((await rendered()).projection.semantic_closure,termReviewed.projection.semantic_closure);
  await runPython("import sys; from workbench.sandbox_snapshot import build_snapshot,export_snapshot; export_snapshot(build_snapshot(sys.argv[1],'closure-browser'),sys.argv[2])",root,path.join(closureOutput,'benchmark.snapshot.json'));
  const closureReport={questions:{before:closureBefore.questions.length,after_count:counted.questions.length,after_term:termReviewed.questions.length},closure:termReviewed.projection.semantic_closure};
  await fs.writeFile(path.join(closureOutput,'benchmark.json'),JSON.stringify(closureReport,null,2));

  // Genuine identity entailment demonstrates a Term question disappearing.
  await page.goto('http://127.0.0.1:'+port+'?review_job=closure-identity-browser');
  await page.locator('.source .char').first().waitFor();await settled();
  const identityBefore=await rendered();
  await clickFacet('term:sifen:901:1-3','term_meaning');
  await page.getByRole('button',{name:'Confirm and re-run',exact:true}).click();
  const identityAfter=await saveRevision(2);
  const inherited='term:sifen:901:6-8';
  assert.equal(identityAfter.renderer.objects[inherited].gloss.kind,'derived');
  assert.equal(identityAfter.questions.some(q=>q.kind==='term_interpretation'&&q.anchor.start===6),false);
  await clickObject(inherited);
  await page.getByText('Derived interpretation',{exact:true}).waitFor();
  await snapshot('02-derived-term-desktop',null,closureOutput);
  const dependency=page.getByRole('button',{name:/Derived: /}).first();
  await dependency.click();await rendered(s=>s.selected!==inherited);await settled();
  await clickObject(inherited);
  for(const width of [1440,768,390]){
    await page.setViewportSize({width,height:1000});await page.waitForTimeout(300);await settled();
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),false);
    await checkTopBadges();
    await page.screenshot({path:path.join(closureOutput,'derived-term-'+width+'.png'),fullPage:true});
  }
  await runPython("import sys; from workbench.sandbox_snapshot import build_snapshot,export_snapshot; export_snapshot(build_snapshot(sys.argv[1],'closure-identity-browser'),sys.argv[2])",root,path.join(closureOutput,'identity.snapshot.json'));
  await runPython("import sys; from workbench import service; from tests.workbench.test_review_jobs import ACTOR; r=service.compile_review_job(sys.argv[1],'closure-identity-browser'); d=r['session']['decisions'][0]; retract=service.review_decision(r,'retract',d['targets'][0],{'decision_id':d['decision_id']},ACTOR,'Disposable closure invalidation'); service.apply_review_job_changes(sys.argv[1],'closure-identity-browser',decisions=[retract],expected_revision=r['job']['revision'],expected_digest=r['job_digest'])",root);
  await page.reload();await page.locator('.source .char').first().waitFor();await settled();
  const invalidated=await rendered(s=>s.job.revision===3);
  assert.equal(invalidated.projection.derived_assertions.length,0);
  assert.equal(invalidated.questions.length,identityBefore.questions.length);
  assert.equal(invalidated.renderer.objects[inherited].gloss.kind,'suggestions');
  await fs.writeFile(path.join(closureOutput,'invalidation.json'),JSON.stringify({before:identityBefore.questions.length,reviewed:identityAfter.questions.length,retracted:invalidated.questions.length,remaining_derived:invalidated.projection.derived_assertions.length},null,2));
  checks.push('semantic closure: reviewed ordinal → derived elapsed; arithmetic lexical gaps remain; exact identity derives a named Term; clickable provenance, 1440/768/390, reload and retract verified; candidate snapshots exported only under tmp');
  }
  const presentationAfter=await fs.readFile(presentationPath);
  assert.deepEqual(presentationAfter,presentationBefore,'presentation ReviewJob must remain byte-identical');
  assert.deepEqual(pageErrors,[]);
  await fs.writeFile(path.join(output,process.env.SOURCE_REVIEW_ONLY?'source-review-acceptance.json':'acceptance.json'),JSON.stringify({status:'passed',checks,root,presentation:{path:presentationPath,before:sha256(presentationBefore),after:sha256(presentationAfter)},jobs:['renderer-browser','renderer-context-browser','renderer-boundary-browser'],pageErrors},null,2));
  console.log(JSON.stringify({status:'passed',checks,output}));
}catch(error){
  if(page)await fs.writeFile(path.join(output,'failure-dom.txt'),await page.locator('body').ariaSnapshot()).catch(()=>{});
  if(page)await snapshot('failure').catch(()=>{});
  await fs.writeFile(path.join(output,'server.log'),serverLog);
  throw error;
}finally{
  await browser?.close();
  if(child&&child.exitCode===null)child.kill();
}
