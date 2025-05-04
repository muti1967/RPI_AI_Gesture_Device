#!/usr/bin/python
# -*- coding:utf-8 -*-

import os
import subprocess

# Always use /home/seniora as the base directory for audio files
SENIORA_BASE = "/home/seniora/RPI_AI_Gesture_Device/finalv/audio_files"
NAV_AUDIO_DIR = os.path.join(SENIORA_BASE, "navaudio")
AUDIO_FILES_DIR = SENIORA_BASE

def play_bootup_sound():
    file_bootup = os.path.join(NAV_AUDIO_DIR, "bootup.mp3")
    if os.path.exists(file_bootup):
        print("Playing bootup sound...")
        try:
            subprocess.run(["ffplay", "-nodisp", "-autoexit", file_bootup],
                           capture_output=True, text=True)
        except Exception as e:
            print(f"Error playing bootup sound: {e}")
    else:
        print("Bootup file not found:", file_bootup)

def play_upload_confirmation():
    file_confirm = os.path.join(NAV_AUDIO_DIR, "upload_conformation.mp3")
    if os.path.exists(file_confirm):
        print("Playing upload confirmation sound...")
        try:
            subprocess.run(["ffplay", "-nodisp", "-autoexit", file_confirm],
                           capture_output=True, text=True)
        except Exception as e:
            print(f"Error playing upload confirmation: {e}")
    else:
        print("Upload confirmation file not found:", file_confirm)

def play_task_audio(task_number):
    task_file_mp3 = os.path.join(AUDIO_FILES_DIR, f"{task_number}.mp3")
    task_file_m4a = os.path.join(AUDIO_FILES_DIR, f"{task_number}.m4a")
    
    if os.path.exists(task_file_mp3):
        print(f"Playing task {task_number} (MP3)")
        try:
            subprocess.run(["ffplay", "-nodisp", "-autoexit", task_file_mp3],
                           capture_output=True, text=True)
        except Exception as e:
            print(f"Error playing task {task_number} (MP3): {e}")
    elif os.path.exists(task_file_m4a):
        print(f"Playing task {task_number} (M4A)")
        try:
            subprocess.run(["ffplay", "-nodisp", "-autoexit", task_file_m4a],
                           capture_output=True, text=True)
        except Exception as e:
            print(f"Error playing task {task_number} (M4A): {e}")
    else:
        print(f"Task {task_number} file not found (MP3 or M4A).")

def play_nav_audio(task_number):
    nav_file_mp3 = os.path.join(NAV_AUDIO_DIR, f"{task_number}.mp3")
    nav_file_m4a = os.path.join(NAV_AUDIO_DIR, f"{task_number}.m4a")
    generic_nav_file = os.path.join(NAV_AUDIO_DIR, "task.mp3")

    if os.path.exists(nav_file_mp3):
        print(f"Playing navigation audio for task {task_number} (MP3)")
        try:
            subprocess.run(["ffplay", "-nodisp", "-autoexit", nav_file_mp3],
                           capture_output=True, text=True)
        except Exception as e:
            print(f"Error playing navigation audio: {e}")
    elif os.path.exists(nav_file_m4a):
        print(f"Playing navigation audio for task {task_number} (M4A)")
        try:
            subprocess.run(["ffplay", "-nodisp", "-autoexit", nav_file_m4a],
                           capture_output=True, text=True)
        except Exception as e:
            print(f"Error playing navigation audio: {e}")
    elif os.path.exists(generic_nav_file):
        print(f"Playing generic navigation audio for task {task_number}")
        try:
            subprocess.run(["ffplay", "-nodisp", "-autoexit", generic_nav_file],
                           capture_output=True, text=True)
        except Exception as e:
            print(f"Error playing generic navigation audio: {e}")
    else:
        print(f"No navigation audio found for task {task_number} (checked: {nav_file_mp3}, {nav_file_m4a}, {generic_nav_file})")

def play_pairing_confirmation():
    pairing_file = os.path.join(NAV_AUDIO_DIR, "pairingconformation.mp3")
    if os.path.exists(pairing_file):
        print("Playing pairing confirmation sound...")
        try:
            subprocess.run(["ffplay", "-nodisp", "-autoexit", pairing_file],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            print(f"Error playing pairing confirmation: {e}")
    else:
        print("Pairing confirmation file not found:", pairing_file)
