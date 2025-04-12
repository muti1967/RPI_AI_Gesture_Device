import os
import threading
from gesture import handle_gesture
from scheduler import schedule_tasks
from audio import play_bootup_sound
from bluetooth import start_bluetooth_agent, remove_paired_devices
from PAJ7620U2 import PAJ7620U2  # Import the PAJ7620U2 class for gesture detection

HOME_DIR = "/home/senior"
BASE_DIR = os.path.join(HOME_DIR, "RPI_AI_Gesture_Device")
INFO_FILE_PATH = os.path.join(BASE_DIR, "finalv/info/info.txt")
AUDIO_FILES_DIR = os.path.join(BASE_DIR, "finalv/audio_files")
NAV_AUDIO_DIR = os.path.join(AUDIO_FILES_DIR, "navaudio")

if __name__ == '__main__':
    print("Starting Gesture Sensor Program...")
    os.makedirs(AUDIO_FILES_DIR, exist_ok=True)
    os.makedirs(NAV_AUDIO_DIR, exist_ok=True)

    # Play the bootup sound
    play_bootup_sound(NAV_AUDIO_DIR)

    # Initialize the gesture sensor
    sensor = PAJ7620U2()
    tasks = []  # Load tasks from info.txt or other source
    current_task = 1

    # Start the scheduler thread
    scheduler_thread = threading.Thread(target=schedule_tasks, args=(tasks, AUDIO_FILES_DIR))
    scheduler_thread.daemon = True
    scheduler_thread.start()

    # Remove previously paired Bluetooth devices and start the Bluetooth agent
    remove_paired_devices()
    start_bluetooth_agent()

    # Main loop to check gestures and handle them
    while True:
        gesture_data = sensor.check_gesture()  # Get gesture data from the sensor
        current_task = handle_gesture(gesture_data, NAV_AUDIO_DIR, current_task, tasks)
