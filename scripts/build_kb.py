from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path


STOPWORDS = {
    "materials",
    "material",
    "science",
    "basic",
    "edition",
    "tsinghua",
    "university",
    "press",
    "chapter",
    "figure",
    "table",
    "page",
    "isbn",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a local knowledge-base index from OCR text.")
    parser.add_argument("--root", required=True, help="Knowledge-base root directory.")
    parser.add_argument("--source-name", required=True, help="Human-readable source PDF name.")
    parser.add_argument("--chunk-size", type=int, default=1200, help="Approximate chars per chunk.")
    parser.add_argument("--book-total-pages", type=int, default=699, help="Total pages in source PDF.")
    return parser.parse_args()


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_long_paragraph(paragraph: str, chunk_size: int) -> list[str]:
    if len(paragraph) <= chunk_size:
        return [paragraph]

    sentences = re.split(r"(?<=[。！？.!?；;])", paragraph)
    sentences = [s.strip() for s in sentences if s.strip()]
    if not sentences:
        return [paragraph[i : i + chunk_size] for i in range(0, len(paragraph), chunk_size)]

    chunks: list[str] = []
    current = []
    current_len = 0
    for sentence in sentences:
        if current and current_len + len(sentence) > chunk_size:
            chunks.append("".join(current).strip())
            current = [sentence]
            current_len = len(sentence)
        else:
            current.append(sentence)
            current_len += len(sentence)
    if current:
        chunks.append("".join(current).strip())
    return chunks


def split_chunks(text: str, chunk_size: int) -> list[str]:
    if len(text) <= chunk_size:
        return [text] if text else []

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    current = []
    current_len = 0

    for para in paragraphs:
        para_parts = split_long_paragraph(para, chunk_size)
        for part in para_parts:
            part_len = len(part)
            if current and current_len + part_len + 2 > chunk_size:
                chunks.append("\n\n".join(current))
                current = [part]
                current_len = part_len
            else:
                current.append(part)
                current_len += part_len + 2

    if current:
        chunks.append("\n\n".join(current))

    return chunks


def extract_terms(text: str) -> list[str]:
    candidates = re.findall(r"[\u4e00-\u9fffA-Za-z0-9\-]{2,20}", text)
    counter = Counter()
    for token in candidates:
        normalized = token.lower()
        if normalized in STOPWORDS or normalized.isdigit():
            continue
        counter[token] += 1
    return [token for token, _ in counter.most_common(25)]


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    args = parse_args()
    root = Path(args.root)
    ocr_dir = root / "02_ocr_pages"
    chunk_dir = root / "03_chunks"
    index_dir = root / "04_index"
    cards_dir = root / "05_cards"
    source_dir = root / "00_source"
    logs_dir = root / "logs"
    for path in (chunk_dir, index_dir, cards_dir, source_dir, logs_dir):
        path.mkdir(parents=True, exist_ok=True)

    page_files = sorted(ocr_dir.glob("page_*.txt"))
    pages = []
    all_terms: Counter[str] = Counter()
    page_map = []
    chunk_records = []

    for page_file in page_files:
        page_number = int(page_file.stem.split("_")[1])
        text = normalize_text(page_file.read_text(encoding="utf-8", errors="ignore"))
        if not text:
            continue

        terms = extract_terms(text)
        all_terms.update(terms)
        pages.append(
            {
                "page": page_number,
                "text_length": len(text),
                "terms": terms,
            }
        )
        page_map.append(
            {
                "page": page_number,
                "ocr_file": str(page_file),
                "preview": text[:180],
            }
        )

        page_chunks = split_chunks(text, args.chunk_size)
        for idx, chunk_text in enumerate(page_chunks, start=1):
            chunk_id = f"page_{page_number:04d}_chunk_{idx:02d}"
            chunk_path = chunk_dir / f"{chunk_id}.md"
            chunk_body = "\n".join(
                [
                    f"# {chunk_id}",
                    "",
                    f"- source: {args.source_name}",
                    f"- page: {page_number}",
                    f"- chunk_index: {idx}",
                    f"- char_count: {len(chunk_text)}",
                    "",
                    chunk_text,
                    "",
                ]
            )
            chunk_path.write_text(chunk_body, encoding="utf-8")
            chunk_records.append(
                {
                    "chunk_id": chunk_id,
                    "page": page_number,
                    "path": str(chunk_path),
                    "char_count": len(chunk_text),
                }
            )

    glossary_path = cards_dir / "glossary_candidates.md"
    glossary_lines = ["# Glossary Candidates", ""]
    for term, count in all_terms.most_common(120):
        glossary_lines.append(f"- {term} ({count})")
    glossary_path.write_text("\n".join(glossary_lines) + "\n", encoding="utf-8")

    processed_pages = [entry["page"] for entry in pages]
    max_processed_page = max(processed_pages, default=0)
    next_start_page = max_processed_page + 1 if max_processed_page < args.book_total_pages else None
    processed_ranges = []
    if processed_pages:
        start = prev = processed_pages[0]
        for page_number in processed_pages[1:]:
            if page_number == prev + 1:
                prev = page_number
                continue
            processed_ranges.append([start, prev])
            start = prev = page_number
        processed_ranges.append([start, prev])

    source_note = {
        "source_name": args.source_name,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "processed_pages": len(processed_pages),
        "max_processed_page": max_processed_page,
        "processed_ranges": processed_ranges,
    }
    write_json(source_dir / "source_info.json", source_note)
    write_json(index_dir / "page_map.json", page_map)
    write_json(index_dir / "chunk_index.json", chunk_records)
    write_json(index_dir / "page_stats.json", pages)

    status = {
        "source_name": args.source_name,
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "book_total_pages": args.book_total_pages,
        "processed_page_count": len(processed_pages),
        "max_processed_page": max_processed_page,
        "processed_ranges": processed_ranges,
        "chunk_count": len(chunk_records),
        "next_recommended_start_page": next_start_page,
        "next_recommended_end_page": min(args.book_total_pages, (next_start_page or args.book_total_pages) + 79)
        if next_start_page
        else None,
    }
    write_json(index_dir / "kb_status.json", status)
    write_json(logs_dir / "latest_status.json", status)

    overview_lines = [
        "# Knowledge Base Overview",
        "",
        f"- Source: {args.source_name}",
        f"- Processed page count: {len(processed_pages)}",
        f"- Max processed page: {max_processed_page}",
        f"- Chunk count: {len(chunk_records)}",
        f"- Updated at: {status['updated_at']}",
        "",
        "## Retrieval Workflow",
        "",
        "- Start with `04_index/kb_status.json` to see current progress.",
        "- Use `04_index/page_map.json` to locate relevant pages and previews.",
        "- Use `03_chunks/` for page-grounded answer assembly.",
        "- Verify important conclusions across multiple pages when possible.",
        "",
        "## Next Suggested Batch",
        "",
        f"- next_start_page: {status['next_recommended_start_page']}",
        f"- next_end_page: {status['next_recommended_end_page']}",
    ]
    (root / "KNOWLEDGE_BASE_OVERVIEW.md").write_text("\n".join(overview_lines) + "\n", encoding="utf-8")

    next_steps_lines = [
        "# Next Steps",
        "",
        f"- Current max processed page: {max_processed_page}",
        f"- Recommended next batch: {status['next_recommended_start_page']} to {status['next_recommended_end_page']}",
        "- Resume by running render -> OCR -> build_kb for the next batch.",
        "- Before answering content questions, prefer searching page_map and chunks first.",
        "- If context is tight in a future chat, point the agent to `04_index/kb_status.json` and this file.",
    ]
    (root / "NEXT_STEPS.md").write_text("\n".join(next_steps_lines) + "\n", encoding="utf-8")

    print(f"Processed pages: {len(processed_pages)}")
    print(f"Max processed page: {max_processed_page}")
    print(f"Chunks created: {len(chunk_records)}")
    print(f"Next batch starts at: {next_start_page}")
    print(f"Glossary file: {glossary_path}")


if __name__ == "__main__":
    main()
