import fs from "node:fs/promises";
import path from "node:path";
import { readJson, resolveRepoPath, writeJson } from "./cullen-oracle-common.mjs";
import {
  REQUIRED_SANTONG_PROC_IDS,
  REQUIRED_SIFEN_PROC_IDS,
} from "./cullen-procedure-anchor-common.mjs";

const INPUT_PATH = "tmp/procedure-ir/cullen-procedure-anchors.json";
const SOURCE_SPANS_PATH = "tmp/procedure-ir/source_spans.json";
const PROCEDURE_IR_PATH = "tmp/procedure-ir/procedure_IR.json";
const COVERAGE_PATH = "tmp/procedure-ir/cullen-coverage-matrix.json";
const CHUNKS_PATH = "tmp/procedure-ir/cullen-chunks.json";
const CLAIMS_PATH = "tmp/procedure-ir/cullen-claimbank.json";
const OUTPUT_PATH = "tmp/procedure-ir/cullen-procedure-anchor-audit.json";
const OUTPUT_MD_PATH = "tmp/procedure-ir/cullen-procedure-anchor-audit.md";

function normalizeTitleForMatch(value) {
  return String(value ?? "")
    .replace(/\bT\s+o\b/giu, "To")
    .replace(/\s*-\s*\n\s*/gu, "")
    .replace(/\s+/gu, " ")
    .trim()
    .toLowerCase();
}

function normalizeChunkText(value) {
  return String(value ?? "")
    .replace(/\s*-\s*\n\s*/gu, "")
    .replace(/\s+/gu, " ")
    .trim();
}

function escapeRegex(value) {
  return String(value ?? "").replace(/[.*+?^${}()|[\]\\]/gu, "\\$&");
}

function hasExactProcMention(text, procId) {
  return new RegExp(`${escapeRegex(procId)}(?!\\d)`, "u").test(String(text ?? ""));
}

function excerpt(value, max = 240) {
  const text = normalizeChunkText(value);
  return text.length > max ? `${text.slice(0, max)}...` : text;
}

function pushIssue(issues, {
  anchor,
  expectedTitle,
  badChunkIds = [],
  badClaimIds = [],
  actualChunkExcerpt = "",
  problemType,
  suggestedFix,
}) {
  issues.push({
    cullen_proc_id: anchor.cullen_proc_id,
    expected_title: expectedTitle,
    bad_chunk_ids: badChunkIds,
    bad_claim_ids: badClaimIds,
    actual_chunk_excerpt: actualChunkExcerpt,
    problem_type: problemType,
    suggested_fix: suggestedFix,
  });
}

function renderMarkdown(report) {
  const lines = [
    "# Cullen Procedure Anchor Audit",
    "",
    `Generated: ${report.generated_at}`,
    "",
    `- anchor_count: ${report.counts.anchor_count}`,
    `- sifen_anchor_count: ${report.counts.sifen_anchor_count}`,
    `- santong_anchor_count: ${report.counts.santong_anchor_count}`,
    `- anchors_with_source_span_candidates: ${report.counts.anchors_with_source_span_candidates}`,
    `- anchors_without_source_span_candidates: ${report.counts.anchors_without_source_span_candidates}`,
    `- wrong_family_anchor_count: ${report.counts.wrong_family_anchor_count}`,
    `- anchor_has_no_claim_ids_count: ${report.counts.anchor_has_no_claim_ids_count}`,
    `- anchor_chunk_proc_mismatch_count: ${report.counts.anchor_chunk_proc_mismatch_count}`,
    `- anchor_claim_missing_count: ${report.counts.anchor_claim_missing_count}`,
    `- anchor_claim_chunk_mismatch_count: ${report.counts.anchor_claim_chunk_mismatch_count}`,
    `- anchor_source_family_mismatch_count: ${report.counts.anchor_source_family_mismatch_count}`,
    `- L66_has_proc_3_2_anchor: ${report.counts.L66_has_proc_3_2_anchor}`,
    `- L66_proc_3_2_chunk_contains_source_text: ${report.counts.L66_proc_3_2_chunk_contains_source_text}`,
    `- missing_required_sifen_proc_ids: ${report.counts.missing_required_sifen_proc_ids.join(", ") || "none"}`,
    `- missing_required_santong_proc_ids: ${report.counts.missing_required_santong_proc_ids.join(", ") || "none"}`,
    "",
    "## By Family",
    "",
  ];

  for (const [family, count] of Object.entries(report.counts.anchors_by_procedure_family)) {
    lines.push(`- ${family}: ${count}`);
  }

  lines.push("", "## By System", "");
  for (const [system, count] of Object.entries(report.counts.anchors_by_system)) {
    lines.push(`- ${system}: ${count}`);
  }

  lines.push("", "## Detailed Issues", "");
  if (!report.issues.length) {
    lines.push("- none", "");
  } else {
    for (const issue of report.issues) {
      lines.push(`### ${issue.cullen_proc_id} / ${issue.problem_type}`);
      lines.push(`- expected_title: ${issue.expected_title}`);
      lines.push(`- bad_chunk_ids: ${issue.bad_chunk_ids.join(", ") || "none"}`);
      lines.push(`- bad_claim_ids: ${issue.bad_claim_ids.join(", ") || "none"}`);
      lines.push(`- actual_chunk_excerpt: ${issue.actual_chunk_excerpt || "none"}`);
      lines.push(`- suggested_fix: ${issue.suggested_fix}`);
      lines.push("");
    }
  }

  return `${lines.join("\n")}\n`;
}

async function main() {
  const [anchors, sourceSpans, procedureIr, coverage, chunksPayload, claimsPayload] = await Promise.all([
    readJson(INPUT_PATH),
    readJson(SOURCE_SPANS_PATH),
    readJson(PROCEDURE_IR_PATH),
    readJson(COVERAGE_PATH),
    readJson(CHUNKS_PATH),
    readJson(CLAIMS_PATH),
  ]);

  const chunkById = new Map((chunksPayload.chunks ?? []).map((chunk) => [chunk.id, chunk]));
  const claimById = new Map((claimsPayload.claims ?? []).map((claim) => [claim.claim_id, claim]));
  const spanById = new Map((sourceSpans.spans ?? []).map((span) => [span.id, span]));
  const procedureBySpanId = new Map((procedureIr.procedures ?? []).map((procedure) => [procedure.source_span_id, procedure]));
  const coverageBySpanId = new Map((coverage.source_span_coverage ?? []).map((entry) => [entry.source_span_id, entry]));
  const anchorsByProcId = new Map((anchors.items ?? []).map((anchor) => [anchor.cullen_proc_id, anchor]));

  const anchorsByProcedureFamily = {};
  const anchorsBySystem = {};
  const issues = [];
  const wrongFamilyAnchors = [];

  let anchorHasNoClaimIdsCount = 0;
  let anchorChunkProcMismatchCount = 0;
  let anchorClaimMissingCount = 0;
  let anchorClaimChunkMismatchCount = 0;
  let anchorSourceFamilyMismatchCount = 0;

  for (const anchor of anchors.items ?? []) {
    anchorsByProcedureFamily[anchor.procedure_family] = (anchorsByProcedureFamily[anchor.procedure_family] ?? 0) + 1;
    anchorsBySystem[anchor.system] = (anchorsBySystem[anchor.system] ?? 0) + 1;

    if (!(anchor.claim_ids ?? []).length) {
      anchorHasNoClaimIdsCount += 1;
      pushIssue(issues, {
        anchor,
        expectedTitle: anchor.english_title,
        problemType: "anchor_has_no_claim_ids",
        suggestedFix: "Rebind this anchor against current chunk-local claims or accept it as context-only with an explicit warning.",
      });
    }

    if (!anchor.procedure_bank_id) {
      for (const chunkId of anchor.body_chunk_ids ?? anchor.chunk_ids ?? []) {
        const chunk = chunkById.get(chunkId);
        const chunkText = normalizeChunkText(chunk?.normalized_text ?? chunk?.text ?? "");
        const hasProcId = hasExactProcMention(chunkText, anchor.cullen_proc_id);
        const hasTitle = normalizeTitleForMatch(chunkText).includes(normalizeTitleForMatch(anchor.english_title));
        if (!(hasProcId && (hasTitle || !anchor.english_title))) {
          anchorChunkProcMismatchCount += 1;
          pushIssue(issues, {
            anchor,
            expectedTitle: anchor.english_title,
            badChunkIds: [chunkId],
            actualChunkExcerpt: excerpt(chunkText),
            problemType: "anchor_chunk_proc_mismatch",
            suggestedFix: "Re-select chunk_ids from current cullen-chunks.json using the current Proc id and normalized English title.",
          });
        }
      }
    }

    for (const claimId of anchor.claim_ids ?? []) {
      const claim = claimById.get(claimId);
      if (!claim) {
        anchorClaimMissingCount += 1;
        pushIssue(issues, {
          anchor,
          expectedTitle: anchor.english_title,
          badClaimIds: [claimId],
          problemType: "anchor_claim_missing",
          suggestedFix: "Drop stale claim_ids and rebuild from the current claimbank.",
        });
        continue;
      }

      if (anchor.procedure_bank_id) continue;

      const claimChunk = chunkById.get(claim.evidence_chunk_id);
      const claimChunkText = normalizeChunkText(claimChunk?.normalized_text ?? claimChunk?.text ?? "");
      const claimText = `${claim.formula_text ?? ""} ${claim.evidence_text ?? ""}`;
      const claimChunkIsAnchorChunk = (anchor.chunk_ids ?? []).includes(claim.evidence_chunk_id);
      const claimChunkHasProc = hasExactProcMention(claimChunkText, anchor.cullen_proc_id);
      const claimTextHasProc = hasExactProcMention(claimText, anchor.cullen_proc_id);
      if (!(claimChunkIsAnchorChunk || claimChunkHasProc || claimTextHasProc)) {
        anchorClaimChunkMismatchCount += 1;
        pushIssue(issues, {
          anchor,
          expectedTitle: anchor.english_title,
          badChunkIds: claim.evidence_chunk_id ? [claim.evidence_chunk_id] : [],
          badClaimIds: [claimId],
          actualChunkExcerpt: excerpt(claimChunkText || claimText),
          problemType: "anchor_claim_chunk_mismatch",
          suggestedFix: "Keep only claims whose evidence_chunk_id resolves to one of the current anchor.chunk_ids for this Proc.",
        });
      }
    }

    for (const sourceSpanId of anchor.source_span_candidates ?? []) {
      const span = spanById.get(sourceSpanId);
      const procedure = procedureBySpanId.get(sourceSpanId);
      const inferredFamily = coverageBySpanId.get(sourceSpanId)?.procedure_family ?? "unknown";
      if (inferredFamily !== "unknown" && inferredFamily !== anchor.procedure_family) {
        anchorSourceFamilyMismatchCount += 1;
        wrongFamilyAnchors.push({
          anchor_id: anchor.anchor_id,
          source_span_id: sourceSpanId,
          anchor_family: anchor.procedure_family,
          inferred_family: inferredFamily,
          procedure_title: procedure?.title_guess ?? null,
          source_text: span?.text ?? null,
        });
        pushIssue(issues, {
          anchor,
          expectedTitle: anchor.english_title,
          actualChunkExcerpt: excerpt(span?.text ?? ""),
          problemType: "anchor_source_family_mismatch",
          suggestedFix: "Remove this source_span_candidate or rebind it to an anchor with the matching procedure_family.",
        });
      }
    }
  }

  const proc32Anchor = anchorsByProcId.get("Proc. 3.2");
  const proc32HeadingText = (proc32Anchor?.heading_chunk_ids ?? [])
    .map((chunkId) => normalizeChunkText(chunkById.get(chunkId)?.normalized_text ?? chunkById.get(chunkId)?.text ?? ""))
    .join("\n");
  const proc32BodyText = (proc32Anchor?.body_chunk_ids ?? [])
    .map((chunkId) => normalizeChunkText(chunkById.get(chunkId)?.normalized_text ?? chunkById.get(chunkId)?.text ?? ""))
    .join("\n");
  const l66Proc32ChunkContainsSourceText = (proc32HeadingText.includes("推入蔀術") || proc32HeadingText.includes("推入蔀術曰") || normalizeChunkText(proc32Anchor?.chinese_heading_excerpt ?? "").includes("推入蔀術"))
    && proc32BodyText.includes("以元法除去上元")
    && hasExactProcMention(proc32BodyText, "Proc. 3.2")
    && proc32BodyText.includes("Cast out Origin Factor [4560]");

  const report = {
    generated_at: new Date().toISOString(),
    input: INPUT_PATH,
    counts: {
      anchor_count: (anchors.items ?? []).length,
      sifen_anchor_count: (anchors.items ?? []).filter((item) => item.system === "sifen").length,
      santong_anchor_count: (anchors.items ?? []).filter((item) => item.system === "santong").length,
      anchors_with_source_span_candidates: (anchors.items ?? []).filter((item) => (item.source_span_candidates ?? []).length > 0).length,
      anchors_without_source_span_candidates: (anchors.items ?? []).filter((item) => !(item.source_span_candidates ?? []).length).length,
      wrong_family_anchor_count: wrongFamilyAnchors.length,
      anchor_has_no_claim_ids_count: anchorHasNoClaimIdsCount,
      anchor_chunk_proc_mismatch_count: anchorChunkProcMismatchCount,
      anchor_claim_missing_count: anchorClaimMissingCount,
      anchor_claim_chunk_mismatch_count: anchorClaimChunkMismatchCount,
      anchor_source_family_mismatch_count: anchorSourceFamilyMismatchCount,
      anchors_by_procedure_family: anchorsByProcedureFamily,
      anchors_by_system: anchorsBySystem,
      missing_required_sifen_proc_ids: REQUIRED_SIFEN_PROC_IDS.filter((procId) => !anchorsByProcId.has(procId)),
      missing_required_santong_proc_ids: REQUIRED_SANTONG_PROC_IDS.filter((procId) => !anchorsByProcId.has(procId)),
      L66_has_proc_3_2_anchor: Boolean(
        proc32Anchor
        && (proc32Anchor.source_span_candidates ?? []).includes("sifen:L66")
        && proc32Anchor.procedure_family === "obscuration_entry"
      ),
      L66_proc_3_2_chunk_contains_source_text: l66Proc32ChunkContainsSourceText,
    },
    wrong_family_anchors: wrongFamilyAnchors,
    issues,
  };

  await writeJson(OUTPUT_PATH, report);
  const markdown = renderMarkdown(report);
  const markdownTarget = resolveRepoPath(OUTPUT_MD_PATH);
  await fs.mkdir(path.dirname(markdownTarget), { recursive: true });
  await fs.writeFile(markdownTarget, markdown, "utf8");

  console.log(JSON.stringify({
    stage: "audit-cullen-procedure-anchors",
    output: OUTPUT_PATH,
    markdown_output: OUTPUT_MD_PATH,
    anchor_count: report.counts.anchor_count,
    sifen_anchor_count: report.counts.sifen_anchor_count,
    santong_anchor_count: report.counts.santong_anchor_count,
    anchors_with_source_span_candidates: report.counts.anchors_with_source_span_candidates,
    anchors_without_source_span_candidates: report.counts.anchors_without_source_span_candidates,
    wrong_family_anchor_count: report.counts.wrong_family_anchor_count,
    anchor_has_no_claim_ids_count: report.counts.anchor_has_no_claim_ids_count,
    anchor_chunk_proc_mismatch_count: report.counts.anchor_chunk_proc_mismatch_count,
    anchor_claim_missing_count: report.counts.anchor_claim_missing_count,
    anchor_claim_chunk_mismatch_count: report.counts.anchor_claim_chunk_mismatch_count,
    anchor_source_family_mismatch_count: report.counts.anchor_source_family_mismatch_count,
    anchors_by_procedure_family: report.counts.anchors_by_procedure_family,
    anchors_by_system: report.counts.anchors_by_system,
    missing_required_sifen_proc_ids: report.counts.missing_required_sifen_proc_ids,
    missing_required_santong_proc_ids: report.counts.missing_required_santong_proc_ids,
    L66_has_proc_3_2_anchor: report.counts.L66_has_proc_3_2_anchor,
    L66_proc_3_2_chunk_contains_source_text: report.counts.L66_proc_3_2_chunk_contains_source_text,
  }, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
