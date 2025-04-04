import time
import RPi.GPIO as GPIO

# Set up GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Pin configuration
BUTTON_PIN = 12            # Joystick button pin
VRX_PIN = 17               # X-axis (treated as digital input)
VRY_PIN = 27               # Y-axis (treated as digital input)
SERVO_HORIZONTAL_PIN = 23  # Horizontal servo
SERVO_VERTICAL_PIN = 24    # Vertical servo

# Servo configuration
SERVO_MIN_ANGLE = 0        # degrees
SERVO_MAX_ANGLE = 180      # degrees
SERVO_CENTER = 90
STEP_SIZE = 2               # Degrees per movement step
MOVE_DELAY = 0.1           # Time between steps (seconds)

# Initialize GPIO
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(VRX_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(VRY_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(SERVO_HORIZONTAL_PIN, GPIO.OUT)
GPIO.setup(SERVO_VERTICAL_PIN, GPIO.OUT)

# Initialize PWM for servos
horizontal_pwm = GPIO.PWM(SERVO_HORIZONTAL_PIN, 50)
vertical_pwm = GPIO.PWM(SERVO_VERTICAL_PIN, 50)
horizontal_pwm.start(0)
vertical_pwm.start(0)

# Current servo positions
horizontal_angle = SERVO_CENTER
vertical_angle = SERVO_CENTER

def set_angle(pwm, angle):
    duty = angle / 18 + 2
    pwm.ChangeDutyCycle(duty)
    time.sleep(0.1)  # Allow servo to move
    pwm.ChangeDutyCycle(0)  # Stop sending signal

def update_position():
    global horizontal_angle, vertical_angle

    # Read digital states (active low)
    x_left = not GPIO.input(VRX_PIN)
    x_right = False  # Not used in this configuration
    y_up = not GPIO.input(VRY_PIN)
    y_down = False   # Not used in this configuration

    # Update horizontal position
    if x_left and horizontal_angle > SERVO_MIN_ANGLE:
        horizontal_angle -= STEP_SIZE
    # Add right handling if using different pin configuration

    # Update vertical position
    if y_up and vertical_angle < SERVO_MAX_ANGLE:
        vertical_angle += STEP_SIZE
    # Add down handling if using different pin configuration

try:
    # Set initial position
    set_angle(horizontal_pwm, SERVO_CENTER)
    set_angle(vertical_pwm, SERVO_CENTER)
    print("Joystick control started. Press CTRL+C to exit.")

    while True:
        # Update positions based on joystick
        update_position()

        # Apply new positions
        set_angle(horizontal_pwm, horizontal_angle)
        set_angle(vertical_pwm, vertical_angle)

        # Center button handling
        if not GPIO.input(BUTTON_PIN):
            horizontal_angle = vertical_angle = SERVO_CENTER
            set_angle(horizontal_pwm, SERVO_CENTER)
            set_angle(vertical_pwm, SERVO_CENTER)
            print("\nCentered servos!")
            time.sleep(0.5)

        print(f"H: {horizontal_angle:03}° V: {vertical_angle:03}°", end='\r')
        time.sleep(MOVE_DELAY)

except KeyboardInterrupt:
    print("\nExiting...")

finally:
    horizontal_pwm.stop()
    vertical_pwm.stop()
    GPIO.cleanup()
