import fs from "node:fs/promises";
import path from "node:path";
import {
  readJson,
  readPipelineConfig,
  resolveRepoPath,
  writeJson,
} from "./cullen-oracle-common.mjs";
import {
  buildConstantIndex,
  buildOperationSignature,
  chineseNumeralToNumber,
  evaluateGroundingStatus,
  enrichQuantity,
  extractConstantsFromSpans,
  normalizeChineseName,
  operationSignatureString,
  resolveQuantityReference,
  splitChineseSentences,
} from "./procedure-ir-common.mjs";

function lineRecord(raw, index) {
  const match = raw.match(/^(\d+)\s*[\t ]*(.*)$/u);
  return {
    line: index + 1,
    source_number: match ? Number(match[1]) : null,
    text: match ? match[2].trim() : raw.trim(),
  };
}

function isProcedureLine(text) {
  return /术曰|術曰|推.+章|推.+术|推.+術/u.test(text);
}

function isConstantLine(text) {
  return /^[^\d零〇一二三四五六七八九十百千万萬亿億]{1,24}[零〇一二三四五六七八九十百千万萬亿億两兩\d]+[。．.，,]/u.test(text)
    || /^[^\d零〇一二三四五六七八九十百千万萬亿億]{1,24}[零〇一二三四五六七八九十百千万萬亿億两兩\d]+$/u.test(text);
}

function applyScope(lines, source) {
  if (!source.include_patterns?.length) return lines;
  const includeRegexes = source.include_patterns.map((item) => new RegExp(item, "u"));
  const stopRegexes = (source.stop_patterns ?? []).map((item) => new RegExp(item, "u"));
  const scoped = [];
  let active = false;
  for (const line of lines) {
    if (!active && includeRegexes.some((regex) => regex.test(line.text))) active = true;
    if (active && stopRegexes.some((regex) => regex.test(line.text))) break;
    if (active) scoped.push(line);
  }
  return scoped;
}

function extractSourceSpans(lines, source) {
  const spans = [];
  for (const record of lines) {
    if (!record.text) continue;
    if (!isProcedureLine(record.text) && !isConstantLine(record.text)) continue;
    spans.push({
      id: `${source.id}:L${record.line}`,
      source_id: source.id,
      source_title: source.title,
      kind: isProcedureLine(record.text) ? "procedure" : "constant_or_rate",
      line_start: record.line,
      line_end: record.line,
      source_number_start: record.source_number,
      source_number_end: record.source_number,
      text: record.text,
    });
  }
  return spans;
}

function titleGuess(text) {
  const match = text.match(/^(推[^，。；：]+章?|推[^，。；：]+術?|推[^，。；：]+术?)/u);
  return match ? match[1] : "untitled procedure";
}

function buildStepBase(procedureId, span, index, operationType, expression) {
  return {
    id: `${procedureId}:step:${index + 1}`,
    step_id: `${procedureId}:step:${index + 1}`,
    procedure_id: procedureId,
    source_id: span.source_id,
    source_span_id: span.id,
    operation_type: operationType,
    expression,
    source_phrase: expression,
    inputs: [],
    output: null,
    divisor: null,
    quotient: null,
    remainder: null,
    modulus: null,
    operation_signature: null,
    validation_status: "NEEDS_REVIEW",
  };
}

function parseQuantity(rawName, span, constantIndex) {
  return resolveQuantityReference(rawName, span.source_id, constantIndex, span.id);
}

function parseNumericQuantity(raw, span, role = "number") {
  const value = chineseNumeralToNumber(String(raw));
  if (value === null) return null;
  return enrichQuantity({
    source_id: span.source_id,
    name_zh: String(raw),
    normalized_name: String(value),
    value,
    quantity_role: role,
    quantity_value_source: "explicit_numeric_text",
    confidence: "A_textual_explicit",
    source_span_id: span.id,
  }, span.source_id);
}

function parseMultiply(sentence, procedureId, span, index, constantIndex) {
  const match = sentence.match(/以(.+?)乘(.+?)，?得(.+)$/u);
  if (!match) return null;
  const step = buildStepBase(procedureId, span, index, "multiply", sentence);
  step.inputs = [
    parseQuantity(match[1], span, constantIndex),
    parseQuantity(match[2], span, constantIndex),
  ];
  step.output = parseQuantity(match[3], span, constantIndex);
  return step;
}

function parseAdd(sentence, procedureId, span, index, constantIndex) {
  const match = sentence.match(/以(.+?)加(.+?)，?得(.+)$/u);
  if (!match) return null;
  const step = buildStepBase(procedureId, span, index, "add", sentence);
  step.inputs = [
    parseQuantity(match[1], span, constantIndex),
    parseQuantity(match[2], span, constantIndex),
  ];
  step.output = parseQuantity(match[3], span, constantIndex);
  return step;
}

function parseQuotientRemainder(sentence, procedureId, span, index, constantIndex) {
  const multiplyQr = sentence.match(/(?:置(.+?)，)?以(.+?)乘之，?(?:滿|盈)(.+?)得一，?名[為曰](.+?)，?(?:不滿|不盈|不盡)為(.+)$/u);
  if (multiplyQr) {
    const step = buildStepBase(procedureId, span, index, "quotient_remainder", sentence);
    const dividend = multiplyQr[1] ? parseQuantity(multiplyQr[1], span, constantIndex) : null;
    const multiplier = parseQuantity(multiplyQr[2], span, constantIndex);
    step.inputs = [dividend, multiplier].filter(Boolean);
    step.divisor = parseQuantity(multiplyQr[3], span, constantIndex);
    step.quotient = parseQuantity(multiplyQr[4], span, constantIndex);
    step.output = step.quotient;
    step.remainder = parseQuantity(multiplyQr[5], span, constantIndex);
    step.modulus = step.divisor?.value ?? null;
    return step;
  }

  const divideQr = sentence.match(/(?:又置|置)?(.+?)，?以(.+?)除之，?得(.+?)，?(?:不盡|不满|不滿|馀|餘為|其餘為)(.+)$/u);
  if (divideQr) {
    const step = buildStepBase(procedureId, span, index, "quotient_remainder", sentence);
    step.inputs = [parseQuantity(divideQr[1], span, constantIndex)];
    step.divisor = parseQuantity(divideQr[2], span, constantIndex);
    step.quotient = parseQuantity(divideQr[3], span, constantIndex);
    step.output = step.quotient;
    step.remainder = parseQuantity(divideQr[4], span, constantIndex);
    step.modulus = step.divisor?.value ?? null;
    return step;
  }

  const implicitRemainder = sentence.match(/(.+?)以([零〇一二三四五六七八九十百千万萬亿億两兩\d]+)除去之，?其(?:餘|余)為(.+)$/u);
  if (implicitRemainder) {
    const step = buildStepBase(procedureId, span, index, "quotient_remainder", sentence);
    step.inputs = [parseQuantity(implicitRemainder[1], span, constantIndex)];
    step.divisor = parseNumericQuantity(implicitRemainder[2], span, "divisor");
    step.remainder = parseQuantity(implicitRemainder[3], span, constantIndex);
    step.output = step.remainder;
    step.modulus = step.divisor?.value ?? null;
    return step;
  }

  const namedQr = sentence.match(/(?:以|Count one for each time )(.+?)(?:乘|除| fills? )(.+?)?.*?(?:名[曰為]|called)(.+?)(?:，|;|。).*(?:不滿|不盈|不盡|what does not fill is called)(.+)$/iu);
  if (namedQr) {
    const step = buildStepBase(procedureId, span, index, "quotient_remainder", sentence);
    step.inputs = [parseQuantity(namedQr[1], span, constantIndex)].filter(Boolean);
    step.divisor = namedQr[2] ? parseQuantity(namedQr[2], span, constantIndex) : null;
    step.quotient = parseQuantity(namedQr[3], span, constantIndex);
    step.output = step.quotient;
    step.remainder = parseQuantity(namedQr[4], span, constantIndex);
    step.modulus = step.divisor?.value ?? null;
    return step;
  }

  return null;
}

function parseModulo(sentence, procedureId, span, index, constantIndex) {
  const modMatch = sentence.match(/(?:又置|置)?(.+?)，?以([零〇一二三四五六七八九十百千万萬亿億两兩\d]+)除，?棄之餘，?(?:從.+?命之，?)?得(.+)$/u);
  if (!modMatch) return null;
  const step = buildStepBase(procedureId, span, index, "mod_cycle", sentence);
  step.inputs = [parseQuantity(modMatch[1], span, constantIndex)];
  step.divisor = parseNumericQuantity(modMatch[2], span, "modulus");
  step.modulus = step.divisor?.value ?? null;
  step.remainder = enrichQuantity({
    source_id: span.source_id,
    name_zh: "餘",
    normalized_name: "餘",
    value: null,
    quantity_role: "remainder",
    quantity_value_source: "derived_remainder",
    confidence: "B_textual_internal",
    source_span_id: span.id,
  }, span.source_id);
  step.output = parseQuantity(modMatch[3], span, constantIndex);
  return step;
}

function parseSet(sentence, procedureId, span, index, constantIndex) {
  const match = sentence.match(/^(?:其.+?，)?(?:其餘|餘|其分|其度分|減讫，餘相度分|減餘列)[^，。；]*?為(.+)$/u);
  if (!match) return null;
  const step = buildStepBase(procedureId, span, index, "set", sentence);
  step.output = parseQuantity(match[1], span, constantIndex);
  return step;
}

function parseSupplementarySteps(sentence, procedureId, span, startIndex, constantIndex) {
  const extraSteps = [];

  const remainderCycleMatch = sentence.match(/(.+?)以六十除去之，?其(?:餘|余)為(.+)$/u);
  if (remainderCycleMatch) {
    const step = buildStepBase(procedureId, span, startIndex + extraSteps.length, "mod_cycle", `${remainderCycleMatch[1]}以六十除去之，其餘為${remainderCycleMatch[2]}`);
    step.inputs = [parseQuantity(remainderCycleMatch[1], span, constantIndex)];
    step.divisor = parseNumericQuantity("六十", span, "modulus");
    step.modulus = 60;
    step.remainder = parseQuantity(remainderCycleMatch[2], span, constantIndex);
    step.output = step.remainder;
    step.signature = buildOperationSignature(step);
    extraSteps.push(step);
  }

  if (span.source_id === "jiuzhi") {
    const cyclePatterns = [
      { regex: /置积日，以六十除，弃之馀。?从.+?命之，得(.+?)(?:，|。|$)/u, modulus: "六十" },
      { regex: /又置积日，以七除，弃之馀，?从.+?命得之(.+?)(?:，|。|$)/u, modulus: "七" },
    ];
    for (const pattern of cyclePatterns) {
      const match = span.text.match(pattern.regex);
      if (!match) continue;
      const step = buildStepBase(procedureId, span, startIndex + extraSteps.length, "mod_cycle", match[0]);
      step.inputs = [parseQuantity("积日", span, constantIndex)];
      step.divisor = parseNumericQuantity(pattern.modulus, span, "modulus");
      step.modulus = step.divisor?.value ?? null;
      step.remainder = enrichQuantity({
        source_id: span.source_id,
        name_zh: "餘",
        normalized_name: "餘",
        value: null,
        quantity_role: "remainder",
        quantity_value_source: "derived_remainder",
        confidence: "B_textual_internal",
        source_span_id: span.id,
      }, span.source_id);
      step.output = parseQuantity(match[1], span, constantIndex);
      step.signature = buildOperationSignature(step);
      extraSteps.push(step);
    }
  }

  return extraSteps;
}

function parseProcedureSteps(span, procedureId, constantIndex) {
  const sentences = splitChineseSentences(span.text);
  const parsers = [parseQuotientRemainder, parseModulo, parseMultiply, parseAdd, parseSet];
  const steps = [];

  for (const sentence of sentences) {
    const cleanSentence = sentence.trim();
    if (!cleanSentence) continue;
    let parsed = null;
    for (const parser of parsers) {
      parsed = parser(cleanSentence, procedureId, span, steps.length, constantIndex);
      if (parsed) break;
    }
    if (parsed) {
      parsed.signature = buildOperationSignature(parsed);
      parsed.operation_signature = operationSignatureString(parsed);
      steps.push(parsed);
    }
    const supplementary = parseSupplementarySteps(cleanSentence, procedureId, span, steps.length, constantIndex);
    steps.push(...supplementary);
  }

  const deduped = [];
  const seen = new Set();
  for (const step of steps) {
    const key = `${step.operation_type}:${step.expression}`;
    if (seen.has(key)) continue;
    seen.add(key);
    step.id = `${procedureId}:step:${deduped.length + 1}`;
    step.step_id = step.id;
    step.signature = buildOperationSignature(step);
    step.operation_signature = operationSignatureString(step);
    deduped.push(step);
  }

  return deduped;
}

function buildProcedureIR(spans, constantIndex) {
  return spans
    .filter((span) => span.kind === "procedure" || /以.+?(乘|除).+?(得|名為|名曰)/u.test(span.text))
    .map((span) => {
      const procedureId = span.id.replace(":L", ":procedure:L");
      const steps = parseProcedureSteps(span, procedureId, constantIndex);
      return {
        id: procedureId,
        procedure_id: procedureId,
        source_id: span.source_id,
        source_span_id: span.id,
        title_guess: titleGuess(span.text),
        procedure_ir_schema: "executable_step_ir_v1",
        steps,
      };
    });
}

function buildValidationChecks(procedureIR, alignments) {
  const alignmentMap = new Map();
  for (const alignment of alignments ?? []) {
    alignmentMap.set(alignment.step_id, alignment);
  }

  const checks = [];
  for (const procedure of procedureIR) {
    for (const step of procedure.steps) {
      const check = {
        id: `${step.id}:validation`,
        procedure_id: procedure.id,
        step_id: step.id,
        source_id: step.source_id,
        source_span_id: step.source_span_id,
        expression: step.expression,
        operation_type: step.operation_type,
        status: "not_checked",
        arithmetic: null,
        cullen_grounding: alignmentMap.get(step.id) ?? null,
      };

      if (
        step.operation_type === "multiply"
        && step.inputs.length === 2
        && step.inputs.every((item) => item?.value !== null)
        && step.output?.value !== null
      ) {
        check.arithmetic = {
          expected: step.inputs[0].value * step.inputs[1].value,
          actual: step.output.value,
        };
        check.status = check.arithmetic.expected === check.arithmetic.actual ? "pass" : "fail";
      } else if (
        ["quotient_remainder", "mod_cycle"].includes(step.operation_type)
        && step.divisor?.value !== null
      ) {
        check.status = "pass";
      } else {
        check.status = "needs_review";
      }

      check.grounding_status = evaluateGroundingStatus(step, check.cullen_grounding, check.status);
      step.validation_status = check.grounding_status === "A_confirmed"
        ? "PASS"
        : check.status === "fail"
          ? "FAIL"
          : "NEEDS_REVIEW";
      checks.push(check);
    }
  }

  return checks;
}

function buildVectors(procedureIR, validationChecks) {
  const checkMap = new Map();
  for (const check of validationChecks) {
    if (!checkMap.has(check.procedure_id)) checkMap.set(check.procedure_id, []);
    checkMap.get(check.procedure_id).push(check);
  }

  return procedureIR.map((procedure) => {
    const steps = procedure.steps;
    const checks = checkMap.get(procedure.id) ?? [];
    const cycleModuli = [...new Set(
      steps
        .filter((step) => step.operation_type === "mod_cycle")
        .map((step) => step.modulus)
        .filter((value) => value !== null)
    )];
    return {
      procedure_id: procedure.id,
      source_id: procedure.source_id,
      title_guess: procedure.title_guess,
      vector_schema: "interpretable_procedure_vector_v1",
      operation_sequence: steps.map((step) => step.operation_type),
      uses_accumulated_days: steps.some((step) =>
        [step.output, ...step.inputs].filter(Boolean).some((item) => item.normalized_name === "积日")
      ),
      uses_quotient_remainder: steps.some((step) => step.operation_type === "quotient_remainder"),
      uses_cycle: cycleModuli.length > 0,
      cycle_moduli: cycleModuli,
      outputs: uniqueOutputs(steps),
      confidence_profile: {
        A_confirmed: checks.filter((item) => item.grounding_status === "A_confirmed").length,
        B_textual_internal: checks.filter((item) => item.grounding_status === "B_textual_internal").length,
        B_textual_partial: checks.filter((item) => item.grounding_status === "B_textual_partial").length,
        B_supported_with_semantic_count: checks.filter((item) => item.grounding_status === "B_supported_with_semantic_count").length,
        needs_review: checks.filter((item) => item.grounding_status === "needs_review").length,
      },
    };
  });
}

function uniqueOutputs(steps) {
  return [...new Set(
    steps
      .map((step) => step.output?.name_zh ?? null)
      .filter(Boolean)
  )];
}

async function maybeReadText(relativePath) {
  try {
    return await fs.readFile(resolveRepoPath(relativePath), "utf8");
  } catch (error) {
    if (error.code === "ENOENT") return null;
    throw error;
  }
}

async function maybeReadJson(relativePath) {
  try {
    return await readJson(relativePath);
  } catch (error) {
    if (error.code === "ENOENT") return null;
    throw error;
  }
}

async function main() {
  const config = await readPipelineConfig();
  const outputDir = resolveRepoPath(config.outputs.dir);
  await fs.mkdir(outputDir, { recursive: true });

  const runStartedAt = new Date().toISOString();
  const inputStatus = [];
  const reviewQueue = [];
  const allSpans = [];

  for (const source of config.inputs.source_texts) {
    const text = await maybeReadText(source.path);
    if (!text) {
      inputStatus.push({ source_id: source.id, path: source.path, status: "missing" });
      reviewQueue.push({
        id: `${source.id}:missing-input`,
        severity: "blocking",
        item_type: "missing_input",
        message: `Source text not found at ${source.path}.`,
      });
      continue;
    }
    const rawLines = text.split(/\r?\n/u).map(lineRecord);
    const scopedLines = applyScope(rawLines, source);
    const spans = extractSourceSpans(scopedLines, source);
    allSpans.push(...spans);
    inputStatus.push({
      source_id: source.id,
      path: source.path,
      status: "loaded",
      line_count: rawLines.length,
      scoped_line_count: scopedLines.length,
      extracted_span_count: spans.length,
    });
  }

  const constants = extractConstantsFromSpans(allSpans);
  const constantIndex = buildConstantIndex(constants);
  const procedureIR = buildProcedureIR(allSpans, constantIndex);
  const cullenAlignmentsPayload = await maybeReadJson(config.inputs.cullen.artifacts.alignments);
  const validationChecks = buildValidationChecks(procedureIR, cullenAlignmentsPayload?.alignments ?? []);
  const vectors = buildVectors(procedureIR, validationChecks);

  for (const procedure of procedureIR) {
    if (procedure.steps.length === 0) {
      reviewQueue.push({
        id: `${procedure.id}:empty-steps`,
        severity: "medium",
        item_type: "procedure_ir",
        source_span_id: procedure.source_span_id,
        message: "Procedure span detected, but no executable steps were parsed.",
      });
    }
  }

  for (const check of validationChecks) {
    if (check.status === "fail" || check.grounding_status === "needs_review") {
      reviewQueue.push({
        id: `${check.id}:review`,
        severity: check.status === "fail" ? "high" : "low",
        item_type: "validation",
        source_span_id: check.source_span_id,
        message: `${check.operation_type} step requires review: ${check.expression}`,
      });
    }
  }

  const validationReport = {
    generated_at: runStartedAt,
    input_status: inputStatus,
    summary: {
      source_span_count: allSpans.length,
      extracted_constant_count: constants.length,
      procedure_count: procedureIR.length,
      step_count: procedureIR.reduce((sum, procedure) => sum + procedure.steps.length, 0),
      validation_count: validationChecks.length,
      pass_count: validationChecks.filter((item) => item.status === "pass").length,
      fail_count: validationChecks.filter((item) => item.status === "fail").length,
      needs_review_count: validationChecks.filter((item) => item.status === "needs_review").length,
      cullen_grounding_metrics: {
        A_confirmed: validationChecks.filter((item) => item.grounding_status === "A_confirmed").length,
        B_textual_internal: validationChecks.filter((item) => item.grounding_status === "B_textual_internal").length,
        B_textual_partial: validationChecks.filter((item) => item.grounding_status === "B_textual_partial").length,
        B_supported_with_semantic_count: validationChecks.filter((item) => item.grounding_status === "B_supported_with_semantic_count").length,
        needs_review: validationChecks.filter((item) => item.grounding_status === "needs_review").length,
      },
    },
    extracted_constants: constants,
    checks: validationChecks,
  };

  await writeJson(path.join(config.outputs.dir, "source_spans.json").replace(/\\/gu, "/"), {
    generated_at: runStartedAt,
    spans: allSpans,
  });
  await writeJson(path.join(config.outputs.dir, "procedure_IR.json").replace(/\\/gu, "/"), {
    generated_at: runStartedAt,
    procedure_ir_schema: "executable_step_ir_v1",
    procedures: procedureIR,
  });
  await writeJson(path.join(config.outputs.dir, "validation_report.json").replace(/\\/gu, "/"), validationReport);
  await writeJson(path.join(config.outputs.dir, "review_queue.json").replace(/\\/gu, "/"), {
    generated_at: runStartedAt,
    items: reviewQueue,
  });
  await writeJson(path.join(config.outputs.dir, "procedure_vectors.json").replace(/\\/gu, "/"), {
    generated_at: runStartedAt,
    vector_schema: "interpretable_procedure_vector_v1",
    vectors,
  });

  console.log(JSON.stringify({
    output_dir: config.outputs.dir,
    source_spans: allSpans.length,
    procedures: procedureIR.length,
    steps: procedureIR.reduce((sum, procedure) => sum + procedure.steps.length, 0),
    validations: validationChecks.length,
    review_items: reviewQueue.length,
  }, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
