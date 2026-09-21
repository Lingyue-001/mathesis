// Actual Streamlit controls, isolated source and job stores; no human decisions.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import net from 'node:net';
import {spawn} from 'node:child_process';
import {once} from 'node:events';
import {fileURLToPath} from 'node:url';
import {chromium} from 'playwright';

const repo = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const python = path.join(repo, 'tools/parser_inspector/.venv/Scripts/python.exe');
const directory = await fs.mkdtemp(path.join(os.tmpdir(), 'mathesis-k2a-browser-'));
const root = path.join(directory, 'source');
const evidence = path.join(repo, 'tmp/k2a-review-tests');
await fs.mkdir(root); await fs.mkdir(evidence, {recursive:true});
const checks = [], errors = [];
let child, serverLog = '';
const browser = await chromium.launch({headless:true});

async function until(fn, description, timeout=30000) {
  const deadline = Date.now()+timeout;
  while(Date.now()<deadline) {
    if(await fn()) return;
    await new Promise(resolve=>setTimeout(resolve,100));
  }
  throw Error(`Timeout: ${description}\n${serverLog}`);
}
async function settled(page) {
  await until(async()=>await page.locator('[data-testid="stApp"]').getAttribute('data-test-script-state')==='notRunning', 'render settled');
  assert.equal(await page.locator('[data-testid="stException"]').count(),0);
}
async function choose(page,key,text,exact=true) {
  await settled(page);
  const box=page.locator(`.st-key-${key}`).getByRole('combobox');
  await box.click(); await box.fill(text);
  await page.getByRole('option',{name:text,exact}).first().click();
  await settled(page);
}
async function fill(page,key,text) {
  await page.locator(`.st-key-${key}`).locator('input,textarea').fill(text);
  await page.locator(`.st-key-${key}`).locator('input,textarea').blur();
  await settled(page);
}
async function click(page,key) {
  await page.locator(`.st-key-${key} button`).click();
  await settled(page);
}
async function revealEvidence(page) {
  const label=page.getByText('查看原文依据 / 高级定位',{exact:true});
  if(await label.count()) {await label.click();await settled(page);}
}
async function job() {return JSON.parse(await fs.readFile(path.join(root,'.local/review-jobs/browser-job.json'),'utf8'));}
async function revision(value) {await until(async()=>{try{return (await job()).revision===value;}catch{return false;}},`revision ${value}`);}
async function start() {
  const server=net.createServer(); server.listen(0,'127.0.0.1'); await once(server,'listening');
  const port=server.address().port; await new Promise(resolve=>server.close(resolve));
  child=spawn(python,['-X','utf8','-B','-m','streamlit','run',path.join(directory,'host.py'),
    '--server.address','127.0.0.1','--server.port',String(port),'--server.headless','true',
    '--server.fileWatcherType','none','--browser.gatherUsageStats','false'],
    {cwd:repo,windowsHide:true,env:{...process.env,PYTHONUTF8:'1',PYTHONDONTWRITEBYTECODE:'1'}});
  child.stdout.on('data',d=>serverLog+=d); child.stderr.on('data',d=>serverLog+=d);
  const url=`http://127.0.0.1:${port}`;
  await until(async()=>{try{return (await fetch(url+'/_stcore/health')).ok;}catch{return false;}},'server');
  return url;
}
async function stop() {
  if(child && child.exitCode===null) {const exit=once(child,'exit');child.kill();await exit;}
  child=null;
}
try {
  const setup=spawn(python,['-X','utf8','-B','-c','from pathlib import Path; import sys; from tests.workbench.test_review_jobs import isolated_source; isolated_source(Path(sys.argv[1]))',root],{cwd:repo,windowsHide:true});
  let setupLog='';setup.stderr.on('data',d=>setupLog+=d);
  assert.equal((await once(setup,'exit'))[0],0,setupLog);
  await fs.writeFile(path.join(directory,'host.py'),`import sys\nsys.path.insert(0, ${JSON.stringify(repo.replaceAll('\\','/'))})\nimport streamlit as st\nfrom tools.parser_inspector.readable import render\nst.set_page_config(layout='wide')\nrender(${JSON.stringify(root.replaceAll('\\','/'))}, 'zh')\n`,'utf8');
  let url=await start();
  const page=await browser.newPage({viewport:{width:1450,height:1100}});
  page.on('pageerror',e=>errors.push(String(e)));
  await page.goto(url); await page.locator('.st-key-k2_new_id input').waitFor();await settled(page);
  await fill(page,'k2_new_id','browser-job'); await click(page,'k2_create'); await revision(1);
  const identity=(await job()).session.session_id;
  await page.locator('.st-key-k2_actor_id input').waitFor();
  await choose(page,'k2_question','当前计算缺少所需背景材料或已登记配置。',false);
  await fill(page,'k2_actor_id','browser-fixture');await choose(page,'k2_actor_type','scripted_fixture');
  await choose(page,'k2_action','attach_context');await choose(page,'k2_context_unit','sifen:section:38');
  await fill(page,'k2_reason','合成开发验收：附加真实来源背景');await click(page,'k2_save');await revision(2);
  checks.push('create and attach_context persisted through actual controls');
  await revealEvidence(page);
  await choose(page,'k2_document','sifen:38');
  await until(async()=>/Context.*sifen:38/.test(await page.locator('.k2-evidence').innerText()),'Context viewer rerender');
  await page.locator('.k2-evidence mark').waitFor();
  const context=await page.locator('.k2-evidence').innerText();
  assert.match(context,/Context.*sifen:38/);assert.match(context,/sifen:38\.[a-f0-9]+/);
  assert.ok(await page.locator('.k2-evidence mark').innerText());
  await page.locator('.k2-evidence').screenshot({path:path.join(evidence,'context-evidence.png')});
  await choose(page,'k2_action','defer');await fill(page,'k2_reason','合成开发验收：Context 上暂留未决');
  await click(page,'k2_save');await revision(3);
  let current=await job();assert.equal(current.session.decisions[1].targets[0].doc_id,'sifen:38');
  assert.deepEqual(current.session.decisions[1].depends_on,[current.session.decisions[0].decision_id]);
  checks.push('Context reading/span highlighted and dependent decision saved');
  await page.getByText('已保存的判断 / 撤销',{exact:true}).click();
  await fill(page,'k2_retract_reason','合成开发验收：撤销暂留判断');await click(page,'k2_retract');await revision(4);
  await page.reload();await page.locator('.st-key-k2_actor_id input').waitFor();await settled(page);
  assert.equal((await job()).session.session_id,identity);
  assert.match(await page.locator('[data-testid="stCaptionContainer"]').allTextContents().then(x=>x.join(' ')),/revision 4/);
  await revealEvidence(page);await choose(page,'k2_document','sifen:39');
  await until(async()=>/Primary.*sifen:39/.test(await page.locator('.k2-evidence').innerText()),'Primary viewer rerender');
  assert.match(await page.locator('.k2-evidence').innerText(),/Primary.*sifen:39/);
  const frame=page.frames().find(f=>f!==page.mainFrame());
  assert.ok(frame);await frame.locator('#term-semantics').waitFor();assert.equal(await frame.locator('#R4').count(),1);
  checks.push('retract, refresh, same session, Primary evidence and K1.5/R4 preserved');
  await page.evaluate(()=>window.scrollTo(0,0));
  await page.screenshot({path:path.join(evidence,'inspector.png')});
  await stop();url=await start();await page.goto(url+'/?review_job=browser-job');
  await page.locator('.st-key-k2_actor_id input').waitFor();await settled(page);
  assert.equal((await job()).session.session_id,identity);
  assert.match(await page.locator('[data-testid="stCaptionContainer"]').allTextContents().then(x=>x.join(' ')),/revision 4/);
  checks.push('full Streamlit process restart reopens same ReviewJob/session/revision');
  assert.deepEqual(errors,[]);
  await fs.writeFile(path.join(evidence,'result.json'),JSON.stringify({checks,errors,job_id:'browser-job',revision:4,isolated:true},null,2)+'\n','utf8');
  console.log(JSON.stringify({checks,errors,evidence},null,2));
} finally {await stop();await browser.close();}
