// Stateless rendering of the researcher projection; no page state or compiler.
export const pretty = value => value == null ? '未记录' : typeof value === 'object' ? JSON.stringify(value) : String(value);
const names = {
  Heading: '过程标题', Load: '置入', Multiply: '相乘', DivMod: '整除与余数',
  Name: '命名', NameRemainder: '命名余数', Threshold: '阈值判断', Judgment: '判断结果', Declaration: '参数声明',
  input: '外部输入', load: '置入', literal: '字面量', subtract: '相减', add: '相加',
  multiply: '相乘', divmod: '整除与余数', alias: '命名', threshold: '阈值判断', parameter: '参数',
};
export const label = kind => names[kind] ? `${names[kind]} · ${kind}` : kind;
export function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text != null) node.textContent = text;
  return node;
}
export function action(text, onClick) {
  const button = element('button', 'object-select', text);
  button.type = 'button';
  button.addEventListener('click', onClick);
  return button;
}

export function renderStructure(container, projection, onStep, onFrame) {
  container.replaceChildren();
  const frames = new Map(projection.frames.map(f => [f.id, f]));
  const steps = new Map(projection.steps.map(s => [s.id, s]));
  const shown = new Set();
  function stepNode(step, order) {
    shown.add(step.id);
    const card = element('li', 'entry-card research-object');
    card.dataset.stepId = step.id;
    card.append(action(`${order}. ${label(step.kind)} — ${step.surface}`, () => onStep([step.id])));
    card.append(element('p', 'entry-card-note', `${step.event_ids.length ? step.event_ids.join(' · ') : '无独立 graph event'}${step.issue_ids.length ? ` · ${step.issue_ids.length} 项结构提示` : ''}`));
    return card;
  }
  function frameNode(frame, ancestors = new Set()) {
    if (ancestors.has(frame.id)) return element('p', 'entry-card-note', `循环引用：${frame.id}`);
    const next = new Set([...ancestors, frame.id]);
    const box = element('section', 'research-object');
    box.dataset.frameId = frame.id;
    box.append(action(`${frame.kind === 'QueryDef' ? 'Query / stage' : frame.kind} · ${frame.label}`, () => onFrame(frame.id)));
    box.append(element('p', 'entry-card-note', `${frame.source_role || 'source'}${frame.base_ref ? ` · base: ${frame.base_ref}` : ''}`));
    const list = element('ol', 'research-tree');
    let order = 0;
    for (const item of frame.body) {
      if (item.type === 'frame' && frames.has(item.id)) {
        const li = element('li'); li.append(frameNode(frames.get(item.id), next)); list.append(li);
      } else if (steps.has(item.id)) list.append(stepNode(steps.get(item.id), ++order));
    }
    box.append(list);
    return box;
  }
  for (const frame of projection.frames.filter(f => !f.parent || !frames.has(f.parent))) container.append(frameNode(frame));
  const orphaned = projection.steps.filter(s => !shown.has(s.id));
  if (orphaned.length) {
    container.append(element('h3', 'entry-card-title', '未归入 procedure 的语法节点'));
    const list = element('ol', 'research-tree');
    orphaned.forEach((step, i) => list.append(stepNode(step, i + 1)));
    container.append(list);
  }
}

function svgElement(tag, attributes = {}, text) {
  const node = document.createElementNS('http://www.w3.org/2000/svg', tag);
  for (const [key, value] of Object.entries(attributes)) node.setAttribute(key, value);
  if (text != null) node.textContent = text;
  return node;
}

export function renderGraph(container, projection, onNode) {
  container.replaceChildren();
  const nodes = projection.nodes;
  const svg = svgElement('svg', { class: 'research-graph', viewBox: `0 0 330 ${Math.max(100, nodes.length * 80 + 20)}`, role: 'group', 'aria-label': 'Event dependency graph' });
  const defs = svgElement('defs');
  const marker = svgElement('marker', { id: 'procedure-edge-arrow', viewBox: '0 0 10 10', refX: 9, refY: 5, markerWidth: 6, markerHeight: 6, orient: 'auto' });
  marker.append(svgElement('path', { d: 'M 0 0 L 10 5 L 0 10 z' })); defs.append(marker); svg.append(defs);
  const positions = new Map(nodes.map((n, i) => [n.id, i * 80 + 39]));
  projection.edges.forEach((edge, i) => {
    if (!positions.has(edge.producer) || !positions.has(edge.consumer)) return;
    const a = positions.get(edge.producer), b = positions.get(edge.consumer), gutter = 12 + i % 5 * 10;
    const path = svgElement('path', { class: 'graph-edge', d: `M 90 ${a} C ${gutter} ${a}, ${gutter} ${b}, 90 ${b}`,
      'marker-end': 'url(#procedure-edge-arrow)', 'data-producer': edge.producer, 'data-consumer': edge.consumer });
    path.append(svgElement('title', {}, `${edge.producer}.${edge.output_port} → ${edge.value_id} → ${edge.consumer}.${edge.input_port}`));
    svg.append(path);
  });
  nodes.forEach(node => {
    const y = positions.get(node.id) - 29;
    const group = svgElement('g', { 'data-node-id': node.id, role: 'button', tabindex: 0, 'aria-pressed': 'false', 'aria-label': `${node.id} ${label(node.kind)}` });
    group.append(svgElement('rect', { x: 90, y, width: 232, height: 58 }));
    group.append(svgElement('text', { x: 100, y: y + 22 }, label(node.kind)));
    group.append(svgElement('text', { x: 100, y: y + 43, class: 'graph-node-id' }, `${node.id} → ${Object.entries(node.writes || {}).map(([p, v]) => `${p}:${v}`).join(' / ')}`));
    group.addEventListener('click', () => onNode(node.id));
    group.addEventListener('keydown', event => {
      if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); onNode(node.id); }
    });
    svg.append(group);
  });
  container.append(svg);
}

export function markObjects(container, attribute, ids) {
  for (const node of container.querySelectorAll(`[${attribute}]`)) {
    const selected = ids.has(node.getAttribute(attribute));
    node.dataset.selected = String(selected);
    if (node.getAttribute('role') === 'button') node.setAttribute('aria-pressed', String(selected));
    else node.querySelector('.object-select')?.setAttribute('aria-pressed', String(selected));
  }
}

export function renderRelationships(container, projection, nodeIds, stepIds, onNode) {
  container.replaceChildren();
  const values = new Map(projection.quantities.map(v => [v.id, v]));
  const available = new Set(projection.nodes.map(n => n.id));
  const selectedSteps = projection.steps.filter(s => stepIds.has(s.id));
  for (const step of selectedSteps) {
    const slots = Object.entries(step.slots).map(([role, slot]) => `${role} = ${slot.surface || '省略项'} [${slot.node_id}]`).join(' · ');
    container.append(element('p', 'entry-card-row', `${step.id} · ${label(step.kind)}${slots ? ` · ${slots}` : ''}`));
  }
  for (const node of projection.nodes.filter(n => nodeIds.has(n.id))) {
    const card = element('article', 'entry-card');
    card.append(element('h3', 'entry-card-title', `${node.id} · ${label(node.kind)}`));
    const list = element('dl', 'match-detail-list research-properties');
    const row = (name, text) => list.append(element('dt', '', name), element('dd', '', text));
    row('Scope', Object.entries(node.scope || {}).map(([k, v]) => `${k}: ${v}`).join(' · ') || '未记录');
    row('Control / attributes', Object.entries(node.attributes || {}).filter(([k]) => k !== 'quantity_transition').map(([k, v]) => `${k}: ${pretty(v)}`).join(' · ') || '未记录');
    row('Order', `source/text ${pretty(node.text_order)} · dependency ${pretty(node.dependency_order)}`);
    row('IR / source link', selectedSteps.flatMap(s => s.graph_links.filter(l => l.event_id === node.id).map(l => `${s.id}: ${l.basis}`)).join(' · ') || '未记录');
    card.append(list);
    const wrapper = element('div', 'research-table-wrap');
    const table = element('table', 'research-table');
    const head = element('thead'); const header = element('tr');
    for (const title of ['Direction / slot', 'Quantity', 'Role / kind', 'Producer.port', 'Unit / scale', 'Status']) header.append(element('th', '', title));
    head.append(header); table.append(head);
    const body = element('tbody');
    for (const [direction, ports] of [['Input', node.reads], ['Output', node.writes]]) {
      for (const [port, ident] of Object.entries(ports || {})) {
        const value = values.get(ident) || { id: ident };
        const tr = element('tr');
        tr.append(element('td', '', `${direction} · ${port}`));
        tr.append(element('td', '', `${value.id}${value.labels?.length ? ` · ${value.labels.join(' / ')}` : ''}`));
        tr.append(element('td', '', `${pretty(value.role)} / ${pretty(value.quantity_kind)}`));
        const producer = element('td');
        const producerLabel = `${pretty(value.producer)}.${pretty(value.output_port)}`;
        producer.append(available.has(value.producer) ? action(producerLabel, () => onNode(value.producer)) : document.createTextNode(producerLabel));
        if (value.origin_producer) producer.append(element('p', 'entry-card-note', `origin: ${value.origin_producer}.${value.origin_port}`));
        tr.append(producer, element('td', '', `${pretty(value.unit)} / ${pretty(value.scale)}`), element('td', '', pretty(value.resolution_status)));
        body.append(tr);
      }
    }
    table.append(body); wrapper.append(table); card.append(wrapper);
    const dependencies = projection.edges.filter(e => e.consumer === node.id || e.producer === node.id);
    card.append(element('p', 'entry-card-row', `Dependencies: ${dependencies.map(e => `${e.producer}.${e.output_port} → ${e.value_id} → ${e.consumer}.${e.input_port}`).join(' · ') || '无数据依赖边'}`));
    container.append(card);
  }
  if (!nodeIds.size) container.append(element('p', 'entry-card-note', '此语法结构没有独立 graph event；原文与结构仍可定位。'));
}
