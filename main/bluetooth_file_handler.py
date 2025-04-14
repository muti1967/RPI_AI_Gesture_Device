#!/usr/bin/env python3

import os
import shutil
from config import INFO_FILE_PATH, AUDIO_FILES_DIR

def ensure_dir(path):
    """Ensure the directory exists; create it if not."""
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"Created directory: {path}")

def process_received_files(temp_dir):
    """Process files received via Bluetooth from iPhone"""
    ensure_dir(AUDIO_FILES_DIR)
    ensure_dir(os.path.dirname(INFO_FILE_PATH))
    
    # Find the students_tasks.txt file and audio directory
    tasks_file = None
    audio_dir = None
    
    for item in os.listdir(temp_dir):
        item_path = os.path.join(temp_dir, item)
        if item.lower() == 'students_tasks.txt':
            tasks_file = item_path
        elif os.path.isdir(item_path) and any(f.endswith(('.mp3', '.m4a', '.wav')) 
                                             for f in os.listdir(item_path)):
            audio_dir = item_path

    if not tasks_file:
        raise ValueError("Missing students_tasks.txt in received data")

    process_tasks_file(tasks_file, INFO_FILE_PATH, AUDIO_FILES_DIR)

def process_tasks_file(source_file, dest_info_file, dest_audio_dir):
    """Process the tasks file and move audio files to their destinations"""
    tasks = []  # Will hold tuples: (task_number, original_audio, task_time)
    
    with open(source_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Process each line, skipping student info (first 6 fields)
    for line in lines:
        line = line.strip()
        if not line:
            continue
        parts = [part.strip() for part in line.split(',')]
        if len(parts) <= 6:
            continue
            
        # Process tasks (starting from index 6, every 4 fields is one task)
        i = 6
        while i + 3 < len(parts):
            task_number = parts[i]
            original_audio = parts[i+2]
            task_time = parts[i+3]
            tasks.append((task_number, original_audio, task_time))
            i += 4

    # Write the formatted info.txt file
    with open(dest_info_file, 'w', encoding='utf-8') as fout:
        for task_number, _, task_time in tasks:
            fout.write(f"{task_number},{task_number}.mp3,{task_time}\n")
    print(f"Generated info file at: {dest_info_file}")
    
    # Process audio files
    process_audio_files(tasks, dest_audio_dir)

def process_audio_files(tasks, dest_audio_dir):
    """Process and move audio files for each task"""
    ensure_dir(dest_audio_dir)
    
    for task_number, original_audio, _ in tasks:
        if not original_audio:
            print(f"No audio file provided for task {task_number}")
            continue

        source_path = original_audio if os.path.isabs(original_audio) else \
                     os.path.join(os.getcwd(), original_audio)
                     
        if not os.path.exists(source_path):
            print(f"Audio file not found: {source_path}")
            continue
            
        dest_path = os.path.join(dest_audio_dir, f"{task_number}.mp3")
        
        try:
            if not source_path.lower().endswith('.mp3'):
                convert_to_mp3(source_path, dest_path)
            else:
                shutil.copy2(source_path, dest_path)
            print(f"Processed audio for task {task_number}")
        except Exception as e:
            print(f"Error processing audio for task {task_number}: {e}")

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
