import { readJson, writeJson } from "./cullen-oracle-common.mjs";

const CANDIDATE_PATH = "config/sifen-target-family-gold.candidate.json";
const OUTPUT_PATH = "tmp/procedure-ir/sifen-target-family-candidate-audit.json";

function hasForbiddenGoldMarker(item) {
  const forbiddenStrings = new Set(["final_gold", "approved_gold", "locked_gold", "reviewed"]);
  const forbiddenKeys = new Set(["final_gold", "approved_gold", "locked_gold", "reviewed"]);

  for (const [key, value] of Object.entries(item ?? {})) {
    if (forbiddenKeys.has(key)) return true;
    if (typeof value === "string" && forbiddenStrings.has(value)) return true;
    if (Array.isArray(value) && value.some((entry) => typeof entry === "string" && forbiddenStrings.has(entry))) {
      return true;
    }
  }

  return false;
}

async function main() {
  const candidateMap = await readJson(CANDIDATE_PATH);
  const items = candidateMap.items ?? [];
  const forbiddenItems = items
    .filter((item) => hasForbiddenGoldMarker(item))
    .map((item) => item.source_span_id);
  const acceptedCandidateClaims = items.flatMap((item) => item.accepted_cullen_clues_candidate ?? []);
  const topNoisyCandidates = items.flatMap((item) => item.top_noisy_candidates ?? []);
  const genericOnlyCandidates = items.flatMap((item) => item.generic_term_only_candidates ?? []);
  const allDisplayCandidates = [
    ...acceptedCandidateClaims,
    ...topNoisyCandidates,
    ...genericOnlyCandidates,
  ];

  const report = {
    generated_at: new Date().toISOString(),
    input: CANDIDATE_PATH,
    counts: {
      target_span_count: items.length,
      with_candidate_expected_family: items.filter((item) => Boolean(item.machine_expected_family)).length,
      with_accepted_candidate_claims: items.filter((item) => (item.current_accepted_claims ?? []).length > 0).length,
      with_noisy_claims: items.filter((item) => (item.current_noisy_claims ?? []).length > 0).length,
      requiring_human_review: items.filter((item) => item.human_review_status !== "approved_gold").length,
      top_noisy_display_limit: 3,
      generic_term_only_candidate_count: genericOnlyCandidates.length,
      strong_candidate_count: allDisplayCandidates.filter((item) => item.match_strength === "strong").length,
      medium_candidate_count: allDisplayCandidates.filter((item) => item.match_strength === "medium").length,
      weak_candidate_count: allDisplayCandidates.filter((item) => item.match_strength === "weak").length,
      generic_only_candidate_count: allDisplayCandidates.filter((item) => item.match_strength === "generic_only").length,
      accepted_candidate_claim_count: acceptedCandidateClaims.length,
      omitted_noisy_candidate_count: items.reduce((sum, item) => sum + (item.omitted_noisy_candidate_count ?? 0), 0),
    },
    no_final_gold_marked: forbiddenItems.length === 0,
    forbidden_gold_markers_found: forbiddenItems,
  };

  await writeJson(OUTPUT_PATH, report);
  console.log(JSON.stringify({
    stage: "audit-sifen-target-family-candidates",
    output: OUTPUT_PATH,
    ...report.counts,
    no_final_gold_marked: report.no_final_gold_marked,
  }, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
