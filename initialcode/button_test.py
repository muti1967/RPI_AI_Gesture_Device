import RPi.GPIO as GPIO
import time

# Set up GPIO mode
GPIO.setmode(GPIO.BCM)

# Define the GPIO pin connected to the button
BUTTON_PIN = 17  # Replace with the correct GPIO pin number if different

# Set up the button pin as input with an internal pull-up resistor
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def enter_pairing_mode():
    print("Entering Bluetooth Pairing Mode")

    # Simulate LED blinking
    def blink_led():
        for _ in range(6):  # Blink for 3 seconds
            print("LED ON")
            time.sleep(0.5)
            print("LED OFF")
            time.sleep(0.5)
        print("LED SOLID")  # Solid LED when connected

print("Testing button. Press Ctrl+C to exit.")

try:
    button_pressed_time = 0
    while True:
        # Read the button state
        button_state = GPIO.input(BUTTON_PIN)
        if button_state == GPIO.LOW:  # Button pressed (LOW because of pull-up)
            button_pressed_time += 1
            print(f"Button held for {button_pressed_time * 0.1} seconds")
            time.sleep(0.1)  # Debounce delay
            
            if button_pressed_time >= 30:  # 3 seconds
                enter_pairing_mode()
                break
        else:
            button_pressed_time = 0
        time.sleep(0.1)  # Delay to avoid flooding the terminal
except KeyboardInterrupt:
    print("\nExiting test.")
finally:
    GPIO.cleanup()  # Clean up GPIO settings
