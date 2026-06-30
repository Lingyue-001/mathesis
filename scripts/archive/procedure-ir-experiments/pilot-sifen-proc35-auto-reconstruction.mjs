import fs from "node:fs/promises";
import { normalizeWhitespace, readJson, resolveRepoPath, writeJson } from "./cullen-oracle-common.mjs";

// Automatic single-Proc reconstruction trial.
//
// This is deliberately different from pilot-sifen-proc35-mini-pipeline.mjs:
// it does not contain a handwritten STEP_SPECS list. It only uses generic
// clause splitting, operation-shape recognizers, local source/translation order,
// commentary keyword lookup, and exploratory template/audit outputs.
//
// It is not gold, not a full parser, and not a writeback plan.

const CHUNKS_PATH = "tmp/procedure-ir/cullen-chunks.json";
const TEMPLATE_DISCOVERY_PATH = "tmp/procedure-ir/sifen-template-discovery.json";
const CANDIDATE_AUDIT_PATH = "tmp/procedure-ir/sifen-candidate-evidence-audit.json";
const CLAUSE_ALIGNMENT_PATH = "tmp/procedure-ir/sifen-clause-alignments.json";

const OUTPUT_JSON_PATH = "tmp/procedure-ir/sifen-proc35-auto-reconstruction.json";
const OUTPUT_MD_PATH = "tmp/procedure-ir/sifen-proc35-auto-reconstruction.md";

const TARGET_PROC_ID = "Proc. 3.5";
const TARGET_UNIT_ID = "§46";

const CHINESE_NUMERAL_VALUES = new Map([
  ["零", 0],
  ["〇", 0],
  ["一", 1],
  ["二", 2],
  ["三", 3],
  ["四", 4],
  ["五", 5],
  ["六", 6],
  ["七", 7],
  ["八", 8],
  ["九", 9],
  ["十", 10],
]);

const EN_STOPWORDS = new Set([
  "the", "this", "that", "with", "from", "into", "each", "filled", "call", "called",
  "one", "for", "and", "does", "not", "fill", "what", "more", "year", "years",
  "current", "there", "have", "has", "is", "are", "was", "were", "out", "set",
  "multiply", "count", "subtract", "remainder", "if", "it", "or"
]);

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

function normalizeHyphenated(text) {
  return normalizeWhitespace(text || "").replace(/([A-Za-z])- ([A-Za-z])/gu, "$1$2");
}

function splitChineseClauses(text) {
  return String(text || "")
    .split(/[，。．；;：]/u)
    .map((clause) => normalizeWhitespace(clause))
    .filter(Boolean);
}

function splitTranslationSentences(text) {
  return normalizeHyphenated(text)
    .split(/(?<=[.!?])\s+/u)
    .map((sentence) => normalizeWhitespace(sentence))
    .filter(Boolean);
}

function splitCommentarySentences(text) {
  return normalizeHyphenated(text)
    .split(/(?<=[.!?])\s+/u)
    .map((sentence) => normalizeWhitespace(sentence))
    .filter(Boolean);
}

function parseChineseSmallNumber(raw) {
  if (!raw) return null;
  if (/^\d+$/u.test(raw)) return Number(raw);
  if (CHINESE_NUMERAL_VALUES.has(raw)) return CHINESE_NUMERAL_VALUES.get(raw);
  if (raw.startsWith("十") && raw.length === 2) {
    return 10 + (CHINESE_NUMERAL_VALUES.get(raw[1]) || 0);
  }
  if (raw.length === 2 && raw.endsWith("十")) {
    return (CHINESE_NUMERAL_VALUES.get(raw[0]) || 1) * 10;
  }
  if (raw.length === 3 && raw[1] === "十") {
    return (CHINESE_NUMERAL_VALUES.get(raw[0]) || 1) * 10 + (CHINESE_NUMERAL_VALUES.get(raw[2]) || 0);
  }
  return null;
}

function expandCompoundChineseClause(clause, clauseIndex) {
  const clean = normalizeWhitespace(clause);
  const subclauses = [];
  const push = (raw, role = "source_subclause") => {
    const text = normalizeWhitespace(raw);
    if (!text) return;
    subclauses.push({
      raw_clause: text,
      parent_clause: clean,
      parent_clause_index: clauseIndex,
      subclause_index: subclauses.length,
      generated_by: role
    });
  };

  const setAndSubtract = clean.match(/^置(.+?)減([一二三四五六七八九十\d]+)$/u);
  if (setAndSubtract) {
    push(`置${setAndSubtract[1]}`, "generic_split_set_then_subtract");
    push(`減${setAndSubtract[2]}`, "generic_split_set_then_subtract");
    return subclauses;
  }

  push(clean);
  return subclauses;
}

function expandTranslationSentence(sentence, sentenceIndex) {
  const clean = normalizeWhitespace(sentence).replace(/^§\d+\s*/u, "");
  const subclauses = [];
  const push = (raw, role = "translation_subsentence") => {
    const text = normalizeWhitespace(raw);
    if (!text) return;
    subclauses.push({
      raw_clause: text.endsWith(".") || text.endsWith("?") || text.endsWith("!") ? text : `${text}.`,
      parent_sentence: sentence,
      parent_sentence_index: sentenceIndex,
      subsentence_index: subclauses.length,
      generated_by: role
    });
  };

  const setAndSubtract = clean.match(/^(Set out .+?) and subtract ([^.]+)\.$/iu);
  if (setAndSubtract) {
    push(setAndSubtract[1], "generic_split_set_then_subtract");
    push(`subtract ${setAndSubtract[2]}`, "generic_split_set_then_subtract");
    return subclauses;
  }

  push(clean);
  return subclauses;
}

function inferChineseOperation(rawClause) {
  const text = normalizeWhitespace(rawClause);
  if (/^推.+術$/u.test(text)) {
    return { operation_type: "procedure_scope_title", object_zh: text, value: null };
  }
  if (/^置/u.test(text)) {
    return { operation_type: "set_out", object_zh: text.replace(/^置/u, ""), value: null };
  }
  const subtract = text.match(/^減([一二三四五六七八九十\d]+)$/u) || text.match(/減([一二三四五六七八九十\d]+)$/u);
  if (subtract) {
    return { operation_type: "subtract", object_zh: null, value: parseChineseSmallNumber(subtract[1]), value_raw: subtract[1] };
  }
  const multiply = text.match(/^以(.+?)乘之$/u) || text.match(/^(.+?)以(.+?)乘之$/u);
  if (multiply) {
    return { operation_type: "multiply", object_zh: multiply[2] || multiply[1], value: null };
  }
  const countFilled = text.match(/^(?:滿|如)(.+?)得一$/u);
  if (countFilled) {
    return { operation_type: "count_filled", object_zh: countFilled[1], value: 1 };
  }
  const nameOutput = text.match(/^(?:名為|名曰|謂之)(.+)$/u);
  if (nameOutput) {
    return { operation_type: "name_output", object_zh: nameOutput[1], value: null };
  }
  const remainderOutput = text.match(/^(?:不滿|不盡)為(.+)$/u);
  if (remainderOutput) {
    return { operation_type: "remainder_output", object_zh: remainderOutput[1], value: null };
  }
  const threshold = text.match(/([一二三四五六七八九十\d]+)以上/u);
  if (threshold) {
    return { operation_type: "threshold_condition", object_zh: text, value: parseChineseSmallNumber(threshold[1]), value_raw: threshold[1] };
  }
  return { operation_type: "unknown", object_zh: text, value: null };
}

function inferEnglishOperation(rawClause) {
  const text = normalizeHyphenated(rawClause).replace(/^§\d+\s*/u, "");
  if (/^Set out\b/iu.test(text)) {
    return { operation_type: "set_out", object_en: text.replace(/^Set out\s+/iu, "").replace(/\.$/u, ""), value: null };
  }
  if (/^subtract\b/iu.test(text)) {
    const valueMatch = text.match(/\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten)\b/iu);
    return { operation_type: "subtract", object_en: null, value: englishNumber(valueMatch?.[1]), value_raw: valueMatch?.[1] || null };
  }
  if (/^Multiply\b/iu.test(text)) {
    return { operation_type: "multiply", object_en: extractEnglishObject(text, /^Multiply(?:\s+the\s+remainder)?\s+by\s+/iu), value: extractBracketNumber(text) };
  }
  if (/^Count one for each\b/iu.test(text)) {
    return { operation_type: "count_filled", object_en: extractEnglishObject(text, /^Count one for each\s+/iu), value: extractBracketNumber(text) };
  }
  if (/^Call this\b|^called\b/iu.test(text)) {
    return { operation_type: "name_output", object_en: text.replace(/^Call this\s+/iu, "").replace(/^called\s+/iu, "").replace(/\.$/u, ""), value: null };
  }
  if (/^(?:The remainder is|What does not fill)/iu.test(text)) {
    const object = text
      .replace(/^The remainder is\s+/iu, "")
      .replace(/^What does not fill.*?\bis\s+/iu, "")
      .replace(/\.$/u, "");
    return { operation_type: "remainder_output", object_en: object, value: null };
  }
  if (/^If\b.+\bor more\b/iu.test(text)) {
    const valueMatch = text.match(/\b(\d+)\s+or more\b/iu);
    return { operation_type: "threshold_condition", object_en: text.replace(/\.$/u, ""), value: valueMatch ? Number(valueMatch[1]) : null };
  }
  return { operation_type: "unknown", object_en: text, value: extractBracketNumber(text) };
}

function englishNumber(raw) {
  if (!raw) return null;
  const lowered = raw.toLowerCase();
  const map = { one: 1, two: 2, three: 3, four: 4, five: 5, six: 6, seven: 7, eight: 8, nine: 9, ten: 10 };
  if (lowered in map) return map[lowered];
  const value = Number(raw);
  return Number.isFinite(value) ? value : null;
}

function extractBracketNumber(text) {
  const match = text.match(/\[(\d[\d,]*)\]/u);
  if (!match) return null;
  return Number(match[1].replace(/,/gu, ""));
}

function extractEnglishObject(text, prefixPattern) {
  return normalizeWhitespace(text)
    .replace(prefixPattern, "")
    .replace(/\s+filled\.$/iu, "")
    .replace(/\.$/u, "");
}

function buildSourceUnits(chunk) {
  return splitChineseClauses(chunk.source_text_zh)
    .flatMap((clause, index) => expandCompoundChineseClause(clause, index))
    .map((unit, index) => ({
      ...unit,
      source_unit_id: `${chunk.id}:auto:zh:${index + 1}`,
      unit_index: index,
      ...inferChineseOperation(unit.raw_clause)
    }));
}

function buildTranslationUnits(chunk) {
  return splitTranslationSentences(chunk.translation_en)
    .flatMap((sentence, index) => expandTranslationSentence(sentence, index))
    .map((unit, index) => ({
      ...unit,
      translation_unit_id: `${chunk.id}:auto:en:${index + 1}`,
      unit_index: index,
      ...inferEnglishOperation(unit.raw_clause)
    }));
}

function alignUnits(sourceUnits, translationUnits) {
  const unusedTranslations = new Set(translationUnits.map((_, index) => index));
  const alignments = [];
  let lastTranslationIndex = -1;

  for (const source of sourceUnits) {
    if (source.operation_type === "procedure_scope_title") {
      alignments.push({
        source,
        translation: null,
        alignment_status: "source_scope_only",
        alignment_method: "generic_title_detection",
        alignment_score: 0.55,
        confidence: "medium",
        matched_features: ["source_matches_^推.+術$"]
      });
      continue;
    }

    const candidates = translationUnits
      .map((translation, index) => ({ translation, index }))
      .filter(({ index }) => unusedTranslations.has(index))
      .map(({ translation, index }) => {
        let score = 0;
        const features = [];
        if (translation.operation_type === source.operation_type) {
          score += 60;
          features.push("same_operation_type");
        }
        if (index > lastTranslationIndex) {
          score += 15;
          features.push("preserves_order");
        }
        const distance = Math.abs(index - Math.max(source.unit_index - 1, 0));
        score += Math.max(0, 12 - distance * 3);
        features.push(`order_distance_${distance}`);
        if (source.value !== null && translation.value !== null && source.value === translation.value) {
          score += 10;
          features.push("numeric_value_match");
        }
        if (source.operation_type === "set_out" && /years into the Obscuration/iu.test(translation.raw_clause)) {
          score += 8;
          features.push("set_out_object_match_obscuration_years");
        }
        return { translation, index, score, features };
      })
      .sort((a, b) => b.score - a.score || a.index - b.index);

    const best = candidates[0];
    if (!best || best.score < 35) {
      alignments.push({
        source,
        translation: null,
        alignment_status: "unmatched_source",
        alignment_method: "generic_operation_type_and_order",
        alignment_score: best?.score || 0,
        confidence: "low",
        matched_features: best?.features || []
      });
      continue;
    }

    unusedTranslations.delete(best.index);
    lastTranslationIndex = Math.max(lastTranslationIndex, best.index);
    alignments.push({
      source,
      translation: best.translation,
      alignment_status: "aligned",
      alignment_method: "generic_operation_type_and_order",
      alignment_score: best.score,
      confidence: best.score >= 80 ? "high" : best.score >= 58 ? "medium" : "low",
      matched_features: best.features
    });
  }

  for (const index of [...unusedTranslations].sort((a, b) => a - b)) {
    alignments.push({
      source: null,
      translation: translationUnits[index],
      alignment_status: "unmatched_translation",
      alignment_method: "generic_operation_type_and_order",
      alignment_score: 0,
      confidence: "low",
      matched_features: []
    });
  }

  return alignments;
}

function keywordCandidatesFromEnglish(text) {
  const normalized = normalizeHyphenated(text);
  const bracketValues = [...normalized.matchAll(/\[(\d[\d,]*)\]/gu)].map((match) => match[1].replace(/,/gu, ""));
  const capitalPhrases = [...normalized.matchAll(/\b(?:[A-Z][a-z]+(?:\s+|\s*-\s*)){0,4}[A-Z][a-z]+\b/gu)]
    .map((match) => normalizeWhitespace(match[0].replace(/\s*-\s*/gu, "")))
    .filter((phrase) => phrase.length > 3 && !/^(Set|Multiply|Count|Call|The|If)$/u.test(phrase));
  const lexical = normalizeSearchText(normalized)
    .split(/[^a-z0-9]+/u)
    .filter((token) => token.length >= 4 && !EN_STOPWORDS.has(token));
  return [...new Set([...bracketValues, ...capitalPhrases, ...lexical])].slice(0, 12);
}

function operationSpecificCommentaryKeywords(alignment) {
  const source = alignment.source;
  const translation = alignment.translation;
  if (!source && !translation) return [];
  const operationType = source?.operation_type || translation?.operation_type;
  const objectEn = translation?.object_en || "";
  const value = translation?.value ?? source?.value ?? null;
  const keywords = [];

  if (objectEn) keywords.push(objectEn);
  if (value !== null) keywords.push(String(value));

  switch (operationType) {
    case "set_out":
      if (/years into the Obscuration/iu.test(translation?.raw_clause || "")) {
        keywords.push("years into the obscuration", "ordinal number of year in the Obscuration");
      }
      break;
    case "subtract":
      keywords.push("subtract one", "subtract one from this number");
      break;
    case "multiply":
      if (value !== null) keywords.push(`${value} months`, "whole months have elapsed");
      break;
    case "count_filled":
      keywords.push("Rule Factor", "scale of Rule Factor", "filled");
      break;
    case "name_output":
      keywords.push(objectEn, "whole months have elapsed");
      break;
    case "remainder_output":
      keywords.push(objectEn, "This is the Intercalation Remainder", "fraction of a month");
      break;
    case "threshold_condition":
      if (value !== null) keywords.push(`${value} or more`);
      keywords.push("intercalary month", "Remainder is 12 or more");
      break;
    default:
      break;
  }
  return keywords.filter(Boolean);
}

function findCommentarySupport(commentarySentences, alignment) {
  const keywords = [
    ...keywordCandidatesFromEnglish(alignment.translation?.raw_clause || ""),
    ...operationSpecificCommentaryKeywords(alignment)
  ];
  const matches = [];
  for (const sentence of commentarySentences) {
    const normalizedSentence = normalizeSearchText(sentence);
    const score = keywords.reduce((sum, keyword) => {
      const needle = normalizeSearchText(keyword);
      return needle && normalizedSentence.includes(needle) ? sum + 1 : sum;
    }, 0);
    if (score > 0) {
      matches.push({ sentence, keyword_hits: score, matched_keywords: keywords.filter((keyword) => normalizedSentence.includes(normalizeSearchText(keyword))) });
    }
  }
  return matches.sort((a, b) => b.keyword_hits - a.keyword_hits).slice(0, 3);
}

function findTemplateSupport(discovery, alignment, chunkId) {
  if (!alignment.source || !alignment.translation) return [];
  const pairs = discovery?.bilingual_template_pairs || [];
  const sourceNeedle = normalizeSearchText(alignment.source.raw_clause);
  const translationNeedle = normalizeSearchText(alignment.translation.raw_clause);
  const matches = [];

  for (const pair of pairs) {
    for (const example of pair.examples || []) {
      if (example.chunk_id !== chunkId) continue;
      const exampleSource = normalizeSearchText(example.source_text_zh_clause || "");
      const exampleTranslation = normalizeSearchText(example.translation_en_clause || "");
      const sourceMatches = sourceNeedle.includes(exampleSource) || exampleSource.includes(sourceNeedle);
      const translationMatches = translationNeedle.includes(exampleTranslation) || exampleTranslation.includes(translationNeedle);
      if (sourceMatches && translationMatches) {
        matches.push({
          zh_template: pair.zh_template,
          en_template: pair.en_template,
          count: pair.count,
          distinct_chunks: pair.distinct_chunks,
          best_alignment_strength: pair.best_alignment_strength,
          source_text_zh_clause: example.source_text_zh_clause,
          translation_en_clause: example.translation_en_clause
        });
      }
    }
  }
  return matches.slice(0, 5);
}

function findCandidateAuditSupport(candidateAudit, alignment, chunkId) {
  if (!alignment.source || !alignment.translation) return [];
  const candidates = candidateAudit?.all_candidates || [];
  const sourceNeedle = normalizeSearchText(alignment.source.raw_clause);
  const translationNeedle = normalizeSearchText(alignment.translation.raw_clause);
  return candidates
    .filter((candidate) => (candidate.examples || []).some((example) => {
      if (example.chunk_id !== chunkId) return false;
      const source = normalizeSearchText(example.source_text_zh_clause || example.zh_match || "");
      const translation = normalizeSearchText(example.translation_en_clause || example.en_match || "");
      return (sourceNeedle.includes(source) || source.includes(sourceNeedle))
        && (translationNeedle.includes(translation) || translation.includes(translationNeedle));
    }))
    .slice(0, 5)
    .map((candidate) => ({
      candidate_id: candidate.candidate_id,
      candidate_type: candidate.candidate_type,
      status: candidate.status,
      overall_score: candidate.scores?.overall ?? null,
      failed_checks: candidate.failed_checks || []
    }));
}

function inferExpression(alignment, previousState) {
  const source = alignment.source;
  const translation = alignment.translation;
  if (!source) return { expression: null, status: "not_formalizable_yet", bindings: [], statePatch: {} };

  const objectLabel = source.object_zh || translation?.object_en || "value";
  const englishObject = translation?.object_en || null;
  const constant = translation?.value ?? source.value ?? null;

  switch (source.operation_type) {
    case "procedure_scope_title":
      return { expression: null, status: "not_formalizable_yet", bindings: [], statePatch: {} };
    case "set_out":
      return {
        expression: `current_value = input(${JSON.stringify(objectLabel)})`,
        status: "formalizable_with_caveat",
        bindings: [{ role: "input", source_object_zh: objectLabel, translation_object_en: englishObject }],
        statePatch: { current_value_label: objectLabel }
      };
    case "subtract":
      return {
        expression: `current_value = current_value - ${constant ?? "UNKNOWN"}`,
        status: constant !== null ? "formalizable_now" : "formalizable_with_caveat",
        bindings: [{ role: "constant", value: constant, source_value_raw: source.value_raw, translation_value_raw: translation?.value_raw || null }],
        statePatch: { current_value_label: "current_value_after_subtraction" }
      };
    case "multiply":
      return {
        expression: `current_value = current_value * ${englishObject || objectLabel}`,
        status: constant !== null ? "formalizable_now" : "formalizable_with_caveat",
        bindings: [{ role: "multiplier", source_object_zh: objectLabel, translation_object_en: englishObject, value: constant }],
        statePatch: { current_value_label: "product" }
      };
    case "count_filled":
      return {
        expression: `quotient = floor(current_value / ${englishObject || objectLabel})`,
        status: constant !== null ? "formalizable_with_caveat" : "formalizable_with_caveat",
        bindings: [{ role: "divisor_or_count_unit", source_object_zh: objectLabel, translation_object_en: englishObject, value: constant }],
        statePatch: { last_divisor: englishObject || objectLabel, last_divisor_value: constant, last_quotient_label: "quotient" }
      };
    case "name_output":
      return {
        expression: `${objectLabel} = ${previousState.last_quotient_label || "current_result"}`,
        status: "formalizable_with_caveat",
        bindings: [{ role: "named_output", source_object_zh: objectLabel, translation_object_en: englishObject }],
        statePatch: { last_named_output: objectLabel }
      };
    case "remainder_output":
      return {
        expression: `${objectLabel} = current_value mod ${previousState.last_divisor || "previous_divisor"}`,
        status: previousState.last_divisor ? "formalizable_with_caveat" : "needs_human_review",
        bindings: [{ role: "named_remainder", source_object_zh: objectLabel, translation_object_en: englishObject, divisor: previousState.last_divisor || null, divisor_value: previousState.last_divisor_value ?? null }],
        statePatch: { last_remainder_label: objectLabel }
      };
    case "threshold_condition":
      return {
        expression: `condition = ${previousState.last_remainder_label || "current_value"} >= ${constant ?? "UNKNOWN"}`,
        status: constant !== null ? "formalizable_now" : "formalizable_with_caveat",
        bindings: [{ role: "threshold", value: constant, source_value_raw: source.value_raw, condition_target: previousState.last_remainder_label || null }],
        statePatch: {}
      };
    default:
      return { expression: null, status: "needs_human_review", bindings: [], statePatch: {} };
  }
}

function evidenceScore(alignment, commentarySupport, templateSupport, candidateSupport, expression) {
  let score = 0;
  if (alignment.source) score += 0.18;
  if (alignment.translation) score += 0.18;
  if (alignment.alignment_status === "aligned") score += Math.min(0.24, alignment.alignment_score / 100 * 0.24);
  if (commentarySupport.length) score += 0.18;
  if (templateSupport.length) score += 0.1;
  if (candidateSupport.length) score += 0.06;
  if (expression) score += 0.06;
  return Number(Math.max(0, Math.min(1, score)).toFixed(3));
}

function confidenceFromScore(score) {
  if (score >= 0.78) return "high";
  if (score >= 0.58) return "medium";
  return "low";
}

function buildAutoCandidates(chunk, discovery, candidateAudit) {
  const sourceUnits = buildSourceUnits(chunk);
  const translationUnits = buildTranslationUnits(chunk);
  const commentarySentences = splitCommentarySentences(chunk.commentary_en);
  const alignments = alignUnits(sourceUnits, translationUnits);
  const state = {};

  const candidates = [];
  for (const alignment of alignments) {
    const expressionInfo = inferExpression(alignment, state);
    Object.assign(state, expressionInfo.statePatch);
    const commentarySupport = findCommentarySupport(commentarySentences, alignment);
    const templateSupport = findTemplateSupport(discovery, alignment, chunk.id);
    const candidateSupport = findCandidateAuditSupport(candidateAudit, alignment, chunk.id);
    const score = evidenceScore(alignment, commentarySupport, templateSupport, candidateSupport, expressionInfo.expression);

    candidates.push({
      candidate_id: `${chunk.procedure_id || TARGET_PROC_ID}.auto.${candidates.length + 1}`,
      source_unit: alignment.source ? {
        source_unit_id: alignment.source.source_unit_id,
        raw_clause: alignment.source.raw_clause,
        parent_clause: alignment.source.parent_clause,
        operation_type: alignment.source.operation_type,
        object_zh: alignment.source.object_zh ?? null,
        value: alignment.source.value ?? null
      } : null,
      translation_unit: alignment.translation ? {
        translation_unit_id: alignment.translation.translation_unit_id,
        raw_clause: alignment.translation.raw_clause,
        parent_sentence: alignment.translation.parent_sentence,
        operation_type: alignment.translation.operation_type,
        object_en: alignment.translation.object_en ?? null,
        value: alignment.translation.value ?? null
      } : null,
      inferred_operation_id: alignment.source?.operation_type || alignment.translation?.operation_type || "unknown",
      alignment_status: alignment.alignment_status,
      alignment_method: alignment.alignment_method,
      alignment_score: alignment.alignment_score,
      matched_features: alignment.matched_features,
      commentary_support: commentarySupport.map((item) => ({
        sentence: item.sentence,
        matched_keywords: item.matched_keywords
      })),
      template_support: templateSupport,
      candidate_audit_support: candidateSupport,
      formal_expression_candidate: expressionInfo.expression,
      formalization_status: expressionInfo.status,
      bindings: expressionInfo.bindings,
      evidence_score: score,
      confidence: confidenceFromScore(score),
      caveats: buildCaveats(alignment, expressionInfo, commentarySupport, templateSupport),
      generated_without_handwritten_step_spec: true,
      do_not_writeback: true
    });
  }
  return { sourceUnits, translationUnits, alignments, candidates };
}

function buildCaveats(alignment, expressionInfo, commentarySupport, templateSupport) {
  const caveats = [];
  if (alignment.alignment_status !== "aligned") caveats.push("not_aligned");
  if (!commentarySupport.length) caveats.push("no_commentary_sentence_matched_by_keywords");
  if (!templateSupport.length) caveats.push("no_same_chunk_template_support");
  if (expressionInfo.status !== "formalizable_now") caveats.push(expressionInfo.status);
  if (alignment.confidence === "low") caveats.push("low_alignment_confidence");
  if (alignment.source?.operation_type === "count_filled") caveats.push("counting_filled_as_floor_division_is_modern_formalization");
  if (alignment.source?.operation_type === "remainder_output") caveats.push("remainder_as_modulo_depends_on_previous_count_filled_step");
  return [...new Set(caveats)];
}

function inspectExploratoryAlignment(alignmentData, chunkId) {
  const chunks = alignmentData?.chunks || alignmentData?.chunk_alignments || alignmentData?.alignments_by_chunk || [];
  const item = chunks.find((entry) => entry.chunk_id === chunkId || entry.id === chunkId);
  if (!item) return { found: false, note: "No exploratory alignment output found." };
  const lowOrMismatched = (item.alignments || []).filter((alignment) => alignment.confidence !== "high");
  return {
    found: true,
    source_clause_count: item.source_clause_count,
    translation_clause_count: item.translation_clause_count,
    alignment_count: (item.alignments || []).length,
    high_count: (item.alignments || []).filter((alignment) => alignment.confidence === "high").length,
    medium_count: (item.alignments || []).filter((alignment) => alignment.confidence === "medium").length,
    low_count: (item.alignments || []).filter((alignment) => alignment.confidence === "low").length,
    note: "Existing exploratory alignment is recorded for comparison only; it is not used as binding authority by this automatic trial.",
    preview_non_high: lowOrMismatched.slice(0, 5).map((alignment) => ({
      source_text_zh_clauses: alignment.source_text_zh_clauses,
      translation_en_clauses: alignment.translation_en_clauses,
      confidence: alignment.confidence,
      score: alignment.score
    }))
  };
}

function summarize(candidates, sourceUnits, translationUnits) {
  const aligned = candidates.filter((candidate) => candidate.alignment_status === "aligned");
  const high = candidates.filter((candidate) => candidate.confidence === "high");
  const medium = candidates.filter((candidate) => candidate.confidence === "medium");
  const low = candidates.filter((candidate) => candidate.confidence === "low");
  const operationCounts = {};
  for (const candidate of candidates) {
    operationCounts[candidate.inferred_operation_id] = (operationCounts[candidate.inferred_operation_id] || 0) + 1;
  }
  return {
    target_proc_id: TARGET_PROC_ID,
    target_unit_id: TARGET_UNIT_ID,
    source_unit_count: sourceUnits.length,
    translation_unit_count: translationUnits.length,
    candidate_count: candidates.length,
    aligned_candidate_count: aligned.length,
    unmatched_source_count: candidates.filter((candidate) => candidate.alignment_status === "unmatched_source").length,
    unmatched_translation_count: candidates.filter((candidate) => candidate.alignment_status === "unmatched_translation").length,
    confidence_counts: {
      high: high.length,
      medium: medium.length,
      low: low.length
    },
    operation_counts: operationCounts,
    arithmetic_validation_ready_now: false,
    automation_verdict: "automatic_trial_partially_successful_but_requires_human_review",
    main_limitation: "Automatic rules can recover the local operation sequence, but semantic variable names and quotient/remainder formalization remain caveated."
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
  lines.push("# Sifen Proc. 3.5 Automatic Reconstruction Trial");
  lines.push("");
  lines.push("This file is an automatic trial. It does not use a handwritten step list and does not generate gold.");
  lines.push("");
  lines.push("## Summary");
  lines.push("");
  lines.push(markdownTable(
    ["Field", "Value"],
    [
      ["target", `${report.target.proc_id} / ${report.target.unit_id} / ${report.target.chunk_id}`],
      ["source units", report.summary.source_unit_count],
      ["translation units", report.summary.translation_unit_count],
      ["candidate count", report.summary.candidate_count],
      ["aligned candidates", report.summary.aligned_candidate_count],
      ["confidence", `high ${report.summary.confidence_counts.high}, medium ${report.summary.confidence_counts.medium}, low ${report.summary.confidence_counts.low}`],
      ["arithmetic validation ready", report.summary.arithmetic_validation_ready_now],
      ["automation verdict", report.summary.automation_verdict],
      ["main limitation", report.summary.main_limitation]
    ]
  ));
  lines.push("");
  lines.push("## Auto Candidates");
  lines.push("");
  lines.push(markdownTable(
    ["id", "op", "source", "translation", "expression", "score", "confidence", "caveats"],
    report.auto_candidates.map((candidate) => [
      candidate.candidate_id,
      candidate.inferred_operation_id,
      candidate.source_unit?.raw_clause || "",
      candidate.translation_unit?.raw_clause || "",
      candidate.formal_expression_candidate || "",
      candidate.evidence_score,
      candidate.confidence,
      candidate.caveats.join(", ")
    ])
  ));
  lines.push("");
  lines.push("## Evidence Highlights");
  for (const candidate of report.auto_candidates) {
    lines.push("");
    lines.push(`### ${candidate.candidate_id} ${candidate.inferred_operation_id}`);
    lines.push("");
    lines.push(`- Source: ${candidate.source_unit?.raw_clause || "(none)"}`);
    lines.push(`- Translation: ${candidate.translation_unit?.raw_clause || "(none)"}`);
    lines.push(`- Expression candidate: ${candidate.formal_expression_candidate || "(none)"}`);
    lines.push(`- Matched features: ${candidate.matched_features.join(", ") || "(none)"}`);
    if (candidate.commentary_support.length) {
      lines.push("- Commentary support:");
      for (const support of candidate.commentary_support.slice(0, 2)) {
        lines.push(`  - ${support.sentence}`);
      }
    }
    if (candidate.template_support.length) {
      lines.push("- Template support:");
      for (const support of candidate.template_support.slice(0, 2)) {
        lines.push(`  - ${support.zh_template} ↔ ${support.en_template}; count ${support.count}`);
      }
    }
  }
  lines.push("");
  lines.push("## Existing Exploratory Alignment Comparison");
  lines.push("");
  lines.push(`- Found: ${report.existing_exploratory_alignment.found}`);
  lines.push(`- Note: ${report.existing_exploratory_alignment.note}`);
  if (report.existing_exploratory_alignment.preview_non_high?.length) {
    lines.push("");
    lines.push(markdownTable(
      ["source", "translation", "confidence", "score"],
      report.existing_exploratory_alignment.preview_non_high.map((item) => [
        (item.source_text_zh_clauses || []).join(" / "),
        (item.translation_en_clauses || []).join(" / "),
        item.confidence,
        item.score
      ])
    ));
  }
  lines.push("");
  lines.push("## Quality Judgment");
  lines.push("");
  lines.push("- The automatic trial recovers the broad operation order for this Proc without a handwritten step list.");
  lines.push("- It still produces generic expressions such as `current_value = ...`; human/LLM review is needed to assign stable algorithmic variable names.");
  lines.push("- The count-filled and remainder steps are machine-formalizable only with caveats because floor/modulo are modern formalizations of Cullen's wording.");
  lines.push("- This supports building a reviewable extraction layer, but not yet autonomous full algorithm reconstruction.");
  lines.push("");
  return `${lines.join("\n")}\n`;
}

async function main() {
  const chunks = ensureArray(await readJson(CHUNKS_PATH));
  const discovery = await readJsonIfExists(TEMPLATE_DISCOVERY_PATH, {});
  const candidateAudit = await readJsonIfExists(CANDIDATE_AUDIT_PATH, {});
  const alignmentData = await readJsonIfExists(CLAUSE_ALIGNMENT_PATH, {});

  const chunk = chunks.find((item) => item.procedure_id === TARGET_PROC_ID || item.unit_id === TARGET_UNIT_ID);
  if (!chunk) {
    throw new Error(`Could not find ${TARGET_PROC_ID} / ${TARGET_UNIT_ID}`);
  }

  const { sourceUnits, translationUnits, candidates } = buildAutoCandidates(chunk, discovery, candidateAudit);
  const report = {
    generated_at: new Date().toISOString(),
    inputs: {
      chunks: CHUNKS_PATH,
      template_discovery: TEMPLATE_DISCOVERY_PATH,
      candidate_evidence_audit: CANDIDATE_AUDIT_PATH,
      clause_alignments_for_comparison_only: CLAUSE_ALIGNMENT_PATH
    },
    outputs: {
      json: OUTPUT_JSON_PATH,
      markdown: OUTPUT_MD_PATH
    },
    target: {
      proc_id: chunk.procedure_id,
      unit_id: chunk.unit_id,
      chunk_id: chunk.id,
      book_page_start: chunk.book_page_start,
      book_page_end: chunk.book_page_end
    },
    method: {
      name: "generic_clause_operation_alignment_without_handwritten_steps",
      no_handwritten_step_specs: true,
      generation_rules: [
        "split source by Chinese punctuation",
        "split generic 置...減N clauses into set_out and subtract subclauses",
        "split generic Set out ... and subtract ... translations into two subclauses",
        "infer operation type from generic Chinese and English operation shapes",
        "align source and translation by operation type plus order",
        "infer provisional expressions from operation type and local constants",
        "use commentary/template/audit outputs only as evidence support"
      ],
      not_gold: true,
      do_not_writeback: true
    },
    source_chunk: {
      source_text_zh: chunk.source_text_zh,
      translation_en: chunk.translation_en,
      commentary_excerpt: excerpt(chunk.commentary_en, 900)
    },
    parsed_units: {
      source_units: sourceUnits,
      translation_units: translationUnits
    },
    summary: summarize(candidates, sourceUnits, translationUnits),
    auto_candidates: candidates,
    existing_exploratory_alignment: inspectExploratoryAlignment(alignmentData, chunk.id),
    conclusion: {
      did_script_derive_steps_automatically: true,
      did_script_use_curated_step_specs: false,
      strongest_result: "The generic operation recognizers align the main sequence: set out, subtract, multiply, count filled, name quotient, name remainder, threshold condition.",
      weakest_result: "The generated expressions are intentionally generic and require human review for stable variables and modern floor/modulo interpretation.",
      suitable_next_use: "Use as an automated first-pass proposal for a human-reviewed Proc reconstruction sheet."
    },
    do_not_writeback: true
  };

  await writeJson(OUTPUT_JSON_PATH, report);
  await fs.writeFile(resolveRepoPath(OUTPUT_MD_PATH), renderMarkdown(report), "utf8");

  console.log(JSON.stringify({
    output_json: OUTPUT_JSON_PATH,
    output_md: OUTPUT_MD_PATH,
    target: `${report.target.proc_id} / ${report.target.unit_id}`,
    candidates: report.summary.candidate_count,
    aligned: report.summary.aligned_candidate_count,
    confidence_counts: report.summary.confidence_counts,
    operation_counts: report.summary.operation_counts,
    verdict: report.summary.automation_verdict
  }, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
