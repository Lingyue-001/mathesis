import {
  inferCullenSystem,
  readJson,
  readPipelineConfig,
  splitIntoSentences,
  unique,
  writeJson,
} from "./cullen-oracle-common.mjs";
import {
  buildClaimQuantity,
  buildClaimValues,
  collectNumericValues,
  extractBracketValuePairs,
  findEnglishTerms,
  operationTypeAliases,
} from "./procedure-ir-common.mjs";

const TERM_NORMALIZERS = [
  [/Compat\s+ibility/giu, "Compatibility"],
  [/Obscura\s+tion/giu, "Obscuration"],
  [/0bscuration/gu, "Obscuration"],
  [/Cotmt/gu, "Count"],
  [/\[Qt\]/gu, "[Qi]"],
  [/Acc(?:mn|m|cl+u?t+i?u?)lated/giu, "Accumulated"],
  [/conjtmction/giu, "conjunction"],
  [/AcclUTiulated/gu, "Accumulated"],
  [/AcclllTiulated/gu, "Accumulated"],
];

const CONSTANT_VERB_RE = /\b(Multiply|Add|Subtract|Cast|Predict|Set|Seek|Count|Obtain|Call|Join|Start|Remove|First|With|Diminish)\b/i;

const CANONICAL_TERM_MAP = new Map([
  ["the day factor", "Day Factor"],
  ["obscuration days", "Obscuration Days"],
  ["obscuration months", "Obscuration Months"],
  ["obscuration factor", "Obscuration Factor"],
  ["greater remainder", "Greater Remainder"],
  ["lesser remainder", "Lesser Remainder"],
  ["day remainder", "Day Remainder"],
  ["medial [qi] factor", "Medial [Qi] Factor"],
  ["rule factor", "Rule Factor"],
  ["rule months", "Rule Months"],
  ["rule intercalations", "Rule Intercalation Number"],
  ["rule intercalation number", "Rule Intercalation Number"],
  ["intercalation remainder", "Intercalation Remainder"],
  ["years entered into the obscuration", "Years Entered into the Obscuration"],
  ["year of entry into obscuration coincidence", "Year of Entry into Obscuration Coincidence"],
  ["greater circuits", "Greater Circuits"],
  ["circuits of heaven", "Circuits of Heaven"],
  ["compatibility factor", "Compatibility Factor"],
  ["extinction number", "Extinction Number"],
  ["extinction factor", "Extinction Factor"],
  ["extinction remainder", "Extinction Remainder"],
  ["accumulated extinctions", "Accumulated Extinctions"],
  ["eclipse number", "Eclipse Number"],
  ["year number", "Year Number"],
  ["accumulated eclipses", "Accumulated Eclipses"],
  ["eclipse remainder", "Eclipse Remainder"],
  ["cycle rate", "Cycle Rate"],
  ["solar rate", "Solar Rate"],
  ["lunation factor", "Lunation Factor"],
  ["lunation remainder", "Lunation Remainder"],
  ["conjunction accumulated lunations", "Conjunction Accumulated Lunations"],
  ["void parts", "Void Parts"],
  ["days of entry into month", "Days of Entry into Month"],
  ["day and du factor", "Day and Du Factor"],
  ["accumulated du", "Accumulated Du"],
  ["lunar circuits", "Lunar Circuits"],
  ["night clepsydra", "night clepsydra"],
  ["lodge", "Lodge"],
  ["du and parts", "du and parts"],
]);

const ENGLISH_TO_CHINESE = new Map([
  ["Obscuration Months", ["蔀月"]],
  ["Obscuration Days", ["蔀日"]],
  ["Obscuration Factor", ["蔀法"]],
  ["Day Factor", ["日法"]],
  ["Rule Factor", ["章法"]],
  ["Rule Months", ["章月"]],
  ["Intercalation Remainder", ["閏餘"]],
  ["Rule Intercalation Number", ["章閏數"]],
  ["Accumulated Months", ["積月", "入蔀積月"]],
  ["Accumulated Days", ["積日"]],
  ["Lesser Remainder", ["小餘"]],
  ["Greater Remainder", ["大餘"]],
  ["Medial [Qi] Factor", ["中法"]],
  ["Years Entered into the Obscuration", ["入蔀年"]],
  ["Extinction Number", ["沒數"]],
  ["Accumulated Extinctions", ["積沒"]],
  ["Extinction Remainder", ["沒餘"]],
  ["Compatibility Factor", ["通法"]],
  ["Extinction Factor", ["沒法"]],
  ["Year Number", ["歲數"]],
  ["Eclipse Number", ["食數"]],
  ["Accumulated Eclipses", ["積食"]],
  ["Eclipse Remainder", ["食餘"]],
  ["Conjunction Accumulated Lunations", ["合積月"]],
  ["Lunation Remainder", ["月餘"]],
  ["Lunation Factor", ["月法"]],
  ["Void Parts", ["虛分"]],
  ["Days of Entry into Month", ["入月日"]],
  ["Day Remainder", ["日餘"]],
  ["Day and Du Factor", ["日度法"]],
  ["Accumulated Du", ["積度"]],
  ["Lunar Circuits", ["月周"]],
  ["night clepsydra", ["夜漏"]],
  ["Lodge", ["宿次"]],
  ["du and parts", ["度分"]],
]);

function normalizeClaimSentence(sentence) {
  let normalized = String(sentence ?? "").replace(/\s+/gu, " ").trim();
  for (const [pattern, replacement] of TERM_NORMALIZERS) {
    normalized = normalized.replace(pattern, replacement);
  }
  return normalized;
}

function canonicalizeEnglishTerm(term) {
  const normalized = normalizeClaimSentence(term)
    .replace(/^the\s+/iu, "")
    .replace(/\s+/gu, " ")
    .trim();
  return CANONICAL_TERM_MAP.get(normalized.toLowerCase()) ?? normalized;
}

function makeQuantity(term, value, system) {
  return buildClaimQuantity(canonicalizeEnglishTerm(term), value, system);
}

function annotateClaimTerms(claim) {
  const englishTerms = new Set((claim.english_terms ?? []).map((term) => canonicalizeEnglishTerm(term)));
  for (const item of claim.inputs ?? []) englishTerms.add(canonicalizeEnglishTerm(item.english_term));
  if (claim.output?.english_term) englishTerms.add(canonicalizeEnglishTerm(claim.output.english_term));
  if (claim.divisor?.english_term) englishTerms.add(canonicalizeEnglishTerm(claim.divisor.english_term));
  if (claim.quotient?.english_term) englishTerms.add(canonicalizeEnglishTerm(claim.quotient.english_term));
  if (claim.remainder?.english_term) englishTerms.add(canonicalizeEnglishTerm(claim.remainder.english_term));

  const chineseTerms = new Set(claim.chinese_terms ?? []);
  for (const term of englishTerms) {
    const mapped = ENGLISH_TO_CHINESE.get(term) ?? [];
    for (const item of mapped) chineseTerms.add(item);
  }

  claim.english_terms = [...englishTerms];
  claim.chinese_terms = [...chineseTerms];
  return claim;
}

function makeClaimBase(id, chunk, sentence, sentenceIndex, system, claimType, operationType) {
  return {
    id: `cullen:claim:${id}`,
    claim_id: `cullen:claim:${id}`,
    claim_type: claimType,
    system,
    chinese_terms: [],
    english_terms: [],
    operation_type: operationType,
    inputs: [],
    output: null,
    divisor: null,
    quotient: null,
    remainder: null,
    values: [],
    formula_text: sentence,
    procedure_name: chunk.heading ?? null,
    sentence,
    sentence_index: sentenceIndex,
    evidence_chunk_id: chunk.id,
    page_start: chunk.page_start,
    page_end: chunk.page_end,
    evidence_chunk: {
      chunk_id: chunk.id,
      page_start: chunk.page_start,
      page_end: chunk.page_end,
      heading: chunk.heading,
    },
    confidence: "B_structured_heuristic",
    claim_confidence: "B",
  };
}

function parseConstantSentence(sentence, chunk, sentenceIndex, claimId) {
  const normalized = normalizeClaimSentence(sentence);
  const match = normalized.match(/^(?:[^A-Z]*?)?(?:§\d+\s+)?([A-Z][A-Za-z \[\]'/()-]{2,80}?)\s+(\d[\d,]*)\.$/u);
  if (!match || CONSTANT_VERB_RE.test(match[1])) return null;
  if (/\b(?:of|the|is|at|from|scale of)\s*$/iu.test(match[1])) return null;
  const system = inferCullenSystem(chunk.text) ?? inferCullenSystem(sentence);
  const claim = makeClaimBase(claimId, chunk, sentence, sentenceIndex, system, "constant_definition", "set");
  claim.output = makeQuantity(match[1], Number(match[2].replace(/,/gu, "")), system);
  claim.english_terms = [claim.output.english_term];
  claim.values = [claim.output.value];
  claim.confidence = "A_structured_constant";
  claim.claim_confidence = "A";
  return annotateClaimTerms(claim);
}

function parseBinaryOperation(sentence, chunk, sentenceIndex, claimId) {
  const normalized = normalizeClaimSentence(sentence);
  const match = normalized.match(/(Multiplying|Adding)\s+the?\s*([A-Z][A-Za-z \[\]'/()-]{2,80}?)\s*\[(\d[\d,]*)\]\s+(?:by|to)\s+([A-Z][A-Za-z \[\]'/()-]{2,80}?)\s*\[(\d[\d,]*)\],\s*one obtains\s+(?:the\s+)?([A-Z][A-Za-z \[\]'/()-]{2,80}?)(?:\.|,|$)/iu);
  if (!match) return null;
  const operationType = match[1].toLowerCase().startsWith("add") ? "add" : "multiply";
  const system = inferCullenSystem(chunk.text) ?? inferCullenSystem(sentence);
  const claim = makeClaimBase(claimId, chunk, sentence, sentenceIndex, system, "derived_constant", operationType);
  claim.inputs = [
    makeQuantity(match[2], Number(match[3].replace(/,/gu, "")), system),
    makeQuantity(match[4], Number(match[5].replace(/,/gu, "")), system),
  ];
  claim.output = makeQuantity(match[6], null, system);
  claim.english_terms = unique([...claim.inputs.map((item) => item.english_term), claim.output.english_term]);
  claim.values = buildClaimValues(claim);
  claim.confidence = claim.values.length >= 2 ? "A_structured_formula" : "B_structured_heuristic";
  claim.claim_confidence = claim.values.length >= 2 ? "A" : "B";
  return annotateClaimTerms(claim);
}

function parseUnaryMultiplier(sentence, chunk, sentenceIndex, claimId) {
  const normalized = normalizeClaimSentence(sentence);
  const match = normalized.match(/(Trebling|Doubling|Quartering)\s+the?\s*([A-Z][A-Za-z \[\]'/()-]{2,80}?)\s*\[(\d[\d,]*)\],\s*one obtains\s+(?:the\s+)?([A-Z][A-Za-z \[\]'/()-]{2,80}?)(?:\.|,|$)/iu);
  if (!match) return null;
  const scalarMap = { Trebling: 3, Doubling: 2, Quartering: 4 };
  const scalar = scalarMap[match[1][0].toUpperCase() + match[1].slice(1).toLowerCase()] ?? null;
  const system = inferCullenSystem(chunk.text) ?? inferCullenSystem(sentence);
  const claim = makeClaimBase(claimId, chunk, sentence, sentenceIndex, system, "formula", "multiply");
  claim.inputs = [
    makeQuantity(match[2], Number(match[3].replace(/,/gu, "")), system),
    makeQuantity(`${match[1].replace(/ing$/u, "")} Scalar`, scalar, system),
  ];
  claim.output = makeQuantity(match[4], null, system);
  claim.english_terms = unique([claim.inputs[0].english_term, claim.output.english_term]);
  claim.values = buildClaimValues(claim);
  claim.confidence = "A_structured_formula";
  claim.claim_confidence = "A";
  return annotateClaimTerms(claim);
}

function parseStructuredWindow(sentences, index, chunk, claimId) {
  const window = [sentences[index - 1], sentences[index], sentences[index + 1], sentences[index + 2], sentences[index + 3]]
    .filter(Boolean)
    .map((sentence) => normalizeClaimSentence(sentence))
    .join(" ");
  const system = inferCullenSystem(chunk.text) ?? inferCullenSystem(window);

  const fillPatternA = /(?:Set out(?: the)?\s+([A-Z][A-Za-z \[\]'/()-]{2,80}?)(?:\s+of entry into the Obscuration|\s+into the Obscuration)?(?: and subtract one)?\.\s+)?Multiply(?:\s+(?:it|them|the remainder|Accumulated Months|Accumulated Extinctions))?\s*(?:by\s+)?([A-Z][A-Za-z \[\]'/()-]{2,80}?)\s*\[(\d[\d,]*)\](?:,?\s*and)?\s*(?:obtain|Count)\s+one\s+for each(?:\s+(?:time\s+)?)?(?:(?:completed|full)\s+)?(?:filling of(?: the)?\s+)([A-Z][A-Za-z \[\]'/()-]{2,80}?)\s*\[(\d[\d,]*)\]\.?\s*(?:This is called|Call(?:ed)?(?: this| that)?|Called this|Call that)\s+(?:the\s+)?([A-Z][A-Za-z \[\]'/()-]{2,80}?)\.?\s*(?:The remainder is|What is not exhausted is|What does not fill(?: \[[^\]]+\])? is)\s+(?:the\s+)?([A-Z][A-Za-z \[\]'/()-]{2,80}?)(?:\.|,|$)/iu;
  const fillPatternB = /(?:Set out(?: the)?\s+([A-Z][A-Za-z \[\]'/()-]{2,80}?)(?:\s+of entry into the Obscuration|\s+into the Obscuration)?(?: and subtract one)?\.\s+)?Multiply(?:\s+(?:it|them|the remainder|Accumulated Months|Accumulated Extinctions))?\s*(?:by\s+)?([A-Z][A-Za-z \[\]'/()-]{2,80}?)\s*\[(\d[\d,]*)\](?:,?\s*and)?\s*(?:obtain|Count)\s+one\s+for each(?:\s+(?:time\s+)?)?(?:([A-Z][A-Za-z \[\]'/()-]{2,80}?)\s*\[(\d[\d,]*)\]\s+filled)\.?\s*(?:This is called|Call(?:ed)?(?: this| that)?|Called this|Call that)\s+(?:the\s+)?([A-Z][A-Za-z \[\]'/()-]{2,80}?)\.?\s*(?:The remainder is|What is not exhausted is|What does not fill(?: \[[^\]]+\])? is)\s+(?:the\s+)?([A-Z][A-Za-z \[\]'/()-]{2,80}?)(?:\.|,|$)/iu;
  const filledStep = window.match(fillPatternA) ?? window.match(fillPatternB);
  if (filledStep) {
    const claim = makeClaimBase(claimId, chunk, window, index, system, "procedure_step", "quotient_remainder");
    if (filledStep[1]) claim.inputs.push(makeQuantity(filledStep[1], null, system));
    claim.inputs.push(makeQuantity(filledStep[2], Number(filledStep[3].replace(/,/gu, "")), system));
    const divisorTerm = filledStep[4];
    const divisorValue = filledStep[5];
    claim.divisor = makeQuantity(divisorTerm, Number(divisorValue.replace(/,/gu, "")), system);
    claim.quotient = makeQuantity(filledStep[6], null, system);
    claim.output = claim.quotient;
    claim.remainder = makeQuantity(filledStep[7], null, system);
    claim.english_terms = unique([
      ...claim.inputs.map((item) => item.english_term),
      claim.divisor.english_term,
      claim.output.english_term,
      claim.remainder.english_term,
    ]);
    claim.values = buildClaimValues(claim);
    claim.confidence = "A_structured_procedure";
    claim.claim_confidence = "A";
    return annotateClaimTerms(claim);
  }

  const accumulatedParts = window.match(/set out the number for the\s+([A-Z][A-Za-z \[\]'/()-]{2,80}?)\s*,?\s+and multiply by\s+([A-Z][A-Za-z \[\]'/()-]{2,80}?)\s*\[(\d[\d,]*)\],\s+then cast out\s+(\d+),\s+making(?: \[the number obtained\])?\s+([A-Z][A-Za-z \[\]'/()-]{2,80}?)\.\s+Obtain 1 for each time\s+([A-Z][A-Za-z \[\]'/()-]{2,80}?)\s+fills\s+([A-Z][A-Za-z \[\]'/()-]{2,80}?)\s*\[(\d[\d,]*)\],\s+and by that increase the midnight du,\s+then that is the\s+([A-Z][A-Za-z \[\]'/()-]{2,120}?)(?:\.|,|$)/iu);
  if (accumulatedParts) {
    const claim = makeClaimBase(claimId, chunk, window, index, system, "procedure_step", "quotient_remainder");
    claim.inputs = [
      makeQuantity(accumulatedParts[1], null, system),
      makeQuantity(accumulatedParts[2], Number(accumulatedParts[3].replace(/,/gu, "")), system),
      makeQuantity(accumulatedParts[5], null, system),
    ];
    claim.modulus = Number(accumulatedParts[4]);
    claim.divisor = makeQuantity(accumulatedParts[7], Number(accumulatedParts[8].replace(/,/gu, "")), system);
    claim.quotient = makeQuantity(accumulatedParts[9], null, system);
    claim.output = claim.quotient;
    claim.english_terms = unique([
      ...claim.inputs.map((item) => item.english_term),
      claim.divisor.english_term,
      claim.output.english_term,
    ]);
    claim.values = buildClaimValues(claim);
    claim.confidence = "A_structured_procedure";
    claim.claim_confidence = "A";
    return annotateClaimTerms(claim);
  }

  const duskAndCrescent = window.match(/(?:By the parts moved by the sun from midnight to dawn, subtract from\s+([A-Z][A-Za-z \[\]'/()-]{2,80}?)\s*\[(\d[\d,]*)\],\s+and the remainder is the\s+([A-Z][A-Za-z \[\]'/()-]{2,80}?)\.\s+If you add this to the\s+([A-Z][A-Za-z \[\]'/()-]{2,120}?),\s+this is the\s+([A-Z][A-Za-z \[\]'/()-]{2,120}?))|(?:Set out the number of the\s+([A-Z][A-Za-z \[\]'/()-]{2,120}?)\s+at conjunction,\s+and add\s+(\d+)\s+du.*?Cast out the Lodges in succession,\s+and that is the\s+([A-Z][A-Za-z \[\]'/()-]{2,120}?))(?:\.|,|$)/iu);
  if (duskAndCrescent) {
    const claim = makeClaimBase(claimId, chunk, window, index, system, "procedure_step", "add");
    if (duskAndCrescent[1]) {
      claim.inputs = [
        makeQuantity(duskAndCrescent[1], Number(duskAndCrescent[2].replace(/,/gu, "")), system),
        makeQuantity(duskAndCrescent[3], null, system),
        makeQuantity(duskAndCrescent[4], null, system),
      ];
      claim.output = makeQuantity(duskAndCrescent[5], null, system);
    } else {
      claim.inputs = [
        makeQuantity(duskAndCrescent[6], null, system),
        makeQuantity("du and parts increment", Number(duskAndCrescent[7]), system),
      ];
      claim.output = makeQuantity(duskAndCrescent[8], null, system);
    }
    claim.english_terms = unique([...claim.inputs.map((item) => item.english_term), claim.output.english_term]);
    claim.values = buildClaimValues(claim);
    claim.confidence = "A_structured_procedure";
    claim.claim_confidence = "A";
    return annotateClaimTerms(claim);
  }

  const castOut = window.match(/Cast out\s+(\d+)\s+from the\s+([A-Z][A-Za-z \[\]'/()-]{2,80}?)\.\s+The remainder is the\s+([A-Z][A-Za-z \[\]'/()-]{2,80}?)(?:\.|,|$)/iu);
  if (castOut) {
    const claim = makeClaimBase(claimId, chunk, window, index, system, "procedure_step", "mod_cycle");
    claim.inputs = [makeQuantity(castOut[2], null, system)];
    claim.modulus = Number(castOut[1]);
    claim.remainder = makeQuantity(castOut[3], null, system);
    claim.output = claim.remainder;
    claim.english_terms = unique([claim.inputs[0].english_term, claim.remainder.english_term]);
    claim.values = buildClaimValues(claim);
    claim.confidence = "A_structured_procedure";
    claim.claim_confidence = "A";
    return annotateClaimTerms(claim);
  }

  const directFormula = window.match(/(?:By multiplying|Multiply)\s+(?:the\s+)?([A-Z][A-Za-z \[\]'/()-]{2,80}?)\s+by\s+(?:the\s+)?([A-Z][A-Za-z \[\]'/()-]{2,80}?)\s*\[(\d[\d,]*)\]\s+(?:one makes|to make)\s+(?:the\s+)?([A-Z][A-Za-z \[\]'/()-]{2,80}?)(?:\.|,|$)/iu)
    ?? window.match(/By the\s+([A-Z][A-Za-z \[\]'/()-]{2,80}?)\s*\[(\d[\d,]*)\]\s+Multiply\s+(?:the\s+)?([A-Z][A-Za-z \[\]'/()-]{2,80}?)\s+to make\s+(?:the\s+)?([A-Z][A-Za-z \[\]'/()-]{2,80}?)(?:\.|,|$)/iu);
  if (directFormula) {
    const claim = makeClaimBase(claimId, chunk, window, index, system, "formula", "multiply");
    if (window.includes("By the")) {
      claim.inputs = [
        makeQuantity(directFormula[3], null, system),
        makeQuantity(directFormula[1], Number(directFormula[2].replace(/,/gu, "")), system),
      ];
      claim.output = makeQuantity(directFormula[4], null, system);
    } else {
      claim.inputs = [
        makeQuantity(directFormula[1], null, system),
        makeQuantity(directFormula[2], Number(directFormula[3].replace(/,/gu, "")), system),
      ];
      claim.output = makeQuantity(directFormula[4], null, system);
    }
    claim.english_terms = unique([...claim.inputs.map((item) => item.english_term), claim.output.english_term]);
    claim.values = buildClaimValues(claim);
    claim.confidence = "A_structured_formula";
    claim.claim_confidence = "A";
    return annotateClaimTerms(claim);
  }

  const intercalation = window.match(/Subtract the\s+([A-Z][A-Za-z \[\]'/()-]{2,80}?)\s+from\s+([A-Z][A-Za-z \[\]'/()-]{2,80}?)\s*\[(\d[\d,]*)\]\.\s+Multiply the remainder by\s+(\d+)\.\s+Count one for each completed\s+([A-Z][A-Za-z \[\]'/()-]{2,80}?)\s*\[(\d[\d,]*)\](?:; for a completed\s+(\d+)\s+also get one count)?/iu);
  if (intercalation) {
    const claim = makeClaimBase(claimId, chunk, window, index, system, "procedure_step", "quotient_remainder");
    claim.inputs = [
      makeQuantity(intercalation[2], Number(intercalation[3].replace(/,/gu, "")), system),
      makeQuantity(intercalation[1], null, system),
      makeQuantity("Scalar 12", Number(intercalation[4]), system),
    ];
    claim.divisor = makeQuantity(intercalation[5], Number(intercalation[6].replace(/,/gu, "")), system);
    claim.quotient = makeQuantity("Intercalary Month", null, system);
    claim.output = claim.quotient;
    claim.remainder = makeQuantity("Intercalation Remainder", null, system);
    claim.english_terms = unique([
      ...claim.inputs.map((item) => item.english_term),
      claim.divisor.english_term,
      claim.output.english_term,
      claim.remainder.english_term,
    ]);
    claim.values = buildClaimValues(claim);
    claim.confidence = "A_structured_procedure";
    claim.claim_confidence = "A";
    return annotateClaimTerms(claim);
  }

  const addRemainders = window.match(/add(?: to)? the\s+([A-Z][A-Za-z \[\]'/()-]{2,80}?)\s+(\d+),\s+and\s+(?:to the\s+)?([A-Z][A-Za-z \[\]'/()-]{2,80}?)\s+(\d+)/iu);
  if (addRemainders) {
    const claim = makeClaimBase(claimId, chunk, window, index, system, "procedure_step", "add");
    claim.inputs = [
      makeQuantity(addRemainders[1], Number(addRemainders[2]), system),
      makeQuantity(addRemainders[3], Number(addRemainders[4]), system),
    ];
    claim.output = makeQuantity("Greater and Lesser Remainder Update", null, system);
    claim.english_terms = unique(claim.inputs.map((item) => item.english_term));
    claim.values = buildClaimValues(claim);
    claim.confidence = "A_structured_procedure";
    claim.claim_confidence = "A";
    return annotateClaimTerms(claim);
  }

  return null;
}

function parseEnglishClaim(sentence, chunk, sentenceIndex, claimId, windowSentences) {
  return (
    parseConstantSentence(sentence, chunk, sentenceIndex, claimId)
    ?? parseBinaryOperation(sentence, chunk, sentenceIndex, claimId)
    ?? parseUnaryMultiplier(sentence, chunk, sentenceIndex, claimId)
    ?? parseStructuredWindow(windowSentences, sentenceIndex, chunk, claimId)
  );
}

function buildContextualClaim(sentence, chunk, sentenceIndex, claimId) {
  const normalized = normalizeClaimSentence(sentence);
  const englishTerms = findEnglishTerms(normalized).map((term) => canonicalizeEnglishTerm(term));
  const values = collectNumericValues(normalized);
  const operationType = ["multiply", "divide", "add", "subtract", "remainder", "set"]
    .find((type) => operationTypeAliases(type).some((needle) => normalized.toLowerCase().includes(needle)));

  if (!englishTerms.length && !values.length) return null;

  const system = inferCullenSystem(chunk.text) ?? inferCullenSystem(sentence);
  const claimType = englishTerms.length && !operationType ? "term_gloss" : "formula";
  const claim = makeClaimBase(claimId, chunk, sentence, sentenceIndex, system, claimType, operationType ?? null);
  claim.english_terms = englishTerms;
  claim.values = values;
  claim.confidence = "C_contextual";
  claim.claim_confidence = "C";
  return annotateClaimTerms(claim);
}

async function main() {
  const config = await readPipelineConfig();
  const chunkPayload = await readJson(config.inputs.cullen.artifacts.chunks);
  const claims = [];

  for (const chunk of chunkPayload.chunks) {
    if (chunk.page_end <= 20) continue;
    const sentences = splitIntoSentences(chunk.text);
    for (let index = 0; index < sentences.length; index += 1) {
      const sentence = sentences[index];
      const claim =
        parseEnglishClaim(sentence, chunk, index, claims.length + 1, sentences)
        ?? buildContextualClaim(sentence, chunk, index, claims.length + 1);
      if (!claim) continue;
      if (!claim.english_terms.length) {
        claim.english_terms = unique([
          ...extractBracketValuePairs(claim.formula_text).map((item) => canonicalizeEnglishTerm(item.term)),
          ...(claim.output ? [claim.output.english_term] : []),
          ...(claim.inputs ?? []).map((item) => item.english_term),
        ]);
      }
      if (!claim.values.length) {
        claim.values = buildClaimValues(claim);
      }
      annotateClaimTerms(claim);
      claims.push(claim);
    }
  }

  const oracle = {
    generated_at: new Date().toISOString(),
    input: config.inputs.cullen,
    status: "structured_claims_extracted",
    terms: unique(claims.flatMap((claim) => claim.english_terms)).sort(),
    formulae: claims.filter((claim) => claim.claim_type === "formula"),
    procedure_explanations: claims.filter((claim) => claim.claim_type === "procedure_step"),
    worked_examples: claims.filter((claim) => claim.values.length >= 2),
    claims,
  };

  await writeJson(config.inputs.cullen.artifacts.claims, {
    generated_at: oracle.generated_at,
    claim_count: claims.length,
    claims,
  });
  await writeJson(config.outputs.cullen_oracle, oracle);

  console.log(JSON.stringify({
    stage: "extract-cullen-claims",
    claim_count: claims.length,
    output: config.inputs.cullen.artifacts.claims,
  }, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
