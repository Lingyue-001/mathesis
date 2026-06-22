import fs from "node:fs/promises";
import path from "node:path";
import { resolveRepoPath, writeJson } from "./cullen-oracle-common.mjs";

export const CULLEN_PROCEDURE_INVENTORY_JSON = "tmp/procedure-ir/cullen-procedure-inventory.json";
export const CULLEN_PROCEDURE_INVENTORY_MD = "tmp/procedure-ir/cullen-procedure-inventory.md";
export const CULLEN_PROCEDURE_COMPLETENESS_AUDIT_JSON = "tmp/procedure-ir/cullen-procedure-completeness-audit.json";
export const CULLEN_PROCEDURE_COMPLETENESS_AUDIT_MD = "tmp/procedure-ir/cullen-procedure-completeness-audit.md";

const CHAPTER_SYSTEM_MAP = {
  2: "santong",
  3: "sifen",
  4: "qianxiang",
};

const PROC_RE = /Proc\. (([234])\.(\d+))(?!\d)/gu;

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

function normalizeTitle(value) {
  return normalizeWhitespace(value).replace(/\bT\s+o\b/giu, "To");
}

function escapeRegex(value) {
  return String(value ?? "").replace(/[.*+?^${}()|[\]\\]/gu, "\\$&");
}

function parseChunkSequenceId(chunkId) {
  const match = String(chunkId ?? "").match(/cullen:chunk:(\d+)/u);
  return match ? Number(match[1]) : null;
}

function excerptBefore(text, index, maxChars = 180) {
  const start = Math.max(0, index - maxChars);
  return normalizeWhitespace(text.slice(start, index));
}

function excerptAfter(text, index, maxChars = 520) {
  return normalizeWhitespace(text.slice(index, index + maxChars));
}

function getChineseHeadingExcerpt(chunkText, procIndex) {
  const raw = excerptBefore(chunkText, procIndex, 220);
  if (!raw) return "";
  const splitIndex = Math.max(
    raw.lastIndexOf("2.2."),
    raw.lastIndexOf("3.2."),
    raw.lastIndexOf("4.2."),
    raw.lastIndexOf("§"),
  );
  return normalizeWhitespace(splitIndex >= 0 ? raw.slice(splitIndex + 1) : raw);
}

function getEnglishProcedureExcerpt(chunkText, procIndex) {
  const after = excerptAfter(chunkText, procIndex, 560);
  const stopAt = after.search(/\b(?:Proc\. [234]\.\d+(?!\d)|The [A-Z][a-z]+ .* system \d+|4\.2\.\d|3\.2\.\d|2\.2\.\d)\b/u);
  if (stopAt > 40) return normalizeWhitespace(after.slice(0, stopAt));
  return after;
}

function getCommentaryExcerpt(chunkText, procIndex) {
  const after = excerptAfter(chunkText, procIndex, 1200);
  const firstSection = after.indexOf("§");
  if (firstSection < 0) return "";
  const commentaryStart = after.indexOf(". ", firstSection);
  if (commentaryStart < 0) return "";
  return normalizeWhitespace(after.slice(commentaryStart + 2, commentaryStart + 380));
}

function detectSourceTextQuality(chineseHeadingExcerpt, chunkText) {
  const text = `${chineseHeadingExcerpt} ${chunkText}`;
  const weirdCount = (text.match(/[�]/gu) ?? []).length;
  const hanCount = (text.match(/\p{Script=Han}/gu) ?? []).length;
  if (weirdCount > 0) return "garbled";
  if (hanCount > 0) return "good";
  return "mixed";
}

function inferProcedureFamily(procId, englishTitle, chineseHeadingExcerpt = "") {
  const text = `${procId} ${englishTitle} ${chineseHeadingExcerpt}`.toLowerCase();
  if (/entry into the obscuration|entry into the era|入蔀|入纪/u.test(text)) return "obscuration_entry";
  if (/intercalary month|闰月/u.test(text)) return "intercalary_month";
  if (/celestial standard|conjunction|天正|朔日/u.test(text)) return "tianzheng_shuori";
  if (/eclipse|月食/u.test(text)) return "eclipse_chain";
  if (/sun at dawn|sun at dusk|sun .* full moon|日.*所入/u.test(text)) return "du_lodge_sun";
  if (/moon at dawn|moon at dusk|moon .* entered|月.*所入/u.test(text)) return "du_lodge_moon";
  if (/five planets|planet|五星/u.test(text)) return "planet_conjunction";
  if (/extinction|obliteration|灭/u.test(text)) return "mei_mie";
  return "unknown";
}

function extractKeyConstants(text) {
  const matches = text.match(/[A-Z][A-Za-z \[\]\-]+?\[\d[\d,]*(?: ?\d\/\d)?\]/gu) ?? [];
  return uniqueStrings(matches).slice(0, 8);
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

  return uniqueStrings(operations).slice(0, 8);
}

function buildProcId(chapter, number) {
  return `Proc. ${chapter}.${number}`;
}

function parseTitleFromTail(procId, tail) {
  const pattern = new RegExp(
    `${escapeRegex(procId)}\\.\\s*((?:T\\s+o|To|\\[[^\\]]+\\]|[A-Z])[^§]{1,240}?)(?:(?::|\\.)\\s*(?:§|Table\\b)|:\\s*$)`,
    "u",
  );
  const match = String(tail ?? "").match(pattern);
  if (!match) return "";
  return normalizeTitle(match[1]).replace(/[.:]\s*$/u, "");
}

function scoreProcOccurrence(procId, chunkText, index) {
  const tail = chunkText.slice(index, index + 480);
  let score = 1;
  if (parseTitleFromTail(procId, tail)) score += 5;
  if (/§\d+/u.test(tail)) score += 3;
  if (/\bTable\b/u.test(tail)) score += 2;
  if (/\p{Script=Han}/u.test(chunkText.slice(Math.max(0, index - 120), index))) score += 1;
  return score;
}

function locateProcItem(procId, chunks) {
  let best = null;
  for (const chunk of chunks ?? []) {
    const chunkText = normalizeWhitespace(chunk.normalized_text ?? chunk.text ?? "");
    const procMatch = new RegExp(`${escapeRegex(procId)}(?!\\d)`, "u").exec(chunkText);
    if (!procMatch) continue;
    const index = procMatch.index ?? 0;
    const score = scoreProcOccurrence(procId, chunkText, index);
    if (!best || score > best.score) {
      best = { chunk, chunkText, index, score };
    }
  }
  return best;
}

function inventoryItemFromLocated(procId, chapter, located, anchorByProcId, sourceSpanHints) {
  const anchor = anchorByProcId.get(procId) ?? null;
  if (!located) {
    return {
      proc_id: procId,
      chapter,
      system_guess: CHAPTER_SYSTEM_MAP[chapter] ?? "unknown",
      page_start: null,
      page_end: null,
      chunk_ids: [],
      english_title: "",
      chinese_heading_excerpt: "",
      english_procedure_excerpt: "",
      commentary_excerpt: "",
      source_text_quality: "missing",
      anchor_status: anchor ? "needs_review" : "unanchored",
      anchor_id: anchor?.anchor_id ?? null,
      source_span_candidates: uniqueStrings(anchor?.source_span_candidates ?? sourceSpanHints.get(procId) ?? []),
      alignment_status: "no_chunk",
      notes: ["missing_chunk_for_proc_id"],
    };
  }

  const { chunk, chunkText, index } = located;
  const anchorStatus = chapter === 4
    ? (anchor ? ((anchor.source_span_candidates ?? []).length ? "anchored" : "out_of_current_scope") : "out_of_current_scope")
    : (anchor ? ((anchor.source_span_candidates ?? []).length ? "anchored" : "needs_review") : "unanchored");

  return {
    proc_id: procId,
    chapter,
    system_guess: CHAPTER_SYSTEM_MAP[chapter] ?? "unknown",
    page_start: chunk.page_start ?? null,
    page_end: chunk.page_end ?? null,
    chunk_ids: [chunk.id],
    english_title: parseTitleFromTail(procId, chunkText.slice(index, index + 480)),
    chinese_heading_excerpt: getChineseHeadingExcerpt(chunkText, index),
    english_procedure_excerpt: getEnglishProcedureExcerpt(chunkText, index),
    commentary_excerpt: getCommentaryExcerpt(chunkText, index),
    source_text_quality: detectSourceTextQuality(getChineseHeadingExcerpt(chunkText, index), chunkText),
    anchor_status: anchorStatus,
    anchor_id: anchor?.anchor_id ?? null,
    source_span_candidates: uniqueStrings(anchor?.source_span_candidates ?? sourceSpanHints.get(procId) ?? []),
    alignment_status: (anchor?.source_span_candidates ?? sourceSpanHints.get(procId) ?? []).length
      ? "linked_source_span_candidate"
      : "no_source_span_candidate",
    notes: uniqueStrings([
      parseTitleFromTail(procId, chunkText.slice(index, index + 480)) ? null : "missing_english_title",
      getChineseHeadingExcerpt(chunkText, index) ? null : "missing_chinese_heading_excerpt",
      chapter === 4 ? "chapter_4_inventory_only" : null,
    ]),
  };
}

function buildAnchorLookup(anchorPayload) {
  return new Map((anchorPayload?.items ?? []).map((item) => [item.cullen_proc_id, item]));
}

function buildSourceSpanHintMap(existingAnchors) {
  const hints = new Map();
  for (const anchor of existingAnchors?.items ?? []) {
    if (!(anchor.source_span_candidates ?? []).length) continue;
    hints.set(anchor.cullen_proc_id, uniqueStrings(anchor.source_span_candidates));
  }
  return hints;
}

export function buildProcedureInventory({ chunks, existingAnchors = null }) {
  const anchorByProcId = buildAnchorLookup(existingAnchors);
  const sourceSpanHints = buildSourceSpanHintMap(existingAnchors);
  const items = [];

  for (let number = 1; number <= 31; number += 1) {
    const procId = buildProcId(2, number);
    items.push(inventoryItemFromLocated(procId, 2, locateProcItem(procId, chunks), anchorByProcId, sourceSpanHints));
  }

  for (let number = 1; number <= 53; number += 1) {
    const procId = buildProcId(3, number);
    items.push(inventoryItemFromLocated(procId, 3, locateProcItem(procId, chunks), anchorByProcId, sourceSpanHints));
  }

  const seenChapter4 = new Set();
  for (const chunk of chunks ?? []) {
    const chunkText = normalizeWhitespace(chunk.normalized_text ?? chunk.text ?? "");
    for (const match of chunkText.matchAll(PROC_RE)) {
      const procId = `Proc. ${match[1]}`;
      if (!procId.startsWith("Proc. 4.") || seenChapter4.has(procId)) continue;
      seenChapter4.add(procId);
      items.push(inventoryItemFromLocated(procId, 4, locateProcItem(procId, chunks), anchorByProcId, sourceSpanHints));
    }
  }

  items.sort((left, right) => {
    const leftSeq = Number(String(left.proc_id).split(". ").at(-1)?.split(".")[1] ?? 0);
    const rightSeq = Number(String(right.proc_id).split(". ").at(-1)?.split(".")[1] ?? 0);
    return left.chapter - right.chapter || leftSeq - rightSeq;
  });

  return {
    generated_at: new Date().toISOString(),
    note: "Machine-generated Cullen procedure inventory from current chunk extraction.",
    items,
  };
}

export function buildAnchorSeedFromInventoryItem(item, { chunksById, claimsById = null, sourceSpanHints = new Map() }) {
  const chunkTexts = (item.chunk_ids ?? [])
    .map((chunkId) => normalizeWhitespace(chunksById.get(chunkId)?.normalized_text ?? chunksById.get(chunkId)?.text ?? ""))
    .filter(Boolean);
  const currentChunkText = chunkTexts.join("\n\n");
  const claimIds = [];

  for (const claim of claimsById?.values?.() ?? []) {
    if (!(item.chunk_ids ?? []).includes(claim.evidence_chunk_id)) continue;
    const claimText = normalizeWhitespace(`${claim.formula_text ?? ""} ${claim.evidence_text ?? ""}`);
    if (claimText.includes(item.proc_id) || currentChunkText.includes(claimText.slice(0, 80))) {
      claimIds.push(claim.claim_id);
    }
  }

  const sourceSpanCandidates = uniqueStrings(sourceSpanHints.get(item.proc_id) ?? item.source_span_candidates ?? []);
  const procedureFamily = inferProcedureFamily(item.proc_id, item.english_title, item.chinese_heading_excerpt);
  const keyConstants = extractKeyConstants(currentChunkText);
  const operationSkeleton = extractOperationSkeleton(currentChunkText);
  const warnings = uniqueStrings([
    !(item.chunk_ids ?? []).length ? "anchor_has_no_chunk_ids" : null,
    !claimIds.length ? "anchor_has_no_claim_ids" : null,
    !sourceSpanCandidates.length ? "anchor_has_no_source_span_candidates" : null,
    procedureFamily === "unknown" ? "anchor_family_needs_review" : null,
  ]);

  return {
    anchor_id: `cullen:anchor:${item.proc_id.toLowerCase().replace(/[^a-z0-9]+/gu, "-").replace(/^-+|-+$/gu, "")}`,
    cullen_proc_id: item.proc_id,
    system: item.system_guess,
    procedure_family: procedureFamily,
    english_title: item.english_title,
    page_start: item.page_start,
    page_end: item.page_end,
    chunk_ids: uniqueStrings(item.chunk_ids),
    claim_ids: uniqueStrings(claimIds),
    key_constants: keyConstants,
    operation_skeleton: operationSkeleton,
    source_span_candidates: sourceSpanCandidates,
    anchor_confidence: sourceSpanCandidates.length ? "high" : (claimIds.length ? "medium" : "low"),
    anchor_notes: item.notes?.join("; ") || "",
    warnings,
    inventory_status: item.chapter === 4
      ? "out_of_current_scope"
      : (sourceSpanCandidates.length ? "anchored" : "needs_review"),
    current_chunk_text: currentChunkText,
    distinctive_terms: uniqueStrings([procedureFamily]),
  };
}

export function renderProcedureInventoryMarkdown(payload) {
  const lines = [
    "# Cullen Procedure Inventory",
    "",
    "Machine-generated inventory from the current Cullen chunks.",
    "",
    `Generated: ${payload.generated_at}`,
    "",
  ];

  for (const item of payload.items ?? []) {
    lines.push(`## ${item.proc_id}`);
    lines.push(`- chapter: ${item.chapter}`);
    lines.push(`- system_guess: ${item.system_guess}`);
    lines.push(`- pages: ${item.page_start ?? "null"}-${item.page_end ?? "null"}`);
    lines.push(`- chunk_ids: ${(item.chunk_ids ?? []).join(", ") || "none"}`);
    lines.push(`- english_title: ${item.english_title || "none"}`);
    lines.push(`- chinese_heading_excerpt: ${item.chinese_heading_excerpt || "none"}`);
    lines.push(`- english_procedure_excerpt: ${item.english_procedure_excerpt || "none"}`);
    lines.push(`- commentary_excerpt: ${item.commentary_excerpt || "none"}`);
    lines.push(`- source_text_quality: ${item.source_text_quality}`);
    lines.push(`- anchor_status: ${item.anchor_status}`);
    lines.push(`- anchor_id: ${item.anchor_id ?? "none"}`);
    lines.push(`- source_span_candidates: ${(item.source_span_candidates ?? []).join(", ") || "none"}`);
    lines.push(`- alignment_status: ${item.alignment_status}`);
    lines.push(`- notes: ${(item.notes ?? []).join(", ") || "none"}`);
    lines.push("");
  }

  return `${lines.join("\n")}\n`;
}

export async function writeProcedureInventoryOutputs(payload) {
  await writeJson(CULLEN_PROCEDURE_INVENTORY_JSON, payload);
  const target = resolveRepoPath(CULLEN_PROCEDURE_INVENTORY_MD);
  await fs.mkdir(path.dirname(target), { recursive: true });
  await fs.writeFile(target, renderProcedureInventoryMarkdown(payload), "utf8");
}

export function buildProcedureIdSet(items) {
  return new Set((items ?? []).map((item) => item.proc_id ?? item.cullen_proc_id).filter(Boolean));
}

export function chapterFromProcId(procId) {
  const match = String(procId ?? "").match(/Proc\. ([234])\.\d+(?!\d)/u);
  return match ? Number(match[1]) : null;
}

export function sortProcIds(procIds) {
  return [...new Set(procIds)]
    .sort((left, right) => {
      const leftMatch = String(left).match(/Proc\. ([234])\.(\d+)(?!\d)/u);
      const rightMatch = String(right).match(/Proc\. ([234])\.(\d+)(?!\d)/u);
      if (!leftMatch || !rightMatch) return String(left).localeCompare(String(right));
      return Number(leftMatch[1]) - Number(rightMatch[1]) || Number(leftMatch[2]) - Number(rightMatch[2]);
    });
}
