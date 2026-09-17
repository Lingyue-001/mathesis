import { highlightedText } from './heatmap.js';

// Compiler ranges count code points, never UTF-16 code units or matched words.
export function sourceSegments(text, spans) {
  const points = Array.from(text);
  const valid = spans.filter(s => Number.isInteger(s.start) && Number.isInteger(s.end)
    && s.start >= 0 && s.end <= points.length && s.start < s.end);
  const bounds = [...new Set([0, points.length, ...valid.flatMap(s => [s.start, s.end])])].sort((a, b) => a - b);
  return bounds.slice(0, -1).map((start, i) => ({
    start, end: bounds[i + 1], text: points.slice(start, bounds[i + 1]).join(''),
    spans: valid.filter(s => s.start < bounds[i + 1] && s.end > start),
  }));
}

export function overlaps(a, b) {
  return a.doc_id === b.doc_id && a.reading_id === b.reading_id && a.start < b.end && b.start < a.end;
}

export function renderSource(container, documents, steps, onSelect, evidence = [], onAnchor = () => {}, presentation = {}) {
  container.replaceChildren();
  const contexts = document.createElement('details');
  contexts.className = 'research-context';
  const contextSummary = document.createElement('summary');
  contextSummary.textContent = `背景材料 · ${documents.filter(doc => doc.category === 'context_documents').length}`;
  contexts.append(contextSummary);
  for (const doc of documents) {
    const card = document.createElement('article');
    card.className = 'entry-card';
    card.dataset.sourceDoc = doc.doc_id;
    const heading = document.createElement('h3');
    heading.className = 'entry-card-title';
    heading.textContent = `${doc.category === 'context_documents' ? '背景' : '原文'}${doc.source?.section ? ` · §${doc.source.section}` : ''}`;
    heading.title = `${doc.source?.path || doc.doc_id} · ${doc.reading_id}`;
    const body = document.createElement('p');
    body.className = 'source-text pattern-source-text';
    const spans = [...steps.flatMap(step => step.source_spans
      .filter(s => s.doc_id === doc.doc_id && s.reading_id === doc.reading_id)
      .map(s => ({ ...s, step_id: step.id }))), ...evidence
      .filter(row => row.span?.doc_id === doc.doc_id && row.span?.reading_id === doc.reading_id)
      .map(row => ({ ...row.span, evidence: row }))];
    for (const segment of sourceSegments(doc.text, spans)) {
      if (!segment.spans.length) {
        body.append(document.createTextNode(segment.text));
        continue;
      }
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'source-span';
      button.dataset.docId = doc.doc_id;
      button.dataset.readingId = doc.reading_id;
      button.dataset.start = segment.start;
      button.dataset.end = segment.end;
      button.setAttribute('aria-pressed', 'false');
      const address = { doc_id: doc.doc_id, reading_id: doc.reading_id, start: segment.start, end: segment.end };
      const questions = (presentation.questions || []).filter(q => q.source_anchors?.some(span => overlaps(span, address)));
      const labels = [...new Set(segment.spans.map(s => presentation.candidates?.find(c => c.id === s.step_id)?.label || presentation.steps?.[s.step_id]?.label).filter(Boolean))];
      button.dataset.unresolved = String(questions.length > 0);
      button.title = [...labels, ...new Set(questions.map(q => q.label))].join(' · ');
      // Reuse Pattern Lab's markup/color utility with a fixed visual intensity,
      // not similarity scoring. Only local markup uses UTF-16 lengths; source
      // addresses remain code points. Trim formatter whitespace outside <mark>.
      button.innerHTML = labels.length ? highlightedText(segment.text, [{
        start: 0, end: segment.text.length, family: 'operation_skeleton', value: 0.08, title: labels.join(' · '),
      }]).trim() : highlightedText(segment.text, []);
      button.addEventListener('click', () => {
        const stepIds = [...new Set(segment.spans.map(s => s.step_id).filter(Boolean))];
        if (stepIds.length) onSelect(stepIds);
        onAnchor({ doc_id: doc.doc_id, reading_id: doc.reading_id, start: segment.start, end: segment.end });
      });
      body.append(button);
    }
    card.append(heading, body);
    if (doc.category === 'context_documents') contexts.append(card);
    else container.append(card);
  }
  if (contexts.children.length > 1) container.append(contexts);
}

export function markSourceSelection(container, spans) {
  for (const button of container.querySelectorAll('.source-span')) {
    const span = { doc_id: button.dataset.docId, reading_id: button.dataset.readingId,
      start: Number(button.dataset.start), end: Number(button.dataset.end) };
    const selected = spans.some(s => overlaps(s, span));
    button.dataset.selected = String(selected);
    button.setAttribute('aria-pressed', String(selected));
    button.classList.toggle('heat-text-mark', selected);
  }
}

// Convert a browser text selection back to code-point source coordinates.
// Buttons already partition one document into source spans, so no string
// matching is involved and repeated text remains distinct.
export function selectionAnchor(container) {
  const selection = window.getSelection();
  if (!selection || selection.isCollapsed || !selection.rangeCount) return null;
  const buttonFor = node => (node.nodeType === Node.ELEMENT_NODE ? node : node.parentElement)?.closest?.('.source-span');
  const first = buttonFor(selection.anchorNode), last = buttonFor(selection.focusNode);
  if (!first || !last || !container.contains(first) || !container.contains(last)
      || first.dataset.docId !== last.dataset.docId || first.dataset.readingId !== last.dataset.readingId) return null;
  const offset = (button, node, index) => {
    const range = document.createRange(); range.selectNodeContents(button); range.setEnd(node, index);
    return Number(button.dataset.start) + Array.from(range.toString()).length;
  };
  const a = offset(first, selection.anchorNode, selection.anchorOffset);
  const b = offset(last, selection.focusNode, selection.focusOffset);
  const start = Math.min(a, b), end = Math.max(a, b);
  return start < end ? { doc_id: first.dataset.docId, reading_id: first.dataset.readingId, start, end } : null;
}

export function revealInPanel(container, target) {
  if (!target) return;
  for (let ancestor = target.parentElement; ancestor && container.contains(ancestor); ancestor = ancestor.parentElement) {
    if (ancestor.tagName === 'DETAILS') ancestor.open = true;
  }
  const box = container.getBoundingClientRect();
  const item = target.getBoundingClientRect();
  if (item.top < box.top || item.bottom > box.bottom) container.scrollTop += item.top - box.top - 10;
}
