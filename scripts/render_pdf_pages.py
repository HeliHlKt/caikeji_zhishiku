from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

import pypdfium2 as pdfium


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render PDF pages to PNG files.")
    parser.add_argument("--pdf", required=True, help="Source PDF path.")
    parser.add_argument("--out-root", required=True, help="Knowledge base root.")
    parser.add_argument("--start", type=int, required=True, help="1-based start page.")
    parser.add_argument("--end", type=int, required=True, help="1-based end page.")
    parser.add_argument("--scale", type=float, default=2.0, help="Render scale.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    pdf_path = Path(args.pdf)
    out_root = Path(args.out_root)
    render_dir = out_root / "01_renders"
    index_dir = out_root / "04_index"
    render_dir.mkdir(parents=True, exist_ok=True)
    index_dir.mkdir(parents=True, exist_ok=True)

    doc = pdfium.PdfDocument(str(pdf_path))
    total_pages = len(doc)
    start_page = max(1, args.start)
    end_page = min(args.end, total_pages)
    page_manifest = []

    for page_number in range(start_page, end_page + 1):
        page = doc[page_number - 1]
        image = page.render(scale=args.scale).to_pil()
        file_name = f"page_{page_number:04d}.png"
        out_path = render_dir / file_name
        image.save(out_path)
        page_manifest.append(
            {
                "page": page_number,
                "image": str(out_path),
                "size": {"width": image.width, "height": image.height},
            }
        )

    manifest_path = index_dir / f"render_manifest_{start_page:04d}_{end_page:04d}.json"
    manifest = {
        "source_pdf": str(pdf_path),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "total_pages": total_pages,
        "rendered_range": [start_page, end_page],
        "pages": page_manifest,
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Rendered {len(page_manifest)} pages to {render_dir}")
    print(f"Manifest: {manifest_path}")


if __name__ == "__main__":
    main()
