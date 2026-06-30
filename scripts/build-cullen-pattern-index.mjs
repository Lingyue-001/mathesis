import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";

const BREAKDOWN_PATH = "tmp/procedure-ir/cullen-ch3-chunk-拆解.json";
const CHUNKS_PATH = "tmp/procedure-ir/cullen-ch3-chunks.json";
const TMP_INDEX_PATH = "tmp/procedure-ir/cullen-ch3-algorithm-comparison-index.json";
const TMP_REPORT_PATH = "tmp/procedure-ir/cullen-ch3-algorithm-comparison-index.md";
const STATIC_INDEX_PATH = "static/procedure-ir/cullen-ch3-algorithm-comparison.json";

const HAN_NUMERAL = "〇零一二三四五六七八九十百千萬万兩两半";
const PUNCT_BOUNDARY = "，。；：、,.;:\\n";
const SPAN = `[^${PUNCT_BOUNDARY}]+`;
const SHORT_SPAN = `[^${PUNCT_BOUNDARY}]{1,36}`;

const STOP_TERMS = new Set([
  "術",
  "術曰",
  "推",
  "置",
  "加",
  "以",
  "之",
  "也",
  "其",
  "為",
  "得一",
  "一",
]);

const IMPORTANT_SINGLE_TERMS = new Set(["餘", "除"]);

const CHANNEL_RULES = [
  {
    id: "lunar_phase",
    label: "lunar phase",
    terms: ["朔", "弦", "望", "晦", "合朔", "月"],
  },
  {
    id: "lodge_degree",
    label: "lodge / du / parts",
    terms: ["宿", "星", "度", "分", "宿次"],
  },
  {
    id: "calendar_cycle",
    label: "calendar cycle",
    terms: ["章", "蔀", "紀", "元", "歲", "年"],
  },
  {
    id: "solar_terms",
    label: "solar terms",
    terms: ["中", "節", "氣", "冬至", "夏至"],
  },
  {
    id: "day_count",
    label: "day count",
    terms: ["日", "日數", "朔日", "大餘", "小餘"],
  },
  {
    id: "remainder_modulus",
    label: "remainder / modulus",
    terms: ["餘", "法", "滿", "不滿", "除去", "分"],
  },
  {
    id: "sexagenary_count",
    label: "sexagenary counting",
    terms: ["甲子", "六十", "命之", "筭盡"],
  },
  {
    id: "eclipse",
    label: "eclipse",
    terms: ["食", "月食", "日食"],
  },
];

const OPERATION_PATTERNS = [
  {
    id: "target.tui_shu_yue",
    family: "procedure_target",
    op: "target",
    description: "Procedure target introduced by 推...術曰",
    regex: new RegExp(`推(?<target>.+?)術曰`, "gu"),
  },
  {
    id: "target.tui_before_comma",
    family: "procedure_target",
    op: "target",
    description: "Procedure target introduced by 推... before the first comma",
    regex: new RegExp(`推(?<target>[^${PUNCT_BOUNDARY}]{2,28})(?=[，,])`, "gu"),
  },
  {
    id: "op.set.zhi",
    family: "procedure_operation",
    op: "set",
    description: "Set out an initial quantity with 置",
    regex: new RegExp(`置(?<input>${SPAN})`, "gu"),
  },
  {
    id: "op.add.jia",
    family: "procedure_operation",
    op: "add",
    description: "Add an explicit quantity with 加",
    regex: new RegExp(`加(?<parameter>${SPAN})`, "gu"),
  },
  {
    id: "op.subtract.jian",
    family: "procedure_operation",
    op: "subtract",
    description: "Subtract or remove a quantity with 減 / 去",
    regex: new RegExp(`(?:減|去)(?<parameter>${SPAN})`, "gu"),
  },
  {
    id: "op.multiply.yi_cheng_zhi",
    family: "procedure_operation",
    op: "multiply",
    description: "Multiply by a parameter with 以...乘之",
    regex: new RegExp(`以(?<parameter>${SHORT_SPAN}?)乘之`, "gu"),
  },
  {
    id: "op.fill_divide.man_de_yi",
    family: "procedure_operation",
    op: "fill_divide",
    description: "Take one quotient whenever the divisor is filled: 滿...得一",
    regex: new RegExp(`滿(?<parameter>${SHORT_SPAN}?)得一`, "gu"),
  },
  {
    id: "op.divide.yi_chu_zhi",
    family: "procedure_operation",
    op: "divide",
    description: "Divide or cast out by a parameter with 以...除之",
    regex: new RegExp(`以(?<parameter>${SHORT_SPAN}?)除之`, "gu"),
  },
  {
    id: "op.remove_modulus.chu_qu_zhi",
    family: "procedure_operation",
    op: "remove_modulus",
    description: "Remove a modulus with 除去之",
    regex: new RegExp(`以(?<parameter>${SHORT_SPAN}?)除去之`, "gu"),
  },
  {
    id: "op.name_result.ming_wei",
    family: "procedure_operation",
    op: "name_result",
    description: "Name a quotient or result with 名為 / 名之曰",
    regex: new RegExp(`(?:名為|名之曰)(?<output>${SHORT_SPAN})`, "gu"),
  },
  {
    id: "op.define.wei_zhi",
    family: "semantic_relation",
    op: "define",
    description: "Definition or naming expression with 謂之",
    regex: new RegExp(`謂之(?<output>${SHORT_SPAN})`, "gu"),
  },
  {
    id: "op.output.ji_ye",
    family: "procedure_operation",
    op: "output",
    description: "Final result introduced by 即...也",
    regex: new RegExp(`即(?<output>${SHORT_SPAN}?)也`, "gu"),
  },
  {
    id: "op.name_remainder.bu_man_wei",
    family: "procedure_operation",
    op: "name_remainder",
    description: "Name a remainder with 不滿為",
    regex: new RegExp(`不滿為(?<output>${SHORT_SPAN})`, "gu"),
  },
  {
    id: "op.name_remainder.qi_yu_wei",
    family: "procedure_operation",
    op: "name_remainder",
    description: "Name a remainder with 其餘為",
    regex: new RegExp(`其餘為(?<output>${SHORT_SPAN})`, "gu"),
  },
  {
    id: "op.count.yi_ming_zhi",
    family: "procedure_operation",
    op: "count",
    description: "Count through a cycle with 以...命之",
    regex: new RegExp(`以(?<parameter>${SHORT_SPAN}?)命之`, "gu"),
  },
  {
    id: "op.seek.qiu",
    family: "procedure_operation",
    op: "seek",
    description: "Seek or derive a requested result with 求",
    regex: new RegExp(`求(?<output>${SHORT_SPAN})`, "gu"),
  },
  {
    id: "op.judge.yi_shang",
    family: "procedure_operation",
    op: "judge",
    description: "Threshold judgment with ...以上",
    regex: new RegExp(`(?<input>${SHORT_SPAN}?)以上`, "gu"),
  },
];

async function readJson(filePath) {
  return JSON.parse(await readFile(filePath, "utf8"));
}

async function writeJson(filePath, value) {
  await mkdir(path.dirname(filePath), { recursive: true });
  await writeFile(filePath, `${JSON.stringify(value, null, 2)}\n`, "utf8");
}

async function writeText(filePath, value) {
  await mkdir(path.dirname(filePath), { recursive: true });
  await writeFile(filePath, value, "utf8");
}

function normalizeWhitespace(value) {
  return String(value ?? "").replace(/\s+/gu, "");
}

function unique(values) {
  return [...new Set(values.filter(Boolean))];
}

function sortedUnique(values) {
  return unique(values).sort((a, b) => a.localeCompare(b));
}

function countBy(items, keyFn) {
  const counts = new Map();
  for (const item of items) {
    const key = keyFn(item);
    if (!key) continue;
    counts.set(key, (counts.get(key) ?? 0) + 1);
  }
  return Object.fromEntries([...counts.entries()].sort((a, b) => b[1] - a[1]));
}

function cleanRoleValue(value) {
  return normalizeWhitespace(value)
    .replace(/^[以其為之]+/u, "")
    .replace(/[也之]+$/u, "")
    .replace(/[()[\]（）]/gu, "")
    .trim();
}

function isUsefulTerm(value) {
  const text = cleanRoleValue(value);
  return (text.length >= 2 || IMPORTANT_SINGLE_TERMS.has(text))
    && !STOP_TERMS.has(text)
    && !isNumberTerm(text)
    && !/^[曰也之其以為]+$/u.test(text);
}

function isNumberTerm(value) {
  return new RegExp(`^[${HAN_NUMERAL}\\d]+(?:之[${HAN_NUMERAL}\\d]+)?$`, "u").test(cleanRoleValue(value));
}

function extractNumberConstants(text) {
  const constants = [];
  const re = new RegExp(`[${HAN_NUMERAL}]{2,}(?:之[${HAN_NUMERAL}]+)?|\\d+(?:\\.\\d+)?`, "gu");
  for (const match of normalizeWhitespace(text).matchAll(re)) {
    constants.push(match[0]);
  }
  return sortedUnique(constants.filter((item) => item !== "十一" || /十一月/u.test(text)));
}

function buildTermLexicon(breakdownChunks) {
  const terms = [];
  for (const chunk of breakdownChunks) {
    for (const term of chunk.terms ?? []) {
      if (isUsefulTerm(term.text)) {
        terms.push({
          text: cleanRoleValue(term.text),
          term_id: term.term_id ?? null,
          type: term.type ?? null,
          en: term.en ?? null,
          evidence_chunk_id: chunk.chunk_id,
        });
      }
    }
    for (const step of chunk.steps ?? []) {
      for (const value of [step.input, step.parameter, step.output]) {
        for (const part of splitRoleField(value)) {
          if (isUsefulTerm(part)) {
            terms.push({
              text: cleanRoleValue(part),
              term_id: null,
              type: "STEP_ROLE",
              en: null,
              evidence_chunk_id: chunk.chunk_id,
            });
          }
        }
      }
    }
  }

  const byText = new Map();
  for (const term of terms) {
    const existing = byText.get(term.text) ?? { ...term, evidence_chunk_ids: [] };
    existing.evidence_chunk_ids = unique([...existing.evidence_chunk_ids, term.evidence_chunk_id]);
    byText.set(term.text, existing);
  }

  return [...byText.values()].sort((a, b) => b.text.length - a.text.length || a.text.localeCompare(b.text));
}

function splitRoleField(value) {
  return String(value ?? "")
    .split(/[;,；，]/u)
    .flatMap((part) => part.split(/>=|<=|=|>|</u))
    .map((part) => part
      .replace(/^(presence|value)\((.+)\)$/u, "$2")
      .replace(/^(quotient|remainder)=/u, "")
      .replace(/^(start|cycle|advance|return)=/u, "")
      .trim())
    .filter(Boolean);
}

function matchOperations(text) {
  const normalized = normalizeWhitespace(text);
  const matches = [];
  const seen = new Set();

  for (const pattern of OPERATION_PATTERNS) {
    pattern.regex.lastIndex = 0;
    for (const match of normalized.matchAll(pattern.regex)) {
      const role_bindings = Object.fromEntries(
        Object.entries(match.groups ?? {})
          .filter(([, value]) => value)
          .map(([key, value]) => [key, cleanRoleValue(value)])
          .filter(([, value]) => value)
      );
      const key = `${pattern.id}|${match.index}|${match[0]}`;
      if (seen.has(key)) continue;
      seen.add(key);
      matches.push({
        pattern_id: pattern.id,
        family: pattern.family,
        op: pattern.op,
        description: pattern.description,
        matched_text: match[0],
        match_index: match.index,
        role_bindings,
      });
    }
  }

  return matches.sort((a, b) => a.match_index - b.match_index || a.matched_text.length - b.matched_text.length);
}

function findLexiconHits(text, lexicon) {
  const normalized = normalizeWhitespace(text);
  const hits = [];
  for (const term of lexicon) {
    const index = normalized.indexOf(term.text);
    if (index === -1) continue;
    hits.push({
      text: term.text,
      term_id: term.term_id,
      type: term.type,
      en: term.en,
      index,
    });
  }
  return hits.sort((a, b) => a.index - b.index || b.text.length - a.text.length);
}

function detectChannels(text, terms) {
  const haystack = `${normalizeWhitespace(text)} ${terms.join(" ")}`;
  return CHANNEL_RULES
    .filter((rule) => rule.terms.some((term) => haystack.includes(term)))
    .map((rule) => ({ id: rule.id, label: rule.label }));
}

function operationSequence(matches) {
  return matches
    .filter((match) => match.family === "procedure_operation")
    .map((match) => match.op);
}

function roleTermsFromMatches(matches) {
  const terms = [];
  for (const match of matches) {
    for (const value of Object.values(match.role_bindings ?? {})) {
      if (isUsefulTerm(value)) terms.push(cleanRoleValue(value));
    }
  }
  return sortedUnique(terms);
}

function namedOutputs(matches) {
  return sortedUnique(
    matches
      .flatMap((match) => [match.role_bindings?.output])
      .filter(isUsefulTerm)
      .map(cleanRoleValue)
  );
}

function targetClasses(text, channels, terms) {
  const haystack = `${normalizeWhitespace(text)} ${terms.join(" ")}`;
  const classes = [];
  const channelIds = new Set(channels.map((channel) => channel.id));
  if (channelIds.has("lunar_phase") && channelIds.has("lodge_degree")) classes.push("lunar_lodge_position");
  if (channelIds.has("calendar_cycle") && channelIds.has("day_count")) classes.push("calendar_accumulation");
  if (channelIds.has("solar_terms")) classes.push("solar_term_model");
  if (channelIds.has("eclipse")) classes.push("eclipse_constant");
  if (/閏/u.test(haystack)) classes.push("intercalation");
  if (/月食|日食|食/u.test(haystack)) classes.push("eclipse");
  if (/宿次|所入宿/u.test(haystack)) classes.push("lodge_casting");
  return sortedUnique(classes);
}

function detectMotifs(matches) {
  const sequence = operationSequence(matches);
  const motifs = [];
  const hasParameter = (op, pattern) => matches.some((match) =>
    match.op === op && pattern.test(match.role_bindings?.parameter ?? match.matched_text ?? "")
  );

  if (hasOrderedSubsequence(sequence, ["set", "add", "add", "divide"])) motifs.push("set_add_add_divide");
  if (sequence.includes("fill_divide") && sequence.includes("name_remainder")) motifs.push("quotient_remainder");
  if (hasOrderedSubsequence(sequence, ["multiply", "fill_divide"])) motifs.push("multiply_then_modulus");
  if (sequence.includes("remove_modulus")) motifs.push("remove_modulus_remainder");
  if (sequence.includes("count")) motifs.push("cycle_counting");
  if (hasParameter("divide", /宿次/u)) motifs.push("cast_out_by_lodge_sequence");
  if (hasParameter("add", /^度/u) && hasParameter("add", /^分/u)) motifs.push("add_du_and_parts");
  if (sequence.filter((op) => op === "name_result").length >= 2) motifs.push("naming_result_cluster");
  if (sequence.includes("name_remainder")) motifs.push("remainder_naming");
  if (sequence.includes("output")) motifs.push("final_output_formula");
  return sortedUnique(motifs);
}

function motifEvidence(motifs, matches) {
  const sequence = operationSequence(matches);
  const descriptions = {
    set_add_add_divide: "operation_sequence contains set -> add -> add -> divide",
    quotient_remainder: "operation_sequence contains fill_divide and name_remainder",
    multiply_then_modulus: "operation_sequence contains multiply -> fill_divide",
    remove_modulus_remainder: "operation_sequence contains remove_modulus",
    cycle_counting: "operation_sequence contains count",
    cast_out_by_lodge_sequence: "a divide operation has parameter 宿次",
    add_du_and_parts: "two add operations separately use 度... and 分... parameters",
    naming_result_cluster: "two or more name_result operations occur",
    remainder_naming: "operation_sequence contains name_remainder",
    final_output_formula: "operation_sequence contains output",
  };
  return motifs.map((motif) => ({
    motif,
    rule: descriptions[motif] ?? "derived from operation matches",
    operation_sequence: sequence,
  }));
}

function hasOrderedSubsequence(sequence, motif) {
  let index = 0;
  for (const op of sequence) {
    if (op === motif[index]) index += 1;
    if (index === motif.length) return true;
  }
  return false;
}

function buildChunkFeature(chunk, lexicon, manualChunkById) {
  const source_text_zh = chunk.source_text_zh ?? "";
  const manualChunk = manualChunkById.get(chunk.id);
  const isProcChunk = Boolean((chunk.procedure_ids ?? []).length);
  const matches = isProcChunk ? matchOperations(source_text_zh) : [];
  const lexiconHits = findLexiconHits(source_text_zh, lexicon);
  const manualTerms = (manualChunk?.terms ?? [])
    .map((term) => ({
      text: cleanRoleValue(term.text),
      type: term.type ?? null,
      term_id: term.term_id ?? null,
      en: term.en ?? null,
    }))
    .filter((term) => isUsefulTerm(term.text));
  const manualRelations = (manualChunk?.relations ?? []).map((relation) => ({
    subject: relation.subject,
    relation: relation.relation,
    object: relation.object,
    anchor: relation.anchor ?? null,
  }));
  const manualSteps = (manualChunk?.steps ?? []).map((step) => ({
    order: step.order,
    op: step.op,
    phrase: step.phrase,
    input: step.input,
    parameter: step.parameter,
    output: step.output,
  }));
  const terms = sortedUnique([
    ...manualTerms.map((term) => term.text),
    ...lexiconHits.map((hit) => hit.text),
    ...roleTermsFromMatches(matches),
  ].filter(isUsefulTerm));
  const channels = detectChannels(source_text_zh, terms);
  const constants = extractNumberConstants(source_text_zh);
  const sequence = operationSequence(matches);
  const motifs = detectMotifs(matches);
  const outputs = namedOutputs(matches);

  return {
    chunk_id: chunk.id,
    chunk_type: manualChunk?.chunk_type ?? manualChunk?.type ?? (isProcChunk ? "procedure" : "source_chunk"),
    annotation_source: manualChunk ? "manual_breakdown" : "machine_extracted",
    has_manual_steps: Boolean((manualChunk?.steps ?? []).length),
    manual_step_count: (manualChunk?.steps ?? []).length,
    manual_term_count: (manualChunk?.terms ?? []).length,
    manual_relation_count: (manualChunk?.relations ?? []).length,
    manual_terms: manualTerms,
    manual_relations: manualRelations,
    manual_steps: manualSteps,
    section_path: chunk.section_path ?? [],
    heading: chunk.heading ?? "",
    procedure_ids: chunk.procedure_ids ?? [],
    procedure_titles: chunk.procedure_titles ?? [],
    unit_ids: chunk.unit_ids ?? [],
    source_text_zh,
    english_text: chunk.english_text ?? "",
    is_procedure_like: isProcChunk,
    operation_sequence: sequence,
    operation_matches: matches,
    target_classes: targetClasses(source_text_zh, channels, terms),
    motifs,
    motif_evidence: motifEvidence(motifs, matches),
    quantity_channels: channels,
    constants,
    terms,
    named_outputs: outputs,
    pattern_ids: sortedUnique(matches.map((match) => match.pattern_id)),
    coverage_summary: {
      operation_count: sequence.length,
      term_count: terms.length,
      channel_count: channels.length,
      motif_count: motifs.length,
      constant_count: constants.length,
    },
  };
}

function lcsLength(a, b) {
  const dp = Array.from({ length: a.length + 1 }, () => Array(b.length + 1).fill(0));
  for (let i = 1; i <= a.length; i += 1) {
    for (let j = 1; j <= b.length; j += 1) {
      dp[i][j] = a[i - 1] === b[j - 1]
        ? dp[i - 1][j - 1] + 1
        : Math.max(dp[i - 1][j], dp[i][j - 1]);
    }
  }
  return dp[a.length][b.length];
}

function intersection(a, b) {
  const setB = new Set(b);
  return sortedUnique(a.filter((item) => setB.has(item)));
}

function comparableTerms(terms) {
  return terms.filter((term) => term.length >= 2 && !STOP_TERMS.has(term));
}

const AXIS_RULES = [
  {
    id: "operation_skeleton",
    label: "Operation skeleton",
    max_weight: 0.24,
    definition: "Ordered comparison of steps.op extracted from procedure chunks.",
  },
  {
    id: "quantity_flow",
    label: "Quantity flow",
    max_weight: 0.20,
    definition: "Comparison of input/output roles and remainder/date/lodge/calendar channels.",
  },
  {
    id: "parameter_role",
    label: "Parameter role",
    max_weight: 0.18,
    definition: "Comparison of multiplier, divisor, modulus, threshold, and counting-frame roles.",
  },
  {
    id: "target_output_class",
    label: "Target/output class",
    max_weight: 0.18,
    definition: "Comparison of final target class and named output type.",
  },
  {
    id: "surface_wording",
    label: "Surface wording",
    max_weight: 0.08,
    definition: "Phrase-pattern overlap. This is intentionally low weight.",
  },
  {
    id: "term_overlap",
    label: "Term overlap",
    max_weight: 0.12,
    definition: "Shared technical terms. This is low-to-medium weight.",
  },
];

const AXIS_MAX_WEIGHT = Object.fromEntries(AXIS_RULES.map((axis) => [axis.id, axis.max_weight]));
const HIGH_WEIGHT_AXES = new Set(["operation_skeleton", "quantity_flow", "parameter_role", "target_output_class"]);

function axisLevel(matchedCount, possibleCount) {
  if (!matchedCount || !possibleCount) return "none";
  const ratio = matchedCount / possibleCount;
  if (ratio >= 0.67) return "strong";
  if (ratio >= 0.34) return "partial";
  return "weak";
}

function axisContribution(axisId, matchedCount, possibleCount) {
  if (!matchedCount || !possibleCount) return 0;
  const maxWeight = AXIS_MAX_WEIGHT[axisId] ?? 0;
  return Number(Math.min(maxWeight, (matchedCount / possibleCount) * maxWeight).toFixed(3));
}

function makeAxis(axisId, matchedCount, possibleCount, details = []) {
  return {
    axis: axisId,
    label: AXIS_RULES.find((axis) => axis.id === axisId)?.label ?? axisId,
    level: axisLevel(matchedCount, possibleCount),
    matched_count: matchedCount,
    possible_count: possibleCount,
    weight: AXIS_MAX_WEIGHT[axisId] ?? 0,
    contribution: axisContribution(axisId, matchedCount, possibleCount),
    details,
  };
}

function sourceForMatch(chunk, match, stepOrder = null) {
  return {
    chunk_id: chunk.chunk_id,
    step_order: stepOrder,
    phrase: match?.matched_text ?? "",
    op: match?.op ?? "",
    input: match?.role_bindings?.input ?? null,
    parameter: match?.role_bindings?.parameter ?? null,
    output: match?.role_bindings?.output ?? null,
    target: match?.role_bindings?.target ?? null,
  };
}

function lcsOperationPairsForChunks(a, b) {
  const aOps = a.operation_matches.filter((match) => match.family === "procedure_operation");
  const bOps = b.operation_matches.filter((match) => match.family === "procedure_operation");
  const dp = Array.from({ length: aOps.length + 1 }, () => Array(bOps.length + 1).fill(0));

  for (let i = aOps.length - 1; i >= 0; i -= 1) {
    for (let j = bOps.length - 1; j >= 0; j -= 1) {
      dp[i][j] = aOps[i].op === bOps[j].op
        ? dp[i + 1][j + 1] + 1
        : Math.max(dp[i + 1][j], dp[i][j + 1]);
    }
  }

  const pairs = [];
  let i = 0;
  let j = 0;
  while (i < aOps.length && j < bOps.length) {
    if (aOps[i].op === bOps[j].op) {
      pairs.push({
        op: aOps[i].op,
        a,
        b,
        a_match: aOps[i],
        b_match: bOps[j],
        a_index: i,
        b_index: j,
      });
      i += 1;
      j += 1;
    } else if (dp[i + 1][j] >= dp[i][j + 1]) {
      i += 1;
    } else {
      j += 1;
    }
  }

  return { pairs, aOps, bOps };
}

function roleValue(match, role) {
  return cleanRoleValue(match?.role_bindings?.[role] ?? "");
}

function parameterRoleName(match) {
  if (!match) return null;
  if (match.op === "multiply") return "multiplier";
  if (match.op === "fill_divide" || match.op === "divide") return "divisor";
  if (match.op === "remove_modulus") return "modulus";
  if (match.op === "judge") return "threshold";
  if (match.op === "count") return "counting_frame";
  if (match.op === "add") return "increment";
  if (match.op === "subtract") return "decrement";
  return match.role_bindings?.parameter ? "parameter" : null;
}

function detailForPair(type, pair, extra = {}) {
  return {
    type,
    ...extra,
    a: sourceForMatch(pair.a, pair.a_match, pair.a_index + 1),
    b: sourceForMatch(pair.b, pair.b_match, pair.b_index + 1),
  };
}

function valueEvidenceDetail(type, value, chunkA, chunkB, extra = {}) {
  return {
    type,
    value,
    ...extra,
    a: { chunk_id: chunkA.chunk_id, phrase: value },
    b: { chunk_id: chunkB.chunk_id, phrase: value },
  };
}

function compareOperationSkeleton(a, b, opAlignment) {
  const details = opAlignment.pairs.map((pair) => detailForPair("matched_operation", pair, { op: pair.op }));
  return makeAxis(
    "operation_skeleton",
    opAlignment.pairs.length,
    Math.max(opAlignment.aOps.length, opAlignment.bOps.length, 1),
    details
  );
}

function inputOutputRoleTerms(chunk) {
  return sortedUnique(
    chunk.operation_matches
      .flatMap((match) => [match.role_bindings?.input, match.role_bindings?.output])
      .filter(isUsefulTerm)
      .map(cleanRoleValue)
  );
}

function compareQuantityFlow(a, b) {
  const aChannels = a.quantity_channels.map((item) => item.id);
  const bChannels = b.quantity_channels.map((item) => item.id);
  const aRoleTerms = inputOutputRoleTerms(a);
  const bRoleTerms = inputOutputRoleTerms(b);
  const sharedChannels = intersection(aChannels, bChannels);
  const sharedRoleTerms = intersection(aRoleTerms, bRoleTerms);
  const possible = unique([...aChannels, ...bChannels, ...aRoleTerms, ...bRoleTerms]).length;
  const details = [
    ...sharedChannels.map((value) => valueEvidenceDetail("shared_quantity_channel", value, a, b)),
    ...sharedRoleTerms.map((value) => valueEvidenceDetail("shared_input_output_role", value, a, b)),
  ];
  return makeAxis("quantity_flow", details.length, Math.max(possible, 1), details);
}

function compareParameterRole(a, b, opAlignment) {
  const possiblePairs = opAlignment.pairs.filter((pair) => parameterRoleName(pair.a_match) || parameterRoleName(pair.b_match));
  const details = [];
  for (const pair of possiblePairs) {
    const aRole = parameterRoleName(pair.a_match);
    const bRole = parameterRoleName(pair.b_match);
    const aValue = roleValue(pair.a_match, "parameter") || roleValue(pair.a_match, "input");
    const bValue = roleValue(pair.b_match, "parameter") || roleValue(pair.b_match, "input");
    if (aRole === bRole && aValue && aValue === bValue) {
      details.push(detailForPair("same_parameter_role", pair, { role: aRole, value: aValue }));
    }
  }
  return makeAxis("parameter_role", details.length, Math.max(possiblePairs.length, 1), details);
}

function compareTargetOutputClass(a, b) {
  const aValues = sortedUnique([...a.target_classes, ...a.named_outputs]);
  const bValues = sortedUnique([...b.target_classes, ...b.named_outputs]);
  const shared = intersection(aValues, bValues);
  const possible = unique([...aValues, ...bValues]).length;
  return makeAxis(
    "target_output_class",
    shared.length,
    Math.max(possible, 1),
    shared.map((value) => valueEvidenceDetail("shared_target_or_output", value, a, b))
  );
}

function compareSurfaceWording(a, b) {
  const shared = intersection(a.pattern_ids, b.pattern_ids);
  const possible = unique([...a.pattern_ids, ...b.pattern_ids]).length;
  return makeAxis(
    "surface_wording",
    shared.length,
    Math.max(possible, 1),
    shared.map((value) => valueEvidenceDetail("shared_surface_pattern", value, a, b))
  );
}

function compareTermOverlap(a, b) {
  const shared = intersection(comparableTerms(a.terms), comparableTerms(b.terms))
    .filter((term) => !/^[骞存湀鏃ュ害鍒嗙椁樻硶]+$/u.test(term))
    .slice(0, 18);
  const possible = unique([...comparableTerms(a.terms), ...comparableTerms(b.terms)]).length;
  return makeAxis(
    "term_overlap",
    shared.length,
    Math.max(possible, 1),
    shared.map((value) => valueEvidenceDetail("shared_term", value, a, b))
  );
}

function compareDifferences(a, b, opAlignment) {
  const pairedA = new Set(opAlignment.pairs.map((pair) => pair.a_index));
  const pairedB = new Set(opAlignment.pairs.map((pair) => pair.b_index));
  const aOnly = opAlignment.aOps
    .map((match, index) => ({ match, index }))
    .filter((item) => !pairedA.has(item.index));
  const bOnly = opAlignment.bOps
    .map((match, index) => ({ match, index }))
    .filter((item) => !pairedB.has(item.index));
  const differentParameters = [];
  const differentOutputs = [];

  for (const pair of opAlignment.pairs) {
    const aParam = roleValue(pair.a_match, "parameter");
    const bParam = roleValue(pair.b_match, "parameter");
    if ((aParam || bParam) && aParam !== bParam) {
      differentParameters.push(detailForPair("different_parameter", pair, { a_value: aParam || null, b_value: bParam || null }));
    }
    const aOutput = roleValue(pair.a_match, "output") || roleValue(pair.a_match, "target");
    const bOutput = roleValue(pair.b_match, "output") || roleValue(pair.b_match, "target");
    if ((aOutput || bOutput) && aOutput !== bOutput) {
      differentOutputs.push(detailForPair("different_output", pair, { a_value: aOutput || null, b_value: bOutput || null }));
    }
  }

  return {
    a_only_operations: aOnly.map((item) => sourceForMatch(a, item.match, item.index + 1)),
    b_only_operations: bOnly.map((item) => sourceForMatch(b, item.match, item.index + 1)),
    different_parameters: differentParameters,
    different_outputs: differentOutputs,
    unmatched_phrases: [
      ...aOnly.map((item) => ({ side: "A", chunk_id: a.chunk_id, phrase: item.match.matched_text, op: item.match.op })),
      ...bOnly.map((item) => ({ side: "B", chunk_id: b.chunk_id, phrase: item.match.matched_text, op: item.match.op })),
    ],
  };
}

function classifyComparison(score, axes) {
  const highWeightMatches = axes.filter((axis) =>
    HIGH_WEIGHT_AXES.has(axis.axis) && (axis.level === "strong" || axis.level === "partial")
  ).length;
  const hasRequiredSemanticAxis = axes.some((axis) =>
    (axis.axis === "quantity_flow" || axis.axis === "target_output_class")
    && axis.level !== "none"
  );
  const onlySurfaceOrTerm = axes.some((axis) => axis.matched_count > 0)
    && axes.every((axis) => axis.matched_count === 0 || axis.axis === "surface_wording" || axis.axis === "term_overlap");

  if (score >= 0.7 && highWeightMatches >= 2 && hasRequiredSemanticAxis && !onlySurfaceOrTerm) return "strong";
  if (score >= 0.4 && !onlySurfaceOrTerm) return "partial";
  return "weak";
}

function compareChunksLegacy(a, b) {
  const evidence = [];
  const opLcs = lcsLength(a.operation_sequence, b.operation_sequence);
  const opNorm = opLcs / Math.max(a.operation_sequence.length, b.operation_sequence.length, 1);
  if (opLcs >= 2 && opNorm >= 0.35) {
    evidence.push({
      family: "operation_sequence",
      weight: Math.min(0.14, opNorm * 0.14),
      label: "shared operation order",
      values: [`lcs=${opLcs}`, `similarity=${opNorm.toFixed(2)}`],
    });
  }

  const sharedMotifs = intersection(a.motifs, b.motifs);
  if (sharedMotifs.length) {
    evidence.push({
      family: "motif",
      weight: Math.min(0.26, sharedMotifs.length * 0.13),
      label: "shared computational motif",
      values: sharedMotifs,
    });
  }

  const sharedChannels = intersection(
    a.quantity_channels.map((item) => item.id),
    b.quantity_channels.map((item) => item.id)
  );
  if (sharedChannels.length) {
    evidence.push({
      family: "quantity_channel",
      weight: Math.min(0.18, sharedChannels.length * 0.06),
      label: "shared quantity channel",
      values: sharedChannels,
    });
  }

  const sharedTargetClasses = intersection(a.target_classes, b.target_classes);
  if (sharedTargetClasses.length) {
    evidence.push({
      family: "target_class",
      weight: Math.min(0.18, sharedTargetClasses.length * 0.12),
      label: "shared target class",
      values: sharedTargetClasses,
    });
  }

  const sharedConstants = intersection(a.constants, b.constants)
    .filter((value) => value.length > 1 && value !== "十二");
  if (sharedConstants.length) {
    evidence.push({
      family: "constant",
      weight: Math.min(0.1, sharedConstants.length * 0.04),
      label: "shared constants",
      values: sharedConstants,
    });
  }

  const sharedTerms = intersection(comparableTerms(a.terms), comparableTerms(b.terms))
    .filter((term) => !/^[年月日度分宿餘法]+$/u.test(term))
    .slice(0, 12);
  if (sharedTerms.length) {
    evidence.push({
      family: "term",
      weight: Math.min(0.12, sharedTerms.length * 0.03),
      label: "shared term candidates",
      values: sharedTerms,
    });
  }

  const sharedOutputs = intersection(a.named_outputs, b.named_outputs);
  if (sharedOutputs.length) {
    evidence.push({
      family: "named_output",
      weight: Math.min(0.1, sharedOutputs.length * 0.05),
      label: "shared named outputs",
      values: sharedOutputs,
    });
  }

  const sharedPatterns = intersection(a.pattern_ids, b.pattern_ids);
  if (sharedPatterns.length) {
    evidence.push({
      family: "surface_pattern",
      weight: Math.min(0.12, sharedPatterns.length * 0.035),
      label: "shared surface patterns",
      values: sharedPatterns,
    });
  }

  const nonGenericEvidence = evidence.filter((item) => item.family !== "operation_sequence");
  const score = Number(Math.min(1, evidence.reduce((sum, item) => sum + item.weight, 0)).toFixed(3));
  const isWeakGeneric = nonGenericEvidence.length < 2 || (evidence.length === 1 && evidence[0].family === "operation_sequence");

  return {
    chunk_a: a.chunk_id,
    chunk_b: b.chunk_id,
    score,
    evidence_family_count: evidence.length,
    non_generic_evidence_family_count: nonGenericEvidence.length,
    evidence,
    verdict: score >= 0.46 && !isWeakGeneric
      ? "strong"
      : score >= 0.3 && !isWeakGeneric
        ? "partial"
        : "weak",
  };
}

function compareChunks(a, b) {
  const opAlignment = lcsOperationPairsForChunks(a, b);
  const evidenceAxes = [
    compareOperationSkeleton(a, b, opAlignment),
    compareQuantityFlow(a, b),
    compareParameterRole(a, b, opAlignment),
    compareTargetOutputClass(a, b),
    compareSurfaceWording(a, b),
    compareTermOverlap(a, b),
  ];
  const score = Number(Math.min(1, evidenceAxes.reduce((sum, axis) => sum + axis.contribution, 0)).toFixed(3));
  const verdict = classifyComparison(score, evidenceAxes);

  return {
    chunk_a: a.chunk_id,
    chunk_b: b.chunk_id,
    score,
    evidence_family_count: evidenceAxes.filter((axis) => axis.matched_count > 0).length,
    non_generic_evidence_family_count: evidenceAxes.filter((axis) =>
      axis.matched_count > 0 && axis.axis !== "surface_wording" && axis.axis !== "term_overlap"
    ).length,
    evidence_axes: evidenceAxes,
    differences: compareDifferences(a, b, opAlignment),
    evidence: evidenceAxes
      .filter((axis) => axis.matched_count > 0)
      .map((axis) => ({
        family: axis.axis,
        weight: axis.contribution,
        label: axis.label,
        values: axis.details.map((detail) => detail.value ?? detail.op ?? detail.type).filter(Boolean),
      })),
    verdict,
  };
}

function buildComparisons(features) {
  const candidates = features.filter((chunk) =>
    chunk.is_procedure_like && (chunk.operation_sequence.length >= 2 || chunk.motifs.length)
  );
  const comparisons = [];

  for (let i = 0; i < candidates.length; i += 1) {
    for (let j = i + 1; j < candidates.length; j += 1) {
      const comparison = compareChunks(candidates[i], candidates[j]);
      if (comparison.verdict === "weak") continue;
      comparisons.push(comparison);
    }
  }

  return comparisons
    .sort((a, b) => b.score - a.score || a.chunk_a.localeCompare(b.chunk_a) || a.chunk_b.localeCompare(b.chunk_b))
    .slice(0, 250);
}

function buildChunkNeighbors(features, comparisons) {
  const byId = new Map(features.map((feature) => [feature.chunk_id, []]));
  for (const comparison of comparisons) {
    byId.get(comparison.chunk_a)?.push({
      chunk_id: comparison.chunk_b,
      score: comparison.score,
      verdict: comparison.verdict,
      evidence: comparison.evidence,
    });
    byId.get(comparison.chunk_b)?.push({
      chunk_id: comparison.chunk_a,
      score: comparison.score,
      verdict: comparison.verdict,
      evidence: comparison.evidence,
    });
  }
  return Object.fromEntries(
    [...byId.entries()].map(([chunkId, neighbors]) => [
      chunkId,
      neighbors.sort((a, b) => b.score - a.score).slice(0, 8),
    ])
  );
}

function buildMarkdownReport(index) {
  const byId = new Map(index.chunks.map((chunk) => [chunk.chunk_id, chunk]));
  const lines = [
    "# Cullen Ch3 Algorithm Comparison Index",
    "",
    `- Generated: ${index.generated_at}`,
    `- Chunks scanned: ${index.summary.chunk_count}`,
    `- Manually annotated chunks: ${index.summary.manual_breakdown_chunk_count}`,
    `- Procedure chunks with steps: ${index.summary.manual_step_chunk_count}`,
    `- Chunks with derived motifs: ${index.summary.chunks_with_motifs}`,
    `- Comparisons retained: ${index.summary.comparison_count}`,
    "",
    "## Scoring Evidence",
    "",
    "- Operation skeleton: ordered comparison of extracted steps.op.",
    "- Quantity flow: comparison of input/output roles and remainder/date/lodge/calendar channels.",
    "- Parameter role: comparison of multiplier, divisor, modulus, threshold, and counting-frame roles.",
    "- Target/output class: comparison of final target class and named output type.",
    "- Surface wording: phrase-pattern overlap, low weight.",
    "- Term overlap: shared technical terms, low-to-medium weight.",
    "",
    "Strong requires total score >= 0.70, at least two high-weight axes, at least one of Quantity flow or Target/output class, and cannot be produced by operation order alone.",
    "Partial requires total score >= 0.40 without being only surface/term overlap.",
    "Weak is total score < 0.40, or only surface/term overlap.",
    "",
    "## Top Comparisons",
    "",
  ];

  for (const comparison of index.comparisons.slice(0, 40)) {
    const a = byId.get(comparison.chunk_a);
    const b = byId.get(comparison.chunk_b);
    lines.push(`### ${comparison.score.toFixed(3)} ${comparison.verdict}: ${comparison.chunk_a} ↔ ${comparison.chunk_b}`);
    lines.push(`- A: ${(a?.procedure_ids ?? []).join(", ") || "no Proc"} ${a?.source_text_zh ?? ""}`);
    lines.push(`- B: ${(b?.procedure_ids ?? []).join(", ") || "no Proc"} ${b?.source_text_zh ?? ""}`);
    for (const item of comparison.evidence) {
      lines.push(`- ${item.label}: ${item.values.join(", ")}`);
    }
    lines.push("");
  }

  return `${lines.join("\n")}\n`;
}

function buildIndex(breakdownChunks, sourceArtifact) {
  const sourceChunks = sourceArtifact.chunks ?? [];
  const lexicon = buildTermLexicon(breakdownChunks);
  const manualChunkById = new Map(breakdownChunks.map((chunk) => [chunk.chunk_id, chunk]));
  const chunks = sourceChunks.map((chunk) => buildChunkFeature(chunk, lexicon, manualChunkById));
  const comparisons = buildComparisons(chunks);
  const neighbors_by_chunk = buildChunkNeighbors(chunks, comparisons);

  return {
    generated_at: new Date().toISOString(),
    schema_version: "cullen_ch3_algorithm_comparison_index_v1",
    sources: {
      breakdown_json: BREAKDOWN_PATH,
      chunks_json: CHUNKS_PATH,
      note: "Derived index only. It does not overwrite Cullen text, anchors, claims, or canonical project data.",
    },
    scoring_model: {
      principle: "Six-axis evidence model with source-backed details and negative evidence.",
      retained_verdicts: ["strong", "partial"],
      axes: AXIS_RULES,
      thresholds: {
        strong: "score >= 0.70, at least two high-weight axes match, at least one of quantity_flow or target_output_class matches, and operation order alone cannot produce Strong.",
        partial: "score 0.40-0.69, unless the only matches are surface wording or term overlap.",
        weak: "score < 0.40, or only surface/term overlap.",
      },
      high_weight_axes: [...HIGH_WEIGHT_AXES],
    },
    pattern_bank: {
      operation_patterns: OPERATION_PATTERNS.map(({ regex, ...pattern }) => ({
        ...pattern,
        regex: regex.source,
      })),
      quantity_channels: CHANNEL_RULES,
      motif_rules: [
        "set_add_add_divide",
        "quotient_remainder",
        "multiply_then_modulus",
        "remove_modulus_remainder",
        "cycle_counting",
        "cast_out_by_lodge_sequence",
        "add_du_and_parts",
        "naming_result_cluster",
        "remainder_naming",
        "final_output_formula",
      ],
    },
    summary: {
      chunk_count: chunks.length,
      procedure_like_chunk_count: chunks.filter((chunk) => chunk.is_procedure_like).length,
      manual_breakdown_chunk_count: chunks.filter((chunk) => chunk.annotation_source === "manual_breakdown").length,
      manual_step_chunk_count: chunks.filter((chunk) => chunk.has_manual_steps).length,
      chunks_with_operations: chunks.filter((chunk) => chunk.operation_sequence.length).length,
      chunks_with_motifs: chunks.filter((chunk) => chunk.motifs.length).length,
      comparison_count: comparisons.length,
      strong_comparison_count: comparisons.filter((item) => item.verdict === "strong").length,
      partial_comparison_count: comparisons.filter((item) => item.verdict === "partial").length,
      operation_counts: countBy(chunks.flatMap((chunk) => chunk.operation_sequence), (op) => op),
      motif_counts: countBy(chunks.flatMap((chunk) => chunk.motifs), (motif) => motif),
      channel_counts: countBy(chunks.flatMap((chunk) => chunk.quantity_channels), (channel) => channel.id),
    },
    chunks,
    comparisons,
    neighbors_by_chunk,
  };
}

async function main() {
  const breakdownChunks = await readJson(BREAKDOWN_PATH);
  const sourceArtifact = await readJson(CHUNKS_PATH);
  const index = buildIndex(breakdownChunks, sourceArtifact);

  await writeJson(TMP_INDEX_PATH, index);
  await writeJson(STATIC_INDEX_PATH, index);
  await writeText(TMP_REPORT_PATH, buildMarkdownReport(index));

  console.log(JSON.stringify({
    index_json: TMP_INDEX_PATH,
    static_json: STATIC_INDEX_PATH,
    report_md: TMP_REPORT_PATH,
    summary: index.summary,
  }, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
