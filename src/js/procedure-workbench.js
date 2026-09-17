import { renderSource, markSourceSelection, revealInPanel, selectionAnchor } from './ui/source-links.js';
import { renderStructure, renderGraph, renderRelationships, markObjects, element, action } from './ui/procedure-view.js';
import { exportSession, importSession, loadSession, saveSession } from './ui/adjudication-session-store.js';

const byId = id => document.getElementById(id);
const base = document.documentElement.dataset.baseurl || '/';
const json = value => JSON.stringify(value, null, 2);
const scriptedActor = new URLSearchParams(location.search).get('actor') === 'scripted_browser';
let analysis;
let selectedAnchor;
let requestRevision = 0;

async function request(path, body) {
  const response = await fetch(`${base.replace(/\/?$/, '/')}${path}`, body === undefined ? {} : { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: json(body) });
  if (!response.headers.get('Content-Type')?.includes('application/json')) throw new Error('此站点当前未连接本地分析服务。');
  const value = await response.json();
  if (!response.ok) { console.debug('Workbench API', response.status, value); throw new Error('服务未接受本次请求；原分析仍保留。详细协议记录见浏览器调试控制台。'); }
  return value;
}
function busy(value) {
  for (const node of document.querySelectorAll('.procedure-workbench button, .procedure-workbench select, .procedure-workbench input')) {
    const mutatesReview = node.closest('[aria-labelledby="decision-title"], #execute-form') || ['create-branch', 'branch-name', 'branch-select'].includes(node.id);
    if (node.id !== 'import-session') node.disabled = value || Boolean(analysis?.referenceOnly && mutatesReview);
  }
}
function actor() { return scriptedActor ? { type: 'scripted_fixture', id: 'browser-test' } : { type: 'human', id: 'local-workbench' }; }
function makeDecision(actionName, targets, payload, reason = 'local workbench review', dependsOn = []) {
  return { decision_id: `ui-${crypto.randomUUID()}`, actor: actor(), created_at: new Date().toISOString(), branch_id: analysis.branch_id, action: actionName, targets, payload, evidence_refs: ['workbench:visible-source'], reason, depends_on: dependsOn };
}
function documentFor(anchor) { return analysis.graph.documents.find(doc => doc.doc_id === anchor.doc_id && doc.reading_id === anchor.reading_id); }
function anchorFor(doc, start, end) { return { doc_id: doc.doc_id, reading_id: doc.reading_id, source_sha256: doc.text_sha256, start, end, quote: Array.from(doc.text).slice(start, end).join(''), offset_unit: 'unicode_code_point' }; }

function select(stepIds, nodeIds, spans, title) {
  const steps = new Set(stepIds), nodes = new Set(nodeIds);
  markObjects(byId('structure'), 'data-step-id', steps); markObjects(byId('graph'), 'data-node-id', nodes); markSourceSelection(byId('source'), spans);
  for (const edge of byId('graph').querySelectorAll('.graph-edge')) edge.dataset.selected = String(nodes.has(edge.dataset.consumer) || nodes.has(edge.dataset.producer));
  byId('selection-status').textContent = `${title} · ${steps.size} 个语法步骤 · ${nodes.size} 个 graph events`;
  renderRelationships(byId('selection-detail'), analysis.projection, nodes, steps, selectNode);
  const relations = analysis.projection.nodes.filter(n => nodes.has(n.id)).map(node => {
    const name = id => analysis.presentation.quantities[id]?.name || '未记录的量';
    return `${Object.values(node.reads || {}).map(name).join('、') || '无上游读取'} → ${analysis.presentation.nodes[node.id].operation} → ${Object.values(node.writes || {}).map(name).join('、') || '无独立输出'}`;
  });
  byId('relation-summary').textContent = relations.join('；') || `${title}：没有独立操作，参见待审问题。`;
  const linkedValues = new Set(analysis.projection.nodes.filter(n => nodes.has(n.id)).flatMap(n => [...Object.values(n.reads || {}), ...Object.values(n.writes || {})]));
  markObjects(byId('graph'), 'data-value-id', linkedValues);
  for (const id of ['source', 'structure', 'graph']) revealInPanel(byId(id), byId(id).querySelector('[data-selected="true"]:not(.graph-edge)'));
}
function selectSteps(ids) {
  const steps = analysis.projection.steps.filter(step => ids.includes(step.id));
  select(ids, steps.flatMap(step => step.event_ids), steps.flatMap(step => step.source_spans), steps.map(step => step.surface).join(' / '));
  if (steps[0]?.source_spans[0]) chooseAnchor(steps[0].source_spans[0]);
}
function selectNode(id) { const node = analysis.projection.nodes.find(item => item.id === id); if (node) { select(node.step_ids, [id], node.source_spans || [], analysis.presentation.nodes[id].label); if (node.source_spans?.[0]) chooseAnchor(node.source_spans[0]); } }
function selectFrame(id) {
  const frame = analysis.projection.frames.find(item => item.id === id); if (!frame) return;
  const seen = new Set();
  const children = ident => { if (seen.has(ident)) return []; seen.add(ident); const current = analysis.projection.frames.find(item => item.id === ident); return (current?.body || []).flatMap(item => item.type === 'frame' ? children(item.id) : [item.id]); };
  selectSteps(children(id));
}
function chooseAnchor(anchor) {
  const doc = documentFor(anchor); if (!doc) return;
  selectedAnchor = anchorFor(doc, anchor.start, anchor.end);
  const node = byId('selected-anchor'); node.dataset.docId = selectedAnchor.doc_id; node.dataset.start = selectedAnchor.start; node.dataset.end = selectedAnchor.end;
  node.textContent = `${selectedAnchor.doc_id} [${selectedAnchor.start}, ${selectedAnchor.end}) · ${selectedAnchor.quote}`;
  byId('split-at').min = String(selectedAnchor.start + 1); byId('split-at').max = String(selectedAnchor.end - 1); byId('split-at').value = String(Math.floor((selectedAnchor.start + selectedAnchor.end) / 2)); showCandidateOptions();
}

function renderStages() {
  const box = byId('system-stages'); box.replaceChildren();
  for (const stage of analysis.presentation.stages) {
    const row = element('details', 'research-stage'); row.dataset.stageId = stage.id;
    row.append(element('summary', '', `${stage.label} · ${stage.status}`), element('p', 'entry-card-note', stage.text), element('p', 'entry-card-note', stage.downstream));
    const debug = element('details'); debug.dataset.debug = 'true';
    debug.append(element('summary', '', '调试／阶段原始证据'), element('pre', '', json(stage.provenance)));
    row.append(debug); box.append(row);
  }
}
function selectQuestion(question, location) {
  const spans = location ? [location] : question.source_anchors || [];
  const steps = analysis.projection.steps.filter(step => spans.some(anchor => step.source_spans.some(span => span.doc_id === anchor.doc_id && span.reading_id === anchor.reading_id && span.start < anchor.end && anchor.start < span.end)));
  select(steps.map(s => s.id), steps.flatMap(s => s.event_ids), spans, question.label);
  if (spans[0]) chooseAnchor(spans[0]);
}
function renderQuestions() {
  const box = byId('review-queue'); box.replaceChildren();
  const summary = byId('review-summary'); summary.replaceChildren();
  const groups = new Map();
  for (const question of analysis.presentation.questions) {
    if (!groups.has(question.label)) groups.set(question.label, []);
    groups.get(question.label).push(question);
    const card = element('article', 'entry-card'); card.dataset.reviewId = question.id;
    card.append(action(`${question.label} · ${question.severity}`, () => selectQuestion(question)));
    card.append(element('p', 'entry-card-note', question.text));
    card.append(element('p', 'entry-card-note', `后端建议的动作：${question.actions.map(row => row.label).join(' / ') || '未提供'}`));
    card.append(element('p', 'entry-card-note', question.affected_text));
    card.append(element('p', 'entry-card-note', `${question.evidence_note}：${question.nearby_evidence.map(row => `${row.label}「${row.text}」`).join(' / ') || '未提供'}`));
    box.append(card);
  }
  for (const [label, questions] of groups) {
    const button = action(`${label} · ${questions.length}`, () => selectQuestion(questions[0]));
    button.dataset.kind = 'unresolved'; button.title = questions[0].text; summary.append(button);
  }
  if (!groups.size) summary.append(element('p', 'entry-card-note', '当前没有待审问题；完整性与审定状态见详细检查。'));
}
function showCandidateOptions() {
  const selectBox = byId('candidate-select'); selectBox.replaceChildren();
  const candidates = analysis?.presentation?.candidates || [];
  const matching = !selectedAnchor ? [] : candidates.filter(row => row.source_spans?.some(span => span.doc_id === selectedAnchor.doc_id && span.start < selectedAnchor.end && selectedAnchor.start < span.end));
  for (const row of matching) selectBox.add(new Option(`${row.label} · ${row.surface} · ${row.evidence}`, row.id));
  if (!matching.length) selectBox.add(new Option('所选范围没有可选候选', ''));
}
function showIssues() {
  const box = byId('analysis-issues'); box.replaceChildren();
  for (const issue of analysis.presentation.issues) {
    const item = element('details', 'research-disclosure');
    item.append(element('summary', '', issue.label), element('p', '', issue.text)); box.append(item);
  }
}
function showControls() {
  for (const [id, options] of Object.entries(analysis.presentation.controls)) {
    if (id === 'candidate-select') continue;
    const control = byId(id), selected = control.value; control.replaceChildren();
    for (const option of options) control.add(new Option(option.label, option.code));
    if (options.some(option => option.code === selected)) control.value = selected;
  }
  for (const row of analysis.presentation.actions) {
    for (const button of document.querySelectorAll(`[data-action="${row.code}"]`)) button.textContent = row.label;
  }
}
function showDefinitions() {
  for (const id of ['binding-consumer', 'binding-producer', 'scope-definition', 'scope-base']) byId(id).replaceChildren();
  byId('scope-base').add(new Option('No explicit query base', ''));
  for (const frame of analysis.projection.frames) if (frame.source_spans?.[0]) {
    for (const id of ['binding-consumer', 'binding-producer', 'scope-definition', 'scope-base']) byId(id).add(new Option(analysis.presentation.frames[frame.id].label, frame.id));
  }
  const contexts = byId('context-select'); contexts.replaceChildren();
  for (const doc of analysis.graph.documents.filter(doc => doc.category === 'context_documents')) contexts.add(new Option(`${doc.source?.path || '背景材料'} · ${doc.text}`, doc.doc_id));
}
function showHistory() {
  const box = byId('decision-history'); box.replaceChildren();
  for (const row of analysis.presentation.history) {
    const line = element('p', 'entry-card-row', `${row.revision}. ${row.label} · ${row.actor} · ${row.status} · ${row.quote}`);
    line.dataset.decisionAction = row.action;
    if (row.action !== 'retract') {
      const decision = analysis.session.decisions.find(item => item.decision_id === row.id);
      line.append(action(analysis.presentation.actions.find(item => item.code === 'retract').label, () => applyDecision(makeDecision('retract', decision.targets, { decision_id: row.id }, `retract ${row.id}`))));
    }
    box.append(line);
  }
}
function showInputs() { byId('inputs').replaceChildren(); for (const [index, spec] of analysis.procedure.inputs.entries()) { const field = element('input'); field.type = 'text'; field.inputMode = 'numeric'; field.id = `input-${index}`; field.name = spec.name; const labelNode = element('label', '', `${spec.name}（${spec.minimum}–${spec.maximum}）`); labelNode.htmlFor = field.id; const box = element('div'); box.append(labelNode, field); byId('inputs').append(box); } }
function renderSourceView() {
  const layer = byId('annotation-layer').value;
  const evidence = layer === 'all' ? Object.values(analysis.projection.layers).flat() : (analysis.projection.layers[layer] || []);
  renderSource(byId('structure'), analysis.graph.documents, analysis.projection.steps, selectSteps, evidence, chooseAnchor, analysis.presentation);
  renderStructure(byId('structure'), analysis.projection, selectSteps, selectFrame, true);
}
function consume(next) {
  const referenceOnly = !next.graph;
  const display = referenceOnly ? next.reference_analysis : next;
  if (!display?.graph) throw new Error('当前会话需要重新核验；暂时没有可展示的程序图。');
  analysis = { ...next, graph: display.graph, projection: { ...display.projection, presentation: next.presentation }, stages: display.stages, referenceOnly };
  if (referenceOnly) {
    analysis.projection = { ...analysis.projection, review_queue: { ...display.projection.review_queue,
      items: [...next.projection.review_queue.items, ...display.projection.review_queue.items] } };
    analysis.stages = [...next.stages, ...display.stages.map(stage => ({ ...stage, id: `reference-${stage.id}`, label: `自动参考：${stage.label}` }))];
  } else saveSession(next.procedure.id, next.session, next.branch_id);
  selectedAnchor = null;
  byId('selected-anchor').textContent = '先从原文、结构或问题选择一个 source span。';
  byId('scope').textContent = next.procedure.scope_note;
  const branchSelect = byId('branch-select'); branchSelect.replaceChildren();
  for (const branch of next.session.branches) branchSelect.add(new Option(branch.id, branch.id, false, branch.id === next.branch_id));
  branchSelect.value = next.branch_id;
  renderStages(); renderSourceView(); renderGraph(byId('graph'), analysis.projection, selectNode, selectQuestion);
  byId('relation-summary').textContent = '选择原文或操作，查看输入量 → 操作 → 输出量。';
  byId('graph-summary').textContent = next.presentation.graph_text;
  byId('graph-raw').textContent = json(display.graph); byId('selection-detail').replaceChildren(); byId('selection-status').textContent = '选择原文、步骤、图节点或问题，查看 typed relationships。';
  byId('session-status').textContent = next.presentation.session_text;
  showIssues(); renderQuestions(); showControls(); showDefinitions(); showHistory(); showInputs(); showCandidateOptions(); byId('analysis').hidden = false;
  byId('status').textContent = next.presentation.status_text;
  busy(false);
}
async function loadAnalysis() {
  const procedureId = byId('procedure').value; const revision = ++requestRevision; busy(true); byId('status').textContent = '正在调用 reviewed compiler…';
  try { const saved = loadSession(procedureId); const next = saved ? await request('api/adjudication/compile', { procedure_id: procedureId, session: saved.session, branch_id: saved.branch_id }) : await request(`api/adjudication/${encodeURIComponent(procedureId)}`); if (revision !== requestRevision) return; consume(next); } catch (error) { if (revision === requestRevision) byId('status').textContent = `分析未完成；已保留本地 session：${error.message}`; } finally { if (revision === requestRevision) busy(false); }
}
async function applyDecision(row) {
  if (analysis?.referenceOnly) throw new Error('旧 session 待重验；自动参考为只读。');
  if (!selectedAnchor && !row.targets?.length) throw new Error('请先选择 source span'); const revision = ++requestRevision; busy(true); byId('session-status').textContent = '正在应用 decision 并重新编译…';
  try { const next = await request('api/adjudication/decision', { procedure_id: analysis.procedure.id, session: analysis.session, decision: row, branch_id: analysis.branch_id }); if (revision === requestRevision) consume(next); } catch (error) { if (revision === requestRevision) byId('session-status').textContent = `Decision rejected: ${error.message}`; } finally { if (revision === requestRevision) busy(false); }
}
function currentCandidate() { const value = byId('candidate-select').value; if (!value) throw new Error('当前范围没有可选 candidate'); return value; }
function frameAnchor(selectId) { return analysis.projection.frames.find(row => row.id === byId(selectId).value)?.source_spans?.[0]; }

byId('procedure').addEventListener('change', () => { selectedAnchor = null; loadAnalysis(); }); byId('analyze').addEventListener('click', loadAnalysis); byId('annotation-layer').addEventListener('change', renderSourceView);
byId('source').addEventListener('mouseup', () => { const range = selectionAnchor(byId('source')); if (range) { chooseAnchor(range); window.getSelection().removeAllRanges(); } });
byId('branch-select').addEventListener('change', async () => { if (!analysis) return; busy(true); try { consume(await request('api/adjudication/compile', { procedure_id: analysis.procedure.id, session: analysis.session, branch_id: byId('branch-select').value })); } catch (error) { byId('session-status').textContent = `Branch load rejected: ${error.message}`; } finally { busy(false); } });
byId('select-candidate').addEventListener('click', () => applyDecision(makeDecision('select_candidate', [selectedAnchor], { selected_candidate_id: currentCandidate(), candidate_set_complete: true })));
byId('reject-candidate').addEventListener('click', () => applyDecision(makeDecision('reject_candidate', [selectedAnchor], { candidate_id: currentCandidate() })));
byId('resegment').addEventListener('click', () => { const split = Number(byId('split-at').value); if (!Number.isInteger(split) || split <= selectedAnchor.start || split >= selectedAnchor.end) throw new Error('split 必须在当前 source span 内'); const doc = documentFor(selectedAnchor); applyDecision(makeDecision('resegment', [selectedAnchor], { segments: [anchorFor(doc, selectedAnchor.start, split), anchorFor(doc, split, selectedAnchor.end)] })); });
byId('assemble-known').addEventListener('click', () => { const kind = byId('manual-operation').value; const slots = kind === 'load' ? { value: { ref_kind: 'source_anchor', anchor: selectedAnchor } } : { label: { ref_kind: 'source_anchor', anchor: selectedAnchor } }; applyDecision(makeDecision('assemble_known_structure', [selectedAnchor], { replace_automatic: true, candidates: [{ kind, slots }] }, 'assemble existing registry type')); });
byId('apply-lexical-role').addEventListener('click', () => applyDecision(makeDecision('set_lexical_role', [selectedAnchor], { contract_version: '1.0', grammatical_role: byId('lexical-role').value }, 'local occurrence grammar review')));
byId('mark-unresolved').addEventListener('click', () => applyDecision(makeDecision('defer', [selectedAnchor], { unresolved: true }, 'retain unresolved'))); byId('request-extension').addEventListener('click', () => applyDecision(makeDecision('defer', [selectedAnchor], { schema_extension_required: true }, 'existing registry cannot express this structure')));
byId('apply-binding').addEventListener('click', () => applyDecision(makeDecision('bind_value', [selectedAnchor], { consumer_definition_anchor: frameAnchor('binding-consumer'), producer_definition_anchor: frameAnchor('binding-producer'), formal: byId('binding-formal').value, output_port: byId('binding-port').value })));
byId('apply-scope').addEventListener('click', () => { const definition = frameAnchor('scope-definition'); const base = frameAnchor('scope-base'); if (!definition) throw new Error('请选择要修改的 procedure 或 stage'); applyDecision(makeDecision('set_scope', [selectedAnchor], { definition_anchor: definition, ...(base ? { query_base_anchor: base } : {}) })); }); byId('apply-profile').addEventListener('click', () => applyDecision(makeDecision('select_profile', [selectedAnchor], { profile_id: byId('profile-select').value })));
byId('attach-context').addEventListener('click', () => { const doc = analysis.graph.documents.find(row => row.doc_id === byId('context-select').value); applyDecision(makeDecision('attach_context', [selectedAnchor], { document: doc })); });
byId('declare-parameter').addEventListener('click', () => applyDecision(makeDecision('declare_parameter', [selectedAnchor], { name: byId('parameter-name').value, unit: byId('parameter-unit').value, root_input: true, role: 'root_input', evidence_basis: 'scholarship' })));
byId('create-branch').addEventListener('click', async () => { const branch = byId('branch-name').value.trim(); if (!branch) return; busy(true); try { consume(await request('api/adjudication/branch', { procedure_id: analysis.procedure.id, session: analysis.session, branch_id: branch, from_branch: analysis.branch_id })); } catch (error) { byId('session-status').textContent = `Branch rejected: ${error.message}`; } finally { busy(false); } });
byId('export-session').addEventListener('click', () => { const blob = new Blob([exportSession(analysis.procedure.id, analysis.session, analysis.branch_id)], { type: 'application/json' }); const link = document.createElement('a'); link.href = URL.createObjectURL(blob); link.download = `${analysis.procedure.id}-${analysis.branch_id}-session.json`; link.click(); setTimeout(() => URL.revokeObjectURL(link.href), 0); });
byId('import-session').addEventListener('change', async event => { const file = event.target.files[0]; if (!file || !analysis) return; try { const saved = importSession(await file.text(), analysis.procedure.id); consume(await request('api/adjudication/compile', { procedure_id: analysis.procedure.id, session: saved.session, branch_id: saved.branch_id })); } catch (error) { byId('session-status').textContent = `Import rejected: ${error.message}`; } });
byId('execute-form').addEventListener('submit', async event => { event.preventDefault(); if (!analysis) return; busy(true); byId('execution-result').hidden = true; try { const inputs = {}; for (const field of byId('inputs').querySelectorAll('input')) { const text = field.value.trim(); if (text) { if (!/^\d+$/.test(text) || !Number.isSafeInteger(Number(text))) throw new Error(`${field.name} 请输入整数`); inputs[field.name] = Number(text); } } const result = await request('api/adjudication/execute', { procedure_id: analysis.procedure.id, session: analysis.session, branch_id: analysis.branch_id, inputs }); byId('execution-status').textContent = result.presentation.session_text; byId('outputs').textContent = result.presentation.execution_text; byId('execution-raw').textContent = json(result.execution); byId('execution-result').hidden = false; } catch (error) { byId('execution-status').textContent = `数值验证未完成：${error.message}`; } finally { busy(false); } });

try { const response = await request('api/procedures'); for (const procedure of response.procedures) byId('procedure').add(new Option(procedure.title, procedure.id)); if (!response.procedures.length) throw new Error('没有已登记的 procedure'); await loadAnalysis(); } catch (error) { byId('status').textContent = `无法载入：${error.message}`; }
