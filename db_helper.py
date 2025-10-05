import sqlite3

DATABASE = "sign_language.db"

# Function to connect to the database
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Enables dictionary-like row access
    return conn

# Function to add a user
def add_user(username, password, role="user"):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", 
                   (username, password, role))
    conn.commit()
    conn.close()

# Function to check if user exists
def get_user(username):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    return user

# Function to save a detected sign
def save_detection(user_id, sign_detected):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO detections (user_id, sign_detected) VALUES (?, ?)", 
                   (user_id, sign_detected))
    conn.commit()
    conn.close()
