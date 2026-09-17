// Start the same-origin workbench with the Eleventy build, then run this file.
import assert from 'node:assert/strict';
import { mkdir } from 'node:fs/promises';
import { chromium } from 'playwright';

const origin = process.env.WORKBENCH_URL || 'http://127.0.0.1:8789';
const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  const errors = [];
  const requests = [];
  page.on('pageerror', error => errors.push(error.message));
  page.on('request', request => requests.push(request.url()));
  await page.goto(`${origin}/adjudication/`);
  assert.equal(await page.locator('#homeSideNav a[href="/adjudication/"]').count(), 1, 'Must be a website page with shared navigation');
  await page.waitForFunction(() => document.querySelectorAll('[data-step-id]').length > 0);
  for (const viewport of [{ width: 1440, height: 900 }, { width: 1366, height: 768 }]) {
  await page.setViewportSize(viewport);
  await page.evaluate(() => scrollTo(0, 0));
  for (const procedure of ['sifen-3-5', 'sifen-3-7-alternative']) {
    await page.selectOption('#procedure', procedure);
    await page.waitForFunction(() => !document.querySelector('#procedure').disabled);
    assert.equal(await page.locator('#source-structure #source').count(), 1, 'source and annotated structure share one panel');
    assert.equal(await page.locator('#source-structure #structure').count(), 1);
    assert.equal(await page.locator('#advanced-details').getAttribute('open'), null);
    assert.equal(await page.locator('#branch-select').isVisible(), false);
    assert.equal(await page.locator('#apply-lexical-role').isVisible(), false);
    await mkdir('.cache/workbench', { recursive: true });
    await page.screenshot({ path: `.cache/workbench/presentation-${procedure}-${viewport.width}.png` });
    for (const id of ['source', 'structure', 'graph', 'review-summary']) {
      const box = await page.locator(`#${id}`).boundingBox();
      assert.ok(box && box.y >= 0 && box.y + box.height <= viewport.height, `${procedure}: ${id} fits ${viewport.width}×${viewport.height}: ${JSON.stringify(box)}`);
    }
    const graph = JSON.parse(await page.locator('#graph-raw').textContent());
    assert.equal(await page.locator('#graph [data-value-id]').count(), graph.value_instances.length, 'quantity objects are represented, not only events');
    assert.equal(await page.locator('#graph [data-node-id]').count(), graph.events.length);
    for (const kind of ['parameter-input', 'operation', 'result', 'unresolved']) assert.ok(await page.locator(`#graph [data-kind="${kind}"]`).count(), `${kind} has a distinct presentation`);
    if (procedure === 'sifen-3-5') assert.ok(await page.locator('#graph [data-kind="value"]').count());
    const viewBox = await page.locator('#graph svg').getAttribute('viewBox');
    const dimensions = viewBox.split(' ').map(Number);
    assert.ok(dimensions[2] > dimensions[3], 'graph is horizontal and compact');
    assert.ok(await page.locator('#review-summary button').count());
    assert.doesNotMatch(await page.locator('#presentation-view').innerText(), /\b[ev]\d+\b|G_[A-Z_0-9]+|unresolved_parser/);
    if (procedure === 'sifen-3-7-alternative') {
      const unresolved = page.locator('#source button[data-doc-id="sifen:40"][data-start="9"]');
      assert.equal(await unresolved.getAttribute('data-unresolved'), 'true');
      await unresolved.click();
      assert.ok(await page.locator('#structure [data-selected="true"]').count());
      const multiplier = page.locator('#graph [data-node-id]', { hasText: '相乘' });
      await multiplier.click();
      assert.match(await page.locator('#relation-summary').innerText(), /大周.*年/);
      assert.equal(await page.locator('#source button[data-doc-id="sifen:40"][data-start="3"]').getAttribute('data-selected'), 'true');
    }
  }
  }
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.selectOption('#procedure', 'sifen-3-5');
  await page.waitForFunction(() => !document.querySelector('#procedure').disabled);
  assert.equal(requests.filter(url => url.endsWith('/api/adjudication/execute')).length, 0, 'Analysis must not execute');
  assert.equal(await page.locator('#numerical-check').getAttribute('open'), null);
  assert.equal(await page.locator('#execute-form').isVisible(), false);
  assert.match(await page.locator('#source').innerText(), /置入蔀年減一/);
  const source = page.locator('#source button[data-doc-id="sifen:38"][data-start="12"]');
  await source.click();
  assert.equal(await page.locator('[data-step-id="sifen:38:ast9"]').getAttribute('data-selected'), 'true');
  assert.equal(await page.locator('[data-node-id="e7"]').getAttribute('data-selected'), 'true');
  await page.locator('[data-step-id="sifen:38:ast12"] button').first().click();
  assert.equal(await page.locator('#source button[data-start="18"]').getAttribute('data-selected'), 'true');
  assert.equal(await page.locator('[data-node-id="e8"]').getAttribute('data-selected'), 'true');
  await page.locator('#advanced-details > summary').click();
  assert.match(await page.locator('#selection-detail').innerText(), /余数/);
  assert.match(await page.locator('#selection-detail').innerText(), /月分量/);
  await page.locator('[data-node-id="e10"]').click();
  assert.equal(await page.locator('[data-step-id="sifen:38:ast16"]').getAttribute('data-selected'), 'true');
  assert.equal(await page.locator('#source button[data-start="29"]').getAttribute('data-selected'), 'true');
  assert.match(await page.locator('#analysis-issues').innerText(), /输入缺少来源/);
  assert.match(await page.locator('#analysis-issues').innerText(), /数量语义未定/);
  await page.locator('[data-node-id="e8"]').focus();
  await page.keyboard.press('Enter');
  assert.equal(await page.locator('[data-node-id="e8"]').getAttribute('data-selected'), 'true');
  const segments = await page.evaluate(async () => {
    const { sourceSegments } = await import('/js/ui/source-links.js');
    return sourceSegments('𠀀甲，甲', [{ start: 0, end: 2 }, { start: 3, end: 4 }]);
  });
  assert.deepEqual(segments.map(s => s.text), ['𠀀甲', '，', '甲']);
  assert.deepEqual(segments.map(s => [s.start, s.end]), [[0, 2], [2, 3], [3, 4]]);
  await page.locator('#graph-json summary').click();
  assert.equal(JSON.parse(await page.locator('#graph-raw').innerText()).ir_revision, '3.1-rescue');
  await page.locator('#graph-json summary').click();
  await mkdir('.cache/workbench', { recursive: true });
  await page.screenshot({ path: '.cache/workbench/analysis-desktop.png', fullPage: true });
  await page.locator('#numerical-check > summary').click();
  const execute = async () => {
    const response = page.waitForResponse(r => r.url() === `${origin}/api/adjudication/execute`);
    await page.locator('#execute').click();
    const value = await (await response).json();
    await page.waitForFunction(() => !document.getElementById('execute').disabled);
    return value;
  };
  assert.equal((await execute()).summary.execution_status, 'missing_inputs');
  await page.locator('#input-0').fill('25');
  const success = await execute();
  assert.equal(success.execution.named_outputs['main:積月'], 296);
  assert.equal(success.execution.named_outputs['main:閏餘'], 16);
  assert.match(await page.locator('#execution-status').innerText(), /数值核算完成/);
  assert.equal(await page.locator('[data-node-id="e8"]').getAttribute('data-selected'), 'true', 'Executing must retain structure selection');
  await page.locator('#input-0').fill('77');
  assert.match((await execute()).error, /invalid_input/);
  assert.equal(await page.locator('#execution-result').isVisible(), false);
  await page.locator('#numerical-check > summary').click();
  await page.setViewportSize({ width: 390, height: 844 });
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
  await page.screenshot({ path: '.cache/workbench/analysis-mobile.png', fullPage: true });
  await page.locator('#homeMenuToggle').click();
  await page.locator('#homeSideNav a[href="/patterns/"]').click();
  await page.waitForURL(`${origin}/patterns/`);
  await page.waitForFunction(() => document.getElementById('comparisonResults').children.length > 0);
  assert.equal(await page.locator('#patternSearch').count(), 1);
  assert.deepEqual(errors, []);
  console.log('Browser smoke passed: site navigation, compile-only analysis, bidirectional source/step/graph links, typed ports, uncertainty, Unicode offsets, keyboard, auxiliary execution, mobile layout, Pattern Lab entry.');
} finally {
  await browser.close();
}
