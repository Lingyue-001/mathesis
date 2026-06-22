import fs from "node:fs/promises";
import path from "node:path";
import {
  normalizeWhitespace,
  readJson,
  resolveRepoPath,
  writeJson,
} from "./cullen-oracle-common.mjs";

const ANCHORS_PATH = "tmp/procedure-ir/cullen-procedure-anchors.json";
const CHUNKS_PATH = "tmp/procedure-ir/cullen-chunks.json";
const SOURCE_SPANS_PATH = "tmp/procedure-ir/source_spans.json";

const RECONSTRUCTION_JSON = "tmp/procedure-ir/cullen-led-source-reconstruction.json";
const RECONSTRUCTION_MD = "tmp/procedure-ir/cullen-led-source-reconstruction.md";
const ALIGNMENT_CANDIDATES_JSON = "tmp/procedure-ir/cullen-led-source-alignment-candidates.json";
const ALIGNMENT_REVIEW_PACKET_MD = "tmp/procedure-ir/cullen-led-source-alignment-review-packet.md";
const AUDIT_JSON = "tmp/procedure-ir/cullen-led-source-reconstruction-audit.json";
const AUDIT_MD = "tmp/procedure-ir/cullen-led-source-reconstruction-audit.md";

const VALID_SYSTEMS = new Set(["santong", "sifen"]);
const GENERIC_TERMS = ["積日", "餘", "乘", "除", "法", "實", "置", "得一", "不盈", "滿", "算外"];
const TABLE_TITLE_HINTS = [
  "Table",
  "year-names",
  "Month Names",
  "Medial qi",
  "Lodges on equator",
  "Lodges on ecliptic",
  "12 stations",
];
const ENGLISH_OPERATION_PATTERNS = [
  ["cast out", /cast out/iu],
  ["multiply", /multiply/iu],
  ["subtract", /subtract|diminish/iu],
  ["add", /add|increase/iu],
  ["count outside", /outside the count|outside your count/iu],
  ["label", /label that|call this/iu],
  ["number from", /number from/iu],
  ["double", /double/iu],
  ["take", /take /iu],
  ["set out", /set out/iu],
];
const PROC_MARKER_RE = /Proc\.\s*([23])\.(\d+)(?!\d)/giu;
const HAN_BLOCK_RE = /[\p{Script=Han}0-9〇零一二三四五六七八九十百千廿卅甲乙丙丁戊己庚辛壬癸子丑寅卯辰巳午未申酉戌亥，。？！；：、〔〕（）［］【】「」『』〈〉《》]{4,}/gu;
const LEADING_NUMERIC_NOISE_RE = /^(?:\s|[\[(（【]?\d[\d,./\-]*[\])）】]?|[A-Za-z][A-Za-z0-9 .,'":;()\-]{1,40})+/u;
const KEY_OPERATION_TERMS = ["以", "乘", "盈", "得一", "除", "加", "減", "置", "名曰", "數", "算外", "不盈者", "求", "推"];
const QUOTE_TARGET_PROC_IDS = new Set(["Proc. 2.2", "Proc. 2.3", "Proc. 2.4", "Proc. 2.5", "Proc. 2.8", "Proc. 2.9", "Proc. 2.10", "Proc. 3.2"]);
const TARGET_SOURCE_RECOVERY_PROC_IDS = new Set(["Proc. 2.3", "Proc. 2.9", "Proc. 2.10"]);
const QUOTE_REPAIR_PROC_IDS = new Set(["Proc. 2.2", "Proc. 2.4", "Proc. 2.5", "Proc. 2.8"]);
const CHINESE_VARIANT_MAP = new Map([
  ["統", "统"],
  ["歲", "岁"],
  ["餘", "馀"],
  ["閏", "闰"],
  ["數", "数"],
  ["積", "积"],
  ["減", "减"],
  ["氣", "气"],
  ["牽", "牵"],
  ["筭", "算"],
  ["從", "从"],
  ["為", "为"],
  ["滿", "满"],
  ["紀", "纪"],
]);

function uniqueStrings(items) {
  return [...new Set((items ?? [])
    .flatMap((item) => Array.isArray(item) ? item : [item])
    .filter(Boolean)
    .map((item) => String(item).trim())
    .filter(Boolean))];
}

function foldChineseVariants(text) {
  return [...String(text ?? "")]
    .map((char) => CHINESE_VARIANT_MAP.get(char) ?? char)
    .join("");
}

function normalizeChinese(text) {
  return foldChineseVariants(String(text ?? ""))
    .replace(/[()（）<>〈〉《》「」『』【】〔〕\[\]]/gu, "")
    .replace(/[，。？！；：、\s]/gu, "")
    .trim();
}

function chineseOnly(text) {
  const matches = String(text ?? "").match(HAN_BLOCK_RE) ?? [];
  return normalizeWhitespace(matches.join(" "));
}

function preserveChineseEvidence(text) {
  const matches = String(text ?? "").match(/[\p{Script=Han}0-9〇零一二三四五六七八九十百千廿卅甲乙丙丁戊己庚辛壬癸子丑寅卯辰巳午未申酉戌亥，。？！；：、〔〕（）［］【】「」『』〈〉《》()\[\]]+/gu) ?? [];
  return normalizeWhitespace(matches.join(" "));
}

function trimToProcBoundary(text, procId) {
  const raw = String(text ?? "");
  const procIndex = raw.indexOf(procId);
  if (procIndex < 0) {
    return {
      beforeProc: raw,
      procScopedText: raw,
      boundaryIssue: false,
      nextProcId: "",
    };
  }

  const beforeProc = raw.slice(0, procIndex);
  const afterProc = raw.slice(procIndex + procId.length);
  const nextMatch = [...afterProc.matchAll(PROC_MARKER_RE)][0];
  if (!nextMatch) {
    return {
      beforeProc,
      procScopedText: afterProc,
      boundaryIssue: false,
      nextProcId: "",
    };
  }

  return {
    beforeProc,
    procScopedText: afterProc.slice(0, nextMatch.index),
    boundaryIssue: true,
    nextProcId: `Proc. ${nextMatch[1]}.${nextMatch[2]}`,
  };
}

function removeLeadingNumericNoise(text) {
  const value = normalizeWhitespace(String(text ?? ""));
  const firstHanIndex = value.search(/\p{Script=Han}/u);
  if (firstHanIndex < 0) {
    return { text: value, numericPrefixRemoved: false };
  }

  const leading = value.slice(0, firstHanIndex);
  if (/\d/.test(leading) || /[A-Za-z]/.test(leading)) {
    return {
      text: normalizeWhitespace(value.slice(firstHanIndex)),
      numericPrefixRemoved: /\d/.test(leading),
    };
  }

  const trimmed = value.replace(LEADING_NUMERIC_NOISE_RE, "");
  const changed = trimmed !== value;
  return {
    text: normalizeWhitespace(trimmed),
    numericPrefixRemoved: changed && /\d/.test(value.slice(0, value.length - trimmed.length)),
  };
}

function removeTrailingNumericNoise(text) {
  const value = normalizeWhitespace(String(text ?? ""));
  const trimmed = value.replace(/(?:\s|^)(?:\d[\d,./\-]*\s*){2,}$/u, "").trim();
  return {
    text: trimmed,
    removed: trimmed !== value,
  };
}

function cleanChineseQuoteSegment(text) {
  const chinese = chineseOnly(text);
  if (!chinese) {
    return { text: "", numericPrefixRemoved: false, removedNoiseSegments: [] };
  }
  const leading = removeLeadingNumericNoise(chinese);
  const trailing = removeTrailingNumericNoise(leading.text);
  const removedNoiseSegments = [];
  if (leading.numericPrefixRemoved) removedNoiseSegments.push("leading_numeric_or_page_noise");
  if (trailing.removed) removedNoiseSegments.push("trailing_numeric_noise");
  return {
    text: trailing.text,
    numericPrefixRemoved: leading.numericPrefixRemoved || trailing.removed,
    removedNoiseSegments,
  };
}

function splitChineseSentences(text) {
  return uniqueStrings(
    normalizeWhitespace(String(text ?? ""))
      .split(/[。；？！]/u)
      .map((item) => item.trim())
      .filter(Boolean),
  );
}

function dedupeRepeatedSentences(text) {
  const sentences = splitChineseSentences(text);
  const deduped = [];
  let hadDuplicate = false;
  for (const sentence of sentences) {
    const normalized = normalizeChinese(sentence);
    if (!normalized) continue;
    if (deduped.some((existing) => normalizeChinese(existing) === normalized)) {
      hadDuplicate = true;
      continue;
    }
    deduped.push(sentence);
  }
  return {
    text: deduped.join("。"),
    hadDuplicate,
  };
}

function buildMatchKey(text) {
  return normalizeChinese(text)
    .replace(/\d+/gu, "")
    .slice(0, 180);
}

function buildPreservedQuoteFromRaw(rawText) {
  const preserved = preserveChineseEvidence(rawText)
    .replace(/[．]/gu, "。");
  const procLeadIndex = preserved.search(/[推置]/u);
  const scoped = procLeadIndex >= 0 ? preserved.slice(procLeadIndex) : preserved;
  const leading = removeLeadingNumericNoise(scoped);
  const trailing = removeTrailingNumericNoise(leading.text);
  const deduped = dedupeRepeatedSentences(trailing.text);
  return {
    rawBoundedText: normalizeWhitespace(trailing.text),
    quote: normalizeWhitespace(deduped.text),
    numericPrefixRemoved: leading.numericPrefixRemoved || trailing.removed,
    cleanQuoteApplied: leading.numericPrefixRemoved || trailing.removed || deduped.hadDuplicate,
    quoteRepairApplied: Boolean(leading.numericPrefixRemoved || trailing.removed || deduped.hadDuplicate),
  };
}

function extractClauses(text) {
  return uniqueStrings(
    chineseOnly(text)
      .split(/[，。？！；：]/u)
      .map((clause) => clause.trim())
      .filter((clause) => normalizeChinese(clause).length >= 4),
  );
}

function isGenericClause(clause) {
  const normalized = normalizeChinese(clause);
  if (!normalized) return true;
  const stripped = GENERIC_TERMS.reduce((value, term) => value.replaceAll(normalizeChinese(term), ""), normalized);
  return stripped.length <= 2;
}

function extractEnglishOperations(text) {
  const value = String(text ?? "");
  return ENGLISH_OPERATION_PATTERNS
    .filter(([, pattern]) => pattern.test(value))
    .map(([name]) => name);
}

function extractChineseOperationPhrases(text) {
  const operationHints = ["置", "乘", "除", "加", "減", "命", "求", "起", "算外", "倍", "從"];
  return uniqueStrings(
    extractClauses(text).filter((clause) => operationHints.some((hint) => clause.includes(hint))),
  );
}

function extractArabicConstants(text) {
  return [...new Set(
    [...String(text ?? "").matchAll(/\[(\d[\d,]*)\]/gu)]
      .map((match) => Number(match[1].replace(/,/gu, "")))
      .filter(Number.isFinite),
  )];
}

function parseProcNumber(procId) {
  const match = String(procId ?? "").match(/Proc\. ([23])\.(\d+)(?!\d)/u);
  if (!match) return null;
  return { chapter: Number(match[1]), procNumber: Number(match[2]) };
}

function sortProc(left, right) {
  const leftInfo = parseProcNumber(left.cullen_proc_id);
  const rightInfo = parseProcNumber(right.cullen_proc_id);
  return (leftInfo?.chapter ?? 99) - (rightInfo?.chapter ?? 99)
    || (leftInfo?.procNumber ?? 999) - (rightInfo?.procNumber ?? 999);
}

function sortByLine(left, right) {
  return (left.line_start ?? 0) - (right.line_start ?? 0) || String(left.id).localeCompare(String(right.id));
}

function buildSourceIndexes(sourceSpansPayload) {
  const bySystem = new Map();
  for (const span of sourceSpansPayload.spans ?? []) {
    if (!VALID_SYSTEMS.has(span.source_id)) continue;
    if (!bySystem.has(span.source_id)) bySystem.set(span.source_id, []);
    bySystem.get(span.source_id).push(span);
  }
  for (const spans of bySystem.values()) spans.sort(sortByLine);

  const windows = new Map();
  const orderByWindowId = new Map();
  const orderBySpanId = new Map();

  for (const [system, spans] of bySystem.entries()) {
    const systemWindows = [];
    spans.forEach((span, index) => {
      orderBySpanId.set(span.id, index);
      const single = {
        window_id: `${system}:${span.id}`,
        system,
        source_span_ids: [span.id],
        line_start: span.line_start,
        line_end: span.line_end,
        text: span.text,
      };
      systemWindows.push(single);
      orderByWindowId.set(single.window_id, systemWindows.length - 1);

      const next = spans[index + 1];
      if (next && (next.line_start ?? 0) - (span.line_end ?? 0) <= 8) {
        const pair = {
          window_id: `${system}:${span.id}+${next.id}`,
          system,
          source_span_ids: [span.id, next.id],
          line_start: span.line_start,
          line_end: next.line_end,
          text: `${span.text} ${next.text}`,
        };
        systemWindows.push(pair);
        orderByWindowId.set(pair.window_id, systemWindows.length - 1);
      }
    });
    windows.set(system, systemWindows);
  }

  return { windows, orderByWindowId, orderBySpanId };
}

function extractTrailingChineseBlock(text, maxChars = 2200) {
  const tail = chineseOnly(String(text ?? "").slice(-maxChars));
  const clauses = extractClauses(tail);
  return clauses.length ? clauses.join("，") : tail;
}

function extractLeadingChineseBlocks(text, maxChars = 2600) {
  const head = String(text ?? "").slice(0, maxChars);
  return [...head.matchAll(HAN_BLOCK_RE)]
    .map((match) => normalizeWhitespace(match[0]))
    .filter(Boolean);
}

function deriveChineseQuoteFromScopedText(anchor, scopedText, beforeProc) {
  if (QUOTE_TARGET_PROC_IDS.has(anchor.cullen_proc_id)) {
    const targetedRaw = uniqueStrings([
      anchor.chinese_heading_excerpt ?? "",
      anchor.chinese_procedure_excerpt ?? "",
    ]).join(" ");
    const targetedQuote = buildPreservedQuoteFromRaw(targetedRaw);
    if (normalizeChinese(targetedQuote.quote).length >= 8) {
      return {
        rawBoundedText: targetedQuote.rawBoundedText,
        quote: targetedQuote.quote,
        matchKey: buildMatchKey(targetedQuote.quote),
        reason: "",
        numericPrefixRemoved: targetedQuote.numericPrefixRemoved,
        cleanQuoteApplied: targetedQuote.cleanQuoteApplied,
        rawTruncatedForMatching: false,
        targetProcQuoteRepairApplied: targetedQuote.quoteRepairApplied,
      };
    }
  }

  const derivedSegments = [];
  const rawSegments = [];

  const headingRaw = preserveChineseEvidence(anchor.chinese_heading_excerpt ?? "");
  const procedureRaw = preserveChineseEvidence(anchor.chinese_procedure_excerpt ?? "");
  const excerptStrength = normalizeChinese(`${headingRaw}${procedureRaw}`).length;
  const heading = cleanChineseQuoteSegment(headingRaw);
  const procedure = cleanChineseQuoteSegment(procedureRaw);
  if (normalizeChinese(heading.text).length >= 4) derivedSegments.push(heading);
  if (normalizeChinese(procedure.text).length >= 8) derivedSegments.push(procedure);
  if (normalizeChinese(headingRaw).length >= 4) rawSegments.push(headingRaw);
  if (normalizeChinese(procedureRaw).length >= 8) rawSegments.push(procedureRaw);

  if (excerptStrength < 20) {
    const trailingBeforeRaw = extractTrailingChineseBlock(beforeProc);
    const trailingBefore = cleanChineseQuoteSegment(trailingBeforeRaw);
    if (normalizeChinese(trailingBefore.text).length >= 4) derivedSegments.push(trailingBefore);
    if (normalizeChinese(trailingBeforeRaw).length >= 4) rawSegments.push(trailingBeforeRaw);
  }

  for (const block of extractLeadingChineseBlocks(scopedText).slice(0, excerptStrength < 20 ? 1 : 0)) {
    const cleaned = cleanChineseQuoteSegment(block);
    if (normalizeChinese(cleaned.text).length >= 4) derivedSegments.push(cleaned);
    if (normalizeChinese(block).length >= 4) rawSegments.push(block);
  }

  const mergedSegments = [];
  let numericPrefixRemoved = false;
  for (const segment of derivedSegments) {
    numericPrefixRemoved ||= segment.numericPrefixRemoved;
    if (!segment.text) continue;
    const current = normalizeChinese(segment.text);
    if (!current) continue;
    const duplicate = mergedSegments.some((item) => {
      const existing = normalizeChinese(item);
      return existing.includes(current) || current.includes(existing);
    });
    if (!duplicate) mergedSegments.push(segment.text);
  }

  const quote = mergedSegments.join(" ");
  const rawBoundedText = uniqueStrings(rawSegments).join(" ");
  if (normalizeChinese(quote).length < 8) {
    return {
      rawBoundedText,
      quote: "",
      matchKey: "",
      reason: TABLE_TITLE_HINTS.some((hint) => (anchor.english_title ?? "").includes(hint))
        ? "table_only_no_stable_cullen_quoted_chinese"
        : "unable_to_extract_stable_cullen_chinese_quote",
      numericPrefixRemoved,
      cleanQuoteApplied: false,
      rawTruncatedForMatching: excerptStrength < 20,
    };
  }

  return {
    rawBoundedText,
    quote,
    matchKey: buildMatchKey(quote),
    reason: "",
    numericPrefixRemoved,
    cleanQuoteApplied: numericPrefixRemoved || quote !== normalizeWhitespace(quote),
    rawTruncatedForMatching: excerptStrength < 20,
    targetProcQuoteRepairApplied: false,
  };
}

function stripTrailingChineseBleed(text) {
  const value = normalizeWhitespace(String(text ?? ""));
  const match = value.match(/(?:\s|^)([\p{Script=Han}0-9〇零一二三四五六七八九十百千廿卅甲乙丙丁戊己庚辛壬癸子丑寅卯辰巳午未申酉戌亥，。？！；：、〔〕（）［］【】「」『』〈〉《》 ]{12,})$/u);
  if (!match) return { text: value, removed: false };

  const tail = match[1];
  const alphaCount = (tail.match(/[A-Za-z]/gu) ?? []).length;
  const hanCount = (tail.match(/\p{Script=Han}/gu) ?? []).length;
  if (hanCount < 8 || alphaCount > 0) {
    return { text: value, removed: false };
  }

  return {
    text: normalizeWhitespace(value.slice(0, value.length - tail.length)),
    removed: true,
  };
}

function extractEnglishTranslation(anchor, scopedText) {
  const raw = scopedText || anchor.english_procedure_excerpt || "";
  const trimmed = stripTrailingChineseBleed(raw);
  return {
    text: normalizeWhitespace(trimmed.text).replace(/^[\s.:;,-]+/u, ""),
    bleedRemoved: trimmed.removed,
  };
}

function extractCommentaryExcerpt(anchor, scopedText) {
  const commentary = uniqueStrings([
    anchor.commentary_excerpt ?? "",
    scopedText,
  ]).join(" ");
  return normalizeWhitespace(commentary);
}

function extractHeadingTitle(anchor, quoteText) {
  const heading = cleanChineseQuoteSegment(anchor.chinese_heading_excerpt ?? "").text;
  if (normalizeChinese(heading).length >= 4) return heading;
  return extractClauses(quoteText)[0] ?? "";
}

function longestContainedClause(clauses, sourceText) {
  const source = normalizeChinese(sourceText);
  let best = "";
  for (const clause of clauses) {
    const normalized = normalizeChinese(clause);
    if (normalized.length < 4) continue;
    if (source.includes(normalized) && normalized.length > normalizeChinese(best).length) best = clause;
  }
  return best;
}

function ngramMatches(quoteText, sourceText) {
  const quote = normalizeChinese(quoteText);
  const source = normalizeChinese(sourceText);
  let bestLength = 0;
  const matches = [];
  for (const length of [18, 14, 12, 10, 8, 6, 4]) {
    const seen = new Set();
    for (let index = 0; index <= quote.length - length; index += 1) {
      const ngram = quote.slice(index, index + length);
      if (seen.has(ngram)) continue;
      seen.add(ngram);
      if (source.includes(ngram)) {
        matches.push(ngram);
        bestLength = Math.max(bestLength, length);
      }
    }
    if (bestLength >= length && length >= 10) break;
  }
  return {
    best_length: bestLength,
    matched_ngrams: uniqueStrings(matches).slice(0, 8),
  };
}

function scoreCandidate({ quoteText, matchKey, headingTitle, englishProcedureText, procIndex, totalProcCount, systemWindowOrder, candidateWindow }) {
  const sourceText = candidateWindow.text;
  const sourceNormalized = normalizeChinese(sourceText);
  const clauses = extractClauses(quoteText);
  const distinctiveClauses = clauses.filter((clause) => !isGenericClause(clause));
  const matchedDistinctiveClauses = distinctiveClauses.filter((clause) => sourceNormalized.includes(normalizeChinese(clause)));
  const matchedGenericClauses = clauses
    .filter((clause) => isGenericClause(clause))
    .filter((clause) => sourceNormalized.includes(normalizeChinese(clause)));
  const bestClause = longestContainedClause(distinctiveClauses, sourceText);
  const titleMatch = Boolean(headingTitle && sourceNormalized.includes(normalizeChinese(headingTitle)));
  const ngrams = ngramMatches(matchKey || quoteText, sourceText);
  const quoteConstants = extractArabicConstants(englishProcedureText);
  const sourceConstants = extractArabicConstants(sourceText);
  const matchedConstants = quoteConstants.filter((value) => sourceConstants.includes(value));
  const quoteOps = extractChineseOperationPhrases(quoteText);
  const matchedOps = quoteOps.filter((phrase) => sourceNormalized.includes(normalizeChinese(phrase)));

  const sourceOrder = systemWindowOrder.get(candidateWindow.window_id) ?? 0;
  const expectedOrder = totalProcCount > 1 ? procIndex / (totalProcCount - 1) : 0;
  const actualOrder = systemWindowOrder.size > 1 ? sourceOrder / (systemWindowOrder.size - 1) : 0;
  const orderDistance = Math.abs(expectedOrder - actualOrder);
  const orderScore = Math.max(0, 10 - Math.round(orderDistance * 20));

  let score = 0;
  if (titleMatch) score += 35;
  if (bestClause) score += normalizeChinese(bestClause).length >= 10 ? 35 : 20;
  score += matchedDistinctiveClauses.length * 10;
  if (ngrams.best_length >= 12) score += 30;
  else if (ngrams.best_length >= 8) score += 18;
  else if (ngrams.best_length >= 6) score += 10;
  score += matchedConstants.length * 6;
  score += matchedOps.length * 5;
  score += orderScore;

  const genericOnly = !titleMatch
    && !bestClause
    && matchedDistinctiveClauses.length === 0
    && matchedConstants.length === 0
    && matchedOps.length === 0
    && ngrams.best_length < 6
    && matchedGenericClauses.length > 0;

  let confidence = "insufficient";
  if (genericOnly) confidence = "generic_only_rejected";
  else if ((titleMatch && (bestClause || ngrams.best_length >= 8)) || matchedDistinctiveClauses.length >= 2 || ngrams.best_length >= 12) confidence = "high";
  else if (bestClause || matchedDistinctiveClauses.length === 1 || ngrams.best_length >= 8 || (titleMatch && ngrams.best_length >= 6)) confidence = "medium";
  else if (matchedGenericClauses.length || ngrams.best_length >= 4) confidence = "review";

  return {
    window_id: candidateWindow.window_id,
    source_span_ids: candidateWindow.source_span_ids,
    line_start: candidateWindow.line_start,
    line_end: candidateWindow.line_end,
    source_text_excerpt: normalizeWhitespace(sourceText).slice(0, 260),
    confidence,
    score,
    title_overlap: titleMatch ? headingTitle : "",
    matched_distinctive_clauses: matchedDistinctiveClauses.slice(0, 6),
    matched_generic_clauses: matchedGenericClauses.slice(0, 6),
    best_clause_overlap: bestClause,
    matched_ngrams: ngrams.matched_ngrams,
    longest_ngram_length: ngrams.best_length,
    matched_constants: matchedConstants,
    matched_operation_phrases: matchedOps,
    matched_english_operations: extractEnglishOperations(englishProcedureText),
    order_score: orderScore,
    generic_only_rejected: genericOnly,
  };
}

function prefilterCandidateWindows({ quoteText, matchKey, headingTitle, englishProcedureText, candidateWindows, procIndex, totalProcCount, systemWindowOrder }) {
  const clauses = extractClauses(quoteText).filter((clause) => !isGenericClause(clause)).slice(0, 4);
  const compactMatchKey = buildMatchKey(matchKey || quoteText);
  const keyFragments = [];
  for (const length of [12, 10, 8]) {
    if (compactMatchKey.length >= length) keyFragments.push(compactMatchKey.slice(0, length));
  }
  const constants = extractArabicConstants(englishProcedureText);
  const headingNormalized = normalizeChinese(headingTitle);

  const prefiltered = candidateWindows
    .map((candidateWindow) => {
    const sourceText = candidateWindow.text;
    const sourceNormalized = normalizeChinese(sourceText);
    let prefilterScore = 0;
    if (headingNormalized && sourceNormalized.includes(headingNormalized)) prefilterScore += 10;
    prefilterScore += clauses.filter((clause) => sourceNormalized.includes(normalizeChinese(clause))).length * 6;
    prefilterScore += keyFragments.filter((fragment) => fragment && sourceNormalized.includes(fragment)).length * 4;
    if (constants.length && constants.some((value) => sourceText.includes(`[${value}]`) || sourceText.includes(String(value)))) prefilterScore += 3;
    const sourceOrder = systemWindowOrder.get(candidateWindow.window_id) ?? 0;
    const expectedOrder = totalProcCount > 1 ? procIndex / (totalProcCount - 1) : 0;
    const actualOrder = systemWindowOrder.size > 1 ? sourceOrder / (systemWindowOrder.size - 1) : 0;
    const orderDistance = Math.abs(expectedOrder - actualOrder);
    if (orderDistance <= 0.12) prefilterScore += 1;
    return {
      candidateWindow,
      prefilterScore,
      orderDistance,
    };
  })
    .filter(({ prefilterScore, orderDistance }) => prefilterScore > 0 || orderDistance <= 0.12)
    .sort((left, right) => right.prefilterScore - left.prefilterScore || left.orderDistance - right.orderDistance)
    .map(({ candidateWindow }) => candidateWindow);

  return prefiltered.length ? prefiltered.slice(0, 24) : candidateWindows.slice(0, 16);
}

function assessQuoteIntegrity({ procId, quoteText, rawBoundedText }) {
  const normalizedQuote = normalizeChinese(quoteText);
  const normalizedRaw = normalizeChinese(rawBoundedText);
  if (!normalizedQuote) return { status: "fail", reason: "missing_quote" };

  const missingTerms = KEY_OPERATION_TERMS.filter((term) => rawBoundedText.includes(term) && !quoteText.includes(term));
  if (missingTerms.length) return { status: "fail", reason: `missing_key_terms:${missingTerms.join("|")}` };

  if (procId === "Proc. 2.2" && /[\[(（【].+[\])）】]/u.test(rawBoundedText)) {
    return { status: "needs_human_check", reason: "bracketed_variant_unresolved" };
  }

  if (normalizedRaw && normalizedQuote.length < Math.floor(normalizedRaw.length * 0.7)) {
    return { status: "needs_human_check", reason: "quote_shortened_significantly" };
  }

  return { status: "pass", reason: "" };
}

function isAdjacentContextWindow(primaryCandidate, candidate, spanOrderMap) {
  if (!primaryCandidate) return false;
  if (!candidate.source_span_ids.includes(primaryCandidate.source_span_ids[0])) return false;

  const primarySpanId = primaryCandidate.source_span_ids[0];
  const primaryIndex = spanOrderMap.get(primarySpanId);
  const otherSpanIds = candidate.source_span_ids.filter((spanId) => spanId !== primarySpanId);
  if (!otherSpanIds.length) return false;

  return otherSpanIds.every((spanId) => Math.abs((spanOrderMap.get(spanId) ?? 999) - primaryIndex) <= 1);
}

function isSubstantiveCandidate(candidate) {
  return Boolean(
    candidate.title_overlap
    || candidate.best_clause_overlap
    || (candidate.matched_distinctive_clauses?.length ?? 0) > 0
    || (candidate.matched_constants?.length ?? 0) > 0
    || (candidate.matched_operation_phrases?.length ?? 0) > 0
    || (candidate.longest_ngram_length ?? 0) >= 8
  );
}

function classifyPrimaryAndContext(candidates, spanOrderMap) {
  const primarySingle = candidates.find((candidate) => candidate.source_span_ids.length === 1)
    ?? candidates[0]
    ?? null;

  if (!primarySingle) {
    return {
      primarySourceSpanId: null,
      contextSourceSpanIds: [],
      relationshipType: "no_match",
      contextWindows: [],
      competingCandidates: [],
      weakDistantNoise: [],
      reclassifiedToContext: 0,
      weakDistantNoiseRejected: 0,
    };
  }

  const contextWindows = [];
  const competingCandidates = [];
  const weakDistantNoise = [];

  for (const candidate of candidates) {
    if (candidate.window_id === primarySingle.window_id) continue;

    if (isAdjacentContextWindow(primarySingle, candidate, spanOrderMap)) {
      contextWindows.push(candidate);
      continue;
    }

    const closeScore = candidate.score >= Math.max(primarySingle.score - 15, Math.floor(primarySingle.score * 0.75));
    const substantive = isSubstantiveCandidate(candidate);
    if (closeScore && substantive && candidate.confidence !== "review") {
      competingCandidates.push(candidate);
      continue;
    }

    weakDistantNoise.push(candidate);
  }

  let relationshipType = "single_primary_span";
  if (contextWindows.length) relationshipType = "primary_with_adjacent_context";
  if (competingCandidates.length) relationshipType = "true_competing_candidates";

  return {
    primarySourceSpanId: primarySingle.source_span_ids[0] ?? null,
    contextSourceSpanIds: uniqueStrings(contextWindows.flatMap((candidate) => candidate.source_span_ids.filter((spanId) => spanId !== primarySingle.source_span_ids[0]))),
    relationshipType,
    contextWindows,
    competingCandidates,
    weakDistantNoise,
    reclassifiedToContext: contextWindows.length,
    weakDistantNoiseRejected: weakDistantNoise.length,
  };
}

function recommendWriteback({ procId, quoteReason, topCandidates, primary, primaryCandidate, quoteIntegrityStatus }) {
  if (quoteReason) {
    return quoteReason === "table_only_no_stable_cullen_quoted_chinese"
      ? "do_not_write_back"
      : "insufficient_source_match";
  }

  if (!topCandidates.length) return "insufficient_source_match";
  if (quoteIntegrityStatus !== "pass") return "needs_human_review";
  if (primary.relationshipType === "true_competing_candidates") return "needs_human_review";
  if (
    procId === "Proc. 2.10"
    && primaryCandidate
    && !primaryCandidate.title_overlap
    && (primaryCandidate.matched_distinctive_clauses?.length ?? 0) < 2
    && (primaryCandidate.longest_ngram_length ?? 0) < 8
  ) {
    return "needs_human_review";
  }

  const safeBase = Boolean(
    primaryCandidate
    && primaryCandidate.source_span_ids.length === 1
    && (
      primaryCandidate.confidence === "high"
      || primaryCandidate.confidence === "medium"
      || (
        primary.contextWindows.length > 0
        && primary.competingCandidates.length === 0
        && (primaryCandidate.longest_ngram_length ?? 0) >= 6
        && (primaryCandidate.score ?? 0) >= 10
      )
    )
    && (
      isSubstantiveCandidate(primaryCandidate)
      || (primaryCandidate.longest_ngram_length ?? 0) >= 6
    )
  );

  if (!safeBase) return "needs_human_review";
  if (primary.contextWindows.length || primary.weakDistantNoise.length) return "safe_with_context";
  return "safe_to_write_back";
}

async function writeMarkdown(relativePath, content) {
  const target = resolveRepoPath(relativePath);
  await fs.mkdir(path.dirname(target), { recursive: true });
  await fs.writeFile(target, content, "utf8");
}

function renderReconstructionMarkdown(payload) {
  const lines = [
    "# Cullen-led Source Reconstruction",
    "",
    "Machine-generated review layer. Starts from Cullen Proc blocks and reconstructs source-side candidates from Cullen Chinese quoted text only.",
    "",
    `Generated: ${payload.generated_at}`,
    "",
  ];

  for (const item of payload.items) {
    lines.push(`## ${item.proc_id}`);
    lines.push(`- system: ${item.system}`);
    lines.push(`- english_title: ${item.english_title || "none"}`);
    lines.push(`- cullen_chinese_quoted_text: ${item.cullen_chinese_quoted_text || "none"}`);
    lines.push(`- primary_source_span_id: ${item.primary_source_span_id || "none"}`);
    lines.push(`- context_source_span_ids: ${item.context_source_span_ids.join(", ") || "none"}`);
    lines.push(`- relationship_type: ${item.relationship_type}`);
    lines.push(`- writeback_recommendation: ${item.writeback_recommendation}`);
    lines.push(`- blocker_reason: ${item.blocker_reason || "none"}`);
    lines.push("");
  }

  return `${lines.join("\n")}\n`;
}

function renderReviewPacketMarkdown(payload) {
  const lines = [
    "# Cullen-led Source Alignment Review Packet",
    "",
    "Machine-generated review packet. No candidates here are written back to anchors automatically.",
    "",
    `Generated: ${payload.generated_at}`,
    "",
  ];

  for (const item of payload.items) {
    lines.push(`## ${item.proc_id}`);
    lines.push("");
    lines.push(`- system: ${item.system}`);
    lines.push(`- english_title: ${item.english_title || "none"}`);
    lines.push(`- cullen_chinese_quoted_text: ${item.cullen_chinese_quoted_text || "none"}`);
    lines.push(`- cullen_english_translation: ${item.cullen_english_translation || "none"}`);
    lines.push(`- cullen_commentary_excerpt: ${item.cullen_commentary_excerpt || "none"}`);
    lines.push(`- primary_source_span_id: ${item.primary_source_span_id || "none"}`);
    lines.push(`- context_source_span_ids: ${item.context_source_span_ids.join(", ") || "none"}`);
    lines.push(`- relationship_type: ${item.relationship_type}`);
    lines.push(`- writeback_recommendation: ${item.writeback_recommendation}`);
    lines.push(`- blocker_reason: ${item.blocker_reason || "none"}`);
    lines.push("");
    lines.push("### Candidates");
    lines.push("");

    if (!item.candidates.length) {
      lines.push("- none", "");
      continue;
    }

    for (const candidate of item.candidates) {
      lines.push(`- source_span_ids: ${candidate.source_span_ids.join(", ")}`);
      lines.push(`  confidence: ${candidate.confidence}`);
      lines.push(`  score: ${candidate.score}`);
      lines.push(`  candidate_role: ${candidate.candidate_role || "candidate"}`);
      lines.push(`  lines: ${candidate.line_start}-${candidate.line_end}`);
      lines.push(`  title_overlap: ${candidate.title_overlap || "none"}`);
      lines.push(`  best_clause_overlap: ${candidate.best_clause_overlap || "none"}`);
      lines.push(`  matched_distinctive_clauses: ${(candidate.matched_distinctive_clauses ?? []).join(" | ") || "none"}`);
      lines.push(`  matched_generic_clauses: ${(candidate.matched_generic_clauses ?? []).join(" | ") || "none"}`);
      lines.push(`  matched_ngrams: ${(candidate.matched_ngrams ?? []).join(" | ") || "none"}`);
      lines.push(`  longest_ngram_length: ${candidate.longest_ngram_length}`);
      lines.push(`  matched_constants: ${(candidate.matched_constants ?? []).join(", ") || "none"}`);
      lines.push(`  matched_operation_phrases: ${(candidate.matched_operation_phrases ?? []).join(" | ") || "none"}`);
      lines.push(`  source_text_excerpt: ${candidate.source_text_excerpt}`);
      lines.push("");
    }
  }

  return `${lines.join("\n")}\n`;
}

function renderAuditMarkdown(audit) {
  const lines = [
    "# Cullen-led Source Reconstruction Audit",
    "",
    `Generated: ${audit.generated_at}`,
    "",
    `- cullen_proc_count: ${audit.cullen_proc_count}`,
    `- proc_with_cullen_chinese_quote_count: ${audit.proc_with_cullen_chinese_quote_count}`,
    `- quote_extraction_blocker_count: ${audit.quote_extraction_blocker_count}`,
    `- reconstructed_source_match_count: ${audit.reconstructed_source_match_count}`,
    `- safe_to_write_back_count: ${audit.safe_to_write_back_count}`,
    `- safe_with_context_count: ${audit.safe_with_context_count}`,
    `- needs_human_review_count: ${audit.needs_human_review_count}`,
    `- insufficient_source_match_count: ${audit.insufficient_source_match_count}`,
    `- primary_context_window_count: ${audit.primary_context_window_count}`,
    `- true_competing_candidate_count: ${audit.true_competing_candidate_count}`,
    `- quote_numeric_prefix_count: ${audit.quote_numeric_prefix_count}`,
    `- translation_bleed_into_next_proc_count: ${audit.translation_bleed_into_next_proc_count}`,
    `- proc_block_boundary_issue_count: ${audit.proc_block_boundary_issue_count}`,
    `- clean_quote_count: ${audit.clean_quote_count}`,
    `- primary_context_reclassified_count: ${audit.primary_context_reclassified_count}`,
    `- weak_distant_noise_rejected_count: ${audit.weak_distant_noise_rejected_count}`,
    `- generic_term_only_rejected_count: ${audit.generic_term_only_rejected_count}`,
    `- heading_body_split_count: ${audit.heading_body_split_count}`,
    `- proc_3_2_matched_sifen_L66_by_quote: ${audit.proc_3_2_matched_sifen_L66_by_quote}`,
    `- proc_3_2_writeback_recommendation: ${audit.proc_3_2_writeback_recommendation}`,
    "",
  ];

  if (audit.target_proc_summary?.length) {
    lines.push("## Target Proc Summary", "");
    for (const item of audit.target_proc_summary) {
      lines.push(`### ${item.proc_id}`);
      lines.push(`- quote_integrity_status: ${item.quote_integrity_status}`);
      lines.push(`- quote_integrity_reason: ${item.quote_integrity_reason || "none"}`);
      lines.push(`- primary_source_span_id: ${item.primary_source_span_id || "none"}`);
      lines.push(`- relationship_type: ${item.relationship_type}`);
      lines.push(`- writeback_recommendation: ${item.writeback_recommendation}`);
      lines.push(`- blocker_reason: ${item.blocker_reason || "none"}`);
      lines.push(`- quote_repaired: ${item.quote_repaired}`);
      lines.push(`- source_match_recovered: ${item.source_match_recovered}`);
      lines.push("");
    }
  }

  return `${lines.join("\n")}\n`;
}

async function main() {
  const [anchorPayload, chunkPayload, sourceSpansPayload] = await Promise.all([
    readJson(ANCHORS_PATH),
    readJson(CHUNKS_PATH),
    readJson(SOURCE_SPANS_PATH),
  ]);

  const chunksById = new Map((chunkPayload.chunks ?? []).map((chunk) => [chunk.id, chunk]));
  const { windows, orderByWindowId, orderBySpanId } = buildSourceIndexes(sourceSpansPayload);

  const anchors = (anchorPayload.items ?? [])
    .filter((anchor) => VALID_SYSTEMS.has(anchor.system))
    .sort(sortProc);

  let genericTermOnlyRejectedCount = 0;
  let quoteNumericPrefixCount = 0;
  let translationBleedIntoNextProcCount = 0;
  let procBlockBoundaryIssueCount = 0;
  let cleanQuoteCount = 0;
  let primaryContextReclassifiedCount = 0;
  let weakDistantNoiseRejectedCount = 0;

  const reconstructionItems = [];
  const alignmentCandidateItems = [];

  for (const [procIndex, anchor] of anchors.entries()) {
    const combinedBlockText = uniqueStrings([
      ...((anchor.heading_chunk_ids ?? []).map((id) => chunksById.get(id)?.text ?? "")),
      ...((anchor.body_chunk_ids ?? []).map((id) => chunksById.get(id)?.text ?? "")),
      ...((anchor.commentary_chunk_ids ?? []).map((id) => chunksById.get(id)?.text ?? "")),
    ]).join("\n\n");

    const boundary = trimToProcBoundary(combinedBlockText, anchor.cullen_proc_id);
    procBlockBoundaryIssueCount += boundary.boundaryIssue ? 1 : 0;

    const quoteResult = deriveChineseQuoteFromScopedText(anchor, boundary.procScopedText, boundary.beforeProc);
    quoteNumericPrefixCount += quoteResult.numericPrefixRemoved ? 1 : 0;
    cleanQuoteCount += quoteResult.cleanQuoteApplied ? 1 : 0;

    const englishTranslation = extractEnglishTranslation(anchor, boundary.procScopedText);
    translationBleedIntoNextProcCount += englishTranslation.bleedRemoved ? 1 : 0;

    const headingTitle = extractHeadingTitle(anchor, quoteResult.quote);
    const commentaryText = extractCommentaryExcerpt(anchor, boundary.procScopedText);
    const systemWindows = windows.get(anchor.system) ?? [];
    const systemWindowOrder = new Map(systemWindows.map((window) => [window.window_id, orderByWindowId.get(window.window_id) ?? 0]));
    const quoteIntegrity = assessQuoteIntegrity({
      procId: anchor.cullen_proc_id,
      quoteText: quoteResult.quote,
      rawBoundedText: quoteResult.rawBoundedText ?? quoteResult.quote,
    });
    const candidateWindows = normalizeChinese(quoteResult.quote).length >= 8
      ? prefilterCandidateWindows({
        quoteText: quoteResult.quote,
        matchKey: quoteResult.matchKey ?? quoteResult.quote,
        headingTitle,
        englishProcedureText: englishTranslation.text,
        candidateWindows: systemWindows,
        procIndex,
        totalProcCount: anchors.length,
        systemWindowOrder,
      })
      : [];

    const scoredCandidates = normalizeChinese(quoteResult.quote).length >= 8
      ? candidateWindows
        .map((candidateWindow) => scoreCandidate({
          quoteText: quoteResult.quote,
          matchKey: quoteResult.matchKey ?? quoteResult.quote,
          headingTitle,
          englishProcedureText: englishTranslation.text,
          procIndex,
          totalProcCount: anchors.length,
          systemWindowOrder,
          candidateWindow,
        }))
        .filter((candidate) => candidate.confidence !== "insufficient")
        .sort((left, right) =>
          (right.score - left.score)
          || (left.source_span_ids.length - right.source_span_ids.length)
          || left.line_start - right.line_start
        )
      : [];

    genericTermOnlyRejectedCount += scoredCandidates.filter((candidate) => candidate.generic_only_rejected).length;
    const nonGenericCandidates = scoredCandidates.filter((candidate) => candidate.confidence !== "generic_only_rejected");
    const topCandidates = nonGenericCandidates.slice(0, 8);
    const primary = classifyPrimaryAndContext(topCandidates, orderBySpanId);
    primaryContextReclassifiedCount += primary.reclassifiedToContext;
    weakDistantNoiseRejectedCount += primary.weakDistantNoiseRejected;

    const primaryCandidate = primary.primarySourceSpanId
      ? topCandidates.find((candidate) => candidate.source_span_ids.length === 1 && candidate.source_span_ids[0] === primary.primarySourceSpanId)
      : null;

    const writebackRecommendation = recommendWriteback({
      procId: anchor.cullen_proc_id,
      quoteReason: quoteResult.reason,
      topCandidates,
      primary,
      primaryCandidate,
      quoteIntegrityStatus: quoteIntegrity.status,
    });

    const enrichedCandidates = topCandidates.map((candidate) => {
      let candidateRole = "candidate";
      if (primary.primarySourceSpanId && candidate.source_span_ids.length === 1 && candidate.source_span_ids[0] === primary.primarySourceSpanId) candidateRole = "primary";
      else if (primary.contextWindows.some((item) => item.window_id === candidate.window_id)) candidateRole = "adjacent_context_window";
      else if (primary.competingCandidates.some((item) => item.window_id === candidate.window_id)) candidateRole = "true_competing_candidate";
      else if (primary.weakDistantNoise.some((item) => item.window_id === candidate.window_id)) candidateRole = "weak_distant_noise";
      return { ...candidate, candidate_role: candidateRole };
    });

    reconstructionItems.push({
      proc_id: anchor.cullen_proc_id,
      chapter: parseProcNumber(anchor.cullen_proc_id)?.chapter ?? null,
      system: anchor.system,
      english_title: anchor.english_title ?? "",
      cullen_chinese_raw_bounded_text: quoteResult.rawBoundedText ?? quoteResult.quote,
      cullen_chinese_quoted_text: quoteResult.quote,
      cullen_chinese_match_key: quoteResult.matchKey ?? buildMatchKey(quoteResult.quote),
      raw_truncated_for_matching: Boolean(quoteResult.rawTruncatedForMatching),
      target_proc_quote_repaired: Boolean(quoteResult.targetProcQuoteRepairApplied),
      quote_integrity_status: quoteIntegrity.status,
      quote_integrity_reason: quoteIntegrity.reason,
      cullen_english_translation: englishTranslation.text,
      cullen_commentary_excerpt: commentaryText,
      heading_chunk_ids: anchor.heading_chunk_ids ?? [],
      body_chunk_ids: anchor.body_chunk_ids ?? [],
      commentary_chunk_ids: anchor.commentary_chunk_ids ?? [],
      heading_body_split: Boolean(
        anchor.heading_body_split
        || (
          (anchor.heading_chunk_ids ?? []).length
          && (anchor.body_chunk_ids ?? []).length
          && JSON.stringify(anchor.heading_chunk_ids) !== JSON.stringify(anchor.body_chunk_ids)
        )
      ),
      title_or_heading: headingTitle,
      chinese_quote_clauses: extractClauses(quoteResult.quote),
      key_constants: uniqueStrings([
        ...(anchor.key_constants ?? []),
        ...extractArabicConstants(englishTranslation.text).map(String),
      ]),
      operation_skeleton: uniqueStrings([
        ...(anchor.operation_skeleton ?? []),
        ...extractEnglishOperations(englishTranslation.text),
        ...extractChineseOperationPhrases(quoteResult.quote),
      ]),
      current_chunk_text_excerpt: normalizeWhitespace(combinedBlockText).slice(0, 1200),
      matched_source_span_ids: primary.primarySourceSpanId
        ? uniqueStrings([primary.primarySourceSpanId, ...primary.contextSourceSpanIds])
        : [],
      matched_line_start: primaryCandidate?.line_start ?? null,
      matched_line_end: primaryCandidate?.line_end ?? null,
      match_method: primary.primarySourceSpanId ? "cullen_quoted_chinese_overlap" : "no_match",
      match_confidence: primaryCandidate?.confidence ?? "insufficient",
      overlap_score: primaryCandidate?.score ?? 0,
      distinctive_overlap_terms: uniqueStrings([
        ...(primaryCandidate?.matched_distinctive_clauses ?? []),
        ...(primaryCandidate?.matched_ngrams ?? []),
        ...(primaryCandidate?.matched_operation_phrases ?? []),
      ]),
      generic_terms_ignored: GENERIC_TERMS,
      primary_source_span_id: primary.primarySourceSpanId,
      context_source_span_ids: primary.contextSourceSpanIds,
      relationship_type: primary.relationshipType,
      writeback_recommendation: writebackRecommendation,
      safe_to_write_back: writebackRecommendation === "safe_to_write_back",
      safe_with_context: writebackRecommendation === "safe_with_context",
      target_proc_source_match_recovered: Boolean(
        TARGET_SOURCE_RECOVERY_PROC_IDS.has(anchor.cullen_proc_id)
        && primary.primarySourceSpanId
      ),
      blocker_reason: quoteResult.reason
        || (anchor.cullen_proc_id === "Proc. 2.10" && writebackRecommendation === "needs_human_review"
          ? "shared_suffix_overlap_only_with_santong_L116"
          : "")
        || (writebackRecommendation === "insufficient_source_match" ? "no_non_generic_source_candidate_from_cullen_quote" : ""),
      proc_block_boundary_issue: boundary.boundaryIssue,
      quote_numeric_prefix_removed: quoteResult.numericPrefixRemoved,
      translation_bleed_removed: englishTranslation.bleedRemoved,
      notes: uniqueStrings([
        boundary.boundaryIssue ? `trimmed_before_${boundary.nextProcId || "next_proc"}` : "",
        quoteResult.numericPrefixRemoved ? "quote_numeric_prefix_removed" : "",
        englishTranslation.bleedRemoved ? "translation_trailing_chinese_bleed_removed" : "",
      ]).join("; "),
      candidates: enrichedCandidates,
    });

    alignmentCandidateItems.push({
      proc_id: anchor.cullen_proc_id,
      system: anchor.system,
      cullen_chinese_quoted_text: quoteResult.quote,
      cullen_chinese_match_key: quoteResult.matchKey ?? buildMatchKey(quoteResult.quote),
      quote_integrity_status: quoteIntegrity.status,
      title_or_heading: headingTitle,
      primary_source_span_id: primary.primarySourceSpanId,
      context_source_span_ids: primary.contextSourceSpanIds,
      relationship_type: primary.relationshipType,
      writeback_recommendation: writebackRecommendation,
      candidates: enrichedCandidates,
    });
  }

  const reconstructionPayload = {
    generated_at: new Date().toISOString(),
    note: "Machine-generated Cullen-led source reconstruction layer. Starts from Cullen Proc blocks and does not write back to cullen-procedure-anchors.json.",
    items: reconstructionItems,
  };
  const alignmentPayload = {
    generated_at: reconstructionPayload.generated_at,
    note: "Machine-generated Cullen-led source alignment candidates from Cullen Chinese quoted text.",
    items: alignmentCandidateItems,
  };

  const quoteExtractionBlockers = reconstructionItems
    .filter((item) => item.blocker_reason === "unable_to_extract_stable_cullen_chinese_quote" || item.blocker_reason === "table_only_no_stable_cullen_quoted_chinese")
    .map((item) => ({ proc_id: item.proc_id, reason: item.blocker_reason }));

  const proc32Item = reconstructionItems.find((item) => item.proc_id === "Proc. 3.2");
  const proc32Matched = proc32Item?.primary_source_span_id === "sifen:L66";
  const targetProcSummary = reconstructionItems
    .filter((item) => QUOTE_TARGET_PROC_IDS.has(item.proc_id))
    .map((item) => ({
      proc_id: item.proc_id,
      quote_integrity_status: item.quote_integrity_status,
      quote_integrity_reason: item.quote_integrity_reason,
      primary_source_span_id: item.primary_source_span_id,
      relationship_type: item.relationship_type,
      writeback_recommendation: item.writeback_recommendation,
      blocker_reason: item.blocker_reason,
      quote_repaired: Boolean(item.target_proc_quote_repaired || (QUOTE_REPAIR_PROC_IDS.has(item.proc_id) && item.quote_integrity_status !== "fail")),
      source_match_recovered: Boolean(item.target_proc_source_match_recovered),
    }));

  const auditPayload = {
    generated_at: reconstructionPayload.generated_at,
    cullen_proc_count: reconstructionItems.length,
    proc_with_cullen_chinese_quote_count: reconstructionItems.filter((item) => normalizeChinese(item.cullen_chinese_quoted_text).length >= 8).length,
    quote_extraction_blocker_count: quoteExtractionBlockers.length,
    reconstructed_source_match_count: reconstructionItems.filter((item) => ["safe_to_write_back", "safe_with_context", "needs_human_review"].includes(item.writeback_recommendation)).length,
    safe_to_write_back_count: reconstructionItems.filter((item) => item.writeback_recommendation === "safe_to_write_back").length,
    safe_with_context_count: reconstructionItems.filter((item) => item.writeback_recommendation === "safe_with_context").length,
    needs_human_review_count: reconstructionItems.filter((item) => item.writeback_recommendation === "needs_human_review").length,
    insufficient_source_match_count: reconstructionItems.filter((item) => item.writeback_recommendation === "insufficient_source_match" || item.writeback_recommendation === "do_not_write_back").length,
    primary_context_window_count: reconstructionItems.filter((item) => item.relationship_type === "primary_with_adjacent_context").length,
    true_competing_candidate_count: reconstructionItems.filter((item) => item.relationship_type === "true_competing_candidates").length,
    quote_numeric_prefix_count: quoteNumericPrefixCount,
    translation_bleed_into_next_proc_count: translationBleedIntoNextProcCount,
    proc_block_boundary_issue_count: procBlockBoundaryIssueCount,
    clean_quote_count: cleanQuoteCount,
    primary_context_reclassified_count: primaryContextReclassifiedCount,
    weak_distant_noise_rejected_count: weakDistantNoiseRejectedCount,
    generic_term_only_rejected_count: genericTermOnlyRejectedCount,
    heading_body_split_count: reconstructionItems.filter((item) => item.heading_body_split).length,
    safe_with_context_integrity_pass_count: reconstructionItems.filter((item) => item.writeback_recommendation === "safe_with_context" && item.quote_integrity_status === "pass").length,
    remaining_translation_bleed_count: reconstructionItems.filter((item) => /Proc\.\s*[23]\.\d+/u.test(item.cullen_english_translation)).length,
    proc_3_2_matched_sifen_L66_by_quote: Boolean(proc32Matched),
    proc_3_2_writeback_recommendation: proc32Item?.writeback_recommendation ?? "missing",
    target_proc_summary: targetProcSummary,
    quote_extraction_blockers: quoteExtractionBlockers,
    insufficient_procs: reconstructionItems
      .filter((item) => item.writeback_recommendation === "insufficient_source_match" || item.writeback_recommendation === "do_not_write_back")
      .map((item) => ({ proc_id: item.proc_id, reason: item.blocker_reason || item.writeback_recommendation })),
  };

  await writeJson(RECONSTRUCTION_JSON, reconstructionPayload);
  await writeJson(ALIGNMENT_CANDIDATES_JSON, alignmentPayload);
  await writeJson(AUDIT_JSON, auditPayload);
  await writeMarkdown(RECONSTRUCTION_MD, renderReconstructionMarkdown(reconstructionPayload));
  await writeMarkdown(ALIGNMENT_REVIEW_PACKET_MD, renderReviewPacketMarkdown(reconstructionPayload));
  await writeMarkdown(AUDIT_MD, renderAuditMarkdown(auditPayload));

  console.log([
    "audit:cullen-led-source-reconstruction",
    `cullen_proc_count=${auditPayload.cullen_proc_count}`,
    `reconstructed_source_match_count=${auditPayload.reconstructed_source_match_count}`,
    `safe_with_context_count=${auditPayload.safe_with_context_count}`,
    `true_competing_candidate_count=${auditPayload.true_competing_candidate_count}`,
    `quote_numeric_prefix_count=${auditPayload.quote_numeric_prefix_count}`,
    `translation_bleed_into_next_proc_count=${auditPayload.translation_bleed_into_next_proc_count}`,
  ].join(" "));
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});




