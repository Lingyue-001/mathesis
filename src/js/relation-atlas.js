const baseUrl = document.documentElement.dataset.baseurl || "/";
const withBase = (path) => `${baseUrl.replace(/\/?$/, "/")}${path.replace(/^\/+/, "")}`;

const TYPES = ["AUTHORITY", "KNOWLEDGE_OP", "ASTRO_TERM", "MOTION", "PARAMETER", "QUANTITY", "CALC_OP"];
const RELATION_LABELS = ["DEFINES", "HAS_VALUE", "HAS_PART", "UNDERGOES", "TAKES_OBJECT", "PERFORMS", "LEADS_TO", "LOCATES_AT"];
const RELATION_NAMES = {
  DEFINES: "Definition Relation",
  HAS_VALUE: "Parameter Definition",
  HAS_PART: "Component Relation",
  UNDERGOES: "Motion Predicate",
  TAKES_OBJECT: "Observed Object",
  PERFORMS: "Agent Action",
  LEADS_TO: "Derivation Relation",
  LOCATES_AT: "Locative Relation",
};

let data = [];
let terms = [];
let relations = [];
let steps = [];
let termByMention = new Map();
let chunksById = new Map();

const el = (selector) => document.querySelector(selector);
const els = (selector) => [...document.querySelectorAll(selector)];

function esc(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function shortId(id) {
  return String(id || "").replace("cullen:ch3:chunk:", "chunk");
}

function chunkNumber(id) {
  return String(id || "").match(/(\d{4})$/u)?.[1] || "";
}

function typeClass(type) {
  return `type-${String(type || "UNCLASSIFIED").replace(/[^\w-]/g, "_")}`;
}

function normalizeIndex(index) {
  data = (index.chunks || [])
    .filter((chunk) => chunk.annotation_source === "manual_breakdown")
    .map((chunk) => ({
      chunk_id: chunk.chunk_id,
      chunk_type: chunk.chunk_type,
      source_text_zh: chunk.source_text_zh || "",
      english_text: chunk.english_text || "",
      terms: (chunk.manual_terms || []).map((term, index) => ({
        ...term,
        mention_id: `${chunk.chunk_id}::term::${index}`,
        anchor: term.anchor || term.text,
        type: term.type || "UNCLASSIFIED",
        en: term.en || "",
      })),
      relations: (chunk.manual_relations || []).map((relation, index) => ({
        ...relation,
        relation_id: `${chunk.chunk_id}::relation::${index}`,
        anchor: relation.anchor || "",
      })),
      steps: chunk.manual_steps || [],
      motifs: chunk.motifs || [],
    }))
    .sort((a, b) => Number(chunkNumber(a.chunk_id)) - Number(chunkNumber(b.chunk_id)));

  terms = data.flatMap((chunk) => chunk.terms.map((term) => ({ ...term, chunk_id: chunk.chunk_id, chunk_type: chunk.chunk_type })));
  relations = flattenRelations();
  steps = data.flatMap((chunk) => chunk.steps.map((step) => ({ ...step, chunk_id: chunk.chunk_id, chunk_type: chunk.chunk_type })));
  termByMention = new Map(terms.map((term) => [term.mention_id, term]));
  chunksById = new Map(data.map((chunk) => [chunk.chunk_id, chunk]));
}

function flattenRelations() {
  const out = [];
  data.forEach((chunk) => {
    (chunk.relations || []).forEach((relation) => {
      const objects = Array.isArray(relation.object) ? relation.object : [relation.object];
      objects.forEach((object, index) => out.push({
        uid: `${relation.relation_id}::${index}`,
        chunk_id: chunk.chunk_id,
        chunk_type: chunk.chunk_type,
        subject: relation.subject,
        relation: relation.relation,
        object,
        anchor: relation.anchor || "",
      }));
    });
  });
  return out;
}

function initStats() {
  el("#relationStats").innerHTML = `
    <div class="relation-demo-stat"><strong>${esc(data.length)}</strong><span>annotated chunks</span></div>
    <div class="relation-demo-stat"><strong>${esc(terms.length)}</strong><span>terms</span></div>
    <div class="relation-demo-stat"><strong>${esc(relations.length)}</strong><span>relations</span></div>
    <div class="relation-demo-stat"><strong>${esc(steps.length)}</strong><span>procedure steps</span></div>
  `;
}

function initTabs() {
  els(".relation-demo-tab").forEach((button) => {
    button.addEventListener("click", () => switchView(button.dataset.view));
  });
}

function switchView(view) {
  els(".relation-demo-tab").forEach((button) => button.classList.toggle("active", button.dataset.view === view));
  els(".relation-demo-view").forEach((panel) => panel.classList.remove("active"));
  el(`#view-${view}`)?.classList.add("active");
}

function termForText(text) {
  return terms.find((term) => term.text === text)
    || terms.find((term) => String(text || "").includes(term.text) || String(term.text || "").includes(text));
}

function termLabel(text, options = {}) {
  const term = termForText(text);
  const en = options.en || term?.en || "";
  const suffix = en ? `<small>${esc(en)}</small>` : "";
  return `<span class="relation-term-label">${esc(text)}${suffix}</span>`;
}

function valueLabel(text) {
  return `<span class="relation-term-label">${esc(text)}</span>`;
}

function showInspector(item, kind = "intro") {
  const box = el("#relationInspector");
  if (!item) {
    box.innerHTML = `
      <h3>Inspector</h3>
      <p class="relation-demo-note">Click graph nodes, relation cards, steps, role dots, or term chips to inspect their source-backed fields.</p>
    `;
    return;
  }

  if (kind === "term") {
    const incoming = relations.filter((relation) => relation.object === item.text);
    const outgoing = relations.filter((relation) => relation.subject === item.text);
    const usedSteps = steps.filter((step) => [step.input, step.parameter, step.output].some((value) => String(value || "").includes(item.text)));
    box.innerHTML = `
      <h3>${esc(item.text)} <span class="relation-demo-tag ${typeClass(item.type)}">${esc(item.type)}</span></h3>
      <div class="relation-demo-note">${esc(item.en || "")}</div>
      <div class="relation-detail-block"><h4>Source</h4>
        <div class="relation-kv"><b>chunk</b><span>${esc(shortId(item.chunk_id))}</span></div>
        <div class="relation-kv"><b>anchor</b><span>${esc(item.anchor)}</span></div>
        <div class="relation-kv"><b>term id</b><span>${esc(item.term_id || "")}</span></div>
      </div>
      <div class="relation-detail-block"><h4>Incoming relations</h4>${incoming.length ? incoming.map(relationCard).join("") : `<p class="relation-empty">none</p>`}</div>
      <div class="relation-detail-block"><h4>Outgoing relations</h4>${outgoing.length ? outgoing.map(relationCard).join("") : `<p class="relation-empty">none</p>`}</div>
      <div class="relation-detail-block"><h4>Procedure uses</h4>${usedSteps.length ? usedSteps.map(stepCard).join("") : `<p class="relation-empty">none in annotated procedure steps</p>`}</div>
    `;
    return;
  }

  if (kind === "relation") {
    box.innerHTML = `
      <h3>${esc(RELATION_NAMES[item.relation] || item.relation)} <span class="relation-demo-tag">${esc(item.relation)}</span></h3>
      <div class="relation-detail-block"><h4>Visual sentence</h4>
        <p><b>${termLabel(item.subject)}</b> <span class="relation-demo-tag">${esc(item.relation)}</span> <b>${termLabel(item.object)}</b></p>
      </div>
      <div class="relation-detail-block"><h4>Evidence</h4>
        <div class="relation-kv"><b>chunk</b><span>${esc(shortId(item.chunk_id))}</span></div>
        <div class="relation-kv"><b>anchor</b><span>${esc(item.anchor || "not specified")}</span></div>
      </div>
    `;
    return;
  }

  if (kind === "step") {
    box.innerHTML = `
      <h3>Step ${esc(item.order)} <span class="relation-demo-tag type-CALC_OP">${esc(item.op)}</span></h3>
      <div class="relation-detail-block"><h4>Phrase</h4><p class="relation-inspector-phrase">${esc(item.phrase)}</p></div>
      <div class="relation-detail-block"><h4>Flow</h4>
        <div class="relation-kv"><b>input</b><span>${esc(item.input || "none")}</span></div>
        <div class="relation-kv"><b>parameter</b><span>${esc(item.parameter || "none")}</span></div>
        <div class="relation-kv"><b>output</b><span>${esc(item.output || "none")}</span></div>
        <div class="relation-kv"><b>chunk</b><span>${esc(shortId(item.chunk_id))}</span></div>
      </div>
    `;
    return;
  }

  box.innerHTML = `
    <h3>${esc(item.label)} <span class="relation-demo-tag">${esc(item.kind || "node")}</span></h3>
    <p class="relation-demo-note">${esc(item.note || "")}</p>
    <div class="relation-detail-block"><h4>Visual role</h4><p>${esc(item.visual || "")}</p></div>
    <div class="relation-detail-block"><h4>Evidence</h4><p>${esc(item.source || "")}</p></div>
  `;
}

function relationCard(relation) {
  return `<div class="relation-demo-card"><b>${termLabel(relation.subject)}</b> <span class="relation-demo-tag">${esc(relation.relation)}</span> ${termLabel(relation.object)}<div class="relation-demo-note">${esc(shortId(relation.chunk_id))}</div></div>`;
}

function stepCard(step) {
  return `<div class="relation-demo-card"><b>${esc(shortId(step.chunk_id))} · step ${esc(step.order)}</b><div>${esc(step.phrase)}</div><div class="relation-demo-note">${esc(step.input || "none")} -> ${esc(step.op)} / ${esc(step.parameter || "none")} -> ${esc(step.output || "none")}</div></div>`;
}

function buildBuConceptGraph() {
  const definition = relations.find((relation) => relation.relation === "DEFINES" && relation.object === "蔀");
  const parameters = ["蔀法", "蔀月", "蔀日"].map((name) => {
    const relation = relations.find((item) => item.relation === "HAS_VALUE" && item.subject === name);
    const term = termForText(name);
    return { name, value: relation?.object || "", en: term?.en || "", relation };
  });
  const contextTerms = [
    termForText("入蔀年"),
    termForText("入蔀積月"),
    termForText("所入蔀名"),
  ].filter(Boolean);
  const operationNodes = [
    steps.find((step) => step.op === "multiply" && step.parameter === "蔀日"),
    steps.find((step) => step.op === "fill_divide" && step.parameter === "蔀月"),
    steps.find((step) => step.op === "count" && String(step.parameter || "").includes("所入蔀名")),
  ].filter(Boolean);

  const nodes = [
    node("definition", definition?.subject || "同在日首", "definition condition", 60, 145, 155, 70, "#f7e5e8", "var(--relation-def)", "DEFINES", definition),
    node("concept", "蔀", "Obscuration", 285, 145, 140, 70, "#eef5fa", "var(--relation-astro)", "ASTRO_TERM", termForText("蔀")),
    ...parameters.map((param, index) => node(`param-${index}`, `${param.name} = ${param.value}`, param.en, 520, 60 + index * 85, 190, 62, "#fff1df", "var(--relation-param)", "PARAMETER", param.relation || termForText(param.name))),
    ...contextTerms.map((term, index) => node(`context-${index}`, term.text, term.en || "procedure context", 790, 58 + index * 87, 160, 58, index === 2 ? "#edf4ff" : "#f0edfb", index === 2 ? "var(--relation-loc)" : "var(--relation-quantity)", term.type, term)),
    ...operationNodes.map((step, index) => node(`op-${index}`, step.op, step.phrase, 1030, 112 + index * 82, 150, 58, "#fdebe8", "var(--relation-calc)", "CALC_OP", step)),
    node("result", "積月 / 小餘 / 大餘 / 朔日", "computed results", 1245, 182, 220, 82, "#f3effb", "var(--relation-quantity)", "QUANTITY", null),
  ];

  return {
    nodes,
    edges: [
      ["definition", "concept", "DEFINES"],
      ["concept", "param-0", "parameter family"],
      ["concept", "param-1", "parameter family"],
      ["concept", "param-2", "parameter family"],
      ["concept", "context-0", "procedure context"],
      ["concept", "context-1", "procedure context"],
      ["concept", "context-2", "counting frame"],
      ["param-2", "op-0", "parameter"],
      ["context-1", "op-0", "input"],
      ["param-1", "op-1", "parameter"],
      ["op-0", "op-1", "output"],
      ["op-1", "result", "quotient / remainder"],
      ["context-2", "op-2", "start"],
      ["op-2", "result", "date name"],
    ],
  };
}

function node(id, label, sub, x, y, w, h, color, stroke, kind, sourceItem) {
  return {
    id,
    label,
    sub,
    x,
    y,
    w,
    h,
    color,
    stroke,
    kind,
    sourceItem,
    visual: kind,
    source: sourceItem?.chunk_id ? shortId(sourceItem.chunk_id) : sourceItem?.anchor || "",
  };
}

function renderConcept() {
  const graph = buildBuConceptGraph();
  el("#view-concept").innerHTML = `
    <div class="relation-panel-title">
      <h2>Concept-to-computation layered graph: 蔀</h2>
      <span class="relation-demo-tag">DEFINES + HAS_VALUE + steps</span>
    </div>
    <p class="relation-demo-note">Relation labels become layers: definition condition -> concept -> parameter definitions -> procedure context -> operations -> computed quantities.</p>
    <div class="relation-graph-wrap"><svg viewBox="0 0 1500 420" id="conceptSvg" role="img" aria-label="Concept to computation layered graph"></svg></div>
    <div class="relation-demo-legend"><span class="relation-demo-tag type-ASTRO_TERM">concept</span><span class="relation-demo-tag type-PARAMETER">parameter</span><span class="relation-demo-tag type-QUANTITY">quantity/result</span><span class="relation-demo-tag type-CALC_OP">operation</span></div>
  `;

  const svg = el("#conceptSvg");
  svg.innerHTML = `
    <defs><marker id="relationArrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto" markerUnits="strokeWidth"><path d="M0,0 L0,6 L9,3 z" fill="#927f65"></path></marker></defs>
    <text x="70" y="35" class="relation-layer-label">1. definition</text>
    <text x="520" y="35" class="relation-layer-label">2. parameter definitions</text>
    <text x="790" y="35" class="relation-layer-label">3. procedure context</text>
    <text x="1030" y="35" class="relation-layer-label">4. operations</text>
    <text x="1245" y="35" class="relation-layer-label">5. results</text>
  `;
  graph.edges.forEach(([from, to, label]) => {
    const a = graph.nodes.find((item) => item.id === from);
    const b = graph.nodes.find((item) => item.id === to);
    drawEdge(svg, a.x + a.w / 2, a.y + a.h / 2, b.x + b.w / 2, b.y + b.h / 2, label);
  });
  graph.nodes.forEach((item) => drawNode(svg, item));
}

function drawEdge(svg, x1, y1, x2, y2, label) {
  const midx = (x1 + x2) / 2;
  const midy = (y1 + y2) / 2;
  const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
  path.setAttribute("d", `M ${x1} ${y1} C ${midx} ${y1}, ${midx} ${y2}, ${x2} ${y2}`);
  path.setAttribute("class", "relation-edge");
  path.setAttribute("marker-end", "url(#relationArrow)");
  svg.appendChild(path);
  const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
  text.setAttribute("x", midx);
  text.setAttribute("y", midy - 5);
  text.setAttribute("class", "relation-edge-label");
  text.textContent = label;
  svg.appendChild(text);
}

function drawNode(svg, item) {
  const group = document.createElementNS("http://www.w3.org/2000/svg", "g");
  group.setAttribute("class", "relation-node");
  group.innerHTML = `
    <rect x="${item.x}" y="${item.y}" width="${item.w}" height="${item.h}" rx="18" fill="${item.color}" stroke="${item.stroke}" stroke-width="2"></rect>
    <text x="${item.x + 14}" y="${item.y + 30}" class="relation-node-label">${esc(item.label)}</text>
    <text x="${item.x + 14}" y="${item.y + 51}" class="relation-node-sub">${esc(truncate(item.sub, 24))}</text>
  `;
  group.addEventListener("click", () => {
    els("#conceptSvg .relation-node").forEach((node) => node.classList.remove("selected"));
    group.classList.add("selected");
    if (item.sourceItem?.op) showInspector(item.sourceItem, "step");
    else if (item.sourceItem?.relation) showInspector(item.sourceItem, "relation");
    else if (item.sourceItem?.text) showInspector(item.sourceItem, "term");
    else showInspector(item, "node");
  });
  svg.appendChild(group);
}

function renderGrammar(mode = "DEFINES") {
  const labels = RELATION_LABELS.filter((label) => relations.some((relation) => relation.relation === label));
  const rels = relations.filter((relation) => relation.relation === mode);
  el("#view-grammar").innerHTML = `
    <div class="relation-panel-title"><h2>Relation Visual Grammar</h2><span class="relation-demo-tag">${esc(mode)}</span></div>
    <p class="relation-demo-note">Each tab uses one exact relation label from the breakdown index. Agent Action and Observed Object are kept separate.</p>
    <div class="relation-demo-toolbar">${labels.map((label) => `<button class="relation-demo-pill ${label === mode ? "active" : ""}" type="button" data-relation="${label}">${esc(RELATION_NAMES[label] || label)}</button>`).join("")}</div>
    <div id="grammarArea" class="relation-grammar-area"></div>
  `;
  els("[data-relation]").forEach((button) => button.addEventListener("click", () => renderGrammar(button.dataset.relation)));
  const area = el("#grammarArea");

  if (mode === "DEFINES") {
    area.innerHTML = `<div class="relation-demo-cards">${rels.map((relation) => `<button class="relation-demo-card definition-card" type="button" data-relation-id="${esc(relation.uid)}"><h4>${termLabel(relation.object)}</h4><div class="relation-arrow">defined by</div><div>${termLabel(relation.subject)}</div><div class="relation-demo-note">${esc(shortId(relation.chunk_id))}</div></button>`).join("")}</div>`;
  } else if (mode === "HAS_VALUE") {
    area.innerHTML = `<div class="relation-demo-cards">${rels.map((relation) => `<button class="relation-demo-card value-card" type="button" data-relation-id="${esc(relation.uid)}"><h4>${termLabel(relation.subject)} = ${valueLabel(relation.object)}</h4><div class="relation-demo-note">${esc(shortId(relation.chunk_id))}</div></button>`).join("")}</div>`;
  } else if (mode === "HAS_PART") {
    area.innerHTML = groupedRelationCards(rels, "part-box", "component set");
  } else if (mode === "UNDERGOES") {
    area.innerHTML = groupedRelationCards(rels, "motion-card", "motion predicate set");
  } else if (mode === "TAKES_OBJECT") {
    renderObservedObject(area, rels);
  } else if (mode === "PERFORMS") {
    area.innerHTML = `<div class="relation-demo-cards">${rels.map((relation) => `<button class="relation-demo-card actor-card" type="button" data-relation-id="${esc(relation.uid)}"><h4>${termLabel(relation.subject)}</h4><div class="relation-arrow">performs</div><div>${termLabel(relation.object)}</div><div class="relation-demo-note">${esc(shortId(relation.chunk_id))}</div></button>`).join("")}</div>`;
  } else if (mode === "LEADS_TO") {
    area.innerHTML = `<div class="relation-flow">${rels.map((relation) => `<button class="relation-step" type="button" data-relation-id="${esc(relation.uid)}"><strong>${esc(shortId(relation.chunk_id))}</strong><div class="phrase">${termLabel(relation.subject)}</div><div class="op">LEADS_TO</div><div class="phrase">-> ${termLabel(relation.object)}</div></button>`).join("")}</div>`;
  } else if (mode === "LOCATES_AT") {
    area.innerHTML = groupedRelationCards(rels, "frame-box", "locative frame");
  }

  area.querySelectorAll("[data-relation-id]").forEach((button) => {
    button.addEventListener("click", () => showInspector(relations.find((relation) => relation.uid === button.dataset.relationId), "relation"));
  });
}

function groupedRelationCards(rels, className, note) {
  const grouped = groupBy(rels, (relation) => relation.subject);
  return `<div class="relation-frame-note">${esc(note)}</div><div class="relation-demo-cards">${[...grouped.entries()].map(([subject, records]) => `<div class="${className}"><h4>${termLabel(subject)}</h4><div class="relation-part-children">${records.map((relation) => `<button class="relation-demo-tag type-ASTRO_TERM" type="button" data-relation-id="${esc(relation.uid)}">${termLabel(relation.object)}</button>`).join("")}</div></div>`).join("")}</div>`;
}

function renderObservedObject(area, rels) {
  const grouped = groupBy(rels, (relation) => relation.subject);
  area.innerHTML = `<div class="relation-frame-note">observed-object frame</div><div class="relation-demo-cards">${[...grouped.entries()].map(([subject, records]) => `<div class="relation-hub-card"><h4>${termLabel(subject)}</h4><div class="relation-part-children">${records.map((relation) => `<button class="relation-demo-tag type-ASTRO_TERM" type="button" data-relation-id="${esc(relation.uid)}">${termLabel(relation.object)}</button>`).join("")}</div></div>`).join("")}</div>`;
}

function renderOperations(selected = "all") {
  const ops = [...new Set(steps.map((step) => step.op))].sort();
  const filtered = selected === "all" ? steps : steps.filter((step) => step.op === selected);
  const grouped = groupBy(filtered, (step) => step.op);
  el("#view-operations").innerHTML = `
    <div class="relation-panel-title"><h2>Operation Clusters</h2><span class="relation-demo-tag">steps as algorithmic grammar</span></div>
    <p class="relation-demo-note">Procedure steps are grouped by operation so repeated computational grammar is visible across annotated procedure chunks.</p>
    <div class="relation-demo-toolbar"><button class="relation-demo-pill ${selected === "all" ? "active" : ""}" type="button" data-op="all">All</button>${ops.map((op) => `<button class="relation-demo-pill ${selected === op ? "active" : ""}" type="button" data-op="${esc(op)}">${esc(op)} <span class="relation-demo-note">${steps.filter((step) => step.op === op).length}</span></button>`).join("")}</div>
    <div>${[...grouped.entries()].map(([op, opSteps]) => `<div class="relation-cluster"><div class="relation-cluster-name"><b>${esc(op)}</b><p class="relation-demo-note">${esc(operationNote(op))}</p></div><div class="relation-cluster-steps">${opSteps.map((step) => `<button class="relation-step" type="button" data-step-id="${esc(`${step.chunk_id}::${step.order}`)}"><strong>${esc(shortId(step.chunk_id))} · step ${esc(step.order)}</strong><div class="phrase">${esc(step.phrase)}</div><div class="op">${esc(step.input || "none")} -> ${esc(step.parameter || "none")} -> ${esc(step.output || "none")}</div></button>`).join("")}</div></div>`).join("")}</div>
  `;
  els("[data-op]").forEach((button) => button.addEventListener("click", () => renderOperations(button.dataset.op)));
  els("[data-step-id]").forEach((button) => button.addEventListener("click", () => showInspector(stepById(button.dataset.stepId), "step")));
}

function renderMatrix() {
  const typeList = TYPES.filter((type) => terms.some((term) => term.type === type));
  const rows = [...groupBy(terms, (term) => term.text).entries()]
    .map(([text, records]) => ({ text, records, typeCount: new Set(records.map((record) => record.type)).size }))
    .sort((a, b) => b.typeCount - a.typeCount || b.records.length - a.records.length || a.text.localeCompare(b.text));
  el("#view-matrix").innerHTML = `
    <div class="relation-panel-title"><h2>Role-Shift Matrix</h2><span class="relation-demo-tag">same text, different roles</span></div>
    <p class="relation-demo-note">Each dot shows where the same written term appears under a role type. Click a dot to inspect occurrences and anchors.</p>
    <div class="relation-matrix-wrap"><table class="relation-matrix"><thead><tr><th>text</th>${typeList.map((type) => `<th>${esc(type)}</th>`).join("")}</tr></thead><tbody>${rows.map(({ text, records }) => `<tr><td><b>${termLabel(text)}</b></td>${typeList.map((type) => {
      const typed = records.filter((record) => record.type === type);
      return `<td>${typed.length ? `<button class="relation-dot ${typeClass(type)}" type="button" data-text="${esc(text)}" data-type="${esc(type)}" title="${typed.length} occurrence(s)"></button><div class="relation-demo-note">${typed.length}</div>` : ""}</td>`;
    }).join("")}</tr>`).join("")}</tbody></table></div>
  `;
  els(".relation-dot").forEach((dot) => dot.addEventListener("click", () => {
    const selected = terms.filter((term) => term.text === dot.dataset.text && term.type === dot.dataset.type);
    el("#relationInspector").innerHTML = `
      <h3>${esc(dot.dataset.text)} × ${esc(dot.dataset.type)}</h3>
      <div class="relation-detail-block"><h4>Occurrences</h4>${selected.map((term) => `<div class="relation-demo-card"><b>${termLabel(term.text)}</b> <span class="relation-demo-tag ${typeClass(term.type)}">${esc(term.type)}</span><div class="relation-demo-note">${esc(shortId(term.chunk_id))} · ${esc(term.anchor)} · ${esc(term.en)}</div></div>`).join("")}</div>
    `;
  }));
}

function renderExplorer(selectedId = data[0]?.chunk_id) {
  const selected = chunksById.get(selectedId) || data[0];
  el("#view-explorer").innerHTML = `
    <div class="relation-panel-title"><h2>Chunk Explorer</h2><span class="relation-demo-tag">source-backed annotations</span></div>
    <p class="relation-demo-note">A chunk list on the left; source text, bilingual term chips, and procedure steps on the right.</p>
    <div class="relation-explorer-grid">
      <div class="relation-chunk-list">${data.map((chunk) => `<button class="relation-chunk-button ${chunk.chunk_id === selected.chunk_id ? "active" : ""}" type="button" data-chunk="${esc(chunk.chunk_id)}">${esc(shortId(chunk.chunk_id))} · ${esc(chunk.chunk_type)}<br><span class="relation-demo-note">${chunk.terms.length} terms · ${chunk.relations.length} rel · ${chunk.steps.length} steps</span></button>`).join("")}</div>
      <div>
        <h3>${esc(shortId(selected.chunk_id))} <span class="relation-demo-tag">${esc(selected.chunk_type)}</span></h3>
        <div class="relation-demo-legend">${TYPES.map((type) => `<span class="relation-demo-tag ${typeClass(type)}">${esc(type)}</span>`).join("")}</div>
        <div class="relation-anchor-block"><div class="relation-anchor-text">${esc(selected.source_text_zh || selected.english_text || "No source text in index.")}</div><div>${selected.terms.map((term) => `<button class="relation-term-chip ${typeClass(term.type)}" type="button" data-mention="${esc(term.mention_id)}">${termLabel(term.text, { en: term.en })}<span>${esc(term.type)}</span></button>`).join("")}</div></div>
        ${selected.steps.length ? `<div class="relation-anchor-block"><h4>Procedure steps</h4>${selected.steps.map((step) => `<button class="relation-step" type="button" data-step-id="${esc(`${selected.chunk_id}::${step.order}`)}"><strong>step ${esc(step.order)} · ${esc(step.op)}</strong><div class="phrase">${esc(step.phrase)}</div><div class="op">${esc(step.input || "none")} -> ${esc(step.parameter || "none")} -> ${esc(step.output || "none")}</div></button>`).join("")}</div>` : ""}
      </div>
    </div>
  `;
  els("[data-chunk]").forEach((button) => button.addEventListener("click", () => renderExplorer(button.dataset.chunk)));
  els("[data-mention]").forEach((chip) => chip.addEventListener("click", () => showInspector(termByMention.get(chip.dataset.mention), "term")));
  els("[data-step-id]").forEach((button) => button.addEventListener("click", () => showInspector(stepById(button.dataset.stepId), "step")));
}

function operationNote(op) {
  return {
    set: "place or initialize a quantity",
    subtract: "subtract a value",
    multiply: "parameter as multiplier",
    divide: "ordinary division",
    fill_divide: "threshold or factor division; usually creates quotient and remainder logic",
    name_result: "assign a textual name to a result",
    name_remainder: "assign a textual name to a remainder",
    remove_modulus: "cast out cycles or modulus",
    count: "cyclic counting, often sexagenary",
    judge: "threshold or presence condition",
    seek: "open a new target",
    add: "increment or carry",
    distribute: "distribute fractions to calendrical positions",
    output: "state the final result",
  }[op] || "";
}

function stepById(id) {
  const [chunkId, order] = String(id).split("::");
  return steps.find((step) => step.chunk_id === chunkId && String(step.order) === String(order));
}

function groupBy(items, keyFn) {
  const map = new Map();
  for (const item of items) {
    const key = keyFn(item);
    if (!map.has(key)) map.set(key, []);
    map.get(key).push(item);
  }
  return map;
}

function truncate(value, size) {
  const text = String(value || "");
  return text.length > size ? `${text.slice(0, size)}...` : text;
}

async function init() {
  const response = await fetch(withBase("static/procedure-ir/cullen-ch3-algorithm-comparison.json"));
  if (!response.ok) throw new Error(`Could not load visual grammar index: ${response.status}`);
  normalizeIndex(await response.json());
  initStats();
  initTabs();
  showInspector();
  renderConcept();
  renderGrammar();
  renderOperations();
  renderMatrix();
  renderExplorer();
}

init().catch((error) => {
  el("#relationStats").innerHTML = `<p class="empty-state">${esc(error.message)}</p>`;
});
