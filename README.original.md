# 材料科学基础知识库工作台

这个工作台用于把 `材料科学基础  修订版_清华教材_清晰版.pdf` 转成一个可检索、可追溯、可持续追加的本地知识库。

## 流程

1. `render_pdf_pages.py`
   - 把 PDF 指定页范围渲染成 PNG。
2. `ocr_pages.ps1`
   - 使用 Windows 自带 OCR 识别 PNG，输出逐页文本与清单。
3. `build_kb.py`
   - 读取 OCR 文本，生成分块、术语候选、主题索引、页码映射。

## 默认知识库目录

`F:\材料科学基础_知识库`

## 推荐执行顺序

```powershell
& "C:\Users\AAA\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" `
  "C:\Users\AAA\Downloads\kb_workbench\scripts\render_pdf_pages.py" `
  --pdf "C:\Users\AAA\Downloads\材料科学基础  修订版_清华教材_清晰版.pdf" `
  --out-root "F:\材料科学基础_知识库" `
  --start 1 --end 20

powershell -NoProfile -ExecutionPolicy Bypass `
  -File "C:\Users\AAA\Downloads\kb_workbench\scripts\ocr_pages.ps1" `
  -Root "F:\材料科学基础_知识库" -StartPage 1 -EndPage 20

& "C:\Users\AAA\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" `
  "C:\Users\AAA\Downloads\kb_workbench\scripts\build_kb.py" `
  --root "F:\材料科学基础_知识库" `
  --source-name "材料科学基础  修订版_清华教材_清晰版.pdf"
```

## 目录说明

- `00_source`：原始 PDF 与来源说明。
- `01_renders`：逐页渲染的 PNG。
- `02_ocr_pages`：逐页 OCR 文本。
- `03_chunks`：适合检索的知识块。
- `04_index`：索引文件与清单。
- `05_cards`：术语卡和概念卡。
- `06_topics`：后续专题整理。
- `07_qa`：沉淀的问答。
- `08_outputs`：最终输出的笔记、讲义、摘要。
