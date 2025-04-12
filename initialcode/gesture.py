from audio import play_audio
from bluetooth import enable_bluetooth, disable_bluetooth

def handle_gesture(gesture_data, nav_audio_dir, current_task, tasks):
    if gesture_data == 0x01:  # PAJ_UP
        print("Gesture UP detected.")
        disable_bluetooth()
        play_audio(os.path.join(nav_audio_dir, "bluetoothoff.mp3"))
    elif gesture_data == 0x02:  # PAJ_DOWN
        print("Gesture DOWN detected.")
        play_audio("/home/senior/RPI_AI_Gesture_Device/audio_test.mp3")
    elif gesture_data == 0x04:  # PAJ_LEFT
        print("Gesture LEFT detected.")
        current_task = max(1, current_task - 1)
        if tasks and 1 <= current_task <= len(tasks):
            tasks[current_task - 1].play_nav_audio()
    elif gesture_data == 0x08:  # PAJ_RIGHT
        print("Gesture RIGHT detected.")
        current_task = min(len(tasks), current_task + 1)
        if tasks and 1 <= current_task <= len(tasks):
            tasks[current_task - 1].play_nav_audio()
    elif gesture_data == 0x10:  # PAJ_FORWARD
        print("Gesture FORWARD detected.")
        if tasks and 1 <= current_task <= len(tasks):
            play_audio(tasks[current_task - 1].audio_file)
    elif gesture_data == 0x20:  # PAJ_BACKWARD
        print("Gesture BACKWARD detected.")
        enable_bluetooth()
        play_audio(os.path.join(nav_audio_dir, "bluetoothon.mp3"))
    return current_task
