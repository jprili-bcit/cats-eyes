import time
import RPi.GPIO as GPIO

# Set up GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Pin configuration
BUTTON_PIN = 17            # Joystick button pin
JOYSTICK_UP_PIN = 22       # Digital input for up direction
JOYSTICK_DOWN_PIN = 23     # Digital input for down direction
JOYSTICK_LEFT_PIN = 24     # Digital input for left direction
JOYSTICK_RIGHT_PIN = 25    # Digital input for right direction
SERVO_HORIZONTAL_PIN = 18  # GPIO for horizontal (azimuth) servo
SERVO_VERTICAL_PIN = 19    # GPIO for vertical (elevation) servo

# Servo configuration
SERVO_MIN_PULSE = 500      # Minimum pulse width (μs)
SERVO_MAX_PULSE = 2500     # Maximum pulse width (μs)
SERVO_MIN_ANGLE = 0        # Minimum angle (degrees)
SERVO_MAX_ANGLE = 180      # Maximum angle (degrees)
SERVO_REFRESH_RATE = 50    # Hz (standard for servos)
SERVO_MOVE_STEP = 2        # Degrees to move per update

# Set up GPIO
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(JOYSTICK_UP_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(JOYSTICK_DOWN_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(JOYSTICK_LEFT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(JOYSTICK_RIGHT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(SERVO_HORIZONTAL_PIN, GPIO.OUT)
GPIO.setup(SERVO_VERTICAL_PIN, GPIO.OUT)

# Initialize servo positions
horizontal_angle = 90
vertical_angle = 90

def set_servo_angle(pin, angle):
    """Set servo angle without hardware PWM"""
    pulse_width = SERVO_MIN_PULSE + (angle / SERVO_MAX_ANGLE) * (SERVO_MAX_PULSE - SERVO_MIN_PULSE)
    pulse_width = pulse_width / 1000000.0  # Convert to seconds

    # Generate the pulse
    GPIO.output(pin, GPIO.HIGH)
    time.sleep(pulse_width)
    GPIO.output(pin, GPIO.LOW)

    # Wait for the remainder of the 20ms period
    time.sleep((1.0/SERVO_REFRESH_RATE) - pulse_width)

try:
    print("Digital Joystick Camera Control System")
    print("Move joystick to aim, press button to center")
    print("Press Ctrl+C to exit")

    # Initial position
    set_servo_angle(SERVO_HORIZONTAL_PIN, horizontal_angle)
    set_servo_angle(SERVO_VERTICAL_PIN, vertical_angle)

    while True:
        # Read joystick directions (active low)
        up_pressed = not GPIO.input(JOYSTICK_UP_PIN)
        down_pressed = not GPIO.input(JOYSTICK_DOWN_PIN)
        left_pressed = not GPIO.input(JOYSTICK_LEFT_PIN)
        right_pressed = not GPIO.input(JOYSTICK_RIGHT_PIN)
        button_pressed = not GPIO.input(BUTTON_PIN)

        # Center servos if button pressed
        if button_pressed:
            horizontal_angle = 90
            vertical_angle = 90
            set_servo_angle(SERVO_HORIZONTAL_PIN, horizontal_angle)
            set_servo_angle(SERVO_VERTICAL_PIN, vertical_angle)
            print("Centering servos...")
            time.sleep(0.5)  # Debounce delay

        # Update vertical position
        if up_pressed and vertical_angle < SERVO_MAX_ANGLE:
            vertical_angle += SERVO_MOVE_STEP
            set_servo_angle(SERVO_VERTICAL_PIN, vertical_angle)
        elif down_pressed and vertical_angle > SERVO_MIN_ANGLE:
            vertical_angle -= SERVO_MOVE_STEP
            set_servo_angle(SERVO_VERTICAL_PIN, vertical_angle)

        # Update horizontal position
        if right_pressed and horizontal_angle < SERVO_MAX_ANGLE:
            horizontal_angle += SERVO_MOVE_STEP
            set_servo_angle(SERVO_HORIZONTAL_PIN, horizontal_angle)
        elif left_pressed and horizontal_angle > SERVO_MIN_ANGLE:
            horizontal_angle -= SERVO_MOVE_STEP
            set_servo_angle(SERVO_HORIZONTAL_PIN, horizontal_angle)

        # Small delay to control movement speed
        time.sleep(0.05)

except KeyboardInterrupt:
    print("\nShutting down...")

finally:
    # Clean up
    GPIO.cleanup()
