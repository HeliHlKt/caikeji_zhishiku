# Materials Science Basic Knowledge Base

This repository is a private-share version of a complete local knowledge base built from a textbook-style PDF.

It is intended for:

- private GitHub repositories
- small-group internal sharing
- direct retrieval and study use
- follow-up question answering based on the indexed content

It is not intended as a public redistribution template unless you have the right to share the source content.

## What Is Included

- OCR page text in `02_ocr_pages/`
- retrieval chunks in `03_chunks/`
- page and chunk indexes in `04_index/`
- concept cards in `05_cards/`
- topic guides in `06_topics/`
- QA-oriented answer scaffolding in `07_qa/`
- ready-to-use summary outputs in `08_outputs/`
- rebuild and maintenance scripts in `scripts/`

## What Is Not Included

- rendered page images in `01_renders/`

This keeps the repository smaller while preserving the actual retrieval value.

## Source PDF

The original source PDF is included in `00_source/original.pdf` for private use inside this private repository version.

## Recommended Usage

1. Start with `08_outputs/ready_for_qa.md`
2. Use `04_index/chapter_map.json` to locate chapter scope
3. Use `04_index/topic_routes.json` for topic routing
4. Use `03_chunks/` and `02_ocr_pages/` for grounded lookup
5. Use `07_qa/answer_playbook.md` to structure final answers

## Key Entry Files

- `04_index/chapter_map.json`
- `04_index/page_map.json`
- `04_index/chunk_index.json`
- `06_topics/chapter_guides.md`
- `07_qa/answer_playbook.md`
- `08_outputs/chapter_summary_pack.md`

## Suggested Share Rules

- Keep the repository private
- Share only with trusted users in your study group or team
- Do not mirror it publicly unless you have explicit permission for the source material
- If you need to rebuild or extend the KB, use the scripts under `scripts/`

## Rebuild Notes

The included scripts support:

- PDF page rendering
- Windows OCR extraction
- chunk/index generation
- enhanced QA-layer generation

See `KNOWLEDGE_BASE_OVERVIEW.md` and `RESUME_INSTRUCTIONS.md` for workflow details.
