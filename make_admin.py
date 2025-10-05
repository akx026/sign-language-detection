import sqlite3

DATABASE = "users.db"

conn = sqlite3.connect(DATABASE)
cursor = conn.cursor()

# Change 'target_username' to the username you want to make an admin
target_username = "akhil varghese"

cursor.execute("UPDATE users SET role = 'admin' WHERE username = ?", (target_username,))
conn.commit()
conn.close()

print(f"{target_username} is now an admin!")
