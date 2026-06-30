import fs from "node:fs/promises";
import path from "node:path";
import { normalizeWhitespace, readJson, resolveRepoPath, writeJson } from "./cullen-oracle-common.mjs";

// Corpus profiling only: this script surfaces exploratory patterns and chunk
// quality signals from the current Sifen Cullen chunks. It is not a final
// extractor and does not write gold/canonical annotations.

const INPUT_PATH = "tmp/procedure-ir/cullen-chunks.json";
const OUTPUT_JSON_PATH = "tmp/procedure-ir/sifen-corpus-profile.json";
const OUTPUT_MD_PATH = "tmp/procedure-ir/sifen-corpus-profile.md";

const TOP_N = 50;
const LONG_SHORT_N = 20;
const EXAMPLE_LIMIT = 10;
const CHINESE_RE = /[\u3400-\u9fff]/u;
const CHINESE_GLOBAL_RE = /[\u3400-\u9fff]/gu;
const CHINESE_NUMBER_RE = /[零〇一二三四五六七八九十百千萬万億亿兩]+/gu;
const ASCII_NUMBER_RE = /\b\d[\d,]*(?:\.\d+)?(?:\s*(?:and\s+)?(?:a\s+)?(?:half|quarter|third|fourth|¾|½|⅓|⅔|¼))?\b/giu;
const EN_STOPWORDS = new Set([
  "the", "and", "for", "that", "this", "with", "from", "are", "was", "were",
  "has", "have", "had", "into", "not", "but", "you", "your", "one", "two",
  "its", "his", "her", "their", "there", "then", "than", "when", "where",
  "which", "what", "does", "did", "each", "will", "can", "may", "all",
  "out", "set", "see", "also", "these", "those", "they", "them", "been",
  "being", "such", "more", "less", "over", "under", "between", "within",
  "section", "proc"
]);

const TERM_ENDINGS = [
  "Factor",
  "Remainder",
  "Number",
  "Months",
  "Days",
  "Circuits",
  "Coincidence",
  "Origin",
  "Rule",
  "Obscuration"
];

const OPERATION_PATTERNS = [
  ["Set out", /\bset out\b/giu],
  ["Cast out", /\bcast out\b/giu],
  ["Multiply", /\bmultiply(?:ing|ies|ied)?\b/giu],
  ["Divide", /\bdivide(?:d|s|ing)?\b/giu],
  ["Add", /\badd(?:ed|s|ing)?\b/giu],
  ["Subtract", /\bsubtract(?:ed|s|ing)?\b/giu],
  ["Count", /\bcount(?:ed|s|ing)?\b/giu],
  ["Obtain", /\bobtain(?:ed|s|ing)?\b/giu],
  ["Remainder", /\bremainder\b/giu],
  ["What does not fill", /\bwhat does not fill\b/giu],
  ["Count one for each", /\bcount one for each\b/giu],
  ["Call this", /\bcall this\b/giu],
  ["called", /\bcalled\b/giu]
];

const CROSS_REFERENCE_PATTERNS = [
  ["Proc. 3.x", /\bProc\.\s*3\.\d+\b/giu],
  ["section §x", /\bsection\s+§\s*\d+\b/giu],
  ["see Proc.", /\bsee\s+Proc\./giu],
  ["see section", /\bsee\s+section\b/giu]
];

const PATTERN_DEFINITIONS = [
  {
    pattern_name: "zh_term_number ↔ en_term_number",
    zh: /[\u3400-\u9fff]{1,8}[零〇一二三四五六七八九十百千萬万億亿兩]+/u,
    en: /[A-Z][A-Za-z -]{1,40}:\s*\d/u
  },
  {
    pattern_name: "謂之X ↔ called Y",
    zh: /謂之[\u3400-\u9fff]{1,8}/u,
    en: /\bcalled\s+[A-Za-z][A-Za-z -]{1,40}/iu
  },
  {
    pattern_name: "置X ↔ Set out X",
    zh: /置[\u3400-\u9fff]{1,12}/u,
    en: /\bset out\b/iu
  },
  {
    pattern_name: "以X乘之 ↔ Multiply by X",
    zh: /以[\u3400-\u9fff\d零〇一二三四五六七八九十百千萬万億亿兩]{1,16}乘之/u,
    en: /\bmultiply\b/iu
  },
  {
    pattern_name: "滿X得一 / 如X得一 ↔ Count one for each X filled",
    zh: /(?:滿|如)[\u3400-\u9fff\d零〇一二三四五六七八九十百千萬万億亿兩]{1,16}得一/u,
    en: /\b(?:count one for each|for each|filled)\b/iu
  },
  {
    pattern_name: "不滿為X ↔ what does not fill ... is X",
    zh: /不滿為[\u3400-\u9fff]{1,8}/u,
    en: /\bwhat does not fill\b/iu
  }
];

function excerpt(text, length = 160) {
  const clean = normalizeWhitespace(text || "");
  return clean.length > length ? `${clean.slice(0, length - 1)}…` : clean;
}

function countBy(items, keyFn) {
  const counts = new Map();
  for (const item of items) {
    const key = keyFn(item);
    counts.set(key, (counts.get(key) || 0) + 1);
  }
  return [...counts.entries()]
    .sort((a, b) => b[1] - a[1] || String(a[0]).localeCompare(String(b[0])))
    .map(([key, count]) => ({ key, count }));
}

function topMap(map, limit = TOP_N) {
  return [...map.entries()]
    .sort((a, b) => b[1].count - a[1].count || a[0].localeCompare(b[0]))
    .slice(0, limit)
    .map(([term, data]) => ({
      term,
      count: data.count,
      examples: [...data.examples].slice(0, 5)
    }));
}

function addCount(map, term, example = null) {
  const key = normalizeWhitespace(term);
  if (!key) return;
  if (!map.has(key)) map.set(key, { count: 0, examples: new Set() });
  const entry = map.get(key);
  entry.count += 1;
  if (example) entry.examples.add(example);
}

function chunkRef(chunk) {
  return {
    chunk_id: chunk.id,
    chunk_type: chunk.chunk_type,
    unit_id: chunk.unit_id,
    procedure_id: chunk.procedure_id,
    section_path: chunk.section_path,
    book_page_start: chunk.book_page_start,
    book_page_end: chunk.book_page_end,
    char_count: chunk.char_count
  };
}

function chunkPreview(chunk, field = "text", length = 160) {
  return {
    ...chunkRef(chunk),
    excerpt: excerpt(chunk[field] || chunk.text, length)
  };
}

function pageNumber(value) {
  const parsed = Number.parseInt(String(value ?? ""), 10);
  return Number.isFinite(parsed) ? parsed : null;
}

function charStats(chunks) {
  const values = chunks.map((chunk) => Number(chunk.char_count || 0));
  const sum = values.reduce((acc, value) => acc + value, 0);
  return {
    min: Math.min(...values),
    max: Math.max(...values),
    average: values.length ? Number((sum / values.length).toFixed(2)) : 0
  };
}

function tokenizeEnglish(text) {
  return normalizeWhitespace(text)
    .toLowerCase()
    .split(/[^a-z0-9§.]+/u)
    .filter((token) => token.length >= 2 && !EN_STOPWORDS.has(token));
}

function collectEnglishNgrams(chunks, n) {
  const map = new Map();
  for (const chunk of chunks) {
    const tokens = tokenizeEnglish(chunk.translation_en || "");
    for (let i = 0; i <= tokens.length - n; i += 1) {
      addCount(map, tokens.slice(i, i + n).join(" "), chunk.id);
    }
  }
  return topMap(map);
}

function collectChineseNgrams(chunks, n) {
  const map = new Map();
  for (const chunk of chunks) {
    const sequences = (chunk.source_text_zh || "").match(/[\u3400-\u9fff]+/gu) || [];
    for (const sequence of sequences) {
      const chars = [...sequence];
      for (let i = 0; i <= chars.length - n; i += 1) {
        addCount(map, chars.slice(i, i + n).join(""), chunk.id);
      }
    }
  }
  return topMap(map);
}

function collectChineseCharacters(chunks) {
  const map = new Map();
  for (const chunk of chunks) {
    for (const match of chunk.source_text_zh.matchAll(CHINESE_GLOBAL_RE)) {
      addCount(map, match[0], chunk.id);
    }
  }
  return topMap(map);
}

function collectChineseSuffixPhrases(chunks) {
  const map = new Map();
  const suffixes = "法數餘積月日歲分率會";
  for (const chunk of chunks) {
    const sequences = (chunk.source_text_zh || "").match(/[\u3400-\u9fff]+/gu) || [];
    for (const sequence of sequences) {
      const chars = [...sequence];
      for (let start = 0; start < chars.length; start += 1) {
        for (let len = 2; len <= 6 && start + len <= chars.length; len += 1) {
          const phrase = chars.slice(start, start + len).join("");
          if (suffixes.includes(phrase.at(-1))) addCount(map, phrase, chunk.id);
        }
      }
    }
  }
  return topMap(map, 80);
}

function collectChineseOperationSegments(chunks) {
  const map = new Map();
  const opRe = /(置|以|滿|不滿|得|減|乘|除|謂之|為)/u;
  for (const chunk of chunks) {
    const segments = (chunk.source_text_zh || "")
      .split(/[，,。；;：:．\n]+/u)
      .map((segment) => normalizeWhitespace(segment))
      .filter((segment) => segment.length >= 2 && opRe.test(segment));
    for (const segment of segments) addCount(map, segment, chunk.id);
  }
  return topMap(map, 80);
}

function collectChineseNumberCandidates(chunks) {
  const map = new Map();
  for (const chunk of chunks) {
    for (const match of (chunk.source_text_zh || "").matchAll(CHINESE_NUMBER_RE)) {
      const value = match[0];
      if (value.length >= 2) addCount(map, value, chunk.id);
    }
  }
  return topMap(map, 80);
}

function collectEnglishTermCandidates(chunks) {
  const map = new Map();
  const endingRe = new RegExp(`\\b(?:[A-Z][A-Za-z-]*\\s+){0,4}(?:${TERM_ENDINGS.join("|")})\\b`, "gu");
  for (const chunk of chunks) {
    for (const match of (chunk.translation_en || "").matchAll(endingRe)) {
      addCount(map, match[0], chunk.id);
    }
  }
  return topMap(map, 80);
}

function collectColonCandidates(chunks) {
  const map = new Map();
  const colonRe = /\b[A-Z][A-Za-z \[\]-]{1,50}:\s*[-\d,./ +¼½¾]+/gu;
  for (const chunk of chunks) {
    for (const match of (chunk.translation_en || "").matchAll(colonRe)) {
      addCount(map, match[0], chunk.id);
    }
  }
  return topMap(map, 80);
}

function countRegexMatches(text, regex) {
  return [...String(text || "").matchAll(regex)].length;
}

function collectOperationCounts(chunks) {
  return OPERATION_PATTERNS.map(([operation, regex]) => {
    const examples = [];
    let count = 0;
    for (const chunk of chunks) {
      const matches = countRegexMatches(chunk.translation_en || "", regex);
      if (matches) {
        count += matches;
        if (examples.length < 5) examples.push(chunk.id);
      }
    }
    return { operation, count, examples };
  }).sort((a, b) => b.count - a.count || a.operation.localeCompare(b.operation));
}

function collectCrossReferences(chunks) {
  return CROSS_REFERENCE_PATTERNS.map(([pattern, regex]) => {
    const examples = [];
    let count = 0;
    for (const chunk of chunks) {
      const haystack = `${chunk.translation_en || ""}\n${chunk.commentary_en || ""}`;
      const matches = countRegexMatches(haystack, regex);
      if (matches) {
        count += matches;
        if (examples.length < 5) examples.push(chunk.id);
      }
    }
    return { pattern, count, examples };
  }).sort((a, b) => b.count - a.count || a.pattern.localeCompare(b.pattern));
}

function parseChineseNumeral(raw) {
  const digits = {
    零: 0,
    〇: 0,
    一: 1,
    二: 2,
    兩: 2,
    三: 3,
    四: 4,
    五: 5,
    六: 6,
    七: 7,
    八: 8,
    九: 9
  };
  const smallUnits = { 十: 10, 百: 100, 千: 1000 };
  const largeUnits = { 萬: 10000, 万: 10000, 億: 100000000, 亿: 100000000 };
  let total = 0;
  let section = 0;
  let number = 0;
  for (const char of raw) {
    if (char in digits) {
      number = digits[char];
    } else if (char in smallUnits) {
      section += (number || 1) * smallUnits[char];
      number = 0;
    } else if (char in largeUnits) {
      section += number;
      total += (section || 1) * largeUnits[char];
      section = 0;
      number = 0;
    } else {
      return null;
    }
  }
  return total + section + number;
}

function parseAsciiNumber(raw) {
  const cleaned = String(raw).replace(/,/gu, "");
  const number = Number.parseFloat(cleaned);
  return Number.isFinite(number) ? number : null;
}

function phraseAround(text, index, length, radius = 12) {
  const start = Math.max(0, index - radius);
  const end = Math.min(text.length, index + length + radius);
  return normalizeWhitespace(text.slice(start, end));
}

function collectBilingualNumberCandidates(chunks) {
  const candidates = [];
  for (const chunk of chunks) {
    const zhText = chunk.source_text_zh || "";
    const enText = chunk.translation_en || "";
    const zhMatches = [...zhText.matchAll(CHINESE_NUMBER_RE)]
      .map((match) => ({
        raw: match[0],
        value: parseChineseNumeral(match[0]),
        phrase: phraseAround(zhText, match.index, match[0].length)
      }))
      .filter((match) => match.raw.length >= 1 && match.value !== null);
    const enMatches = [...enText.matchAll(ASCII_NUMBER_RE)]
      .map((match) => ({
        raw: match[0],
        value: parseAsciiNumber(match[0]),
        phrase: phraseAround(enText, match.index, match[0].length)
      }))
      .filter((match) => match.value !== null);
    for (const zh of zhMatches) {
      const en = enMatches.find((candidate) => candidate.value === zh.value);
      if (!en) continue;
      candidates.push({
        zh_phrase: zh.phrase,
        zh_value_raw: zh.raw,
        en_phrase: en.phrase,
        en_value_raw: en.raw,
        normalized_value: zh.value,
        chunk_id: chunk.id,
        unit_id: chunk.unit_id,
        book_page_start: chunk.book_page_start,
        book_page_end: chunk.book_page_end
      });
    }
  }
  return candidates;
}

function firstMatch(text, regex) {
  const match = String(text || "").match(regex);
  return match ? match[0] : "";
}

function collectPatternSeeds(chunks) {
  return PATTERN_DEFINITIONS.map((definition) => {
    const matches = [];
    for (const chunk of chunks) {
      const zh = firstMatch(chunk.source_text_zh, definition.zh);
      const en = firstMatch(chunk.translation_en, definition.en);
      if (!zh || !en) continue;
      matches.push({
        chunk_id: chunk.id,
        unit_id: chunk.unit_id,
        book_page_start: chunk.book_page_start,
        book_page_end: chunk.book_page_end,
        zh_excerpt: excerpt(chunk.source_text_zh, 180),
        en_excerpt: excerpt(chunk.translation_en, 180),
        zh_match: zh,
        en_match: en
      });
    }
    return {
      pattern_name: definition.pattern_name,
      count: matches.length,
      example_chunk_ids: matches.slice(0, 10).map((match) => match.chunk_id),
      examples: matches.slice(0, 10),
      confidence: "exploratory"
    };
  });
}

function isSuspiciousFootnoteOrPageIntro(chunk) {
  const text = normalizeWhitespace(chunk.text || "");
  return /(?:–\s*\d+\s*–|-\s*\d+\s*-)/u.test(text)
    || /^\d+$/u.test(text)
    || text.length <= 12
    || /^(?:Table|Figure)\s+\d/u.test(text);
}

function collectSuspiciousChunks(chunks, translationUnits, sectionIntros) {
  const missingSource = translationUnits
    .filter((chunk) => !normalizeWhitespace(chunk.source_text_zh || ""))
    .map((chunk) => ({ reason: "translation_unit_missing_source_text_zh", ...chunkPreview(chunk) }));
  const missingTranslation = translationUnits
    .filter((chunk) => !normalizeWhitespace(chunk.translation_en || ""))
    .map((chunk) => ({ reason: "translation_unit_missing_translation_en", ...chunkPreview(chunk) }));
  const introHasChinese = sectionIntros
    .filter((chunk) => CHINESE_RE.test(chunk.text || ""))
    .map((chunk) => ({ reason: "section_intro_contains_chinese", ...chunkPreview(chunk) }));
  const footnoteLikeIntro = sectionIntros
    .filter(isSuspiciousFootnoteOrPageIntro)
    .map((chunk) => ({ reason: "section_intro_footnote_page_or_label_like", ...chunkPreview(chunk) }));
  const extremelyLong = [...chunks]
    .sort((a, b) => (b.char_count || 0) - (a.char_count || 0))
    .slice(0, 5)
    .map((chunk) => ({ reason: "very_long_chunk_review_boundary", ...chunkPreview(chunk) }));
  return {
    top_10_for_human_review: [
      ...missingSource.slice(0, 5),
      ...footnoteLikeIntro.slice(0, 3),
      ...introHasChinese.slice(0, 2)
    ].slice(0, 10),
    by_category: {
      translation_unit_missing_source_text_zh: missingSource,
      translation_unit_missing_translation_en: missingTranslation,
      section_intro_contains_chinese: introHasChinese,
      section_intro_footnote_page_or_label_like: footnoteLikeIntro,
      very_long_chunk_review_boundary: extremelyLong
    }
  };
}

function qualityAssessment(profile) {
  const missingSource = profile.field_integrity.translation_unit_source_text_zh_empty.count;
  const missingTranslation = profile.field_integrity.translation_unit_translation_en_empty.count;
  const unitCount = profile.basic_overview.chunk_counts_by_type.find((item) => item.key === "translation_unit")?.count || 0;
  const missingRate = unitCount ? missingSource / unitCount : 1;
  const strengths = [
    "chunk_type and field separation are strong enough for field-aware corpus profiling",
    "translation_unit coverage is high enough to surface repeated operation and constant patterns",
    "source_text_zh and translation_en pairing is good enough for exploratory bilingual number candidates"
  ];
  const limitations = [
    "statistics are limited to Cullen book pages 138-234, not the full book",
    "table-like chunks, footnotes, and a small set of missing Chinese sources still require manual review",
    "pattern seeds are exploratory and must not be treated as gold extraction rules"
  ];
  let verdict = "good_for_exploratory_profile";
  if (missingRate > 0.12 || missingTranslation > 0) verdict = "usable_but_needs_chunker_review";
  return {
    verdict,
    missing_source_text_zh_rate: Number(missingRate.toFixed(4)),
    strengths,
    limitations,
    recommended_next_steps: [
      "review the top suspicious chunks before turning pattern seeds into parser rules",
      "promote only repeated field-aligned patterns with clear source_text_zh and translation_en evidence",
      "use bilingual number candidates as pairing checks, not as final term alignments"
    ]
  };
}

function makeMarkdown(profile) {
  const lines = [];
  const counts = Object.fromEntries(profile.basic_overview.chunk_counts_by_type.map((item) => [item.key, item.count]));
  lines.push("# Sifen Corpus Profile");
  lines.push("");
  lines.push("> Exploratory corpus profiling only. This is not final extraction and does not define gold annotations.");
  lines.push("");
  lines.push("## Summary");
  lines.push("");
  lines.push("| Metric | Value |");
  lines.push("| --- | ---: |");
  lines.push(`| Body chunks | ${profile.basic_overview.total_chunks} |`);
  lines.push(`| section_intro | ${counts.section_intro || 0} |`);
  lines.push(`| translation_unit | ${counts.translation_unit || 0} |`);
  lines.push(`| translation_unit missing source_text_zh | ${profile.field_integrity.translation_unit_source_text_zh_empty.count} |`);
  lines.push(`| translation_unit missing translation_en | ${profile.field_integrity.translation_unit_translation_en_empty.count} |`);
  lines.push(`| translation_unit with commentary_en | ${profile.field_integrity.translation_unit_commentary_en_nonempty.count} |`);
  lines.push(`| section_intro containing Chinese | ${profile.field_integrity.section_intro_contains_chinese.count} |`);
  lines.push(`| Book page range | ${profile.basic_overview.book_page_range.min}-${profile.basic_overview.book_page_range.max} |`);
  lines.push(`| Average char_count | ${profile.basic_overview.char_count.average} |`);
  lines.push(`| Quality verdict | ${profile.quality_assessment.verdict} |`);
  lines.push("");
  lines.push("## Result Yield");
  lines.push("");
  for (const strength of profile.quality_assessment.strengths) lines.push(`- ${strength}`);
  lines.push("");
  lines.push("## Quality Limits");
  lines.push("");
  for (const limitation of profile.quality_assessment.limitations) lines.push(`- ${limitation}`);
  lines.push("");
  lines.push("## Section Distribution");
  lines.push("");
  lines.push("| Section path | Chunks |");
  lines.push("| --- | ---: |");
  for (const item of profile.basic_overview.chunk_counts_by_section_path.slice(0, 30)) {
    lines.push(`| ${item.key} | ${item.count} |`);
  }
  lines.push("");
  lines.push("## Operation Verb Candidates");
  lines.push("");
  lines.push("| English operation cue | Count | Example chunks |");
  lines.push("| --- | ---: | --- |");
  for (const item of profile.english_stats.operation_verb_candidates) {
    lines.push(`| ${item.operation} | ${item.count} | ${item.examples.join(", ")} |`);
  }
  lines.push("");
  lines.push("## Top Chinese Operation Segments");
  lines.push("");
  lines.push("| Segment | Count | Example chunks |");
  lines.push("| --- | ---: | --- |");
  for (const item of profile.chinese_stats.operation_segments.slice(0, 30)) {
    lines.push(`| ${item.term} | ${item.count} | ${item.examples.join(", ")} |`);
  }
  lines.push("");
  lines.push("## English Term Candidates");
  lines.push("");
  lines.push("| Term | Count | Example chunks |");
  lines.push("| --- | ---: | --- |");
  for (const item of profile.english_stats.term_candidates.slice(0, 30)) {
    lines.push(`| ${item.term} | ${item.count} | ${item.examples.join(", ")} |`);
  }
  lines.push("");
  lines.push("## Bilingual Number Candidates");
  lines.push("");
  lines.push("| chunk | unit | book page | Chinese | English | Value |");
  lines.push("| --- | --- | --- | --- | --- | ---: |");
  for (const item of profile.bilingual_number_candidates.slice(0, 50)) {
    lines.push(`| ${item.chunk_id} | ${item.unit_id || ""} | ${item.book_page_start}-${item.book_page_end} | ${item.zh_phrase} | ${item.en_phrase} | ${item.normalized_value} |`);
  }
  lines.push("");
  lines.push("## Pattern Seeds");
  lines.push("");
  for (const seed of profile.pattern_seeds) {
    lines.push(`### ${seed.pattern_name}`);
    lines.push("");
    lines.push(`Count: ${seed.count}`);
    lines.push("");
    for (const example of seed.examples.slice(0, 5)) {
      lines.push(`- ${example.chunk_id} ${example.unit_id || ""} p.${example.book_page_start}-${example.book_page_end}: ${example.zh_match} ↔ ${example.en_match}`);
      lines.push(`  - zh: ${example.zh_excerpt}`);
      lines.push(`  - en: ${example.en_excerpt}`);
    }
    lines.push("");
  }
  lines.push("## Suspicious Chunks For Review");
  lines.push("");
  lines.push("| Reason | chunk | unit | book page | Excerpt |");
  lines.push("| --- | --- | --- | --- | --- |");
  for (const item of profile.suspicious_chunks.top_10_for_human_review) {
    lines.push(`| ${item.reason} | ${item.chunk_id} | ${item.unit_id || ""} | ${item.book_page_start}-${item.book_page_end} | ${item.excerpt} |`);
  }
  lines.push("");
  lines.push("## Longest 20 Chunks");
  lines.push("");
  lines.push("| chunk | type | unit | book page | chars | Excerpt |");
  lines.push("| --- | --- | --- | --- | ---: | --- |");
  for (const item of profile.basic_overview.longest_20_chunks) {
    lines.push(`| ${item.chunk_id} | ${item.chunk_type} | ${item.unit_id || ""} | ${item.book_page_start}-${item.book_page_end} | ${item.char_count} | ${item.excerpt} |`);
  }
  lines.push("");
  lines.push("## Shortest 20 Chunks");
  lines.push("");
  lines.push("| chunk | type | unit | book page | chars | Excerpt |");
  lines.push("| --- | --- | --- | --- | ---: | --- |");
  for (const item of profile.basic_overview.shortest_20_chunks) {
    lines.push(`| ${item.chunk_id} | ${item.chunk_type} | ${item.unit_id || ""} | ${item.book_page_start}-${item.book_page_end} | ${item.char_count} | ${item.excerpt} |`);
  }
  lines.push("");
  return `${lines.join("\n")}\n`;
}

async function writeText(relativePath, text) {
  const target = resolveRepoPath(relativePath);
  await fs.mkdir(path.dirname(target), { recursive: true });
  await fs.writeFile(target, text, "utf8");
}

async function main() {
  const input = await readJson(INPUT_PATH);
  const chunks = (input.chunks || []).filter((chunk) => chunk.chunk_role === "body");
  const translationUnits = chunks.filter((chunk) => chunk.chunk_type === "translation_unit");
  const sectionIntros = chunks.filter((chunk) => chunk.chunk_type === "section_intro");
  const pages = chunks.flatMap((chunk) => [pageNumber(chunk.book_page_start), pageNumber(chunk.book_page_end)]).filter((value) => value !== null);

  const longest = [...chunks]
    .sort((a, b) => (b.char_count || 0) - (a.char_count || 0))
    .slice(0, LONG_SHORT_N)
    .map((chunk) => chunkPreview(chunk, "text", 180));
  const shortest = [...chunks]
    .sort((a, b) => (a.char_count || 0) - (b.char_count || 0))
    .slice(0, LONG_SHORT_N)
    .map((chunk) => chunkPreview(chunk, "text", 180));

  const profile = {
    generated_at: new Date().toISOString(),
    input_path: INPUT_PATH,
    scope: {
      corpus: "Cullen Sifen chunks",
      chunk_role: "body",
      note: "Corpus profiling only; no embedding, no LLM, no gold writeback."
    },
    basic_overview: {
      total_chunks: chunks.length,
      chunk_counts_by_type: countBy(chunks, (chunk) => chunk.chunk_type || "missing"),
      chunk_counts_by_section_path: countBy(chunks, (chunk) => (chunk.section_path || []).join(" > ") || "missing"),
      procedure_id_distribution: countBy(chunks, (chunk) => chunk.procedure_id || "null"),
      unit_id_coverage: {
        translation_unit_count: translationUnits.length,
        translation_unit_with_unit_id: translationUnits.filter((chunk) => chunk.unit_id).length,
        translation_unit_missing_unit_id: translationUnits.filter((chunk) => !chunk.unit_id).length
      },
      book_page_range: {
        min: pages.length ? Math.min(...pages) : null,
        max: pages.length ? Math.max(...pages) : null,
        missing_book_page_chunks: chunks.filter((chunk) => pageNumber(chunk.book_page_start) === null || pageNumber(chunk.book_page_end) === null).map(chunkRef)
      },
      char_count: charStats(chunks),
      longest_20_chunks: longest,
      shortest_20_chunks: shortest
    },
    field_integrity: {
      translation_unit_source_text_zh_empty: {
        count: translationUnits.filter((chunk) => !normalizeWhitespace(chunk.source_text_zh || "")).length,
        items: translationUnits.filter((chunk) => !normalizeWhitespace(chunk.source_text_zh || "")).map((chunk) => chunkPreview(chunk))
      },
      translation_unit_translation_en_empty: {
        count: translationUnits.filter((chunk) => !normalizeWhitespace(chunk.translation_en || "")).length,
        items: translationUnits.filter((chunk) => !normalizeWhitespace(chunk.translation_en || "")).map((chunk) => chunkPreview(chunk))
      },
      translation_unit_commentary_en_nonempty: {
        count: translationUnits.filter((chunk) => normalizeWhitespace(chunk.commentary_en || "")).length,
        items: translationUnits.filter((chunk) => normalizeWhitespace(chunk.commentary_en || "")).map((chunk) => chunkPreview(chunk, "commentary_en"))
      },
      section_intro_contains_chinese: {
        count: sectionIntros.filter((chunk) => CHINESE_RE.test(chunk.text || "")).length,
        items: sectionIntros.filter((chunk) => CHINESE_RE.test(chunk.text || "")).map((chunk) => chunkPreview(chunk))
      },
      section_intro_footnote_or_page_garbage_candidates: {
        count: sectionIntros.filter(isSuspiciousFootnoteOrPageIntro).length,
        items: sectionIntros.filter(isSuspiciousFootnoteOrPageIntro).map((chunk) => chunkPreview(chunk))
      }
    },
    chinese_stats: {
      source: "source_text_zh on translation_unit chunks",
      frequent_characters: collectChineseCharacters(translationUnits),
      frequent_2grams: collectChineseNgrams(translationUnits, 2),
      frequent_3grams: collectChineseNgrams(translationUnits, 3),
      frequent_4grams: collectChineseNgrams(translationUnits, 4),
      suffix_phrases: collectChineseSuffixPhrases(translationUnits),
      operation_segments: collectChineseOperationSegments(translationUnits),
      number_expression_candidates: collectChineseNumberCandidates(translationUnits)
    },
    english_stats: {
      source: "translation_en on translation_unit chunks",
      frequent_unigrams: collectEnglishNgrams(translationUnits, 1),
      frequent_bigrams: collectEnglishNgrams(translationUnits, 2),
      frequent_trigrams: collectEnglishNgrams(translationUnits, 3),
      term_candidates: collectEnglishTermCandidates(translationUnits),
      colon_format_candidates: collectColonCandidates(translationUnits),
      operation_verb_candidates: collectOperationCounts(translationUnits),
      cross_references: collectCrossReferences(translationUnits)
    },
    bilingual_number_candidates: collectBilingualNumberCandidates(translationUnits),
    pattern_seeds: collectPatternSeeds(translationUnits),
    suspicious_chunks: collectSuspiciousChunks(chunks, translationUnits, sectionIntros)
  };
  profile.quality_assessment = qualityAssessment(profile);

  await writeJson(OUTPUT_JSON_PATH, profile);
  await writeText(OUTPUT_MD_PATH, makeMarkdown(profile));

  console.log(JSON.stringify({
    stage: "profile-sifen-corpus",
    input: INPUT_PATH,
    outputs: [OUTPUT_JSON_PATH, OUTPUT_MD_PATH],
    total_chunks: profile.basic_overview.total_chunks,
    chunk_counts_by_type: profile.basic_overview.chunk_counts_by_type,
    translation_unit_source_text_zh_empty: profile.field_integrity.translation_unit_source_text_zh_empty.count,
    translation_unit_translation_en_empty: profile.field_integrity.translation_unit_translation_en_empty.count,
    translation_unit_commentary_en_nonempty: profile.field_integrity.translation_unit_commentary_en_nonempty.count,
    section_intro_contains_chinese: profile.field_integrity.section_intro_contains_chinese.count,
    bilingual_number_candidates: profile.bilingual_number_candidates.length,
    quality_verdict: profile.quality_assessment.verdict,
    top_suspicious_chunks: profile.suspicious_chunks.top_10_for_human_review
  }, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
