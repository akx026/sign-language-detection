import sqlite3

DATABASE = "users.db"

conn = sqlite3.connect(DATABASE)
cursor = conn.cursor()

# Create users table with email, username, password, and role
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL
    )
''')

# Insert an admin user
cursor.execute("INSERT INTO users (email, username, password, role) VALUES (?, ?, ?, ?)", 
               ("admin@gmail.com", "admin", "admin123", "admin"))


conn.commit()
conn.close()

print("✅ Admin user created! Use username: 'admin' and password: 'adminpassword'")
