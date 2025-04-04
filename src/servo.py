import time
import RPi.GPIO as GPIO

# Set up GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Pin configuration
BUTTON_PIN = 12            # Joystick button pin
UP_PIN = 17                # Up direction
DOWN_PIN = 27              # Down direction
LEFT_PIN = 22              # Left direction
RIGHT_PIN = 23             # Right direction
SERVO_HORIZONTAL_PIN = 24  # Horizontal servo
SERVO_VERTICAL_PIN = 25    # Vertical servo

# Servo configuration
SERVO_MIN_ANGLE = 0        # degrees
SERVO_MAX_ANGLE = 180      # degrees
SERVO_REFRESH_RATE = 50    # Hz
STEP_SIZE = 2               # Degrees per movement step
MOVE_DELAY = 0.1           # Time between steps (seconds)

# Initialize GPIO
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(UP_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(DOWN_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(LEFT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(RIGHT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(SERVO_HORIZONTAL_PIN, GPIO.OUT)
GPIO.setup(SERVO_VERTICAL_PIN, GPIO.OUT)

# Initialize PWM for servos
horizontal_pwm = GPIO.PWM(SERVO_HORIZONTAL_PIN, SERVO_REFRESH_RATE)
vertical_pwm = GPIO.PWM(SERVO_VERTICAL_PIN, SERVO_REFRESH_RATE)
horizontal_pwm.start(0)
vertical_pwm.start(0)

# Servo control variables
horizontal_angle = 90
vertical_angle = 90

def set_angle(pwm, angle):
    duty = angle / 18 + 2
    pwm.ChangeDutyCycle(duty)

try:
    print("Digital Joystick Camera Control")
    print("Use directions to move, press to center")

    # Initial position
    set_angle(horizontal_pwm, horizontal_angle)
    set_angle(vertical_pwm, vertical_angle)
    time.sleep(0.5)  # Allow servos to settle

    while True:
        # Read joystick directions (active low)
        up = not GPIO.input(UP_PIN)
        down = not GPIO.input(DOWN_PIN)
        left = not GPIO.input(LEFT_PIN)
        right = not GPIO.input(RIGHT_PIN)
        center_btn = not GPIO.input(BUTTON_PIN)

        # Handle vertical movement
        if up and vertical_angle < SERVO_MAX_ANGLE:
            vertical_angle += STEP_SIZE
        if down and vertical_angle > SERVO_MIN_ANGLE:
            vertical_angle -= STEP_SIZE

        # Handle horizontal movement
        if right and horizontal_angle < SERVO_MAX_ANGLE:
            horizontal_angle += STEP_SIZE
        if left and horizontal_angle > SERVO_MIN_ANGLE:
            horizontal_angle -= STEP_SIZE

        # Update servo positions
        set_angle(horizontal_pwm, horizontal_angle)
        set_angle(vertical_pwm, vertical_angle)

        # Center button handling
        if center_btn:
            horizontal_angle = vertical_angle = 90
            set_angle(horizontal_pwm, 90)
            set_angle(vertical_pwm, 90)
            print("\nCentered servos!")
            time.sleep(0.5)  # Debounce delay

        # Display status
        print(f"H: {horizontal_angle:03}° V: {vertical_angle:03}°", end='\r')
        time.sleep(MOVE_DELAY)

except KeyboardInterrupt:
    print("\nExiting...")

finally:
    horizontal_pwm.stop()
    vertical_pwm.stop()
    GPIO.cleanup()
