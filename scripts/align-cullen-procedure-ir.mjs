import {
  readJson,
  readPipelineConfig,
  writeJson,
} from "./cullen-oracle-common.mjs";
import {
  buildConstantIndex,
  buildOperationSignature,
  evaluateGroundingStatus,
  operationSignatureString,
  quantitySignature,
  resolveQuantityReference,
  termMatchScore,
} from "./procedure-ir-common.mjs";

function systemCompatibilityScore(stepSystem, claimSystem) {
  if (!claimSystem) return 0;
  return stepSystem === claimSystem ? 2 : -2;
}

function compareQuantities(stepQuantity, claimQuantity) {
  if (!stepQuantity || !claimQuantity) return 0;
  return termMatchScore(stepQuantity, claimQuantity);
}

function compareInputLists(stepInputs, claimInputs) {
  if (!stepInputs.length || !claimInputs.length) return 0;
  let score = 0;
  const remaining = [...claimInputs];
  for (const input of stepInputs) {
    let bestIndex = -1;
    let bestScore = 0;
    for (let index = 0; index < remaining.length; index += 1) {
      const candidateScore = compareQuantities(input, remaining[index]);
      if (candidateScore > bestScore) {
        bestScore = candidateScore;
        bestIndex = index;
      }
    }
    if (bestIndex >= 0) {
      score += bestScore;
      remaining.splice(bestIndex, 1);
    }
  }
  return score;
}

function scoreAlignment(step, claim) {
  const stepSignature = step.signature;
  let score = 0;

  if (stepSignature.operation_type && claim.operation_type && stepSignature.operation_type === claim.operation_type) {
    score += 4;
  } else if (stepSignature.operation_type && claim.operation_type) {
    return { score: -5, reasons: ["operation_type_mismatch"] };
  }

  score += systemCompatibilityScore(step.source_id, claim.system);
  score += compareInputLists(stepSignature.inputs ?? [], claim.inputs ?? []);
  score += compareQuantities(stepSignature.output, claim.output);
  score += compareQuantities(stepSignature.divisor, claim.divisor);
  score += compareQuantities(stepSignature.quotient, claim.quotient);
  score += compareQuantities(stepSignature.remainder, claim.remainder);

  if (
    stepSignature.modulus !== null
    && claim.modulus !== null
    && stepSignature.modulus === claim.modulus
  ) {
    score += 2;
  }

  const reasons = [];
  if (compareInputLists(stepSignature.inputs ?? [], claim.inputs ?? []) > 0) reasons.push("inputs_aligned");
  if (compareQuantities(stepSignature.output, claim.output) > 0) reasons.push("output_aligned");
  if (compareQuantities(stepSignature.divisor, claim.divisor) > 0) reasons.push("divisor_aligned");
  if (compareQuantities(stepSignature.remainder, claim.remainder) > 0) reasons.push("remainder_aligned");
  if (step.source_id === claim.system && claim.system) reasons.push("system_aligned");

  return { score, reasons };
}

function statusFromScore(score) {
  if (score >= 10) return "direct_support";
  if (score >= 6) return "partial_support";
  if (score >= 3) return "weak_support";
  return "unmatched";
}

function claimSummary(claim, score, reasons) {
  return {
    claim_id: claim.id,
    score,
    reasons,
    claim_type: claim.claim_type,
    operation_type: claim.operation_type,
    system: claim.system,
    english_terms: claim.english_terms,
    values: claim.values,
    evidence_chunk: claim.evidence_chunk,
    formula_text: claim.formula_text,
  };
}

function hydrateStepQuantities(step, constantIndex) {
  const hydrate = (quantity) => {
    if (!quantity || quantity.quantity_value_source !== "unresolved_reference") return quantity;
    return resolveQuantityReference(
      quantity.normalized_name ?? quantity.name_zh,
      step.source_id,
      constantIndex,
      step.source_span_id,
    );
  };

  step.inputs = (step.inputs ?? []).map(hydrate);
  step.output = hydrate(step.output);
  step.divisor = hydrate(step.divisor);
  step.quotient = hydrate(step.quotient);
  step.remainder = hydrate(step.remainder);
  step.signature = buildOperationSignature(step);
  step.operation_signature = operationSignatureString(step);
  return step;
}

function refreshValidationAndProcedures(procedurePayload, validationPayload, alignments) {
  const alignmentMap = new Map(alignments.map((item) => [item.step_id, item]));
  const checkMap = new Map((validationPayload.checks ?? []).map((item) => [item.step_id, item]));
  const constantIndex = buildConstantIndex(validationPayload.extracted_constants ?? []);

  for (const procedure of procedurePayload.procedures ?? []) {
    for (const step of procedure.steps ?? []) {
      hydrateStepQuantities(step, constantIndex);
      const alignment = alignmentMap.get(step.step_id) ?? null;
      const check = checkMap.get(step.step_id);
      if (!check) continue;
      check.cullen_grounding = alignment;
      check.grounding_status = evaluateGroundingStatus(step, alignment, check.status);
      step.validation_status = check.grounding_status === "A_confirmed"
        ? "PASS"
        : check.status === "fail"
          ? "FAIL"
          : "NEEDS_REVIEW";
    }
  }

  validationPayload.summary.cullen_grounding_metrics = {
    A_confirmed: validationPayload.checks.filter((item) => item.grounding_status === "A_confirmed").length,
    B_textual_internal: validationPayload.checks.filter((item) => item.grounding_status === "B_textual_internal").length,
    B_textual_partial: validationPayload.checks.filter((item) => item.grounding_status === "B_textual_partial").length,
    B_supported_with_semantic_count: validationPayload.checks.filter((item) => item.grounding_status === "B_supported_with_semantic_count").length,
    needs_review: validationPayload.checks.filter((item) => item.grounding_status === "needs_review").length,
  };

  return { procedurePayload, validationPayload };
}

async function main() {
  const config = await readPipelineConfig();
  const procedurePayload = await readJson(`${config.outputs.dir}/procedure_IR.json`);
  const claimsPayload = await readJson(config.inputs.cullen.artifacts.claims);
  const validationPayload = await readJson(`${config.outputs.dir}/validation_report.json`);
  const constantIndex = buildConstantIndex(validationPayload.extracted_constants ?? []);
  const alignments = [];

  for (const procedure of procedurePayload.procedures ?? []) {
    for (const step of procedure.steps ?? []) {
      hydrateStepQuantities(step, constantIndex);
    }
  }

  for (const procedure of procedurePayload.procedures) {
    for (const step of procedure.steps) {
      const ranked = claimsPayload.claims
        .filter((claim) => claim.operation_type)
        .map((claim) => {
          const { score, reasons } = scoreAlignment(step, claim);
          return { claim, score, reasons };
        })
        .filter((item) => item.score > 0)
        .sort((left, right) => right.score - left.score)
        .slice(0, 5);

      const best = ranked[0] ?? null;
      alignments.push({
        step_id: step.id,
        procedure_id: procedure.id,
        source_id: procedure.source_id,
        operation_type: step.operation_type,
        expression: step.expression,
        operation_signature: step.operation_signature,
        signature: step.signature,
        matched_cullen_claim_id: best?.claim?.id ?? null,
        alignment_basis: best?.reasons ?? [],
        alignment_status: best ? statusFromScore(best.score) : "no_support",
        status: best ? statusFromScore(best.score) : "no_support",
        best_score: best?.score ?? 0,
        confidence_after_alignment: best
          ? (statusFromScore(best.score) === "direct_support"
            ? "A_confirmed"
            : statusFromScore(best.score) === "partial_support"
              ? "B_partial"
              : "B_textual_internal")
          : "needs_review",
        matches: ranked.map((item) => claimSummary(item.claim, item.score, item.reasons)),
      });
    }
  }

  const deduped = [];
  const seen = new Set();
  for (const alignment of alignments) {
    if (seen.has(alignment.step_id)) continue;
    seen.add(alignment.step_id);
    deduped.push(alignment);
  }

  await writeJson(config.inputs.cullen.artifacts.alignments, {
    generated_at: new Date().toISOString(),
    alignment_count: deduped.length,
    alignments: deduped,
  });

  const refreshed = refreshValidationAndProcedures(procedurePayload, validationPayload, deduped);
  await writeJson(`${config.outputs.dir}/procedure_IR.json`, refreshed.procedurePayload);
  await writeJson(`${config.outputs.dir}/validation_report.json`, refreshed.validationPayload);

  console.log(JSON.stringify({
    stage: "align-cullen-procedure-ir",
    alignment_count: deduped.length,
    output: config.inputs.cullen.artifacts.alignments,
  }, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
