// Production artifact acceptance. No Python or application API is served here.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import http from 'node:http';
import {once} from 'node:events';
import {chromium} from 'playwright';

const root=path.resolve('dist'), output=path.resolve('tmp/static-scholar-sandbox');
await fs.mkdir(output,{recursive:true});
const types={'.html':'text/html','.css':'text/css','.mjs':'text/javascript','.js':'text/javascript','.json':'application/json','.svg':'image/svg+xml','.png':'image/png','.woff2':'font/woff2'};
const server=http.createServer(async(req,res)=>{
  try{
    const url=new URL(req.url,'http://localhost');
    if(!url.pathname.startsWith('/mathesis/')){res.writeHead(404);res.end();return;}
    let filename=path.resolve(root,decodeURIComponent(url.pathname.slice('/mathesis/'.length)));
    if(filename!==root&&!filename.startsWith(root+path.sep))throw Error('Outside static root');
    if((await fs.stat(filename)).isDirectory())filename=path.join(filename,'index.html');
    res.setHeader('Content-Type',types[path.extname(filename)]||'application/octet-stream');res.end(await fs.readFile(filename));
  }catch{res.writeHead(404);res.end('Not found');}
});
server.listen(0,'127.0.0.1');await once(server,'listening');
const origin='http://127.0.0.1:'+server.address().port;
const browser=await chromium.launch({headless:true});
const page=await browser.newPage({viewport:{width:1440,height:1000}});
const errors=[],failed=[],api=[],checks=[];
page.on('pageerror',e=>errors.push(String(e)));
page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
page.on('request',r=>{if(new URL(r.url()).pathname.includes('/api/'))api.push(r.url());});
page.on('requestfailed',r=>failed.push(r.url()));
page.on('response',r=>{if(r.status()>=400)failed.push(r.url()+': '+r.status());});
const snapshot=JSON.parse(await fs.readFile('static/data/inspector/sifen-38.snapshot.json','utf8').catch(()=>'{}'));
const render=async()=>{await page.locator('.source .char').first().waitFor();await page.waitForTimeout(100);};
const noOverflow=async()=>assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),false);
try{
  const response=await page.goto(origin+'/mathesis/inspector/');
  assert.equal(response.status(),200,'production /mathesis/inspector/ route exists');
  await render();
  assert.equal(await page.locator('.glyphs:not(.probe)').allTextContents().then(rows=>rows.join('')),snapshot.source.text);
  assert.equal(await page.getByRole('heading',{level:1}).innerText(),'Parser Stages');
  assert.equal(await page.locator('#parser-source option:checked').innerText(),'Sifen li · 四分曆');
  const sourceLabels=['Santong li · 三統曆','Sifen li · 四分曆','Jiuzhi li · 九執曆'];
  for(const id of ['segmentation-source','corpus-source'])assert.deepEqual(await page.locator('#'+id+' option').allTextContents(),sourceLabels);
  checks.push('production route and shared Annotated Source loaded from committed snapshot');
  const facet=snapshot.renderer.facets.find(f=>f.facet==='term_meaning'&&snapshot.questions.find(q=>q.id===f.question_id));
  await page.locator('.source .char[data-object-id="'+facet.object_id+'"]').first().click();
  for(const reviewedFacet of snapshot.details.objects[facet.object_id].facets.filter(f=>f.question_id)){
    await page.locator('#selection-detail .research-record').filter({hasText:reviewedFacet.label+' · '+reviewedFacet.status}).getByRole('button',{name:'Review',exact:true}).click();
    const title=snapshot.questions.find(q=>q.id===reviewedFacet.question_id).title;
    assert.ok((await page.locator('#question-detail').innerText()).includes(title),'Review opens its precise question');
    assert.equal(await page.evaluate(()=>document.activeElement.id),'current-question-heading');
    const questionHeading=await page.locator('#current-question-heading').boundingBox();
    assert.ok(questionHeading.y>=0&&questionHeading.y<500,'Review brings the question into view');
    assert.ok(questionHeading.y<(await page.getByRole('heading',{name:'Selected source object',exact:true}).boundingBox()).y);
  }
  checks.push('Current question precedes Selected; every Review action selects and focuses its exact question');
  await page.locator('.source .facet[data-facet-key="'+facet.facet_key+'"]').first().click();
  const question=snapshot.questions.find(q=>q.id===facet.question_id);
  const option=question.options.find(o=>o.action!=='defer'&&o.mode!=='compose');
  await page.getByRole('radio',{name:option.label,exact:true}).check();
  await page.getByLabel('Draft note', {exact:true}).fill('Static acceptance draft');
  await page.getByRole('button',{name:'Save as draft',exact:true}).click();
  await page.getByText('Draft review · not recompiled',{exact:true}).waitFor();
  assert.ok((await page.locator('.source .facet[data-facet-key="'+facet.facet_key+'"]').first().innerText()).endsWith(' · draft'));
  assert.ok((await page.locator('#question-draft-summary').innerText()).includes(option.label));
  await page.reload();await render();
  await page.locator('.source .facet[data-facet-key="'+facet.facet_key+'"]').first().click();
  assert.equal(await page.getByRole('radio',{name:option.label,exact:true}).isChecked(),true);
  assert.ok((await page.locator('.source .facet[data-facet-key="'+facet.facet_key+'"]').first().innerText()).endsWith(' · draft'));
  checks.push('existing question option saved as a local draft and survives reload');
  const stored=()=>page.evaluate(()=>JSON.parse(localStorage.getItem(Object.keys(localStorage).find(k=>k.startsWith('scholar-sandbox-drafts:')))));
  const alternate=question.options.find(o=>o.id!==option.id&&o.mode!=='compose');
  await page.getByRole('radio',{name:alternate.label,exact:true}).check();
  await page.getByText('Local draft decisions',{exact:true}).click();
  await page.getByRole('button',{name:'Edit draft',exact:true}).click();
  assert.equal(await page.getByRole('radio',{name:option.label,exact:true}).isChecked(),true,'editing restores saved option, not an unsaved choice');
  await page.getByLabel('Draft note',{exact:true}).fill('Edited static draft');
  await page.getByRole('button',{name:'Save as draft',exact:true}).click();
  assert.equal((await stored()).decisions.length,1);
  assert.equal((await stored()).decisions[0].reason,'Edited static draft');
  // Every exported facet presents exactly the current research-mode choices.
  for(const current of snapshot.renderer.facets.filter(f=>f.question_id)){
    const q=snapshot.questions.find(q=>q.id===current.question_id);if(!q)continue;
    await page.locator('.source .facet[data-facet-key="'+current.facet_key+'"]').first().click();
    assert.deepEqual(await page.getByRole('radio').evaluateAll(ns=>ns.map(n=>n.value)),q.options.map(o=>o.id));
  }
  const contextQuestion=snapshot.questions.find(q=>q.options.some(o=>o.action==='attach_context'));
  const contextFacet=snapshot.renderer.facets.find(f=>f.question_id===contextQuestion.id);
  const contextOption=contextQuestion.options.find(o=>o.action==='attach_context');
  await page.locator('.source .facet[data-facet-key="'+contextFacet.facet_key+'"]').first().click();
  await page.getByRole('radio',{name:contextOption.label,exact:true}).check();
  const contextId=snapshot.context_catalog.at(-1).id;
  await page.getByLabel('Additional context',{exact:true}).selectOption(contextId);
  await page.getByLabel('Draft note',{exact:true}).fill('Context draft only');
  await page.locator('#option-fields').getByRole('button',{name:'Add context as draft',exact:true}).click();
  assert.equal((await stored()).decisions.find(d=>d.kind==='context').context_id,contextId);
  assert.ok((await page.locator('.source .facet[data-facet-key="'+contextFacet.facet_key+'"]').first().innerText()).endsWith(' · draft'));
  const contextRow=page.locator('#local-drafts .research-record').filter({hasText:'Context draft only'});
  await contextRow.getByRole('button',{name:'Edit draft',exact:true}).click();
  assert.equal(await page.getByLabel('Additional context',{exact:true}).inputValue(),contextId);
  await contextRow.getByRole('button',{name:'Retract draft',exact:true}).click();
  assert.equal((await stored()).decisions.some(d=>d.kind==='context'),false);
  const originalContextBadge=[...snapshot.renderer.terms,...snapshot.renderer.constructions].flatMap(row=>row.badges||[]).find(f=>f.facet_key===contextFacet.facet_key);
  assert.equal(await page.locator('.source .facet[data-facet-key="'+contextFacet.facet_key+'"]').first().innerText(),originalContextBadge.label);
  checks.push('saved question drafts are visible on original source badges and in the question panel, survive reload and disappear on retraction');
  checks.push('all meaning/source/count/context options match snapshot; drafts edit in place and context drafts retract');
  await page.locator('.source .facet[data-facet-key="'+facet.facet_key+'"]').first().click();
  await page.getByRole('radio',{name:'Compose a local interpretation from registered concepts',exact:true}).check();
  await page.getByLabel('Composition meaning',{exact:true}).selectOption('constructor:accumulation');
  await page.getByLabel('Composition meaning.quantity',{exact:true}).selectOption('constructor:accumulation');
  const leaf=await page.getByLabel('Composition meaning.quantity.quantity',{exact:true}).inputValue();
  await page.getByRole('button',{name:'Save as draft',exact:true}).click();
  const expression=(await stored()).decisions.find(d=>d.question_id===question.id).inputs.expression;
  assert.equal(expression.op,'accumulation');assert.equal(expression.arguments.quantity.op,'accumulation');
  assert.equal(expression.arguments.quantity.arguments.quantity.concept_id,leaf.slice('concept:'.length));
  await page.reload();await render();
  await page.locator('.source .facet[data-facet-key="'+facet.facet_key+'"]').first().click();
  assert.equal(await page.getByLabel('Composition meaning.quantity',{exact:true}).inputValue(),'constructor:accumulation');
  await page.getByRole('radio',{name:option.label,exact:true}).check();
  await page.getByRole('button',{name:'Save as draft',exact:true}).click();
  checks.push('registered nested composition choices reuse exported research controls and survive reload as drafts');
  await page.getByRole('button',{name:'Procedure Model',exact:true}).click();
  await page.locator('.procedure-node').first().waitFor();
  assert.equal(await page.locator('.procedure-node').count(),snapshot.procedure_model.nodes.length);
  const node=snapshot.procedure_model.nodes.find(n=>n.operation==='divmod');
  await page.locator('.procedure-node[data-node-id="'+node.id+'"]').click();
  await page.getByRole('button',{name:'Annotated Source',exact:true}).click();
  await page.locator('.source .focus[data-object-id="'+node.selection_object_id+'"]').first().waitFor();
  assert.ok(await page.locator('.source .focus[data-object-id="'+node.selection_object_id+'"]').count());
  await page.locator('.source .char[data-object-id="'+facet.object_id+'"]').first().click();
  await page.getByRole('button',{name:'Procedure Model',exact:true}).click();
  assert.ok(await page.locator('.procedure-node.active[data-object-id="'+facet.object_id+'"]').count());
  checks.push('Procedure Model and bidirectional source/graph selection preserve object identities');
  await page.getByRole('button',{name:'Annotated Source',exact:true}).click();
  await page.getByLabel('Adjust term boundary',{exact:true}).check();
  const a=page.locator('.source .char[data-offset="6"]'),b=page.locator('.source .char[data-offset="8"]');
  await a.scrollIntoViewIfNeeded();const ab=await a.boundingBox(),bb=await b.boundingBox();
  await page.mouse.move(ab.x+ab.width/2,ab.y+ab.height/2);await page.mouse.down();
  await page.mouse.move(bb.x+bb.width/2,bb.y+bb.height/2,{steps:8});await page.mouse.up();
  await page.getByRole('button',{name:'Save boundary as draft',exact:true}).click();
  await page.getByLabel('Adjust term boundary',{exact:true}).uncheck();
  await page.getByText('Snapshot & drafts',{exact:true}).click();
  const downloadEvent=page.waitForEvent('download');await page.getByRole('button',{name:'Export drafts',exact:true}).click();
  const download=await downloadEvent, exportPath=path.join(output,'drafts.json');await download.saveAs(exportPath);
  const drafts=JSON.parse(await fs.readFile(exportPath,'utf8'));
  const boundary=drafts.decisions.find(d=>d.kind==='term_boundary');
  assert.equal(boundary.anchor.start,6);assert.equal(boundary.anchor.end,9);assert.equal(boundary.anchor.quote,'入蔀年');
  assert.equal(boundary.anchor.source_sha256,snapshot.source.text_sha256);
  const before=JSON.stringify(drafts);
  await page.getByLabel('Import draft JSON',{exact:true}).setInputFiles(exportPath);
  await page.getByText('Drafts imported.',{exact:true}).waitFor();
  const secondDownload=page.waitForEvent('download');await page.getByRole('button',{name:'Export drafts',exact:true}).click();
  const second=await secondDownload;await second.saveAs(path.join(output,'drafts-roundtrip.json'));
  assert.deepEqual(JSON.parse(await fs.readFile(path.join(output,'drafts-roundtrip.json'),'utf8')),JSON.parse(before));
  checks.push('real Unicode pointer span is exact [6,9) 入蔀年; draft JSON import/export round-trips');
  await page.getByLabel('Import draft JSON',{exact:true}).setInputFiles({name:'wrong-snapshot.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify({...drafts,snapshot_id:'different-snapshot'}))});
  await page.getByRole('alert').filter({hasText:'Draft import rejected'}).waitFor();
  assert.deepEqual(await stored(),drafts,'failed import preserves saved drafts');
  const badSpan=structuredClone(drafts);badSpan.decisions.find(d=>d.kind==='term_boundary').anchor.end+=1;
  await page.getByLabel('Import draft JSON',{exact:true}).setInputFiles({name:'bad-unicode-span.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(badSpan))});
  await page.getByRole('alert').filter({hasText:'quote does not exactly match'}).waitFor();
  assert.deepEqual(await stored(),drafts,'bad Unicode range import preserves saved drafts');
  // The downloadable snapshot is still exactly the original, without draft overlays.
  const snapshotDownload=page.waitForEvent('download');await page.getByRole('button',{name:'Export snapshot',exact:true}).click();
  const exportedSnapshot=await snapshotDownload;await exportedSnapshot.saveAs(path.join(output,'snapshot-roundtrip.json'));
  assert.deepEqual(JSON.parse(await fs.readFile(path.join(output,'snapshot-roundtrip.json'),'utf8')),snapshot);
  await page.reload();await render();
  await page.locator('.source .facet[data-facet-key="'+facet.facet_key+'"]').first().click();
  checks.push('invalid import preserves drafts; local decisions never alter exported analysis');
  for(const width of [1440,768,390]){
    await page.setViewportSize({width,height:1000});await page.waitForTimeout(250);
    if(width<=800&&await page.getByRole('button',{name:'Collapse workspace navigation'}).isVisible())await page.getByRole('button',{name:'Collapse workspace navigation'}).click();
    await page.evaluate(()=>scrollTo(0,0));await noOverflow();
    for(const id of ['parser-source','parser-section']){
      const select=page.locator('#'+id),closed=await select.boundingBox();
      await select.click();
      const samples=await select.evaluate(async el=>{
        const values=[];
        for(let i=0;i<12;i++){
          await new Promise(requestAnimationFrame);
          const box=el.querySelector('option:checked').getBoundingClientRect();
          values.push({left:box.left,width:box.width});
        }
        return values;
      });
      for(const sample of samples){
        assert.ok(Math.abs(sample.left-closed.x)<8,'picker stays aligned with its field');
        assert.ok(Math.abs(sample.width-closed.width)<12,'selected background spans the full field width');
        assert.ok(Math.abs(sample.width-samples[0].width)<1,'picker highlight does not jump during opening');
      }
      await page.screenshot({path:path.join(output,id+'-open-'+width+'.png')});
      await page.keyboard.press('Escape');
      await select.click();await page.keyboard.press('Enter');
      assert.equal(await select.evaluate(el=>el.matches(':open')),false);
    }
    await page.mouse.move(0,0);await page.evaluate(()=>scrollTo(0,0));
    await page.screenshot({path:path.join(output,'parser-stages-'+width+'.png'),fullPage:true});
    await page.screenshot({path:path.join(output,'parser-viewport-'+width+'.png')});
    const clipped=await page.locator('.source .char,.source .facet,.source .rail,.source .step-token').evaluateAll(ns=>ns.filter(n=>{const r=n.getBoundingClientRect();return r.width&&(r.left<0||r.right>innerWidth+1);}).map(n=>n.textContent));
    assert.deepEqual(clipped,[]);
    await page.locator('#source-host').evaluate(el=>scrollTo(0,el.getBoundingClientRect().top+scrollY-90));
    await page.mouse.move(0,0);
    await page.screenshot({path:path.join(output,'source-viewport-'+width+'.png')});
    const details=await page.getByRole('complementary',{name:'Selected object and question'}).boundingBox();
    const source=await page.getByRole('region',{name:'Source and procedure'}).boundingBox();
    if(width<=800)assert.ok(details.y>=source.y+source.height-1,'mobile selection/questions stack beneath source');
    await page.getByLabel('Draft note',{exact:true}).fill('Responsive '+width);
    await page.getByRole('button',{name:'Save as draft',exact:true}).click();
    assert.equal(await page.getByText('Saved as local draft.',{exact:true}).count(),1);
    await noOverflow();
    const controlsClipped=await page.locator('#question-detail button,#question-detail input,#question-detail textarea').evaluateAll(ns=>ns.filter(n=>{const r=n.getBoundingClientRect();return r.width&&(r.left<0||r.right>innerWidth+1);}).map(n=>n.outerHTML));
    assert.deepEqual(controlsClipped,[]);
    await page.getByRole('heading',{name:'Current question',exact:true}).evaluate(el=>scrollTo(0,el.getBoundingClientRect().top+scrollY-90));
    await page.screenshot({path:path.join(output,'question-viewport-'+width+'.png')});
    await page.getByRole('button',{name:'Procedure Model',exact:true}).click();await noOverflow();
    await page.screenshot({path:path.join(output,'procedure-model-'+width+'.png'),fullPage:true});
    await page.getByRole('button',{name:'Annotated Source',exact:true}).click();
    for(const workspace of ['Segmentation Review','Corpus Browser','Parser Stages']){
      const open=page.getByRole('button',{name:'Expand workspace navigation'});if(await open.isVisible())await open.click();
      await page.getByRole('navigation',{name:'Workspace'}).getByRole('button',{name:workspace,exact:true}).click();
      assert.equal(await page.getByRole('heading',{level:1}).innerText(),workspace);await noOverflow();
      if(workspace==='Corpus Browser'){
        await page.locator('#corpus-source').click();await page.keyboard.press('Home');await page.keyboard.press('Enter');
        assert.equal(await page.locator('#corpus-source').inputValue(),'santong');
        await page.locator('#corpus-source').selectOption('sifen');
      }
      if(workspace!=='Parser Stages')await page.screenshot({path:path.join(output,workspace.toLowerCase().replaceAll(' ','-')+'-'+width+'.png'),fullPage:true});
    }
  }
  checks.push('all workspaces, source annotations, options/drafts and graph usable at 1440/768/390 px');
  checks.push('shared traditional/pinyin source labels; open picker highlights stay aligned at full width without animation jumps; keyboard selection works');
  assert.deepEqual(api,[]);assert.deepEqual(failed,[]);assert.deepEqual(errors,[]);
  const text=await page.locator('#scholar-sandbox').innerText();assert.doesNotMatch(text,/Confirm and re-run|Execute|Retract and re-run/);
  checks.push('zero API requests, missing assets or console errors; no fake backend controls');
  await fs.writeFile(path.join(output,'acceptance.json'),JSON.stringify({status:'passed',checks,errors,failed,api,snapshot_id:snapshot.snapshot_id},null,2));
  console.log(JSON.stringify({status:'passed',checks,output},null,2));
}catch(error){await page.screenshot({path:path.join(output,'failure.png'),fullPage:true});await fs.writeFile(path.join(output,'failure.txt'),await page.locator('body').ariaSnapshot());throw error;}
finally{await browser.close();await new Promise(resolve=>server.close(resolve));}
