// M3 browser acceptance: the page drives reviewed compilation, never graph editing.
import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const origin = process.env.WORKBENCH_URL || 'http://127.0.0.1:8789';
const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage({ viewport: { width: 1440, height: 1050 } });
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto(`${origin}/adjudication/?actor=scripted_browser`);
  await page.waitForFunction(() => document.querySelectorAll('[data-step-id]').length > 0);
  assert.equal(await page.locator('#system-stages [data-stage-id]').count(), 6, 'real processing records are visible');
  assert.equal(await page.locator('#annotation-layer').count(), 1, 'source layers are selectable');
  assert.equal(await page.locator('#review-queue [data-review-id]').count() > 0, true, 'real compiler questions are visible');
  const coordinateSegments = await page.evaluate(async () => {
    const { sourceSegments } = await import('/js/ui/source-links.js');
    return sourceSegments('𠀀a\u0301\n甲甲', [{ start: 0, end: 3 }, { start: 4, end: 6 }, { start: 5, end: 6 }]);
  });
  assert.deepEqual(coordinateSegments.map(row => [row.start, row.end, row.text, row.spans.length]), [[0, 3, '𠀀á', 1], [3, 4, '\n', 0], [4, 5, '甲', 1], [5, 6, '甲', 2]], 'astral, combining, newline, repeated text and multi-event spans retain code-point coordinates');
  const annotatedSelection = await page.evaluate(async () => {
    const { renderSource, selectionAnchor } = await import('/js/ui/source-links.js');
    const text = '𠀀a\u0301\n甲甲', doc = { doc_id: 'coordinate-probe', reading_id: 'reading-1', text, category: 'primary_documents' };
    const spans = [[0, 3], [4, 6], [5, 6]].map(([start, end]) => ({ doc_id: doc.doc_id, reading_id: doc.reading_id, start, end }));
    const steps = spans.map((span, i) => ({ id: `probe-${i}`, source_spans: [span] }));
    const host = document.createElement('div'); document.body.append(host);
    renderSource(host, [doc], steps, () => {}, [], () => {}, { steps: Object.fromEntries(steps.map(s => [s.id, { label: '结构标注' }])) });
    const actualText = host.querySelector('.source-text').textContent;
    const marks = host.querySelectorAll('.source-span mark');
    const range = document.createRange(); range.setStart(marks[0].firstChild, 2); range.setEnd(marks[marks.length - 1].firstChild, 1);
    const selection = window.getSelection(); selection.removeAllRanges(); selection.addRange(range);
    const anchor = selectionAnchor(host); selection.removeAllRanges(); host.remove();
    return { actualText, anchor };
  });
  assert.equal(annotatedSelection.actualText, '𠀀á\n甲甲', 'shared annotation markup must not insert characters into source');
  assert.deepEqual(annotatedSelection.anchor, { doc_id: 'coordinate-probe', reading_id: 'reading-1', start: 1, end: 6 }, 'selection inside shared mark markup remains in source code points');
  const source = page.locator('#source button[data-doc-id="sifen:38"][data-start="0"]');
  await source.click();
  assert.equal(await page.locator('#selected-anchor').getAttribute('data-doc-id'), 'sifen:38');
  await page.locator('#advanced-details > summary').click();
  await page.locator('#lexical-role').selectOption('term');
  const response = page.waitForResponse(r => r.url() === `${origin}/api/adjudication/decision`);
  await page.locator('#apply-lexical-role').click();
  assert.equal((await response).ok(), true);
  await page.locator('#decision-history [data-decision-action="set_lexical_role"]').waitFor();
  const before = await page.locator('#decision-history').innerText();
  await page.reload();
  await page.locator('#advanced-details > summary').click();
  await page.locator('#decision-history [data-decision-action="set_lexical_role"]').waitFor();
  assert.equal(await page.locator('#decision-history').innerText(), before, 'session restores after browser reload');
  const persistedSession = await page.evaluate(() => localStorage.getItem('mathesis.adjudication-session.v1.sifen-3-5'));
  await page.route('**/api/adjudication/compile', route => route.fulfill({ status: 409, contentType: 'application/json', body: JSON.stringify({ error: 'transient_test_failure' }) }));
  await page.locator('#analyze').click();
  await page.waitForFunction(() => document.querySelector('#status').textContent.includes('已保留本地 session'), null, { timeout: 5000 });
  assert.equal(await page.evaluate(() => localStorage.getItem('mathesis.adjudication-session.v1.sifen-3-5')), persistedSession, 'failed replay preserves the saved session');
  await page.unroute('**/api/adjudication/compile');
  const segment = page.locator('#source button[data-doc-id="sifen:38"][data-start="12"]');
  await segment.click();
  await page.locator('#split-at').fill('14');
  const resegment = page.waitForResponse(r => r.url() === `${origin}/api/adjudication/decision`);
  await page.locator('#resegment').click();
  const segmentedResponse = await resegment;
  assert.equal(segmentedResponse.ok(), true, await segmentedResponse.text());
  await page.locator('#decision-history [data-decision-action="resegment"]').waitFor();
  const retract = page.waitForResponse(r => r.url() === `${origin}/api/adjudication/decision`);
  await page.locator('#decision-history [data-decision-action="resegment"]').getByRole('button', { name: '撤销决定' }).click();
  assert.equal((await retract).ok(), true);
  await page.waitForFunction(() => JSON.parse(document.querySelector('#graph-raw').textContent).adjudication.effective_decisions.segments.length === 0);
  await page.locator('#branch-name').fill('browser-reading');
  const branch = page.waitForResponse(r => r.url() === `${origin}/api/adjudication/branch`);
  await page.locator('#create-branch').click();
  assert.equal((await branch).ok(), true);
  await page.waitForFunction(() => document.querySelector('#branch-select').value === 'browser-reading');
  assert.equal(await page.locator('#branch-select').inputValue(), 'browser-reading');
  const downloadPromise = page.waitForEvent('download');
  await page.locator('#export-session').click();
  const download = await downloadPromise;
  const chunks = [];
  for await (const chunk of await download.createReadStream()) chunks.push(chunk);
  const imported = page.waitForResponse(r => r.url() === `${origin}/api/adjudication/compile`);
  await page.locator('#import-session').setInputFiles({ name: 'session.json', mimeType: 'application/json', buffer: Buffer.concat(chunks) });
  assert.equal((await imported).ok(), true);
  assert.equal(await page.locator('#branch-select').inputValue(), 'browser-reading', 'export then import preserves branch replay state');
  await page.selectOption('#procedure', 'sifen-3-7-alternative');
  await page.waitForFunction(() => document.querySelector('#scope').textContent.includes('一术'));
  assert.equal(await page.locator('#review-queue [data-review-id]').count() > 0, true, 'same view renders the real hole target');
  async function assertRealHoleVisible() {
    if (await page.locator('#advanced-details').getAttribute('open') === null) await page.locator('#advanced-details > summary').click();
    for (const id of ['source', 'structure', 'graph']) {
      assert.equal(await page.locator(`#${id}`).isVisible(), true, `${id} is actually visible for §40`);
      assert.ok((await page.locator(`#${id}`).innerText()).trim(), `${id} has rendered content`);
    }
    const graph = JSON.parse(await page.locator('#graph-raw').textContent());
    assert.ok(graph.unresolved.some(issue => issue.source_spans.some(span => span.doc_id === 'sifen:40' && span.start === 9 && span.end === 14 && span.quote === '周天乘減之')), 'known unresolved construction retains its actual source address');
    const questions = page.locator('#review-queue article', { hasText: '当前规则未能解释这段文字' });
    let located = false;
    for (const question of await questions.all()) {
      assert.equal(await question.isVisible(), true, 'unresolved question is visible');
      await question.getByRole('button').click();
      if (await page.locator('#selected-anchor').getAttribute('data-start') === '9') {
        assert.equal(await page.locator('#selected-anchor').getAttribute('data-doc-id'), 'sifen:40');
        assert.equal(await page.locator('#selected-anchor').getAttribute('data-end'), '14');
        assert.match(await page.locator('#selected-anchor').innerText(), /周天乘減之/);
        located = true;
        break;
      }
    }
    assert.equal(located, true, 'the actual unresolved question locates its known source span');
  }
  await assertRealHoleVisible();
  await page.locator('#apply-lexical-role').click();
  await page.locator('#decision-history [data-decision-action="set_lexical_role"]').waitFor();
  // A compiler upgrade leaves real persisted sessions with obsolete identity locks.
  // Seed both registered targets so cold reload starts without an old visible graph.
  const savedStale = await page.evaluate(() => {
    for (const id of ['sifen-3-5', 'sifen-3-7-alternative']) {
      const key = `mathesis.adjudication-session.v1.${id}`;
      const saved = JSON.parse(localStorage.getItem(key));
      saved.session.identity_locks.engine.sha256 = 'previous-engine-version';
      localStorage.setItem(key, JSON.stringify(saved));
    }
    return localStorage.getItem('mathesis.adjudication-session.v1.sifen-3-7-alternative');
  });
  await page.reload();
  await page.waitForFunction(() => !document.querySelector('#procedure').disabled);
  await page.selectOption('#procedure', 'sifen-3-7-alternative');
  await page.waitForFunction(() => !document.querySelector('#procedure').disabled);
  await assertRealHoleVisible();
  assert.match(await page.locator('#status').innerText(), /待重验/);
  assert.match(await page.locator('#session-status').innerText(), /待重新核验/);
  assert.equal(await page.locator('#decision-history [data-decision-action="set_lexical_role"]').count(), 1);
  assert.equal(await page.locator('#resegment').isDisabled(), true, 'stale decisions cannot mutate the automatic reference');
  assert.equal(await page.locator('#execute').isDisabled(), true);
  assert.equal(await page.evaluate(() => localStorage.getItem('mathesis.adjudication-session.v1.sifen-3-7-alternative')), savedStale, 'stale session is retained byte-for-byte');
  const staleExport = page.waitForEvent('download');
  await page.locator('#export-session').click();
  const staleChunks = [];
  for await (const chunk of await (await staleExport).createReadStream()) staleChunks.push(chunk);
  assert.deepEqual(JSON.parse(Buffer.concat(staleChunks)).session, JSON.parse(savedStale).session, 'export retains original identity locks');
  await page.locator('#import-session').setInputFiles({ name: 'stale-session.json', mimeType: 'application/json', buffer: Buffer.concat(staleChunks) });
  await page.waitForFunction(() => document.querySelector('#status').textContent.includes('待重验'));
  await assertRealHoleVisible();
  const visibleText = await page.locator('#analysis').innerText();
  assert.doesNotMatch(visibleText, /\b[ev]\d+\b|G_[A-Z_0-9]+|unresolved_parser|missing_import|unknown_quantity|no_legal_candidate|needs_revalidation|unresolved_focus/, 'normal view contains backend language, not machine codes');
  const ontology = await (await page.request.get(`${origin}/api/ontology`)).json();
  const reference = await browser.newPage();
  await reference.goto(`${origin}/methodology/`);
  await reference.waitForFunction(() => document.querySelectorAll('[data-ontology-code]').length > 0);
  assert.equal(await reference.locator('[data-ontology-code]').count(), ontology.entries.length, 'reference renders every live registry entry');
  const label = ontology.entries.find(row => row.category === 'cause' && row.code === 'unresolved_parser').label;
  assert.equal(await reference.locator('[data-ontology-category="cause"][data-ontology-code="unresolved_parser"] h2').innerText(), label);
  // Presentation transport contract: newly authored backend labels do not require
  // a browser map or release. This is a scripted renderer test, not scholarship.
  const extension = { ...ontology.entries.find(row => row.category === 'issue'), code: 'new_test_issue', label: '新登记的审核事项', definition: '由测试目录提供的定义' };
  await reference.route('**/api/ontology', route => route.fulfill({ json: { ...ontology, entries: [...ontology.entries, extension] } }));
  await reference.reload();
  await reference.locator('[data-ontology-code="new_test_issue"]').waitFor();
  assert.equal(await reference.locator('[data-ontology-code="new_test_issue"] h2').innerText(), extension.label);
  const extra = await browser.newPage();
  await extra.route('**/api/adjudication/sifen-3-5', async route => {
    const response = await route.fetch(); const body = await response.json();
    body.presentation.questions.push({ ...body.presentation.questions[0], id: extension.code, label: extension.label, text: extension.definition });
    await route.fulfill({ json: body });
  });
  await extra.goto(`${origin}/adjudication/?actor=scripted_browser`);
  await extra.locator('#review-summary button', { hasText: extension.label }).waitFor();
  await extra.locator('#advanced-details > summary').click();
  await extra.locator('[data-review-id="new_test_issue"]').waitFor();
  assert.match(await extra.locator('[data-review-id="new_test_issue"]').innerText(), /新登记的审核事项/);
  await extra.close(); await reference.close();
  assert.equal(await page.locator('#numerical-check').getAttribute('open'), null);
  assert.deepEqual(errors, []);
  console.log('M3 browser acceptance passed: stages, layers, linked source, real decision/recompile, restore, and two corpus targets.');
} finally {
  await browser.close();
}
