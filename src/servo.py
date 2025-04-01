import time
import RPi.GPIO as GPIO
import spidev

# Set up GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Pin configuration
BUTTON_PIN = 13            # Joystick button pin
SERVO_HORIZONTAL_PIN = 17  # GPIO for horizontal (azimuth) servo
SERVO_VERTICAL_PIN = 27    # GPIO for vertical (elevation) servo

# Servo configuration
SERVO_MIN_PULSE = 500      # Minimum pulse width (μs)
SERVO_MAX_PULSE = 2500     # Maximum pulse width (μs)
SERVO_MIN_ANGLE = 0        # Minimum angle (degrees)
SERVO_MAX_ANGLE = 180      # Maximum angle (degrees)
SERVO_REFRESH_RATE = 50    # Hz (standard for servos)

# Joystick deadzone (to prevent drift when joystick is centered)
DEADZONE = 10              # Percentage from center

# Set up GPIO
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(SERVO_HORIZONTAL_PIN, GPIO.OUT)
GPIO.setup(SERVO_VERTICAL_PIN, GPIO.OUT)

# Initialize servo positions
horizontal_angle = 90
vertical_angle = 90

# Set up SPI for MCP3008
spi = spidev.SpiDev()
spi.open(0, 0)  # SPI bus 0, device 0
spi.max_speed_hz = 1000000  # 1 MHz

def read_channel(channel):
    """Read MCP3008 channel (0-7)"""
    adc = spi.xfer2([1, (8 + channel) << 4, 0])
    return ((adc[1] & 3) << 8) + adc[2]

def map_value(value, in_min, in_max, out_min, out_max):
    """Map value from one range to another"""
    return (value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

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

def update_servo(current_angle, joystick_input):
    """Update servo angle based on joystick input (-100 to 100)"""
    if abs(joystick_input) < DEADZONE:
        return current_angle  # Within deadzone, don't move

    # Calculate new angle (limit to min/max)
    new_angle = current_angle + (joystick_input * 0.5)  # Sensitivity factor

    if new_angle < SERVO_MIN_ANGLE:
        return SERVO_MIN_ANGLE
    elif new_angle > SERVO_MAX_ANGLE:
        return SERVO_MAX_ANGLE
    else:
        return new_angle

try:
    print("Joystick-controlled camera aiming system (No-PWM version)")
    print("Move joystick to aim, press button to center")
    print("Press Ctrl+C to exit")

    # Initial position
    set_servo_angle(SERVO_HORIZONTAL_PIN, 90)
    set_servo_angle(SERVO_VERTICAL_PIN, 90)

    while True:
        # Read joystick values
        x_raw = read_channel(0)
        y_raw = read_channel(1)

        # Map to -100 to 100 range (with deadzone)
        x_value = int(map_value(x_raw, 0, 1023, -100, 100))
        y_value = int(map_value(y_raw, 0, 1023, -100, 100))

        # Read button state (0 when pressed)
        button_state = GPIO.input(BUTTON_PIN)

        # Center servos if button pressed
        if button_state == 0:
            horizontal_angle = 90
            vertical_angle = 90
            set_servo_angle(SERVO_HORIZONTAL_PIN, horizontal_angle)
            set_servo_angle(SERVO_VERTICAL_PIN, vertical_angle)
            print("Centering servos...")
            time.sleep(0.5)  # Debounce delay

        # Update horizontal servo
        new_h_angle = update_servo(horizontal_angle, x_value)
        if new_h_angle != horizontal_angle:
            horizontal_angle = new_h_angle
            set_servo_angle(SERVO_HORIZONTAL_PIN, horizontal_angle)

        # Update vertical servo (invert Y axis if needed)
        new_v_angle = update_servo(vertical_angle, -y_value)  # Negative to make up=up
        if new_v_angle != vertical_angle:
            vertical_angle = new_v_angle
            set_servo_angle(SERVO_VERTICAL_PIN, vertical_angle)

        # Small delay to prevent flooding the console
        time.sleep(0.02)

except KeyboardInterrupt:
    print("\nShutting down...")

finally:
    # Clean up
    spi.close()
    GPIO.cleanup()
