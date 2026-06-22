import {
  collectAnchorConstants,
  collectAnchorOperations,
  collectAnchorSourceSpans,
  collectAnchorWarnings,
  findAnchorsForPage,
  sanitizeForFileSegment,
  writeDebugMarkdown,
} from "./cullen-procedure-anchor-common.mjs";
import { readJson } from "./cullen-oracle-common.mjs";

function getArg(flag) {
  const index = process.argv.indexOf(flag);
  return index >= 0 ? process.argv[index + 1] : null;
}

async function main() {
  const pageValue = Number(getArg("--page"));
  if (!Number.isFinite(pageValue)) throw new Error("Missing or invalid --page value");

  const [anchors, claims, chunks] = await Promise.all([
    readJson("tmp/procedure-ir/cullen-procedure-anchors.json"),
    readJson("tmp/procedure-ir/cullen-claimbank.json"),
    readJson("tmp/procedure-ir/cullen-chunks.json"),
  ]);

  const pageChunks = (chunks.chunks ?? []).filter((chunk) => pageValue >= chunk.page_start && pageValue <= chunk.page_end);
  const pageChunkIds = new Set(pageChunks.map((chunk) => chunk.id));
  const matchedClaims = (claims.claims ?? []).filter((claim) => pageChunkIds.has(claim.evidence_chunk_id));
  const matchedAnchors = findAnchorsForPage(anchors, pageValue);

  const lines = [
    `# Cullen Page Query: ${pageValue}`,
    "",
    "## Page text / chunks",
    "",
  ];

  if (!pageChunks.length) {
    lines.push("- none", "");
  } else {
    for (const chunk of pageChunks) {
      lines.push(`- ${chunk.id} (pages ${chunk.page_start}-${chunk.page_end})`);
      lines.push(`  text: ${chunk.text}`);
    }
    lines.push("");
  }

  lines.push("## Matched claims", "");
  if (!matchedClaims.length) {
    lines.push("- none", "");
  } else {
    for (const claim of matchedClaims) {
      lines.push(`- ${claim.claim_id}`);
      lines.push(`  procedure_family: ${claim.procedure_family ?? "unknown"}`);
      lines.push(`  evidence_chunk_id: ${claim.evidence_chunk_id ?? "null"}`);
      lines.push(`  evidence_text: ${claim.evidence_text ?? claim.formula_text ?? ""}`);
    }
    lines.push("");
  }

  lines.push("## Procedure anchors", "");
  if (!matchedAnchors.length) {
    lines.push("- none", "");
  } else {
    for (const anchor of matchedAnchors) {
      lines.push(`- ${anchor.cullen_proc_id}: ${anchor.english_title}`);
      lines.push(`  source_span: ${collectAnchorSourceSpans([anchor]).join(", ") || "none"}`);
      lines.push(`  matched_constants: ${collectAnchorConstants([anchor]).join(", ") || "none"}`);
      lines.push(`  operation_skeleton: ${collectAnchorOperations([anchor]).join(" | ") || "none"}`);
      lines.push(`  warnings: ${collectAnchorWarnings(anchor).join(", ") || "none"}`);
    }
    lines.push("");
  }

  const markdown = `${lines.join("\n")}\n`;
  const outputName = `cullen-page-${sanitizeForFileSegment(String(pageValue))}.md`;
  const outputPath = await writeDebugMarkdown(outputName, markdown);
  process.stdout.write(markdown);
  console.error(`Saved debug markdown: ${outputPath}`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
