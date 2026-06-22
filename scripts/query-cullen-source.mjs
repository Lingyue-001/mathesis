import {
  collectAnchorConstants,
  collectAnchorOperations,
  collectAnchorWarnings,
  findAnchorsForSourceSpan,
  sanitizeForFileSegment,
  writeDebugMarkdown,
} from "./cullen-procedure-anchor-common.mjs";
import { readJson } from "./cullen-oracle-common.mjs";

function getArg(flag) {
  const index = process.argv.indexOf(flag);
  return index >= 0 ? process.argv[index + 1] : null;
}

function renderDiagnostic(diagnostic) {
  return [
    `- ${diagnostic.claim_id}`,
    `  procedure_family: ${diagnostic.procedure_family ?? "unknown"}`,
    `  candidate_status: ${diagnostic.candidate_status ?? "unknown"}`,
    `  match_strength: ${diagnostic.match_strength ?? "weak"}`,
    `  evidence_chunk_id: ${diagnostic.evidence_chunk_id ?? "null"}`,
    `  matched_terms: ${(diagnostic.matched_chinese_terms ?? []).join(", ") || "none"} | ${(diagnostic.matched_english_terms ?? []).join(", ") || "none"}`,
    `  operation_types: ${(diagnostic.matched_operation_types ?? []).join(", ") || "none"}`,
    `  warnings: ${(diagnostic.mismatch_warning ?? []).join(", ") || "none"}`,
    `  evidence_text: ${diagnostic.evidence_text ?? ""}`,
  ].join("\n");
}

async function main() {
  const sourceSpanId = getArg("--source");
  if (!sourceSpanId) throw new Error("Missing --source value");

  const [anchors, sourceSpans, coverage, procedureIr] = await Promise.all([
    readJson("tmp/procedure-ir/cullen-procedure-anchors.json"),
    readJson("tmp/procedure-ir/source_spans.json"),
    readJson("tmp/procedure-ir/cullen-coverage-matrix.json"),
    readJson("tmp/procedure-ir/procedure_IR.json"),
  ]);

  const span = (sourceSpans.spans ?? []).find((item) => item.id === sourceSpanId);
  const coverageEntry = (coverage.source_span_coverage ?? []).find((item) => item.source_span_id === sourceSpanId);
  const procedure = (procedureIr.procedures ?? []).find((item) => item.source_span_id === sourceSpanId);
  const matchedAnchors = findAnchorsForSourceSpan(anchors, sourceSpanId);

  const acceptedClaims = (coverageEntry?.claim_match_diagnostics ?? []).filter((item) => item.candidate_status === "compatible_candidate");
  const noisyClaims = (coverageEntry?.claim_match_diagnostics ?? []).filter((item) => item.candidate_status === "noisy_candidate");

  const lines = [
    `# Cullen Source Query: ${sourceSpanId}`,
    "",
    `- source_span: ${sourceSpanId}`,
    `- source_text: ${span?.text ?? "not found"}`,
    `- procedure_title: ${procedure?.title_guess ?? "null"}`,
    `- procedure_family: ${coverageEntry?.procedure_family ?? "unknown"}`,
    `- cullen_evidence_status: ${coverageEntry?.cullen_evidence_status ?? "none"}`,
    `- alignment_status: ${coverageEntry?.alignment_status ?? "no_alignment_signal"}`,
    `- validation_status: ${coverageEntry?.validation_status ?? "no_validation_checks"}`,
    `- final_confidence: ${coverageEntry?.final_confidence ?? "needs_review"}`,
    `- blocking_reason: ${coverageEntry?.blocking_reason ?? "none"}`,
    "",
    "## Procedure anchors",
    "",
  ];

  if (!matchedAnchors.length) {
    lines.push("- none", "");
  } else {
    for (const anchor of matchedAnchors) {
      lines.push(`- ${anchor.cullen_proc_id}: ${anchor.english_title}`);
      lines.push(`  quality_tier: ${anchor.quality_tier ?? "unknown"}`);
      lines.push(`  alignment_status: ${anchor.alignment_status ?? "none"}`);
      lines.push(`  claim_binding_status: ${anchor.claim_binding_status ?? "none"}`);
      lines.push(`  heading_chunk_ids: ${(anchor.heading_chunk_ids ?? []).join(", ") || "none"}`);
      lines.push(`  body_chunk_ids: ${(anchor.body_chunk_ids ?? []).join(", ") || "none"}`);
      lines.push(`  commentary_chunk_ids: ${(anchor.commentary_chunk_ids ?? []).join(", ") || "none"}`);
      lines.push(`  matched_constants: ${collectAnchorConstants([anchor]).join(", ") || "none"}`);
      lines.push(`  operation_skeleton: ${collectAnchorOperations([anchor]).join(" | ") || "none"}`);
      lines.push(`  warnings: ${collectAnchorWarnings(anchor).join(", ") || "none"}`);
      lines.push(`  combined_excerpt: ${anchor.combined_excerpt ?? "none"}`);
    }
    lines.push("");
  }

  lines.push("## Accepted candidate claims", "");
  lines.push(acceptedClaims.length ? acceptedClaims.map((item) => renderDiagnostic(item)).join("\n") : "- none");
  lines.push("");
  lines.push("## Noisy candidate claims", "");
  lines.push(noisyClaims.length ? noisyClaims.map((item) => renderDiagnostic(item)).join("\n") : "- none");
  lines.push("");

  const markdown = `${lines.join("\n")}\n`;
  const outputName = `cullen-source-${sanitizeForFileSegment(sourceSpanId)}.md`;
  const outputPath = await writeDebugMarkdown(outputName, markdown);
  process.stdout.write(markdown);
  console.error(`Saved debug markdown: ${outputPath}`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
