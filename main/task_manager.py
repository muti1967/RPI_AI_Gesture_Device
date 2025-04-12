#!/usr/bin/python
# -*- coding:utf-8 -*-

import os
import time
import schedule
import subprocess
from watchdog.events import FileSystemEventHandler
from config import AUDIO_FILES_DIR, INFO_FILE_PATH, NAV_AUDIO_DIR

class Task:
    def __init__(self, task_number, audio_file, play_time):
        self.task_number = task_number
        self.audio_file = os.path.join(AUDIO_FILES_DIR, audio_file)  # Full path
        self.play_time = play_time
        self.completed = False

    def play_nav_audio(self):
        nav_file = os.path.join(NAV_AUDIO_DIR, f"{self.task_number}.mp3")
        if os.path.exists(nav_file):
            try:
                subprocess.run(["ffplay", "-nodisp", "-autoexit", nav_file],
                               capture_output=True, text=True)
            except Exception as e:
                print(f"Error playing navigation audio: {e}")

class InfoFileHandler(FileSystemEventHandler):
    def __init__(self, sensor):
        self.sensor = sensor
        self.last_modified = 0

    def on_modified(self, event):
        if event.src_path == INFO_FILE_PATH:
            current_time = time.time()
            if current_time - self.last_modified > 1:
                print("Info file changed, reloading tasks...")
                self.sensor.tasks = read_task_info()
                schedule.clear()
                for task in self.sensor.tasks:
                    schedule.every().day.at(task.play_time).do(play_scheduled_audio, task)
                # Schedule the task one-two playback every minute.
                schedule.every(0.5).minute.do(play_task_one_two)
                self.last_modified = current_time

def read_task_info():
    tasks = []
    try:
        with open(INFO_FILE_PATH, 'r') as file:
            for line in file:
                line = line.strip()
                if line:
                    task_number, audio_file, play_time = line.split(',')
                    audio_path = os.path.join(AUDIO_FILES_DIR, audio_file)
                    if not os.path.exists(audio_path):
                        print(f"Warning: Audio file not found: {audio_path}")
                    tasks.append(Task(int(task_number), audio_file, play_time))
        if len(tasks) < 9:
            print("Updating info.txt to include all 9 tasks...")
            with open(INFO_FILE_PATH, 'w') as file:
                for i in range(1, 10):
                    file.write(f"{i},{i}.mp3,09:00\n")
            tasks = []
            with open(INFO_FILE_PATH, 'r') as file:
                for line in file:
                    line = line.strip()
                    if line:
                        task_number, audio_file, play_time = line.split(',')
                        tasks.append(Task(int(task_number), audio_file, play_time))
        print(f"Loaded {len(tasks)} tasks from info.txt")
        return tasks
    except FileNotFoundError:
        print(f"{INFO_FILE_PATH} not found. Creating default file with 9 tasks...")
        os.makedirs(os.path.dirname(INFO_FILE_PATH), exist_ok=True)
        with open(INFO_FILE_PATH, 'w') as file:
            for i in range(1, 10):
                file.write(f"{i},{i}.mp3,09:00\n")
        return read_task_info()
    except Exception as e:
        print(f"Error reading {INFO_FILE_PATH}: {e}")
        return []

def play_scheduled_audio(task):
    if not task.completed:
        print(f"Playing task {task.task_number}: {task.audio_file}")
        if not os.path.exists(task.audio_file):
            print(f"Error: Audio file not found: {task.audio_file}")
            return
        file_ext = os.path.splitext(task.audio_file)[1].lower()
        print(f"Playing audio with ffplay... ({file_ext})")
        result = subprocess.run(["ffplay", "-nodisp", "-autoexit", task.audio_file],
                                capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error playing audio with ffplay: {result.stderr}")
            print("Ensure:")
            print("1. ffplay is installed (sudo apt-get install ffmpeg)")
            print("2. The audio system is configured")
            print("3. The file format is supported")

def play_task_one_two():
    file1 = os.path.join(AUDIO_FILES_DIR, "1.mp3")
    file2 = os.path.join(AUDIO_FILES_DIR, "2.mp3")
    if os.path.exists(file1):
        print("Playing Task 1 (1.mp3)")
        try:
            subprocess.run(["ffplay", "-nodisp", "-autoexit", file1],
                           capture_output=True, text=True)
        except Exception as e:
            print(f"Error playing Task 1: {e}")
    else:
        print("Task 1 file not found:", file1)
    if os.path.exists(file2):
        print("Playing Task 2 (2.mp3)")
        try:
            subprocess.run(["ffplay", "-nodisp", "-autoexit", file2],
                           capture_output=True, text=True)
        except Exception as e:
            print(f"Error playing Task 2: {e}")
    else:
        print("Task 2 file not found:", file2)

def schedule_tasks(tasks):
    for task in tasks:
        schedule.every().day.at(task.play_time).do(play_scheduled_audio, task)
    # Update interval to run every 30 seconds
    schedule.every(30).seconds.do(play_task_one_two)
    while True:
        schedule.run_pending()
        time.sleep(1)
