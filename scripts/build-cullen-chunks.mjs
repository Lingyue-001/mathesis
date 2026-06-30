import {
  normalizeWhitespace,
  readJson,
  readPipelineConfig,
  writeJson,
} from "./cullen-oracle-common.mjs";

// Chapter 3 / Sifen chunk builder.
//
// This script intentionally replaces the earlier broad Cullen chunker. It reads
// the staged Chapter 3 page artifact after footnote extraction and table
// neutralization, then writes the canonical Chapter 3 chunk artifact path so
// old/new chunk outputs do not accumulate in parallel.
//
// Chunking policy:
// - 3.1.x: one English background chunk per smallest section heading.
// - 3.2.x: one source/translation group per Chinese source block plus the
//   following English block beginning with §N, through the text before the next
//   Chinese source block or section heading.
// - §N validates the grouping but is not the primary boundary. If §N and source
//   blocks do not line up, preserve the text and emit warnings.

const INPUT_PAGES_PATH = "tmp/procedure-ir/cullen-ch3-table-neutralized-pages.json";
const WARNINGS_OUTPUT_PATH = "tmp/procedure-ir/cullen-ch3-chunk-warnings.json";
const STRUCTURE_AUDIT_OUTPUT_PATH = "tmp/procedure-ir/cullen-ch3-chunk-structure-audit.json";
const TARGET_BOOK_PAGE_START = 138;
const TARGET_BOOK_PAGE_END = 234;
const TARGET_CHAPTER_ID = "3";
const TARGET_SYSTEM_ID = "sifen";
const CHUNK_SCHEMA_VERSION = "cullen_ch3_minimal_v2";
const CHUNKING_METHOD = "ch3_section_heading_and_source_translation_group";

const STRICT_HEADING_RE = /^(?<id>3\.(?:1|2)(?:\.[1-9]\d*)?)\s+(?<title>.+)$/u;
const NON_TARGET_NUMBERED_HEADING_RE = /^(?<id>[1-5]\.[1-9]\d*(?:\.[1-9]\d*)?)\s+(?<title>.+)$/u;
const PROC_RE = /^Proc\.\s*(?<id>3\.\d+)\.(?:\s*(?<title>.*))?$/u;
const SECTION_MARKER_RE = /§\s*(\d{1,3})/gu;
const SECTION_MARKER_AT_LINE_START_RE = /^§\s*\d{1,3}/u;
const TABLE_REF_RE = /\[TABLE_3_\d+\]/gu;
const FOOTNOTE_REF_RE = /\[\^\d+\]/gu;
const PAGE_ARTIFACT_RE = /^[-–]\s*\d{3,5}\s*[-–]$/u;
const TABLE_PLACEHOLDER_RE = /^\[TABLE_3_\d+\]$/u;
const QUARTER_REMAINDER_HEADER_RE = /^(?:\d{1,3}\s+)?The Han Quarter Remainder system(?:\s+\d{1,3})?$/iu;

const ISSUE_SEVERITY_BY_CODE = {
  page_artifact_line_removed_from_chunk_stream: "info",
  unexpected_source_or_section_marker_in_3_1: "info",
  proc_like_line_treated_as_body: "info",
  source_text_without_section_marker: "review",
  english_group_does_not_start_with_section_marker: "review",
  source_interrupted_by_heading: "warning",
  section_marker_before_source: "warning",
  section_marker_outside_expected_1_260_range: "warning",
  duplicate_section_markers: "warning",
  missing_section_markers_1_260: "warning",
  section_markers_not_monotonic_in_text_order: "warning",
};

function parseNumericBookPage(value) {
  const text = String(value ?? "").trim();
  if (!/^\d{1,3}$/u.test(text)) return null;
  return Number.parseInt(text, 10);
}

function isTargetBookPage(page) {
  const bookPage = parseNumericBookPage(page.book_page_number);
  return bookPage !== null
    && bookPage >= TARGET_BOOK_PAGE_START
    && bookPage <= TARGET_BOOK_PAGE_END;
}

function countMatches(text, regex) {
  return [...String(text ?? "").matchAll(regex)].length;
}

function unique(items) {
  return [...new Set(items.filter((item) => item !== null && item !== undefined && item !== ""))];
}

function mergeProcedureEntries(entries) {
  const merged = [];
  const byId = new Map();
  for (const entry of entries ?? []) {
    if (!entry?.id) continue;
    const normalizedTitle = normalizeWhitespace(entry.title ?? "");
    if (!byId.has(entry.id)) {
      const normalized = { id: entry.id, title: normalizedTitle };
      byId.set(entry.id, normalized);
      merged.push(normalized);
      continue;
    }
    const existing = byId.get(entry.id);
    if (!existing.title && normalizedTitle) existing.title = normalizedTitle;
  }
  return merged;
}

function parseHeading(line) {
  const text = line.trim();
  const match = text.match(STRICT_HEADING_RE);
  if (!match) return null;
  return {
    id: match.groups.id,
    heading: `${match.groups.id} ${normalizeWhitespace(match.groups.title)}`,
  };
}

function sectionPathFromHeadingId(headingId) {
  const parts = headingId.split(".");
  if (parts.length === 2) return [TARGET_CHAPTER_ID, headingId];
  return [TARGET_CHAPTER_ID, `${parts[0]}.${parts[1]}`, headingId];
}

function sectionKind(sectionPath) {
  const leaf = sectionPath.at(-1) ?? "";
  if (leaf.startsWith("3.1")) return "background";
  if (leaf.startsWith("3.2")) return "source_translation";
  return "unknown";
}

function parseProcedure(line) {
  const match = line.trim().match(PROC_RE);
  if (!match) return null;
  const title = normalizeWhitespace(match.groups.title ?? "");
  const looksLikeProcedureHeading = !title
    || title.includes("[")
    || title.endsWith(":")
    || /^(?:T\s*o|To|Another|Method|Table|T\s*able|Month Names)\b/iu.test(title);
  if (!looksLikeProcedureHeading) return null;
  return {
    id: `Proc. ${match.groups.id}`,
    title,
    title_complete: title.endsWith(":"),
  };
}

function isRunningHeader(line) {
  return QUARTER_REMAINDER_HEADER_RE.test(line.trim());
}

function isPageArtifact(line) {
  return PAGE_ARTIFACT_RE.test(line.trim());
}

function isTablePlaceholder(line) {
  return TABLE_PLACEHOLDER_RE.test(line.trim());
}

function cjkStats(text) {
  const cjk = countMatches(text, /[\u3400-\u9fff]/gu);
  const latin = countMatches(text, /[A-Za-z]/gu);
  const digits = countMatches(text, /\d/gu);
  const meaningful = cjk + latin + digits;
  return {
    cjk,
    latin,
    digits,
    meaningful,
    ratio: meaningful ? cjk / meaningful : 0,
  };
}

function isChineseSourceLine(line) {
  const text = line.trim();
  if (!text) return false;
  if (isTablePlaceholder(text)) return false;
  if (isRunningHeader(text) || isPageArtifact(text)) return false;
  if (parseHeading(text) || parseProcedure(text)) return false;
  if (/^§\s*\d+/u.test(text)) return false;
  const stats = cjkStats(text);
  return stats.cjk >= 3 && stats.ratio >= 0.35 && stats.latin <= Math.max(2, stats.cjk / 3);
}

function isShortChineseSourceContinuation(line) {
  const text = line.trim();
  if (!text) return false;
  if (parseHeading(text) || parseProcedure(text) || startsWithSectionMarker(text)) return false;
  const stats = cjkStats(text);
  if (stats.latin > 0 || stats.digits > 0) return false;
  return stats.cjk >= 1 && stats.ratio >= 0.6 && text.length <= 24;
}

function startsWithSectionMarker(text) {
  return SECTION_MARKER_AT_LINE_START_RE.test(text.trim());
}

function isLikelyProcedureTitleContinuation(text) {
  const trimmed = text.trim();
  if (!trimmed) return false;
  if (startsWithSectionMarker(trimmed)) return false;
  if (parseHeading(trimmed) || parseProcedure(trimmed)) return false;
  if (isTablePlaceholder(trimmed) || isRunningHeader(trimmed) || isPageArtifact(trimmed)) return false;
  if (trimmed.length > 120) return false;
  const stats = cjkStats(trimmed);
  if (stats.cjk > 0) return false;
  return /^[A-Za-z\[\(]/u.test(trimmed) || /^[a-z]/u.test(trimmed);
}

function extractUnitIds(text) {
  return unique([...String(text ?? "").matchAll(SECTION_MARKER_RE)].map((match) => `§${match[1]}`));
}

function extractUnitNumbersFromUnitIds(unitIds) {
  return unitIds
    .map((unitId) => String(unitId).match(/^§(\d{1,3})$/u))
    .filter(Boolean)
    .map((match) => Number.parseInt(match[1], 10));
}

function extractUnitIdsFromMarkerLines(lineRefs) {
  return unique(lineRefs.flatMap((line, index) => {
    const trimmed = line.text.trim();
    if (!startsWithSectionMarker(trimmed)) return [];
    const previousText = lineRefs[index - 1]?.text.trim() ?? "";
    if (/\bsections?$/iu.test(previousText)) return [];
    return extractUnitIds(trimmed);
  }));
}

function hasUnitMarkerLine(lineRefs) {
  return extractUnitIdsFromMarkerLines(lineRefs).length > 0;
}

function extractRefs(text, regex) {
  return unique([...String(text ?? "").matchAll(regex)].map((match) => match[0]));
}

function collectPageRange(lineRefs) {
  const pdfs = lineRefs
    .map((line) => line.pdf_page_number)
    .filter(Number.isFinite);
  const books = lineRefs
    .map((line) => String(line.book_page_number ?? ""))
    .filter((value) => parseNumericBookPage(value) !== null);
  return {
    pdf_pages: pdfs.length ? [Math.min(...pdfs), Math.max(...pdfs)] : [null, null],
    book_pages: books.length ? [books[0], books.at(-1)] : [null, null],
  };
}

function buildText(parts) {
  return parts
    .map((part) => part.trim())
    .filter(Boolean)
    .join("\n\n");
}

function lineText(lineRefs) {
  return normalizeWhitespace(lineRefs.map((line) => line.text).join(" "));
}

function bodyTextFromLineRefs(lineRefs) {
  const paragraphs = [];
  let buffer = [];

  function flushBuffer() {
    const text = normalizeWhitespace(buffer.map((line) => line.text).join(" "));
    if (text) paragraphs.push(text);
    buffer = [];
  }

  for (const line of lineRefs) {
    if (!line.text.trim()) {
      flushBuffer();
      continue;
    }
    buffer.push(line);
  }
  flushBuffer();

  return paragraphs.join("\n\n");
}

function makeWarning(warnings, code, message, context = {}) {
  const id = `cullen:ch3:warning:${String(warnings.length + 1).padStart(4, "0")}`;
  const { severity, ...rest } = context;
  warnings.push({
    id,
    severity: severity ?? ISSUE_SEVERITY_BY_CODE[code] ?? "warning",
    code,
    message,
    ...rest,
  });
  return id;
}

function prepareTargetLines(pagesPayload, warnings) {
  const targetPages = (pagesPayload.pages ?? []).filter(isTargetBookPage);
  const lines = [];

  for (const page of targetPages) {
    const rawText = String(page.raw_text ?? page.normalized_text ?? "");
    const rawLines = rawText.replace(/\r\n?/gu, "\n").split("\n");

    rawLines.forEach((rawLine, index) => {
      const text = rawLine.trimEnd();
      const trimmed = text.trim();
      if (isRunningHeader(trimmed)) return;
      if (isPageArtifact(trimmed)) {
        makeWarning(warnings, "page_artifact_line_removed_from_chunk_stream", "High-confidence page artifact line was excluded from chunks.", {
          pdf_page_number: page.pdf_page_number ?? null,
          book_page_number: String(page.book_page_number ?? ""),
          raw_line_index: index,
          text: trimmed,
        });
        return;
      }
      lines.push({
        text,
        raw_line_index: index,
        pdf_page_number: page.pdf_page_number ?? null,
        book_page_number: String(page.book_page_number ?? ""),
        footnote_refs: page.footnote_refs ?? [],
        table_refs: page.table_refs ?? [],
      });
    });
  }

  return lines;
}

function makeChunk(nextId, payload, warnings) {
  const text = payload.text;
  const { pdf_pages, book_pages } = collectPageRange(payload.refs);
  const unitIds = payload.unit_ids ?? [];
  const procedureEntries = mergeProcedureEntries(payload.procedure_entries ?? []);
  const warningIds = [...payload.warningIds];
  const isTableBackedUnitWithoutInlineSource = unitIds.length > 0
    && !payload.source_text_zh
    && (/\[TABLE_3_\d+\]/u.test(text) || /^§\s*\d+\s+T\s*able\b/iu.test(payload.english_text.trim()));

  if (sectionKind(payload.section_path) === "source_translation") {
    if (unitIds.length > 0 && !payload.source_text_zh) {
      warningIds.push(makeWarning(warnings, "section_marker_without_source_text", "A § marker was chunked without a preceding Chinese source block.", {
        severity: isTableBackedUnitWithoutInlineSource ? "review" : undefined,
        chunk_id: `cullen:ch3:chunk:${String(nextId).padStart(4, "0")}`,
        section_path: payload.section_path,
        heading: payload.heading,
        unit_ids: unitIds,
        reason: isTableBackedUnitWithoutInlineSource ? "table_backed_unit_without_inline_source_text" : undefined,
        preview: text.slice(0, 240),
      }));
    }
    if (payload.source_text_zh && unitIds.length === 0) {
      warningIds.push(makeWarning(warnings, "source_text_without_section_marker", "A Chinese source block was chunked without a following § marker.", {
        chunk_id: `cullen:ch3:chunk:${String(nextId).padStart(4, "0")}`,
        section_path: payload.section_path,
        heading: payload.heading,
        preview: payload.source_text_zh.slice(0, 240),
      }));
    }
    if (payload.english_text && unitIds.length > 0 && !payload.english_text.trim().startsWith("§")) {
      warningIds.push(makeWarning(warnings, "english_group_does_not_start_with_section_marker", "A 3.2 English group does not start with §N.", {
        chunk_id: `cullen:ch3:chunk:${String(nextId).padStart(4, "0")}`,
        section_path: payload.section_path,
        heading: payload.heading,
        preview: payload.english_text.slice(0, 240),
      }));
    }
  }

  return {
    id: `cullen:ch3:chunk:${String(nextId).padStart(4, "0")}`,
    section_path: payload.section_path,
    heading: payload.heading,
    pdf_pages,
    book_pages,
    unit_ids: unitIds,
    procedure_ids: procedureEntries.map((entry) => entry.id),
    procedure_titles: procedureEntries.map((entry) => entry.title || ""),
    footnote_refs: extractRefs(text, FOOTNOTE_REF_RE),
    table_refs: extractRefs(text, TABLE_REF_RE),
    text,
    source_text_zh: payload.source_text_zh,
    english_text: payload.english_text,
    warning_ids: unique(warningIds),
  };
}

function currentContextDefaults() {
  return {
    section_path: [TARGET_CHAPTER_ID],
    heading: null,
    procedure_entries: [],
  };
}

function buildChunks(lines, warnings) {
  const chunks = [];
  let nextChunkId = 1;
  let context = currentContextDefaults();
  let backgroundBuffer = [];
  let sourceBuffer = [];
  let englishBuffer = [];
  let groupProcedureEntries = [];
  let pendingProcedure = null;

  function syncPendingProcedure(nextProcedure) {
    pendingProcedure = nextProcedure;
    context.procedure_entries = nextProcedure ? mergeProcedureEntries([nextProcedure]) : [];
    groupProcedureEntries = nextProcedure ? mergeProcedureEntries([nextProcedure]) : [];
  }

  function extendPendingProcedureTitle(lineTextValue) {
    if (!pendingProcedure) return false;
    pendingProcedure = {
      ...pendingProcedure,
      title: normalizeWhitespace([pendingProcedure.title, lineTextValue].filter(Boolean).join(" ")),
    };
    pendingProcedure.title_complete = pendingProcedure.title.endsWith(":");
    context.procedure_entries = mergeProcedureEntries([pendingProcedure]);
    groupProcedureEntries = mergeProcedureEntries([pendingProcedure]);
    return true;
  }

  function flushBackground(reason = "background_flush") {
    if (!backgroundBuffer.length) return;
    const text = bodyTextFromLineRefs(backgroundBuffer);
    const refs = [...backgroundBuffer];
    backgroundBuffer = [];
    if (!text) return;
    chunks.push(makeChunk(nextChunkId++, {
      refs,
      section_path: [...context.section_path],
      heading: context.heading,
      procedure_entries: [],
      unit_ids: [],
      text,
      source_text_zh: "",
      english_text: "",
      warningIds: reason === "background_without_3_1_leaf"
        ? [makeWarning(warnings, "background_text_without_3_1_leaf_heading", "Background text appeared before a 3.1.x leaf heading.", {
          section_path: context.section_path,
          preview: text.slice(0, 240),
        })]
        : [],
    }, warnings));
  }

  function flushSourceTranslationGroup(reason = "source_translation_flush") {
    if (!sourceBuffer.length && !englishBuffer.length) return;
    const sourceText = lineText(sourceBuffer);
    const englishText = bodyTextFromLineRefs(englishBuffer);
    const text = buildText([sourceText, englishText]);
    const refs = [...sourceBuffer, ...englishBuffer];
    const warningIds = [];

    if (!text) {
      sourceBuffer = [];
      englishBuffer = [];
      groupProcedureEntries = [];
      return;
    }

    if (reason === "section_marker_before_source") {
      const tableBackedUnitWithoutInlineSource = /\[TABLE_3_\d+\]/u.test(text)
        || /^§\s*\d+\s+T\s*able\b/iu.test(englishText.trim());
      warningIds.push(makeWarning(warnings, "section_marker_before_source", "A § marker appeared before a matching Chinese source block.", {
        severity: tableBackedUnitWithoutInlineSource ? "review" : undefined,
        section_path: context.section_path,
        heading: context.heading,
        procedure_ids: groupProcedureEntries.map((entry) => entry.id),
        reason: tableBackedUnitWithoutInlineSource ? "table_backed_unit_without_inline_source_text" : undefined,
        preview: englishText.slice(0, 240),
      }));
    }
    if (reason === "source_interrupted_by_heading") {
      warningIds.push(makeWarning(warnings, "source_interrupted_by_heading", "A Chinese source block was interrupted by a section heading before a § marker appeared.", {
        section_path: context.section_path,
        heading: context.heading,
        preview: sourceText.slice(0, 240),
      }));
    }

    chunks.push(makeChunk(nextChunkId++, {
      refs,
      section_path: [...context.section_path],
      heading: context.heading,
      procedure_entries: groupProcedureEntries.length ? groupProcedureEntries : context.procedure_entries,
      unit_ids: extractUnitIdsFromMarkerLines(englishBuffer),
      text,
      source_text_zh: sourceText,
      english_text: englishText,
      warningIds,
    }, warnings));

    sourceBuffer = [];
    englishBuffer = [];
    groupProcedureEntries = [];
  }

  function setHeading(heading) {
    flushBackground();
    if (sourceBuffer.length || englishBuffer.length) {
      const reason = sourceBuffer.length && !englishBuffer.length
        ? "source_interrupted_by_heading"
        : "heading_after_group";
      flushSourceTranslationGroup(reason);
    }
    context = {
      section_path: sectionPathFromHeadingId(heading.id),
      heading: heading.heading,
      procedure_entries: [],
    };
    pendingProcedure = null;
  }

  for (let index = 0; index < lines.length; index += 1) {
    const line = lines[index];
    const trimmed = line.text.trim();
    const heading = parseHeading(trimmed);

    if (heading) {
      setHeading(heading);
      continue;
    }

    const nonTargetHeading = trimmed.match(NON_TARGET_NUMBERED_HEADING_RE);
    if (nonTargetHeading && !heading) {
      makeWarning(warnings, "non_target_numbered_heading_in_ch3_stream", "A numbered heading-like line was not accepted as a Ch3 3.1/3.2 heading.", {
        pdf_page_number: line.pdf_page_number,
        book_page_number: line.book_page_number,
        text: trimmed,
      });
    }

    const proc = parseProcedure(trimmed);
    if (proc) {
      if (englishBuffer.length && hasUnitMarkerLine(englishBuffer)) {
        flushSourceTranslationGroup("procedure_heading_boundary");
      }
      syncPendingProcedure(proc);
      continue;
    }
    if (PROC_RE.test(trimmed)) {
      makeWarning(warnings, "proc_like_line_treated_as_body", "A Proc-like line did not match the conservative Proc heading rules and was kept as body text.", {
        section_path: context.section_path,
        heading: context.heading,
        pdf_page_number: line.pdf_page_number,
        book_page_number: line.book_page_number,
        text: trimmed,
      });
    }

    const kind = sectionKind(context.section_path);

    if (kind === "background") {
      if (isChineseSourceLine(trimmed) || startsWithSectionMarker(trimmed)) {
        makeWarning(warnings, "unexpected_source_or_section_marker_in_3_1", "Chinese-like source text or § marker appeared inside 3.1 background.", {
          section_path: context.section_path,
          heading: context.heading,
          pdf_page_number: line.pdf_page_number,
          book_page_number: line.book_page_number,
          text: trimmed.slice(0, 240),
        });
      }
      backgroundBuffer.push(line);
      continue;
    }

    if (kind !== "source_translation") {
      backgroundBuffer.push(line);
      continue;
    }

    const isSource = isChineseSourceLine(trimmed);
    const lineHasSectionMarker = startsWithSectionMarker(trimmed);

    if (isSource) {
      if (englishBuffer.length) {
        const reason = sourceBuffer.length
          ? "source_translation_before_next_source"
          : (hasUnitMarkerLine(englishBuffer) ? "section_marker_before_source" : "english_prose_before_source");
        flushSourceTranslationGroup(reason);
      }
      sourceBuffer.push(line);
      continue;
    }

    if (sourceBuffer.length && !englishBuffer.length && isShortChineseSourceContinuation(trimmed)) {
      sourceBuffer.push(line);
      continue;
    }

    if (pendingProcedure && sourceBuffer.length && !englishBuffer.length && !pendingProcedure.title_complete && isLikelyProcedureTitleContinuation(trimmed)) {
      extendPendingProcedureTitle(trimmed);
      continue;
    }

    if (lineHasSectionMarker) {
      if (!sourceBuffer.length && englishBuffer.length && !hasUnitMarkerLine(englishBuffer)) {
        flushSourceTranslationGroup("english_prose_before_section_marker");
      }
      if (englishBuffer.length && !sourceBuffer.length) {
        flushSourceTranslationGroup("section_marker_before_source");
      }
      englishBuffer.push(line);
      groupProcedureEntries = mergeProcedureEntries([...groupProcedureEntries, ...context.procedure_entries]);
      continue;
    }

    if (sourceBuffer.length || englishBuffer.length) {
      englishBuffer.push(line);
      continue;
    }

    if (trimmed) {
      // Preserve prose/table placeholders in 3.2 that are not part of a normal
      // Chinese+§ group. They become warning-bearing chunks instead of being
      // dropped from the corpus.
      englishBuffer.push(line);
      groupProcedureEntries = mergeProcedureEntries([...groupProcedureEntries, ...context.procedure_entries]);
    }
  }

  flushBackground();
  if (sourceBuffer.length || englishBuffer.length) {
    const reason = !sourceBuffer.length && hasUnitMarkerLine(englishBuffer)
      ? "section_marker_before_source"
      : "trailing_source_translation_group";
    flushSourceTranslationGroup(reason);
  }

  return chunks;
}

function validateUnitSequence(chunks, warnings) {
  const observed = [];
  for (const chunk of chunks) {
    for (const unitNumber of extractUnitNumbersFromUnitIds(chunk.unit_ids)) {
      observed.push({ unitNumber, chunk_id: chunk.id });
      if (unitNumber < 1 || unitNumber > 260) {
        const warningId = makeWarning(warnings, "section_marker_outside_expected_1_260_range", "A § marker fell outside the expected Ch3 range 1-260.", {
          chunk_id: chunk.id,
          unit_number: unitNumber,
        });
        chunk.warning_ids = unique([...chunk.warning_ids, warningId]);
      }
    }
  }

  const duplicates = [];
  const seen = new Map();
  for (const item of observed) {
    if (seen.has(item.unitNumber)) {
      duplicates.push({
        unit_number: item.unitNumber,
        first_chunk_id: seen.get(item.unitNumber),
        duplicate_chunk_id: item.chunk_id,
      });
    } else {
      seen.set(item.unitNumber, item.chunk_id);
    }
  }
  if (duplicates.length) {
    makeWarning(warnings, "duplicate_section_markers", "Duplicate § markers were found in the Ch3 chunk stream.", {
      duplicates,
    });
  }

  const sorted = observed.map((item) => item.unitNumber).sort((a, b) => a - b);
  const missing = [];
  for (let expected = 1; expected <= 260; expected += 1) {
    if (!sorted.includes(expected)) missing.push(expected);
  }
  if (missing.length) {
    makeWarning(warnings, "missing_section_markers_1_260", "Some expected § markers from 1-260 were not found in chunks.", {
      missing,
      missing_count: missing.length,
    });
  }

  const orderProblems = [];
  let previous = 0;
  for (const item of observed) {
    if (item.unitNumber <= previous) {
      orderProblems.push({
        previous_unit_number: previous,
        current_unit_number: item.unitNumber,
        chunk_id: item.chunk_id,
      });
    }
    previous = item.unitNumber;
  }
  if (orderProblems.length) {
    makeWarning(warnings, "section_markers_not_monotonic_in_text_order", "§ markers were not strictly increasing in text order.", {
      orderProblems,
    });
  }

  return {
    observed_count: observed.length,
    min_observed: sorted[0] ?? null,
    max_observed: sorted.at(-1) ?? null,
    duplicate_count: duplicates.length,
    missing_count: missing.length,
    order_problem_count: orderProblems.length,
  };
}

function summarizeIssues(warnings) {
  const countsBySeverity = {};
  const countsByCode = {};
  const warningCountsByCode = {};

  for (const warning of warnings) {
    countsBySeverity[warning.severity] = (countsBySeverity[warning.severity] ?? 0) + 1;
    countsByCode[warning.code] = (countsByCode[warning.code] ?? 0) + 1;
    if (warning.severity === "warning") {
      warningCountsByCode[warning.code] = (warningCountsByCode[warning.code] ?? 0) + 1;
    }
  }

  return {
    issue_count: warnings.length,
    warning_count: countsBySeverity.warning ?? 0,
    review_count: countsBySeverity.review ?? 0,
    info_count: countsBySeverity.info ?? 0,
    issue_counts_by_severity: countsBySeverity,
    issue_counts_by_code: countsByCode,
    warning_counts_by_code: warningCountsByCode,
  };
}

function summarizeChunks(chunks, warnings) {
  const bySection = {};
  const warningsById = new Map(warnings.map((warning) => [warning.id, warning]));
  for (const chunk of chunks) {
    const section = chunk.section_path.at(-1) ?? "unknown";
    bySection[section] = (bySection[section] ?? 0) + 1;
  }
  const chunkHasSeverity = (chunk, severity) => (
    chunk.warning_ids.some((warningId) => warningsById.get(warningId)?.severity === severity)
  );
  return {
    chunk_count: chunks.length,
    background_chunk_count: chunks.filter((chunk) => sectionKind(chunk.section_path) === "background").length,
    source_translation_chunk_count: chunks.filter((chunk) => sectionKind(chunk.section_path) === "source_translation").length,
    chunks_by_section: bySection,
    chunks_with_warning_severity: chunks.filter((chunk) => chunkHasSeverity(chunk, "warning")).length,
    chunks_with_review_severity: chunks.filter((chunk) => chunkHasSeverity(chunk, "review")).length,
    chunks_with_info_severity: chunks.filter((chunk) => chunkHasSeverity(chunk, "info")).length,
  };
}

async function main() {
  const config = await readPipelineConfig();
  const pagesPayload = await readJson(INPUT_PAGES_PATH);
  const warnings = [];
  const lines = prepareTargetLines(pagesPayload, warnings);
  const chunks = buildChunks(lines, warnings);
  const unit_sequence = validateUnitSequence(chunks, warnings);
  const issueSummary = summarizeIssues(warnings);
  const summary = summarizeChunks(chunks, warnings);

  const chunksPayload = {
    generated_at: new Date().toISOString(),
    schema_version: CHUNK_SCHEMA_VERSION,
    artifact_scope: {
      chapter_id: TARGET_CHAPTER_ID,
      system_id: TARGET_SYSTEM_ID,
      book_page_start: TARGET_BOOK_PAGE_START,
      book_page_end: TARGET_BOOK_PAGE_END,
      note: "Chapter 3 / Sifen chunks only; this replaces the earlier broad Cullen chunk output.",
    },
    source_pages_artifact: INPUT_PAGES_PATH,
    source_footnotes_artifact: "tmp/procedure-ir/cullen-ch3-footnotes.json",
    source_tables_artifact: "tmp/procedure-ir/cullen-ch3-tables.json",
    chunking_method: CHUNKING_METHOD,
    field_policy: {
      omitted_redundant_fields: [
        "chunk_type",
        "chapter_id",
        "section_id",
        "source_page_refs",
        "char_count",
        "page_start",
        "page_end",
        "translation_en",
        "commentary_en",
      ],
      page_range_policy: "pdf_pages/book_pages store [start,end]; per-page expansion is intentionally omitted.",
      text_policy: "text is authoritative; source_text_zh and english_text are best-effort splits for 3.2 source/translation groups.",
      procedure_policy: "procedure_ids remain stable identifiers; procedure_titles preserves the parsed Proc heading title aligned by index.",
    },
    ...summary,
    chunks,
  };

  const warningsPayload = {
    generated_at: chunksPayload.generated_at,
    schema_version: CHUNK_SCHEMA_VERSION,
    artifact_scope: chunksPayload.artifact_scope,
    source_pages_artifact: INPUT_PAGES_PATH,
    chunks_artifact: config.inputs.cullen.artifacts.chunks,
    chunking_method: CHUNKING_METHOD,
    ...issueSummary,
    unit_sequence,
    warnings,
  };
  const structureAuditPayload = {
    generated_at: chunksPayload.generated_at,
    schema_version: CHUNK_SCHEMA_VERSION,
    artifact_scope: chunksPayload.artifact_scope,
    source_pages_artifact: INPUT_PAGES_PATH,
    chunks_artifact: config.inputs.cullen.artifacts.chunks,
    warnings_artifact: WARNINGS_OUTPUT_PATH,
    chunking_method: CHUNKING_METHOD,
    field_policy: chunksPayload.field_policy,
    ...summary,
    unit_sequence,
    ...issueSummary,
  };

  await writeJson(config.inputs.cullen.artifacts.chunks, chunksPayload);
  await writeJson(WARNINGS_OUTPUT_PATH, warningsPayload);
  await writeJson(STRUCTURE_AUDIT_OUTPUT_PATH, structureAuditPayload);

  console.log(JSON.stringify({
    stage: "build-cullen-chunks",
    input: INPUT_PAGES_PATH,
    chunks_output: config.inputs.cullen.artifacts.chunks,
    warnings_output: WARNINGS_OUTPUT_PATH,
    structure_audit_output: STRUCTURE_AUDIT_OUTPUT_PATH,
    ...summary,
    ...issueSummary,
    unit_sequence,
  }, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
