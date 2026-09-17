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

export function renderStructure(container, projection, onStep, onFrame, annotateSources = false) {
  if (!annotateSources) container.replaceChildren();
  const frames = new Map(projection.frames.map(f => [f.id, f]));
  const steps = new Map(projection.steps.map(s => [s.id, s]));
  const shown = new Set();
  function stepNode(step, order) {
    shown.add(step.id);
    const card = element('li', 'entry-card research-object');
    card.dataset.stepId = step.id;
    const text = projection.presentation.steps[step.id];
    const construction = projection.presentation.candidates.find(c => c.id === step.id);
    const button = action(`${order}. ${step.surface} · ${construction?.label || text.label}`, () => onStep([step.id]));
    button.title = `${text.events} · ${text.issues}`;
    card.append(button);
    return card;
  }
  function frameNode(frame, ancestors = new Set()) {
    if (ancestors.has(frame.id)) return element('p', 'entry-card-note', '范围存在循环引用');
    const next = new Set([...ancestors, frame.id]);
    const box = element('section', 'research-object research-annotations');
    box.dataset.frameId = frame.id;
    const text = projection.presentation.frames[frame.id];
    box.append(action(text.label, () => onFrame(frame.id)));
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
  const owner = spans => annotateSources ? [...container.querySelectorAll('[data-source-doc]')].find(card => spans?.some(span => span.doc_id === card.dataset.sourceDoc)) || container : container;
  for (const frame of projection.frames.filter(f => !f.parent || !frames.has(f.parent))) owner(frame.source_spans).append(frameNode(frame));
  const orphaned = projection.steps.filter(s => !shown.has(s.id));
  if (orphaned.length) {
    container.append(element('h3', 'entry-card-title', '未归入 procedure 的语法节点'));
    const list = element('ol', 'research-tree research-annotations');
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

export function renderGraph(container, projection, onNode, onQuestion = () => {}) {
  container.replaceChildren();
  const nodes = projection.nodes;
  // Three visual lanes use recorded producers/ports, not a second evaluator.
  // Source events share a glyph with their output quantity; every event/value
  // retains its own address. Right-lane quantities may feed later operations.
  const sourceNodes = nodes.filter(n => ['input', 'parameter', 'literal'].includes(n.kind)
    && projection.quantities.filter(v => v.producer === n.id).length === 1);
  const sourceIds = new Set(sourceNodes.map(n => n.id));
  const operations = nodes.filter(n => !sourceIds.has(n.id));
  const sourceValues = projection.quantities.filter(v => sourceIds.has(v.producer));
  const derivedValues = projection.quantities.filter(v => !sourceIds.has(v.producer));
  const rowHeight = 42, top = 30, width = 210;
  const height = Math.max(sourceValues.length, operations.length, derivedValues.length, 2) * rowHeight + top;
  const svg = svgElement('svg', { class: 'research-graph', viewBox: `0 0 900 ${height}`, role: 'group', 'aria-label': 'Quantity and operation graph' });
  for (const [x, text] of [[20, '来源量'], [345, '操作'], [670, '派生量／输出']]) svg.append(svgElement('text', { x, y: 18 }, text));
  const defs = svgElement('defs');
  const marker = svgElement('marker', { id: 'procedure-edge-arrow', viewBox: '0 0 10 10', refX: 9, refY: 5, markerWidth: 6, markerHeight: 6, orient: 'auto' });
  marker.append(svgElement('path', { d: 'M 0 0 L 10 5 L 0 10 z' })); defs.append(marker); svg.append(defs);
  const eventPositions = new Map(operations.map((n, i) => [n.id, { x: 345, y: top + i * rowHeight }]));
  const valuePositions = new Map([...sourceValues.map((v, i) => [v.id, { x: 20, y: top + i * rowHeight }]), ...derivedValues.map((v, i) => [v.id, { x: 670, y: top + i * rowHeight }])]);
  const connect = (from, to, title, attrs) => {
    const rightward = from.x < to.x;
    const x1 = from.x + (rightward ? width : 0), x2 = to.x + (rightward ? 0 : width);
    const y1 = from.y + 18, y2 = to.y + 18, mid = (x1 + x2) / 2;
    const path = svgElement('path', { class: 'graph-edge', d: `M ${x1} ${y1} C ${mid} ${y1}, ${mid} ${y2}, ${x2} ${y2}`, 'marker-end': 'url(#procedure-edge-arrow)', ...attrs });
    path.append(svgElement('title', {}, title)); svg.append(path);
  };
  projection.edges.forEach((edge, i) => {
    const from = valuePositions.get(edge.value_id), to = eventPositions.get(edge.consumer);
    if (from && to) connect(from, to, projection.presentation.edges[i].text, { 'data-producer': edge.producer, 'data-consumer': edge.consumer });
  });
  for (const value of derivedValues) {
    const from = eventPositions.get(value.producer), to = valuePositions.get(value.id);
    if (from && to) connect(from, to, projection.presentation.quantities[value.id].role, { 'data-producer': value.producer });
  }
  const glyph = (position, title, subtitle, attrs, select) => {
    const { x, y } = position;
    const group = svgElement('g', { role: 'button', tabindex: 0, 'aria-pressed': 'false', 'aria-label': `${title} · ${subtitle}`, ...attrs });
    group.append(svgElement('rect', { x, y, width, height: 38 }));
    group.append(svgElement('text', { x: x + 8, y: y + 16 }, title));
    group.append(svgElement('text', { x: x + 8, y: y + 31, class: 'graph-node-note' }, subtitle));
    group.append(svgElement('title', {}, `${title} · ${subtitle}`));
    group.addEventListener('click', select);
    group.addEventListener('keydown', event => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); select(); } });
    svg.append(group);
  };
  operations.forEach(node => {
    const text = projection.presentation.nodes[node.id];
    glyph(eventPositions.get(node.id), text.operation, text.source, { 'data-node-id': node.id, 'data-kind': 'operation' }, () => onNode(node.id));
  });
  const consumed = new Set(projection.edges.map(e => e.value_id));
  for (const value of projection.quantities) {
    const text = projection.presentation.quantities[value.id];
    const source = sourceIds.has(value.producer);
    const kind = source && ['parameter', 'external_input', 'root_input', 'missing_upstream'].includes(value.role) ? 'parameter-input' : source || consumed.has(value.id) ? 'value' : 'result';
    glyph(valuePositions.get(value.id), text.name, `${text.role} · ${text.unit}`, { 'data-value-id': value.id, 'data-kind': kind,
      ...(source ? { 'data-node-id': value.producer } : {}), 'data-producer-id': value.producer,
      'data-unresolved': String(value.resolution_status !== 'resolved') }, () => onNode(value.producer));
  }
  container.append(svg);
  const holes = element('div', 'research-annotations');
  const locations = new Map();
  for (const question of projection.presentation.questions) {
    for (const span of question.source_anchors?.length ? question.source_anchors : [null]) {
      const key = span ? JSON.stringify([span.doc_id, span.reading_id, span.start, span.end]) : question.id;
      if (!locations.has(key)) locations.set(key, { span, questions: [] });
      locations.get(key).questions.push(question);
    }
  }
  for (const { span, questions } of locations.values()) {
    const badge = action(span?.quote ? `待审「${span.quote}」` : questions[0].label, () => onQuestion(questions[0], span));
    badge.dataset.kind = 'unresolved'; badge.dataset.questionId = questions[0].id;
    badge.title = [...new Set(questions.map(q => q.label))].join(' · '); holes.append(badge);
  }
  container.append(holes);
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
