import cv2
import numpy as np
import time
import RPi.GPIO as GPIO
from smbus2 import SMBus

# ========= GPIO SETUP =========
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

RED_LED   = 27
GREEN_LED = 17
BUTTON    = 23
SERVO_PIN = 18
BUZZER    = 22

GPIO.setup(RED_LED, GPIO.OUT)
GPIO.setup(GREEN_LED, GPIO.OUT)
GPIO.setup(BUZZER, GPIO.OUT)
GPIO.setup(BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

servo_pwm = GPIO.PWM(SERVO_PIN, 50)   # 50 Hz
servo_pwm.start(0)

# ========= LCD (I2C 16x2) =========
I2C_ADDR   = 0x27      # change to 0x3F if needed
LCD_WIDTH  = 16

LCD_CHR = 1
LCD_CMD = 0

LCD_LINE_1 = 0x80
LCD_LINE_2 = 0xC0

LCD_BACKLIGHT = 0x08
ENABLE = 0b00000100

bus = SMBus(1)

def lcd_toggle_enable(bits):
    time.sleep(0.0005)
    bus.write_byte(I2C_ADDR, bits | ENABLE)
    time.sleep(0.0005)
    bus.write_byte(I2C_ADDR, bits & ~ENABLE)
    time.sleep(0.0005)

def lcd_byte(bits, mode):
    bits_high = mode | (bits & 0xF0) | LCD_BACKLIGHT
    bits_low  = mode | ((bits << 4) & 0xF0) | LCD_BACKLIGHT
    bus.write_byte(I2C_ADDR, bits_high)
    lcd_toggle_enable(bits_high)
    bus.write_byte(I2C_ADDR, bits_low)
    lcd_toggle_enable(bits_low)

def lcd_init():
    lcd_byte(0x33, LCD_CMD)
    lcd_byte(0x32, LCD_CMD)
    lcd_byte(0x06, LCD_CMD)
    lcd_byte(0x0C, LCD_CMD)
    lcd_byte(0x28, LCD_CMD)
    lcd_byte(0x01, LCD_CMD)
    time.sleep(0.005)

def lcd_string(message, line):
    message = message.ljust(LCD_WIDTH, " ")
    lcd_byte(line, LCD_CMD)
    for ch in message[:LCD_WIDTH]:
        lcd_byte(ord(ch), LCD_CHR)

# ========= SERVO HELPERS =========
def servo_angle(angle):
    duty = 2 + angle / 18.0
    GPIO.output(SERVO_PIN, True)
    servo_pwm.ChangeDutyCycle(duty)
    time.sleep(0.4)
    GPIO.output(SERVO_PIN, False)
    servo_pwm.ChangeDutyCycle(0)

def lock_door():
    servo_angle(0)

def unlock_door():
    servo_angle(90)

# ========= FEEDBACK =========
def leds_off():
    GPIO.output(RED_LED, False)
    GPIO.output(GREEN_LED, False)

def buzzer_beep(times=1, t=0.1):
    for _ in range(times):
        GPIO.output(BUZZER, True)
        time.sleep(t)
        GPIO.output(BUZZER, False)
        time.sleep(t)

# ========= FACE RECOGNITION SETUP =========
recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read("face_model.yml")
label_dict = np.load("labels.npy", allow_pickle=True).item()  # {id: name} [file:2][file:4]

face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

cam = cv2.VideoCapture(0)   # USB webcam on Pi

MAX_ATTEMPTS = 3
BLOCK_TIME   = 300   # 5 min
TIMEOUT      = 10    # seconds
CONF_THRESH  = 60    # lower = better match

def wait_for_button():
    lcd_string("System ready", LCD_LINE_1)
    lcd_string("Press button", LCD_LINE_2)
    leds_off()
    lock_door()
    while True:
        if GPIO.input(BUTTON) == GPIO.HIGH:
            time.sleep(0.05)  # debounce
            if GPIO.input(BUTTON) == GPIO.HIGH:
                return
        time.sleep(0.05)

def recognize_once():
    start = time.time()
    while time.time() - start < TIMEOUT:
        ret, frame = cam.read()
        if not ret:
            continue
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        for (x, y, w, h) in faces:
            roi = gray[y:y+h, x:x+w]
            id_, conf = recognizer.predict(roi)
            return id_, conf
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    return None, None  # timeout or quit

def main():
    lcd_init()
    attempts = 0

    try:
        while True:
            wait_for_button()

            lcd_string("Camera ON", LCD_LINE_1)
            lcd_string("Look at camera", LCD_LINE_2)

            id_, conf = recognize_once()

            if id_ is None:
                # Timeout
                lcd_string("Timeout", LCD_LINE_1)
                lcd_string("Access denied", LCD_LINE_2)
                GPIO.output(RED_LED, True)
                buzzer_beep(2, 0.2)
                time.sleep(2)
                leds_off()
                continue

            if conf < CONF_THRESH:
                # Access granted
                name = label_dict.get(id_, "User")
                lcd_string("Access granted", LCD_LINE_1)
                lcd_string(f"Welcome {name}", LCD_LINE_2)
                GPIO.output(GREEN_LED, True)
                buzzer_beep(1, 0.1)
                unlock_door()
                time.sleep(5)   # door open time
                lock_door()
                leds_off()
                attempts = 0
            else:
                # Access denied
                attempts += 1
                lcd_string("Access denied", LCD_LINE_1)
                lcd_string("Unknown face", LCD_LINE_2)
                GPIO.output(RED_LED, True)
                buzzer_beep(3, 0.15)
                time.sleep(2)
                leds_off()

                if attempts >= MAX_ATTEMPTS:
                    lcd_string("BLOCKED 5 min", LCD_LINE_1)
                    lcd_string("Admin alert", LCD_LINE_2)
                    GPIO.output(RED_LED, True)
                    buzzer_beep(5, 0.2)
                    time.sleep(BLOCK_TIME)
                    attempts = 0
                    leds_off()

    except KeyboardInterrupt:
        pass
    finally:
        lcd_string("System stopped", LCD_LINE_1)
        lcd_string(" ", LCD_LINE_2)
        servo_pwm.stop()
        leds_off()
        GPIO.output(BUZZER, False)
        GPIO.cleanup()
        cam.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
