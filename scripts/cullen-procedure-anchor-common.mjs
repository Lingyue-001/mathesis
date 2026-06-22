import fs from "node:fs/promises";
import path from "node:path";
import { resolveRepoPath, writeJson } from "./cullen-oracle-common.mjs";
import { buildProcedureInventory } from "./cullen-procedure-inventory-common.mjs";

export const CULLEN_PROCEDURE_ANCHOR_JSON = "tmp/procedure-ir/cullen-procedure-anchors.json";
export const CULLEN_PROCEDURE_ANCHOR_MD = "tmp/procedure-ir/cullen-procedure-anchors.md";
export const CULLEN_PROCEDURE_DEBUG_DIR = "tmp/procedure-ir/debug";
export const REQUIRED_SIFEN_PROC_IDS = [];
export const REQUIRED_SANTONG_PROC_IDS = [];

const MANUAL_SOURCE_SPAN_HINTS = new Map([
  ["Proc. 3.2", ["sifen:L66"]],
  ["Proc. 3.5", ["sifen:L74"]],
  ["Proc. 3.6", ["sifen:L74"]],
  ["Proc. 3.9", ["sifen:L84"]],
  ["Proc. 3.21", ["sifen:L112"]],
  ["Proc. 3.23", ["sifen:L118"]],
  ["Proc. 3.24", ["sifen:L118"]],
  ["Proc. 3.25", ["sifen:L122"]],
  ["Proc. 3.26", ["sifen:L122"]],
  ["Proc. 3.27", ["sifen:L126"]],
  ["Proc. 3.28", ["sifen:L126"]],
  ["Proc. 3.29", ["sifen:L126"]],
  ["Proc. 3.30", ["sifen:L126"]],
  ["Proc. 3.31", ["sifen:L126"]],
  ["Proc. 3.47", ["sifen:L152"]],
]);

const MANUAL_FAMILY_OVERRIDES = new Map([
  ["Proc. 3.2", "obscuration_entry"],
  ["Proc. 3.5", "tianzheng_shuori"],
  ["Proc. 3.6", "tianzheng_shuori"],
  ["Proc. 3.9", "intercalary_month"],
  ["Proc. 3.20", "du_lodge_sun"],
  ["Proc. 3.21", "du_lodge_moon"],
  ["Proc. 3.22", "du_lodge_moon"],
  ["Proc. 3.23", "du_lodge_sun"],
  ["Proc. 3.24", "du_lodge_sun"],
  ["Proc. 3.25", "du_lodge_moon"],
  ["Proc. 3.26", "du_lodge_moon"],
  ["Proc. 3.27", "eclipse_chain"],
  ["Proc. 3.28", "eclipse_chain"],
  ["Proc. 3.29", "eclipse_chain"],
  ["Proc. 3.30", "eclipse_chain"],
  ["Proc. 3.31", "eclipse_chain"],
  ["Proc. 3.47", "planet_conjunction"],
]);

const GENERIC_CHINESE_TERMS = new Set(["蔀法", "積日", "餘", "乘", "除"]);
const GENERIC_ENGLISH_TERMS = new Set(["obscuration factor", "accumulated days", "remainder", "multiply", "divide"]);
const GENERIC_OPERATION_TYPES = new Set(["multiply", "divide"]);
const NON_DISTINCTIVE_ALIGNMENT_TERMS = new Set([
  "unknown",
  "obscuration_entry",
  "tianzheng_shuori",
  "intercalary_month",
  "eclipse_chain",
  "du_lodge_sun",
  "du_lodge_moon",
  "planet_conjunction",
  "mei_mie",
]);

function uniqueStrings(items) {
  return [...new Set((items ?? [])
    .flatMap((item) => Array.isArray(item) ? item : [item])
    .filter(Boolean)
    .map((item) => String(item).trim())
    .filter(Boolean))];
}

function normalizeWhitespace(value) {
  return String(value ?? "")
    .replace(/\s*-\s*\n\s*/gu, "")
    .replace(/\s+/gu, " ")
    .trim();
}

function normalizeTitleForMatch(value) {
  return normalizeWhitespace(value)
    .replace(/\bT\s+o\b/giu, "To")
    .replace(/\bT\s+able\b/giu, "Table")
    .toLowerCase();
}

function normalizeEnglishTitleDisplay(value) {
  return normalizeWhitespace(value)
    .replace(/\bT\s+o\b/giu, "To")
    .replace(/\bT\s+able\b/giu, "Table");
}

function normalizeChineseTitle(value) {
  return String(value ?? "")
    .replace(/[：:．。．，、\s\[\]\(\)（）]/gu, "")
    .replace(/術曰$|术曰$|術$|术$|法曰$|法$/u, "")
    .trim();
}

function escapeRegex(value) {
  return String(value ?? "").replace(/[.*+?^${}()|[\]\\]/gu, "\\$&");
}

function hasExactProcMention(text, procId) {
  return new RegExp(`${escapeRegex(procId)}(?!\\d)`, "u").test(String(text ?? ""));
}

function parseChunkSequenceId(chunkId) {
  const match = String(chunkId ?? "").match(/cullen:chunk:(\d+)/u);
  return match ? Number(match[1]) : null;
}

function getChunkText(chunk) {
  return normalizeWhitespace(chunk?.normalized_text ?? chunk?.text ?? "");
}

function findProcIndex(text, procId) {
  return normalizeWhitespace(text).indexOf(procId);
}

function textContainsNormalizedTitle(text, title) {
  const normalizedText = normalizeTitleForMatch(text);
  const normalizedTitle = normalizeTitleForMatch(title);
  return Boolean(normalizedTitle) && normalizedText.includes(normalizedTitle);
}

function excerpt(value, max = 420) {
  const text = normalizeWhitespace(value);
  return text.length > max ? `${text.slice(0, max)}...` : text;
}

function extractChineseHeadingCandidate(text) {
  const tail = String(text ?? "").slice(-220);
  const matches = [
    ...tail.matchAll(/([推求置][^。．：:\n]{1,40}(?:術曰|术曰|術|术|法曰|法))/gu),
  ];
  return matches.length ? normalizeWhitespace(matches.at(-1)[1]) : "";
}

function extractChineseHeadingFromCurrentChunk(chunkText, procIndex) {
  return extractChineseHeadingCandidate(String(chunkText ?? "").slice(Math.max(0, procIndex - 220), procIndex));
}

function extractChineseProcedureExcerpt(chunkText, procIndex, chineseHeadingExcerpt = "") {
  const before = normalizeWhitespace(String(chunkText ?? "").slice(0, procIndex));
  if (!before) return "";
  const pageTrimmed = before.replace(/^[A-Za-z].*?\d+\s+/u, "");
  let excerptValue = pageTrimmed;
  if (chineseHeadingExcerpt) {
    const pos = excerptValue.lastIndexOf(chineseHeadingExcerpt);
    if (pos >= 0) excerptValue = excerptValue.slice(pos + chineseHeadingExcerpt.length).trim();
  }
  return normalizeWhitespace(excerptValue);
}

function extractEnglishTitleFromChunk(chunkText, procId) {
  const normalized = normalizeWhitespace(chunkText);
  const match = normalized.match(new RegExp(
    `${escapeRegex(procId)}\\.\\s*((?:T\\s+o|To|\\[[^\\]]+\\]|Method|Table|[A-Z])[^\n§]{1,240}?)(?:(?::|\\.)\\s*(?:§|Table\\b)|:\\s*$)`,
    "u",
  ));
  return match ? normalizeEnglishTitleDisplay(match[1]).replace(/[.:]\s*$/u, "") : "";
}

function extractEnglishProcedureExcerpt(chunkText, procId) {
  const text = normalizeWhitespace(chunkText);
  const procStart = text.indexOf(procId);
  if (procStart < 0) return "";
  const after = text.slice(procStart);
  const stopAt = after.search(/\b(?:Proc\. [234]\.\d+(?!\d)|[234]\.2\.\d+)\b/u);
  const excerptValue = stopAt > 20 ? after.slice(0, stopAt) : after.slice(0, 900);
  return normalizeEnglishTitleDisplay(excerptValue);
}

function extractCommentaryExcerpt(chunks) {
  const text = chunks.map((chunk) => getChunkText(chunk)).join("\n\n");
  return excerpt(text, 800);
}

function extractKeyConstants(text) {
  const matches = text.match(/[A-Z][A-Za-z \[\]\-]+?\[\d[\d,]*(?: ?\d\/\d)?\]/gu) ?? [];
  return uniqueStrings(matches).slice(0, 12);
}

function extractOperationSkeleton(text) {
  const operations = [];
  const normalized = normalizeWhitespace(text);
  const patterns = [
    { re: /\bcast out\b/giu, label: "cast out" },
    { re: /\bmultiply\b/giu, label: "multiply" },
    { re: /\bdivide\b/giu, label: "divide" },
    { re: /\bsubtract\b/giu, label: "subtract" },
    { re: /\badd\b/giu, label: "add" },
    { re: /\bcount\b/giu, label: "count" },
    { re: /\bnumber from\b/giu, label: "number from" },
    { re: /\bset out\b/giu, label: "set out" },
    { re: /\bremove\b/giu, label: "remove" },
    { re: /\btake\b/giu, label: "take" },
  ];

  for (const pattern of patterns) {
    if (pattern.re.test(normalized)) operations.push(pattern.label);
  }
  return uniqueStrings(operations).slice(0, 10);
}

function extractDistinctiveTermsFromTexts(...texts) {
  const value = texts.map((item) => String(item ?? "")).join(" ");
  const out = [];
  if (/推入蔀|入蔀|entry into the obscuration|entered obscuration/i.test(value)) out.push("obscuration_entry");
  if (/天正|celestial standard|first day of the first month/i.test(value)) out.push("celestial_standard");
  if (/闰月|intercalary month/i.test(value)) out.push("intercalary_month");
  if (/月食|lunar eclipse|eclipse/i.test(value)) out.push("lunar_eclipse");
  if (/五星|planet|conjunction/i.test(value)) out.push("planet_conjunction");
  if (/弦|望|crescent|full moon/i.test(value)) out.push("crescent_full_moon");
  if (/月明|moon at dawn|moon at dusk/i.test(value)) out.push("moon_lodge_motion");
  if (/日所入|sun at dawn|sun at dusk/i.test(value)) out.push("sun_lodge_motion");
  if (/蔀會|obscuration coincidence/i.test(value)) out.push("obscuration_coincidence");
  return uniqueStrings(out);
}

function inferProcedureFamily(anchorLike) {
  const text = `${anchorLike.cullen_proc_id ?? ""} ${anchorLike.english_title ?? ""} ${anchorLike.chinese_heading_excerpt ?? ""} ${anchorLike.chinese_procedure_excerpt ?? ""}`;
  if (/entry into the obscuration|入蔀/u.test(text)) return "obscuration_entry";
  if (/intercalary month|闰月/u.test(text)) return "intercalary_month";
  if (/celestial standard|天正/u.test(text)) return "tianzheng_shuori";
  if (/lunar eclipse|月食/u.test(text)) return "eclipse_chain";
  if (/moon at dawn|moon at dusk|月明/u.test(text)) return "du_lodge_moon";
  if (/sun at dawn|sun at dusk|日所入/u.test(text)) return "du_lodge_sun";
  if (/five planets|planet|五星/u.test(text)) return "planet_conjunction";
  if (/extinction|obliteration|灭/u.test(text)) return "mei_mie";
  return "unknown";
}

function inferSourceProcedureFamily(text, procedureTitle = "") {
  const value = `${procedureTitle} ${text}`;
  return inferProcedureFamily({
    cullen_proc_id: "",
    english_title: "",
    chinese_heading_excerpt: value,
    chinese_procedure_excerpt: value,
  });
}

function extractSourceOps(text) {
  const value = String(text ?? "");
  const ops = [];
  if (/置/u.test(value)) ops.push("set out");
  if (/乘/u.test(value)) ops.push("multiply");
  if (/除/u.test(value)) ops.push("divide");
  if (/減/u.test(value)) ops.push("subtract");
  if (/加/u.test(value)) ops.push("add");
  if (/命/u.test(value) || /筭/u.test(value)) ops.push("count");
  return uniqueStrings(ops);
}

function isTableLikeAnchor(anchor) {
  return /\btable\b/i.test(anchor.english_title)
    || /\btable\b/i.test(anchor.english_procedure_excerpt)
    || /表/u.test(anchor.chinese_heading_excerpt);
}

function buildChunkIndex(chunks) {
  const chunkById = new Map();
  const chunkBySeq = new Map();
  for (const chunk of chunks ?? []) {
    chunkById.set(chunk.id, chunk);
    const seq = parseChunkSequenceId(chunk.id);
    if (Number.isFinite(seq)) chunkBySeq.set(seq, chunk);
  }
  return { chunkById, chunkBySeq };
}

function getChunkWithSequence(chunkBySeq, seq) {
  return Number.isFinite(seq) ? chunkBySeq.get(seq) ?? null : null;
}

function nextChunkStartsNewProc(chunk) {
  return /\bProc\. [234]\.\d+(?!\d)/u.test(getChunkText(chunk));
}

function buildChunkGroups(item, chunkById, chunkBySeq) {
  const primaryChunk = chunkById.get(item.chunk_ids?.[0]) ?? null;
  if (!primaryChunk) {
    return {
      heading_chunk_ids: [],
      body_chunk_ids: [],
      commentary_chunk_ids: [],
      chunk_ids: [],
      chinese_heading_excerpt: "",
      chinese_procedure_excerpt: "",
      english_title: normalizeEnglishTitleDisplay(item.english_title ?? ""),
      english_procedure_excerpt: "",
      commentary_excerpt: "",
      combined_excerpt: "",
      current_chunk_text: "",
      heading_body_split: false,
    };
  }

  const primaryText = getChunkText(primaryChunk);
  const procIndex = findProcIndex(primaryText, item.proc_id);
  const primarySeq = parseChunkSequenceId(primaryChunk.id);
  const previousChunk = getChunkWithSequence(chunkBySeq, primarySeq - 1);
  const previousText = getChunkText(previousChunk);

  let chineseHeadingExcerpt = extractChineseHeadingFromCurrentChunk(primaryText, procIndex);
  const chineseProcedureExcerpt = extractChineseProcedureExcerpt(primaryText, procIndex, chineseHeadingExcerpt);

  const headingChunkIds = [];
  if (chineseHeadingExcerpt) {
    headingChunkIds.push(primaryChunk.id);
  } else {
    const previousHeading = extractChineseHeadingCandidate(previousText);
    if (previousHeading && chineseProcedureExcerpt) {
      chineseHeadingExcerpt = previousHeading;
      headingChunkIds.push(previousChunk.id);
    }
  }

  const bodyChunkIds = [primaryChunk.id];
  const commentaryChunkIds = [];
  let lookaheadSeq = primarySeq + 1;
  while (true) {
    const nextChunk = getChunkWithSequence(chunkBySeq, lookaheadSeq);
    if (!nextChunk) break;
    if (nextChunkStartsNewProc(nextChunk)) break;
    commentaryChunkIds.push(nextChunk.id);
    lookaheadSeq += 1;
  }

  const bodyChunks = bodyChunkIds.map((chunkId) => chunkById.get(chunkId)).filter(Boolean);
  const commentaryChunks = commentaryChunkIds.map((chunkId) => chunkById.get(chunkId)).filter(Boolean);
  const englishTitle = normalizeEnglishTitleDisplay(item.english_title || extractEnglishTitleFromChunk(primaryText, item.proc_id));
  const englishProcedureExcerpt = extractEnglishProcedureExcerpt(primaryText, item.proc_id);
  const commentaryExcerpt = extractCommentaryExcerpt(commentaryChunks);
  const chunkIds = uniqueStrings([...headingChunkIds, ...bodyChunkIds, ...commentaryChunkIds]);
  const combinedExcerpt = uniqueStrings([
    chineseHeadingExcerpt,
    chineseProcedureExcerpt,
    englishProcedureExcerpt,
    commentaryExcerpt,
  ]).join("\n\n");
  const currentChunkText = chunkIds.map((chunkId) => getChunkText(chunkById.get(chunkId))).filter(Boolean).join("\n\n");

  return {
    heading_chunk_ids: headingChunkIds,
    body_chunk_ids: bodyChunkIds,
    commentary_chunk_ids: commentaryChunkIds,
    chunk_ids: chunkIds,
    chinese_heading_excerpt: chineseHeadingExcerpt,
    chinese_procedure_excerpt: chineseProcedureExcerpt,
    english_title: englishTitle,
    english_procedure_excerpt: englishProcedureExcerpt,
    commentary_excerpt: commentaryExcerpt,
    combined_excerpt: combinedExcerpt,
    current_chunk_text: currentChunkText,
    heading_body_split: headingChunkIds.length > 0 && !headingChunkIds.every((chunkId) => bodyChunkIds.includes(chunkId)),
  };
}

function rawClaimText(claim) {
  return normalizeWhitespace(`${claim.procedure_name ?? ""} ${claim.formula_text ?? ""} ${claim.evidence_text ?? ""} ${claim.sentence ?? ""}`);
}

function claimBindingResult(anchor, strictClaims, rawClaims) {
  const relevantChunkIds = new Set([...(anchor.body_chunk_ids ?? []), ...(anchor.commentary_chunk_ids ?? [])]);
  const rawChunkClaims = (rawClaims ?? []).filter((claim) =>
    claim.system === anchor.system && relevantChunkIds.has(claim.evidence_chunk_id)
  );
  const strictChunkClaims = (strictClaims ?? []).filter((claim) =>
    claim.system === anchor.system && relevantChunkIds.has(claim.evidence_chunk_id)
  );

  const directClaims = strictChunkClaims.filter((claim) => {
    const claimText = rawClaimText(claim);
    return hasExactProcMention(claimText, anchor.cullen_proc_id)
      || textContainsNormalizedTitle(claimText, anchor.english_title)
      || (anchor.chinese_heading_excerpt && claimText.includes(anchor.chinese_heading_excerpt));
  });

  const procMentionsInBody = (anchor.body_chunk_ids ?? [])
    .map((chunkId) => (anchor.current_chunk_text.match(/\bProc\. [234]\.\d+(?!\d)/gu) ?? []).length)
    .reduce((sum, count) => sum + count, 0);

  const fallbackClaims = directClaims.length ? [] : strictChunkClaims.filter((claim) => {
    if (!anchor.procedure_family || anchor.procedure_family === "unknown") return false;
    if (claim.procedure_family !== anchor.procedure_family) return false;
    if (procMentionsInBody > 1) return false;
    const claimText = rawClaimText(claim);
    const overlap = extractDistinctiveTermsFromTexts(claimText).filter((term) =>
      (anchor.distinctive_terms ?? []).includes(term)
    );
    return overlap.length > 0;
  });

  const boundClaims = uniqueStrings([...directClaims, ...fallbackClaims].map((claim) => claim.claim_id));
  let claimBindingStatus = "bound";
  let claimBindingReason = "direct_proc_binding";

  if (!boundClaims.length) {
    if (isTableLikeAnchor(anchor)) {
      claimBindingStatus = "commentary_only";
      claimBindingReason = "commentary_only";
    } else if (rawChunkClaims.length || strictChunkClaims.length) {
      claimBindingStatus = "claim_exists_but_not_bound";
      claimBindingReason = "claim_exists_but_not_bound";
    } else {
      claimBindingStatus = "no_claim_extracted";
      claimBindingReason = "no_claim_extracted";
    }
  } else if (fallbackClaims.length && !directClaims.length) {
    claimBindingStatus = "needs_review";
    claimBindingReason = "family_distinctive_fallback";
  }

  return {
    claim_ids: boundClaims,
    claim_binding_status: claimBindingStatus,
    claim_binding_reason: claimBindingReason,
  };
}

function buildSourceContext(sourceSpansPayload, procedurePayload, coverageMatrix) {
  const spans = sourceSpansPayload?.spans ?? [];
  const procedures = procedurePayload?.procedures ?? [];
  const coverageEntries = coverageMatrix?.source_span_coverage ?? [];
  const procedureBySpanId = new Map(procedures.map((item) => [item.source_span_id, item]));
  const coverageBySpanId = new Map(coverageEntries.map((item) => [item.source_span_id, item]));
  return spans.map((span) => ({
    span,
    procedure: procedureBySpanId.get(span.id) ?? null,
    coverage: coverageBySpanId.get(span.id) ?? null,
  }));
}

function filterAlignmentDistinctiveTerms(terms) {
  return uniqueStrings(terms).filter((term) => !NON_DISTINCTIVE_ALIGNMENT_TERMS.has(term));
}

function scoreSourceCandidate(anchor, candidate) {
  const coverage = candidate.coverage;
  const procedure = candidate.procedure;
  const span = candidate.span;
  const spanText = span?.text ?? "";
  const procedureTitle = procedure?.title_guess ?? "";
  const sourceFamily = coverage?.procedure_family ?? inferSourceProcedureFamily(spanText, procedureTitle);
  const sourceDistinctiveTerms = filterAlignmentDistinctiveTerms(
    extractDistinctiveTermsFromTexts(spanText, procedureTitle, ...(coverage?.distinctive_terms ?? []))
  );
  const anchorDistinctiveTerms = filterAlignmentDistinctiveTerms(anchor.distinctive_terms ?? []);
  const sourceOps = extractSourceOps(spanText);
  const anchorTitle = normalizeChineseTitle(anchor.chinese_heading_excerpt);
  const sourceTitle = normalizeChineseTitle(procedureTitle || spanText.slice(0, 40));
  const titleOverlap = anchorTitle && sourceTitle && (anchorTitle.includes(sourceTitle) || sourceTitle.includes(anchorTitle));
  const familyMatch = anchor.procedure_family !== "unknown" && sourceFamily === anchor.procedure_family;
  const distinctiveOverlap = sourceDistinctiveTerms.filter((term) => anchorDistinctiveTerms.includes(term));
  const opOverlap = sourceOps.filter((op) => (anchor.operation_skeleton ?? []).includes(op));
  const manualHint = (MANUAL_SOURCE_SPAN_HINTS.get(anchor.cullen_proc_id) ?? []).includes(span.id);
  const genericOnly = !manualHint
    && !titleOverlap
    && !familyMatch
    && distinctiveOverlap.length === 0
    && opOverlap.every((op) => GENERIC_OPERATION_TYPES.has(op));

  let score = 0;
  if (manualHint) score += 100;
  if (familyMatch) score += 8;
  if (titleOverlap) score += 10;
  score += distinctiveOverlap.length * 4;
  score += opOverlap.length * 2;
  if ((coverage?.matched_cullen_anchors ?? []).includes(anchor.anchor_id) || (coverage?.matched_cullen_procedures ?? []).includes(anchor.cullen_proc_id)) score += 6;
  if ((coverage?.matched_cullen_anchors ?? []).includes(anchor.cullen_proc_id)) score += 6;

  return {
    source_span_id: span.id,
    score,
    familyMatch,
    titleOverlap,
    distinctiveOverlap,
    opOverlap,
    genericOnly,
    manualHint,
    sourceFamily,
  };
}

function resolveSourceAlignment(anchor, sourceContext) {
  const manualHints = uniqueStrings(MANUAL_SOURCE_SPAN_HINTS.get(anchor.cullen_proc_id) ?? []);
  if (manualHints.length) {
    return {
      source_span_candidates: manualHints,
      alignment_status: "manual_or_high_confidence_source_alignment",
      source_alignment_candidates: manualHints.map((source_span_id) => ({ source_span_id, score: 100, manualHint: true })),
      source_alignment_warnings: [],
    };
  }

  const scored = sourceContext
    .filter((candidate) => candidate.span?.source_id === anchor.system)
    .map((candidate) => scoreSourceCandidate(anchor, candidate))
    .filter((candidate) => !candidate.genericOnly)
    .filter((candidate) => candidate.titleOverlap || candidate.distinctiveOverlap.length > 0 || (candidate.familyMatch && candidate.opOverlap.length > 0));

  const sorted = scored.sort((left, right) => right.score - left.score || left.source_span_id.localeCompare(right.source_span_id));
  const titleMatched = sorted.filter((candidate) => candidate.titleOverlap);
  const topCandidate = sorted[0] ?? null;
  const secondCandidate = sorted[1] ?? null;
  const hasStableLead = topCandidate && (!secondCandidate || topCandidate.score - secondCandidate.score >= 4);
  const allowUniqueFamilyInference = Boolean(
    topCandidate
    && hasStableLead
    && anchor.procedure_family !== "unknown"
    && !/^another method$/iu.test(anchor.english_title ?? "")
    && topCandidate.familyMatch
    && topCandidate.distinctiveOverlap.length > 0
    && topCandidate.opOverlap.length >= 1
    && topCandidate.score >= 16
  );
  const accepted = titleMatched.length
    ? titleMatched
    : allowUniqueFamilyInference
      ? [topCandidate]
      : [];
  const sourceSpanCandidates = uniqueStrings(accepted.map((candidate) => candidate.source_span_id));
  const warnings = [];
  let alignmentStatus = "no_source_span_candidate";

  if (sourceSpanCandidates.length) {
    alignmentStatus = accepted.some((candidate) => candidate.manualHint)
      ? "manual_or_high_confidence_source_alignment"
      : "inferred_source_alignment";
  } else if (sorted.length) {
    alignmentStatus = "source_alignment_needs_review";
    warnings.push("source_alignment_low_score");
  } else {
    warnings.push("anchor_has_no_source_span_candidates");
  }

  return { source_span_candidates: sourceSpanCandidates, alignment_status: alignmentStatus, source_alignment_candidates: sorted.slice(0, 5), source_alignment_warnings: warnings };
}

function buildQualityTier(anchor) {
  const hasSource = (anchor.source_span_candidates ?? []).length > 0;
  const hasClaims = (anchor.claim_ids ?? []).length > 0;
  const hasOps = (anchor.operation_skeleton ?? []).length > 0;
  const hasBody = (anchor.body_chunk_ids ?? []).length > 0;
  const hasHeadingOrTitle = Boolean(anchor.english_title || anchor.chinese_heading_excerpt);

  if (hasSource && hasClaims && hasOps && hasBody && hasHeadingOrTitle) return "A_ready_for_phase2";
  if (!hasSource && hasClaims && hasOps && hasBody) return "B_needs_source_alignment";
  if (hasSource && !hasClaims) return "C_needs_claim_enrichment";
  return "D_needs_human_review";
}

function buildAnchorConfidence(anchor) {
  if (anchor.quality_tier === "A_ready_for_phase2") return "high";
  if (anchor.quality_tier === "B_needs_source_alignment" || anchor.quality_tier === "C_needs_claim_enrichment") return "medium";
  return "low";
}

function pageBoundsFromChunks(chunkIds, chunkById) {
  const pages = chunkIds
    .map((chunkId) => chunkById.get(chunkId))
    .filter(Boolean)
    .flatMap((chunk) => [chunk.page_start, chunk.page_end])
    .filter(Number.isFinite);
  return {
    page_start: pages.length ? Math.min(...pages) : null,
    page_end: pages.length ? Math.max(...pages) : null,
  };
}

function buildInitialAnchor(item, chunkById, chunkBySeq, strictClaims, rawClaims) {
  const chunkGroups = buildChunkGroups(item, chunkById, chunkBySeq);
  const family = MANUAL_FAMILY_OVERRIDES.get(item.proc_id) ?? inferProcedureFamily(chunkGroups);
  const preAnchor = {
    anchor_id: `cullen:anchor:${item.proc_id.toLowerCase().replace(/[^a-z0-9]+/gu, "-").replace(/^-+|-+$/gu, "")}`,
    cullen_proc_id: item.proc_id,
    system: item.system_guess,
    procedure_family: family,
    english_title: chunkGroups.english_title,
    ...pageBoundsFromChunks(chunkGroups.chunk_ids, chunkById),
    ...chunkGroups,
    key_constants: extractKeyConstants(`${chunkGroups.english_procedure_excerpt} ${chunkGroups.commentary_excerpt}`),
    operation_skeleton: extractOperationSkeleton(`${chunkGroups.english_procedure_excerpt} ${chunkGroups.commentary_excerpt}`),
    source_span_candidates: uniqueStrings(MANUAL_SOURCE_SPAN_HINTS.get(item.proc_id) ?? item.source_span_candidates ?? []),
    distinctive_terms: uniqueStrings([
      ...extractDistinctiveTermsFromTexts(
        chunkGroups.chinese_heading_excerpt,
        chunkGroups.chinese_procedure_excerpt,
        chunkGroups.english_title,
        chunkGroups.english_procedure_excerpt,
      ),
      family,
    ]),
    inventory_status: item.chapter === 4 ? "out_of_current_scope" : "needs_review",
    anchor_notes: uniqueStrings(item.notes ?? []).join("; "),
    warnings: [],
  };

  const binding = claimBindingResult(preAnchor, strictClaims, rawClaims);
  const warnings = uniqueStrings([
    !(preAnchor.chunk_ids ?? []).length ? "anchor_has_no_chunk_ids" : null,
    preAnchor.heading_body_split ? "heading_body_split" : null,
    (preAnchor.chunk_ids ?? []).length > 1 ? "multi_chunk_anchor" : null,
    !preAnchor.english_title ? "missing_english_title" : null,
    !preAnchor.chinese_heading_excerpt ? "missing_chinese_heading_excerpt" : null,
    !preAnchor.chinese_procedure_excerpt ? "missing_chinese_procedure_excerpt" : null,
    !preAnchor.english_procedure_excerpt ? "missing_english_procedure_excerpt" : null,
    !(preAnchor.operation_skeleton ?? []).length ? "anchor_has_no_operation_skeleton" : null,
    binding.claim_binding_reason !== "direct_proc_binding" ? binding.claim_binding_reason : null,
    !(preAnchor.source_span_candidates ?? []).length ? "anchor_has_no_source_span_candidates" : null,
  ]);

  const anchor = {
    ...preAnchor,
    ...binding,
    warnings,
  };
  anchor.quality_tier = buildQualityTier(anchor);
  anchor.anchor_confidence = buildAnchorConfidence(anchor);
  return anchor;
}

export function buildProcedureAnchorSet({ claims, chunks, procedureBank, rawClaims = [] }) {
  const inventory = buildProcedureInventory({ chunks });
  const { chunkById, chunkBySeq } = buildChunkIndex(chunks ?? []);
  const items = [];

  for (const item of inventory.items ?? []) {
    if (![2, 3].includes(item.chapter)) continue;
    items.push(buildInitialAnchor(item, chunkById, chunkBySeq, claims ?? [], rawClaims ?? []));
  }

  return {
    generated_at: new Date().toISOString(),
    note: "Machine-generated Cullen procedure anchors. Non-authoritative and intended for review/debug support.",
    items,
  };
}

export function enrichProcedureAnchorSet(anchorPayload, coverageMatrix, procedurePayload, sourceSpansPayload) {
  const sourceContext = buildSourceContext(sourceSpansPayload, procedurePayload, coverageMatrix);
  const items = (anchorPayload?.items ?? []).map((anchor) => {
    const sourceAlignment = resolveSourceAlignment(anchor, sourceContext);
    const merged = {
      ...anchor,
      source_span_candidates: uniqueStrings([
        ...(anchor.source_span_candidates ?? []),
        ...(sourceAlignment.source_span_candidates ?? []),
      ]),
      alignment_status: sourceAlignment.alignment_status,
      source_alignment_candidates: sourceAlignment.source_alignment_candidates,
    };
    merged.warnings = uniqueStrings([
      ...(anchor.warnings ?? []).filter((warning) => warning !== "anchor_has_no_source_span_candidates" && warning !== "source_alignment_low_score"),
      ...(sourceAlignment.source_alignment_warnings ?? []),
      !(merged.source_span_candidates ?? []).length ? "anchor_has_no_source_span_candidates" : null,
      !(merged.claim_ids ?? []).length ? merged.claim_binding_reason : null,
    ]);
    merged.quality_tier = buildQualityTier(merged);
    merged.anchor_confidence = buildAnchorConfidence(merged);
    merged.inventory_status = merged.source_span_candidates.length ? "anchored" : "needs_review";
    return merged;
  });

  return {
    ...anchorPayload,
    generated_at: new Date().toISOString(),
    items,
  };
}

export function renderProcedureAnchorsMarkdown(payload) {
  const lines = [
    "# Cullen Procedure Anchors",
    "",
    "Machine-generated procedure anchor layer. This is not final gold.",
    "",
    `Generated: ${payload.generated_at}`,
    "",
  ];

  for (const anchor of payload.items ?? []) {
    lines.push(`## ${anchor.cullen_proc_id}`);
    lines.push(`- anchor_id: ${anchor.anchor_id}`);
    lines.push(`- system: ${anchor.system}`);
    lines.push(`- procedure_family: ${anchor.procedure_family}`);
    lines.push(`- quality_tier: ${anchor.quality_tier}`);
    lines.push(`- alignment_status: ${anchor.alignment_status ?? "none"}`);
    lines.push(`- claim_binding_status: ${anchor.claim_binding_status ?? "none"}`);
    lines.push(`- english_title: ${anchor.english_title || "none"}`);
    lines.push(`- pages: ${anchor.page_start ?? "null"}-${anchor.page_end ?? "null"}`);
    lines.push(`- heading_chunk_ids: ${(anchor.heading_chunk_ids ?? []).join(", ") || "none"}`);
    lines.push(`- body_chunk_ids: ${(anchor.body_chunk_ids ?? []).join(", ") || "none"}`);
    lines.push(`- commentary_chunk_ids: ${(anchor.commentary_chunk_ids ?? []).join(", ") || "none"}`);
    lines.push(`- chunk_ids: ${(anchor.chunk_ids ?? []).join(", ") || "none"}`);
    lines.push(`- chinese_heading_excerpt: ${anchor.chinese_heading_excerpt || "none"}`);
    lines.push(`- chinese_procedure_excerpt: ${anchor.chinese_procedure_excerpt || "none"}`);
    lines.push(`- english_procedure_excerpt: ${anchor.english_procedure_excerpt || "none"}`);
    lines.push(`- commentary_excerpt: ${anchor.commentary_excerpt || "none"}`);
    lines.push(`- combined_excerpt: ${anchor.combined_excerpt || "none"}`);
    lines.push(`- claim_ids: ${(anchor.claim_ids ?? []).join(", ") || "none"}`);
    lines.push(`- key_constants: ${(anchor.key_constants ?? []).join(", ") || "none"}`);
    lines.push(`- operation_skeleton: ${(anchor.operation_skeleton ?? []).join(" | ") || "none"}`);
    lines.push(`- source_span_candidates: ${(anchor.source_span_candidates ?? []).join(", ") || "none"}`);
    lines.push(`- anchor_confidence: ${anchor.anchor_confidence}`);
    lines.push(`- anchor_notes: ${anchor.anchor_notes ?? ""}`);
    lines.push(`- warnings: ${(anchor.warnings ?? []).join(", ") || "none"}`);
    lines.push("");
  }

  return `${lines.join("\n")}\n`;
}

export async function writeProcedureAnchorOutputs(payload) {
  await writeJson(CULLEN_PROCEDURE_ANCHOR_JSON, payload);
  const target = resolveRepoPath(CULLEN_PROCEDURE_ANCHOR_MD);
  await fs.mkdir(path.dirname(target), { recursive: true });
  await fs.writeFile(target, renderProcedureAnchorsMarkdown(payload), "utf8");
}

export function findAnchorsForSourceSpan(anchorPayload, sourceSpanId) {
  return (anchorPayload.items ?? []).filter((anchor) => (anchor.source_span_candidates ?? []).includes(sourceSpanId));
}

export function findAnchorsForPage(anchorPayload, pageNumber) {
  return (anchorPayload.items ?? []).filter((anchor) =>
    Number.isFinite(anchor.page_start)
    && Number.isFinite(anchor.page_end)
    && pageNumber >= anchor.page_start
    && pageNumber <= anchor.page_end
  );
}

function normalizeProcQuery(value) {
  const text = String(value ?? "").trim();
  if (!text) return "";
  if (/^proc\./i.test(text)) return text.replace(/\s+/gu, " ").trim().toLowerCase();
  return `proc. ${text}`.toLowerCase();
}

export function findAnchorsForProc(anchorPayload, procQuery) {
  const normalized = normalizeProcQuery(procQuery);
  return (anchorPayload.items ?? []).filter((anchor) =>
    normalizeProcQuery(anchor.cullen_proc_id) === normalized
    || normalizeProcQuery(anchor.english_title) === normalized
  );
}

export function sanitizeForFileSegment(value) {
  return String(value ?? "")
    .replace(/[:/\\\s]+/gu, "-")
    .replace(/[^a-zA-Z0-9.-]+/gu, "-")
    .replace(/-+/gu, "-")
    .replace(/^-+|-+$/gu, "");
}

export async function writeDebugMarkdown(name, content) {
  const filePath = resolveRepoPath(path.join(CULLEN_PROCEDURE_DEBUG_DIR, name));
  await fs.mkdir(path.dirname(filePath), { recursive: true });
  await fs.writeFile(filePath, content, "utf8");
  return filePath;
}

export function collectAnchorWarnings(anchor) {
  return uniqueStrings(anchor.warnings ?? []);
}

export function collectAnchorConstants(anchors) {
  return uniqueStrings((anchors ?? []).flatMap((anchor) => anchor.key_constants ?? []));
}

export function collectAnchorOperations(anchors) {
  return uniqueStrings((anchors ?? []).flatMap((anchor) => anchor.operation_skeleton ?? []));
}

export function collectAnchorSourceSpans(anchors) {
  return uniqueStrings((anchors ?? []).flatMap((anchor) => anchor.source_span_candidates ?? []));
}

export function chooseBetterDiagnostic(left, right) {
  const strengthScore = { strong: 4, medium: 3, weak: 2, generic_only: 1 };
  const qualityScore = { good: 4, plausible: 3, noisy: 2, wrong: 1, none: 0 };
  const leftStrength = strengthScore[left?.match_strength ?? "weak"] ?? 0;
  const rightStrength = strengthScore[right?.match_strength ?? "weak"] ?? 0;
  if (rightStrength !== leftStrength) return rightStrength > leftStrength ? right : left;
  const leftQuality = qualityScore[left?.alignment_quality ?? "none"] ?? 0;
  const rightQuality = qualityScore[right?.alignment_quality ?? "none"] ?? 0;
  return rightQuality > leftQuality ? right : left;
}
