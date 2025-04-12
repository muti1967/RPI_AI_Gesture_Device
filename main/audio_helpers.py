#!/usr/bin/python
# -*- coding:utf-8 -*-

import os
import subprocess
from config import NAV_AUDIO_DIR

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
