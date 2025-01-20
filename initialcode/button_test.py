import RPi.GPIO as GPIO
import time

# Set up GPIO mode
GPIO.setmode(GPIO.BCM)
BUTTON_PIN = 17

# Set up the button pin as input with an internal pull-up resistor
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def button_callback(channel):
    print("Button pressed!")

# Add an event detection on the button pin
GPIO.add_event_detect(BUTTON_PIN, GPIO.FALLING, callback=button_callback, bouncetime=200)

try:
    print("Press the button to test...")
    while True:
        time.sleep(1)  # Keep the script running
except KeyboardInterrupt:
    print("Exiting program")
finally:
    GPIO.cleanup()  # Clean up GPIO on exit
