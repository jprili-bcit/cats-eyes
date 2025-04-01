import time
import RPi.GPIO as GPIO

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
SERVO_REFRESH_RATE = 50    # Hz

# Joystick configuration
SAMPLE_INTERVAL = 0.1      # seconds
MOVE_THRESHOLD = 0.2       # 20% of movement range
CALIBRATION_SAMPLES = 10    # Number of samples for calibration
MIN_READING = 1            # Minimum allowed reading to prevent divide-by-zero

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

    return max(count, MIN_READING)  # Ensure we never return 0

def calibrate_joystick(pin, samples=5):
    """Get stable center position with multiple samples"""
    readings = []
    for _ in range(samples):
        readings.append(read_rc_time(pin))
        time.sleep(0.05)
    return sum(readings) / len(readings)  # Return average

def set_servo_angle(pin, angle):
    """Set servo angle with pulse width modulation"""
    angle = max(SERVO_MIN_ANGLE, min(SERVO_MAX_ANGLE, angle))  # Constrain angle
    pulse_width = SERVO_MIN_PULSE + (angle / 180) * (SERVO_MAX_PULSE - SERVO_MIN_PULSE)
    pulse_width = pulse_width / 1000000.0  # Convert to seconds

    GPIO.output(pin, GPIO.HIGH)
    time.sleep(pulse_width)
    GPIO.output(pin, GPIO.LOW)
    time.sleep((1.0/SERVO_REFRESH_RATE) - pulse_width)

try:
    print("Analog Joystick Camera Control System")
    print("Calibrating - Please center the joystick...")

    # Robust calibration with multiple samples
    x_center = calibrate_joystick(VRX_PIN, CALIBRATION_SAMPLES)
    y_center = calibrate_joystick(VRY_PIN, CALIBRATION_SAMPLES)

    # Validate calibration
    if x_center <= MIN_READING or y_center <= MIN_READING:
        raise ValueError("Calibration failed - check joystick connections")

    print(f"Calibration complete - Center X: {x_center:.1f}, Y: {y_center:.1f}")

    # Initial position
    set_servo_angle(SERVO_HORIZONTAL_PIN, horizontal_angle)
    set_servo_angle(SERVO_VERTICAL_PIN, vertical_angle)

    while True:
        # Read button
        if not GPIO.input(BUTTON_PIN):
            horizontal_angle = vertical_angle = 90
            set_servo_angle(SERVO_HORIZONTAL_PIN, horizontal_angle)
            set_servo_angle(SERVO_VERTICAL_PIN, vertical_angle)
            print("\nCentered servos!")
            time.sleep(0.5)

        # Read joystick
        x_val = read_rc_time(VRX_PIN)
        y_val = read_rc_time(VRY_PIN)

        # Calculate relative position (-1.0 to 1.0)
        x_rel = (x_center - x_val) / x_center  # Invert so right=positive
        y_rel = (y_center - y_val) / y_center  # Invert so up=positive

        # Update servos if movement exceeds threshold
        if abs(x_rel) > MOVE_THRESHOLD:
            horizontal_angle = 90 + (x_rel * 90)  # Scale to ±90° from center
            set_servo_angle(SERVO_HORIZONTAL_PIN, horizontal_angle)

        if abs(y_rel) > MOVE_THRESHOLD:
            vertical_angle = 90 + (y_rel * 90)
            set_servo_angle(SERVO_VERTICAL_PIN, vertical_angle)

        # Display status
        print(f"X: {x_val:4d} ({x_rel:+.2f}) | Y: {y_val:4d} ({y_rel:+.2f}) | Servos: H{horizontal_angle:3.0f}° V{vertical_angle:3.0f}°", end='\r')
        time.sleep(SAMPLE_INTERVAL)

except Exception as e:
    print(f"\nError: {str(e)}")

finally:
    GPIO.cleanup()
    print("\nGPIO cleaned up")
