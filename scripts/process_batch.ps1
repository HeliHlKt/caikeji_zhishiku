param(
  [Parameter(Mandatory = $true)]
  [string]$PdfPath,

  [Parameter(Mandatory = $true)]
  [string]$Root,

  [Parameter(Mandatory = $true)]
  [int]$StartPage,

  [Parameter(Mandatory = $true)]
  [int]$EndPage,

  [string]$PythonExe = "C:\Users\AAA\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe",

  [string]$SourceName = "材料科学基础  修订版_清华教材_清晰版.pdf"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$renderScript = Join-Path $scriptDir "render_pdf_pages.py"
$ocrScript = Join-Path $scriptDir "ocr_pages.ps1"
$buildScript = Join-Path $scriptDir "build_kb.py"

& $PythonExe $renderScript --pdf $PdfPath --out-root $Root --start $StartPage --end $EndPage
powershell -NoProfile -ExecutionPolicy Bypass -File $ocrScript -Root $Root -StartPage $StartPage -EndPage $EndPage
& $PythonExe $buildScript --root $Root --source-name $SourceName
