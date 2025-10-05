import numpy as np
import cv2
import tensorflow as tf
from tensorflow import keras
import os

# ✅ Load the full model from .h5
model = keras.models.load_model("model/best_model_dataflair.h5")


# Load trained model dynamically based on available classes
model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'best_model_dataflair.h5')
model = keras.models.load_model(model_path)

background = None
accumulated_weight = 0.5
ROI_top, ROI_bottom, ROI_right, ROI_left = 100, 300, 150, 350

# Dynamically load available classes based on the dataset
train_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gesture', 'train')
available_classes = sorted([d for d in os.listdir(train_path) if os.path.isdir(os.path.join(train_path, d))])
n_classes = len(available_classes)

if n_classes == 0:
    raise ValueError("No classes found! Please ensure you have trained at least one class.")

print(f"Loaded Model with {n_classes} classes: {available_classes}")

def cal_accum_avg(frame, accumulated_weight):
    global background
    if background is None:
        background = frame.copy().astype("float")
        return None
    cv2.accumulateWeighted(frame, background, accumulated_weight)

def segment_hand(frame, threshold=25):
    global background
    diff = cv2.absdiff(background.astype("uint8"), frame)
    _, thresholded = cv2.threshold(diff, threshold, 255, cv2.THRESH_BINARY)
    contours, hierarchy = cv2.findContours(thresholded.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if len(contours) == 0:
        return None
    else:
        hand_segment_max_cont = max(contours, key=cv2.contourArea)
        return (thresholded, hand_segment_max_cont)

cam = cv2.VideoCapture(0)

# Set windows to stay on top
cv2.namedWindow('Sign Detection', cv2.WINDOW_NORMAL)
cv2.setWindowProperty('Sign Detection', cv2.WND_PROP_TOPMOST, 1)
cv2.namedWindow('Thresholded Hand Image', cv2.WINDOW_NORMAL)
cv2.setWindowProperty('Thresholded Hand Image', cv2.WND_PROP_TOPMOST, 1)

num_frames = 0

while True:
    ret, frame = cam.read()
    frame = cv2.flip(frame, 1)
    frame_copy = frame.copy()
    roi = frame[ROI_top:ROI_bottom, ROI_right:ROI_left]
    gray_frame = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    gray_frame = cv2.GaussianBlur(gray_frame, (9, 9), 0)
    
    if num_frames < 60:
        cal_accum_avg(gray_frame, accumulated_weight)
        if num_frames <= 59:
            cv2.putText(frame_copy, "FETCHING BACKGROUND...PLEASE WAIT", (80, 400), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,0,255), 2)
    else:
        hand = segment_hand(gray_frame)
        if hand is not None:
            thresholded, hand_segment = hand
            cv2.drawContours(frame_copy, [hand_segment + (ROI_right, ROI_top)], -1, (255, 0, 0), 1)
            cv2.imshow("Thresholded Hand Image", thresholded)
            
            thresholded = cv2.resize(thresholded, (64, 64))
            thresholded = cv2.cvtColor(thresholded, cv2.COLOR_GRAY2RGB)
            thresholded = np.reshape(thresholded, (1, 64, 64, 3))
            pred = model.predict(thresholded, verbose=0)
            predicted_class = available_classes[np.argmax(pred)]
            
            cv2.putText(frame_copy, predicted_class, (170, 45), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)
        else:
            cv2.putText(frame_copy, 'No hand detected...', (200, 400), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)
    
    cv2.rectangle(frame_copy, (ROI_left, ROI_top), (ROI_right, ROI_bottom), (255, 128, 0), 3)
    cv2.putText(frame_copy, "DataFlair hand sign recognition_ _ _", (10, 20), cv2.FONT_ITALIC, 0.5, (51,255,51), 1)
    
    num_frames += 1
    cv2.imshow("Sign Detection", frame_copy)
    
    if cv2.waitKey(1) & 0xFF == 27:
        break

cam.release()
cv2.destroyAllWindows()
