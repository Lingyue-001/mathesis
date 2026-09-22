import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';

async function downloadJSON(page,button) {
  const wait=page.waitForEvent('download');await button.click();
  const file=await wait;return JSON.parse(await fs.readFile(await file.path(),'utf8'));
}

export async function checkPrecompiledScenario({page,scenario,output,render,noOverflow}) {
  assert.equal(scenario.schema,'ScholarSandboxScenario/1');
  const shell=page.locator('#scholar-sandbox');
  const baseline=scenario.states[scenario.initial_state_id];
  // Precompiled transitions remain usable when browser storage is unavailable.
  const quotaPage=await page.context().browser().newPage();
  try {
    await quotaPage.addInitScript(()=>{Storage.prototype.setItem=function(){throw new DOMException('quota full','QuotaExceededError');};});
    await quotaPage.goto(page.url());
    await quotaPage.locator('#scholar-sandbox[data-ready="true"]').waitFor();
    const first=scenario.transitions[0];
    const facet=baseline.renderer.facets.find(f=>f.question_id===first.question_id);
    await quotaPage.locator('.source .facet[data-facet-key="'+facet.facet_key+'"]').first().click();
    const option=baseline.questions.find(q=>q.id===first.question_id).options.find(o=>o.id===first.option_id);
    await quotaPage.getByRole('radio',{name:option.label,exact:true}).check();
    assert.equal(await quotaPage.getByRole('button',{name:'Confirm',exact:true}).count(),1,'storage failures cannot block precompiled Confirm');
    await quotaPage.getByRole('button',{name:'Confirm',exact:true}).click();
    assert.equal(await quotaPage.locator('#scholar-sandbox').getAttribute('data-snapshot-id'),scenario.states[first.to_state_id].snapshot_id);
  } finally {await quotaPage.close();}
  const openQuestion=async(snapshot,id)=>{
    const facet=snapshot.renderer.facets.find(f=>f.question_id===id);
    assert.ok(facet,'recorded facet exists for '+id);
    await page.getByRole('button',{name:'Annotated Source',exact:true}).click();
    await page.locator('.source .facet[data-facet-key="'+facet.facet_key+'"]').first().click();
  };
  const assertSnapshot=async snapshot=>{
    await render();
    assert.equal(await shell.getAttribute('data-snapshot-id'),snapshot.snapshot_id);
    assert.equal((await page.locator('.glyphs:not(.probe)').allTextContents()).join(''),snapshot.source.text);
    await page.locator('#snapshot-tools').evaluate(el=>el.open=true);
    assert.deepEqual(await downloadJSON(page,page.getByRole('button',{name:'Export snapshot',exact:true})),snapshot);
    await page.getByRole('button',{name:'Procedure Model',exact:true}).click();
    assert.equal(await page.locator('.procedure-node').count(),snapshot.procedure_model.nodes.length);
    assert.equal(await page.locator('.procedure-edge').count(),snapshot.procedure_model.edges.length);
    for(const node of snapshot.procedure_model.nodes){
      const rendered=page.locator('.procedure-node[data-node-id="'+node.id+'"]');
      assert.equal(await rendered.locator('.procedure-node-label').textContent(),node.label);
      if(node.semantic_summary)assert.ok((await rendered.getAttribute('aria-description')).includes(node.semantic_summary),
        'visible node evidence follows the compiled semantic summary');
    }
    assert.deepEqual(await downloadJSON(page,page.getByRole('button',{name:'Download Procedure Model JSON',exact:true})),snapshot.procedure_model);
    await page.getByRole('button',{name:'Annotated Source',exact:true}).click();
  };
  await assertSnapshot(baseline);
  const draftQuestion=baseline.questions.find(q=>q.kind==='term_interpretation');
  const draftOption=draftQuestion.options.find(o=>o.mode!=='compose'&&o.action!=='defer');
  await openQuestion(baseline,draftQuestion.id);
  await page.getByRole('radio',{name:draftOption.label,exact:true}).check();
  await page.getByRole('button',{name:'Save as draft',exact:true}).click();
  await page.reload();await render();
  await openQuestion(baseline,draftQuestion.id);
  assert.equal(await page.getByRole('radio',{name:draftOption.label,exact:true}).isChecked(),true);
  await page.getByText('Draft review · not recompiled',{exact:true}).waitFor();
  await assertSnapshot(baseline);
  const titles=['Term','Construction','Computational step','Quantity flow'];
  for(const transition of scenario.transitions) {
    const before=scenario.states[transition.from_state_id],after=scenario.states[transition.to_state_id];
    await openQuestion(before,transition.question_id);
    const q=before.questions.find(q=>q.id===transition.question_id);
    const option=q.options.find(o=>o.id===transition.option_id);
    await page.getByRole('radio',{name:option.label,exact:true}).check();
    await page.getByRole('button',{name:'Confirm',exact:true}).click();
    await page.getByText('Precompiled successor loaded.',{exact:true}).waitFor();
    await assertSnapshot(after);
    await page.reload();await render();
    assert.equal(await shell.getAttribute('data-snapshot-id'),after.snapshot_id,'reload retains this tab’s scenario state');
    await page.locator('#review-history').locator('xpath=..').evaluate(el=>el.open=true);
    assert.ok((await page.locator('#review-history').innerText()).includes(transition.decision.reason));
    // The selected object remains present with the same fixed layer headings.
    const term=after.renderer.terms.find(t=>t.surface==='入蔀年');
    await page.locator('.source .char[data-object-id="'+term.id+'"]').first().click();
    assert.deepEqual(await page.locator('#selection-detail > section > h3').allTextContents(),titles);
  }
  const final=scenario.states[scenario.transitions.at(-1).to_state_id];
  for(const width of [1440,768,390]) {
    await page.setViewportSize({width,height:1000});await noOverflow();
    const term=final.renderer.terms.find(t=>t.surface==='章月');
    await page.locator('.source .char[data-object-id="'+term.id+'"]').first().click();
    assert.deepEqual(await page.locator('#selection-detail > section > h3').allTextContents(),titles);
    await page.mouse.move(0,0);
    await page.locator('#snapshot-tools').evaluate(el=>el.open=false);
    await page.locator('#review-history').locator('xpath=..').evaluate(el=>el.open=false);
    await page.screenshot({path:path.join(output,'scenario-source-'+width+'.png'),fullPage:true});
    await page.evaluate(()=>window.scrollTo(0,0));
    await page.screenshot({path:path.join(output,'scenario-viewport-'+width+'.png')});
    await page.getByRole('button',{name:'Procedure Model',exact:true}).click();
    const node=final.procedure_model.nodes.find(n=>n.selection_object_id&&final.details.objects[n.selection_object_id]);
    await page.locator('.procedure-node[data-object-id="'+node.selection_object_id+'"]').first().click();
    await page.getByRole('button',{name:'Annotated Source',exact:true}).click();
    assert.ok(await page.locator('.source .focus').count(),'graph selection reaches source');
    await page.getByRole('button',{name:'Procedure Model',exact:true}).click();await noOverflow();
    await page.screenshot({path:path.join(output,'scenario-graph-'+width+'.png'),fullPage:true});
    await page.getByRole('button',{name:'Annotated Source',exact:true}).click();
    const pending=final.questions.find(q=>q.semantic_key?.formal==='入蔀年'&&q.semantic_key?.issue_family==='source_supply');
    await openQuestion(final,pending.id);
    assert.equal(await page.locator('#question-detail details[open]').count(),0,'source chunks stay collapsed');
    const options=await page.locator('#question-detail fieldset').boundingBox();
    const heading=await page.locator('#current-question-heading').boundingBox();
    assert.ok(options.y-heading.y<1000,'source choices occur in the first question viewport');
    await page.mouse.move(0,0);
    await page.screenshot({path:path.join(output,'scenario-question-'+width+'.png')});
  }
  await page.getByRole('button',{name:'Reset demonstration',exact:true}).click();
  await assertSnapshot(baseline);
  await page.getByText('Draft review · not recompiled',{exact:true}).waitFor();
  await page.getByLabel('Adjust term boundary',{exact:true}).check();
  await page.getByLabel('Start offset',{exact:true}).fill('5');
  await page.getByLabel('End offset',{exact:true}).fill('8');
  await page.getByRole('button',{name:'Save boundary as draft',exact:true}).click();
  await page.locator('#snapshot-tools').evaluate(el=>el.open=true);
  const exported=await downloadJSON(page,page.getByRole('button',{name:'Export drafts',exact:true}));
  const boundary=exported.decisions.find(d=>d.kind==='term_boundary');
  assert.equal(boundary.anchor.quote,Array.from(baseline.source.text).slice(5,8).join(''));
  assert.deepEqual([boundary.anchor.start,boundary.anchor.end,boundary.anchor.offset_unit],[5,8,'unicode_code_point']);
  await page.getByLabel('Import draft JSON',{exact:true}).setInputFiles({name:'drafts.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(exported))});
  await page.getByText('Drafts imported.',{exact:true}).waitFor();
  assert.deepEqual(await downloadJSON(page,page.getByRole('button',{name:'Export drafts',exact:true})),exported);
  await assertSnapshot(baseline);
}
