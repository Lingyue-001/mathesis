// K2 final UI flow: source-first automatic session plus Segmentation handoff.
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
const scratch=await fs.mkdtemp(path.join(os.tmpdir(),'mathesis-k2-ui-slim-'));
const root=path.join(scratch,'source');
let child, log='';

async function until(fn, description, timeout=10000) {
  const deadline=Date.now()+timeout;
  while(Date.now()<deadline) { if(await fn()) return; await new Promise(done=>setTimeout(done,100)); }
  throw Error(`Timeout: ${description}\n${log}`);
}
async function settled(page) {
  await until(()=>page.locator('[data-testid="stApp"]').getAttribute('data-test-script-state').then(x=>x==='notRunning'),'render');
  assert.equal(await page.locator('[data-testid="stException"]').count(),0);
}
async function section(page, label) {
  const box=page.getByRole('combobox',{name:'Section',exact:true});
  await box.click(); await box.fill(label);
  await page.getByRole('option',{name:label,exact:true}).click(); await settled(page);
}
async function effective(page, label) {
  const box=page.getByRole('combobox',{name:'Current effective unit',exact:true});
  await box.click(); await box.fill(label);
  await page.getByRole('option').filter({hasText:new RegExp(`^${label} `)}).first().click(); await settled(page);
}
async function sessionFor(unit) {
  const folder=path.join(root,'.local','review-jobs');
  const selections=[];
  for(const name of await fs.readdir(folder)) if(name.endsWith('.json')) {
    const job=JSON.parse(await fs.readFile(path.join(folder,name),'utf8'));
    selections.push(job.source_selection);
    if(job.source_selection.source_id==='sifen' && job.source_selection.primary_unit_ids.join()===unit) return job.job_id;
  }
  throw Error('automatic session missing for '+unit+': '+JSON.stringify(selections));
}
async function start() {
  const server=net.createServer(); server.listen(0,'127.0.0.1'); await once(server,'listening');
  const port=server.address().port; await new Promise(done=>server.close(done));
  child=spawn(python,['-X','utf8','-B','-m','streamlit','run',path.join(scratch,'host.py'),'--server.address','127.0.0.1','--server.port',String(port),'--server.headless','true','--server.fileWatcherType','none'],{cwd:repo,windowsHide:true});
  child.stdout.on('data',data=>log+=data); child.stderr.on('data',data=>log+=data);
  await until(async()=>{try{return (await fetch(`http://127.0.0.1:${port}/_stcore/health`)).ok;}catch{return false;}},'server');
  return `http://127.0.0.1:${port}`;
}
async function stop(){ if(child&&child.exitCode===null) child.kill(); child=null; }

const browser=await chromium.launch({headless:true});
try {
  await fs.mkdir(root);
  const setup=spawn(python,['-X','utf8','-B','-c','from pathlib import Path; import sys; from tests.workbench.test_review_jobs import isolated_source; isolated_source(Path(sys.argv[1]))',root],{cwd:repo,windowsHide:true});
  assert.equal((await once(setup,'exit'))[0],0);
  await fs.writeFile(path.join(scratch,'host.py'),`import sys\nsys.path.insert(0,${JSON.stringify(repo.replaceAll('\\','/'))})\nimport streamlit as st\nfrom tools.parser_inspector.segmentation_review import render as segmentation\nfrom tools.parser_inspector.readable import render as parser\nst.set_page_config(layout='wide')\npage=st.sidebar.radio('Workspace',['Segmentation Review','Parser stages'],index=1,key='inspector_page')\n(segmentation if page=='Segmentation Review' else parser)(${JSON.stringify(root.replaceAll('\\','/'))}, 'en') if page=='Parser stages' else segmentation(${JSON.stringify(root.replaceAll('\\','/'))})\n`,'utf8');
  const page=await browser.newPage({viewport:{width:1440,height:1000}});
  const url=await start(); await page.goto(url); await page.getByRole('combobox',{name:'Source',exact:true}).waitFor(); await settled(page);
  assert.equal(await page.locator('.st-key-k2_job_picker').count(),0);
  assert.equal(await page.getByText('Create review job',{exact:true}).count(),0);
  await page.getByText('Current question',{exact:true}).waitFor();
  const direct=await sessionFor('sifen:section:1');
  await page.reload(); await settled(page);
  assert.equal(await sessionFor('sifen:section:1'),direct);
  await page.getByRole('radio',{name:'Segmentation Review',exact:true}).click({force:true}); await settled(page);
  await page.locator('.st-key-seg_continue_procedure-sifen button').click(); await settled(page);
  await page.getByText('Current question',{exact:true}).waitFor();
  assert.equal(await sessionFor('sifen:section:1'),direct);
  await page.screenshot({path:path.join(scratch,'k2-ui-slim.png')});
  console.log(JSON.stringify({status:'passed',direct_session:direct,checks:['source-section auto session','session restore','segmentation handoff']}));
} finally {
  await stop(); await browser.close(); await fs.rm(scratch,{recursive:true,force:true});
}
process.exit(0);
