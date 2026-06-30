# Resume Instructions

If a later chat needs to continue this project, use the files below first:

- `F:\材料科学基础_知识库\04_index\kb_status.json`
- `F:\材料科学基础_知识库\NEXT_STEPS.md`
- `F:\材料科学基础_知识库\scripts\process_batch.ps1`

## Suggested resume command

```powershell
powershell -NoProfile -ExecutionPolicy Bypass `
  -File "F:\材料科学基础_知识库\scripts\process_batch.ps1" `
  -PdfPath "F:\材料科学基础_知识库\00_source\original.pdf" `
  -Root "F:\材料科学基础_知识库" `
  -StartPage <next_start_page> `
  -EndPage <next_end_page>
```

## Resume workflow

1. Read `kb_status.json` to determine the current max processed page.
2. Run the next batch with `process_batch.ps1`.
3. Read `NEXT_STEPS.md` again after the batch finishes.
4. Use `page_map.json` and `03_chunks` to answer content questions.
