import sqlite3

DATABASE = "users.db"

# Connect to the database
conn = sqlite3.connect(DATABASE)
cursor = conn.cursor()

# Fetch all users and their roles
cursor.execute("SELECT username, role FROM users;")
users = cursor.fetchall()

# Display users and roles
for user in users:
    print(f"Username: {user[0]}, Role: {user[1]}")

conn.close()
