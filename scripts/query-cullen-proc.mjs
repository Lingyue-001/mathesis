import {
  collectAnchorConstants,
  collectAnchorOperations,
  collectAnchorWarnings,
  findAnchorsForProc,
  sanitizeForFileSegment,
  writeDebugMarkdown,
} from "./cullen-procedure-anchor-common.mjs";
import { readJson } from "./cullen-oracle-common.mjs";

function getArg(flag) {
  const index = process.argv.indexOf(flag);
  return index >= 0 ? process.argv[index + 1] : null;
}

function renderClaim(claim) {
  return [
    `- ${claim.claim_id}`,
    `  evidence_chunk_id: ${claim.evidence_chunk_id ?? "null"}`,
    `  procedure_family: ${claim.procedure_family ?? "unknown"}`,
    `  evidence_text: ${claim.evidence_text ?? claim.formula_text ?? ""}`,
  ].join("\n");
}

async function main() {
  const procQuery = getArg("--proc");
  if (!procQuery) throw new Error("Missing --proc value");

  const [anchors, claims, chunks, sourceSpans] = await Promise.all([
    readJson("tmp/procedure-ir/cullen-procedure-anchors.json"),
    readJson("tmp/procedure-ir/cullen-claimbank.json"),
    readJson("tmp/procedure-ir/cullen-chunks.json"),
    readJson("tmp/procedure-ir/source_spans.json"),
  ]);

  const anchorMatches = findAnchorsForProc(anchors, procQuery);
  const claimById = new Map((claims.claims ?? []).map((claim) => [claim.claim_id, claim]));
  const chunkById = new Map((chunks.chunks ?? []).map((chunk) => [chunk.id, chunk]));
  const spanById = new Map((sourceSpans.spans ?? []).map((span) => [span.id, span]));

  const lines = [
    `# Cullen Proc Query: ${procQuery}`,
    "",
  ];

  if (!anchorMatches.length) {
    lines.push("No matching procedure anchors found.");
  } else {
    for (const anchor of anchorMatches) {
      const matchedClaims = (anchor.claim_ids ?? []).map((claimId) => claimById.get(claimId)).filter(Boolean);
      const matchedChunks = (anchor.chunk_ids ?? []).map((chunkId) => chunkById.get(chunkId)).filter(Boolean);
      const sourceCandidates = (anchor.source_span_candidates ?? []).map((sourceSpanId) => spanById.get(sourceSpanId)).filter(Boolean);

      lines.push(`## ${anchor.cullen_proc_id}`);
      lines.push(`- english_title: ${anchor.english_title}`);
      lines.push(`- procedure_family: ${anchor.procedure_family}`);
      lines.push(`- quality_tier: ${anchor.quality_tier ?? "unknown"}`);
      lines.push(`- alignment_status: ${anchor.alignment_status ?? "none"}`);
      lines.push(`- claim_binding_status: ${anchor.claim_binding_status ?? "none"}`);
      lines.push(`- anchor_confidence: ${anchor.anchor_confidence}`);
      lines.push(`- source_span_candidates: ${(anchor.source_span_candidates ?? []).join(", ") || "none"}`);
      lines.push(`- heading_chunk_ids: ${(anchor.heading_chunk_ids ?? []).join(", ") || "none"}`);
      lines.push(`- body_chunk_ids: ${(anchor.body_chunk_ids ?? []).join(", ") || "none"}`);
      lines.push(`- commentary_chunk_ids: ${(anchor.commentary_chunk_ids ?? []).join(", ") || "none"}`);
      lines.push(`- matched_constants: ${collectAnchorConstants([anchor]).join(", ") || "none"}`);
      lines.push(`- operation_skeleton: ${collectAnchorOperations([anchor]).join(" | ") || "none"}`);
      lines.push(`- warnings: ${collectAnchorWarnings(anchor).join(", ") || "none"}`);
      lines.push("");
      lines.push("### Combined excerpt", "");
      lines.push(anchor.combined_excerpt || "- none");
      lines.push("");
      lines.push("### Matched claims");
      lines.push("");
      lines.push(matchedClaims.length ? matchedClaims.map((claim) => renderClaim(claim)).join("\n") : "- none");
      lines.push("");
      lines.push("### Chunks");
      lines.push("");
      if (!matchedChunks.length) {
        lines.push("- none");
      } else {
        for (const chunk of matchedChunks) {
          lines.push(`- ${chunk.id} (pages ${chunk.page_start}-${chunk.page_end})`);
          lines.push(`  text: ${chunk.text}`);
        }
      }
      lines.push("");
      lines.push("### Source spans");
      lines.push("");
      if (!sourceCandidates.length) {
        lines.push("- none");
      } else {
        for (const span of sourceCandidates) {
          lines.push(`- ${span.id}: ${span.text}`);
        }
      }
      lines.push("");
    }
  }

  const markdown = `${lines.join("\n")}\n`;
  const outputName = `cullen-proc-${sanitizeForFileSegment(procQuery)}.md`;
  const outputPath = await writeDebugMarkdown(outputName, markdown);
  process.stdout.write(markdown);
  console.error(`Saved debug markdown: ${outputPath}`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
