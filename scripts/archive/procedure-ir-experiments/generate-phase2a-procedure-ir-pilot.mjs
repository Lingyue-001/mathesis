import { readJson, writeJson } from "./cullen-oracle-common.mjs";
import fs from "node:fs/promises";
import path from "node:path";

const OUTPUT_JSON = "tmp/procedure-ir/phase2a-procedure-ir-pilot.json";
const OUTPUT_MD = "tmp/procedure-ir/phase2a-procedure-ir-pilot.md";

const PILOT_SPECS = [
  {
    proc_id: "Proc. 2.3",
    phase2_role: "pilot_positive_example",
    source_span_id: "santong:L109",
    expected_title: "推正月朔",
    confidence: "high",
    procedure_goal: "Predict the conjunction day of the standard month, then derive the next month's conjunction and the first-quarter/full-moon offsets from the same remainder pair.",
    translation_excerpt:
      "To predict the conjunction of the Standard Month: §175 Multiply Accumulated Months by Lunation Factor [2392]. Count 1 for each filling of the Day Factor [81], and the name of this is Accumulated Days. What does not fill is called the Lesser Remainder. If the Lesser Remainder is 38 or above, the month is long. If the Accumulated Days fills 60, cast it out. What does not fill is called the Greater Remainder. Count starting from the Concordance Head, and outside the count is the day of conjunction. To seek the next month, add to the Greater Remainder 29, and to the Lesser Remainder 43. Count one for each time the Lesser Remainder fills the Day Factor [81], and let it go with the Greater Remainder. Then count and cast out according to the method. To seek the first quarter, add to the Greater Remainder 7, and to the Lesser Remainder 31. To seek full moon, double [the amounts] for the first quarter.",
    commentary_excerpt:
      "The example states that 24 × 2392 = 57,408 and 57,408/81 = 708 remainder 60, explaining why 29 and 43 advance the next conjunction and why 7 and 31 give the first-quarter increment.",
    inputs: [
      { name: "积月", provenance: "source_text", note: "Primary variable multiplied at the start." },
      { name: "统首日", provenance: "source_text", note: "Base point for counting outside to the conjunction day." },
    ],
    constants: [
      { name: "月法", value: 2392, provenance: "Cullen translation", note: "Lunation Factor used in the opening multiplication." },
      { name: "日法", value: 81, provenance: "Cullen translation", note: "Day Factor used for quotient/remainder." },
      { name: "小馀 long-month threshold", value: 38, provenance: "source_text + Cullen translation", note: "Threshold for declaring a long month." },
      { name: "sexagenary cycle", value: 60, provenance: "source_text + Cullen translation", note: "Accumulated Days are cast out by 60." },
      { name: "next-month increment", value: [29, 43], provenance: "source_text + Cullen translation", note: "Added to Greater/Lesser Remainders." },
      { name: "first-quarter increment", value: [7, 31], provenance: "source_text + Cullen translation", note: "Added to Greater/Lesser Remainders." },
    ],
    operations: [
      { action: "multiply", provenance: "source_text + Cullen translation", evidence: "以月法乘积月 / Multiply Accumulated Months by Lunation Factor [2392]." },
      { action: "count", provenance: "Cullen translation", evidence: "Count 1 for each filling of the Day Factor [81]." },
      { action: "cast out", provenance: "source_text + Cullen translation", evidence: "积日盈六十，除之 / If the Accumulated Days fills 60, cast it out." },
      { action: "count outside", provenance: "source_text + Cullen translation", evidence: "数从统首日起，算外，则朔日也 / Count starting from the Concordance Head, and outside the count is the day of conjunction." },
      { action: "add", provenance: "source_text + Cullen translation", evidence: "加大馀二十九，小馀四十三；加大馀七，小馀三十一。" },
      { action: "double", provenance: "source_text + Cullen translation", evidence: "求望，倍弦 / To seek full moon, double [the amounts] for the first quarter." },
    ],
    outputs: [
      { name: "积日", provenance: "source_text + Cullen translation" },
      { name: "小馀", provenance: "source_text + Cullen translation" },
      { name: "大馀", provenance: "source_text + Cullen translation" },
      { name: "朔日", provenance: "source_text + Cullen translation" },
      { name: "次月 remainder pair", provenance: "source_text + Cullen translation" },
      { name: "弦 remainder pair", provenance: "source_text + Cullen translation" },
      { name: "望 remainder pair", provenance: "source_text + Cullen translation" },
    ],
    ordered_steps: [
      "Multiply 积月 by 月法 to produce 积日 and a 小馀 under 日法.",
      "If 小馀 is 38 or above, mark the month as long.",
      "If 积日 fills 60, cast out 60 and retain 大馀.",
      "Count from 统首日 and take the day outside the count as 朔日.",
      "For the next month, add 29 to 大馀 and 43 to 小馀, then carry again by 日法 and cast out as before.",
      "For the first quarter, add 7 to 大馀 and 31 to 小馀; for full moon, double the first-quarter increment.",
    ],
    arithmetic_validation_plan: [
      "Verify that the pilot constants reproduce Cullen's example structure: 积月 × 2392, then divide by 81 to get quotient/remainder.",
      "Check that the long-month threshold is applied only to 小馀 and not to the 60-day cast-out step.",
      "Check that the 29/43 and 7/31 updates preserve the text order and operate on the Greater/Lesser Remainder pair rather than on a modernized timestamp.",
    ],
    uncertainties: [
      "The source span compresses several derived subprocedures into one line, so the pilot keeps them in one item rather than splitting them into separate IR records.",
      "This pilot does not resolve whether later Phase 2 should separate conjunction, next-month, quarter, and full-moon branches into sub-items.",
    ],
    cullen_support: {
      anchor_quality_tier: "A_ready_for_phase2",
      source_alignment: "inferred_source_alignment",
      note: "Phase 1 reconstruction matches santong:L109 directly and preserves the quoted Chinese block.",
    },
  },
  {
    proc_id: "Proc. 2.4",
    phase2_role: "pilot_positive_example",
    source_span_id: "santong:L110",
    expected_title: "推闰馀所在",
    confidence: "needs_human_review",
    procedure_goal: "Locate the medial qi at which the Intercalation Surplus completes, then judge whether the preceding month is intercalary.",
    translation_excerpt:
      "To seek where the Intercalation Surplus is located: §176 Multiply the Intercalation Surplus by 12. For an addition of seven, obtain 1, [until you] fill Rule Medial [Qi] [228]. With the number you get, start counting off from winter solstice. Outside the count, then the Medial [Qi] has reached the conclusion of the filling of the Intercalation [Surplus]. The Medial [Qi] is on the conjunction or the second day, so the preceding month is intercalary.",
    commentary_excerpt:
      "Cullen explains that there are 12 medial qi in a year, so the Intercalation Surplus in nineteenth-of-a-lunation units must first be rescaled to 228, then advanced by repeated additions of 7 until the total exceeds the medial-qi cycle.",
    inputs: [
      { name: "闰馀", provenance: "source_text + Cullen translation", note: "Primary surplus being located." },
      { name: "冬至", provenance: "source_text + Cullen translation", note: "Starting point for counting outside." },
    ],
    constants: [
      { name: "multiplier", value: 12, provenance: "source_text + Cullen translation + Cullen commentary", note: "Rescales 闰馀 from nineteenth-of-a-lunation units." },
      { name: "increment after multiplication", value: { source_text: 10, cullen_reconstruction: 7 }, provenance: "source_text + Cullen translation", note: "This is the key boundary discrepancy and is not normalized away in the pilot." },
      { name: "章中 / Rule Medial [Qi]", value: 228, provenance: "Cullen translation + Cullen commentary", note: "Filling threshold for the repeated advance." },
    ],
    operations: [
      { action: "multiply", provenance: "source_text + Cullen translation", evidence: "以十二乘闰馀 / Multiply the Intercalation Surplus by 12." },
      { action: "add", provenance: "source_text + Cullen translation", evidence: "加十得一 vs. Cullen's 加七得一." },
      { action: "count", provenance: "source_text + Cullen translation", evidence: "盈章中，数所得 / obtain counts until filling Rule Medial [Qi] [228]." },
      { action: "count outside", provenance: "source_text + Cullen translation", evidence: "起冬至，算外 / start from winter solstice; outside the count..." },
      { action: "classify", provenance: "source_text + Cullen translation", evidence: "中气在朔若二日，则前月闰也 / if the medial qi is on conjunction or day two, the preceding month is intercalary." },
    ],
    outputs: [
      { name: "中至终闰盈的中气位置", provenance: "source_text + Cullen translation" },
      { name: "前月是否为闰月", provenance: "source_text + Cullen translation" },
    ],
    ordered_steps: [
      "Multiply 闰馀 by 12.",
      "Advance the result by the stated increment until 章中 is filled, recording how many advances are obtained.",
      "Count from winter solstice and take the qi outside the count as the qi where the intercalation surplus completes.",
      "If that medial qi falls on conjunction day or day two, mark the preceding month as intercalary.",
    ],
    arithmetic_validation_plan: [
      "Validate the unit conversion logic Cullen states explicitly: 12 × 19 = 228, so the multiplier must be preserving the commentary's rescaling argument.",
      "Keep the source's 加十 and Cullen's 加七 side by side and verify later by page-level evidence rather than silently choosing one.",
      "Test the counting rule only as an ordered procedure over qi positions; do not yet promote it into a finalized calendar-month writeback rule.",
    ],
    uncertainties: [
      "The source span reads 加十得一, while the Phase 1 Cullen reconstruction preserves the emended reading 加(十)[七]得一.",
      "Current automated alignment has not closed a direct anchor, so this pilot relies on the confirmed Phase 1 mapping rather than on existing bound claims.",
      "The exact operational meaning of 盈章中 and whether it is best modeled as repeated addition or quotient/remainder remains for human review.",
    ],
    cullen_support: {
      anchor_quality_tier: "D_needs_human_review",
      source_alignment: "phase1_confirmed_mapping_override",
      note: "The pilot follows the confirmed Proc. 2.4 -> santong:L110 mapping without changing Phase 1 reconstruction outputs.",
    },
  },
  {
    proc_id: "Proc. 2.5",
    phase2_role: "pilot_positive_example",
    source_span_id: "santong:L111",
    expected_title: "推冬至",
    confidence: "medium",
    procedure_goal: "Predict the winter-solstice day for the target year from years into the concordance and the reckoning surplus.",
    translation_excerpt:
      "To predict winter solstice: §177 By Reckoning Surplus [8080] multiply the number of years into the Concordance, obtaining 1 for each filling of the Concordance Factor [1539]. [This] is called the Greater Remainder. What does not fill is called the Lesser Remainder. Cast out and count off according to the method, then that is the winter solstice day of the year sought.",
    commentary_excerpt:
      "Cullen notes that 8080 is the number of days by which the days in a Concordance of 1539 years exceed a multiple of 360, and that the rest of the procedure follows the already established counting method.",
    inputs: [
      { name: "入统岁数", provenance: "source_text + Cullen translation", note: "Years into the concordance." },
      { name: "算馀", provenance: "source_text + Cullen translation", note: "Reckoning Surplus multiplier." },
    ],
    constants: [
      { name: "算馀 / Reckoning Surplus", value: 8080, provenance: "Cullen translation + Cullen commentary", note: "Introduced explicitly by Cullen." },
      { name: "统法 / Concordance Factor", value: 1539, provenance: "Cullen translation + Cullen commentary", note: "Filling threshold for quotient/remainder." },
    ],
    operations: [
      { action: "multiply", provenance: "source_text + Cullen translation", evidence: "以算馀乘人统岁数 / By Reckoning Surplus multiply the number of years into the Concordance." },
      { action: "count", provenance: "Cullen translation", evidence: "obtaining 1 for each filling of the Concordance Factor [1539]." },
      { action: "cast out", provenance: "source_text + Cullen translation", evidence: "除数如法 / Cast out and count off according to the method." },
      { action: "count outside", provenance: "Cullen translation", evidence: "the winter solstice day is recovered by the same established counting method." },
    ],
    outputs: [
      { name: "大馀", provenance: "source_text + Cullen translation" },
      { name: "小馀", provenance: "source_text + Cullen translation" },
      { name: "冬至日", provenance: "source_text + Cullen translation" },
    ],
    ordered_steps: [
      "Multiply 入统岁数 by 算馀.",
      "For each filling of 统法, obtain one unit and name the quotient 大馀.",
      "Name the remainder 小馀.",
      "Cast out and count according to the previously established method to get the winter-solstice day.",
    ],
    arithmetic_validation_plan: [
      "Check Cullen's commentary equation linking 8080 and 1539 before trusting any later quotient/remainder implementation.",
      "Verify that the pilot keeps this procedure dependent on an earlier counting convention rather than inventing a new standalone day-cycle base.",
      "Confirm later whether the source variants 算/策 and 人/入 affect only orthography or also downstream normalization rules.",
    ],
    uncertainties: [
      "The source phrase 除数如法 presupposes an earlier counting method not restated in this line, so the pilot does not over-specify the final count base.",
      "The Phase 1 executable step parse for this line is still mechanically rough, so the pilot relies on source text plus Cullen rather than on current step parsing.",
    ],
    cullen_support: {
      anchor_quality_tier: "A_ready_for_phase2",
      source_alignment: "inferred_source_alignment",
      note: "Phase 1 reconstruction matches santong:L111 directly, but downstream executable parsing remains incomplete.",
    },
  },
  {
    proc_id: "Proc. 2.9",
    phase2_role: "pilot_positive_example",
    source_span_id: "santong:L116",
    expected_title: "推其日夜半所在星",
    confidence: "medium",
    procedure_goal: "Predict the sun's midnight lodge/du position by backing off from the conjunction mark-point using the month's Lesser Remainder.",
    translation_excerpt:
      "To predict the star where the sun is located at midnight: §182 Multiply the Lesser Remainder of the month by Rule Years [19], and by that diminish the du of the mark-point for the conjunction. If the Lesser Remainder is insufficient, break a whole du [into parts].",
    commentary_excerpt:
      "Cullen explains that the month's Lesser Remainder is a day-fraction on an 81-part scale; multiplying by 19 converts it to the 1539-part scale used for fractions of a du, and subtraction from the conjunction mark-point gives the preceding midnight position.",
    inputs: [
      { name: "月小馀", provenance: "source_text + Cullen translation", note: "Fractional part of the month used as the time offset." },
      { name: "合晨度", provenance: "source_text + Cullen translation", note: "Conjunction mark-point in du/parts." },
    ],
    constants: [
      { name: "章岁 / Rule Years", value: 19, provenance: "source_text + Cullen translation + Cullen commentary", note: "Multiplier for converting the time fraction." },
      { name: "fractional day scale", value: 81, provenance: "Cullen commentary", note: "Scale of the monthly Lesser Remainder." },
      { name: "统法 / Concordance Factor", value: 1539, provenance: "Cullen commentary", note: "19 × 81, used for du fractions." },
    ],
    operations: [
      { action: "multiply", provenance: "source_text + Cullen translation", evidence: "以章岁乘月小馀 / Multiply the Lesser Remainder of the month by Rule Years [19]." },
      { action: "subtract", provenance: "source_text + Cullen translation", evidence: "以减合晨度 / diminish the du of the mark-point for the conjunction." },
      { action: "break whole degree into parts", provenance: "source_text + Cullen translation", evidence: "小馀不足者，破全度 / If the Lesser Remainder is insufficient, break a whole du [into parts]." },
    ],
    outputs: [
      { name: "日夜半所在星/度", provenance: "source_text + Cullen translation" },
    ],
    ordered_steps: [
      "Take the month's 小馀.",
      "Multiply 小馀 by 章岁.",
      "Subtract the resulting amount from 合晨度.",
      "If the available remainder is insufficient for subtraction, break one whole degree into parts and continue the subtraction.",
    ],
    arithmetic_validation_plan: [
      "Verify Cullen's scale-conversion explanation explicitly: 19 × 81 = 1539.",
      "Check that subtraction is modeled as backing off from conjunction toward the preceding midnight rather than as a forward advance.",
      "Keep the borrow step ('break a whole du into parts') explicit and separate from any later generalized borrow logic.",
    ],
    uncertainties: [
      "The current Phase 1 anchor inventory does not bind this proc directly even though reconstruction matches santong:L116 well.",
      "The quoted translation in reconstruction trims immediately before Proc. 2.10, so this pilot must keep a strict boundary at the Proc. 2.9 procedural clause.",
      "The exact representation of 合晨度 as lodge+du+parts is left open in the pilot.",
    ],
    cullen_support: {
      anchor_quality_tier: "B_needs_source_alignment",
      source_alignment: "phase1_confirmed_mapping_override",
      note: "The pilot accepts the confirmed Proc. 2.9 -> santong:L116 mapping while keeping alignment uncertainty explicit.",
    },
  },
  {
    proc_id: "Proc. 3.2",
    phase2_role: "benchmark_do_not_touch",
    source_span_id: "sifen:L66",
    expected_title: "推入蔀術曰",
    confidence: "high",
    procedure_goal: "Find the entered Era and Obscuration, then recover the sexagenary year-name position for the target year.",
    translation_excerpt:
      "To find [the sexagenary year number of] entry into the Obscuration: §43 Cast out Origin Factor [4560] from accumulated years from Grand Origin. Cast out Era Factor [1520] from the remainder. Number from the Heaven Era by how many you obtain, then outside the count is the Era you are entering. As for what does not amount to an Era Factor [1520], it is the number of years entered into the Era. Cast out Obscuration Factor [76] from it. Number from the jiazi.1 Obscuration by how many you obtain, then outside your count, [that is the Obscuration which is being entered. As for what does not amount to an Obscuration Factor [76], that is the number of years into the Obscuration.]",
    commentary_excerpt:
      "Cullen states that the aim is to find the sexagenary number of the year now beginning by first locating the current Era and Obscuration from repeating cycles, then counting forward from the row and column data supplied in Table 3.1.",
    inputs: [
      { name: "上元积年", provenance: "source_text + Cullen translation", note: "Accumulated years from Grand Origin." },
    ],
    constants: [
      { name: "元法 / Origin Factor", value: 4560, provenance: "source_text + Cullen translation", note: "First cycle cast-out." },
      { name: "纪法 / Era Factor", value: 1520, provenance: "source_text + Cullen translation", note: "Second cycle cast-out." },
      { name: "蔀法 / Obscuration Factor", value: 76, provenance: "source_text + Cullen translation", note: "Third cycle cast-out." },
      { name: "天纪", provenance: "source_text + Cullen translation", note: "Reference sequence for numbering the Era." },
      { name: "甲子蔀", provenance: "source_text + Cullen translation", note: "Reference sequence for numbering the Obscuration." },
    ],
    operations: [
      { action: "cast out", provenance: "source_text + Cullen translation", evidence: "以元法除去上元；其馀以纪法除之；以蔀法除之。" },
      { action: "number from", provenance: "source_text + Cullen translation", evidence: "所得数从天纪；所得数从甲子蔀起。" },
      { action: "count outside", provenance: "source_text + Cullen translation", evidence: "算外则所入纪也；算外，所入蔀也。" },
      { action: "label", provenance: "source_text + Cullen translation", evidence: "所入...岁名命之。" },
      { action: "count above", provenance: "source_text + Cullen translation", evidence: "算上，即所求年太岁所在。" },
    ],
    outputs: [
      { name: "所入纪", provenance: "source_text + Cullen translation" },
      { name: "入纪年数", provenance: "source_text + Cullen translation" },
      { name: "所入蔀", provenance: "source_text + Cullen translation" },
      { name: "入蔀年数", provenance: "Cullen translation" },
      { name: "所求年太岁所在", provenance: "source_text + Cullen translation" },
    ],
    ordered_steps: [
      "Cast out whole Origins from accumulated years from Grand Origin.",
      "Cast out Era Factor from the remainder to determine the entered Era and the years into that Era.",
      "Cast out Obscuration Factor from the years-into-Era remainder to determine the entered Obscuration and the years into that Obscuration.",
      "Label the entry point by the relevant year-name sequence.",
      "Count upward from that labeled entry to locate the Great Year / year-name of the target year.",
    ],
    arithmetic_validation_plan: [
      "Check the nested cycle structure explicitly: 4560 -> 1520 -> 76, without collapsing them into a single modulus.",
      "Validate later against Cullen's Table 3.1 usage only after the lookup-table representation is stable.",
      "Keep this item as a benchmark reference for Phase 2A and do not generalize its table-driven counting behavior to other procedures yet.",
    ],
    uncertainties: [
      "Cullen notes that the end of the text is slightly garbled and depends on emendation, so the last labeling/count-above step remains text-critical.",
      "The source span is shorter than Cullen's reconstructed procedural explanation, so some suboutputs are only explicit in Cullen's translation/commentary.",
    ],
    cullen_support: {
      anchor_quality_tier: "A_ready_for_phase2",
      source_alignment: "manual_or_high_confidence_source_alignment",
      note: "This is retained as the benchmark_do_not_touch item for Phase 2A, not a writeback target.",
    },
  },
];

function normalize(text) {
  return String(text ?? "")
    .replace(/\s+/gu, " ")
    .trim();
}

function validateContains(haystack, needle, message) {
  if (!normalize(haystack).includes(normalize(needle))) {
    throw new Error(message);
  }
}

function renderMarkdown(items) {
  const lines = [
    "# Phase 2A Procedure IR Pilot",
    "",
    "- Scope: Proc. 2.3 / 2.4 / 2.5 / 2.9 / 3.2 only",
    "- Generated from Phase 1 confirmed source spans plus Cullen-led reconstruction outputs",
    "- Writeback status: all items remain `do_not_writeback: true`",
    "",
  ];

  for (const item of items) {
    lines.push(`## ${item.proc_id} (${item.phase2_role})`);
    lines.push("");
    lines.push(`- source_span_id: ${item.source_span_id}`);
    lines.push(`- procedure_title: ${item.procedure_title}`);
    lines.push(`- confidence: ${item.confidence}`);
    lines.push(`- do_not_writeback: ${item.do_not_writeback}`);
    lines.push(`- procedure_goal: ${item.procedure_goal}`);
    lines.push("");
    lines.push("### Source Text");
    lines.push("");
    lines.push(item.source_text);
    lines.push("");
    lines.push("### Cullen Support");
    lines.push("");
    lines.push(`- chinese_quote: ${item.cullen_chinese_quoted_text}`);
    lines.push(`- english_translation_excerpt: ${item.cullen_english_translation_excerpt}`);
    lines.push(`- commentary_excerpt: ${item.cullen_commentary_excerpt}`);
    lines.push(`- anchor_quality_tier: ${item.cullen_support.anchor_quality_tier}`);
    lines.push(`- source_alignment: ${item.cullen_support.source_alignment}`);
    lines.push(`- note: ${item.cullen_support.note}`);
    lines.push("");
    lines.push("### Inputs");
    lines.push("");
    for (const input of item.inputs) {
      lines.push(`- ${input.name} | ${input.provenance} | ${input.note}`);
    }
    lines.push("");
    lines.push("### Constants");
    lines.push("");
    for (const constant of item.constants) {
      lines.push(`- ${constant.name} | ${JSON.stringify(constant.value)} | ${constant.provenance} | ${constant.note}`);
    }
    lines.push("");
    lines.push("### Operations");
    lines.push("");
    for (const operation of item.operations) {
      lines.push(`- ${operation.action} | ${operation.provenance} | ${operation.evidence}`);
    }
    lines.push("");
    lines.push("### Outputs");
    lines.push("");
    for (const output of item.outputs) {
      lines.push(`- ${output.name} | ${output.provenance}`);
    }
    lines.push("");
    lines.push("### Ordered Steps");
    lines.push("");
    item.ordered_steps.forEach((step, index) => {
      lines.push(`${index + 1}. ${step}`);
    });
    lines.push("");
    lines.push("### Arithmetic Validation Plan");
    lines.push("");
    for (const step of item.arithmetic_validation_plan) {
      lines.push(`- ${step}`);
    }
    lines.push("");
    lines.push("### Uncertainties");
    lines.push("");
    for (const note of item.uncertainties) {
      lines.push(`- ${note}`);
    }
    lines.push("");
  }

  return `${lines.join("\n")}\n`;
}

async function main() {
  const [sourceSpansRaw, reconstructionRaw] = await Promise.all([
    readJson("tmp/procedure-ir/source_spans.json"),
    readJson("tmp/procedure-ir/cullen-led-source-reconstruction.json"),
  ]);

  const sourceSpanById = new Map((sourceSpansRaw.spans ?? []).map((span) => [span.id, span]));
  const reconstructionByProcId = new Map((reconstructionRaw.items ?? []).map((item) => [item.proc_id, item]));

  const items = PILOT_SPECS.map((spec) => {
    const sourceSpan = sourceSpanById.get(spec.source_span_id);
    const reconstruction = reconstructionByProcId.get(spec.proc_id);

    if (!sourceSpan) throw new Error(`Missing source span for ${spec.proc_id}: ${spec.source_span_id}`);
    if (!reconstruction) throw new Error(`Missing reconstruction item for ${spec.proc_id}`);

    validateContains(
      sourceSpan.text,
      spec.expected_title,
      `Source span ${spec.source_span_id} does not contain expected title ${spec.expected_title}`
    );
    validateContains(
      reconstruction.cullen_chinese_quoted_text,
      spec.expected_title.replace("闰", "閏").replace("馀", "餘").replace("岁", "歲"),
      `Reconstruction quote for ${spec.proc_id} does not contain expected title`
    );

    return {
      proc_id: spec.proc_id,
      phase2_role: spec.phase2_role,
      source_span_id: spec.source_span_id,
      source_text: sourceSpan.text,
      cullen_chinese_quoted_text: reconstruction.cullen_chinese_quoted_text,
      cullen_english_translation_excerpt: spec.translation_excerpt,
      cullen_commentary_excerpt: spec.commentary_excerpt,
      procedure_title: spec.expected_title,
      procedure_goal: spec.procedure_goal,
      inputs: spec.inputs,
      constants: spec.constants,
      operations: spec.operations,
      outputs: spec.outputs,
      ordered_steps: spec.ordered_steps,
      arithmetic_validation_plan: spec.arithmetic_validation_plan,
      cullen_support: spec.cullen_support,
      uncertainties: spec.uncertainties,
      confidence: spec.confidence,
      do_not_writeback: true,
    };
  });

  const payload = {
    generated_at: new Date().toISOString(),
    stage: "phase2a_pilot",
    note: "Scope is explicitly limited to Proc. 2.3 / 2.4 / 2.5 / 2.9 / 3.2 using confirmed Phase 1 mappings only.",
    items,
  };

  await writeJson(OUTPUT_JSON, payload);
  await fs.mkdir(path.dirname(OUTPUT_MD), { recursive: true });
  await fs.writeFile(OUTPUT_MD, renderMarkdown(items), "utf8");

  process.stdout.write(`${OUTPUT_JSON}\n${OUTPUT_MD}\n`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
