// Real source-first ReviewJob controls, isolated source/job stores.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import net from 'node:net';
import {spawn} from 'node:child_process';
import {once} from 'node:events';
import {fileURLToPath} from 'node:url';
import {chromium} from 'playwright';

const repo=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const python=path.join(repo,'tools/parser_inspector/.venv/Scripts/python.exe');
const scratch=await fs.mkdtemp(path.join(os.tmpdir(),'mathesis-k2bc-browser-'));
const root=path.join(scratch,'source');
const evidence=path.join(repo,'tmp/k2bc-review-tests');
await fs.mkdir(root);await fs.mkdir(evidence,{recursive:true});
let child, serverLog='';
const browser=await chromium.launch({headless:true});
const errors=[];

async function until(fn,description,timeout=30000) {
  const deadline=Date.now()+timeout;
  while(Date.now()<deadline) {
    if(await fn())return;
    await new Promise(resolve=>setTimeout(resolve,100));
  }
  throw Error(`Timeout: ${description}\n${serverLog}`);
}
async function settled(page) {
  await until(async()=>await page.locator('[data-testid="stApp"]').getAttribute('data-test-script-state')==='notRunning','render settled');
  assert.equal(await page.locator('[data-testid="stException"]').count(),0);
}
async function click(page,key) {
  await page.locator(`.st-key-${key} button`).click();await page.waitForTimeout(200);await settled(page);
}
async function fill(page,key,value) {
  const input=page.locator(`.st-key-${key}`).locator('input,textarea');
  await input.fill(value);await input.blur();await settled(page);
}
async function revision(value,job='browser-job') {
  await until(async()=>{
    try {const record=JSON.parse(await fs.readFile(path.join(root,'.local/review-jobs',job+'.json'),'utf8'));
      return record.revision===value;} catch {return false;}
  },`revision ${value}`);
}
async function start() {
  const server=net.createServer();server.listen(0,'127.0.0.1');await once(server,'listening');
  const port=server.address().port;await new Promise(resolve=>server.close(resolve));
  child=spawn(python,['-X','utf8','-B','-m','streamlit','run',path.join(scratch,'host.py'),
    '--server.address','127.0.0.1','--server.port',String(port),'--server.headless','true',
    '--server.fileWatcherType','none','--browser.gatherUsageStats','false'],
    {cwd:repo,windowsHide:true,env:{...process.env,PYTHONUTF8:'1',PYTHONDONTWRITEBYTECODE:'1'}});
  child.stdout.on('data',d=>serverLog+=d);child.stderr.on('data',d=>serverLog+=d);
  const url=`http://127.0.0.1:${port}`;
  await until(async()=>{try{return (await fetch(url+'/_stcore/health')).ok;}catch{return false;}},'server');
  return url;
}
async function stop() {
  if(child&&child.exitCode===null){const exit=once(child,'exit');child.kill();await exit;}
  child=null;
}

try {
  const setup=spawn(python,['-X','utf8','-B','-c',
    `from pathlib import Path
import sys
from tests.workbench.test_review_jobs import isolated_source
from tests.workbench.test_review_effects import SYNTHETIC, selection
from source_adapters import corpus_review
from workbench import service, review_jobs
root=Path(sys.argv[1]); isolated_source(root)
source=root/'calendars-四分历.md'
samples={**SYNTHETIC,903:'置甲量'}
source.write_text(source.read_text(encoding='utf-8')+'\\n\\n'+'\\n\\n'.join(f'{n}\\t{text}' for n,text in samples.items())+'\\n',encoding='utf-8')
corpus_review.regenerate(root)
for name,section in [('B1',900),('C1',38),('C7',903)]:
 service.create_review_job(root,name,selection(section))
service.create_review_job(root,'C5',selection(39,[14,15,16,19,38]))
baseline=service.create_review_job(root,'C2',selection(901))
source_question=next(q for q in baseline['questions'] if any(o['action']=='declare_parameter' for o in q['options']))
source_option=next(o for o in source_question['options'] if o['action']=='declare_parameter')
root_decision=service.review_decision(baseline,source_option['action'],source_question['anchor'],source_option['payload'],{'type':'scripted_fixture','id':'browser'},'Scripted neutral probe root')
baseline=service.apply_review_job_changes(root,'C2',decisions=[root_decision],expected_revision=1,expected_digest=baseline['job_digest'])
counting=next(q for q in baseline['questions'] if q['kind']=='counting_convention')
construction=counting['anchor']; formal=counting['evidence']['construction']['slots']['value']['text']
address={'definition_anchor':construction,'construction_anchor':construction,'construction_role':'load','semantic_role':'load','input_slot':'value','formal':formal,'branch_id':'main','invocation_path':[construction]}
facets={'coordinate_kind':'ordinal','index_base':1,'reference_origin':'current_bu_start','counting_boundary':'start_of_current_month','step_unit':'month'}
semantic_target=service.normalize_decision_target('set_quantity_semantics',{'semantic_input':address},[construction])
decision=service.review_decision(baseline,'set_quantity_semantics',construction,{'contract_version':'2.0','semantic_input':address,'facets':facets},{'type':'scripted_fixture','id':'browser'},'Scripted neutral month coordinate')
events=[{'event_id':'C2-manage-'+facet,'action':'manage','target':construction,'facet':facet,'branch_id':'main','actor':{'type':'scripted_fixture','id':'browser'},'created_at':service._now(),'reason':'Scripted neutral probe ownership','semantic_target':semantic_target} for facet in facets]
service.apply_review_job_changes(root,'C2',decisions=[decision],management_events=events,expected_revision=baseline['job']['revision'],expected_digest=baseline['job_digest'])
old=service.create_review_job(root,'C8',selection(903))['job']
old['session']['identity_locks']['engine']['sha256']='pre-BC-runtime-identity'
review_jobs.write_job_atomic(root,old)
`,root],
    {cwd:repo,windowsHide:true});
  let setupLog='';setup.stderr.on('data',d=>setupLog+=d);
  assert.equal((await once(setup,'exit'))[0],0,setupLog);
  await fs.writeFile(path.join(scratch,'host.py'),
    `import sys\nsys.path.insert(0, ${JSON.stringify(repo.replaceAll('\\','/'))})\nimport streamlit as st\nfrom tools.parser_inspector.readable import render\nst.set_page_config(layout='wide')\nrender(${JSON.stringify(root.replaceAll('\\','/'))}, 'en')\n`,'utf8');
  const url=await start();
  const page=await browser.newPage({viewport:{width:1450,height:1050}});
  page.on('pageerror',error=>errors.push(String(error)));
  await page.goto(url);await page.locator('.st-key-k2_new_id input').waitFor();await settled(page);
  await fill(page,'k2_new_id','browser-job');await click(page,'k2_create');await revision(1);
  await page.getByText('Current question',{exact:true}).waitFor();
  assert.equal(await page.locator('.st-key-k2_action').count(),0);
  await click(page,'k2_next');
  await page.getByText(/How should .*入蔀積月.* be interpreted here/).first().waitFor();
  const option=page.getByText('Accumulated months within the 蔀 cycle',{exact:true}).first();
  await option.click();await settled(page);
  await page.screenshot({path:path.join(evidence,'term-question.png')});
  await click(page,'k2_save');await revision(2);
  assert.equal(await page.locator('[data-testid="stException"]').count(),0);
  const history=page.locator('[data-testid="stExpander"] summary').filter({hasText:'Decision history and retract'}).first();
  await until(async()=>{
    if(!await history.locator('xpath=..').evaluate(node=>node.open))await history.click();
    return await page.locator('.st-key-k2_retract_reason input').isVisible();
  },'history expanded');
  await fill(page,'k2_retract_reason','Reopen this interpretation');
  await click(page,'k2_retract');await revision(3);
  await page.screenshot({path:path.join(evidence,'term-retracted.png')});
  await click(page,'k2_next');
  await page.getByText(/How should .*入蔀積月.* be interpreted here/).first().waitFor();
  async function openJob(job) {
    const p=await browser.newPage({viewport:{width:1450,height:1050}});
    p.on('pageerror',error=>errors.push(String(error)));
    await p.goto(url+'?review_job='+job);
    await p.getByText('Current question',{exact:true}).waitFor();await settled(p);return p;
  }
  async function expand(p,label) {
    const summary=p.locator('[data-testid="stExpander"] summary').filter({hasText:label}).first();
    if(!await summary.locator('xpath=..').evaluate(node=>node.open))await summary.click();
    await p.waitForTimeout(200);
  }
  async function retract(p,job,rev,label='Term interpretation') {
    await expand(p,'Decision history and retract');
    await p.locator('.st-key-k2_retract_target').getByRole('combobox').click();
    await p.getByRole('option').filter({hasText:label}).first().click();await p.waitForTimeout(200);await settled(p);
    await fill(p,'k2_retract_reason','Reopen this scholarly judgment');
    await click(p,'k2_retract');await revision(rev,job);
  }
  async function focusTitle(p,pattern) {
    let forward=true;
    for(let i=0;i<50;i++){
      await p.waitForTimeout(300);await settled(p);
      if(pattern.test(await p.locator('body').innerText()))return;
      if(await p.locator('.st-key-'+(forward?'k2_next':'k2_previous')+' button').isDisabled())forward=!forward;
      await click(p,forward?'k2_next':'k2_previous');
    }
    throw Error('Question not reached: '+pattern);
  }
  const b=await openJob('B1');
  await b.screenshot({path:path.join(evidence,'B1-before.png')});
  await b.getByText('Adjust term span',{exact:true}).click();await settled(b);
  for(const [start,end] of [[1,2],[4,5]]) {
    const expected='Selected span: '+(start===1?'日率':'月率');
    for(let attempt=0;attempt<3;attempt++) {
      await b.waitForTimeout(350);
      const a=await b.getByRole('button',{name:new RegExp('^Source character '+(start+1)+':')}).boundingBox();
      const z=await b.getByRole('button',{name:new RegExp('^Source character '+(end+1)+':')}).boundingBox();
      assert.ok(a&&z,'source character buttons rendered');
      await b.mouse.move(a.x+a.width/2,a.y+a.height/2);await b.mouse.down();
      await b.mouse.move(z.x+z.width/2,z.y+z.height/2,{steps:5});await b.mouse.up();
      await b.waitForTimeout(250);await settled(b);
      if(await b.getByText(expected,{exact:true}).isVisible())break;
    }
    await b.getByText(expected,{exact:true}).waitFor();await click(b,'k2_queue_boundary');
  }
  await b.getByText('Terms to confirm: 日率, 月率',{exact:true}).waitFor();
  await click(b,'k2_save_boundaries');await revision(2,'B1');
  await b.screenshot({path:path.join(evidence,'B1-reviewed-multiply.png')});

  const c1=await openJob('C1');
  await focusTitle(c1,/How is .*入蔀年.* counted here/);
  await c1.getByText('One-based ordinal year count within the current 蔀',{exact:true}).click();await settled(c1);
  await c1.screenshot({path:path.join(evidence,'C1-year-decision.png')});
  await click(c1,'k2_save');await revision(2,'C1');
  await expand(c1,'What changed');await c1.screenshot({path:path.join(evidence,'C1-reviewed-years.png')});

  const c2=await openJob('C2');
  await c2.getByText('No current scholar question. Review history and execution remain available.',{exact:true}).waitFor();
  await expand(c2,'Run current reviewed model');
  await c2.getByRole('textbox',{name:'Value for 甲量',exact:true}).fill('5');
  await c2.getByRole('textbox',{name:'Value for 甲量',exact:true}).blur();await settled(c2);
  await click(c2,'k2_run');await c2.getByText('Status: executed',{exact:true}).waitFor();
  await c2.getByText('Graph: partial',{exact:true}).waitFor();
  await c2.getByText('Numerical check: executed for current closed region',{exact:true}).waitFor();
  await c2.getByText('elapsed month',{exact:true}).scrollIntoViewIfNeeded();
  await c2.screenshot({path:path.join(evidence,'C2-execution-months.png')});
  await retract(c2,'C2',4,'Quantity interpretation');
  await expand(c2,'Run current reviewed model');await c2.getByText('STALE — re-run required',{exact:true}).waitFor();
  await click(c2,'k2_run');await c2.getByText('Status: unresolved',{exact:true}).waitFor();
  await c2.screenshot({path:path.join(evidence,'C2-retracted-managed-blocked.png')});
  await expand(c2,'Management');
  const action=c2.locator('.st-key-k2_management_action').getByRole('combobox');
  await action.click();await c2.getByRole('option',{name:'unmanage',exact:true}).click();await settled(c2);
  await c2.getByRole('button',{name:'Release this interpretation takeover',exact:true}).waitFor();
  await click(c2,'k2_manage');await revision(5,'C2');
  await expand(c2,'Run current reviewed model');await click(c2,'k2_run');
  await c2.getByText('Status: executed',{exact:true}).waitFor();
  await c2.screenshot({path:path.join(evidence,'C2-unmanage-legacy-restored.png')});

  const c5=await openJob('C5');
  await focusTitle(c5,/Use the attested Han Si-fen month-to-day relation/);
  await c5.getByText('Use this evidenced month-to-day relation',{exact:true}).click();await settled(c5);
  await click(c5,'k2_save');await revision(2,'C5');
  await c5.getByText('C5 · revision 2',{exact:true}).waitFor();await c5.waitForTimeout(350);await settled(c5);
  await expand(c5,'Run current reviewed model');
  const labels=await c5.getByRole('textbox',{name:/^Value for /}).evaluateAll(fields=>fields.map(f=>f.getAttribute('aria-label')));
  for(const label of labels){
    await expand(c5,'Run current reviewed model');
    const field=c5.getByRole('textbox',{name:label,exact:true});
    await field.fill(label.includes('入蔀年')?'2':'0');await field.blur();await settled(c5);
  }
  await expand(c5,'Run current reviewed model');
  await click(c5,'k2_run');await c5.getByText('348/940',{exact:true}).first().waitFor();
  await c5.getByText('348/940',{exact:true}).first().scrollIntoViewIfNeeded();
  await c5.screenshot({path:path.join(evidence,'C5-fractional-day-execution.png')});

  const c7=await openJob('C7');
  await c7.getByText('Supply “甲量” as an external input',{exact:true}).click();await settled(c7);
  await click(c7,'k2_save');await revision(2,'C7');
  await c7.getByText('No current scholar question. Review history and execution remain available.',{exact:true}).waitFor();
  await expand(c7,'Decision history and retract');await expand(c7,'Run current reviewed model');
  await c7.getByRole('textbox',{name:'Value for 甲量',exact:true}).fill('5');
  await c7.getByRole('textbox',{name:'Value for 甲量',exact:true}).blur();await settled(c7);
  await click(c7,'k2_run');await c7.getByText('Status: executed',{exact:true}).waitFor();
  assert.ok(await c7.locator('[data-testid="stExpander"] summary').filter({hasText:'Inspection / Evidence'}).count());
  await c7.screenshot({path:path.join(evidence,'C7-last-question-execution.png'),fullPage:true});
  await c7.getByText('No current scholar question. Review history and execution remain available.',{exact:true}).scrollIntoViewIfNeeded();
  await c7.screenshot({path:path.join(evidence,'C7-no-question-controls.png')});
  await retract(c7,'C7',3,'External input');await c7.getByText(/Which source supplies .*甲量/).waitFor();
  await expand(c7,'Run current reviewed model');await c7.getByText('STALE — re-run required',{exact:true}).waitFor();
  await c7.screenshot({path:path.join(evidence,'C7-restored-question-stale.png'),fullPage:true});
  const c8=await browser.newPage({viewport:{width:1450,height:1050}});
  await c8.goto(url+'?review_job=C8');
  await c8.getByText(/This job is read-only under the current analysis/).waitFor();
  assert.equal(await c8.locator('.st-key-k2_run').count(),0);
  await c8.screenshot({path:path.join(evidence,'C8-stale-job.png')});
  await click(c8,'k2_create_fresh');await revision(1,'C8-current');
  await c8.getByText('Current question',{exact:true}).waitFor();
  const proof=spawn(python,['-X','utf8','-B','-c',`import sys,json
from pathlib import Path
from workbench import service
from tests.workbench.test_review_effects import snapshot
root=Path(sys.argv[1]); evidence={}
for name in ('B1','C1','C2','C5','C7','C8-current'):
 r=service.compile_review_job(root,name);evidence[name]=snapshot(r)
 if name=='B1': assert any(c['kind']=='multiply' and c['slots']['left']['text']=='日率' and c['slots']['right']['text']=='月率' for c in r['graph']['construction_candidates'])
 if name=='C1': assert any(v.get('coordinate_kind')=='elapsed' and v['unit']=='year' and v.get('adjudication_decision_refs') for v in r['graph']['value_instances'])
 if name=='C2': assert not any(m['managed'] for m in r['managed_scope'])
 if name=='C5':
  run=service.execute_review_job(root,name,{'入蔀年':2},expected_revision=r['job']['revision'],expected_digest=r['job_digest'])
  assert any(v['value']==348 and v['representation'].get('denominator_value')==940 for v in run['output_quantities'].values())
  evidence[name]['execution']=run
 if name=='C7': assert len(r['questions'])==1
Path(sys.argv[2]).write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8')
`,root,path.join(evidence,'browser-effects.json')],{cwd:repo,windowsHide:true});
  let proofLog='';proof.stderr.on('data',d=>proofLog+=d);
  assert.equal((await once(proof,'exit'))[0],0,proofLog);
  assert.deepEqual(errors,[]);
  await fs.writeFile(path.join(evidence,'result.json'),JSON.stringify({
    checks:['English source-first question','real term adoption','saved history and retract','question restored',
      'B1 exact character drag and boundary grammar rebuild','C1 reviewed ordinal year','C2 reviewed ordinal month execution',
      'C2 graph status is separate from current closed-region numerical check',
      'C2 retract retains ownership and blocks execution','C2 one-click explicit unmanage restores legacy ownership',
      'C5 real quotient and fractional-day denominator','C7 last question controls','C8 read-only and fresh same selection','C9 stale execution'],
    errors,job_id:'browser-job',revision:3,isolated:true},null,2)+'\n','utf8');
  console.log(JSON.stringify({checks:14,errors,evidence}));
} catch(error) {
  for(const [i,p] of browser.contexts().flatMap(c=>c.pages()).entries()) {
    await p.screenshot({path:path.join(evidence,'failure-'+i+'.png'),fullPage:true}).catch(()=>{});
    await fs.writeFile(path.join(evidence,'failure-'+i+'.txt'),await p.locator('body').innerText(),'utf8').catch(()=>{});
  }
  throw error;
} finally {await stop();await browser.close();}
