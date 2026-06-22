import fs from "node:fs/promises";
import {
  readJson,
  readPipelineConfig,
  unique,
  writeJson,
} from "./cullen-oracle-common.mjs";
import {
  buildProcedureAnchorSet,
  chooseBetterDiagnostic,
  enrichProcedureAnchorSet,
  findAnchorsForSourceSpan,
  writeProcedureAnchorOutputs,
  CULLEN_PROCEDURE_ANCHOR_JSON,
  CULLEN_PROCEDURE_ANCHOR_MD,
} from "./cullen-procedure-anchor-common.mjs";
import {
  buildProcedureInventory,
  writeProcedureInventoryOutputs,
  CULLEN_PROCEDURE_INVENTORY_JSON,
  CULLEN_PROCEDURE_INVENTORY_MD,
} from "./cullen-procedure-inventory-common.mjs";
import {
  QUANTITY_ENGLISH_MAP,
  normalizeChineseName,
} from "./procedure-ir-common.mjs";

const SCOPE_DEFS = {
  santong: {
    system: "santong",
    pageStart: 45,
    pageEnd: 121,
    chapterLabel: "Cullen Santong authority scope",
  },
  sifen: {
    system: "sifen",
    pageStart: 151,
    pageEnd: 205,
    chapterLabel: "Cullen Sifen authority scope",
  },
};

const TERM_VARIANT_GROUPS = [
  ["餘", "馀", "余"],
  ["小餘", "小馀"],
  ["大餘", "大馀"],
  ["積日", "积日"],
  ["沒", "没"],
];

const PROCEDURE_PROFILES = [
  {
    cullen_procedure_id: "cullen:santong:basic-constants",
    system: "santong",
    procedure_title_zh: "基本常数",
    cullen_title_or_section: "Triple Concordance basic constants",
    cues: [
      "Intercalation Factor",
      "Day Factor",
      "Concordance Factor",
      "Origin Factor",
      "Rule Months",
      "Lunation Factor",
      "Compatibility Factor",
      "Circuits of Heaven",
    ],
  },
  {
    cullen_procedure_id: "cullen:santong:accumulated-calendar",
    system: "santong",
    procedure_title_zh: "积月积日小馀大馀",
    cullen_title_or_section: "Triple Concordance accumulated months and days",
    cues: [
      "Accumulated Months",
      "Accumulated Days",
      "Lesser Remainder",
      "Greater Remainder",
      "Rule Head",
      "Concordance Workings",
    ],
  },
  {
    cullen_procedure_id: "cullen:santong:quotient-remainder",
    system: "santong",
    procedure_title_zh: "馀法与商法",
    cullen_title_or_section: "Triple Concordance quotient-remainder explanations",
    cues: [
      "for each filling",
      "what does not fill",
      "Lesser Remainder",
      "Greater Remainder",
      "remainder",
    ],
  },
  {
    cullen_procedure_id: "cullen:sifen:basic-constants",
    system: "sifen",
    procedure_title_zh: "基本太阳月亮常数",
    cullen_title_or_section: "Han Quarter Remainder basic constants",
    cues: [
      "Origin Factor",
      "Obscuration Months",
      "Day Factor",
      "Obscuration Days",
      "Extinction Number",
      "Medial [Qi] Factor",
      "Greater Remainder",
      "Lesser Remainder",
    ],
  },
  {
    cullen_procedure_id: "cullen:sifen:tianzheng-shuori",
    system: "sifen",
    procedure_title_zh: "推天正朔日",
    cullen_title_or_section: "Han Quarter Remainder new moon / Greater-Lesser Remainder procedures",
    cues: [
      "Greater Remainder",
      "Lesser Remainder",
      "Count one for each filling of the Day Factor [4]",
      "Count off the Greater Remainder from the jiazi",
      "Accumulated Days",
    ],
  },
  {
    cullen_procedure_id: "cullen:sifen:mei-mie",
    system: "sifen",
    procedure_title_zh: "推沒滅",
    cullen_title_or_section: "Han Quarter Remainder extinction / obliteration procedures",
    cues: [
      "Extinction Number",
      "Year Extinction",
      "Obliteration",
      "Proc. 3.11",
      "Day Factor [4]",
    ],
  },
  {
    cullen_procedure_id: "cullen:sifen:eclipse-day",
    system: "sifen",
    procedure_title_zh: "推月食日",
    cullen_title_or_section: "Han Quarter Remainder eclipse day procedure",
    cues: [
      "seek the day of the eclipse",
      "Greater Remainder",
      "Lesser Remainder",
      "Obscuration Months [940]",
    ],
  },
];

const GENERIC_ENGLISH_TERMS = new Set([
  "introduction",
  "table",
  "general introduction",
  "general introduction table",
  "the triple concordance system",
  "the han quarter remainder system",
  "han quarter remainder system",
  "triple concordance system",
]);

const DIRECT_CONFIDENCE = new Set([
  "A_structured_constant",
  "A_structured_formula",
  "A_structured_procedure",
]);

const CONTEXTUAL_CONFIDENCE = new Set([
  "B_contextual",
  "C_contextual",
]);

const STRUCTURED_ENGLISH_TERM_RE = /\b(factor|remainder|months|month|days|day|circuits|medial|qi|rule|origin|obscuration|extinction|accumulated|lunation|void parts|entry|du|coincidence)\b/i;
const PROCEDURE_FAMILY_ORDER = [
  "intercalary_month",
  "tianzheng_shuori",
  "eclipse_chain",
  "du_lodge_sun",
  "du_lodge_moon",
  "planet_conjunction",
  "obscuration_entry",
  "mei_mie",
  "general_context",
  "unknown",
];

const SIFEN_TARGET_SPAN_IDS = [
  "sifen:L66",
  "sifen:L74",
  "sifen:L84",
  "sifen:L112",
  "sifen:L118",
  "sifen:L122",
  "sifen:L126",
  "sifen:L152",
  "sifen:L154",
];

const SIFEN_TARGET_FAMILY_CANDIDATE_PATH = "config/sifen-target-family-gold.candidate.json";
const SIFEN_TARGET_FAMILY_REVIEW_PACKET_PATH = "tmp/procedure-ir/sifen-target-family-review-packet.md";
const PRESERVED_HUMAN_FIELDS = [
  "human_review_status",
  "human_expected_family",
  "human_accept_claim_ids",
  "human_reject_claim_ids",
  "human_notes",
];
const NOISY_DISPLAY_LIMIT = 3;
const GENERIC_CHINESE_TERMS = new Set([
  "蔀法",
  "積日",
  "余",
  "餘",
]);
const GENERIC_ENGLISH_TERMS_FOR_MATCH = new Set([
  "obscuration factor",
  "accumulated days",
  "remainder",
  "multiply",
  "divide",
]);
const GENERIC_OPERATION_TYPES = new Set(["multiply", "divide"]);
const DISTINCTIVE_TERM_RULES = [
  {
    key: "入蔀",
    chinese: [/入蔀/u],
    english: [/\bentered obscuration\b/i, /\bentered era\b/i],
  },
  {
    key: "推天正",
    chinese: [/天正/u],
    english: [/\bcelestial standard conjunction\b/i, /\bfirst day of the first month\b/i, /\bcelestial year\b/i],
  },
  {
    key: "閏月所在",
    chinese: [/閏月/u],
    english: [/\bintercalary month\b/i],
  },
  {
    key: "月食",
    chinese: [/月食|食月|食術/u],
    english: [/\blunar eclipse\b/i, /\beclipse\b/i],
  },
  {
    key: "五星",
    chinese: [/五星|星合/u],
    english: [/\bfive planets\b/i, /\bplanet\b/i, /\bconjunction\b/i],
  },
  {
    key: "弦望",
    chinese: [/弦|望/u],
    english: [/\bcrescent\b/i, /\bfull moon\b/i],
  },
  {
    key: "月明",
    chinese: [/月明/u],
    english: [/\bmoon at dawn\b/i, /\bmoon at dusk\b/i, /\bmoon\b/i],
  },
  {
    key: "日明",
    chinese: [/日明/u],
    english: [/\bsun at dawn\b/i, /\bsun at dusk\b/i, /\bsun\b/i],
  },
];

function inScope(system, pageStart, pageEnd) {
  const scope = SCOPE_DEFS[system];
  return scope && pageStart >= scope.pageStart && pageEnd <= scope.pageEnd;
}

function strongestLevel(levels) {
  const order = ["A_direct", "B_contextual", "C_background"];
  return order.find((level) => levels.includes(level)) ?? "C_background";
}

function strongestValue(values, order, fallback = null) {
  return order.find((value) => values.includes(value)) ?? fallback;
}

function strongestFamily(families) {
  return PROCEDURE_FAMILY_ORDER.find((family) => families.includes(family)) ?? "unknown";
}

function uniqueBy(items, keyFn) {
  const seen = new Set();
  const out = [];
  for (const item of items) {
    const key = keyFn(item);
    if (seen.has(key)) continue;
    seen.add(key);
    out.push(item);
  }
  return out;
}

function uniqueStrings(items) {
  return unique(items.filter(Boolean).map((item) => String(item).trim()).filter(Boolean));
}

async function maybeReadJson(relativePath) {
  try {
    return await readJson(relativePath);
  } catch (error) {
    if (error?.code === "ENOENT") return null;
    throw error;
  }
}

function detectClaimType(claim) {
  const text = `${claim.formula_text ?? ""} ${claim.sentence ?? ""}`;
  if (/for example|let us carry out the calculation|thus after|we have:/i.test(text)) {
    return "worked_example";
  }
  if (claim.output?.value !== null && !(claim.inputs?.length)) {
    return "constant_definition";
  }
  if (claim.operation_type && (claim.divisor || claim.remainder || claim.quotient)) {
    return "procedure_step";
  }
  if (claim.operation_type && claim.inputs?.length && claim.output) {
    return claim.output.value !== null ? "derived_constant" : "formula";
  }
  if ((claim.english_terms?.length ?? 0) > 0 && !claim.operation_type) {
    return "term_gloss";
  }
  return "contextual_explanation";
}

function normalizeProcedureLabel(text) {
  return String(text ?? "")
    .replace(/[：:]/gu, "")
    .replace(/術曰|术曰|術|术|曰/gu, "")
    .replace(/\s+/gu, "")
    .trim();
}

function inferSourceProcedureFamily(sourceSpan, currentProcedure = null) {
  const label = normalizeProcedureLabel(currentProcedure?.title_guess ?? sourceSpan.title_guess ?? sourceSpan.source_text ?? sourceSpan.text ?? "");
  const text = `${label} ${sourceSpan.source_text ?? sourceSpan.text ?? ""}`;
  if (/五星|星合月/.test(label)) return "planet_conjunction";
  if (/月食/.test(label)) return "eclipse_chain";
  if (/閏月所在/.test(label)) return "intercalary_month";
  if (/天正朔日|天正朔|天正/.test(label)) return "tianzheng_shuori";
  if (/日明|弦望日|日所入度分|日所入星度/.test(label)) return "du_lodge_sun";
  if (/月明|弦望月|月所入度分|月所入星度/.test(label)) return "du_lodge_moon";
  if (/入蔀|入紀|入元/.test(label)) return "obscuration_entry";
  if (/閏月所在|閏月/.test(text)) return "intercalary_month";
  if (/天正朔日|天正朔|天正/.test(text)) return "tianzheng_shuori";
  if (/月食/.test(text)) return "eclipse_chain";
  if (/日明|日所入度分|日所入星度|弦望日/.test(text)) return "du_lodge_sun";
  if (/月明|月所入度分|月所入星度|弦望月/.test(text)) return "du_lodge_moon";
  if (/五星|星合月|合積|積合|合餘/.test(text)) return "planet_conjunction";
  if (/入蔀|入紀|入元/.test(text)) return "obscuration_entry";
  if (/沒滅|灭|沒/.test(text)) return "mei_mie";
  if (/曆數之生|天之動/.test(text)) return "general_context";
  return "unknown";
}

function inferClaimProcedureFamily(claim) {
  const text = `${claim.formula_text ?? ""} ${claim.evidence_text ?? ""} ${claim.procedure_name ?? ""}`.toLowerCase();
  if (/intercalary month|rule intercalation/i.test(text)) return "intercalary_month";
  if (/celestial standard conjunction|accumulated days|obscuration days|greater remainder|lesser remainder/i.test(text)) return "tianzheng_shuori";
  if (/lunar eclipse|eclipse|eclipse number|accumulated eclipses/i.test(text)) return "eclipse_chain";
  if (/sun at dawn|sun at dusk|sun at crescents and full moon|first crescent|lodge entered by the sun/i.test(text)) return "du_lodge_sun";
  if (/moon at dawn|moon at dusk|du and parts entered by the moon|midnight du of the sun/i.test(text)) return "du_lodge_moon";
  if (/five planets|planetary constants|cycle rate|solar rate|conjunctions between planet and sun|wood star|jupiter|venus|mercury/i.test(text)) return "planet_conjunction";
  if (/entered by the lunar eclipse|year of obscuration coincidence entered|era entered|obscuration entered|high origin/i.test(text)) return "obscuration_entry";
  if (/extinction|obliteration/i.test(text)) return "mei_mie";
  return "unknown";
}

function procedureFamiliesCompatible(sourceFamily, claimFamily) {
  if (!sourceFamily || sourceFamily === "unknown") return true;
  if (!claimFamily || claimFamily === "unknown") return false;
  if (sourceFamily === claimFamily) return true;
  return false;
}

function detectEvidenceLevel(strictType, claim) {
  if (DIRECT_CONFIDENCE.has(claim.confidence)) return "A_direct";
  if (strictType === "term_gloss" || CONTEXTUAL_CONFIDENCE.has(claim.confidence)) return "B_contextual";
  return "C_background";
}

function canSupportAConfirmed(strictType, claim) {
  const directType = ["constant_definition", "derived_constant", "procedure_step", "formula", "worked_example"];
  return DIRECT_CONFIDENCE.has(claim.confidence)
    && directType.includes(strictType)
    && isMeaningfulStructuredClaim(claim);
}

function reverseEnglishMap() {
  const out = new Map();
  for (const [system, mapping] of Object.entries(QUANTITY_ENGLISH_MAP)) {
    for (const [chineseTerm, englishTerms] of Object.entries(mapping)) {
      for (const english of englishTerms) {
        const key = english.toLowerCase();
        if (!out.has(key)) out.set(key, []);
        out.get(key).push({ system, chineseTerm });
      }
    }
  }
  return out;
}

function cleanEnglishTerm(term) {
  return String(term ?? "").trim().replace(/\s+/g, " ");
}

function normalizedEnglishTerm(term) {
  return cleanEnglishTerm(term).toLowerCase();
}

function normalizeChineseTerm(term) {
  return normalizeChineseName(term ?? "");
}

function isStructuredEnglishTerm(term) {
  const normalized = normalizedEnglishTerm(term);
  if (!normalized || isGenericEnglishTerm(normalized)) return false;
  return STRUCTURED_ENGLISH_TERM_RE.test(normalized);
}

function isGenericEnglishTerm(term) {
  const normalized = normalizedEnglishTerm(term);
  if (!normalized) return true;
  if (GENERIC_ENGLISH_TERMS.has(normalized)) return true;
  return /^(chapter|section|table|introduction)\b/i.test(normalized)
    || /\bchapter\b/i.test(normalized)
    || /\bcalendar\b/i.test(normalized)
    || /\bbce\b|\bce\b/i.test(normalized);
}

function claimKnownEnglishTerms(claim) {
  const terms = new Set();
  for (const item of claim.english_terms ?? []) {
    const cleaned = cleanEnglishTerm(item);
    if (isStructuredEnglishTerm(cleaned)) terms.add(cleaned);
  }
  for (const item of claim.inputs ?? []) {
    const cleaned = cleanEnglishTerm(item.english_term);
    if (isStructuredEnglishTerm(cleaned)) terms.add(cleaned);
  }
  for (const item of claim.output?.english_terms ?? []) {
    const cleaned = cleanEnglishTerm(item);
    if (isStructuredEnglishTerm(cleaned)) terms.add(cleaned);
  }
  if (claim.output?.english_term) {
    const cleaned = cleanEnglishTerm(claim.output.english_term);
    if (isStructuredEnglishTerm(cleaned)) terms.add(cleaned);
  }
  return [...terms];
}

function claimKnownChineseTerms(claim, reverseMap) {
  const chineseTerms = new Set((claim.chinese_terms ?? []).map((item) => normalizeChineseName(item)).filter(Boolean));
  for (const english of claimKnownEnglishTerms(claim)) {
    const mapped = reverseMap.get(normalizedEnglishTerm(english)) ?? [];
    for (const item of mapped) {
      if (item.system === claim.system) chineseTerms.add(item.chineseTerm);
    }
  }
  return [...chineseTerms];
}

function hasKnownTermSupport(claim, reverseMap) {
  return claimKnownEnglishTerms(claim).length > 0 || claimKnownChineseTerms(claim, reverseMap).length > 0;
}

function isMeaningfulStructuredClaim(claim) {
  const hasKnownOutput = isStructuredEnglishTerm(claim.output?.english_term)
    || (claim.output?.english_terms ?? []).some((term) => isStructuredEnglishTerm(term));
  const hasKnownInput = (claim.inputs ?? []).some((item) => isStructuredEnglishTerm(item.english_term));
  const hasOperation = Boolean(claim.operation_type && ["set", "multiply", "divide", "remainder", "add", "subtract"].includes(claim.operation_type));
  const hasValue = claim.output?.value !== null
    || (claim.inputs ?? []).some((item) => item.value !== null)
    || (claim.values ?? []).some((value) => Number.isFinite(value));

  if (!hasOperation && !hasKnownOutput && !hasKnownInput) return false;
  if (!hasValue) return false;
  if (claim.operation_type === "set") return hasKnownOutput;
  if (["multiply", "divide", "remainder", "add", "subtract"].includes(claim.operation_type)) {
    return (hasKnownInput || hasKnownOutput) && hasValue;
  }
  return hasKnownOutput || hasKnownInput;
}

function classifyStrictClaim(claim, reverseMap) {
  if (DIRECT_CONFIDENCE.has(claim.confidence) && isMeaningfulStructuredClaim(claim)) {
    const strictType = detectClaimType(claim);
    if (["constant_definition", "derived_constant", "procedure_step", "formula", "worked_example"].includes(strictType)) {
      return strictType;
    }
  }

  if (hasKnownTermSupport(claim, reverseMap)) {
    return "term_gloss";
  }

  return null;
}

function buildStrictClaimBank(claimsPayload) {
  const reverseMap = reverseEnglishMap();
  const strictClaims = [];

  for (const claim of claimsPayload.claims ?? []) {
    if (!inScope(claim.system, claim.page_start, claim.page_end)) continue;
    if (!["santong", "sifen"].includes(claim.system)) continue;

    const strictType = classifyStrictClaim(claim, reverseMap);
    if (!strictType) continue;

    const evidenceLevel = detectEvidenceLevel(strictType, claim);
    const chineseTerms = new Set(claimKnownChineseTerms(claim, reverseMap));
    const englishTerms = claimKnownEnglishTerms(claim);

    strictClaims.push({
      claim_id: claim.claim_id ?? claim.id,
      system: claim.system,
      claim_type: strictType,
      procedure_family: inferClaimProcedureFamily(claim),
      procedure_name: claim.procedure_name ?? null,
      operation_type: claim.operation_type ?? null,
      inputs: claim.inputs ?? [],
      output: claim.output ?? null,
      values: {
        numbers: claim.values ?? [],
        output_value: claim.output?.value ?? null,
        input_values: (claim.inputs ?? []).map((item) => item.value).filter((value) => value !== null),
      },
      chinese_terms: [...chineseTerms],
      english_terms: englishTerms,
      formula_text: claim.formula_text ?? claim.sentence ?? "",
      evidence_text: claim.sentence ?? claim.formula_text ?? "",
      evidence_chunk_id: claim.evidence_chunk_id,
      page_start: claim.page_start,
      page_end: claim.page_end,
      evidence_level: evidenceLevel,
      can_support_A_confirmed: canSupportAConfirmed(strictType, claim),
      source_claim_confidence: claim.confidence ?? null,
    });
  }

  return uniqueBy(strictClaims, (item) => item.claim_id);
}

function buildVariantMap() {
  const map = new Map();
  for (const group of TERM_VARIANT_GROUPS) {
    const normalized = group[0];
    for (const item of group) map.set(item, normalized);
  }
  return map;
}

function normalizeVariant(term, variantMap) {
  const raw = normalizeChineseName(term);
  return variantMap.get(raw) ?? raw;
}

function inferTermType(term, value) {
  const normalized = normalizeChineseName(term);
  if (/餘|余|馀/u.test(normalized)) return "remainder";
  if (/甲子|之次|日次|次$/u.test(normalized)) return "cycle";
  if (/積|积/u.test(normalized)) return "procedure_output";
  if (/法/u.test(normalized) && value !== null) return "constant";
  if (/法/u.test(normalized)) return "method_term";
  if (/度|分|日|月|歲|岁/u.test(normalized) && value === null) return "unit";
  if (value !== null) return "derived_constant";
  return "method_term";
}

function extractScopedChunks(chunksPayload, system) {
  return (chunksPayload.chunks ?? []).filter((chunk) => inScope(system, chunk.page_start, chunk.page_end));
}

function strongestClaimForTerm(strictClaims, system, englishTerms, value) {
  const lowered = new Set((englishTerms ?? []).map((item) => String(item).toLowerCase()));
  const matches = strictClaims.filter((claim) => {
    if (claim.system !== system) return false;
    const claimEnglish = new Set((claim.english_terms ?? []).map((item) => String(item).toLowerCase()));
    const englishOverlap = [...lowered].some((term) => claimEnglish.has(term));
    const valueMatch = value !== null && (claim.values?.numbers ?? []).includes(value);
    return englishOverlap || (claim.can_support_A_confirmed && valueMatch);
  });

  const ordered = matches.sort((left, right) => {
    const leftWeight = left.evidence_level === "A_direct" ? 3 : left.evidence_level === "B_contextual" ? 2 : 1;
    const rightWeight = right.evidence_level === "A_direct" ? 3 : right.evidence_level === "B_contextual" ? 2 : 1;
    return rightWeight - leftWeight;
  });

  return ordered[0] ?? null;
}

function buildTermBank(strictClaims, validationReport) {
  const variantMap = buildVariantMap();
  const termbank = [];

  for (const [system, mapping] of Object.entries(QUANTITY_ENGLISH_MAP)) {
    if (!["santong", "sifen"].includes(system)) continue;
    for (const [chineseTerm, englishTerms] of Object.entries(mapping)) {
      const normalizedChinese = normalizeVariant(chineseTerm, variantMap);
      const explicitConstant = (validationReport.extracted_constants ?? []).find((item) =>
        item.source_id === system
        && normalizeVariant(item.normalized_name ?? item.name_zh, variantMap) === normalizedChinese
      ) ?? null;
      const bestClaim = strongestClaimForTerm(strictClaims, system, englishTerms, explicitConstant?.value ?? null);
      if (!bestClaim && !explicitConstant) continue;

      termbank.push({
        term_id: `cullen:term:${system}:${normalizedChinese}`,
        system,
        chinese_term: normalizedChinese,
        english_terms: englishTerms,
        normalized_variants: TERM_VARIANT_GROUPS.find((group) => group.includes(chineseTerm)) ?? [normalizedChinese],
        term_type: inferTermType(normalizedChinese, explicitConstant?.value ?? null),
        value_if_constant: explicitConstant?.value ?? null,
        source: {
          cullen_chunk_id: bestClaim?.evidence_chunk_id ?? null,
          page_start: bestClaim?.page_start ?? null,
          page_end: bestClaim?.page_end ?? null,
        },
        evidence_level: bestClaim?.evidence_level ?? "C_background",
        notes: explicitConstant
          ? `Matched Cullen support for ${englishTerms.join(", ")}; value grounded in ${explicitConstant.source_span_id}.`
          : `Matched Cullen support for ${englishTerms.join(", ")}.`,
      });
    }
  }

  for (const claim of strictClaims) {
    if (!["santong", "sifen"].includes(claim.system)) continue;
    if (!(claim.chinese_terms ?? []).length) continue;
    for (const chineseTerm of claim.chinese_terms ?? []) {
      const normalizedChinese = normalizeVariant(chineseTerm, variantMap);
      if (!normalizedChinese) continue;
      const explicitConstant = (validationReport.extracted_constants ?? []).find((item) =>
        item.source_id === claim.system
        && normalizeVariant(item.normalized_name ?? item.name_zh, variantMap) === normalizedChinese
      ) ?? null;
      const candidateEnglishTerms = unique([
        ...(claim.english_terms ?? []),
        ...(claim.inputs ?? []).map((item) => item.english_term).filter(Boolean),
        ...(claim.output?.english_term ? [claim.output.english_term] : []),
        ...(claim.divisor?.english_term ? [claim.divisor.english_term] : []),
        ...(claim.remainder?.english_term ? [claim.remainder.english_term] : []),
      ]).filter(Boolean);
      if (!candidateEnglishTerms.length && !explicitConstant) continue;

      termbank.push({
        term_id: `cullen:term:${claim.system}:${normalizedChinese}`,
        system: claim.system,
        chinese_term: normalizedChinese,
        english_terms: candidateEnglishTerms,
        normalized_variants: TERM_VARIANT_GROUPS.find((group) => group.includes(chineseTerm)) ?? [normalizedChinese],
        term_type: inferTermType(normalizedChinese, explicitConstant?.value ?? null),
        value_if_constant: explicitConstant?.value ?? null,
        source: {
          cullen_chunk_id: claim.evidence_chunk_id ?? null,
          page_start: claim.page_start ?? null,
          page_end: claim.page_end ?? null,
        },
        evidence_level: claim.evidence_level ?? "B_contextual",
        notes: explicitConstant
          ? `Claim-derived Cullen support for ${candidateEnglishTerms.join(", ")}; value grounded in ${explicitConstant.source_span_id}.`
          : `Claim-derived Cullen support for ${candidateEnglishTerms.join(", ")}.`,
      });
    }
  }

  return uniqueBy(termbank, (item) => item.term_id).sort((a, b) => a.term_id.localeCompare(b.term_id));
}

function buildProcedureBank(strictClaims, chunksPayload, termbank) {
  return PROCEDURE_PROFILES.map((profile) => {
    const scopeChunks = extractScopedChunks(chunksPayload, profile.system);
    const matchedChunks = scopeChunks.filter((chunk) =>
      profile.cues.some((cue) => `${chunk.heading ?? ""} ${chunk.text ?? ""}`.toLowerCase().includes(cue.toLowerCase()))
    );
    const matchedClaims = strictClaims.filter((claim) =>
      claim.system === profile.system
      && claim.evidence_level !== "C_background"
      && matchedChunks.some((chunk) => chunk.id === claim.evidence_chunk_id)
    );
    const operations = [...new Set(matchedClaims.map((claim) => claim.operation_type).filter(Boolean))];
    const knownInputs = [...new Set(matchedClaims.flatMap((claim) => (claim.inputs ?? []).flatMap((item) => item.english_term ? [item.english_term] : [])))];
    const knownOutputs = [...new Set(matchedClaims.flatMap((claim) => claim.output?.english_term ? [claim.output.english_term] : []))];
    const knownConstants = [...new Set(
      termbank
        .filter((term) => term.system === profile.system && term.value_if_constant !== null)
        .filter((term) => matchedClaims.some((claim) => (claim.english_terms ?? []).some((english) => term.english_terms.includes(english))))
        .map((term) => term.chinese_term)
    )];
    const evidenceLevel = strongestLevel(matchedClaims.map((claim) => claim.evidence_level));

    return {
      cullen_procedure_id: profile.cullen_procedure_id,
      system: profile.system,
      procedure_title_zh: profile.procedure_title_zh,
      cullen_title_or_section: profile.cullen_title_or_section,
      source_chunks: matchedChunks.map((chunk) => chunk.id),
      supported_operations: operations,
      known_inputs: knownInputs,
      known_outputs: knownOutputs,
      known_constants: knownConstants,
      evidence_level: evidenceLevel,
    };
  }).filter((item) => item.source_chunks.length > 0);
}

function mapProcedureBySpan(procedurePayload) {
  const out = new Map();
  for (const procedure of procedurePayload.procedures ?? []) {
    out.set(procedure.source_span_id, procedure);
  }
  return out;
}

function mapValidationByProcedure(validationReport) {
  const out = new Map();
  for (const check of validationReport.checks ?? []) {
    if (!out.has(check.procedure_id)) out.set(check.procedure_id, []);
    out.get(check.procedure_id).push(check);
  }
  return out;
}

function findMatchedTermsForText(text, system, termbank) {
  return termbank
    .filter((term) => term.system === system)
    .filter((term) => {
      const variants = term.normalized_variants ?? [term.chinese_term];
      return variants.some((variant) => text.includes(variant));
    })
    .map((term) => term.chinese_term);
}

function matchedClaimTerms(claim, matchedTerms) {
  const claimTerms = new Set(claim.chinese_terms ?? []);
  return matchedTerms.filter((term) => claimTerms.has(term));
}

function claimMatchScore(claim, matchedTerms, values) {
  let score = 0;
  const termMatches = matchedClaimTerms(claim, matchedTerms);
  for (const term of termMatches) score += 3;
  for (const value of values) {
    if ((claim.values?.numbers ?? []).includes(value) && claim.can_support_A_confirmed) score += 1;
  }
  if (claim.can_support_A_confirmed && termMatches.length > 0) score += 2;
  return score;
}

function extractMatchedNumbers(sourceText, claim) {
  const sourceValues = new Set(parseSourceValues(sourceText));
  return (claim.values?.numbers ?? []).filter((value) => sourceValues.has(value));
}

function buildClaimMatchDiagnostic(sourceSpan, claim, matchedTerms, sourceFamily) {
  const matchedChineseTerms = matchedClaimTerms(claim, matchedTerms);
  const matchedEnglishTerms = (claim.english_terms ?? []).filter(Boolean);
  const matchedNumbers = extractMatchedNumbers(sourceSpan.source_text ?? sourceSpan.text ?? "", claim);
  const matchedOperationTypes = [claim.operation_type].filter(Boolean);
  const compatible = procedureFamiliesCompatible(sourceFamily, claim.procedure_family);
  const distinctiveTerms = extractDistinctiveTermsForClaim(claim, sourceSpan);
  const hasProcedureTitleSupport = Boolean(claim.procedure_name && extractDistinctiveTermsFromText(claim.procedure_name).length);
  const coreSignals = buildCoreMatchSignals({
    matchedChineseTerms,
    matchedEnglishTerms,
    matchedOperationTypes,
    distinctiveTerms,
  });
  const matchStrength = deriveMatchStrength(compatible, coreSignals, hasProcedureTitleSupport);
  const matchReasons = [];
  if (matchedChineseTerms.length) matchReasons.push("shared_chinese_terms");
  if (matchedEnglishTerms.length) matchReasons.push("structured_english_terms");
  if (matchedNumbers.length) matchReasons.push("shared_numbers");
  if (compatible) matchReasons.push("procedure_family_compatible");
  if (distinctiveTerms.length) matchReasons.push("distinctive_terms");
  const warnings = [];
  if (!compatible) warnings.push(`procedure_family_mismatch:${sourceFamily}->${claim.procedure_family}`);
  if (!matchedChineseTerms.length) warnings.push("no_direct_chinese_term_overlap");
  if (!claim.can_support_A_confirmed) warnings.push("not_direct_supporting_claim");
  if (matchStrength === "generic_only") warnings.push("generic_term_only_match");
  const candidateStatus = compatible && matchStrength !== "generic_only"
    ? "compatible_candidate"
    : "noisy_candidate";
  return {
    claim_id: claim.claim_id,
    claim_type: claim.claim_type,
    procedure_family: claim.procedure_family ?? "unknown",
    cullen_procedure_title: claim.procedure_name ?? null,
    evidence_chunk_id: claim.evidence_chunk_id,
    evidence_text: claim.evidence_text,
    matched_chinese_terms: matchedChineseTerms,
    matched_english_terms: matchedEnglishTerms,
    matched_numbers: matchedNumbers,
    matched_operation_types: matchedOperationTypes,
    distinctive_terms: distinctiveTerms,
    match_strength: matchStrength,
    match_reason: matchReasons.length ? matchReasons.join(",") : "weak_term_overlap",
    mismatch_warning: warnings,
    candidate_status: candidateStatus,
    alignment_quality: compatible
      ? ((matchStrength === "strong" || matchStrength === "medium")
        ? (claim.can_support_A_confirmed && matchedChineseTerms.length ? "good" : "plausible")
        : "noisy")
      : (matchedChineseTerms.length || matchedNumbers.length ? "noisy" : "wrong"),
  };
}

function parseSourceValues(text) {
  const values = [];
  for (const match of text.matchAll(/\d+/gu)) values.push(Number(match[0]));
  return values;
}

function isGenericChineseTerm(term) {
  return GENERIC_CHINESE_TERMS.has(normalizeChineseTerm(term));
}

function isGenericEnglishMatchTerm(term) {
  return GENERIC_ENGLISH_TERMS_FOR_MATCH.has(normalizedEnglishTerm(term));
}

function extractDistinctiveTermsFromText(text) {
  const haystack = String(text ?? "");
  const found = [];
  for (const rule of DISTINCTIVE_TERM_RULES) {
    const chineseMatch = (rule.chinese ?? []).some((pattern) => pattern.test(haystack));
    const englishMatch = (rule.english ?? []).some((pattern) => pattern.test(haystack));
    if (chineseMatch || englishMatch) found.push(rule.key);
  }
  return unique(found);
}

function extractDistinctiveTermsForClaim(claim, sourceSpan = null) {
  return unique([
    ...extractDistinctiveTermsFromText(claim.procedure_name ?? ""),
    ...extractDistinctiveTermsFromText(claim.evidence_text ?? claim.formula_text ?? ""),
    ...extractDistinctiveTermsFromText(sourceSpan?.source_text ?? sourceSpan?.text ?? ""),
  ]);
}

function extractDistinctiveTermsForSpan(sourceSpan, currentProcedure = null) {
  return unique([
    ...extractDistinctiveTermsFromText(currentProcedure?.title_guess ?? ""),
    ...extractDistinctiveTermsFromText(sourceSpan?.source_text ?? sourceSpan?.text ?? ""),
  ]);
}

function buildCoreMatchSignals({
  matchedChineseTerms,
  matchedEnglishTerms,
  matchedOperationTypes,
  distinctiveTerms,
}) {
  const nonGenericChineseTerms = matchedChineseTerms.filter((term) => !isGenericChineseTerm(term));
  const nonGenericEnglishTerms = matchedEnglishTerms.filter((term) => !isGenericEnglishMatchTerm(term));
  const nonGenericOperationTypes = matchedOperationTypes.filter((term) => !GENERIC_OPERATION_TYPES.has(term));
  const hasOnlyGenericTerms = !nonGenericChineseTerms.length
    && !nonGenericEnglishTerms.length
    && !nonGenericOperationTypes.length
    && (
      matchedChineseTerms.length > 0
      || matchedEnglishTerms.length > 0
      || matchedOperationTypes.length > 0
    );

  return {
    nonGenericChineseTerms,
    nonGenericEnglishTerms,
    nonGenericOperationTypes,
    hasOnlyGenericTerms,
    hasDistinctiveTerms: distinctiveTerms.length > 0,
  };
}

function deriveMatchStrength(compatible, coreSignals, hasProcedureTitleSupport) {
  if (coreSignals.hasOnlyGenericTerms && !coreSignals.hasDistinctiveTerms) return "generic_only";
  if (compatible && (coreSignals.hasDistinctiveTerms || hasProcedureTitleSupport)) return "strong";
  if (compatible && (
    coreSignals.nonGenericChineseTerms.length
    || coreSignals.nonGenericEnglishTerms.length
    || coreSignals.nonGenericOperationTypes.length
  )) return "medium";
  if (
    coreSignals.nonGenericChineseTerms.length
    || coreSignals.nonGenericEnglishTerms.length
    || coreSignals.nonGenericOperationTypes.length
    || coreSignals.hasDistinctiveTerms
  ) return "weak";
  return "generic_only";
}

function scoreMatchStrength(matchStrength) {
  return {
    strong: 4,
    medium: 3,
    weak: 2,
    generic_only: 1,
  }[matchStrength] ?? 0;
}

function scoreAlignmentQuality(alignmentQuality) {
  return {
    good: 4,
    plausible: 3,
    noisy: 2,
    wrong: 1,
    none: 0,
  }[alignmentQuality] ?? 0;
}

function summarizeAlignmentQuality(diagnostics) {
  const qualities = diagnostics.map((item) => item.alignment_quality);
  if (qualities.includes("good")) return "good";
  if (qualities.includes("plausible")) return "plausible";
  if (qualities.includes("noisy")) return "noisy";
  if (qualities.includes("wrong")) return "wrong";
  return "none";
}

function buildAnchorBackedClaimDiagnostics(sourceSpan, matchedTerms, strictClaimsById, sourceFamily, procedureAnchors) {
  const matchingAnchors = findAnchorsForSourceSpan({ items: procedureAnchors }, sourceSpan.source_span_id ?? sourceSpan.id);
  const diagnostics = [];

  for (const anchor of matchingAnchors) {
    for (const claimId of anchor.claim_ids ?? []) {
      const claim = strictClaimsById.get(claimId);
      if (!claim) continue;

      const diagnostic = buildClaimMatchDiagnostic(
        sourceSpan,
        {
          ...claim,
          procedure_family: anchor.procedure_family,
          procedure_name: `${anchor.cullen_proc_id}. ${anchor.english_title}`,
        },
        matchedTerms,
        sourceFamily,
      );

      const distinctiveTerms = uniqueStrings([
        ...(diagnostic.distinctive_terms ?? []),
        ...(anchor.distinctive_terms ?? []),
      ]);
      const directAnchorMatch = procedureFamiliesCompatible(sourceFamily, anchor.procedure_family);
      const matchStrength = directAnchorMatch
        ? (distinctiveTerms.length ? "strong" : "medium")
        : (diagnostic.match_strength ?? "weak");
      const filteredWarnings = (diagnostic.mismatch_warning ?? []).filter((warning) =>
        !warning.startsWith("procedure_family_mismatch:")
      );

      diagnostics.push({
        ...diagnostic,
        procedure_family: anchor.procedure_family,
        cullen_procedure_title: `${anchor.cullen_proc_id}. ${anchor.english_title}`,
        matched_english_terms: uniqueStrings([
          ...(diagnostic.matched_english_terms ?? []),
          anchor.english_title,
        ]),
        distinctive_terms: distinctiveTerms,
        match_strength: matchStrength,
        candidate_status: directAnchorMatch ? "compatible_candidate" : diagnostic.candidate_status,
        alignment_quality: directAnchorMatch
          ? (matchStrength === "strong" ? "good" : "plausible")
          : diagnostic.alignment_quality,
        mismatch_warning: filteredWarnings,
        supporting_anchor_ids: [anchor.anchor_id],
      });
    }
  }

  return diagnostics;
}

function summarizeCullenEvidenceStatus({
  directClaims,
  compatibleClaimDiagnostics,
  noisyClaimDiagnostics,
  matchedTerms,
  matchedProcedures,
}) {
  if (directClaims.length) return "direct_candidate_claims";
  if (compatibleClaimDiagnostics.length) return "contextual_candidate_claims";
  if (noisyClaimDiagnostics.length) return "noisy_only";
  if (matchedTerms.length || matchedProcedures.length) return "term_or_procedure_signal_only";
  return "none";
}

function summarizeAlignmentStatus(validationChecks, {
  directClaims,
  compatibleClaimDiagnostics,
  noisyClaimDiagnostics,
} = {}) {
  const validationStatuses = (validationChecks ?? [])
    .map((item) => item.cullen_grounding?.alignment_status)
    .filter(Boolean);
  const aligned = strongestValue(
    validationStatuses,
    ["direct_support", "partial_support", "weak_support", "no_support"],
    null,
  );
  if (aligned) return aligned;
  if (directClaims?.length) return "candidate_direct_claim_match";
  if (compatibleClaimDiagnostics?.length) return "candidate_family_match";
  if (noisyClaimDiagnostics?.length) return "family_mismatch_only";
  return "no_alignment_signal";
}

function summarizeValidationStatus(validationChecks) {
  const statuses = unique((validationChecks ?? []).map((item) => item.grounding_status).filter(Boolean));
  if (!statuses.length) return "no_validation_checks";
  return strongestValue(
    statuses,
    ["A_confirmed", "B_supported_with_semantic_count", "B_textual_partial", "B_textual_internal", "needs_review"],
    statuses[0],
  );
}

function summarizeFinalConfidence(validationChecks, cullenEvidenceStatus) {
  const confidenceValues = unique((validationChecks ?? [])
    .map((item) => item.cullen_grounding?.confidence_after_alignment)
    .filter(Boolean));
  const strongest = strongestValue(
    confidenceValues,
    ["A_confirmed", "B_textual_internal", "B_partial", "needs_review"],
    null,
  );
  if (strongest) return strongest;
  if (cullenEvidenceStatus === "direct_candidate_claims") return "candidate_direct_only";
  if (cullenEvidenceStatus === "contextual_candidate_claims") return "candidate_contextual_only";
  if (cullenEvidenceStatus === "noisy_only") return "noisy_candidate_only";
  return "needs_review";
}

function preserveHumanFields(existingItem) {
  const preserved = {};
  for (const field of PRESERVED_HUMAN_FIELDS) {
    if (Object.prototype.hasOwnProperty.call(existingItem ?? {}, field)) {
      preserved[field] = existingItem[field];
    }
  }
  if (!Object.prototype.hasOwnProperty.call(preserved, "human_review_status")) {
    preserved.human_review_status = "unreviewed";
  }
  return preserved;
}

function sortClaimDiagnosticsForReview(items) {
  return [...items].sort((left, right) => {
    const strengthDiff = scoreMatchStrength(right.match_strength) - scoreMatchStrength(left.match_strength);
    if (strengthDiff) return strengthDiff;
    const qualityDiff = scoreAlignmentQuality(right.alignment_quality) - scoreAlignmentQuality(left.alignment_quality);
    if (qualityDiff) return qualityDiff;
    return left.claim_id.localeCompare(right.claim_id);
  });
}

function buildRejectedFamiliesCandidate(noisyClaimDiagnostics) {
  const grouped = new Map();
  for (const item of noisyClaimDiagnostics) {
    const key = item.procedure_family ?? "unknown";
    if (!grouped.has(key)) grouped.set(key, []);
    grouped.get(key).push(item.claim_id);
  }
  return [...grouped.entries()]
    .map(([procedureFamily, claimIds]) => ({
      procedure_family: procedureFamily,
      claim_ids: claimIds,
    }))
    .sort((left, right) => left.procedure_family.localeCompare(right.procedure_family));
}

function buildAcceptedCluesCandidate(compatibleClaimDiagnostics) {
  return compatibleClaimDiagnostics
    .filter((item) => item.match_strength !== "generic_only")
    .map((item) => ({
    claim_id: item.claim_id,
    evidence_chunk_id: item.evidence_chunk_id,
    procedure_family: item.procedure_family,
    alignment_quality: item.alignment_quality,
    match_strength: item.match_strength,
    distinctive_terms: item.distinctive_terms ?? [],
    matched_chinese_terms: item.matched_chinese_terms ?? [],
    matched_english_terms: item.matched_english_terms ?? [],
    matched_operation_types: item.matched_operation_types ?? [],
    evidence_text: item.evidence_text ?? "",
  }));
}

function buildCandidateUncertaintyNotes({
  coverageEntry,
  validationChecks,
  currentProcedure,
  acceptedClues,
  rejectedFamilies,
}) {
  const notes = [];
  if (!currentProcedure?.steps?.length) notes.push("No structured procedure step is currently extracted for this span.");
  if (!acceptedClues.length) notes.push("No compatible accepted candidate claim is currently available.");
  if (rejectedFamilies.length) {
    notes.push(`Competing noisy families present: ${rejectedFamilies.map((item) => item.procedure_family).join(", ")}.`);
  }
  if (coverageEntry?.blocking_reason) notes.push(`Blocking reason: ${coverageEntry.blocking_reason}.`);
  const validationStatus = summarizeValidationStatus(validationChecks);
  if (validationStatus !== "A_confirmed") notes.push(`Validation remains ${validationStatus}.`);
  const unresolvedReference = (validationChecks ?? []).some((item) =>
    JSON.stringify(item.cullen_grounding?.signature ?? {}).includes("unresolved_reference")
  );
  if (unresolvedReference) notes.push("Validation still contains unresolved_reference quantities.");
  const lexicalCount = (validationChecks ?? []).some((item) =>
    JSON.stringify(item.cullen_grounding?.signature ?? {}).includes("lexical_count")
  );
  if (lexicalCount) notes.push("Validation still contains lexical_count-derived quantities.");
  return notes.length ? notes : ["Machine candidate only; human review is still required."];
}

function buildCoverageEntry(sourceSpan, matchedTerms, strictClaims, strictClaimsById, procedureBank, procedureAnchors, currentProcedure, validationChecks, benchmarkId = null) {
  const sourceFamily = inferSourceProcedureFamily(sourceSpan, currentProcedure);
  const values = parseSourceValues(sourceSpan.source_text ?? sourceSpan.text ?? "");
  const scoredClaims = strictClaims
    .filter((claim) => claim.system === sourceSpan.system || claim.system === sourceSpan.source_id)
    .map((claim) => ({ claim, score: claimMatchScore(claim, matchedTerms, values) }))
    .filter((item) => item.score > 0)
    .sort((left, right) => right.score - left.score);
  const seededClaimDiagnostics = scoredClaims.slice(0, 12).map((item) =>
    buildClaimMatchDiagnostic(sourceSpan, item.claim, matchedTerms, sourceFamily)
  );
  const anchorClaimDiagnostics = buildAnchorBackedClaimDiagnostics(
    sourceSpan,
    matchedTerms,
    strictClaimsById,
    sourceFamily,
    procedureAnchors,
  );
  const claimDiagnosticsById = new Map();
  for (const diagnostic of [...seededClaimDiagnostics, ...anchorClaimDiagnostics]) {
    const existing = claimDiagnosticsById.get(diagnostic.claim_id);
    claimDiagnosticsById.set(
      diagnostic.claim_id,
      existing ? chooseBetterDiagnostic(existing, diagnostic) : diagnostic,
    );
  }
  const claimDiagnostics = [...claimDiagnosticsById.values()];
  const sourceDistinctiveTerms = extractDistinctiveTermsForSpan(sourceSpan, currentProcedure);
  const compatibleClaimDiagnostics = claimDiagnostics.filter((item) => item.candidate_status === "compatible_candidate");
  const noisyClaimDiagnostics = claimDiagnostics.filter((item) => item.candidate_status === "noisy_candidate");
  const matchedClaims = compatibleClaimDiagnostics.slice(0, 8).map((item) => item.claim_id);
  const matchedAnchors = findAnchorsForSourceSpan({ items: procedureAnchors }, sourceSpan.source_span_id ?? sourceSpan.id);
  const matchedProcedures = procedureBank
    .filter((procedure) => procedure.system === (sourceSpan.system ?? sourceSpan.source_id))
    .filter((procedure) => procedureFamiliesCompatible(sourceFamily, inferSourceProcedureFamily({
      source_text: procedure.procedure_title_zh ?? procedure.cullen_title_or_section ?? "",
      text: procedure.cullen_title_or_section ?? "",
      title_guess: procedure.procedure_title_zh ?? "",
    })))
    .filter((procedure) => {
      const known = [...procedure.known_inputs, ...procedure.known_outputs, ...procedure.known_constants].join(" ").toLowerCase();
      return matchedTerms.some((term) => known.includes(term.toLowerCase()))
        || procedure.source_chunks.some((chunkId) => matchedClaims.some((claimId) => strictClaims.find((claim) => claim.claim_id === claimId)?.evidence_chunk_id === chunkId));
    })
    .map((procedure) => procedure.cullen_procedure_id);
  const matchedProcedureIds = uniqueStrings([
    ...matchedProcedures,
    ...matchedAnchors.map((anchor) => anchor.cullen_proc_id),
  ]);

  const directClaims = scoredClaims
    .filter((item) => procedureFamiliesCompatible(sourceFamily, item.claim.procedure_family))
    .filter((item) => item.claim.can_support_A_confirmed && matchedClaimTerms(item.claim, matchedTerms).length > 0);
  const contextualClaims = scoredClaims
    .filter((item) => procedureFamiliesCompatible(sourceFamily, item.claim.procedure_family))
    .filter((item) => !item.claim.can_support_A_confirmed);
  const validationA = (validationChecks ?? []).some((item) => item.grounding_status === "A_confirmed");
  const lexicalBlock = (validationChecks ?? []).some((item) => item.grounding_status === "B_supported_with_semantic_count");
  const unresolvedBlock = (validationChecks ?? []).some((item) => item.grounding_status === "needs_review");

  let coverageStatus = "not_covered";
  if (directClaims.length && validationA) coverageStatus = "directly_covered";
  else if (directClaims.length || (matchedProcedures.length && matchedTerms.length > 0)) coverageStatus = "partially_covered";
  else if (contextualClaims.length || matchedTerms.length) coverageStatus = "context_only";

  let blockingReason = null;
  if (coverageStatus !== "directly_covered") {
    if (!directClaims.length) blockingReason = "no_direct_cullen_claim";
    else if (!validationA && unresolvedBlock) blockingReason = "validation_not_closed";
    else if (lexicalBlock) blockingReason = "critical_quantity_lexical_only";
  }

  const cullenEvidenceStatus = summarizeCullenEvidenceStatus({
    directClaims,
    compatibleClaimDiagnostics,
    noisyClaimDiagnostics,
    matchedTerms,
    matchedProcedures,
  });
  const alignmentStatus = summarizeAlignmentStatus(validationChecks, {
    directClaims,
    compatibleClaimDiagnostics,
    noisyClaimDiagnostics,
  });
  const validationStatus = summarizeValidationStatus(validationChecks);
  const finalConfidence = summarizeFinalConfidence(validationChecks, cullenEvidenceStatus);

  return {
    source_span_id: sourceSpan.source_span_id ?? sourceSpan.id,
    benchmark_id: benchmarkId,
    system: sourceSpan.system ?? sourceSpan.source_id,
    procedure_id: currentProcedure?.procedure_id ?? null,
    procedure_family: sourceFamily,
    source_text: sourceSpan.source_text ?? sourceSpan.text,
    distinctive_terms: sourceDistinctiveTerms,
    matched_cullen_terms: matchedTerms,
    matched_cullen_claims: matchedClaims,
    matched_cullen_anchors: matchedAnchors.map((anchor) => anchor.anchor_id),
    noisy_candidate_claims: noisyClaimDiagnostics.map((item) => item.claim_id),
    claim_match_diagnostics: claimDiagnostics,
    matched_cullen_procedures: matchedProcedureIds,
    coverage_status: coverageStatus,
    cullen_evidence_status: cullenEvidenceStatus,
    alignment_status: alignmentStatus,
    validation_status: validationStatus,
    final_confidence: finalConfidence,
    can_support_A_confirmed: coverageStatus === "directly_covered" && !blockingReason,
    blocking_reason: blockingReason,
  };
}

function buildCoverageMatrix(sourceSpansPayload, strictClaims, strictClaimsById, procedureBank, procedureAnchors, procedurePayload, validationReport, benchmarkConfig, termbank) {
  const procedureBySpan = mapProcedureBySpan(procedurePayload);
  const validationByProcedure = mapValidationByProcedure(validationReport);

  const sourceSpanCoverage = (sourceSpansPayload.spans ?? [])
    .filter((span) => ["santong", "sifen"].includes(span.source_id))
    .map((span) => {
      const currentProcedure = procedureBySpan.get(span.id) ?? null;
      const validationChecks = currentProcedure ? (validationByProcedure.get(currentProcedure.procedure_id) ?? []) : [];
      const matchedTerms = findMatchedTermsForText(span.text, span.source_id, termbank);
      return buildCoverageEntry(
        { ...span, system: span.source_id, source_text: span.text },
        matchedTerms,
        strictClaims,
        strictClaimsById,
        procedureBank,
        procedureAnchors,
        currentProcedure,
        validationChecks,
      );
    });

  const benchmarkCoverage = (benchmarkConfig.items ?? [])
    .filter((item) => ["santong", "sifen"].includes(item.source_id))
    .map((item) => {
      const sourceText = (item.source_terms ?? []).join(" ");
      const matchedTerms = findMatchedTermsForText(sourceText, item.source_id, termbank);
      const currentProcedure = (procedurePayload.procedures ?? []).find((procedure) =>
        procedure.source_id === item.source_id
        && (procedure.steps ?? []).some((step) =>
          (item.validation_expression_terms ?? item.operation_terms ?? item.source_terms ?? []).some((term) =>
            `${step.expression} ${step.operation_signature}`.includes(term)
          )
        )
      ) ?? null;
      const validationChecks = currentProcedure ? (validationByProcedure.get(currentProcedure.procedure_id) ?? []) : [];
      return buildCoverageEntry(
        {
          source_span_id: item.id,
          system: item.source_id,
          source_text: item.label,
        },
        matchedTerms,
        strictClaims,
        strictClaimsById,
        procedureBank,
        procedureAnchors,
        currentProcedure,
        validationChecks,
        item.id,
      );
    });

  return {
    generated_at: new Date().toISOString(),
    source_span_coverage: sourceSpanCoverage,
    benchmark_item_coverage: benchmarkCoverage,
  };
}

function inferCapability(item) {
  if ((item.expected_ops ?? []).includes("divide") && (item.source_terms ?? []).some((term) => /甲子|七曜/u.test(term))) {
    return "mod_cycle";
  }
  if ((item.expected_ops ?? []).includes("divide")) return "quotient_remainder";
  if (item.validation_expression_terms?.length >= 2) return "multiply_step";
  if (item.expected_value !== undefined && item.source_terms?.length === 1) return "constant_definition";
  return "term_mapping";
}

function buildExpectedStep(item) {
  if (inferCapability(item) === "multiply_step") {
    return {
      source_terms: item.validation_expression_terms ?? item.source_terms ?? [],
      expected_value: item.expected_value ?? null,
    };
  }
  if (inferCapability(item) === "quotient_remainder" || inferCapability(item) === "mod_cycle") {
    return {
      source_terms: item.operation_terms ?? item.source_terms ?? [],
      expected_ops: item.expected_ops ?? [],
    };
  }
  return {
    source_terms: item.source_terms ?? [],
    expected_value: item.expected_value ?? null,
  };
}

function buildGoldCandidates(benchmarkConfig, coverageMatrix, validationReport) {
  const benchmarkCoverageMap = new Map((coverageMatrix.benchmark_item_coverage ?? []).map((item) => [item.benchmark_id, item]));

  return (benchmarkConfig.items ?? []).map((item) => {
    const coverage = benchmarkCoverageMap.get(item.id) ?? null;
    const candidateValidation = (validationReport.checks ?? []).find((check) =>
      (coverage?.procedure_id && check.procedure_id === coverage.procedure_id)
      || (item.validation_expression_terms ?? item.operation_terms ?? item.source_terms ?? []).some((term) =>
        check.expression.includes(term)
      )
    ) ?? null;

    const capability = inferCapability(item);
    const riskNotes = [];
    if (!item.cullen_expected) riskNotes.push("Phase-1 authority layer does not treat Cullen as direct support here.");
    if (coverage?.coverage_status !== "directly_covered") riskNotes.push(`Coverage is ${coverage?.coverage_status ?? "not_covered"}.`);
    if (candidateValidation?.grounding_status !== "A_confirmed") riskNotes.push(`Current validation status is ${candidateValidation?.grounding_status ?? "unknown"}.`);

    return {
      candidate_id: `cullen-gold:${item.id}`,
      system: item.source_id,
      source_span_id: coverage?.source_span_id ?? item.id,
      source_text: item.label,
      tested_capability: capability,
      expected_step: buildExpectedStep(item),
      expected_values: item.expected_value !== undefined ? { primary: item.expected_value } : {},
      required_cullen_support: Boolean(item.cullen_expected),
      matched_cullen_claims: coverage?.matched_cullen_claims ?? [],
      why_candidate_is_valid: item.cullen_expected
        ? `Candidate targets ${capability} and has Cullen-linked coverage status ${coverage?.coverage_status ?? "not_covered"}.`
        : `Candidate is retained as a transfer/boundary case for ${capability}.`,
      risk_notes: riskNotes.join(" ") || "Requires human review before promotion to final gold.",
      recommended_status: candidateValidation?.grounding_status === "A_confirmed" ? "reviewed_candidate" : "candidate",
    };
  });
}

function summarizeCounts(items, field) {
  const counts = {};
  for (const item of items) {
    const key = item[field];
    counts[key] = (counts[key] ?? 0) + 1;
  }
  return counts;
}

function buildSifenTargetFamilyCandidateMap(
  sourceSpansPayload,
  procedurePayload,
  validationReport,
  coverageMatrix,
  existingCandidateMap,
) {
  const spanById = new Map((sourceSpansPayload.spans ?? []).map((span) => [span.id, span]));
  const procedureBySpanId = new Map((procedurePayload.procedures ?? []).map((procedure) => [procedure.source_span_id, procedure]));
  const validationByProcedure = mapValidationByProcedure(validationReport);
  const coverageBySpanId = new Map((coverageMatrix.source_span_coverage ?? []).map((entry) => [entry.source_span_id, entry]));
  const existingBySpanId = new Map((existingCandidateMap?.items ?? []).map((item) => [item.source_span_id, item]));

  const items = SIFEN_TARGET_SPAN_IDS.map((sourceSpanId) => {
    const sourceSpan = spanById.get(sourceSpanId) ?? null;
    const currentProcedure = procedureBySpanId.get(sourceSpanId) ?? null;
    const validationChecks = currentProcedure ? (validationByProcedure.get(currentProcedure.procedure_id) ?? []) : [];
    const coverageEntry = coverageBySpanId.get(sourceSpanId) ?? null;
    const compatibleClaimDiagnostics = (coverageEntry?.claim_match_diagnostics ?? [])
      .filter((item) => item.candidate_status === "compatible_candidate");
    const noisyClaimDiagnostics = (coverageEntry?.claim_match_diagnostics ?? [])
      .filter((item) => item.candidate_status === "noisy_candidate");
    const acceptedClues = buildAcceptedCluesCandidate(compatibleClaimDiagnostics);
    const rejectedFamilies = buildRejectedFamiliesCandidate(noisyClaimDiagnostics);
    const genericTermOnlyCandidates = sortClaimDiagnosticsForReview(
      noisyClaimDiagnostics.filter((item) => item.match_strength === "generic_only")
    );
    const topNoisyCandidates = sortClaimDiagnosticsForReview(
      noisyClaimDiagnostics.filter((item) => item.match_strength !== "generic_only")
    ).slice(0, NOISY_DISPLAY_LIMIT);
    const omittedNoisyCandidateCount = noisyClaimDiagnostics.length - topNoisyCandidates.length - genericTermOnlyCandidates.length;
    const existingItem = existingBySpanId.get(sourceSpanId) ?? {};

    return {
      source_span_id: sourceSpanId,
      source_text: sourceSpan?.text ?? "",
      distinctive_terms: coverageEntry?.distinctive_terms ?? extractDistinctiveTermsForSpan(sourceSpan, currentProcedure),
      machine_expected_family: coverageEntry?.procedure_family ?? inferSourceProcedureFamily(sourceSpan ?? {}, currentProcedure),
      accepted_cullen_clues_candidate: acceptedClues,
      rejected_families_candidate: rejectedFamilies,
      top_noisy_candidates: topNoisyCandidates.map((item) => ({
        claim_id: item.claim_id,
        evidence_chunk_id: item.evidence_chunk_id,
        procedure_family: item.procedure_family,
        alignment_quality: item.alignment_quality,
        match_strength: item.match_strength,
        distinctive_terms: item.distinctive_terms ?? [],
        matched_chinese_terms: item.matched_chinese_terms ?? [],
        matched_english_terms: item.matched_english_terms ?? [],
        matched_operation_types: item.matched_operation_types ?? [],
        mismatch_warning: item.mismatch_warning ?? [],
        evidence_text: item.evidence_text ?? "",
      })),
      omitted_noisy_candidate_count: Math.max(0, omittedNoisyCandidateCount),
      generic_term_only_candidates: genericTermOnlyCandidates.map((item) => ({
        claim_id: item.claim_id,
        evidence_chunk_id: item.evidence_chunk_id,
        procedure_family: item.procedure_family,
        alignment_quality: item.alignment_quality,
        match_strength: item.match_strength,
        distinctive_terms: item.distinctive_terms ?? [],
        matched_chinese_terms: item.matched_chinese_terms ?? [],
        matched_english_terms: item.matched_english_terms ?? [],
        matched_operation_types: item.matched_operation_types ?? [],
        mismatch_warning: item.mismatch_warning ?? [],
        evidence_text: item.evidence_text ?? "",
      })),
      current_alignment_quality: summarizeAlignmentQuality(coverageEntry?.claim_match_diagnostics ?? []),
      current_accepted_claims: acceptedClues.map((item) => item.claim_id),
      current_noisy_claims: coverageEntry?.noisy_candidate_claims ?? [],
      uncertainty_notes: buildCandidateUncertaintyNotes({
        coverageEntry,
        validationChecks,
        currentProcedure,
        acceptedClues,
        rejectedFamilies,
      }),
      ...preserveHumanFields(existingItem),
    };
  });

  return {
    generated_at: new Date().toISOString(),
    authority: "machine_candidate_only",
    note: "Machine-generated candidate map. Non-authoritative until explicit human review.",
    target_span_ids: SIFEN_TARGET_SPAN_IDS,
    items,
  };
}

function renderClaimSection(title, claims) {
  const lines = [`### ${title}`, ""];
  if (!claims.length) {
    lines.push("- none", "");
    return lines;
  }

  for (const claim of claims) {
    lines.push(`- claim_id: ${claim.claim_id}`);
    lines.push(`  evidence_chunk_id: ${claim.evidence_chunk_id ?? "null"}`);
    lines.push(`  procedure_family: ${claim.procedure_family ?? "unknown"}`);
    lines.push(`  alignment_quality: ${claim.alignment_quality ?? "none"}`);
    lines.push(`  match_strength: ${claim.match_strength ?? "weak"}`);
    lines.push(`  distinctive_terms: ${(claim.distinctive_terms ?? []).join(", ") || "none"}`);
    lines.push(`  Cullen evidence text: ${claim.evidence_text ?? ""}`);
    lines.push(`  matched Chinese terms: ${(claim.matched_chinese_terms ?? []).join(", ") || "none"}`);
    lines.push(`  matched English terms: ${(claim.matched_english_terms ?? []).join(", ") || "none"}`);
    lines.push(`  matched operation types: ${(claim.matched_operation_types ?? []).join(", ") || "none"}`);
    lines.push(`  mismatch warnings: ${(claim.mismatch_warning ?? []).join("; ") || "none"}`);
    lines.push("");
  }
  return lines;
}

function buildSifenTargetFamilyReviewPacket(candidateMap, coverageMatrix, procedurePayload, procedureAnchorPayload) {
  const coverageBySpanId = new Map((coverageMatrix.source_span_coverage ?? []).map((entry) => [entry.source_span_id, entry]));
  const procedureBySpanId = new Map((procedurePayload.procedures ?? []).map((procedure) => [procedure.source_span_id, procedure]));
  const anchorById = new Map((procedureAnchorPayload.items ?? []).map((anchor) => [anchor.anchor_id, anchor]));
  const lines = [
    "# Sifen Target Family Review Packet",
    "",
    "Machine-generated review packet. This is not final gold and remains non-authoritative until human review.",
    "",
    `Generated: ${candidateMap.generated_at}`,
    "",
  ];

  for (const item of candidateMap.items ?? []) {
    const coverageEntry = coverageBySpanId.get(item.source_span_id) ?? null;
    const procedure = procedureBySpanId.get(item.source_span_id) ?? null;
    const acceptedClaims = (coverageEntry?.claim_match_diagnostics ?? [])
      .filter((claim) => claim.candidate_status === "compatible_candidate" && claim.match_strength !== "generic_only");
    const acceptedAnchors = (coverageEntry?.matched_cullen_anchors ?? [])
      .map((anchorId) => anchorById.get(anchorId))
      .filter(Boolean)
      .filter((anchor) => anchor.source_span_candidates?.includes(item.source_span_id));
    const topNoisyClaims = item.top_noisy_candidates ?? [];
    const genericOnlyClaims = item.generic_term_only_candidates ?? [];

    lines.push(`## ${item.source_span_id}`);
    lines.push("");
    lines.push(`- source text: ${item.source_text}`);
    lines.push(`- distinctive_terms: ${(item.distinctive_terms ?? []).join(", ") || "none"}`);
    lines.push(`- current procedure_family: ${coverageEntry?.procedure_family ?? "unknown"}`);
    lines.push(`- current procedure_title: ${procedure?.title_guess ?? "null"}`);
    lines.push(`- cullen_evidence_status: ${coverageEntry?.cullen_evidence_status ?? "none"}`);
    lines.push(`- alignment_status: ${coverageEntry?.alignment_status ?? "no_alignment_signal"}`);
    lines.push(`- validation_status: ${coverageEntry?.validation_status ?? "no_validation_checks"}`);
    lines.push(`- final_confidence: ${coverageEntry?.final_confidence ?? "needs_review"}`);
    lines.push(`- blocking_reason: ${coverageEntry?.blocking_reason ?? "none"}`);
    lines.push(`- matched_cullen_anchors: ${acceptedAnchors.map((anchor) => anchor.cullen_proc_id).join(", ") || "none"}`);
    lines.push(`- omitted_noisy_candidate_count: ${item.omitted_noisy_candidate_count ?? 0}`);
    lines.push("");
    lines.push(...renderClaimSection("Accepted candidate claims", acceptedClaims));
    lines.push("### Accepted candidate anchors", "");
    if (!acceptedAnchors.length) {
      lines.push("- none", "");
    } else {
      for (const anchor of acceptedAnchors) {
        lines.push(`- ${anchor.cullen_proc_id}: ${anchor.english_title}`);
        lines.push(`  procedure_family: ${anchor.procedure_family}`);
        lines.push(`  chunk_ids: ${(anchor.chunk_ids ?? []).join(", ") || "none"}`);
        lines.push(`  claim_ids: ${(anchor.claim_ids ?? []).join(", ") || "none"}`);
        lines.push(`  key_constants: ${(anchor.key_constants ?? []).join(", ") || "none"}`);
        lines.push(`  operation_skeleton: ${(anchor.operation_skeleton ?? []).join(" | ") || "none"}`);
        lines.push(`  anchor_confidence: ${anchor.anchor_confidence}`);
        lines.push(`  anchor_notes: ${anchor.anchor_notes ?? ""}`);
        lines.push("");
      }
    }
    lines.push(...renderClaimSection("Top noisy candidates", topNoisyClaims));
    lines.push(...renderClaimSection("Generic term only candidates", genericOnlyClaims));
    lines.push("### Human decision", "");
    lines.push("human_expected_family:");
    lines.push("accept_claim_ids:");
    lines.push("reject_claim_ids:");
    lines.push("notes:");
    lines.push("");
  }

  return `${lines.join("\n")}\n`;
}

async function main() {
  const config = await readPipelineConfig();
  const chunksPayload = await readJson(config.inputs.cullen.artifacts.chunks);
  const claimsPayload = await readJson(config.inputs.cullen.artifacts.claims);
  const sourceSpansPayload = await readJson(`${config.outputs.dir}/source_spans.json`);
  const procedurePayload = await readJson(`${config.outputs.dir}/procedure_IR.json`);
  const validationReport = await readJson(`${config.outputs.dir}/validation_report.json`);
  const auditReport = await readJson(`${config.outputs.dir}/cullen-audit-report.json`);
  const benchmarkConfig = await readJson("config/cullen-mini-gold-benchmark.json");
  const existingSifenCandidateMap = await maybeReadJson(SIFEN_TARGET_FAMILY_CANDIDATE_PATH);

  const strictClaims = buildStrictClaimBank(claimsPayload);
  const strictClaimsById = new Map(strictClaims.map((claim) => [claim.claim_id, claim]));
  const termbank = buildTermBank(strictClaims, validationReport);
  const procedureBank = buildProcedureBank(strictClaims, chunksPayload, termbank);
  const procedureInventoryPayload = buildProcedureInventory({
    chunks: chunksPayload.chunks ?? [],
  });
  const initialProcedureAnchorPayload = buildProcedureAnchorSet({
    claims: strictClaims,
    chunks: chunksPayload.chunks ?? [],
    procedureBank,
    rawClaims: claimsPayload.claims ?? [],
  });
  const initialCoverageMatrix = buildCoverageMatrix(
    sourceSpansPayload,
    strictClaims,
    strictClaimsById,
    procedureBank,
    initialProcedureAnchorPayload.items ?? [],
    procedurePayload,
    validationReport,
    benchmarkConfig,
    termbank,
  );
  const procedureAnchorPayload = enrichProcedureAnchorSet(
    initialProcedureAnchorPayload,
    initialCoverageMatrix,
    procedurePayload,
    sourceSpansPayload,
  );
  const coverageMatrix = buildCoverageMatrix(
    sourceSpansPayload,
    strictClaims,
    strictClaimsById,
    procedureBank,
    procedureAnchorPayload.items ?? [],
    procedurePayload,
    validationReport,
    benchmarkConfig,
    termbank,
  );
  const goldCandidates = buildGoldCandidates(benchmarkConfig, coverageMatrix, validationReport);
  const sifenTargetFamilyCandidateMap = buildSifenTargetFamilyCandidateMap(
    sourceSpansPayload,
    procedurePayload,
    validationReport,
    coverageMatrix,
    existingSifenCandidateMap,
  );
  const sifenTargetFamilyReviewPacket = buildSifenTargetFamilyReviewPacket(
    sifenTargetFamilyCandidateMap,
    coverageMatrix,
    procedurePayload,
    procedureAnchorPayload,
  );

  const report = {
    generated_at: new Date().toISOString(),
    scopes: SCOPE_DEFS,
    metrics: {
      CullenTermBank: {
        total_terms: termbank.length,
        santong_terms: termbank.filter((item) => item.system === "santong").length,
        sifen_terms: termbank.filter((item) => item.system === "sifen").length,
        A_direct_terms: termbank.filter((item) => item.evidence_level === "A_direct").length,
      },
      CullenProcedureBank: {
        total_procedures: procedureBank.length,
        santong_procedures: procedureBank.filter((item) => item.system === "santong").length,
        sifen_procedures: procedureBank.filter((item) => item.system === "sifen").length,
        procedures_with_structured_operations: procedureBank.filter((item) => item.supported_operations.length > 0).length,
      },
      CullenProcedureAnchors: {
        total_anchors: procedureAnchorPayload.items?.length ?? 0,
        sifen_anchors: (procedureAnchorPayload.items ?? []).filter((item) => item.system === "sifen").length,
        santong_anchors: (procedureAnchorPayload.items ?? []).filter((item) => item.system === "santong").length,
        anchors_with_source_span_candidates: (procedureAnchorPayload.items ?? []).filter((item) => (item.source_span_candidates ?? []).length > 0).length,
      },
      CullenProcedureInventory: {
        total_procedures: procedureInventoryPayload.items?.length ?? 0,
        chapter_2_count: (procedureInventoryPayload.items ?? []).filter((item) => item.chapter === 2).length,
        chapter_3_count: (procedureInventoryPayload.items ?? []).filter((item) => item.chapter === 3).length,
        chapter_4_count: (procedureInventoryPayload.items ?? []).filter((item) => item.chapter === 4).length,
      },
      CullenClaimBank: {
        total_claims: strictClaims.length,
        ...summarizeCounts(strictClaims, "claim_type"),
        claims_that_can_support_A_confirmed: strictClaims.filter((item) => item.can_support_A_confirmed).length,
      },
      CullenCoverageMatrix: {
        directly_covered_source_spans: coverageMatrix.source_span_coverage.filter((item) => item.coverage_status === "directly_covered").length,
        partially_covered_source_spans: coverageMatrix.source_span_coverage.filter((item) => item.coverage_status === "partially_covered").length,
        context_only_source_spans: coverageMatrix.source_span_coverage.filter((item) => item.coverage_status === "context_only").length,
        not_covered_source_spans: coverageMatrix.source_span_coverage.filter((item) => item.coverage_status === "not_covered").length,
      },
      GoldCandidates: {
        total_candidates: goldCandidates.length,
        by_tested_capability: summarizeCounts(goldCandidates, "tested_capability"),
        candidates_requiring_human_review: goldCandidates.filter((item) => item.recommended_status !== "reviewed_candidate").length,
      },
      ValidationConsistency: {
        validation_report_A_confirmed: validationReport.summary?.cullen_grounding_metrics?.A_confirmed ?? 0,
        audit_A_confirmed: auditReport.validation?.cullen_grounding_metrics?.A_confirmed ?? 0,
        match: (validationReport.summary?.cullen_grounding_metrics?.A_confirmed ?? 0)
          === (auditReport.validation?.cullen_grounding_metrics?.A_confirmed ?? 0),
        A_confirmed_with_unresolved_reference: (validationReport.checks ?? []).filter((item) =>
          item.grounding_status === "A_confirmed"
          && JSON.stringify(item.cullen_grounding?.signature ?? {}).includes("unresolved_reference")
        ).length,
        A_confirmed_with_lexical_count_critical_quantity: (validationReport.checks ?? []).filter((item) =>
          item.grounding_status === "A_confirmed"
          && JSON.stringify(item.cullen_grounding?.signature ?? {}).includes("lexical_count")
        ).length,
      },
    },
  };

  await writeJson(`${config.outputs.dir}/cullen-termbank.json`, {
    generated_at: report.generated_at,
    terms: termbank,
  });
  await writeJson(`${config.outputs.dir}/cullen-procedurebank.json`, {
    generated_at: report.generated_at,
    procedures: procedureBank,
  });
  await writeProcedureInventoryOutputs(procedureInventoryPayload);
  await writeProcedureAnchorOutputs(procedureAnchorPayload);
  await writeJson(`${config.outputs.dir}/cullen-claimbank.json`, {
    generated_at: report.generated_at,
    claims: strictClaims,
  });
  await writeJson(`${config.outputs.dir}/cullen-coverage-matrix.json`, coverageMatrix);
  await writeJson(`${config.outputs.dir}/cullen-gold-candidates.json`, {
    generated_at: report.generated_at,
    candidates: goldCandidates,
  });
  await writeJson(`${config.outputs.dir}/cullen-assimilation-report.json`, report);
  await writeJson(SIFEN_TARGET_FAMILY_CANDIDATE_PATH, sifenTargetFamilyCandidateMap);
  await fs.writeFile(SIFEN_TARGET_FAMILY_REVIEW_PACKET_PATH, sifenTargetFamilyReviewPacket, "utf8");

  console.log(JSON.stringify({
    stage: "assimilate-cullen",
    outputs: [
      `${config.outputs.dir}/cullen-termbank.json`,
      `${config.outputs.dir}/cullen-procedurebank.json`,
      CULLEN_PROCEDURE_INVENTORY_JSON,
      CULLEN_PROCEDURE_INVENTORY_MD,
      CULLEN_PROCEDURE_ANCHOR_JSON,
      CULLEN_PROCEDURE_ANCHOR_MD,
      `${config.outputs.dir}/cullen-claimbank.json`,
      `${config.outputs.dir}/cullen-coverage-matrix.json`,
      `${config.outputs.dir}/cullen-gold-candidates.json`,
      `${config.outputs.dir}/cullen-assimilation-report.json`,
      SIFEN_TARGET_FAMILY_CANDIDATE_PATH,
      SIFEN_TARGET_FAMILY_REVIEW_PACKET_PATH,
    ],
    metrics: report.metrics,
  }, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
