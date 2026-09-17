// Stateless rendering of the researcher projection; no page state or compiler.
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
    const text = projection.presentation.steps[step.id];
    card.append(action(`${order}. ${text.label} — ${step.surface}`, () => onStep([step.id])));
    card.append(element('p', 'entry-card-note', `${text.events} · ${text.issues}`));
    return card;
  }
  function frameNode(frame, ancestors = new Set()) {
    if (ancestors.has(frame.id)) return element('p', 'entry-card-note', '范围存在循环引用');
    const next = new Set([...ancestors, frame.id]);
    const box = element('section', 'research-object');
    box.dataset.frameId = frame.id;
    const text = projection.presentation.frames[frame.id];
    box.append(action(text.label, () => onFrame(frame.id)));
    box.append(element('p', 'entry-card-note', `${text.source_role} · ${text.base}`));
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
    path.append(svgElement('title', {}, projection.presentation.edges[i].text));
    svg.append(path);
  });
  nodes.forEach(node => {
    const text = projection.presentation.nodes[node.id];
    const y = positions.get(node.id) - 29;
    const group = svgElement('g', { 'data-node-id': node.id, role: 'button', tabindex: 0, 'aria-pressed': 'false', 'aria-label': text.label });
    group.append(svgElement('rect', { x: 90, y, width: 232, height: 58 }));
    group.append(svgElement('text', { x: 100, y: y + 22 }, text.label));
    group.append(svgElement('text', { x: 100, y: y + 43, class: 'graph-node-id' }, text.outputs));
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
  const available = new Set(projection.nodes.map(n => n.id));
  const selectedSteps = projection.steps.filter(s => stepIds.has(s.id));
  for (const step of selectedSteps) {
    const text = projection.presentation.steps[step.id];
    container.append(element('p', 'entry-card-row', `${text.label} · ${text.slots}`));
  }
  for (const node of projection.nodes.filter(n => nodeIds.has(n.id))) {
    const text = projection.presentation.nodes[node.id];
    const card = element('article', 'entry-card');
    card.append(element('h3', 'entry-card-title', text.label));
    const list = element('dl', 'match-detail-list research-properties');
    const row = (name, text) => list.append(element('dt', '', name), element('dd', '', text));
    row('原文证据', text.source);
    row('证据类别', text.evidence);
    row('步骤次序', text.order);
    row('所属范围', text.scope);
    row('控制属性', text.control);
    card.append(list);
    const wrapper = element('div', 'research-table-wrap');
    const table = element('table', 'research-table');
    const head = element('thead'); const header = element('tr');
    for (const title of ['方向／操作对象', '数量', '角色／类型', '生产步骤与端口', '单位／尺度', '状态']) header.append(element('th', '', title));
    head.append(header); table.append(head);
    const body = element('tbody');
    for (const value of text.rows) {
        const tr = element('tr');
        tr.append(element('td', '', value.direction));
        tr.append(element('td', '', value.name));
        tr.append(element('td', '', value.role));
        const producer = element('td');
        producer.append(available.has(value.producer_id) ? action(value.producer, () => onNode(value.producer_id)) : document.createTextNode(value.producer));
        tr.append(producer, element('td', '', value.unit_scale), element('td', '', value.status));
        body.append(tr);
    }
    table.append(body); wrapper.append(table); card.append(wrapper);
    card.append(element('p', 'entry-card-row', `依赖：${text.dependencies.join(' · ') || '未记录数据依赖边'}`));
    container.append(card);
  }
  if (!nodeIds.size) container.append(element('p', 'entry-card-note', '此语法结构没有独立 graph event；原文与结构仍可定位。'));
}
