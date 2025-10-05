from tensorflow import keras

# Load the old model (force old-style loading)
model = keras.models.load_model("asl_model.h5", compile=False)

# Re-save it in the new Keras format (recommended)
model.save("asl_model.keras", save_format="keras")

print("✅ Model converted and saved as 'asl_model.keras'")
