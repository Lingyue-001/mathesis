import fs from "node:fs/promises";
import path from "node:path";
import { normalizeWhitespace, readJson, resolveRepoPath, writeJson } from "./cullen-oracle-common.mjs";

// Candidate evidence audit only. This script quantifies support for candidate
// term/template signals from the exploratory Sifen corpus profile and template
// discovery outputs. It does not assign final meaning, generate gold data,
// modify chunks, use embeddings, or call an LLM.

const CHUNKS_PATH = "tmp/procedure-ir/cullen-chunks.json";
const PROFILE_PATH = "tmp/procedure-ir/sifen-corpus-profile.json";
const DISCOVERY_PATH = "tmp/procedure-ir/sifen-template-discovery.json";
const OUTPUT_JSON_PATH = "tmp/procedure-ir/sifen-candidate-evidence-audit.json";
const OUTPUT_MD_PATH = "tmp/procedure-ir/sifen-candidate-evidence-audit.md";

const ALIGNMENT_SCORE = {
  single_zh_single_en: 1,
  ordinal_aligned: 0.92,
  near_ordinal_aligned: 0.76,
  targeted_prespecified_same_unit: 0.64,
  one_to_many_ambiguous: 0.42,
  same_unit_cooccurrence: 0.24
};

const FORMULA = {
  coverage_score: "0.40 source_text_zh + 0.40 translation_en + 0.10 unit_id + 0.10 book_page, averaged over examples",
  alignment_score: "weighted average of alignment_strength counts; single=1.00, ordinal=0.92, near=0.76, targeted_same_unit=0.64, one_to_many=0.42, same_unit=0.24",
  repetition_score: "distinct chunk count mapped to 0.20/0.45/0.60/0.72/0.82/0.95/1.00",
  specificity_score: "literal template content after placeholders, penalizing over-general placeholders",
  numeric_agreement_score: "matched normalized Chinese/Arabic numbers divided by examples with numbers on both sides; null when not applicable",
  contamination_penalty: "weighted rate of missing source/translation, page garbage, table-like context, clause-ratio anomaly, and suppressed pairing",
  overall_term_pair: "0.22 coverage + 0.24 alignment + 0.18 repetition + 0.18 specificity + 0.12 numeric_or_neutral + 0.06 procedure_coverage - 0.22 contamination",
  overall_operation_template_pair: "0.24 coverage + 0.30 alignment + 0.18 repetition + 0.20 specificity + 0.08 procedure_coverage - 0.26 contamination",
  status_thresholds: "single_chunk_only is capped at single_instance_needs_human_review; otherwise >=0.82 strong_candidate, >=0.62 medium_candidate_needs_human_confirmation, >=0.42 weak_candidate, lower human_review_or_exclude"
};

const CHINESE_NUMBER_RE = /[零〇一二三四五六七八九十百千萬万億亿兩]+/gu;
const ARABIC_NUMBER_RE = /\b\d[\d,]*(?:\.\d+)?\b/gu;
const OPERATION_RE = /(置|以\[OBJECT\]乘之|乘|滿|不滿|不盡|得一|除|減|加|命|名為|謂之|餘為|Set out|Multiply|Count one|Cast out|Add|Subtract|Call this|called|remainder is|What does not fill)/iu;
const MOTION_RE = /(留不行|伏逆|見東方|日行|行\[NUM\]度|moves?|delays?|visible|invisible|retreats?|direct motion|Appearance)/iu;
const TERM_RE = /(餘|法|率|積|月|日|度|分|會|蔀|章|Remainder|Factor|Rate|Accumulated|Lunation|Du|Days|Months|Parts|Coincidence|Origin|Obscuration|Circuits|Solar|Cycle)/iu;

function clamp(value, min = 0, max = 1) {
  return Math.max(min, Math.min(max, value));
}

function round(value, digits = 4) {
  if (value === null || value === undefined || Number.isNaN(value)) return null;
  return Number(value.toFixed(digits));
}

function excerpt(text, length = 180) {
  const clean = normalizeWhitespace(text || "");
  return clean.length > length ? `${clean.slice(0, length - 1)}…` : clean;
}

function safeId(text) {
  return normalizeWhitespace(text)
    .replace(/\[[A-Z]+\]/gu, "")
    .replace(/[^\p{L}\p{N}\u3400-\u9fff]+/gu, "_")
    .replace(/^_+|_+$/gu, "")
    .slice(0, 80);
}

function pageLabel(item) {
  const start = item.book_page_start || "";
  const end = item.book_page_end || "";
  return start === end ? String(start) : `${start}-${end}`;
}

function parseChineseNumeral(raw) {
  const digits = { 零: 0, 〇: 0, 一: 1, 二: 2, 兩: 2, 三: 3, 四: 4, 五: 5, 六: 6, 七: 7, 八: 8, 九: 9 };
  const smallUnits = { 十: 10, 百: 100, 千: 1000 };
  const largeUnits = { 萬: 10000, 万: 10000, 億: 100000000, 亿: 100000000 };
  let total = 0;
  let section = 0;
  let number = 0;
  for (const char of raw) {
    if (char in digits) number = digits[char];
    else if (char in smallUnits) {
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

function extractNumberValues(text) {
  const values = [];
  for (const match of String(text || "").matchAll(CHINESE_NUMBER_RE)) {
    const value = parseChineseNumeral(match[0]);
    if (value !== null) values.push(value);
  }
  for (const match of String(text || "").matchAll(ARABIC_NUMBER_RE)) {
    const value = Number.parseFloat(match[0].replace(/,/gu, ""));
    if (Number.isFinite(value)) values.push(value);
  }
  return values;
}

function hasNumberAgreement(zhText, enText) {
  const zhValues = extractNumberValues(zhText);
  const enValues = extractNumberValues(enText);
  if (!zhValues.length || !enValues.length) return null;
  const enSet = new Set(enValues);
  return zhValues.some((value) => enSet.has(value));
}

function buildChunkFlagMap(chunks, discovery) {
  const map = new Map();
  for (const chunk of chunks) {
    map.set(chunk.id, {
      chunk_id: chunk.id,
      missing_source_text_zh: !normalizeWhitespace(chunk.source_text_zh || ""),
      missing_translation_en: !normalizeWhitespace(chunk.translation_en || ""),
      missing_unit_id: !chunk.unit_id,
      missing_book_page: !chunk.book_page_start || !chunk.book_page_end,
      missing_procedure_id: !chunk.procedure_id,
      page_garbage: false,
      table_like: false,
      clause_ratio_extreme: false,
      suppressed_pairing: false
    });
  }
  const quality = discovery.quality_checks || {};
  for (const item of quality.chunks_with_page_garbage || []) {
    if (map.has(item.chunk_id)) map.get(item.chunk_id).page_garbage = true;
  }
  for (const item of quality.table_like_chunks || []) {
    if (map.has(item.chunk_id)) map.get(item.chunk_id).table_like = true;
  }
  for (const item of quality.chunks_with_many_zh_few_en_clauses || []) {
    if (map.has(item.chunk_id)) map.get(item.chunk_id).clause_ratio_extreme = true;
  }
  for (const item of quality.chunks_with_many_en_few_zh_clauses || []) {
    if (map.has(item.chunk_id)) map.get(item.chunk_id).clause_ratio_extreme = true;
  }
  for (const item of quality.suppressed_pairing_chunks || []) {
    if (map.has(item.chunk_id)) map.get(item.chunk_id).suppressed_pairing = true;
  }
  return map;
}

function classifyPair(pair) {
  const text = `${pair.zh_template} ${pair.en_template}`;
  if (OPERATION_RE.test(text) || pair.is_prespecified_template) return "operation_template_pair";
  if (MOTION_RE.test(text)) return "motion_template_pair";
  if (TERM_RE.test(text)) return /:\s*$/u.test(pair.en_template) || /\[NUM\]/u.test(pair.en_template)
    ? "term_or_constant_label_pair"
    : "term_pair";
  return "expression_template_pair";
}

function repetitionScore(distinctChunks) {
  if (distinctChunks >= 10) return 1;
  if (distinctChunks >= 7) return 0.95;
  if (distinctChunks >= 5) return 0.82;
  if (distinctChunks >= 4) return 0.72;
  if (distinctChunks >= 3) return 0.6;
  if (distinctChunks >= 2) return 0.45;
  if (distinctChunks >= 1) return 0.2;
  return 0;
}

function specificityScore(...templates) {
  const joined = templates.join(" ");
  const placeholderCount = (joined.match(/\[[A-Z]+\]/gu) || []).length;
  const literal = joined
    .replace(/\[[A-Z]+\]/gu, "")
    .replace(/[^\p{L}\p{N}\u3400-\u9fff]+/gu, "");
  const raw = (literal.length - placeholderCount * 1.8) / 22;
  return clamp(raw);
}

function alignmentScore(alignmentCounts = {}) {
  let total = 0;
  let weighted = 0;
  for (const [strength, count] of Object.entries(alignmentCounts)) {
    const score = ALIGNMENT_SCORE[strength] ?? 0.2;
    total += count;
    weighted += score * count;
  }
  return total ? weighted / total : 0;
}

function coverageScores(examples, chunkFlagMap) {
  if (!examples.length) {
    return {
      coverage: 0,
      procedure_coverage: 0,
      evidence_counts: {
        source_text_present: 0,
        translation_present: 0,
        unit_id_present: 0,
        book_page_present: 0,
        procedure_id_present: 0
      }
    };
  }
  const counts = {
    source_text_present: 0,
    translation_present: 0,
    unit_id_present: 0,
    book_page_present: 0,
    procedure_id_present: 0
  };
  for (const example of examples) {
    const flags = chunkFlagMap.get(example.chunk_id);
    if (!flags?.missing_source_text_zh) counts.source_text_present += 1;
    if (!flags?.missing_translation_en) counts.translation_present += 1;
    if (!flags?.missing_unit_id) counts.unit_id_present += 1;
    if (!flags?.missing_book_page) counts.book_page_present += 1;
    if (!flags?.missing_procedure_id) counts.procedure_id_present += 1;
  }
  const n = examples.length;
  return {
    coverage:
      (counts.source_text_present / n) * 0.4
      + (counts.translation_present / n) * 0.4
      + (counts.unit_id_present / n) * 0.1
      + (counts.book_page_present / n) * 0.1,
    procedure_coverage: counts.procedure_id_present / n,
    evidence_counts: counts
  };
}

function contaminationPenalty(examples, chunkFlagMap) {
  if (!examples.length) return { penalty: 1, counts: {} };
  const counts = {
    missing_source_text_zh: 0,
    missing_translation_en: 0,
    page_garbage: 0,
    table_like: 0,
    clause_ratio_extreme: 0,
    suppressed_pairing: 0
  };
  for (const example of examples) {
    const flags = chunkFlagMap.get(example.chunk_id);
    if (!flags) continue;
    for (const key of Object.keys(counts)) {
      if (flags[key]) counts[key] += 1;
    }
  }
  const n = examples.length;
  const penalty =
    (counts.missing_source_text_zh / n) * 0.25
    + (counts.missing_translation_en / n) * 0.25
    + (counts.page_garbage / n) * 0.16
    + (counts.table_like / n) * 0.14
    + (counts.clause_ratio_extreme / n) * 0.12
    + (counts.suppressed_pairing / n) * 0.10;
  return { penalty: clamp(penalty), counts };
}

function numericAgreementScore(examples) {
  let applicable = 0;
  let matched = 0;
  for (const example of examples) {
    const result = hasNumberAgreement(example.source_text_zh_clause || example.zh_excerpt || "", example.translation_en_clause || example.en_excerpt || "");
    if (result === null) continue;
    applicable += 1;
    if (result) matched += 1;
  }
  if (!applicable) return { score: null, applicable, matched };
  return { score: matched / applicable, applicable, matched };
}

function failedChecks(scores, evidenceCounts, pair) {
  const failed = [];
  if (scores.coverage < 0.95) failed.push("incomplete_basic_coverage");
  if (scores.alignment < 0.7) failed.push("weak_or_ambiguous_alignment");
  if (scores.repetition < 0.6) failed.push("low_repetition");
  if (scores.specificity < 0.45) failed.push("overgeneral_template");
  if (scores.contamination_penalty >= 0.18) failed.push("contaminated_examples");
  if (scores.numeric_agreement !== null && scores.numeric_agreement < 0.8) failed.push("numeric_disagreement_or_partial_match");
  if (pair.best_alignment_strength === "same_unit_cooccurrence") failed.push("same_unit_only_not_clause_aligned");
  if (pair.best_alignment_strength === "one_to_many_ambiguous") failed.push("one_to_many_clause_ambiguity");
  if (evidenceCounts.distinct_chunks < 2) failed.push("single_chunk_only");
  return failed;
}

function overallScore(candidateType, scores) {
  const numeric = scores.numeric_agreement === null ? 0.65 : scores.numeric_agreement;
  const isOperation = candidateType === "operation_template_pair" || candidateType === "motion_template_pair";
  const score = isOperation
    ? scores.coverage * 0.24
      + scores.alignment * 0.30
      + scores.repetition * 0.18
      + scores.specificity * 0.20
      + scores.procedure_coverage * 0.08
      - scores.contamination_penalty * 0.26
    : scores.coverage * 0.22
      + scores.alignment * 0.24
      + scores.repetition * 0.18
      + scores.specificity * 0.18
      + numeric * 0.12
      + scores.procedure_coverage * 0.06
      - scores.contamination_penalty * 0.22;
  return clamp(score);
}

function statusFromScore(overall, failed) {
  if (failed.includes("single_chunk_only")) {
    return overall >= 0.42 ? "single_instance_needs_human_review" : "human_review_or_exclude";
  }
  if (failed.includes("incomplete_basic_coverage") || failed.includes("contaminated_examples") && overall < 0.68) {
    return overall >= 0.42 ? "human_review" : "exclude_or_rechunk_first";
  }
  if (overall >= 0.82 && failed.length <= 1) return "strong_candidate";
  if (overall >= 0.62) return "medium_candidate_needs_human_confirmation";
  if (overall >= 0.42) return "weak_candidate";
  return "human_review_or_exclude";
}

function usableFor(candidateType, status, scores, failed, evidenceCounts) {
  const usable = [];
  const notUsable = ["gold", "automatic_final_extraction"];
  if (status === "strong_candidate" || status === "medium_candidate_needs_human_confirmation") {
    if (candidateType.includes("term") || candidateType.includes("constant")) {
      usable.push("glossary_candidate", "concept_inventory", "variable_label_candidate");
    }
    if (candidateType === "operation_template_pair" || candidateType === "motion_template_pair") {
      usable.push("operation_template_candidate");
    }
    if (
      (candidateType === "operation_template_pair" || candidateType === "motion_template_pair")
      && scores.alignment >= 0.82
      && scores.contamination_penalty < 0.12
      && (evidenceCounts.distinct_chunks || 0) >= 2
      && !failed.includes("one_to_many_clause_ambiguity")
    ) {
      usable.push("procedure_ir_draft_evidence");
    }
  }
  if (status === "weak_candidate" || status === "single_instance_needs_human_review" || status.startsWith("human_review") || status.startsWith("exclude")) {
    usable.push("human_review_queue");
  }
  if (!(usable.includes("procedure_ir_draft_evidence"))) notUsable.push("procedure_ir_without_manual_review");
  if (candidateType !== "operation_template_pair" || scores.alignment < 0.9) notUsable.push("formal_expression");
  return { usable, not_usable: notUsable };
}

function auditDiscoveryPair(pair, chunkFlagMap) {
  const candidateType = classifyPair(pair);
  const examples = pair.examples || [];
  const coverage = coverageScores(examples, chunkFlagMap);
  const contamination = contaminationPenalty(examples, chunkFlagMap);
  const numeric = numericAgreementScore(examples);
  const evidenceCounts = {
    distinct_chunks: pair.distinct_chunks || new Set(examples.map((example) => example.chunk_id)).size,
    total_examples: examples.length,
    numeric_applicable_examples: numeric.applicable,
    numeric_matched_examples: numeric.matched,
    ...coverage.evidence_counts,
    ...contamination.counts
  };
  const scores = {
    coverage: coverage.coverage,
    alignment: alignmentScore(pair.alignment_strength_counts || { [pair.best_alignment_strength]: pair.count || 1 }),
    repetition: repetitionScore(evidenceCounts.distinct_chunks),
    specificity: specificityScore(pair.zh_template, pair.en_template),
    numeric_agreement: numeric.score,
    procedure_coverage: coverage.procedure_coverage,
    contamination_penalty: contamination.penalty
  };
  scores.overall = overallScore(candidateType, scores);
  const failed = failedChecks(scores, evidenceCounts, pair);
  const status = statusFromScore(scores.overall, failed);
  const readiness = usableFor(candidateType, status, scores, failed, evidenceCounts);
  return {
    candidate_id: `${candidateType}:${safeId(pair.zh_template)}__${safeId(pair.en_template)}`,
    candidate_type: candidateType,
    source: "sifen-template-discovery.bilingual_template_pairs",
    zh_template: pair.zh_template,
    en_template: pair.en_template,
    is_prespecified_template: Boolean(pair.is_prespecified_template),
    best_alignment_strength: pair.best_alignment_strength,
    alignment_strength_counts: pair.alignment_strength_counts || {},
    scores: Object.fromEntries(Object.entries(scores).map(([key, value]) => [key, round(value)])),
    evidence_counts: evidenceCounts,
    status,
    usable_for: readiness.usable,
    not_usable_for: readiness.not_usable,
    failed_checks: failed,
    examples: examples.slice(0, 10).map((example) => ({
      chunk_id: example.chunk_id,
      unit_id: example.unit_id,
      procedure_id: example.procedure_id,
      book_page: example.book_page || pageLabel(example),
      alignment_strength: example.alignment_strength,
      source_text_zh_clause: example.source_text_zh_clause,
      translation_en_clause: example.translation_en_clause
    }))
  };
}

function auditProfileSeed(seed) {
  const count = seed.count || 0;
  const repetition = repetitionScore(count);
  const specificity = specificityScore(seed.pattern_name);
  const alignment = /↔/u.test(seed.pattern_name) ? 0.52 : 0.35;
  const coverage = seed.example_chunk_ids?.length ? 0.65 : 0.25;
  const contamination = 0.08;
  const scores = {
    coverage,
    alignment,
    repetition,
    specificity,
    numeric_agreement: null,
    procedure_coverage: 0,
    contamination_penalty: contamination
  };
  scores.overall = clamp(
    coverage * 0.2
    + alignment * 0.25
    + repetition * 0.25
    + specificity * 0.18
    - contamination * 0.12
  );
  const failed = [];
  if (alignment < 0.7) failed.push("profile_seed_not_clause_aligned");
  if (count < 2) failed.push("low_repetition");
  const status = scores.overall >= 0.62 ? "medium_candidate_needs_human_confirmation" : "weak_candidate";
  return {
    candidate_id: `profile_seed:${safeId(seed.pattern_name)}`,
    candidate_type: "profile_pattern_seed",
    source: "sifen-corpus-profile.pattern_seeds",
    pattern_name: seed.pattern_name,
    scores: Object.fromEntries(Object.entries(scores).map(([key, value]) => [key, round(value)])),
    evidence_counts: {
      count,
      example_chunk_count: seed.example_chunk_ids?.length || 0
    },
    status,
    usable_for: ["human_review_queue", "pattern_discovery_context"],
    not_usable_for: ["gold", "automatic_final_extraction", "procedure_ir_without_manual_review"],
    failed_checks: failed,
    examples: (seed.examples || []).slice(0, 10)
  };
}

function summarize(candidates) {
  const by = (keyFn) => {
    const map = new Map();
    for (const candidate of candidates) {
      const key = keyFn(candidate);
      map.set(key, (map.get(key) || 0) + 1);
    }
    return [...map.entries()]
      .sort((a, b) => b[1] - a[1] || String(a[0]).localeCompare(String(b[0])))
      .map(([key, count]) => ({ key, count }));
  };
  return {
    total_candidates: candidates.length,
    by_candidate_type: by((candidate) => candidate.candidate_type),
    by_status: by((candidate) => candidate.status),
    by_source: by((candidate) => candidate.source),
    strong_candidates: candidates.filter((candidate) => candidate.status === "strong_candidate").length,
    medium_candidates: candidates.filter((candidate) => candidate.status === "medium_candidate_needs_human_confirmation").length,
    human_review_or_weaker: candidates.filter((candidate) => !["strong_candidate", "medium_candidate_needs_human_confirmation"].includes(candidate.status)).length
  };
}

function sortCandidates(candidates) {
  return [...candidates].sort((a, b) => b.scores.overall - a.scores.overall || b.evidence_counts.distinct_chunks - a.evidence_counts.distinct_chunks || a.candidate_id.localeCompare(b.candidate_id));
}

function safeCell(value) {
  return normalizeWhitespace(String(value ?? "")).replace(/\|/gu, "\\|");
}

function table(headers, rows) {
  return [
    `| ${headers.join(" | ")} |`,
    `| ${headers.map(() => "---").join(" | ")} |`,
    ...rows.map((row) => `| ${row.map(safeCell).join(" | ")} |`)
  ];
}

function candidateRows(candidates) {
  return candidates.map((candidate) => [
    candidate.status,
    candidate.candidate_type,
    candidate.zh_template || candidate.pattern_name || "",
    candidate.en_template || "",
    candidate.scores.overall,
    candidate.scores.alignment,
    candidate.evidence_counts.distinct_chunks || candidate.evidence_counts.count || "",
    candidate.failed_checks.join(", ")
  ]);
}

function makeMarkdown(report) {
  const lines = [];
  lines.push("# Sifen Candidate Evidence Audit");
  lines.push("");
  lines.push("> Quantitative evidence audit only. This does not create gold data, final glossary entries, or algorithm reconstructions.");
  lines.push("");
  lines.push("## Scoring Formula");
  lines.push("");
  for (const [key, value] of Object.entries(report.scoring_framework)) {
    lines.push(`- ${key}: ${value}`);
  }
  lines.push("");
  lines.push("## Summary");
  lines.push("");
  lines.push(...table(["Metric", "Value"], [
    ["Total candidates", report.summary.total_candidates],
    ["Strong candidates", report.summary.strong_candidates],
    ["Medium candidates", report.summary.medium_candidates],
    ["Human review or weaker", report.summary.human_review_or_weaker]
  ]));
  lines.push("");
  lines.push("### By Status");
  lines.push("");
  lines.push(...table(["Status", "Count"], report.summary.by_status.map((item) => [item.key, item.count])));
  lines.push("");
  lines.push("### By Candidate Type");
  lines.push("");
  lines.push(...table(["Candidate type", "Count"], report.summary.by_candidate_type.map((item) => [item.key, item.count])));
  lines.push("");
  lines.push("## Strong Candidates");
  lines.push("");
  lines.push(...table(["Status", "Type", "ZH", "EN", "Overall", "Alignment", "Chunks", "Failed checks"], candidateRows(report.strong_candidates.slice(0, 40))));
  lines.push("");
  lines.push("## Medium Candidates");
  lines.push("");
  lines.push(...table(["Status", "Type", "ZH", "EN", "Overall", "Alignment", "Chunks", "Failed checks"], candidateRows(report.medium_candidates.slice(0, 40))));
  lines.push("");
  lines.push("## Needs Human Review");
  lines.push("");
  lines.push(...table(["Status", "Type", "ZH", "EN", "Overall", "Alignment", "Chunks", "Failed checks"], candidateRows(report.human_review_candidates.slice(0, 40))));
  lines.push("");
  lines.push("## Top Examples For Strong Candidates");
  lines.push("");
  for (const candidate of report.strong_candidates.slice(0, 12)) {
    lines.push(`### ${candidate.zh_template || candidate.pattern_name} ${candidate.en_template ? `↔ ${candidate.en_template}` : ""}`);
    lines.push("");
    lines.push(`Status: ${candidate.status}; overall: ${candidate.scores.overall}; usable for: ${candidate.usable_for.join(", ")}`);
    lines.push("");
    for (const example of candidate.examples.slice(0, 3)) {
      lines.push(`- ${example.chunk_id || ""} ${example.unit_id || ""} ${example.procedure_id || ""} p.${example.book_page || ""} [${example.alignment_strength || ""}]`);
      if (example.source_text_zh_clause) lines.push(`  - zh: ${example.source_text_zh_clause}`);
      if (example.translation_en_clause) lines.push(`  - en: ${example.translation_en_clause}`);
    }
    lines.push("");
  }
  return `${lines.join("\n")}\n`;
}

async function writeText(relativePath, text) {
  const target = resolveRepoPath(relativePath);
  await fs.mkdir(path.dirname(target), { recursive: true });
  await fs.writeFile(target, text, "utf8");
}

async function main() {
  const chunksData = await readJson(CHUNKS_PATH);
  const profile = await readJson(PROFILE_PATH);
  const discovery = await readJson(DISCOVERY_PATH);
  const chunks = chunksData.chunks || [];
  const chunkFlagMap = buildChunkFlagMap(chunks, discovery);

  const pairCandidates = (discovery.bilingual_template_pairs || []).map((pair) => auditDiscoveryPair(pair, chunkFlagMap));
  const seedCandidates = (profile.pattern_seeds || []).map(auditProfileSeed);
  const candidates = sortCandidates([...pairCandidates, ...seedCandidates]);
  const strongCandidates = candidates.filter((candidate) => candidate.status === "strong_candidate");
  const mediumCandidates = candidates.filter((candidate) => candidate.status === "medium_candidate_needs_human_confirmation");
  const humanReviewCandidates = candidates.filter((candidate) => !["strong_candidate", "medium_candidate_needs_human_confirmation"].includes(candidate.status));

  const report = {
    generated_at: new Date().toISOString(),
    inputs: [CHUNKS_PATH, PROFILE_PATH, DISCOVERY_PATH],
    outputs: [OUTPUT_JSON_PATH, OUTPUT_MD_PATH],
    scope: {
      note: "Evidence scoring for candidates only; no gold, no chunk mutation, no LLM, no embedding."
    },
    scoring_framework: FORMULA,
    alignment_score_table: ALIGNMENT_SCORE,
    summary: summarize(candidates),
    strong_candidates: strongCandidates,
    medium_candidates: mediumCandidates,
    human_review_candidates: humanReviewCandidates,
    all_candidates: candidates
  };

  await writeJson(OUTPUT_JSON_PATH, report);
  await writeText(OUTPUT_MD_PATH, makeMarkdown(report));

  console.log(JSON.stringify({
    stage: "audit-sifen-candidate-evidence",
    inputs: report.inputs,
    outputs: report.outputs,
    summary: report.summary,
    top_strong_candidates: strongCandidates.slice(0, 10).map((candidate) => ({
      candidate_type: candidate.candidate_type,
      zh_template: candidate.zh_template,
      en_template: candidate.en_template,
      overall: candidate.scores.overall,
      alignment: candidate.scores.alignment,
      distinct_chunks: candidate.evidence_counts.distinct_chunks,
      usable_for: candidate.usable_for,
      failed_checks: candidate.failed_checks
    })),
    top_human_review_candidates: humanReviewCandidates.slice(0, 10).map((candidate) => ({
      candidate_type: candidate.candidate_type,
      zh_template: candidate.zh_template || candidate.pattern_name,
      en_template: candidate.en_template,
      overall: candidate.scores.overall,
      failed_checks: candidate.failed_checks
    }))
  }, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
