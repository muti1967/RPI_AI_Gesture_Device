import os
import subprocess

def play_audio(file_path):
    if not os.path.exists(file_path):
        print(f"Error: Audio file not found: {file_path}")
        return
    try:
        subprocess.run(["ffplay", "-nodisp", "-autoexit", file_path], capture_output=True, text=True)
        print(f"Playing audio: {file_path}")
    except Exception as e:
        print(f"Error playing audio: {e}")

def play_bootup_sound(nav_audio_dir):
    file_bootup = os.path.join(nav_audio_dir, "bootup.mp3")
    play_audio(file_bootup)

def play_upload_confirmation(nav_audio_dir):
    file_confirm = os.path.join(nav_audio_dir, "upload_conformation.mp3")
    play_audio(file_confirm)
