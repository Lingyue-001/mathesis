import { formatBilingualLabel } from "./formatters/text.js";

export const FIELD_LABELS = {
  name_sa: "Entry Name (Sanskrit)",
  transliteration: "Entry Name (Transliteration)",
  name_zh: "Entry Name (Chinese)",
  name_en: "Entry Name (English)",
  meaning_sa: "Meaning (Sanskrit)",
  meaning_tr: "Meaning (Transliteration)",
  meaning_zh: "Meaning (Chinese)",
  meaning_en: "Meaning (English)",
  symbolic_meaning_en: "Symbolic Meaning",
  explanation: "Explanation",
  note: "Explanation",
  value: "Number",
  related_concepts: "Related Concept",
  traditional_term_en: "Related Concept (English)",
  traditional_term_zh: "Related Concept (Chinese)",
  traditional_term_pinyin: "Related Concept (Pinyin)",
  system_tags: "System Tag",
  system: "System",
  original_text_en: "Primary Source (English Translation)",
  original_text_zh: "Primary Source (Chinese)",
  original_text_sa: "Primary Source (Sanskrit)",
  original_text_tr: "Primary Source (Transliteration)",
  cullen_quote_en: "Secondary Source - Cullen (Quote)",
  cullen_source: "Secondary Source - Cullen (Reference)",
  petrocchi_quote_en: "Secondary Source - Petrocchi (Quote)",
  petrocchi_source: "Secondary Source - Petrocchi (Reference)",
  source: "Primary Source (Reference)"
};

export const FIELD_ORDER = [
  "name_sa", "transliteration", "name_zh", "name_en",
  "meaning_sa", "meaning_tr", "meaning_zh", "meaning_en", "symbolic_meaning_en",
  "value", "note", "explanation",
  "related_concepts", "traditional_term_en", "traditional_term_zh", "traditional_term_pinyin",
  "system_tags", "system",
  "original_text_zh", "original_text_en", "original_text_sa", "original_text_tr", "source",
  "cullen_quote_en", "cullen_source", "petrocchi_quote_en", "petrocchi_source"
];

export const HIDDEN_FIELDS = new Set([
  "name", "name_zh_simple", "meaning_zh_simple", "nodes",
  "system_tags_zh", "system_tags_zh_simple",
  "style", "visualisation", "relationships", "id", "cardURL", "label"
]);

export function collectNodeDisplayRows(properties, options = {}) {
  const {
    fieldOrder = FIELD_ORDER,
    hiddenFields = HIDDEN_FIELDS,
    fieldLabels = FIELD_LABELS,
    skipNumberValue = false,
    excludeKeys = new Set(),
    valueFilter = null
  } = options;

  const p = properties || {};
  const rows = [];
  for (const key of fieldOrder) {
    if (hiddenFields.has(key)) continue;
    if (excludeKeys.has(key)) continue;
    if (skipNumberValue && key === "value") continue;
    const value = p[key];
    if (value === undefined || value === null || String(value).trim() === "") continue;
    if (typeof valueFilter === "function" && !valueFilter({ key, value })) continue;

    const label = fieldLabels[key] || key;
    const isReference = label.includes("(Reference)");
    const isPrimaryText = key.startsWith("original_text");
    rows.push({ key, label, value: String(value), isReference, isPrimaryText });
  }
  return rows;
}

export function buildUnifiedEntryName(properties) {
  const p = properties || {};
  const sa = String(p.name_sa || "").trim();
  const tr = String(p.transliteration || "").trim();
  const zh = String(p.name_zh || "").trim();
  const en = String(p.name_en || "").trim();
  const left = [sa, tr].filter(Boolean).join(" ");
  const right = formatBilingualLabel(zh, en);
  if (left && right) return `${left} / ${right}`;
  if (left) return left;
  if (right) return right;
  return String(p.name || "Unnamed Node");
}
