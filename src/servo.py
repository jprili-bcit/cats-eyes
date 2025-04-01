import time
import RPi.GPIO as GPIO

# Set up GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Pin configuration
BUTTON_PIN = 12            # Joystick button pin
VRX_PIN = 17               # Analog X-axis (must be a digital pin capable of input)
VRY_PIN = 27               # Analog Y-axis (must be a digital pin capable of input)
SERVO_HORIZONTAL_PIN = 23  # GPIO for horizontal (azimuth) servo
SERVO_VERTICAL_PIN = 24    # GPIO for vertical (elevation) servo

# Servo configuration
SERVO_MIN_PULSE = 500      # Minimum pulse width (μs)
SERVO_MAX_PULSE = 2500     # Maximum pulse width (μs)
SERVO_MIN_ANGLE = 0        # Minimum angle (degrees)
SERVO_MAX_ANGLE = 180      # Maximum angle (degrees)
SERVO_REFRESH_RATE = 50    # Hz (standard for servos)

# Joystick configuration
SAMPLE_INTERVAL = 0.1      # Time between joystick reads (seconds)
MOVE_THRESHOLD = 0.2       # Minimum joystick movement to respond

# Set up GPIO
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(VRX_PIN, GPIO.IN)
GPIO.setup(VRY_PIN, GPIO.IN)
GPIO.setup(SERVO_HORIZONTAL_PIN, GPIO.OUT)
GPIO.setup(SERVO_VERTICAL_PIN, GPIO.OUT)

# Initialize servo positions
horizontal_angle = 90
vertical_angle = 90

def read_rc_time(pin):
    """Measure RC charging time for analog value approximation"""
    count = 0
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)
    time.sleep(0.1)  # Discharge capacitor

    GPIO.setup(pin, GPIO.IN)
    while GPIO.input(pin) == GPIO.LOW:
        count += 1
    return count

def set_servo_angle(pin, angle):
    """Set servo angle without hardware PWM"""
    pulse_width = SERVO_MIN_PULSE + (angle / SERVO_MAX_ANGLE) * (SERVO_MAX_PULSE - SERVO_MIN_PULSE)
    pulse_width = pulse_width / 1000000.0  # Convert to seconds

    GPIO.output(pin, GPIO.HIGH)
    time.sleep(pulse_width)
    GPIO.output(pin, GPIO.LOW)
    time.sleep((1.0/SERVO_REFRESH_RATE) - pulse_width)

def map_value(value, in_min, in_max, out_min, out_max):
    """Map value from one range to another"""
    return (value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

try:
    print("Analog Joystick Camera Control System")
    print("Move joystick to aim, press button to center")
    print("Press Ctrl+C to exit")

    # Calibration - find center values
    print("Calibrating joystick center...")
    x_center = read_rc_time(VRX_PIN)
    y_center = read_rc_time(VRY_PIN)
    print(f"Calibration complete - Center X: {x_center}, Y: {y_center}")

    # Initial position
    set_servo_angle(SERVO_HORIZONTAL_PIN, horizontal_angle)
    set_servo_angle(SERVO_VERTICAL_PIN, vertical_angle)

    while True:
        # Read button state (0 when pressed)
        button_pressed = not GPIO.input(BUTTON_PIN)

        # Center servos if button pressed
        if button_pressed:
            horizontal_angle = 90
            vertical_angle = 90
            set_servo_angle(SERVO_HORIZONTAL_PIN, horizontal_angle)
            set_servo_angle(SERVO_VERTICAL_PIN, vertical_angle)
            print("Centering servos...")
            time.sleep(0.5)  # Debounce delay

        # Read joystick position
        x_value = read_rc_time(VRX_PIN)
        y_value = read_rc_time(VRY_PIN)

        # Calculate relative position (-1.0 to 1.0 range)
        x_rel = (x_value - x_center) / x_center
        y_rel = (y_value - y_center) / y_center

        # Only move if joystick is pushed beyond threshold
        if abs(x_rel) > MOVE_THRESHOLD:
            horizontal_angle = map_value(x_rel, -1, 1, SERVO_MIN_ANGLE, SERVO_MAX_ANGLE)
            set_servo_angle(SERVO_HORIZONTAL_PIN, horizontal_angle)

        if abs(y_rel) > MOVE_THRESHOLD:
            vertical_angle = map_value(y_rel, -1, 1, SERVO_MIN_ANGLE, SERVO_MAX_ANGLE)
            set_servo_angle(SERVO_VERTICAL_PIN, vertical_angle)

        # Print debug info
        print(f"X: {x_value:4d} ({x_rel:+.2f}), Y: {y_value:4d} ({y_rel:+.2f}) | Servos: H{horizontal_angle:3.0f}° V{vertical_angle:3.0f}°", end='\r')

        time.sleep(SAMPLE_INTERVAL)

except KeyboardInterrupt:
    print("\nShutting down...")

finally:
    # Clean up
    GPIO.cleanup()
