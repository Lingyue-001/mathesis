import fs from "node:fs/promises";
import { normalizeWhitespace, readJson, resolveRepoPath, writeJson } from "./cullen-oracle-common.mjs";

// Single-Proc pilot only. This script assembles local evidence for one Cullen
// Sifen procedure into auditable step candidates. It is not a full parser, does
// not generate gold, and does not modify cullen-chunks or any canonical data.

const CHUNKS_PATH = "tmp/procedure-ir/cullen-chunks.json";
const TEMPLATE_DISCOVERY_PATH = "tmp/procedure-ir/sifen-template-discovery.json";
const CANDIDATE_AUDIT_PATH = "tmp/procedure-ir/sifen-candidate-evidence-audit.json";
const CLAUSE_ALIGNMENT_PATH = "tmp/procedure-ir/sifen-clause-alignments.json";

const OUTPUT_JSON_PATH = "tmp/procedure-ir/sifen-proc35-mini-pipeline.json";
const OUTPUT_MD_PATH = "tmp/procedure-ir/sifen-proc35-mini-pipeline.md";

const TARGET = {
  proc_id: "Proc. 3.5",
  unit_id: "§46",
  chunk_id: "cullen:chunk:62"
};

const STEP_SPECS = [
  {
    step_id: "Proc.3.5.step.0",
    step_role: "procedure_title",
    operation_id: "procedure_scope_title",
    source_phrase: "推天正術",
    source_clause: "推天正術",
    translation_phrase: "",
    translation_keywords: [],
    commentary_keywords: ["aim to find how many whole months", "intercalary month"],
    formal_expression: null,
    variables: [],
    constants: [],
    input_bindings: [],
    output_bindings: [],
    validation_rule: null,
    formalization_status: "not_formalizable_yet",
    confidence: "medium",
    notes: ["Treat as the procedure title/scope phrase, not as an arithmetic operation."]
  },
  {
    step_id: "Proc.3.5.step.1",
    step_role: "input_binding",
    operation_id: "set_out_years_into_obscuration",
    source_phrase: "置入蔀年",
    source_clause: "置入蔀年減一",
    translation_phrase: "Set out the years into the Obscuration",
    translation_keywords: ["Set out the years into the Obscuration"],
    commentary_keywords: ["years into the obscuration", "ordinal number of year in the Obscuration"],
    formal_expression: "years_into_obscuration = input(\"入蔀年\")",
    variables: ["years_into_obscuration"],
    constants: [],
    input_bindings: [{ name: "years_into_obscuration", source: "source_text_zh + Cullen translation", value: "入蔀年 / years into the Obscuration" }],
    output_bindings: [{ name: "years_into_obscuration", role: "input variable" }],
    validation_rule: "Check that the procedure starts by binding the ordinal year within the Obscuration before subtraction.",
    formalization_status: "formalizable_with_caveat",
    confidence: "high",
    notes: ["This is a variable-binding step, not an arithmetic calculation."]
  },
  {
    step_id: "Proc.3.5.step.2",
    step_role: "operation",
    operation_id: "subtract_one_to_elapsed_years",
    source_phrase: "減一",
    source_clause: "置入蔀年減一",
    translation_phrase: "subtract one",
    translation_keywords: ["subtract one"],
    commentary_keywords: ["we have to subtract one from this number", "number of years from the start of the Obscuration"],
    formal_expression: "elapsed_years = years_into_obscuration - 1",
    variables: ["years_into_obscuration", "elapsed_years"],
    constants: [{ name: "one", value: 1, source: "source_text_zh + Cullen translation + Cullen commentary" }],
    input_bindings: [{ name: "years_into_obscuration", source: "Proc.3.5.step.1" }],
    output_bindings: [{ name: "elapsed_years", role: "years elapsed from start of Obscuration" }],
    validation_rule: "For any supplied ordinal year n, verify elapsed_years = n - 1.",
    formalization_status: "formalizable_now",
    confidence: "high",
    notes: ["Cullen commentary explicitly explains why one is subtracted."]
  },
  {
    step_id: "Proc.3.5.step.3",
    step_role: "operation",
    operation_id: "multiply_by_rule_months",
    source_phrase: "以章月乘之",
    source_clause: "以章月乘之",
    translation_phrase: "Multiply by Rule Months [235].",
    translation_keywords: ["Multiply by Rule Months", "Rule Months [235]"],
    commentary_keywords: ["235 months are exactly equivalent to 19 years", "whole months have elapsed"],
    formal_expression: "product = elapsed_years × 章月",
    variables: ["elapsed_years", "product"],
    constants: [{ name: "章月 / Rule Months", value: 235, source: "Cullen translation + Cullen commentary" }],
    input_bindings: [{ name: "elapsed_years", source: "Proc.3.5.step.2" }],
    output_bindings: [{ name: "product", role: "months-at-rule-scale numerator before Rule Factor division" }],
    validation_rule: "Given elapsed_years, verify product = elapsed_years × 235.",
    formalization_status: "formalizable_now",
    confidence: "high",
    notes: ["Global template support exists for 以[OBJECT]乘之 ↔ Multiply by [OBJECT], but local binding comes from this Proc."]
  },
  {
    step_id: "Proc.3.5.step.4",
    step_role: "operation",
    operation_id: "count_one_for_each_rule_factor_filled",
    source_phrase: "滿章法得一",
    source_clause: "滿章法得一",
    translation_phrase: "Count one for each Rule Factor [19] filled.",
    translation_keywords: ["Count one for each Rule Factor", "Rule Factor [19] filled"],
    commentary_keywords: ["235 months are exactly equivalent to 19 years", "Rule Factor [19]", "how many whole months have elapsed"],
    formal_expression: "quotient = floor(product / 章法)",
    variables: ["product", "quotient"],
    constants: [{ name: "章法 / Rule Factor", value: 19, source: "Cullen translation + Cullen commentary" }],
    input_bindings: [{ name: "product", source: "Proc.3.5.step.3" }],
    output_bindings: [{ name: "quotient", role: "count of filled Rule Factors" }],
    validation_rule: "Given product, verify quotient = floor(product / 19).",
    formalization_status: "formalizable_with_caveat",
    confidence: "high",
    notes: ["Cullen gives the operation as counting filled Rule Factors; floor division is the modern formalization of that count."]
  },
  {
    step_id: "Proc.3.5.step.5",
    step_role: "output_label",
    operation_id: "name_quotient_accumulated_months",
    source_phrase: "名為積月",
    source_clause: "名為積月",
    translation_phrase: "Call this Accu- mulated Months.",
    translation_keywords: ["Call this", "Accumulated Months"],
    commentary_keywords: ["how many whole months have elapsed", "whole months have elapsed since the start of the Obscuration"],
    formal_expression: "積月 = quotient",
    variables: ["quotient", "積月"],
    constants: [],
    input_bindings: [{ name: "quotient", source: "Proc.3.5.step.4" }],
    output_bindings: [{ name: "積月 / Accumulated Months", role: "named quotient" }],
    validation_rule: "Check that the quotient produced by filled Rule Factors is the value named Accumulated Months.",
    formalization_status: "formalizable_with_caveat",
    confidence: "high",
    notes: ["This is a naming/binding step rather than a new arithmetic operation."]
  },
  {
    step_id: "Proc.3.5.step.6",
    step_role: "output_label",
    operation_id: "name_remainder_intercalation_remainder",
    source_phrase: "不滿為閏餘",
    source_clause: "不滿為閏餘",
    translation_phrase: "The remainder is the Intercalation Remainder.",
    translation_keywords: ["The remainder is the Intercalation Remainder"],
    commentary_keywords: ["The remainder will be a fraction of a month at a scale of Rule Factor [19]", "This is the Intercalation Remainder"],
    formal_expression: "閏餘 = product mod 章法",
    variables: ["product", "閏餘"],
    constants: [{ name: "章法 / Rule Factor", value: 19, source: "Cullen commentary relation to remainder scale" }],
    input_bindings: [{ name: "product", source: "Proc.3.5.step.3" }, { name: "章法", source: "Proc.3.5.step.4" }],
    output_bindings: [{ name: "閏餘 / Intercalation Remainder", role: "named remainder" }],
    validation_rule: "Given product, verify 閏餘 = product mod 19.",
    formalization_status: "formalizable_with_caveat",
    confidence: "high",
    notes: ["The modulo expression is a modern formalization of the named remainder after counting filled Rule Factors."]
  },
  {
    step_id: "Proc.3.5.step.7",
    step_role: "condition",
    operation_id: "threshold_intercalary_year",
    source_phrase: "十二以上, 其歲有閏",
    source_clause: "十二以上, 其歲有閏",
    translation_phrase: "If it is 12 or more, this year has an intercalation.",
    translation_keywords: ["If it is 12 or more", "this year has an intercalation"],
    commentary_keywords: ["if at the start of the current year this Remainder is 12 or more", "requires an intercalary month to be inserted"],
    formal_expression: "has_intercalary_month = 閏餘 >= 12",
    variables: ["閏餘", "has_intercalary_month"],
    constants: [{ name: "intercalation threshold", value: 12, source: "source_text_zh + Cullen translation + Cullen commentary" }],
    input_bindings: [{ name: "閏餘", source: "Proc.3.5.step.6" }],
    output_bindings: [{ name: "has_intercalary_month", role: "boolean condition for current year" }],
    validation_rule: "Given 閏餘, verify has_intercalary_month is true exactly when 閏餘 >= 12.",
    formalization_status: "formalizable_now",
    confidence: "high",
    notes: ["This is a threshold condition, not a lookup table."]
  }
];

function ensureArray(data) {
  if (Array.isArray(data)) return data;
  if (Array.isArray(data?.chunks)) return data.chunks;
  return [];
}

async function readJsonIfExists(relativePath, fallback) {
  try {
    return await readJson(relativePath);
  } catch {
    return fallback;
  }
}

function excerpt(text, length = 260) {
  const clean = normalizeWhitespace(text || "");
  return clean.length > length ? `${clean.slice(0, length - 1)}…` : clean;
}

function normalizeSearchText(text) {
  return normalizeWhitespace(text || "")
    .replace(/\u00ad/gu, "")
    .replace(/-\s+/gu, "")
    .toLowerCase();
}

function splitChineseClauses(text) {
  return String(text || "")
    .split(/[，。．；;：]/u)
    .map((clause) => normalizeWhitespace(clause))
    .filter(Boolean);
}

function splitEnglishSentences(text) {
  return String(text || "")
    .replace(/\s+/gu, " ")
    .split(/(?<=[.!?])\s+/u)
    .map((sentence) => normalizeWhitespace(sentence))
    .filter(Boolean);
}

function findFirstSentence(sentences, keywords) {
  if (!keywords?.length) return "";
  return sentences.find((sentence) => {
    const normalized = normalizeSearchText(sentence);
    return keywords.some((keyword) => normalized.includes(normalizeSearchText(keyword)));
  }) || "";
}

function findCommentarySupport(commentarySentences, keywords) {
  const matches = [];
  for (const keyword of keywords || []) {
    const normalizedKeyword = normalizeSearchText(keyword);
    const sentence = commentarySentences.find((candidate) =>
      normalizeSearchText(candidate).includes(normalizedKeyword)
    );
    if (sentence && !matches.includes(sentence)) matches.push(sentence);
  }
  return matches;
}

function findTemplateSupport(discovery, step) {
  const pairs = discovery?.bilingual_template_pairs || [];
  const sourceNeedle = normalizeSearchText(step.source_phrase);
  const translationNeedles = [
    ...step.translation_keywords,
    step.translation_phrase
  ].filter(Boolean).map(normalizeSearchText);

  const examples = [];
  for (const pair of pairs) {
    for (const example of pair.examples || []) {
      if (example.chunk_id !== TARGET.chunk_id) continue;
      const source = normalizeSearchText(example.source_text_zh_clause || "");
      const translation = normalizeSearchText(example.translation_en_clause || "");
      const sourceMatches = source.includes(sourceNeedle) || sourceNeedle.includes(source);
      const translationMatches = translationNeedles.some((needle) => needle && translation.includes(needle));
      if (sourceMatches && translationMatches) {
        examples.push({
          zh_template: pair.zh_template,
          en_template: pair.en_template,
          count: pair.count,
          distinct_chunks: pair.distinct_chunks,
          best_alignment_strength: pair.best_alignment_strength,
          example: {
            source_text_zh_clause: example.source_text_zh_clause,
            translation_en_clause: example.translation_en_clause,
            alignment_strength: example.alignment_strength,
            pairing_mode: example.pairing_mode
          }
        });
      }
    }
  }
  return examples;
}

function findCandidateAuditSupport(candidateAudit, step) {
  const candidates = candidateAudit?.all_candidates || [];
  const sourceNeedle = normalizeSearchText(step.source_phrase);
  const translationNeedles = [
    ...step.translation_keywords,
    step.translation_phrase
  ].filter(Boolean).map(normalizeSearchText);

  return candidates
    .filter((candidate) => (candidate.examples || []).some((example) => {
      if (example.chunk_id !== TARGET.chunk_id) return false;
      const source = normalizeSearchText(example.source_text_zh_clause || example.zh_match || example.zh_excerpt || "");
      const translation = normalizeSearchText(example.translation_en_clause || example.en_match || example.en_excerpt || "");
      const sourceMatches = source.includes(sourceNeedle) || sourceNeedle.includes(source);
      const translationMatches = translationNeedles.some((needle) => needle && translation.includes(needle));
      return sourceMatches && translationMatches;
    }))
    .slice(0, 6)
    .map((candidate) => ({
      candidate_id: candidate.candidate_id,
      candidate_type: candidate.candidate_type,
      status: candidate.status,
      overall_score: candidate.scores?.overall ?? null,
      failed_checks: candidate.failed_checks || [],
      examples: (candidate.examples || [])
        .filter((example) => example.chunk_id === TARGET.chunk_id)
        .slice(0, 2)
        .map((example) => ({
          source_text_zh_clause: example.source_text_zh_clause || example.zh_match || null,
          translation_en_clause: example.translation_en_clause || example.en_match || null,
          alignment_strength: example.alignment_strength || null
        }))
    }));
}

function detectAlignmentRisk(alignmentData, step) {
  const chunkAlignment = (alignmentData?.chunks || alignmentData?.chunk_alignments || alignmentData?.alignments_by_chunk || [])
    .find((item) => item.chunk_id === TARGET.chunk_id || item.id === TARGET.chunk_id);
  if (!chunkAlignment) return [];

  const sourceNeedle = normalizeSearchText(step.source_phrase);
  const translationNeedles = [
    ...step.translation_keywords,
    step.translation_phrase
  ].filter(Boolean).map(normalizeSearchText);

  return (chunkAlignment.alignments || [])
    .filter((alignment) => {
      const source = normalizeSearchText((alignment.source_text_zh_clauses || []).join(" "));
      if (!source.includes(sourceNeedle) && !sourceNeedle.includes(source)) return false;
      const translation = normalizeSearchText((alignment.translation_en_clauses || []).join(" "));
      if (!translationNeedles.length) return false;
      return !translationNeedles.some((needle) => needle && translation.includes(needle));
    })
    .map((alignment) => ({
      alignment_id: alignment.alignment_id,
      confidence: alignment.confidence,
      score: alignment.score,
      source_text_zh_clauses: alignment.source_text_zh_clauses,
      translation_en_clauses: alignment.translation_en_clauses,
      reason: "Existing exploratory clause alignment pairs this source phrase with a different translation phrase."
    }));
}

function scoreEvidence(step, translationSentence, commentarySupport, templateSupport, candidateSupport, alignmentRisks) {
  let score = 0;
  if (step.source_phrase) score += 0.2;
  if (translationSentence || step.translation_phrase) score += 0.22;
  if (commentarySupport.length) score += 0.28;
  if (templateSupport.length) score += 0.1;
  if (candidateSupport.length) score += 0.08;
  if (step.formal_expression) score += 0.12;
  if (alignmentRisks.length) score -= 0.08;
  score = Math.max(0, Math.min(1, score));
  return Number(score.toFixed(3));
}

function classifyEvidenceLevel(step, commentarySupport, templateSupport) {
  if (step.step_role === "procedure_title") return "scope_phrase_not_operation";
  if (commentarySupport.length && templateSupport.length) return "translation_commentary_template_supported";
  if (commentarySupport.length) return "translation_and_commentary_explicit";
  if (step.translation_phrase) return "translation_explicit_only";
  return "source_only_needs_human_review";
}

function buildStepCandidates(chunk, discovery, candidateAudit, alignmentData) {
  const translationSentences = splitEnglishSentences(chunk.translation_en);
  const commentarySentences = splitEnglishSentences(chunk.commentary_en);

  return STEP_SPECS.map((step) => {
    const translationSentence = findFirstSentence(translationSentences, step.translation_keywords) || step.translation_phrase;
    const commentarySupport = findCommentarySupport(commentarySentences, step.commentary_keywords);
    const templateSupport = findTemplateSupport(discovery, step);
    const candidateAuditSupport = findCandidateAuditSupport(candidateAudit, step);
    const alignmentRisks = detectAlignmentRisk(alignmentData, step);
    const evidenceScore = scoreEvidence(step, translationSentence, commentarySupport, templateSupport, candidateAuditSupport, alignmentRisks);

    return {
      step_id: step.step_id,
      step_role: step.step_role,
      operation_id: step.operation_id,
      source_phrase: step.source_phrase,
      source_clause: step.source_clause,
      translation_phrase: step.translation_phrase,
      translation_sentence_context: translationSentence,
      commentary_support: commentarySupport.map((sentence) => excerpt(sentence)),
      template_support: templateSupport,
      candidate_audit_support: candidateAuditSupport,
      evidence_level: classifyEvidenceLevel(step, commentarySupport, templateSupport),
      evidence_score: evidenceScore,
      formal_expression: step.formal_expression,
      variables: step.variables,
      constants: step.constants,
      input_bindings: step.input_bindings,
      output_bindings: step.output_bindings,
      validation_rule: step.validation_rule,
      formalization_status: step.formalization_status,
      confidence: step.confidence,
      alignment_risks: alignmentRisks,
      machine_verifiability: {
        symbolic_relation_ready: Boolean(step.formal_expression) && step.step_role !== "procedure_title",
        arithmetic_validation_ready_now: false,
        reason: "Proc. 3.5 chunk gives explicit procedure relations but no concrete Cullen worked-example input value for 入蔀年."
      },
      do_not_writeback: true,
      notes: step.notes
    };
  });
}

function collectAlignmentRisks(stepCandidates) {
  return stepCandidates.flatMap((step) =>
    step.alignment_risks.map((risk) => ({
      step_id: step.step_id,
      source_phrase: step.source_phrase,
      expected_translation_phrase: step.translation_phrase,
      ...risk
    }))
  );
}

function summarize(stepCandidates, chunk) {
  const evidenceScores = stepCandidates.map((step) => step.evidence_score);
  const averageEvidenceScore = evidenceScores.reduce((sum, value) => sum + value, 0) / evidenceScores.length;
  return {
    proc_id: TARGET.proc_id,
    unit_id: TARGET.unit_id,
    chunk_id: TARGET.chunk_id,
    book_page_start: chunk.book_page_start,
    book_page_end: chunk.book_page_end,
    step_count: stepCandidates.length,
    operation_step_count: stepCandidates.filter((step) => step.step_role === "operation").length,
    output_or_condition_step_count: stepCandidates.filter((step) => ["output_label", "condition"].includes(step.step_role)).length,
    high_confidence_step_count: stepCandidates.filter((step) => step.confidence === "high").length,
    alignment_risk_count: collectAlignmentRisks(stepCandidates).length,
    average_evidence_score: Number(averageEvidenceScore.toFixed(3)),
    arithmetic_validation_ready_now: false,
    algorithm_reconstruction_readiness: "proc_level_candidate_ready_for_human_review",
    verdict: "Supports a curated Proc-level mini pipeline, but does not yet support fully automatic reconstruction or arithmetic validation."
  };
}

function markdownTable(headers, rows) {
  return [
    `| ${headers.join(" | ")} |`,
    `| ${headers.map(() => "---").join(" | ")} |`,
    ...rows.map((row) => `| ${row.map((cell) => String(cell ?? "").replace(/\|/gu, "\\|")).join(" | ")} |`)
  ].join("\n");
}

function renderMarkdown(report) {
  const lines = [];
  lines.push("# Sifen Proc. 3.5 Mini Pipeline Pilot");
  lines.push("");
  lines.push("This is a single-Proc pilot for evidence assembly, not final extraction, not gold, and not a writeback plan.");
  lines.push("");
  lines.push("## Summary");
  lines.push("");
  lines.push(markdownTable(
    ["Field", "Value"],
    [
      ["proc_id", report.summary.proc_id],
      ["unit_id", report.summary.unit_id],
      ["chunk_id", report.summary.chunk_id],
      ["book pages", `${report.summary.book_page_start}-${report.summary.book_page_end}`],
      ["step count", report.summary.step_count],
      ["alignment risks", report.summary.alignment_risk_count],
      ["average evidence score", report.summary.average_evidence_score],
      ["arithmetic validation ready now", report.summary.arithmetic_validation_ready_now],
      ["verdict", report.summary.verdict]
    ]
  ));
  lines.push("");
  lines.push("## Source Chunk");
  lines.push("");
  lines.push(`- Source: ${report.source_chunk.source_text_zh}`);
  lines.push(`- Translation: ${report.source_chunk.translation_en}`);
  lines.push(`- Commentary excerpt: ${report.source_chunk.commentary_excerpt}`);
  lines.push("");
  lines.push("## Step Candidates");
  lines.push("");
  lines.push(markdownTable(
    ["step", "role", "operation_id", "source", "translation", "formal expression", "evidence", "confidence"],
    report.step_candidates.map((step) => [
      step.step_id,
      step.step_role,
      step.operation_id,
      step.source_phrase,
      step.translation_phrase,
      step.formal_expression || "",
      `${step.evidence_level} (${step.evidence_score})`,
      step.confidence
    ])
  ));
  lines.push("");
  lines.push("## Detailed Evidence");
  for (const step of report.step_candidates) {
    lines.push("");
    lines.push(`### ${step.step_id} ${step.operation_id}`);
    lines.push("");
    lines.push(`- Source phrase: ${step.source_phrase}`);
    if (step.translation_phrase) lines.push(`- Cullen translation phrase: ${step.translation_phrase}`);
    if (step.commentary_support.length) {
      lines.push("- Cullen commentary support:");
      for (const item of step.commentary_support) lines.push(`  - ${item}`);
    }
    if (step.template_support.length) {
      lines.push("- Template support:");
      for (const item of step.template_support.slice(0, 3)) {
        lines.push(`  - ${item.zh_template} ↔ ${item.en_template}; count ${item.count}; strength ${item.best_alignment_strength}`);
      }
    }
    if (step.candidate_audit_support.length) {
      lines.push("- Candidate audit support:");
      for (const item of step.candidate_audit_support.slice(0, 3)) {
        lines.push(`  - ${item.candidate_id}; status ${item.status}; score ${item.overall_score}`);
      }
    }
    if (step.alignment_risks.length) {
      lines.push("- Alignment risk:");
      for (const risk of step.alignment_risks) {
        lines.push(`  - Existing alignment paired with: ${risk.translation_en_clauses.join(" / ")}`);
      }
    }
    if (step.notes.length) {
      lines.push("- Notes:");
      for (const note of step.notes) lines.push(`  - ${note}`);
    }
  }
  lines.push("");
  lines.push("## Alignment Risks");
  lines.push("");
  if (!report.alignment_risks.length) {
    lines.push("No exploratory alignment risk detected for this pilot.");
  } else {
    lines.push(markdownTable(
      ["step", "source", "expected translation", "existing aligned translation", "confidence"],
      report.alignment_risks.map((risk) => [
        risk.step_id,
        risk.source_phrase,
        risk.expected_translation_phrase,
        (risk.translation_en_clauses || []).join(" / "),
        risk.confidence
      ])
    ));
  }
  lines.push("");
  lines.push("## Interpretation");
  lines.push("");
  lines.push("- This Proc is suitable for a curated algorithm-reconstruction pilot because source, translation, and Cullen commentary all support the main sequence.");
  lines.push("- It is not ready for automatic arithmetic validation because no concrete worked-example input value for 入蔀年 is present in this chunk.");
  lines.push("- Existing global template evidence is useful as schema support, but local source/translation/commentary binding remains the authority for this pilot.");
  lines.push("- All items are `do_not_writeback: true`.");
  lines.push("");
  return `${lines.join("\n")}\n`;
}

async function main() {
  const chunks = ensureArray(await readJson(CHUNKS_PATH));
  const discovery = await readJsonIfExists(TEMPLATE_DISCOVERY_PATH, {});
  const candidateAudit = await readJsonIfExists(CANDIDATE_AUDIT_PATH, {});
  const alignmentData = await readJsonIfExists(CLAUSE_ALIGNMENT_PATH, {});

  const chunk = chunks.find((item) =>
    item.id === TARGET.chunk_id || item.unit_id === TARGET.unit_id || item.procedure_id === TARGET.proc_id
  );
  if (!chunk) {
    throw new Error(`Could not find target chunk for ${TARGET.proc_id} / ${TARGET.unit_id}.`);
  }

  const stepCandidates = buildStepCandidates(chunk, discovery, candidateAudit, alignmentData);
  const report = {
    generated_at: new Date().toISOString(),
    inputs: {
      chunks: CHUNKS_PATH,
      template_discovery: TEMPLATE_DISCOVERY_PATH,
      candidate_evidence_audit: CANDIDATE_AUDIT_PATH,
      clause_alignments: CLAUSE_ALIGNMENT_PATH
    },
    outputs: {
      json: OUTPUT_JSON_PATH,
      markdown: OUTPUT_MD_PATH
    },
    pilot_scope: {
      ...TARGET,
      scope_control: "single_proc_only",
      purpose: "test whether current chunk/template/evidence outputs can support Proc-level algorithm reconstruction candidates",
      not_gold: true,
      do_not_writeback: true
    },
    source_chunk: {
      id: chunk.id,
      proc_id: chunk.procedure_id,
      unit_id: chunk.unit_id,
      section_path: chunk.section_path,
      book_page_start: chunk.book_page_start,
      book_page_end: chunk.book_page_end,
      source_text_zh: chunk.source_text_zh,
      translation_en: chunk.translation_en,
      commentary_excerpt: excerpt(chunk.commentary_en, 900),
      source_clauses: splitChineseClauses(chunk.source_text_zh),
      translation_sentences: splitEnglishSentences(chunk.translation_en)
    },
    method: {
      name: "curated_single_proc_evidence_assembly",
      description: "Uses fixed local source/translation anchors for Proc. 3.5 and gathers support from Cullen commentary plus exploratory template/audit/alignment outputs.",
      why_not_direct_alignment: "The exploratory clause alignment for this chunk is shifted by the source title phrase 推天正術, so this pilot treats alignment output as risk evidence rather than primary binding authority."
    },
    summary: summarize(stepCandidates, chunk),
    step_candidates: stepCandidates,
    alignment_risks: collectAlignmentRisks(stepCandidates),
    conclusion: {
      improves_machine_verifiability: true,
      how: "The pilot converts one Cullen-backed Proc into ordered, source-bound symbolic relations with explicit constants, variables, validation rules, and evidence scores.",
      still_human_readable_only: [
        "No worked example input value is available here, so arithmetic validation cannot run yet.",
        "The mapping from counting filled Rule Factors to floor division/modulo is a modern formalization and should remain caveated until human review.",
        "Global templates support operation families but do not by themselves prove local variable bindings."
      ],
      recommended_next_step: "Have a human review this single Proc output; if acceptable, generalize the same evidence-assembly pattern to the next Proc with strong commentary support."
    },
    do_not_writeback: true
  };

  await writeJson(OUTPUT_JSON_PATH, report);
  await fs.writeFile(resolveRepoPath(OUTPUT_MD_PATH), renderMarkdown(report), "utf8");

  console.log(JSON.stringify({
    output_json: OUTPUT_JSON_PATH,
    output_md: OUTPUT_MD_PATH,
    proc_id: report.summary.proc_id,
    step_count: report.summary.step_count,
    alignment_risk_count: report.summary.alignment_risk_count,
    average_evidence_score: report.summary.average_evidence_score,
    arithmetic_validation_ready_now: report.summary.arithmetic_validation_ready_now,
    verdict: report.summary.verdict
  }, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
