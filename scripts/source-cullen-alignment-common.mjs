import fs from "node:fs/promises";
import path from "node:path";
import {
  normalizeWhitespace,
  resolveRepoPath,
  writeJson,
} from "./cullen-oracle-common.mjs";

export const SOURCE_PROCEDURE_INVENTORY_JSON = "tmp/procedure-ir/source-procedure-inventory.json";
export const SOURCE_PROCEDURE_INVENTORY_MD = "tmp/procedure-ir/source-procedure-inventory.md";
export const SOURCE_CULLEN_ALIGNMENT_CANDIDATES_JSON = "tmp/procedure-ir/source-cullen-alignment-candidates.json";
export const SOURCE_CULLEN_ALIGNMENT_REVIEW_PACKET_MD = "tmp/procedure-ir/source-cullen-alignment-review-packet.md";
export const SOURCE_CULLEN_ALIGNMENT_AUDIT_JSON = "tmp/procedure-ir/source-cullen-alignment-audit.json";
export const SOURCE_CULLEN_ALIGNMENT_AUDIT_MD = "tmp/procedure-ir/source-cullen-alignment-audit.md";

export const SOURCE_PROCEDURE_INVENTORY_REFINED_JSON = "tmp/procedure-ir/source-procedure-inventory.refined.json";
export const SOURCE_PROCEDURE_INVENTORY_REFINED_MD = "tmp/procedure-ir/source-procedure-inventory.refined.md";
export const SOURCE_PROCEDURE_SEGMENTATION_AUDIT_JSON = "tmp/procedure-ir/source-procedure-segmentation-audit.json";
export const SOURCE_PROCEDURE_SEGMENTATION_AUDIT_MD = "tmp/procedure-ir/source-procedure-segmentation-audit.md";
export const SOURCE_CULLEN_ALIGNMENT_CANDIDATES_REFINED_JSON = "tmp/procedure-ir/source-cullen-alignment-candidates.refined.json";
export const SOURCE_CULLEN_ALIGNMENT_REVIEW_PACKET_REFINED_MD = "tmp/procedure-ir/source-cullen-alignment-review-packet.refined.md";
export const SOURCE_CULLEN_ALIGNMENT_AUDIT_REFINED_JSON = "tmp/procedure-ir/source-cullen-alignment-audit.refined.json";
export const SOURCE_CULLEN_ALIGNMENT_AUDIT_REFINED_MD = "tmp/procedure-ir/source-cullen-alignment-audit.refined.md";

const SYSTEMS = new Set(["santong", "sifen"]);
const GENERIC_CHINESE_TERMS = new Set(["積日", "餘", "乘", "除", "法", "實", "蔀法"]);
const GENERIC_OPERATION_TERMS = new Set(["multiply", "divide", "set out", "remainder", "count"]);
const NON_DISTINCTIVE_ALIGNMENT_TERMS = new Set([
  "unknown",
  "obscuration_entry",
  "tianzheng_shuori",
  "intercalary_month",
  "eclipse_chain",
  "du_lodge_sun",
  "du_lodge_moon",
  "planet_conjunction",
  "mei_mie",
]);
const TITLE_ONLY_PREFIXES = [/^推/u, /^求/u];
const CONTINUATION_PREFIX = /^(求|加|又|其|滿|不滿|餘|乃|則|從)/u;
const PROCEDURE_DETECTION_RE = /(術曰|推[^，。]{0,24}|求[^，。]{0,24}|置[^，。]{0,24}|以[^，。]{0,24}(除之|乘之)|滿[^，。]{0,16}為|不滿|餘)/u;

function uniqueStrings(items) {
  return [...new Set((items ?? [])
    .flatMap((item) => Array.isArray(item) ? item : [item])
    .filter(Boolean)
    .map((item) => String(item).trim())
    .filter(Boolean))];
}

function sanitizeText(text) {
  return String(text ?? "").replace(/\s+/gu, " ").trim();
}

function excerpt(text, max = 220) {
  const value = sanitizeText(text);
  return value.length > max ? `${value.slice(0, max)}...` : value;
}

function chapterForSystem(system) {
  return system === "santong" ? 2 : system === "sifen" ? 3 : null;
}

function normalizeChineseTitleForMatch(text) {
  return sanitizeText(text)
    .replace(/[：:，。、「」『』（）()〈〉《》〔〕【】\[\]\s]/gu, "")
    .replace(/術曰|術|曰/gu, "")
    .trim();
}

function parseProcNumber(procId) {
  const match = String(procId ?? "").match(/Proc\. ([234])\.(\d+)(?!\d)/u);
  if (!match) return null;
  return { chapter: Number(match[1]), procNumber: Number(match[2]) };
}

function getOrderedSpans(sourceSpansPayload) {
  const bySystem = new Map();
  for (const span of sourceSpansPayload.spans ?? []) {
    if (!SYSTEMS.has(span.source_id)) continue;
    if (!bySystem.has(span.source_id)) bySystem.set(span.source_id, []);
    bySystem.get(span.source_id).push(span);
  }
  for (const spans of bySystem.values()) {
    spans.sort((left, right) => (left.line_start ?? 0) - (right.line_start ?? 0));
  }
  return bySystem;
}

function inferHeading(text) {
  const value = String(text ?? "");
  const match = value.match(/^(推[^：:，。]{1,32}(?:術曰|術)?|求[^：:，。]{1,20}|置[^：:，。]{1,20})/u);
  return match ? match[1] : excerpt(value, 80);
}

function extractDistinctiveTerms(text) {
  const value = String(text ?? "");
  const terms = [];
  if (/入蔀|entry into the Obscuration|entered into the Obscuration/iu.test(value)) terms.push("入蔀");
  if (/天正|Celestial Standard|Standard Month|first month/iu.test(value)) terms.push("天正");
  if (/閏月|intercalary month/iu.test(value)) terms.push("閏月");
  if (/冬至|winter solstice/iu.test(value)) terms.push("冬至");
  if (/朔日|conjunction day|day of conjunction/iu.test(value)) terms.push("朔日");
  if (/月食|lunar eclipse|eclipse/iu.test(value)) terms.push("月食");
  if (/五星|five planets|planet/iu.test(value)) terms.push("五星");
  if (/星合月|planet.?s conjunction month|month of a planet.?s conjunction/iu.test(value)) terms.push("星合月");
  if (/日明|sun at dawn|sun at dusk/iu.test(value)) terms.push("日明");
  if (/月明|moon at dawn|moon at dusk/iu.test(value)) terms.push("月明");
  if (/弦|望|crescent|full moon/iu.test(value)) terms.push("弦望");
  if (/沒滅|extinction|obliteration/iu.test(value)) terms.push("沒滅");
  if (/見月|month of visibility/iu.test(value)) terms.push("見月");
  if (/至日|Arrival|Medial qi/iu.test(value)) terms.push("至日");
  return uniqueStrings(terms).filter((term) => !NON_DISTINCTIVE_ALIGNMENT_TERMS.has(term));
}

function extractOperationTermsFromText(text) {
  const value = String(text ?? "");
  const ops = [];
  if (/置/u.test(value)) ops.push("set out");
  if (/乘/u.test(value)) ops.push("multiply");
  if (/除/u.test(value)) ops.push("divide");
  if (/減/u.test(value)) ops.push("subtract");
  if (/加/u.test(value)) ops.push("add");
  if (/從|起|命/u.test(value)) ops.push("count");
  if (/餘|算外|筭外/u.test(value)) ops.push("remainder");
  return uniqueStrings(ops);
}

function canonicalOperation(operation) {
  const value = String(operation ?? "").toLowerCase();
  if (value === "quotient_remainder") return "remainder";
  if (value === "mod_cycle") return "count";
  if (value === "set") return "set out";
  return value;
}

function extractSourceConstants(procedure) {
  const values = [];
  for (const step of procedure?.steps ?? []) {
    for (const quantity of [...(step.inputs ?? []), step.output, step.divisor, step.quotient, step.remainder]) {
      if (quantity && Number.isFinite(quantity.value)) values.push(quantity.value);
    }
    if (Number.isFinite(step.modulus)) values.push(step.modulus);
  }
  return [...new Set(values)];
}

function extractAnchorConstants(anchor) {
  const text = `${anchor.english_procedure_excerpt ?? ""} ${anchor.commentary_excerpt ?? ""} ${(anchor.key_constants ?? []).join(" ")}`;
  return [...new Set(
    [...text.matchAll(/\[(\d[\d,]*)\]/gu)]
      .map((match) => Number(match[1].replace(/,/gu, "")))
      .filter(Number.isFinite)
  )];
}

function getAnchorChineseTitle(anchor) {
  const source = `${anchor.chinese_heading_excerpt ?? ""} ${anchor.chinese_procedure_excerpt ?? ""}`;
  const match = source.match(/(推[^：:，。]{1,40}(?:術曰|術)?|求[^：:，。]{1,20}|置[^：:，。]{1,20})/u);
  return match ? match[1] : "";
}

function buildNearbyContext(span, orderedSpans) {
  const index = orderedSpans.findIndex((item) => item.id === span.id);
  const previous = index > 0 ? orderedSpans[index - 1] : null;
  const next = index >= 0 && index < orderedSpans.length - 1 ? orderedSpans[index + 1] : null;
  return {
    previous_span_id: previous?.id ?? null,
    previous_text: previous?.text ?? null,
    next_span_id: next?.id ?? null,
    next_text: next?.text ?? null,
  };
}

function sequenceOrder(items, key) {
  return new Map(items.map((item, index) => [item[key], index]));
}

function overlap(left, right) {
  const leftSet = new Set(left ?? []);
  const rightSet = new Set(right ?? []);
  return [...leftSet].filter((item) => rightSet.has(item));
}

function baselineProcedureMap(sourceSpansPayload, procedurePayload) {
  const map = new Map();

  for (const procedure of procedurePayload.procedures ?? []) {
    if (!SYSTEMS.has(procedure.source_id)) continue;
    if (!procedure.title_guess || procedure.title_guess === "untitled procedure") continue;
    map.set(procedure.source_span_id, procedure);
  }

  for (const span of sourceSpansPayload.spans ?? []) {
    if (!SYSTEMS.has(span.source_id)) continue;
    if (span.kind !== "procedure") continue;
    if (!map.has(span.id)) {
      map.set(span.id, {
        procedure_id: `${span.source_id}:source-proc:${span.id}`,
        source_id: span.source_id,
        source_span_id: span.id,
        title_guess: inferHeading(span.text),
        steps: [],
      });
    }
  }

  return map;
}

function buildInventoryItem({
  sourceProcId,
  system,
  span,
  procedure,
  orderedSpans,
  detectedBy,
  segmentationConfidence,
  headingSpanIds,
  bodySpanIds,
  possibleSplitHeadingBody = false,
  possibleContinuation = false,
  notes = [],
}) {
  const titleOrHeading = procedure?.title_guess && procedure.title_guess !== "untitled procedure"
    ? procedure.title_guess
    : inferHeading(span.text);
  const bodyText = bodySpanIds
    .map((spanId) => orderedSpans.find((item) => item.id === spanId)?.text ?? "")
    .filter(Boolean)
    .join(" ");
  const headingText = headingSpanIds
    .map((spanId) => orderedSpans.find((item) => item.id === spanId)?.text ?? "")
    .filter(Boolean)
    .join(" ");
  const steps = procedure?.steps ?? [];

  return {
    source_proc_id: sourceProcId,
    system,
    source_span_id: span.id,
    line_start: span.line_start ?? null,
    line_end: orderedSpans.find((item) => item.id === bodySpanIds.at(-1))?.line_end ?? span.line_end ?? null,
    title_or_heading: titleOrHeading,
    heading_line_ids: headingSpanIds,
    body_line_ids: bodySpanIds,
    chinese_heading_excerpt: headingText || titleOrHeading,
    chinese_body_excerpt: bodyText || span.text || "",
    combined_excerpt: uniqueStrings([headingText || titleOrHeading, bodyText || span.text]).join("\n\n"),
    nearby_context: buildNearbyContext(span, orderedSpans),
    detected_by: detectedBy,
    segmentation_confidence: segmentationConfidence,
    possible_split_heading_body: possibleSplitHeadingBody,
    possible_continuation: possibleContinuation,
    possible_one_to_many_cullen: false,
    distinctive_terms: extractDistinctiveTerms(`${titleOrHeading} ${bodyText || span.text}`),
    constants: extractSourceConstants(procedure),
    operation_terms: uniqueStrings([
      ...(steps.map((step) => canonicalOperation(step.operation_type)).filter(Boolean)),
      ...extractOperationTermsFromText(bodyText || span.text),
    ]),
    candidate_cullen_proc_ids: [],
    alignment_status: "unmatched",
    notes: uniqueStrings(notes),
  };
}

function buildBaselineInventory(sourceSpansPayload, procedurePayload) {
  const bySystem = getOrderedSpans(sourceSpansPayload);
  const spanById = new Map((sourceSpansPayload.spans ?? []).map((span) => [span.id, span]));
  const items = [];

  for (const procedure of baselineProcedureMap(sourceSpansPayload, procedurePayload).values()) {
    const span = spanById.get(procedure.source_span_id);
    if (!span) continue;
    const orderedSpans = bySystem.get(span.source_id) ?? [];
    const hasProcedureTitle = Boolean(procedure.title_guess && procedure.title_guess !== "untitled procedure");
    items.push(buildInventoryItem({
      sourceProcId: procedure.procedure_id ?? `${span.source_id}:source-proc:${span.id}`,
      system: span.source_id,
      span,
      procedure,
      orderedSpans,
      detectedBy: hasProcedureTitle ? ["procedure_ir_title"] : ["source_span_kind_procedure"],
      segmentationConfidence: hasProcedureTitle ? "high" : "medium",
      headingSpanIds: [span.id],
      bodySpanIds: [span.id],
      notes: hasProcedureTitle ? [] : ["baseline_inventory_without_procedure_ir_title"],
    }));
  }

  items.sort((left, right) => left.system.localeCompare(right.system) || left.line_start - right.line_start);
  return { generated_at: new Date().toISOString(), items };
}

function scanProcedureLikeSpan(span) {
  const text = String(span.text ?? "");
  const detectedBy = [];
  if (/術曰/u.test(text)) detectedBy.push("contains_shu_yue");
  if (/^推/u.test(text)) detectedBy.push("starts_with_tui");
  if (/^求/u.test(text)) detectedBy.push("starts_with_qiu");
  if (/^置/u.test(text)) detectedBy.push("starts_with_zhi");
  if (/以[^，。]{0,20}除之/u.test(text)) detectedBy.push("contains_yi_chu_zhi");
  if (/以[^，。]{0,20}乘之/u.test(text)) detectedBy.push("contains_yi_cheng_zhi");
  if (/滿[^，。]{0,20}為/u.test(text)) detectedBy.push("contains_man_wei");
  if (/不滿/u.test(text)) detectedBy.push("contains_bu_man");
  if (/餘/u.test(text)) detectedBy.push("contains_yu");

  const score = detectedBy.length
    + (/^推/u.test(text) ? 2 : 0)
    + (/術曰/u.test(text) ? 2 : 0)
    + (/^求/u.test(text) || /^置/u.test(text) ? 1 : 0);

  return {
    matches: PROCEDURE_DETECTION_RE.test(text),
    detectedBy,
    score,
  };
}

function buildRefinedInventory(sourceSpansPayload, procedurePayload) {
  const baseline = buildBaselineInventory(sourceSpansPayload, procedurePayload);
  const bySystem = getOrderedSpans(sourceSpansPayload);
  const spanById = new Map((sourceSpansPayload.spans ?? []).map((span) => [span.id, span]));
  const baselineBySpanId = new Map(baseline.items.map((item) => [item.source_span_id, item]));
  const procedureBySpanId = new Map(
    (procedurePayload.procedures ?? [])
      .filter((procedure) => SYSTEMS.has(procedure.source_id))
      .map((procedure) => [procedure.source_span_id, procedure]),
  );

  const items = [...baseline.items];

  for (const [system, spans] of bySystem.entries()) {
    for (let index = 0; index < spans.length; index += 1) {
      const span = spans[index];
      const procedure = procedureBySpanId.get(span.id) ?? null;
      const scan = scanProcedureLikeSpan(span);
      const alreadyInBaseline = baselineBySpanId.has(span.id);
      const hasProcedureTitle = Boolean(procedure?.title_guess && procedure.title_guess !== "untitled procedure");
      const shouldAdd = !alreadyInBaseline && (hasProcedureTitle || scan.matches);
      if (!shouldAdd) continue;

      const nextSpan = index < spans.length - 1 ? spans[index + 1] : null;
      const nextScan = nextSpan ? scanProcedureLikeSpan(nextSpan) : { matches: false, detectedBy: [], score: 0 };
      const shortHeading = sanitizeText(span.text).length < 24 && TITLE_ONLY_PREFIXES.some((pattern) => pattern.test(span.text));
      const truncatedBody = /：$|:$/.test(span.text) || /夜半$|其節氣夜半$/.test(span.text);
      const continuationByNext = Boolean(
        nextSpan
        && nextSpan.line_start - span.line_end <= 6
        && (nextScan.matches || CONTINUATION_PREFIX.test(nextSpan.text))
        && !baselineBySpanId.has(nextSpan.id)
      );

      const headingSpanIds = [span.id];
      const bodySpanIds = continuationByNext ? [nextSpan.id] : [span.id];
      const possibleSplitHeadingBody = shortHeading || truncatedBody || (continuationByNext && shortHeading);
      const possibleContinuation = continuationByNext;
      const detectedBy = uniqueStrings([
        ...(hasProcedureTitle ? ["procedure_ir_title_nonbaseline"] : []),
        ...scan.detectedBy,
        continuationByNext ? "next_span_continuation_candidate" : null,
      ]);
      const confidence = hasProcedureTitle
        ? "high"
        : scan.score >= 4
          ? "medium"
          : "low";

      items.push(buildInventoryItem({
        sourceProcId: procedure?.procedure_id ?? `${system}:refined-source-proc:${span.id}`,
        system,
        span,
        procedure,
        orderedSpans: spans,
        detectedBy,
        segmentationConfidence: confidence,
        headingSpanIds,
        bodySpanIds,
        possibleSplitHeadingBody,
        possibleContinuation,
        notes: uniqueStrings([
          alreadyInBaseline ? null : "refined_inventory_candidate",
          continuationByNext ? `continuation_candidate:${nextSpan.id}` : null,
        ]),
      }));
    }
  }

  const deduped = [];
  const seen = new Set();
  for (const item of items) {
    const key = `${item.system}:${item.heading_line_ids.join(",")}:${item.body_line_ids.join(",")}:${item.title_or_heading}`;
    if (seen.has(key)) continue;
    seen.add(key);
    deduped.push(item);
  }

  deduped.sort((left, right) => left.system.localeCompare(right.system) || left.line_start - right.line_start);
  return { generated_at: new Date().toISOString(), items: deduped, baseline };
}

function scoreCandidate(sourceItem, anchor, sourceOrderMap, anchorOrderMap) {
  const sourceTitle = normalizeChineseTitleForMatch(sourceItem.title_or_heading);
  const anchorTitleRaw = getAnchorChineseTitle(anchor);
  const anchorTitle = normalizeChineseTitleForMatch(anchorTitleRaw);
  const titleMatch = Boolean(
    sourceTitle
    && anchorTitle
    && (sourceTitle === anchorTitle || sourceTitle.includes(anchorTitle) || anchorTitle.includes(sourceTitle))
  );
  const sourceDistinctive = (sourceItem.distinctive_terms ?? []).filter((term) => !NON_DISTINCTIVE_ALIGNMENT_TERMS.has(term));
  const anchorDistinctive = (anchor.distinctive_terms ?? []).filter((term) => !NON_DISTINCTIVE_ALIGNMENT_TERMS.has(term));
  const distinctiveOverlap = overlap(sourceDistinctive, anchorDistinctive);
  const constantOverlap = overlap(sourceItem.constants ?? [], extractAnchorConstants(anchor));
  const operationOverlap = overlap(
    sourceItem.operation_terms ?? [],
    (anchor.operation_skeleton ?? []).map(canonicalOperation),
  ).filter((item) => !GENERIC_OPERATION_TERMS.has(item));
  const genericLexicalOverlap = [...GENERIC_CHINESE_TERMS].filter((term) =>
    sourceItem.combined_excerpt.includes(term)
    && `${anchor.chinese_heading_excerpt ?? ""} ${anchor.chinese_procedure_excerpt ?? ""}`.includes(term)
  );

  const sourceOrder = sourceOrderMap.get(sourceItem.source_proc_id);
  const anchorOrder = anchorOrderMap.get(anchor.anchor_id);
  const orderDelta = Number.isFinite(sourceOrder) && Number.isFinite(anchorOrder)
    ? Math.abs(sourceOrder - anchorOrder)
    : null;
  const orderScore = orderDelta === null ? 0 : Math.max(0, 5 - Math.min(orderDelta, 5));
  const existingAnchorLink = (anchor.source_span_candidates ?? []).includes(sourceItem.source_span_id);

  let score = 0;
  if (existingAnchorLink) score += 20;
  if (titleMatch) score += 16;
  score += distinctiveOverlap.length * 6;
  score += constantOverlap.length * 4;
  score += operationOverlap.length * 2;
  score += orderScore;

  const genericOnly = !existingAnchorLink
    && !titleMatch
    && distinctiveOverlap.length === 0
    && constantOverlap.length === 0
    && operationOverlap.length === 0
    && genericLexicalOverlap.length > 0;

  let confidenceTier = "none";
  if (existingAnchorLink || (titleMatch && (distinctiveOverlap.length > 0 || constantOverlap.length > 0 || orderScore >= 2))) {
    confidenceTier = "high";
  } else if (
    titleMatch
    || (distinctiveOverlap.length > 0 && (constantOverlap.length > 0 || orderScore >= 2))
    || (distinctiveOverlap.length >= 2 && orderScore >= 1)
    || (sourceItem.possible_split_heading_body && titleMatch)
  ) {
    confidenceTier = "medium";
  } else if (score >= 5 || genericOnly) {
    confidenceTier = genericOnly ? "generic_only" : "review";
  }

  return {
    cullen_proc_id: anchor.cullen_proc_id,
    anchor_id: anchor.anchor_id,
    confidence_tier: confidenceTier,
    score,
    order_delta: orderDelta,
    anchor_title_or_heading: anchorTitleRaw || anchor.english_title || "",
    anchor_quality_tier: anchor.quality_tier,
    matched_distinctive_terms: distinctiveOverlap,
    matched_constants: constantOverlap,
    matched_operation_terms: operationOverlap,
    generic_term_matches: genericLexicalOverlap,
    title_match: titleMatch,
    existing_anchor_link: existingAnchorLink,
    reasons: uniqueStrings([
      existingAnchorLink ? "existing_anchor_source_span_candidate" : null,
      titleMatch ? "title_or_heading_overlap" : null,
      distinctiveOverlap.length ? `distinctive_terms:${distinctiveOverlap.join(",")}` : null,
      constantOverlap.length ? `constants:${constantOverlap.join(",")}` : null,
      operationOverlap.length ? `operation_terms:${operationOverlap.join(",")}` : null,
      orderDelta !== null ? `order_delta:${orderDelta}` : null,
      genericOnly ? `generic_terms:${genericLexicalOverlap.join(",")}` : null,
    ]),
  };
}

function buildAlignmentPayload(inventoryPayload, anchorPayload) {
  const items = inventoryPayload.items ?? [];
  const anchors = (anchorPayload.items ?? []).filter((anchor) => SYSTEMS.has(anchor.system));
  const sourceOrderMap = sequenceOrder(items, "source_proc_id");
  const anchorOrderMap = sequenceOrder(
    anchors.slice().sort((left, right) => {
      const leftInfo = parseProcNumber(left.cullen_proc_id);
      const rightInfo = parseProcNumber(right.cullen_proc_id);
      return (leftInfo?.chapter ?? 99) - (rightInfo?.chapter ?? 99)
        || (leftInfo?.procNumber ?? 999) - (rightInfo?.procNumber ?? 999);
    }),
    "anchor_id",
  );

  const alignedItems = items.map((sourceItem) => {
    const chapter = chapterForSystem(sourceItem.system);
    const compatibleAnchors = anchors.filter((anchor) => {
      if (anchor.system !== sourceItem.system) return false;
      return parseProcNumber(anchor.cullen_proc_id)?.chapter === chapter;
    });

    const scored = compatibleAnchors
      .map((anchor) => scoreCandidate(sourceItem, anchor, sourceOrderMap, anchorOrderMap))
      .filter((candidate) => candidate.confidence_tier !== "none")
      .sort((left, right) =>
        (right.score - left.score)
        || ((left.order_delta ?? 999) - (right.order_delta ?? 999))
        || left.cullen_proc_id.localeCompare(right.cullen_proc_id)
      );

    const high = scored.filter((candidate) => candidate.confidence_tier === "high");
    const medium = scored.filter((candidate) => candidate.confidence_tier === "medium");
    const review = scored.filter((candidate) => candidate.confidence_tier === "review").slice(0, 6);
    const genericOnly = scored.filter((candidate) => candidate.confidence_tier === "generic_only");

    let alignmentStatus = "unmatched";
    if (high.length) alignmentStatus = "aligned_high_confidence";
    else if (medium.length) alignmentStatus = "aligned_medium_confidence";
    else if (review.length || genericOnly.length) alignmentStatus = "needs_review";

    return {
      ...sourceItem,
      candidate_cullen_proc_ids: uniqueStrings([...high, ...medium].map((candidate) => candidate.cullen_proc_id)),
      alignment_status: alignmentStatus,
      high_confidence_candidates: high,
      medium_confidence_candidates: medium,
      review_candidates: review,
      generic_only_candidates: genericOnly,
      generic_term_only_candidate_count: genericOnly.length,
      possible_one_to_many_cullen: uniqueStrings([...high, ...medium].map((candidate) => candidate.cullen_proc_id)).length > 1,
      notes: uniqueStrings([
        ...(sourceItem.notes ?? []),
        high.length > 1 ? "multiple_high_confidence_candidates" : null,
        medium.length > 1 ? "multiple_medium_confidence_candidates" : null,
        !high.length && !medium.length && review.length ? "review_required_before_any_anchor_update" : null,
        genericOnly.length ? "generic_term_only_candidates_disallowed_for_anchor_updates" : null,
      ]),
    };
  });

  return {
    generated_at: new Date().toISOString(),
    note: "Machine-generated source-side procedure inventory and Cullen alignment candidates. Non-authoritative review layer only.",
    items: alignedItems,
  };
}

function buildAnchorCandidateMaps(alignmentPayload, anchorPayload) {
  const anchorsWithoutSource = (anchorPayload.items ?? []).filter((anchor) =>
    SYSTEMS.has(anchor.system) && !(anchor.source_span_candidates ?? []).length
  );
  const byAnchor = new Map();
  for (const item of alignmentPayload.items ?? []) {
    for (const candidate of [...(item.high_confidence_candidates ?? []), ...(item.medium_confidence_candidates ?? [])]) {
      if (!byAnchor.has(candidate.anchor_id)) byAnchor.set(candidate.anchor_id, []);
      byAnchor.get(candidate.anchor_id).push(item.source_proc_id);
    }
  }
  return {
    anchorsWithNewCandidates: anchorsWithoutSource
      .filter((anchor) => byAnchor.has(anchor.anchor_id))
      .map((anchor) => anchor.cullen_proc_id),
    anchorsStillWithoutCandidates: anchorsWithoutSource
      .filter((anchor) => !byAnchor.has(anchor.anchor_id))
      .map((anchor) => anchor.cullen_proc_id),
    byAnchor,
  };
}

function buildSegmentationAudit(oldInventoryPayload, refinedInventoryPayload) {
  const oldCount = oldInventoryPayload.items?.length ?? 0;
  const refinedItems = refinedInventoryPayload.items ?? [];
  const newCandidates = refinedItems.filter((item) => (item.notes ?? []).includes("refined_inventory_candidate"));
  return {
    generated_at: new Date().toISOString(),
    old_source_proc_count: oldCount,
    refined_source_proc_count: refinedItems.length,
    new_candidate_source_proc_count: newCandidates.length,
    santong_refined_source_proc_count: refinedItems.filter((item) => item.system === "santong").length,
    sifen_refined_source_proc_count: refinedItems.filter((item) => item.system === "sifen").length,
    possible_heading_body_split_count: refinedItems.filter((item) => item.possible_split_heading_body).length,
    refined_candidates: newCandidates.map((item) => item.source_proc_id),
  };
}

function buildAlignmentAudit({
  oldInventoryPayload,
  refinedInventoryPayload,
  refinedAlignmentPayload,
  anchorPayload,
}) {
  const refinedItems = refinedAlignmentPayload.items ?? [];
  const anchorMaps = buildAnchorCandidateMaps(refinedAlignmentPayload, anchorPayload);
  const possibleOneToMany = refinedItems
    .filter((item) => item.possible_one_to_many_cullen)
    .map((item) => ({
      source_proc_id: item.source_proc_id,
      candidate_cullen_proc_ids: item.candidate_cullen_proc_ids,
      reason: "multiple high/medium candidate Cullen procedures remain plausible",
    }));

  const possibleManyToOne = [...anchorMaps.byAnchor.entries()]
    .filter(([, sourceProcIds]) => uniqueStrings(sourceProcIds).length > 1)
    .map(([anchorId, sourceProcIds]) => {
      const anchor = (anchorPayload.items ?? []).find((item) => item.anchor_id === anchorId);
      return {
        cullen_proc_id: anchor?.cullen_proc_id ?? anchorId,
        source_proc_ids: uniqueStrings(sourceProcIds),
        reason: "multiple refined source procedures point to the same Cullen anchor at high/medium confidence",
      };
    });

  return {
    generated_at: new Date().toISOString(),
    old_source_proc_count: oldInventoryPayload.items?.length ?? 0,
    refined_source_proc_count: refinedInventoryPayload.items?.length ?? 0,
    new_candidate_source_proc_count: (refinedInventoryPayload.items ?? []).filter((item) =>
      (item.notes ?? []).includes("refined_inventory_candidate")
    ).length,
    santong_refined_source_proc_count: refinedItems.filter((item) => item.system === "santong").length,
    sifen_refined_source_proc_count: refinedItems.filter((item) => item.system === "sifen").length,
    possible_heading_body_split_count: refinedItems.filter((item) => item.possible_split_heading_body).length,
    possible_one_to_many_count: possibleOneToMany.length,
    possible_many_to_one_count: possibleManyToOne.length,
    aligned_high_confidence_count: refinedItems.filter((item) => item.alignment_status === "aligned_high_confidence").length,
    aligned_medium_confidence_count: refinedItems.filter((item) => item.alignment_status === "aligned_medium_confidence").length,
    needs_review_count: refinedItems.filter((item) => item.alignment_status === "needs_review").length,
    unmatched_count: refinedItems.filter((item) => item.alignment_status === "unmatched").length,
    wrong_system_candidate_count: 0,
    generic_term_only_candidate_count: refinedItems.reduce((sum, item) => sum + (item.generic_term_only_candidate_count ?? 0), 0),
    cullen_anchors_with_new_high_or_medium_candidates: anchorMaps.anchorsWithNewCandidates,
    cullen_anchors_still_without_source_candidates: anchorMaps.anchorsStillWithoutCandidates,
    possible_one_to_many_alignments: possibleOneToMany,
    possible_many_to_one_alignments: possibleManyToOne,
  };
}

function renderInventoryMarkdown(title, payload, refined = false) {
  const lines = [
    `# ${title}`,
    "",
    refined
      ? "Machine-generated refined source-side procedure inventory. Non-authoritative review layer."
      : "Machine-generated source-side procedure inventory. Non-authoritative review layer.",
    "",
    `Generated: ${payload.generated_at}`,
    "",
  ];

  for (const item of payload.items ?? []) {
    lines.push(`## ${item.source_proc_id}`);
    lines.push(`- system: ${item.system}`);
    lines.push(`- source_span_id: ${item.source_span_id}`);
    lines.push(`- lines: ${item.line_start}-${item.line_end}`);
    lines.push(`- title_or_heading: ${item.title_or_heading}`);
    lines.push(`- heading_line_ids: ${item.heading_line_ids.join(", ") || "none"}`);
    lines.push(`- body_line_ids: ${item.body_line_ids.join(", ") || "none"}`);
    lines.push(`- detected_by: ${(item.detected_by ?? []).join(", ") || "none"}`);
    lines.push(`- segmentation_confidence: ${item.segmentation_confidence}`);
    lines.push(`- possible_split_heading_body: ${item.possible_split_heading_body}`);
    lines.push(`- possible_continuation: ${item.possible_continuation}`);
    lines.push(`- distinctive_terms: ${(item.distinctive_terms ?? []).join(", ") || "none"}`);
    lines.push(`- constants: ${(item.constants ?? []).join(", ") || "none"}`);
    lines.push(`- operation_terms: ${(item.operation_terms ?? []).join(", ") || "none"}`);
    lines.push(`- candidate_cullen_proc_ids: ${(item.candidate_cullen_proc_ids ?? []).join(", ") || "none"}`);
    lines.push(`- alignment_status: ${item.alignment_status}`);
    lines.push(`- chinese_heading_excerpt: ${item.chinese_heading_excerpt}`);
    lines.push(`- chinese_body_excerpt: ${item.chinese_body_excerpt}`);
    lines.push(`- notes: ${(item.notes ?? []).join(", ") || "none"}`);
    lines.push("");
  }

  return `${lines.join("\n")}\n`;
}

function renderReviewPacketMarkdown(title, payload) {
  const lines = [
    `# ${title}`,
    "",
    "Machine-generated review packet. Low-confidence candidates remain review-only and do not update anchor source_span_candidates.",
    "",
    `Generated: ${payload.generated_at}`,
    "",
  ];

  for (const item of payload.items ?? []) {
    lines.push(`## ${item.source_proc_id}`);
    lines.push("");
    lines.push(`- system: ${item.system}`);
    lines.push(`- source_span_id: ${item.source_span_id}`);
    lines.push(`- lines: ${item.line_start}-${item.line_end}`);
    lines.push(`- title_or_heading: ${item.title_or_heading}`);
    lines.push(`- heading_line_ids: ${item.heading_line_ids.join(", ") || "none"}`);
    lines.push(`- body_line_ids: ${item.body_line_ids.join(", ") || "none"}`);
    lines.push(`- alignment_status: ${item.alignment_status}`);
    lines.push(`- segmentation_confidence: ${item.segmentation_confidence}`);
    lines.push(`- distinctive_terms: ${(item.distinctive_terms ?? []).join(", ") || "none"}`);
    lines.push(`- constants: ${(item.constants ?? []).join(", ") || "none"}`);
    lines.push(`- operation_terms: ${(item.operation_terms ?? []).join(", ") || "none"}`);
    lines.push(`- combined_excerpt: ${item.combined_excerpt}`);
    lines.push("");

    const sections = [
      ["High confidence candidates", item.high_confidence_candidates ?? []],
      ["Medium confidence candidates", item.medium_confidence_candidates ?? []],
      ["Review candidates", item.review_candidates ?? []],
      ["Generic term only candidates", item.generic_only_candidates ?? []],
    ];

    for (const [sectionTitle, candidates] of sections) {
      lines.push(`### ${sectionTitle}`);
      lines.push("");
      if (!candidates.length) {
        lines.push("- none", "");
        continue;
      }
      for (const candidate of candidates) {
        lines.push(`- ${candidate.cullen_proc_id}`);
        lines.push(`  confidence_tier: ${candidate.confidence_tier}`);
        lines.push(`  score: ${candidate.score}`);
        lines.push(`  order_delta: ${candidate.order_delta ?? "null"}`);
        lines.push(`  anchor_title_or_heading: ${candidate.anchor_title_or_heading || "none"}`);
        lines.push(`  matched_distinctive_terms: ${(candidate.matched_distinctive_terms ?? []).join(", ") || "none"}`);
        lines.push(`  matched_constants: ${(candidate.matched_constants ?? []).join(", ") || "none"}`);
        lines.push(`  matched_operation_terms: ${(candidate.matched_operation_terms ?? []).join(", ") || "none"}`);
        lines.push(`  generic_term_matches: ${(candidate.generic_term_matches ?? []).join(", ") || "none"}`);
        lines.push(`  reasons: ${(candidate.reasons ?? []).join("; ") || "none"}`);
        lines.push("");
      }
    }
  }

  return `${lines.join("\n")}\n`;
}

function renderSegmentationAuditMarkdown(audit) {
  const lines = [
    "# Source Procedure Segmentation Audit",
    "",
    `Generated: ${audit.generated_at}`,
    "",
    `- old_source_proc_count: ${audit.old_source_proc_count}`,
    `- refined_source_proc_count: ${audit.refined_source_proc_count}`,
    `- new_candidate_source_proc_count: ${audit.new_candidate_source_proc_count}`,
    `- santong_refined_source_proc_count: ${audit.santong_refined_source_proc_count}`,
    `- sifen_refined_source_proc_count: ${audit.sifen_refined_source_proc_count}`,
    `- possible_heading_body_split_count: ${audit.possible_heading_body_split_count}`,
    `- refined_candidates: ${audit.refined_candidates.join(", ") || "none"}`,
    "",
  ];
  return `${lines.join("\n")}\n`;
}

function renderAlignmentAuditMarkdown(audit) {
  const lines = [
    "# Source-Cullen Alignment Audit",
    "",
    `Generated: ${audit.generated_at}`,
    "",
    `- old_source_proc_count: ${audit.old_source_proc_count}`,
    `- refined_source_proc_count: ${audit.refined_source_proc_count}`,
    `- new_candidate_source_proc_count: ${audit.new_candidate_source_proc_count}`,
    `- santong_refined_source_proc_count: ${audit.santong_refined_source_proc_count}`,
    `- sifen_refined_source_proc_count: ${audit.sifen_refined_source_proc_count}`,
    `- possible_heading_body_split_count: ${audit.possible_heading_body_split_count}`,
    `- possible_one_to_many_count: ${audit.possible_one_to_many_count}`,
    `- possible_many_to_one_count: ${audit.possible_many_to_one_count}`,
    `- aligned_high_confidence_count: ${audit.aligned_high_confidence_count}`,
    `- aligned_medium_confidence_count: ${audit.aligned_medium_confidence_count}`,
    `- needs_review_count: ${audit.needs_review_count}`,
    `- unmatched_count: ${audit.unmatched_count}`,
    `- wrong_system_candidate_count: ${audit.wrong_system_candidate_count}`,
    `- generic_term_only_candidate_count: ${audit.generic_term_only_candidate_count}`,
    `- cullen_anchors_with_new_high_or_medium_candidates: ${audit.cullen_anchors_with_new_high_or_medium_candidates.length}`,
    `- cullen_anchors_still_without_source_candidates: ${audit.cullen_anchors_still_without_source_candidates.length}`,
    "",
    `- anchors_with_new_high_or_medium_candidates: ${audit.cullen_anchors_with_new_high_or_medium_candidates.join(", ") || "none"}`,
    `- anchors_still_without_source_candidates: ${audit.cullen_anchors_still_without_source_candidates.join(", ") || "none"}`,
    "",
    "## Possible One-to-Many",
    "",
  ];

  if (!audit.possible_one_to_many_alignments.length) {
    lines.push("- none", "");
  } else {
    for (const item of audit.possible_one_to_many_alignments) {
      lines.push(`- ${item.source_proc_id}: ${item.candidate_cullen_proc_ids.join(", ")}`);
    }
    lines.push("");
  }

  lines.push("## Possible Many-to-One", "");
  if (!audit.possible_many_to_one_alignments.length) {
    lines.push("- none", "");
  } else {
    for (const item of audit.possible_many_to_one_alignments) {
      lines.push(`- ${item.cullen_proc_id}: ${item.source_proc_ids.join(", ")}`);
    }
    lines.push("");
  }

  return `${lines.join("\n")}\n`;
}

async function writeMarkdown(relativePath, content) {
  const target = resolveRepoPath(relativePath);
  await fs.mkdir(path.dirname(target), { recursive: true });
  await fs.writeFile(target, content, "utf8");
}

export async function writeSourceAlignmentOutputs({
  oldInventoryPayload,
  oldAlignmentPayload,
  oldAuditPayload,
  refinedInventoryPayload,
  refinedAlignmentPayload,
  refinedAuditPayload,
  segmentationAuditPayload,
}) {
  await writeJson(SOURCE_PROCEDURE_INVENTORY_JSON, oldInventoryPayload);
  await writeJson(SOURCE_CULLEN_ALIGNMENT_CANDIDATES_JSON, oldAlignmentPayload);
  await writeJson(SOURCE_CULLEN_ALIGNMENT_AUDIT_JSON, oldAuditPayload);

  await writeJson(SOURCE_PROCEDURE_INVENTORY_REFINED_JSON, refinedInventoryPayload);
  await writeJson(SOURCE_CULLEN_ALIGNMENT_CANDIDATES_REFINED_JSON, refinedAlignmentPayload);
  await writeJson(SOURCE_CULLEN_ALIGNMENT_AUDIT_REFINED_JSON, refinedAuditPayload);
  await writeJson(SOURCE_PROCEDURE_SEGMENTATION_AUDIT_JSON, segmentationAuditPayload);

  await writeMarkdown(SOURCE_PROCEDURE_INVENTORY_MD, renderInventoryMarkdown("Source Procedure Inventory", oldInventoryPayload, false));
  await writeMarkdown(SOURCE_CULLEN_ALIGNMENT_REVIEW_PACKET_MD, renderReviewPacketMarkdown("Source-Cullen Alignment Review Packet", oldAlignmentPayload));
  await writeMarkdown(SOURCE_CULLEN_ALIGNMENT_AUDIT_MD, renderAlignmentAuditMarkdown(oldAuditPayload));

  await writeMarkdown(SOURCE_PROCEDURE_INVENTORY_REFINED_MD, renderInventoryMarkdown("Refined Source Procedure Inventory", refinedInventoryPayload, true));
  await writeMarkdown(SOURCE_CULLEN_ALIGNMENT_REVIEW_PACKET_REFINED_MD, renderReviewPacketMarkdown("Refined Source-Cullen Alignment Review Packet", refinedAlignmentPayload));
  await writeMarkdown(SOURCE_CULLEN_ALIGNMENT_AUDIT_REFINED_MD, renderAlignmentAuditMarkdown(refinedAuditPayload));
  await writeMarkdown(SOURCE_PROCEDURE_SEGMENTATION_AUDIT_MD, renderSegmentationAuditMarkdown(segmentationAuditPayload));
}

export function buildSourceCullenAlignmentArtifacts(sourceSpansPayload, procedurePayload, anchorPayload) {
  const oldInventoryPayload = buildBaselineInventory(sourceSpansPayload, procedurePayload);
  const oldAlignmentPayload = buildAlignmentPayload(oldInventoryPayload, anchorPayload);
  const refinedInventoryEnvelope = buildRefinedInventory(sourceSpansPayload, procedurePayload);
  const refinedInventoryPayload = {
    generated_at: refinedInventoryEnvelope.generated_at,
    items: refinedInventoryEnvelope.items,
  };
  const refinedAlignmentPayload = buildAlignmentPayload(refinedInventoryPayload, anchorPayload);
  const segmentationAuditPayload = buildSegmentationAudit(oldInventoryPayload, refinedInventoryPayload);
  const refinedAuditPayload = buildAlignmentAudit({
    oldInventoryPayload,
    refinedInventoryPayload,
    refinedAlignmentPayload,
    anchorPayload,
  });
  const oldAuditPayload = {
    ...refinedAuditPayload,
    source_proc_count: oldInventoryPayload.items.length,
    santong_source_proc_count: oldInventoryPayload.items.filter((item) => item.system === "santong").length,
    sifen_source_proc_count: oldInventoryPayload.items.filter((item) => item.system === "sifen").length,
    aligned_high_confidence_count: oldAlignmentPayload.items.filter((item) => item.alignment_status === "aligned_high_confidence").length,
    aligned_medium_confidence_count: oldAlignmentPayload.items.filter((item) => item.alignment_status === "aligned_medium_confidence").length,
    needs_review_count: oldAlignmentPayload.items.filter((item) => item.alignment_status === "needs_review").length,
    unmatched_source_proc_count: oldAlignmentPayload.items.filter((item) => item.alignment_status === "unmatched").length,
    cullen_anchors_with_new_source_candidates: buildAnchorCandidateMaps(oldAlignmentPayload, anchorPayload).anchorsWithNewCandidates,
    cullen_anchors_still_without_source_span: buildAnchorCandidateMaps(oldAlignmentPayload, anchorPayload).anchorsStillWithoutCandidates,
  };

  return {
    oldInventoryPayload,
    oldAlignmentPayload,
    oldAuditPayload,
    refinedInventoryPayload,
    refinedAlignmentPayload,
    refinedAuditPayload,
    segmentationAuditPayload,
  };
}
