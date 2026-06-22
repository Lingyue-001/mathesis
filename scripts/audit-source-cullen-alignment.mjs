import { readJson } from "./cullen-oracle-common.mjs";
import {
  buildSourceCullenAlignmentArtifacts,
  SOURCE_CULLEN_ALIGNMENT_AUDIT_JSON,
  SOURCE_CULLEN_ALIGNMENT_AUDIT_MD,
  SOURCE_CULLEN_ALIGNMENT_CANDIDATES_JSON,
  SOURCE_CULLEN_ALIGNMENT_CANDIDATES_REFINED_JSON,
  SOURCE_CULLEN_ALIGNMENT_AUDIT_REFINED_JSON,
  SOURCE_CULLEN_ALIGNMENT_AUDIT_REFINED_MD,
  SOURCE_CULLEN_ALIGNMENT_REVIEW_PACKET_MD,
  SOURCE_CULLEN_ALIGNMENT_REVIEW_PACKET_REFINED_MD,
  SOURCE_PROCEDURE_INVENTORY_JSON,
  SOURCE_PROCEDURE_INVENTORY_MD,
  SOURCE_PROCEDURE_INVENTORY_REFINED_JSON,
  SOURCE_PROCEDURE_INVENTORY_REFINED_MD,
  SOURCE_PROCEDURE_SEGMENTATION_AUDIT_JSON,
  SOURCE_PROCEDURE_SEGMENTATION_AUDIT_MD,
  writeSourceAlignmentOutputs,
} from "./source-cullen-alignment-common.mjs";

const SOURCE_SPANS_PATH = "tmp/procedure-ir/source_spans.json";
const PROCEDURE_IR_PATH = "tmp/procedure-ir/procedure_IR.json";
const ANCHORS_PATH = "tmp/procedure-ir/cullen-procedure-anchors.json";

async function main() {
  const [sourceSpansPayload, procedurePayload, anchorPayload] = await Promise.all([
    readJson(SOURCE_SPANS_PATH),
    readJson(PROCEDURE_IR_PATH),
    readJson(ANCHORS_PATH),
  ]);

  const artifacts = buildSourceCullenAlignmentArtifacts(
    sourceSpansPayload,
    procedurePayload,
    anchorPayload,
  );

  await writeSourceAlignmentOutputs(artifacts);

  const {
    oldInventoryPayload,
    refinedInventoryPayload,
    refinedAuditPayload,
    segmentationAuditPayload,
  } = artifacts;

  console.log(JSON.stringify({
    stage: "audit-source-cullen-alignment",
    outputs: [
      SOURCE_PROCEDURE_INVENTORY_JSON,
      SOURCE_PROCEDURE_INVENTORY_MD,
      SOURCE_CULLEN_ALIGNMENT_CANDIDATES_JSON,
      SOURCE_CULLEN_ALIGNMENT_REVIEW_PACKET_MD,
      SOURCE_CULLEN_ALIGNMENT_AUDIT_JSON,
      SOURCE_CULLEN_ALIGNMENT_AUDIT_MD,
      SOURCE_PROCEDURE_INVENTORY_REFINED_JSON,
      SOURCE_PROCEDURE_INVENTORY_REFINED_MD,
      SOURCE_PROCEDURE_SEGMENTATION_AUDIT_JSON,
      SOURCE_PROCEDURE_SEGMENTATION_AUDIT_MD,
      SOURCE_CULLEN_ALIGNMENT_CANDIDATES_REFINED_JSON,
      SOURCE_CULLEN_ALIGNMENT_REVIEW_PACKET_REFINED_MD,
      SOURCE_CULLEN_ALIGNMENT_AUDIT_REFINED_JSON,
      SOURCE_CULLEN_ALIGNMENT_AUDIT_REFINED_MD,
    ],
    old_source_proc_count: oldInventoryPayload.items.length,
    refined_source_proc_count: refinedInventoryPayload.items.length,
    new_candidate_source_proc_count: segmentationAuditPayload.new_candidate_source_proc_count,
    santong_refined_source_proc_count: refinedAuditPayload.santong_refined_source_proc_count,
    sifen_refined_source_proc_count: refinedAuditPayload.sifen_refined_source_proc_count,
    possible_heading_body_split_count: refinedAuditPayload.possible_heading_body_split_count,
    possible_one_to_many_count: refinedAuditPayload.possible_one_to_many_count,
    possible_many_to_one_count: refinedAuditPayload.possible_many_to_one_count,
    aligned_high_confidence_count: refinedAuditPayload.aligned_high_confidence_count,
    aligned_medium_confidence_count: refinedAuditPayload.aligned_medium_confidence_count,
    needs_review_count: refinedAuditPayload.needs_review_count,
    unmatched_count: refinedAuditPayload.unmatched_count,
    wrong_system_candidate_count: refinedAuditPayload.wrong_system_candidate_count,
    generic_term_only_candidate_count: refinedAuditPayload.generic_term_only_candidate_count,
    cullen_anchors_with_new_high_or_medium_candidates: refinedAuditPayload.cullen_anchors_with_new_high_or_medium_candidates,
    cullen_anchors_still_without_source_candidates: refinedAuditPayload.cullen_anchors_still_without_source_candidates,
    possible_many_to_one_alignments: refinedAuditPayload.possible_many_to_one_alignments,
    possible_one_to_many_alignments: refinedAuditPayload.possible_one_to_many_alignments,
  }, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
