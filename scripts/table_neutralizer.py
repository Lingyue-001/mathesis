import json
import re
import sys
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path


# Table neutralization for the current Cullen Chapter 3 / Sifen chunking pass.
#
# This is a narrow, whitelist-driven stage. It only targets the 11 Chapter 3
# tables listed in Cullen's table list and uses expected book pages plus anchored
# table-title lines. It is not a full-book table detector. The goal is to remove
# table-shaped noise from the page stream while preserving the removed text in a
# reviewable table archive.

DEFAULT_INPUT = Path("tmp/procedure-ir/cullen-ch3-footnote-cleaned-pages.json")
DEFAULT_TABLES_OUTPUT = Path("tmp/procedure-ir/cullen-ch3-tables.json")
DEFAULT_NEUTRALIZED_OUTPUT = Path("tmp/procedure-ir/cullen-ch3-table-neutralized-pages.json")

DEFAULT_BOOK_PAGE_START = 138
DEFAULT_BOOK_PAGE_END = 234
DEFAULT_CHAPTER_ID = "3"
DEFAULT_SYSTEM_ID = "sifen"

PAGE_START = "__PAGE_START__"

TABLES = [
    {
        "table_id": "3.1",
        "title": "Table of year-names (text)",
        "expected_book_page": "162",
        "placeholder": "[TABLE_3_1]",
    },
    {
        "table_id": "3.2",
        "title": "Table of year-names",
        "expected_book_page": "163",
        "placeholder": "[TABLE_3_2]",
    },
    {
        "table_id": "3.3",
        "title": "Night lengths for the four principal qi",
        "expected_book_page": "170",
        "placeholder": "[TABLE_3_3]",
    },
    {
        "table_id": "3.4",
        "title": "Month names and Medial qi (text)",
        "expected_book_page": "220",
        "placeholder": "[TABLE_3_4]",
    },
    {
        "table_id": "3.5",
        "title": "Month names and Medial qi, with number in sequence of all 24 qi",
        "expected_book_page": "220",
        "placeholder": "[TABLE_3_5]",
    },
    {
        "table_id": "3.6",
        "title": "Lodges on equator (text)",
        "expected_book_page": "221",
        "placeholder": "[TABLE_3_6]",
    },
    {
        "table_id": "3.7",
        "title": "Lodges on ecliptic (text)",
        "expected_book_page": "222",
        "placeholder": "[TABLE_3_7]",
    },
    {
        "table_id": "3.8",
        "title": "Lodges on the equator and the ecliptic",
        "expected_book_page": "223",
        "placeholder": "[TABLE_3_8]",
    },
    {
        "table_id": "3.9",
        "title": "Representing fractions",
        "expected_book_page": "225",
        "placeholder": "[TABLE_3_9]",
    },
    {
        "table_id": "3.10",
        "title": "Solar data (text)",
        "expected_book_page": "226",
        "placeholder": "[TABLE_3_10]",
    },
    {
        "table_id": "3.11",
        "title": "Solar data, day and night lengths, and centred stars",
        "expected_book_page": "229",
        "placeholder": "[TABLE_3_11]",
    },
]


# Segment rules are deliberately explicit because Chapter 3 tables can share
# pages with prose, Proc blocks, and other tables. End markers are excluded from
# the extracted table segment.
TABLE_SEGMENTS = [
    {
        "table_id": "3.1",
        "book_page_number": "162",
        "start_pattern": r"^Table 3\.1\b.*$",
        "end_pattern": None,
    },
    {
        "table_id": "3.2",
        "book_page_number": "163",
        "start_pattern": r"^Table 3\.2\b.*$",
        "end_pattern": r"^How does this table work\?",
    },
    {
        "table_id": "3.3",
        "book_page_number": "170",
        "start_pattern": r"^Table 3\.3\b.*$",
        "end_pattern": r"^From this it is clear",
    },
    {
        "table_id": "3.4",
        "book_page_number": "220",
        "start_pattern": r"^Table 3\.4\b.*$",
        "end_pattern": r"^Proc\. 3\.49\.",
    },
    {
        "table_id": "3.5",
        "book_page_number": "220",
        "start_pattern": r"^Table 3\.5\b.*$",
        "end_pattern": None,
    },
    {
        "table_id": "3.5",
        "book_page_number": "221",
        "start_pattern": r"^Month Medial Qi$",
        "end_pattern": r"^Table 3\.5 above tells us",
    },
    {
        "table_id": "3.6",
        "book_page_number": "221",
        "start_pattern": r"^Table 3\.6\b.*$",
        "end_pattern": None,
    },
    {
        "table_id": "3.6",
        "book_page_number": "222",
        # Page 222 begins with the tail of Table 3.6, followed by the source
        # heading "黃道度" that introduces Table 3.7. Keep that heading in the
        # body stream instead of folding it into the Table 3.6 continuation.
        "start_pattern": r"^亢 九 退 一$",
        "end_pattern": r"^黃道度$",
    },
    {
        "table_id": "3.7",
        "book_page_number": "222",
        "start_pattern": r"^Table 3\.7\b.*$",
        "end_pattern": r"^Table 3\.6 \(Continued\)\s*$",
    },
    {
        "table_id": "3.8",
        "book_page_number": "223",
        "start_pattern": r"^Table 3\.8\b.*$",
        "end_pattern": r"^The .advances and retardations.",
    },
    {
        "table_id": "3.9",
        "book_page_number": "225",
        "start_pattern": r"^Table 3\.9\b.*$",
        "end_pattern": None,
    },
    {
        "table_id": "3.10",
        "book_page_number": "226",
        "start_pattern": r"^Table 3\.10\b.*$",
        "end_pattern": None,
    },
    {
        "table_id": "3.10",
        "book_page_number": "227",
        "start_pattern": PAGE_START,
        "end_pattern": r"^The format of Table 3\.10",
    },
    {
        "table_id": "3.11",
        "book_page_number": "229",
        "start_pattern": r"^Table 3\.11\b.*$",
        "end_pattern": None,
    },
    {
        "table_id": "3.11",
        "book_page_number": "230",
        "start_pattern": PAGE_START,
        "end_pattern": None,
    },
]


# Some "continued" captions appear out of natural reading order in extracted
# plain text. Remove them as table residue, but record that removal separately.
ORPHAN_TABLE_MARKERS = [
    {
        "table_id": "3.6",
        "book_page_number": "222",
        "pattern": r"^Table 3\.6 \(Continued\)\s*$",
    },
    {
        "table_id": "3.10",
        "book_page_number": "227",
        "pattern": r"^Table 3\.10 \(Continued\)\s*$",
    },
]


def normalize_text(text: str) -> str:
    text = text.replace("\u00ad", "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"(?<=\w)-\n(?=\w)", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def page_by_book_number(pages: list[dict]) -> dict[str, dict]:
    return {str(page.get("book_page_number")): page for page in pages}


def find_pattern(text: str, pattern: str, start: int = 0):
    return re.search(pattern, text[start:], flags=re.MULTILINE)


def find_segment(raw_text: str, segment: dict) -> tuple[int | None, int | None, str | None]:
    if segment["start_pattern"] == PAGE_START:
        start = 0
    else:
        start_match = find_pattern(raw_text, segment["start_pattern"])
        if not start_match:
            return None, None, "start_pattern_not_found"
        start = start_match.start()

    if segment["end_pattern"]:
        end_match = find_pattern(raw_text, segment["end_pattern"], start=start)
        if not end_match:
            return None, None, "end_pattern_not_found"
        end = start + end_match.start()
    else:
        end = len(raw_text)

    if end <= start:
        return None, None, "empty_or_inverted_segment"
    return start, end, None


def make_page_ref(page: dict) -> dict:
    return {
        "pdf_page_number": page.get("pdf_page_number"),
        "book_page_number": page.get("book_page_number"),
    }


def build_table_records() -> dict[str, dict]:
    return {
        table["table_id"]: {
            **table,
            "segments": [],
            "removed_orphan_markers": [],
            "raw_text": "",
            "segment_count": 0,
            "page_refs": [],
        }
        for table in TABLES
    }


def append_table_segment(table: dict, segment_record: dict) -> None:
    table["segments"].append(segment_record)
    page_ref = {
        "pdf_page_number": segment_record["pdf_page_number"],
        "book_page_number": segment_record["book_page_number"],
    }
    if page_ref not in table["page_refs"]:
        table["page_refs"].append(page_ref)


def finalize_table_records(tables: dict[str, dict]) -> list[dict]:
    finalized = []
    for table_id in sorted(tables, key=lambda value: [int(part) for part in value.split(".")]):
        table = tables[table_id]
        table["segment_count"] = len(table["segments"])
        table["raw_text"] = "\n\n".join(
            f"[TABLE {table_id} SEGMENT {index + 1} "
            f"pdf={segment['pdf_page_number']} book={segment['book_page_number']}]\n"
            f"{segment['raw_text']}"
            for index, segment in enumerate(table["segments"])
        )
        finalized.append(table)
    return finalized


def build_content_accounting(replacements_by_book: dict[str, list[dict]], tables: dict[str, dict]) -> dict:
    overlap_warnings = []
    scheduled_removed_char_count = 0
    replacement_char_count = 0

    for book_page_number, replacements in sorted(replacements_by_book.items()):
        previous = None
        for replacement in sorted(replacements, key=lambda item: item["start"]):
            scheduled_removed_char_count += replacement["end"] - replacement["start"]
            replacement_char_count += len(replacement["replacement"])
            if previous and replacement["start"] < previous["end"]:
                overlap_warnings.append({
                    "book_page_number": book_page_number,
                    "previous": {
                        "table_id": previous["table_id"],
                        "start": previous["start"],
                        "end": previous["end"],
                        "kind": previous["kind"],
                    },
                    "current": {
                        "table_id": replacement["table_id"],
                        "start": replacement["start"],
                        "end": replacement["end"],
                        "kind": replacement["kind"],
                    },
                })
            previous = replacement

    archived_table_segment_char_count = sum(
        len(segment["raw_text"])
        for table in tables.values()
        for segment in table["segments"]
    )
    archived_orphan_marker_char_count = sum(
        len(marker["raw_text"])
        for table in tables.values()
        for marker in table["removed_orphan_markers"]
    )
    archived_removed_char_count = archived_table_segment_char_count + archived_orphan_marker_char_count

    return {
        "accounting_scope": "table-neutralizer replacement spans only",
        "replacement_span_count": sum(len(replacements) for replacements in replacements_by_book.values()),
        "scheduled_removed_char_count": scheduled_removed_char_count,
        "archived_removed_char_count": archived_removed_char_count,
        "archived_table_segment_char_count": archived_table_segment_char_count,
        "archived_orphan_marker_char_count": archived_orphan_marker_char_count,
        "placeholder_replacement_char_count": replacement_char_count,
        "archived_removed_chars_match_scheduled_removed_chars": archived_removed_char_count == scheduled_removed_char_count,
        "overlap_warning_count": len(overlap_warnings),
        "overlap_warnings": overlap_warnings,
        "note": "If true and overlap_warning_count is 0, every table-neutralizer removed span is archived in cullen-ch3-tables.json. Non-table page text remains in the neutralized pages; whitespace normalization of page raw_text may still change blank-line formatting.",
    }


def neutralize_tables(pages_payload: dict, source_path: Path) -> tuple[dict, dict]:
    neutralized_payload = deepcopy(pages_payload)
    pages = neutralized_payload.get("pages", [])
    pages_by_book = page_by_book_number(pages)

    tables = build_table_records()
    replacements_by_book: dict[str, list[dict]] = {}
    unmatched_segments = []
    removed_orphan_markers = []

    for segment in TABLE_SEGMENTS:
        page = pages_by_book.get(segment["book_page_number"])
        if page is None:
            unmatched_segments.append({
                **segment,
                "reason": "book_page_not_found",
            })
            continue

        raw_text = page.get("raw_text") or ""
        start, end, reason = find_segment(raw_text, segment)
        if reason:
            unmatched_segments.append({
                **segment,
                "pdf_page_number": page.get("pdf_page_number"),
                "reason": reason,
            })
            continue

        table = tables[segment["table_id"]]
        raw_segment = raw_text[start:end]
        segment_record = {
            "table_id": segment["table_id"],
            "pdf_page_number": page.get("pdf_page_number"),
            "book_page_number": page.get("book_page_number"),
            "char_start": start,
            "char_end": end,
            "raw_text": raw_segment,
            "removed_char_count": len(raw_segment),
            "extraction_method": "chapter3_whitelist_expected_page_title_boundary",
            "start_pattern": segment["start_pattern"],
            "end_pattern": segment["end_pattern"],
        }
        append_table_segment(table, segment_record)

        replacements_by_book.setdefault(segment["book_page_number"], []).append({
            "start": start,
            "end": end,
            "replacement": f"\n{table['placeholder']}\n",
            "table_id": segment["table_id"],
            "kind": "table_segment",
        })

    for marker in ORPHAN_TABLE_MARKERS:
        page = pages_by_book.get(marker["book_page_number"])
        if page is None:
            continue
        raw_text = page.get("raw_text") or ""
        for match in re.finditer(marker["pattern"], raw_text, flags=re.MULTILINE):
            removed_text = match.group(0)
            if not removed_text.strip():
                continue
            table = tables[marker["table_id"]]
            marker_record = {
                "table_id": marker["table_id"],
                "pdf_page_number": page.get("pdf_page_number"),
                "book_page_number": page.get("book_page_number"),
                "char_start": match.start(),
                "char_end": match.end(),
                "raw_text": removed_text,
                "removed_char_count": len(removed_text),
                "extraction_method": "orphan_continued_caption_marker",
            }
            table["removed_orphan_markers"].append(marker_record)
            removed_orphan_markers.append(marker_record)
            replacements_by_book.setdefault(marker["book_page_number"], []).append({
                "start": match.start(),
                "end": match.end(),
                "replacement": "",
                "table_id": marker["table_id"],
                "kind": "orphan_table_marker",
            })

    for page in pages:
        book_page = str(page.get("book_page_number"))
        replacements = replacements_by_book.get(book_page, [])
        if not replacements:
            continue

        raw_text = page.get("raw_text") or ""
        table_refs = list(page.get("table_refs", []))
        for replacement in sorted(replacements, key=lambda item: item["start"], reverse=True):
            raw_text = raw_text[:replacement["start"]] + replacement["replacement"] + raw_text[replacement["end"]:]
            ref = f"Table {replacement['table_id']}"
            if ref not in table_refs:
                table_refs.append(ref)

        page["raw_text"] = re.sub(r"\n{3,}", "\n\n", raw_text).strip()
        page["normalized_text"] = normalize_text(page["raw_text"])
        page["char_count"] = len(page["normalized_text"])
        page["table_refs"] = table_refs

    finalized_tables = finalize_table_records(tables)
    matched_table_count = sum(1 for table in finalized_tables if table["segment_count"] > 0)
    extracted_segment_count = sum(table["segment_count"] for table in finalized_tables)
    content_accounting = build_content_accounting(replacements_by_book, tables)

    generated_at = datetime.now(timezone.utc).isoformat()
    neutralized_payload["source_pages_artifact"] = str(source_path)
    neutralized_payload["artifact_scope"] = {
        "chapter_id": DEFAULT_CHAPTER_ID,
        "system_id": DEFAULT_SYSTEM_ID,
        "book_page_start": DEFAULT_BOOK_PAGE_START,
        "book_page_end": DEFAULT_BOOK_PAGE_END,
        "note": "Chapter 3 / Sifen pages after footnote extraction and table neutralization; not a full-book cleaned pages artifact.",
    }
    neutralized_payload["table_neutralization"] = {
        "method": "chapter3_expected_table_whitelist_with_page_local_boundaries",
        "generated_at": generated_at,
        "source_pages_artifact": str(source_path),
        "expected_table_count": len(TABLES),
        "matched_table_count": matched_table_count,
        "extracted_segment_count": extracted_segment_count,
        "unmatched_segments": unmatched_segments,
        "removed_orphan_marker_count": len(removed_orphan_markers),
        "removed_orphan_markers": removed_orphan_markers,
        "content_accounting": content_accounting,
        "note": "This stage replaces table blocks with placeholders while preserving raw table text in cullen-ch3-tables.json.",
    }

    tables_payload = {
        "artifact_scope": {
            "chapter_id": DEFAULT_CHAPTER_ID,
            "system_id": DEFAULT_SYSTEM_ID,
            "book_page_start": DEFAULT_BOOK_PAGE_START,
            "book_page_end": DEFAULT_BOOK_PAGE_END,
            "note": "Chapter 3 / Sifen table archive extracted from footnote-cleaned pages.",
        },
        "source_pages_artifact": str(source_path),
        "generated_at": generated_at,
        "table_extraction": {
            "method": "chapter3_expected_table_whitelist_with_page_local_boundaries",
            "expected_table_count": len(TABLES),
            "matched_table_count": matched_table_count,
            "extracted_segment_count": extracted_segment_count,
            "unmatched_segments": unmatched_segments,
            "removed_orphan_marker_count": len(removed_orphan_markers),
            "content_accounting": content_accounting,
        },
        "tables": finalized_tables,
    }

    return neutralized_payload, tables_payload


def main() -> int:
    input_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_INPUT
    tables_output = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_TABLES_OUTPUT
    neutralized_output = Path(sys.argv[3]) if len(sys.argv) > 3 else DEFAULT_NEUTRALIZED_OUTPUT

    if not input_path.exists():
        print(json.dumps({
            "ok": False,
            "error": "input_not_found",
            "input": str(input_path),
            "hint": "Run scripts/footnote_extractor.py first to create the Chapter 3 footnote-cleaned pages artifact.",
        }, ensure_ascii=False, indent=2))
        return 1

    pages_payload = load_json(input_path)
    neutralized_payload, tables_payload = neutralize_tables(pages_payload, input_path)

    write_json(tables_output, tables_payload)
    write_json(neutralized_output, neutralized_payload)

    print(json.dumps({
        "ok": True,
        "input": str(input_path),
        "tables_output": str(tables_output),
        "neutralized_output": str(neutralized_output),
        "expected_table_count": tables_payload["table_extraction"]["expected_table_count"],
        "matched_table_count": tables_payload["table_extraction"]["matched_table_count"],
        "extracted_segment_count": tables_payload["table_extraction"]["extracted_segment_count"],
        "unmatched_segment_count": len(tables_payload["table_extraction"]["unmatched_segments"]),
        "removed_orphan_marker_count": tables_payload["table_extraction"]["removed_orphan_marker_count"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
