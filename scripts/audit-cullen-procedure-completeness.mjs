import fs from "node:fs/promises";
import path from "node:path";
import { readJson, resolveRepoPath, writeJson } from "./cullen-oracle-common.mjs";
import {
  buildProcedureInventory,
  buildProcedureIdSet,
  chapterFromProcId,
  CULLEN_PROCEDURE_COMPLETENESS_AUDIT_JSON,
  CULLEN_PROCEDURE_COMPLETENESS_AUDIT_MD,
  writeProcedureInventoryOutputs,
} from "./cullen-procedure-inventory-common.mjs";

const CHUNKS_PATH = "tmp/procedure-ir/cullen-chunks.json";
const ANCHORS_PATH = "tmp/procedure-ir/cullen-procedure-anchors.json";

function sortProcIds(procIds) {
  return [...new Set(procIds)]
    .sort((left, right) => {
      const leftMatch = String(left).match(/Proc\. ([234])\.(\d+)(?!\d)/u);
      const rightMatch = String(right).match(/Proc\. ([234])\.(\d+)(?!\d)/u);
      if (!leftMatch || !rightMatch) return String(left).localeCompare(String(right));
      return Number(leftMatch[1]) - Number(rightMatch[1]) || Number(leftMatch[2]) - Number(rightMatch[2]);
    });
}

function duplicateProcIds(items) {
  const counts = new Map();
  for (const item of items ?? []) {
    counts.set(item.proc_id, (counts.get(item.proc_id) ?? 0) + 1);
  }
  return sortProcIds([...counts.entries()].filter(([, count]) => count > 1).map(([procId]) => procId));
}

function coverageRate(anchorCount, inventoryCount) {
  if (!inventoryCount) return 0;
  return Number((anchorCount / inventoryCount).toFixed(4));
}

function renderMarkdown(report) {
  const lines = [
    "# Cullen Procedure Completeness Audit",
    "",
    `Generated: ${report.generated_at}`,
    "",
    `- inventory_proc_count: ${report.inventory_proc_count}`,
    `- chapter_2_inventory_count: ${report.chapter_2_inventory_count}`,
    `- chapter_3_inventory_count: ${report.chapter_3_inventory_count}`,
    `- chapter_4_inventory_count: ${report.chapter_4_inventory_count}`,
    `- anchor_proc_count: ${report.anchor_proc_count}`,
    `- chapter_2_anchor_count: ${report.chapter_2_anchor_count}`,
    `- chapter_3_anchor_count: ${report.chapter_3_anchor_count}`,
    `- chapter_4_anchor_count: ${report.chapter_4_anchor_count}`,
    `- chapter_2_anchor_coverage_rate: ${report.chapter_2_anchor_coverage_rate}`,
    `- chapter_3_anchor_coverage_rate: ${report.chapter_3_anchor_coverage_rate}`,
    "",
    `- proc_ids_in_inventory_not_anchored: ${report.proc_ids_in_inventory_not_anchored.join(", ") || "none"}`,
    `- proc_ids_anchored_not_in_inventory: ${report.proc_ids_anchored_not_in_inventory.join(", ") || "none"}`,
    `- duplicate_proc_ids: ${report.duplicate_proc_ids.join(", ") || "none"}`,
    `- proc_ids_with_no_chunk: ${report.proc_ids_with_no_chunk.join(", ") || "none"}`,
    `- proc_ids_with_no_title: ${report.proc_ids_with_no_title.join(", ") || "none"}`,
    `- proc_ids_with_garbled_chinese: ${report.proc_ids_with_garbled_chinese.join(", ") || "none"}`,
    `- anchors_with_no_source_span_candidates: ${report.anchors_with_no_source_span_candidates.join(", ") || "none"}`,
    `- anchors_with_no_claim_ids: ${report.anchors_with_no_claim_ids.join(", ") || "none"}`,
    "",
  ];

  return `${lines.join("\n")}\n`;
}

async function main() {
  const [chunksPayload, anchors] = await Promise.all([
    readJson(CHUNKS_PATH),
    readJson(ANCHORS_PATH),
  ]);

  const inventory = buildProcedureInventory({
    chunks: chunksPayload.chunks ?? [],
    existingAnchors: anchors,
  });
  await writeProcedureInventoryOutputs(inventory);

  const inventoryProcIds = buildProcedureIdSet(inventory.items ?? []);
  const anchorProcIds = new Set((anchors.items ?? []).map((item) => item.cullen_proc_id));
  const chapter2Inventory = (inventory.items ?? []).filter((item) => item.chapter === 2);
  const chapter3Inventory = (inventory.items ?? []).filter((item) => item.chapter === 3);
  const chapter4Inventory = (inventory.items ?? []).filter((item) => item.chapter === 4);
  const chapter2Anchors = (anchors.items ?? []).filter((item) => chapterFromProcId(item.cullen_proc_id) === 2);
  const chapter3Anchors = (anchors.items ?? []).filter((item) => chapterFromProcId(item.cullen_proc_id) === 3);
  const chapter4Anchors = (anchors.items ?? []).filter((item) => chapterFromProcId(item.cullen_proc_id) === 4);

  const report = {
    generated_at: new Date().toISOString(),
    inventory_proc_count: (inventory.items ?? []).length,
    chapter_2_inventory_count: chapter2Inventory.length,
    chapter_3_inventory_count: chapter3Inventory.length,
    chapter_4_inventory_count: chapter4Inventory.length,
    anchor_proc_count: (anchors.items ?? []).length,
    chapter_2_anchor_count: chapter2Anchors.length,
    chapter_3_anchor_count: chapter3Anchors.length,
    chapter_4_anchor_count: chapter4Anchors.length,
    chapter_2_anchor_coverage_rate: coverageRate(chapter2Anchors.length, chapter2Inventory.length),
    chapter_3_anchor_coverage_rate: coverageRate(chapter3Anchors.length, chapter3Inventory.length),
    proc_ids_in_inventory_not_anchored: sortProcIds(
      [...inventoryProcIds].filter((procId) => {
        const chapter = chapterFromProcId(procId);
        return [2, 3].includes(chapter) && !anchorProcIds.has(procId);
      })
    ),
    proc_ids_anchored_not_in_inventory: sortProcIds(
      [...anchorProcIds].filter((procId) => !inventoryProcIds.has(procId))
    ),
    duplicate_proc_ids: duplicateProcIds(inventory.items ?? []),
    proc_ids_with_no_chunk: sortProcIds(
      (inventory.items ?? []).filter((item) => !(item.chunk_ids ?? []).length).map((item) => item.proc_id)
    ),
    proc_ids_with_no_title: sortProcIds(
      (inventory.items ?? []).filter((item) => !item.english_title).map((item) => item.proc_id)
    ),
    proc_ids_with_garbled_chinese: sortProcIds(
      (inventory.items ?? []).filter((item) => item.source_text_quality === "garbled").map((item) => item.proc_id)
    ),
    anchors_with_no_source_span_candidates: sortProcIds(
      (anchors.items ?? []).filter((item) => !(item.source_span_candidates ?? []).length).map((item) => item.cullen_proc_id)
    ),
    anchors_with_no_claim_ids: sortProcIds(
      (anchors.items ?? []).filter((item) => !(item.claim_ids ?? []).length).map((item) => item.cullen_proc_id)
    ),
  };

  await writeJson(CULLEN_PROCEDURE_COMPLETENESS_AUDIT_JSON, report);
  const markdown = renderMarkdown(report);
  const markdownTarget = resolveRepoPath(CULLEN_PROCEDURE_COMPLETENESS_AUDIT_MD);
  await fs.mkdir(path.dirname(markdownTarget), { recursive: true });
  await fs.writeFile(markdownTarget, markdown, "utf8");

  console.log(JSON.stringify({
    stage: "audit-cullen-procedure-completeness",
    output: CULLEN_PROCEDURE_COMPLETENESS_AUDIT_JSON,
    markdown_output: CULLEN_PROCEDURE_COMPLETENESS_AUDIT_MD,
    inventory_proc_count: report.inventory_proc_count,
    chapter_2_inventory_count: report.chapter_2_inventory_count,
    chapter_3_inventory_count: report.chapter_3_inventory_count,
    chapter_4_inventory_count: report.chapter_4_inventory_count,
    anchor_proc_count: report.anchor_proc_count,
    chapter_2_anchor_count: report.chapter_2_anchor_count,
    chapter_3_anchor_count: report.chapter_3_anchor_count,
    chapter_4_anchor_count: report.chapter_4_anchor_count,
    chapter_2_anchor_coverage_rate: report.chapter_2_anchor_coverage_rate,
    chapter_3_anchor_coverage_rate: report.chapter_3_anchor_coverage_rate,
    proc_ids_in_inventory_not_anchored: report.proc_ids_in_inventory_not_anchored,
    anchors_with_no_source_span_candidates: report.anchors_with_no_source_span_candidates,
    anchors_with_no_claim_ids: report.anchors_with_no_claim_ids,
  }, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
