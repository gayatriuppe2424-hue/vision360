
import cv2
import mediapipe as mp
import os
import math

from mediapipe.tasks import python
from mediapipe.tasks.python import vision

MODEL_PATH = "face_landmarker.task"

if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError("face_landmarker.task not found.")

base_options = python.BaseOptions(
    model_asset_path=MODEL_PATH
)

options = vision.FaceLandmarkerOptions(
    base_options=base_options,
    running_mode=vision.RunningMode.VIDEO,
    num_faces=1
)

detector = vision.FaceLandmarker.create_from_options(options)
camera = cv2.VideoCapture(0)

# Eye landmark indices
LEFT_EYE = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]

def distance(point1, point2):
    return math.sqrt(
        (point1.x - point2.x) ** 2 +
        (point1.y - point2.y) ** 2
    )

def eye_ratio(landmarks, indices):
    # Vertical eye opening
    vertical1 = distance(
        landmarks[indices[1]],
        landmarks[indices[5]]
    )
    vertical2 = distance(
        landmarks[indices[2]],
        landmarks[indices[4]]
    )

    # Horizontal eye width
    horizontal = distance(
        landmarks[indices[0]],
        landmarks[indices[3]]
    )

    return (vertical1 + vertical2) / (2 * horizontal)

if not camera.isOpened():
    detector.close()
    raise RuntimeError("Could not open webcam.")

blink_count = 0
eyes_closed = False
CLOSE_THRESHOLD = 0.18
OPEN_THRESHOLD = 0.23
timestamp_ms = 0

print("Blink detection started. Press Q to quit.")

try:
    while True:
        success, frame = camera.read()

        if not success:
            break

        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(
            frame, cv2.COLOR_BGR2RGB
        )

        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb_frame
        )

        timestamp_ms += 33
        result = detector.detect_for_video(
            mp_image, timestamp_ms
        )

        status = "Face not detected"

        if result.face_landmarks:
            face = result.face_landmarks[0]

            left_ratio = eye_ratio(face, LEFT_EYE)
            right_ratio = eye_ratio(face, RIGHT_EYE)
            average_ratio = (left_ratio + right_ratio) / 2

            # Count a blink when eyes close and reopen
            if average_ratio < CLOSE_THRESHOLD:
                if not eyes_closed:
                    eyes_closed = True

            elif average_ratio > OPEN_THRESHOLD:
                if eyes_closed:
                    blink_count += 1
                    eyes_closed = False

            status = (
                "Eyes closed" if eyes_closed
                else "Eyes open"
            )

            height, width, _ = frame.shape

            for index in LEFT_EYE + RIGHT_EYE:
                landmark = face[index]
                x = int(landmark.x * width)
                y = int(landmark.y * height)

                cv2.circle(
                    frame, (x, y), 3, (0, 255, 0), -1
                )

            cv2.putText(
                frame,
                f"Eye ratio: {average_ratio:.3f}",
                (20, 80),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 0),
                2
            )

        cv2.putText(
            frame,
            status,
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2
        )

        cv2.putText(
            frame,
            f"Blinks: {blink_count}",
            (20, 120),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 255),
            2
        )

        cv2.imshow("Irisync - Blink Detection", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

finally:
    camera.release()
    detector.close()
    cv2.destroyAllWindows()
