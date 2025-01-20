import RPi.GPIO as GPIO
import time

BUTTON_GPIO = 17

def button_callback(channel):
    print("Button Press Detected!")

GPIO.cleanup()  # Clear any previous setup
GPIO.setmode(GPIO.BCM)  # Use BCM pin numbering
GPIO.setup(BUTTON_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Configure pin as input with pull-up resistor

try:
    GPIO.add_event_detect(BUTTON_GPIO, GPIO.FALLING, callback=button_callback, bouncetime=300)
    print("Waiting for button press...")
    while True:
        time.sleep(1)  # Keep the script running
except KeyboardInterrupt:
    print("Exiting...")
finally:
    GPIO.cleanup()
