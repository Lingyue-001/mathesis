// Real Streamlit controls against isolated copies; never writes human corpus reviews.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import net from 'node:net';
import { spawn } from 'node:child_process';
import { once } from 'node:events';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const repo = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const python = path.join(repo, 'tools/parser_inspector/.venv/Scripts/python.exe');
const directory = await fs.mkdtemp(path.join(os.tmpdir(), 'mathesis-segmentation-browser-'));
const evidence = path.join(repo, 'tmp/segmentation-review-tests');
await fs.mkdir(evidence, { recursive: true });
const errors = [];
const checks = [];
const browser = await chromium.launch({ headless: true });
let child;
let serverLog = '';
async function until(check, description, timeout = 20000) {
  const deadline = Date.now() + timeout;
  while (Date.now() < deadline) {
    if (await check()) return;
    await new Promise(resolve => setTimeout(resolve, 100));
  }
  throw new Error(`Timed out: ${description}\n${serverLog}`);
}
async function command(args) {
  const process = spawn(python, ['-X', 'utf8', '-B', ...args], { cwd: repo, windowsHide: true });
  let log = '';
  process.stdout.on('data', chunk => log += chunk);
  process.stderr.on('data', chunk => log += chunk);
  const [code] = await once(process, 'exit');
  assert.equal(code, 0, log);
}
async function start(root) {
  const listener = net.createServer();
  listener.listen(0, '127.0.0.1');
  await once(listener, 'listening');
  const port = listener.address().port;
  await new Promise(resolve => listener.close(resolve));
  const host = path.join(directory, 'test_host.py');
  await fs.writeFile(host, `import sys\nsys.path.insert(0, ${JSON.stringify(repo.replaceAll('\\', '/'))})\nimport streamlit as st\nfrom tools.parser_inspector.segmentation_review import render, render_full_text\nst.set_page_config(layout='wide')\nview = render_full_text if st.session_state.get('inspector_page') == 'Corpus Full Text' else render\nview(${JSON.stringify(root.replaceAll('\\', '/'))})\n`, 'utf8');
  child = spawn(python, ['-X', 'utf8', '-B', '-m', 'streamlit', 'run', host,
    '--server.address', '127.0.0.1', '--server.port', String(port), '--server.headless', 'true',
    '--server.fileWatcherType', 'none', '--browser.gatherUsageStats', 'false'],
  { cwd: repo, windowsHide: true, env: { ...process.env, PYTHONDONTWRITEBYTECODE: '1', PYTHONUTF8: '1' } });
  child.stdout.on('data', chunk => serverLog += chunk);
  child.stderr.on('data', chunk => serverLog += chunk);
  const url = `http://127.0.0.1:${port}`;
  await until(async () => { try { return (await fetch(url + '/_stcore/health')).ok; } catch { return false; } }, 'Streamlit health');
  return url;
}
async function stop() {
  if (child && child.exitCode === null) {
    const exited = once(child, 'exit');
    child.kill();
    await exited;
  }
  child = null;
}
async function read(root, layer, sourceId = 'sifen') {
  const filename = `corpus-review/${sourceId}/${layer}.json`;
  return JSON.parse(await fs.readFile(path.join(root, filename), 'utf8'));
}
function autoUnit(state, section) { return state.units.find(u => u.sections.length === 1 && u.sections[0] === section); }
async function choose(page, label, option) {
  await settled(page);
  const input = page.getByRole('combobox', { name: label, exact: true });
  await input.click();
  await input.fill(option instanceof RegExp ? option.source.match(/§\d+/)?.[0] || '' : option);
  await page.getByRole('option', { name: option, exact: typeof option === 'string' }).waitFor();
  await page.getByRole('option', { name: option, exact: typeof option === 'string' }).click();
  if (label === 'Source') {
    const id = {'四分历':'sifen', '三统历':'santong', '九执历':'jiuzhi'}[option];
    await page.locator(`.st-key-seg_accept-${id} button`).waitFor();
  }
  await settled(page);
}
async function settled(page) {
  await page.waitForFunction(() => document.querySelector('[data-testid="stApp"]')?.getAttribute('data-test-script-state') === 'notRunning');
}
async function open(page, label) {
  await settled(page);
  await page.getByRole('tab').filter({hasText:label}).click();
}
async function ready(page) {
  await page.getByRole('heading', { name: 'Corpus Segmentation Review' }).waitFor();
  await page.getByRole('tab').filter({ hasText: 'Edit relation' }).waitFor();
  assert.equal(await page.getByTestId('stException').count(), 0);
  await settled(page);
}
async function actor(page) {
  await page.getByRole('textbox', { name: '审阅者', exact: true }).fill('browser-acceptance');
  await page.getByRole('textbox', { name: '审阅者', exact: true }).press('Tab');
  await choose(page, '操作身份', 'automated_browser');
}
async function click(page, label) {
  await settled(page);
  const revision = page.locator('[class*="st-key-seg_revision_"]');
  const previous = await revision.getAttribute('class');
  await page.getByRole('button', { name: label, exact: true }).click();
  await page.waitForFunction(old => {
    const el = document.querySelector('[class*="st-key-seg_revision_"]');
    return el && el.className !== old;
  }, previous);
  await settled(page);
}

try {
  const root = path.join(directory, 'real');
  await fs.mkdir(path.join(root, 'config'), { recursive: true });
  for (const name of ['calendrical-ir-pipeline.json', 'workbench-procedures.json'])
    await fs.copyFile(path.join(repo, 'config', name), path.join(root, 'config', name));
  for (const [id, name] of [['sifen', '四分历'], ['santong', '三统历'], ['jiuzhi', '九执历']]) {
    await fs.copyFile(path.join(repo, `calendars-${name}.md`), path.join(root, `calendars-${name}.md`));
    await command(['scripts/corpus/extract_sifen_units.py', '--root', root, '--source-id', id]);
  }
  const original = await read(root, 'auto');
  const page = await browser.newPage({ viewport: { width: 1440, height: 1100 } });
  page.on('pageerror', e => errors.push(e.message));
  let url = await start(root);
  await page.goto(url);
  await ready(page);
  assert.equal(await page.getByRole('button', { name: '重新载入文件', exact: true }).count(), 0);
  const effectivePanel = page.locator('.st-key-seg_effective_panel');
  assert.equal(await effectivePanel.getByRole('tab').count(), 3, 'all edit controls live in right effective pane');
  await choose(page, 'Source', '四分历');
  await actor(page);
  const typeColors = {};
  for (const section of [38, 40]) {
    const input = page.getByRole('combobox', {name:'Current effective unit',exact:true});
    await input.click();
    await input.fill(`§${section}`);
    const option = page.getByRole('option').filter({hasText:new RegExp(`^§${section} ·`)});
    await option.waitFor();
    const badge = await option.evaluate(el => {
      const style = getComputedStyle(el, '::after');
      return {text:style.content, background:style.backgroundColor};
    });
    const type = autoUnit(original,section).type;
    assert.equal(badge.text, `"${type}"`, 'filtered options keep the correct type badge');
    typeColors[type] = badge.background;
    await input.press('Escape');
  }
  assert.notEqual(typeColors.procedure, typeColors.alternative_procedure);
  checks.push('Searchable native dropdown shows correctly anchored type badges, with distinct variant shades');
  // Use the real machine proposal at §40; do not invent corpus relations.
  await choose(page, 'Current effective unit', /^§40 ·/);
  assert.equal((await page.getByRole('combobox', {name:'Current effective unit',exact:true}).inputValue()).includes('未审'), false,
    'default unreviewed selection has no status tag');
  assert.equal((await page.getByRole('combobox', {name:'Current effective unit',exact:true}).inputValue()).includes('一术，'), false,
    'selector preview omits the first punctuation');
  for (const panel of [page.locator('.st-key-seg_auto_panel'), effectivePanel]) {
    await panel.getByText(autoUnit(original,40).text_original, {exact:true}).first().waitFor();
    await panel.getByText(autoUnit(original,39).text_original, {exact:true}).first().waitFor();
  }
  checks.push('Auto and Effective show the complete source and alternative target, not selector previews');
  await open(page, 'Edit relation');
  await page.getByRole('combobox', {name:'关系 1 类型',exact:true}).waitFor();
  assert.equal(await page.getByRole('textbox', {name:'新增关系名称',exact:true}).count(), 0);
  await choose(page, '关系 1 类型', 'alternative_of');
  await click(page, '保存关系');
  await until(async () => autoUnit(await read(root, 'effective'),40).relations[0].kind === 'alternative_of', 'candidate confirmed');
  await until(async () => (await page.getByRole('combobox', {name:'Current effective unit',exact:true}).inputValue()).includes('已审·已修改'), 'modified status shown in selector');
  await page.locator('.st-key-seg_auto_panel').getByText(autoUnit(original,40).text_original, {exact:true}).waitFor();
  assert.equal(autoUnit(await read(root, 'auto'),40).relations[0].kind, 'alternative_of_candidate');
  const target38 = autoUnit(original,38);
  const firstClause = target38.text_original.match(/^[^，。；：！？、,.!?;:\r\n]*/)[0];
  await choose(page, '关系 1 对应文本块', `§38 · ${firstClause} · ${target38.source_spans[0].start}`);
  await click(page, '保存关系');
  await until(async () => autoUnit(await read(root, 'effective'),40).relations[0].target_id === 'sifen:section:38', 'target changed');
  await click(page, '删除关系');
  await until(async () => autoUnit(await read(root, 'effective'),40).relations.length === 0, 'relation deleted');
  await click(page, 'Undo · 撤销上次操作');
  await click(page, 'Undo · 撤销上次操作');
  await click(page, 'Undo · 撤销上次操作');
  await choose(page, 'Current effective unit', /^§40 ·/);
  await open(page, 'Change type');
  await choose(page, '分块类型', 'procedure');
  await click(page, '保存类型');
  await until(async () => autoUnit(await read(root, 'effective'),40).type === 'procedure', 'independent type persists');
  assert.deepEqual(autoUnit(await read(root, 'effective'),40).relations, [], 'retyping clears incompatible alternative relation');
  await open(page, 'Edit relation');
  assert.equal(await page.getByRole('combobox', {name:'关系 1 类型',exact:true}).count(), 0, 'independent procedure cannot add alternative relation');
  await click(page, 'Undo · 撤销上次操作');
  await until(async () => autoUnit(await read(root, 'effective'),40).type === 'alternative_procedure', 'undo restores original candidate');
  await choose(page, 'Current effective unit', /^§49,50 ·/);
  const beforeBoundaryMerge = await read(root, 'effective');
  await click(page, 'Merge ↑');
  const boundaryMerge = (await read(root, 'effective')).units.find(u => u.sections.includes(48) && u.sections.includes(49));
  assert.equal(boundaryMerge.type, 'procedure', 'merge-up keeps active procedure type');
  assert.deepEqual(boundaryMerge.relations, [], 'merge-up cannot import neighbor alternative relation');
  await click(page, 'Undo · 撤销上次操作');
  assert.deepEqual((await read(root, 'effective')).units, beforeBoundaryMerge.units);
  checks.push('Merge-up of §49–50 with §48 changes boundaries only; no alternative type or relation is imported');
  const earlierRevisions = (await read(root, 'overrides')).history.length;
  assert.equal(earlierRevisions, 10);
  checks.push('Real §40 candidate can be confirmed, retargeted, deleted and undone through fixed relation choices');
  await choose(page, 'Current effective unit', /^§38 ·/);
  await until(async () => (await page.locator('.st-key-seg_auto_panel').innerText()).includes(autoUnit(original,38).text_original), 'section 38 loaded');
  await page.getByRole('button', {name:'下一块 →',exact:true}).click();
  await until(async () => (await page.locator('.st-key-seg_auto_panel').innerText()).includes(autoUnit(original,39).text_original), 'Next unit');
  await page.getByRole('button', {name:'← 上一块',exact:true}).click();
  await until(async () => (await page.locator('.st-key-seg_auto_panel').innerText()).includes(autoUnit(original,38).text_original), 'Previous unit');
  await page.getByText(autoUnit(original, 38).text_original, { exact: true }).first().waitFor();
  await click(page, 'Accept · 原样接受');
  await until(async () => autoUnit(await read(root, 'auto'), 38).human_review.at(-1)?.status === 'accepted', 'Accept persists');
  await until(async () => (await page.getByRole('combobox', {name:'Current effective unit',exact:true}).inputValue()).includes('已审·原样接受'), 'accepted status shown in selector');
  await page.locator('.st-key-seg_auto_panel').getByText(autoUnit(original,38).text_original, {exact:true}).waitFor();
  // Explicitly rerender after status changes: selection must not reset to the first item.
  await open(page, 'Edit relation');
  await page.locator('.st-key-seg_auto_panel').getByText(autoUnit(original,38).text_original, {exact:true}).waitFor();
  checks.push('Accept and relation save update review labels while retaining the current unit');
  assert.deepEqual(autoUnit(await read(root, 'auto'), 38).human_review.at(-1).actor,
    {type: 'automated_browser', id: 'browser-acceptance'});
  assert.deepEqual((await read(root, 'overrides')).operations, []);
  checks.push('Accept persists with no override operation');
  await open(page, 'Change type');
  await page.getByText('分块类型说明 · 含义与边界', {exact:true}).click();
  await page.getByText(/computational_exposition — 计算性说明/).waitFor();
  for (const [type, color] of Object.entries(typeColors)) {
    const badge = page.locator('span').filter({hasText:new RegExp(`^${type}$`)});
    assert.equal(await badge.evaluate(el => getComputedStyle(el).backgroundColor), color, 'legend and dropdown share type colors');
  }
  await choose(page, '分块类型', 'discourse');
  await page.getByText(/有未保存的修改/).waitFor();
  await until(async () => await page.getByRole('button', {name:'下一块 →',exact:true}).isDisabled(), 'type draft blocks next');
  await until(async () => await page.getByRole('combobox', {name:'Current effective unit',exact:true}).isDisabled(), 'unsaved changes block unit selector');
  await until(async () => await page.getByRole('combobox', {name:'Source',exact:true}).isDisabled(), 'unsaved changes block source selector');
  assert.equal(await page.getByRole('button', {name:'Full text',exact:true}).isDisabled(), true, 'unsaved changes also block full text navigation');
  await click(page, '保存类型');
  await until(async () => autoUnit(await read(root, 'effective'), 38).type === 'discourse', 'type persists');
  await until(async () => !(await page.getByRole('button', {name:'下一块 →',exact:true}).isDisabled()), 'navigation restored after save');
  const revisedIndex = (await read(root, 'effective')).units.findIndex(unit => unit.sections.length === 1 && unit.sections[0] === 38);
  const typeRules = (await page.locator('style').allTextContents()).join('\n');
  assert.match(typeRules, new RegExp(`\\[data-key="${revisedIndex}"\\][\\s\\S]*?content:"discourse"`),
    'current-unit dropdown reflects the reviewed type, not the AUTO type');
  assert.equal(await effectivePanel.locator('mark').count(), 0, 'type-only edit does not highlight source text');
  assert.equal(autoUnit(await read(root, 'auto'), 38).type, 'procedure');
  checks.push('Retype changes effective only, machine type retained');
  await click(page, 'Merge ↓');
  await until(async () => (await read(root, 'effective')).units.some(u => u.sections.includes(38) && u.sections.includes(39)), 'merge persists');
  await until(async () => (await effectivePanel.locator('mark.seg-source-change').allTextContents()).join('') === autoUnit(original,39).text_original, 'only merged-in original text is highlighted');
  const colors = await effectivePanel.locator('mark.seg-source-change').first().evaluate(el => ({background:getComputedStyle(el).backgroundColor,text:getComputedStyle(el).color}));
  assert.notEqual(colors.background, 'rgb(255, 255, 0)', 'highlight uses muted theme color');
  await effectivePanel.screenshot({path:path.join(evidence,'source-diff.png')});
  await open(page, 'Split ·');
  await page.locator('button[data-boundary="3"]').click();
  await page.getByText(/有未保存的修改/).waitFor();
  await until(async () => await page.getByRole('button', {name:'下一块 →',exact:true}).isDisabled(), 'split draft blocks next');
  await open(page, 'Change type');
  await choose(page, '分块类型', 'procedure');
  await open(page, 'Split ·');
  await page.getByRole('button', {name:'保存拆分',exact:true}).click();
  await page.getByText('请先保存类型／关系，再保存拆分；已选边界会保留。', {exact:true}).waitFor();
  await open(page, 'Change type');
  await click(page, '保存类型');
  await open(page, 'Split ·');
  assert.equal(await page.locator('button[data-boundary="3"]').getAttribute('aria-pressed'), 'true');
  await click(page, '保存拆分');
  await until(async () => (await read(root, 'effective')).units.filter(u => u.sections.includes(38)).length === 2, 'split merged block');
  const pieces = (await read(root, 'effective')).units.filter(u => u.sections.includes(38));
  assert.equal(pieces[0].text_original, autoUnit(original, 38).text_original.slice(0, 3));
  await click(page, 'Merge ↓');
  await until(async () => (await read(root, 'effective')).units.filter(u => u.sections.includes(38)).length === 1, 'merge derived blocks');
  checks.push('Merge → click character boundary → split → merge works on final blocks');
  await click(page, 'Undo · 撤销上次操作');
  await until(async () => (await read(root, 'effective')).units.filter(u => u.sections.includes(38)).length === 2, 'undo restores split');
  const persisted = await read(root, 'effective');
  await page.getByRole('button', {name:'Full text',exact:true}).click();
  await page.getByRole('heading', {name:'Corpus Full Text',exact:true}).waitFor();
  await page.locator('.seg-full-text section').first().waitFor();
  const fullText = await page.locator('.seg-full-text section').evaluateAll(sections => sections.map(el => ({
    id:el.dataset.unitId, text:el.querySelector('.seg-full-text-source').textContent,
    type:el.querySelector('span').textContent,
  })));
  assert.deepEqual(fullText, persisted.units.map(u => ({id:u.id, text:u.text_original, type:u.type})));
  await page.getByRole('button', {name:'返回 Review',exact:true}).click();
  await ready(page);
  await page.locator('.st-key-seg_auto_panel').getByText(autoUnit(original,38).text_original, {exact:true}).waitFor();
  assert.equal(await page.getByRole('textbox', {name:'审阅者',exact:true}).inputValue(), 'browser-acceptance');
  assert.deepEqual(await read(root,'effective'), persisted, 'full text is read only');
  checks.push('Full text shows every effective block and type in order; return preserves review source, unit and actor');
  const history = (await read(root, 'overrides')).history;
  const lastRevision = earlierRevisions + 7;
  assert.equal(history.length, lastRevision);
  assert.equal(history.at(-1).action, 'undo');
  assert.equal(history.at(-1).reverts, lastRevision-1);
  await page.getByText('审阅记录', {exact:true}).click();
  await page.getByRole('button', {name:`View before / after · rev ${lastRevision}`,exact:true}).click();
  await page.getByText('Before', {exact:true}).waitFor();
  await page.getByText('After', {exact:true}).waitFor();
  checks.push('Permanent revision history retains undone action and renders before/after');
  await page.screenshot({ path: path.join(evidence, 'real-review.png'), fullPage: true });
  await page.close();
  await stop();
  url = await start(root);
  const reopened = await browser.newPage();
  await reopened.goto(url);
  await ready(reopened);
  await choose(reopened, 'Source', '四分历');
  await actor(reopened);
  await choose(reopened, 'Current effective unit', /^§38 ·/);
  assert.deepEqual(await read(root, 'effective'), persisted);
  await until(async () => (await reopened.locator('.st-key-seg_effective_panel').innerText()).includes(pieces[0].text_original), 'reopened selected effective block renders');
  await reopened.getByRole('button', {name:'Resume review · 继续未审阅',exact:true}).click();
  await settled(reopened);
  await until(async () => (await reopened.locator('.st-key-seg_auto_panel').innerText()).includes(original.units[0].text_original), 'Resume renders first unreviewed unit');
  await choose(reopened, 'Current effective unit', /^§38 ·/);
  checks.push('Close browser + stop service + reopen preserves same effective and review');
  await click(reopened, 'Reset · 恢复本区域机器结果');
  await until(async () => (await read(root, 'overrides')).operations.length === 0, 'reset restores region');
  assert.deepEqual((await read(root, 'auto')).units, original.units);
  checks.push('Reset restores connected original auto units and removes active deltas');
  for (const [id, name] of [['santong', '三统历'], ['jiuzhi', '九执历']]) {
    await choose(reopened, 'Source', name);
    await click(reopened, 'Accept · 原样接受');
    assert.equal((await read(root, 'manifest', id)).review_status.accepted, 1);
    assert.equal((await read(root, 'manifest')).review_status.reviewed, 0);
    await click(reopened, 'Undo · 撤销上次操作');
    assert.equal((await read(root, 'manifest', id)).review_status.reviewed, 0);
  }
  await choose(reopened, 'Source', '四分历');
  assert.deepEqual((await read(root, 'auto')).units, original.units);
  checks.push('Source switching uses the same UI with isolated progress, files and Undo');
  await reopened.close();
  await stop();

  const unicodeRoot = path.join(directory, 'unicode');
  await fs.mkdir(path.join(unicodeRoot, 'config'), { recursive: true });
  await fs.writeFile(path.join(unicodeRoot, 'config/calendrical-ir-pipeline.json'), JSON.stringify({ inputs: { source_texts: [{ id: 'sifen', path: 'calendars-test.md' }] } }));
  const source = '題\r\n1 推術𠀀é甲。\r\n2 推術𠀀é甲。\r\n';
  await fs.writeFile(path.join(unicodeRoot, 'calendars-test.md'), source);
  await command(['scripts/corpus/extract_sifen_units.py', '--root', unicodeRoot]);
  url = await start(unicodeRoot);
  const unicodePage = await browser.newPage();
  await unicodePage.goto(url);
  await ready(unicodePage);
  await actor(unicodePage);
  await open(unicodePage, 'Split ·');
  await unicodePage.locator('button[data-boundary="3"]').click();
  await unicodePage.locator('button[data-boundary="5"]').click();
  await click(unicodePage, '保存拆分');
  await until(async () => (await read(unicodeRoot, 'effective')).units.length === 4, 'Unicode browser split');
  const split = await read(unicodeRoot, 'effective');
  assert.deepEqual(split.units.map(u => u.text_original), ['推術𠀀', 'é', '甲。', '推術𠀀é甲。']);
  for (const unit of split.units) for (const span of unit.source_spans)
    assert.equal([...source].slice(span.start, span.end).join(''), span.text);
  assert.deepEqual((await read(unicodeRoot, 'auto')).units[1].human_review, []);
  checks.push('Real glyph clicks preserve astral/combining/CRLF offsets and repeated occurrence isolation');
  assert.deepEqual(errors, []);
  await fs.writeFile(path.join(evidence, 'browser-report.json'), JSON.stringify({ status: 'passed', actor: 'automated_browser', time: new Date().toISOString(), checks }, null, 2) + '\n');
  console.log(JSON.stringify({ status: 'passed', checks }, null, 2));
} catch (error) {
  for (const context of browser.contexts()) for (const page of context.pages()) {
    await page.screenshot({ path: path.join(evidence, 'failure.png'), fullPage: true }).catch(() => {});
    await fs.writeFile(path.join(evidence, 'failure.html'), await page.content());
  }
  await fs.writeFile(path.join(evidence, 'server.log'), serverLog);
  throw error;
} finally {
  await browser.close();
  await stop();
  assert.ok(path.resolve(directory).startsWith(path.resolve(os.tmpdir()) + path.sep + 'mathesis-segmentation-browser-'));
  await fs.rm(directory, { recursive: true, force: true });
}
