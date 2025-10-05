import cv2
import numpy as np
from tensorflow.keras.models import load_model

# Load the trained model
model = load_model('asl_model.h5')  # Ensure the model is trained on A-Z
labels = [chr(i) for i in range(65, 91)]  # A-Z

# Initialize webcam
cap = cv2.VideoCapture(0)

print("Press 'q' to quit.")

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # Preprocess the frame
    resized_frame = cv2.resize(frame, (64, 64))  # Match the input size of your model
    input_data = np.expand_dims(resized_frame / 255.0, axis=0)

    # Predict the class
    prediction = model.predict(input_data)
    predicted_label = labels[np.argmax(prediction)]

    # Display the frame and prediction
    cv2.putText(frame, f"Prediction: {predicted_label}", (10, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.imshow('ASL Recognition', frame)

    # Quit the program
    if cv2.waitKey(1) & 0xFF == ord('q'):  # 'q' key
        break

cap.release()
cv2.destroyAllWindows()
