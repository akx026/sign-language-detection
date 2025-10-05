import pickle
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
import joblib

# Load data
print("Loading training data...")
with open('gesture_data/training_data.pkl', 'rb') as f:
    dataset = pickle.load(f)

X = np.array(dataset['data'])
y = np.array(dataset['labels'])

print(f"Total samples: {len(X)}")
print(f"Gestures: {set(y)}")

# Split data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train model
print("\nTraining model...")
model = RandomForestClassifier(n_estimators=200, max_depth=20, random_state=42)
model.fit(X_train, y_train)

# Test model
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)

print(f"\nAccuracy: {accuracy * 100:.2f}%")
print("\nClassification Report:")
print(classification_report(y_test, y_pred))

# Save model
joblib.dump(model, 'gesture_model.pkl')
print("\nModel saved as 'gesture_model.pkl'")