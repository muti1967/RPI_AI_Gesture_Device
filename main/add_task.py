#!/usr/bin/python
# -*- coding:utf-8 -*-

import os
import subprocess
import time
from config import INFO_FILE_PATH, AUDIO_FILES_DIR

def get_next_task_number():
    """Get the next available task number from info.txt"""
    if not os.path.exists(INFO_FILE_PATH):
        return 1
        
    try:
        with open(INFO_FILE_PATH, 'r') as f:
            lines = f.readlines()
            if not lines:
                return 1
            # Get last line and extract task number
            last_line = lines[-1].strip()
            task_num = int(last_line.split(',')[0])
            return task_num + 1
    except Exception as e:
        print(f"Error reading info.txt: {e}")
        return 1

def add_task(time="15:00", duration=4):
    """Record a new task and add it to info.txt"""
    task_number = get_next_task_number()
    audio_file = f"{task_number}.mp3"
    audio_path = os.path.join(AUDIO_FILES_DIR, audio_file)
    
    print(f"\nRecording new task {task_number}")
    print(f"Recording for {duration} seconds...")
    
    try:
        # Record audio for specified duration using arecord
        process = subprocess.Popen([
            'arecord', '-f', 'cd', '-t', 'wav', '-d', str(duration), '-'
        ], stdout=subprocess.PIPE)
        
        subprocess.run([
            'ffmpeg', '-i', '-', '-acodec', 'libmp3lame', '-ab', '192k',
            audio_path
        ], stdin=process.stdout)
        
        # Add task to info.txt
        os.makedirs(os.path.dirname(INFO_FILE_PATH), exist_ok=True)
        with open(INFO_FILE_PATH, 'a') as f:
            f.write(f"{task_number},{audio_file},{time}\n")
            
        print(f"\nTask {task_number} recorded and saved!")
        return task_number
        
    except Exception as e:
        print(f"Error adding task: {e}")
        if os.path.exists(audio_path):
            os.remove(audio_path)
        return None

if __name__ == "__main__":
    add_task()
