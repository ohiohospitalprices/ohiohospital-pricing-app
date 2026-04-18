#!/usr/bin/env node

/**
 * Luetgert TikTok Video Builder
 * Creates a 90-second vertical video from images + audio narration
 * Uses ffmpeg-static and fluent-ffmpeg
 */

const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

// Configuration
const CONFIG = {
  imageFolder: 'C:\\Users\\Owner\\Desktop\\TikTok_Resized',
  audioFile: 'C:\\Users\\Owner\\.openclaw\\media\\inbound\\ElevenLabs_2026_03_26T02_08_07_Bill_Oxley_Documentary_Commen---038bfcd0-bfa5-4032-9d88-eecccc71f3f5.mp3',
  outputVideo: 'C:\\Users\\Owner\\Desktop\\luetgert_video_final.mp4',
  tempFolder: 'C:\\Users\\Owner\\.openclaw\\workspace-openclaw-ai\\temp_video',
  width: 1080,
  height: 1920,
  fps: 30,
  duration: 90
};

// Image sequence with timing
const imageSequence = [
  // Hook (0-10 sec)
  { images: ['download hearse_resized.jpg', 'download prison_resized.jpg'], duration: 10 },
  // Story 1 (10-25 sec)
  { images: ['Frippers-makers_resized.jpg', 'OIP-1716863957_resized.jpg', 'OIP-2706810849_resized.jpg'], duration: 15 },
  // Story 2 (25-45 sec)
  { images: ['OIP-107910903_resized.jpg', 'OIP-1801312799_resized.jpg', 'OIP-2430578495_resized.jpg', 'OIP-2467464917_resized.jpg'], duration: 20 },
  // Story 3 (45-85 sec)
  { images: ['OIP-3281209669_resized.jpg', 'OIP-3373467249_resized.jpg', 'OIP-3464079385_resized.jpg', 'OIP-3505066323_resized.jpg', 'OIP-4076698131_resized.jpg'], duration: 40 },
  // Close (85-90 sec)
  { images: ['download 333_resized.jpg'], duration: 5 }
];

// Create concat demuxer file for FFmpeg
function createConcatFile() {
  console.log('Creating image sequence...');
  
  if (!fs.existsSync(CONFIG.tempFolder)) {
    fs.mkdirSync(CONFIG.tempFolder, { recursive: true });
  }

  let concatContent = '';
  let totalFrames = 0;

  for (const segment of imageSequence) {
    const timePerImage = segment.duration / segment.images.length;
    const framesPerImage = Math.ceil(timePerImage * CONFIG.fps);

    for (const img of segment.images) {
      const imgPath = path.join(CONFIG.imageFolder, img);
      if (fs.existsSync(imgPath)) {
        concatContent += `file '${imgPath}'\n`;
        concatContent += `duration ${timePerImage}\n`;
        totalFrames += framesPerImage;
      }
    }
  }

  const concatFile = path.join(CONFIG.tempFolder, 'concat.txt');
  fs.writeFileSync(concatFile, concatContent);
  
  console.log(`✓ Created concat file with image sequence`);
  return concatFile;
}

// Run FFmpeg command
function runFFmpeg(args, description) {
  return new Promise((resolve, reject) => {
    console.log(`${description}...`);
    
    const ffmpeg = spawn('ffmpeg', args, {
      stdio: ['pipe', 'pipe', 'pipe']
    });

    let stderr = '';
    ffmpeg.stderr.on('data', (data) => {
      stderr += data.toString();
      process.stderr.write('.');
    });

    ffmpeg.on('close', (code) => {
      if (code === 0) {
        console.log(`\n✓ ${description} completed`);
        resolve();
      } else {
        console.log(`\n✗ ${description} failed with code ${code}`);
        reject(new Error(`FFmpeg failed: ${stderr}`));
      }
    });

    ffmpeg.on('error', (err) => {
      reject(err);
    });
  });
}

// Main build function
async function buildVideo() {
  console.log('═'.repeat(60));
  console.log('LUETGERT TIKTOK VIDEO BUILDER');
  console.log('═'.repeat(60));
  console.log();

  try {
    // Verify files exist
    if (!fs.existsSync(CONFIG.imageFolder)) {
      throw new Error(`Image folder not found: ${CONFIG.imageFolder}`);
    }
    if (!fs.existsSync(CONFIG.audioFile)) {
      throw new Error(`Audio file not found: ${CONFIG.audioFile}`);
    }

    console.log(`✓ Image folder: ${CONFIG.imageFolder}`);
    console.log(`✓ Audio file found`);
    console.log();

    // Create concat file
    const concatFile = createConcatFile();

    // Step 1: Build video from images (without audio)
    const videoNoAudio = path.join(CONFIG.tempFolder, 'video_no_audio.mp4');
    const ffmpegArgs1 = [
      '-f', 'concat',
      '-safe', '0',
      '-i', concatFile,
      '-framerate', CONFIG.fps.toString(),
      '-pix_fmt', 'yuv420p',
      '-y',
      videoNoAudio
    ];

    await runFFmpeg(ffmpegArgs1, 'Building video from images');

    // Step 2: Merge video with audio
    const ffmpegArgs2 = [
      '-i', videoNoAudio,
      '-i', CONFIG.audioFile,
      '-c:v', 'copy',
      '-c:a', 'aac',
      '-shortest',
      '-y',
      CONFIG.outputVideo
    ];

    await runFFmpeg(ffmpegArgs2, 'Adding audio to video');

    console.log();
    console.log('═'.repeat(60));
    console.log('✓ VIDEO SUCCESSFULLY CREATED!');
    console.log('═'.repeat(60));
    console.log(`Location: ${CONFIG.outputVideo}`);
    console.log(`Format: 1080x1920 (TikTok vertical)`);
    console.log(`Duration: ~90 seconds`);
    console.log();

    return true;

  } catch (error) {
    console.error('✗ Error:', error.message);
    return false;
  }
}

// Run the builder
buildVideo().then(success => {
  process.exit(success ? 0 : 1);
});
