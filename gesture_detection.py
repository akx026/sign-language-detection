import cv2
import mediapipe as mp
import numpy as np
import joblib
from collections import deque
import os

class GestureDetector:
    def __init__(self):
        # Initialize MediaPipe
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5
        )
        self.mp_draw = mp.solutions.drawing_utils
        
        # Load trained model
        try:
            self.model = joblib.load('gesture_model.pkl')
            self.model_loaded = True
            print("Model loaded successfully!")
        except:
            print("Model not found. Please train the model first.")
            self.model_loaded = False
        
        # Prediction smoothing
        self.gesture_buffer = deque(maxlen=10)
        self.last_prediction = ""
        self.confidence = 0.0
        
    def extract_landmarks(self, hand_landmarks):
        """Extract hand landmark coordinates"""
        landmark_list = []
        for lm in hand_landmarks.landmark:
            landmark_list.extend([lm.x, lm.y, lm.z])
        return landmark_list
    
    def predict_gesture(self, landmarks):
        """Predict gesture from landmarks"""
        if not self.model_loaded:
            return None
        
        try:
            # Predict using the trained model
            prediction = self.model.predict([landmarks])[0]
            
            # Get prediction probability for confidence
            probabilities = self.model.predict_proba([landmarks])[0]
            confidence = max(probabilities)
            
            return prediction, confidence
        except Exception as e:
            print(f"Prediction error: {e}")
            return None, 0
    
    def process_frame(self, frame):
        """Process frame and detect gestures"""
        # Convert to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_frame)
        
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Draw hand landmarks
                self.mp_draw.draw_landmarks(
                    frame, 
                    hand_landmarks, 
                    self.mp_hands.HAND_CONNECTIONS,
                    self.mp_draw.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2),
                    self.mp_draw.DrawingSpec(color=(0, 0, 255), thickness=2)
                )
                
                if self.model_loaded:
                    # Extract landmarks
                    landmarks = self.extract_landmarks(hand_landmarks)
                    
                    # Predict gesture
                    result = self.predict_gesture(landmarks)
                    
                    if result and result[0]:
                        prediction, confidence = result
                        self.gesture_buffer.append(prediction)
                        
                        # Smooth predictions using buffer
                        if len(self.gesture_buffer) >= 5:
                            most_common = max(set(self.gesture_buffer), 
                                            key=self.gesture_buffer.count)
                            if self.gesture_buffer.count(most_common) >= 5:
                                self.last_prediction = most_common
                                self.confidence = confidence
        
        # Draw prediction box
        self.draw_prediction_box(frame)
        
        return frame
    
    def draw_prediction_box(self, frame):
        """Draw prediction information on frame"""
        h, w, _ = frame.shape
        
        # Main prediction box
        cv2.rectangle(frame, (10, 10), (300, 100), (0, 0, 0), -1)
        cv2.rectangle(frame, (10, 10), (300, 100), (0, 255, 0), 2)
        
        # Display prediction
        cv2.putText(frame, f"Sign: {self.last_prediction}", 
                   (20, 45), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # Display confidence
        confidence_text = f"Confidence: {self.confidence:.2%}"
        cv2.putText(frame, confidence_text, 
                   (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Status message
        if not self.model_loaded:
            cv2.putText(frame, "Model not loaded!", 
                       (20, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

# Create global detector instance
detector = GestureDetector()

def detect_sign_from_frame(frame, num_frames):
    """
    Main function called by Flask app
    Returns: processed frame and prediction
    """
    processed_frame = detector.process_frame(frame)
    return processed_frame, detector.last_prediction