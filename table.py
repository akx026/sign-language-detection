import sqlite3

# Connect to the database
conn = sqlite3.connect("users.db")
cursor = conn.cursor()

# Fetch all records from the users table
cursor.execute("SELECT * FROM users")
rows = cursor.fetchall()

# Print the table contents
for row in rows:
    print(row)

# Close the connection
conn.close()
