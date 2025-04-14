#!/usr/bin/env python3

import os
import shutil
from config import INFO_FILE_PATH, AUDIO_FILES_DIR

def process_received_files(temp_dir):
    """Process files received via Bluetooth from iPhone"""
    
    # Find the info file (should be named info.txt or similar)
    info_file = None
    audio_dir = None
    
    for item in os.listdir(temp_dir):
        item_path = os.path.join(temp_dir, item)
        if item.lower() == 'info.txt':
            info_file = item_path
        elif os.path.isdir(item_path) and any(f.endswith(('.mp3', '.m4a', '.wav')) 
                                             for f in os.listdir(item_path)):
            audio_dir = item_path

    if not info_file or not audio_dir:
        raise ValueError("Missing required files in received data")

    # Process the info file and move audio files
    tasks = generate_info_file(info_file, INFO_FILE_PATH)
    move_audio_files(tasks, audio_dir, AUDIO_FILES_DIR)

def generate_info_file(source_file, destination_info_file):
    """Generate standardized info file from received file"""
    os.makedirs(os.path.dirname(destination_info_file), exist_ok=True)
    
    tasks = []
    with open(source_file, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(",")
            if len(parts) >= 3:
                task_number = parts[0].strip()
                task_time = parts[2].strip()
                tasks.append((task_number, task_time))

    with open(destination_info_file, "w") as out_f:
        for task_number, task_time in tasks:
            out_f.write(f"{task_number},{task_number}.mp3,{task_time}\n")
    
    return tasks

def move_audio_files(tasks, source_dir, destination_audio_dir):
    """Move and rename received audio files"""
    os.makedirs(destination_audio_dir, exist_ok=True)
    
    audio_files = [f for f in sorted(os.listdir(source_dir)) 
                  if f.lower().endswith(('.mp3', '.m4a', '.wav'))]

    if len(audio_files) < len(tasks):
        print("Warning: fewer audio files than tasks")

    # Move and rename files according to task numbers
    for i, (task_number, _) in enumerate(tasks):
        if i < len(audio_files):
            source_file = os.path.join(source_dir, audio_files[i])
            dest_file = os.path.join(destination_audio_dir, f"{task_number}.mp3")
            
            # Convert to mp3 if needed
            if not source_file.lower().endswith('.mp3'):
                convert_to_mp3(source_file, dest_file)
            else:
                shutil.copy2(source_file, dest_file)
            print(f"Processed audio file for task {task_number}")

def convert_to_mp3(source_file, dest_file):
    """Convert audio file to mp3 format using ffmpeg"""
    try:
        import subprocess
        subprocess.run([
            'ffmpeg', '-i', source_file,
            '-codec:a', 'libmp3lame', '-qscale:a', '2',
            dest_file
        ], check=True, capture_output=True)
    except Exception as e:
        print(f"Error converting file to mp3: {e}")
        # Fallback: just copy the file
        shutil.copy2(source_file, dest_file)
