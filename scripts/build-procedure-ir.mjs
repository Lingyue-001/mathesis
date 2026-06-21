import fs from "node:fs/promises";
import path from "node:path";

const ROOT = process.cwd();
const CONFIG_PATH = path.join(ROOT, "config", "calendrical-ir-pipeline.json");

const HAN_NUMERAL_MAP = new Map([
  ["零", 0], ["〇", 0], ["一", 1], ["二", 2], ["三", 3], ["四", 4], ["五", 5],
  ["六", 6], ["七", 7], ["八", 8], ["九", 9], ["十", 10], ["百", 100], ["千", 1000],
  ["万", 10000], ["萬", 10000], ["亿", 100000000], ["億", 100000000]
]);

const UNIT_VALUES = new Map([
  ["十", 10], ["百", 100], ["千", 1000], ["万", 10000], ["萬", 10000], ["亿", 100000000], ["億", 100000000]
]);

const OP_RULES = [
  { type: "set", pattern: /置|列为|名为|名曰|是为/g },
  { type: "multiply", pattern: /乘|倍|参/g },
  { type: "divide", pattern: /除|盈|满|滿|如法得一|得一/g },
  { type: "add", pattern: /加|并|從之|从之/g },
  { type: "subtract", pattern: /减|減|损|損|去/g },
  { type: "remainder", pattern: /不满|不滿|不尽|不盡|馀|餘/g },
  { type: "discard", pattern: /弃|棄|除去/g },
  { type: "label", pattern: /命|起|筭外|算外/g },
  { type: "compare", pattern: /以上|以下|若|如不足|不成减|成减/g }
];

const HAN_NUMBER_CHARS = "一二三四五六七八九十百千万萬亿億〇零两兩0-9";

function resolveRepoPath(relativePath) {
  return path.join(ROOT, relativePath);
}

function lineRecord(raw, index) {
  const match = raw.match(/^(\d+)\s*[\t ]*(.*)$/u);
  return {
    line: index + 1,
    source_number: match ? Number(match[1]) : null,
    text: match ? match[2].trim() : raw.trim()
  };
}

function splitSentences(text) {
  return text
    .split(/[。；;]/u)
    .map((part) => part.trim())
    .filter(Boolean);
}

function isProcedureLine(text) {
  return /术曰|術曰/u.test(text)
    || /^(推|求).{0,28}(术|術)/u.test(text)
    || /^(一术|一術)/u.test(text);
}

function isConstantLine(text) {
  const earlyClause = text.split(/[。；;]/u)[0] ?? text;
  return new RegExp(`^[^${HAN_NUMBER_CHARS}]{1,30}[${HAN_NUMBER_CHARS}]`, "u").test(earlyClause);
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
    if (isProcedureLine(record.text) || isConstantLine(record.text)) {
      const kind = isProcedureLine(record.text) ? "procedure" : "constant_or_rate";
      spans.push({
        id: `${source.id}:L${record.line}`,
        source_id: source.id,
        source_title: source.title,
        kind,
        line_start: record.line,
        line_end: record.line,
        source_number_start: record.source_number,
        source_number_end: record.source_number,
        text: record.text
      });
    }
  }
  return spans;
}

function operationNodes(span) {
  const sentences = splitSentences(span.text);
  const nodes = [];
  const edges = [];
  for (const [sentenceIndex, sentence] of sentences.entries()) {
    for (const rule of OP_RULES) {
      rule.pattern.lastIndex = 0;
      if (rule.pattern.test(sentence)) {
        const nodeId = `${span.id}:op${nodes.length + 1}`;
        nodes.push({
          id: nodeId,
          op: rule.type,
          expression: sentence,
          sentence_index: sentenceIndex
        });
        if (nodes.length > 1) {
          edges.push({
            from: nodes[nodes.length - 2].id,
            to: nodeId,
            relation: "then"
          });
        }
      }
    }
  }
  return { nodes, edges };
}

function extractProcedureIR(spans) {
  return spans
    .filter((span) => span.kind === "procedure")
    .map((span) => {
      const graph = operationNodes(span);
      return {
        id: span.id.replace(":L", ":procedure:L"),
        source_id: span.source_id,
        source_span_id: span.id,
        title_guess: titleGuess(span.text),
        graph
      };
    });
}

function titleGuess(text) {
  const match = text.match(/^(推[^，。；：:]+|求[^，。；：:]+|一术|一術)/u);
  return match ? match[1] : "untitled procedure";
}

function chineseNumeralToNumber(input) {
  if (!input) return null;
  const normalized = input.replace(/[又有之算上外個个]/gu, "").replace(/兩/gu, "二").replace(/两/gu, "二");
  if (/^\d+$/u.test(normalized)) return Number(normalized);
  let total = 0;
  let section = 0;
  let number = 0;
  for (const char of normalized) {
    if (!HAN_NUMERAL_MAP.has(char)) return null;
    const value = HAN_NUMERAL_MAP.get(char);
    if (UNIT_VALUES.has(char)) {
      if (value >= 10000) {
        section = (section + number || 1) * value;
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

function extractConstants(spans) {
  const constants = new Map();
  for (const span of spans) {
    if (span.kind !== "constant_or_rate") continue;
    const text = span.text.replace(/[。.]$/u, "");
    const match = text.match(new RegExp(`^([^${HAN_NUMBER_CHARS}，,。；;]+?)([${HAN_NUMBER_CHARS}]+)(?:[，,。；;]|$)`, "u"));
    if (!match) continue;
    const name = match[1].trim();
    const value = chineseNumeralToNumber(match[2]);
    if (name && value !== null) {
      constants.set(`${span.source_id}:${name}`, { source_id: span.source_id, name, value, span_id: span.id });
    }
  }
  return constants;
}

function normalizeName(name) {
  return name.replace(/[之的其各以为為曰名\s]/gu, "");
}

function validateDerivedConstants(spans) {
  const constants = extractConstants(spans);
  const bySource = new Map();
  for (const item of constants.values()) {
    if (!bySource.has(item.source_id)) bySource.set(item.source_id, []);
    bySource.get(item.source_id).push(item);
  }

  const checks = [];
  for (const span of spans) {
    if (span.kind !== "constant_or_rate") continue;
    const sentences = splitSentences(span.text);
    for (const sentence of sentences) {
      const multiplyMatch = sentence.match(/以([^，,。；;]+?)乘([^，,。；;]+?)[，,]?得([^，,。；;]+)$/u);
      if (!multiplyMatch) continue;
      const [, leftRaw, rightRaw, resultRaw] = multiplyMatch;
      const constantsForSource = bySource.get(span.source_id) ?? [];
      const left = findConstant(constantsForSource, leftRaw);
      const right = findConstant(constantsForSource, rightRaw);
      const result = findConstant(constantsForSource, resultRaw);
      const check = {
        id: `${span.id}:validation:${checks.length + 1}`,
        source_id: span.source_id,
        source_span_id: span.id,
        rule: "derived_constant_multiplication",
        expression: sentence,
        status: "not_checked",
        operands: {
          left: left?.name ?? leftRaw.trim(),
          right: right?.name ?? rightRaw.trim(),
          result: result?.name ?? resultRaw.trim()
        }
      };
      if (left && right && result) {
        check.expected = left.value * right.value;
        check.actual = result.value;
        check.status = check.expected === check.actual ? "pass" : "fail";
      } else {
        check.status = "needs_review";
        check.reason = "Could not resolve every named quantity against extracted constants.";
      }
      checks.push(check);
    }
  }
  return checks;
}

function findConstant(constants, rawName) {
  const needle = normalizeName(rawName);
  return constants.find((item) => {
    const haystack = normalizeName(item.name);
    return haystack === needle || haystack.includes(needle) || needle.includes(haystack);
  });
}

function buildVectors(procedureIR) {
  return procedureIR.map((procedure) => {
    const counts = Object.fromEntries(OP_RULES.map((rule) => [rule.type, 0]));
    for (const node of procedure.graph.nodes) {
      counts[node.op] = (counts[node.op] ?? 0) + 1;
    }
    return {
      procedure_id: procedure.id,
      source_id: procedure.source_id,
      title_guess: procedure.title_guess,
      vector_schema: "op_count_v1",
      dimensions: counts,
      length: procedure.graph.nodes.length,
      edge_count: procedure.graph.edges.length
    };
  });
}

async function maybeReadText(relativePath) {
  try {
    return await fs.readFile(resolveRepoPath(relativePath), "utf8");
  } catch (error) {
    if (error.code === "ENOENT") return null;
    throw error;
  }
}

async function writeJson(outDir, fileName, data) {
  await fs.writeFile(path.join(outDir, fileName), `${JSON.stringify(data, null, 2)}\n`, "utf8");
}

async function main() {
  const config = JSON.parse(await fs.readFile(CONFIG_PATH, "utf8"));
  const outputDir = resolveRepoPath(config.outputs.dir);
  await fs.mkdir(outputDir, { recursive: true });

  const runStartedAt = new Date().toISOString();
  const inputStatus = [];
  const allSpans = [];
  const reviewQueue = [];

  const cullenText = await maybeReadText(config.inputs.cullen.path);
  const cullenExists = cullenText !== null;
  const cullenOracle = {
    generated_at: runStartedAt,
    input: config.inputs.cullen,
    status: cullenExists && config.inputs.cullen.format === "pdf"
      ? "registered_pdf_pending_text_extraction"
      : cullenExists
        ? "ready_for_extraction"
        : "missing_input",
    terms: [],
    formulae: [],
    procedure_explanations: [],
    worked_examples: []
  };
  if (!cullenExists) {
    reviewQueue.push({
      id: "cullen:missing-input",
      severity: "blocking_for_cullen_oracle",
      item_type: "missing_input",
      message: `Cullen source not found at ${config.inputs.cullen.path}. Add text/PDF extraction before oracle generation.`
    });
  } else if (config.inputs.cullen.format === "pdf") {
    reviewQueue.push({
      id: "cullen:pdf-text-extraction",
      severity: "high",
      item_type: "cullen_oracle",
      message: "Cullen PDF is registered, but text extraction and oracle mapping are not implemented in this first deterministic pass."
    });
  }

  for (const source of config.inputs.source_texts) {
    const text = await maybeReadText(source.path);
    if (!text) {
      inputStatus.push({ source_id: source.id, path: source.path, status: "missing" });
      reviewQueue.push({
        id: `${source.id}:missing-input`,
        severity: "blocking",
        item_type: "missing_input",
        message: `Source text not found at ${source.path}.`
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
      scope: source.scope,
      line_count: rawLines.length,
      scoped_line_count: scopedLines.length,
      extracted_span_count: spans.length
    });
  }

  const procedureIR = extractProcedureIR(allSpans);
  const validationChecks = validateDerivedConstants(allSpans);
  const vectors = buildVectors(procedureIR);

  for (const procedure of procedureIR) {
    if (procedure.graph.nodes.length === 0) {
      reviewQueue.push({
        id: `${procedure.id}:empty-ir`,
        severity: "medium",
        item_type: "procedure_ir",
        source_span_id: procedure.source_span_id,
        message: "Procedure span was detected, but no operation keywords were mapped into graph nodes."
      });
    }
  }
  for (const check of validationChecks) {
    if (check.status !== "pass") {
      reviewQueue.push({
        id: `${check.id}:review`,
        severity: check.status === "fail" ? "high" : "low",
        item_type: "validation",
        source_span_id: check.source_span_id,
        message: check.status === "fail"
          ? `Validation failed for ${check.expression}.`
          : `Validation needs review for ${check.expression}.`
      });
    }
  }

  const validationReport = {
    generated_at: runStartedAt,
    input_status: inputStatus,
    summary: {
      source_span_count: allSpans.length,
      procedure_count: procedureIR.length,
      validation_count: validationChecks.length,
      pass_count: validationChecks.filter((item) => item.status === "pass").length,
      fail_count: validationChecks.filter((item) => item.status === "fail").length,
      needs_review_count: validationChecks.filter((item) => item.status === "needs_review").length
    },
    checks: validationChecks
  };

  await writeJson(outputDir, "cullen_oracle.json", cullenOracle);
  await writeJson(outputDir, "source_spans.json", {
    generated_at: runStartedAt,
    spans: allSpans
  });
  await writeJson(outputDir, "procedure_IR.json", {
    generated_at: runStartedAt,
    procedures: procedureIR
  });
  await writeJson(outputDir, "validation_report.json", validationReport);
  await writeJson(outputDir, "review_queue.json", {
    generated_at: runStartedAt,
    items: reviewQueue
  });
  await writeJson(outputDir, "procedure_vectors.json", {
    generated_at: runStartedAt,
    vector_schema: "op_count_v1",
    vectors
  });

  console.log(JSON.stringify({
    output_dir: config.outputs.dir,
    source_spans: allSpans.length,
    procedures: procedureIR.length,
    validations: validationChecks.length,
    review_items: reviewQueue.length
  }, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
