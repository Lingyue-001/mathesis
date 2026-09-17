import { renderSource, markSourceSelection, revealInPanel, selectionAnchor } from './ui/source-links.js';
import { renderStructure, renderGraph, renderRelationships, markObjects, element, action, pretty } from './ui/procedure-view.js';
import { clearSession, exportSession, importSession, loadSession, saveSession } from './ui/adjudication-session-store.js';

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
  if (!response.ok) throw new Error(value.error || `HTTP ${response.status}`);
  return value;
}
function busy(value) { for (const node of document.querySelectorAll('.procedure-workbench button, .procedure-workbench select, .procedure-workbench input')) if (node.id !== 'import-session') node.disabled = value; }
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
  for (const id of ['source', 'structure', 'graph']) revealInPanel(byId(id), byId(id).querySelector('[data-selected="true"]:not(.graph-edge)'));
}
function selectSteps(ids) {
  const steps = analysis.projection.steps.filter(step => ids.includes(step.id));
  select(ids, steps.flatMap(step => step.event_ids), steps.flatMap(step => step.source_spans), steps.map(step => step.surface).join(' / '));
  if (steps[0]?.source_spans[0]) chooseAnchor(steps[0].source_spans[0]);
}
function selectNode(id) { const node = analysis.projection.nodes.find(item => item.id === id); if (node) { select(node.step_ids, [id], node.source_spans || [], `${node.id} · ${node.kind}`); if (node.source_spans?.[0]) chooseAnchor(node.source_spans[0]); } }
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
  for (const stage of analysis.stages) { const row = element('details', 'research-stage'); row.dataset.stageId = stage.id; row.append(element('summary', '', `${stage.label} · ${stage.status}`), element('p', 'entry-card-note', `Inputs: ${stage.inputs.join(' · ') || '—'} · Rules: ${stage.rules.join(' · ') || '—'}`), element('pre', '', json(stage.artifacts))); box.append(row); }
}
function renderQuestions() {
  const box = byId('review-queue'); box.replaceChildren(); const questions = analysis.projection.review_queue.items;
  if (!questions.length) box.append(element('p', 'entry-card-note', '当前编译没有 review question。'));
  for (const question of questions) {
    const card = element('article', 'entry-card'); card.dataset.reviewId = question.id;
    card.append(action(`${question.kind} · ${question.severity}`, () => { if (question.source_anchors?.[0]) chooseAnchor(question.source_anchors[0]); const steps = analysis.projection.steps.filter(step => question.source_anchors?.some(anchor => step.source_spans.some(span => span.doc_id === anchor.doc_id && span.start < anchor.end && anchor.start < span.end))); if (steps.length) selectSteps(steps.map(step => step.id)); }));
    card.append(element('p', 'entry-card-note', `原因：${pretty(question.reason)} · 允许：${question.suggested_actions.join(' / ')}`));
    card.append(element('p', 'entry-card-note', `受影响：${question.affected_outputs.join(' / ') || '未记录'} · 候选：${question.candidate_options.map(row => `${row.kind} (${row.production_id || 'reviewed'})`).join(' / ') || '无合法候选'}`)); box.append(card);
  }
}
function showCandidateOptions() {
  const selectBox = byId('candidate-select'); selectBox.replaceChildren();
  const candidates = analysis?.graph?.construction_candidates || [];
  const matching = !selectedAnchor ? [] : candidates.filter(row => row.source_spans?.some(span => span.doc_id === selectedAnchor.doc_id && span.start < selectedAnchor.end && selectedAnchor.start < span.end));
  for (const row of matching) selectBox.add(new Option(`${row.kind} · ${row.text || row.surface || row.node_id} · ${row.production_id || 'rule'}`, row.node_id));
  if (!matching.length) selectBox.add(new Option('No candidate at selected span', ''));
}
function showIssues() { const box = byId('analysis-issues'); box.replaceChildren(); for (const issue of analysis.projection.issues) { const item = element('details', 'research-disclosure'); item.append(element('summary', '', `${issue.origin} · ${issue.kind}`), element('pre', '', json(issue))); box.append(item); } }
function showDefinitions() {
  for (const id of ['binding-consumer', 'binding-producer']) byId(id).replaceChildren();
  for (const frame of analysis.projection.frames) if (frame.source_spans?.[0]) for (const id of ['binding-consumer', 'binding-producer']) byId(id).add(new Option(`${frame.label} · ${frame.id}`, frame.id));
  const contexts = byId('context-select'); contexts.replaceChildren();
  for (const doc of analysis.graph.documents.filter(doc => doc.category === 'context_documents')) contexts.add(new Option(`${doc.doc_id} · ${doc.text}`, doc.doc_id));
}
function showHistory() { const box = byId('decision-history'); box.replaceChildren(); for (const row of analysis.session.decisions) { const line = element('p', 'entry-card-row', `${row.revision}. ${row.action} · ${row.actor.type} · ${row.targets[0]?.quote || ''}`); if (row.action !== 'retract') line.append(action('Retract', () => applyDecision(makeDecision('retract', row.targets, { decision_id: row.decision_id }, `retract ${row.decision_id}`)))); box.append(line); } }
function showInputs() { byId('inputs').replaceChildren(); for (const [index, spec] of analysis.procedure.inputs.entries()) { const field = element('input'); field.type = 'text'; field.inputMode = 'numeric'; field.id = `input-${index}`; field.name = spec.name; const labelNode = element('label', '', `${spec.name}（${spec.minimum}–${spec.maximum}）`); labelNode.htmlFor = field.id; const box = element('div'); box.append(labelNode, field); byId('inputs').append(box); } }
function renderSourceView() { const layer = byId('annotation-layer').value; const evidence = layer === 'all' ? Object.values(analysis.projection.layers).flat() : (analysis.projection.layers[layer] || []); renderSource(byId('source'), analysis.graph.documents, analysis.projection.steps, selectSteps, evidence, chooseAnchor); }
function consume(next) {
  if (!next.graph) {
    byId('session-status').textContent = `Session requires revalidation: ${next.bundle?.replay?.status || 'stale_source'}`;
    return;
  }
  analysis = next; saveSession(next.procedure.id, next.session, next.branch_id); byId('scope').textContent = next.procedure.scope_note;
  const branchSelect = byId('branch-select'); branchSelect.replaceChildren();
  for (const branch of next.session.branches) branchSelect.add(new Option(branch.id, branch.id, false, branch.id === next.branch_id));
  branchSelect.value = next.branch_id;
  renderStages(); renderSourceView(); renderStructure(byId('structure'), next.projection, selectSteps, selectFrame); renderGraph(byId('graph'), next.projection, selectNode);
  byId('graph-summary').textContent = `${next.projection.nodes.length} events · ${next.projection.quantities.length} values · ${next.projection.edges.length} dependency edges · graph ${next.summary.graph_status}`;
  byId('graph-raw').textContent = json(next.graph); byId('selection-detail').replaceChildren(); byId('selection-status').textContent = '选择原文、步骤、图节点或问题，查看 typed relationships。';
  byId('session-status').textContent = `Branch ${next.branch_id} · review ${next.summary.review_status} · graph ${next.summary.graph_status} · execution ${next.summary.execution_status} · comparison ${next.summary.comparison_status}`;
  showIssues(); renderQuestions(); showDefinitions(); showHistory(); showInputs(); showCandidateOptions(); byId('analysis').hidden = false;
}
async function loadAnalysis() {
  const procedureId = byId('procedure').value; const revision = ++requestRevision; busy(true); byId('status').textContent = '正在调用 reviewed compiler…';
  try { const saved = loadSession(procedureId); let next; try { next = saved ? await request('api/adjudication/compile', { procedure_id: procedureId, session: saved.session, branch_id: saved.branch_id }) : await request(`api/adjudication/${encodeURIComponent(procedureId)}`); } catch (error) { if (!saved) throw error; clearSession(procedureId); next = await request(`api/adjudication/${encodeURIComponent(procedureId)}`); } if (revision !== requestRevision) return; consume(next); byId('status').textContent = `已载入 reviewed structure · ${next.projection.review_queue.items.length} 个当前问题`; } catch (error) { if (revision === requestRevision) byId('status').textContent = `分析未完成：${error.message}`; } finally { if (revision === requestRevision) busy(false); }
}
async function applyDecision(row) {
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
byId('apply-scope').addEventListener('click', () => applyDecision(makeDecision('set_scope', [selectedAnchor], { query_base: byId('scope-value').value }))); byId('apply-profile').addEventListener('click', () => applyDecision(makeDecision('select_profile', [selectedAnchor], { profile_id: byId('profile-select').value })));
byId('attach-context').addEventListener('click', () => { const doc = analysis.graph.documents.find(row => row.doc_id === byId('context-select').value); applyDecision(makeDecision('attach_context', [selectedAnchor], { document: doc })); });
byId('declare-parameter').addEventListener('click', () => applyDecision(makeDecision('declare_parameter', [selectedAnchor], { name: byId('parameter-name').value, unit: byId('parameter-unit').value, root_input: true, role: 'root_input', evidence_basis: 'scholarship' })));
byId('create-branch').addEventListener('click', async () => { const branch = byId('branch-name').value.trim(); if (!branch) return; busy(true); try { consume(await request('api/adjudication/branch', { procedure_id: analysis.procedure.id, session: analysis.session, branch_id: branch, from_branch: analysis.branch_id })); } catch (error) { byId('session-status').textContent = `Branch rejected: ${error.message}`; } finally { busy(false); } });
byId('export-session').addEventListener('click', () => { const blob = new Blob([exportSession(analysis.procedure.id, analysis.session, analysis.branch_id)], { type: 'application/json' }); const link = document.createElement('a'); link.href = URL.createObjectURL(blob); link.download = `${analysis.procedure.id}-${analysis.branch_id}-session.json`; link.click(); setTimeout(() => URL.revokeObjectURL(link.href), 0); });
byId('import-session').addEventListener('change', async event => { const file = event.target.files[0]; if (!file || !analysis) return; try { const saved = importSession(await file.text(), analysis.procedure.id); consume(await request('api/adjudication/compile', { procedure_id: analysis.procedure.id, session: saved.session, branch_id: saved.branch_id })); } catch (error) { byId('session-status').textContent = `Import rejected: ${error.message}`; } });
byId('execute-form').addEventListener('submit', async event => { event.preventDefault(); if (!analysis) return; busy(true); byId('execution-result').hidden = true; try { const inputs = {}; for (const field of byId('inputs').querySelectorAll('input')) { const text = field.value.trim(); if (text) { if (!/^\d+$/.test(text) || !Number.isSafeInteger(Number(text))) throw new Error(`${field.name} 请输入整数`); inputs[field.name] = Number(text); } } const result = await request('api/adjudication/execute', { procedure_id: analysis.procedure.id, session: analysis.session, branch_id: analysis.branch_id, inputs }); byId('execution-status').textContent = `Execution: ${result.summary.execution_status} · graph: ${result.summary.execution_graph}`; byId('outputs').textContent = json(result.execution.named_outputs); byId('execution-raw').textContent = json(result.execution); byId('execution-result').hidden = false; } catch (error) { byId('execution-status').textContent = `数值验证未完成：${error.message}`; } finally { busy(false); } });

try { const response = await request('api/procedures'); for (const procedure of response.procedures) byId('procedure').add(new Option(procedure.title, procedure.id)); if (!response.procedures.length) throw new Error('没有已登记的 procedure'); await loadAnalysis(); } catch (error) { byId('status').textContent = `无法载入：${error.message}`; }
