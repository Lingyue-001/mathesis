import { readJson, readPipelineConfig, writeJson } from "./cullen-oracle-common.mjs";

function average(values) {
  return values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : 0;
}

function containsAll(text, terms) {
  const haystack = text ?? "";
  return terms.every((term) => haystack.includes(term));
}

function containsAny(text, terms) {
  const haystack = text ?? "";
  return terms.some((term) => haystack.includes(term));
}

function summarizePages(pagesPayload) {
  const pages = pagesPayload.pages ?? [];
  const lengths = pages.map((page) => page.char_count);
  const emptyPages = pages.filter((page) => page.char_count === 0).map((page) => page.page_number);
  return {
    page_count: pagesPayload.page_count,
    empty_page_count: emptyPages.length,
    average_char_count: average(lengths),
  };
}

function summarizeClaims(claimsPayload) {
  const claims = claimsPayload.claims ?? [];
  const claimTypeCounts = Object.fromEntries(
    [...new Set(claims.map((claim) => claim.claim_type))]
      .sort()
      .map((type) => [type, claims.filter((claim) => claim.claim_type === type).length])
  );
  return {
    claim_count: claims.length,
    claim_type_counts: claimTypeCounts,
    structured_claim_count: claims.filter((claim) => claim.operation_type || claim.output || claim.inputs?.length).length,
    with_evidence_count: claims.filter((claim) => claim.evidence_chunk_id && claim.page_start && claim.page_end).length,
  };
}

function summarizeProcedures(procedurePayload) {
  const procedures = procedurePayload.procedures ?? [];
  const steps = procedures.flatMap((procedure) => procedure.steps ?? []);
  return {
    procedure_count: procedures.length,
    step_count: steps.length,
    structured_step_count: steps.filter((step) => step.operation_type).length,
    steps_with_inputs_outputs: steps.filter((step) => (step.inputs?.length ?? 0) > 0 && step.output).length,
    steps_with_resolved_quantities: steps.filter((step) => {
      const quantities = [...(step.inputs ?? []), step.output, step.divisor, step.quotient, step.remainder].filter(Boolean);
      return quantities.length > 0 && quantities.every((item) => item.value !== null || item.quantity_role);
    }).length,
  };
}

function summarizeAlignment(alignmentsPayload) {
  const alignments = alignmentsPayload.alignments ?? [];
  return {
    alignment_count: alignments.length,
    direct_support_count: alignments.filter((item) => item.alignment_status === "direct_support").length,
    partial_support_count: alignments.filter((item) => item.alignment_status === "partial_support").length,
    no_support_count: alignments.filter((item) => item.alignment_status === "no_support").length,
  };
}

function summarizeValidation(validationReport) {
  return {
    validation_count: validationReport.summary?.validation_count ?? (validationReport.checks ?? []).length,
    pass_count: validationReport.summary?.pass_count ?? 0,
    fail_count: validationReport.summary?.fail_count ?? 0,
    needs_review_count: validationReport.summary?.needs_review_count ?? 0,
    cullen_grounding_metrics: validationReport.summary?.cullen_grounding_metrics ?? {},
  };
}

function findSourceSpan(sourceSpansPayload, item) {
  const spans = sourceSpansPayload.spans.filter((span) => span.source_id === item.source_id);
  return spans.find((span) => containsAll(span.text, item.source_terms ?? []))
    ?? spans.find((span) => containsAny(span.text, item.source_terms ?? []))
    ?? null;
}

function findStructuredStep(procedurePayload, item) {
  const procedures = procedurePayload.procedures.filter((procedure) => procedure.source_id === item.source_id);
  const steps = procedures.flatMap((procedure) => procedure.steps ?? []);
  return steps.find((step) =>
    containsAny(step.expression, item.operation_terms ?? item.source_terms ?? [])
    || containsAny(step.operation_signature, item.operation_terms ?? item.source_terms ?? [])
  ) ?? null;
}

function findValidation(validationReport, step) {
  if (!step) return null;
  return (validationReport.checks ?? []).find((check) => check.step_id === step.step_id) ?? null;
}

function findClaim(claimsPayload, item) {
  if (!item.cullen_expected) return null;
  return (claimsPayload.claims ?? []).find((claim) =>
    containsAll(`${claim.formula_text} ${claim.english_terms.join(" ")}`, item.cullen_terms ?? [])
  ) ?? null;
}

function findAlignment(alignmentsPayload, step) {
  if (!step) return null;
  return (alignmentsPayload.alignments ?? []).find((alignment) => alignment.step_id === step.step_id) ?? null;
}

function benchmarkItemResult(item, artifacts) {
  const sourceSpan = findSourceSpan(artifacts.sourceSpans, item);
  const step = findStructuredStep(artifacts.procedureIR, item);
  const validation = findValidation(artifacts.validation, step);
  const claim = findClaim(artifacts.claims, item);
  const alignment = findAlignment(artifacts.alignments, step);

  const resolvedQuantities = step
    ? [...(step.inputs ?? []), step.output, step.divisor, step.quotient, step.remainder].filter(Boolean)
    : [];

  const finalConfidence = validation?.grounding_status ?? "needs_review";
  const arithmeticPass = Boolean(validation?.arithmetic ? validation.status === "pass" : validation?.status === "pass");
  const structuredStepFound = Boolean(step);
  const resolvedQuantitiesFound = resolvedQuantities.length > 0
    && resolvedQuantities.every((quantity) => quantity.value !== null || quantity.quantity_role);

  const failureReasons = [];
  if (!sourceSpan) failureReasons.push("source_span_not_found");
  if (!structuredStepFound) failureReasons.push("structured_step_not_found");
  if (structuredStepFound && !resolvedQuantitiesFound) failureReasons.push("resolved_quantities_missing");
  if (!arithmeticPass && item.cullen_expected) failureReasons.push("arithmetic_validation_missing");
  if (item.cullen_expected && !claim) failureReasons.push("cullen_claim_not_found");
  if (item.cullen_expected && alignment?.alignment_status !== "direct_support") failureReasons.push("no_direct_cullen_alignment");

  return {
    id: item.id,
    label: item.label,
    source_span_found: Boolean(sourceSpan),
    source_span_id: sourceSpan?.id ?? null,
    structured_step_found: structuredStepFound,
    step_id: step?.step_id ?? null,
    resolved_quantities_found: resolvedQuantitiesFound,
    arithmetic_validation_pass: arithmeticPass,
    cullen_claim_found: Boolean(claim),
    cullen_claim_id: claim?.claim_id ?? null,
    cullen_alignment_status: alignment?.alignment_status ?? "no_support",
    final_confidence: finalConfidence,
    failure_reasons: failureReasons,
  };
}

function summarizeBenchmark(results) {
  const pass = results.filter((item) => item.failure_reasons.length === 0).length;
  const partial = results.filter((item) => item.failure_reasons.length > 0 && item.failure_reasons.length <= 2).length;
  const fail = results.length - pass - partial;
  return {
    item_count: results.length,
    source_span_found_count: results.filter((item) => item.source_span_found).length,
    structured_step_found_count: results.filter((item) => item.structured_step_found).length,
    resolved_quantities_found_count: results.filter((item) => item.resolved_quantities_found).length,
    arithmetic_validation_pass_count: results.filter((item) => item.arithmetic_validation_pass).length,
    cullen_claim_found_count: results.filter((item) => item.cullen_claim_found).length,
    benchmark_A_confirmed_count: results.filter((item) => item.final_confidence === "A_confirmed").length,
    pass,
    partial,
    fail,
  };
}

async function main() {
  const config = await readPipelineConfig();
  const benchmarkConfig = await readJson("config/cullen-mini-gold-benchmark.json");
  const artifacts = {
    pages: await readJson(config.inputs.cullen.artifacts.pages),
    claims: await readJson(config.inputs.cullen.artifacts.claims),
    alignments: await readJson(config.inputs.cullen.artifacts.alignments),
    sourceSpans: await readJson(`${config.outputs.dir}/source_spans.json`),
    procedureIR: await readJson(`${config.outputs.dir}/procedure_IR.json`),
    validation: await readJson(`${config.outputs.dir}/validation_report.json`),
  };

  const benchmarkResults = benchmarkConfig.items.map((item) => benchmarkItemResult(item, artifacts));
  const report = {
    generated_at: new Date().toISOString(),
    pages: summarizePages(artifacts.pages),
    claims: summarizeClaims(artifacts.claims),
    procedures: summarizeProcedures(artifacts.procedureIR),
    alignment: summarizeAlignment(artifacts.alignments),
    validation: summarizeValidation(artifacts.validation),
    mini_gold_benchmark: {
      summary: summarizeBenchmark(benchmarkResults),
      items: benchmarkResults,
    },
  };

  await writeJson(`${config.outputs.dir}/cullen-audit-report.json`, report);
  console.log(JSON.stringify({
    stage: "audit-cullen-oracle",
    output: `${config.outputs.dir}/cullen-audit-report.json`,
    benchmark: report.mini_gold_benchmark.summary,
  }, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
