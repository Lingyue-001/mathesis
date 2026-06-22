import fs from "node:fs/promises";
import path from "node:path";
import { readJson, resolveRepoPath, writeJson } from "./cullen-oracle-common.mjs";

const INPUT_PATH = "tmp/procedure-ir/cullen-procedure-anchors.json";
const OUTPUT_PATH = "tmp/procedure-ir/cullen-anchor-quality-audit.json";
const OUTPUT_MD_PATH = "tmp/procedure-ir/cullen-anchor-quality-audit.md";

function sortProcIds(procIds) {
  return [...new Set(procIds)]
    .sort((left, right) => {
      const leftMatch = String(left).match(/Proc\. ([234])\.(\d+)(?!\d)/u);
      const rightMatch = String(right).match(/Proc\. ([234])\.(\d+)(?!\d)/u);
      if (!leftMatch || !rightMatch) return String(left).localeCompare(String(right));
      return Number(leftMatch[1]) - Number(rightMatch[1]) || Number(leftMatch[2]) - Number(rightMatch[2]);
    });
}

function renderMarkdown(report) {
  const lines = [
    "# Cullen Anchor Quality Audit",
    "",
    `Generated: ${report.generated_at}`,
    "",
    `- anchor_count: ${report.anchor_count}`,
    `- chapter_2_anchor_count: ${report.chapter_2_anchor_count}`,
    `- chapter_3_anchor_count: ${report.chapter_3_anchor_count}`,
    `- tier_A_count: ${report.tier_A_count}`,
    `- tier_B_count: ${report.tier_B_count}`,
    `- tier_C_count: ${report.tier_C_count}`,
    `- tier_D_count: ${report.tier_D_count}`,
    `- anchors_without_source_span_candidates: ${report.anchors_without_source_span_candidates.length}`,
    `- anchors_without_claim_ids: ${report.anchors_without_claim_ids.length}`,
    `- anchors_without_operation_skeleton: ${report.anchors_without_operation_skeleton.length}`,
    `- multi_chunk_anchor_count: ${report.multi_chunk_anchor_count}`,
    `- anchors_with_heading_body_split: ${report.anchors_with_heading_body_split.length}`,
    `- source_alignment_warning_count: ${report.source_alignment_warning_count}`,
    `- claim_binding_warning_count: ${report.claim_binding_warning_count}`,
    "",
    `- B_needs_source_alignment: ${report.B_needs_source_alignment_anchors.join(", ") || "none"}`,
    `- C_needs_claim_enrichment: ${report.C_needs_claim_enrichment_anchors.join(", ") || "none"}`,
    `- D_needs_human_review: ${report.D_needs_human_review_anchors.join(", ") || "none"}`,
    `- anchors_with_heading_body_split: ${report.anchors_with_heading_body_split.join(", ") || "none"}`,
    `- anchors_without_claim_ids: ${report.anchors_without_claim_ids.join(", ") || "none"}`,
    `- anchors_without_source_span_candidates: ${report.anchors_without_source_span_candidates.join(", ") || "none"}`,
    "",
  ];

  return `${lines.join("\n")}\n`;
}

async function main() {
  const anchors = await readJson(INPUT_PATH);
  const chapterAnchors = (anchors.items ?? []).filter((item) => item.system === "santong" || item.system === "sifen");

  const report = {
    generated_at: new Date().toISOString(),
    anchor_count: chapterAnchors.length,
    chapter_2_anchor_count: chapterAnchors.filter((item) => item.system === "santong").length,
    chapter_3_anchor_count: chapterAnchors.filter((item) => item.system === "sifen").length,
    tier_A_count: chapterAnchors.filter((item) => item.quality_tier === "A_ready_for_phase2").length,
    tier_B_count: chapterAnchors.filter((item) => item.quality_tier === "B_needs_source_alignment").length,
    tier_C_count: chapterAnchors.filter((item) => item.quality_tier === "C_needs_claim_enrichment").length,
    tier_D_count: chapterAnchors.filter((item) => item.quality_tier === "D_needs_human_review").length,
    anchors_without_source_span_candidates: sortProcIds(chapterAnchors.filter((item) => !(item.source_span_candidates ?? []).length).map((item) => item.cullen_proc_id)),
    anchors_without_claim_ids: sortProcIds(chapterAnchors.filter((item) => !(item.claim_ids ?? []).length).map((item) => item.cullen_proc_id)),
    anchors_without_operation_skeleton: sortProcIds(chapterAnchors.filter((item) => !(item.operation_skeleton ?? []).length).map((item) => item.cullen_proc_id)),
    multi_chunk_anchor_count: chapterAnchors.filter((item) => (item.chunk_ids ?? []).length > 1).length,
    anchors_with_heading_body_split: sortProcIds(chapterAnchors.filter((item) => item.heading_body_split).map((item) => item.cullen_proc_id)),
    source_alignment_warning_count: chapterAnchors.filter((item) => (item.warnings ?? []).some((warning) => warning.includes("source_alignment") || warning.includes("no_source_span"))).length,
    claim_binding_warning_count: chapterAnchors.filter((item) => (item.warnings ?? []).some((warning) => warning.includes("claim"))).length,
    B_needs_source_alignment_anchors: sortProcIds(chapterAnchors.filter((item) => item.quality_tier === "B_needs_source_alignment").map((item) => item.cullen_proc_id)),
    C_needs_claim_enrichment_anchors: sortProcIds(chapterAnchors.filter((item) => item.quality_tier === "C_needs_claim_enrichment").map((item) => item.cullen_proc_id)),
    D_needs_human_review_anchors: sortProcIds(chapterAnchors.filter((item) => item.quality_tier === "D_needs_human_review").map((item) => item.cullen_proc_id)),
  };

  await writeJson(OUTPUT_PATH, report);
  const target = resolveRepoPath(OUTPUT_MD_PATH);
  await fs.mkdir(path.dirname(target), { recursive: true });
  await fs.writeFile(target, renderMarkdown(report), "utf8");

  console.log(JSON.stringify({
    stage: "audit-cullen-anchor-quality",
    output: OUTPUT_PATH,
    markdown_output: OUTPUT_MD_PATH,
    anchor_count: report.anchor_count,
    chapter_2_anchor_count: report.chapter_2_anchor_count,
    chapter_3_anchor_count: report.chapter_3_anchor_count,
    tier_A_count: report.tier_A_count,
    tier_B_count: report.tier_B_count,
    tier_C_count: report.tier_C_count,
    tier_D_count: report.tier_D_count,
    anchors_without_source_span_candidates: report.anchors_without_source_span_candidates,
    anchors_without_claim_ids: report.anchors_without_claim_ids,
    anchors_without_operation_skeleton: report.anchors_without_operation_skeleton,
    multi_chunk_anchor_count: report.multi_chunk_anchor_count,
    anchors_with_heading_body_split: report.anchors_with_heading_body_split,
    source_alignment_warning_count: report.source_alignment_warning_count,
    claim_binding_warning_count: report.claim_binding_warning_count,
  }, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
