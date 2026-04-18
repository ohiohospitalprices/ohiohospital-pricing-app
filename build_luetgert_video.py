#!/usr/bin/env python3
"""
Luetgert TikTok Video Builder
Sequences images with audio narration to create a 90-second vertical video
"""

import os
import sys
from pathlib import Path
from PIL import Image
import subprocess
import json

# Configuration
IMAGE_FOLDER = r"C:\Users\Owner\Desktop\TikTok_Resized"
AUDIO_FILE = r"C:\Users\Owner\.openclaw\media\inbound\ElevenLabs_2026_03_26T02_08_07_Bill_Oxley_Documentary_Commen---038bfcd0-bfa5-4032-9d88-eecccc71f3f5.mp3"
OUTPUT_VIDEO = r"C:\Users\Owner\Desktop\luetgert_video_final.mp4"
TEMP_FOLDER = r"C:\Users\Owner\.openclaw\workspace-openclaw-ai\temp_video_build"

# Video specs
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
FPS = 30
DURATION = 90  # seconds

# Image sequence timing (in seconds)
IMAGE_SEQUENCE = [
    # Hook (0-10 sec): Mysterious opening
    {"images": ["download hearse_resized.jpg", "download prison_resized.jpg"], "duration": 5},
    
    # Story Part 1 (10-25 sec): Who was Adolph
    {"images": ["Frippers-makers_resized.jpg", "OIP-1716863957_resized.jpg", "OIP-2706810849_resized.jpg"], "duration": 15},
    
    # Story Part 2 (25-45 sec): The discovery
    {"images": ["OIP-107910903_resized.jpg", "OIP-1801312799_resized.jpg", "OIP-2430578495_resized.jpg", "OIP-2467464917_resized.jpg"], "duration": 20},
    
    # Story Part 3 (45-85 sec): Justice
    {"images": ["OIP-3281209669_resized.jpg", "OIP-3373467249_resized.jpg", "OIP-3464079385_resized.jpg", "OIP-3505066323_resized.jpg", "OIP-4076698131_resized.jpg"], "duration": 40},
    
    # Close (85-90 sec): Call to action
    {"images": ["download 333_resized.jpg"], "duration": 5},
]

def create_temp_folder():
    """Create temporary working folder"""
    Path(TEMP_FOLDER).mkdir(parents=True, exist_ok=True)
    print(f"✓ Created temp folder: {TEMP_FOLDER}")

def get_audio_duration():
    """Get duration of audio file in seconds"""
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', 
             '-of', 'default=noprint_wrappers=1:nokey=1:noprint_wrappers=1', 
             AUDIO_FILE],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            return float(result.stdout.strip())
    except:
        pass
    return DURATION

def create_image_list():
    """Create list of images with timing for video"""
    image_list = []
    current_time = 0
    frame_count = 0
    
    for segment in IMAGE_SEQUENCE:
        images = segment.get("images", [])
        duration = segment.get("duration", 5)
        time_per_image = duration / len(images) if images else duration
        
        for img in images:
            img_path = os.path.join(IMAGE_FOLDER, img)
            if os.path.exists(img_path):
                frames_for_image = int(time_per_image * FPS)
                for _ in range(frames_for_image):
                    image_list.append(img_path)
                    frame_count += 1
    
    print(f"✓ Created image sequence: {frame_count} frames")
    return image_list

def build_video_with_ffmpeg(image_list):
    """Build video using FFmpeg"""
    # Create intermediate video from images
    concat_file = os.path.join(TEMP_FOLDER, "concat.txt")
    
    # Write concat demuxer file
    with open(concat_file, 'w') as f:
        for img_path in image_list:
            f.write(f"file '{img_path}'\n")
            f.write(f"duration {1/FPS}\n")  # Each frame is 1/30 of a second
    
    print(f"✓ Created concat file with {len(image_list)} frames")
    
    # Build video without audio first
    video_no_audio = os.path.join(TEMP_FOLDER, "video_no_audio.mp4")
    
    cmd_video = [
        'ffmpeg',
        '-f', 'concat',
        '-safe', '0',
        '-i', concat_file,
        '-framerate', str(FPS),
        '-pix_fmt', 'yuv420p',
        '-y',
        video_no_audio
    ]
    
    print("Building video from images...")
    result = subprocess.run(cmd_video, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"✗ Video build failed: {result.stderr}")
        return False
    
    print(f"✓ Video created (no audio): {video_no_audio}")
    
    # Add audio to video
    cmd_final = [
        'ffmpeg',
        '-i', video_no_audio,
        '-i', AUDIO_FILE,
        '-c:v', 'copy',
        '-c:a', 'aac',
        '-shortest',
        '-y',
        OUTPUT_VIDEO
    ]
    
    print("Adding audio to video...")
    result = subprocess.run(cmd_final, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"✗ Audio merge failed: {result.stderr}")
        return False
    
    print(f"✓ Final video created: {OUTPUT_VIDEO}")
    return True

def main():
    print("=" * 60)
    print("LUETGERT VIDEO BUILDER")
    print("=" * 60)
    
    # Check files exist
    if not os.path.exists(IMAGE_FOLDER):
        print(f"✗ Image folder not found: {IMAGE_FOLDER}")
        return False
    
    if not os.path.exists(AUDIO_FILE):
        print(f"✗ Audio file not found: {AUDIO_FILE}")
        return False
    
    print(f"✓ Image folder: {IMAGE_FOLDER}")
    print(f"✓ Audio file: {AUDIO_FILE}")
    print(f"✓ Output: {OUTPUT_VIDEO}")
    print()
    
    # Create temp folder
    create_temp_folder()
    
    # Create image sequence
    image_list = create_image_list()
    
    if not image_list:
        print("✗ No images found!")
        return False
    
    # Build video with FFmpeg
    success = build_video_with_ffmpeg(image_list)
    
    if success:
        print()
        print("=" * 60)
        print("✓ VIDEO SUCCESSFULLY CREATED!")
        print("=" * 60)
        print(f"Location: {OUTPUT_VIDEO}")
        print(f"Format: 1080x1920 (TikTok vertical)")
        print(f"Duration: ~90 seconds")
        print()
        return True
    else:
        print("✗ Video build failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
