import cv2
import RPi.GPIO as GPIO
from picamera.array import PiRGBArray
from picamera import PiCamera
import time


def set_angle(pwm, angle):
    """Set servo angle, clamped to 0°–180°."""
    angle = max(0, min(180, angle))  # Clamp to 0°–180°
    duty = 2.5 + (angle * 10 / 180)  # Map 0°–180° to 2.5–12.5% duty cycle
    pwm.ChangeDutyCycle(duty)
    time.sleep(0.3)  # Allow servo to settle
    pwm.ChangeDutyCycle(0)  # Stop signal


def main():
    """Main function to run the laser-guided turret."""
    # Setup GPIO for 180-degree servos
    GPIO.setmode(GPIO.BCM)
    motor1_pin = 18  # Polar axis (vertical, 0° to 180°)
    motor2_pin = 23  # Azimuthal axis (horizontal, 0° to 180°)
    GPIO.setup(motor1_pin, GPIO.OUT)
    GPIO.setup(motor2_pin, GPIO.OUT)
    pwm1 = GPIO.PWM(motor1_pin, 50)  # 50 Hz for standard servos
    pwm2 = GPIO.PWM(motor2_pin, 50)
    pwm1.start(0)
    pwm2.start(0)

    # Setup camera
    camera = PiCamera()
    camera.resolution = (640, 480)
    camera.framerate = 32
    raw_capture = PiRGBArray(camera, size=(640, 480))

    # Initial position (center: 90°)
    set_angle(pwm1, 90)
    set_angle(pwm2, 90)

    try:
        # Main loop
        for frame in camera.capture_continuous(raw_capture, format="bgr", use_video_port=True):
            image = frame.array
            # Convert to HSV and detect laser dot (e.g., red)
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            lower_red = (0, 120, 70)  # Adjust for your laser color
            upper_red = (10, 255, 255)
            mask = cv2.inRange(hsv, lower_red, upper_red)
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            if contours:
                largest = max(contours, key=cv2.contourArea)
                x, y, w, h = cv2.boundingRect(largest)
                center_x = x + w // 2
                center_y = y + h // 2
                # Map pixel coordinates to 0°–180°
                angle_x = int((center_x / 640) * 180)  # Horizontal: 0°–180°
                angle_y = int((center_y / 480) * 180)  # Vertical: 0°–180°
                set_angle(pwm2, angle_x)  # Azimuthal
                set_angle(pwm1, angle_y)  # Polar

            cv2.imshow("Frame", image)
            raw_capture.truncate(0)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    except KeyboardInterrupt:
        print("Interrupted by user")

    finally:
        # Cleanup
        pwm1.stop()
        pwm2.stop()
        GPIO.cleanup()
        cv2.destroyAllWindows()
        camera.close()
        print("Cleanup complete")


if __name__ == "__main__":
    main()