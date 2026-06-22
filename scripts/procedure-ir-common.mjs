import {
  extractAsciiNumberValues,
  normalizeWhitespace,
  unique,
} from "./cullen-oracle-common.mjs";

export const CHINESE_NUMBER_MAP = new Map([
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
  ["百", 100],
  ["千", 1000],
  ["万", 10000],
  ["萬", 10000],
  ["亿", 100000000],
  ["億", 100000000],
]);

export const CHINESE_UNIT_VALUES = new Map([
  ["十", 10],
  ["百", 100],
  ["千", 1000],
  ["万", 10000],
  ["萬", 10000],
  ["亿", 100000000],
  ["億", 100000000],
]);

export const CHINESE_NUMERAL_PATTERN = /[零〇一二三四五六七八九十百千万萬亿億两兩\d]+/gu;

export const QUANTITY_ENGLISH_MAP = {
  santong: {
    闰法: ["Intercalation Factor"],
    日法: ["Day Factor"],
    统法: ["Concordance Factor", "Tong Factor"],
    元法: ["Origin Factor"],
    通法: ["Lunation Factor"],
    月法: ["Lunation Factor"],
    章月: ["Rule Months"],
    章岁: ["Rule Years", "Intercalation Factor"],
    周天: ["Circuits of Heaven"],
    四时: ["Four Seasons"],
    三统: ["Three Concordances"],
    岁中: ["Year Medial [Qi]", "Year Medial Qi"],
    积月: ["Accumulated Months"],
    积日: ["Accumulated Days"],
    小馀: ["Lesser Remainder"],
    大馀: ["Greater Remainder"],
    算馀: ["Reckoning Surplus"],
    中法: ["Medial [Qi] Factor", "Medial Qi Factor"],
    见中法: ["Entry Medial [Qi] Factor"],
    见中日法: ["Entry Medial Qi Day Factor"],
    见月法: ["Entry Lunation Factor"],
    见月日法: ["Entry Lunation Day Factor"],
    月周: ["Lunar Circuits"],
  },
  sifen: {
    蔀月: ["Obscuration Months"],
    蔀日: ["Obscuration Days"],
    没数: ["Obscuration Number"],
    没法: ["Obscuration Factor"],
    日法: ["Day Factor"],
    通法: ["Compatibility Factor"],
    积没: ["Accumulated Obscurations", "Accumulated Obscuration Days"],
    没馀: ["Obscuration Remainder"],
    积日: ["Accumulated Days"],
    小馀: ["Lesser Remainder"],
    大馀: ["Greater Remainder"],
    入蔀积月: ["Months Entered into the Obscuration"],
    入蔀年: ["Years Entered into the Obscuration"],
  },
  jiuzhi: {
    积日: ["Accumulated Days"],
    小馀: ["Lesser Remainder"],
    小月: ["Small Months"],
    甲子之次: ["Sexagenary Day Sequence", "Jiazi Sequence"],
    七曜直日次: ["Seven Governors Day Sequence", "Seven Luminaries Day Sequence"],
  },
};

export const CULLEN_TERM_ALIASES = Object.fromEntries(
  Object.entries(QUANTITY_ENGLISH_MAP).flatMap(([, value]) =>
    Object.entries(value).map(([name, englishTerms]) => [name, englishTerms])
  )
);

export const OPERATION_TERM_MAP = {
  multiply: ["multiply"],
  add: ["add"],
  subtract: ["subtract"],
  divide: ["divide"],
  quotient_remainder: ["divide", "quotient_remainder"],
  mod_cycle: ["divide", "mod_cycle"],
  set: ["set"],
};

export function splitChineseSentences(text) {
  return text
    .split(/[。；;]/u)
    .map((sentence) => sentence.trim())
    .filter(Boolean);
}

export function normalizeChineseName(name) {
  return (name ?? "")
    .trim()
    .replace(/[，,。；：:「」『』（）()〈〉《》\[\]]/gu, "")
    .replace(/^(以|置|又置|重張位下位|重張位下|重張位|其|其餘|其小餘及|其小餘|其小|其度分|所入|所經|所求|求其|求後|求|加自入|自入|從|名為|名曰|得|為|曰)+/gu, "")
    .replace(/(乘之|除之|加之|減之|并之|滿.+$|盈.+$|不盡.+$|不滿.+$|棄之.+$|命之.+$|算外.+$)/gu, "")
    .trim();
}

export function chineseNumeralToNumber(input) {
  if (!input) return null;
  const normalized = input
    .trim()
    .replace(/[兩两]/gu, "二")
    .replace(/[^\d零〇一二三四五六七八九十百千万萬亿億]/gu, "");
  if (!normalized) return null;
  if (/^\d+$/u.test(normalized)) return Number(normalized);

  let total = 0;
  let section = 0;
  let number = 0;

  for (const char of normalized) {
    const value = CHINESE_NUMBER_MAP.get(char);
    if (value === undefined) return null;
    if (CHINESE_UNIT_VALUES.has(char)) {
      if (value >= 10000) {
        section = (section + (number || 0) || 1) * value;
        total += section;
        section = 0;
      } else {
        section += (number || 1) * value;
      }
      number = 0;
    } else {
      number = value;
    }
  }

  return total + section + number;
}

export function lexicalCountCandidate(rawName, sourceId = null) {
  const text = normalizeChineseName(rawName);
  const match = text.match(/^([零〇一二三四五六七八九十百千万萬亿億两兩\d]+)([\p{Script=Han}]{1,16})$/u);
  if (!match) return null;
  const value = chineseNumeralToNumber(match[1]);
  if (value === null) return null;
  return {
    source_id: sourceId,
    name_zh: text,
    normalized_name: normalizeChineseName(match[2]),
    value,
    quantity_role: inferQuantityRole(match[2]),
    quantity_value_source: "lexical_count",
    confidence: "B_textual_semantic",
    source_span_id: null,
    english_terms: [],
  };
}

export function inferQuantityRole(name) {
  const normalized = normalizeChineseName(name);
  if (!normalized) return "unknown";
  if (/法$/u.test(normalized)) return "factor";
  if (/月$/u.test(normalized)) return "months";
  if (/日$/u.test(normalized)) return "days";
  if (/岁$/u.test(normalized)) return "years";
  if (/馀$/u.test(normalized)) return "remainder";
  if (/度$/u.test(normalized)) return "degree";
  if (/次$/u.test(normalized)) return "cycle_output";
  if (/数$/u.test(normalized)) return "count";
  if (/时$/u.test(normalized)) return "seasonal_count";
  return "quantity";
}

export function resolveEnglishTerms(sourceId, name) {
  const normalized = normalizeChineseName(name);
  const scoped = QUANTITY_ENGLISH_MAP[sourceId]?.[normalized] ?? [];
  const global = CULLEN_TERM_ALIASES[normalized] ?? [];
  return unique([...scoped, ...global]);
}

export function enrichQuantity(base, sourceId) {
  if (!base) return null;
  const normalizedName = normalizeChineseName(base.normalized_name ?? base.name_zh);
  return {
    ...base,
    source_id: base.source_id ?? sourceId ?? null,
    name_zh: base.name_zh ?? normalizedName,
    term: base.term ?? base.name_zh ?? normalizedName,
    normalized_name: normalizedName,
    normalized_term: normalizedName,
    quantity_role: base.quantity_role ?? inferQuantityRole(normalizedName),
    english_terms: unique([
      ...(base.english_terms ?? []),
      ...resolveEnglishTerms(sourceId ?? base.source_id, normalizedName),
    ]),
  };
}

export function extractConstantsFromSpans(spans) {
  const constants = [];
  const seen = new Set();

  for (const span of spans) {
    if (span.kind !== "constant_or_rate") continue;
    const sentence = span.text.replace(/[。]$/u, "");
    const match = sentence.match(/^([^，,。；;：:\d零〇一二三四五六七八九十百千万萬亿億]+?)([零〇一二三四五六七八九十百千万萬亿億两兩\d]+)(?:[。；;，,]|$)/u);
    if (!match) continue;
    const rawName = normalizeChineseName(match[1]);
    const value = chineseNumeralToNumber(match[2]);
    if (!rawName || value === null) continue;
    const key = `${span.source_id}:${rawName}`;
    if (seen.has(key)) continue;
    seen.add(key);
    constants.push(enrichQuantity({
      source_id: span.source_id,
      name_zh: rawName,
      normalized_name: rawName,
      value,
      quantity_value_source: "explicit_numeric_text",
      confidence: "A_textual_explicit",
      source_span_id: span.id,
    }, span.source_id));
  }

  return constants;
}

export function buildConstantIndex(constants) {
  const bySource = new Map();
  for (const constant of constants) {
    if (!bySource.has(constant.source_id)) {
      bySource.set(constant.source_id, {
        exact: new Map(),
        items: [],
      });
    }
    const bucket = bySource.get(constant.source_id);
    bucket.exact.set(constant.normalized_name, constant);
    bucket.items.push(constant);
  }
  return bySource;
}

function sourceSpanLineNumber(sourceSpanId) {
  const match = String(sourceSpanId ?? "").match(/:L(\d+)$/u);
  return match ? Number(match[1]) : null;
}

function overlapCount(left, right) {
  const leftSet = new Set(left ?? []);
  const rightSet = new Set(right ?? []);
  let count = 0;
  for (const value of leftSet) {
    if (rightSet.has(value)) count += 1;
  }
  return count;
}

function bestConstantCandidate(normalized, sourceId, constantIndex, sourceSpanId = null) {
  const bucket = constantIndex.get(sourceId);
  if (!bucket) return null;

  const direct = bucket.exact.get(normalized);
  if (direct) {
    return {
      constant: direct,
      score: 100,
      match_type: "exact_constant_match",
    };
  }

  const requestedEnglishTerms = resolveEnglishTerms(sourceId, normalized);
  const targetLine = sourceSpanLineNumber(sourceSpanId);
  let best = null;

  for (const candidate of bucket.items) {
    let score = 0;
    let matchType = null;

    if (candidate.normalized_name.endsWith(normalized) || normalized.endsWith(candidate.normalized_name)) {
      score += 60;
      matchType = "name_suffix_match";
    }

    const englishOverlap = overlapCount(requestedEnglishTerms, candidate.english_terms ?? []);
    if (englishOverlap > 0) {
      score += englishOverlap * 20;
      matchType = matchType ?? "english_term_match";
    }

    if (score <= 0) continue;

    const candidateLine = sourceSpanLineNumber(candidate.source_span_id);
    if (targetLine !== null && candidateLine !== null) {
      const distance = Math.abs(candidateLine - targetLine);
      score -= Math.min(distance, 40);
      if (distance === 0) {
        score += 10;
      } else if (distance <= 3) {
        score += 6;
      } else if (distance <= 8) {
        score += 3;
      }
    }

    if (!best || score > best.score) {
      best = {
        constant: candidate,
        score,
        match_type: matchType ?? "nearby_constant_match",
      };
    }
  }

  return best?.score > 0 ? best : null;
}

export function resolveQuantityReference(rawName, sourceId, constantIndex, sourceSpanId = null) {
  if (!rawName) return null;
  const normalized = normalizeChineseName(rawName);
  if (!normalized) return null;
  const matched = bestConstantCandidate(normalized, sourceId, constantIndex, sourceSpanId);
  if (matched?.constant) {
    const explicit = matched.constant;
    return enrichQuantity({
      ...explicit,
      name_zh: normalized,
      term: normalized,
      normalized_name: normalized,
      normalized_term: normalized,
      quantity_value_source: matched.match_type === "exact_constant_match"
        ? explicit.quantity_value_source
        : "same_source_or_nearby_constant_backfill",
      confidence: matched.match_type === "exact_constant_match"
        ? explicit.confidence
        : "A_textual_backfill",
      matched_constant_name: explicit.normalized_name,
      matched_constant_source_span_id: explicit.source_span_id,
    }, sourceId);
  }

  const lexical = lexicalCountCandidate(normalized, sourceId);
  if (lexical) return enrichQuantity({ ...lexical, source_span_id: sourceSpanId }, sourceId);

  return enrichQuantity({
    source_id: sourceId,
    name_zh: normalized,
    normalized_name: normalized,
    value: null,
    quantity_value_source: "unresolved_reference",
    confidence: "needs_review",
    source_span_id: sourceSpanId,
  }, sourceId);
}

export function parseExplicitNumber(raw, sourceId = null) {
  if (raw === null || raw === undefined) return null;
  const normalized = String(raw).replace(/[,\s]/gu, "");
  const value = /^\d+$/u.test(normalized) ? Number(normalized) : chineseNumeralToNumber(normalized);
  if (value === null) return null;
  return {
    source_id: sourceId,
    name_zh: normalized,
    normalized_name: normalized,
    value,
    quantity_role: "number",
    quantity_value_source: "explicit_numeric_text",
    confidence: "A_textual_explicit",
    source_span_id: null,
    english_terms: [],
  };
}

export function quantitySignature(quantity) {
  if (!quantity) return null;
  return {
    normalized_name: quantity.normalized_name ?? normalizeChineseName(quantity.name_zh),
    value: quantity.value ?? null,
    english_terms: unique(quantity.english_terms ?? []),
    quantity_role: quantity.quantity_role ?? inferQuantityRole(quantity.name_zh),
    quantity_value_source: quantity.quantity_value_source ?? "unknown",
  };
}

export function buildOperationSignature(step) {
  const inputs = (step.inputs ?? []).map(quantitySignature).filter(Boolean);
  const output = quantitySignature(step.output);
  const divisor = quantitySignature(step.divisor);
  const quotient = quantitySignature(step.quotient);
  const remainder = quantitySignature(step.remainder);
  return {
    operation_type: step.operation_type,
    system: step.source_id,
    inputs,
    output,
    divisor,
    quotient,
    remainder,
    modulus: step.modulus ?? divisor?.value ?? null,
  };
}

export function operationSignatureString(step) {
  const signature = buildOperationSignature(step);
  const left = (signature.inputs ?? [])
    .map((item) => {
      const label = item?.normalized_name ?? "?";
      return item?.value !== null && item?.value !== undefined ? `${label}=${item.value}` : label;
    })
    .join(", ");

  const output = signature.output
    ? (signature.output.value !== null && signature.output.value !== undefined
      ? `${signature.output.normalized_name}=${signature.output.value}`
      : signature.output.normalized_name)
    : "null";

  if (signature.operation_type === "quotient_remainder") {
    const divisor = signature.divisor
      ? (signature.divisor.value !== null && signature.divisor.value !== undefined
        ? `${signature.divisor.normalized_name}=${signature.divisor.value}`
        : signature.divisor.normalized_name)
      : "null";
    const quotient = signature.quotient
      ? (signature.quotient.value !== null && signature.quotient.value !== undefined
        ? `${signature.quotient.normalized_name}=${signature.quotient.value}`
        : signature.quotient.normalized_name)
      : "null";
    const remainder = signature.remainder
      ? (signature.remainder.value !== null && signature.remainder.value !== undefined
        ? `${signature.remainder.normalized_name}=${signature.remainder.value}`
        : signature.remainder.normalized_name)
      : "null";
    return `quotient_remainder(${left}; divisor=${divisor})->quotient=${quotient}; remainder=${remainder}`;
  }

  if (signature.operation_type === "mod_cycle") {
    return `mod_cycle(${left}; modulus=${signature.modulus ?? "?"})->${output}`;
  }

  return `${signature.operation_type}(${left})->${output}`;
}

export function stepUsesLexicalCount(step) {
  const quantities = [
    ...(step.inputs ?? []),
    step.output,
    step.divisor,
    step.quotient,
    step.remainder,
  ].filter(Boolean);
  return quantities.some((item) => item.quantity_value_source === "lexical_count");
}

export function isResolvedQuantity(quantity) {
  if (!quantity) return false;
  return quantity.quantity_value_source !== "unresolved_reference"
    && (quantity.value !== null || Boolean(quantity.quantity_role));
}

export function criticalStepQuantities(step) {
  const critical = [...(step.inputs ?? [])];
  if (step.output) critical.push(step.output);
  if (["quotient_remainder", "mod_cycle"].includes(step.operation_type) && step.divisor) {
    critical.push(step.divisor);
  }
  return critical.filter(Boolean);
}

export function stepHasUnresolvedCriticalQuantities(step) {
  return criticalStepQuantities(step).some((item) => item.quantity_value_source === "unresolved_reference");
}

export function stepHasLexicalCriticalQuantities(step) {
  return criticalStepQuantities(step).some((item) => item.quantity_value_source === "lexical_count");
}

export function stepCriticalQuantitiesResolved(step) {
  const critical = criticalStepQuantities(step);
  return critical.length > 0 && critical.every(isResolvedQuantity);
}

export function evaluateGroundingStatus(step, alignment, arithmeticStatus) {
  const arithmeticPass = arithmeticStatus === "pass";
  const directSupport = alignment?.alignment_status === "direct_support";
  const partialSupport = alignment?.alignment_status === "partial_support";
  const keyQuantitiesResolved = stepCriticalQuantitiesResolved(step);
  const criticalLexical = stepHasLexicalCriticalQuantities(step);
  const unresolvedCritical = stepHasUnresolvedCriticalQuantities(step);

  if (
    directSupport
    && arithmeticPass
    && keyQuantitiesResolved
    && !criticalLexical
    && !unresolvedCritical
  ) {
    return "A_confirmed";
  }

  if (unresolvedCritical) return "needs_review";
  if (criticalLexical && directSupport) return "B_supported_with_semantic_count";
  if (partialSupport) return "B_textual_partial";
  if (directSupport) return "B_textual_internal";
  if (criticalLexical) return "needs_review";
  return "B_textual_internal";
}

export function termMatchScore(chineseQuantity, englishClaimQuantity) {
  if (!chineseQuantity || !englishClaimQuantity) return 0;
  const leftTerms = new Set(chineseQuantity.english_terms ?? []);
  const rightTerms = new Set(englishClaimQuantity.english_terms ?? []);
  let score = 0;
  for (const term of leftTerms) {
    if (rightTerms.has(term)) score += 2;
  }
  if (
    chineseQuantity.value !== null
    && englishClaimQuantity.value !== null
    && chineseQuantity.value === englishClaimQuantity.value
  ) {
    score += 2;
  }
  return score;
}

export function buildClaimQuantity(term, value, system) {
  return {
    english_term: normalizeWhitespace(term),
    english_terms: [normalizeWhitespace(term)],
    value: value ?? null,
    system,
  };
}

export function operationTypeAliases(type) {
  return OPERATION_TERM_MAP[type] ?? [type];
}

export function buildClaimValues(claim) {
  const values = [
    ...(claim.inputs ?? []).map((item) => item.value).filter((value) => value !== null),
    claim.output?.value ?? null,
    claim.divisor?.value ?? null,
    claim.modulus ?? null,
  ].filter((value) => value !== null);
  return unique(values);
}

export function extractBracketValuePairs(text) {
  return [...text.matchAll(/([A-Z][A-Za-z \[\]'/()-]{2,80}?)\s*\[(\d[\d,]*)\]/gu)]
    .map((match) => ({
      term: normalizeWhitespace(match[1]),
      value: Number(match[2].replace(/,/gu, "")),
    }));
}

export function findEnglishTerms(text) {
  return unique(
    extractBracketValuePairs(text).map((item) => item.term)
  );
}

export function collectNumericValues(text) {
  return unique([
    ...extractAsciiNumberValues(text),
    ...[...text.matchAll(/\b(\d[\d,]*)\b/gu)].map((match) => Number(match[1].replace(/,/gu, ""))),
  ]);
}
