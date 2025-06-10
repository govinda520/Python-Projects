import cv2
import numpy as np
import time
from utils import play_alert, stop_alert, is_drowsy

# Load Haar cascade classifiers
face_cascade = cv2.CascadeClassifier("haarcascades/haarcascade_frontalface_default.xml")
eye_cascade = cv2.CascadeClassifier("haarcascades/haarcascade_eye.xml")

def detect_eyes(roi_gray, roi_color):
    eyes = eye_cascade.detectMultiScale(roi_gray, 1.3, 5)
    eye_centers = []
    
    for (ex, ey, ew, eh) in eyes:
        eye_center = (ex + ew//2, ey + eh//2)
        eye_centers.append(eye_center)
        cv2.rectangle(roi_color, (ex, ey), (ex+ew, ey+eh), (0, 255, 0), 2)
        
        # Get the eye region
        eye_roi = roi_gray[ey:ey+eh, ex:ex+ew]
        eye_roi = cv2.resize(eye_roi, (50, 50))
        
        # Calculate the average brightness of the eye region
        brightness = np.mean(eye_roi)
        
        # Draw the brightness value
        cv2.putText(roi_color, f"{brightness:.1f}", (ex, ey-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    
    return len(eyes), eye_centers

cap = cv2.VideoCapture(0)
closed_eyes_start = None
alert_triggered = False
BRIGHTNESS_THRESHOLD = 50  # Adjust this value based on your lighting conditions

while True:
    ret, frame = cap.read()
    if not ret:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)
    
    eyes_closed = True  # Default to eyes closed if no face detected
    total_brightness = 0
    eye_count = 0

    for (x, y, w, h) in faces:
        roi_gray = gray[y:y+h, x:x+w]
        roi_color = frame[y:y+h, x:x+w]
        
        # Detect eyes and get their centers
        num_eyes, eye_centers = detect_eyes(roi_gray, roi_color)
        
        if num_eyes > 0:
            eyes_closed = False
            cv2.putText(frame, "Eyes Open", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        else:
            cv2.putText(frame, "Eyes Closed", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        # Draw face rectangle
        cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
        break  # Only consider the first face

    current_time = time.time()

    if not eyes_closed:
        if closed_eyes_start is not None:
            closed_eyes_start = None
            if alert_triggered:
                stop_alert()
                alert_triggered = False
    else:
        if closed_eyes_start is None:
            closed_eyes_start = current_time
        elif is_drowsy(closed_eyes_start, current_time) and not alert_triggered:
            cv2.putText(frame, "DROWSY ALERT!", (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            play_alert("sounds/alert.wav")
            alert_triggered = True

    cv2.imshow('Driver Monitor', frame)
    if cv2.waitKey(1) == 27:  # ESC to quit
        break

cap.release()
cv2.destroyAllWindows()
