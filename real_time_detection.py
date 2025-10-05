import cv2
import os
import numpy as np
import tensorflow as tf

# ✅ Load the trained model (Ensure the correct path)
MODEL_PATH = "model/sign_language_model.h5"

if not os.path.exists(MODEL_PATH):
    print(f"❌ Error: Model file not found at {MODEL_PATH}")
    exit()

model = tf.keras.models.load_model(MODEL_PATH)

# ✅ Open Webcam with Error Handling
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("❌ Error: Could not open webcam. Trying alternative index...")
    cap = cv2.VideoCapture(1)  # Try different index

if not cap.isOpened():
    print("❌ Error: Still could not open webcam. Exiting.")
    exit()

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        print("❌ Error: Frame not captured")
        break

    # ✅ Convert frame to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # ✅ Resize image to 64x64 (to match model input)
    resized = cv2.resize(gray, (64, 64))

    # ✅ Normalize pixel values (0 to 1)
    normalized = resized / 255.0

    # ✅ Reshape to (1, 64, 64, 1) for model
    input_image = np.reshape(normalized, (1, 64, 64, 1))

    # ✅ Make prediction
    prediction = model.predict(input_image)
    sign_class = np.argmax(prediction)  # Get the predicted class
    confidence = np.max(prediction)  # Get confidence score

    # ✅ Display Prediction
    cv2.putText(frame, f"Sign: {sign_class} ({confidence:.2f})", (50, 50), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    # ✅ Show the video feed
    cv2.imshow("Sign Detection", frame)

    # ✅ Press 'q' to exit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
