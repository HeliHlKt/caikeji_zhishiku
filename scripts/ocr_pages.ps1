param(
  [Parameter(Mandatory = $true)]
  [string]$Root,

  [Parameter(Mandatory = $true)]
  [int]$StartPage,

  [Parameter(Mandatory = $true)]
  [int]$EndPage
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Add-Type -AssemblyName System.Runtime.WindowsRuntime

function Await-AsyncResult {
  param(
    [Parameter(Mandatory = $true)]
    [object]$Operation,

    [Parameter(Mandatory = $true)]
    [type]$ResultType
  )

  $method = [System.WindowsRuntimeSystemExtensions].GetMethods() |
    Where-Object {
      $_.Name -eq "AsTask" -and
      $_.IsGenericMethod -and
      @($_.GetParameters()).Count -eq 1
    } |
    Select-Object -First 1

  $generic = $method.MakeGenericMethod($ResultType)
  $task = $generic.Invoke($null, @($Operation))
  return $task.Result
}

$null = [Windows.Storage.StorageFile, Windows.Storage, ContentType = WindowsRuntime]
$null = [Windows.Storage.Streams.IRandomAccessStream, Windows.Storage.Streams, ContentType = WindowsRuntime]
$null = [Windows.Graphics.Imaging.BitmapDecoder, Windows.Foundation, ContentType = WindowsRuntime]
$null = [Windows.Graphics.Imaging.SoftwareBitmap, Windows.Foundation, ContentType = WindowsRuntime]
$null = [Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType = WindowsRuntime]
$null = [Windows.Media.Ocr.OcrResult, Windows.Foundation, ContentType = WindowsRuntime]

$renderDir = Join-Path $Root "01_renders"
$ocrDir = Join-Path $Root "02_ocr_pages"
$indexDir = Join-Path $Root "04_index"
New-Item -ItemType Directory -Path $ocrDir -Force | Out-Null
New-Item -ItemType Directory -Path $indexDir -Force | Out-Null

$engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
if ($null -eq $engine) {
  throw "Windows OCR engine is not available for current user profile languages."
}

$manifest = @()

for ($page = $StartPage; $page -le $EndPage; $page++) {
  $imageName = "page_{0:d4}.png" -f $page
  $imagePath = Join-Path $renderDir $imageName
  if (-not (Test-Path $imagePath)) {
    Write-Warning "Skip page $page because render is missing: $imagePath"
    continue
  }

  $file = Await-AsyncResult ([Windows.Storage.StorageFile]::GetFileFromPathAsync($imagePath)) ([Windows.Storage.StorageFile])
  $stream = Await-AsyncResult ($file.OpenAsync([Windows.Storage.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])
  $decoder = Await-AsyncResult ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)) ([Windows.Graphics.Imaging.BitmapDecoder])
  $bitmap = Await-AsyncResult ($decoder.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
  $result = Await-AsyncResult ($engine.RecognizeAsync($bitmap)) ([Windows.Media.Ocr.OcrResult])

  $textPath = Join-Path $ocrDir ("page_{0:d4}.txt" -f $page)
  [System.IO.File]::WriteAllText($textPath, $result.Text, [System.Text.Encoding]::UTF8)

  $manifest += [pscustomobject]@{
    page = $page
    image = $imagePath
    text = $textPath
    text_length = $result.Text.Length
    line_count = @($result.Lines).Count
  }

  Write-Output ("OCR page {0} complete, chars={1}" -f $page, $result.Text.Length)
}

$manifestPath = Join-Path $indexDir ("ocr_manifest_{0:d4}_{1:d4}.json" -f $StartPage, $EndPage)
$manifest | ConvertTo-Json -Depth 4 | Set-Content -Path $manifestPath -Encoding UTF8
Write-Output "OCR manifest saved to $manifestPath"
