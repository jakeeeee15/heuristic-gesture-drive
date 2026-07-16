import cv2
import mediapipe as mp
import math
import keyboard
import urllib.request
import os
import time

# --- 1. MODEL SETUP ---
model_path = 'hand_landmarker.task'
if not os.path.exists(model_path):
    print("Downloading hand tracking model...")
    url = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
    urllib.request.urlretrieve(url, model_path)

BaseOptions = mp.tasks.BaseOptions
HandLandmarker = mp.tasks.vision.HandLandmarker
HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

options = HandLandmarkerOptions(
    base_options=BaseOptions(model_asset_path=model_path),
    running_mode=VisionRunningMode.IMAGE,
    num_hands=2,
    min_hand_detection_confidence=0.7
)
landmarker = HandLandmarker.create_from_options(options)

HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (5, 6), (6, 7), (7, 8),
    (9, 10), (10, 11), (11, 12),
    (13, 14), (14, 15), (15, 16),
    (17, 18), (18, 19), (19, 20),
    (0, 5), (5, 9), (9, 13), (13, 17), (0, 17)
]


def is_hand_flat(landmarks):
    """Returns True if 3 or more fingers are extended upwards."""
    tips, pips = [8, 12, 16, 20], [6, 10, 14, 18]
    extended_fingers = sum(1 for tip, pip in zip(tips, pips) if landmarks[tip].y < landmarks[pip].y)
    return extended_fingers >= 3


# --- 2. CAMERA SETUP ---
cap = cv2.VideoCapture(0)
TILT_THRESHOLD = 8

cv2.namedWindow("Steering Cam")
cv2.setWindowProperty("Steering Cam", cv2.WND_PROP_TOPMOST, 1)

current_gas_key = None
last_tap_time = 0
active_steer_key = None
steer_release_time = 0
display_steer_text = None
current_tap_interval = 0.4  # Default

# --- 3. MAIN LOOP ---
while cap.isOpened():
    success, img = cap.read()
    if not success: break

    img = cv2.flip(img, 1)
    h, w, c = img.shape

    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=img_rgb)
    result = landmarker.detect(mp_image)

    if result.hand_landmarks and len(result.hand_landmarks) == 2:
        hand1_lms = result.hand_landmarks[0]
        hand2_lms = result.hand_landmarks[1]

        # --- CONTINUOUS GAS / BRAKE ---
        target_gas_key = 's' if (is_hand_flat(hand1_lms) or is_hand_flat(hand2_lms)) else 'w'

        if target_gas_key != current_gas_key:
            if current_gas_key:
                keyboard.release(current_gas_key)
            keyboard.press(target_gas_key)
            current_gas_key = target_gas_key

        cv2.putText(img, "BRAKING" if current_gas_key == 's' else "ACCELERATING", (50, 100), cv2.FONT_HERSHEY_SIMPLEX,
                    1, (0, 0, 255) if current_gas_key == 's' else (0, 255, 0), 3)

        # --- PROPORTIONAL TAPPING STEERING (SHARPER TUNING) ---
        x1, y1 = int(hand1_lms[9].x * w), int(hand1_lms[9].y * h)
        x2, y2 = int(hand2_lms[9].x * w), int(hand2_lms[9].y * h)

        if x1 > x2:
            x1, y1, x2, y2 = x2, y2, x1, y1

        angle = math.degrees(math.atan2(y2 - y1, x2 - x1))
        abs_angle = abs(angle)

        if abs_angle > TILT_THRESHOLD:
            target_steer_key = 'd' if angle > 0 else 'a'

            # Lowered max angle: hits fastest tap rate at 50 degrees instead of 70
            MAX_ANGLE = 50.0
            capped_angle = min(abs_angle, MAX_ANGLE)

            turn_percent = (capped_angle - TILT_THRESHOLD) / (MAX_ANGLE - TILT_THRESHOLD)

            # Tap interval scales between 0.4s and 0.1s
            current_tap_interval = 0.4 - (turn_percent * 0.3)
        else:
            target_steer_key = None

        current_time = time.time()

        if active_steer_key and (current_time >= steer_release_time or target_steer_key is None):
            keyboard.release(active_steer_key)
            active_steer_key = None

        if target_steer_key:
            if current_time - last_tap_time >= current_tap_interval:
                keyboard.press(target_steer_key)
                active_steer_key = target_steer_key
                # Increased hold time: holds the key twice as long (150ms) per tap to bite harder
                steer_release_time = current_time + 0.15
                last_tap_time = current_time

            display_steer_text = f"TURN {target_steer_key.upper()} (Angle: {int(abs_angle)})"
        else:
            display_steer_text = "STRAIGHT"

        cv2.putText(img, display_steer_text, (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

        # --- DRAWING THE VISUALS ---
        cv2.line(img, (x1, y1), (x2, y2), (0, 255, 0), 8)

        for hand_landmarks in result.hand_landmarks:
            for start_idx, end_idx in HAND_CONNECTIONS:
                cx1, cy1 = int(hand_landmarks[start_idx].x * w), int(hand_landmarks[start_idx].y * h)
                cx2, cy2 = int(hand_landmarks[end_idx].x * w), int(hand_landmarks[end_idx].y * h)
                cv2.line(img, (cx1, cy1), (cx2, cy2), (255, 255, 255), 2)

            for landmark in hand_landmarks:
                cx, cy = int(landmark.x * w), int(landmark.y * h)
                cv2.circle(img, (cx, cy), 6, (0, 0, 255), -1)
                cv2.circle(img, (cx, cy), 6, (255, 0, 0), 1)

    else:
        # Failsafe
        if current_gas_key:
            keyboard.release(current_gas_key)
            current_gas_key = None
        if active_steer_key:
            keyboard.release(active_steer_key)
            active_steer_key = None

    cv2.imshow("Steering Cam", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Clean up before quitting
if current_gas_key: keyboard.release(current_gas_key)
if active_steer_key: keyboard.release(active_steer_key)
cap.release()
cv2.destroyAllWindows()