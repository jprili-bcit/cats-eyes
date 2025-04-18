import time
import RPi.GPIO as GPIO
from collections import deque

# Set up GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Pin configuration
BUTTON_PIN = 12            # Joystick button pin
VRX_PIN = 17               # X-axis capacitor pin
VRY_PIN = 27               # Y-axis capacitor pin
SERVO_HORIZONTAL_PIN = 23  # Horizontal servo
SERVO_VERTICAL_PIN = 24    # Vertical servo

# Servo configuration
SERVO_MIN_ANGLE = 0        # degrees
SERVO_MAX_ANGLE = 180      # degrees
SERVO_CENTER = 90
STEP_SIZE = 2              # Degrees per movement step
MOVE_DELAY = 0.1           # Time between movement updates (seconds)

# Neutral pulse width range (adjust based on your joystick and capacitors)
NEUTRAL_THRESHOLD = 1e-6  # Pulse width range for "joystick released" state

# Add smoothing configuration at the top
SMOOTHING_SAMPLES = 10  # Number of samples for moving average
NEUTRAL_DEADZONE = 0.15  # 15% deadzone around center position

# Initialize GPIO
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(SERVO_HORIZONTAL_PIN, GPIO.OUT)
GPIO.setup(SERVO_VERTICAL_PIN, GPIO.OUT)

# Initialize PWM for servos
horizontal_pwm = GPIO.PWM(SERVO_HORIZONTAL_PIN, 50)
vertical_pwm = GPIO.PWM(SERVO_VERTICAL_PIN, 50)
horizontal_pwm.start(0)
vertical_pwm.start(0)

x_buffer = deque(maxlen=SMOOTHING_SAMPLES)
y_buffer = deque(maxlen=SMOOTHING_SAMPLES)

# Current servo positions
horizontal_angle = SERVO_CENTER
vertical_angle = SERVO_CENTER

# Function to measure capacitor charging time
def measure_pulse(pin):
    GPIO.setup(pin, GPIO.OUT)      # Set the pin as output
    GPIO.output(pin, GPIO.LOW)    # Discharge the capacitor
    time.sleep(0.1)               # Give time to fully discharge
    GPIO.setup(pin, GPIO.IN)      # Set the pin to input mode

    # Measure charging time
    start_time = time.time()
    while GPIO.input(pin) == GPIO.LOW:  # Wait until the capacitor charges
        if time.time() - start_time > 0.1:  # Timeout to avoid infinite loop
            break
    return time.time() - start_time  # Return the pulse width

# Function to map charging time to servo angle
def map_pulse_to_angle(pulse_width, max_width=0.01):
    # Map charging time (pulse width) to servo angle
    angle = SERVO_MIN_ANGLE + (pulse_width / max_width) * (SERVO_MAX_ANGLE - SERVO_MIN_ANGLE)
    return max(SERVO_MIN_ANGLE, min(SERVO_MAX_ANGLE, angle))  # Clamp to valid range

# Function to set servo angle
def set_angle(pwm, angle):
    duty = angle / 18 + 2
    pwm.ChangeDutyCycle(duty)
    time.sleep(0.1)  # Allow servo to move
    pwm.ChangeDutyCycle(0)  # Stop sending signal

def map_pulse_to_angle(current_angle, pulse_width, max_width=0.01):
    # Normalize to -1 to 1 range with deadzone
    normalized = (pulse_width / max_width) * 2 - 1
    if abs(normalized) < NEUTRAL_DEADZONE:
        return current_angle

    # Map to servo range
    angle = current_angle + normalized * (SERVO_MAX_ANGLE - SERVO_MIN_ANGLE)/2
    return max(SERVO_MIN_ANGLE, min(SERVO_MAX_ANGLE, angle))

try:
    # Set initial servo positions
    set_angle(horizontal_pwm, horizontal_angle)
    set_angle(vertical_pwm, vertical_angle)
    print("Joystick control started. Press CTRL+C to exit.")

    while True:
        # Measure pulse width for X and Y axes
        pulse_x = measure_pulse(VRX_PIN)
        pulse_y = measure_pulse(VRY_PIN)
        print(f"{pulse_x}, {pulse_y}")

        horizontal_angle = map_pulse_to_angle(horizontal_angle, pulse_x)
        vertical_angle = map_pulse_to_angle(vertical_angle, pulse_y)

        # Apply new servo positions
        set_angle(horizontal_pwm, horizontal_angle)
        set_angle(vertical_pwm, vertical_angle)

        # Debug output
        print(f"H: {horizontal_angle:03}° V: {vertical_angle:03}°")
        time.sleep(MOVE_DELAY)

except KeyboardInterrupt:
    print("\nExiting...")

finally:
    horizontal_pwm.stop()
    vertical_pwm.stop()
    GPIO.cleanup()
