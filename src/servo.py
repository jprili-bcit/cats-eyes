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
SERVO_SMOOTHING_FACTOR = 0.1  # Lower = smoother (0.1-0.5 recommended)

# Joystick configuration
SAMPLE_INTERVAL = 0.001     # Reduced from 0.1s for more frequent updates
MOVE_THRESHOLD = 0.15      # Slightly reduced threshold
CALIBRATION_SAMPLES = 10    # Number of samples for calibration
MIN_READING = 1            # Minimum allowed reading
JOYSTICK_SMOOTHING_SAMPLES = 5  # Number of samples for moving average

# Set up GPIO
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(VRX_PIN, GPIO.IN)
GPIO.setup(VRY_PIN, GPIO.IN)
GPIO.setup(SERVO_HORIZONTAL_PIN, GPIO.OUT)
GPIO.setup(SERVO_VERTICAL_PIN, GPIO.OUT)

# Initialize servo positions
horizontal_angle = 90
vertical_angle = 90
target_h_angle = 90
target_v_angle = 90

# Create smoothing buffers for joystick readings
x_buffer = deque(maxlen=JOYSTICK_SMOOTHING_SAMPLES)
y_buffer = deque(maxlen=JOYSTICK_SMOOTHING_SAMPLES)

def read_rc_time(pin):
    """Measure RC charging time with safeguards"""
    count = 0
    try:
        # Discharge capacitor
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, GPIO.LOW)
        time.sleep(0.1)

        # Time charging
        GPIO.setup(pin, GPIO.IN)
        start_time = time.time()
        while GPIO.input(pin) == GPIO.LOW:
            count += 1
            # Timeout after 0.1s to prevent hanging
            if time.time() - start_time > 0.1:
                break
    except:
        pass

    return max(count, MIN_READING)

def calibrate_joystick(pin, samples=5):
    """Get stable center position with multiple samples"""
    readings = []
    for _ in range(samples):
        readings.append(read_rc_time(pin))
        time.sleep(0.05)
    return sum(readings) / len(readings)

def set_servo_angle(pin, angle):
    """Set servo angle with pulse width modulation"""
    angle = max(SERVO_MIN_ANGLE, min(SERVO_MAX_ANGLE, angle))
    pulse_width = SERVO_MIN_PULSE + (angle / 180) * (SERVO_MAX_PULSE - SERVO_MIN_PULSE)
    pulse_width = pulse_width / 1000000.0  # Convert to seconds

    GPIO.output(pin, GPIO.HIGH)
    GPIO.output(pin, GPIO.LOW)

def smooth_servo_movement(current, target, factor):
    """Gradually move current angle toward target angle"""
    return current + (target - current) * factor

try:
    x_center = 0
    y_center = 0

    # Initial position
    set_servo_angle(SERVO_HORIZONTAL_PIN, horizontal_angle)
    set_servo_angle(SERVO_VERTICAL_PIN, vertical_angle)

    while True:
        # Read button
        if not GPIO.input(BUTTON_PIN):
            target_h_angle = target_v_angle = 90
            horizontal_angle = vertical_angle = 90
            set_servo_angle(SERVO_HORIZONTAL_PIN, horizontal_angle)
            set_servo_angle(SERVO_VERTICAL_PIN, vertical_angle)
            print("\nCentered servos!")
            time.sleep(0.5)
            x_buffer.clear()
            y_buffer.clear()

        # Read joystick and apply smoothing
        x_val = read_rc_time(VRX_PIN)
        y_val = read_rc_time(VRY_PIN)

        x_buffer.append(x_val)
        y_buffer.append(y_val)

        # Use moving average of readings
        smooth_x = sum(x_buffer) / len(x_buffer)
        smooth_y = sum(y_buffer) / len(y_buffer)

        # Calculate relative position (-1.0 to 1.0)
        x_rel = (x_center - smooth_x)
        y_rel = (y_center - smooth_y)

        # Update target angles if movement exceeds threshold
        if abs(x_rel) > MOVE_THRESHOLD:
            target_h_angle = 90 + (x_rel * 90)
        else:
            target_h_angle = 90

        if abs(y_rel) > MOVE_THRESHOLD:
            target_v_angle = 90 + (y_rel * 90)
        else:
            target_v_angle = 90

        # Smoothly move servos toward target angles
        horizontal_angle = smooth_servo_movement(horizontal_angle, target_h_angle, SERVO_SMOOTHING_FACTOR)
        vertical_angle = smooth_servo_movement(vertical_angle, target_v_angle, SERVO_SMOOTHING_FACTOR)

        set_servo_angle(SERVO_HORIZONTAL_PIN, horizontal_angle)
        set_servo_angle(SERVO_VERTICAL_PIN, vertical_angle)

        # Display status
        print(f"X: {x_val:4d} ({x_rel:+.2f}) | Y: {y_val:4d} ({y_rel:+.2f}) | Servos: H{horizontal_angle:3.0f}° V{vertical_angle:3.0f}°", end='\r')
        time.sleep(SAMPLE_INTERVAL)

except Exception as e:
    print(f"\nError: {str(e)}")

finally:
    GPIO.cleanup()
    print("\nGPIO cleaned up")
