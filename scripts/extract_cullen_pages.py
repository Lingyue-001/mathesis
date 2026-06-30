import json
import re
import sys
from pathlib import Path

from pypdf import PdfReader


ROMAN_PAGE_RE = re.compile(
    r"^(?P<roman>(?:i|ii|iii|iv|v|vi|vii|viii|ix|x|xi|xii|xiii|xiv|xv|xvi|xvii|xviii|xix|xx))$",
    re.IGNORECASE,
)
ARABIC_PAGE_RE = re.compile(r"^\d{1,3}$")


def normalize_text(text: str) -> str:
    text = text.replace("\u00ad", "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"(?<=\w)-\n(?=\w)", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def first_sentence(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not text:
        return ""

    match = re.match(r"^(.{0,260}?(?:[.!?](?:\s|$)|\n))", text, flags=re.DOTALL)
    sentence = match.group(1) if match else text[:260]
    sentence = sentence.replace("\n", " ")
    sentence = re.sub(r"\s+", " ", sentence)
    return sentence.strip()


def classify_book_page_token(token: str | None) -> str | None:
    if token is None:
        return None
    if ROMAN_PAGE_RE.match(token):
        return "roman_lower"
    if ARABIC_PAGE_RE.match(token):
        return "arabic"
    return None


def parse_arabic_book_page_number(value: str | None) -> int | None:
    if value is None:
        return None
    token = str(value).strip()
    if not ARABIC_PAGE_RE.match(token):
        return None
    return int(token)


def extract_book_page_number(raw_text: str) -> tuple[str | None, str | None]:
    sentence = first_sentence(raw_text)
    if not sentence:
        return None, None

    if re.match(r"^\d+\.\d", sentence):
        return None, None

    tokens = sentence.split()
    if not tokens:
        return None, None

    start_token = re.sub(r"^[^\w]+|[^\w]+$", "", tokens[0]).lower()
    if classify_book_page_token(start_token):
        return start_token, "first_sentence_start"

    end_token = re.sub(r"^[^\w]+|[^\w]+$", "", tokens[-1]).lower()
    if classify_book_page_token(end_token):
        return end_token, "first_sentence_end"

    return None, None


def infer_missing_arabic_book_page_numbers(pages: list[dict]) -> list[dict]:
    """Fill unprinted book page numbers only when surrounding Arabic pages prove continuity.

    This deliberately does not infer front-matter roman numerals or unbounded
    blanks. A null block is filled only if the nearest previous and next detected
    Arabic book page numbers have exactly the same gap as the PDF/page-array gap.
    """

    inferred = []
    index = 0
    while index < len(pages):
        if pages[index]["book_page_number"] is not None:
            index += 1
            continue

        start = index
        while index < len(pages) and pages[index]["book_page_number"] is None:
            index += 1
        end = index - 1

        previous_index = start - 1
        next_index = index
        if previous_index < 0 or next_index >= len(pages):
            continue

        previous_number = parse_arabic_book_page_number(pages[previous_index]["book_page_number"])
        next_number = parse_arabic_book_page_number(pages[next_index]["book_page_number"])
        if previous_number is None or next_number is None:
            continue

        page_gap = next_index - previous_index
        book_page_gap = next_number - previous_number
        if page_gap != book_page_gap:
            continue

        for offset, page_index in enumerate(range(start, end + 1), start=1):
            inferred_number = str(previous_number + offset)
            pages[page_index]["book_page_number"] = inferred_number
            pages[page_index]["book_page_number_type"] = "arabic"
            pages[page_index]["book_page_number_position"] = "inferred_from_surrounding_arabic_sequence"
            inferred.append({
                "pdf_page_number": pages[page_index]["pdf_page_number"],
                "book_page_number": inferred_number,
                "previous_pdf_page_number": pages[previous_index]["pdf_page_number"],
                "previous_book_page_number": str(previous_number),
                "next_pdf_page_number": pages[next_index]["pdf_page_number"],
                "next_book_page_number": str(next_number),
            })

    return inferred


def main() -> int:
    if len(sys.argv) != 3:
      raise SystemExit("Usage: extract_cullen_pages.py <input_pdf> <output_json>")

    input_pdf = Path(sys.argv[1])
    output_json = Path(sys.argv[2])

    reader = PdfReader(str(input_pdf))
    pages = []
    for index, page in enumerate(reader.pages, start=1):
        raw_text = page.extract_text() or ""
        normalized_text = normalize_text(raw_text)
        book_page_number, book_page_number_position = extract_book_page_number(raw_text)
        pages.append({
            "pdf_page_number": index,
            "pdf_page_number_type": "pdf_electronic",
            "book_page_number": book_page_number,
            "book_page_number_type": classify_book_page_token(book_page_number),
            "book_page_number_position": book_page_number_position,
            "raw_text": raw_text,
            "normalized_text": normalized_text,
            "char_count": len(normalized_text),
        })

    inferred_book_page_numbers = infer_missing_arabic_book_page_numbers(pages)

    payload = {
        "source_pdf": input_pdf.name,
        "page_count": len(pages),
        "book_page_number_inference": {
            "method": "fill_null_blocks_only_when_surrounding_arabic_book_pages_are_strictly_continuous",
            "inferred_count": len(inferred_book_page_numbers),
            "items": inferred_book_page_numbers,
        },
        "pages": pages,
    }

    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
