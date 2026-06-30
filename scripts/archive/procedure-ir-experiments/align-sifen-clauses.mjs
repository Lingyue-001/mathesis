import fs from "node:fs/promises";
import path from "node:path";
import { normalizeWhitespace, readJson, resolveRepoPath, writeJson } from "./cullen-oracle-common.mjs";

// Clause alignment only. This script aligns Chinese source clauses with Cullen's
// English translation clauses inside Sifen translation_unit chunks. It does not
// extract algorithmic meaning, create gold data, use embeddings, call an LLM, or
// mutate cullen-chunks.json.

const INPUT_PATH = "tmp/procedure-ir/cullen-chunks.json";
const OUTPUT_JSON_PATH = "tmp/procedure-ir/sifen-clause-alignments.json";
const OUTPUT_MD_PATH = "tmp/procedure-ir/sifen-clause-alignments-review.md";

const MIN_ALIGNMENT_SCORE = 30;
const HIGH_SCORE = 70;
const MEDIUM_SCORE = 50;
const SEQUENTIAL_BASELINE_SCORE = 28;
const PAGE_GARBAGE_RE = /(?:–|-)\s*\d{3,5}\s*(?:–|-)/u;
const CHINESE_NUMERAL_RE = /[零〇一二三四五六七八九十百千萬万億亿兩]+/gu;
const ARABIC_NUMBER_RE = /\b\d[\d,]*(?:\.\d+)?\b/gu;

const TERM_FEATURES = [
  ["大餘", /\bGreater Remainder\b/iu, "term_greater_remainder"],
  ["小餘", /\bLesser Remainder\b/iu, "term_lesser_remainder"],
  ["日餘", /\bDay Remainder\b/iu, "term_day_remainder"],
  ["月餘", /\bLunation Remainder\b/iu, "term_lunation_remainder"],
  ["度餘", /\bDu Remainder\b/iu, "term_du_remainder"],
  ["餘分", /\bRemainder Parts?\b/iu, "term_remainder_parts"],
  ["日法", /\bDay Factor\b/iu, "term_day_factor"],
  ["月法", /\bLunation Factor\b/iu, "term_lunation_factor"],
  ["日度法", /\bDay and Du Factor\b/iu, "term_day_du_factor"],
  ["月數", /\bMonth Number\b/iu, "term_month_number"],
  ["月周", /\bLunation\b|\bLunation Circuit\b/iu, "term_lunation"],
  ["積月", /\bAccumulated (?:Months|Lunations)\b/iu, "term_accumulated_months"],
  ["積日", /\bAccumulated Days\b/iu, "term_accumulated_days"],
  ["積度", /\bAccumulated Du\b/iu, "term_accumulated_du"],
  ["周率", /\bCycle Rate\b/iu, "term_cycle_rate"],
  ["日率", /\bSolar Rate\b/iu, "term_solar_rate"],
  ["虛分", /\bV\s*oid Parts\b|\bVoid Parts\b/iu, "term_void_parts"],
  ["入月日", /\bDays of entry into month\b/iu, "term_days_entry_month"],
  ["蔀月", /\bRule Months\b|\bObscuration Months\b/iu, "term_rule_months"],
  ["蔀日", /\bRule Days\b|\bObscuration Days\b/iu, "term_rule_days"],
  ["蔀法", /\bObscuration Factor\b|\bRule Factor\b/iu, "term_obscuration_factor"],
  ["章月", /\bRule Months\b/iu, "term_rule_months"],
  ["章歲", /\bRule Years\b/iu, "term_rule_years"],
  ["紀法", /\bEra Factor\b/iu, "term_era_factor"],
  ["元法", /\bOrigin Factor\b/iu, "term_origin_factor"],
  ["會", /\bCoincidence\b/iu, "term_coincidence"]
];

const OPERATION_FEATURES = [
  [/置/u, /\bset out\b/iu, "operation_set_out"],
  [/乘/u, /\bmultiply\b/iu, "operation_multiply"],
  [/加/u, /\badd\b/iu, "operation_add"],
  [/減/u, /\bsubtract\b|\bsubtracted\b/iu, "operation_subtract"],
  [/除/u, /\bcast out\b|\bdivide\b|\bremove\b/iu, "operation_cast_out_or_divide"],
  [/滿/u, /\bfill(?:s|ed|ing)?\b|\bcount one for each\b/iu, "operation_fill_count"],
  [/得/u, /\bobtain\b|\bget\b|\bgets\b/iu, "operation_obtain"],
  [/命/u, /\bcount off\b|\bname\b/iu, "operation_count_or_name"],
  [/求/u, /\bfind\b|\bto find\b/iu, "operation_find"]
];

const DEFINITION_FEATURES = [
  [/(?:謂之|名之曰|名為|名曰)/u, /\bcalled\b|\bcall this\b|\bis called\b/iu, "definition_called"],
  [/為/u, /\bmake\b|\bmakes\b|\bis\b|\bare\b/iu, "definition_make_or_is"],
  [/(?:不盡|不滿)/u, /\bnot exhausted\b|\bdoes not fill\b|\bwhat is not\b/iu, "result_not_exhausted_or_not_fill"],
  [/餘/u, /\bremainder\b/iu, "result_remainder"]
];

function excerpt(text, length = 180) {
  const clean = normalizeWhitespace(text || "");
  return clean.length > length ? `${clean.slice(0, length - 1)}…` : clean;
}

function chunkId(chunk) {
  return chunk.id || chunk.chunk_id;
}

function pageLabel(item) {
  const start = item.book_page_start || "";
  const end = item.book_page_end || "";
  return start === end ? String(start) : `${start}-${end}`;
}

function chunkMeta(chunk) {
  return {
    chunk_id: chunkId(chunk),
    unit_id: chunk.unit_id,
    procedure_id: chunk.procedure_id,
    section_path: chunk.section_path,
    book_page_start: chunk.book_page_start,
    book_page_end: chunk.book_page_end
  };
}

function splitChineseClauses(text) {
  return (text || "")
    .split(/[，。．；;：:\n]+/u)
    .map((clause) => normalizeWhitespace(clause))
    .filter((clause) => clause && !PAGE_GARBAGE_RE.test(clause));
}

function protectEnglish(text) {
  const replacements = [];
  const protect = (regex, source) => source.replace(regex, (match) => {
    const token = `__PROTECTED_${replacements.length}__`;
    replacements.push(match);
    return token;
  });
  let protectedText = text || "";
  protectedText = protect(/\bProc\.\s*\d+(?:\.\d+)*/gu, protectedText);
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
    .filter((clause) => clause && !PAGE_GARBAGE_RE.test(clause));
}

function buildClauses(chunk, language, text) {
  const splitter = language === "zh" ? splitChineseClauses : splitEnglishClauses;
  return splitter(text).map((raw_clause, index) => ({
    clause_id: `${chunkId(chunk)}:${language}:${index + 1}`,
    clause_index: index,
    language,
    raw_clause,
    ...chunkMeta(chunk)
  }));
}

function parseChineseNumeral(raw) {
  const digits = {
    零: 0,
    〇: 0,
    一: 1,
    二: 2,
    兩: 2,
    三: 3,
    四: 4,
    五: 5,
    六: 6,
    七: 7,
    八: 8,
    九: 9
  };
  const smallUnits = { 十: 10, 百: 100, 千: 1000 };
  const largeUnits = { 萬: 10000, 万: 10000, 億: 100000000, 亿: 100000000 };
  let total = 0;
  let section = 0;
  let number = 0;
  for (const char of raw) {
    if (char in digits) {
      number = digits[char];
    } else if (char in smallUnits) {
      section += (number || 1) * smallUnits[char];
      number = 0;
    } else if (char in largeUnits) {
      section += number;
      total += (section || 1) * largeUnits[char];
      section = 0;
      number = 0;
    } else {
      return null;
    }
  }
  return total + section + number;
}

function extractNumbers(text, language) {
  const values = [];
  for (const match of String(text || "").matchAll(ARABIC_NUMBER_RE)) {
    const parsed = Number.parseFloat(match[0].replace(/,/gu, ""));
    if (Number.isFinite(parsed)) values.push(parsed);
  }
  if (language === "zh") {
    for (const match of String(text || "").matchAll(CHINESE_NUMERAL_RE)) {
      const parsed = parseChineseNumeral(match[0]);
      if (parsed !== null) values.push(parsed);
    }
  }
  return [...new Set(values)];
}

function groupText(clauses) {
  return clauses.map((clause) => clause.raw_clause).join(" ");
}

function numberFeature(zhText, enText) {
  const zhNumbers = extractNumbers(zhText, "zh");
  const enNumbers = extractNumbers(enText, "en");
  const exact = zhNumbers.filter((value) => enNumbers.includes(value));
  if (exact.length) {
    return {
      score: Math.min(35, 20 + exact.length * 5),
      features: exact.map((value) => ({
        feature: "number_exact_match",
        value,
        weight: 10
      }))
    };
  }
  if (zhNumbers.length && enNumbers.length) {
    return {
      score: 8,
      features: [{ feature: "numbers_present_without_exact_match", zh_numbers: zhNumbers, en_numbers: enNumbers, weight: 8 }]
    };
  }
  return { score: 0, features: [] };
}

function regexFeatureScore(zhText, enText, definitions, weight, maxScore) {
  const features = [];
  let score = 0;
  for (const definition of definitions) {
    const [zhPatternOrLiteral, enPattern, feature] = definition;
    const zhMatched = typeof zhPatternOrLiteral === "string"
      ? zhText.includes(zhPatternOrLiteral)
      : zhPatternOrLiteral.test(zhText);
    if (!zhMatched || !enPattern.test(enText)) continue;
    features.push({ feature, weight });
    score += weight;
    if (score >= maxScore) break;
  }
  return { score: Math.min(score, maxScore), features };
}

function orderFeature(zhStart, zhLength, enStart, enLength, zhTotal, enTotal) {
  if (!zhTotal || !enTotal) return { score: 0, features: [] };
  const zhCenter = (zhStart + (zhLength - 1) / 2) / Math.max(1, zhTotal - 1);
  const enCenter = (enStart + (enLength - 1) / 2) / Math.max(1, enTotal - 1);
  const distance = Math.abs(zhCenter - enCenter);
  const score = Math.max(0, Math.round(18 * (1 - Math.min(1, distance))));
  return {
    score,
    features: score >= 10 ? [{ feature: "order_proximity", distance: Number(distance.toFixed(3)), weight: score }] : []
  };
}

function scoreCandidate(zhClauses, enClauses, zhStart, enStart, zhTotal, enTotal, options = {}) {
  const zhText = groupText(zhClauses);
  const enText = groupText(enClauses);
  const features = [];
  let score = 0;

  if (options.sequentialBaseline) {
    score += SEQUENTIAL_BASELINE_SCORE;
    features.push({
      feature: "sequential_baseline_alignment",
      weight: SEQUENTIAL_BASELINE_SCORE,
      note: "same translation_unit order-based alignment"
    });
  }

  const order = orderFeature(zhStart, zhClauses.length, enStart, enClauses.length, zhTotal, enTotal);
  score += order.score;
  features.push(...order.features);

  const number = numberFeature(zhText, enText);
  score += number.score;
  features.push(...number.features);

  const terms = regexFeatureScore(zhText, enText, TERM_FEATURES, 12, 36);
  score += terms.score;
  features.push(...terms.features);

  const operations = regexFeatureScore(zhText, enText, OPERATION_FEATURES, 12, 30);
  score += operations.score;
  features.push(...operations.features);

  const definitions = regexFeatureScore(zhText, enText, DEFINITION_FEATURES, 10, 24);
  score += definitions.score;
  features.push(...definitions.features);

  const groupPenalty = options.sequentialBaseline
    ? Math.max(0, zhClauses.length - 1) + Math.max(0, enClauses.length - 1)
    : (zhClauses.length + enClauses.length - 2) * 3;
  score = Math.max(0, Math.min(100, score - groupPenalty));

  return {
    score,
    confidence: confidenceForScore(score),
    matched_features: features,
    zh_text: zhText,
    en_text: enText
  };
}

function confidenceForScore(score) {
  if (score >= HIGH_SCORE) return "high";
  if (score >= MEDIUM_SCORE) return "medium";
  if (score >= MIN_ALIGNMENT_SCORE) return "low";
  return "unmatched";
}

function alignmentType(zhLength, enLength) {
  if (zhLength === 1 && enLength === 1) return "one_to_one";
  if (zhLength === 1 && enLength > 1) return "one_to_many";
  if (zhLength > 1 && enLength === 1) return "many_to_one";
  return "many_to_many";
}

function makeAlignedRecord(chunk, index, zhGroup, enGroup, zhStart, enStart, zhTotal, enTotal) {
  const scored = scoreCandidate(zhGroup, enGroup, zhStart, enStart, zhTotal, enTotal, {
    sequentialBaseline: true
  });
  return {
    alignment_id: `${chunkId(chunk)}:align:${index + 1}`,
    alignment_status: "aligned",
    alignment_type: alignmentType(zhGroup.length, enGroup.length),
    alignment_method: "sequential_baseline_with_feature_scoring",
    score: scored.score,
    confidence: scored.confidence,
    matched_features: scored.matched_features,
    source_clause_ids: zhGroup.map((clause) => clause.clause_id),
    translation_clause_ids: enGroup.map((clause) => clause.clause_id),
    source_text_zh_clauses: zhGroup.map((clause) => clause.raw_clause),
    translation_en_clauses: enGroup.map((clause) => clause.raw_clause)
  };
}

function makeUnmatchedSourceRecord(chunk, index, clause) {
  return {
    alignment_id: `${chunkId(chunk)}:align:${index + 1}`,
    alignment_status: "unmatched_source",
    alignment_type: "unmatched_source",
    alignment_method: "no_translation_clause_available",
    score: 0,
    confidence: "unmatched",
    matched_features: [],
    source_clause_ids: [clause.clause_id],
    translation_clause_ids: [],
    source_text_zh_clauses: [clause.raw_clause],
    translation_en_clauses: []
  };
}

function makeUnmatchedTranslationRecord(chunk, index, clause) {
  return {
    alignment_id: `${chunkId(chunk)}:align:${index + 1}`,
    alignment_status: "unmatched_translation",
    alignment_type: "unmatched_translation",
    alignment_method: "no_source_clause_available",
    score: 0,
    confidence: "unmatched",
    matched_features: [],
    source_clause_ids: [],
    translation_clause_ids: [clause.clause_id],
    source_text_zh_clauses: [],
    translation_en_clauses: [clause.raw_clause]
  };
}

function alignChunk(chunk, zhClauses, enClauses, commentaryClauses) {
  const zhTotal = zhClauses.length;
  const enTotal = enClauses.length;
  let alignments = [];

  if (!zhTotal || !enTotal) {
    alignments = [
      ...zhClauses.map((clause, index) => makeUnmatchedSourceRecord(chunk, index, clause)),
      ...enClauses.map((clause, index) => makeUnmatchedTranslationRecord(chunk, zhClauses.length + index, clause))
    ];
  } else if (zhTotal >= enTotal) {
    alignments = enClauses.map((enClause, enIndex) => {
      const zhStart = Math.floor((enIndex * zhTotal) / enTotal);
      const zhEnd = Math.max(zhStart + 1, Math.floor(((enIndex + 1) * zhTotal) / enTotal));
      const zhGroup = zhClauses.slice(zhStart, Math.min(zhEnd, zhTotal));
      return makeAlignedRecord(chunk, enIndex, zhGroup, [enClause], zhStart, enIndex, zhTotal, enTotal);
    });
  } else {
    alignments = zhClauses.map((zhClause, zhIndex) => {
      const enStart = Math.floor((zhIndex * enTotal) / zhTotal);
      const enEnd = Math.max(enStart + 1, Math.floor(((zhIndex + 1) * enTotal) / zhTotal));
      const enGroup = enClauses.slice(enStart, Math.min(enEnd, enTotal));
      return makeAlignedRecord(chunk, zhIndex, [zhClause], enGroup, zhIndex, enStart, zhTotal, enTotal);
    });
  }

  return {
    ...chunkMeta(chunk),
    book_page: pageLabel(chunk),
    source_clause_count: zhClauses.length,
    translation_clause_count: enClauses.length,
    commentary_clause_count: commentaryClauses.length,
    source_clauses: zhClauses,
    translation_clauses: enClauses,
    commentary_clauses: commentaryClauses.map((clause) => ({ ...clause, commentary_role: "commentary_not_aligned" })),
    alignments,
    unmatched_source_clauses: alignments.filter((item) => item.alignment_status === "unmatched_source"),
    unmatched_translation_clauses: alignments.filter((item) => item.alignment_status === "unmatched_translation")
  };
}

function summarize(chunkAlignments) {
  const all = chunkAlignments.flatMap((chunk) => chunk.alignments);
  const aligned = all.filter((item) => item.alignment_status === "aligned");
  const high = aligned.filter((item) => item.confidence === "high").length;
  const medium = aligned.filter((item) => item.confidence === "medium").length;
  const low = aligned.filter((item) => item.confidence === "low").length;
  const unmatchedSource = all.filter((item) => item.alignment_status === "unmatched_source").length;
  const unmatchedTranslation = all.filter((item) => item.alignment_status === "unmatched_translation").length;
  return {
    chunk_count: chunkAlignments.length,
    alignment_count: aligned.length,
    high_confidence_count: high,
    medium_confidence_count: medium,
    low_confidence_count: low,
    unmatched_source_clause_count: unmatchedSource,
    unmatched_translation_clause_count: unmatchedTranslation,
    commentary_clause_count: chunkAlignments.reduce((sum, chunk) => sum + chunk.commentary_clause_count, 0)
  };
}

function reviewPriority(chunkAlignment) {
  const low = chunkAlignment.alignments.filter((item) => item.confidence === "low").length;
  const unmatched = chunkAlignment.unmatched_source_clauses.length + chunkAlignment.unmatched_translation_clauses.length;
  const missingSource = chunkAlignment.source_clause_count === 0 ? 5 : 0;
  const imbalance = Math.abs(chunkAlignment.source_clause_count - chunkAlignment.translation_clause_count);
  return unmatched * 5 + low * 2 + missingSource + imbalance;
}

function topReviewChunks(chunkAlignments) {
  return [...chunkAlignments]
    .map((chunk) => ({
      chunk_id: chunk.chunk_id,
      unit_id: chunk.unit_id,
      procedure_id: chunk.procedure_id,
      book_page: chunk.book_page,
      source_clause_count: chunk.source_clause_count,
      translation_clause_count: chunk.translation_clause_count,
      low_confidence_count: chunk.alignments.filter((item) => item.confidence === "low").length,
      unmatched_source_clause_count: chunk.unmatched_source_clauses.length,
      unmatched_translation_clause_count: chunk.unmatched_translation_clauses.length,
      review_priority_score: reviewPriority(chunk)
    }))
    .sort((a, b) => b.review_priority_score - a.review_priority_score || a.chunk_id.localeCompare(b.chunk_id))
    .slice(0, 20);
}

function safeCell(value) {
  return normalizeWhitespace(String(value ?? "")).replace(/\|/gu, "\\|");
}

function alignmentReviewRank(alignment) {
  if (alignment.confidence === "high") return 0;
  if (alignment.confidence === "medium") return 1;
  if (alignment.confidence === "low") return 2;
  if (alignment.alignment_status === "unmatched_source") return 3;
  if (alignment.alignment_status === "unmatched_translation") return 4;
  return 5;
}

function makeMarkdown(report) {
  const lines = [];
  lines.push("# Sifen Clause Alignments Review");
  lines.push("");
  lines.push("> Clause alignment only. This is not extraction, not gold, and not an interpretation of algorithmic meaning. Commentary clauses are listed separately and are not used in main translation alignment.");
  lines.push("");
  lines.push("## Summary");
  lines.push("");
  lines.push("| Metric | Value |");
  lines.push("| --- | ---: |");
  lines.push(`| Chunks processed | ${report.summary.chunk_count} |`);
  lines.push(`| Successful alignments | ${report.summary.alignment_count} |`);
  lines.push(`| High confidence | ${report.summary.high_confidence_count} |`);
  lines.push(`| Medium confidence | ${report.summary.medium_confidence_count} |`);
  lines.push(`| Low confidence | ${report.summary.low_confidence_count} |`);
  lines.push(`| Unmatched Chinese clauses | ${report.summary.unmatched_source_clause_count} |`);
  lines.push(`| Unmatched English clauses | ${report.summary.unmatched_translation_clause_count} |`);
  lines.push(`| Commentary clauses, not aligned | ${report.summary.commentary_clause_count} |`);
  lines.push("");
  lines.push("## Chunks To Review First");
  lines.push("");
  lines.push("| chunk | unit | page | procedure | zh | en | low | unmatched zh | unmatched en |");
  lines.push("| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |");
  for (const chunk of report.review_priority_chunks.slice(0, 20)) {
    lines.push(`| ${chunk.chunk_id} | ${chunk.unit_id || ""} | ${chunk.book_page} | ${chunk.procedure_id || ""} | ${chunk.source_clause_count} | ${chunk.translation_clause_count} | ${chunk.low_confidence_count} | ${chunk.unmatched_source_clause_count} | ${chunk.unmatched_translation_clause_count} |`);
  }
  lines.push("");
  lines.push("## Alignments By Chunk");
  for (const chunk of report.chunks) {
    lines.push("");
    lines.push(`### ${chunk.chunk_id} ${chunk.unit_id || ""} p.${chunk.book_page} ${chunk.procedure_id || ""}`);
    lines.push("");
    lines.push(`Clauses: zh=${chunk.source_clause_count}, en=${chunk.translation_clause_count}, commentary=${chunk.commentary_clause_count}`);
    lines.push("");
    lines.push("| status | conf | score | type | zh | en | features |");
    lines.push("| --- | --- | ---: | --- | --- | --- | --- |");
    const reviewAlignments = [...chunk.alignments].sort((a, b) => alignmentReviewRank(a) - alignmentReviewRank(b));
    for (const alignment of reviewAlignments) {
      const features = alignment.matched_features.map((feature) => feature.feature).join(", ");
      lines.push(`| ${alignment.alignment_status} | ${alignment.confidence} | ${alignment.score} | ${alignment.alignment_type} | ${safeCell(alignment.source_text_zh_clauses.join(" / "))} | ${safeCell(alignment.translation_en_clauses.join(" / "))} | ${safeCell(features)} |`);
    }
    if (chunk.commentary_clauses.length) {
      lines.push("");
      lines.push("Commentary, not aligned:");
      for (const clause of chunk.commentary_clauses.slice(0, 5)) {
        lines.push(`- ${safeCell(clause.raw_clause)}`);
      }
    }
  }
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

  const chunkAlignments = chunks.map((chunk) => {
    const zhClauses = buildClauses(chunk, "zh", chunk.source_text_zh || "");
    const enClauses = buildClauses(chunk, "en", chunk.translation_en || "");
    const commentaryClauses = buildClauses(chunk, "commentary_en", chunk.commentary_en || "");
    return alignChunk(chunk, zhClauses, enClauses, commentaryClauses);
  });

  const report = {
    generated_at: new Date().toISOString(),
    input_path: INPUT_PATH,
    outputs: [OUTPUT_JSON_PATH, OUTPUT_MD_PATH],
    scope: {
      chunk_role: "body",
      chunk_type: "translation_unit",
      note: "Clause alignment only; no embedding, no LLM, no gold writeback, no chunk mutation."
    },
    scoring_policy: {
      score_features: [
        "order proximity",
        "number exact match",
        "term/label correspondence",
        "operation-word correspondence",
        "definition-word correspondence",
        "result/remainder correspondence"
      ],
      confidence_thresholds: {
        high: `>= ${HIGH_SCORE}`,
        medium: `>= ${MEDIUM_SCORE}`,
        low: `>= ${MIN_ALIGNMENT_SCORE}`,
        unmatched: `< ${MIN_ALIGNMENT_SCORE}`
      },
      commentary_policy: "commentary_en is split and recorded separately, but not used in main source/translation alignment"
    },
    summary: null,
    review_priority_chunks: null,
    chunks: chunkAlignments
  };
  report.summary = summarize(chunkAlignments);
  report.review_priority_chunks = topReviewChunks(chunkAlignments);

  await writeJson(OUTPUT_JSON_PATH, report);
  await writeText(OUTPUT_MD_PATH, makeMarkdown(report));

  console.log(JSON.stringify({
    stage: "align-sifen-clauses",
    input: INPUT_PATH,
    outputs: [OUTPUT_JSON_PATH, OUTPUT_MD_PATH],
    total_chunk_count: report.summary.chunk_count,
    successful_alignment_count: report.summary.alignment_count,
    high_confidence_count: report.summary.high_confidence_count,
    medium_confidence_count: report.summary.medium_confidence_count,
    low_confidence_count: report.summary.low_confidence_count,
    unmatched_source_clause_count: report.summary.unmatched_source_clause_count,
    unmatched_translation_clause_count: report.summary.unmatched_translation_clause_count,
    commentary_clause_count: report.summary.commentary_clause_count,
    chunks_to_review_first: report.review_priority_chunks.slice(0, 10)
  }, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
