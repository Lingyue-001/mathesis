import fs from "node:fs/promises";
import { readJson, readPipelineConfig, writeJson } from "./cullen-oracle-common.mjs";

const TARGET_SPAN_IDS = [
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

function normalizeProcedureLabel(text) {
  return String(text ?? "")
    .replace(/[：:]/gu, "")
    .replace(/術曰|术曰|術|术|曰/gu, "")
    .replace(/\s+/gu, "")
    .trim();
}

function summarizeAlignmentQuality(diagnostics) {
  const qualities = diagnostics.map((item) => item.alignment_quality);
  if (qualities.includes("good")) return "good";
  if (qualities.includes("plausible")) return "plausible";
  if (qualities.includes("noisy")) return "noisy";
  return "wrong";
}

function unique(items) {
  return [...new Set(items)];
}

function toMarkdown(report) {
  const lines = [
    "# Cullen Target-Span Alignment Quality Audit",
    "",
    `Generated: ${report.generated_at}`,
    "",
  ];

  for (const item of report.spans) {
    lines.push(`## ${item.source_span_id}`);
    lines.push(`- procedure_label: ${item.normalized_procedure_label}`);
    lines.push(`- procedure_family: ${item.procedure_family}`);
    lines.push(`- alignment_quality: ${item.alignment_quality}`);
    lines.push(`- cullen_evidence_status: ${item.cullen_evidence_status}`);
    lines.push(`- alignment_status: ${item.alignment_status}`);
    lines.push(`- validation_status: ${item.validation_status}`);
    lines.push(`- final_confidence: ${item.final_confidence}`);
    lines.push(`- coverage_status: ${item.coverage_status}`);
    lines.push(`- blocking_reason: ${item.blocking_reason ?? "none"}`);
    if (item.noisy_candidate_claims.length) {
      lines.push(`- noisy_candidate_claims: ${item.noisy_candidate_claims.join(", ")}`);
    }
    lines.push(`- source_text: ${item.source_text}`);
    lines.push("");
    for (const claim of item.matched_claims) {
      lines.push(`### ${claim.claim_id}`);
      lines.push(`- cullen_procedure_title: ${claim.cullen_procedure_title ?? "null"}`);
      lines.push(`- procedure_family: ${claim.procedure_family}`);
      lines.push(`- candidate_status: ${claim.candidate_status}`);
      lines.push(`- alignment_quality: ${claim.alignment_quality}`);
      lines.push(`- match_strength: ${claim.match_strength ?? "weak"}`);
      lines.push(`- distinctive_terms: ${claim.distinctive_terms.join(", ") || "none"}`);
      lines.push(`- matched_chinese_terms: ${claim.matched_chinese_terms.join(", ") || "none"}`);
      lines.push(`- matched_english_terms: ${claim.matched_english_terms.join(", ") || "none"}`);
      lines.push(`- matched_numbers: ${claim.matched_numbers.join(", ") || "none"}`);
      lines.push(`- matched_operation_types: ${claim.matched_operation_types.join(", ") || "none"}`);
      lines.push(`- match_reason: ${claim.match_reason}`);
      lines.push(`- mismatch_warning: ${claim.mismatch_warning.join("; ") || "none"}`);
      lines.push(`- evidence_text: ${claim.evidence_text}`);
      lines.push("");
    }
  }

  return `${lines.join("\n")}\n`;
}

async function main() {
  const config = await readPipelineConfig();
  const [sourceSpans, procedureIr, coverageMatrix, claimBank] = await Promise.all([
    readJson(`${config.outputs.dir}/source_spans.json`),
    readJson(`${config.outputs.dir}/procedure_IR.json`),
    readJson(`${config.outputs.dir}/cullen-coverage-matrix.json`),
    readJson(`${config.outputs.dir}/cullen-claimbank.json`),
  ]);

  const spanById = new Map((sourceSpans.spans ?? []).map((span) => [span.id, span]));
  const procedureBySpanId = new Map((procedureIr.procedures ?? []).map((procedure) => [procedure.source_span_id, procedure]));
  const claimById = new Map((claimBank.claims ?? []).map((claim) => [claim.claim_id, claim]));
  const coverageBySpanId = new Map((coverageMatrix.source_span_coverage ?? []).map((entry) => [entry.source_span_id, entry]));

  const spans = TARGET_SPAN_IDS.map((sourceSpanId) => {
    const span = spanById.get(sourceSpanId);
    const procedure = procedureBySpanId.get(sourceSpanId) ?? null;
    const coverage = coverageBySpanId.get(sourceSpanId) ?? null;
    const diagnostics = coverage?.claim_match_diagnostics ?? [];
    const matchedClaims = diagnostics.map((diagnostic) => {
      const claim = claimById.get(diagnostic.claim_id) ?? null;
      return {
        ...diagnostic,
        cullen_procedure_title: diagnostic.cullen_procedure_title ?? claim?.procedure_name ?? null,
        matched_english_terms: unique(diagnostic.matched_english_terms ?? []),
        matched_chinese_terms: unique(diagnostic.matched_chinese_terms ?? []),
        matched_numbers: unique(diagnostic.matched_numbers ?? []),
        matched_operation_types: unique(diagnostic.matched_operation_types ?? []),
        distinctive_terms: unique(diagnostic.distinctive_terms ?? []),
        match_strength: diagnostic.match_strength ?? "weak",
        evidence_text: diagnostic.evidence_text ?? claim?.evidence_text ?? claim?.formula_text ?? "",
      };
    });

    return {
      source_span_id: sourceSpanId,
      source_text: span?.text ?? null,
      source_procedure_title: procedure?.title_guess ?? null,
      normalized_procedure_label: normalizeProcedureLabel(procedure?.title_guess ?? span?.text ?? ""),
      procedure_family: coverage?.procedure_family ?? "unknown",
      cullen_evidence_status: coverage?.cullen_evidence_status ?? "none",
      alignment_status: coverage?.alignment_status ?? "no_alignment_signal",
      validation_status: coverage?.validation_status ?? "no_validation_checks",
      final_confidence: coverage?.final_confidence ?? "needs_review",
      coverage_status: coverage?.coverage_status ?? "not_covered",
      blocking_reason: coverage?.blocking_reason ?? null,
      matched_cullen_claim_ids: coverage?.matched_cullen_claims ?? [],
      noisy_candidate_claims: coverage?.noisy_candidate_claims ?? [],
      matched_claims: matchedClaims,
      alignment_quality: summarizeAlignmentQuality(matchedClaims),
    };
  });

  const report = {
    generated_at: new Date().toISOString(),
    target_span_ids: TARGET_SPAN_IDS,
    spans,
  };

  await writeJson(`${config.outputs.dir}/cullen-target-span-alignment-quality.json`, report);
  await fs.writeFile(
    `${config.outputs.dir}/cullen-target-span-alignment-quality.md`,
    toMarkdown(report),
    "utf8",
  );

  console.log(JSON.stringify({
    stage: "audit-cullen-target-span-alignment",
    output: `${config.outputs.dir}/cullen-target-span-alignment-quality.json`,
    span_count: spans.length,
  }, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
