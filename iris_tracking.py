import cv2
import mediapipe as mp
import numpy as np
import pyautogui
import time
from pathlib import Path
from collections import deque

# =========================================================
# VISION360: HEAD TRACKING + WINK CLICK
# =========================================================

BASE_DIR = Path(__file__).resolve().parent
TASK_PATH = BASE_DIR / "face_landmarker.task"

if not TASK_PATH.exists():
    raise FileNotFoundError(f"Missing required file: {TASK_PATH}")

# Movement & Smoothing settings
PREDICTION_HISTORY = 5
MOVEMENT_THRESHOLD = 3
MAX_MOVEMENT_STEP = 150

# Active Head Zone (Normalized [0.0, 1.0])
HEAD_X_RANGE = [0.35, 0.65] 
HEAD_Y_RANGE = [0.35, 0.65]

# Blink settings
BLINK_MIN_FRAMES = 2
BLINK_COOLDOWN = 1.0

# Screen setup
screen_width, screen_height = pyautogui.size()
print(f"Desktop resolution: {screen_width} x {screen_height}")
print("Mouse control starts PAUSED.")
print("M = pause/resume | Q or ESC = quit")

mouse_enabled = False

# =========================================================
# MEDIAPIPE SETUP
# =========================================================

BaseOptions = mp.tasks.BaseOptions
FaceLandmarker = mp.tasks.vision.FaceLandmarker
FaceLandmarkerOptions = mp.tasks.vision.FaceLandmarkerOptions
RunningMode = mp.tasks.vision.RunningMode

options = FaceLandmarkerOptions(
    base_options=BaseOptions(model_asset_path=str(TASK_PATH)),
    running_mode=RunningMode.VIDEO,
    num_faces=1,
)

# =========================================================
# BLINK DETECTION
# =========================================================

def eye_openness(landmarks, corners, upper_lower_pairs):
    left_corner = landmarks[corners[0]]
    right_corner = landmarks[corners[1]]
    width = np.hypot(right_corner.x - left_corner.x, right_corner.y - left_corner.y)

    if width < 1e-6:
        return 1.0

    vertical_distances = [
        np.hypot(landmarks[u].x - landmarks[l].x, landmarks[u].y - landmarks[l].y)
        for u, l in upper_lower_pairs
    ]
    return float(np.mean(vertical_distances) / width)

def detect_wink(landmarks, threshold):
    left_ratio = eye_openness(landmarks, (33, 133), [(159, 145), (158, 153)])
    right_ratio = eye_openness(landmarks, (362, 263), [(386, 374), (385, 380)])
    
    left_closed = left_ratio < threshold
    right_closed = right_ratio < threshold
    
    # Trigger ONLY if exactly one eye is closed (a deliberate wink)
    return (left_closed and not right_closed) or (right_closed and not left_closed)

# =========================================================
# CAMERA & CALIBRATION
# =========================================================

camera = cv2.VideoCapture(0)
if not camera.isOpened():
    raise RuntimeError("Could not open webcam.")
camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)

with FaceLandmarker.create_from_options(options) as landmarker:
    print("\nLooking for face to calibrate baseline blink threshold...")
    baseline_ratios = []
    
    while len(baseline_ratios) < 30:
        success, frame = camera.read()
        if not success:
            continue
        rgb = cv2.cvtColor(cv2.flip(frame, 1), cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result = landmarker.detect_for_video(mp_image, int(time.monotonic() * 1000))
        
        if result.face_landmarks:
            landmarks = result.face_landmarks[0]
            l_ratio = eye_openness(landmarks, (33, 133), [(159, 145), (158, 153)])
            r_ratio = eye_openness(landmarks, (362, 263), [(386, 374), (385, 380)])
            baseline_ratios.append((l_ratio + r_ratio) / 2)
            
            cv2.putText(frame, f"Calibrating: {len(baseline_ratios)}/30", (20, 50), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            cv2.imshow("Vision360", frame)
            cv2.waitKey(1)

    BLINK_THRESHOLD = np.mean(baseline_ratios) * 0.70
    print(f"Dynamic blink threshold set to: {BLINK_THRESHOLD:.3f}")

    # Variables for tracking state
    prediction_history = deque(maxlen=PREDICTION_HISTORY)
    smoothed_x, smoothed_y = None, None
    blink_frames = 0
    eyes_were_closed = False
    last_click_time = 0.0
    last_timestamp_ms = 0

    while True:
        success, frame = camera.read()
        if not success:
            break

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

        timestamp_ms = max(int(time.monotonic() * 1000), last_timestamp_ms + 1)
        last_timestamp_ms = timestamp_ms
        result = landmarker.detect_for_video(mp_image, timestamp_ms)

        status = "MOUSE: ON" if mouse_enabled else "MOUSE: PAUSED"
        cv2.putText(frame, status, (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.8, 
                    (0, 255, 0) if mouse_enabled else (0, 165, 255), 2)

        if result.face_landmarks:
            landmarks = result.face_landmarks[0]

            # 1. WINK TO CLICK
            closed = detect_wink(landmarks, BLINK_THRESHOLD)
            
            if closed:
                blink_frames += 1
            else:
                blink_frames = 0
            
            if blink_frames >= BLINK_MIN_FRAMES and not eyes_were_closed:
                eyes_were_closed = True

            if not closed and eyes_were_closed:
                now = time.monotonic()
                if mouse_enabled and now - last_click_time >= BLINK_COOLDOWN:
                    pyautogui.click()
                    last_click_time = now
                    print("Wink click registered")
                eyes_were_closed = False

            cv2.putText(frame, "ACTION: WINKING" if closed else "ACTION: EYES OPEN", 
                        (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 0), 2)

            # 2. HEAD TRACKING (Nose Tip -> Screen)
            nose = landmarks[1]
            
            target_x = np.interp(nose.x, HEAD_X_RANGE, [0, screen_width])
            target_y = np.interp(nose.y, HEAD_Y_RANGE, [0, screen_height])
            
            prediction_history.append([target_x, target_y])
            filtered = np.median(np.array(prediction_history), axis=0)

            if smoothed_x is None:
                smoothed_x, smoothed_y = float(filtered[0]), float(filtered[1])

            # Adaptive smoothing
            distance = np.hypot(float(filtered[0]) - smoothed_x, float(filtered[1]) - smoothed_y)
            dynamic_alpha = 0.5 if distance > 50 else 0.15

            smoothed_x += dynamic_alpha * (float(filtered[0]) - smoothed_x)
            smoothed_y += dynamic_alpha * (float(filtered[1]) - smoothed_y)

            # Visualize tracking
            preview_x = int(np.interp(nose.x, HEAD_X_RANGE, [0, frame.shape[1]]))
            preview_y = int(np.interp(nose.y, HEAD_Y_RANGE, [0, frame.shape[0]]))
            cv2.circle(frame, (preview_x, preview_y), 9, (0, 255, 255), -1)

            # Move Mouse
            if mouse_enabled:
                current_x, current_y = pyautogui.position()
                dx, dy = smoothed_x - current_x, smoothed_y - current_y

                if abs(dx) >= MOVEMENT_THRESHOLD or abs(dy) >= MOVEMENT_THRESHOLD:
                    step_x = np.clip(dx, -MAX_MOVEMENT_STEP, MAX_MOVEMENT_STEP)
                    step_y = np.clip(dy, -MAX_MOVEMENT_STEP, MAX_MOVEMENT_STEP)
                    
                    next_x = int(np.clip(current_x + step_x, 0, screen_width - 1))
                    next_y = int(np.clip(current_y + step_y, 0, screen_height - 1))
                    
                    pyautogui.moveTo(next_x, next_y, duration=0)
        else:
            prediction_history.clear()
            smoothed_x, smoothed_y = None, None
            blink_frames = 0
            eyes_were_closed = False
            cv2.putText(frame, "Face not detected", (20, 105), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        cv2.imshow("Vision360", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("m"):
            mouse_enabled = not mouse_enabled
            prediction_history.clear()
            smoothed_x, smoothed_y = None, None
            print("Mouse control:", "ENABLED" if mouse_enabled else "PAUSED")
        elif key == ord("q") or key == 27:
            break

camera.release()
cv2.destroyAllWindows()
print("Vision360 stopped.")