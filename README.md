# 🔐 Smart Door Lock with Face Recognition (Raspberry Pi + LBPH)

A Raspberry Pi-based smart door lock system that uses **face recognition** to grant or deny access. Built with OpenCV's LBPH (Local Binary Pattern Histogram) algorithm, it controls a servo motor lock, LEDs, a buzzer, and an I2C LCD display — all triggered by a physical button press.

---

## ✨ Features

- 👤 **Face Recognition** using OpenCV LBPH algorithm
- 🚪 **Servo-controlled door lock** (unlocks on authorized face, locks after 5 seconds)
- 🟢🔴 **LED indicators** — green for access granted, red for denied
- 🔔 **Buzzer feedback** — distinct beep patterns for success/failure/block
- 🖥️ **16×2 I2C LCD** status display (e.g., "Welcome Ahmed", "Access Denied")
- 🛡️ **Brute-force protection** — locks system for 5 minutes after 3 failed attempts
- ⏱️ **10-second recognition timeout** per attempt

---

## 🗂️ Project Structure

```
smart-door-lock/
│
├── capture_faces.py       # Step 1: Capture face samples for a person
├── train_lbph.py          # Step 2: Train the LBPH model on captured faces
├── recognize_lbph.py      # (Optional) Standalone face recognition test
├── main_door_lock.py      # Step 3: Main system — runs on Raspberry Pi
│
├── dataset/               # Auto-created, stores face images per person
│   └── <person_name>/
│       └── 1.jpg, 2.jpg, ...
│
├── face_model.yml         # Auto-generated trained model
└── labels.npy             # Auto-generated label dictionary
```

---

## 🔧 Hardware Requirements

| Component         | Details                                        |
|-------------------|------------------------------------------------|
| Raspberry Pi      | Any model with GPIO (tested on Pi 3/4)         |
| USB Webcam        | Or Pi Camera Module                            |
| Servo Motor       | GPIO pin 18 (PWM)                              |
| Green LED         | GPIO pin 17                                    |
| Red LED           | GPIO pin 27                                    |
| Push Button       | GPIO pin 23                                    |
| Buzzer            | GPIO pin 22                                    |
| I2C LCD (16×2)    | I2C address `0x27` (or `0x3F`)                 |

### GPIO Wiring Summary

```
Green LED  → GPIO 17
Red LED    → GPIO 27
Button     → GPIO 23 (pull-down)
Servo      → GPIO 18 (PWM, 50Hz)
Buzzer     → GPIO 22
LCD SDA    → SDA (GPIO 2)
LCD SCL    → SCL (GPIO 3)
```

---

## 📦 Installation

### 1. Clone the repository
```bash
git clone https://github.com/your-username/smart-door-lock.git
cd smart-door-lock
```

### 2. Install dependencies
```bash
pip install opencv-python opencv-contrib-python numpy smbus2 RPi.GPIO
```

> ⚠️ `opencv-contrib-python` is required for the LBPH face recognizer.

---

## 🚀 Usage

### Step 1 — Capture Face Samples
Run this for each person you want to authorize. It captures **20 face samples** automatically.
```bash
python capture_faces.py
```
Enter the person's name when prompted. Samples are saved in `dataset/<name>/`.

### Step 2 — Train the Model
```bash
python train_lbph.py
```
This generates `face_model.yml` and `labels.npy`.

### Step 3 — Run the Door Lock System
```bash
python main_door_lock.py
```
The system waits for a button press, activates the camera, and recognizes the face within 10 seconds.

### (Optional) Test Recognition Only
```bash
python recognize_lbph.py
```
Runs face recognition in a standalone window without any hardware interaction.

---

## ⚙️ Configuration

You can adjust these constants in `main_door_lock.py`:

| Constant       | Default | Description                              |
|----------------|---------|------------------------------------------|
| `CONF_THRESH`  | `60`    | Confidence threshold (lower = stricter)  |
| `MAX_ATTEMPTS` | `3`     | Failed attempts before system blocks     |
| `BLOCK_TIME`   | `300`   | Block duration in seconds (5 min)        |
| `TIMEOUT`      | `10`    | Seconds to wait for a face per attempt   |
| `I2C_ADDR`     | `0x27`  | Change to `0x3F` if LCD not detected     |

---

## 🔄 System Flow

```
[Button Press]
      ↓
[Camera Activates — 10s timeout]
      ↓
   Face Detected?
   ├── NO  → Red LED + 2 beeps + "Timeout"
   └── YES → LBPH Predict
              ├── conf < 60 → ✅ GREEN LED + unlock servo + "Welcome <name>"
              └── conf ≥ 60 → ❌ RED LED + 3 beeps + attempt counter
                                   └── 3 failures → BLOCKED 5 minutes
```

---

## 🛠️ Built With

- [OpenCV](https://opencv.org/) — Face detection (Haar Cascade) & LBPH recognition
- [RPi.GPIO](https://pypi.org/project/RPi.GPIO/) — GPIO control
- [smbus2](https://pypi.org/project/smbus2/) — I2C LCD communication
- [NumPy](https://numpy.org/) — Label management

---

## 🙋 Author

Built as an embedded systems project integrating computer vision with Raspberry Pi hardware.
