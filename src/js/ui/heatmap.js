const DEFAULT_FAMILIES = {
  operation_skeleton: { label: "Operation skeleton", color: "#8ac8dd", max: 0.24 },
  quantity_flow: { label: "Quantity flow", color: "#f2c76b", max: 0.2 },
  parameter_role: { label: "Parameter role", color: "#f0a6ca", max: 0.18 },
  target_output_class: { label: "Target/output class", color: "#b7d98b", max: 0.18 },
  surface_wording: { label: "Surface wording", color: "#aebde8", max: 0.08 },
  term_overlap: { label: "Term overlap", color: "#8fd8c6", max: 0.12 },
  operation_sequence: { label: "Operation order", color: "#8ac8dd", max: 0.14 },
  motif: { label: "Motif", color: "#ee8f7d", max: 0.26 },
  quantity_channel: { label: "Quantity channel", color: "#f2c76b", max: 0.18 },
  target_class: { label: "Target class", color: "#b7d98b", max: 0.18 },
  constant: { label: "Constant", color: "#f0a6ca", max: 0.1 },
  term: { label: "Term", color: "#8fd8c6", max: 0.12 },
  named_output: { label: "Named output", color: "#bca7ed", max: 0.1 },
  surface_pattern: { label: "Surface pattern", color: "#aebde8", max: 0.12 },
  alignment_shared: { label: "Shared / aligned", color: "#8fd7a3", max: 1 },
  alignment_similar: { label: "Same kind, different value", color: "#86c5ef", max: 1 },
  alignment_a_only: { label: "A only", color: "#f3b26f", max: 1 },
  alignment_b_only: { label: "B only", color: "#c7a6ee", max: 1 },
  alignment_inactive: { label: "Not compared", color: "#d2d6dc", max: 1 },
};

const STRUCTURAL_MARKERS = [
  "不滿為",
  "其餘為",
  "名之曰",
  "除去之",
  "乘之",
  "除之",
  "得一",
  "術曰",
  "名為",
  "謂之",
  "命之",
  "以上",
  "推",
  "置",
  "加",
  "減",
  "去",
  "以",
  "滿",
  "即",
  "也",
  "求",
];

export function clamp(value, min = 0, max = 1) {
  return Math.min(max, Math.max(min, Number(value) || 0));
}

export function heatFamilyMeta(family) {
  return DEFAULT_FAMILIES[family] ?? { label: family, color: "#7c6f62", max: 0.12 };
}

export function heatRatio(value, family = "") {
  const meta = heatFamilyMeta(family);
  return clamp((Number(value) || 0) / (meta.max || 1));
}

export function heatStyle(value, family = "") {
  const meta = heatFamilyMeta(family);
  const ratio = family ? heatRatio(value, family) : clamp(value);
  const alpha = 0.1 + ratio * 0.42;
  return `--heat-color:${meta.color};--heat-rgb:${hexToRgb(meta.color)};--heat-alpha:${alpha.toFixed(3)};--heat-scale:${ratio.toFixed(3)};`;
}

export function heatCell({ value, family, label, title, className = "" }) {
  const meta = heatFamilyMeta(family);
  const displayLabel = label ?? meta.label;
  return `
    <span
      class="heat-cell ${className}"
      style="${heatStyle(value, family)}"
      title="${escapeHtml(title ?? `${displayLabel}: ${value}`)}"
      aria-label="${escapeHtml(title ?? `${displayLabel}: ${value}`)}"
    >
      ${escapeHtml(displayLabel)}
    </span>
  `;
}

export function heatStrip(evidence) {
  if (!evidence?.length) return "";
  return `
    <div class="heat-strip" aria-label="Comparison evidence heatmap">
      ${evidence.map((item) => heatCell({
        value: item.weight,
        family: item.family,
        label: item.family.replace(/_/g, " "),
        title: `${heatFamilyMeta(item.family).label}: ${item.values.join(", ")}; contribution ${item.weight}`,
      })).join("")}
    </div>
  `;
}

export function highlightedText(text, spans) {
  const source = String(text ?? "");
  const normalizedSpans = normalizeSpans(source, spans);
  if (!normalizedSpans.length) return escapeHtml(source);

  return renderNestedText(source, 0, source.length, normalizedSpans);
}

export function spansFromMatches(text, matches, options = {}) {
  const source = String(text ?? "");
  const spans = [];
  for (const match of matches ?? []) {
    const matched = match.matched_text;
    if (!matched) continue;
    const base = findSpanInSource(source, matched, match.match_index ?? 0);
    if (!base) continue;
    const segment = source.slice(base.start, base.end);

    for (const marker of STRUCTURAL_MARKERS) {
      for (const markerSpan of findAllSpans(segment, marker)) {
        spans.push({
          start: base.start + markerSpan.start,
          end: base.start + markerSpan.end,
          family: options.markerFamily ?? "surface_pattern",
          value: options.markerValue ?? 0.42,
          priority: 1,
          title: `${match.op ?? match.family} marker: ${marker}`,
        });
      }
    }

    for (const [role, value] of Object.entries(match.role_bindings ?? {})) {
      if (!value) continue;
      const roleFamily = roleSpanFamily(role, value);
      for (const roleSpan of findAllSpans(segment, value)) {
        spans.push({
          start: base.start + roleSpan.start,
          end: base.start + roleSpan.end,
          family: roleFamily,
          value: options.value ?? roleSpanValue(roleFamily),
          priority: 3,
          title: `${role}: ${value}`,
        });
      }
    }

    if (!Object.keys(match.role_bindings ?? {}).length) {
      spans.push({
        start: base.start,
        end: base.end,
        family: options.family ?? "surface_pattern",
        value: options.value ?? 0.5,
        priority: 0,
        title: `${match.op ?? match.family}: ${matched}`,
      });
    }
  }
  return spans;
}

export function spansFromTerms(text, terms, options = {}) {
  const source = String(text ?? "");
  const spans = [];
  for (const term of terms ?? []) {
    if (!term || term.length < 2) continue;
    let start = source.indexOf(term);
    while (start !== -1) {
      spans.push({
        start,
        end: start + term.length,
        family: options.family ?? "term",
        value: options.value ?? 0.65,
        priority: options.priority ?? 4,
        title: `${options.label ?? "shared term"}: ${term}`,
      });
      start = source.indexOf(term, start + term.length);
    }
  }
  return spans;
}

function normalizeSpans(source, spans) {
  return (spans ?? [])
    .filter((span) => Number.isFinite(span.start) && Number.isFinite(span.end))
    .map((span) => ({
      ...span,
      start: clamp(span.start, 0, source.length),
      end: clamp(span.end, 0, source.length),
    }))
    .filter((span) => span.end > span.start)
    .sort((a, b) => a.start - b.start || (b.end - b.start) - (a.end - a.start));
}

function resolveSpans(source, spans) {
  const normalized = normalizeSpans(source, spans)
    .sort((a, b) =>
      (b.priority ?? 0) - (a.priority ?? 0)
      || (b.end - b.start) - (a.end - a.start)
      || a.start - b.start
    );
  const accepted = [];
  const occupied = Array(source.length).fill(false);

  for (const span of normalized) {
    let overlaps = false;
    for (let i = span.start; i < span.end; i += 1) {
      if (occupied[i]) {
        overlaps = true;
        break;
      }
    }
    if (overlaps) continue;
    accepted.push(span);
    for (let i = span.start; i < span.end; i += 1) {
      occupied[i] = true;
    }
  }

  return accepted.sort((a, b) => a.start - b.start || a.end - b.end);
}

function renderNestedText(source, start, end, spans) {
  const contained = (spans ?? [])
    .filter((span) => span.start >= start && span.end <= end)
    .sort((a, b) => a.start - b.start || (b.end - b.start) - (a.end - a.start));
  const outerSpans = contained
    .filter((span) => !contained.some((other) => other !== span && containsSpan(other, span)))
    .sort((a, b) => a.start - b.start || (b.end - b.start) - (a.end - a.start));

  let cursor = start;
  const output = [];
  for (const span of outerSpans) {
    if (span.start < cursor) continue;
    output.push(escapeHtml(source.slice(cursor, span.start)));
    output.push(renderSpanMark(source, span, contained.filter((child) => child !== span && containsSpan(span, child))));
    cursor = span.end;
  }
  output.push(escapeHtml(source.slice(cursor, end)));
  return output.join("");
}

function renderSpanMark(source, span, childSpans) {
  const label = span.label ? `<span class="heat-text-label">${escapeHtml(span.label)}</span>` : "";
  return `
    <mark
      class="heat-text-mark"
      style="${heatStyle(span.value ?? 0.7, span.family)}"
      title="${escapeHtml(span.title ?? span.family ?? "matched span")}"
    >${label}${renderNestedText(source, span.start, span.end, childSpans)}</mark>
  `;
}

function containsSpan(outer, inner) {
  const outerLength = outer.end - outer.start;
  const innerLength = inner.end - inner.start;
  return outer.start <= inner.start
    && outer.end >= inner.end
    && (outer.start !== inner.start || outer.end !== inner.end || outerLength > innerLength);
}

function roleSpanFamily(role, value) {
  if (role === "output") return "named_output";
  if (role === "target") return "target_class";
  if (isNumericPhrase(value)) return "constant";
  return "term";
}

function roleSpanValue(family) {
  if (family === "constant") return 0.82;
  if (family === "named_output") return 0.82;
  if (family === "target_class") return 0.72;
  return 0.68;
}

function isNumericPhrase(value) {
  return /[〇零一二三四五六七八九十百千萬万兩两半\d]/u.test(String(value ?? ""));
}

function findAllSpans(source, needle) {
  const normalizedNeedle = String(needle ?? "");
  if (!normalizedNeedle) return [];
  const spans = [];
  let start = source.indexOf(normalizedNeedle);
  while (start !== -1) {
    spans.push({ start, end: start + normalizedNeedle.length });
    start = source.indexOf(normalizedNeedle, start + normalizedNeedle.length);
  }
  return spans;
}

function findSpanInSource(source, needle, fallbackStart = 0) {
  const direct = source.indexOf(needle);
  if (direct !== -1) return { start: direct, end: direct + needle.length };

  const compact = [];
  const map = [];
  for (let i = 0; i < source.length; i += 1) {
    if (/\s/u.test(source[i])) continue;
    compact.push(source[i]);
    map.push(i);
  }

  const compactSource = compact.join("");
  const compactNeedle = String(needle).replace(/\s+/gu, "");
  const compactStart = compactSource.indexOf(compactNeedle, Math.max(0, fallbackStart - 6));
  if (compactStart === -1) return null;

  return {
    start: map[compactStart],
    end: map[compactStart + compactNeedle.length - 1] + 1,
  };
}

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function hexToRgb(hex) {
  const value = String(hex ?? "").replace("#", "");
  if (!/^[0-9a-f]{6}$/iu.test(value)) return "124,111,98";
  const r = parseInt(value.slice(0, 2), 16);
  const g = parseInt(value.slice(2, 4), 16);
  const b = parseInt(value.slice(4, 6), 16);
  return `${r},${g},${b}`;
}
