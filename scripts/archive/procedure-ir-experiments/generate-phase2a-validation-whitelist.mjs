import fs from "node:fs/promises";
import { readJson, writeJson } from "./cullen-oracle-common.mjs";

const INPUT_MAP = "tmp/procedure-ir/phase2a-cullen-backed-expression-map.json";
const INPUT_AUDIT = "tmp/procedure-ir/phase2a-expression-quality-audit.json";
const INPUT_PILOT = "tmp/procedure-ir/phase2a-procedure-ir-pilot.json";
const INPUT_RECON = "tmp/procedure-ir/cullen-led-source-reconstruction.json";

const OUTPUT_WHITELIST_JSON = "tmp/procedure-ir/phase2a-arithmetic-validation-whitelist.json";
const OUTPUT_WHITELIST_MD = "tmp/procedure-ir/phase2a-arithmetic-validation-whitelist.md";
const OUTPUT_DOWNGRADE_JSON = "tmp/procedure-ir/phase2a-expression-downgrade-report.json";
const OUTPUT_DOWNGRADE_MD = "tmp/procedure-ir/phase2a-expression-downgrade-report.md";
const OUTPUT_VALIDATION_JSON = "tmp/procedure-ir/phase2a-arithmetic-validation-pilot.json";
const OUTPUT_VALIDATION_MD = "tmp/procedure-ir/phase2a-arithmetic-validation-pilot.md";

const TARGET_PROC_IDS = ["Proc. 2.3", "Proc. 2.4", "Proc. 2.5", "Proc. 2.9", "Proc. 3.2"];

const RUN_NOW_STEP_IDS = [
  "Proc.2.3.step.1",
  "Proc.2.3.step.2",
  "Proc.2.3.step.4",
  "Proc.2.3.step.6",
  "Proc.2.3.step.8",
  "Proc.2.9.step.1",
];

const CANDIDATE_BUT_NOT_RUN_NOW_STEP_IDS = [
  "Proc.2.3.step.7",
  "Proc.2.5.step.1",
  "Proc.2.5.step.2",
  "Proc.2.9.step.2",
];

const EXCLUDED_STEP_RULES = new Map([
  [
    "Proc.2.3.step.3",
    {
      excluded_parts: ["38-threshold predicate cannot be detached cleanly from the 43/carry commentary relation yet"],
      reason:
        "needs_cullen_page_check: current allowed inputs do not fully reconcile source threshold 38 with Cullen's 43/carry explanation, so keep out of arithmetic validation.",
    },
  ],
  [
    "Proc.2.3.step.5",
    {
      excluded_parts: ["算外 counting convention", "external Concordance Head index"],
      reason: "Counting-outside convention is explicitly excluded from run-now arithmetic validation.",
    },
  ],
  [
    "Proc.2.3.step.9",
    {
      excluded_parts: ["pair-level doubling interpretation", "full-moon paired carry consequences"],
      reason:
        "Only C-level translation backup is present, so this step must be downgraded from clean formalizable_now and excluded from run-now validation.",
    },
  ],
  [
    "Proc.2.4.step.1",
    {
      excluded_parts: ["proc-level discrepancy context"],
      reason:
        "Although the multiplication itself is clear, Proc. 2.4 remains under a source/Cullen discrepancy and is not admitted to the run-now whitelist in this round.",
    },
  ],
  [
    "Proc.2.4.step.2a",
    {
      excluded_parts: ["source 加十 vs Cullen 加七 discrepancy"],
      reason: "Source/Cullen discrepancy blocks deterministic arithmetic formalization.",
    },
  ],
  [
    "Proc.2.4.step.2b",
    {
      excluded_parts: ["overflow-count naming certainty", "source 加十 vs Cullen 加七 discrepancy"],
      reason:
        "Worked-example arithmetic exists, but this round keeps all Proc. 2.4 steps out of run-now because the discrepancy and off-by-one naming risk remain open.",
    },
  ],
  [
    "Proc.2.4.step.3",
    {
      excluded_parts: ["起冬至 / 算外 ordinal counting convention"],
      reason: "Counting-outside convention is excluded from arithmetic auto-run.",
    },
  ],
  [
    "Proc.2.4.step.4",
    {
      excluded_parts: ["calendar placement of medial qi", "intercalary-month classification rule"],
      reason: "Calendrical placement logic still requires human review and discrepancy resolution.",
    },
  ],
  [
    "Proc.2.5.step.3",
    {
      excluded_parts: ["如法 counting convention", "winter-solstice day recovery"],
      reason: "As instructed, 如法 counting remains excluded from run-now arithmetic validation.",
    },
  ],
  [
    "Proc.2.9.step.3",
    {
      excluded_parts: ["borrow bookkeeping", "whole-du decomposition detail"],
      reason: "Borrow bookkeeping is explicitly excluded from run-now arithmetic validation.",
    },
  ],
  [
    "Proc.3.2.step.1",
    {
      excluded_parts: ["benchmark-only nested cycle step"],
      reason: "Proc. 3.2 is benchmark only and must not be promoted into the Santong run-now whitelist.",
    },
  ],
  [
    "Proc.3.2.step.2",
    {
      excluded_parts: ["benchmark-only nested cycle step"],
      reason: "Proc. 3.2 is benchmark only and must not be promoted into the Santong run-now whitelist.",
    },
  ],
  [
    "Proc.3.2.step.3",
    {
      excluded_parts: ["table/counting convention dependency", "benchmark-only nested cycle step"],
      reason: "Proc. 3.2 remains benchmark only; C-level backup also blocks auto-run.",
    },
  ],
  [
    "Proc.3.2.step.4",
    {
      excluded_parts: ["Heaven Era counting convention", "table lookup behavior"],
      reason: "Benchmark-only table/counting convention remains human review.",
    },
  ],
  [
    "Proc.3.2.step.5",
    {
      excluded_parts: ["jiazi Obscuration counting convention", "table lookup behavior"],
      reason: "Benchmark-only table/counting convention remains human review.",
    },
  ],
  [
    "Proc.3.2.step.6",
    {
      excluded_parts: ["岁名命之 labeling", "算上 counting-above convention"],
      reason: "Benchmark-only labeling/counting convention remains human review.",
    },
  ],
]);

function ensure(condition, message) {
  if (!condition) throw new Error(message);
}

function groupBy(items, key) {
  const grouped = new Map();
  for (const item of items) {
    const value = item[key];
    const list = grouped.get(value) ?? [];
    list.push(item);
    grouped.set(value, list);
  }
  return grouped;
}

function pickProcId(stepId) {
  const match = /^Proc\.(\d+\.\d+)\.step\./u.exec(stepId);
  return match ? `Proc. ${match[1]}` : null;
}

function renderWhitelistMarkdown(payload) {
  const lines = [
    "# Phase 2A-3 Arithmetic Validation Whitelist",
    "",
    `- Scope: ${TARGET_PROC_IDS.join(", ")}`,
    `- run_now_count: ${payload.summary.run_now.length}`,
    `- candidate_but_not_run_now_count: ${payload.summary.candidate_but_not_run_now.length}`,
    `- excluded_count: ${payload.summary.excluded.length}`,
    "",
    "## Run Now",
    "",
  ];

  for (const item of payload.summary.run_now) {
    lines.push(`- ${item.step_id} | ${item.backup_level} | ${item.formalization_status} | ${item.reason}`);
  }

  lines.push("", "## Candidate But Not Run Now", "");
  for (const item of payload.summary.candidate_but_not_run_now) {
    lines.push(`- ${item.step_id} | ${item.backup_level} | ${item.formalization_status} | ${item.reason}`);
  }

  lines.push("", "## Excluded", "");
  for (const item of payload.summary.excluded) {
    lines.push(`- ${item.step_id} | ${item.backup_level} | ${item.formalization_status} | ${item.reason}`);
  }

  lines.push("", "## Detailed Items", "");
  for (const item of payload.items) {
    lines.push(`### ${item.step_id}`, "");
    lines.push(`- proc_id: ${item.proc_id}`);
    lines.push(`- formal_expression: ${item.formal_expression ?? "null"}`);
    lines.push(`- backup_level: ${item.backup_level}`);
    lines.push(`- formalization_status: ${item.formalization_status}`);
    lines.push(`- validation_input_source: ${item.validation_input_source}`);
    lines.push(`- expected_output_source: ${item.expected_output_source}`);
    lines.push(`- can_run_now: ${item.can_run_now}`);
    lines.push(`- excluded_parts: ${item.excluded_parts.length ? item.excluded_parts.join("; ") : "none"}`);
    lines.push(`- reason: ${item.reason}`);
    lines.push("");
  }

  return `${lines.join("\n")}\n`;
}

function renderDowngradeMarkdown(payload) {
  const lines = [
    "# Phase 2A-3 Expression Downgrade Report",
    "",
    "## Summary",
    "",
    `- reviewed_entries: ${payload.reviewed_entries.length}`,
    `- downgrade_count: ${payload.downgrade_count}`,
    `- rename_suggestion_count: ${payload.rename_suggestion_count}`,
    `- needs_page_check_count: ${payload.needs_page_check_count}`,
    "",
  ];

  for (const entry of payload.reviewed_entries) {
    lines.push(`## ${entry.step_id}`, "");
    lines.push(`- finding: ${entry.finding}`);
    lines.push(`- current_backup_level: ${entry.current_backup_level}`);
    lines.push(`- current_formalization_status: ${entry.current_formalization_status}`);
    lines.push(`- current_operation_id: ${entry.current_operation_id}`);
    lines.push(`- current_formal_expression: ${entry.current_formal_expression ?? "null"}`);
    if (entry.recommended_backup_level) lines.push(`- recommended_backup_level: ${entry.recommended_backup_level}`);
    if (entry.recommended_formalization_status) lines.push(`- recommended_formalization_status: ${entry.recommended_formalization_status}`);
    if (entry.recommended_operation_id) lines.push(`- recommended_operation_id: ${entry.recommended_operation_id}`);
    lines.push(`- arithmetic_validation_eligibility: ${entry.arithmetic_validation_eligibility}`);
    lines.push(`- rationale: ${entry.rationale}`);
    lines.push("");
  }

  return `${lines.join("\n")}\n`;
}

function renderValidationMarkdown(payload) {
  const lines = [
    "# Phase 2A-3 Arithmetic Validation Pilot",
    "",
    `- executed_results: ${payload.results.length}`,
    `- all_pass: ${payload.summary.all_pass}`,
    "",
    "## Results",
    "",
  ];

  for (const result of payload.results) {
    lines.push(`- ${result.step_id} | ${result.expression} | expected=${JSON.stringify(result.expected_result)} | computed=${JSON.stringify(result.computed_result)} | pass=${result.pass}`);
  }

  lines.push("", "## Excluded From Auto-Run", "");
  for (const item of payload.excluded_from_auto_run) {
    lines.push(`- ${item.step_id} | ${item.reason}`);
  }

  return `${lines.join("\n")}\n`;
}

function buildWhitelistItems(entries) {
  const allowedStepIds = new Set([
    ...RUN_NOW_STEP_IDS,
    ...CANDIDATE_BUT_NOT_RUN_NOW_STEP_IDS,
    ...EXCLUDED_STEP_RULES.keys(),
  ]);

  return entries
    .filter((entry) => allowedStepIds.has(entry.step_id))
    .map((entry) => {
      let canRunNow = false;
      let excludedParts = [];
      let reason = "";

      if (RUN_NOW_STEP_IDS.includes(entry.step_id)) {
        canRunNow = true;
        reason =
          entry.backup_level === "A_worked_example_formula"
            ? "Run now: direct Cullen worked-example arithmetic is available."
            : "Run now: Cullen commentary states a sufficiently explicit arithmetic relation for minimal validation.";
      } else if (CANDIDATE_BUT_NOT_RUN_NOW_STEP_IDS.includes(entry.step_id)) {
        canRunNow = false;
        excludedParts = EXCLUDED_STEP_RULES.get(entry.step_id)?.excluded_parts ?? [];
        reason =
          EXCLUDED_STEP_RULES.get(entry.step_id)?.reason ??
          "Candidate but not run now: arithmetic core is partly formalized, but this round keeps it outside auto-run.";
      } else {
        canRunNow = false;
        excludedParts = EXCLUDED_STEP_RULES.get(entry.step_id)?.excluded_parts ?? [];
        reason = EXCLUDED_STEP_RULES.get(entry.step_id)?.reason ?? "Excluded from this round's arithmetic validation.";
      }

      return {
        step_id: entry.step_id,
        proc_id: entry.proc_id,
        formal_expression: entry.formal_expression,
        backup_level: entry.backup_level,
        formalization_status: entry.formalization_status,
        validation_input_source: entry.cullen_worked_example
          ? `Cullen worked example: ${entry.cullen_worked_example}`
          : `Cullen-backed relation from ${entry.backup_level === "B_commentary_explicit_relation" ? "commentary" : "translation/commentary"} and step bindings`,
        expected_output_source: entry.cullen_worked_example
          ? `Cullen worked example: ${entry.cullen_worked_example}`
          : entry.cullen_commentary_phrase || entry.validation_rule,
        can_run_now: canRunNow,
        excluded_parts: excludedParts,
        reason,
      };
    });
}

function buildDowngradeReport(entryMap) {
  const step39 = entryMap.get("Proc.2.3.step.9");
  const step24b = entryMap.get("Proc.2.4.step.2b");
  const step23 = entryMap.get("Proc.2.3.step.3");

  return {
    generated_at: new Date().toISOString(),
    stage: "phase2a_expression_downgrade_report",
    reviewed_entries: [
      {
        step_id: step39.step_id,
        finding: "C-level backup cannot support a clean formalizable_now status for automatic validation.",
        current_backup_level: step39.backup_level,
        current_formalization_status: step39.formalization_status,
        current_operation_id: step39.operation_id,
        current_formal_expression: step39.formal_expression,
        recommended_backup_level: step39.backup_level,
        recommended_formalization_status: "formalizable_with_caveat",
        recommended_operation_id: step39.operation_id,
        arithmetic_validation_eligibility: "exclude_from_run_now",
        rationale:
          "The doubling rule is explicit only in Cullen's translation, not in a worked example or commentary relation that proves pair-level arithmetic behavior. Keep the expression human-readable but downgrade its machine-readiness.",
      },
      {
        step_id: step24b.step_id,
        finding: "Operation naming carries an off-by-one risk if 'cross' or 'exceed' language is left underspecified.",
        current_backup_level: step24b.backup_level,
        current_formalization_status: step24b.formalization_status,
        current_operation_id: step24b.operation_id,
        current_formal_expression: step24b.formal_expression,
        recommended_backup_level: step24b.backup_level,
        recommended_formalization_status: step24b.formalization_status,
        recommended_operation_id: "completed_seven_advances_before_overflow",
        arithmetic_validation_eligibility: "exclude_from_run_now",
        rationale:
          "The Cullen example supports floor((228 - 168) / 7) = 8, but that quotient is best read as completed seven-unit advances before overflow. Keep the source 加十 vs Cullen 加七 discrepancy explicit and avoid ambiguous cross/exceed naming.",
      },
      {
        step_id: step23.step_id,
        finding: "The 38-threshold source rule and the 43/carry commentary relation are not fully reconciled by current inputs alone.",
        current_backup_level: step23.backup_level,
        current_formalization_status: step23.formalization_status,
        current_operation_id: step23.operation_id,
        current_formal_expression: step23.formal_expression,
        recommended_backup_level: step23.backup_level,
        recommended_formalization_status: "needs_human_review",
        recommended_operation_id: step23.operation_id,
        arithmetic_validation_eligibility: "needs_cullen_page_check",
        rationale:
          "Current inputs show source '38 or above' and Cullen commentary '43 or more' in a carry explanation, but do not establish a page-level explanation tight enough for automatic arithmetic validation. Keep this out of run-now until the Cullen page is checked directly in a later stage.",
      },
    ],
    downgrade_count: 2,
    rename_suggestion_count: 1,
    needs_page_check_count: 1,
  };
}

function validateEqual(actual, expected) {
  return JSON.stringify(actual) === JSON.stringify(expected);
}

function buildValidationResults(entryMap) {
  const results = [];

  const pushResult = (result) => {
    results.push({ ...result, pass: validateEqual(result.computed_result, result.expected_result) });
  };

  pushResult({
    step_id: "Proc.2.3.step.1",
    expression: "24 * 2392 = 57408",
    input_values: { accumulated_months: 24, lunation_factor: 2392 },
    expected_result: { product: 57408 },
    computed_result: { product: 24 * 2392 },
    cullen_backup: entryMap.get("Proc.2.3.step.1").cullen_worked_example,
    notes: "Direct Cullen worked-example multiplication.",
  });

  const step23Product = 24 * 2392;
  pushResult({
    step_id: "Proc.2.3.step.2",
    expression: "floor(57408 / 81) = 708",
    input_values: { product: step23Product, day_factor: 81 },
    expected_result: { accumulated_days: 708 },
    computed_result: { accumulated_days: Math.floor(step23Product / 81) },
    cullen_backup: entryMap.get("Proc.2.3.step.2").cullen_worked_example,
    notes: "Quotient component of the Cullen worked example.",
  });

  pushResult({
    step_id: "Proc.2.3.step.2",
    expression: "57408 mod 81 = 60",
    input_values: { product: step23Product, day_factor: 81 },
    expected_result: { lesser_remainder: 60 },
    computed_result: { lesser_remainder: step23Product % 81 },
    cullen_backup: entryMap.get("Proc.2.3.step.2").cullen_worked_example,
    notes: "Remainder component of the Cullen worked example.",
  });

  pushResult({
    step_id: "Proc.2.3.step.4",
    expression: "708 mod 60 = 48",
    input_values: { accumulated_days: 708, sexagenary_cycle: 60 },
    expected_result: { greater_remainder: 48 },
    computed_result: { greater_remainder: 708 % 60 },
    cullen_backup: entryMap.get("Proc.2.3.step.4").cullen_worked_example,
    notes: "Greater-remainder cast-out from Cullen's worked example.",
  });

  pushResult({
    step_id: "Proc.2.3.step.6",
    expression: "2392 = 29 * 81 + 43",
    input_values: { lunation_factor: 2392, day_factor: 81 },
    expected_result: { quotient: 29, remainder: 43 },
    computed_result: { quotient: Math.floor(2392 / 81), remainder: 2392 % 81 },
    cullen_backup: entryMap.get("Proc.2.3.step.6").cullen_commentary_phrase,
    notes: "Very explicit B-level commentary relation supporting the 29/43 increment pair.",
  });

  const quarter = 2392 / 4;
  pushResult({
    step_id: "Proc.2.3.step.8",
    expression: "2392 / 4 = 598",
    input_values: { lunation_factor: 2392, divisor: 4 },
    expected_result: { quarter_factor: 598 },
    computed_result: { quarter_factor: quarter },
    cullen_backup: entryMap.get("Proc.2.3.step.8").cullen_worked_example,
    notes: "First-quarter factor from Cullen's worked example.",
  });

  pushResult({
    step_id: "Proc.2.3.step.8",
    expression: "598 = 7 * 81 + 31",
    input_values: { quarter_factor: quarter, day_factor: 81 },
    expected_result: { quotient: 7, remainder: 31 },
    computed_result: { quotient: Math.floor(quarter / 81), remainder: quarter % 81 },
    cullen_backup: entryMap.get("Proc.2.3.step.8").cullen_worked_example,
    notes: "Worked-example decomposition behind the 7/31 first-quarter increment.",
  });

  pushResult({
    step_id: "Proc.2.9.step.1",
    expression: "19 * 81 = 1539",
    input_values: { rule_years: 19, day_factor: 81 },
    expected_result: { concordance_factor: 1539 },
    computed_result: { concordance_factor: 19 * 81 },
    cullen_backup: entryMap.get("Proc.2.9.step.1").cullen_commentary_phrase,
    notes: "Very explicit B-level commentary relation for scale conversion.",
  });

  return results;
}

async function main() {
  const [mapPayload, auditPayload, pilotPayload, reconPayload] = await Promise.all([
    readJson(INPUT_MAP),
    readJson(INPUT_AUDIT),
    readJson(INPUT_PILOT),
    readJson(INPUT_RECON),
  ]);

  const entries = mapPayload.entries ?? [];
  ensure(entries.length > 0, "Expression map has no entries.");
  ensure(auditPayload.stage === "phase2a_expression_quality_audit", "Wrong audit input.");
  ensure((pilotPayload.items ?? []).length > 0, "Pilot input has no items.");
  ensure((reconPayload.items ?? []).length > 0, "Reconstruction input has no items.");
  ensure(TARGET_PROC_IDS.every((procId) => entries.some((entry) => entry.proc_id === procId)), "Expression map is missing target Proc entries.");

  const entryMap = new Map(entries.map((entry) => [entry.step_id, entry]));
  const whitelistItems = buildWhitelistItems(entries);
  const whitelistByRunState = {
    run_now: whitelistItems.filter((item) => item.can_run_now),
    candidate_but_not_run_now: whitelistItems.filter(
      (item) => !item.can_run_now && CANDIDATE_BUT_NOT_RUN_NOW_STEP_IDS.includes(item.step_id)
    ),
    excluded: whitelistItems.filter(
      (item) => !item.can_run_now && !CANDIDATE_BUT_NOT_RUN_NOW_STEP_IDS.includes(item.step_id)
    ),
  };

  const whitelistPayload = {
    generated_at: new Date().toISOString(),
    stage: "phase2a_arithmetic_validation_whitelist",
    input_scope: {
      expression_map: INPUT_MAP,
      expression_quality_audit: INPUT_AUDIT,
      phase2a_pilot: INPUT_PILOT,
      reconstruction: INPUT_RECON,
      target_proc_ids: TARGET_PROC_IDS,
    },
    items: whitelistItems,
    summary: whitelistByRunState,
  };

  const downgradePayload = buildDowngradeReport(entryMap);
  const validationResults = buildValidationResults(entryMap);
  const validationPayload = {
    generated_at: new Date().toISOString(),
    stage: "phase2a_arithmetic_validation_pilot",
    source_whitelist_step_ids: RUN_NOW_STEP_IDS,
    results: validationResults,
    summary: {
      total_results: validationResults.length,
      all_pass: validationResults.every((result) => result.pass),
    },
    excluded_from_auto_run: whitelistItems
      .filter((item) => !item.can_run_now)
      .map((item) => ({ step_id: item.step_id, reason: item.reason })),
  };

  await writeJson(OUTPUT_WHITELIST_JSON, whitelistPayload);
  await writeJson(OUTPUT_DOWNGRADE_JSON, downgradePayload);
  await writeJson(OUTPUT_VALIDATION_JSON, validationPayload);
  await fs.writeFile(OUTPUT_WHITELIST_MD, renderWhitelistMarkdown(whitelistPayload), "utf8");
  await fs.writeFile(OUTPUT_DOWNGRADE_MD, renderDowngradeMarkdown(downgradePayload), "utf8");
  await fs.writeFile(OUTPUT_VALIDATION_MD, renderValidationMarkdown(validationPayload), "utf8");

  process.stdout.write(
    [
      OUTPUT_WHITELIST_JSON,
      OUTPUT_WHITELIST_MD,
      OUTPUT_DOWNGRADE_JSON,
      OUTPUT_DOWNGRADE_MD,
      OUTPUT_VALIDATION_JSON,
      OUTPUT_VALIDATION_MD,
    ].join("\n")
  );
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
