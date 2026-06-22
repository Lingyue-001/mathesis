import json
import re
import sys
from pathlib import Path

from pypdf import PdfReader


def normalize_text(text: str) -> str:
    text = text.replace("\u00ad", "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"(?<=\w)-\n(?=\w)", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


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
        pages.append({
            "page_number": index,
            "raw_text": raw_text,
            "normalized_text": normalized_text,
            "char_count": len(normalized_text),
        })

    payload = {
        "source_pdf": input_pdf.name,
        "page_count": len(pages),
        "pages": pages,
    }

    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
