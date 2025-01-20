import RPi.GPIO as GPIO
import time

# GPIO settings
BUTTON_GPIO = 17  # BUTTON is connected to GPIO17 (BCM)

def button_callback(channel):
    print("Button was pressed!")

# Set up GPIO
GPIO.setmode(GPIO.BCM)  # Use BCM pin numbering
GPIO.setup(BUTTON_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Set GPIO17 as input with pull-up resistor

# Add an event listener for the button
GPIO.add_event_detect(BUTTON_GPIO, GPIO.FALLING, callback=button_callback, bouncetime=300)

print("Waiting for button press... Press CTRL+C to exit.")

try:
    while True:
        # Keep the program running
        time.sleep(1)
except KeyboardInterrupt:
    print("Exiting program...")
finally:
    GPIO.cleanup()  # Clean up GPIO on exit
