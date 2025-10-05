from flask import Flask, render_template, request, redirect, url_for, session, flash,Response
import cv2
import sqlite3
import bcrypt
import secrets
from flask_mail import Mail, Message
import os
import re  # ✅ FIXED: Import re module
import requests  # Import this for reCAPTCHA verification
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from tensorflow import keras
import numpy as np
from gesture_detection import detect_sign_from_frame
from werkzeug.utils import secure_filename


# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "your_secret_key")  

# 📧 Email Configuration (Use environment variables)
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")

mail = Mail(app)

DATABASE = "database.db"
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 📌 Ensure video upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 📌 Database Connection
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# ✅ Create Tables
def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS videos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    filename TEXT NOT NULL
);

    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            filename TEXT NOT NULL,
            category TEXT
        )
    """)

    conn.commit()

    # ✅ Ensure Admin Exists
    cursor.execute("SELECT * FROM users WHERE role = 'admin'")
    if not cursor.fetchone():
        hashed_password = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cursor.execute("INSERT INTO users (email, username, password, role) VALUES (?, ?, ?, 'admin')",
                       ("admin@example.com", "admin", hashed_password))
        conn.commit()

    conn.close()

    # ✅ Ensure the upload folder exists before handling files
UPLOAD_FOLDER = 'static/uploads/'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER  # ✅ Add this to Flask config

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def insert_video(title, description, filename, category='All'):
    conn = sqlite3.connect(DATABASE)  # Use the correct DATABASE constant
    cursor = conn.cursor()
    cursor.execute("INSERT INTO videos (title, description, filename, category) VALUES (?, ?, ?, ?)",
                   (title, description, filename, category))
    conn.commit()
    conn.close()

  # Verify Database Table Structure
@app.route('/check_db')
def check_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check table structure
    cursor.execute("PRAGMA table_info(videos)")
    columns = cursor.fetchall()
    
    # Get all videos
    cursor.execute("SELECT * FROM videos")
    videos = cursor.fetchall()
    
    conn.close()
    
    output = "<h2>Videos Table Structure:</h2>"
    output += "<ul>"
    for col in columns:
        output += f"<li>{col}</li>"
    output += "</ul>"
    
    output += f"<h2>Total Videos: {len(videos)}</h2>"
    output += "<ul>"
    for video in videos:
        output += f"<li>{dict(video)}</li>"
    output += "</ul>"
    
    return output

# 🏠 Home Page
@app.route('/')
def home():
    return render_template('index.html', username=session.get("username"), logged_in=session.get("username") is not None, role=session.get("role", "user"))

@app.route("/get_username")
def get_username():
    return {"username": session.get("username", "User")}

# ℹ️ About Page
@app.route('/about')
def about():
    return render_template('about.html')

# 🎥 Sign Detection Page (Requires Login)
@app.route('/detect')
def detect():
    if "username" not in session:
        flash("You must be logged in to access sign detection.", "danger")
        return redirect(url_for("login"))
    
    return render_template('detect.html', video_feed=url_for('video_feed'))


# 🔑 Login (Admins go to /admin, Users go to /)
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username_or_email = request.form.get("username_or_email")
        password = request.form.get("password")

        print(f"Received login request for: {username_or_email}")

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, email, password, role FROM users WHERE username=? OR email=?", 
                       (username_or_email, username_or_email))
        user = cursor.fetchone()
        conn.close()

        print(f"User fetched from DB: {user}")

        if user:
            stored_password_hash = user[3]
            print(f"Stored Password Hash: {stored_password_hash}")

            # ✅ Fix: Use check_password_hash()
            if check_password_hash(stored_password_hash, password):
                session["user_id"] = user[0]
                session["username"] = user[1]
                session["role"] = user[4]

                flash("Login successful!", "success")
                return redirect(url_for("admin")) if user[4] == "admin" else redirect(url_for("home"))

            print("Error in password check: Password does not match.")
        else:
            print("Error: User not found.")

        flash("Invalid username/email or password.", "danger")
        return redirect(url_for("login"))

    return render_template("login.html")

# 🚀 Signup
from werkzeug.security import generate_password_hash, check_password_hash

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form.get("email")
        username = request.form.get("username")
        password = request.form.get("password")

        if not email or not username or not password:
            flash("All fields are required!", "danger")
            return redirect(url_for("signup"))

        if len(username) < 5 or sum(c.isalpha() for c in username) < 4:
            flash("Username must be at least 5 characters with at least 4 letters.", "danger")
            return redirect(url_for("signup"))

        password_regex = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{6,}$"
        if not re.match(password_regex, password):
            flash("Password must contain an uppercase letter, lowercase letter, number, and special character.", "danger")
            return redirect(url_for("signup"))

        # ✅ Fix: Use generate_password_hash()
        hashed_password = generate_password_hash(password)

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE username = ? OR email = ?", (username, email))
        existing_user = cursor.fetchone()

        if existing_user:
            flash("Username or email already exists!", "danger")
            conn.close()
            return redirect(url_for("signup"))

        try:
            cursor.execute("INSERT INTO users (email, username, password, role) VALUES (?, ?, ?, 'user')",
                           (email, username, hashed_password))
            conn.commit()
            conn.close()
            flash("Signup successful! Please login.", "success")
            return redirect(url_for("login"))
        except sqlite3.Error as e:
            flash(f"Database error: {e}", "danger")
            conn.close()
            return redirect(url_for("signup"))

    return render_template("signup.html")

# 🔑 Forgot Password
@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()

        if user:
            reset_token = secrets.token_urlsafe(16)  
            cursor.execute("UPDATE users SET reset_token = ? WHERE email = ?", (reset_token, email))
            conn.commit()

            reset_link = url_for('reset_password', token=reset_token, _external=True)

            msg = Message("Password Reset Request", sender=app.config["MAIL_USERNAME"], recipients=[email])
            msg.body = f"Click the link to reset your password: {reset_link}"
            mail.send(msg)

            flash("A password reset link has been sent to your email.", "info")
        else:
            flash("Error: Email not found.", "danger")

        conn.close()

    return render_template('forgot_password.html')

# 🔑 Reset Password
@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE reset_token = ?", (token,))
    user = cursor.fetchone()

    if not user:
        flash("Invalid or expired reset token.", "danger")
        return redirect(url_for("forgot_password"))

    if request.method == 'POST':
        new_password = bcrypt.hashpw(request.form['new_password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cursor.execute("UPDATE users SET password = ?, reset_token = NULL WHERE email = ?", (new_password, user["email"]))
        conn.commit()
        conn.close()

        flash("Your password has been reset successfully!", "success")
        return redirect(url_for("login"))

    conn.close()
    return render_template('reset_password.html', token=token)

# 🔑 Logout
@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("home"))

    # 🏠 User Dashboard
@app.route('/user_dashboard')
def user_dashboard():
    if "username" not in session:
        flash("You must be logged in to access the dashboard.", "danger")
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Fetch user details
    cursor.execute("SELECT * FROM users WHERE username = ?", (session["username"],))
    user = cursor.fetchone()
    conn.close()

    if not user:
        flash("Error: User not found.", "danger")
        return redirect(url_for("home"))

    return render_template(
        'user_dashboard.html',
        username=user["username"],
        email=user["email"]
    )

# 🎥 Learning Mode - Show Videos from Database
@app.route('/learning')
def learning():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM videos ORDER BY id DESC")
    videos = cursor.fetchall()
    conn.close()
    
    print(f"\n=== LEARNING MODE DEBUG ===")
    print(f"Total videos found: {len(videos)}")
    for video in videos:
        print(f"Video ID: {video['id']}, Title: {video['title']}, Filename: {video['filename']}")
    
    return render_template("learning.html", videos=videos)


# 🎬 Watch Video Page
@app.route('/watch/<int:video_id>')
def watch(video_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, title, description, filename FROM videos WHERE id = ?", (video_id,))
    video = cursor.fetchone()

    cursor.execute("SELECT id, title FROM videos WHERE id != ?", (video_id,))
    other_videos = cursor.fetchall()

    conn.close()

    if not video:
        flash("Video not found!", "danger")
        return redirect(url_for('learning'))

    return render_template('watch.html', video=video, other_videos=other_videos)


# 🛠️ Admin Profile Settings
@app.route('/admin_profile', methods=['GET', 'POST'])
def admin_profile():
    if session.get("role") != "admin":
        flash("Access Denied. Admins only.", "danger")
        return redirect(url_for("home"))

    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        new_email = request.form['email']
        new_password = request.form['password']

        if new_password:
            hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            cursor.execute("UPDATE users SET email = ?, password = ? WHERE username = ?", 
                           (new_email, hashed_password, session["username"]))
        else:
            cursor.execute("UPDATE users SET email = ? WHERE username = ?", 
                           (new_email, session["username"]))

        conn.commit()
        conn.close()
        flash("Profile updated successfully!", "success")
        return redirect(url_for('admin'))

    cursor.execute("SELECT email FROM users WHERE username = ?", (session["username"],))
    admin = cursor.fetchone()
    conn.close()

    return render_template('admin_profile.html', admin=admin)

# Edit User 
@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    if session.get("role") != "admin":
        flash("Access Denied. Admins only.", "danger")
        return redirect(url_for("home"))

    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        new_username = request.form.get('username')
        new_email = request.form.get('email')
        new_role = request.form.get('role')

        cursor.execute("UPDATE users SET username = ?, email = ?, role = ? WHERE id = ?",
                       (new_username, new_email, new_role, user_id))
        conn.commit()
        conn.close()
        flash("User updated successfully!", "success")
        return redirect(url_for('admin'))

    # GET method - fetch user to populate form
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()

    if not user:
        flash("User not found.", "danger")
        return redirect(url_for('admin'))

    return render_template("edit_user.html", user=user)

# Delete User
@app.route('/delete_user/<int:user_id>')
def delete_user(user_id):
    if session.get("role") != "admin":
        flash("Access Denied. Admins only.", "danger")
        return redirect(url_for("home"))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

    flash("User deleted successfully.", "success")
    return redirect(url_for("admin"))

# 🎥 Admin: Upload Video
@app.route('/upload_video', methods=['POST'])
def upload_video():
    print("\n" + "="*50)
    print("VIDEO UPLOAD STARTED")
    print("="*50)
    
    title = request.form.get('title')
    description = request.form.get('description')
    category = request.form.get('category')
    file = request.files.get('video')
    
    print(f"Title received: '{title}'")
    print(f"Description received: '{description}'")
    print(f"Category received: '{category}'")
    print(f"File received: {file}")
    
    if file:
        print(f"File name: {file.filename}")
        print(f"File content type: {file.content_type}")
    
    if not title or not file:
        print("ERROR: Missing title or file")
        flash("Title and video are required.", "danger")
        return redirect(url_for('upload'))

    if file and allowed_file(file.filename):
        print("File type is allowed")
        
        filename = secure_filename(file.filename)
        print(f"Secure filename: {filename}")
        
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        print(f"Full save path: {filepath}")
        print(f"Upload folder exists: {os.path.exists(app.config['UPLOAD_FOLDER'])}")
        
        try:
            file.save(filepath)
            print(f"File saved successfully")
            print(f"File exists after save: {os.path.exists(filepath)}")
            print(f"File size: {os.path.getsize(filepath)} bytes")
        except Exception as e:
            print(f"ERROR saving file: {e}")
            flash(f"Error saving file: {e}", "danger")
            return redirect(url_for('upload'))
        
        # Database path
        relative_path = f'uploads/{filename}'
        print(f"Database path will be: {relative_path}")
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            print("Executing INSERT query...")
            cursor.execute(
                "INSERT INTO videos (title, description, filename, category) VALUES (?, ?, ?, ?)",
                (title, description, relative_path, category)
            )
            
            print(f"Rows affected: {cursor.rowcount}")
            
            conn.commit()
            print("Database commit successful")
            
            # Verify it was inserted
            cursor.execute("SELECT COUNT(*) as count FROM videos")
            count = cursor.fetchone()['count']
            print(f"Total videos in database now: {count}")
            
            conn.close()
            
            print("SUCCESS: Video uploaded and saved to database")
            print("="*50 + "\n")
            
            flash("Video uploaded successfully!", "success")
            return redirect('/admin')
            
        except Exception as e:
            print(f"DATABASE ERROR: {e}")
            print(f"Error type: {type(e)}")
            import traceback
            traceback.print_exc()
            flash(f"Database error: {e}", "danger")
            return redirect(url_for('upload'))
    else:
        print(f"ERROR: File type not allowed: {file.filename}")
        flash("Invalid file type.", "danger")
        return redirect(url_for('upload'))

# 🎥 Admin: Delete Video
@app.route('/delete_video/<int:video_id>')
def delete_video(video_id):
    if session.get("role") != "admin":
        flash("Access Denied. Admins only.", "danger")
        return redirect(url_for("home"))

    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch video filepath
    cursor.execute("SELECT filepath FROM videos WHERE id = ?", (video_id,))
    video = cursor.fetchone()

    if not video:  # If no video found
        flash("Video not found!", "danger")
        conn.close()
        return redirect(url_for('admin_videos'))

    # Convert to absolute path and handle Windows paths
    file_path = os.path.abspath(video[0]).replace("\\", "/")
    print(f"Deleting file: {file_path}")  # Debugging

    # Delete the file if it exists
    if os.path.exists(file_path):
        os.remove(file_path)
        print("File deleted successfully.")
    else:
        print("File not found. Deleting database entry only.")

    # Delete video from database
    cursor.execute("DELETE FROM videos WHERE id = ?", (video_id,))
    conn.commit()
    conn.close()

    flash("Video deleted successfully!", "success")
    return redirect(url_for('admin_videos'))


# 📊 Admin Analytics Page
@app.route('/analytics')
def analytics():
    if session.get("role") != "admin":
        flash("Access Denied. Admins only.", "danger")
        return redirect(url_for("home"))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) AS total_users FROM users")
    total_users = cursor.fetchone()["total_users"]
    cursor.execute("SELECT username, email FROM users ORDER BY id DESC LIMIT 5")
    recent_signups = cursor.fetchall()
    conn.close()

    return render_template('analytics.html', total_users=total_users, recent_signups=recent_signups)

# 🛠️ Admin Panel (User Management)
@app.route('/admin')
def admin():
    if session.get("role") != "admin":
        flash("Access Denied. Admins only.", "danger")
        return redirect(url_for("home"))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, email, role FROM users")
    users = cursor.fetchall()
    conn.close()

    return render_template('admin.html', users=users)

# 📌 Route for Sign Language Detection Video Stream
@app.route('/video_feed')
def video_feed():
    def generate_frames():
        cap = cv2.VideoCapture(0)
        num_frames = 0

        while True:
            success, frame = cap.read()
            if not success:
                break

            frame, prediction = detect_sign_from_frame(frame, num_frames)
            num_frames += 1

            _, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

        cap.release()

    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# ✅ Ensure Database Exists Before Running
if __name__ == '__main__':
    create_tables()
    app.run(debug=True) 