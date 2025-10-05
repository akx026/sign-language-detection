import cv2
import mediapipe as mp
import numpy as np
import os
import pickle
import time

# Initialize MediaPipe
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=1, min_detection_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

# Create data directory
if not os.path.exists('gesture_data'):
    os.makedirs('gesture_data')

# Define gestures - ORGANIZED BY TYPE
gestures = {
    # Numbers (press 0-9)
    '0': '0', '1': '1', '2': '2', '3': '3', '4': '4', 
    '5': '5', '6': '6', '7': '7', '8': '8', '9': '9',
    # Letters (press corresponding letter key)
    'a': 'A', 'b': 'B', 'c': 'C', 'd': 'D', 'e': 'E',
    'f': 'F', 'g': 'G', 'h': 'H', 'i': 'I', 'l': 'L',
    'o': 'O', 'v': 'V', 'y': 'Y'
}

print("Gesture Data Collection")
print("=" * 60)
print("Instructions:")
print("1. Press the KEY for the gesture you want to record")
print("   - Numbers: Press 0-9 for numbers 0-9")
print("   - Letters: Press A-Z for letters A-Z")
print("2. Position your hand and press SPACE")
print("3. It will auto-capture 300 samples (hold gesture steady!)")
print("4. Press 'q' to quit and save")
print("=" * 60)
print("\nAvailable gestures:")
for key, gesture in gestures.items():
    print(f"  Press '{key}' for gesture '{gesture}'")
print("=" * 60)

cap = cv2.VideoCapture(0)
data = []
labels = []

current_gesture = None
is_capturing = False
capture_count = 0
samples_per_gesture = 300

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)
    
    # Draw hand landmarks
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
    
    # Display info
    cv2.rectangle(frame, (10, 10), (630, 120), (0, 0, 0), -1)
    cv2.rectangle(frame, (10, 10), (630, 120), (0, 255, 0), 2)
    
    if current_gesture:
        cv2.putText(frame, f"Selected Gesture: {current_gesture}", 
                   (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
    else:
        cv2.putText(frame, "Press a key to select gesture", 
                   (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
    
    if is_capturing:
        cv2.putText(frame, f"CAPTURING: {capture_count}/{samples_per_gesture}", 
                   (20, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
    else:
        cv2.putText(frame, "Press SPACE to start capturing", 
                   (20, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    cv2.putText(frame, f"Total samples collected: {len(data)}", 
               (20, 105), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
    
    cv2.imshow('Collect Gesture Data', frame)
    
    key = cv2.waitKey(1) & 0xFF
    
    # Select gesture by pressing the key
    key_char = chr(key).lower() if key != 255 else None
    if key_char in gestures and not is_capturing:
        current_gesture = gestures[key_char]
        print(f"\nSelected gesture: {current_gesture}")
        print(f"Press SPACE to capture {samples_per_gesture} samples")
    
    # Start auto-capture
    elif key == ord(' ') and current_gesture and not is_capturing:
        if results.multi_hand_landmarks:
            is_capturing = True
            capture_count = 0
            print(f"Capturing {samples_per_gesture} samples for '{current_gesture}'...")
        else:
            print("No hand detected! Please show your hand to the camera.")
    
    # Auto-capture samples
    if is_capturing and results.multi_hand_landmarks:
        landmarks = results.multi_hand_landmarks[0]
        landmark_list = []
        for lm in landmarks.landmark:
            landmark_list.extend([lm.x, lm.y, lm.z])
        
        data.append(landmark_list)
        labels.append(current_gesture)
        capture_count += 1
        
        if capture_count >= samples_per_gesture:
            is_capturing = False
            print(f"✓ Completed {current_gesture}! Collected {samples_per_gesture} samples.")
            print(f"Total samples so far: {len(data)}")
            current_gesture = None
    
    # Quit
    elif key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

# Save data
if len(data) > 0:
    print("\nSaving data...")
    with open('gesture_data/training_data.pkl', 'wb') as f:
        pickle.dump({'data': data, 'labels': labels}, f)
    
    print(f"✓ Saved {len(data)} samples!")
    print(f"Unique gestures: {set(labels)}")
else:
    print("No data collected!")