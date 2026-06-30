import json
import re
import sys
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path


# Footnote pre-extraction for the current Cullen Sifen chunking pass.
#
# This script is intentionally narrow: by default it processes Cullen book pages
# 138-234, where Chapter 3 footnotes run from 1 to 27. It removes accepted
# page-bottom footnote blocks from the page text and writes footnotes.json
# keyed by footnote number plus a footnote-cleaned page artifact. It does not
# change cullen-pages.json.

DEFAULT_INPUT = Path("tmp/procedure-ir/cullen-pages.json")
DEFAULT_FOOTNOTES_OUTPUT = Path("tmp/procedure-ir/cullen-ch3-footnotes.json")
DEFAULT_CLEAN_PAGES_OUTPUT = Path("tmp/procedure-ir/cullen-ch3-footnote-cleaned-pages.json")
DEFAULT_BOOK_PAGE_START = 138
DEFAULT_BOOK_PAGE_END = 234
DEFAULT_CHAPTER_ID = "3"
DEFAULT_SYSTEM_ID = "sifen"
DEFAULT_MAX_FOOTNOTE = 27
DEFAULT_BOTTOM_CHARS = 4000

FOOTNOTE_RE = re.compile(
    r"\n(\d{1,2}) ([A-Z][^\n]+(?:\n(?!\d{1,2} [A-Z])[^\n]+)*)"
)

# Manual, human-confirmed continuations for unnumbered cross-page footnotes.
# Keep this list tiny and explicit. These continuations have no reliable marker
# in plain extracted text, so they should not be generalized into an automatic
# deletion rule.
MANUAL_CONTINUATION_OVERRIDES = [
    {
        "footnote_number": 24,
        "pdf_page_number": 246,
        "book_page_number": "233",
        "start_text": "元 (1973 reprint of original of 1815), 16, 1b in vol. 2, 540",
        "reason": "human_confirmed_unnumbered_cross_page_footnote_continuation",
    },
]


def normalize_text(text: str) -> str:
    text = text.replace("\u00ad", "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"(?<=\w)-\n(?=\w)", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def parse_arabic_book_page(value) -> int | None:
    token = str(value or "").strip()
    if not re.fullmatch(r"\d{1,3}", token):
        return None
    return int(token)


def in_target_book_page_range(page: dict, start: int, end: int) -> bool:
    book_page = parse_arabic_book_page(page.get("book_page_number"))
    return book_page is not None and start <= book_page <= end


def candidate_matches_from_page_bottom(raw_text: str, bottom_chars: int) -> list[dict]:
    tail_start = max(0, len(raw_text) - bottom_chars)
    tail = raw_text[tail_start:]
    candidates = []
    for match in FOOTNOTE_RE.finditer(tail):
        number = int(match.group(1))
        candidates.append({
            "number": number,
            "text": match.group(2).strip(),
            "start": tail_start + match.start(),
            "end": tail_start + match.end(),
        })
    return candidates


def select_expected_suffix(candidates: list[dict], next_expected: int, max_footnote: int) -> list[dict]:
    """Pick the page-bottom candidate suffix that continues the global sequence.

    OCR sometimes renders an in-text superscript as a line-start digit, e.g.
    "\n1 Then ...", before the actual page-bottom note "1 For ...". Choosing a
    contiguous expected suffix avoids accepting that body reference as a note.
    """

    best = []
    for start_index in range(len(candidates)):
        expected = next_expected
        selected = []
        for candidate in candidates[start_index:]:
            if candidate["number"] != expected or candidate["number"] > max_footnote:
                selected = []
                break
            selected.append(candidate)
            expected += 1
        if selected and len(selected) >= len(best):
            best = selected
    return best


def remove_footnote_block(raw_text: str, selected: list[dict]) -> str:
    if not selected:
        return raw_text
    block_start = selected[0]["start"]
    block_end = selected[-1]["end"]
    return (raw_text[:block_start] + raw_text[block_end:]).rstrip()


def mark_inline_footnote_refs(text: str, accepted_numbers: list[int]) -> tuple[str, list[str]]:
    refs = []
    updated = text
    for number in accepted_numbers:
        marker = f"[^{number}]"
        refs.append(marker)

        # Superscript rendered after punctuation/word, e.g. "discussed.27 The"
        # or "(為章閏)11". Protect decimal/section labels such as "3.2 TEXT".
        inline_re = re.compile(
            rf"(?<!\d\.)(?<=[A-Za-z\u3400-\u9fff\)\]’”.,;:!?]){number}(?=(?:\s|$|[.;,]))"
        )
        updated = inline_re.sub(marker, updated)

        # Superscript rendered at the start of a wrapped line, e.g. "\n1 Then".
        line_start_re = re.compile(rf"(?m)^(\s*){number}\s+(?=[A-Z])")
        updated = line_start_re.sub(rf"\1{marker} ", updated)

        # Superscript rendered as a bare line at the end of a page.
        line_alone_re = re.compile(rf"(?m)^(\s*){number}(\s*)$")
        updated = line_alone_re.sub(rf"\1{marker}\2", updated)

    return updated, refs


def apply_manual_continuation_overrides(pages: list[dict], footnotes: dict) -> list[dict]:
    applied = []
    pages_by_pdf = {page.get("pdf_page_number"): page for page in pages}

    for override in MANUAL_CONTINUATION_OVERRIDES:
        page = pages_by_pdf.get(override["pdf_page_number"])
        key = str(override["footnote_number"])
        if page is None or key not in footnotes:
            applied.append({
                **override,
                "applied": False,
                "reason_not_applied": "page_or_footnote_not_found",
            })
            continue

        raw_text = page.get("raw_text") or ""
        start_index = raw_text.rfind(override["start_text"])
        if start_index < 0:
            applied.append({
                **override,
                "applied": False,
                "reason_not_applied": "start_text_not_found",
            })
            continue

        continuation_text = raw_text[start_index:].strip()
        cleaned_raw = raw_text[:start_index].rstrip()
        page["raw_text"] = cleaned_raw
        page["normalized_text"] = normalize_text(cleaned_raw)
        page["char_count"] = len(page["normalized_text"])
        if f"[^{override['footnote_number']}]" not in page.get("footnote_refs", []):
            page["footnote_refs"] = [*page.get("footnote_refs", []), f"[^{override['footnote_number']}]"]

        footnotes[key]["text"] = normalize_text(f"{footnotes[key]['text']} {continuation_text}")
        footnotes[key].setdefault("continuations", []).append({
            "pdf_page_number": page.get("pdf_page_number"),
            "book_page_number": page.get("book_page_number"),
            "text": normalize_text(continuation_text),
            "extraction_method": "manual_human_confirmed_continuation_override",
            "reason": override["reason"],
        })

        applied.append({
            **override,
            "applied": True,
            "continuation_char_count": len(continuation_text),
        })

    return applied


def build_clean_pages_and_footnotes(
    payload: dict,
    book_page_start: int,
    book_page_end: int,
    max_footnote: int,
    bottom_chars: int,
) -> tuple[dict, dict]:
    clean_payload = deepcopy(payload)
    clean_pages = clean_payload.get("pages", [])
    footnotes = {}
    extraction_items = []
    rejected_candidates = []
    next_expected = 1

    for page in clean_pages:
        raw_text = page.get("raw_text") or ""
        if not in_target_book_page_range(page, book_page_start, book_page_end):
            page["footnote_refs"] = []
            continue

        candidates = candidate_matches_from_page_bottom(raw_text, bottom_chars)
        relevant_candidates = [
            candidate for candidate in candidates
            if 1 <= candidate["number"] <= max_footnote
        ]
        selected = select_expected_suffix(relevant_candidates, next_expected, max_footnote)

        accepted_numbers = []
        if selected:
            cleaned_raw = remove_footnote_block(raw_text, selected)
            accepted_numbers = [candidate["number"] for candidate in selected]
            cleaned_raw, footnote_refs = mark_inline_footnote_refs(cleaned_raw, accepted_numbers)
            page["raw_text"] = cleaned_raw
            page["normalized_text"] = normalize_text(cleaned_raw)
            page["char_count"] = len(page["normalized_text"])
            page["footnote_refs"] = footnote_refs

            for candidate in selected:
                key = str(candidate["number"])
                footnotes[key] = {
                    "footnote_number": candidate["number"],
                    "footnote_ref": f"[^{candidate['number']}]",
                    "text": normalize_text(candidate["text"]),
                    "pdf_page_number": page.get("pdf_page_number"),
                    "book_page_number": page.get("book_page_number"),
                    "extraction_method": "page_bottom_expected_sequence_suffix",
                }
                extraction_items.append({
                    "footnote_number": candidate["number"],
                    "pdf_page_number": page.get("pdf_page_number"),
                    "book_page_number": page.get("book_page_number"),
                    "start": candidate["start"],
                    "end": candidate["end"],
                })
                next_expected += 1
        else:
            page["footnote_refs"] = []

        for candidate in relevant_candidates:
            if candidate["number"] not in accepted_numbers:
                rejected_candidates.append({
                    "number": candidate["number"],
                    "expected_at_page": next_expected,
                    "pdf_page_number": page.get("pdf_page_number"),
                    "book_page_number": page.get("book_page_number"),
                    "text_preview": normalize_text(candidate["text"])[:180],
                })

    manual_continuations = apply_manual_continuation_overrides(clean_pages, footnotes)

    extraction_summary = {
        "method": "page_bottom_expected_sequence_suffix",
        "scope": {
            "chapter_id": DEFAULT_CHAPTER_ID,
            "system_id": DEFAULT_SYSTEM_ID,
            "book_page_start": book_page_start,
            "book_page_end": book_page_end,
            "max_footnote": max_footnote,
            "bottom_chars": bottom_chars,
        },
        "footnotes_extracted": len(footnotes),
        "next_expected_after_extraction": next_expected,
        "complete_expected_sequence": next_expected == max_footnote + 1,
        "items": extraction_items,
        "manual_continuation_overrides": manual_continuations,
        "rejected_candidate_count": len(rejected_candidates),
        "rejected_candidates_preview": rejected_candidates[:80],
    }

    clean_payload["source_pages_artifact"] = str(DEFAULT_INPUT)
    clean_payload["artifact_scope"] = {
        "chapter_id": DEFAULT_CHAPTER_ID,
        "system_id": DEFAULT_SYSTEM_ID,
        "book_page_start": book_page_start,
        "book_page_end": book_page_end,
        "note": "Chapter 3 / Sifen pages after footnote extraction only; table neutralization happens in the next stage.",
    }
    clean_payload["footnote_extraction"] = extraction_summary

    footnote_payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "artifact_scope": {
            "chapter_id": DEFAULT_CHAPTER_ID,
            "system_id": DEFAULT_SYSTEM_ID,
            "book_page_start": book_page_start,
            "book_page_end": book_page_end,
            "note": "Chapter 3 / Sifen footnotes only; not a full-book footnote inventory.",
        },
        "source_pages_artifact": str(DEFAULT_INPUT),
        "clean_pages_artifact": str(DEFAULT_CLEAN_PAGES_OUTPUT),
        "method": extraction_summary["method"],
        "scope": extraction_summary["scope"],
        "footnote_count": len(footnotes),
        "complete_expected_sequence": extraction_summary["complete_expected_sequence"],
        "footnotes": footnotes,
        "audit": {
            "items": extraction_items,
            "manual_continuation_overrides": manual_continuations,
            "rejected_candidate_count": extraction_summary["rejected_candidate_count"],
            "rejected_candidates_preview": extraction_summary["rejected_candidates_preview"],
        },
    }

    return clean_payload, footnote_payload


def main() -> int:
    input_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_INPUT
    footnotes_output = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_FOOTNOTES_OUTPUT
    clean_pages_output = Path(sys.argv[3]) if len(sys.argv) > 3 else DEFAULT_CLEAN_PAGES_OUTPUT

    payload = json.loads(input_path.read_text(encoding="utf-8"))
    clean_payload, footnote_payload = build_clean_pages_and_footnotes(
        payload,
        DEFAULT_BOOK_PAGE_START,
        DEFAULT_BOOK_PAGE_END,
        DEFAULT_MAX_FOOTNOTE,
        DEFAULT_BOTTOM_CHARS,
    )

    footnotes_output.parent.mkdir(parents=True, exist_ok=True)
    clean_pages_output.parent.mkdir(parents=True, exist_ok=True)
    footnotes_output.write_text(
        json.dumps(footnote_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    clean_pages_output.write_text(
        json.dumps(clean_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(json.dumps({
        "stage": "footnote_extractor",
        "input": str(input_path),
        "footnotes_output": str(footnotes_output),
        "clean_pages_output": str(clean_pages_output),
        "footnote_count": footnote_payload["footnote_count"],
        "complete_expected_sequence": footnote_payload["complete_expected_sequence"],
        "rejected_candidate_count": footnote_payload["audit"]["rejected_candidate_count"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
