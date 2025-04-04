import time
import RPi.GPIO as GPIO
from collections import deque

# Set up GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Pin configuration
BUTTON_PIN = 12            # Joystick button pin
VRX_PIN = 17               # Analog X-axis
VRY_PIN = 27               # Analog Y-axis
SERVO_HORIZONTAL_PIN = 23  # Horizontal servo
SERVO_VERTICAL_PIN = 24    # Vertical servo

# Servo configuration
SERVO_MIN_PULSE = 500      # μs
SERVO_MAX_PULSE = 2500     # μs
SERVO_MIN_ANGLE = 0        # degrees
SERVO_MAX_ANGLE = 180      # degrees
SERVO_REFRESH_RATE = 120   # Hz
SERVO_SENSITIVITY = 0.5    # Movement speed multiplier (0.1-1.0)
DEADZONE = 0.15            # Joystick deadzone (15% of total range)

# Joystick configuration
SAMPLE_INTERVAL = 0.02     # Update interval (seconds)
SMOOTHING_SAMPLES = 5      # Moving average samples

# Initialize GPIO
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(VRX_PIN, GPIO.IN)
GPIO.setup(VRY_PIN, GPIO.IN)
GPIO.setup(SERVO_HORIZONTAL_PIN, GPIO.OUT)
GPIO.setup(SERVO_VERTICAL_PIN, GPIO.OUT)

# Servo control variables
horizontal_angle = 90  # Start at center position
vertical_angle = 90
x_buffer = deque(maxlen=SMOOTHING_SAMPLES)
y_buffer = deque(maxlen=SMOOTHING_SAMPLES)

def read_rc_time(pin):
    """Measure capacitor charge time for analog approximation"""
    count = 0
    try:
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, GPIO.LOW)
        time.sleep(0.1)

        GPIO.setup(pin, GPIO.IN)
        start = time.time()
        while GPIO.input(pin) == GPIO.LOW and (time.time() - start) < 0.1:
            count += 1
    except:
        pass
    return max(count, 1)

def set_servo_angle(pin, angle):
    """Update servo position using software PWM"""
    angle = max(SERVO_MIN_ANGLE, min(SERVO_MAX_ANGLE, angle))
    pulse = SERVO_MIN_PULSE + (angle/180)*(SERVO_MAX_PULSE - SERVO_MIN_PULSE)
    pulse_us = pulse / 1e6

    GPIO.output(pin, GPIO.HIGH)
    time.sleep(pulse_us)
    GPIO.output(pin, GPIO.LOW)
    time.sleep((1/SERVO_REFRESH_RATE) - pulse_us)

try:
    # Automatic center detection (no user calibration needed)
    print("Initializing...")
    x_center = sum(read_rc_time(VRX_PIN) for _ in range(5)) / 5
    y_center = sum(read_rc_time(VRY_PIN) for _ in range(5)) / 5
    print(f"Auto-detected center - X: {x_center:.1f}, Y: {y_center:.1f}")

    # Initial servo position
    set_servo_angle(SERVO_HORIZONTAL_PIN, horizontal_angle)
    set_servo_angle(SERVO_VERTICAL_PIN, vertical_angle)

    while True:
        # Read and smooth joystick inputs
        x_val = read_rc_time(VRX_PIN)
        y_val = read_rc_time(VRY_PIN)
        x_buffer.append(x_val)
        y_buffer.append(y_val)

        # Calculate relative offsets
        x_offset = (x_center - sum(x_buffer)/len(x_buffer)) / x_center
        y_offset = (y_center - sum(y_buffer)/len(y_buffer)) / y_center

        # Apply deadzone and sensitivity
        if abs(x_offset) < DEADZONE: x_offset = 0
        if abs(y_offset) < DEADZONE: y_offset = 0

        # Update angles based on relative movement
        horizontal_angle += x_offset * SERVO_SENSITIVITY
        vertical_angle += y_offset * SERVO_SENSITIVITY

        # Constrain angles to valid range
        horizontal_angle = max(SERVO_MIN_ANGLE, min(SERVO_MAX_ANGLE, horizontal_angle))
        vertical_angle = max(SERVO_MIN_ANGLE, min(SERVO_MAX_ANGLE, vertical_angle))

        # Update servos
        set_servo_angle(SERVO_HORIZONTAL_PIN, horizontal_angle)
        set_servo_angle(SERVO_VERTICAL_PIN, vertical_angle)

        # Center button handling
        if not GPIO.input(BUTTON_PIN):
            horizontal_angle = vertical_angle = 90
            print("\nCentered servos!")
            time.sleep(0.5)  # Debounce delay

        # Display status
        print(f"H: {horizontal_angle:05.1f}° | V: {vertical_angle:05.1f}° | X: {x_offset:+.2f} | Y: {y_offset:+.2f}", end='\r')
        time.sleep(SAMPLE_INTERVAL)

except KeyboardInterrupt:
    print("\nExiting...")

finally:
    GPIO.cleanup()
