// Reuse the production static-origin harness; only the exported data changes.
import assert from 'node:assert/strict';
import path from 'node:path';

export async function checkCompiledClosure({page,snapshot,output,render,noOverflow}){
  const derived=snapshot.projection.derived_assertions;
  assert.ok(derived.length);
  const term=derived.find(a=>a.kind==='term');
  const fact=term||derived.find(a=>a.facet==='coordinate_kind'&&a.value==='elapsed');
  const target=fact.target.object_id;
  const choose=async()=>{
    const selector=term?'.source .char':'.source .step-token';
    await page.locator(selector+'[data-object-id="'+target+'"]').first().click();
    assert.ok((await page.locator('#selection-detail').innerText()).includes(term?'Derived interpretation':'Derived quantity properties'));
    if(term)assert.equal(await page.locator('#selection-detail').getByText('Derived interpretation',{exact:true}).count(),1);
  };
  await choose();
  const states=()=>page.locator('.source .char[data-interpretation]').evaluateAll(ns=>ns.map(n=>[n.dataset.objectId,n.dataset.interpretation]));
  const before=await states();
  const dependency=page.locator('#selection-detail button').filter({hasText:/Derived:/}).first();
  assert.ok(await dependency.count());await dependency.click();
  await choose();
  for(const width of [1440,768,390]){
    await page.setViewportSize({width,height:1000});await page.waitForTimeout(150);await noOverflow();
    await page.screenshot({path:path.join(output,'source-'+width+'.png'),fullPage:true});
    await page.getByRole('button',{name:'Procedure Model',exact:true}).click();
    assert.equal(await page.locator('.procedure-node').count(),snapshot.procedure_model.nodes.length);
    assert.equal(await page.locator('.procedure-edge').count(),snapshot.procedure_model.edges.length);
    assert.ok((await page.locator('.procedure-node-subtitle').allTextContents()).some(t=>t.includes('derived')));
    await noOverflow();await page.screenshot({path:path.join(output,'graph-'+width+'.png'),fullPage:true});
    await page.getByRole('button',{name:'Annotated Source',exact:true}).click();await choose();
  }
  const facet=snapshot.renderer.facets.find(f=>snapshot.questions.some(q=>q.id===f.question_id&&q.options.some(o=>!['defer','attach_context'].includes(o.action)&&o.mode!=='compose')));
  const question=snapshot.questions.find(q=>q.id===facet.question_id);
  const option=question.options.find(o=>!['defer','attach_context'].includes(o.action)&&o.mode!=='compose');
  await page.locator('.source .facet[data-facet-key="'+facet.facet_key+'"]').first().click();
  await page.getByRole('radio',{name:option.label,exact:true}).check();
  await page.getByRole('button',{name:'Save as draft',exact:true}).click();
  await page.getByText('Draft review · not recompiled',{exact:true}).first().waitFor();
  assert.deepEqual(await states(),before,'draft must not create/remove reviewed or derived semantics');
  await page.reload();await render();
  assert.deepEqual(await states(),before);
  await choose();
  const response=await page.request.get(new URL(await page.locator('#scholar-sandbox').getAttribute('data-snapshot-url'),page.url()).href);
  assert.deepEqual((await response.json()).projection.semantic_closure,snapshot.projection.semantic_closure);
}
