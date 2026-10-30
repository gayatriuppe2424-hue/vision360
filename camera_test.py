
import cv2

# Open the default webcam
camera = cv2.VideoCapture(0)

if not camera.isOpened():
    print("Error: Could not access the webcam.")
    exit()

print("Webcam started. Press Q to quit.")

while True:
    success, frame = camera.read()

    if not success:
        print("Error: Could not read webcam frame.")
        break

    # Mirror the video like a selfie camera
    frame = cv2.flip(frame, 1)

    cv2.imshow("Irisync - Webcam Test", frame)

    # Press Q to close
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

camera.release()
cv2.destroyAllWindows()
