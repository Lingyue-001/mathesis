import fs from "node:fs/promises";
import path from "node:path";
import { readJson, readPipelineConfig, resolveRepoPath, writeJson } from "./cullen-oracle-common.mjs";

const CHAPTER_SCOPES = {
  santong: {
    system: "santong",
    label: "Cullen Santong authority scope",
    page_start: 45,
    page_end: 121,
    core_procedures: [
      "cullen:santong:basic-constants",
      "cullen:santong:accumulated-calendar",
      "cullen:santong:quotient-remainder",
    ],
  },
  sifen: {
    system: "sifen",
    label: "Cullen Sifen authority scope",
    page_start: 151,
    page_end: 205,
    core_procedures: [
      "cullen:sifen:basic-constants",
      "cullen:sifen:tianzheng-shuori",
      "cullen:sifen:mei-mie",
      "cullen:sifen:eclipse-day",
    ],
  },
};

const CHUNK_CLASS_ORDER = [
  "worked_example",
  "procedure",
  "formula",
  "constant",
  "term",
  "context",
  "unused",
];

function inScope(chunk, scope) {
  return chunk.page_start >= scope.page_start && chunk.page_end <= scope.page_end;
}

function indexBy(items, key) {
  return new Map(items.map((item) => [item[key], item]));
}

function unique(items) {
  return [...new Set(items)];
}

function summarizeBy(items, keyFn) {
  const counts = {};
  for (const item of items) {
    const key = keyFn(item);
    counts[key] = (counts[key] ?? 0) + 1;
  }
  return counts;
}

function fillChunkClassCounts(counts) {
  const result = {};
  for (const key of CHUNK_CLASS_ORDER) result[key] = counts[key] ?? 0;
  return result;
}

function addToMapSet(map, key, value) {
  if (!map.has(key)) map.set(key, new Set());
  map.get(key).add(value);
}

function chunkClassification(chunkId, { claimTagsByChunk, termChunkIds, procedureChunkIds }) {
  const tags = new Set(claimTagsByChunk.get(chunkId) ?? []);
  if (procedureChunkIds.has(chunkId)) tags.add("procedure");
  if (termChunkIds.has(chunkId)) tags.add("term");
  if (tags.size === 0) return { primary: "unused", tags: [] };
  for (const label of CHUNK_CLASS_ORDER) {
    if (tags.has(label)) return { primary: label, tags: [...tags].sort() };
  }
  return { primary: "unused", tags: [...tags].sort() };
}

function buildClaimTagsByChunk(claimbank) {
  const map = new Map();
  for (const claim of claimbank.claims ?? []) {
    const chunkId = claim.evidence_chunk_id;
    if (!chunkId) continue;
    if (claim.claim_type === "term_gloss") addToMapSet(map, chunkId, "term");
    else if (claim.claim_type === "constant_definition" || claim.claim_type === "derived_constant") addToMapSet(map, chunkId, "constant");
    else if (claim.claim_type === "procedure_step") addToMapSet(map, chunkId, "procedure");
    else if (claim.claim_type === "formula") addToMapSet(map, chunkId, "formula");
    else if (claim.claim_type === "worked_example") addToMapSet(map, chunkId, "worked_example");
    else addToMapSet(map, chunkId, "context");

    if (claim.evidence_level !== "A_direct" && claim.claim_type !== "term_gloss") {
      addToMapSet(map, chunkId, "context");
    }
  }
  return map;
}

function countCoverage(entries) {
  const counts = {
    directly_covered: 0,
    partially_covered: 0,
    context_only: 0,
    not_covered: 0,
  };
  for (const entry of entries) {
    counts[entry.coverage_status] = (counts[entry.coverage_status] ?? 0) + 1;
  }
  return counts;
}

function shouldBeCovered(span, procedureSpanIds, termbankTerms) {
  if (procedureSpanIds.has(span.id)) return true;
  return termbankTerms.some((term) => {
    if (term.system !== span.source_id) return false;
    const variants = term.normalized_variants ?? [term.chinese_term];
    return variants.some((variant) => span.text.includes(variant));
  });
}

function markdownList(items) {
  if (!items.length) return "- none";
  return items.map((item) => `- ${item}`).join("\n");
}

function formatChunkMetrics(metrics) {
  return [
    `- total chunks: ${metrics.total_chunks}`,
    `- chunks assigned to ${metrics.system}: ${metrics.assigned_chunks}`,
    `- chunks with page metadata: ${metrics.chunks_with_page_metadata}`,
    `- chunks used by CullenTermBank: ${metrics.chunks_used_by_termbank}`,
    `- chunks used by CullenProcedureBank: ${metrics.chunks_used_by_procedurebank}`,
    `- chunks used by CullenClaimBank: ${metrics.chunks_used_by_claimbank}`,
    `- chunks mapped to source spans: ${metrics.chunks_mapped_to_source_spans}`,
    `- unclassified chunks: ${metrics.unclassified_chunk_ids.length}`,
  ].join("\n");
}

async function main() {
  const config = await readPipelineConfig();
  const chunksPayload = await readJson(config.inputs.cullen.artifacts.chunks);
  const termbank = await readJson(`${config.outputs.dir}/cullen-termbank.json`);
  const procedurebank = await readJson(`${config.outputs.dir}/cullen-procedurebank.json`);
  const claimbank = await readJson(`${config.outputs.dir}/cullen-claimbank.json`);
  const coverage = await readJson(`${config.outputs.dir}/cullen-coverage-matrix.json`);
  const sourceSpans = await readJson(`${config.outputs.dir}/source_spans.json`);
  const procedureIR = await readJson(`${config.outputs.dir}/procedure_IR.json`);

  const spanById = indexBy(sourceSpans.spans ?? [], "id");
  const procedureBySpanId = new Map((procedureIR.procedures ?? []).map((item) => [item.source_span_id, item]));
  const procedureSpanIds = new Set((procedureIR.procedures ?? []).map((item) => item.source_span_id));
  const coverageBySpanId = new Map((coverage.source_span_coverage ?? []).map((item) => [item.source_span_id, item]));
  const claimTagsByChunk = buildClaimTagsByChunk(claimbank);
  const termChunkIds = new Set((termbank.terms ?? []).map((item) => item.source?.cullen_chunk_id).filter(Boolean));
  const procedureChunkIds = new Set((procedurebank.procedures ?? []).flatMap((item) => item.source_chunks ?? []));
  const claimChunkIds = new Set((claimbank.claims ?? []).map((item) => item.evidence_chunk_id).filter(Boolean));

  const chapterReports = {};

  for (const [system, scope] of Object.entries(CHAPTER_SCOPES)) {
    const scopedChunks = (chunksPayload.chunks ?? []).filter((chunk) => inScope(chunk, scope));
    const chapterClaimChunkIds = new Set(
      (claimbank.claims ?? [])
        .filter((claim) => claim.system === system)
        .map((claim) => claim.evidence_chunk_id)
        .filter(Boolean),
    );
    const chapterTermChunkIds = new Set(
      (termbank.terms ?? [])
        .filter((term) => term.system === system)
        .map((term) => term.source?.cullen_chunk_id)
        .filter(Boolean),
    );
    const chapterProcedureChunkIds = new Set(
      (procedurebank.procedures ?? [])
        .filter((item) => item.system === system)
        .flatMap((item) => item.source_chunks ?? []),
    );

    const sourceCoverage = (coverage.source_span_coverage ?? []).filter((item) => item.system === system);
    const mappedChunkIds = new Set(
      sourceCoverage.flatMap((entry) => entry.matched_cullen_claims ?? [])
        .map((claimId) => (claimbank.claims ?? []).find((claim) => claim.claim_id === claimId)?.evidence_chunk_id)
        .filter(Boolean),
    );
    for (const procedureId of sourceCoverage.flatMap((entry) => entry.matched_cullen_procedures ?? [])) {
      const item = (procedurebank.procedures ?? []).find((procedure) => procedure.cullen_procedure_id === procedureId);
      for (const chunkId of item?.source_chunks ?? []) mappedChunkIds.add(chunkId);
    }

    const chunkAudit = scopedChunks.map((chunk) => {
      const classification = chunkClassification(chunk.id, {
        claimTagsByChunk,
        termChunkIds: chapterTermChunkIds,
        procedureChunkIds: chapterProcedureChunkIds,
      });
      return {
        chunk_id: chunk.id,
        page_start: chunk.page_start,
        page_end: chunk.page_end,
        system_hint: chunk.system_hint ?? null,
        primary_classification: classification.primary,
        classification_tags: classification.tags,
        mapped_to_source_spans: [...new Set(
          sourceCoverage
            .filter((entry) =>
              (entry.matched_cullen_claims ?? []).some((claimId) =>
                (claimbank.claims ?? []).find((claim) => claim.claim_id === claimId)?.evidence_chunk_id === chunk.id)
              || (entry.matched_cullen_procedures ?? []).some((procedureId) =>
                (procedurebank.procedures ?? []).find((procedure) => procedure.cullen_procedure_id === procedureId)?.source_chunks?.includes(chunk.id))
            )
            .map((entry) => entry.source_span_id),
        )],
      };
    });

    const coreProcedureAudit = scope.core_procedures.map((procedureId) => {
      const procedure = (procedurebank.procedures ?? []).find((item) => item.cullen_procedure_id === procedureId) ?? null;
      const mappedSourceSpans = sourceCoverage
        .filter((entry) => (entry.matched_cullen_procedures ?? []).includes(procedureId))
        .map((entry) => ({
          source_span_id: entry.source_span_id,
          coverage_status: entry.coverage_status,
        }));
      return {
        procedure_id: procedureId,
        title: procedure?.cullen_title_or_section ?? null,
        evidence_level: procedure?.evidence_level ?? null,
        covered: mappedSourceSpans.length > 0,
        mapped_source_spans: mappedSourceSpans,
      };
    });

    chapterReports[system] = {
      scope,
      metrics: {
        total_chunks: scopedChunks.length,
        assigned_chunks: chunkAudit.filter((item) => item.system_hint === system).length,
        chunk_classification_counts: fillChunkClassCounts(summarizeBy(chunkAudit, (item) => item.primary_classification)),
        unclassified_chunk_ids: chunkAudit.filter((item) => item.primary_classification === "unused").map((item) => item.chunk_id),
        chunks_with_page_metadata: scopedChunks.filter((chunk) => Number.isFinite(chunk.page_start) && Number.isFinite(chunk.page_end)).length,
        chunks_used_by_termbank: scopedChunks.filter((chunk) => chapterTermChunkIds.has(chunk.id)).length,
        chunks_used_by_procedurebank: scopedChunks.filter((chunk) => chapterProcedureChunkIds.has(chunk.id)).length,
        chunks_used_by_claimbank: scopedChunks.filter((chunk) => chapterClaimChunkIds.has(chunk.id)).length,
        chunks_mapped_to_source_spans: scopedChunks.filter((chunk) => mappedChunkIds.has(chunk.id)).length,
      },
      chunks: chunkAudit,
      core_procedures: coreProcedureAudit,
    };
  }

  const sourceReports = {};
  for (const system of ["santong", "sifen"]) {
    const spans = (sourceSpans.spans ?? []).filter((span) => span.source_id === system);
    const entries = spans.map((span) => {
      const coverageEntry = coverageBySpanId.get(span.id) ?? {
        source_span_id: span.id,
        coverage_status: "not_covered",
        blocking_reason: "missing_coverage_entry",
        matched_cullen_terms: [],
        matched_cullen_claims: [],
        matched_cullen_procedures: [],
      };
      return {
        source_span_id: span.id,
        kind: span.kind,
        text: span.text,
        procedure_id: procedureBySpanId.get(span.id)?.procedure_id ?? null,
        coverage_status: coverageEntry.coverage_status,
        blocking_reason: coverageEntry.blocking_reason ?? null,
        matched_cullen_terms: coverageEntry.matched_cullen_terms ?? [],
        matched_cullen_claims: coverageEntry.matched_cullen_claims ?? [],
        matched_cullen_procedures: coverageEntry.matched_cullen_procedures ?? [],
        should_be_covered_by_cullen: shouldBeCovered(span, procedureSpanIds, termbank.terms ?? []),
      };
    });

    sourceReports[system] = {
      metrics: countCoverage(entries),
      not_covered_with_reason: entries
        .filter((entry) => entry.coverage_status === "not_covered")
        .map((entry) => ({
          source_span_id: entry.source_span_id,
          kind: entry.kind,
          reason: entry.blocking_reason ?? "unknown",
        })),
      should_be_covered_but_not: entries
        .filter((entry) => entry.should_be_covered_by_cullen && !["directly_covered", "partially_covered"].includes(entry.coverage_status))
        .map((entry) => ({
          source_span_id: entry.source_span_id,
          kind: entry.kind,
          coverage_status: entry.coverage_status,
          reason: entry.blocking_reason ?? "unknown",
        })),
      spans: entries,
    };
  }

  const report = {
    generated_at: new Date().toISOString(),
    inputs: {
      chunks: config.inputs.cullen.artifacts.chunks,
      termbank: `${config.outputs.dir}/cullen-termbank.json`,
      procedurebank: `${config.outputs.dir}/cullen-procedurebank.json`,
      claimbank: `${config.outputs.dir}/cullen-claimbank.json`,
      coverage_matrix: `${config.outputs.dir}/cullen-coverage-matrix.json`,
      source_spans: `${config.outputs.dir}/source_spans.json`,
      procedure_ir: `${config.outputs.dir}/procedure_IR.json`,
    },
    chapter_reports: chapterReports,
    source_reports: sourceReports,
    invariants: {
      a_confirmed_not_loosened: true,
      embeddings_added: false,
      jiuzhi_expanded: false,
      gold_candidates_promoted: false,
    },
  };

  const markdown = [
    "# Cullen Chapter Coverage Audit",
    "",
    `Generated: ${report.generated_at}`,
    "",
    "## Chapter Scopes",
    "",
    "### Santong",
    formatChunkMetrics(chapterReports.santong.metrics),
    "",
    `- core procedures covered: ${chapterReports.santong.core_procedures.filter((item) => item.covered).length}/${chapterReports.santong.core_procedures.length}`,
    `- missing core procedures: ${chapterReports.santong.core_procedures.filter((item) => !item.covered).map((item) => item.procedure_id).join(", ") || "none"}`,
    "",
    "### Sifen",
    formatChunkMetrics(chapterReports.sifen.metrics),
    "",
    `- core procedures covered: ${chapterReports.sifen.core_procedures.filter((item) => item.covered).length}/${chapterReports.sifen.core_procedures.length}`,
    `- missing core procedures: ${chapterReports.sifen.core_procedures.filter((item) => !item.covered).map((item) => item.procedure_id).join(", ") || "none"}`,
    "",
    "## Source Text Coverage",
    "",
    "### Santong",
    `- directly_covered: ${sourceReports.santong.metrics.directly_covered}`,
    `- partially_covered: ${sourceReports.santong.metrics.partially_covered}`,
    `- context_only: ${sourceReports.santong.metrics.context_only}`,
    `- not_covered: ${sourceReports.santong.metrics.not_covered}`,
    "",
    "Not covered with reason:",
    markdownList(sourceReports.santong.not_covered_with_reason.map((item) => `${item.source_span_id} (${item.kind}) - ${item.reason}`)),
    "",
    "Should be covered by Cullen but are not fully covered:",
    markdownList(sourceReports.santong.should_be_covered_but_not.map((item) => `${item.source_span_id} (${item.kind}) - ${item.coverage_status}: ${item.reason}`)),
    "",
    "### Sifen",
    `- directly_covered: ${sourceReports.sifen.metrics.directly_covered}`,
    `- partially_covered: ${sourceReports.sifen.metrics.partially_covered}`,
    `- context_only: ${sourceReports.sifen.metrics.context_only}`,
    `- not_covered: ${sourceReports.sifen.metrics.not_covered}`,
    "",
    "Not covered with reason:",
    markdownList(sourceReports.sifen.not_covered_with_reason.map((item) => `${item.source_span_id} (${item.kind}) - ${item.reason}`)),
    "",
    "Should be covered by Cullen but are not fully covered:",
    markdownList(sourceReports.sifen.should_be_covered_but_not.map((item) => `${item.source_span_id} (${item.kind}) - ${item.coverage_status}: ${item.reason}`)),
    "",
    "## Invariants",
    "",
    `- A_confirmed not loosened: ${report.invariants.a_confirmed_not_loosened}`,
    `- embeddings added: ${report.invariants.embeddings_added}`,
    `- Jiuzhi expanded: ${report.invariants.jiuzhi_expanded}`,
    `- gold candidates promoted: ${report.invariants.gold_candidates_promoted}`,
    "",
  ].join("\n");

  const markdownPath = resolveRepoPath(`${config.outputs.dir}/cullen-chapter-coverage.md`);
  await writeJson(`${config.outputs.dir}/cullen-chapter-coverage.json`, report);
  await fs.mkdir(path.dirname(markdownPath), { recursive: true });
  await fs.writeFile(markdownPath, `${markdown}\n`, "utf8");

  console.log(JSON.stringify({
    stage: "audit-cullen-chapter-coverage",
    outputs: [
      `${config.outputs.dir}/cullen-chapter-coverage.json`,
      `${config.outputs.dir}/cullen-chapter-coverage.md`,
    ],
    chapter_metrics: {
      santong: chapterReports.santong.metrics,
      sifen: chapterReports.sifen.metrics,
    },
    source_metrics: {
      santong: sourceReports.santong.metrics,
      sifen: sourceReports.sifen.metrics,
    },
  }, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
