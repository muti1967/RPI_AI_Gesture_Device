import RPi.GPIO as GPIO
import time

# Set up GPIO mode
GPIO.setmode(GPIO.BCM)

# Define the GPIO pin connected to the button
BUTTON_PIN = 17  # Replace with the correct GPIO pin number if different

# Set up the button pin as input with an internal pull-up resistor
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

print("Testing button. Press Ctrl+C to exit.")

try:
    while True:
        # Read the button state
        button_state = GPIO.input(BUTTON_PIN)
        if button_state == GPIO.LOW:  # Button pressed (LOW because of pull-up)
            print("Button pressed!")
        else:  # Button not pressed
            print("Button not pressed")
        time.sleep(0.1)  # Delay to avoid flooding the terminal
except KeyboardInterrupt:
    print("\nExiting test.")
finally:
    GPIO.cleanup()  # Clean up GPIO settings
