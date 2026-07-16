# CV Analog Steering Injector

A real-time computer vision controller for browser-based racing games. Built with Python, OpenCV, and MediaPipe, it tracks bilateral hand landmarks to compute spatial steering angles. It injects hardware-level keystrokes via an asynchronous proportional tapping algorithm, successfully emulating analog steering on standard digital inputs.

## 🚀 Features

*   **Kinematic Angle Calculation:** Calculates the real-time slope between both hands to determine the exact steering angle.
*   **Proportional Analog Emulation:** Converts physical steering degrees into a dynamic tapping interval. A gentle 15° tilt taps a steering key every 0.4 seconds, while a steep 70° tilt accelerates the tap rate to 0.1 seconds, preventing the "spin-out" effect typical of digital keyboards.
*   **Heuristic Gesture Recognition:** Evaluates the Y-coordinates of 8 independent finger joints. A closed grip naturally defaults to acceleration, while opening 3 or more fingers instantly triggers the brakes.
*   **Asynchronous Input Optimization:** Tracks the memory state of raw hardware scan codes to prevent input buffer flooding and framerate drops.
*   **Always-On-Top Telemetry:** The OpenCV diagnostic window automatically pins itself above the active browser game, rendering real-time skeletal tracking, connection nodes, and vector states.

## 🛠️ Prerequisites

*   Python 3.x
*   A functional webcam
*   Administrator privileges (required for injecting raw hardware scan codes via the `keyboard` library)

## 📦 Installation

1. Clone the repository:
   ```bash
   git clone [https://github.com/YOUR_USERNAME/YOUR_REPOSITORY_NAME.git](https://github.com/YOUR_USERNAME/YOUR_REPOSITORY_NAME.git)
   cd YOUR_REPOSITORY_NAME
   ```

2. Install the required dependencies:
   ```bash
   pip install opencv-python mediapipe keyboard
   ```

*Note: The first time you run the script, it will automatically download the `hand_landmarker.task` weights file directly from Google Cloud.*

## 🚦 Usage

1. Open a terminal or command prompt as **Administrator**.
2. Run the script:
   ```bash
   python steer.py
   ```
3. Open your browser and load your racing game (e.g., Slowroads).
4. **Crucial:** Click inside the game window with your mouse so the browser is the active application.
5. Bring both hands into the camera frame to drive:
   * **Fists / Gripping Wheel:** Accelerate (Holds `W`)
   * **Open Hands / Stop Sign:** Brake (Holds `S`)
   * **Tilt Hands:** Steer Left/Right (`A` / `D`)
6. Drop your hands out of the frame at any time to trigger the failsafe and release all keys. Press `q` while focused on the camera window to quit.

## 🧠 Architecture Overview

The system bypasses standard OS-level virtual key codes, opting instead to hook directly into the hardware scan code stream. This ensures browser-based WebGL engines register the inputs as continuous, physical key-holds rather than software injections.

To achieve analog-like steering on binary digital switches, the script employs a normalized percentage mapping:

```python
turn_percent = (capped_angle - TILT_THRESHOLD) / (MAX_ANGLE - TILT_THRESHOLD)
current_tap_interval = 0.4 - (turn_percent * 0.3)
```

This mathematical slider dynamically adjusts the temporal gap between `keyboard.press()` injections, allowing for micro-corrections on straightaways and aggressive cornering on hairpins.
