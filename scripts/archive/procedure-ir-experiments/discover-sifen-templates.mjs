import fs from "node:fs/promises";
import path from "node:path";
import { normalizeWhitespace, readJson, resolveRepoPath, writeJson } from "./cullen-oracle-common.mjs";

// Template discovery only. This script discovers repeated clause forms in the
// current Cullen Sifen chunks; it does not assign meaning, create gold data, use
// embeddings, or call an LLM. Meaning assignment happens later via LLM/human
// review.

const INPUT_PATH = "tmp/procedure-ir/cullen-chunks.json";
const OUTPUT_JSON_PATH = "tmp/procedure-ir/sifen-template-discovery.json";
const OUTPUT_MD_PATH = "tmp/procedure-ir/sifen-template-discovery.md";

const TOP_N = 50;
const EXAMPLE_LIMIT = 10;
const CHINESE_RE = /[\u3400-\u9fff]/u;
const CHINESE_NUMERAL_RE = /[零〇一二三四五六七八九十百千萬万億亿兩]+/gu;
const ARABIC_NUMBER_RE = /\b\d[\d,]*(?:\.\d+)?\b/gu;
const PAGE_GARBAGE_RE = /(?:–|-)\s*\d{3,5}\s*(?:–|-)/u;
const CHINESE_SIGNAL_RE = /(?:置|以|滿|不滿|得|減|乘|除|謂之|名為|名曰|為|餘|積|法|數|月|日|歲|分|率|會|蔀|章)/u;
const CROSS_REFERENCE_RE = /^(?:see\s+)?(?:Proc\.|section\s+§|§\s*\d+\s+see\b|see\s+section|see\s+Proc\.)/iu;
const TABLE_FRAGMENT_RE = /\b(?:T able|Table\s+\d|year-name|Celestial Era|Terrestrial Era|Anthropic Era|row|column)\b/iu;

const PRESET_PAIR_PATTERNS = [
  [/^置\[OBJECT\]$/u, /^Set out \[OBJECT\]$/u],
  [/^以\[OBJECT\]乘之$/u, /^Multiply (?:by \[OBJECT\]|\[OBJECT\] by \[OBJECT\])$/u],
  [/^(?:滿|如)\[OBJECT\]得一$/u, /^Count one for each \[OBJECT\] filled$/u],
  [/^不滿為\[RESULT\]$/u, /^What does not fill \[OBJECT\] is \[RESULT\]$/u],
  [/^(?:名為|名曰|謂之)\[RESULT\]$/u, /^(?:Call this|called) \[RESULT\]$/u],
  [/^餘為\[RESULT\]$/u, /^The remainder is \[RESULT\]$/u]
];

const STRENGTH_RANK = {
  single_zh_single_en: 4,
  ordinal_aligned: 3,
  near_ordinal_aligned: 2,
  targeted_prespecified_same_unit: 2,
  one_to_many_ambiguous: 1,
  same_unit_cooccurrence: 0
};

function excerpt(text, length = 180) {
  const clean = normalizeWhitespace(text || "");
  return clean.length > length ? `${clean.slice(0, length - 1)}…` : clean;
}

function pageLabel(chunk) {
  const start = chunk.book_page_start || "";
  const end = chunk.book_page_end || "";
  return start === end ? String(start) : `${start}-${end}`;
}

function chunkMeta(chunk) {
  return {
    chunk_id: chunk.id,
    unit_id: chunk.unit_id,
    procedure_id: chunk.procedure_id,
    section_path: chunk.section_path,
    book_page_start: chunk.book_page_start,
    book_page_end: chunk.book_page_end
  };
}

function clauseMeta(chunk, index, language, rawClause, normalizedTemplate, structuralTemplate, flags = {}) {
  return {
    clause_id: `${chunk.id}:${language}:${index + 1}`,
    language,
    raw_clause: rawClause,
    number_normalized_template: normalizedTemplate,
    structural_template: structuralTemplate,
    template: structuralTemplate,
    ...chunkMeta(chunk),
    ...flags
  };
}

function isPurePageOrNumber(text) {
  const clean = normalizeWhitespace(text);
  return !clean
    || PAGE_GARBAGE_RE.test(clean)
    || /^[\d\s,./+\-–—×*()[\]\u00bc-\u00be=]+$/u.test(clean)
    || /^[零〇一二三四五六七八九十百千萬万億亿兩\s]+$/u.test(clean);
}

function shouldKeepChineseClause(clause) {
  const clean = normalizeWhitespace(clause);
  if (isPurePageOrNumber(clean)) return false;
  const zhChars = [...clean.matchAll(/[\u3400-\u9fff]/gu)].length;
  if (zhChars <= 1) return false;
  if (zhChars <= 2 && !CHINESE_SIGNAL_RE.test(clean)) return false;
  return true;
}

function shouldKeepEnglishClause(clause) {
  const clean = normalizeWhitespace(clause);
  if (isPurePageOrNumber(clean)) return false;
  if (TABLE_FRAGMENT_RE.test(clean)) return false;
  if (/^[A-Z]$/u.test(clean)) return false;
  if (clean.length < 3) return false;
  return true;
}

function isCrossReferenceClause(clause) {
  return CROSS_REFERENCE_RE.test(normalizeWhitespace(clause));
}

function normalizeChineseNumbers(text) {
  return normalizeWhitespace(text)
    .replace(CHINESE_NUMERAL_RE, "[NUM]")
    .replace(ARABIC_NUMBER_RE, "[NUM]");
}

function structuralChineseTemplate(clause) {
  const normalized = normalizeChineseNumbers(clause);
  if (/不滿為/u.test(normalized)) return "不滿為[RESULT]";
  if (/不盡為/u.test(normalized)) return "不盡為[RESULT]";
  if (/滿.+得一/u.test(normalized)) return "滿[OBJECT]得一";
  if (/如.+得一/u.test(normalized)) return "如[OBJECT]得一";
  if (/^置/u.test(normalized)) return "置[OBJECT]";
  if (/以.+乘之/u.test(normalized)) return "以[OBJECT]乘之";
  if (/以.+除之/u.test(normalized)) return "以[OBJECT]除之";
  if (/名為/u.test(normalized)) return "名為[RESULT]";
  if (/名曰/u.test(normalized)) return "名曰[RESULT]";
  if (/謂之/u.test(normalized)) return "謂之[RESULT]";
  if (/餘為/u.test(normalized)) return "餘為[RESULT]";
  if (/滿\[NUM\]除去之/u.test(normalized)) return "[OBJECT]滿[NUM]除去之";
  if (/除去之/u.test(normalized)) return "[OBJECT]除去之";
  return normalized;
}

function protectEnglish(text) {
  const replacements = [];
  const protect = (regex, source) => source.replace(regex, (match) => {
    const token = `__PROTECTED_${replacements.length}__`;
    replacements.push(match);
    return token;
  });
  let protectedText = text;
  protectedText = protect(/\bProc\.\s*\d+(?:\.\d+)+/gu, protectedText);
  protectedText = protect(/\b(?:e\.g|i\.e|cf|ibid|Fig|No|vol|ed|c)\./giu, protectedText);
  protectedText = protect(/\b\d+\.\d+\b/gu, protectedText);
  return {
    protectedText,
    restore(value) {
      return value.replace(/__PROTECTED_(\d+)__/gu, (_, index) => replacements[Number(index)] || "");
    }
  };
}

function splitEnglishClauses(text) {
  const { protectedText, restore } = protectEnglish(text || "");
  return protectedText
    .split(/(?<=[.;:])\s+|\n+/u)
    .map((clause) => normalizeWhitespace(restore(clause)))
    .filter(Boolean);
}

function splitChineseClauses(text) {
  return (text || "")
    .split(/[，。．；;：:\n]+/u)
    .map((clause) => normalizeWhitespace(clause))
    .filter(Boolean);
}

function normalizeEnglishNumbers(text) {
  return normalizeWhitespace(text)
    .replace(/§\s*\d+/gu, "[UNIT]")
    .replace(/\[[^\]]*\d[^\]]*\]/gu, "[BRACKETED]")
    .replace(ARABIC_NUMBER_RE, "[NUM]");
}

function stripLeadingUnit(template) {
  return normalizeWhitespace(template.replace(/^\[UNIT\]\s*/u, ""));
}

function structuralEnglishTemplate(clause) {
  const normalized = stripLeadingUnit(normalizeEnglishNumbers(clause));
  if (/^Set out\b/iu.test(normalized)) return "Set out [OBJECT]";
  if (/^(?:Further,\s*)?(?:and\s+)?multiply\b.+\bby\b/iu.test(normalized)) return "Multiply [OBJECT] by [OBJECT]";
  if (/^Multiply by\b/iu.test(normalized)) return "Multiply by [OBJECT]";
  if (/\bcount one for each\b.+\bfilled\b/iu.test(normalized)) return "Count one for each [OBJECT] filled";
  if (/^Call this\b/iu.test(normalized)) return "Call this [RESULT]";
  if (/\bcalled\b/iu.test(normalized)) return "called [RESULT]";
  if (/^The remainder is\b/iu.test(normalized)) return "The remainder is [RESULT]";
  if (/^What does not fill\b/iu.test(normalized)) return "What does not fill [OBJECT] is [RESULT]";
  if (/\bcast out\b/iu.test(normalized)) return "Cast out [OBJECT]";
  if (/^(?:In each case\s+)?add\b/iu.test(normalized) || /\badd\b.+\bto\b/iu.test(normalized)) return "Add [OBJECT]";
  if (/^Subtract\b/iu.test(normalized) || /\bsubtract\b.+\bfrom\b/iu.test(normalized)) return "Subtract [OBJECT]";
  if (/^Obtain\b/iu.test(normalized)) return "Obtain [RESULT]";
  return normalized;
}

function buildChineseClauses(chunk) {
  const rejected = [];
  const clauses = [];
  for (const rawClause of splitChineseClauses(chunk.source_text_zh || "")) {
    if (!shouldKeepChineseClause(rawClause)) {
      rejected.push({ raw_clause: rawClause, reason: "filtered_chinese_clause" });
      continue;
    }
    clauses.push(clauseMeta(
      chunk,
      clauses.length,
      "zh",
      rawClause,
      normalizeChineseNumbers(rawClause),
      structuralChineseTemplate(rawClause)
    ));
  }
  return { clauses, rejected };
}

function buildEnglishClauses(chunk) {
  const rejected = [];
  const crossReferences = [];
  const clauses = [];
  for (const rawClause of splitEnglishClauses(chunk.translation_en || "")) {
    if (isCrossReferenceClause(rawClause)) {
      crossReferences.push(clauseMeta(
        chunk,
        crossReferences.length,
        "en_cross_reference",
        rawClause,
        normalizeEnglishNumbers(rawClause),
        structuralEnglishTemplate(rawClause),
        { is_cross_reference: true }
      ));
      continue;
    }
    if (!shouldKeepEnglishClause(rawClause)) {
      rejected.push({ raw_clause: rawClause, reason: "filtered_english_clause" });
      continue;
    }
    clauses.push(clauseMeta(
      chunk,
      clauses.length,
      "en",
      rawClause,
      normalizeEnglishNumbers(rawClause),
      structuralEnglishTemplate(rawClause)
    ));
  }
  return { clauses, rejected, crossReferences };
}

function templateSpecificity(template) {
  const text = template || "";
  const placeholderCount = (text.match(/\[[A-Z]+\]/gu) || []).length;
  const literal = text.replace(/\[[A-Z]+\]/gu, "").replace(/[^\p{L}\u3400-\u9fff]/gu, "");
  return literal.length - placeholderCount * 0.5;
}

function isOvergeneralizedTemplate(template) {
  const clean = normalizeWhitespace(template);
  if (/^\[(?:NUM|UNIT|OBJECT|RESULT|BRACKETED)\]$/u.test(clean)) return true;
  if (templateSpecificity(clean) < 2) return true;
  return false;
}

function aggregateTemplates(clauses) {
  const map = new Map();
  for (const clause of clauses) {
    const key = clause.template;
    if (!map.has(key)) {
      map.set(key, {
        template: key,
        count: 0,
        distinct_chunks: new Set(),
        examples: [],
        is_overgeneralized: isOvergeneralizedTemplate(key),
        specificity_score: templateSpecificity(key)
      });
    }
    const entry = map.get(key);
    entry.count += 1;
    entry.distinct_chunks.add(clause.chunk_id);
    if (entry.examples.length < EXAMPLE_LIMIT) {
      entry.examples.push({
        chunk_id: clause.chunk_id,
        unit_id: clause.unit_id,
        procedure_id: clause.procedure_id,
        book_page: pageLabel(clause),
        raw_clause: clause.raw_clause,
        number_normalized_template: clause.number_normalized_template
      });
    }
  }
  return [...map.values()]
    .map((entry) => ({
      ...entry,
      distinct_chunks: entry.distinct_chunks.size
    }))
    .sort((a, b) => b.count - a.count || b.specificity_score - a.specificity_score || a.template.localeCompare(b.template));
}

function pairKey(zhTemplate, enTemplate) {
  return `${zhTemplate}\u241F${enTemplate}`;
}

function parsePairKey(key) {
  const [zhTemplate, enTemplate] = key.split("\u241F");
  return { zhTemplate, enTemplate };
}

function addPair(pairMap, zhClause, enClause, alignmentStrength, pairingMode) {
  if (!zhClause || !enClause) return;
  if (isOvergeneralizedTemplate(zhClause.template) || isOvergeneralizedTemplate(enClause.template)) return;
  const key = pairKey(zhClause.template, enClause.template);
  if (!pairMap.has(key)) {
    pairMap.set(key, {
      zh_template: zhClause.template,
      en_template: enClause.template,
      count: 0,
      distinct_chunks: new Set(),
      alignment_strength_counts: {},
      best_alignment_strength: alignmentStrength,
      examples: [],
      specificity_score: templateSpecificity(zhClause.template) + templateSpecificity(enClause.template),
      is_prespecified_template: isPrespecifiedPair(zhClause.template, enClause.template)
    });
  }
  const entry = pairMap.get(key);
  entry.count += 1;
  entry.distinct_chunks.add(zhClause.chunk_id);
  entry.alignment_strength_counts[alignmentStrength] = (entry.alignment_strength_counts[alignmentStrength] || 0) + 1;
  if (STRENGTH_RANK[alignmentStrength] > STRENGTH_RANK[entry.best_alignment_strength]) {
    entry.best_alignment_strength = alignmentStrength;
  }
  const example = {
    source_text_zh_clause: zhClause.raw_clause,
    translation_en_clause: enClause.raw_clause,
    chunk_id: zhClause.chunk_id,
    unit_id: zhClause.unit_id,
    book_page: pageLabel(zhClause),
    procedure_id: zhClause.procedure_id,
    alignment_strength: alignmentStrength,
    pairing_mode: pairingMode
  };
  if (entry.examples.length < EXAMPLE_LIMIT) entry.examples.push(example);
}

function isPrespecifiedPair(zhTemplate, enTemplate) {
  return PRESET_PAIR_PATTERNS.some(([zhRe, enRe]) => zhRe.test(zhTemplate) && enRe.test(enTemplate));
}

function addStrongPairsForChunk(pairMap, zhClauses, enClauses) {
  const strongKeys = new Set();
  if (!zhClauses.length || !enClauses.length) return strongKeys;
  if (zhClauses.length === 1 && enClauses.length === 1) {
    addPair(pairMap, zhClauses[0], enClauses[0], "single_zh_single_en", "single_clause_unit");
    strongKeys.add(pairKey(zhClauses[0].template, enClauses[0].template));
    return strongKeys;
  }
  if (zhClauses.length === enClauses.length) {
    for (let i = 0; i < zhClauses.length; i += 1) {
      addPair(pairMap, zhClauses[i], enClauses[i], "ordinal_aligned", "same_clause_count_by_ordinal");
      strongKeys.add(pairKey(zhClauses[i].template, enClauses[i].template));
    }
    return strongKeys;
  }
  if (Math.abs(zhClauses.length - enClauses.length) === 1) {
    const count = Math.min(zhClauses.length, enClauses.length);
    for (let i = 0; i < count; i += 1) {
      addPair(pairMap, zhClauses[i], enClauses[i], "near_ordinal_aligned", "near_clause_count_by_ordinal");
      strongKeys.add(pairKey(zhClauses[i].template, enClauses[i].template));
    }
    return strongKeys;
  }
  if (zhClauses.length === 1 || enClauses.length === 1) {
    for (const zhClause of zhClauses) {
      for (const enClause of enClauses) {
        addPair(pairMap, zhClause, enClause, "one_to_many_ambiguous", "one_to_many_clause_unit");
        strongKeys.add(pairKey(zhClause.template, enClause.template));
      }
    }
  }
  return strongKeys;
}

function addTargetedPresetPairsForChunk(pairMap, zhClauses, enClauses, strongKeys) {
  if (!zhClauses.length || !enClauses.length) return strongKeys;
  for (const zhClause of zhClauses) {
    for (const enClause of enClauses) {
      const key = pairKey(zhClause.template, enClause.template);
      if (strongKeys.has(key)) continue;
      if (!isPrespecifiedPair(zhClause.template, enClause.template)) continue;
      addPair(
        pairMap,
        zhClause,
        enClause,
        "targeted_prespecified_same_unit",
        "targeted_prespecified_same_unit"
      );
      strongKeys.add(key);
    }
  }
  return strongKeys;
}

function addWeakCooccurrencePairs(pairMap, zhClauses, enClauses, strongKeys) {
  const maxCombinations = 36;
  if (!zhClauses.length || !enClauses.length) return "no_pair_candidates";
  if (zhClauses.length * enClauses.length > maxCombinations) return "cooccurrence_suppressed_too_many_clauses";
  const seenThisChunk = new Set(strongKeys);
  for (const zhClause of zhClauses) {
    for (const enClause of enClauses) {
      const key = pairKey(zhClause.template, enClause.template);
      if (seenThisChunk.has(key)) continue;
      addPair(pairMap, zhClause, enClause, "same_unit_cooccurrence", "same_unit_weak_cooccurrence");
      seenThisChunk.add(key);
    }
  }
  return "cooccurrence_recorded";
}

function sortPairs(pairMap) {
  return [...pairMap.values()]
    .map((entry) => ({
      ...entry,
      distinct_chunks: entry.distinct_chunks.size,
      review_priority_score:
        entry.distinct_chunks * 3
        + (entry.alignment_strength_counts.single_zh_single_en || 0) * 8
        + (entry.alignment_strength_counts.ordinal_aligned || 0) * 6
        + (entry.alignment_strength_counts.near_ordinal_aligned || 0) * 3
        + entry.specificity_score
    }))
    .sort((a, b) => b.review_priority_score - a.review_priority_score || b.count - a.count || a.zh_template.localeCompare(b.zh_template));
}

function repeatedLowFrequencyTemplates(templates) {
  return templates
    .filter((item) => item.count >= 2 && item.count <= 3 && !item.is_overgeneralized)
    .slice(0, TOP_N);
}

function containsPageGarbage(chunk) {
  return PAGE_GARBAGE_RE.test(chunk.text || "");
}

function isTableLikeChunk(chunk) {
  return TABLE_FRAGMENT_RE.test(`${chunk.text || ""}\n${chunk.translation_en || ""}`);
}

function buildSuspiciousChunks(chunks, chunkClauses, overgeneralizedClauses, suppressedPairingChunks) {
  const byChunk = new Map(chunkClauses.map((entry) => [entry.chunk.id, entry]));
  const add = (items, reason, chunk, extra = {}) => {
    items.push({
      reason,
      ...chunkMeta(chunk),
      book_page: pageLabel(chunk),
      text_excerpt: excerpt(chunk.text || chunk.translation_en || chunk.source_text_zh, 220),
      ...extra
    });
  };
  const items = [];
  for (const chunk of chunks) {
    const clauses = byChunk.get(chunk.id);
    if (!normalizeWhitespace(chunk.source_text_zh || "")) add(items, "translation_unit_missing_source_text_zh", chunk);
    if (clauses && clauses.zh_clauses.length >= 4 && clauses.en_clauses.length <= 1) {
      add(items, "many_zh_clauses_few_en_clauses", chunk, {
        zh_clause_count: clauses.zh_clauses.length,
        en_clause_count: clauses.en_clauses.length
      });
    }
    if (clauses && clauses.en_clauses.length >= 4 && clauses.zh_clauses.length <= 1) {
      add(items, "many_en_clauses_few_zh_clauses", chunk, {
        zh_clause_count: clauses.zh_clauses.length,
        en_clause_count: clauses.en_clauses.length
      });
    }
    if (containsPageGarbage(chunk)) add(items, "text_contains_page_garbage", chunk);
    if (isTableLikeChunk(chunk)) add(items, "table_like_chunk", chunk);
  }
  for (const item of overgeneralizedClauses.slice(0, 20)) {
    items.push({
      reason: "overgeneralized_template",
      ...chunkMeta(item),
      book_page: pageLabel(item),
      template: item.template,
      raw_clause: item.raw_clause
    });
  }
  for (const entry of suppressedPairingChunks) {
    add(items, "pairing_suppressed_too_many_clause_combinations", entry.chunk, {
      zh_clause_count: entry.zh_clause_count,
      en_clause_count: entry.en_clause_count
    });
  }
  return {
    top_10_for_human_review: items.slice(0, 10),
    all: items
  };
}

function buildInterestingUnnamedPairs(pairs) {
  return pairs
    .filter((pair) => !pair.is_prespecified_template)
    .filter((pair) => pair.distinct_chunks >= 2)
    .filter((pair) => STRENGTH_RANK[pair.best_alignment_strength] >= STRENGTH_RANK.near_ordinal_aligned || pair.count >= 3)
    .slice(0, 30);
}

function markdownTableRows(items, columns, rowFn) {
  const lines = [];
  lines.push(`| ${columns.join(" | ")} |`);
  lines.push(`| ${columns.map(() => "---").join(" | ")} |`);
  for (const item of items) lines.push(`| ${rowFn(item).join(" | ")} |`);
  return lines;
}

function safeCell(value) {
  return normalizeWhitespace(String(value ?? "")).replace(/\|/gu, "\\|");
}

function makeMarkdown(report) {
  const lines = [];
  lines.push("# Sifen Template Discovery");
  lines.push("");
  lines.push("> Template discovery only. This is not final extraction, gold data, or semantic naming. Meaning assignment happens later via LLM/human review.");
  lines.push("");
  lines.push("## Summary");
  lines.push("");
  lines.push(...markdownTableRows([
    ["Translation units", report.summary.translation_unit_count],
    ["Chinese clauses", report.summary.zh_clause_count],
    ["English clauses", report.summary.en_clause_count],
    ["Chinese templates", report.summary.zh_template_count],
    ["English templates", report.summary.en_template_count],
    ["Bilingual template pairs", report.summary.bilingual_template_pair_count],
    ["Previously unnamed candidate pairs", report.summary.previously_unnamed_candidate_pair_count],
    ["Suspicious chunks", report.summary.suspicious_chunk_count]
  ], ["Metric", "Value"], ([metric, value]) => [metric, value]));
  lines.push("");
  lines.push("## Top Chinese Templates");
  lines.push("");
  lines.push(...markdownTableRows(report.top_chinese_templates.slice(0, 30), ["Template", "Count", "Chunks", "Examples"], (item) => [
    safeCell(item.template),
    item.count,
    item.distinct_chunks,
    safeCell(item.examples.slice(0, 3).map((example) => `${example.chunk_id}:${example.raw_clause}`).join("; "))
  ]));
  lines.push("");
  lines.push("## Top English Templates");
  lines.push("");
  lines.push(...markdownTableRows(report.top_english_templates.slice(0, 30), ["Template", "Count", "Chunks", "Examples"], (item) => [
    safeCell(item.template),
    item.count,
    item.distinct_chunks,
    safeCell(item.examples.slice(0, 3).map((example) => `${example.chunk_id}:${example.raw_clause}`).join("; "))
  ]));
  lines.push("");
  lines.push("## Top Bilingual Template Pairs");
  lines.push("");
  lines.push(...markdownTableRows(report.top_bilingual_template_pairs.slice(0, 30), ["ZH template", "EN template", "Count", "Chunks", "Best strength", "Preset"], (item) => [
    safeCell(item.zh_template),
    safeCell(item.en_template),
    item.count,
    item.distinct_chunks,
    item.best_alignment_strength,
    item.is_prespecified_template ? "yes" : "no"
  ]));
  lines.push("");
  for (const pair of report.top_bilingual_template_pairs.slice(0, 10)) {
    lines.push(`### ${pair.zh_template} ↔ ${pair.en_template}`);
    lines.push("");
    lines.push(`Count: ${pair.count}; distinct chunks: ${pair.distinct_chunks}; best strength: ${pair.best_alignment_strength}; preset: ${pair.is_prespecified_template ? "yes" : "no"}`);
    lines.push("");
    for (const example of pair.examples.slice(0, 5)) {
      lines.push(`- ${example.chunk_id} ${example.unit_id || ""} p.${example.book_page} ${example.procedure_id || ""} [${example.alignment_strength}]`);
      lines.push(`  - zh: ${example.source_text_zh_clause}`);
      lines.push(`  - en: ${example.translation_en_clause}`);
    }
    lines.push("");
  }
  lines.push("## Potentially Interesting Patterns Not Previously Named");
  lines.push("");
  lines.push(...markdownTableRows(report.previously_unnamed_candidate_patterns.slice(0, 30), ["ZH template", "EN template", "Count", "Chunks", "Best strength"], (item) => [
    safeCell(item.zh_template),
    safeCell(item.en_template),
    item.count,
    item.distinct_chunks,
    item.best_alignment_strength
  ]));
  lines.push("");
  lines.push("## Low-Frequency Repeated Templates");
  lines.push("");
  lines.push("### Chinese");
  lines.push("");
  lines.push(...markdownTableRows(report.low_frequency_repeated_templates.chinese.slice(0, 20), ["Template", "Count", "Examples"], (item) => [
    safeCell(item.template),
    item.count,
    safeCell(item.examples.slice(0, 2).map((example) => `${example.chunk_id}:${example.raw_clause}`).join("; "))
  ]));
  lines.push("");
  lines.push("### English");
  lines.push("");
  lines.push(...markdownTableRows(report.low_frequency_repeated_templates.english.slice(0, 20), ["Template", "Count", "Examples"], (item) => [
    safeCell(item.template),
    item.count,
    safeCell(item.examples.slice(0, 2).map((example) => `${example.chunk_id}:${example.raw_clause}`).join("; "))
  ]));
  lines.push("");
  lines.push("## Suspicious Chunks For Chunker Fix");
  lines.push("");
  lines.push(...markdownTableRows(report.suspicious_chunks.top_10_for_human_review, ["Reason", "Chunk", "Unit", "Book page", "Excerpt"], (item) => [
    item.reason,
    item.chunk_id,
    item.unit_id || "",
    item.book_page,
    safeCell(item.text_excerpt || item.raw_clause || "")
  ]));
  lines.push("");
  return `${lines.join("\n")}\n`;
}

async function writeText(relativePath, text) {
  const target = resolveRepoPath(relativePath);
  await fs.mkdir(path.dirname(target), { recursive: true });
  await fs.writeFile(target, text, "utf8");
}

async function main() {
  const input = await readJson(INPUT_PATH);
  const chunks = (input.chunks || [])
    .filter((chunk) => chunk.chunk_role === "body" && chunk.chunk_type === "translation_unit");

  const chunkClauses = [];
  const zhClauses = [];
  const enClauses = [];
  const rejectedClauses = [];
  const crossReferenceClauses = [];
  const pairMap = new Map();
  const suppressedPairingChunks = [];

  for (const chunk of chunks) {
    const zh = buildChineseClauses(chunk);
    const en = buildEnglishClauses(chunk);
    zhClauses.push(...zh.clauses);
    enClauses.push(...en.clauses);
    rejectedClauses.push(...zh.rejected.map((item) => ({ ...item, language: "zh", ...chunkMeta(chunk) })));
    rejectedClauses.push(...en.rejected.map((item) => ({ ...item, language: "en", ...chunkMeta(chunk) })));
    crossReferenceClauses.push(...en.crossReferences);
    const strongKeys = addTargetedPresetPairsForChunk(
      pairMap,
      zh.clauses,
      en.clauses,
      addStrongPairsForChunk(pairMap, zh.clauses, en.clauses)
    );
    const cooccurrenceStatus = addWeakCooccurrencePairs(pairMap, zh.clauses, en.clauses, strongKeys);
    if (cooccurrenceStatus === "cooccurrence_suppressed_too_many_clauses") {
      suppressedPairingChunks.push({
        chunk,
        zh_clause_count: zh.clauses.length,
        en_clause_count: en.clauses.length
      });
    }
    chunkClauses.push({
      chunk,
      zh_clauses: zh.clauses,
      en_clauses: en.clauses,
      cross_reference_clauses: en.crossReferences,
      rejected_chinese_clauses: zh.rejected,
      rejected_english_clauses: en.rejected,
      cooccurrence_status: cooccurrenceStatus
    });
  }

  const chineseTemplates = aggregateTemplates(zhClauses);
  const englishTemplates = aggregateTemplates(enClauses);
  const bilingualPairs = sortPairs(pairMap);
  const overgeneralizedClauses = [...zhClauses, ...enClauses].filter((clause) => isOvergeneralizedTemplate(clause.template));
  const interestingUnnamedPairs = buildInterestingUnnamedPairs(bilingualPairs);
  const suspiciousChunks = buildSuspiciousChunks(chunks, chunkClauses, overgeneralizedClauses, suppressedPairingChunks);

  const report = {
    generated_at: new Date().toISOString(),
    input_path: INPUT_PATH,
    outputs: [OUTPUT_JSON_PATH, OUTPUT_MD_PATH],
    scope: {
      chunk_role: "body",
      chunk_type: "translation_unit",
      note: "Template discovery only; no embedding, no LLM, no gold writeback, no chunk mutation."
    },
    summary: {
      translation_unit_count: chunks.length,
      zh_clause_count: zhClauses.length,
      en_clause_count: enClauses.length,
      cross_reference_clause_count: crossReferenceClauses.length,
      rejected_clause_count: rejectedClauses.length,
      zh_template_count: chineseTemplates.length,
      en_template_count: englishTemplates.length,
      bilingual_template_pair_count: bilingualPairs.length,
      previously_unnamed_candidate_pair_count: interestingUnnamedPairs.length,
      suspicious_chunk_count: suspiciousChunks.all.length,
      chunks_without_source_text_zh: chunks.filter((chunk) => !normalizeWhitespace(chunk.source_text_zh || "")).length
    },
    clauses: {
      chinese: zhClauses,
      english: enClauses,
      english_cross_references: crossReferenceClauses,
      rejected: rejectedClauses.slice(0, 500)
    },
    top_chinese_templates: chineseTemplates.slice(0, TOP_N),
    top_english_templates: englishTemplates.slice(0, TOP_N),
    top_bilingual_template_pairs: bilingualPairs.slice(0, TOP_N),
    bilingual_template_pairs: bilingualPairs,
    low_frequency_repeated_templates: {
      chinese: repeatedLowFrequencyTemplates(chineseTemplates),
      english: repeatedLowFrequencyTemplates(englishTemplates)
    },
    previously_unnamed_candidate_patterns: interestingUnnamedPairs,
    quality_checks: {
      translation_units_without_source_text_zh: chunks
        .filter((chunk) => !normalizeWhitespace(chunk.source_text_zh || ""))
        .map((chunk) => ({ ...chunkMeta(chunk), text_excerpt: excerpt(chunk.text, 220) })),
      chunks_with_many_zh_few_en_clauses: suspiciousChunks.all.filter((item) => item.reason === "many_zh_clauses_few_en_clauses"),
      chunks_with_many_en_few_zh_clauses: suspiciousChunks.all.filter((item) => item.reason === "many_en_clauses_few_zh_clauses"),
      chunks_with_page_garbage: suspiciousChunks.all.filter((item) => item.reason === "text_contains_page_garbage"),
      overgeneralized_template_clauses: overgeneralizedClauses.slice(0, 100),
      table_like_chunks: suspiciousChunks.all.filter((item) => item.reason === "table_like_chunk"),
      suppressed_pairing_chunks: suppressedPairingChunks.map((entry) => ({
        ...chunkMeta(entry.chunk),
        zh_clause_count: entry.zh_clause_count,
        en_clause_count: entry.en_clause_count,
        text_excerpt: excerpt(entry.chunk.text, 220)
      }))
    },
    suspicious_chunks: suspiciousChunks
  };

  await writeJson(OUTPUT_JSON_PATH, report);
  await writeText(OUTPUT_MD_PATH, makeMarkdown(report));

  console.log(JSON.stringify({
    stage: "discover-sifen-templates",
    input: INPUT_PATH,
    outputs: [OUTPUT_JSON_PATH, OUTPUT_MD_PATH],
    zh_template_count: report.summary.zh_template_count,
    en_template_count: report.summary.en_template_count,
    bilingual_template_pair_count: report.summary.bilingual_template_pair_count,
    previously_unnamed_candidate_pair_count: report.summary.previously_unnamed_candidate_pair_count,
    top_10_bilingual_template_pairs: report.top_bilingual_template_pairs.slice(0, 10).map((pair) => ({
      zh_template: pair.zh_template,
      en_template: pair.en_template,
      count: pair.count,
      distinct_chunks: pair.distinct_chunks,
      best_alignment_strength: pair.best_alignment_strength,
      is_prespecified_template: pair.is_prespecified_template
    })),
    top_10_suspicious_chunks: report.suspicious_chunks.top_10_for_human_review
  }, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
