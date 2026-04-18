# Build Luetgert TikTok Video
# Uses FFmpeg to create 90-second vertical video from images + audio

$ffmpegPath = "C:\ffmpeg-bin\ffmpeg-master-latest-win64-gpl\bin\ffmpeg.exe"
$ffprobePath = "C:\ffmpeg-bin\ffmpeg-master-latest-win64-gpl\bin\ffprobe.exe"

$imageFolder = "C:\Users\Owner\Desktop\TikTok_Resized"
$audioFile = "C:\Users\Owner\.openclaw\media\inbound\ElevenLabs_2026_03_26T02_08_07_Bill_Oxley_Documentary_Commen---038bfcd0-bfa5-4032-9d88-eecccc71f3f5.mp3"
$tempFolder = "C:\Users\Owner\.openclaw\workspace-openclaw-ai\temp_luetgert"
$outputVideo = "C:\Users\Owner\Desktop\luetgert_video_final.mp4"

# Image sequence with timing
$imageSequence = @(
    @{ name = "download hearse_resized.jpg"; duration = 5 },
    @{ name = "download prison_resized.jpg"; duration = 5 },
    @{ name = "Frippers-makers_resized.jpg"; duration = 5 },
    @{ name = "OIP-1716863957_resized.jpg"; duration = 5 },
    @{ name = "OIP-2706810849_resized.jpg"; duration = 5 },
    @{ name = "OIP-107910903_resized.jpg"; duration = 5 },
    @{ name = "OIP-1801312799_resized.jpg"; duration = 5 },
    @{ name = "OIP-2430578495_resized.jpg"; duration = 5 },
    @{ name = "OIP-2467464917_resized.jpg"; duration = 5 },
    @{ name = "OIP-3281209669_resized.jpg"; duration = 8 },
    @{ name = "OIP-3373467249_resized.jpg"; duration = 8 },
    @{ name = "OIP-3464079385_resized.jpg"; duration = 8 },
    @{ name = "OIP-3505066323_resized.jpg"; duration = 8 },
    @{ name = "OIP-4076698131_resized.jpg"; duration = 8 },
    @{ name = "download 333_resized.jpg"; duration = 5 }
)

Write-Host "════════════════════════════════════════════"
Write-Host "  LUETGERT VIDEO BUILDER"
Write-Host "════════════════════════════════════════════"
Write-Host ""

# Verify files
if (-not (Test-Path $ffmpegPath)) {
    Write-Host "✗ FFmpeg not found at: $ffmpegPath"
    exit 1
}

if (-not (Test-Path $imageFolder)) {
    Write-Host "✗ Image folder not found"
    exit 1
}

if (-not (Test-Path $audioFile)) {
    Write-Host "✗ Audio file not found"
    exit 1
}

Write-Host "✓ FFmpeg: Found"
Write-Host "✓ Images: Found ($imageFolder)"
Write-Host "✓ Audio: Found"
Write-Host ""

# Create temp folder
if (-not (Test-Path $tempFolder)) {
    New-Item -ItemType Directory -Path $tempFolder -Force | Out-Null
}

# Create concat demuxer file
Write-Host "Creating image sequence..."
$concatFile = Join-Path $tempFolder "concat.txt"
$concatContent = ""

foreach ($item in $imageSequence) {
    $imgPath = Join-Path $imageFolder $item.name
    if (Test-Path $imgPath) {
        $concatContent += "file '$imgPath'`n"
        $concatContent += "duration $($item.duration)`n"
    } else {
        Write-Host "⚠ Missing: $($item.name)"
    }
}

Set-Content -Path $concatFile -Value $concatContent -Force
Write-Host "✓ Image sequence created ($(($concatContent -split "`n").Count / 2) images)"
Write-Host ""

# Build video from images
Write-Host "Building video from images..."
$videoNoAudio = Join-Path $tempFolder "video_no_audio.mp4"

$ffmpegArgs = @(
    "-f", "concat",
    "-safe", "0",
    "-i", $concatFile,
    "-framerate", "30",
    "-pix_fmt", "yuv420p",
    "-y",
    $videoNoAudio
)

& $ffmpegPath $ffmpegArgs 2>&1 | ForEach-Object { 
    if ($_ -match "error|Error") { Write-Host "! $_" } 
}

if (Test-Path $videoNoAudio) {
    Write-Host "✓ Video created (no audio)"
} else {
    Write-Host "✗ Video creation failed"
    exit 1
}

Write-Host ""
Write-Host "Adding audio..."

$ffmpegArgs2 = @(
    "-i", $videoNoAudio,
    "-i", $audioFile,
    "-c:v", "copy",
    "-c:a", "aac",
    "-shortest",
    "-y",
    $outputVideo
)

& $ffmpegPath $ffmpegArgs2 2>&1 | ForEach-Object { 
    if ($_ -match "error|Error") { Write-Host "! $_" } 
}

Write-Host ""
if (Test-Path $outputVideo) {
    $fileSize = (Get-Item $outputVideo).Length / 1MB
    Write-Host "════════════════════════════════════════════"
    Write-Host "✓ VIDEO SUCCESSFULLY CREATED!"
    Write-Host "════════════════════════════════════════════"
    Write-Host "Location: $outputVideo"
    Write-Host "Size: $([Math]::Round($fileSize, 2)) MB"
    Write-Host "Format: 1080x1920 (TikTok vertical)"
    Write-Host "Duration: 90 seconds"
    Write-Host ""
    Write-Host "Ready to upload to TikTok! 🎸"
} else {
    Write-Host "✗ Final video creation failed"
    exit 1
}
