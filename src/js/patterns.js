import { highlightedText } from "./ui/heatmap.js";

const state = {
  index: null,
  query: "",
  viewMode: "pairs",
  annotation: "all",
  evidence: "all",
  sort: "similarity_desc",
};

const baseUrl = document.documentElement.dataset.baseurl || "/";
const withBase = (targetPath) => `${baseUrl.replace(/\/?$/, "/")}${targetPath.replace(/^\/+/, "")}`;

const summaryEl = document.getElementById("patternSummary");
const searchEl = document.getElementById("patternSearch");
const searchBtnEl = document.getElementById("patternSearchBtn");
const modeSwitchEl = document.querySelector(".pattern-mode-switch");
const modeButtons = [...document.querySelectorAll("[data-pattern-mode]")];
const annotationEl = document.getElementById("patternAnnotation");
const evidenceEl = document.getElementById("patternEvidence");
const resultsTitleEl = document.getElementById("patternResultsTitle");
const resultsMetaEl = document.getElementById("patternResultsMeta");
const comparisonResultsEl = document.getElementById("comparisonResults");
const sortControlsEl = document.getElementById("patternSortControls");
const compareAEl = document.getElementById("compareA");
const compareBEl = document.getElementById("compareB");
const compareBtnEl = document.getElementById("compareBtn");
const manualCompareResultEl = document.getElementById("manualCompareResult");

const EVIDENCE_DISPLAY = [
  ["operation_skeleton", "Operation skeleton"],
  ["quantity_flow", "Quantity flow"],
  ["parameter_role", "Parameter role"],
  ["target_output_class", "Target/output class"],
  ["surface_wording", "Surface wording"],
  ["term_overlap", "Term overlap"],
];

const EVIDENCE_MAX = {
  operation_skeleton: 0.24,
  quantity_flow: 0.2,
  parameter_role: 0.18,
  target_output_class: 0.18,
  surface_wording: 0.08,
  term_overlap: 0.12,
};

const CHANNEL_TERMS = {
  lunar_phase: ["朔", "弦", "望", "晦", "合朔", "月"],
  lodge_degree: ["宿", "度", "分", "宿次"],
  calendar_cycle: ["章", "蔀", "紀", "元", "歲", "年"],
  solar_terms: ["中", "節", "氣", "冬至", "夏至"],
  day_count: ["日", "日數", "朔日", "大餘", "小餘"],
  remainder_modulus: ["餘", "法", "滿", "不滿", "除"],
  sexagenary_count: ["甲子", "六十", "命之", "筭盡"],
  eclipse: ["食", "月食", "日食"],
};

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function normalize(value) {
  return String(value ?? "").toLowerCase().replace(/\s+/g, "");
}

function chunkOrdinal(chunkId) {
  return Number(String(chunkId ?? "").match(/chunk:(\d+)/)?.[1] ?? 0);
}

function chunkLabel(chunk) {
  const proc = (chunk.procedure_ids || []).join(", ");
  const units = (chunk.unit_ids || []).join(", ");
  return [proc, units, shortChunkId(chunk.chunk_id)].filter(Boolean).join(" | ");
}

function shortChunkId(chunkId) {
  return String(chunkId ?? "").replace("cullen:ch3:chunk:", "chunk ");
}

function chunkKind(chunk) {
  if (chunk.is_procedure_like || chunk.operation_sequence?.length) return "procedure";
  if ((chunk.constants ?? []).length && !(chunk.operation_sequence ?? []).length) return "constant";
  if ((chunk.target_classes ?? []).length || (chunk.motifs ?? []).length) return "technical";
  return "description";
}

function annotationKind(chunk) {
  if (chunk.has_manual_steps) return "manual_steps";
  if (chunk.annotation_source === "manual_breakdown") return "manual_breakdown";
  return "machine";
}

function hasManualBreakdown(chunk) {
  return Boolean(chunk?.has_manual_steps || chunk?.annotation_source === "manual_breakdown");
}

function sectionKey(chunk) {
  return (chunk.section_path ?? []).join(" > ") || "unsectioned";
}

function searchableChunkText(chunk) {
  return normalize([
    chunk.chunk_id,
    chunkLabel(chunk),
    chunk.source_text_zh,
    chunk.english_text,
    chunk.heading,
    chunk.procedure_ids?.join(" "),
    chunk.procedure_titles?.join(" "),
    chunk.operation_sequence?.join(" "),
    chunk.motifs?.join(" "),
    chunk.target_classes?.join(" "),
    chunk.quantity_channels?.map((channel) => channel.id).join(" "),
    chunk.constants?.join(" "),
    chunk.terms?.join(" "),
    chunk.named_outputs?.join(" "),
  ].join(" "));
}

function searchablePairText(pair, chunksById) {
  const a = chunksById.get(pair.chunk_a);
  const b = chunksById.get(pair.chunk_b);
  return normalize([
    pair.chunk_a,
    pair.chunk_b,
    pair.verdict,
    searchableChunkText(a),
    searchableChunkText(b),
    pair.evidence_axes?.flatMap((axis) => [
      axis.axis,
      axis.label,
      axis.level,
      axis.details?.map((detail) => [detail.value, detail.op, detail.type, detail.a?.phrase, detail.b?.phrase].join(" ")).join(" "),
    ]).join(" "),
    pair.evidence?.flatMap((item) => [item.family, item.label, ...item.values]).join(" "),
  ].join(" "));
}

function renderSummary() {
  const { summary, scoring_model: scoringModel } = state.index;
  const cards = [
    ["Chunks scanned", summary.chunk_count],
    ["Manually annotated chunks", summary.manual_breakdown_chunk_count ?? 0],
    ["Procedure chunks with steps", summary.manual_step_chunk_count ?? summary.chunks_with_operations ?? 0],
    ["Chunks with derived motifs", summary.chunks_with_motifs],
  ];

  summaryEl.innerHTML = `
    <div class="pattern-summary-grid">
      ${cards.map(([label, value]) => `
        <article class="pattern-summary-card">
          <strong class="pattern-summary-value">${escapeHtml(value)}</strong>
          <span>${escapeHtml(label)}</span>
        </article>
      `).join("")}
    </div>
    <p class="pattern-lab-note">Evidence model: ${escapeHtml(scoringModel.principle)}</p>
  `;
}

function populateCompareSelectors() {
  const manualRefs = state.index.chunks
    .filter((chunk) => chunk.annotation_source === "manual_breakdown")
    .sort((a, b) => Number(b.has_manual_steps) - Number(a.has_manual_steps) || chunkOrdinal(a.chunk_id) - chunkOrdinal(b.chunk_id));
  const candidates = state.index.chunks
    .filter(isIndexedChunk)
    .sort((a, b) => chunkOrdinal(a.chunk_id) - chunkOrdinal(b.chunk_id));

  compareAEl.innerHTML = manualRefs.map((chunk) => optionForChunk(chunk)).join("");
  compareBEl.innerHTML = candidates.map((chunk) => optionForChunk(chunk)).join("");

  const firstManualStep = manualRefs.find((chunk) => chunk.has_manual_steps) ?? manualRefs[0];
  if (firstManualStep) compareAEl.value = firstManualStep.chunk_id;
  const firstDifferent = candidates.find((chunk) => chunk.chunk_id !== compareAEl.value);
  if (firstDifferent) compareBEl.value = firstDifferent.chunk_id;
  renderManualComparison();
}

function optionForChunk(chunk) {
  const sourceLabel = chunk.has_manual_steps
    ? "manual steps"
    : chunk.annotation_source === "manual_breakdown"
      ? "manual terms"
      : "auto";
  const text = `${chunk.procedure_ids?.join(", ") || "no Proc"} | ${shortChunkId(chunk.chunk_id)} | ${sourceLabel}`;
  return `<option value="${escapeHtml(chunk.chunk_id)}">${escapeHtml(text)}</option>`;
}

function isIndexedChunk(chunk) {
  return chunk?.is_procedure_like || chunk?.operation_sequence?.length || chunk?.motifs?.length || chunk?.terms?.length;
}

function chunkPassesFilters(chunk) {
  if (!chunk) return false;
  if (state.annotation !== "all" && annotationKind(chunk) !== state.annotation) return false;
  if (state.query && !searchableChunkText(chunk).includes(normalize(state.query))) return false;
  return true;
}

function pairPassesFilters(pair, chunksById) {
  const a = chunksById.get(pair.chunk_a);
  const b = chunksById.get(pair.chunk_b);
  if (!a || !b) return false;
  if (!chunkPassesFilters(a) && !chunkPassesFilters(b)) return false;
  if (state.evidence !== "all" && !comparisonAxes(pair).some((axis) => axis.axis === state.evidence && axis.matched_count > 0)) return false;
  if (state.query && !searchablePairText(pair, chunksById).includes(normalize(state.query))) return false;
  return true;
}

function sortedChunks(chunks) {
  const items = [...chunks];
  if (state.sort === "document_desc") return items.sort((a, b) => chunkOrdinal(b.chunk_id) - chunkOrdinal(a.chunk_id));
  return items.sort((a, b) => chunkOrdinal(a.chunk_id) - chunkOrdinal(b.chunk_id));
}

function sortedPairs(pairs) {
  const items = [...pairs];
  if (state.sort === "similarity_asc") return items.sort((a, b) => a.score - b.score);
  if (state.sort === "document_asc") {
    return items.sort((a, b) => chunkOrdinal(a.chunk_a) - chunkOrdinal(b.chunk_a) || chunkOrdinal(a.chunk_b) - chunkOrdinal(b.chunk_b));
  }
  if (state.sort === "document_desc") {
    return items.sort((a, b) => chunkOrdinal(b.chunk_a) - chunkOrdinal(a.chunk_a) || chunkOrdinal(b.chunk_b) - chunkOrdinal(a.chunk_b));
  }
  return items.sort((a, b) => b.score - a.score);
}

function comparisonAxes(comparison) {
  if (comparison?.evidence_axes?.length) return comparison.evidence_axes;
  const legacy = new Map((comparison?.evidence ?? []).map((item) => [item.family, item]));
  return EVIDENCE_DISPLAY.map(([axis, label]) => {
    const legacyKeys = {
      operation_skeleton: ["operation_sequence"],
      quantity_flow: ["quantity_channel"],
      parameter_role: ["constant"],
      target_output_class: ["target_class", "named_output"],
      surface_wording: ["surface_pattern"],
      term_overlap: ["term"],
    }[axis] ?? [];
    const values = legacyKeys.flatMap((key) => legacy.get(key)?.values ?? []);
    const contribution = legacyKeys.reduce((sum, key) => sum + (legacy.get(key)?.weight ?? 0), 0);
    return {
      axis,
      label,
      level: strengthLabel(contribution / (EVIDENCE_MAX[axis] || 1), contribution ? { weight: contribution, family: axis } : null),
      matched_count: values.length,
      possible_count: Math.max(values.length, 1),
      weight: EVIDENCE_MAX[axis] ?? 0,
      contribution: Number(contribution.toFixed(3)),
      details: values.map((value) => ({ type: "legacy_evidence", value })),
    };
  });
}

function render() {
  if (!state.index) return;
  const chunksById = new Map(state.index.chunks.map((chunk) => [chunk.chunk_id, chunk]));
  const filteredChunkList = sortedChunks(state.index.chunks.filter(isIndexedChunk).filter(chunkPassesFilters));
  const filteredPairList = sortedPairs(comparisonList(chunksById).filter((pair) => pairPassesFilters(pair, chunksById)));
  renderSortControls();

  if (state.viewMode === "chunks") {
    resultsTitleEl.textContent = "Single Chunk Index";
    resultsMetaEl.textContent = `${filteredChunkList.length} chunks match current filters`;
    comparisonResultsEl.innerHTML = filteredChunkList.length
      ? filteredChunkList.map(renderChunkFeature).join("")
      : `<p class="empty-state">No chunks match the current filters.</p>`;
    return;
  }

  resultsTitleEl.textContent = "Pairwise Alignment";
  resultsMetaEl.textContent = `${filteredPairList.length} alignments match current filters`;
  comparisonResultsEl.innerHTML = filteredPairList.length
    ? filteredPairList.map((comparison) => renderComparison(comparison, chunksById)).join("")
    : `<p class="empty-state">No alignments match the current filters.</p>`;
}

function comparisonList(chunksById) {
  const existing = new Set((state.index.comparisons ?? []).map((pair) => comparisonKey(pair.chunk_a, pair.chunk_b)));
  const manualReferencePairs = manualReferenceComparisons(chunksById)
    .filter((pair) => !existing.has(comparisonKey(pair.chunk_a, pair.chunk_b)));
  return [...(state.index.comparisons ?? []), ...manualReferencePairs];
}

function manualReferenceComparisons(chunksById) {
  const manualChunks = [...chunksById.values()]
    .filter((chunk) => chunk.has_manual_steps)
    .sort((a, b) => chunkOrdinal(a.chunk_id) - chunkOrdinal(b.chunk_id));
  const comparisons = [];
  for (let i = 0; i < manualChunks.length; i += 1) {
    for (let j = i + 1; j < manualChunks.length; j += 1) {
      comparisons.push(compareChunksLive(manualChunks[i], manualChunks[j]));
    }
  }
  return comparisons;
}

function comparisonKey(aId, bId) {
  return [aId, bId].sort().join("::");
}

function renderSortControls() {
  if (!sortControlsEl) return;
  const sortControls = state.viewMode === "pairs"
    ? `
      <button type="button" data-sort-toggle="similarity" class="${state.sort.startsWith("similarity") ? "is-active" : ""}">
        Similarity ${state.sort === "similarity_asc" ? "low -> high" : "high -> low"}
      </button>
      <button type="button" data-sort-toggle="document" class="${state.sort.startsWith("document") ? "is-active" : ""}">
        Text order ${state.sort === "document_desc" ? "reverse" : "forward"}
      </button>
    `
    : `
      <button type="button" data-sort-toggle="document" class="is-active">
        Text order ${state.sort === "document_desc" ? "reverse" : "forward"}
      </button>
    `;
  sortControlsEl.innerHTML = sortControls;
}

function renderComparison(comparison, chunksById) {
  const chunkA = chunksById.get(comparison.chunk_a);
  const chunkB = chunksById.get(comparison.chunk_b);
  const alignment = buildOperationAlignment(chunkA, chunkB);
  const axes = comparisonAxes(comparison);
  const evidenceByFamily = highlightEvidenceByFamily(axes);
  return `
    <article class="pattern-record pattern-comparison-card">
      <div class="pattern-card-head">
        <strong class="result-title">Alignment</strong>
        <span class="pattern-card-kicker">${escapeHtml(shortChunkId(comparison.chunk_a))} vs ${escapeHtml(shortChunkId(comparison.chunk_b))} · ${escapeHtml(comparison.verdict)}</span>
      </div>
      ${renderStrengthSummary(comparison, chunkA, chunkB, alignment)}
      <div class="pattern-comparison-grid">
        ${renderChunkExcerpt("A", chunkA, comparison, alignment, evidenceByFamily)}
        ${renderChunkExcerpt("B", chunkB, comparison, alignment, evidenceByFamily)}
      </div>
      ${renderAlignmentBridge(alignment)}
    </article>
  `;
}

function renderManualComparison() {
  if (!state.index || !manualCompareResultEl) return;
  const chunksById = new Map(state.index.chunks.map((chunk) => [chunk.chunk_id, chunk]));
  const chunkA = chunksById.get(compareAEl.value);
  const chunkB = chunksById.get(compareBEl.value);
  if (!chunkA || !chunkB) {
    manualCompareResultEl.innerHTML = `<p class="empty-state">Choose two chunks to compare.</p>`;
    return;
  }
  const comparison = compareChunksLive(chunkA, chunkB);
  manualCompareResultEl.innerHTML = renderComparison(comparison, chunksById);
}

function renderChunkExcerpt(label, chunk, comparison = null, alignment = null, evidenceByFamily = new Map()) {
  if (!chunk) return "";
  const spans = comparison ? evidenceHighlightSpans(label, chunk, alignment, evidenceByFamily) : featureHighlightSpans(chunk);
  return `
    <div class="pattern-text-pane">
      <strong>${escapeHtml(label)} | ${escapeHtml(chunkLabel(chunk))}</strong>
      <p>${highlightedText(chunk.source_text_zh, spans)}</p>
      ${renderEnglishText(chunk, spans)}
      <dl class="pattern-feature-list">
        <dt>Chunk type</dt><dd>${escapeHtml(chunkKind(chunk))} / ${escapeHtml(annotationKind(chunk))}</dd>
        <dt>Operational Order</dt><dd>${escapeHtml(chunk.operation_sequence.join(" -> ") || "none")}</dd>
        <dt>Motifs</dt><dd>${escapeHtml(chunk.motifs.join(", ") || "none")}</dd>
      </dl>
    </div>
  `;
}

function renderChunkFeature(chunk) {
  if (chunk.has_manual_steps || chunk.operation_sequence.length) return renderProcedureChunk(chunk);
  if ((chunk.manual_relations ?? []).length) return renderKnowledgeChunk(chunk);
  if (chunkKind(chunk) === "constant") return renderConstantChunk(chunk);
  return renderDescriptionChunk(chunk);
}

function renderProcedureChunk(chunk) {
  const parameters = procedureParameters(chunk);
  const outputs = procedureOutputs(chunk);
  const spans = featureHighlightSpans(chunk);
  return `
    <article class="pattern-record pattern-feature-card">
      <div class="pattern-card-head">
        <strong class="result-title">${escapeHtml(chunkLabel(chunk))}</strong>
        <span class="pattern-card-kicker">${escapeHtml(chunkKind(chunk))} / ${escapeHtml(annotationKind(chunk))}</span>
      </div>
      <p class="pattern-source-text">${highlightedText(chunk.source_text_zh, spans)}</p>
      ${renderEnglishText(chunk, spans)}
      <dl class="pattern-feature-list">
        <dt>Operation sequence</dt><dd>${escapeHtml(chunk.operation_sequence.join(" -> ") || "none")}</dd>
        <dt>Parameters used</dt><dd>${escapeHtml(parameters.join(" · ") || "none")}</dd>
        <dt>Outputs</dt><dd>${escapeHtml(outputs.join(" · ") || "none")}</dd>
        <dt>Motifs</dt><dd>${escapeHtml(chunk.motifs.join(" · ") || "none")}</dd>
        <dt>Motif rules</dt><dd>${escapeHtml((chunk.motif_evidence ?? []).map((item) => `${item.motif}: ${item.rule}`).join(" | ") || "none")}</dd>
      </dl>
    </article>
  `;
}

function renderKnowledgeChunk(chunk) {
  const relationTypes = [...new Set((chunk.manual_relations ?? []).map((relation) => relation.relation))];
  const keyTerms = (chunk.manual_terms ?? []).map((term) => term.text).slice(0, 16);
  const spans = featureHighlightSpans(chunk);
  return `
    <article class="pattern-record pattern-feature-card">
      <div class="pattern-card-head">
        <strong class="result-title">${escapeHtml(chunkLabel(chunk))}</strong>
        <span class="pattern-card-kicker">${escapeHtml(chunk.chunk_type)} / ${escapeHtml(annotationKind(chunk))}</span>
      </div>
      <p class="pattern-source-text">${highlightedText(chunk.source_text_zh, spans)}</p>
      ${renderEnglishText(chunk, spans)}
      <dl class="pattern-feature-list">
        <dt>Knowledge frame</dt><dd>${escapeHtml(knowledgeFrame(chunk))}</dd>
        <dt>Relation types</dt><dd>${escapeHtml(relationTypes.join(" · ") || "none")}</dd>
        <dt>Key terms</dt><dd>${escapeHtml(keyTerms.join(" · ") || "none")}</dd>
      </dl>
    </article>
  `;
}

function renderConstantChunk(chunk) {
  const spans = featureHighlightSpans(chunk);
  return `
    <article class="pattern-record pattern-feature-card">
      <div class="pattern-card-head">
        <strong class="result-title">${escapeHtml(chunkLabel(chunk))}</strong>
        <span class="pattern-card-kicker">constant / ${escapeHtml(annotationKind(chunk))}</span>
      </div>
      <p class="pattern-source-text">${escapeHtml(chunk.source_text_zh)}</p>
      ${renderEnglishText(chunk, spans)}
      <dl class="pattern-feature-list">
        <dt>Constants</dt><dd>${escapeHtml(chunk.constants.join(" · ") || "none")}</dd>
        <dt>Terms</dt><dd>${escapeHtml(chunk.terms.slice(0, 16).join(" · ") || "none")}</dd>
        <dt>Section</dt><dd>${escapeHtml(sectionKey(chunk))}</dd>
      </dl>
    </article>
  `;
}

function renderDescriptionChunk(chunk) {
  const spans = featureHighlightSpans(chunk);
  return `
    <article class="pattern-record pattern-feature-card">
      <div class="pattern-card-head">
        <strong class="result-title">${escapeHtml(chunkLabel(chunk))}</strong>
        <span class="pattern-card-kicker">${escapeHtml(chunkKind(chunk))} / ${escapeHtml(annotationKind(chunk))}</span>
      </div>
      <p class="pattern-source-text">${escapeHtml(chunk.source_text_zh)}</p>
      ${renderEnglishText(chunk, spans)}
      <dl class="pattern-feature-list">
        <dt>Key terms</dt><dd>${escapeHtml(chunk.terms.slice(0, 16).join(" · ") || "none")}</dd>
        <dt>Quantity flow</dt><dd>${escapeHtml(chunk.quantity_channels.map((item) => item.id).join(" · ") || "none")}</dd>
        <dt>Section</dt><dd>${escapeHtml(sectionKey(chunk))}</dd>
      </dl>
    </article>
  `;
}

function renderEnglishText(chunk, sourceSpans = null) {
  if (!hasManualBreakdown(chunk)) return "";
  const section = manualEnglishSection(chunk, sourceSpans ?? featureHighlightSpans(chunk));
  if (!section.text) return "";
  return `<p class="pattern-english-text">${highlightedText(section.text, section.spans)}</p>`;
}

function manualEnglishSection(chunk, sourceSpans = []) {
  const sectionText = clippedEnglishText(chunk);
  if (!sectionText) return { text: "", spans: [] };
  return {
    text: sectionText,
    spans: manualEnglishHighlightSpans(chunk, sourceSpans, sectionText),
  };
}

function oldManualEnglishSection(chunk) {
  const fragments = manualEnglishFragments(chunk);
  let text = "";
  const spans = [];
  for (const fragment of fragments) {
    const separator = text ? " · " : "";
    const start = text.length + separator.length;
    text += `${separator}${fragment.en}`;
    spans.push({
      start,
      end: start + fragment.en.length,
      family: familyForManualTerm(fragment),
      value: valueForManualTerm(fragment),
      priority: priorityForManualTerm(fragment),
      title: `${fragment.type ?? "manual term"}: ${fragment.text} / ${fragment.en}`,
    });
  }
  return { text, spans };
}

function manualEnglishFragments(chunk) {
  const candidates = [];
  for (const term of chunk?.manual_terms ?? []) {
    if (!term?.text || !term?.en) continue;
    for (const span of allSourceSpans(chunk.source_text_zh, term.text)) {
      candidates.push({ ...term, start: span.start, end: span.end });
    }
  }
  return resolvedManualEnglishFragments(dedupeManualEnglishCandidates(candidates));
}

function dedupeManualEnglishCandidates(candidates) {
  const seen = new Set();
  return candidates.filter((candidate) => {
    const key = `${candidate.start}:${candidate.end}:${candidate.term_id ?? candidate.text}:${candidate.en}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

function resolvedManualEnglishFragments(candidates) {
  const topLevel = candidates.filter((candidate) => !candidates.some((other) =>
    other !== candidate
    && other.start <= candidate.start
    && other.end >= candidate.end
    && spanLength(other) > spanLength(candidate)
  ));
  const ordered = [...topLevel].sort((a, b) =>
    a.start - b.start
    || spanLength(b) - spanLength(a)
    || String(a.text).localeCompare(String(b.text))
  );
  const resolved = [];
  let cursor = -1;
  for (const candidate of ordered) {
    if (candidate.start < cursor) continue;
    resolved.push(candidate);
    cursor = candidate.end;
  }
  return resolved;
}

function clippedEnglishText(chunk) {
  const source = String(chunk?.english_text ?? "").trim();
  if (!source) return "";
  return source.slice(0, englishBoundaryEnd(chunk, source)).trim();
}

function englishBoundaryEnd(chunk, englishText) {
  const boundaryCandidates = manualTermOccurrences(chunk)
    .filter((item) => item.term.en)
    .slice(-12)
    .reverse();
  for (const occurrence of boundaryCandidates) {
    const span = firstEnglishSpan(englishText, occurrence.term.en);
    if (span) return extendToSentenceEnd(englishText, span.end);
  }
  return englishText.length;
}

function extendToSentenceEnd(text, index) {
  const tail = String(text ?? "").slice(index);
  const punctuation = tail.match(/[.!?]/u);
  if (!punctuation) return index;
  return index + punctuation.index + punctuation[0].length;
}

function manualEnglishHighlightSpans(chunk, sourceSpans, englishText) {
  const spans = [];
  const englishCursorByKey = new Map();
  const matchedOccurrences = manualTermOccurrences(chunk)
    .map((occurrence) => ({
      ...occurrence,
      sourceSpan: bestSourceSpanForOccurrence(occurrence, sourceSpans),
    }))
    .filter((occurrence) => occurrence.term.en && occurrence.sourceSpan);

  for (const occurrence of matchedOccurrences) {
    const term = occurrence.term;
    const englishKey = normalizedEnglishKey(term.en);
    if (!englishKey || englishKey.length < 3) continue;
    const cursor = englishCursorByKey.get(englishKey) ?? 0;
    const englishSpan = nextEnglishSpan(englishText, term.en, cursor);
    if (!englishSpan) continue;
    englishCursorByKey.set(englishKey, englishSpan.end);
    spans.push({
      start: englishSpan.start,
      end: englishSpan.end,
      family: occurrence.sourceSpan.family ?? familyForManualTerm(term),
      value: occurrence.sourceSpan.value ?? valueForManualTerm(term),
      priority: (occurrence.sourceSpan.priority ?? priorityForManualTerm(term)) + 1,
      title: `${term.type ?? "manual term"}: ${term.text} / ${term.en}`,
    });
  }
  return dedupeEnglishHighlightSpans(spans);
}

function manualTermOccurrences(chunk) {
  const candidates = [];
  for (const term of chunk?.manual_terms ?? []) {
    if (!term?.text || !term?.en) continue;
    for (const span of allSourceSpans(chunk.source_text_zh, term.text)) {
      candidates.push({ term, start: span.start, end: span.end });
    }
  }
  return dedupeManualTermOccurrences(candidates).sort((a, b) =>
    a.start - b.start
    || spanLength(b) - spanLength(a)
    || String(a.term.text).localeCompare(String(b.term.text))
  );
}

function dedupeManualTermOccurrences(candidates) {
  const seen = new Set();
  return candidates.filter((candidate) => {
    const key = `${candidate.start}:${candidate.end}:${candidate.term.term_id ?? candidate.term.text}:${candidate.term.en}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

function resolvedManualTermOccurrences(candidates) {
  const topLevel = candidates.filter((candidate) => !candidates.some((other) =>
    other !== candidate
    && other.start <= candidate.start
    && other.end >= candidate.end
    && spanLength(other) > spanLength(candidate)
  ));
  const ordered = [...topLevel].sort((a, b) =>
    a.start - b.start
    || spanLength(b) - spanLength(a)
    || String(a.term.text).localeCompare(String(b.term.text))
  );
  const resolved = [];
  let cursor = -1;
  for (const candidate of ordered) {
    if (candidate.start < cursor) continue;
    resolved.push(candidate);
    cursor = candidate.end;
  }
  return resolved;
}

function bestSourceSpanForOccurrence(occurrence, sourceSpans = []) {
  return (sourceSpans ?? [])
    .filter((span) => spansOverlap(occurrence, span))
    .sort((a, b) =>
      (b.priority ?? 0) - (a.priority ?? 0)
      || spanLength(a) - spanLength(b)
      || a.start - b.start
    )[0] ?? null;
}

function spansOverlap(a, b) {
  return a.start < b.end && b.start < a.end;
}

function dedupeEnglishHighlightSpans(spans) {
  const seen = new Set();
  return (spans ?? []).filter((span) => {
    const key = `${span.start}:${span.end}:${span.family}:${span.title}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

function firstEnglishSpan(sourceText, phrase) {
  return englishSpans(sourceText, phrase)[0] ?? null;
}

function nextEnglishSpan(sourceText, phrase, cursor = 0) {
  return englishSpans(sourceText, phrase).find((span) => span.start >= cursor) ?? null;
}

function englishSpans(sourceText, phrase) {
  const source = String(sourceText ?? "");
  const target = normalizedEnglishKey(phrase);
  if (!target) return [];
  const { normalized, map } = normalizedEnglishSource(source);
  const spans = [];
  let start = normalized.indexOf(target);
  while (start !== -1) {
    spans.push({
      start: map[start],
      end: map[start + target.length - 1] + 1,
    });
    start = normalized.indexOf(target, start + target.length);
  }
  return spans;
}

function normalizedEnglishSource(sourceText) {
  const chars = [];
  const map = [];
  const source = String(sourceText ?? "");
  for (let i = 0; i < source.length; i += 1) {
    const char = source[i];
    if (!/[A-Za-z0-9]/.test(char)) continue;
    chars.push(char.toLowerCase());
    map.push(i);
  }
  return { normalized: chars.join(""), map };
}

function normalizedEnglishKey(value) {
  return String(value ?? "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "");
}

function spanLength(span) {
  return Math.max(0, Number(span?.end ?? 0) - Number(span?.start ?? 0));
}

function familyForManualTerm(term) {
  const type = term?.type;
  if (type === "CALC_OP" || type === "KNOWLEDGE_OP" || type === "MOTION") return "surface_pattern";
  if (type === "PARAMETER") return "constant";
  if (type === "QUANTITY") return "named_output";
  return "term";
}

function valueForManualTerm(term) {
  const type = term?.type;
  if (type === "CALC_OP") return 0.7;
  if (type === "PARAMETER" || type === "QUANTITY") return 0.78;
  return 0.66;
}

function priorityForManualTerm(term) {
  const type = term?.type;
  if (type === "CALC_OP") return 5;
  if (type === "PARAMETER" || type === "QUANTITY") return 4;
  return 3;
}

function procedureParameters(chunk) {
  return [...new Set([
    ...chunk.operation_matches.flatMap((match) => [match.role_bindings?.parameter]).filter(Boolean),
    ...chunk.constants,
  ])].slice(0, 24);
}

function procedureOutputs(chunk) {
  return [...new Set([
    ...chunk.named_outputs,
    ...chunk.operation_matches.flatMap((match) => [match.role_bindings?.output]).filter(Boolean),
  ])].slice(0, 24);
}

function knowledgeFrame(chunk) {
  const relations = chunk.manual_relations ?? [];
  if (!relations.length) return "none";
  return relations
    .slice(0, 6)
    .map((relation) => `${relation.subject} -> ${relation.relation} -> ${relation.object}`)
    .join(" | ");
}

function featureHighlightSpans(chunk) {
  return stepSpansForChunk(chunk);
}

function stepSpansForChunk(chunk) {
  if ((chunk.manual_steps ?? []).length) return manualStepSpansForChunk(chunk);
  return operationSpansForChunk(chunk, "surface_pattern", 0.42);
}

function manualStepSpansForChunk(chunk) {
  return operationMatches(chunk)
    .map((match, index) => {
      const sourceSpan = sourceSpanForMatch(chunk.source_text_zh, match);
      if (!sourceSpan) return null;
      const label = operationLabel(match, index);
      return {
        ...sourceSpan,
        family: "operation_skeleton",
        value: 0.82,
        priority: 6,
        label,
        title: `${label}. ${match.op}: ${match.matched_text}`,
      };
    })
    .filter(Boolean);
}

function highlightEvidenceByFamily(axes) {
  const byAxis = new Map(axes.map((axis) => [axis.axis, axis]));
  const makeItem = (axisId, family, values) => ({
    family,
    weight: byAxis.get(axisId)?.contribution ?? 0,
    values: values.filter(Boolean),
  });
  return new Map([
    ["surface_pattern", makeItem("surface_wording", "surface_pattern", detailValues(byAxis.get("surface_wording")))],
    ["term", makeItem("term_overlap", "term", detailValues(byAxis.get("term_overlap")))],
    ["constant", makeItem("parameter_role", "constant", detailValues(byAxis.get("parameter_role")))],
    ["named_output", makeItem("target_output_class", "named_output", detailValues(byAxis.get("target_output_class")))],
    ["target_class", makeItem("target_output_class", "target_class", detailValues(byAxis.get("target_output_class")))],
    ["quantity_channel", makeItem("quantity_flow", "quantity_channel", detailValues(byAxis.get("quantity_flow")))],
  ]);
}

function detailValues(axis) {
  return (axis?.details ?? []).map((detail) => detail.value ?? detail.a?.parameter ?? detail.a?.output ?? detail.a?.phrase).filter(Boolean);
}

function renderStrengthSummary(comparison, chunkA, chunkB, alignment) {
  const evidenceByFamily = new Map(comparison.evidence.map((item) => [item.family, item]));
  return `
    <div class="match-joy-panel" aria-label="Pattern match joy plot">
      <div class="match-joy-title">Evidence Breakdown</div>
      ${EVIDENCE_DISPLAY.map(([family, label], index) => {
        const item = evidenceByFamily.get(family);
        const ratio = evidenceRatio(item);
        const strength = strengthLabel(ratio, item);
        return `
          <details class="match-joy-row">
            <summary>
              <span class="match-joy-name">${escapeHtml(label)}</span>
              <span class="match-joy-wave" style="${joyWaveStyle(ratio, index)}" aria-hidden="true"></span>
              <span class="match-joy-label">${escapeHtml(strength)}</span>
            </summary>
            <div class="match-strength-detail">
              ${renderStrengthDetail(family, item, chunkA, chunkB, alignment)}
            </div>
          </details>
        `;
      }).join("")}
    </div>
  `;
}

function joyWaveStyle(ratio, index) {
  const height = 16 + ratio * 42;
  const alpha = 0.16 + ratio * 0.36;
  const hue = [196, 8, 42, 92, 318, 170, 260, 220][index % 8];
  return `--joy-height:${height.toFixed(1)}px;--joy-alpha:${alpha.toFixed(3)};--joy-hue:${hue};--joy-fill:${(ratio * 100).toFixed(0)}%;`;
}

function renderStrengthDetail(family, item, chunkA, chunkB, alignment) {
  if (family === "operation_skeleton") {
    const shared = alignment.pairs.map((pair) => `${pair.label} ${pair.op}`).join(" -> ") || "none";
    const aUnique = alignment.aUnique.map((item) => item.op).join(", ") || "none";
    const bUnique = alignment.bUnique.map((item) => item.op).join(", ") || "none";
    return `
      <dl class="match-detail-list">
        <dt>Shared / aligned</dt><dd>${escapeHtml(shared)}</dd>
        <dt>A unique</dt><dd>${escapeHtml(aUnique)}</dd>
        <dt>B unique</dt><dd>${escapeHtml(bUnique)}</dd>
      </dl>
    `;
  }

  if (!item) return `<p>No strong evidence for this comparison.</p>`;

  return `
    <dl class="match-detail-list">
      <dt>Shared</dt><dd>${escapeHtml(item.values.join(", ") || "none")}</dd>
      <dt>A context</dt><dd>${escapeHtml(familyValues(chunkA, family).join(", ") || "none")}</dd>
      <dt>B context</dt><dd>${escapeHtml(familyValues(chunkB, family).join(", ") || "none")}</dd>
    </dl>
  `;
}

function renderAlignmentBridge(alignment) {
  if (!alignment.pairs.length && !alignment.aUnique.length && !alignment.bUnique.length) return "";
  const rows = alignmentRows(alignment);
  return `
    <div class="alignment-bridge" aria-label="Operation alignment bridge">
      <h3 class="alignment-bridge-title">Step Alignment</h3>
      ${rows.map((row) => row.type === "pair" ? `
        <div class="alignment-row is-${row.item.status}">
          <span class="alignment-side">${escapeHtml(row.item.aLabel)} ${escapeHtml(row.item.a.matched_text)}</span>
          <span class="alignment-link" title="${row.item.status === "shared" ? "same operation and same roles" : "same operation"}">${row.item.status === "shared" ? "=" : "same operation"}</span>
          <span class="alignment-side">${escapeHtml(row.item.bLabel)} ${escapeHtml(row.item.b.matched_text)}</span>
        </div>
      ` : row.type === "a" ? `
        <div class="alignment-row is-a-only">
          <span class="alignment-side">${escapeHtml(row.item.label)} ${escapeHtml(row.item.match.matched_text)}</span>
          <span class="alignment-link">A only</span>
          <span class="alignment-side is-empty">no aligned B step</span>
        </div>
      ` : `
        <div class="alignment-row is-b-only">
          <span class="alignment-side is-empty">no aligned A step</span>
          <span class="alignment-link">B only</span>
          <span class="alignment-side">${escapeHtml(row.item.label)} ${escapeHtml(row.item.match.matched_text)}</span>
        </div>
      `).join("")}
    </div>
  `;
}

function alignmentRows(alignment) {
  return [
    ...(alignment.pairs ?? []).map((item) => ({
      type: "pair",
      item,
      aOrder: operationNumber(item.a, item.aIndex),
      bOrder: operationNumber(item.b, item.bIndex),
    })),
    ...(alignment.aUnique ?? []).map((item) => ({
      type: "a",
      item,
      aOrder: operationNumber(item.match, item.index),
      bOrder: Number.POSITIVE_INFINITY,
    })),
    ...(alignment.bUnique ?? []).map((item) => ({
      type: "b",
      item,
      aOrder: Number.POSITIVE_INFINITY,
      bOrder: operationNumber(item.match, item.index),
    })),
  ].sort((left, right) =>
    Math.min(left.aOrder, left.bOrder) - Math.min(right.aOrder, right.bOrder)
    || left.aOrder - right.aOrder
    || left.bOrder - right.bOrder
    || alignmentRowTypeRank(left.type) - alignmentRowTypeRank(right.type)
  );
}

function alignmentRowTypeRank(type) {
  return { pair: 0, a: 1, b: 2 }[type] ?? 3;
}

function compareChunksLive(chunkA, chunkB) {
  const alignment = buildOperationAlignment(chunkA, chunkB);
  const axes = buildLiveAxes(chunkA, chunkB, alignment);
  const score = Math.min(1, axes.reduce((sum, axis) => sum + axis.contribution, 0));
  return {
    chunk_a: chunkA.chunk_id,
    chunk_b: chunkB.chunk_id,
    score: Number(score.toFixed(3)),
    verdict: classifyLiveVerdict(score, axes),
    evidence_axes: axes,
    differences: differencesFromAlignment(chunkA, chunkB, alignment),
    evidence: axes
      .filter((axis) => axis.matched_count > 0)
      .map((axis) => ({
        family: axis.axis,
        weight: axis.contribution,
        label: axis.label,
        values: axis.details.map((detail) => detail.value ?? detail.op ?? detail.type).filter(Boolean),
      })),
  };
}

function buildLiveAxes(chunkA, chunkB, alignment) {
  const axis = (axisId, matched, possible, details = []) => {
    const weight = EVIDENCE_MAX[axisId] ?? 0;
    const contribution = matched && possible ? Math.min(weight, (matched / possible) * weight) : 0;
    return {
      axis: axisId,
      label: EVIDENCE_DISPLAY.find(([id]) => id === axisId)?.[1] ?? axisId,
      level: axisLevel(matched, possible),
      matched_count: matched,
      possible_count: Math.max(possible, 1),
      weight,
      contribution: Number(contribution.toFixed(3)),
      details,
    };
  };

  const aOps = operationMatches(chunkA);
  const bOps = operationMatches(chunkB);
  const sharedChannels = intersection(chunkA.quantity_channels?.map((item) => item.id), chunkB.quantity_channels?.map((item) => item.id));
  const ioA = inputOutputTerms(chunkA);
  const ioB = inputOutputTerms(chunkB);
  const sharedIo = intersection(ioA, ioB);
  const parameterPairs = alignment.pairs.filter((pair) => roleName(pair.a) || roleName(pair.b));
  const sameParameterPairs = parameterPairs.filter((pair) => {
    const aValue = pair.a.role_bindings?.parameter || pair.a.role_bindings?.input;
    const bValue = pair.b.role_bindings?.parameter || pair.b.role_bindings?.input;
    return roleName(pair.a) === roleName(pair.b) && aValue && aValue === bValue;
  });
  const targetValuesA = [...(chunkA.target_classes ?? []), ...(chunkA.named_outputs ?? [])];
  const targetValuesB = [...(chunkB.target_classes ?? []), ...(chunkB.named_outputs ?? [])];
  const sharedTargets = intersection(targetValuesA, targetValuesB);
  const sharedPatterns = intersection(chunkA.pattern_ids ?? [], chunkB.pattern_ids ?? []);
  const sharedTerms = intersection(chunkA.terms ?? [], chunkB.terms ?? []).filter((term) => term.length >= 2).slice(0, 18);

  return [
    axis("operation_skeleton", alignment.pairs.length, Math.max(aOps.length, bOps.length, 1), alignment.pairs.map((pair) => pairedDetail("matched_operation", pair, chunkA, chunkB))),
    axis("quantity_flow", sharedChannels.length + sharedIo.length, new Set([...sharedChannels, ...ioA, ...ioB]).size || 1, [
      ...sharedChannels.map((value) => valueDetail("shared_quantity_channel", value, chunkA, chunkB)),
      ...sharedIo.map((value) => valueDetail("shared_input_output_role", value, chunkA, chunkB)),
    ]),
    axis("parameter_role", sameParameterPairs.length, parameterPairs.length || 1, sameParameterPairs.map((pair) => pairedDetail("same_parameter_role", pair, chunkA, chunkB))),
    axis("target_output_class", sharedTargets.length, new Set([...targetValuesA, ...targetValuesB]).size || 1, sharedTargets.map((value) => valueDetail("shared_target_or_output", value, chunkA, chunkB))),
    axis("surface_wording", sharedPatterns.length, new Set([...(chunkA.pattern_ids ?? []), ...(chunkB.pattern_ids ?? [])]).size || 1, sharedPatterns.map((value) => valueDetail("shared_surface_pattern", value, chunkA, chunkB))),
    axis("term_overlap", sharedTerms.length, new Set([...(chunkA.terms ?? []), ...(chunkB.terms ?? [])]).size || 1, sharedTerms.map((value) => valueDetail("shared_term", value, chunkA, chunkB))),
  ];
}

function axisLevel(matched, possible) {
  if (!matched || !possible) return "none";
  const ratio = matched / possible;
  if (ratio >= 0.67) return "strong";
  if (ratio >= 0.34) return "partial";
  return "weak";
}

function classifyLiveVerdict(score, axes) {
  const highWeightMatches = axes.filter((axis) =>
    ["operation_skeleton", "quantity_flow", "parameter_role", "target_output_class"].includes(axis.axis)
    && ["strong", "partial"].includes(axis.level)
  ).length;
  const hasSemanticAxis = axes.some((axis) =>
    ["quantity_flow", "target_output_class"].includes(axis.axis) && axis.level !== "none"
  );
  const onlySurfaceOrTerm = axes.some((axis) => axis.matched_count > 0)
    && axes.every((axis) => axis.matched_count === 0 || ["surface_wording", "term_overlap"].includes(axis.axis));
  if (score >= 0.7 && highWeightMatches >= 2 && hasSemanticAxis && !onlySurfaceOrTerm) return "strong";
  if (score >= 0.4 && !onlySurfaceOrTerm) return "partial";
  return "weak";
}

function pairedDetail(type, pair, chunkA = null, chunkB = null) {
  return {
    type,
    op: pair.op,
    a: sourceForOperation({ ...pair.a, chunk_id: chunkA?.chunk_id ?? pair.a.chunk_id }, operationNumber(pair.a, pair.aIndex)),
    b: sourceForOperation({ ...pair.b, chunk_id: chunkB?.chunk_id ?? pair.b.chunk_id }, operationNumber(pair.b, pair.bIndex)),
  };
}

function valueDetail(type, value, chunkA, chunkB) {
  return {
    type,
    value,
    a: { chunk_id: chunkA.chunk_id, phrase: value },
    b: { chunk_id: chunkB.chunk_id, phrase: value },
  };
}

function sourceForOperation(match, stepOrder = null) {
  return {
    chunk_id: match?.chunk_id,
    step_order: stepOrder,
    phrase: match?.matched_text,
    op: match?.op,
    input: match?.role_bindings?.input,
    parameter: match?.role_bindings?.parameter,
    output: match?.role_bindings?.output,
    target: match?.role_bindings?.target,
  };
}

function inputOutputTerms(chunk) {
  return [...new Set((chunk.operation_matches ?? [])
    .flatMap((match) => [match.role_bindings?.input, match.role_bindings?.output])
    .filter(Boolean))];
}

function roleName(match) {
  if (match?.op === "multiply") return "multiplier";
  if (match?.op === "fill_divide" || match?.op === "divide") return "divisor";
  if (match?.op === "remove_modulus") return "modulus";
  if (match?.op === "judge") return "threshold";
  if (match?.op === "count") return "counting_frame";
  if (match?.op === "add") return "increment";
  if (match?.op === "subtract") return "decrement";
  return match?.role_bindings?.parameter ? "parameter" : null;
}

function differencesFromAlignment(chunkA, chunkB, alignment) {
  const aOnly = alignment.aUnique.map((item) => sourceForOperation({ ...item.match, chunk_id: chunkA.chunk_id }, operationNumber(item.match, item.index)));
  const bOnly = alignment.bUnique.map((item) => sourceForOperation({ ...item.match, chunk_id: chunkB.chunk_id }, operationNumber(item.match, item.index)));
  const differentParameters = [];
  const differentOutputs = [];
  for (const pair of alignment.pairs) {
    const aParameter = pair.a.role_bindings?.parameter;
    const bParameter = pair.b.role_bindings?.parameter;
    if ((aParameter || bParameter) && aParameter !== bParameter) {
      differentParameters.push({
        type: "different_parameter",
        a_value: aParameter,
        b_value: bParameter,
        a: sourceForOperation({ ...pair.a, chunk_id: chunkA.chunk_id }, operationNumber(pair.a, pair.aIndex)),
        b: sourceForOperation({ ...pair.b, chunk_id: chunkB.chunk_id }, operationNumber(pair.b, pair.bIndex)),
      });
    }
    const aOutput = pair.a.role_bindings?.output || pair.a.role_bindings?.target;
    const bOutput = pair.b.role_bindings?.output || pair.b.role_bindings?.target;
    if ((aOutput || bOutput) && aOutput !== bOutput) {
      differentOutputs.push({
        type: "different_output",
        a_value: aOutput,
        b_value: bOutput,
        a: sourceForOperation({ ...pair.a, chunk_id: chunkA.chunk_id }, operationNumber(pair.a, pair.aIndex)),
        b: sourceForOperation({ ...pair.b, chunk_id: chunkB.chunk_id }, operationNumber(pair.b, pair.bIndex)),
      });
    }
  }
  return {
    a_only_operations: aOnly,
    b_only_operations: bOnly,
    different_parameters: differentParameters,
    different_outputs: differentOutputs,
    unmatched_phrases: [
      ...aOnly.map((item) => ({ side: "A", ...item })),
      ...bOnly.map((item) => ({ side: "B", ...item })),
    ],
  };
}

function addSharedEvidence(evidence, family, label, aValues = [], bValues = [], unitWeight, maxWeight) {
  const shared = intersection(aValues ?? [], bValues ?? [])
    .filter((value) => value && !/^(一|十二)$/u.test(value))
    .slice(0, family === "term" ? 18 : 10);
  if (!shared.length) return;
  evidence.push({ family, weight: Math.min(maxWeight, shared.length * unitWeight), label, values: shared });
}

function intersection(aValues, bValues) {
  const setB = new Set(bValues ?? []);
  return [...new Set((aValues ?? []).filter((value) => setB.has(value)))];
}

function buildOperationAlignment(chunkA, chunkB) {
  const aOps = operationMatches(chunkA);
  const bOps = operationMatches(chunkB);
  const pairs = lcsOperationPairs(aOps, bOps).map((pair, index) => ({
    ...pair,
    aLabel: operationLabel(pair.a, pair.aIndex),
    bLabel: operationLabel(pair.b, pair.bIndex),
    label: operationNumber(pair.a, pair.aIndex) === operationNumber(pair.b, pair.bIndex)
      ? operationLabel(pair.a, pair.aIndex)
      : `${operationLabel(pair.a, pair.aIndex)}/${operationLabel(pair.b, pair.bIndex)}`,
    status: sameRoles(pair.a, pair.b) ? "shared" : "similar",
  }));
  const pairedA = new Set(pairs.map((pair) => pair.aIndex));
  const pairedB = new Set(pairs.map((pair) => pair.bIndex));
  const aUnique = aOps
    .map((match, index) => ({ match, index }))
    .filter((item) => !pairedA.has(item.index))
    .map((item) => ({ ...item, op: item.match.op, label: operationLabel(item.match, item.index, "A") }));
  const bUnique = bOps
    .map((match, index) => ({ match, index }))
    .filter((item) => !pairedB.has(item.index))
    .map((item) => ({ ...item, op: item.match.op, label: operationLabel(item.match, item.index, "B") }));
  return { pairs, aUnique, bUnique };
}

function operationMatches(chunk) {
  if ((chunk?.manual_steps ?? []).length) {
    const occurrenceCursor = new Map();
    return chunk.manual_steps
      .map((step, index) => manualStepOperationMatch(chunk, step, index, occurrenceCursor))
      .filter(Boolean);
  }
  return (chunk?.operation_matches ?? [])
    .filter((match) => match.family === "procedure_target" || match.family === "procedure_operation")
    .sort((a, b) => a.match_index - b.match_index)
    .map((match, index) => ({
      ...match,
      canonical_order: operationNumber(match, index),
    }));
}

function manualStepOperationMatch(chunk, step, fallbackIndex = 0, occurrenceCursor = new Map()) {
  if (!step?.phrase) return null;
  const sourceSpans = allSourceSpans(chunk.source_text_zh, step.phrase);
  const phraseKey = String(step.phrase ?? "").trim();
  const occurrenceIndex = occurrenceCursor.get(phraseKey) ?? 0;
  const sourceSpan = sourceSpans[Math.min(occurrenceIndex, Math.max(sourceSpans.length - 1, 0))];
  occurrenceCursor.set(phraseKey, occurrenceIndex + 1);
  const canonicalOrder = operationNumber(step, fallbackIndex);
  return {
    pattern_id: `manual_step.${step.op}`,
    family: "procedure_operation",
    op: step.op,
    description: "Manual procedure step annotation",
    matched_text: step.phrase,
    match_index: sourceSpan ? compactSourceIndex(chunk.source_text_zh, sourceSpan.start) : Number(step.order ?? 0),
    canonical_order: canonicalOrder,
    source_span: sourceSpan,
    role_bindings: {
      input: step.input || "",
      parameter: step.parameter || "",
      output: step.output || "",
    },
    manual_order: step.order,
  };
}

function operationNumber(match, fallbackIndex = 0) {
  const value = Number(match?.canonical_order ?? match?.manual_order ?? match?.step_order ?? match?.order ?? fallbackIndex + 1);
  return Number.isFinite(value) && value > 0 ? value : fallbackIndex + 1;
}

function operationLabel(match, fallbackIndex = 0, prefix = "") {
  return `${prefix}${operationNumber(match, fallbackIndex)}`;
}

function lcsOperationPairs(aOps, bOps) {
  const dp = Array.from({ length: aOps.length + 1 }, () => Array(bOps.length + 1).fill(0));
  for (let i = aOps.length - 1; i >= 0; i -= 1) {
    for (let j = bOps.length - 1; j >= 0; j -= 1) {
      dp[i][j] = aOps[i].op === bOps[j].op
        ? dp[i + 1][j + 1] + 1
        : Math.max(dp[i + 1][j], dp[i][j + 1]);
    }
  }
  const pairs = [];
  let i = 0;
  let j = 0;
  while (i < aOps.length && j < bOps.length) {
    if (aOps[i].op === bOps[j].op) {
      pairs.push({ a: aOps[i], b: bOps[j], aIndex: i, bIndex: j, op: aOps[i].op });
      i += 1;
      j += 1;
    } else if (dp[i + 1][j] >= dp[i][j + 1]) {
      i += 1;
    } else {
      j += 1;
    }
  }
  return pairs;
}

function evidenceHighlightSpans(side, chunk, alignment, evidenceByFamily) {
  if (!alignment) return [];
  const spans = stepSpansForComparisonSide(side, chunk, alignment);

  addEvidenceValueSpans(spans, chunk, evidenceByFamily.get("surface_pattern"), "surface_pattern", 0.7, 4, "surface wording");
  addEvidenceValueSpans(spans, chunk, evidenceByFamily.get("term"), "term", 0.74, 5, "shared technical term");
  addEvidenceValueSpans(spans, chunk, evidenceByFamily.get("constant"), "constant", 0.78, 6, "shared parameter / constant");
  addEvidenceValueSpans(spans, chunk, evidenceByFamily.get("named_output"), "named_output", 0.78, 6, "shared named output");
  addEvidenceValueSpans(spans, chunk, evidenceByFamily.get("target_class"), "target_class", 0.52, 2, "shared output / target type");
  addEvidenceValueSpans(spans, chunk, evidenceByFamily.get("quantity_channel"), "quantity_channel", 0.44, 1, "shared quantity flow");
  return spans;
}

function stepSpansForComparisonSide(side, chunk, alignment) {
  const pairByIndex = new Map();
  const uniqueByIndex = new Map();
  for (const pair of alignment.pairs ?? []) {
    const index = side === "A" ? pair.aIndex : pair.bIndex;
    pairByIndex.set(index, pair);
  }
  for (const item of side === "A" ? alignment.aUnique ?? [] : alignment.bUnique ?? []) {
    uniqueByIndex.set(item.index, item);
  }

  return operationMatches(chunk)
    .map((match, index) => {
      const sourceSpan = sourceSpanForMatch(chunk.source_text_zh, match);
      if (!sourceSpan) return null;
      const pair = pairByIndex.get(index);
      const unique = uniqueByIndex.get(index);
      const label = pair
        ? side === "A" ? pair.aLabel : pair.bLabel
        : unique?.label ?? operationLabel(match, index);
      const isUnique = Boolean(unique);
      return {
        start: sourceSpan.start,
        end: sourceSpan.end,
        family: isUnique ? "surface_pattern" : "operation_sequence",
        value: isUnique ? 0.32 : pair.status === "shared" ? 0.88 : 0.58,
        priority: isUnique ? 1 : 3,
        label,
        title: `${label} ${match.op}: ${match.matched_text}`,
      };
    })
    .filter(Boolean);
}

function addEvidenceValueSpans(spans, chunk, evidenceItem, family, value, priority, label) {
  if (!evidenceItem?.values?.length) return;
  for (const evidenceValue of evidenceItem.values) {
    const candidates = evidenceSpanCandidates(chunk, family, evidenceValue);
    for (const candidate of candidates) {
      for (const sourceSpan of allSourceSpans(chunk.source_text_zh, candidate)) {
        spans.push({ start: sourceSpan.start, end: sourceSpan.end, family, value, priority, title: `${label}: ${candidate}` });
      }
    }
  }
}

function evidenceSpanCandidates(chunk, family, value) {
  if (family === "surface_pattern") {
    return (chunk.operation_matches ?? [])
      .filter((match) => match.pattern_id === value)
      .map((match) => match.matched_text);
  }
  if (family === "target_class") {
    return (chunk.operation_matches ?? [])
      .filter((match) => match.family === "procedure_target")
      .flatMap((match) => [match.matched_text, match.role_bindings?.target])
      .filter(Boolean);
  }
  if (family === "quantity_channel") return CHANNEL_TERMS[value] ?? [value];
  return [value];
}

function operationSpansForChunk(chunk, family, value) {
  return operationMatches(chunk)
    .map((match, index) => {
      const sourceSpan = sourceSpanForMatch(chunk.source_text_zh, match);
      if (!sourceSpan) return null;
      const label = operationLabel(match, index);
      return {
        start: sourceSpan.start,
        end: sourceSpan.end,
        family,
        value,
        priority: 1,
        label,
        title: `${label}. ${match.op}: ${match.matched_text}`,
      };
    })
    .filter(Boolean);
}

function sameRoles(a, b) {
  return normalizeRoleText(a.role_bindings) === normalizeRoleText(b.role_bindings);
}

function normalizeRoleText(bindings) {
  return Object.entries(bindings ?? {})
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([key, value]) => `${key}:${normalize(value)}`)
    .join("|");
}

function familyValues(chunk, family) {
  if (!chunk) return [];
  const map = {
    operation_skeleton: chunk.operation_sequence,
    quantity_flow: [
      ...(chunk.quantity_channels?.map((item) => item.id) ?? []),
      ...inputOutputTerms(chunk),
    ],
    parameter_role: procedureParameters(chunk),
    target_output_class: [...(chunk.target_classes ?? []), ...(chunk.named_outputs ?? [])],
    surface_wording: chunk.pattern_ids,
    term_overlap: chunk.terms,
    motif: chunk.motifs,
    quantity_channel: chunk.quantity_channels?.map((item) => item.id),
    target_class: chunk.target_classes,
    constant: chunk.constants,
    term: chunk.terms,
    named_output: chunk.named_outputs,
    surface_pattern: chunk.pattern_ids,
  };
  return (map[family] ?? []).slice(0, 18);
}

function evidenceRatio(item) {
  if (!item) return 0;
  return Math.min(1, (Number(item.weight) || 0) / (EVIDENCE_MAX[item.family] || 1));
}

function strengthLabel(ratio, item) {
  if (!item || ratio < 0.2) return "weak";
  if (ratio >= 0.72) return "strong";
  if (ratio >= 0.4) return "partial";
  return "weak";
}

function sourceSpanForMatch(sourceText, match) {
  if (match?.source_span) return match.source_span;
  const spans = allSourceSpans(sourceText, match?.matched_text);
  if (!spans.length) return null;
  const compactIndex = Number(match?.match_index ?? 0);
  if (!Number.isFinite(compactIndex)) return spans[0];
  const closest = spans
    .map((span) => ({ span, distance: Math.abs(compactSourceIndex(sourceText, span.start) - compactIndex) }))
    .sort((a, b) => a.distance - b.distance)[0];
  return closest?.span ?? spans[0];
}

function compactSourceIndex(sourceText, sourceIndex) {
  return String(sourceText ?? "").slice(0, sourceIndex).replace(/\s+/g, "").length;
}

function allSourceSpans(sourceText, needle) {
  const source = String(sourceText ?? "");
  const target = String(needle ?? "").trim();
  if (!target) return [];
  const spans = [];
  let start = source.indexOf(target);
  while (start !== -1) {
    spans.push({ start, end: start + target.length });
    start = source.indexOf(target, start + target.length);
  }

  const compactTarget = target.replace(/\s+/g, "");
  if (!compactTarget) return dedupeSpans(spans);
  const chars = [];
  const map = [];
  for (let i = 0; i < source.length; i += 1) {
    if (/\s/u.test(source[i])) continue;
    chars.push(source[i]);
    map.push(i);
  }
  const compactSource = chars.join("");
  let compactStart = compactSource.indexOf(compactTarget);
  while (compactStart !== -1) {
    spans.push({ start: map[compactStart], end: map[compactStart + compactTarget.length - 1] + 1 });
    compactStart = compactSource.indexOf(compactTarget, compactStart + compactTarget.length);
  }
  return dedupeSpans(spans).sort((a, b) => compactSourceIndex(source, a.start) - compactSourceIndex(source, b.start));
}

function dedupeSpans(spans) {
  const seen = new Set();
  return (spans ?? []).filter((span) => {
    const key = `${span.start}:${span.end}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

function updateStateFromControls() {
  state.query = searchEl?.value ?? "";
  state.annotation = annotationEl?.value ?? "all";
  state.evidence = evidenceEl?.value ?? "all";
  if (state.viewMode === "chunks" && state.sort.startsWith("similarity")) {
    state.sort = "document_asc";
  }
}

async function loadIndex() {
  summaryEl.innerHTML = `<p class="empty-state">Loading algorithm comparison index...</p>`;
  const response = await fetch(withBase("static/procedure-ir/cullen-ch3-algorithm-comparison.json"));
  if (!response.ok) throw new Error(`Could not load pattern index: ${response.status}`);
  state.index = await response.json();
  renderSummary();
  populateCompareSelectors();
  syncModeSwitch();
  render();
}

[searchEl, annotationEl, evidenceEl].forEach((control) => {
  control?.addEventListener("input", () => {
    updateStateFromControls();
    render();
  });
  control?.addEventListener("change", () => {
    updateStateFromControls();
    render();
  });
});

searchBtnEl?.addEventListener("click", () => {
  updateStateFromControls();
  render();
});

searchEl?.addEventListener("keydown", (event) => {
  if (event.key !== "Enter") return;
  updateStateFromControls();
  render();
});

modeButtons.forEach((button) => {
  button.addEventListener("click", () => {
    state.viewMode = button.dataset.patternMode || "pairs";
    modeButtons.forEach((item) => item.classList.toggle("is-active", item === button));
    syncModeSwitch();
    updateStateFromControls();
    render();
  });
});

function syncModeSwitch() {
  if (!modeSwitchEl) return;
  modeSwitchEl.classList.toggle("is-chunks", state.viewMode === "chunks");
  modeSwitchEl.classList.toggle("is-pairs", state.viewMode === "pairs");
}

sortControlsEl?.addEventListener("click", (event) => {
  const button = event.target.closest("button");
  if (!button) return;
  const sortToggle = button.dataset.sortToggle;
  if (sortToggle === "similarity") {
    state.sort = state.sort === "similarity_asc" ? "similarity_desc" : "similarity_asc";
    render();
    return;
  }
  if (sortToggle === "document") {
    state.sort = state.sort === "document_desc" ? "document_asc" : "document_desc";
    render();
  }
});

compareAEl?.addEventListener("change", renderManualComparison);
compareBEl?.addEventListener("change", renderManualComparison);
compareBtnEl?.addEventListener("click", renderManualComparison);

loadIndex().catch((error) => {
  summaryEl.innerHTML = `<p class="empty-state">${escapeHtml(error.message)}</p>`;
});
