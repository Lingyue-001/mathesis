import { renderSource, markSourceSelection, revealInPanel } from './ui/source-links.js';
import { renderStructure, renderGraph, renderRelationships, markObjects, element, action, pretty } from './ui/procedure-view.js';

const byId = id => document.getElementById(id);
const base = document.documentElement.dataset.baseurl || '/';
const json = value => JSON.stringify(value, null, 2);
let analysis;

async function request(path, body) {
  const response = await fetch(`${base.replace(/\/?$/, '/')}${path}`, body === undefined ? {} : {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: json(body),
  });
  if (!response.headers.get('Content-Type')?.includes('application/json')) throw new Error('此站点当前未连接本地分析服务。');
  const value = await response.json();
  if (!response.ok) throw new Error(value.error || `HTTP ${response.status}`);
  return value;
}

function busy(value) {
  byId('procedure').disabled = value;
  byId('analyze').disabled = value;
  byId('execute').disabled = value;
  byId('inputs').querySelectorAll('input').forEach(input => { input.disabled = value; });
}

function select(stepIds, nodeIds, spans, title) {
  const steps = new Set(stepIds), nodes = new Set(nodeIds);
  markObjects(byId('structure'), 'data-step-id', steps);
  markObjects(byId('graph'), 'data-node-id', nodes);
  markSourceSelection(byId('source'), spans);
  for (const edge of byId('graph').querySelectorAll('.graph-edge')) {
    edge.dataset.selected = String(nodes.has(edge.dataset.consumer) || nodes.has(edge.dataset.producer));
  }
  byId('selection-status').textContent = `${title} · ${steps.size} 个语法步骤 · ${nodes.size} 个 graph events`;
  renderRelationships(byId('selection-detail'), analysis.projection, nodes, steps, selectNode);
  for (const id of ['source', 'structure', 'graph']) revealInPanel(byId(id), byId(id).querySelector('[data-selected="true"]:not(.graph-edge)'));
}

function selectSteps(ids) {
  const steps = analysis.projection.steps.filter(s => ids.includes(s.id));
  select(ids, steps.flatMap(s => s.event_ids), steps.flatMap(s => s.source_spans), steps.map(s => s.surface).join(' / '));
}

function selectNode(id) {
  const node = analysis.projection.nodes.find(n => n.id === id);
  if (node) select(node.step_ids, [id], node.source_spans || [], `${node.id} · ${node.kind}`);
}

function selectFrame(id) {
  const frame = analysis.projection.frames.find(f => f.id === id);
  if (!frame) return;
  const seen = new Set();
  function children(ident) {
    if (seen.has(ident)) return [];
    seen.add(ident);
    const current = analysis.projection.frames.find(f => f.id === ident);
    return (current?.body || []).flatMap(item => item.type === 'frame' ? children(item.id) : [item.id]);
  }
  selectSteps(children(id));
  byId('selection-detail').prepend(element('p', 'entry-card-row', `${frame.kind} · ${frame.id} · formal inputs: ${pretty(frame.formal_inputs)} · return ports: ${pretty(frame.return_ports)}${frame.base_ref ? ` · base: ${frame.base_ref}` : ''}`));
}

function showIssues() {
  byId('analysis-issues').replaceChildren();
  if (!analysis.projection.issues.length) byId('analysis-issues').append(element('p', 'entry-card-note', 'IR 未报告 unresolved 或类型缺口。'));
  for (const issue of analysis.projection.issues) {
    const item = element('details', 'research-disclosure');
    item.append(element('summary', '', `${issue.origin} · ${issue.kind}${issue.formal ? ` · ${issue.formal}` : ''}${issue.value_id ? ` · ${issue.value_id}` : ''}`));
    const steps = analysis.projection.steps.filter(s => s.issue_ids.includes(issue.id));
    if (steps.length) item.append(action('定位相关原文与步骤', () => selectSteps(steps.map(s => s.id))));
    item.append(element('pre', '', json(issue)));
    byId('analysis-issues').append(item);
  }
}

function showInputs() {
  byId('inputs').replaceChildren();
  for (const [i, spec] of analysis.procedure.inputs.entries()) {
    const box = element('div');
    const label = element('label', '', `${spec.name}（${spec.minimum}–${spec.maximum}）`);
    label.htmlFor = `input-${i}`;
    const field = element('input');
    field.type = 'text'; field.inputMode = 'numeric'; field.id = label.htmlFor; field.name = spec.name;
    box.append(label, field);
    byId('inputs').append(box);
  }
}

async function analyze() {
  busy(true);
  analysis = null;
  byId('analysis').hidden = true;
  byId('status').textContent = '正在分析原文与 procedure structure…';
  byId('execution-result').hidden = true;
  byId('execution-status').textContent = '尚未执行。';
  byId('numerical-check').open = false;
  try {
    analysis = await request(`api/analysis/${encodeURIComponent(byId('procedure').value)}`);
    byId('scope').textContent = analysis.procedure.scope_note;
    const p = analysis.projection;
    renderSource(byId('source'), analysis.graph.documents, p.steps, selectSteps);
    renderStructure(byId('structure'), p, selectSteps, selectFrame);
    renderGraph(byId('graph'), p, selectNode);
    byId('graph-summary').textContent = `${p.nodes.length} events · ${p.quantities.length} values · ${p.edges.length} dependency edges`;
    byId('selection-detail').replaceChildren();
    byId('selection-status').textContent = '选择原文、步骤或图节点，查看 typed relationships。';
    byId('graph-raw').textContent = json(analysis.graph);
    showIssues(); showInputs();
    byId('analysis').hidden = false;
    byId('status').textContent = `结构已载入 · ${p.steps.length} 个语法步骤 · ${p.issues.length} 项结构提示 · 数值执行尚未运行`;
  } catch (error) {
    byId('status').textContent = `分析未完成：${error.message}`;
  } finally {
    busy(false);
  }
}

byId('procedure').addEventListener('change', analyze);
byId('analyze').addEventListener('click', analyze);
byId('execute-form').addEventListener('submit', async event => {
  event.preventDefault();
  if (!analysis) return;
  busy(true);
  byId('execution-result').hidden = true;
  byId('execution-status').textContent = '正在执行辅助数值验证…';
  try {
    const inputs = {};
    for (const field of byId('inputs').querySelectorAll('input')) {
      const text = field.value.trim();
      if (!text) continue;
      if (!/^\d+$/.test(text) || !Number.isSafeInteger(Number(text))) throw new Error(`${field.name} 请输入整数`);
      inputs[field.name] = Number(text);
    }
    const result = await request('api/compile', { procedure_id: analysis.procedure.id, inputs });
    byId('execution-status').textContent = `Execution: ${result.summary.execution_status}`;
    byId('outputs').textContent = json(result.execution.named_outputs);
    byId('execution-raw').textContent = json(result.execution);
    byId('execution-result').hidden = false;
  } catch (error) {
    byId('execution-status').textContent = `数值验证未完成：${error.message}`;
  } finally {
    busy(false);
  }
});

try {
  const response = await request('api/procedures');
  for (const procedure of response.procedures) byId('procedure').add(new Option(procedure.title, procedure.id));
  if (!response.procedures.length) throw new Error('没有已登记的 procedure');
  await analyze();
} catch (error) {
  byId('status').textContent = `无法载入：${error.message}`;
}
