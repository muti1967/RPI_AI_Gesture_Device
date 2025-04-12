import schedule
import time
from audio import play_audio

def play_task_one_two(audio_files_dir):
    play_audio(os.path.join(audio_files_dir, "1.mp3"))
    play_audio(os.path.join(audio_files_dir, "2.mp3"))

def schedule_tasks(tasks, audio_files_dir):
    for task in tasks:
        schedule.every().day.at(task.play_time).do(play_audio, task.audio_file)
    schedule.every(30).seconds.do(play_task_one_two, audio_files_dir)
    while True:
        schedule.run_pending()
        time.sleep(1)
